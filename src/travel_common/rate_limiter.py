from __future__ import annotations

import asyncio
import logging
import time

log = logging.getLogger(__name__)


class RateLimitedQueue:
    """Async token-bucket rate limiter with FIFO request queuing.

    Concurrent callers that exceed the rate are queued and served in order.
    """

    def __init__(self, max_per_second: float, name: str = "") -> None:
        self._min_interval = 1.0 / max_per_second
        self._last_call = 0.0
        self._lock = asyncio.Lock()
        self._name = name or "default"
        self._pending = 0
        log.info("Rate limiter [%s] initialized: %.2f req/s (interval=%.3fs)", self._name, max_per_second, self._min_interval)

    async def acquire(self) -> None:
        self._pending += 1
        async with self._lock:
            self._pending -= 1
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_call)
            if wait > 0:
                log.debug("Rate limiter [%s] throttling %.3fs (pending=%d)", self._name, wait, self._pending)
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
