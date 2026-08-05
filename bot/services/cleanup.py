"""Background cleanup: sweep stale temp files and prune the download log."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from ..config import Settings
from ..database.db import Database

logger = logging.getLogger(__name__)

LOG_RETENTION_DAYS = 30


class CleanupService:
    """Periodically removes old temp files and prunes the database."""

    def __init__(self, settings: Settings, db: Database) -> None:
        self.settings = settings
        self.db = db

    async def run(self) -> None:
        """Long-running background loop. Start it with asyncio.create_task."""
        await asyncio.sleep(5)  # let the bot boot first
        await self._sweep()
        while True:
            await asyncio.sleep(self.settings.cleanup_interval_minutes * 60)
            await self._sweep()

    async def _sweep(self) -> None:
        await self._clean_temp_files()
        await self.db.prune_logs(days=LOG_RETENTION_DAYS)

    def _clean_temp_files(self) -> None:
        cutoff = time.time() - self.settings.cleanup_age_hours * 3600
        removed = 0
        for path in self.settings.temp_dir.rglob("*"):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
                    removed += 1
            except OSError as exc:  # file locked / being written
                logger.debug("Could not remove %s: %s", path, exc)
        if removed:
            logger.info("Temp cleanup removed %d stale file(s)", removed)

    def temp_dir_size(self) -> int:
        """Total bytes currently stored in the temp dir (for /stats)."""
        if not self.settings.temp_dir.exists():
            return 0
        return sum(
            p.stat().st_size
            for p in self.settings.temp_dir.rglob("*")
            if p.is_file()
        )
