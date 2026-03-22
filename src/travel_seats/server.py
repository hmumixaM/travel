from __future__ import annotations

import travel_common  # noqa: F401 — configure logging early

from travel_seats.server_core import main, mcp
from travel_seats.tools import (
    get_award_flight_details,
    list_award_programs,
    search_award_flights,
)

__all__ = [
    "get_award_flight_details",
    "list_award_programs",
    "main",
    "mcp",
    "search_award_flights",
]

if __name__ == "__main__":
    main()
