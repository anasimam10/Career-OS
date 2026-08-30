"""
Synchronous MCP client helpers over the SSE transport (Phase 5).

The two MCP servers are mounted inside this same FastAPI application
(/mcp/career/sse and /mcp/opportunity/sse). These helpers connect back to
them with the MCP SDK's SSE client, so Pattern B exercises the real MCP
protocol — tool listing and tool calls go through the mounted servers.

Every public function is synchronous (the SDK's async client is bridged
with asyncio.run) and converts every transport-level failure into one
controlled exception, MCPClientError, which mcp_search_service uses to
drive the retry / deterministic-fallback policy (spec §11).
"""

from __future__ import annotations

import asyncio
import json
import logging

from config import settings
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger("ah_career.mcp_client")

# The only MCP servers in this project (spec §9 — no third-party servers).
_KNOWN_SERVERS = {"career", "opportunity"}


class MCPClientError(Exception):
    """An MCP server/tool call failed (controlled, never leaks internals)."""


def server_url(server: str) -> str:
    """SSE endpoint URL for one of the project's two MCP servers."""
    if server not in _KNOWN_SERVERS:
        raise MCPClientError(f"Unknown MCP server '{server}'.")
    base = settings.MCP_SERVER_BASE_URL.rstrip("/")
    return f"{base}/mcp/{server}/sse"


# ---------------------------------------------------------------------------
# Async internals (one short-lived SSE session per call)
# ---------------------------------------------------------------------------


async def _list_tools_async(url: str) -> list[dict]:
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema,
                    },
                }
                for tool in result.tools
            ]


async def _call_tool_async(url: str, name: str, arguments: dict) -> dict:
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            if result.is_error:
                raise MCPClientError(
                    f"MCP tool '{name}' returned an error result."
                )
            if not result.content:
                raise MCPClientError(
                    f"MCP tool '{name}' returned no content."
                )
            text = getattr(result.content[0], "text", None)
            if text is None:
                raise MCPClientError(
                    f"MCP tool '{name}' returned non-text content."
                )
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise MCPClientError(
                    f"MCP tool '{name}' returned malformed JSON."
                ) from exc
            if not isinstance(parsed, dict):
                raise MCPClientError(
                    f"MCP tool '{name}' returned a non-object JSON result."
                )
            return parsed


# ---------------------------------------------------------------------------
# Public synchronous API
# ---------------------------------------------------------------------------


def list_tools(server: str) -> list[dict]:
    """List a server's tools as OpenAI-style tool definitions."""
    try:
        url = server_url(server)
        return asyncio.run(_list_tools_async(url))
    except MCPClientError:
        raise
    except Exception as exc:  # transport / protocol / OS level failures
        logger.warning("MCP list_tools failed for '%s': %s", server, type(exc).__name__)
        raise MCPClientError(
            f"MCP server '{server}' could not be reached for tool listing."
        ) from exc


def call_tool(server: str, name: str, arguments: dict) -> dict:
    """Call one tool on a server and return its parsed JSON result."""
    try:
        url = server_url(server)
        return asyncio.run(_call_tool_async(url, name, arguments))
    except MCPClientError:
        raise
    except Exception as exc:  # transport / protocol / OS level failures
        logger.warning(
            "MCP call_tool failed for '%s' on '%s': %s",
            name, server, type(exc).__name__,
        )
        raise MCPClientError(
            f"MCP tool '{name}' on server '{server}' could not be called."
        ) from exc
