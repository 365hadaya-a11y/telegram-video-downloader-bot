"""HTTP layer for the web download site.

All routes are registered onto the SAME aiohttp app that serves the Telegram
webhook (port 8080), so Northflank exposes both under one public URL:

    /                 → premium download page (RTL Arabic / English)
    /health           → "ok" for platform health checks
    /d/{job_id}       → redirect to the page with the job preloaded
    /api/info         → GET  ?url=…   → curated video info
    /api/download     → POST {url, mode, height} → {job_id}
    /api/progress/{id}→ GET  → live download state
    /api/cancel/{id}  → POST → cancel the job
    /api/file/{id}    → GET  → stream the finished file
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from aiohttp import web
from aiohttp.web import json_response

from ..services import Services

logger = logging.getLogger(__name__)

_FRONTEND = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")

# Cheap per-IP limiter for the expensive /api/info endpoint.
_INFO_LIMIT = 6  # requests
_INFO_WINDOW = 60.0  # seconds


class _InfoLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def limited(self, ip: str) -> bool:
        now = time.monotonic()
        async with self._lock:
            hits = [ts for ts in self._hits.get(ip, []) if now - ts < _INFO_WINDOW]
            hits.append(now)
            self._hits[ip] = hits
            # prune stale IPs so the dict stays bounded on long-lived instances
            if len(self._hits) > 500:
                for key, stamps in list(self._hits.items()):
                    if not any(now - ts < _INFO_WINDOW for ts in stamps):
                        del self._hits[key]
            return len(hits) > _INFO_LIMIT


def _client_ip(request: web.Request) -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    peer = request.transport.get_extra_info("peername") if request.transport else None
    return str(peer[0] if peer else "unknown")


def create_web_app(app: web.Application, services: Services) -> None:
    """Mount every site route on ``app`` (shared with the webhook)."""
    settings = services.settings
    manager = services.web
    limiter = _InfoLimiter()

    frontend = _FRONTEND.replace("__BOT_USERNAME__", settings.bot_username or "")

    # ── pages ──────────────────────────────────────────────────────────
    async def index(_request: web.Request) -> web.Response:
        return web.Response(text=frontend, content_type="text/html", charset="utf-8")

    async def health(_request: web.Request) -> web.Response:
        return web.Response(text="ok")

    async def job_page(request: web.Request) -> web.Response:
        job_id = request.match_info["job_id"]
        if not job_id or not all(c.isalnum() for c in job_id):
            return web.HTTPNotFound()
        return web.HTTPFound(f"/?job={job_id}")

    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/d/{job_id}", job_page)

    # ── API ────────────────────────────────────────────────────────────
    async def api_info(request: web.Request) -> web.Response:
        if await limiter.limited(_client_ip(request)):
            return json_response({"ok": False, "error": "Rate limit reached — slow down!"}, status=429)
        url = (request.query.get("url") or "").strip()
        if not url:
            return json_response({"ok": False, "error": "Missing url parameter"}, status=400)
        if not url.lower().startswith(("http://", "https://")):
            return json_response({"ok": False, "error": "Only http(s) URLs are supported"}, status=400)
        try:
            info = await manager.fetch_info(url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Web /api/info failed for %r: %s", url, exc)
            return json_response({"ok": False, "error": str(exc)[:300]}, status=502)
        return json_response({"ok": True, "info": info})

    async def api_download(request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:  # noqa: BLE001
            return json_response({"ok": False, "error": "Invalid JSON body"}, status=400)

        url = (data.get("url") or "").strip()
        mode = "audio" if data.get("mode") == "audio" else "video"
        height_raw = data.get("height")
        height = int(height_raw) if isinstance(height_raw, int) or (isinstance(height_raw, str) and height_raw.isdigit()) else None

        if not url:
            return json_response({"ok": False, "error": "Missing url"}, status=400)
        if not url.lower().startswith(("http://", "https://")):
            return json_response({"ok": False, "error": "Only http(s) URLs are supported"}, status=400)

        job = manager.create_job(url, mode, height)
        if job is None:
            return json_response({"ok": False, "error": "Server busy — try again in a moment"}, status=409)

        asyncio.create_task(manager.run_job(job))
        logger.info("Web download job %s started (%s)", job.id, url)
        return json_response({"ok": True, "job_id": job.id})

    async def api_progress(request: web.Request) -> web.Response:
        status = manager.status(request.match_info["job_id"])
        if status is None:
            return json_response({"ok": False, "error": "Job not found"}, status=404)
        return json_response({"ok": True, **status})

    async def api_cancel(request: web.Request) -> web.Response:
        ok = manager.cancel(request.match_info["job_id"])
        if not ok:
            return json_response({"ok": False, "error": "Job not found"}, status=404)
        return json_response({"ok": True})

    async def api_file(request: web.Request) -> web.Response:
        response = await manager.file_response(request.match_info["job_id"])
        if response is None:
            return json_response({"ok": False, "error": "File not found or expired"}, status=404)
        return response

    app.router.add_get("/api/info", api_info)
    app.router.add_post("/api/download", api_download)
    app.router.add_get("/api/progress/{job_id}", api_progress)
    app.router.add_post("/api/cancel/{job_id}", api_cancel)
    app.router.add_get("/api/file/{job_id}", api_file)

    logger.info(
        "Web download site mounted — base: %s, max jobs: %d, max file: %d MB",
        settings.web_base or "(derived)",
        settings.web_max_concurrent_jobs,
        settings.web_max_file_size_mb,
    )
