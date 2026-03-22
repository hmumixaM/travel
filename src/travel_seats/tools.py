from __future__ import annotations

import json
import logging
from typing import Optional

from travel_seats.models import (
    CABIN_CODES,
    SOURCES,
    AwardFlight,
    format_award_flight,
    parse_availability,
    parse_trip,
)
from travel_seats.server_core import get_client, mcp

log = logging.getLogger(__name__)


def _attach_trips(awards: list[AwardFlight], trips: list[dict]) -> None:
    """Match trip-level detail to each AwardFlight by cabin."""
    for trip in trips:
        cabin = trip.get("Cabin", "")
        leg = parse_trip(trip)
        for award in awards:
            if award.cabin == cabin:
                award.flights.append(leg)


@mcp.tool()
async def search_award_flights(
    origin: str,
    destination: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cabin: Optional[str] = None,
    source: Optional[str] = None,
    direct_only: bool = False,
    max_results: int = 20,
) -> str:
    """Search for award flight availability using points/miles via Seats.aero.

    Args:
        origin: Origin airport IATA code(s), comma-separated (e.g. 'SFO' or 'SFO,LAX')
        destination: Destination airport IATA code(s), comma-separated (e.g. 'NRT' or 'NRT,HND')
        start_date: Earliest departure date YYYY-MM-DD (optional)
        end_date: Latest departure date YYYY-MM-DD (optional)
        cabin: Filter by cabin class: economy, premium_economy, business, first (optional)
        source: Mileage program to search (e.g. 'united', 'aeroplan'). Use list_award_programs to see all options. (optional)
        direct_only: Only show nonstop flights (default false)
        max_results: Maximum results to return (default 20, max 50)
    """
    log.info("search_award_flights: %s->%s dates=%s/%s cabin=%s source=%s",
             origin, destination, start_date, end_date, cabin, source)

    max_results = min(max_results, 50)

    params = {
        "origin_airport": origin.upper(),
        "destination_airport": destination.upper(),
        "start_date": start_date,
        "end_date": end_date,
        "sources": source,
        "only_direct_flights": direct_only or None,
        "include_trips": True,
        "take": max_results * 3,
    }

    if cabin:
        cabin_map = {v: k for k, v in CABIN_CODES.items()}
        cabin_lower = cabin.lower().replace(" ", "_")
        assert cabin_lower in cabin_map, f"cabin must be one of: {list(CABIN_CODES.values())}"
        params["cabins"] = cabin_lower

    raw = await get_client().search(params)
    data = raw.get("data", [])

    all_awards: list[AwardFlight] = []
    for record in data:
        awards = parse_availability(record)
        trips = record.get("AvailabilityTrips") or []
        if trips:
            _attach_trips(awards, trips)
        all_awards.extend(awards)

    if cabin:
        all_awards = [a for a in all_awards if a.cabin == cabin_lower]

    all_awards.sort(key=lambda a: a.miles)
    all_awards = all_awards[:max_results]

    if not all_awards:
        return "No award flights found for this route and date range."

    has_more = raw.get("hasMore", False)
    header = f"Found {len(all_awards)} award options ({origin.upper()}->{destination.upper()})"
    if has_more:
        header += " (more available — narrow dates or add cabin filter)"

    output = [format_award_flight(a) for a in all_awards]
    return f"{header}\n\n{json.dumps(output, indent=2)}"


@mcp.tool()
async def list_award_programs() -> str:
    """List all supported mileage programs for award flight search."""
    return json.dumps(SOURCES)
