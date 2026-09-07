"""
Centralised application settings.
Values are loaded from environment variables / .env file.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve .env relative to this file (BackEnd/.env)
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)


class Settings:
    """Application configuration — all values sourced from the environment."""

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ah_career.db")

    # --- Qwen / DashScope (Phase 2) ---
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_WORKSPACE_ID: str = os.getenv("DASHSCOPE_WORKSPACE_ID", "ws-knn10vssjylmv6s0")
    DASHSCOPE_BASE_URL: str = os.getenv("DASHSCOPE_BASE_URL", "https://ws-knn10vssjylmv6s0.ap-southeast-1.maas.aliyuncs.com")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-plus-2025-07-28")
    # Ordered backup models tried ONLY when the primary fails with an
    # eligible model-availability error (HTTP 429 / 404 / 5xx). Comma-
    # separated, order preserved; empty entries and duplicates of earlier
    # models are ignored. An empty value disables the fallback entirely.
    QWEN_FALLBACK_MODELS: str = os.getenv(
        "QWEN_FALLBACK_MODELS",
        "qwen3-vl-235b-a22b-thinking,qwen-turbo",
    )
    AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    # --- MCP servers (Phase 5) ---
    # Both MCP servers are mounted inside this FastAPI application; the
    # Pattern B client connects back over SSE to the same server.
    MCP_SERVER_BASE_URL: str = os.getenv("MCP_SERVER_BASE_URL", "http://127.0.0.1:8000")

    # --- Application ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-to-random-string")
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
        ).split(",")
        if origin.strip()
    ]
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- Admin / ingestion (architecture_master §12/§17) ---
    # Bearer token for /api/v1/admin/* endpoints. Empty default is FAIL-CLOSED:
    # when unset, every admin request is rejected with 401. Never hardcode a
    # real value here — set it in BackEnd/.env (gitignored).
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "")


# Mandated deployment chain (model fallback). Application
# startup validates that every model below is present in the resolved
# chain — a configuration check only, never a live API call. Future chain
# changes update QWEN_MODEL / QWEN_FALLBACK_MODELS and this list together.
REQUIRED_QWEN_MODELS = [
    "qwen-plus-2025-07-28",
    "qwen3-vl-235b-a22b-thinking",
    "qwen-turbo",
]


settings = Settings()
