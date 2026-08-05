"""Thin async wrapper around ``yt-dlp``.

yt-dlp is blocking, so every heavy call runs in a worker thread via
``asyncio.to_thread``. Progress events flow from the yt-dlp hook thread
into the event loop through a thread-safe queue.
"""

from __future__ import annotations

import asyncio
import logging
import os
import queue
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yt_dlp

from ..config import Settings

logger = logging.getLogger(__name__)


class DownloadCancelled(Exception):
    """Raised when the user cancels an in-flight download."""


@dataclass(slots=True)
class ProgressPayload:
    """One progress event emitted by the yt-dlp hook."""

    status: str  # "downloading" | "finished" | "done"
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed: float | None = None  # bytes / second
    eta: float | None = None  # seconds
    filename: str | None = None


class ProgressChannel:
    """Thread-safe bridge between yt-dlp hook threads and the asyncio loop."""

    def __init__(self) -> None:
        self._queue: queue.Queue[ProgressPayload] = queue.Queue()

    def push(self, payload: ProgressPayload) -> None:
        self._queue.put(payload)

    async def pop(self) -> ProgressPayload:
        return await asyncio.to_thread(self._queue.get)


# ── Format helpers ───────────────────────────────────────────────────────────


def _video_formats(info: dict) -> list[dict]:
    return [f for f in info.get("formats", []) if f.get("vcodec") and f.get("vcodec") != "none"]


def _audio_formats(info: dict) -> list[dict]:
    return [
        f
        for f in info.get("formats", [])
        if f.get("acodec") and f.get("acodec") != "none" and (not f.get("vcodec") or f.get("vcodec") == "none")
    ]


def _format_size(fmt: dict) -> int | None:
    return fmt.get("filesize") or fmt.get("filesize_approx")


def best_video_format(info: dict) -> dict | None:
    formats = _video_formats(info)
    if not formats:
        return None
    return max(formats, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))


def best_audio_format(info: dict) -> dict | None:
    formats = _audio_formats(info)
    if not formats:
        return None
    return max(formats, key=lambda f: (f.get("abr") or 0, _format_size(f) or 0))


def selected_video_format(info: dict, height: int | None) -> dict | None:
    """Best video format at or below ``height`` (or overall best if None)."""
    if height is None:
        return best_video_format(info)
    candidates = [f for f in _video_formats(info) if (f.get("height") or 0) <= height]
    if not candidates:
        return best_video_format(info)
    return max(candidates, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))


def available_qualities(info: dict, limit: int = 10) -> list[int]:
    heights = sorted({f["height"] for f in _video_formats(info) if f.get("height")}, reverse=True)
    return heights[:limit]


def best_height(info: dict) -> int | None:
    fmt = best_video_format(info)
    return fmt.get("height") if fmt else None


def estimate_size(info: dict, height: int | None) -> int | None:
    """Estimated download size (video + audio) for the given height, if known."""
    total = 0
    known = False

    video = selected_video_format(info, height)
    if video and (size := _format_size(video)):
        total += size
        known = True

    audio = best_audio_format(info)
    if audio and (size := _format_size(audio)):
        total += size
        known = True

    return total if known else None


def format_spec(mode: str, height: int | None) -> str:
    """Build the yt-dlp ``format`` selector."""
    if mode == "audio":
        return "ba/b"
    if height is None:
        return "bv*+ba/b"
    return f"bv*[height<={height}]+ba/b[height<={height}]/b[height<={height}]"


def has_video_formats(info: dict) -> bool:
    return bool(_video_formats(info))


# ── Hook factory ─────────────────────────────────────────────────────────────


def _make_progress_hook(
    channel: ProgressChannel,
    cancel_event: threading.Event,
) -> Callable[[dict], None]:
    def hook(data: dict) -> None:
        if cancel_event.is_set():
            raise DownloadCancelled("Download cancelled by user")
        status = data.get("status")
        if status == "downloading":
            channel.push(
                ProgressPayload(
                    status="downloading",
                    downloaded_bytes=data.get("downloaded_bytes") or 0,
                    total_bytes=data.get("total_bytes") or data.get("total_bytes_estimate"),
                    speed=data.get("speed"),
                    eta=data.get("eta"),
                )
            )
        elif status == "finished":
            channel.push(ProgressPayload(status="finished", filename=data.get("filename")))

    return hook


# ── Service ──────────────────────────────────────────────────────────────────


class YtDlpService:
    """Async facade over yt-dlp for info fetching and downloading."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.ffmpeg_location = settings.ffmpeg_location or shutil.which("ffmpeg")
        if not self.ffmpeg_location:
            logger.warning(
                "FFmpeg was not found — video+audio merging and MP3 extraction will fail. "
                "Install FFmpeg or set FFMPEG_LOCATION."
            )
        else:
            logger.info("Using FFmpeg at %s", self.ffmpeg_location)

    # -- internals -----------------------------------------------------------

    def _base_opts(
        self,
        progress_cb: Callable[[dict], None] | None,
        cancel_event: threading.Event | None,
    ) -> dict:
        opts: dict = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "restrictfilenames": True,
            "windowsfilenames": os.name == "nt",
            "merge_output_format": "mp4",
            "socket_timeout": 30,
            "retries": 3,
            "fragments_retries": 3,
            "continuedl": True,
            "logger": logging.getLogger("yt_dlp"),
        }
        if self.ffmpeg_location:
            opts["ffmpeg_location"] = self.ffmpeg_location
        if self.settings.proxy:
            opts["proxy"] = self.settings.proxy
        if self.settings.cookies_file:
            opts["cookiefile"] = self.settings.cookies_file
        if progress_cb is not None:
            opts["progress_hooks"] = [progress_cb]
        return opts

    def _info_opts(self) -> dict:
        return self._base_opts(progress_cb=None, cancel_event=None)

    def _download_opts(
        self,
        mode: str,
        height: int | None,
        channel: ProgressChannel,
        cancel_event: threading.Event,
        workdir: Path,
    ) -> dict:
        workdir.mkdir(parents=True, exist_ok=True)
        opts = self._base_opts(_make_progress_hook(channel, cancel_event), cancel_event)
        opts["outtmpl"] = str(workdir / "%(id)s.%(ext)s")
        opts["format"] = format_spec(mode, height)
        if mode == "audio":
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(self.settings.audio_bitrate),
                }
            ]
        return opts

    # -- public API ----------------------------------------------------------

    async def get_video_info(self, url: str) -> dict:
        """Extract metadata (title, duration, formats, thumbnail…) without downloading."""
        with yt_dlp.YoutubeDL(self._info_opts()) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
        if not info:
            raise yt_dlp.utils.DownloadError("Could not extract any video information.")
        return info

    async def download(
        self,
        url: str,
        video_id: str,
        mode: str,
        height: int | None,
        channel: ProgressChannel,
        cancel_event: threading.Event,
        workdir: Path,
    ) -> Path:
        """Download the video/audio into ``workdir`` and return the final file path."""
        opts = self._download_opts(mode, height, channel, cancel_event, workdir)
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                await asyncio.to_thread(ydl.download, [url])
            except DownloadCancelled:
                raise
            except Exception as exc:
                if cancel_event.is_set():
                    raise DownloadCancelled from exc
                raise
        return self._resolve_output(video_id, mode, workdir)

    @staticmethod
    def _resolve_output(video_id: str, mode: str, workdir: Path) -> Path:
        expected_ext = "mp3" if mode == "audio" else "mp4"
        expected = workdir / f"{video_id}.{expected_ext}"
        if expected.exists():
            return expected
        candidates = [p for p in workdir.iterdir() if p.is_file() and p.name.startswith(video_id)]
        if candidates:
            return max(candidates, key=lambda p: p.stat().st_mtime)
        raise FileNotFoundError(f"Downloaded file for {video_id} was not found in {workdir}")
