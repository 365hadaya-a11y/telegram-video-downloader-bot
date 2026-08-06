"""Handlers package — one router per concern."""

from .admin import router as admin_router
from .callbacks import router as callbacks_router
from .download import router as download_router
from .panel import router as panel_router
from .start import router as start_router

__all__ = ["admin_router", "callbacks_router", "download_router", "panel_router", "start_router"]
