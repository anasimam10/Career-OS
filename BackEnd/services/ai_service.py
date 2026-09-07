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

Model fallback chain:

    qwen-plus-2025-07-28 (primary)
        -> qwen3-vl-235b-a22b-thinking
        -> qwen-turbo

The chain is deterministic and configuration-driven (QWEN_MODEL + the
ordered QWEN_FALLBACK_MODELS list). A fallback model is used ONLY when
the previous model fails with an eligible model-availability error
(HTTP 429 rate/quota limit, 404 model not found, or >= 500 provider
capacity). Every model goes through the identical retry + Pydantic
validation pipeline; the chain never restarts from the primary and never
recurses. Authentication/configuration errors (401/403, missing key,
invalid base URL), transport errors, and output validation errors never
switch models — a broken configuration is not fixed by another model.

Attempt budget (documented maximums):
    Pattern A: 2 attempts per model x 4 models = 8 API calls worst case.
    Pattern B: one tool-loop per model (max 4 loops); the outer MCP
               retry policy in mcp_search_service may run the whole
               chain twice.

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


def _model_chain() -> list[str]:
    """
    Ordered model chain: primary first, then the configured fallbacks.

    The fallbacks come from QWEN_FALLBACK_MODELS — an ordered,
    comma-separated list. Empty entries and duplicates (including any
    entry equal to the primary) are dropped; an empty setting disables
    the fallback entirely. Future models are added through configuration
    only — no router or feature service ever changes.
    """
    primary = settings.QWEN_MODEL.strip()
    chain = [primary]
    for name in settings.QWEN_FALLBACK_MODELS.split(","):
        name = name.strip()
        if not name or name in chain:
            continue
        chain.append(name)
    return chain


def _raise_controlled_api_error(exc: Exception, operation: str) -> None:
    """
    Translate a provider API error into the controlled AI service error.

    Eligible model-availability failures (HTTP 429 rate/quota limit, 404
    model not found, >= 500 provider capacity) raise _ModelUnavailableError
    so the fallback chain can switch models. Everything else — 401/403
    authentication, 400 bad request, 422, unknown APIError — raises plain
    AIUnavailableError and never triggers a model switch.
    """
    status = getattr(exc, "status_code", None)
    err_str = str(exc).lower()
    if isinstance(exc, RateLimitError) or status == 429 or "insufficient_quota" in err_str:
        logger.error("AI rate limit or quota exhausted: operation=%s", operation)
        raise _ModelUnavailableError(
            f"The AI provider rate-limited or exhausted quota for the model (operation={operation})."
        ) from exc
    if status == 404 or "model not found" in err_str:
        logger.error("AI model unavailable: operation=%s", operation)
        raise _ModelUnavailableError(
            f"The AI model is unavailable (operation={operation})."
        ) from exc
    if isinstance(status, int) and status >= 500:
        logger.error("AI provider capacity error: operation=%s", operation)
        raise _ModelUnavailableError(
            f"The AI provider is temporarily unavailable (operation={operation})."
        ) from exc
    logger.error(
        "AI API error: operation=%s error=%s",
        operation, type(exc).__name__,
    )
    raise AIUnavailableError(
        f"The AI provider returned an error ({type(exc).__name__})."
    ) from exc


# ---------------------------------------------------------------------------
# Controlled application-level exceptions (no provider internals leak out)
# ---------------------------------------------------------------------------


class AIServiceError(Exception):
    """Base class for all AI service failures."""


class AIValidationError(AIServiceError):
    """The model output could not be parsed or schema-validated (after retry)."""


class AIUnavailableError(AIServiceError):
    """The AI provider is not configured, unreachable, or rejected the request."""


class _ModelUnavailableError(AIUnavailableError):
    """
    The configured model is unavailable (HTTP 429 / 404 / 5xx).

    Internal marker: the model fallback chain reacts to it and retries the
    same request on the backup model. Callers only ever see the public
    AIUnavailableError contract (this is a subclass), so no router or
    feature service needs to change.
    """


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

        Per-model retry: at most ONCE for recoverable failures:
        - transport errors (connection / timeout),
        - malformed JSON,
        - Pydantic schema validation failures.

        Model fallback: if a model fails with an ELIGIBLE
        model-availability error (HTTP 429 / 404 / 5xx), the identical
        request + validation pipeline runs on the NEXT model in the
        configured fallback chain (qwen-plus-2025-07-28 -> qwen3-vl-235b-a22b-thinking
        -> qwen-turbo). The chain never restarts from
        the primary and never recurses; non-eligible errors never switch
        models.

        Raises:
            AIValidationError  -- output invalid after the retry.
            AIUnavailableError -- provider not configured, unreachable, or
                                  rejected the request on every model tried.
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

        models = _model_chain()
        for index, model in enumerate(models):
            try:
                return self._structured_attempts(
                    model, list(messages), response_model, operation
                )
            except _ModelUnavailableError as exc:
                if index + 1 < len(models):
                    logger.warning(
                        "AI model unavailable; attempting next model in the "
                        "fallback chain: operation=%s from_model=%s "
                        "to_model=%s error=%s",
                        operation, model, models[index + 1], type(exc).__name__,
                    )
                    continue
                # Chain exhausted — the public AIUnavailableError contract.
                raise
        raise AIUnavailableError("No model configured for the fallback chain.")

    def _structured_attempts(
        self,
        model: str,
        messages: list[dict],
        response_model: Type[T],
        operation: str,
    ) -> T:
        """Pattern A attempt loop for ONE model: initial call + at most one retry."""
        last_error: Exception | None = None
        last_kind = "validation"  # or "unavailable"

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            if attempt > 1:
                logger.warning(
                    "AI retry: operation=%s model=%s", operation, model
                )
                messages = messages + [{"role": "system", "content": _RETRY_INSTRUCTION}]

            # --- make the request ---------------------------------------
            try:
                raw = self._request_raw(messages, operation, model)
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
            # _ModelUnavailableError (429/404/5xx) propagates immediately:
            # rate limits and model outages are never retried on the SAME
            # model — the fallback chain in call_structured reacts instead.

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
                operation, model, attempt,
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

        Model fallback: on an ELIGIBLE model-availability failure
        (HTTP 429 / 404 / 5xx) the whole tool-calling loop re-runs on the
        NEXT model in the configured fallback chain — a fresh conversation
        with the same tools and executor. MCP transport failures,
        validation failures, and tool-executor errors never switch models.

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

        models = _model_chain()
        for index, model in enumerate(models):
            try:
                return self._mcp_attempts(
                    model,
                    prompt,
                    tools=tools,
                    tool_executor=tool_executor,
                    system_prompt=system_prompt,
                    operation=operation,
                    max_tool_rounds=max_tool_rounds,
                )
            except _ModelUnavailableError as exc:
                if index + 1 < len(models):
                    logger.warning(
                        "AI model unavailable; attempting next model in the "
                        "fallback chain: operation=%s from_model=%s "
                        "to_model=%s error=%s",
                        operation, model, models[index + 1], type(exc).__name__,
                    )
                    continue
                # Chain exhausted — the public AIUnavailableError contract.
                raise
        raise AIUnavailableError("No model configured for the fallback chain.")

    def _mcp_attempts(
        self,
        model: str,
        prompt: str,
        *,
        tools: list[dict],
        tool_executor: Callable[[str, dict], dict],
        system_prompt: str,
        operation: str,
        max_tool_rounds: int,
    ) -> MCPCallResult:
        """Pattern B tool-calling loop for ONE model (fresh conversation)."""
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        used_tool_calls: list[dict] = []

        for _round in range(max_tool_rounds + 1):
            response = self._request_with_tools(messages, tools, operation, model)
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
                    operation, model, len(used_tool_calls),
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

    def _request_raw(self, messages: list[dict], operation: str, model: str) -> str:
        """Call Qwen chat completions in json_object mode; return raw text content."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
        except APIConnectionError:
            # Transport-level failure — the caller decides whether to retry.
            raise
        except APIError as exc:
            # Classified: 429/404/5xx -> model-chain eligible; rest -> plain.
            _raise_controlled_api_error(exc, operation)  # always raises

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise ValueError("malformed response structure") from exc

        if content is None or not str(content).strip():
            raise ValueError("empty response content")
        return content

    def _request_with_tools(
        self, messages: list[dict], tools: list[dict], operation: str, model: str
    ):
        """Call Qwen chat completions in tool-calling mode (Pattern B)."""
        try:
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except APIConnectionError:
            # Transport-level failure — the caller decides whether to retry.
            raise
        except APIError as exc:
            # Classified: 429/404/5xx -> model-chain eligible; rest -> plain.
            _raise_controlled_api_error(exc, operation)  # always raises


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
