from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from travel_seats.server_core import get_client, mcp

log = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    origin_airport: str = Field(
        ...,
        description="Origin airports, comma-delimited (e.g. 'SFO,LAX').",
    )
    destination_airport: str = Field(
        ...,
        description="Destination airports, comma-delimited (e.g. 'FRA,LHR').",
    )
    start_date: Optional[date] = Field(
        None,
        description="Start of departure date range (YYYY-MM-DD).",
    )
    end_date: Optional[date] = Field(
        None,
        description="End of departure date range (YYYY-MM-DD).",
    )
    cursor: Optional[int] = Field(
        None,
        description="Cursor from a previous search call for pagination.",
    )
    take: Optional[int] = Field(
        None,
        description="Max results (10-1000, default 500).",
    )
    order_by: Optional[str] = Field(
        None,
        description="Order by 'lowest_mileage' or default date-based ordering.",
    )
    skip: Optional[int] = Field(None, description="Number of results to skip.")
    include_trips: Optional[bool] = Field(
        False,
        description="Include trip-level details (may slow response).",
    )
    only_direct_flights: Optional[bool] = Field(
        False,
        description="Only return results with a direct flight available.",
    )
    carriers: Optional[str] = Field(
        None,
        description="Filter by carriers, comma-delimited (e.g. 'DL,AA').",
    )
    include_filtered: Optional[bool] = Field(
        False,
        description="Return results with raw (filtered) results.",
    )
    sources: Optional[str] = Field(
        None,
        description="Mileage programs, comma-delimited (e.g. 'aeroplan,united').",
    )
    minify_trips: Optional[bool] = Field(
        None,
        description="When include_trips is True, return reduced trip fields.",
    )
    cabins: Optional[str] = Field(
        None,
        description="Required cabins, comma-delimited (e.g. 'economy,business').",
    )


@mcp.tool()
async def cached_search(request: SearchRequest) -> dict:
    """Search for award flight availability via Seats.aero cached data."""
    log.info("Tool cached_search: %s -> %s", request.origin_airport, request.destination_airport)
    client = get_client()
    result = await client.search(**request.model_dump(exclude_unset=True))
    return result.model_dump()


@mcp.tool()
async def get_bulk_availability(
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
) -> dict:
    """Retrieve bulk award availability from a specific mileage program."""
    log.info("Tool get_bulk_availability: source=%s cabin=%s", source, cabin)
    client = get_client()
    result = await client.get_bulk_availability(
        source=source,
        cabin=cabin,
        start_date=start_date,
        end_date=end_date,
        origin_region=origin_region,
        destination_region=destination_region,
        take=take,
        cursor=cursor,
        skip=skip,
        include_filtered=include_filtered,
    )
    return result.model_dump()


@mcp.tool()
async def get_trip_by_id(trip_id: str) -> dict:
    """Retrieve a single trip by its ID."""
    log.info("Tool get_trip_by_id: %s", trip_id)
    client = get_client()
    result = await client.get_trip_by_id(trip_id=trip_id)
    return result.model_dump()


@mcp.tool()
async def get_routes(source: str) -> list[dict]:
    """Retrieve all routes for a given mileage program source."""
    log.info("Tool get_routes: source=%s", source)
    client = get_client()
    routes = await client.get_routes(source=source)
    return [r.model_dump() for r in routes]
