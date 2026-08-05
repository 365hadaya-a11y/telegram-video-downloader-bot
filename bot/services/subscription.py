"""Forced channel subscription gate (الاشتراك الإجباري).

When a ``FORCE_CHANNEL`` is configured, users must be a member of that
channel before the bot will download anything for them. Admins are exempt.
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

_MEMBER_STATUSES = (
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
    ChatMemberStatus.RESTRICTED,
)


class JoinCB(CallbackData, prefix="join"):
    """Callback for the \"✅ I've Joined\" button."""

    action: str = "check"


class ForcedSubscription:
    """Checks membership and builds the \"join the channel\" card."""

    def __init__(self, channel: str | None) -> None:
        self.channel = (channel or "").strip() or None
        self._invalid_warned = False

    @property
    def enabled(self) -> bool:
        return self.channel is not None

    @property
    def channel_ref(self) -> str:
        return self.channel or ""

    def join_keyboard(self) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        if self.channel:
            url = f"https://t.me/{self.channel.lstrip('@').split('?')[0]}"
            if not self.channel.lstrip("-").isdigit():  # only @usernames get a link
                rows.append([InlineKeyboardButton(text="🔗 Join Channel", url=url)])
        rows.append([InlineKeyboardButton(text="✅ I've Joined", callback_data=JoinCB().pack())])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def join_message(self) -> str:
        return (
            "🔒 <b>Channel subscription required</b>\n\n"
            f"To use the bot, please join our channel first:\n"
            f"👉 <b>{self.channel_ref}</b>\n\n"
            "Then press the button below to verify. ✅"
        )

    async def require_membership(self, bot: Bot, user_id: int, admin_ids: list[int]) -> bool:
        """Admins are always allowed; everyone else must have joined the channel."""
        if user_id in admin_ids:
            return True
        return await self.is_member(bot, user_id)

    async def is_member(self, bot: Bot, user_id: int) -> bool:
        """True when the gate is disabled or the user has joined the channel."""
        if not self.enabled:
            return True
        try:
            member = await bot.get_chat_member(chat_id=self.channel, user_id=user_id)  # type: ignore[arg-type]
            return member.status in _MEMBER_STATUSES
        except TelegramBadRequest as exc:
            # The configured channel itself is missing/invalid — never brick
            # the whole bot because of a typo in FORCE_CHANNEL.
            if not self._invalid_warned:
                logger.warning("Force channel %r unavailable (%s) — skipping checks", self.channel, exc)
                self._invalid_warned = True
            return True
        except TelegramAPIError:
            return False
