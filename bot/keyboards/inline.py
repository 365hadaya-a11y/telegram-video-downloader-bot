"""Inline keyboards and callback data for the download flow."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class DownloadCB(CallbackData, prefix="dl"):
    """Callback payload.

    Actions: ``best``, ``choose``, ``audio``, ``cancel``, ``quality``,
    ``page``, ``main``.
    """

    action: str
    value: str = ""


def _btn(text: str, action: str, value: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=DownloadCB(action=action, value=value).pack())


def info_keyboard(has_qualities: bool = True) -> InlineKeyboardMarkup:
    """Main action keyboard shown on the info card."""
    rows = [[_btn("🎥 Best Quality", "best")]]
    rows.append(
        [_btn("📺 Choose Quality", "choose"), _btn("🎵 Audio Only", "audio")]
        if has_qualities
        else [_btn("🎵 Audio Only", "audio")]
    )
    rows.append([_btn("❌ Cancel", "cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quality_keyboard(
    heights: list[int],
    page: int,
    num_pages: int,
    size_map: dict[int, str],
) -> InlineKeyboardMarkup:
    """Paged resolution picker."""
    rows = [[_btn(f"📺 {h}p · {size_map.get(h, 'size ?')}", "quality", str(h))] for h in heights]

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("◀️", "page", str(page - 1)))
    nav.append(_btn("🔙 Main", "main"))
    if page < num_pages - 1:
        nav.append(_btn("▶️", "page", str(page + 1)))

    keyboard = rows + [nav, [_btn("❌ Cancel", "cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def oversize_keyboard() -> InlineKeyboardMarkup:
    """Offered when the selected size exceeds the configured limit."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn("📺 Choose Quality", "choose")],
            [_btn("🎵 Audio Only", "audio")],
            [_btn("❌ Cancel", "cancel")],
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Single cancel button — used during queueing, downloading and uploading."""
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("❌ Cancel", "cancel")]])


def remove_keyboard() -> InlineKeyboardMarkup:
    """Empty keyboard — passing this REMOVES the inline keyboard on edit.

    (``reply_markup=None`` would keep the existing keyboard, so terminal
    states must pass an explicitly empty markup instead.)
    """
    return InlineKeyboardMarkup(inline_keyboard=[])
