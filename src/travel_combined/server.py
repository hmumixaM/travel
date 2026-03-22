"""Combined server that mounts all three MCP servers on a single port.

Endpoints:
  /seats/mcp    – travel-seats (Seats.aero reward flights)
  /flights/mcp  – travel-flights (Google Flights)
  /maps/mcp     – travel-maps (Google Maps)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import travel_common  # noqa: F401 — configure logging / dotenv early
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route

from travel_seats.server_core import mcp as seats_mcp
from travel_seats.tools import *  # noqa: F401,F403 — register tools

from travel_flights.server_core import mcp as flights_mcp
from travel_flights.tools import *  # noqa: F401,F403 — register tools

from travel_maps.server_core import mcp as maps_mcp
from travel_maps.tools import *  # noqa: F401,F403 — register tools

log = logging.getLogger(__name__)

MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

_sub_apps = {
    "seats": seats_mcp,
    "flights": flights_mcp,
    "maps": maps_mcp,
}


@asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncIterator[None]:
    managers = []
    for name, mcp in _sub_apps.items():
        log.info("Starting session manager for %s", name)
        mgr = mcp.session_manager.run()
        ctx = mgr.__aenter__()
        await ctx
        managers.append((name, mgr))
    yield
    for name, mgr in reversed(managers):
        log.info("Stopping session manager for %s", name)
        await mgr.__aexit__(None, None, None)


def _build_sub_routes(name: str, mcp_instance: object) -> Mount:
    starlette_app = mcp_instance.streamable_http_app()
    return Mount(f"/{name}", app=starlette_app)


async def _health(request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def create_app() -> Starlette:
    routes: list[Route | Mount] = [Route("/health", _health)]
    for name, mcp_instance in _sub_apps.items():
        routes.append(_build_sub_routes(name, mcp_instance))
        log.info("Mounted /%s/mcp", name)
    return Starlette(routes=routes, lifespan=_lifespan)


app = create_app()


def main() -> None:
    log.info(
        "Starting travel-combined on http://%s:%s (seats=/seats/mcp, flights=/flights/mcp, maps=/maps/mcp)",
        MCP_HOST,
        MCP_PORT,
    )
    uvicorn.run("travel_combined.server:app", host=MCP_HOST, port=MCP_PORT, workers=1)


if __name__ == "__main__":
    main()
