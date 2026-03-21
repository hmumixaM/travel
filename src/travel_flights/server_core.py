from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "streamable-http")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP(name="travel-flights", host=MCP_HOST, port=MCP_PORT)


def main() -> None:
    if MCP_TRANSPORT in ("sse", "streamable-http"):
        print(f"[travel-flights] Starting on http://{MCP_HOST}:{MCP_PORT}")
        print(f"[travel-flights] Transport: {MCP_TRANSPORT}")
    mcp.run(transport=MCP_TRANSPORT)
