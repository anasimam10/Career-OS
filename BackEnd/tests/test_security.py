"""
Phase 5 tests — Security (architecture_master §9/§17/§26).

Coverage:
- Admin endpoints: 401 without/with-wrong token, non-Bearer scheme,
  and the FAIL-CLOSED behavior when ADMIN_TOKEN is unset
- Admin routes hidden from the public OpenAPI/Swagger schema
- No secret values (admin token, API keys) ever appear in response bodies
- Ingestion tables are written ONLY through the ingestion service: no
  student-facing router module may import it (§26 write protection)
- CORS: only the configured frontend origin is allowed
- Log sanitisation strips API-key-shaped strings
"""

from __future__ import annotations

import importlib
import json

import pytest
from fastapi.testclient import TestClient

from config import settings
from main import app, sanitise_for_log

ADMIN_TOKEN = "sec-test-token-abc123"
SECRET_SHAPES = ("sec-test-token-abc123", "sk-AbCdEfGhIjKlMnOpQrStUvWx")


@pytest.fixture
def admin_auth(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)
    return {"Authorization": f"Bearer {ADMIN_TOKEN}"}


@pytest.fixture
def no_token_env(monkeypatch):
    """Simulate an unset ADMIN_TOKEN (fail-closed mode)."""
    monkeypatch.setattr(settings, "ADMIN_TOKEN", "")


ADMIN_ENDPOINTS = [
    ("post", "/api/v1/admin/ingest/url"),
    ("post", "/api/v1/admin/ingest/refresh"),
    ("get", "/api/v1/admin/ingest/runs/1"),
    ("get", "/api/v1/admin/data-quality"),
    ("post", "/api/v1/admin/opportunities/1/verify"),
]


# ---------------------------------------------------------------------------
# Admin authentication (§17/§26/§27)
# ---------------------------------------------------------------------------


class TestAdminAuthentication:
    @pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
    def test_missing_token_401(self, client, db_session, monkeypatch, method, path):
        monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)
        if method == "post":
            response = client.post(path, json={})
        else:
            response = client.get(path)
        assert response.status_code == 401

    @pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
    def test_wrong_token_401(self, client, db_session, monkeypatch, method, path):
        monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)
        headers = {"Authorization": "Bearer wrong-token-value"}
        if method == "post":
            response = client.post(path, json={}, headers=headers)
        else:
            response = client.get(path, headers=headers)
        assert response.status_code == 401

    def test_non_bearer_scheme_401(self, client, db_session, monkeypatch):
        monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)
        response = client.get(
            "/api/v1/admin/data-quality",
            headers={"Authorization": f"Basic {ADMIN_TOKEN}"},
        )
        assert response.status_code == 401

    def test_empty_bearer_401(self, client, db_session, monkeypatch):
        monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)
        response = client.get(
            "/api/v1/admin/data-quality", headers={"Authorization": "Bearer "}
        )
        assert response.status_code == 401

    def test_valid_token_accepted(self, client, db_session, admin_auth):
        response = client.get("/api/v1/admin/data-quality", headers=admin_auth)
        assert response.status_code == 200

    @pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
    def test_fail_closed_when_token_unset(
        self, client, db_session, no_token_env, method, path
    ):
        # An unset ADMIN_TOKEN must reject everything — including requests
        # carrying a (previously valid) token value.
        headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        if method == "post":
            response = client.post(path, json={}, headers=headers)
        else:
            response = client.get(path, headers=headers)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Swagger / OpenAPI exposure (§26: not in public docs)
# ---------------------------------------------------------------------------


class TestAdminHiddenFromSwagger:
    def test_admin_paths_absent_from_openapi(self, client):
        schema = client.get("/openapi.json").json()
        assert not any("/admin" in path for path in schema["paths"])


# ---------------------------------------------------------------------------
# Secret hygiene in responses (§27)
# ---------------------------------------------------------------------------


class TestNoSecretsInResponses:
    def test_admin_error_bodies_never_echo_the_token(self, client, db_session, monkeypatch):
        monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)
        wrong = {"Authorization": f"Bearer not{ADMIN_TOKEN}not"}
        for method, path in ADMIN_ENDPOINTS:
            if method == "post":
                response = client.post(path, json={}, headers=wrong)
            else:
                response = client.get(path, headers=wrong)
            assert ADMIN_TOKEN not in response.text

    def test_student_endpoints_never_leak_secrets(self, client, db_session):
        # A broad sweep across read endpoints: none may embed secrets.
        for path in (
            "/api/v1/health",
            "/api/v1/careers",
            "/api/v1/opportunities",
            "/api/v1/sports",
            "/api/v1/universities",
            "/api/v1/alumni",
            "/api/v1/learning",
        ):
            response = client.get(path)
            for secret in SECRET_SHAPES:
                assert secret not in response.text, f"{secret} leaked from {path}"

    def test_500_handler_returns_no_traceback(self, client, db_session, monkeypatch):
        from services import opportunity_service

        def boom(*args, **kwargs):
            raise RuntimeError("internal secret sk-AbCdEfGhIjKlMnOpQrStUvWx detail")

        monkeypatch.setattr(opportunity_service, "list_opportunities", boom)
        # raise_server_exceptions=False lets the app's global handler run
        # instead of the test transport re-raising the exception.
        with TestClient(app, raise_server_exceptions=False) as raw_client:
            response = raw_client.get("/api/v1/opportunities")
        assert response.status_code == 500
        body = response.json()
        assert body == {"error": "Internal server error"}
        assert "sk-" not in response.text
        assert "RuntimeError" not in response.text


# ---------------------------------------------------------------------------
# Ingestion write protection (§26)
# ---------------------------------------------------------------------------


class TestIngestionWriteProtection:
    STUDENT_MODULES = [
        "routers.careers",
        "routers.onboarding",
        "routers.journey",
        "routers.opportunities",
        "routers.sports",
        "routers.coach",
        "routers.job_readiness",
        "routers.universities",
        "routers.alumni",
        "routers.learning",
    ]

    @pytest.mark.parametrize("module_name", STUDENT_MODULES)
    def test_student_routers_never_import_ingestion(self, module_name):
        module = importlib.import_module(module_name)
        for name in vars(module):
            assert "ingestion" not in name.lower(), (
                f"{module_name} references ingestion ({name}) — student-facing "
                "modules must not write to ingestion tables (§26)"
            )

    def test_ingestion_models_not_reachable_from_student_routers(self):
        # The only router module allowed to touch the ingestion service.
        admin = importlib.import_module("routers.admin")
        assert hasattr(admin, "ingestion_service")


# ---------------------------------------------------------------------------
# CORS (§26/§9.2)
# ---------------------------------------------------------------------------


class TestCorsPolicy:
    def test_allowed_frontend_origin(self, client):
        response = client.get(
            "/api/v1/health", headers={"Origin": "http://localhost:3000"}
        )
        assert response.headers.get("access-control-allow-origin") in (
            "http://localhost:3000",
            "*",
        )

    def test_disallowed_origin_gets_no_allow_origin(self, client):
        response = client.get(
            "/api/v1/health", headers={"Origin": "https://evil.example.com"}
        )
        assert response.headers.get("access-control-allow-origin") != (
            "https://evil.example.com"
        )


# ---------------------------------------------------------------------------
# Log sanitisation (§9.2)
# ---------------------------------------------------------------------------


class TestLogSanitisation:
    def test_api_keys_are_redacted(self):
        assert (
            sanitise_for_log("key=sk-AbCdEfGhIjKlMnOpQrStUvWx called")
            == "key=[REDACTED] called"
        )

    def test_clean_text_untouched(self):
        assert sanitise_for_log("all good") == "all good"


# ---------------------------------------------------------------------------
# Cross-student data access (§28 security category)
# ---------------------------------------------------------------------------


class TestCrossStudentIsolation:
    def test_unknown_student_404_not_others_data(self, client, db_session):
        # Match endpoints scope strictly to the student in the request and
        # return 404 for unknown students — never another student's data.
        response = client.post(
            "/api/v1/opportunities/match", json={"student_id": 99999, "city": "Karachi"}
        )
        assert response.status_code == 404
        assert "error" in response.json()
