from __future__ import annotations

import asyncio
import time


class RateLimitedQueue:
    """Async token-bucket rate limiter with FIFO request queuing.

    Concurrent callers that exceed the rate are queued and served in order.
    """

    def __init__(self, max_per_second: float) -> None:
        self._min_interval = 1.0 / max_per_second
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
