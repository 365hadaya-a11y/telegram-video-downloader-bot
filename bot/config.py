"""Application configuration loaded from environment variables (``.env``).

All tunables live here. See ``.env.example`` for a fully commented copy.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration.

    Values can come from environment variables or a ``.env`` file
    (both supported by pydantic-settings).
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Core ──────────────────────────────────────────────────────
    bot_token: str = Field(..., description="Telegram bot token from @BotFather")
    admin_ids: list[int] = Field(default_factory=list, description="Admin Telegram user IDs")
    # "ar" (default) or "en" — the bot is bilingual; users can switch via /language
    default_language: str = "ar"

    # ── Storage ───────────────────────────────────────────────────
    db_path: Path = BASE_DIR / "data" / "bot.db"
    temp_dir: Path = BASE_DIR / "temp"
    log_dir: Path = BASE_DIR / "logs"
    log_level: str = "INFO"

    # ── Downloads ─────────────────────────────────────────────────
    max_file_size_mb: int = 2000
    download_workers: int = 2
    progress_update_seconds: float = 2.5
    upload_progress_seconds: float = 3.5
    audio_bitrate: int = 192
    max_quality_choices: int = 8
    daily_download_limit: int = 20
    retry_attempts: int = 3
    retry_backoff_seconds: float = 2.0
    choice_timeout_seconds: int = 150
    ffmpeg_location: str | None = None
    proxy: str | None = None
    cookies_file: str | None = None

    # ── Rate limiting ─────────────────────────────────────────────
    rate_limit_max: int = 4
    rate_limit_window_seconds: float = 3.0
    rate_limit_warn_cooldown_seconds: float = 20.0

    # ── Cleanup ───────────────────────────────────────────────────
    cleanup_interval_minutes: int = 30
    cleanup_age_hours: int = 6

    # ── Forced channel subscription ────────────────────────────────
    # e.g. "@MyAnnouncements" or "-1001234567890". Empty disables the gate.
    force_channel: str | None = None

    # ── Webhook (production / Koyeb) ───────────────────────────────
    # Polling is the default for local dev. Set WEBHOOK_MODE=true on a
    # hosted platform (Koyeb/Railway/Render…) so Telegram pushes updates
    # to a public HTTPS URL instead of long-polling.
    webhook_mode: bool = False
    webhook_url: str | None = None  # full public URL, e.g. https://app-org.koyeb.app/webhook
    webhook_secret: str | None = None  # secret_token for Telegram (auto-generated if empty)
    webhook_path: str = "/webhook"
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8080

    # ── Stickers (optional) ───────────────────────────────────────
    sticker_set_name: str | None = None
    sticker_welcome_file_id: str | None = None
    sticker_loading_file_id: str | None = None
    sticker_downloading_file_id: str | None = None
    sticker_uploading_file_id: str | None = None
    sticker_success_file_id: str | None = None
    sticker_error_file_id: str | None = None
    sticker_celebration_file_id: str | None = None

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> list[int]:
        """Accept either JSON (``[1, 2]``) or comma-separated (``1, 2``)."""
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                return json.loads(text)
            return [int(part) for part in text.split(",") if part.strip()]
        return value  # type: ignore[return-value]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def load_settings() -> Settings:
    """Load settings once per process (cached)."""
    return Settings()
