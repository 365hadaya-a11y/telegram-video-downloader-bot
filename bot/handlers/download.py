"""Handlers for plain text messages: URL detection, hints, unknown commands."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from ..services import Services
from ..utils.formatters import extract_url

router = Router(name="download")


@router.message(F.text, F.chat.type == ChatType.PRIVATE, ~F.text.startswith("/"))
async def on_private_text(message: Message, services: Services) -> None:
    url = extract_url(message.text or "")
    if not url:
        await message.answer(
            "🤔 <b>I couldn't find a video link</b> in your message.\n\n"
            "🔗 Send me a valid URL, e.g.\n"
            "<code>https://youtube.com/watch?v=…</code>\n\n"
            "💡 Use /help if you need a hand."
        )
        return

    # Forced channel subscription gate (الاشتراك الإجباري)
    assert message.from_user is not None
    if not await services.subscription.require_membership(
        message.bot, message.from_user.id, services.settings.admin_ids
    ):
        await message.answer(
            services.subscription.join_message(),
            reply_markup=services.subscription.join_keyboard(),
        )
        return

    await services.downloader.handle_url(message, url)


@router.message(F.text.startswith("/"))
async def on_unknown_command(message: Message) -> None:
    await message.answer("❓ <b>Unknown command.</b>\nUse /help to see what I can do.")


@router.message(F.text, F.chat.type != ChatType.PRIVATE)
async def on_group_text(message: Message) -> None:
    await message.answer("🔒 <b>Please use me in a private chat</b> to download videos. 😊")
