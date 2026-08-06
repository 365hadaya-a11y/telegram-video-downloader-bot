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
import bot.web.server  # noqa: F401
from bot.config import Settings, load_settings
from bot.database import Database
from bot.keyboards.inline import (
    DownloadCB,
    LanguageCB,
    PanelCB,
    admin_panel_keyboard,
    cancel_keyboard,
    info_keyboard,
    language_keyboard,
    oversize_keyboard,
    panel_channels_keyboard,
    panel_language_keyboard,
    panel_stats_keyboard,
    quality_keyboard,
    remove_keyboard,
    web_offer_keyboard,
    welcome_keyboard,
)
from bot.services import Services
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
from bot.utils.i18n import (
    _STRINGS,
    LANG_AR,
    LANG_EN,
    DEFAULT_LANG,
    lang_name,
    normalize_lang,
    t,
    web_mention,
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

# ── i18n (bilingual) ──
check("i18n default ar", DEFAULT_LANG == LANG_AR)
check("i18n ar welcome", "أهلاً" in t(LANG_AR, "welcome", name="سارة", lang_name="العربية", web=""))
check("i18n en welcome", "Welcome" in t(LANG_EN, "welcome", name="Sara", lang_name="English", web=""))
check("web_mention empty", web_mention("ar", "") == "")
check("web_mention set", "اضغط هنا" in web_mention("ar", "https://dl.example.com") and "https://dl.example.com" in web_mention("ar", "https://dl.example.com"))
check("i18n normalize", normalize_lang("EN") == LANG_EN and normalize_lang("xx") == LANG_AR and normalize_lang(None) == LANG_AR)
check("i18n lang_name", lang_name("ar") == "العربية" and lang_name("en") == "English")
check("i18n buttons ar", t(LANG_AR, "btn_cancel") == "❌ إلغاء")
check("i18n buttons en", t(LANG_EN, "btn_cancel") == "❌ Cancel")
check("i18n err ar", "تسجيل" in t(LANG_AR, "err_login"))
check("i18n every key both langs", all({k[0] for k in _STRINGS if k[1] == key} == {LANG_AR, LANG_EN} for key in {k[1] for k in _STRINGS}))

# Every template must be VALID str.format syntax. Missing kwargs raise
# KeyError (expected — callers pass them); anything else (e.g. ValueError
# from a method call inside a format field) is a real bug.
_format_failures = []
for (lang, key), template in _STRINGS.items():
    try:
        template.format()
    except KeyError:
        pass  # needs kwargs — fine
    except Exception as exc:  # noqa: BLE001
        _format_failures.append((lang, key, str(exc)))
check("i18n all templates valid format", not _format_failures)
if _format_failures:
    print("FORMAT FAILURES:", _format_failures[:5])

# ── Rate limiter ──
rl = RateLimiter(max_events=2, window_seconds=10)
rl.is_limited(1)
rl.is_limited(1)
check("rate limiter trips", rl.is_limited(1) is True)

# ── Keyboards ──
kb = info_keyboard(has_qualities=True)
check("info keyboard buttons", len(kb.inline_keyboard) == 3)
kbw = info_keyboard(has_qualities=True, web_url="https://dl.example.com")
check("info keyboard web row", len(kbw.inline_keyboard) == 4)
check("oversize keyboard web row", len(oversize_keyboard(web_url="https://dl.example.com").inline_keyboard) == 4)
check("web offer keyboard", len(web_offer_keyboard("https://dl.example.com/?url=x").inline_keyboard) == 2)
qkb = quality_keyboard([2160, 1080, 720], page=0, num_pages=1, size_map={1080: "1.2 GB"})
check("quality keyboard", len(qkb.inline_keyboard) >= 3)
check("remove_keyboard empty", remove_keyboard().inline_keyboard == [])

# ── Admin panel keyboards (لوحة تحكم المدير) ──
from bot.database import Database as _Db

_panel_kb = admin_panel_keyboard()
check("panel main keyboard", len(_panel_kb.inline_keyboard) >= 5)
check("panel stats keyboard", len(panel_stats_keyboard().inline_keyboard) >= 2)
check("panel channels keyboard", len(panel_channels_keyboard(["@A", "@B"]).inline_keyboard) == 4)  # 2 del + add + back/close
check("panel language keyboard", len(panel_language_keyboard().inline_keyboard) >= 2)
_panel_cb = PanelCB(view="stats", action="open").pack()
check("panel cb round-trip", PanelCB.unpack(_panel_cb).view == "stats")
_lang_cb = LanguageCB(lang="en").pack()
check("language cb round-trip", LanguageCB.unpack(_lang_cb).lang == "en")
check("welcome keyboard", len(welcome_keyboard().inline_keyboard) == 1)

# ── Forced subscription (multi-channel; disabled path needs no bot) ──
fs_off = ForcedSubscription(_Db(Path(".") / "nope.db"), env_channels=[])
check("sub disabled", fs_off.enabled is False)
fs_on = ForcedSubscription(_Db(Path(".") / "nope.db"), env_channels=["@A", "@B"])
check("sub enabled multi", fs_on.enabled is True and fs_on.channels == ["@A", "@B"])
join_kb = fs_on.join_keyboard()
check("join kb per-channel rows", len(join_kb.inline_keyboard) == 3)  # @A, @B, I've joined
join_msg = fs_on.join_message()
check("join msg lists channels", "@A" in join_msg and "@B" in join_msg)
check("broadcast cancel kb", len(broadcast_cancel_keyboard().inline_keyboard) == 1)

# multi-channel env config parsing
from bot.config import Settings as _Settings

s_multi = _Settings(_env_file=None, BOT_TOKEN="t", force_channels="@X, @Y")
check("force_channels parsed", s_multi.all_force_channels == ["@X", "@Y"])
s_legacy = _Settings(_env_file=None, BOT_TOKEN="t", force_channel="@Old")
check("legacy force_channel", s_legacy.all_force_channels == ["@Old"])
s_web = _Settings(_env_file=None, BOT_TOKEN="t", webhook_url="https://x.example.com/webhook")
check("web_base derived", s_web.web_base == "https://x.example.com")
s_web2 = _Settings(_env_file=None, BOT_TOKEN="t", web_base_url="https://dl.example.com/")
check("web_base explicit", s_web2.web_base == "https://dl.example.com")
check("web max size bytes", s_web2.web_max_file_size_bytes == 2000 * 1024 * 1024)


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

    # Runtime channel management (DB-backed, used by /setchannel + panel)
    with tempfile.TemporaryDirectory() as tmp:
        cdb = Database(Path(tmp) / "chan.db")
        await cdb.connect()
        sub = ForcedSubscription(cdb, env_channels=["@EnvA"])
        await sub.refresh_runtime()
        check("runtime sub initial", sub.channels == ["@EnvA"])
        added = await sub.add_channel("@RuntimeB", 111)
        check("runtime add channel", added is True and sub.channels == ["@EnvA", "@RuntimeB"])
        dup = await sub.add_channel("@RuntimeB", 111)
        check("runtime dup rejected", dup is False)
        # env channels are protected from removal
        env_removed = await sub.remove_channel("@EnvA")
        check("env channel protected", env_removed is False and sub.channels == ["@EnvA", "@RuntimeB"])
        rt_removed = await sub.remove_channel("@RuntimeB")
        check("runtime channel removed", rt_removed is True and sub.channels == ["@EnvA"])
        # dedup when env + db overlap
        await sub.add_channel("@EnvA", 111)
        check("dedup overlap", sub.channels == ["@EnvA"])
        await cdb.close()

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
        # top_users for the admin panel
        await db.upsert_user(2, "bob", "Bob", None)
        await db.log_download(2, "https://y", "video", 720, 200, 120, True)
        await db.log_download(2, "https://z", "audio", None, 50, 60, True)
        top = await db.top_users(limit=5)
        check("top_users order", len(top) == 2 and top[0][0] == 2 and top[0][2] == 2)
        await db.remove_user(1)
        await db.remove_user(2)
        check("remove_user", await db.users_count() == 0)
        await db.close()

    # ── aiohttp app assembly (webhook + web site mount) ──
    from bot.main import build_aiohttp_app
    from bot.web.manager import WebDownloadManager
    from aiogram import Bot as AiogramBot
    from aiogram import Dispatcher as AiogramDispatcher

    class _MountFakeYtdlp:
        async def get_video_info(self, url: str) -> dict:
            return {"title": "T", "id": "v1", "formats": [], "thumbnails": []}

        async def download(self, *args, **kwargs):
            raise RuntimeError("no")

    with tempfile.TemporaryDirectory() as tmp:
        s3 = _Settings(_env_file=None, BOT_TOKEN="t", webhook_url="https://x.example.com/webhook")
        app, _secret = build_aiohttp_app(
            AiogramBot("123456:TESTTOKEN"),
            AiogramDispatcher(),
            Services(
                settings=s3, db=None, ytdlp=_MountFakeYtdlp(), stickers=None,
                queue=None, downloader=None, cleanup=None, subscription=None, broadcast=None,
                web=WebDownloadManager(s3, _MountFakeYtdlp()),
            ),
        )
        routes = {r.resource.canonical for r in app.router.routes() if r.resource}
        check("app routes include web site", "/" in routes and "/health" in routes and "/api/info" in routes)
        check("app routes include webhook", "/webhook" in routes)

    # ── Web download manager (shares the yt-dlp engine) ──
    from bot.web.manager import WebDownloadManager, _validate_url
    from bot.services.ytdlp import ProgressPayload
    from aiohttp import web as aiohttp_web

    _validate_url("https://youtu.be/x")
    _validate_url("http://example.com/v")
    try:
        _validate_url("file:///etc/passwd")
        check("web url rejects file scheme", False)
    except ValueError:
        check("web url rejects file scheme", True)

    class _FakeYtdlp:
        def __init__(self, out_path: Path) -> None:
            self.out_path = out_path

        async def get_video_info(self, url: str) -> dict:
            return dict(
                SAMPLE_INFO,
                id="vid123",
                title="Test Video",
                webpage_url=url,
                duration=65,
                thumbnails=[{"url": "https://x/t.jpg"}],
            )

        async def download(self, url, video_id, mode, height, channel, cancel_event, workdir):
            workdir.mkdir(parents=True, exist_ok=True)
            channel.push(ProgressPayload(status="downloading", downloaded_bytes=50, total_bytes=100, speed=1024.0, eta=3.0))
            channel.push(ProgressPayload(status="finished"))
            return self.out_path

    with tempfile.TemporaryDirectory() as tmp:
        s2 = _Settings(_env_file=None, BOT_TOKEN="t", temp_dir=Path(tmp))
        out = Path(tmp) / "done.mp4"
        out.write_bytes(b"x" * 100)
        wm = WebDownloadManager(s2, _FakeYtdlp(out))

        info = await wm.fetch_info("https://youtu.be/abc")
        check("web fetch_info curated", info["title"] == "Test Video" and info["has_video"] is True and len(info["qualities"]) == 2)
        cached = await wm.fetch_info("https://youtu.be/abc")
        check("web info cache hit", cached is info)

        job = wm.create_job("https://youtu.be/abc", "video", None)
        check("web job created", job is not None and job.mode == "video")
        await wm.run_job(job)
        st = wm.status(job.id)
        check("web job done", st is not None and st["state"] == "done" and st["filename"] == "done.mp4" and st["progress"] == 100.0)
        fr = await wm.file_response(job.id)
        check("web file response", fr is not None and isinstance(fr, aiohttp_web.FileResponse))

        aj = wm.create_job("https://youtu.be/abc", "audio", 1080)
        check("web audio job forces height None", aj is not None and aj.height is None)
        await wm.run_job(aj)
        check("web audio job done", wm.status(aj.id)["state"] == "done")

        # concurrency cap
        extra = sum(1 for _ in range(s2.web_max_concurrent_jobs) if wm.create_job("https://x.com/a", "video", None))
        check("web capacity fills", extra == s2.web_max_concurrent_jobs)
        check("web capacity blocks", wm.create_job("https://x.com/b", "video", None) is None)

        check("web cancel missing job", wm.cancel("nope") is False)
        check("web status missing job", wm.status("nope") is None)

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
