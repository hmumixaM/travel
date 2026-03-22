from __future__ import annotations

import csv
import io
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

from travel_common import RateLimitedQueue
from travel_flights.server_core import mcp

log = logging.getLogger(__name__)

FLIGHTS_RATE_LIMIT = float(os.environ.get("FLIGHTS_RATE_LIMIT", "0.5"))
_limiter = RateLimitedQueue(FLIGHTS_RATE_LIMIT, name="google-flights")

CSV_URL = "https://raw.githubusercontent.com/mborsetti/airportsdata/refs/heads/main/airportsdata/airports.csv"
CACHE_FILE = Path(__file__).parent / "airports_cache.json"

airports: dict[str, str] = {}


async def _fetch_airports_csv() -> dict[str, str]:
    log.info("Fetching airports CSV from %s", CSV_URL)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(CSV_URL)
        resp.raise_for_status()

    result: dict[str, str] = {}
    reader = csv.DictReader(io.StringIO(resp.text))
    for row in reader:
        iata = row.get("iata", "")
        if iata and len(iata) == 3 and iata.isalpha() and iata.isupper():
            name = row.get("name", "")
            city = row.get("city", "")
            country = row.get("country", "")
            result[iata] = f"{name}, {city}, {country}" if city else f"{name}, {country}"

    if result:
        CACHE_FILE.write_text(json.dumps(result))
        log.info("Airports cache written: %d entries", len(result))

    return result


def _load_cache() -> dict[str, str]:
    if CACHE_FILE.exists():
        data = json.loads(CACHE_FILE.read_text())
        log.info("Loaded airport cache: %d entries", len(data))
        return data
    log.info("No airport cache file found")
    return {}


def _ensure_airports() -> None:
    global airports
    if not airports:
        airports = _load_cache()


def _format_results(result: object, trip_type: str, max_results: int = 10) -> str:
    if not result or not hasattr(result, "flights") or not result.flights:
        return "No flights found matching your criteria."

    output = [f"Found {len(result.flights)} flight options."]
    if hasattr(result, "current_price"):
        output.append(f"Price assessment: {result.current_price}")
    output.append("")

    for i, flight in enumerate(result.flights[:max_results], 1):
        tag = " [BEST]" if getattr(flight, "is_best", False) else ""
        output.append(f"Option {i}{tag}:")
        for attr, label in [
            ("name", "Airline"),
            ("departure", "Departure"),
            ("arrival", "Arrival"),
            ("arrival_time_ahead", "Arrives"),
            ("duration", "Duration"),
            ("stops", "Stops"),
            ("delay", "Delay"),
            ("price", "Price"),
        ]:
            val = getattr(flight, attr, None)
            if val:
                output.append(f"  {label}: {val}")
        output.append("")

    if len(result.flights) > max_results:
        output.append(f"... and {len(result.flights) - max_results} more options.")
    if trip_type == "round-trip":
        output.append("Note: Price shown is for the entire round trip.")

    return "\n".join(output)


@mcp.tool()
async def search_flights(
    from_airport: str,
    to_airport: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat_class: str = "economy",
) -> str:
    """Search for flights between two airports on Google Flights.

    Args:
        from_airport: Departure airport IATA code (e.g. 'LAX')
        to_airport: Arrival airport IATA code (e.g. 'JFK')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (optional, for round trips)
        adults: Number of adult passengers (default: 1)
        children: Number of children (default: 0)
        infants_in_seat: Number of infants in seat (default: 0)
        infants_on_lap: Number of infants on lap (default: 0)
        seat_class: economy, premium_economy, business, or first (default: economy)
    """
    log.info("Tool search_flights: %s->%s on %s (return=%s, class=%s)", from_airport, to_airport, departure_date, return_date, seat_class)
    _ensure_airports()
    from_airport = from_airport.upper()
    to_airport = to_airport.upper()

    departure_dt = datetime.strptime(departure_date, "%Y-%m-%d")
    return_dt = None
    if return_date:
        return_dt = datetime.strptime(return_date, "%Y-%m-%d")
        assert return_dt >= departure_dt, "Return date cannot be before departure date."

    from fast_flights import FlightData, Passengers, Result, get_flights

    flight_data = [FlightData(date=departure_date, from_airport=from_airport, to_airport=to_airport)]
    if return_date:
        flight_data.append(FlightData(date=return_date, from_airport=to_airport, to_airport=from_airport))

    trip_type = "round-trip" if return_date else "one-way"
    passengers = Passengers(
        adults=adults,
        children=children,
        infants_in_seat=infants_in_seat,
        infants_on_lap=infants_on_lap,
    )

    await _limiter.acquire()
    log.info("Calling fast-flights get_flights for %s->%s", from_airport, to_airport)
    result: Result = get_flights(
        flight_data=flight_data,
        trip=trip_type,
        seat=seat_class,
        passengers=passengers,
        fetch_mode="fallback",
    )
    flight_count = len(result.flights) if hasattr(result, "flights") and result.flights else 0
    log.info("fast-flights returned %d flights for %s->%s", flight_count, from_airport, to_airport)

    return _format_results(result, trip_type)


@mcp.tool()
async def airport_search(query: str) -> str:
    """Search for airport codes by name, city, or partial code.

    Args:
        query: Search term (city name, airport name, or partial code). Min 2 chars.
    """
    log.info("Tool airport_search: query=%r", query)
    _ensure_airports()
    assert len(query.strip()) >= 2, "Please provide at least 2 characters."

    q = query.strip().upper()
    matches = [
        f"{name} ({code})"
        for code, name in airports.items()
        if q in code or q in name.upper()
    ]

    if not matches:
        return f"No airports found matching '{query}'."

    matches.sort()
    lines = [f"Found {len(matches)} airports matching '{query}':"]
    lines.extend(matches[:20])
    if len(matches) > 20:
        lines.append(f"...and {len(matches) - 20} more. Refine your search.")
    return "\n".join(lines)


@mcp.tool()
async def get_travel_dates(
    days_from_now: Optional[int] = None,
    trip_length: Optional[int] = None,
) -> str:
    """Get suggested travel dates.

    Args:
        days_from_now: Days from today for departure (default: 30)
        trip_length: Trip length in days (default: 7)
    """
    days_from_now = days_from_now or 30
    trip_length = trip_length or 7
    assert days_from_now >= 1, "Days from now must be at least 1."
    assert trip_length >= 1, "Trip length must be at least 1 day."

    today = datetime.now()
    departure = today + timedelta(days=days_from_now)
    ret = departure + timedelta(days=trip_length)
    return f"Departure date: {departure.strftime('%Y-%m-%d')}\nReturn date: {ret.strftime('%Y-%m-%d')}"


@mcp.tool()
async def update_airports_database() -> str:
    """Update the airports database from the online CSV source."""
    log.info("Tool update_airports_database")
    global airports
    fresh = await _fetch_airports_csv()
    assert fresh, "Failed to fetch airports."
    airports = fresh
    return f"Updated airports database with {len(airports)} airports."
