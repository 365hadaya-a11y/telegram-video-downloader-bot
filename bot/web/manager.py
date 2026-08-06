"""Web download jobs.

The website reuses the bot's :class:`YtDlpService` (same engine, same temp
storage) but runs its own jobs: every browser request gets a job id, progress
is polled over HTTP, and the finished file is streamed straight from disk.

State lives in memory only — there is a single app instance on Northflank, so
this is fine and keeps the design simple. Finished files are deleted by a TTL
cleanup loop.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from aiohttp import web

from ..config import Settings
from ..utils.formatters import format_duration, format_size
from ..utils.retry import retry_async
from ..services.ytdlp import (
    DownloadCancelled,
    ProgressChannel,
    ProgressPayload,
    YtDlpService,
    available_qualities,
    best_height,
    best_audio_format,
    estimate_size,
    has_video_formats,
)

logger = logging.getLogger(__name__)

# yt-dlp extraction is expensive — cache /api/info responses briefly.
_INFO_CACHE_TTL = 300.0  # seconds
_MAX_INFO_CACHE = 200  # hard cap to keep memory bounded
# Max simultaneous yt-dlp extractions (each eats ~50-100 MB on a 256 MB plan).
_MAX_INFO_INFLIGHT = 2


def _validate_url(url: str) -> None:
    """Reject anything that isn't an http(s) URL (blocks file://, data:, ftp…)."""
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("Only http(s) URLs are supported")


@dataclass(slots=True)
class WebJob:
    """One browser-initiated download."""

    id: str
    url: str
    mode: str  # "video" | "audio"
    height: int | None
    state: str = "queued"  # queued | downloading | processing | done | error | cancelled
    progress: float = 0.0
    downloaded: int = 0
    total: int | None = None
    speed: float | None = None
    eta: float | None = None
    title: str | None = None
    path: Path | None = None
    filename: str | None = None
    error: str | None = None
    created: float = field(default_factory=time.monotonic)
    cancel_event: threading.Event = field(default_factory=threading.Event)


def _audio_size(info: dict) -> str | None:
    """Real audio-stream size for the audio-only button (video excluded)."""
    audio = best_audio_format(info)
    if not audio:
        return None
    size = audio.get("filesize") or audio.get("filesize_approx")
    return format_size(size) if size else None


def _curate_info(settings: Settings, info: dict) -> dict:
    """Turn a raw yt-dlp info dict into the small payload the site needs."""
    qualities = [
        {"height": h, "size": format_size(estimate_size(info, h))}
        for h in available_qualities(info, limit=10)
    ]
    audio = best_audio_format(info)
    return {
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "duration": format_duration(info.get("duration")),
        "duration_seconds": info.get("duration"),
        "thumbnail": (info.get("thumbnails") or [{}])[-1].get("url") or info.get("thumbnail"),
        "webpage_url": info.get("webpage_url"),
        "best_height": best_height(info),
        "best_size": format_size(estimate_size(info, None)),
        "audio_size": _audio_size(info),
        "has_audio": audio is not None,
        "has_video": has_video_formats(info),
        "qualities": qualities,
        "max_file_size_mb": settings.web_max_file_size_mb,
    }


class WebDownloadManager:
    """Registry + runner for website download jobs."""

    def __init__(self, settings: Settings, ytdlp: YtDlpService) -> None:
        self.settings = settings
        self.ytdlp = ytdlp
        self.jobs: dict[str, WebJob] = {}
        self._info_cache: dict[str, tuple[float, dict]] = {}
        self._info_inflight = 0
        self._lock = asyncio.Lock()

    # -- info ----------------------------------------------------------------

    def info_busy(self) -> bool:
        """True when the extraction concurrency cap is reached."""
        return self._info_inflight >= _MAX_INFO_INFLIGHT

    async def fetch_info(self, url: str) -> dict:
        """Fetch + curate video info (cached briefly)."""
        key = url.strip()
        _validate_url(key)
        now = time.monotonic()
        cached = self._info_cache.get(key)
        if cached and now - cached[0] < _INFO_CACHE_TTL:
            return cached[1]

        self._info_inflight += 1  # run on the loop — no race
        try:
            info = await retry_async(
                lambda: self.ytdlp.get_video_info(url),
                attempts=2,
                base_delay=1.0,
            )
        finally:
            self._info_inflight -= 1
        curated = _curate_info(self.settings, info)
        self._info_cache[key] = (now, curated)
        if len(self._info_cache) > _MAX_INFO_CACHE:
            self._info_cache.pop(next(iter(self._info_cache)))  # drop oldest
        return curated

    # -- jobs ----------------------------------------------------------------

    def capacity_available(self) -> bool:
        active = sum(1 for j in self.jobs.values() if j.state in ("queued", "downloading", "processing"))
        return active < self.settings.web_max_concurrent_jobs

    def create_job(self, url: str, mode: str, height: int | None) -> WebJob | None:
        """Create a job (respecting the concurrency cap). ``None`` = busy."""
        if not self.capacity_available():
            return None
        _validate_url(url.strip())
        job = WebJob(
            id=uuid4().hex[:16],
            url=url.strip(),
            mode="audio" if mode == "audio" else "video",
            height=None if mode == "audio" else height,
        )
        self.jobs[job.id] = job
        return job

    async def run_job(self, job: WebJob) -> None:
        """Download the job's file into its workdir and publish progress."""
        workdir = self.settings.temp_dir / "web" / job.id
        channel = ProgressChannel()
        job.state = "downloading"
        pump = asyncio.create_task(self._pump(job, channel))
        try:
            info = await retry_async(
                lambda: self.ytdlp.get_video_info(job.url),
                attempts=2,
                base_delay=1.0,
            )
            if not job.cancel_event.is_set():
                estimated = estimate_size(info, job.height if job.mode == "video" else None)
                if estimated and estimated > self.settings.web_max_file_size_bytes:
                    job.error = f"File too large ({format_size(estimated)}) for the web limit"
                else:
                    job.title = info.get("title")
                    path = await self.ytdlp.download(
                        url=info.get("webpage_url") or job.url,
                        video_id=info.get("id") or "video",
                        mode=job.mode,
                        height=job.height,
                        channel=channel,
                        cancel_event=job.cancel_event,
                        workdir=workdir,
                    )
                    if not job.cancel_event.is_set():
                        job.path = path
                        job.filename = path.name
        except DownloadCancelled:
            pass
        except Exception as exc:  # noqa: BLE001
            logger.exception("Web job %s failed", job.id)
            job.error = str(exc)[:400]
        finally:
            channel.push(ProgressPayload(status="done"))
            try:
                await pump
            except Exception:  # noqa: BLE001
                logger.exception("Web progress pump crashed for %s", job.id)

        # The pump may have flipped the state to "processing" — settle the
        # final state only after it has drained (avoids a done->processing race).
        if job.cancel_event.is_set():
            job.state = "cancelled"
            job.path = None
        elif job.path is not None and job.path.exists():
            job.state = "done"
            job.progress = 100.0
        else:
            job.state = "error"
            job.error = job.error or "Unknown error"

    async def _pump(self, job: WebJob, channel: ProgressChannel) -> None:
        while True:
            payload = await channel.pop()
            if payload.status == "done":
                return
            if payload.status == "finished":
                job.state = "processing"
                continue
            job.downloaded = payload.downloaded_bytes
            job.total = payload.total_bytes
            job.speed = payload.speed
            job.eta = payload.eta
            if payload.total_bytes:
                job.progress = min(100.0, payload.downloaded_bytes / payload.total_bytes * 100)

    def status(self, job_id: str) -> dict | None:
        job = self.jobs.get(job_id)
        if job is None:
            return None
        return {
            "state": job.state,
            "progress": round(job.progress, 1),
            "downloaded": job.downloaded,
            "total": job.total,
            "speed": job.speed,
            "eta": job.eta,
            "title": job.title,
            "filename": job.filename,
            "error": job.error,
        }

    def cancel(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if job is None:
            return False
        job.cancel_event.set()
        return True

    async def file_response(self, job_id: str) -> web.FileResponse | None:
        job = self.jobs.get(job_id)
        if job is None or job.state != "done" or not job.path or not job.path.exists():
            return None
        name = (job.filename or job.path.name).replace('"', "").replace("\n", "").replace("\r", "")
        disposition = f"attachment; filename=\"{name}\"; filename*=UTF-8''{quote(name, safe='')}"
        return web.FileResponse(job.path, headers={"Content-Disposition": disposition})

    async def cleanup_loop(self) -> None:
        """Delete job files/dirs whose TTL has expired (also drops stale jobs)."""
        ttl = self.settings.web_job_ttl_minutes * 60
        while True:
            await asyncio.sleep(60)
            now = time.monotonic()
            stale = [j for j in self.jobs.values() if j.state in ("done", "error", "cancelled") and now - j.created > ttl]
            for job in stale:
                if job.path and job.path.exists():
                    try:
                        job.path.unlink(missing_ok=True)
                    except OSError:
                        pass
                workdir = self.settings.temp_dir / "web" / job.id
                if workdir.exists():
                    shutil.rmtree(workdir, ignore_errors=True)
                self.jobs.pop(job.id, None)
                logger.info("Web job %s expired, files cleaned", job.id)
