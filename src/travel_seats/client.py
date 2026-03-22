from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from travel_common import RateLimitedQueue

log = logging.getLogger(__name__)

SEATS_RATE_LIMIT = float(os.environ.get("SEATS_RATE_LIMIT", "1.0"))


class SeatsAeroClient:
    def __init__(self) -> None:
        api_key = os.environ["SEATS_AERO_API_KEY"]
        self.base_url = "https://seats.aero/partnerapi"
        self._http = httpx.AsyncClient(
            headers={"Partner-Authorization": api_key},
            timeout=30.0,
        )
        self._limiter = RateLimitedQueue(SEATS_RATE_LIMIT, name="seats.aero")
        log.info("SeatsAeroClient ready (base_url=%s, rate=%.1f/s)", self.base_url, SEATS_RATE_LIMIT)

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        await self._limiter.acquire()
        url = f"{self.base_url}/{endpoint}"
        filtered = {k: v for k, v in (params or {}).items() if v is not None}
        log.info("GET %s params=%s", url, filtered)
        resp = await self._http.get(url, params=filtered)
        log.info("GET %s -> %d (%d bytes)", url, resp.status_code, len(resp.content))
        resp.raise_for_status()
        return resp.json()

    async def search(self, params: dict[str, Any]) -> dict:
        return await self._get("search", params)
