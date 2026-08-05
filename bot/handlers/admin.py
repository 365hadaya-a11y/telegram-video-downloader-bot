"""Admin-only commands: /stats, /setsticker, /resetsticker, /stickers."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from ..services import Services
from ..services.broadcast import broadcast_cancel_keyboard
from ..services.stickers import STICKER_KEYS
from ..utils.formatters import format_size
from ..keyboards.inline import remove_keyboard

logger = logging.getLogger(__name__)

router = Router(name="admin")


def _is_admin(services: Services, user_id: int) -> bool:
    return user_id in services.settings.admin_ids


def _denied() -> str:
    return "⛔ <b>Admins only.</b>\nThis command is restricted to the bot owner."


@router.message(Command("stats"))
async def on_stats(message: Message, services: Services) -> None:
    assert message.from_user is not None
    if not _is_admin(services, message.from_user.id):
        await message.answer(_denied())
        return

    users = await services.db.users_count()
    total = await services.db.total_downloads()
    today = await services.db.today_downloads_all()
    active = len(services.downloader.sessions)
    queued = services.queue.waiting_count
    temp_size = format_size(services.cleanup.temp_dir_size())

    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 Users: <b>{users}</b>\n"
        f"✅ Total downloads: <b>{total}</b>\n"
        f"📅 Downloads today: <b>{today}</b>\n"
        f"⚙️ Active sessions: <b>{active}</b>\n"
        f"⏳ Queued downloads: <b>{queued}</b>\n"
        f"🗑️ Temp usage: <b>{temp_size}</b>\n\n"
        f"🧵 Workers: <b>{services.settings.download_workers}</b>\n"
        f"🚦 Daily limit/user: <b>{services.settings.daily_download_limit}</b>"
    )
    await message.answer(text)


@router.message(Command("setsticker"))
async def on_set_sticker(message: Message, command: CommandObject, services: Services) -> None:
    assert message.from_user is not None
    if not _is_admin(services, message.from_user.id):
        await message.answer(_denied())
        return

    key = (command.args or "").strip().lower()
    if key not in STICKER_KEYS:
        await message.answer(
            "🎨 <b>Usage:</b> reply to a sticker with\n"
            f"<code>/setsticker {' | '.join(STICKER_KEYS)}</code>\n\n"
            "Example:\n<code>/setsticker welcome</code>"
        )
        return

    sticker = message.reply_to_message.sticker if message.reply_to_message else None
    if sticker is None:
        await message.answer("ℹ️ <b>Reply to a sticker</b> with this command to save it.")
        return

    await services.db.set_sticker(key, sticker.file_id)
    await message.answer(f"✅ Sticker <b>{key}</b> saved! It will be used from now on. ✨")


@router.message(Command("resetsticker"))
async def on_reset_sticker(message: Message, command: CommandObject, services: Services) -> None:
    assert message.from_user is not None
    if not _is_admin(services, message.from_user.id):
        await message.answer(_denied())
        return

    key = (command.args or "").strip().lower()
    if key not in STICKER_KEYS:
        await message.answer(f"🎨 Usage: <code>/resetsticker {' | '.join(STICKER_KEYS)}</code>")
        return

    await services.db.delete_sticker(key)
    await message.answer(f"🗑️ Sticker <b>{key}</b> reset to default behaviour.")


@router.message(Command("broadcast"))
async def on_broadcast(message: Message, command: CommandObject, services: Services) -> None:
    """النشرة الإعلانية — announce text or media to every registered user."""
    assert message.from_user is not None
    if not _is_admin(services, message.from_user.id):
        await message.answer(_denied())
        return
    if services.broadcast.running:
        await message.answer("📣 A broadcast is already running. Wait for it to finish or press 🛑 Stop.")
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
        await message.answer(
            "📣 <b>Usage:</b>\n"
            "<code>/broadcast &lt;text&gt;</code> — announce a text message\n"
            "<code>/broadcast</code> <i>(reply to a photo/video/file)</i> — announce media\n\n"
            "It will be sent to <b>every user</b> who started the bot."
        )
        return

    status_message = await message.answer(
        "📣 <b>Broadcasting…</b>\n\n⏳ Preparing…",
        reply_markup=broadcast_cancel_keyboard(),
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
        caption = (
            "📣 <b>Broadcasting…</b>\n\n"
            f"✅ Sent: <b>{result.sent}</b>\n"
            f"❌ Failed: <b>{result.failed}</b>\n"
            f"🚫 Blocked: <b>{result.blocked}</b>\n\n"
            f"⏳ {done}/{total}"
        )
        try:
            await bot.edit_message_text(
                text=caption,
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
                reply_markup=broadcast_cancel_keyboard(),
            )
        except TelegramAPIError:
            pass

    try:
        result = await services.broadcast.run(deliver, on_progress=progress, progress_every=10)
    except Exception:
        logger.exception("Broadcast crashed unexpectedly")
        try:
            await bot.edit_message_text(
                text="⚠️ <b>Broadcast crashed.</b>\nAn unexpected error interrupted the announcement.",
                chat_id=status_message.chat.id,
                message_id=status_message.message_id,
                reply_markup=remove_keyboard(),
            )
        except TelegramAPIError:
            pass
        return

    if result.cancelled:
        final = "🛑 <b>Broadcast stopped.</b>\n\n"
    else:
        final = "✅ <b>Broadcast finished!</b>\n\n"
    final += (
        f"📨 Sent: <b>{result.sent}</b>\n"
        f"❌ Failed: <b>{result.failed}</b>\n"
        f"🚫 Blocked & removed: <b>{result.blocked}</b>"
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


@router.message(Command("stickers"))
async def on_list_stickers(message: Message, services: Services) -> None:
    assert message.from_user is not None
    if not _is_admin(services, message.from_user.id):
        await message.answer(_denied())
        return

    mapping = await services.db.list_stickers()
    if not mapping:
        await message.answer(
            "🎨 <b>No stickers configured yet.</b>\n"
            "Reply to a sticker with <code>/setsticker &lt;key&gt;</code> to assign one.\n\n"
            f"Available keys: <code>{' '.join(STICKER_KEYS)}</code>"
        )
        return

    lines = ["🎨 <b>Sticker mapping</b>\n"]
    for key in STICKER_KEYS:
        lines.append(f"• <b>{key}</b>: {'✅ set' if key in mapping else '— not set'}")
    await message.answer("\n".join(lines))
