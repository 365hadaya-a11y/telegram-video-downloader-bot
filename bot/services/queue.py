"""Global download queue — limits how many heavy downloads run at once.

When all workers are busy, new downloads wait and show their queue
position to the user.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


class DownloadQueue:
    """A semaphore-based FIFO queue with position tracking."""

    def __init__(self, workers: int) -> None:
        self._workers = workers
        self._semaphore = asyncio.Semaphore(workers)
        self._waiting: list[str] = []
        self._active: set[str] = set()

    @property
    def waiting_count(self) -> int:
        return len(self._waiting)

    @property
    def active_count(self) -> int:
        return len(self._active)

    def register(self) -> str:
        """Claim a spot in the queue and return a ticket id."""
        ticket = uuid.uuid4().hex[:8]
        self._waiting.append(ticket)
        return ticket

    def position(self, ticket: str) -> int:
        """1-based position in the waiting queue (0 if already running)."""
        try:
            return self._waiting.index(ticket) + 1
        except ValueError:
            return 0

    async def acquire(self, ticket: str) -> None:
        """Wait for a free worker, then mark the ticket as active."""
        await self._semaphore.acquire()
        if ticket in self._waiting:
            self._waiting.remove(ticket)
        self._active.add(ticket)

    def release(self, ticket: str) -> None:
        """Free the worker slot."""
        self._active.discard(ticket)
        self._semaphore.release()
