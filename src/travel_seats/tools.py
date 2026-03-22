from __future__ import annotations

import json
import logging
from typing import Optional

from travel_seats.models import (
    CABIN_CODES,
    SOURCES,
    AwardFlight,
    FlightLeg,
    format_flight_leg,
    format_summary,
    parse_availability,
    parse_trip,
    summarize_awards,
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


def _collect_awards(
    raw: dict,
    cabin: str | None,
    max_results: int,
) -> tuple[list[AwardFlight], bool]:
    """Parse raw API response into sorted AwardFlights."""
    data = raw.get("data", [])
    all_awards: list[AwardFlight] = []

    for record in data:
        awards = parse_availability(record)
        trips = record.get("AvailabilityTrips") or []
        if trips:
            _attach_trips(awards, trips)
        all_awards.extend(awards)

    if cabin:
        all_awards = [a for a in all_awards if a.cabin == cabin]

    all_awards.sort(key=lambda a: (a.date, a.miles))
    truncated = len(all_awards) > max_results
    return all_awards[:max_results], truncated


def _build_params(
    origin: str,
    destination: str,
    start_date: str | None,
    end_date: str | None,
    cabin: str | None,
    source: str | None,
    direct_only: bool,
    take: int,
) -> dict:
    params: dict = {
        "origin_airport": origin.upper(),
        "destination_airport": destination.upper(),
        "start_date": start_date,
        "end_date": end_date,
        "sources": source,
        "only_direct_flights": direct_only or None,
        "include_trips": True,
        "take": take,
    }
    if cabin:
        cabin_map = {v: k for k, v in CABIN_CODES.items()}
        cabin_lower = cabin.lower().replace(" ", "_")
        assert cabin_lower in cabin_map, f"cabin must be one of: {list(CABIN_CODES.values())}"
        params["cabins"] = cabin_lower
    return params


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
    """Search award flight availability and return a DAILY SUMMARY.

    Returns one row per date/cabin/mileage-program showing the cheapest
    miles price and seat availability. Use `get_award_flight_details` to
    drill into specific itineraries for a date.

    Args:
        origin: Origin airport IATA code(s), comma-separated (e.g. 'SFO' or 'SFO,LAX')
        destination: Destination airport IATA code(s), comma-separated (e.g. 'NRT' or 'NRT,HND')
        start_date: Earliest departure date YYYY-MM-DD (optional)
        end_date: Latest departure date YYYY-MM-DD (optional)
        cabin: Filter by cabin class: economy, premium_economy, business, first (optional)
        source: Mileage program to search (e.g. 'united', 'aeroplan'). Use list_award_programs to see all options. (optional)
        direct_only: Only show nonstop flights (default false)
        max_results: Maximum daily-summary rows to return (default 20, max 50)
    """
    log.info("search_award_flights: %s->%s dates=%s/%s cabin=%s source=%s",
             origin, destination, start_date, end_date, cabin, source)

    max_results = min(max_results, 50)
    cabin_lower = cabin.lower().replace(" ", "_") if cabin else None
    params = _build_params(origin, destination, start_date, end_date,
                           cabin_lower, source, direct_only, max_results * 5)

    raw = await get_client().search(params)
    all_awards, _ = _collect_awards(raw, cabin_lower, max_results * 5)

    if not all_awards:
        return "No award flights found for this route and date range."

    summaries = summarize_awards(all_awards)[:max_results]
    has_more = raw.get("hasMore", False)

    header = f"Found availability across {len(summaries)} date/program combinations ({origin.upper()}->{destination.upper()})"
    if has_more:
        header += "\n(More results available — narrow dates or add cabin/source filter)"
    header += "\nUse get_award_flight_details() to see individual flight itineraries for a specific date."

    output = [format_summary(s) for s in summaries]
    return f"{header}\n\n{json.dumps(output, indent=2)}"


@mcp.tool()
async def get_award_flight_details(
    origin: str,
    destination: str,
    date: str,
    cabin: Optional[str] = None,
    source: Optional[str] = None,
    direct_only: bool = False,
    max_results: int = 30,
) -> str:
    """Get detailed flight itineraries for a SPECIFIC DATE.

    Call this after search_award_flights to drill into the flights
    available on a particular day. Returns individual bookable itineraries
    with flight numbers, times, aircraft, connections, etc.

    Args:
        origin: Origin airport IATA code(s), comma-separated
        destination: Destination airport IATA code(s), comma-separated
        date: Specific date YYYY-MM-DD
        cabin: Filter by cabin class: economy, premium_economy, business, first (optional)
        source: Mileage program (e.g. 'united', 'alaska') (optional)
        direct_only: Only show nonstop flights (default false)
        max_results: Maximum itineraries to return (default 30, max 100)
    """
    log.info("get_award_flight_details: %s->%s date=%s cabin=%s source=%s",
             origin, destination, date, cabin, source)

    max_results = min(max_results, 100)
    cabin_lower = cabin.lower().replace(" ", "_") if cabin else None
    params = _build_params(origin, destination, date, date,
                           cabin_lower, source, direct_only, max_results * 3)

    raw = await get_client().search(params)
    all_awards, _ = _collect_awards(raw, cabin_lower, 200)

    if not all_awards:
        return f"No award flights found for {origin.upper()}->{destination.upper()} on {date}."

    details: list[dict] = []
    for award in all_awards:
        for leg in award.flights:
            entry = format_flight_leg(leg)
            entry["source"] = award.source
            details.append(entry)

    details.sort(key=lambda d: (d["miles"], d["departs"]))
    details = details[:max_results]

    header = f"{len(details)} itineraries for {origin.upper()}->{destination.upper()} on {date}"
    if cabin_lower:
        header += f" ({cabin_lower})"
    if source:
        header += f" via {source}"

    return f"{header}\n\n{json.dumps(details, indent=2)}"


@mcp.tool()
async def list_award_programs() -> str:
    """List all supported mileage programs for award flight search."""
    return json.dumps(SOURCES)
