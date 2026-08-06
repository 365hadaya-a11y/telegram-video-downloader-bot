"""لوحة تحكم المدير — interactive admin control panel.

One editable message with an inline keyboard. The owner navigates between
sections (stats / users / broadcast / stickers / channels / settings /
language) using :class:`PanelCB` callbacks — every section re-renders the
same message, keeping the chat clean.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ..keyboards.inline import (
    PanelCB,
    admin_panel_keyboard,
    panel_broadcast_keyboard,
    panel_channels_keyboard,
    panel_language_keyboard,
    panel_settings_keyboard,
    panel_stats_keyboard,
    panel_stickers_keyboard,
    panel_users_keyboard,
    remove_keyboard,
)
from ..services import Services
from ..utils.formatters import format_size
from ..utils.i18n import lang_name, normalize_lang, t

logger = logging.getLogger(__name__)

router = Router(name="panel")


async def _admin_lang(services: Services, user_id: int) -> str:
    stored = await services.db.get_user_lang(user_id)
    return normalize_lang(stored or services.settings.default_language)


def _is_owner(services: Services, user_id: int) -> bool:
    return user_id in services.settings.admin_ids


@router.message(Command("panel"))
async def on_panel(message: Message, services: Services) -> None:
    assert message.from_user is not None
    lang = await _admin_lang(services, message.from_user.id)
    if not _is_owner(services, message.from_user.id):
        await message.answer(t(lang, "panel_admins_only"))
        return
    await message.answer(t(lang, "panel_title"), reply_markup=admin_panel_keyboard(lang))


# ── section builders ─────────────────────────────────────────────────────────

async def _stats_text(services: Services, lang: str) -> str:
    users = await services.db.users_count()
    total = await services.db.total_downloads()
    today = await services.db.today_downloads_all()
    active = len(services.downloader.sessions)
    queued = services.queue.waiting_count
    temp_size = format_size(services.cleanup.temp_dir_size())
    return t(
        lang,
        "stats",
        users=users,
        total=total,
        today=today,
        active=active,
        queued=queued,
        temp_size=temp_size,
        workers=services.settings.download_workers,
        limit=services.settings.daily_download_limit,
    )


async def _users_text(services: Services, lang: str) -> str:
    total = await services.db.users_count()
    top = await services.db.top_users(limit=5)
    if not top:
        return t(lang, "panel_users_empty", total=total)
    lines = [t(lang, "panel_users_title", total=total)]
    for rank, (uid, username, count) in enumerate(top, start=1):
        name = f"@{username}" if username else f"ID {uid}"
        lines.append(f"{rank}. {name} — <b>{count}</b> 📥")
    return "\n".join(lines)


def _channels_text(services: Services, lang: str) -> str:
    channels = services.subscription.channels
    if not channels:
        return t(lang, "panel_channels_empty")
    lines: list[str] = []
    for ref in channels:
        note = t(lang, "channel_env_note") if ref in services.subscription._env_channels else ""
        lines.append(f"🔒 <b>{ref}</b> {note}")
    return t(lang, "panel_channels_title", channels="\n".join(lines))


def _settings_text(services: Services, lang: str) -> str:
    s = services.settings
    lines = "\n".join(
        [
            f"🌐 اللغة الافتراضية: <b>{lang_name(s.default_language)}</b>" if lang == "ar"
            else f"🌐 Default language: <b>{lang_name(s.default_language)}</b>",
            f"👥 Admins: <b>{', '.join(str(a) for a in s.admin_ids) or '—'}</b>",
            f"🧵 Workers: <b>{s.download_workers}</b>",
            f"📦 Max size: <b>{s.max_file_size_mb} MB</b>",
            f"🚦 Daily limit: <b>{s.daily_download_limit}</b>",
            f"🔁 Retries: <b>{s.retry_attempts}</b>",
            f"🔒 Webhook: <b>{'ON' if s.webhook_mode else 'OFF'}</b>",
        ]
    )
    return t(lang, "panel_settings_title", lines=lines)


async def _stickers_text(services: Services, lang: str) -> str:
    mapping = await services.db.list_stickers()
    from ..services.stickers import STICKER_KEYS

    lines: list[str] = []
    for key in STICKER_KEYS:
        status = t(lang, "sticker_set") if key in mapping else t(lang, "sticker_not_set")
        lines.append(f"• <b>{key}</b>: {status}")
    return t(lang, "panel_stickers_title", lines="\n".join(lines))


# ── render one panel message ─────────────────────────────────────────────────

async def _render(
    callback: CallbackQuery,
    services: Services,
    view: str,
    *,
    lang: str,
) -> None:
    """Re-render the panel message for ``view``."""
    keyboards = {
        "stats": (await _stats_text(services, lang), panel_stats_keyboard(lang)),
        "users": (await _users_text(services, lang), panel_users_keyboard(lang)),
        "broadcast": (t(lang, "panel_broadcast_title"), panel_broadcast_keyboard(lang)),
        "stickers": (await _stickers_text(services, lang), panel_stickers_keyboard(lang)),
        "channels": (_channels_text(services, lang), panel_channels_keyboard(services.subscription.channels, lang)),
        "settings": (_settings_text(services, lang), panel_settings_keyboard(lang)),
        "language": (t(lang, "language_prompt"), panel_language_keyboard(lang)),
    }
    if view == "main":
        text, keyboard = t(lang, "panel_title"), admin_panel_keyboard(lang)
    else:
        text, keyboard = keyboards.get(view, (t(lang, "panel_title"), admin_panel_keyboard(lang)))
    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except TelegramAPIError:
        logger.debug("Panel edit failed (view=%s)", view, exc_info=True)


@router.callback_query(PanelCB.filter())
async def on_panel_callback(callback: CallbackQuery, callback_data: PanelCB, services: Services) -> None:
    user_id = callback.from_user.id
    if not _is_owner(services, user_id):
        lang = await _admin_lang(services, user_id)
        await callback.answer(t(lang, "panel_admins_only"), show_alert=True)
        return

    lang = await _admin_lang(services, user_id)

    # Actions that don't navigate
    if callback_data.action == "close":
        try:
            await callback.message.edit_text(t(lang, "panel_closed"), reply_markup=remove_keyboard())
        except TelegramAPIError:
            pass
        await callback.answer()
        return

    if callback_data.action == "setlang":
        new_lang = normalize_lang(callback_data.value)
        await services.db.set_user_lang(user_id, new_lang)
        lang = new_lang
        try:
            await callback.message.edit_text(
                t(new_lang, "language_changed"),
                reply_markup=panel_language_keyboard(new_lang),
            )
        except TelegramAPIError:
            pass
        await callback.answer()
        return

    if callback_data.action == "addchan":
        await callback.answer(t(lang, "setchannel_usage"), show_alert=True)
        return

    if callback_data.action == "delchan" and callback_data.value:
        removed = await services.subscription.remove_channel(callback_data.value)
        text = t(lang, "delchannel_removed" if removed else "delchannel_missing", channel=callback_data.value)
        try:
            await callback.message.edit_text(
                text + "\n\n" + _channels_text(services, lang),
                reply_markup=panel_channels_keyboard(services.subscription.channels, lang),
            )
        except TelegramAPIError:
            pass
        await callback.answer()
        return

    # refresh / back / open — just render the target view
    await _render(callback, services, callback_data.view, lang=lang)
    await callback.answer()
