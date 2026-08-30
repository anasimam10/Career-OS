"""
A&H Careers — FastAPI application entry point.

Run with:
    cd BackEnd
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import init_db
from routers.careers import router as careers_router
from routers.coach import router as coach_router
from routers.health import router as health_router
from routers.job_readiness import router as job_readiness_router
from routers.journey import router as journey_router
from routers.onboarding import router as onboarding_router
from routers.opportunities import router as opportunities_router
from routers.sports import router as sports_router

# --- MCP servers (Phase 5) ---------------------------------------------
# The Mcp package lives at the repository root; make it importable, then
# mount the two SSE transports. (Python module lookup is case-sensitive,
# so the SDK's lowercase ``mcp`` and the project's ``Mcp`` never collide.)
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Mcp.career_server import career_server  # noqa: E402
from Mcp.opportunity_server import opportunity_server  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("ah_career")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="A&H Careers API",
    description="Backend API for the A&H Careers AI-powered student career journey.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the existing Next.js frontend
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health_router, prefix="/api/v1")
app.include_router(careers_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(journey_router, prefix="/api/v1")
app.include_router(opportunities_router, prefix="/api/v1")
app.include_router(sports_router, prefix="/api/v1")
app.include_router(coach_router, prefix="/api/v1")
app.include_router(job_readiness_router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# MCP SSE transports (Phase 5)
# ---------------------------------------------------------------------------

app.mount("/mcp/career", career_server.sse_app())
app.mount("/mcp/opportunity", opportunity_server.sse_app())

# ---------------------------------------------------------------------------
# Log sanitisation — never log API keys (architecture §9.2)
# ---------------------------------------------------------------------------

_SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def sanitise_for_log(text: str) -> str:
    """Remove anything that looks like an API key from log output."""
    return _SECRET_PATTERN.sub("[REDACTED]", text)


# ---------------------------------------------------------------------------
# Global exception handler — never leak stack traces to the frontend
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception on %s %s: %s: %s",
        request.method,
        request.url.path,
        type(exc).__name__,
        sanitise_for_log(str(exc)),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Startup — create database tables + validate env vars
# ---------------------------------------------------------------------------

# Required environment variables for production (architecture §12.3).
# Missing vars cause a clear startup failure without exposing secret values.
_REQUIRED_ENV_VARS = [
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_WORKSPACE_ID",
    "SECRET_KEY",
    "DATABASE_URL",
]


@app.on_event("startup")
def on_startup() -> None:
    # Validate required environment variables
    missing = [v for v in _REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        var_list = ", ".join(missing)
        raise RuntimeError(
            f"Required environment variables are not set: {var_list}. "
            "Aborting startup. Set them in your .env file or platform dashboard."
        )
    logger.info("Environment validation passed.")
    logger.info("Initialising database …")
    init_db()
    logger.info("Database ready.")

    # Seed the database if it is empty (e.g. first deploy on a fresh disk).
    # The seeder is insert-only and safe to call on every startup.
    try:
        _seed_data_dir = _REPO_ROOT / "data" / "seed_db.py"
        if _seed_data_dir.exists():
            if str(_REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(_REPO_ROOT))
            from data.seed_db import seed_if_empty
            seed_if_empty()
            logger.info("Seed check complete.")
        else:
            logger.warning("Seed script not found at %s — skipping.", _seed_data_dir)
    except Exception as exc:
        logger.warning("Seed step failed (non-fatal): %s", sanitise_for_log(str(exc)))
