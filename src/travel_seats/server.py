from __future__ import annotations

import travel_common  # noqa: F401 — configure logging early

from travel_seats.server_core import main, mcp
from travel_seats.tools import (
    cached_search,
    get_bulk_availability,
    get_routes,
    get_trip_by_id,
)

__all__ = [
    "cached_search",
    "get_bulk_availability",
    "get_routes",
    "get_trip_by_id",
    "main",
    "mcp",
]

if __name__ == "__main__":
    main()
