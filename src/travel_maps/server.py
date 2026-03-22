from __future__ import annotations

import travel_common  # noqa: F401 — configure logging early

from travel_maps.server_core import main, mcp
from travel_maps.tools import (
    find_place,
    get_directions,
    get_distance,
    get_geocode,
    place_details,
    place_nearby,
)

__all__ = [
    "find_place",
    "get_directions",
    "get_distance",
    "get_geocode",
    "main",
    "mcp",
    "place_details",
    "place_nearby",
]

if __name__ == "__main__":
    main()
