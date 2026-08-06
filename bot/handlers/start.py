"""/start, /help, /cancel and /language command handlers (bilingual)."""

from __future__ import annotations

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from ..keyboards.inline import (
    DownloadCB,
    LanguageCB,
    language_keyboard,
    remove_keyboard,
    welcome_help_keyboard,
    welcome_keyboard,
)
from ..services import Services
from ..utils.i18n import lang_name, normalize_lang, t, web_mention

logger = logging.getLogger(__name__)

router = Router(name="start")


def _welcome_text(lang: str, first_name: str | None, web_base: str | None) -> str:
    name = html.escape(first_name or ("صديقي" if lang == "ar" else "friend"))
    return t(lang, "welcome", name=name, lang_name=lang_name(lang), web=web_mention(lang, web_base or ""))


def _help_text(lang: str) -> str:
    return t(lang, "help")


async def _user_lang(services: Services, user_id: int) -> str:
    """Resolve the user's stored language (falling back to the default)."""
    stored = await services.db.get_user_lang(user_id)
    return normalize_lang(stored or services.settings.default_language)


@router.message(CommandStart())
async def on_start(message: Message, services: Services) -> None:
    user = message.from_user
    assert user is not None
    await services.db.upsert_user(user.id, user.username, user.first_name, user.last_name)
    lang = await _user_lang(services, user.id)

    # Forced channel subscription gate (الاشتراك الإجباري)
    if not await services.subscription.require_membership(message.bot, user.id, services.settings.admin_ids):
        await message.answer(
            services.subscription.join_message(lang),
            reply_markup=services.subscription.join_keyboard(lang),
        )
        return

    await services.stickers.send(message, message.bot, "welcome")
    await message.answer(
        _welcome_text(lang, user.first_name, services.settings.web_base),
        reply_markup=welcome_keyboard(lang),
    )


@router.message(Command("help"))
async def on_help(message: Message, services: Services) -> None:
    assert message.from_user is not None
    lang = await _user_lang(services, message.from_user.id)
    await message.answer(_help_text(lang), reply_markup=welcome_help_keyboard(lang))


@router.message(Command("cancel"))
async def on_cancel(message: Message, services: Services) -> None:
    user = message.from_user
    assert user is not None
    lang = await _user_lang(services, user.id)
    cancelled = await services.downloader.cancel(user.id)
    if cancelled:
        await message.answer(t(lang, "cancel_started"))
    else:
        await message.answer(t(lang, "cancel_nothing"))


@router.message(Command("language"))
async def on_language(message: Message, services: Services) -> None:
    assert message.from_user is not None
    lang = await _user_lang(services, message.from_user.id)
    await message.answer(t(lang, "language_prompt"), reply_markup=language_keyboard(lang))


@router.callback_query(LanguageCB.filter())
async def on_language_pick(callback: CallbackQuery, callback_data: LanguageCB, services: Services) -> None:
    user = callback.from_user
    new_lang = normalize_lang(callback_data.lang)
    await services.db.set_user_lang(user.id, new_lang)
    # If this user has an active download session, update its language too.
    session = services.downloader.sessions.get(user.id)
    if session is not None:
        session.lang = new_lang
    try:
        await callback.message.edit_text(
            t(new_lang, "language_changed"),
            reply_markup=language_keyboard(new_lang),
        )
    except Exception:  # noqa: BLE001
        logger.debug("Could not edit language card", exc_info=True)
    await callback.answer()
