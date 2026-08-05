"""In-memory sliding-window rate limiter."""

from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    """Sliding-window limiter keyed by user id, with a warn cooldown."""

    def __init__(self, max_events: int, window_seconds: float, warn_cooldown_seconds: float = 20.0) -> None:
        self.max_events = max_events
        self.window = window_seconds
        self.warn_cooldown = warn_cooldown_seconds
        self._events: dict[int, deque[float]] = defaultdict(deque)
        self._last_warn: dict[int, float] = {}

    def is_limited(self, key: int) -> bool:
        """Record one event for ``key`` and report whether it exceeds the limit."""
        now = time.monotonic()
        events = self._events[key]
        while events and now - events[0] > self.window:
            events.popleft()
        events.append(now)
        return len(events) > self.max_events

    def can_warn(self, key: int) -> bool:
        now = time.monotonic()
        if now - self._last_warn.get(key, 0.0) > self.warn_cooldown:
            self._last_warn[key] = now
            return True
        return False
