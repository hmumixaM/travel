from __future__ import annotations

import logging
import os
from datetime import date
from typing import Optional

import httpx

from travel_common import RateLimitedQueue
from travel_seats.models import (
    AvailabilityResponse,
    Route,
    SearchResponse,
    TripDetails,
)

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

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
    ) -> dict:
        await self._limiter.acquire()
        url = f"{self.base_url}/{endpoint}"
        log.info("HTTP %s %s params=%s", method, url, params)
        resp = await self._http.request(method, url, params=params)
        log.info("HTTP %s %s -> %d (%d bytes)", method, url, resp.status_code, len(resp.content))
        resp.raise_for_status()
        return resp.json()

    async def search(
        self,
        origin_airport: str,
        destination_airport: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        cursor: Optional[int] = None,
        take: Optional[int] = None,
        order_by: Optional[str] = None,
        skip: Optional[int] = None,
        include_trips: Optional[bool] = True,
        only_direct_flights: Optional[bool] = None,
        carriers: Optional[str] = None,
        include_filtered: Optional[bool] = None,
        sources: Optional[str] = None,
        minify_trips: Optional[bool] = None,
        cabins: Optional[str] = None,
    ) -> SearchResponse:
        payload = {
            "origin_airport": origin_airport,
            "destination_airport": destination_airport,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "cursor": cursor,
            "take": take,
            "order_by": order_by,
            "skip": skip,
            "include_trips": include_trips,
            "only_direct_flights": only_direct_flights,
            "carriers": carriers,
            "include_filtered": include_filtered,
            "sources": sources,
            "minify_trips": minify_trips,
            "cabins": cabins,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        data = await self._request("GET", "search", params=payload)
        result = SearchResponse(**data)
        log.info("Search %s->%s returned %d results", origin_airport, destination_airport, result.count)
        return result

    async def get_routes(self, source: str) -> list[Route]:
        data = await self._request("GET", "routes", params={"source": source})
        routes = [Route(**item) for item in data]
        log.info("Routes source=%s returned %d routes", source, len(routes))
        return routes

    async def get_trip_by_id(self, trip_id: str) -> TripDetails:
        log.info("Getting trip id=%s", trip_id)
        data = await self._request("GET", f"trips/{trip_id}")
        if "data" in data and data["data"]:
            return TripDetails(**data["data"][0])
        return TripDetails(**data)

    async def get_bulk_availability(
        self,
        source: str,
        cabin: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        origin_region: Optional[str] = None,
        destination_region: Optional[str] = None,
        take: Optional[int] = None,
        cursor: Optional[int] = None,
        skip: Optional[int] = None,
        include_filtered: Optional[bool] = None,
    ) -> AvailabilityResponse:
        params = {
            "source": source,
            "cabin": cabin,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "origin_region": origin_region,
            "destination_region": destination_region,
            "take": take,
            "cursor": cursor,
            "skip": skip,
            "include_filtered": include_filtered,
        }
        params = {k: v for k, v in params.items() if v is not None}
        data = await self._request("GET", "availability", params=params)
        result = AvailabilityResponse(**data)
        log.info("Bulk availability source=%s returned %d results", source, result.count)
        return result
