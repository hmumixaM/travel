from __future__ import annotations

import travel_common  # noqa: F401 — configure logging early

from travel_flights.server_core import main, mcp
from travel_flights.tools import (
    airport_search,
    get_travel_dates,
    search_flights,
    update_airports_database,
)

__all__ = [
    "airport_search",
    "get_travel_dates",
    "main",
    "mcp",
    "search_flights",
    "update_airports_database",
]

if __name__ == "__main__":
    main()
