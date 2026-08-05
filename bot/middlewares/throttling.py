"""Message throttling middleware (sliding window per user)."""

from __future__ import annotations

import logging

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from ..config import Settings
from ..services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """Drops (and occasionally warns about) messages that arrive too fast."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.limiter = RateLimiter(
            max_events=settings.rate_limit_max,
            window_seconds=settings.rate_limit_window_seconds,
            warn_cooldown_seconds=settings.rate_limit_warn_cooldown_seconds,
        )

    async def __call__(self, handler, event: Message, data: dict) -> None:  # type: ignore[no-untyped-def]
        user = event.from_user
        # Never throttle admins or bot commands.
        if user is None or user.id in self.settings.admin_ids:
            return await handler(event, data)
        if event.text and event.text.startswith("/"):
            return await handler(event, data)

        if self.limiter.is_limited(user.id):
            if self.limiter.can_warn(user.id):
                try:
                    await event.answer("⏳ <b>Slow down!</b>\nYou're sending messages too fast. 😅")
                except TelegramAPIError:
                    pass
            return None
        return await handler(event, data)
