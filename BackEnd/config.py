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
    DASHSCOPE_WORKSPACE_ID: str = os.getenv("DASHSCOPE_WORKSPACE_ID", "")
    DASHSCOPE_BASE_URL: str = os.getenv("DASHSCOPE_BASE_URL", "")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen3.7-plus")
    AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    # --- MCP servers (Phase 5) ---
    # Both MCP servers are mounted inside this FastAPI application; the
    # Pattern B client connects back over SSE to the same server.
    MCP_SERVER_BASE_URL: str = os.getenv("MCP_SERVER_BASE_URL", "http://127.0.0.1:8000")

    # --- Application ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-to-a-random-string")
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
