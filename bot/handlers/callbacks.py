"""Inline callback handlers: download flow, join-verification, broadcast control (bilingual)."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery

from ..keyboards.inline import DownloadCB, remove_keyboard
from ..services import Services
from ..services.broadcast import BroadcastCB
from ..services.subscription import JoinCB
from ..utils.i18n import normalize_lang, t

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


async def _user_lang(services: Services, user_id: int) -> str:
    stored = await services.db.get_user_lang(user_id)
    return normalize_lang(stored or services.settings.default_language)


@router.callback_query(DownloadCB.filter())
async def on_download_callback(
    callback: CallbackQuery,
    callback_data: DownloadCB,
    services: Services,
) -> None:
    user_id = callback.from_user.id
    session = services.downloader.sessions.get(user_id)

    if session is None:
        lang = await _user_lang(services, user_id)
        await callback.answer(t(lang, "session_expired"), show_alert=False)
        return

    if callback_data.action == "cancel":
        session.cancel_event.set()
        await callback.answer(t(session.lang, "cancelling"))
    else:
        await callback.answer("✅")

    session.resolve(f"{callback_data.action}:{callback_data.value}" if callback_data.value else callback_data.action)


@router.callback_query(JoinCB.filter())
async def on_join_check(callback: CallbackQuery, services: Services) -> None:
    """Re-check channel membership after the user presses the join button."""
    user = callback.from_user
    lang = await _user_lang(services, user.id)
    if await services.subscription.is_member(callback.bot, user.id):
        try:
            await callback.message.edit_text(
                t(lang, "access_granted"),
                reply_markup=remove_keyboard(),
            )
        except TelegramAPIError:
            logger.debug("Could not edit join card", exc_info=True)
        await callback.answer(t(lang, "join_welcome"))
    else:
        await callback.answer(t(lang, "not_joined"), show_alert=True)


@router.callback_query(BroadcastCB.filter())
async def on_broadcast_control(callback: CallbackQuery, callback_data: BroadcastCB, services: Services) -> None:
    if callback.from_user.id not in services.settings.admin_ids:
        lang = await _user_lang(services, callback.from_user.id)
        await callback.answer(t(lang, "admins_only"), show_alert=True)
        return
    if callback_data.action == "cancel":
        services.broadcast.request_cancel()
        lang = await _user_lang(services, callback.from_user.id)
        await callback.answer(t(lang, "broadcast_stop_btn"))
