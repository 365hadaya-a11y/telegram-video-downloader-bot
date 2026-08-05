"""Shared formatting helpers: sizes, durations, progress bars, filenames, URLs."""

from __future__ import annotations

import re

_UNITS = ("B", "KB", "MB", "GB", "TB")


def format_size(num_bytes: float | int | None) -> str:
    """Human-readable file size, e.g. ``12.4 MB``."""
    if num_bytes is None or num_bytes < 0:
        return "Unknown"
    size = float(num_bytes)
    unit = _UNITS[0]
    for unit in _UNITS:
        if size < 1024 or unit == _UNITS[-1]:
            break
        size /= 1024
    return f"{size:,.1f} {unit}"


def format_speed(bytes_per_sec: float | None) -> str:
    """Human-readable transfer speed, e.g. ``4.2 MB/s``."""
    if bytes_per_sec is None or bytes_per_sec < 0:
        return "?/s"
    return f"{format_size(bytes_per_sec)}/s"


def format_duration(seconds: float | int | None) -> str:
    """Format seconds as ``H:MM:SS`` or ``M:SS``."""
    if seconds is None or seconds <= 0:
        return "Unknown"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def progress_bar(percent: float, width: int = 12) -> str:
    """Render a terminal-style progress bar, e.g. ``████████░░ 80%``."""
    percent = max(0.0, min(100.0, float(percent)))
    filled = int(round(percent / 100 * width))
    return "█" * filled + "░" * (width - filled)


def clean_filename(title: str, max_len: int = 90) -> str:
    """Turn an arbitrary title into a safe, short filename."""
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", title).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:max_len].strip() or "video"


def extract_url(text: str) -> str | None:
    """Return the first http(s) URL found in ``text``, if any."""
    match = re.search(r"https?://[^\s<>\"']+", text)
    return match.group(0) if match else None
