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


class PanelCB(CallbackData, prefix="panel"):
    """Admin panel navigation.

    ``view``: main | stats | users | broadcast | stickers | channels |
    settings | language.  ``action``: open | refresh | back | close | delchan.
    """

    view: str = "main"
    action: str = "open"
    value: str = ""


def _btn(text: str, action: str, value: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=DownloadCB(action=action, value=value).pack())


def _panel_btn(text: str, view: str, action: str = "open", value: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=PanelCB(view=view, action=action, value=value).pack(),
    )


def language_keyboard(current_lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Bilingual picker; the active language gets a ✓ marker."""
    rows = []
    for lang in (LANG_AR, LANG_EN):
        label = LANG_LABELS[lang]
        if lang == current_lang:
            label = f"✓ {label}"
        rows.append([InlineKeyboardButton(text=label, callback_data=LanguageCB(lang=lang).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def info_keyboard(
    has_qualities: bool = True,
    lang: str = LANG_AR,
    web_url: str | None = None,
) -> InlineKeyboardMarkup:
    """Main action keyboard shown on the info card."""
    rows = [[_btn(t(lang, "btn_best"), "best")]]
    rows.append(
        [_btn(t(lang, "btn_choose"), "choose"), _btn(t(lang, "btn_audio"), "audio")]
        if has_qualities
        else [_btn(t(lang, "btn_audio"), "audio")]
    )
    if web_url:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_web"), url=web_url)])
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


def oversize_keyboard(lang: str = LANG_AR, web_url: str | None = None) -> InlineKeyboardMarkup:
    """Offered when the selected size exceeds the configured limit."""
    rows: list[list[InlineKeyboardButton]] = [
        [_btn(t(lang, "btn_choose"), "choose")],
        [_btn(t(lang, "btn_audio"), "audio")],
    ]
    if web_url:
        rows.insert(0, [InlineKeyboardButton(text=t(lang, "btn_web_offer"), url=web_url)])
    rows.append([_btn(t(lang, "btn_cancel"), "cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def web_offer_keyboard(web_url: str, lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Shown when the finished file exceeds Telegram's upload limit."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_web_offer"), url=web_url)],
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


# ── Admin panel (لوحة تحكم المدير) ──────────────────────────────────────────


def admin_panel_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Main admin panel menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_panel_btn(t(lang, "panel_btn_stats"), "stats"), _panel_btn(t(lang, "panel_btn_users"), "users")],
            [_panel_btn(t(lang, "panel_btn_broadcast"), "broadcast"), _panel_btn(t(lang, "panel_btn_stickers"), "stickers")],
            [_panel_btn(t(lang, "panel_btn_channels"), "channels"), _panel_btn(t(lang, "panel_btn_settings"), "settings")],
            [_panel_btn(t(lang, "panel_btn_language"), "language")],
            [_panel_btn(t(lang, "panel_btn_close"), "main", action="close")],
        ]
    )


def _panel_back_close(lang: str, view: str) -> list[list[InlineKeyboardButton]]:
    return [
        [_panel_btn(t(lang, "panel_btn_refresh"), view, action="refresh")],
        [_panel_btn(t(lang, "panel_btn_back"), "main"), _panel_btn(t(lang, "panel_btn_close"), "main", action="close")],
    ]


def panel_stats_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=_panel_back_close(lang, "stats"))


def panel_users_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=_panel_back_close(lang, "users"))


def panel_broadcast_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_panel_btn(t(lang, "panel_btn_back"), "main"), _panel_btn(t(lang, "panel_btn_close"), "main", action="close")],
        ]
    )


def panel_stickers_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=_panel_back_close(lang, "stickers"))


def panel_channels_keyboard(channels: list[str], lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Channel list with a ✖️ delete button per runtime channel."""
    rows: list[list[InlineKeyboardButton]] = []
    for ref in channels:
        rows.append([_panel_btn(f"✖️ {ref}", "channels", action="delchan", value=ref)])
    rows.append([_panel_btn(t(lang, "panel_btn_add_channel"), "channels", action="addchan")])
    rows.append(
        [_panel_btn(t(lang, "panel_btn_back"), "main"), _panel_btn(t(lang, "panel_btn_close"), "main", action="close")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def panel_settings_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=_panel_back_close(lang, "settings"))


def panel_language_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    rows = []
    for lg in (LANG_AR, LANG_EN):
        label = LANG_LABELS[lg]
        if lg == lang:
            label = f"✓ {label}"
        rows.append([_panel_btn(label, "language", action="setlang", value=lg)])
    rows.append([_panel_btn(t(lang, "panel_btn_back"), "main"), _panel_btn(t(lang, "panel_btn_close"), "main", action="close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Welcome buttons ──────────────────────────────────────────────────────────


def welcome_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Shown on /start: language picker + help."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "panel_btn_language"),
                    callback_data=LanguageCB(lang=lang).pack(),
                ),
                InlineKeyboardButton(
                    text=t(lang, "welcome_help_btn"),
                    callback_data=DownloadCB(action="help").pack(),
                ),
            ]
        ]
    )


def welcome_help_keyboard(lang: str = LANG_AR) -> InlineKeyboardMarkup:
    """Keyboard for the /help message."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "welcome_help_btn"), callback_data=DownloadCB(action="help").pack())]
        ]
    )
