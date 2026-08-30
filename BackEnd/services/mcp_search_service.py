"""
Pattern B orchestration (Phase 5): Qwen + MCP tool calling, with the
architecture's retry / deterministic-fallback policy.

Flow (spec §8):

    question
      -> MCP server (SSE): list tools
      -> Qwen (chat completions with tools)
      -> Qwen selects a tool
      -> MCP tool over SSE
      -> SQLite
      -> tool result
      -> Qwen
      -> final answer (+ tool-call evidence trail)

Failure policy (spec §11):

    attempt 1 fails -> retry once
    attempt 2 fails -> deterministic direct database fallback
                       (unranked results, never fabricated AI data)

The direct fallback calls the MCP tool functions themselves (plain Python
functions reading the same database through Mcp.db_access) — the identical
queries without the MCP transport, so no query logic is duplicated.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from prompts.mcp import build_mcp_system_prompt
from services import mcp_client
from services.ai_service import (
    AIUnavailableError,
    AIValidationError,
    get_ai_service,
)

# The Mcp package lives at the repository root (main.py adds it to sys.path;
# this module keeps itself importable independently, e.g. from scripts).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Mcp import career_server as _career_module  # noqa: E402
from Mcp import opportunity_server as _opportunity_module  # noqa: E402

logger = logging.getLogger("ah_career.mcp_search")

# First attempt + one retry (spec §11).
MCP_ATTEMPTS = 2

SERVER_LABELS = {
    "career": "Pakistan Career & Education",
    "opportunity": "Pakistan Opportunities & Sports",
}

# Direct-callable tool functions — the same functions the MCP servers
# expose. The deterministic fallback reuses them without the transport.
FALLBACK_TOOLS = {
    "get_career": _career_module.get_career,
    "get_career_reality": _career_module.get_career_reality,
    "get_required_skills": _career_module.get_required_skills,
    "get_university_opportunities": _career_module.get_university_opportunities,
    "get_scholarships": _career_module.get_scholarships,
    "search_internships": _opportunity_module.search_internships,
    "search_jobs": _opportunity_module.search_jobs,
    "match_opportunity": _opportunity_module.match_opportunity,
    "search_sports_opportunities": _opportunity_module.search_sports_opportunities,
    "search_sports_scholarships": _opportunity_module.search_sports_scholarships,
    "search_university_sports": _opportunity_module.search_university_sports,
}

FALLBACK_NOTE = "Live ranking is temporarily unavailable."


def search_with_mcp(
    question: str,
    server: str,
    *,
    fallback_tool: str | None = None,
    fallback_arguments: dict | None = None,
    operation: str = "mcp_search",
) -> dict:
    """
    Answer a student question through the full Pattern B chain, with the
    spec §11 failure policy.

    Args:
        question: the student's natural-language question.
        server: "career" or "opportunity".
        fallback_tool / fallback_arguments: the deterministic tool call used
            when both MCP attempts fail (e.g. ("search_internships",
            {"city": "Karachi", "skills": ["Python"]})). When omitted, no
            fallback runs and an AIUnavailableError is raised.

    Returns:
        {"answer", "tool_calls", "data_quality": "ai_interpreted"} on the
        MCP path, or {"data_quality": "unranked", "note", "results"} on the
        deterministic fallback path.
    """
    label = SERVER_LABELS.get(server)
    if label is None:
        raise ValueError(f"Unknown MCP server '{server}'.")

    for attempt in range(1, MCP_ATTEMPTS + 1):
        try:
            return _attempt_search(question, server, label, operation)
        except (mcp_client.MCPClientError, AIUnavailableError, AIValidationError) as exc:
            logger.warning(
                "MCP search attempt %s/%s failed: operation=%s error=%s",
                attempt, MCP_ATTEMPTS, operation, type(exc).__name__,
            )

    # --- both attempts failed: deterministic direct database fallback -----
    if fallback_tool is not None:
        if fallback_tool not in FALLBACK_TOOLS:
            raise ValueError(f"Unknown fallback tool '{fallback_tool}'.")
        logger.warning(
            "MCP search falling back to direct DB: operation=%s tool=%s",
            operation, fallback_tool,
        )
        results = FALLBACK_TOOLS[fallback_tool](**(fallback_arguments or {}))
        return {
            "data_quality": "unranked",
            "note": FALLBACK_NOTE,
            "results": results,
        }

    raise AIUnavailableError(
        f"MCP search failed after {MCP_ATTEMPTS} attempts "
        f"(operation={operation})."
    )


def _attempt_search(
    question: str, server: str, label: str, operation: str
) -> dict:
    """One full Pattern B attempt: list tools -> Qwen -> tool calls -> answer."""

    def _executor(name: str, arguments: dict) -> dict:
        return mcp_client.call_tool(server, name, arguments)

    tools = mcp_client.list_tools(server)
    result = get_ai_service().call_with_mcp(
        question,
        tools=tools,
        tool_executor=_executor,
        system_prompt=build_mcp_system_prompt(label),
        operation=operation,
    )
    return {
        "answer": result.answer,
        "tool_calls": result.tool_calls,
        "data_quality": "ai_interpreted",
    }
