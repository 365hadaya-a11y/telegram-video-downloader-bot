"""/start, /help and /cancel command handlers."""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from ..services import Services

router = Router(name="start")


def _welcome_text(first_name: str | None) -> str:
    name = html.escape(first_name or "friend")
    return (
        "✨ <b>Premium Video Downloader</b> ✨\n\n"
        f"👋 Welcome, <b>{name}</b>!\n\n"
        "🎬 I can download videos from <b>1000+ websites</b>:\n"
        "• YouTube ▶️\n"
        "• TikTok 🎵\n"
        "• Instagram 📸\n"
        "• X / Twitter 🐦\n"
        "• …and many more 🌐\n\n"
        "⚡ <b>Just send me any video link</b> and I'll handle the rest!\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>Features</b>\n"
        "📥 Best-quality downloads\n"
        "📺 Manual quality selection\n"
        "🎧 Audio extraction (MP3)\n"
        "📊 Real-time progress bar\n\n"
        "🚀 <i>Powered by yt-dlp + FFmpeg</i>"
    )


def _help_text() -> str:
    return (
        "❓ <b>How to use</b>\n\n"
        "1️⃣ Send me a video URL\n"
        "2️⃣ Pick a quality option\n"
        "3️⃣ Enjoy your file! 🎉\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<b>Commands</b>\n"
        "/start — Start the bot\n"
        "/help — Show this help\n"
        "/cancel — Cancel the current download\n\n"
        "💡 <i>Tip: you can cancel anytime with the ❌ button.</i>"
    )


@router.message(CommandStart())
async def on_start(message: Message, services: Services) -> None:
    user = message.from_user
    assert user is not None
    await services.db.upsert_user(user.id, user.username, user.first_name, user.last_name)

    # Forced channel subscription gate (الاشتراك الإجباري)
    if not await services.subscription.require_membership(message.bot, user.id, services.settings.admin_ids):
        await message.answer(
            services.subscription.join_message(),
            reply_markup=services.subscription.join_keyboard(),
        )
        return

    await services.stickers.send(message, message.bot, "welcome")
    await message.answer(_welcome_text(user.first_name))


@router.message(Command("help"))
async def on_help(message: Message) -> None:
    await message.answer(_help_text())


@router.message(Command("cancel"))
async def on_cancel(message: Message, services: Services) -> None:
    user = message.from_user
    assert user is not None
    cancelled = await services.downloader.cancel(user.id)
    if cancelled:
        await message.answer("🚫 <b>Cancelling your download…</b>")
    else:
        await message.answer("😊 <b>Nothing to cancel</b> — you have no active downloads.")
