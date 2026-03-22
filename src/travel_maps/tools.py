from __future__ import annotations

import json
import os
from typing import Any, Optional

import googlemaps
from google.maps import places_v1, routing_v2
from google.maps.routing_v2.types import (
    ComputeRoutesRequest,
    RouteModifiers,
    RouteTravelMode,
    Waypoint,
)
from google.type import latlng_pb2

from travel_common import RateLimitedQueue
from travel_maps.server_core import mcp

MAPS_RATE_LIMIT = float(os.environ.get("MAPS_RATE_LIMIT", "10.0"))
_limiter = RateLimitedQueue(MAPS_RATE_LIMIT)

_api_key: str | None = None
_gmaps: googlemaps.Client | None = None
_places_client: places_v1.PlacesAsyncClient | None = None
_routes_client: routing_v2.RoutesAsyncClient | None = None


def _get_api_key() -> str:
    global _api_key
    if _api_key is None:
        _api_key = os.environ["GOOGLE_MAPS_API_KEY"]
    return _api_key


def _get_gmaps() -> googlemaps.Client:
    global _gmaps
    if _gmaps is None:
        _gmaps = googlemaps.Client(key=_get_api_key())
    return _gmaps


def _get_places() -> places_v1.PlacesAsyncClient:
    global _places_client
    if _places_client is None:
        _places_client = places_v1.PlacesAsyncClient(
            client_options={"api_key": _get_api_key()}
        )
    return _places_client


def _get_routes() -> routing_v2.RoutesAsyncClient:
    global _routes_client
    if _routes_client is None:
        _routes_client = routing_v2.RoutesAsyncClient(
            client_options={"api_key": _get_api_key()}
        )
    return _routes_client


TRAVEL_MODE_MAP = {
    "driving": RouteTravelMode.DRIVE,
    "walking": RouteTravelMode.WALK,
    "bicycling": RouteTravelMode.BICYCLE,
    "transit": RouteTravelMode.TRANSIT,
}


@mcp.tool()
async def get_directions(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> str:
    """Get step-by-step directions from origin to destination using Routes API.

    Args:
        origin: Originating address or place name
        destination: Destination address or place name
        mode: Mode of transport: driving, walking, bicycling, or transit
    """
    assert mode in TRAVEL_MODE_MAP, f"Mode must be one of {set(TRAVEL_MODE_MAP)}"
    await _limiter.acquire()

    request = ComputeRoutesRequest(
        origin=Waypoint(address=origin),
        destination=Waypoint(address=destination),
        travel_mode=TRAVEL_MODE_MAP[mode],
    )
    field_mask = "routes.distanceMeters,routes.duration,routes.legs.steps.navigationInstruction,routes.legs.steps.localizedValues"
    response = await _get_routes().compute_routes(
        request=request,
        metadata=[("x-goog-fieldmask", field_mask)],
    )

    assert response.routes, "No routes found."
    route = response.routes[0]
    leg = route.legs[0]

    steps = []
    for step in leg.steps:
        step_info: dict[str, Any] = {}
        if step.navigation_instruction:
            step_info["instruction"] = step.navigation_instruction.instructions
        if step.localized_values:
            step_info["distance"] = step.localized_values.distance.text if step.localized_values.distance else None
            step_info["duration"] = step.localized_values.duration.text if step.localized_values.duration else None
        steps.append({k: v for k, v in step_info.items() if v})

    output = {
        "total_distance_meters": route.distance_meters,
        "total_duration": route.duration.seconds if route.duration else None,
        "steps": steps,
    }
    return json.dumps(output, separators=(",", ":"))


@mcp.tool()
async def get_distance(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> str:
    """Find the distance and travel time between two locations using Routes API.

    Args:
        origin: Originating address or place name
        destination: Destination address or place name
        mode: Mode of transport: driving, walking, bicycling, or transit
    """
    assert mode in TRAVEL_MODE_MAP, f"Mode must be one of {set(TRAVEL_MODE_MAP)}"
    await _limiter.acquire()

    request = ComputeRoutesRequest(
        origin=Waypoint(address=origin),
        destination=Waypoint(address=destination),
        travel_mode=TRAVEL_MODE_MAP[mode],
    )
    field_mask = "routes.distanceMeters,routes.duration,routes.localizedValues"
    response = await _get_routes().compute_routes(
        request=request,
        metadata=[("x-goog-fieldmask", field_mask)],
    )

    assert response.routes, "No route found between locations."
    route = response.routes[0]

    output: dict[str, Any] = {
        "total_distance_meters": route.distance_meters,
        "total_duration_seconds": route.duration.seconds if route.duration else None,
        "mode": mode,
    }
    if route.localized_values:
        output["total_distance"] = route.localized_values.distance.text if route.localized_values.distance else None
        output["total_duration"] = route.localized_values.duration.text if route.localized_values.duration else None
    output = {k: v for k, v in output.items() if v is not None}
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
) -> str:
    """Search for a place by text query using Places API (New).

    Args:
        query: Place name, address, or description (e.g. 'best ramen in Tokyo')
    """
    await _limiter.acquire()

    request = places_v1.SearchTextRequest(
        text_query=query,
    )
    field_mask = "places.displayName,places.id,places.formattedAddress,places.location,places.types,places.rating,places.googleMapsUri"
    response = await _get_places().search_text(
        request=request,
        metadata=[("x-goog-fieldmask", field_mask)],
    )

    assert response.places, "No places found."

    results = []
    for place in response.places[:5]:
        entry: dict[str, Any] = {
            "name": place.display_name.text if place.display_name else None,
            "place_id": place.id,
            "address": place.formatted_address,
            "types": list(place.types) if place.types else None,
            "rating": place.rating if place.rating else None,
            "google_maps_url": place.google_maps_uri,
        }
        if place.location:
            entry["location"] = {"lat": place.location.latitude, "lng": place.location.longitude}
        results.append({k: v for k, v in entry.items() if v is not None})

    return json.dumps(results, separators=(",", ":"))


@mcp.tool()
async def place_nearby(
    latitude: float,
    longitude: float,
    radius: float,
    place_type: str,
) -> str:
    """Find places of a type within a radius of a location using Places API (New).

    Args:
        latitude: Latitude of the center point
        longitude: Longitude of the center point
        radius: Search radius in meters (max 50000)
        place_type: Type of place (e.g. 'restaurant', 'hotel', 'gas_station')
    """
    await _limiter.acquire()

    center = latlng_pb2.LatLng(latitude=latitude, longitude=longitude)
    circle = places_v1.types.Circle(center=center, radius=radius)
    location_restriction = places_v1.SearchNearbyRequest.LocationRestriction(circle=circle)

    request = places_v1.SearchNearbyRequest(
        location_restriction=location_restriction,
        included_types=[place_type],
    )
    field_mask = "places.displayName,places.id,places.formattedAddress,places.rating,places.googleMapsUri"
    response = await _get_places().search_nearby(
        request=request,
        metadata=[("x-goog-fieldmask", field_mask)],
    )

    assert response.places, "Nothing nearby matching the criteria."

    results = []
    for place in response.places[:10]:
        entry: dict[str, Any] = {
            "name": place.display_name.text if place.display_name else None,
            "place_id": place.id,
            "address": place.formatted_address,
            "rating": place.rating if place.rating else None,
            "google_maps_url": place.google_maps_uri,
        }
        results.append({k: v for k, v in entry.items() if v is not None})

    return json.dumps(results, separators=(",", ":"))


@mcp.tool()
async def place_details(
    place_id: str,
) -> str:
    """Get details about a place by its place_id using Places API (New).

    Args:
        place_id: The place_id (obtainable from find_place or place_nearby)
    """
    await _limiter.acquire()

    request = places_v1.GetPlaceRequest(
        name=f"places/{place_id}",
    )
    field_mask = "displayName,formattedAddress,internationalPhoneNumber,websiteUri,types,rating,userRatingCount,googleMapsUri,regularOpeningHours,priceLevel"
    response = await _get_places().get_place(
        request=request,
        metadata=[("x-goog-fieldmask", field_mask)],
    )

    output: dict[str, Any] = {
        "name": response.display_name.text if response.display_name else None,
        "address": response.formatted_address,
        "phone": response.international_phone_number,
        "website": response.website_uri,
        "types": list(response.types) if response.types else None,
        "rating": response.rating if response.rating else None,
        "user_ratings_total": response.user_rating_count if response.user_rating_count else None,
        "google_maps_url": response.google_maps_uri,
        "price_level": str(response.price_level) if response.price_level else None,
    }
    if response.regular_opening_hours and response.regular_opening_hours.weekday_descriptions:
        output["opening_hours"] = list(response.regular_opening_hours.weekday_descriptions)

    output = {k: v for k, v in output.items() if v is not None}
    return json.dumps(output, separators=(",", ":"), ensure_ascii=False)
