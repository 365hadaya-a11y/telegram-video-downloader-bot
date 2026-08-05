# 🚀 Deploying to Koyeb

This guide documents the exact steps to run the bot on [Koyeb](https://koyeb.com) using
the Koyeb CLI. The bot runs in **webhook mode** there: Telegram pushes updates to a
public HTTPS URL, which keeps the free-tier instance awake and gives us a health
check + public URL.

## Prerequisites

- A GitHub account and a **Personal Access Token** (classic, scope: `repo`):
  https://github.com/settings/tokens
- A Koyeb account and an **API token**:
  https://app.koyeb.com/account/api

## 1. Push the code to GitHub

```bash
git init -b main
git add .
git commit -m "Premium Telegram video downloader bot"
gh auth login --with-token <<< "GITHUB_PAT"
gh repo create telegram-video-downloader-bot --public --source=. --push
```

## 2. Install the Koyeb CLI

```bash
# Windows (Git Bash): download from GitHub releases
curl -sL -o koyeb.zip https://github.com/koyeb/koyeb-cli/releases/download/v5.10.2/koyeb-cli_5.10.2_windows_amd64.zip
unzip koyeb.zip -d koyeb_tmp && cp koyeb_tmp/bin/koyeb.exe ~/.local/bin/
# macOS / Linux: curl -fsSL https://install.koyeb.com/ | sh
```

## 3. Authenticate

```bash
export KOYEB_TOKEN=<your-koyeb-api-token>
```

## 4. Create the app

```bash
koyeb app create video-downloader-bot
```

## 5. Get the app's public domain

```bash
koyeb app get video-downloader-bot          # → https://video-downloader-bot-<org>.koyeb.app
```

## 6. Create the service (Docker build, webhook, port 8080, sleep disabled)

```bash
koyeb service create video-downloader-bot/bot \
  --git https://github.com/<user>/telegram-video-downloader-bot \
  --git-branch main \
  --git-builder docker \
  --git-docker-dockerfile Dockerfile \
  --git-docker-command "python -m bot" \
  --instance-type nano \
  --regions fra \
  --ports 8080:http \
  --routes /:8080 \
  --light-sleep-delay 0 \
  --deep-sleep-delay 0 \
  --env BOT_TOKEN=<token> \
  --env ADMIN_IDS=[7454825548] \
  --env WEBHOOK_MODE=true \
  --env WEBHOOK_URL=https://video-downloader-bot-<org>.koyeb.app/webhook \
  --env WEBHOOK_SECRET=<random-secret> \
  --env MAX_FILE_SIZE_MB=50 \
  --env LOG_LEVEL=INFO \
  --wait
```

Notes:

- `--git-builder docker` → builds via `Dockerfile` (installs FFmpeg + pip deps).
- `--git-docker-command "python -m bot"` → the Run Command.
- `--light-sleep-delay 0 --deep-sleep-delay 0` → keeps the bot running 24/7.
- `MAX_FILE_SIZE_MB=50` → the Telegram Bot API hard limit (no local API server here).

## 7. Monitor

```bash
koyeb deployment list video-downloader-bot/bot
koyeb logs video-downloader-bot/bot --type build     # build logs
koyeb logs video-downloader-bot/bot --type runtime   # runtime logs
```

The bot logs `Webhook registered: <url>` when Telegram accepts the webhook.

## 8. Redeploy after changes

Pushing to `main` auto-redeploys. Or force manually:

```bash
koyeb service redeploy video-downloader-bot/bot
```

## 9. Verify

```bash
curl https://video-downloader-bot-<org>.koyeb.app/          # → ok
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"   # url == WEBHOOK_URL, no pending errors
```

Then message the bot — `/start` should reply with the welcome card.
