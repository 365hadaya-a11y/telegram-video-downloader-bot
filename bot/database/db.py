"""Async SQLite persistence layer (users, stickers, download log).

Uses ``aiosqlite`` so the database never blocks the event loop.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    last_name   TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stickers (
    key        TEXT PRIMARY KEY,
    file_id    TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS downloads_log (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL,
    url              TEXT,
    mode             TEXT,
    quality          TEXT,
    file_size        INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    success          INTEGER DEFAULT 0,
    error            TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_downloads_user_time
    ON downloads_log (user_id, created_at);
"""


class Database:
    """Thin async wrapper around a SQLite connection."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected — call connect() first")
        return self._conn

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.executescript(_SCHEMA)
        await self.conn.commit()
        logger.info("Database ready at %s", self.path)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    # ── Users ─────────────────────────────────────────────────────

    async def upsert_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO users (id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_name  = excluded.last_name,
                last_seen  = datetime('now')
            """,
            (user_id, username, first_name, last_name),
        )
        await self.conn.commit()

    async def users_count(self) -> int:
        cursor = await self.conn.execute("SELECT COUNT(*) AS c FROM users")
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    async def all_user_ids(self) -> list[int]:
        """Every registered user id (used by the /broadcast command)."""
        cursor = await self.conn.execute("SELECT id FROM users ORDER BY id")
        rows = await cursor.fetchall()
        return [int(row["id"]) for row in rows]

    async def remove_user(self, user_id: int) -> None:
        """Remove a user (e.g. someone who blocked the bot)."""
        await self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await self.conn.commit()

    # ── Download log ──────────────────────────────────────────────

    async def log_download(
        self,
        user_id: int,
        url: str | None,
        mode: str,
        quality: int | None,
        file_size: int,
        duration_seconds: int | None,
        success: bool,
        error: str | None = None,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO downloads_log
                (user_id, url, mode, quality, file_size, duration_seconds, success, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                url,
                mode,
                str(quality) if quality else None,
                file_size,
                duration_seconds,
                1 if success else 0,
                error,
            ),
        )
        await self.conn.commit()

    async def today_downloads(self, user_id: int) -> int:
        """Successful downloads by a user today (used for the daily limit)."""
        cursor = await self.conn.execute(
            """
            SELECT COUNT(*) AS c FROM downloads_log
            WHERE user_id = ? AND success = 1 AND date(created_at) = date('now')
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    async def total_downloads(self) -> int:
        cursor = await self.conn.execute("SELECT COUNT(*) AS c FROM downloads_log WHERE success = 1")
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    async def today_downloads_all(self) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM downloads_log WHERE success = 1 AND date(created_at) = date('now')"
        )
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    async def prune_logs(self, days: int = 30) -> None:
        await self.conn.execute(
            "DELETE FROM downloads_log WHERE created_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        await self.conn.commit()

    # ── Stickers ──────────────────────────────────────────────────

    async def set_sticker(self, key: str, file_id: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO stickers (key, file_id, updated_at) VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                file_id = excluded.file_id,
                updated_at = datetime('now')
            """,
            (key, file_id),
        )
        await self.conn.commit()

    async def get_sticker(self, key: str) -> str | None:
        cursor = await self.conn.execute("SELECT file_id FROM stickers WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return str(row["file_id"]) if row else None

    async def delete_sticker(self, key: str) -> None:
        await self.conn.execute("DELETE FROM stickers WHERE key = ?", (key,))
        await self.conn.commit()

    async def list_stickers(self) -> dict[str, Any]:
        cursor = await self.conn.execute("SELECT key, file_id, updated_at FROM stickers ORDER BY key")
        rows = await cursor.fetchall()
        return {str(row["key"]): str(row["file_id"]) for row in rows}
