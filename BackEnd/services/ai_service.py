"""
Reusable Qwen AI service (Alibaba Cloud Model Studio / DashScope).

Implements both AI patterns behind one shared client:

Pattern A (Phase 2) — structured JSON:

    prompt
      -> Qwen (Chat Completions, json_object response format)
      -> raw JSON text
      -> parsed dict
      -> Pydantic validation
      -> validated object returned to caller

Pattern B (Phase 5) — MCP tool calling:

    prompt + tool definitions
      -> Qwen (Chat Completions, tool_choice=auto)
      -> tool requests
      -> caller-supplied tool_executor (MCP tools -> SQLite)
      -> tool results returned to Qwen
      -> final answer + tool-call evidence trail

Usage:

    from services.ai_service import get_ai_service
    nba = get_ai_service().call_structured(prompt, NextBestAction, operation="onboarding_nba")
"""

from __future__ import annotations

import json
import logging
import re
from typing import Callable, Type, TypeVar
from urllib.parse import urlparse

from openai import APIConnectionError, APIError, OpenAI, RateLimitError
from pydantic import BaseModel, ValidationError

from config import settings
from prompts.mcp import DEFAULT_MCP_SYSTEM_PROMPT
from prompts.system_prompt import DEFAULT_STRUCTURED_SYSTEM_PROMPT

logger = logging.getLogger("ah_career.ai")

# Log sanitisation — never log API keys (architecture §9.2)
_SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def _sanitise(text: str) -> str:
    """Remove anything that looks like an API key from log output."""
    return _SECRET_PATTERN.sub("[REDACTED]", text)

T = TypeVar("T", bound=BaseModel)

_MAX_ATTEMPTS = 2  # one initial call + at most one retry

# Documented OpenAI-compatible endpoint path for DashScope / Model Studio.
_COMPATIBLE_MODE_PATH = "/compatible-mode/v1"

_RETRY_INSTRUCTION = (
    "Your previous response was not valid. "
    "Output only a single valid JSON object that matches the requested schema exactly. "
    "No explanations, no markdown, no extra fields."
)


# ---------------------------------------------------------------------------
# Controlled application-level exceptions (no provider internals leak out)
# ---------------------------------------------------------------------------


class AIServiceError(Exception):
    """Base class for all AI service failures."""


class AIValidationError(AIServiceError):
    """The model output could not be parsed or schema-validated (after retry)."""


class AIUnavailableError(AIServiceError):
    """The AI provider is not configured, unreachable, or rejected the request."""


class MCPCallResult(BaseModel):
    """Pattern B result: the final answer plus the tool-call evidence trail."""

    answer: str
    tool_calls: list[dict] = []  # [{tool, arguments, result}, ...]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AIService:
    """
    One reusable DashScope/Qwen client for the whole application.

    The OpenAI-compatible client is created lazily ONCE and reused.
    Feature services must never build their own clients.
    """

    def __init__(self, client: OpenAI | None = None) -> None:
        # An injected client (used by tests) skips real configuration.
        self._client = client

    # ------------------------------------------------------------------ client

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> OpenAI:
        if not settings.DASHSCOPE_API_KEY or not settings.DASHSCOPE_BASE_URL:
            raise AIUnavailableError(
                "AI service is not configured: set DASHSCOPE_API_KEY and DASHSCOPE_BASE_URL."
            )

        base_url = settings.DASHSCOPE_BASE_URL.strip()
        if "{WorkspaceId}" in base_url:
            if not settings.DASHSCOPE_WORKSPACE_ID:
                raise AIUnavailableError(
                    "AI service is not configured: DASHSCOPE_BASE_URL contains "
                    "{WorkspaceId} but DASHSCOPE_WORKSPACE_ID is not set."
                )
            base_url = base_url.replace("{WorkspaceId}", settings.DASHSCOPE_WORKSPACE_ID)

        normalized = _normalize_base_url(base_url)
        if normalized != base_url:
            logger.info(
                "AI base URL normalized (scheme/path completed, workspace masked): %s",
                normalized.replace(settings.DASHSCOPE_WORKSPACE_ID, "***")
                if settings.DASHSCOPE_WORKSPACE_ID else normalized,
            )

        return OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=normalized,
            timeout=settings.AI_TIMEOUT_SECONDS,
        )

    def is_configured(self) -> bool:
        """True when enough configuration exists to build a client."""
        return bool(settings.DASHSCOPE_API_KEY and settings.DASHSCOPE_BASE_URL)

    # ------------------------------------------------- structured call (Pattern A)

    def call_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str | None = None,
        operation: str = "structured_call",
    ) -> T:
        """
        Send ONE structured request to Qwen and return a validated Pydantic object.

        Retries at most ONCE for recoverable failures:
        - transport errors (connection / timeout),
        - malformed JSON,
        - Pydantic schema validation failures.

        Raises:
            AIValidationError  -- output invalid after the retry.
            AIUnavailableError -- provider not configured, unreachable, or rejected.
        """
        if system_prompt is None:
            system_prompt = DEFAULT_STRUCTURED_SYSTEM_PROMPT

        # DashScope json_object mode requires the word "json" in the prompt.
        if "json" not in system_prompt.lower():
            system_prompt = f"{system_prompt}\n\nReturn JSON only."

        schema_json = json.dumps(response_model.model_json_schema(), ensure_ascii=False)

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"{prompt}\n\n"
                    "Return a single JSON object matching this schema exactly:\n"
                    f"{schema_json}"
                ),
            },
        ]

        last_error: Exception | None = None
        last_kind = "validation"  # or "unavailable"

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            if attempt > 1:
                logger.warning(
                    "AI retry: operation=%s model=%s", operation, settings.QWEN_MODEL
                )
                messages = messages + [{"role": "system", "content": _RETRY_INSTRUCTION}]

            # --- make the request ---------------------------------------
            try:
                raw = self._request_raw(messages, operation)
            except APIConnectionError as exc:
                last_error, last_kind = exc, "unavailable"
                logger.warning(
                    "AI transport failure (attempt %s/%s): operation=%s error=%s",
                    attempt, _MAX_ATTEMPTS, operation, type(exc).__name__,
                )
                continue
            except ValueError as exc:
                # empty content / malformed response structure — recoverable
                last_error, last_kind = exc, "validation"
                logger.warning(
                    "AI empty/malformed response (attempt %s/%s): operation=%s",
                    attempt, _MAX_ATTEMPTS, operation,
                )
                continue

            # --- parse the JSON -----------------------------------------
            try:
                parsed = _extract_json_object(raw)
            except ValueError as exc:
                last_error, last_kind = exc, "validation"
                logger.warning(
                    "AI malformed JSON (attempt %s/%s): operation=%s",
                    attempt, _MAX_ATTEMPTS, operation,
                )
                continue

            # --- validate against the schema ----------------------------
            try:
                result = response_model.model_validate(parsed)
            except ValidationError as exc:
                last_error, last_kind = exc, "validation"
                logger.warning(
                    "AI schema validation failed (attempt %s/%s): operation=%s detail=%s",
                    attempt, _MAX_ATTEMPTS, operation, _sanitise(str(exc)[:300]),
                )
                continue

            logger.info(
                "AI structured call succeeded: operation=%s model=%s attempts=%s",
                operation, settings.QWEN_MODEL, attempt,
            )
            return result

        if last_kind == "unavailable":
            raise AIUnavailableError(
                f"The AI service is unreachable after {_MAX_ATTEMPTS} attempts "
                f"(operation={operation})."
            ) from last_error
        raise AIValidationError(
            f"The AI output could not be validated after {_MAX_ATTEMPTS} attempts "
            f"(operation={operation})."
        ) from last_error

    # --------------------------------------------------- MCP call (Pattern B)

    def call_with_mcp(
        self,
        prompt: str,
        *,
        tools: list[dict],
        tool_executor: Callable[[str, dict], dict],
        system_prompt: str | None = None,
        operation: str = "mcp_call",
        max_tool_rounds: int = 3,
    ) -> MCPCallResult:
        """
        Pattern B (Phase 5): Qwen with MCP tool calling.

        Loop:
            1. send the question + tool definitions to Qwen,
            2. if Qwen requests tools, run each through ``tool_executor``
               and return the JSON results as ``role: tool`` messages,
            3. repeat until Qwen produces a final answer (or the round
               limit is hit).

        Returns an MCPCallResult carrying the final answer AND the full
        tool-call trail ({tool, arguments, result} per call) so callers can
        prove which database records the answer is grounded in.

        Raises:
            AIValidationError  -- no usable final answer after the tool rounds.
            AIUnavailableError -- provider not configured, unreachable, or rejected.
            (tool_executor exceptions propagate unchanged so the MCP retry /
            fallback policy in mcp_search_service can react to them.)
        """
        if system_prompt is None:
            system_prompt = DEFAULT_MCP_SYSTEM_PROMPT

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        used_tool_calls: list[dict] = []

        for _round in range(max_tool_rounds + 1):
            response = self._request_with_tools(messages, tools, operation)
            try:
                message = response.choices[0].message
            except (AttributeError, IndexError, TypeError) as exc:
                raise AIValidationError("malformed response structure") from exc

            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                content = message.content
                if content is None or not str(content).strip():
                    raise AIValidationError("empty response content")
                logger.info(
                    "AI MCP call succeeded: operation=%s model=%s tool_rounds=%s",
                    operation, settings.QWEN_MODEL, len(used_tool_calls),
                )
                return MCPCallResult(
                    answer=str(content), tool_calls=used_tool_calls
                )

            # --- record the assistant's tool-call turn ---------------------
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments or "{}",
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            # --- execute every requested tool -----------------------------
            for tc in tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    logger.warning(
                        "AI returned malformed tool arguments: operation=%s tool=%s",
                        operation, tc.function.name,
                    )
                    arguments = {}
                result = tool_executor(tc.function.name, arguments)
                used_tool_calls.append(
                    {
                        "tool": tc.function.name,
                        "arguments": arguments,
                        "result": result,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(
                            result, ensure_ascii=False, default=str
                        ),
                    }
                )

        raise AIValidationError(
            f"The model did not produce a final answer after {max_tool_rounds} "
            f"tool rounds (operation={operation})."
        )

    # ------------------------------------------------------------------ internal

    def _request_raw(self, messages: list[dict], operation: str) -> str:
        """Call Qwen chat completions in json_object mode; return raw text content."""
        try:
            response = self.client.chat.completions.create(
                model=settings.QWEN_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
            )
        except APIConnectionError:
            # Transport-level failure — the caller decides whether to retry.
            raise
        except RateLimitError as exc:
            logger.error("AI rate limit: operation=%s", operation)
            raise AIUnavailableError("The AI provider rate-limited the request.") from exc
        except APIError as exc:
            logger.error(
                "AI API error: operation=%s error=%s",
                operation, type(exc).__name__,
            )
            raise AIUnavailableError(
                f"The AI provider returned an error ({type(exc).__name__})."
            ) from exc

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise ValueError("malformed response structure") from exc

        if content is None or not str(content).strip():
            raise ValueError("empty response content")
        return content

    def _request_with_tools(
        self, messages: list[dict], tools: list[dict], operation: str
    ):
        """Call Qwen chat completions in tool-calling mode (Pattern B)."""
        try:
            return self.client.chat.completions.create(
                model=settings.QWEN_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except APIConnectionError:
            # Transport-level failure — the caller decides whether to retry.
            raise
        except RateLimitError as exc:
            logger.error("AI rate limit: operation=%s", operation)
            raise AIUnavailableError("The AI provider rate-limited the request.") from exc
        except APIError as exc:
            logger.error(
                "AI API error: operation=%s error=%s",
                operation, type(exc).__name__,
            )
            raise AIUnavailableError(
                f"The AI provider returned an error ({type(exc).__name__})."
            ) from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_base_url(url: str) -> str:
    """
    Normalize the configured DashScope base URL to the documented
    OpenAI-compatible endpoint format: https://<host>/compatible-mode/v1

    Accepts common shorthand forms:
    - bare hostname without a scheme  -> https:// is prefixed
    - host without the API path       -> /compatible-mode/v1 is appended
    Full URLs are returned unchanged (trailing slashes stripped).
    """
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    # append the documented path only when no path component exists
    if not urlparse(url).path:
        url = f"{url}{_COMPATIBLE_MODE_PATH}"
    return url


def _extract_json_object(raw: str) -> dict:
    """
    Extract a JSON object from raw model output.

    Tolerates (and strips):
    - markdown code fences,
    - <think>...</think> reasoning blocks emitted by hybrid models.
    """
    text = raw.strip()

    # strip markdown code fences: ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
        text = text.strip()

    # strip reasoning blocks if a hybrid model emits them
    think_end = "</" + "think>"
    if think_end in text:
        text = text.split(think_end, 1)[1].strip()

    return json.loads(text)


# ---------------------------------------------------------------------------
# Module-level singleton — one client for the whole application
# ---------------------------------------------------------------------------

_service: AIService | None = None


def get_ai_service() -> AIService:
    """Return the shared AIService instance (lazy, one client per process)."""
    global _service
    if _service is None:
        _service = AIService()
    return _service
