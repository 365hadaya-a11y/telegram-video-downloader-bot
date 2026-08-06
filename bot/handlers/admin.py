"""Admin-only commands: /stats, /setsticker, /resetsticker, /stickers, /broadcast (bilingual)."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from ..keyboards.inline import remove_keyboard
from ..services import Services
from ..services.broadcast import broadcast_cancel_keyboard
from ..services.stickers import STICKER_KEYS
from ..utils.formatters import format_size
from ..utils.i18n import normalize_lang, t

logger = logging.getLogger(__name__)

router = Router(name="admin")


def _is_admin(services: Services, user_id: int) -> bool:
    return user_id in services.settings.admin_ids


async def _admin_lang(services: Services, user_id: int) -> str:
    stored = await services.db.get_user_lang(user_id)
    return normalize_lang(stored or services.settings.default_language)


@router.message(Command("stats"))
async def on_stats(message: Message, services: Services) -> None:
    assert message.from_user is not None
    lang = await _admin_lang(services, message.from_user.id)
    if not _is_admin(services, message.from_user.id):
        await message.answer(t(lang, "admins_only"))
        return

    users = await services.db.users_count()
    total = await services.db.total_downloads()
    today = await services.db.today_downloads_all()
    active = len(services.downloader.sessions)
    queued = services.queue.waiting_count
    temp_size = format_size(services.cleanup.temp_dir_size())

    text = t(
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
    await message.answer(text)


@router.message(Command("setsticker"))
async def on_set_sticker(message: Message, command: CommandObject, services: Services) -> None:
    assert message.from_user is not None
    lang = await _admin_lang(services, message.from_user.id)
    if not _is_admin(services, message.from_user.id):
        await message.answer(t(lang, "admins_only"))
        return

    key = (command.args or "").strip().lower()
    if key not in STICKER_KEYS:
        await message.answer(t(lang, "setsticker_usage", keys=" | ".join(STICKER_KEYS)))
        return

    sticker = message.reply_to_message.sticker if message.reply_to_message else None
    if sticker is None:
        await message.answer(t(lang, "reply_sticker"))
        return

    await services.db.set_sticker(key, sticker.file_id)
    await message.answer(t(lang, "sticker_saved", key=key))


@router.message(Command("resetsticker"))
async def on_reset_sticker(message: Message, command: CommandObject, services: Services) -> None:
    assert message.from_user is not None
    lang = await _admin_lang(services, message.from_user.id)
    if not _is_admin(services, message.from_user.id):
        await message.answer(t(lang, "admins_only"))
        return

    key = (command.args or "").strip().lower()
    if key not in STICKER_KEYS:
        await message.answer(t(lang, "resetsticker_usage", keys=" | ".join(STICKER_KEYS)))
        return

    await services.db.delete_sticker(key)
    await message.answer(t(lang, "sticker_reset", key=key))


@router.message(Command("broadcast"))
async def on_broadcast(message: Message, command: CommandObject, services: Services) -> None:
    """النشرة الإعلانية — announce text or media to every registered user."""
    assert message.from_user is not None
    lang = await _admin_lang(services, message.from_user.id)
    if not _is_admin(services, message.from_user.id):
        await message.answer(t(lang, "admins_only"))
        return
    if services.broadcast.running:
        await message.answer(t(lang, "broadcast_running"))
        return

    text = (command.args or "").strip()
    reply = message.reply_to_message
    has_media = bool(
        reply
        and (
            reply.photo
            or reply.video
            or reply.document
            or reply.audio
            or reply.animation
            or reply.voice
            or reply.sticker
        )
    )
    if not text and not has_media:
        await message.answer(t(lang, "broadcast_usage"))
        return

    status_message = await message.answer(
        t(lang, "broadcasting"),
        reply_markup=broadcast_cancel_keyboard(lang),
    )
    bot = message.bot
    from_chat_id = message.chat.id
    reply_message_id = reply.message_id if has_media else None

    async def deliver(chat_id: int) -> None:
        if reply_message_id is not None:
            await bot.copy_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=reply_message_id)
        else:
            try:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
            except TelegramBadRequest as exc:
                if "parse" in str(exc).lower() or "entities" in str(exc).lower():
                    await bot.send_message(chat_id=chat_id, text=text)  # fall back to plain text
                else:
                    raise

    async def progress(done: int, total: int, result) -> None:
        caption = t(
            lang,
            "broadcast_progress",
            sent=result.sent,
            failed=result.failed,
            blocked=result.blocked,
            done=done,
            total=total,
        )
        try:
            await bot.edit_message_text(
                text=caption,
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
                reply_markup=broadcast_cancel_keyboard(lang),
            )
        except TelegramAPIError:
            pass

    try:
        result = await services.broadcast.run(deliver, on_progress=progress, progress_every=10)
    except Exception:
        logger.exception("Broadcast crashed unexpectedly")
        try:
            await bot.edit_message_text(
                text=t(lang, "broadcast_crashed"),
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
                reply_markup=remove_keyboard(),
            )
        except TelegramAPIError:
            pass
        return

    if result.cancelled:
        final = t(lang, "broadcast_stopped")
    else:
        final = t(lang, "broadcast_finished")
    final += t(
        lang,
        "broadcast_summary",
        sent=result.sent,
        failed=result.failed,
        blocked=result.blocked,
    )
    try:
        await bot.edit_message_text(
            text=final,
            chat_id=status_message.chat.id,
            message_id=status_message.message_id,
            reply_markup=remove_keyboard(),
        )
    except TelegramAPIError:
        await message.answer(final)


@router.message(Command("setchannel"))
async def on_set_channel(message: Message, command: CommandObject, services: Services) -> None:
    """Add a forced-subscription channel at runtime (admin panel / /setchannel)."""
    assert message.from_user is not None
    lang = await _admin_lang(services, message.from_user.id)
    if not _is_admin(services, message.from_user.id):
        await message.answer(t(lang, "admins_only"))
        return

    ref = (command.args or "").strip()
    if not ref:
        await message.answer(t(lang, "setchannel_usage"))
        return
    if ref in services.subscription.channels:
        await message.answer(t(lang, "setchannel_dup", channel=ref))
        return
    await services.subscription.add_channel(ref, message.from_user.id)
    await message.answer(t(lang, "setchannel_added", channel=ref))


@router.message(Command("delchannel"))
async def on_del_channel(message: Message, command: CommandObject, services: Services) -> None:
    """Remove a forced-subscription channel (runtime only; env channels stay)."""
    assert message.from_user is not None
    lang = await _admin_lang(services, message.from_user.id)
    if not _is_admin(services, message.from_user.id):
        await message.answer(t(lang, "admins_only"))
        return

    ref = (command.args or "").strip()
    if not ref:
        await message.answer(t(lang, "setchannel_usage"))
        return
    if ref in services.subscription.env_channels:
        await message.answer(t(lang, "delchannel_env_protected", channel=ref))
        return
    removed = await services.subscription.remove_channel(ref)
    key = "delchannel_removed" if removed else "delchannel_missing"
    await message.answer(t(lang, key, channel=ref))


@router.message(Command("stickers"))
async def on_list_stickers(message: Message, services: Services) -> None:
    assert message.from_user is not None
    lang = await _admin_lang(services, message.from_user.id)
    if not _is_admin(services, message.from_user.id):
        await message.answer(t(lang, "admins_only"))
        return

    mapping = await services.db.list_stickers()
    if not mapping:
        await message.answer(t(lang, "no_stickers", keys=" ".join(STICKER_KEYS)))
        return

    lines = [t(lang, "sticker_mapping")]
    for key in STICKER_KEYS:
        status = t(lang, "sticker_set") if key in mapping else t(lang, "sticker_not_set")
        lines.append(f"• <b>{key}</b>: {status}")
    await message.answer("\n".join(lines))
