"""
Live end-to-end proof — NOT part of the pytest suite.

Usage:
    cd BackEnd
    .venv\\Scripts\\python.exe live_e2e.py

Boots the real FastAPI application (uvicorn, in-process, free port) against
the real ah_career.db and walks the complete student journey with REAL Qwen
calls plus ONE real URL ingestion through the admin pipeline. This consumes
real API quota — roughly nine AI operations:

    1. onboarding Next Best Action
    2. career reality check (analyze)
    3. 7-day trial plan
    4. progress -> NBA recalculation (+ backend-validated stage transition)
    5. opportunity match (Pattern B over real MCP SSE)
    6. sports match (Pattern B over real MCP SSE)
    7. coach chat
    8. job readiness gap analysis
    9. ingestion extraction (one real public URL)

The ingested record must come back CANDIDATE and stay invisible to student
endpoints — verified live at the end of the run. Never prints credentials.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent

# The MCP Pattern B client connects back to this server over SSE; set the
# override BEFORE any BackEnd import so config picks it up (load_dotenv
# never overwrites variables that are already set).
_free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_free_socket.bind(("127.0.0.1", 0))
PORT = _free_socket.getsockname()[1]
_free_socket.close()
os.environ["MCP_SERVER_BASE_URL"] = f"http://127.0.0.1:{PORT}"

os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))

import httpx  # noqa: E402
import uvicorn  # noqa: E402

BASE_URL = f"http://127.0.0.1:{PORT}"
API = f"{BASE_URL}/api/v1"

# The one real URL ingested by this run (public Python job board — static
# HTML, well under the 512 KiB pipeline cap, clear title/org/type listings).
INGEST_URL = "https://www.python.org/jobs/"

ONBOARDING_PAYLOAD = {
    "education_stage": "HIGH_SCHOOL",
    "interests": ["Technology", "Mathematics"],
    "career_interests": ["Software Engineering"],
    "sports_interest": "Cricket",
    "motivation_tags": ["I genuinely love this subject", "High salary potential"],
    "skills": [{"name": "Python", "level": "beginner"}],
    "city": "Karachi",
}

# The seeded sports catalogue has cricket opportunities in Lahore (none in
# Karachi — that city has badminton/football), so the match query targets
# the data that actually exists and can be ranked honestly.
SPORTS_MATCH_PAYLOAD = {
    "sport": "Cricket",
    "location": "Lahore",
    "level": "beginner",
}

# --- run state ---------------------------------------------------------------

_checks_passed = 0
_checks_failed = 0
_failures: list[str] = []
_qwen_operations: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> bool:
    """Record one E2E check; print PASS/FAIL with detail."""
    global _checks_passed, _checks_failed
    if condition:
        _checks_passed += 1
        suffix = f"  [{detail}]" if detail else ""
        print(f"[PASS] {name}{suffix}")
    else:
        _checks_failed += 1
        _failures.append(name)
        suffix = f"  [{detail}]" if detail else ""
        print(f"[FAIL] {name}{suffix}")
    return condition


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    token: str | None = None,
) -> httpx.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.request(method, path, json=json_body, headers=headers)


def _student_opportunities(client: httpx.Client, params: dict | None = None) -> list[dict]:
    """GET /opportunities normalised to a list (bare list when non-empty)."""
    response = client.get(f"{API}/opportunities", params=params or {})
    response.raise_for_status()
    body = response.json()
    return body if isinstance(body, list) else body.get("opportunities", [])


# --- AI call instrumentation (evidence for the "~9 real Qwen calls") --------


def _instrument_ai_service() -> None:
    from services.ai_service import AIService

    original_structured = AIService.call_structured
    original_mcp = AIService.call_with_mcp

    def counting_structured(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        operation = kwargs.get("operation") or (
            args[3] if len(args) > 3 else "structured_call"
        )
        _qwen_operations.append(str(operation))
        return original_structured(self, *args, **kwargs)

    def counting_mcp(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        _qwen_operations.append(str(kwargs.get("operation", "mcp_call")))
        return original_mcp(self, *args, **kwargs)

    AIService.call_structured = counting_structured
    AIService.call_with_mcp = counting_mcp


def qwen_call_count() -> int:
    return len(_qwen_operations)


# --- server ------------------------------------------------------------------


def start_server() -> uvicorn.Server:
    config = uvicorn.Config(
        "main:app", host="127.0.0.1", port=PORT, log_level="warning"
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="live-e2e-uvicorn", daemon=True)
    thread.start()
    return server


def wait_for_health(client: httpx.Client, timeout_seconds: float = 60.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            response = client.get(f"{API}/health")
            if response.status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    return False


# --- flow steps --------------------------------------------------------------


def step_onboarding(client: httpx.Client) -> str | None:
    print("\n=== STEP 2: onboarding wizard (real Qwen NBA) ===")
    response = _request(client, "POST", f"{API}/onboarding", json_body=ONBOARDING_PAYLOAD)
    ok = check("POST /onboarding returns 200", response.status_code == 200,
               f"status={response.status_code} body={str(response.text)[:200]}")
    if not ok:
        return None
    body = response.json()
    check("profile_updated is true", body.get("profile_updated") is True)
    nba = body.get("next_best_action") or {}
    check("NBA generated with a title", bool(nba.get("title")),
          f"title={nba.get('title')!r}")
    return nba.get("title")


def step_careers(client: httpx.Client) -> None:
    print("\n=== STEP 3: careers catalogue (database only, no AI) ===")
    response = _request(client, "GET", f"{API}/careers")
    ok = check("GET /careers returns 200", response.status_code == 200)
    careers = response.json() if ok else []
    check("at least 15 seeded careers", len(careers) >= 15, f"count={len(careers)}")

    detail = _request(client, "GET", f"{API}/careers/software-engineering")
    ok = check("GET /careers/software-engineering returns 200",
               detail.status_code == 200)
    if ok:
        body = detail.json()
        check("career detail has slug + required skills",
              body.get("slug") == "software-engineering"
              and isinstance(body.get("required_skills"), list))


def step_analyze(client: httpx.Client) -> None:
    print("\n=== STEP 4: career reality check (real Qwen) ===")
    response = _request(
        client, "POST", f"{API}/career/analyze",
        json_body={"career_slug": "software-engineering"},
    )
    ok = check("POST /career/analyze returns 200", response.status_code == 200,
               f"status={response.status_code} body={str(response.text)[:200]}")
    if not ok:
        return
    body = response.json()
    reality = body.get("reality") or {}
    verdict = body.get("verdict") or {}
    check("reality block present with career name + skills",
          bool(reality.get("career_name")) and isinstance(reality.get("required_skills"), list),
          f"career={reality.get('career_name')!r}")
    check("verdict block present", bool(verdict.get("verdict")),
          f"verdict={verdict.get('verdict')!r}")


def step_trial_plan(client: httpx.Client) -> None:
    print("\n=== STEP 5: 7-day trial plan (real Qwen) ===")
    response = _request(
        client, "POST", f"{API}/career/trial-plan",
        json_body={"career_slug": "software-engineering"},
    )
    ok = check("POST /career/trial-plan returns 200", response.status_code == 200,
               f"status={response.status_code} body={str(response.text)[:200]}")
    if not ok:
        return
    body = response.json()
    check("duration_days enforced to 7", body.get("duration_days") == 7)
    check("plan has days + reflection prompt",
          len(body.get("days") or []) >= 1 and bool(body.get("reflection_prompt")),
          f"days={len(body.get('days') or [])}")


def step_journey_cached(client: httpx.Client, onboarding_nba_title: str | None) -> None:
    print("\n=== STEP 6: journey with cached NBA (no AI expected) ===")
    before = qwen_call_count()
    response = _request(client, "GET", f"{API}/journey")
    ok = check("GET /journey returns 200", response.status_code == 200)
    if not ok:
        return
    body = response.json()
    check("stage is HIGH_SCHOOL after onboarding",
          body.get("stage") == "HIGH_SCHOOL", f"stage={body.get('stage')!r}")
    nba_title = (body.get("next_best_action") or {}).get("title")
    check("cached NBA reused (matches onboarding NBA)",
          onboarding_nba_title is not None and nba_title == onboarding_nba_title,
          f"nba={nba_title!r}")
    check("no Qwen call on journey refresh", qwen_call_count() == before,
          f"calls_before={before} calls_after={qwen_call_count()}")


def step_progress(client: httpx.Client) -> tuple[str, str | None]:
    print("\n=== STEP 7: milestone progress (real Qwen NBA + stage transition) ===")
    from database import SessionLocal
    from models.roadmap import Milestone, Roadmap

    db = SessionLocal()
    try:
        pending = (
            db.query(Milestone)
            .join(Milestone.roadmap)
            .filter(Roadmap.student_id == 1, Milestone.status != "done")
            .order_by(Milestone.id)
            .first()
        )
        milestone_id = pending.id if pending else None
        milestone_title = pending.title if pending else ""
    finally:
        db.close()

    if milestone_id is None:
        check("a pending milestone exists to complete", False, "none pending")
        return "", None

    response = _request(
        client, "POST", f"{API}/progress",
        json_body={"milestone_id": milestone_id, "status": "done"},
    )
    ok = check("POST /progress returns 200", response.status_code == 200,
               f"milestone={milestone_id} ({milestone_title[:40]}) "
               f"status={response.status_code}")
    if not ok:
        return "", None
    body = response.json()
    new_stage = str(body.get("new_stage"))
    check("backend-validated stage transition to CAREER_DISCOVERY",
          new_stage == "CAREER_DISCOVERY", f"new_stage={new_stage!r}")
    nba_title = (body.get("next_best_action") or {}).get("title")
    check("new NBA calculated after progress", bool(nba_title), f"nba={nba_title!r}")
    return new_stage, nba_title


def step_journey_after_progress(
    client: httpx.Client, new_stage: str, progress_nba_title: str | None
) -> None:
    print("\n=== STEP 8: journey reflects progress ===")
    response = _request(client, "GET", f"{API}/journey")
    ok = check("GET /journey returns 200", response.status_code == 200)
    if not ok:
        return
    body = response.json()
    check("journey stage advanced", body.get("stage") == new_stage,
          f"stage={body.get('stage')!r}")
    nba_title = (body.get("next_best_action") or {}).get("title")
    check("journey shows the recalculated NBA",
          progress_nba_title is not None and nba_title == progress_nba_title,
          f"nba={nba_title!r}")


def step_opportunity_match(client: httpx.Client) -> None:
    print("\n=== STEP 9: opportunity match (real Qwen + real MCP SSE) ===")
    response = _request(
        client, "POST", f"{API}/opportunities/match",
        json_body={
            "city": "Karachi",
            "opportunity_type": "internship",
            "skills": ["Python"],
        },
    )
    ok = check("POST /opportunities/match returns 200", response.status_code == 200,
               f"status={response.status_code} body={str(response.text)[:200]}")
    if not ok:
        return
    body = response.json()
    matches = body.get("matches") or []
    check("ranked matches returned", len(matches) >= 1, f"count={len(matches)}")
    check("data_quality reported", bool(body.get("data_quality")),
          f"data_quality={body.get('data_quality')!r}")
    if matches:
        first = matches[0]
        check("top match has opportunity_id + positive score",
              bool(first.get("opportunity_id"))
              and float(first.get("match_score") or 0) > 0,
              f"id={first.get('opportunity_id')} score={first.get('match_score')}")


def step_sports_match(client: httpx.Client) -> None:
    print("\n=== STEP 10: sports match (real Qwen + real MCP SSE) ===")
    response = _request(
        client, "POST", f"{API}/sports/match",
        json_body=SPORTS_MATCH_PAYLOAD,
    )
    ok = check("POST /sports/match returns 200", response.status_code == 200,
               f"status={response.status_code} body={str(response.text)[:200]}")
    if not ok:
        return
    body = response.json()
    matches = body.get("matches") or []
    check("sports matches returned", len(matches) >= 1, f"count={len(matches)}")
    check("data_quality reported", bool(body.get("data_quality")),
          f"data_quality={body.get('data_quality')!r}")


def step_universities(client: httpx.Client) -> None:
    print("\n=== STEP 11: universities + programs (database only, no AI) ===")
    response = _request(client, "GET", f"{API}/universities")
    ok = check("GET /universities returns 200", response.status_code == 200)
    body = response.json() if ok else {"universities": [], "total": 0}
    check("24 seeded universities visible", body.get("total", 0) >= 20,
          f"total={body.get('total')}")

    response = _request(client, "GET", f"{API}/universities?field=Computer+Science")
    ok = check("field filter works", response.status_code == 200)
    if ok:
        body = response.json()
        check("multiple universities offer Computer Science",
              body.get("total", 0) >= 3, f"total={body.get('total')}")

    # Programs for the first university that has at least one program.
    listing = _request(client, "GET", f"{API}/universities").json()
    found_programs = False
    for university in (listing.get("universities") or [])[:5]:
        response = _request(
            client, "GET", f"{API}/universities/{university['id']}/programs"
        )
        if response.status_code != 200:
            continue
        programs = response.json().get("programs") or []
        if programs:
            found_programs = True
            check("university programs returned",
                  True, f"university={university.get('short_name')} "
                        f"programs={len(programs)}")
            break
    if not found_programs:
        check("university programs returned", False, "no programs in first 5")


def step_alumni(client: httpx.Client) -> None:
    print("\n=== STEP 12: alumni journeys (database only, no AI) ===")
    response = _request(client, "GET", f"{API}/alumni")
    ok = check("GET /alumni returns 200", response.status_code == 200)
    alumni = response.json().get("alumni", []) if ok else []
    check("seeded alumni journeys visible", len(alumni) >= 5, f"count={len(alumni)}")
    if alumni:
        first_id = alumni[0]["id"]
        detail = _request(client, "GET", f"{API}/alumni/{first_id}")
        ok = check("GET /alumni/{id} returns 200", detail.status_code == 200)
        if ok:
            body = detail.json()
            check("alumni detail resolves by id", body.get("name") == alumni[0]["name"])


def step_learning(client: httpx.Client) -> None:
    print("\n=== STEP 13: learning resources (database only, no AI) ===")
    response = _request(client, "GET", f"{API}/learning?skill=Python")
    ok = check("GET /learning?skill=Python returns 200", response.status_code == 200)
    resources = response.json().get("resources", []) if ok else []
    check("Python learning resources returned", len(resources) >= 1,
          f"count={len(resources)}")
    check("every resource carries a url",
          all(r.get("url") for r in resources) if resources else False)


def step_coach(client: httpx.Client) -> None:
    print("\n=== STEP 14: coach chat (real Qwen) ===")
    response = _request(
        client, "POST", f"{API}/coach/chat",
        json_body={
            "message": (
                "I am a high-school student in Karachi who wants to become a "
                "software engineer in Pakistan. What should I focus on this month?"
            ),
            "conversation_history": [],
        },
    )
    ok = check("POST /coach/chat returns 200", response.status_code == 200,
               f"status={response.status_code} body={str(response.text)[:200]}")
    if not ok:
        return
    body = response.json()
    message = body.get("message") or ""
    check("coach reply is non-empty", len(message) > 20,
          f"chars={len(message)}")


def step_job_readiness(client: httpx.Client) -> None:
    print("\n=== STEP 15: job readiness (real Qwen gap analysis) ===")
    response = _request(client, "POST", f"{API}/job-readiness")
    ok = check("POST /job-readiness returns 200", response.status_code == 200,
               f"status={response.status_code} body={str(response.text)[:200]}")
    if not ok:
        return
    body = response.json()
    score = body.get("overall_score")
    check("deterministic score in [0, 100]",
          isinstance(score, (int, float)) and 0 <= score <= 100, f"score={score}")
    check("hardcoded disclaimer always present", bool(body.get("disclaimer")))


def step_ingestion(client: httpx.Client, admin_token: str) -> None:
    print("\n=== STEP 16: one real URL ingestion (real Qwen extraction) ===")
    # Negative controls first — admin auth must hold live.
    response = _request(client, "GET", f"{API}/admin/ingest/runs/1")
    check("admin endpoint rejects missing token (401)", response.status_code == 401,
          f"status={response.status_code}")

    openapi = client.get(f"{BASE_URL}/openapi.json").json()
    admin_paths = [p for p in openapi.get("paths", {}) if "/admin" in p]
    check("admin routes hidden from Swagger", len(admin_paths) == 0,
          f"paths={admin_paths}")

    # The single real ingestion run.
    response = _request(
        client, "POST", f"{API}/admin/ingest/url",
        json_body={
            "urls": [INGEST_URL],
            "source_type": "SECONDARY_PORTAL",
            "run_label": "live-e2e single URL",
        },
        token=admin_token,
    )
    ok = check("POST /admin/ingest/url returns 200", response.status_code == 200,
               f"status={response.status_code} body={str(response.text)[:300]}")
    if not ok:
        return
    queued = response.json()
    run_id = queued.get("run_id")
    check("one URL queued", queued.get("queued_count") == 1,
          f"run_id={run_id} queued={queued.get('queued_count')}")

    status_response = _request(
        client, "GET", f"{API}/admin/ingest/runs/{run_id}", token=admin_token
    )
    ok = check("GET /admin/ingest/runs/{id} returns 200",
               status_response.status_code == 200)
    if not ok:
        return
    run = status_response.json()
    check("run COMPLETED with 1 successful item",
          run.get("status") == "COMPLETED" and run.get("successful_items") == 1,
          f"status={run.get('status')} ok={run.get('successful_items')} "
          f"failed={run.get('failed_items')}")

    items = run.get("items") or []
    item = items[0] if items else {}
    stored = item.get("status") == "STORED" and item.get("opportunity_id")
    check("item STORED with a new opportunity id", bool(stored),
          f"item_status={item.get('status')} opportunity_id={item.get('opportunity_id')} "
          f"error={item.get('error_message')}")
    if not stored:
        return
    opportunity_id = item["opportunity_id"]

    # Direct DB assertions: CANDIDATE-only persistence (master §11).
    from database import SessionLocal
    from models.opportunity import Opportunity

    db = SessionLocal()
    try:
        record = db.get(Opportunity, opportunity_id)
        check("ingested record is CANDIDATE (never auto-verified)",
              record is not None and record.verification_status == "CANDIDATE",
              f"status={getattr(record, 'verification_status', None)!r}")
        check("record linked to a source with content hash",
              record is not None and record.source_id is not None
              and bool(record.content_hash),
              f"source_id={getattr(record, 'source_id', None)}")
        title = record.title if record else ""
    finally:
        db.close()

    # Student invisibility: the CANDIDATE record must not appear anywhere.
    visible = _student_opportunities(client)
    ids = {o.get("id") for o in visible}
    titles = {o.get("title") for o in visible}
    check("CANDIDATE record hidden from GET /opportunities",
          opportunity_id not in ids and title not in titles,
          f"visible_count={len(visible)}")

    visible_jobs = _student_opportunities(client, {"type": "job"})
    job_ids = {o.get("id") for o in visible_jobs}
    job_titles = {o.get("title") for o in visible_jobs}
    check("CANDIDATE record hidden from filtered listing (type=job)",
          opportunity_id not in job_ids and title not in job_titles,
          f"visible_jobs={len(visible_jobs)}")

    quality = _request(
        client, "GET", f"{API}/admin/data-quality", token=admin_token
    )
    ok = check("GET /admin/data-quality returns 200", quality.status_code == 200)
    if ok:
        counters = quality.json()
        check("data quality reports the CANDIDATE record",
              counters.get("candidate_records", 0) >= 1,
              f"candidate_records={counters.get('candidate_records')}")


def main() -> int:
    started = time.monotonic()

    # --- preflight (hard requirements; no quota consumed) --------------------
    from config import settings
    from services.ai_service import AIService

    if not AIService().is_configured():
        print("FAILED: AI service is not configured "
              "(missing DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL in the environment).")
        return 1
    admin_token = settings.ADMIN_TOKEN
    if not admin_token:
        print("FAILED: ADMIN_TOKEN is not set — the admin ingestion step cannot run.")
        return 1

    _instrument_ai_service()

    print(f"Live E2E against {BASE_URL} (real Qwen + real MCP + real ingestion)")
    print(f"Server port: {PORT} (MCP_SERVER_BASE_URL overridden for this run)")

    server = start_server()
    client = httpx.Client(base_url=BASE_URL, timeout=600.0)
    try:
        print("\n=== STEP 1: server boot ===")
        healthy = wait_for_health(client)
        check("server started and /api/v1/health returns 200", healthy)
        if not healthy:
            print("FAILED: server never became healthy — aborting.")
            return 1

        onboarding_nba_title = step_onboarding(client)
        step_careers(client)
        step_analyze(client)
        step_trial_plan(client)
        step_journey_cached(client, onboarding_nba_title)
        new_stage, progress_nba_title = step_progress(client)
        step_journey_after_progress(client, new_stage, progress_nba_title)
        step_opportunity_match(client)
        step_sports_match(client)
        step_universities(client)
        step_alumni(client)
        step_learning(client)
        step_coach(client)
        step_job_readiness(client)
        step_ingestion(client, admin_token)
    finally:
        client.close()
        server.should_exit = True
        time.sleep(1.0)

    # --- summary ---------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Qwen operations used (public ai_service calls):")
    for index, operation in enumerate(_qwen_operations, start=1):
        print(f"  {index}. {operation}")
    check("all expected AI operations ran (~9)", qwen_call_count() >= 9,
          f"count={qwen_call_count()}")

    elapsed = time.monotonic() - started
    total = _checks_passed + _checks_failed
    print("=" * 72)
    print(f"RESULT: {_checks_passed}/{total} checks passed "
          f"in {elapsed:.0f}s with {qwen_call_count()} real Qwen operations.")
    if _failures:
        print("Failed checks:")
        for name in _failures:
            print(f"  - {name}")
        return 1
    print("LIVE E2E PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
