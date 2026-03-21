from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from travel_seats.client import SeatsAeroClient

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "streamable-http")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP(name="travel-seats", host=MCP_HOST, port=MCP_PORT)

_client: SeatsAeroClient | None = None


def get_client() -> SeatsAeroClient:
    global _client
    if _client is None:
        _client = SeatsAeroClient()
    return _client


def main() -> None:
    if MCP_TRANSPORT in ("sse", "streamable-http"):
        print(f"[travel-seats] Starting on http://{MCP_HOST}:{MCP_PORT}")
        print(f"[travel-seats] Transport: {MCP_TRANSPORT}")
    mcp.run(transport=MCP_TRANSPORT)
