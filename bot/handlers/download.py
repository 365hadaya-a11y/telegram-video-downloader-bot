"""Handlers for plain text messages: URL detection, hints, unknown commands (bilingual)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from ..services import Services
from ..utils.formatters import extract_url
from ..utils.i18n import normalize_lang, t

router = Router(name="download")


async def _user_lang(services: Services, user_id: int) -> str:
    stored = await services.db.get_user_lang(user_id)
    return normalize_lang(stored or services.settings.default_language)


@router.message(F.text, F.chat.type == ChatType.PRIVATE, ~F.text.startswith("/"))
async def on_private_text(message: Message, services: Services) -> None:
    url = extract_url(message.text or "")
    assert message.from_user is not None
    lang = await _user_lang(services, message.from_user.id)

    if not url:
        await message.answer(t(lang, "no_url"))
        return

    # Forced channel subscription gate (الاشتراك الإجباري)
    if not await services.subscription.require_membership(
        message.bot, message.from_user.id, services.settings.admin_ids
    ):
        await message.answer(
            services.subscription.join_message(lang),
            reply_markup=services.subscription.join_keyboard(lang),
        )
        return

    await services.downloader.handle_url(message, url, lang)


@router.message(F.text.startswith("/"))
async def on_unknown_command(message: Message, services: Services) -> None:
    assert message.from_user is not None
    lang = await _user_lang(services, message.from_user.id)
    await message.answer(t(lang, "unknown_command"))


@router.message(F.text, F.chat.type != ChatType.PRIVATE)
async def on_group_text(message: Message, services: Services) -> None:
    assert message.from_user is not None
    lang = await _user_lang(services, message.from_user.id)
    await message.answer(t(lang, "group_only"))
