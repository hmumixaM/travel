from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

log = logging.getLogger(__name__)

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "streamable-http")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP(name="travel-flights", host=MCP_HOST, port=MCP_PORT)


def main() -> None:
    log.info("Starting travel-flights on http://%s:%s transport=%s", MCP_HOST, MCP_PORT, MCP_TRANSPORT)
    mcp.run(transport=MCP_TRANSPORT)
