"""Forced channel subscription gate (الاشتراك الإجباري) — multi-channel.

Users must be a member of EVERY configured channel before the bot will
download anything for them. Admins are exempt.

Channels come from two sources, combined:
- environment: ``FORCE_CHANNEL`` (legacy) / ``FORCE_CHANNELS``
- runtime: added by the owner with ``/setchannel`` (stored in SQLite,
  removable with ``/delchannel`` or from the admin panel)
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..database.db import Database
from ..utils.i18n import LANG_AR, t

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


def _t_me_url(ref: str) -> str | None:
    """A t.me join URL for @usernames; None for numeric channel ids."""
    cleaned = ref.strip().lstrip("@").split("?")[0]
    if cleaned.lstrip("-").isdigit():
        return None
    return f"https://t.me/{cleaned}"


class ForcedSubscription:
    """Checks membership across all channels and builds the join card."""

    def __init__(self, db: Database, env_channels: list[str] | None = None) -> None:
        self.db = db
        self._env_channels = [c.strip() for c in (env_channels or []) if c and c.strip()]
        self._invalid_warned: set[str] = set()
        self._runtime: list[str] = []

    # ── channel list ──────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return len(self.channels) > 0

    @property
    def env_channels(self) -> list[str]:
        """Channels configured via environment (protected from removal)."""
        return list(self._env_channels)

    @property
    def channels(self) -> list[str]:
        """Env channels + runtime channels, deduplicated, order preserved."""
        seen: set[str] = set()
        result: list[str] = []
        for ref in [*self._env_channels, *self._runtime_channels()]:
            if ref not in seen:
                seen.add(ref)
                result.append(ref)
        return result

    def _runtime_channels(self) -> list[str]:
        return self._runtime

    async def refresh_runtime(self) -> None:
        """Load runtime channels from the DB (called once at startup)."""
        try:
            self._runtime = await self.db.list_channels()
        except Exception:  # noqa: BLE001
            logger.exception("Could not load runtime channels")

    async def add_channel(self, ref: str, added_by: int) -> bool:
        """Register a runtime channel. Returns False if already active (env or db)."""
        ref = ref.strip()
        if not ref:
            return False
        if ref in self.channels:
            return False
        await self.db.add_channel(ref, added_by)
        if ref not in self._runtime:
            self._runtime.append(ref)
        return True

    async def remove_channel(self, ref: str) -> bool:
        """Remove a runtime channel (env channels are never removable)."""
        ref = ref.strip()
        if ref in self._env_channels:
            return False
        removed = await self.db.remove_channel(ref)
        if removed and ref in self._runtime:
            self._runtime.remove(ref)
        return removed

    def channel_refs_text(self) -> str:
        return " · ".join(self.channels) or "—"

    # ── join card ─────────────────────────────────────────────────

    def join_keyboard(self, lang: str = LANG_AR) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        for ref in self.channels:
            url = _t_me_url(ref)
            if url:
                rows.append([InlineKeyboardButton(text=t(lang, "join_channel_btn", channel=ref), url=url)])
            else:
                rows.append([InlineKeyboardButton(text=f"🔒 {ref}", callback_data=JoinCB().pack())])
        rows.append([InlineKeyboardButton(text=t(lang, "joined_btn"), callback_data=JoinCB().pack())])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def join_message(self, lang: str = LANG_AR) -> str:
        lines = [t(lang, "join_message_title")]
        for i, ref in enumerate(self.channels, start=1):
            url = _t_me_url(ref)
            if url:
                lines.append(f"{i}. <a href=\"{url}\">{ref}</a>")
            else:
                lines.append(f"{i}. {ref}")
        lines.append("")
        lines.append(t(lang, "join_message_footer"))
        return "\n".join(lines)

    # ── membership checks ─────────────────────────────────────────

    async def require_membership(self, bot: Bot, user_id: int, admin_ids: list[int]) -> bool:
        """Admins are always allowed; everyone else must have joined every channel."""
        if user_id in admin_ids:
            return True
        return await self.is_member(bot, user_id)

    async def is_member(self, bot: Bot, user_id: int) -> bool:
        """True when the gate is disabled or the user has joined every channel."""
        if not self.enabled:
            return True
        for ref in self.channels:
            if not await self._check_one(bot, ref, user_id):
                return False
        return True

    async def missing_channels(self, bot: Bot, user_id: int) -> list[str]:
        """Channels the user still needs to join (for the \"I've joined\" re-check)."""
        if not self.enabled:
            return []
        missing: list[str] = []
        for ref in self.channels:
            if not await self._check_one(bot, ref, user_id):
                missing.append(ref)
        return missing

    async def _check_one(self, bot: Bot, ref: str, user_id: int) -> bool:
        try:
            member = await bot.get_chat_member(chat_id=ref, user_id=user_id)  # type: ignore[arg-type]
            return member.status in _MEMBER_STATUSES
        except TelegramBadRequest as exc:
            # The configured channel itself is missing/invalid — never brick
            # the whole bot because of a typo in FORCE_CHANNEL(S).
            if ref not in self._invalid_warned:
                logger.warning("Force channel %r unavailable (%s) — skipping it", ref, exc)
                self._invalid_warned.add(ref)
            return True
        except TelegramAPIError:
            return False
