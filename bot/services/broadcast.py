"""Admin broadcast service — announces a message/media to every user.

Progress is reported through an optional async callback so the UI can show
a live counter, and the admin can stop the broadcast at any time.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass
from typing import Any

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..database.db import Database

logger = logging.getLogger(__name__)


async def _maybe_await(value: Any) -> None:
    """Await ``value`` if it is a coroutine (accepts sync callbacks too)."""
    if inspect.isawaitable(value):
        await value


class BroadcastCB(CallbackData, prefix="bc"):
    """Callback for the \"🛑 Stop Broadcast\" button."""

    action: str


def broadcast_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛑 Stop Broadcast", callback_data=BroadcastCB(action="cancel").pack())]
        ]
    )


@dataclass
class BroadcastResult:
    sent: int = 0
    failed: int = 0
    blocked: int = 0
    cancelled: bool = False


class BroadcastService:
    """Sends content to every registered user with progress + cancel."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self._cancel = asyncio.Event()
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def request_cancel(self) -> None:
        """Stop the current broadcast at the next user boundary."""
        self._cancel.set()

    async def run(
        self,
        deliver,
        on_progress=None,
        progress_every: int = 10,
    ) -> BroadcastResult:
        """Deliver to every user.

        ``deliver(chat_id)`` is an async callable that sends the content;
        ``on_progress(done, total, result)`` is called periodically.
        """
        self._cancel = asyncio.Event()
        self._running = True
        result = BroadcastResult()
        try:
            user_ids = await self.db.all_user_ids()
            total = len(user_ids)

            for index, user_id in enumerate(user_ids, start=1):
                if self._cancel.is_set():
                    result.cancelled = True
                    break
                try:
                    await deliver(user_id)
                    result.sent += 1
                except TelegramBadRequest as exc:
                    message = str(exc).lower()
                    if "blocked" in message or "chat not found" in message or "bot was kicked" in message:
                        result.blocked += 1
                        await self.db.remove_user(user_id)
                    else:
                        result.failed += 1
                except TelegramAPIError:
                    result.failed += 1

                if on_progress is not None and (index % progress_every == 0 or index == total or result.cancelled):
                    await _maybe_await(on_progress(index, total, result))

            if on_progress is not None and total == 0:
                await _maybe_await(on_progress(0, 0, result))
            return result
        finally:
            self._running = False
            logger.info(
                "Broadcast finished: sent=%d failed=%d blocked=%d cancelled=%s",
                result.sent,
                result.failed,
                result.blocked,
                result.cancelled,
            )
