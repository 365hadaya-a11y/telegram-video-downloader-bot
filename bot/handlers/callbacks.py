"""Inline callback handlers: download flow, join-verification, broadcast control."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery

from ..keyboards.inline import DownloadCB, remove_keyboard
from ..services import Services
from ..services.broadcast import BroadcastCB
from ..services.subscription import JoinCB

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


@router.callback_query(DownloadCB.filter())
async def on_download_callback(
    callback: CallbackQuery,
    callback_data: DownloadCB,
    services: Services,
) -> None:
    user_id = callback.from_user.id
    session = services.downloader.sessions.get(user_id)

    if session is None:
        await callback.answer("⏳ This session has expired — send a new link!", show_alert=False)
        return

    if callback_data.action == "cancel":
        session.cancel_event.set()
        await callback.answer("🚫 Cancelling…")
    else:
        await callback.answer("✅")

    session.resolve(f"{callback_data.action}:{callback_data.value}" if callback_data.value else callback_data.action)


@router.callback_query(JoinCB.filter())
async def on_join_check(callback: CallbackQuery, services: Services) -> None:
    """Re-check channel membership after the user presses \"✅ I've Joined\"."""
    user = callback.from_user
    if await services.subscription.is_member(callback.bot, user.id):
        try:
            await callback.message.edit_text(
                "✅ <b>Access granted!</b>\n\n"
                "You're a member of the channel now. 🎉\n"
                "Send me your video link and let's go! 🎬",
                reply_markup=remove_keyboard(),
            )
        except TelegramAPIError:
            logger.debug("Could not edit join card", exc_info=True)
        await callback.answer("🎉 Welcome!")
    else:
        await callback.answer("❌ Not yet — please join the channel first!", show_alert=True)


@router.callback_query(BroadcastCB.filter())
async def on_broadcast_control(callback: CallbackQuery, callback_data: BroadcastCB, services: Services) -> None:
    if callback.from_user.id not in services.settings.admin_ids:
        await callback.answer("⛔ Admins only.", show_alert=True)
        return
    if callback_data.action == "cancel":
        services.broadcast.request_cancel()
        await callback.answer("🛑 Stopping broadcast…")
