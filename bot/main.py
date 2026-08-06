"""Application bootstrap: builds every service and starts polling."""

from __future__ import annotations

import asyncio
import logging
import secrets
from typing import NoReturn

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from .config import load_settings
from .database import Database
from .handlers import admin_router, callbacks_router, download_router, panel_router, start_router
from .middlewares import ThrottlingMiddleware
from .services import Services
from .services.broadcast import BroadcastService
from .services.cleanup import CleanupService
from .services.downloader import DownloadService
from .services.queue import DownloadQueue
from .services.stickers import StickerService
from .services.subscription import ForcedSubscription
from .services.ytdlp import YtDlpService
from .utils.i18n import t as tr
from .utils.logger import setup_logging

logger = logging.getLogger("bot")

def _default_commands(lang: str) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=tr(lang, "cmd_start")),
        BotCommand(command="help", description=tr(lang, "cmd_help")),
        BotCommand(command="language", description=tr(lang, "cmd_language")),
        BotCommand(command="cancel", description=tr(lang, "cmd_cancel")),
    ]


def _admin_commands(lang: str) -> list[BotCommand]:
    return [
        *_default_commands(lang),
        BotCommand(command="panel", description=tr(lang, "cmd_panel")),
        BotCommand(command="broadcast", description=tr(lang, "cmd_broadcast")),
        BotCommand(command="stats", description=tr(lang, "cmd_stats")),
        BotCommand(command="stickers", description=tr(lang, "cmd_stickers")),
        BotCommand(command="setsticker", description=tr(lang, "cmd_setsticker")),
        BotCommand(command="setchannel", description=tr(lang, "cmd_setchannel")),
        BotCommand(command="delchannel", description=tr(lang, "cmd_delchannel")),
    ]


async def _set_commands(bot: Bot, services: Services) -> None:
    default_lang = services.settings.default_language
    await bot.set_my_commands(_default_commands(default_lang))
    for admin_id in services.settings.admin_ids:
        admin_lang = await services.db.get_user_lang(admin_id)
        await bot.set_my_commands(
            _admin_commands(admin_lang or default_lang),
            scope=BotCommandScopeChat(chat_id=admin_id),
        )


async def main() -> None:
    settings = load_settings()
    setup_logging(settings)
    logger.info("Starting Premium Video Downloader Bot…")

    db = Database(settings.db_path)
    await db.connect()

    ytdlp = YtDlpService(settings)
    web_manager = None
    if settings.web_enabled:
        from .web.manager import WebDownloadManager

        web_manager = WebDownloadManager(settings, ytdlp)
        logger.info(
            "Web download site enabled — base: %s",
            settings.web_base or "(derived from WEBHOOK_URL)",
        )
    stickers = StickerService(settings, db)
    queue = DownloadQueue(settings.download_workers)
    downloader = DownloadService(settings, db, ytdlp, stickers, queue)
    cleanup = CleanupService(settings, db)
    subscription = ForcedSubscription(db, env_channels=settings.all_force_channels)
    await subscription.refresh_runtime()
    broadcast = BroadcastService(db)

    if subscription.enabled:
        logger.info("Forced channel subscription enabled: %s", subscription.channel_refs_text())

    services = Services(
        settings=settings,
        db=db,
        ytdlp=ytdlp,
        stickers=stickers,
        queue=queue,
        downloader=downloader,
        cleanup=cleanup,
        subscription=subscription,
        broadcast=broadcast,
        web=web_manager,
    )

    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )
    dp = Dispatcher()
    dp.workflow_data["services"] = services

    dp.message.middleware(ThrottlingMiddleware(settings))

    for router in (start_router, admin_router, panel_router, callbacks_router, download_router):
        dp.include_router(router)

    try:
        await _set_commands(bot, services)
    except Exception:
        logger.exception("Could not set bot commands (non-fatal)")
    logger.info("Bot is ready — %d admin(s), %d worker(s)", len(settings.admin_ids), settings.download_workers)

    cleanup_task = asyncio.create_task(cleanup.run())
    web_cleanup_task = None
    if web_manager is not None:
        web_cleanup_task = asyncio.create_task(web_manager.cleanup_loop())
    try:
        if settings.webhook_mode:
            await _serve_webhook(bot, dp, services)
        else:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        cleanup_task.cancel()
        if web_cleanup_task is not None:
            web_cleanup_task.cancel()
        await db.close()
        await bot.session.close()


def build_aiohttp_app(bot: Bot, dp: Dispatcher, services: Services) -> tuple[web.Application, str]:
    """Assemble the aiohttp app: webhook handler + optional web download site.

    Returns ``(app, secret)`` without starting the server or registering the
    webhook — used by :func:`_serve_webhook` and covered by smoke tests.
    """
    settings = services.settings
    secret = settings.webhook_secret or secrets.token_urlsafe(32)
    app = web.Application()

    # Health endpoint for the platform's health checks
    async def _health(_request: web.Request) -> web.Response:
        return web.Response(text="ok")

    app.router.add_get("/health", _health)

    # Mount the premium web download site on the same server (shares port 8080)
    if services.web is not None and settings.web_enabled:
        from .web.server import create_web_app

        create_web_app(app, services)
    else:
        app.router.add_get("/", _health)

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=secret)
    webhook_handler.register(app, path=settings.webhook_path)
    setup_application(app, dp)
    return app, secret


async def _serve_webhook(bot: Bot, dp: Dispatcher, services: Services) -> NoReturn:
    """Run an aiohttp server that feeds Telegram updates into the dispatcher.

    Used on Koyeb (and other hosts) where a public HTTPS URL is available:
    Telegram pushes updates to ``WEBHOOK_URL`` — inbound traffic keeps the
    instance awake and the public URL doubles as a health-check target.
    """
    settings = services.settings
    if not settings.webhook_url:
        raise ValueError("WEBHOOK_URL is required when WEBHOOK_MODE=true")

    app, secret = build_aiohttp_app(bot, dp, services)

    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=secret,
        allowed_updates=dp.resolve_used_update_types(),
    )
    logger.info("Webhook registered: %s", settings.webhook_url)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webhook_host, settings.webhook_port)
    await site.start()
    logger.info(
        "Webhook server listening on http://%s:%s%s",
        settings.webhook_host,
        settings.webhook_port,
        settings.webhook_path,
    )

    try:
        await asyncio.Event().wait()  # serve forever
    finally:
        await runner.cleanup()
