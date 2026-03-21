from __future__ import annotations

import json
import os
from typing import Any, Optional

import googlemaps

from travel_common import RateLimitedQueue
from travel_maps.server_core import mcp

MAPS_RATE_LIMIT = float(os.environ.get("MAPS_RATE_LIMIT", "10.0"))
_limiter = RateLimitedQueue(MAPS_RATE_LIMIT)

_gmaps: googlemaps.Client | None = None


def _get_gmaps() -> googlemaps.Client:
    global _gmaps
    if _gmaps is None:
        _gmaps = googlemaps.Client(key=os.environ["GOOGLE_MAPS_API_KEY"])
    return _gmaps


VALID_MODES = {"driving", "walking", "bicycling", "transit"}


@mcp.tool()
async def get_directions(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> str:
    """Get step-by-step directions from origin to destination.

    Args:
        origin: Originating address or place name
        destination: Destination address or place name
        mode: Mode of transport: driving, walking, bicycling, or transit
    """
    assert mode in VALID_MODES, f"Mode must be one of {VALID_MODES}"
    await _limiter.acquire()
    results = _get_gmaps().directions(origin, destination, mode)
    if not results:
        return "No directions found."

    route = results[0]
    leg = route["legs"][0]
    output = {
        "summary": route["summary"],
        "total_distance": leg["distance"]["text"],
        "total_duration": leg["duration"]["text"],
        "steps": [
            {
                "instruction": step["html_instructions"],
                "distance": step["distance"]["text"],
                "duration": step["duration"]["text"],
            }
            for step in leg["steps"]
        ],
    }
    return json.dumps(output, separators=(",", ":"))


@mcp.tool()
async def get_distance(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> str:
    """Find the distance and travel time between two locations.

    Args:
        origin: Originating address or place name
        destination: Destination address or place name
        mode: Mode of transport: driving, walking, bicycling, or transit
    """
    assert mode in VALID_MODES, f"Mode must be one of {VALID_MODES}"
    await _limiter.acquire()
    results = _get_gmaps().distance_matrix(origin, destination, mode)

    rows = results.get("rows", [])
    assert rows, "No distance information found."
    element = rows[0]["elements"][0]
    assert element.get("status") != "ZERO_RESULTS", "No route found between locations."

    output = {
        "total_distance": element["distance"]["text"],
        "total_duration": element["duration"]["text"],
        "mode": mode,
    }
    return json.dumps(output, separators=(",", ":"))


@mcp.tool()
async def get_geocode(address: str) -> str:
    """Get the latitude and longitude of an address or place.

    Args:
        address: Address or place name to geocode
    """
    await _limiter.acquire()
    results = _get_gmaps().geocode(address)
    assert results, "Address not found."

    loc = results[0]["geometry"]["location"]
    return json.dumps({"lat": loc["lat"], "lng": loc["lng"]}, separators=(",", ":"))


@mcp.tool()
async def find_place(
    query: str,
    input_type: str = "textquery",
    fields: Optional[list[str]] = None,
) -> str:
    """Find a place by name or phone number.

    Args:
        query: Place name, address, or phone number
        input_type: 'textquery' or 'phonenumber'
        fields: Fields to return (default: place_id, formatted_address, name, geometry, types, rating)
    """
    if fields is None:
        fields = ["place_id", "formatted_address", "name", "geometry", "types", "rating"]

    await _limiter.acquire()
    results = _get_gmaps().find_place(query, input_type, fields)
    candidates = results.get("candidates", [])
    assert candidates, "No place found."

    place = candidates[0]
    output: dict[str, Any] = {
        "name": place.get("name"),
        "place_id": place.get("place_id"),
        "formatted_address": place.get("formatted_address"),
        "location": place.get("geometry", {}).get("location"),
        "types": place.get("types"),
        "rating": place.get("rating"),
    }
    output = {k: v for k, v in output.items() if v is not None}
    return json.dumps(output, separators=(",", ":"))


@mcp.tool()
async def place_nearby(
    location: dict[str, float],
    radius: int,
    place_type: str,
) -> str:
    """Find places of a type within a radius of a location.

    Args:
        location: Dict with 'lat' and 'lng' keys
        radius: Search radius in meters
        place_type: Type of place (e.g. 'restaurant', 'hotel')
    """
    await _limiter.acquire()
    results = _get_gmaps().places_nearby(location, radius, place_type)
    places = results.get("results", [])
    assert places, "Nothing nearby matching the criteria."

    output = {p["name"]: p["place_id"] for p in places}
    return json.dumps(output, separators=(",", ":"))


@mcp.tool()
async def place_details(
    place_id: str,
    fields: Optional[list[str]] = None,
) -> str:
    """Get details about a place by its place_id.

    Args:
        place_id: The place_id (obtainable from find_place or place_nearby)
        fields: Fields to return (default: name, address, phone, website, types, rating, total ratings)
    """
    if fields is None:
        fields = [
            "name",
            "formatted_address",
            "formatted_phone_number",
            "website",
            "types",
            "rating",
            "user_ratings_total",
        ]

    await _limiter.acquire()
    results = _get_gmaps().place(place_id, fields)
    details = results.get("result", {})
    assert details, "No details found."

    output: dict[str, Any] = {
        "name": details.get("name"),
        "formatted_address": details.get("formatted_address"),
        "formatted_phone_number": details.get("formatted_phone_number"),
        "website": details.get("website"),
        "types": details.get("types"),
        "rating": details.get("rating"),
        "user_ratings_total": details.get("user_ratings_total", 0),
    }
    output = {k: v for k, v in output.items() if v is not None}
    return json.dumps(output, separators=(",", ":"))
