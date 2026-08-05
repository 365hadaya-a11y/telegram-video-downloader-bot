"""Smoke test — validates imports, config, and core logic without a bot token.

Run from the project root:  python tests/test_smoke.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["BOT_TOKEN"] = "123456:TEST_TOKEN"
os.environ["ADMIN_IDS"] = "[111, 222]"

# ── Imports (would fail on any broken module / bad aiogram usage) ──
import bot.main  # noqa: F401
import bot.services.downloader  # noqa: F401
from bot.config import Settings, load_settings
from bot.database import Database
from bot.keyboards.inline import (
    DownloadCB,
    cancel_keyboard,
    info_keyboard,
    quality_keyboard,
    remove_keyboard,
)
from bot.services.broadcast import BroadcastCB, BroadcastService, broadcast_cancel_keyboard
from bot.services.queue import DownloadQueue
from bot.services.rate_limiter import RateLimiter
from bot.services.subscription import ForcedSubscription, JoinCB
from bot.services.ytdlp import (
    available_qualities,
    best_height,
    estimate_size,
    format_spec,
    has_video_formats,
)
from bot.utils.formatters import (
    clean_filename,
    extract_url,
    format_duration,
    format_size,
    progress_bar,
)
from bot.utils.retry import retry_async

results: list[tuple[str, bool]] = []


def check(name: str, cond: bool) -> None:
    results.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name, flush=True)


# ── Settings ──
settings = load_settings()
check("settings loads", settings.bot_token == "123456:TEST_TOKEN")
check("admin_ids parsed", settings.admin_ids == [111, 222])
check("max size bytes", settings.max_file_size_bytes == 2000 * 1024 * 1024)

# ── Formatters ──
check("format_size", format_size(13_000_000) == "12.4 MB")
check("format_duration", format_duration(3723) == "1:02:03")
check("progress_bar", progress_bar(80, 12) == "██████████░░")
check("clean_filename", clean_filename('a/b:c*d "e"') == "a b c d e")
check("extract_url", extract_url("watch https://youtu.be/abc?t=5 ok") == "https://youtu.be/abc?t=5")
check("extract_url none", extract_url("no links here") is None)

# ── yt-dlp format helpers ──
SAMPLE_INFO = {
    "formats": [
        {"format_id": "v1", "vcodec": "avc1", "height": 1080, "tbr": 4500, "filesize": 100_000_000},
        {"format_id": "v2", "vcodec": "avc1", "height": 720, "tbr": 2500, "filesize": 50_000_000},
        {"format_id": "a1", "acodec": "mp4a", "abr": 128, "filesize": 5_000_000},
    ]
}
check("best_height", best_height(SAMPLE_INFO) == 1080)
check("qualities", available_qualities(SAMPLE_INFO) == [1080, 720])
check("has_video", has_video_formats(SAMPLE_INFO) is True)
check("estimate_size", estimate_size(SAMPLE_INFO, None) == 105_000_000)
check("estimate_size_720", estimate_size(SAMPLE_INFO, 720) == 55_000_000)
check("format_spec best", format_spec("video", None) == "bv*+ba/b")
check("format_spec 720", format_spec("video", 720) == "bv*[height<=720]+ba/b[height<=720]/b[height<=720]")
check("format_spec audio", format_spec("audio", None) == "ba/b")

# ── Callback data round-trip ──
packed = DownloadCB(action="quality", value="1080").pack()
cb = DownloadCB.unpack(packed)
check("callback round-trip", (cb.action, cb.value) == ("quality", "1080"))
check("join cb pack", JoinCB().pack().startswith("join:"))
check("broadcast cb pack", BroadcastCB(action="cancel").pack().startswith("bc:"))

# ── Rate limiter ──
rl = RateLimiter(max_events=2, window_seconds=10)
rl.is_limited(1)
rl.is_limited(1)
check("rate limiter trips", rl.is_limited(1) is True)

# ── Keyboards ──
kb = info_keyboard(has_qualities=True)
check("info keyboard buttons", len(kb.inline_keyboard) == 3)
qkb = quality_keyboard([2160, 1080, 720], page=0, num_pages=1, size_map={1080: "1.2 GB"})
check("quality keyboard", len(qkb.inline_keyboard) >= 3)
check("remove_keyboard empty", remove_keyboard().inline_keyboard == [])

# ── Forced subscription (disabled path needs no bot) ──
fs_off = ForcedSubscription(None)
check("sub disabled", fs_off.enabled is False)
fs_on = ForcedSubscription("@MyAnnouncements")
check("sub enabled", fs_on.enabled is True and fs_on.channel_ref == "@MyAnnouncements")
join_kb = fs_on.join_keyboard()
check("join kb rows", len(join_kb.inline_keyboard) == 2)
check("broadcast cancel kb", len(broadcast_cancel_keyboard().inline_keyboard) == 1)


# ── Everything async runs in ONE event loop (Windows-friendly) ──
async def run_all() -> None:
    # Retry
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("boom")
        return "ok"

    retry_result = await retry_async(flaky, attempts=4, base_delay=0.01)
    check("retry succeeds", retry_result == "ok" and calls["n"] == 3)

    # Queue
    q = DownloadQueue(workers=1)
    t1 = q.register()
    t2 = q.register()
    check("queue position", q.position(t1) == 1 and q.position(t2) == 2)
    await q.acquire(t1)
    check("queue started", q.position(t1) == 0 and q.position(t2) == 1)
    q.release(t1)
    await q.acquire(t2)
    check("queue second acquires", q.active_count == 1)
    q.release(t2)

    # Session future resolution (regression: _ask race fix)
    from bot.services.downloader import DownloadSession

    s = DownloadSession(user_id=1, chat_id=1, url="x", workdir=Path("."))
    fut = s.start_wait()
    s.resolve("best")  # resolve before await — tap during edit window
    check("session resolve early", await s.await_choice(fut, 5) == "best")
    fut2 = s.start_wait()
    s.resolve("cancel")
    check("session resolve cancel", await s.await_choice(fut2, 5) == "cancel")

    # Forced subscription disabled path (no bot needed)
    check("sub disabled passes", await fs_off.is_member(None, 1) is True)  # type: ignore[arg-type]

    # Database
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "test.db")
        await db.connect()
        await db.upsert_user(1, "alice", "Alice", None)
        check("upsert user", await db.users_count() == 1)
        await db.log_download(1, "https://x", "video", 1080, 100, 60, True)
        check("today downloads", await db.today_downloads(1) == 1)
        check("total downloads", await db.total_downloads() == 1)
        await db.set_sticker("welcome", "FID123")
        check("sticker get", await db.get_sticker("welcome") == "FID123")
        check("sticker list", "welcome" in await db.list_stickers())
        await db.delete_sticker("welcome")
        check("sticker deleted", await db.get_sticker("welcome") is None)
        await db.log_download(1, "https://x", "audio", None, 50, 60, False, "err")
        check("failed not counted", await db.today_downloads(1) == 1)
        # old row (2 days ago) must be pruned; fresh rows must survive
        await db.conn.execute(
            "INSERT INTO downloads_log (user_id, url, mode, quality, file_size, duration_seconds, success, error, created_at) "
            "VALUES (1, 'https://old', 'video', '720', 100, 60, 1, NULL, datetime('now', '-2 days'))"
        )
        await db.conn.commit()
        await db.prune_logs(days=1)
        check("prune", await db.total_downloads() == 1)
        check("all_user_ids", await db.all_user_ids() == [1])
        await db.remove_user(1)
        check("remove_user", await db.users_count() == 0)
        await db.close()

    # Broadcast service
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "t.db")
        await db.connect()
        await db.upsert_user(1, "alice", "Alice", None)
        await db.upsert_user(2, "bob", "Bob", None)

        bc = BroadcastService(db)
        sent: list[int] = []

        async def deliver(chat_id: int) -> None:
            sent.append(chat_id)

        progress: list[tuple] = []
        result = await bc.run(deliver, on_progress=lambda d, t, r: progress.append((d, t)), progress_every=1)
        check("broadcast sent", result.sent == 2 and sorted(sent) == [1, 2])
        check("broadcast clean", result.failed == 0 and result.blocked == 0 and not result.cancelled)
        check("broadcast progress called", len(progress) == 2)
        check("broadcast not running after", bc.running is False)

        # Deterministic cancel: 6 slow sends → cancel lands mid-loop
        await db.upsert_user(3, "carol", "Carol", None)
        await db.upsert_user(4, "dave", "Dave", None)
        await db.upsert_user(5, "erin", "Erin", None)
        await db.upsert_user(6, "frank", "Frank", None)
        bc2 = BroadcastService(db)

        async def slow_deliver(chat_id: int) -> None:
            await asyncio.sleep(0.1)

        task = asyncio.create_task(bc2.run(slow_deliver, progress_every=1))
        await asyncio.sleep(0.25)
        check("broadcast running while active", bc2.running is True)
        bc2.request_cancel()
        res2 = await task
        check("broadcast cancellable", res2.cancelled is True)
        check("broadcast partial", res2.sent < 6)
        await db.close()


asyncio.run(run_all())

# ── aiogram wiring specifics ──
from aiogram import BaseMiddleware, Bot, Dispatcher  # noqa: E402
from aiogram.types import BotCommandScopeChat, FSInputFile  # noqa: E402

dp = Dispatcher()
dp.workflow_data["services"] = object()
check("workflow_data supported", "services" in dp.workflow_data)
import inspect  # noqa: E402

sig = inspect.signature(Bot)
check("Bot default kwarg", "default" in sig.parameters)
check("FSInputFile import", True)

print("\n" + "=" * 40)
failed = [n for n, ok in results if not ok]
print(f"TOTAL: {len(results)} checks, {len(failed)} failed")
if failed:
    print("FAILED:", failed)
    raise SystemExit(1)
print("ALL CHECKS PASSED ✔")
