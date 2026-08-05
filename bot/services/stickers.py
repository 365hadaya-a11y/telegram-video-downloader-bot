"""Sticker management.

Priority: hard-coded env override → database (set via /setsticker) →
auto-mapping from a public sticker set → graceful skip.

If no stickers are configured the bot simply falls back to premium
emojis — nothing ever breaks.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import Message

from ..config import Settings
from ..database.db import Database

logger = logging.getLogger(__name__)

STICKER_KEYS = ("welcome", "loading", "downloading", "uploading", "success", "error", "celebration")

KEY_EMOJI = {
    "welcome": "👋",
    "loading": "⏳",
    "downloading": "⬇️",
    "uploading": "📤",
    "success": "✅",
    "error": "❌",
    "celebration": "🎉",
}


class StickerService:
    """Resolves and sends stickers for each flow step."""

    def __init__(self, settings: Settings, db: Database) -> None:
        self.settings = settings
        self.db = db
        self._set_cache: dict[str, str] = {}
        self._lock = asyncio.Lock()

    def _env_override(self, key: str) -> str | None:
        return getattr(self.settings, f"sticker_{key}_file_id", None)

    async def get_file_id(self, bot: Bot, key: str) -> str | None:
        """Best-known file_id for ``key`` or None."""
        if key not in STICKER_KEYS:
            return None

        env = self._env_override(key)
        if env:
            return env

        stored = await self.db.get_sticker(key)
        if stored:
            return stored

        return await self._load_from_set(bot, key)

    async def _load_from_set(self, bot: Bot, key: str) -> str | None:
        """Map the key's emoji to a sticker inside a configured public set."""
        if not self.settings.sticker_set_name:
            return None
        async with self._lock:
            if key in self._set_cache:
                return self._set_cache[key]
            try:
                sticker_set = await bot.get_sticker_set(self.settings.sticker_set_name)
            except TelegramAPIError as exc:
                logger.warning("Sticker set %r unavailable: %s", self.settings.sticker_set_name, exc)
                return None

            target = KEY_EMOJI.get(key, "")
            for sticker in sticker_set.stickers:
                if target in (sticker.emoji or ""):
                    self._set_cache[key] = sticker.file_id
                    await self.db.set_sticker(key, sticker.file_id)  # persist for next run
                    return sticker.file_id
        return None

    async def send(self, message: Message, bot: Bot, key: str) -> bool:
        """Send the sticker for ``key`` (best-effort). Returns True on success."""
        file_id = await self.get_file_id(bot, key)
        if not file_id:
            return False
        try:
            await message.answer_sticker(sticker=file_id)
            return True
        except TelegramBadRequest:
            logger.warning("Sticker %s (%s) rejected — removing it", key, file_id)
            await self.db.delete_sticker(key)
            return False
        except TelegramAPIError as exc:
            logger.warning("Failed to send sticker %s: %s", key, exc)
            return False
