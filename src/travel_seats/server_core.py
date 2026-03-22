from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

from travel_seats.client import SeatsAeroClient

log = logging.getLogger(__name__)

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "streamable-http")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP(name="travel-seats", host=MCP_HOST, port=MCP_PORT)

_client: SeatsAeroClient | None = None


def get_client() -> SeatsAeroClient:
    global _client
    if _client is None:
        log.info("Initializing SeatsAeroClient")
        _client = SeatsAeroClient()
    return _client


def main() -> None:
    log.info("Starting travel-seats on http://%s:%s transport=%s", MCP_HOST, MCP_PORT, MCP_TRANSPORT)
    mcp.run(transport=MCP_TRANSPORT)
