<div align="center">

# 💎 Premium Video Downloader Bot

**A polished, production-ready Telegram bot that downloads videos from 1000+ websites — with a premium animated UX.**

> 🌐 **Bilingual** — fully translated into **العربية (Arabic)** and **English**. Users switch anytime with `/language`; the choice is remembered per user.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red?style=for-the-badge)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## ✨ Highlights

| | |
|---|---|
| 🎬 **1000+ sites** | Powered by **yt-dlp** — YouTube, TikTok, Instagram, X, Vimeo, Reddit… |
| 🎥 **Best quality** | Merges the highest-quality video + audio streams with **FFmpeg** |
| 📺 **Choose quality** | Paged resolution picker (up to 8K) with per-quality file sizes |
| 🎧 **Audio only** | One-tap MP3 extraction at your chosen bitrate |
| 📊 **Real-time progress** | Animated `████████░░ 80%` bar, speed & ETA, refreshed every few seconds |
| 💬 **Single-card UX** | The whole flow lives on *one* editable message — no spam |
| 🧵 **Download queue** | Concurrent workers with a visible queue position |
| 👥 **Multi-user** | Per-user sessions, SQLite-backed stats, daily limits |
| 🚦 **Rate limiting** | Sliding-window throttle + per-user daily download cap |
| 🔁 **Auto-retry** | Exponential back-off on network errors (info + download) |
| 🗑️ **Self-cleaning** | Per-download temp folders + periodic sweeper + log pruning |
| 📣 **Broadcast** | One-tap admin announcements (text or media) to every user, with live progress & stop button |
| 🛠️ **Admin panel** | Interactive `/panel` — stats, top users, broadcast, stickers, channels & settings in one editable message |
| 🔒 **Forced channels** | Mandatory subscription gate to **multiple** channels (admins exempt); add/remove live via `/setchannel` |
| 🎨 **Animated stickers** | Welcome / loading / downloading / uploading / success / error / celebration |
| 🐳 **Docker-ready** | One command to deploy |
| 🌐 **Bilingual** | Full **العربية + English** translations, per-user `/language` picker |
| 🖥️ **Web download site** | A premium animated website served from the **same public URL** as the bot — same yt-dlp engine, same storage |

---

## 🎬 The User Flow

```
/start
  │
  ▼  👋 Welcome sticker
  ▼  ✨ Beautiful welcome message
  │
Send a video URL
  │
  ▼  ⏳ Loading sticker
  ▼  🔍 Fetching video information…  (auto-retry on network errors)
  │
  ▼  🎬 Info card — title · duration · size · max quality · thumbnail
  │
  ┌──────────────┬──────────────────┐
  │ 🎥 Best      │ 📺 Choose        │
  │    Quality   │    Quality       │
  ├──────────────┴──────────────────┤
  │ 🎵 Audio Only        ❌ Cancel  │
  └─────────────────────────────────┘
  │
  ▼  ⬇️ Downloading sticker
  ▼  ⏳ In download queue… position #2   (when workers are busy)
  ▼  ⬇️ Downloading…  ████████░░ 80%  ⚡ 4.2 MB/s · ETA 00:12
  ▼  🎬 Processing… (FFmpeg merge)
  ▼  📤 Uploading to Telegram…  █████████░ 90%
  │
  ▼  🎉 Celebration sticker
  ▼  ✅ "Delivered!" card + the video file with a rich caption
```

---

## 🚀 Quick Start (Local)

### 0. Prerequisites

- **Python 3.12**
- **[FFmpeg](https://ffmpeg.org/download.html)** — required for merging video+audio and MP3 extraction
- **Deno** *(recommended)* — JS runtime used by yt-dlp for YouTube extraction; installed automatically in the Docker image
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Install

```bash
git clone <your-repo-url> && cd BOTDAOWNLOD
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# edit .env — at minimum set BOT_TOKEN
```

### 3. Run

```bash
python -m bot
```

That's it. Open your bot, press **Start**, send a URL, and watch the magic. ✨

---

## 🐳 Quick Start (Docker)

```bash
cp .env.example .env   # set BOT_TOKEN
docker compose up -d --build
```

Data persists in `./data`, `./temp` and `./logs` (mounted volumes).

---

## ⚙️ Configuration

All settings live in `.env` (see [`.env.example`](.env.example) for full comments).

| Variable | Default | Description |
|---|---|---|
| `BOT_TOKEN` | — | **Required.** Token from @BotFather |
| `ADMIN_IDS` | `[]` | JSON list, e.g. `[111111111, 222222222]` |
| `DEFAULT_LANGUAGE` | `ar` | Default bot language: `ar` (العربية) or `en` (English) |
| `MAX_FILE_SIZE_MB` | `2000` | Download size limit. ⚠️ Standard Bot API caps uploads at **50 MB** — use a [local Bot API server](https://core.telegram.org/bots/api#using-a-local-bot-api-server) for bigger files |
| `DOWNLOAD_WORKERS` | `2` | Concurrent downloads (queue depth) |
| `PROGRESS_UPDATE_SECONDS` | `2.5` | Progress bar refresh interval |
| `UPLOAD_PROGRESS_SECONDS` | `3.5` | Duration of the upload animation |
| `AUDIO_BITRATE` | `192` | MP3 bitrate for audio-only |
| `MAX_QUALITY_CHOICES` | `8` | Resolutions offered in the picker |
| `DAILY_DOWNLOAD_LIMIT` | `20` | Per-user daily cap |
| `RETRY_ATTEMPTS` / `RETRY_BACKOFF_SECONDS` | `3` / `2.0` | Network retry policy |
| `FFMPEG_LOCATION` | auto | Path to FFmpeg binary |
| `PROXY` / `COOKIES_FILE` | — | For proxied or private/age-restricted videos |
| `RATE_LIMIT_MAX` / `RATE_LIMIT_WINDOW_SECONDS` | `4` / `3.0` | Message throttle |
| `CLEANUP_*` | 30 min / 6 h | Temp file sweeper |
| `FORCE_CHANNEL` | — | Channel users must join first, e.g. `@MyAnnouncements` (see **Forced subscription**) |
| `WEB_ENABLED` | `true` | Serve the web download site from the same server |
| `WEB_BASE_URL` | derived | Public base of the site (auto-derived from `WEBHOOK_URL` if empty) |
| `WEB_MAX_FILE_SIZE_MB` | `2000` | Size cap for website downloads (bigger than Telegram's 50 MB) |
| `WEB_JOB_TTL_MINUTES` | `120` | Website download files are auto-deleted after this |
| `WEB_MAX_CONCURRENT_JOBS` | `3` | Simultaneous downloads through the website |
| `BOT_USERNAME` | — | Shows "open in Telegram" links on the website |
| `STICKER_*` / `STICKER_SET_NAME` | — | See **Stickers** below |

---

## 🎨 Setting Up Animated Stickers

Every flow step can show a beautiful animated sticker. Three ways to configure:

1. **`STICKER_SET_NAME`** — point to any public animated sticker set and the bot auto-maps emojis (👋 ⏳ ⬇️ 📤 ✅ ❌ 🎉) to stickers in that set.
2. **`STICKER_<KEY>_FILE_ID`** — hard-code individual `file_id`s (takes priority).
3. **Admin commands** — send a sticker, reply with `/setsticker <key>` and it's stored in SQLite.

```text
Keys: welcome · loading · downloading · uploading · success · error · celebration
```

No stickers configured? No problem — the bot gracefully falls back to premium emojis everywhere.

---

## 🛠️ Commands

| Command | Access | Description |
|---|---|---|
| `/start` | everyone | Welcome + features |
| `/help` | everyone | Usage guide |
| `/language` | everyone | Switch between العربية and English 🌐 |
| `/cancel` | everyone | Cancel the active download |
| `/broadcast <text>` | admins | Announce text — or reply to a photo/video/file to announce media — to every user (live progress + 🛑 stop) |
| `/panel` | admins | 🛠️ Interactive admin control panel (stats, users, broadcast, stickers, channels, settings, language) |
| `/stats` | admins | Users, downloads, queue, temp usage |
| `/setchannel @channel` | admins | Add a forced-subscription channel (live, no restart) |
| `/delchannel @channel` | admins | Remove a forced-subscription channel (env channels are protected) |
| `/setsticker <key>` | admins | Assign a sticker (reply to a sticker) |
| `/resetsticker <key>` | admins | Unset a sticker |
| `/stickers` | admins | Show the sticker mapping |

---

## 🧱 Architecture

```
bot/
├── __main__.py          # python -m bot entry point
├── main.py              # bootstrap & dependency wiring
├── config.py            # pydantic-settings (.env) configuration
├── database/
│   └── db.py            # aiosqlite: users, stickers, channels, download log
├── handlers/
│   ├── start.py         # /start /help /cancel /language
│   ├── download.py      # URL messages, hints, unknown commands
│   ├── callbacks.py     # inline keyboard decisions
│   ├── admin.py         # /stats /setsticker /setchannel /broadcast…
│   └── panel.py         # 🛠️ interactive admin control panel (/panel)
├── keyboards/
│   └── inline.py        # callback factory + stylish keyboards
├── middlewares/
│   └── throttling.py    # sliding-window rate limiter
├── services/
│   ├── ytdlp.py         # async yt-dlp facade + progress channel
│   ├── downloader.py    # the interactive per-user flow (the heart)
│   ├── queue.py         # worker-pool download queue
│   ├── rate_limiter.py  # in-memory sliding window
│   ├── stickers.py      # env → DB → sticker-set resolution
│   ├── subscription.py  # multi-channel forced-subscription gate
│   ├── broadcast.py     # 📣 announcements to every user
│   └── cleanup.py       # temp sweeper + log pruning
├── web/
│   ├── manager.py       # web download jobs (shares the yt-dlp engine)
│   ├── server.py        # aiohttp routes mounted on the webhook server
│   └── static/
│       └── index.html   # 🖥️ premium bilingual animated download page
└── utils/
    ├── formatters.py    # sizes, durations, progress bars, URLs
    ├── i18n.py          # bilingual strings (العربية + English)
    ├── logger.py        # rotating file + console logging
    └── retry.py         # async retry with exponential back-off
```

**Design notes**

- **One card per user** — the info card message is *edited* through every stage (info → queue → download → upload → done), so the chat stays tidy.
- **Thread-safe progress** — yt-dlp hooks run in worker threads; progress flows into the event loop via a `queue.Queue` bridge, edited on a throttled timer.
- **Per-session temp dirs** — `temp/job_<uuid>/` isolates concurrent downloads of the same video and is deleted in `finally`.
- **Cancel everywhere** — a `threading.Event` aborts yt-dlp mid-chunk; the ❌ button and `/cancel` both work at every stage.

---

## ❓ FAQ

**Why is my file over 50 MB rejected?**
The Telegram Bot API limits uploads to 50 MB unless you run a **local Bot API server**. With the web site enabled, files that exceed the limit are **not lost** — the bot sends you a link to download them from `https://<your-app-url>/` (which supports up to `WEB_MAX_FILE_SIZE_MB`).

**Is the upload progress real?**
The Bot API exposes **no upload progress**, so the bot plays a polished animation scaled to the file size while it uploads. Download progress, however, is 100% real (driven by yt-dlp hooks).

**Does it support playlists?**
Links are treated as single videos (`noplaylist`). Turn it off in `YtDlpService` if you want playlist support.

**Age-restricted / private videos?**
Provide `COOKIES_FILE` (exported from your browser) and `PROXY` if needed.

**The bot doesn't respond in my group.**
It's designed for private chats (like all premium downloader bots). Use it in DM.

---

## 🔒 Forced Channel Subscription (الاشتراك الإجباري) — multi-channel

Set `FORCE_CHANNELS` in `.env` (comma-separated or JSON) and the bot will require every
user to join **all** of those channels before downloading:

```env
FORCE_CHANNELS=@MyAnnouncements, @SecondChannel
# legacy single-channel option still works:  FORCE_CHANNEL=@MyAnnouncements
```

```text
/start
  │
  ▼ 🔒 Channel subscription required
  ▼ 1. Join @MyAnnouncements  [🔗 Join @MyAnnouncements]
  ▼ 2. Join @SecondChannel    [🔗 Join @SecondChannel]
  ▼                              [✅ I've Joined]
  │
  ▼ ✅ Access granted! → send your video link 🎬
```

- **Runtime management** — the owner can add channels live with `/setchannel @channel`
  and remove them with `/delchannel @channel` (or from the admin panel). These are stored
  in SQLite — no restart, no `.env` edits. Channels from the env config are protected
  from removal.
- Admins (from `ADMIN_IDS`) are always exempt.
- The gate is a no-op when no channels are configured.
- If a channel handle is wrong, the bot logs a warning and skips that channel (it never bricks itself).
- 💡 Use public **@usernames** so the join card shows tappable buttons (numeric channel IDs can't be turned into links).

## 🛠️ Admin Control Panel (لوحة تحكم المدير)

The owner gets an interactive panel — one editable message, no command spam:

```text
/panel
  │
  ▼ 🛠️ Admin Control Panel
  ┌────────────┬────────────┐
  │ 📊 Stats   │ 👥 Users   │
  ├────────────┼────────────┤
  │ 📣 Broadcast│ 🎨 Stickers│
  ├────────────┼────────────┤
  │ 🔒 Channels│ ⚙️ Settings │
  ├────────────┴────────────┤
  │ 🌐 Language   ❌ Close  │
  └─────────────────────────┘
```

- **Stats** — users, downloads, queue, temp usage (🔄 refresh button).
- **Users** — total users + top downloaders ranking.
- **Broadcast** — quick reference for `/broadcast`.
- **Stickers** — live mapping status.
- **Channels** — current forced channels, add/remove.
- **Settings** — key configuration overview.
- **Language** — the owner's own bot language.

## 🖥️ Web Download Site (موقع التحميل)

A premium, animated download website is served from the **same public URL** as the
bot's webhook — no extra service, no extra cost. It reuses the **same yt-dlp
engine and temp storage** as the bot.

> Open **`https://<your-app-url>/`** in any browser. 🌐

```text
User pastes a URL
  │
  ▼ 🔍 /api/info → title · channel · duration · sizes · thumbnail
  │
  ▼ 👑 Best Quality · 📺 2160p / 1440p / 1080p / … · 🎵 Audio Only
  │
  ▼ ⬇️ POST /api/download → { job_id }
  │
  ▼ ⬇️ Animated progress bar (real %) · speed · ETA · ❌ cancel
  │
  ▼ 🎉 Done → download straight to disk (up to WEB_MAX_FILE_SIZE_MB)
```

**How it's linked to the bot**

- The info card now carries a **🌐 موقع التحميل** button (opens the site with your
  video preloaded).
- When a finished file **exceeds Telegram's 50 MB limit**, the bot hands you a
  direct link to grab it from the website instead of failing.
- The welcome message mentions the site, and the site has an **"open in Telegram"**
  button back to the bot (set `BOT_USERNAME`).
- The whole page is **RTL Arabic by default** with a one-tap English toggle,
  localStorage download history, and a dark glassmorphism design with animated orbs.

**HTTP API** (used by the page; same origin, no auth):

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | The download page (RTL العربية / English) |
| `/health` | GET | `ok` — platform health checks |
| `/d/{job_id}` | GET | Deep link straight to a finished download |
| `/api/info?url=…` | GET | Curated video info (cached, rate-limited per IP) |
| `/api/download` | POST | Start a job → `{job_id}` (409 when busy) |
| `/api/progress/{job_id}` | GET | Live download state (polled by the page) |
| `/api/cancel/{job_id}` | POST | Cancel an active job |
| `/api/file/{job_id}` | GET | Stream the finished file (auto-deleted after TTL) |

## 📣 Broadcast Announcements (النشرة الإعلانية)

Admins can announce to every registered user with one command:

```text
/broadcast Hello everyone! 👋          # text (HTML supported)
/broadcast  (reply to a photo/video)   # media announcement
```

A live status card shows **sent / failed / blocked** counts while it runs,
with a 🛑 button to stop. Users who blocked the bot are detected and removed
from the database automatically.

## ⚖️ Disclaimer

This project is for **personal and educational use**. Respect copyright and the terms of service of the websites you download from. The authors are not responsible for misuse.

---

## 📄 License

MIT — do whatever you like, just keep the copyright notice. 💎
