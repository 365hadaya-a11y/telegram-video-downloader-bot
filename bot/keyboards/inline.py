"""Inline keyboards and callback data for the download flow."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..utils.i18n import LANG_AR, LANG_EN, LANG_LABELS, t


class DownloadCB(CallbackData, prefix="dl"):
    """Callback payload.

    Actions: ``best``, ``choose``, ``audio``, ``cancel``, ``quality``,
    ``page``, ``main``.
    """

    action: str
    value: str = ""


class LanguageCB(CallbackData, prefix="lang"):
    """Callback for the language picker buttons."""

    lang: str


def _btn(text: str, action: str, value: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=DownloadCB(action=action, value=value).pack())


def language_keyboard(current_lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Bilingual picker; the active language gets a ✓ marker."""
    rows = []
    for lang in (LANG_AR, LANG_EN):
        label = LANG_LABELS[lang]
        if lang == current_lang:
            label = f"✓ {label}"
        rows.append([InlineKeyboardButton(text=label, callback_data=LanguageCB(lang=lang).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def info_keyboard(has_qualities: bool = True, lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Main action keyboard shown on the info card."""
    rows = [[_btn(t(lang, "btn_best"), "best")]]
    rows.append(
        [_btn(t(lang, "btn_choose"), "choose"), _btn(t(lang, "btn_audio"), "audio")]
        if has_qualities
        else [_btn(t(lang, "btn_audio"), "audio")]
    )
    rows.append([_btn(t(lang, "btn_cancel"), "cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quality_keyboard(
    heights: list[int],
    page: int,
    num_pages: int,
    size_map: dict[int, str],
    lang: str = LANG_AR,
) -> InlineKeyboardMarkup:
    """Paged resolution picker."""
    rows = [[_btn(f"📺 {h}p · {size_map.get(h, '?')}", "quality", str(h))] for h in heights]

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("◀️", "page", str(page - 1)))
    nav.append(_btn(t(lang, "btn_main"), "main"))
    if page < num_pages - 1:
        nav.append(_btn("▶️", "page", str(page + 1)))

    keyboard = rows + [nav, [_btn(t(lang, "btn_cancel"), "cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def oversize_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Offered when the selected size exceeds the configured limit."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t(lang, "btn_choose"), "choose")],
            [_btn(t(lang, "btn_audio"), "audio")],
            [_btn(t(lang, "btn_cancel"), "cancel")],
        ]
    )


def cancel_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Single cancel button — used during queueing, downloading and uploading."""
    return InlineKeyboardMarkup(inline_keyboard=[[_btn(t(lang, "btn_cancel"), "cancel")]])


def remove_keyboard() -> InlineKeyboardMarkup:
    """Empty keyboard — passing this REMOVES the inline keyboard on edit.

    (``reply_markup=None`` would keep the existing keyboard, so terminal
    states must pass an explicitly empty markup instead.)
    """
    return InlineKeyboardMarkup(inline_keyboard=[])
