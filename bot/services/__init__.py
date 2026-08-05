"""Service registry — a single object holding every shared service.

Handlers receive this via ``services`` (injected through workflow data).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings
from ..database.db import Database
from .broadcast import BroadcastService
from .cleanup import CleanupService
from .downloader import DownloadService
from .queue import DownloadQueue
from .stickers import StickerService
from .subscription import ForcedSubscription
from .ytdlp import YtDlpService


@dataclass
class Services:
    settings: Settings
    db: Database
    ytdlp: YtDlpService
    stickers: StickerService
    queue: DownloadQueue
    downloader: DownloadService
    cleanup: CleanupService
    subscription: ForcedSubscription
    broadcast: BroadcastService


__all__ = ["Services"]
