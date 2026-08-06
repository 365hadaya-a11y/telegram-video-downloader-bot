"""Download orchestration.

One per-user session drives the whole flow: fetch info → show info card →
let the user choose quality → queue → download with live progress →
simulated upload animation → deliver the file.

Everything happens on a single editable status card per user, so the chat
stays clean and the experience feels premium.
"""

from __future__ import annotations

import asyncio
import html
import logging
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import aiohttp
import yt_dlp
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import FSInputFile, InlineKeyboardMarkup, Message

from ..config import Settings
from ..database.db import Database
from ..keyboards.inline import (
    cancel_keyboard,
    info_keyboard,
    oversize_keyboard,
    quality_keyboard,
    remove_keyboard,
)
from ..utils.formatters import (
    clean_filename,
    format_duration,
    format_size,
    format_speed,
    progress_bar,
)
from ..utils.i18n import normalize_lang, t
from ..utils.retry import retry_async
from .queue import DownloadQueue
from .stickers import StickerService
from .ytdlp import (
    DownloadCancelled,
    ProgressChannel,
    ProgressPayload,
    YtDlpService,
    available_qualities,
    best_height,
    estimate_size,
    format_spec,
    has_video_formats,
    selected_video_format,
)

logger = logging.getLogger(__name__)

MAX_CAPTION = 1024
PAGE_SIZE = 6
_FATAL_HINTS = (
    "private",
    "unavailable",
    "not available",
    "sign in",
    "login required",
    "login to confirm",
    "removed",
    "deleted",
    "age-restricted",
    "members only",
    "copyright",
    "taken down",
    "does not exist",
    "unsupported url",
    "video unavailable",
)


def _clip(text: str, limit: int = MAX_CAPTION) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _is_retryable(exc: BaseException) -> bool:
    message = str(exc).lower()
    return not any(hint in message for hint in _FATAL_HINTS)


def _friendly_error(lang: str, exc: BaseException) -> str:
    """Turn a raw exception into a human-friendly, emoji-driven reason."""
    message = str(exc).lower()

    if isinstance(exc, DownloadCancelled):
        return t(lang, "err_cancelled")
    if "private" in message:
        return t(lang, "err_private")
    if any(hint in message for hint in ("sign in", "login", "member")):
        return t(lang, "err_login")
    if "age" in message:
        return t(lang, "err_age")
    if any(hint in message for hint in ("network", "timed out", "timeout", "connection", "unreachable", "ssl")):
        return t(lang, "err_network")
    if "unsupported" in message:
        return t(lang, "err_unsupported")
    if any(hint in message for hint in ("unavailable", "removed", "deleted", "does not exist", "taken down")):
        return t(lang, "err_unavailable")
    return t(lang, "err_generic")


# ── Session ──────────────────────────────────────────────────────────────────


@dataclass
class DownloadSession:
    """State for one active download flow, keyed by user id."""

    user_id: int
    chat_id: int
    url: str
    lang: str = "ar"
    workdir: Path = field(default_factory=lambda: Path("."))
    message: Message | None = None
    card_message_id: int | None = None
    card_is_photo: bool = True
    status_message_id: int | None = None
    thumb_path: Path | None = None
    phase: str = "info"
    cancel_event: threading.Event = field(default_factory=threading.Event)
    _choice: asyncio.Future[str] | None = None

    def start_wait(self) -> asyncio.Future[str]:
        """Begin waiting for a callback decision."""
        self._choice = asyncio.get_running_loop().create_future()
        return self._choice

    def resolve(self, value: str) -> None:
        if self._choice is not None and not self._choice.done():
            self._choice.set_result(value)

    @staticmethod
    async def await_choice(future: asyncio.Future[str], timeout: float) -> str:
        try:
            return await asyncio.wait_for(asyncio.shield(future), timeout)
        except asyncio.TimeoutError:
            return "cancel"


# ── Caption builders ─────────────────────────────────────────────────────────


def _info_card(info: dict, settings: Settings, lang: str) -> str:
    title = html.escape(info.get("title") or t(lang, "info_untitled"))
    duration = format_duration(info.get("duration"))
    size = format_size(estimate_size(info, None))
    height = best_height(info) or "?"
    channel = html.escape(info.get("channel") or info.get("uploader") or t(lang, "info_unknown"))
    channel_url = info.get("channel_url") or info.get("uploader_url")

    channel_html = (
        f'<a href="{html.escape(channel_url, quote=True)}">{channel}</a>' if channel_url else channel
    )
    text = t(
        lang,
        "info_card",
        title=f"<blockquote>{title}</blockquote>",
        channel=channel_html,
        duration=duration,
        size=size,
        height=height,
    )
    return _clip(text)


def _download_caption(lang: str, payload: ProgressPayload) -> str:
    total = payload.total_bytes
    if total:
        percent = min(100.0, payload.downloaded_bytes / total * 100)
        bar = f"<code>{progress_bar(percent)}</code> {percent:.0f}%"
    else:
        bar = t(lang, "downloading_wait")
    line = f"📥 {format_size(payload.downloaded_bytes)} / {format_size(total)}"
    meta = f"⚡ {format_speed(payload.speed)}"
    if payload.eta:
        meta += f" • ⏱️ ETA {format_duration(payload.eta)}"
    return "\n".join(
        [
            t(lang, "downloading"),
            bar,
            line,
            meta,
            "",
            t(lang, "dl_hint"),
        ]
    )


def _processing_caption(lang: str) -> str:
    return t(lang, "processing")


def _queued_caption(lang: str, position: int, workers: int) -> str:
    return t(lang, "queued", position=position, workers=workers)


def _upload_caption(lang: str, percent: int, size: str) -> str:
    return (
        f"{t(lang, 'uploading')}\n"
        f"<code>{progress_bar(percent)}</code> {percent}%\n"
        f"📦 {size}\n\n"
        f"{t(lang, 'almost_there')}"
    )


def _success_caption(lang: str, info: dict, mode: str, height: int | None, size: int) -> str:
    title = html.escape(info.get("title") or t(lang, "info_untitled"))
    lines = [
        t(lang, "success"),
        "",
        f"<blockquote>{title}</blockquote>",
        f"⏱️ {t(lang, 'duration_label')}: {format_duration(info.get('duration'))}",
        f"{t(lang, 'size_label')}: {format_size(size)}",
    ]
    if mode == "audio":
        lines.append(t(lang, "format_audio"))
    else:
        lines.append(t(lang, "quality_label", height=height) if height else t(lang, "quality_best"))
    lines += ["", t(lang, "thanks")]
    return _clip("\n".join(lines))


def _delivered_caption(lang: str, elapsed: float, size: int) -> str:
    return _clip(t(lang, "delivered", elapsed=elapsed, size=format_size(size)))


def _cancelled_caption(lang: str) -> str:
    return t(lang, "cancelled")


def _error_card(lang: str, reason: str) -> str:
    return _clip(t(lang, "error_card", reason=reason))


def _too_large_card(lang: str, size: str, limit_mb: int) -> str:
    return _clip(t(lang, "too_large", size=size, limit_mb=limit_mb))


# ── Service ──────────────────────────────────────────────────────────────────


class DownloadService:
    """Drives the per-user download flows."""

    def __init__(
        self,
        settings: Settings,
        db: Database,
        ytdlp: YtDlpService,
        stickers: StickerService,
        queue: DownloadQueue,
    ) -> None:
        self.settings = settings
        self.db = db
        self.ytdlp = ytdlp
        self.stickers = stickers
        self.queue = queue
        self.sessions: dict[int, DownloadSession] = {}
        self._lock = asyncio.Lock()

    # -- public API ---------------------------------------------------------

    async def handle_url(self, message: Message, url: str, lang: str | None = None) -> None:
        """Entry point for a URL message. Runs the whole flow in this task."""
        user = message.from_user
        assert user is not None
        bot = message.bot
        session_lang = normalize_lang(lang or self.settings.default_language)

        async with self._lock:
            if user.id in self.sessions:
                await message.answer(
                    t(session_lang, "active_download"),
                    reply_markup=cancel_keyboard(session_lang),
                )
                return

            today = await self.db.today_downloads(user.id)
            if today >= self.settings.daily_download_limit:
                await message.answer(t(session_lang, "daily_limit", limit=self.settings.daily_download_limit))
                return

            session = DownloadSession(
                user_id=user.id,
                chat_id=message.chat.id,
                url=url,
                lang=session_lang,
                workdir=self.settings.temp_dir / f"job_{uuid4().hex[:10]}",
            )
            self.sessions[user.id] = session

        try:
            await self.db.upsert_user(
                user.id, user.username, user.first_name, user.last_name
            )
            await self.stickers.send(message, bot, "loading")
            status = await message.answer(t(session_lang, "fetching"))
            session.status_message_id = status.message_id
            await self._run_flow(session, message, bot, url)
        except Exception:
            logger.exception("Unhandled error in download flow for user %s", user.id)
            await self._show_error_card(session, bot, t(session_lang, "err_unhandled"))
        finally:
            self.sessions.pop(user.id, None)
            await self._cleanup_session(session)

    async def cancel(self, user_id: int) -> bool:
        """Cancel the active session of ``user_id`` (used by /cancel)."""
        session = self.sessions.get(user_id)
        if session is None:
            return False
        session.cancel_event.set()
        session.resolve("cancel")
        return True

    # -- flow steps ----------------------------------------------------------

    async def _run_flow(self, session: DownloadSession, message: Message, bot: Bot, url: str) -> None:
        try:
            info = await retry_async(
                lambda: self.ytdlp.get_video_info(url),
                attempts=self.settings.retry_attempts,
                base_delay=self.settings.retry_backoff_seconds,
                exceptions=(yt_dlp.utils.DownloadError,),
                is_retryable=_is_retryable,
                on_retry=lambda a, t, _e: self._safe_edit_text(
                    session, bot, t(session.lang, "retry_info", attempt=a, total=t)
                ),
            )
        except Exception as exc:
            logger.warning("Info fetch failed for user %s: %s", session.user_id, exc)
            await self._fail(session, message, bot, exc)
            return

        await self._show_info_card(session, message, bot, info)
        qualities = available_qualities(info, limit=self.settings.max_quality_choices)
        info_caption = _info_card(info, self.settings, session.lang)

        while True:
            # caption is passed explicitly so it is restored after the
            # quality menu / oversize warning overwrites it
            choice = await self._ask(
                session,
                bot,
                caption=info_caption,
                keyboard=info_keyboard(has_qualities=bool(qualities), lang=session.lang),
            )
            action, _, value = choice.partition(":")
            logger.info("User %s chose %r (phase=%s)", session.user_id, choice, session.phase)

            if action == "cancel":
                await self._finish_cancelled(session, bot)
                return
            if action == "best":
                mode, height = "video", None
            elif action == "audio":
                mode, height = "audio", None
            elif action == "choose":
                picked = await self._quality_menu(session, bot, info)
                if picked == "cancel":
                    await self._finish_cancelled(session, bot)
                    return
                if picked == "back":
                    continue
                mode, height = "video", picked
            else:
                continue

            estimated = estimate_size(info, height)
            if estimated and estimated > self.settings.max_file_size_bytes:
                warn = t(
                    session.lang,
                    "too_large_warn",
                    size=format_size(estimated),
                    limit_mb=self.settings.max_file_size_mb,
                )
                choice2 = await self._ask(session, bot, caption=warn, keyboard=oversize_keyboard(session.lang))
                action2, _, _ = choice2.partition(":")
                if action2 == "cancel":
                    await self._finish_cancelled(session, bot)
                    return
                if action2 == "choose":
                    picked = await self._quality_menu(session, bot, info)
                    if picked == "cancel":
                        await self._finish_cancelled(session, bot)
                        return
                    if picked == "back":
                        continue
                    mode, height = "video", picked
                elif action2 == "audio":
                    mode, height = "audio", None
                else:
                    continue

            result = await self._execute(session, bot, info, mode, height)
            if result == "cancel":
                await self._finish_cancelled(session, bot)
            return

    async def _quality_menu(self, session: DownloadSession, bot: Bot, info: dict) -> int | str:
        """Let the user pick a resolution. Returns height, ``"cancel"`` or ``"back"``."""
        qualities = available_qualities(info, limit=self.settings.max_quality_choices)
        if not qualities:
            return "back"

        size_map = {h: format_size(estimate_size(info, h)) for h in qualities}
        pages = [qualities[i : i + PAGE_SIZE] for i in range(0, len(qualities), PAGE_SIZE)]
        page = 0

        while True:
            keyboard = quality_keyboard(pages[page], page, len(pages), size_map, lang=session.lang)
            caption = t(session.lang, "choose_quality")
            choice = await self._ask(session, bot, caption=caption, keyboard=keyboard)
            action, _, value = choice.partition(":")

            if action == "cancel":
                return "cancel"
            if action == "main":
                return "back"
            if action == "page":
                page = int(value)
                continue
            if action == "quality":
                return int(value)
            return "back"

    async def _execute(self, session: DownloadSession, bot: Bot, info: dict, mode: str, height: int | None) -> str:
        """Queue → download (with live progress) → upload. Returns outcome string."""
        settings = self.settings

        # Audio-only pages (SoundCloud etc.) can never be "video".
        if mode == "video" and not has_video_formats(info):
            mode = "audio"

        await self.stickers.send(session.message, bot, "downloading")  # type: ignore[arg-type]

        ticket = self.queue.register()
        position = self.queue.position(ticket)
        if position > 1:
            await self._edit_card(
                session,
                bot,
                _queued_caption(session.lang, position, settings.download_workers),
                cancel_keyboard(session.lang),
            )
        await self.queue.acquire(ticket)
        try:
            session.phase = "download"
            channel = ProgressChannel()
            pump = asyncio.create_task(self._pump_progress(session, bot, channel))
            try:
                path = await retry_async(
                    lambda: self.ytdlp.download(
                        url=info.get("webpage_url") or session.url,
                        video_id=info.get("id") or "video",
                        mode=mode,
                        height=height,
                        channel=channel,
                        cancel_event=session.cancel_event,
                        workdir=session.workdir,
                    ),
                    attempts=settings.retry_attempts,
                    base_delay=settings.retry_backoff_seconds,
                    exceptions=(yt_dlp.utils.DownloadError,),
                    is_retryable=lambda exc: not session.cancel_event.is_set() and _is_retryable(exc),
                    on_retry=lambda a, t, _e: self._edit_card(
                        session,
                        bot,
                        t(session.lang, "retry_download", attempt=a, total=t),
                        cancel_keyboard(session.lang),
                    ),
                )
            except Exception as exc:
                logger.warning("Download failed for user %s: %s", session.user_id, exc)
                if session.cancel_event.is_set():
                    return "cancel"
                reason = _friendly_error(session.lang, exc)
                await self._edit_card(session, bot, _error_card(session.lang, reason), remove_keyboard())
                await self.stickers.send(session.message, bot, "error")  # type: ignore[arg-type]
                await self.db.log_download(
                    session.user_id, session.url, mode, height, 0, info.get("duration"), False, reason
                )
                return "error"
            finally:
                channel.push(ProgressPayload(status="done"))
                try:
                    await pump
                except Exception:
                    logger.exception("Progress pump crashed")

            if session.cancel_event.is_set():
                return "cancel"

            return await self._upload(session, bot, path, info, mode, height)
        finally:
            self.queue.release(ticket)

    async def _upload(
        self,
        session: DownloadSession,
        bot: Bot,
        path: Path,
        info: dict,
        mode: str,
        height: int | None,
    ) -> str:
        settings = self.settings
        started = time.monotonic()
        size = path.stat().st_size

        if size > settings.max_file_size_bytes:
            await self._edit_card(
                session,
                bot,
                _too_large_card(session.lang, format_size(size), settings.max_file_size_mb),
                remove_keyboard(),
            )
            await self.stickers.send(session.message, bot, "error")  # type: ignore[arg-type]
            await self.db.log_download(session.user_id, session.url, mode, height, size, info.get("duration"), False, "File too large")
            return "error"

        await self.stickers.send(session.message, bot, "uploading")  # type: ignore[arg-type]

        steps = max(6, int(settings.upload_progress_seconds / 0.35))
        size_str = format_size(size)
        for i in range(1, steps + 1):
            if session.cancel_event.is_set():
                return "cancel"
            percent = round(i / steps * 100)
            await self._edit_card(session, bot, _upload_caption(session.lang, percent, size_str), cancel_keyboard(session.lang))
            await asyncio.sleep(settings.upload_progress_seconds / steps)
        if session.cancel_event.is_set():
            return "cancel"

        # The real upload cannot be interrupted, so drop the cancel button
        # and let /cancel still work via the cancel_event below.
        await self._edit_card(
            session,
            bot,
            t(session.lang, "finalising"),
            remove_keyboard(),
        )

        title = (info.get("title") or "Video").strip()
        ext = path.suffix.lstrip(".") or ("mp3" if mode == "audio" else "mp4")
        filename = f"{clean_filename(title)}.{ext}"
        file_input = FSInputFile(path, filename=filename)

        thumbnail: FSInputFile | None = None
        if session.thumb_path and session.thumb_path.suffix.lower() in (".jpg", ".jpeg") and session.thumb_path.stat().st_size <= 200_000:
            thumbnail = FSInputFile(session.thumb_path)

        duration = info.get("duration")
        caption = _success_caption(session.lang, info, mode, height, size)
        try:
            if mode == "audio":
                await session.message.answer_audio(
                    audio=file_input,
                    caption=caption,
                    duration=duration,
                    title=clean_filename(title, max_len=60),
                    performer=info.get("uploader") or info.get("channel"),
                    thumbnail=thumbnail,
                )
            else:
                fmt = selected_video_format(info, height)
                await session.message.answer_video(
                    video=file_input,
                    caption=caption,
                    duration=duration,
                    width=fmt.get("width") if fmt else None,
                    height=fmt.get("height") if fmt else None,
                    thumbnail=thumbnail,
                )
        except TelegramAPIError as exc:
            logger.warning("Telegram upload rejected for user %s: %s", session.user_id, exc)
            await self._edit_card(
                session,
                bot,
                t(session.lang, "telegram_rejected"),
                remove_keyboard(),
            )
            await self.stickers.send(session.message, bot, "error")  # type: ignore[arg-type]
            await self.db.log_download(session.user_id, session.url, mode, height, size, info.get("duration"), False, "Telegram upload rejected")
            return "error"

        if session.cancel_event.is_set():  # cancelled via /cancel during the send
            await self._edit_card(session, bot, _cancelled_caption(session.lang), remove_keyboard())
            return "cancel"

        elapsed = time.monotonic() - started
        await self._edit_card(session, bot, _delivered_caption(session.lang, elapsed, size), remove_keyboard())
        await self.stickers.send(session.message, bot, "success")  # type: ignore[arg-type]
        await self.stickers.send(session.message, bot, "celebration")  # type: ignore[arg-type]
        await self.db.log_download(session.user_id, session.url, mode, height, size, info.get("duration"), True)
        logger.info("Delivered %s (%s) to user %s", filename, format_size(size), session.user_id)
        return "done"

    # -- progress pump -------------------------------------------------------

    async def _pump_progress(self, session: DownloadSession, bot: Bot, channel: ProgressChannel) -> None:
        """Poll the thread-safe channel and refresh the status card."""
        last_edit = 0.0
        while True:
            payload = await channel.pop()
            if payload.status == "done":
                return
            if payload.status == "finished":
                await self._edit_card(session, bot, _processing_caption(session.lang), cancel_keyboard(session.lang))
                continue
            now = time.monotonic()
            if now - last_edit >= self.settings.progress_update_seconds:
                await self._edit_card(session, bot, _download_caption(session.lang, payload), cancel_keyboard(session.lang))
                last_edit = now

    # -- card management -----------------------------------------------------

    async def _ask(
        self,
        session: DownloadSession,
        bot: Bot,
        *,
        caption: str | None = None,
        keyboard: InlineKeyboardMarkup | None = None,
        timeout: float | None = None,
    ) -> str:
        """Update the card, then wait for the user's inline choice.

        The future is created BEFORE the card edit so a tap that lands while
        the edit round-trip is in flight is not silently dropped.
        """
        future = session.start_wait()
        if caption is not None or keyboard is not None:
            await self._edit_card(session, bot, caption, keyboard)
        return await session.await_choice(future, timeout or self.settings.choice_timeout_seconds)

    async def _edit_card(
        self,
        session: DownloadSession,
        bot: Bot,
        caption: str | None,
        keyboard: InlineKeyboardMarkup | None,
    ) -> None:
        if session.card_message_id is None:
            return
        try:
            if session.card_is_photo:
                await bot.edit_message_caption(
                    chat_id=session.chat_id,
                    message_id=session.card_message_id,
                    caption=_clip(caption) if caption else None,
                    reply_markup=keyboard,
                )
            else:
                await bot.edit_message_text(
                    text=_clip(caption) if caption else None,
                    chat_id=session.chat_id,
                    message_id=session.card_message_id,
                    reply_markup=keyboard,
                )
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc):
                logger.debug("Edit failed for user %s: %s", session.user_id, exc)
        except TelegramAPIError as exc:
            logger.debug("Edit failed for user %s: %s", session.user_id, exc)

    async def _safe_edit_text(self, session: DownloadSession, bot: Bot, text: str) -> None:
        if session.status_message_id is None:
            return
        try:
            await bot.edit_message_text(
                text=_clip(text),
                chat_id=session.chat_id,
                message_id=session.status_message_id,
            )
        except TelegramAPIError:
            pass

    async def _show_info_card(self, session: DownloadSession, message: Message, bot: Bot, info: dict) -> None:
        caption = _info_card(info, self.settings, session.lang)
        qualities = available_qualities(info, limit=self.settings.max_quality_choices)
        keyboard = info_keyboard(has_qualities=bool(qualities), lang=session.lang)

        session.thumb_path = await self._fetch_thumbnail(info, session.workdir)

        sent: Message | None = None
        if session.thumb_path:
            try:
                sent = await message.answer_photo(FSInputFile(session.thumb_path), caption=caption, reply_markup=keyboard)
            except TelegramAPIError:
                sent = None
        if sent is None:
            try:
                if info.get("thumbnail"):
                    sent = await message.answer_photo(info["thumbnail"], caption=caption, reply_markup=keyboard)
                else:
                    raise TelegramAPIError("No thumbnail available")
            except TelegramAPIError:
                sent = await message.answer(caption, reply_markup=keyboard)
                session.card_is_photo = False

        session.message = sent
        session.card_message_id = sent.message_id
        if session.status_message_id is not None:
            try:
                await bot.delete_message(session.chat_id, session.status_message_id)
            except TelegramAPIError:
                pass
            session.status_message_id = None

    async def _fetch_thumbnail(self, info: dict, workdir: Path) -> Path | None:
        thumbnails = [t for t in (info.get("thumbnails") or []) if t.get("url")]
        url = None
        for candidate in thumbnails:
            candidate_url = candidate["url"]
            ext = candidate_url.split("?", 1)[0].lower().rsplit(".", 1)[-1]
            if ext in ("jpg", "jpeg"):
                url = candidate_url
                break
        url = url or (thumbnails[-1]["url"] if thumbnails else info.get("thumbnail"))
        if not url:
            return None

        path = workdir / f"thumb_{info.get('id', 'video')}.jpg"
        try:
            async with aiohttp.ClientSession() as http:
                async with http.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        data = await response.read()
                        if data and len(data) < 5 * 1024 * 1024:
                            path.write_bytes(data)
                            return path
        except Exception as exc:  # noqa: BLE001
            logger.debug("Thumbnail fetch failed: %s", exc)
        return None

    # -- terminal states -----------------------------------------------------

    async def _finish_cancelled(self, session: DownloadSession, bot: Bot) -> None:
        session.cancel_event.set()
        await self._edit_card(session, bot, _cancelled_caption(session.lang), remove_keyboard())

    async def _fail(self, session: DownloadSession, message: Message, bot: Bot, exc: BaseException) -> None:
        reason = _friendly_error(session.lang, exc)
        await self.stickers.send(message, bot, "error")
        if session.card_message_id is not None:
            await self._edit_card(session, bot, _error_card(session.lang, reason), remove_keyboard())
        else:
            await message.answer(_error_card(session.lang, reason))
        if session.status_message_id is not None:
            try:
                await bot.delete_message(session.chat_id, session.status_message_id)
            except TelegramAPIError:
                pass
            session.status_message_id = None
        await self.db.log_download(session.user_id, session.url, "info", None, 0, None, False, reason)

    async def _show_error_card(self, session: DownloadSession, bot: Bot, message: str) -> None:
        if session.card_message_id is not None:
            await self._edit_card(session, bot, _clip(message), remove_keyboard())
        elif session.message is not None:
            await session.message.answer(_clip(message))
        if session.message is not None:
            await self.stickers.send(session.message, bot, "error")

    async def _cleanup_session(self, session: DownloadSession) -> None:
        """Delete per-session temp files."""
        if session.workdir.exists():
            shutil.rmtree(session.workdir, ignore_errors=True)
            logger.debug("Cleaned up workdir %s", session.workdir)
