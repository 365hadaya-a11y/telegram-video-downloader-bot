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
| 🔒 **Forced channel** | Mandatory channel subscription gate before using the bot (admins exempt) |
| 🎨 **Animated stickers** | Welcome / loading / downloading / uploading / success / error / celebration |
| 🐳 **Docker-ready** | One command to deploy |
| 🌐 **Bilingual** | Full **العربية + English** translations, per-user `/language` picker |

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
| `/stats` | admins | Users, downloads, queue, temp usage |
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
│   └── db.py            # aiosqlite: users, stickers, download log
├── handlers/
│   ├── start.py         # /start /help /cancel /language
│   ├── download.py      # URL messages, hints, unknown commands
│   ├── callbacks.py     # inline keyboard decisions
│   └── admin.py         # /stats /setsticker /resetsticker /stickers
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
│   └── cleanup.py       # temp sweeper + log pruning
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
The Telegram Bot API limits uploads to 50 MB unless you run a **local Bot API server**. Set `MAX_FILE_SIZE_MB=50`, or deploy a local server for 2 GB uploads.

**Is the upload progress real?**
The Bot API exposes **no upload progress**, so the bot plays a polished animation scaled to the file size while it uploads. Download progress, however, is 100% real (driven by yt-dlp hooks).

**Does it support playlists?**
Links are treated as single videos (`noplaylist`). Turn it off in `YtDlpService` if you want playlist support.

**Age-restricted / private videos?**
Provide `COOKIES_FILE` (exported from your browser) and `PROXY` if needed.

**The bot doesn't respond in my group.**
It's designed for private chats (like all premium downloader bots). Use it in DM.

---

## 🔒 Forced Channel Subscription (الاشتراك الإجباري)

Set `FORCE_CHANNEL` in `.env` (e.g. `@MyAnnouncements` or `-1001234567890`) and the bot will
require every user to join that channel before downloading:

```text
/start
  │
  ▼ 🔒 Channel subscription required
  ▼ [🔗 Join Channel] [✅ I've Joined]
  │
  ▼ ✅ Access granted! → send your video link 🎬
```

- Admins (from `ADMIN_IDS`) are always exempt.
- The gate is a no-op when `FORCE_CHANNEL` is empty.
- If the channel handle is wrong, the bot logs a warning and skips checks (it never bricks itself).
- 💡 Use a public **@username** for `FORCE_CHANNEL` so the join card shows a tappable **Join Channel** button (numeric channel IDs can't be turned into links).

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
