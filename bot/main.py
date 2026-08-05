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
from .handlers import admin_router, callbacks_router, download_router, start_router
from .middlewares import ThrottlingMiddleware
from .services import Services
from .services.broadcast import BroadcastService
from .services.cleanup import CleanupService
from .services.downloader import DownloadService
from .services.queue import DownloadQueue
from .services.stickers import StickerService
from .services.subscription import ForcedSubscription
from .services.ytdlp import YtDlpService
from .utils.logger import setup_logging

logger = logging.getLogger("bot")

DEFAULT_COMMANDS = [
    BotCommand(command="start", description="🚀 Start the bot"),
    BotCommand(command="help", description="❓ Help"),
    BotCommand(command="cancel", description="🚫 Cancel current download"),
]

ADMIN_COMMANDS = [
    *DEFAULT_COMMANDS,
    BotCommand(command="broadcast", description="📣 Broadcast announcement"),
    BotCommand(command="stats", description="📊 Bot statistics"),
    BotCommand(command="stickers", description="🎨 Sticker mapping"),
    BotCommand(command="setsticker", description="🎨 Set a flow sticker"),
]


async def _set_commands(bot: Bot, services: Services) -> None:
    await bot.set_my_commands(DEFAULT_COMMANDS)
    for admin_id in services.settings.admin_ids:
        await bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_id))


async def main() -> None:
    settings = load_settings()
    setup_logging(settings)
    logger.info("Starting Premium Video Downloader Bot…")

    db = Database(settings.db_path)
    await db.connect()

    ytdlp = YtDlpService(settings)
    stickers = StickerService(settings, db)
    queue = DownloadQueue(settings.download_workers)
    downloader = DownloadService(settings, db, ytdlp, stickers, queue)
    cleanup = CleanupService(settings, db)
    subscription = ForcedSubscription(settings.force_channel)
    broadcast = BroadcastService(db)

    if subscription.enabled:
        logger.info("Forced channel subscription enabled: %s", subscription.channel_ref)

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
    )

    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )
    dp = Dispatcher()
    dp.workflow_data["services"] = services

    dp.message.middleware(ThrottlingMiddleware(settings))

    for router in (start_router, admin_router, callbacks_router, download_router):
        dp.include_router(router)

    try:
        await _set_commands(bot, services)
    except Exception:
        logger.exception("Could not set bot commands (non-fatal)")
    logger.info("Bot is ready — %d admin(s), %d worker(s)", len(settings.admin_ids), settings.download_workers)

    cleanup_task = asyncio.create_task(cleanup.run())
    try:
        if settings.webhook_mode:
            await _serve_webhook(bot, dp, services)
        else:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        cleanup_task.cancel()
        await db.close()
        await bot.session.close()


async def _serve_webhook(bot: Bot, dp: Dispatcher, services: Services) -> NoReturn:
    """Run an aiohttp server that feeds Telegram updates into the dispatcher.

    Used on Koyeb (and other hosts) where a public HTTPS URL is available:
    Telegram pushes updates to ``WEBHOOK_URL`` — inbound traffic keeps the
    instance awake and the public URL doubles as a health-check target.
    """
    settings = services.settings
    if not settings.webhook_url:
        raise ValueError("WEBHOOK_URL is required when WEBHOOK_MODE=true")

    secret = settings.webhook_secret or secrets.token_urlsafe(32)
    app = web.Application()

    # Health endpoint for the platform's health checks (GET /)
    async def _health(_request: web.Request) -> web.Response:
        return web.Response(text="ok")

    app.router.add_get("/", _health)

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=secret)
    webhook_handler.register(app, path=settings.webhook_path)
    setup_application(app, dp)

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
