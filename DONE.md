# A&H Career — DONE.md

**Last updated:** 2026-08-30 (Phase 9 COMPLETE — Full QA, security hardening, 256 tests passing, 11/11 frontend pages verified E2E)

---

## Completed Components

### Frontend (by Antigravity)
- [x] Next.js 14.2.5 application with TypeScript, Tailwind CSS, Framer Motion
- [x] All pages: Home, Onboarding (6-step wizard), Careers list, Career detail, Reality Check, Trial Plan, Journey, Mentor Chat
- [x] Component library: NavBar, Footer, PageTransition, CareerCard, CareerMetricBar, CareerVerdict, MotivationBar, RealityCheckPanel, TrialPlanView, JourneyTimeline, NextStepCard, RoadmapSteps, CoachChat, ChatMessage, QuickActions, TypingIndicator, OnboardingWizard, StepIndicator
- [x] UI primitives: badge, button, card, input, progress, separator, skeleton
- [x] API client layer with snake_case → camelCase conversion
- [x] Mock data system (USE_MOCK toggle) with realistic Pakistani data samples
- [x] Session management (localStorage-based demo student)
- [x] Hooks: useOnboarding, useCareerAnalysis, useCoachChat, useJourney
- [x] All dependencies installed (node_modules present)

### Docs
- [x] Architecture document (`architecture_corrected.md`) — 1,092 lines, comprehensive
- [x] Implementation status audit (`implementation-status.md`)

---

### Backend Foundation (Phase 1 — COMPLETED)
- [x] FastAPI application with CORS, logging, global error handler
- [x] Environment configuration (config.py + .env.example)
- [x] SQLite + SQLAlchemy setup with WAL mode and foreign keys
- [x] All 9 database models (students, student_profiles, careers, roadmaps, milestones, alumni, opportunities, sports_opportunities, student_opportunity_matches)
- [x] Pydantic schemas (shared enums, request payloads, response models)
- [x] Repository/data-access layer (BaseRepository, StudentRepository, CareerRepository)
- [x] Health endpoint (GET /api/v1/health)
- [x] Test suite (28 tests, all passing)
- [x] Python virtual environment with pinned dependencies

### Qwen AI Service (Phase 2 — COMPLETED)
- [x] DashScope configuration (BackEnd/config.py + .env / .env.example)
- [x] qwen3.7-plus (read from QWEN_MODEL env var)
- [x] Structured JSON output (Pattern A, json_object response format)
- [x] Pydantic validation of every AI result (model_validate)
- [x] Retry handling (maximum ONE retry, centralized in ai_service.py)
- [x] AI error handling (connection, timeout, rate limit, empty/malformed response, schema failure)
- [x] Master system prompt (BackEnd/prompts/system_prompt.py) with trust hierarchy + no-invention rules
- [x] Base URL normalization (scheme + /compatible-mode/v1 path completed automatically)
- [x] Unit tests (23 tests, fully mocked — no API quota consumed)
- [x] Real connectivity verification (BackEnd/test_qwen.py) — SUCCESS: qwen3.7-plus responded, output validated as NextBestAction

### Career Intelligence (Phase 3 — COMPLETED)
- [x] GET /api/v1/careers — career list from SQLite (database only, no AI)
- [x] GET /api/v1/careers/{slug} — full career record from SQLite (404 with clean error for unknown slug)
- [x] POST /api/v1/career/analyze — Career Reality Check (Qwen Pattern A via existing ai_service)
- [x] POST /api/v1/career/trial-plan — 7-day trial plan (Qwen Pattern A; duration_days=7 enforced in code)
- [x] Career service (BackEnd/services/career_service.py) — reuses Phase 1 repositories and Phase 2 AI service
- [x] Career prompts (BackEnd/prompts/career_analysis.py, trial_plan.py) — built on the master system prompt, no duplication
- [x] Trust hierarchy enforced in code: database facts overwrite AI-proposed values in CareerReality factual fields
- [x] data_source honestly identifies template seed data (not independently verified) + last_updated date
- [x] Error contract: 404 unknown career, 422 invalid request, 503 AI unavailable, 500 AI output unprocessable — `{error: ...}` bodies
- [x] Demo student session context (id=1, matches Frontend/lib/session.ts); honest "not yet onboarded" context when missing
- [x] Career seed data (data/seed/careers.json — 15 careers, clearly labeled TEMPLATE data converted from frontend mock) + seeding script (data/seed_db.py, never overwrites existing records)
- [x] Phase 3 tests (26 tests, Qwen fully mocked — no API quota)
- [x] Live verification: server start, /docs, all four routes in Swagger, GET endpoints returning seeded data

### Next Best Action + Journey (Phase 4 — COMPLETED)
- [x] POST /api/v1/onboarding — profile update + journey bootstrap + first Next Best Action (Qwen)
- [x] GET /api/v1/journey — current stage + current step + max 3 visible steps + NBA (cached NBA reused — no Qwen on refresh)
- [x] POST /api/v1/progress — milestone completion + backend-validated stage transition + NBA recalculation (Qwen)
- [x] POST /api/v1/roadmap — idempotent milestone instantiation, returns 1–3 visible steps only (no AI)
- [x] Journey state machine (BackEnd/services/journey_state.py) — enum-based EducationStage, explicit VALID_TRANSITIONS map, transition validation; stage changes ONLY via backend-validated milestone completion, never by the AI
- [x] Deterministic candidate generator (BackEnd/services/candidate_service.py) — 3–8 candidates from stage templates + verified career data (learn-a-required-skill candidate grounded in DB); completed actions retired; no Qwen calls
- [x] NBA engine (BackEnd/services/nba_service.py) — candidate-constrained Qwen selection: Qwen returns ONLY candidate_id + one personalized sentence; every other NextBestAction field is backend-generated from the deterministic candidate; invalid selection retried once, then deterministic highest-priority fallback; AI unavailability also falls back (never a dead-end); NBA persisted in student_profiles.next_best_action with validity snapshot
- [x] NBA prompt (BackEnd/prompts/next_best_action.py) — built on the master system prompt; candidates + journey state + student context injected; "select exactly ONE candidate_id" rule
- [x] Roadmap service (BackEnd/services/roadmap_service.py) — stage-specific milestone templates (single source of truth shared with the candidate generator), idempotent instantiation deduped by (stage, title)
- [x] Onboarding service — accepts the wizard payload (display-name career_interests resolved to verified slugs; "Not sure yet" stays no-goal); creates the demo student when missing; bootstraps stage milestones so the frontend's completeMilestone(1) works immediately
- [x] Error contract: 404 unknown student/milestone/career (foreign milestones indistinguishable from unknown), 422 invalid stage/status, onboarding never 503s (deterministic fallback)
- [x] Phase 4 tests (39 tests, Qwen fully mocked — no API quota in tests)
- [x] Live validation with REAL Qwen (2026-08-29): onboarding NBA generated → journey cached → roadmap created → progress recalculated NBA → journey reflected new current step; qwen3.7-plus selected existing candidates in both real calls

### MCP Integration (Phase 5 — COMPLETED)
- [x] Two FastMCP servers mounted inside FastAPI over the SSE transport: `Mcp/career_server.py` (`/mcp/career/sse`) and `Mcp/opportunity_server.py` (`/mcp/opportunity/sse`)
- [x] 11 MCP tools total, all reading the same SQLite database through the shared session factory (`Mcp/db_access.py`):
  - Career server (5): `get_career`, `get_career_reality`, `get_required_skills`, `get_university_opportunities`, `get_scholarships`
  - Opportunity server (6): `search_internships`, `search_jobs`, `match_opportunity`, `search_sports_opportunities`, `search_sports_scholarships`, `search_university_sports`
- [x] Shared serialization/validation helpers (`Mcp/records.py`) — `city_matches` (Nationwide-aware, case-insensitive), deadline ordering, JSON parsing, uniform no-results message
- [x] Synchronous MCP client (`BackEnd/services/mcp_client.py`) — SDK SSE client bridged with asyncio.run; every transport failure converted to one controlled `MCPClientError`
- [x] Pattern B search orchestration (`BackEnd/services/mcp_search_service.py`) — `search_with_mcp()`: Qwen tool-calling loop via `ai_service.call_with_mcp`, ONE retry on MCP failure, then deterministic direct-database fallback (`data_quality: "unranked"` + note "Live ranking is temporarily unavailable."); ungrounded AI answers (no tool calls) are discarded in favour of the direct query
- [x] `call_with_mcp` in ai_service — Chat Completions tool-calling loop (Pattern B) alongside the existing Pattern A
- [x] Seed data: `data/seed/opportunities.json` (10 records) + `data/seed/sports_opportunities.json` (7 records), clearly labeled TEMPLATE data; seeded via `data/seed_db.py`
- [x] Phase 5 tests (50 tests in `tests/test_mcp.py` — tool behavior, validation, Pattern B loop, retry/fallback policy, live server mounting)
- [x] Live-verified with REAL Qwen qwen3.7-plus + real MCP SSE protocol (2026-08-29): grounded tool calls, ranked results, fallback paths

### Opportunities + Sports (Phase 6 — COMPLETED)
- [x] `GET /api/v1/opportunities` — database-only listing with `type` (internship/job/scholarship/education), `city` (Nationwide-aware, case-insensitive), `field`, `skills` (comma-separated, at-least-one rule) filters; inactive records excluded; soonest-deadline ordering; §10 empty envelope when no records
- [x] `GET /api/v1/sports` — database-only listing with `sport` (case-insensitive), `city`, `type` (tournament/trial/scholarship/programme) filters; same exclusions/ordering/envelope
- [x] `POST /api/v1/opportunities/match` — Pattern B: Qwen chooses which records to retrieve (search_internships/search_jobs via real MCP), then DETERMINISTIC scoring in code; response envelope `{matches, data_quality, summary, note, message}`; matches persisted into `student_opportunity_matches` (replace semantics)
- [x] `POST /api/v1/sports/match` — same Pattern B architecture for `{sport, location, level}` requests; eligibility evaluated against the student's education stage; never persisted (no table by design)
- [x] Deterministic scoring service (`BackEnd/services/matching_service.py`) — pure functions, no DB/AI:
  - Opportunities: `matched_required_skills / total_required_skills` (case-insensitive; 1.0 when none listed)
  - Sports: `met_scored_requirements / total_scored` — only `level` (vs requested player level) and `enrollment` (vs education stage) are scored; age requirements surfaced in `eligibility_missing` with "(not verified from your profile)" but never scored
  - §10 freshness rule: `last_verified` older than 30 days → `data_freshness: "unverified"`
  - Ranked ordering (score desc, soonest deadline); fallback keeps retrieval order (unranked)
- [x] Opportunity service (`BackEnd/services/opportunity_service.py`) — listing filters, match orchestration, ungrounded-answer guard, direct-DB fallback retrieval, persistence
- [x] Error contract (§10): 404 unknown student, 422 blank/missing/invalid fields, 503 total AI+MCP failure, 200 + message envelope for no results
- [x] Phase 6 tests (63 tests in `tests/test_opportunities.py` — unit scoring, router/listing, match paths incl. unranked fallback + ungrounded-AI replacement + persistence replace semantics + full-chain tests with only Qwen/transport mocked)
- [x] Live-verified with REAL Qwen qwen3.7-plus + real MCP (2026-08-30): both match endpoints returned `ai_interpreted` ranked matches with deterministic scores; opportunity matches persisted; sports matches not persisted; 65/65 live smoke checks passed (endpoints, MCP protocol, CORS, errors, journey regression, secrets scan)

### Coach Chat + Job Readiness (Phase 8 — COMPLETED)
- [x] `POST /api/v1/coach/chat` — AI mentor conversation with rate limiting (20 req/hr in-memory), context building from DB (profile, roadmap, career, opportunities), history trimming (5 messages, 2000 chars), Qwen Pattern A, post-validation (quick_actions max 3, suggested_resource verified against DB)
- [x] `POST /api/v1/job-readiness` — deterministic scoring (Skills 30%, Projects 20%, Internship 20%, CV 15%, Interview 15%) from DB milestones/profile, AI gap analysis with graceful fallback, hardcoded disclaimer always present
- [x] Rate limiter (`BackEnd/services/rate_limiter.py`) — thread-safe InMemoryRateLimiter, singleton instance, 429 response when limit hit
- [x] Coach prompts (`BackEnd/prompts/coach.py`) — built on master system prompt, grounding rules (no invented resources, max 3 quick_actions, JSON only)
- [x] Job readiness prompts (`BackEnd/prompts/job_readiness.py`) — scores are read-only for Qwen, gap explanation + recommendations only
- [x] Coach service (`BackEnd/services/coach_service.py`) — student context builder, history trimmer, post-validator, resource verification against DB
- [x] Job readiness service (`BackEnd/services/job_readiness_service.py`) — 5-component deterministic scoring, AI gap analysis with fallback, disclaimer enforcement
- [x] Phase 8 tests: `test_coach.py` (13 tests) + `test_job_readiness.py` (14 tests) — 256 total passing, zero regressions
- [x] Real-Qwen smoke test: coach chat 200 OK with personalised response, job readiness 200 OK with 8% score (correct for fresh profile)
- [x] Frontend: job readiness page (`/job-readiness`) with score display, component bars, gap analysis, recommendations, disclaimer; NavBar updated

### Security Hardening + Full QA (Phase 9 — COMPLETED)
- [x] Startup environment variable validation in `main.py` — app fails to start with clear error if DASHSCOPE_API_KEY, DASHSCOPE_WORKSPACE_ID, SECRET_KEY, or DATABASE_URL missing
- [x] Log sanitisation in `main.py` and `ai_service.py` — `sanitise_for_log()` replaces `sk-*` patterns with `[REDACTED]` before logging
- [x] Global exception handler improved — sanitised logging, no stack traces in responses
- [x] Backend endpoint QA: 25/25 checks passed (all 18 endpoints + error paths + security)
- [x] Security verified: no `sk-` in any API response, `.env` protected by `.gitignore`, no DASHSCOPE in frontend `.next/` bundle
- [x] Frontend build: 11 pages compiled successfully (including `/job-readiness`)
- [x] Frontend lint: 0 warnings, 0 errors
- [x] Browser E2E: 11/11 pages pass with real backend data, zero console errors
- [x] Backend pytest: 256 passed, 0 failed — zero regressions

## Not Yet Implemented

### Backend (Phase 10)
- [x] Dockerfile for Render deployment (`BackEnd/Dockerfile`) — Python 3.11-slim, repo-root build context, pre-seeds DB at build time, --workers 1 for SQLite
- [x] render.yaml configuration (`BackEnd/render.yaml`) — starter plan, persistent disk at /data, env var references
- [x] Startup seed hook — `seed_if_empty()` in `data/seed_db.py`, called from `main.py` on startup, non-fatal on failure
- [x] Root-level `.gitignore` — protects .env, .env.local, .next/, node_modules/, *.db, __pycache__/
- [x] Frontend `.env.local.example` — documents required env vars for deployment
- [x] `requirements.txt` updated with `mcp` and `sse-starlette` dependencies
- [ ] Deployment to Render + Vercel (manual — requires GitHub push + dashboard config)
- [ ] External smoke test (manual — requires deployed services)

### Qwen Integration
- [x] Pattern B (MCP tool calls) — DONE (Phase 5)
- [x] Feature-level prompt: coach — DONE (Phase 8)
- [x] Real-Qwen smoke test of /career/analyze and /career/trial-plan — DONE (Phase 6)
- [x] Real-Qwen smoke test of /coach/chat and /job-readiness — DONE (Phase 8)

### MCP
- [x] Pakistan Career & Education MCP server — DONE (Phase 5, 5 tools)
- [x] Pakistan Opportunities & Sports MCP server — DONE (Phase 5, 6 tools)

### Data
- [x] Seed JSON files — DONE: careers.json (15), opportunities.json (10), sports_opportunities.json (7) — all clearly labeled TEMPLATE data
- [ ] Seed files for universities + alumni
- [ ] Verified Pakistan-specific seed data (replaces template labels) — data phase
- [x] Database seeding script — DONE for careers + demo student + opportunities + sports (data/seed_db.py)

### Frontend Integration (Phase 7 — COMPLETED)
- [x] `NEXT_PUBLIC_USE_MOCK=false` switched — frontend now calls real FastAPI backend
- [x] Fixed critical `camelizeKeys` bug — API client was converting snake_case to camelCase but all components/types use snake_case; removed the conversion
- [x] Frontend API modules for opportunities (`Frontend/lib/api/opportunities.ts`) and sports (`Frontend/lib/api/sports.ts`)
- [x] Frontend type definitions for opportunities (`Frontend/lib/types/opportunity.types.ts`) and sports (`Frontend/lib/types/sports.types.ts`)
- [x] Opportunities page (`Frontend/app/opportunities/page.tsx`) — listing with filters + AI match section
- [x] Sports page (`Frontend/app/sports/page.tsx`) — listing with filters + AI match section
- [x] NavBar updated with Opportunities and Sports navigation links
- [x] End-to-end test of the full student flow: Home → Onboarding (6 steps submitted) → Journey (NBA displayed) → Careers (15 real careers) → Reality Check (AI verdict) → Trial Plan (7-day plan) → Opportunities (9 real records + AI match) → Sports (6 real records + AI match) → Mentor (coach chat working) → Job Readiness (8% score, disclaimer, components, gap analysis)
- [x] All 11 pages load without console errors; all data fields render correctly (no undefined/blank)
- [x] CORS verified: localhost:3000 allowed, unauthorized origins blocked
- [x] Security verified: API keys never in responses, not in Swagger, not in frontend bundles
- [x] `npm run build` passes (11 pages including /job-readiness)
- [x] `npm run lint` passes (0 warnings, 0 errors)
- [x] Backend pytest: 256 passed, 0 failed — zero regressions

### Infrastructure
- [ ] Root-level .gitignore (BackEnd/.gitignore exists and protects .env, *.db, __pycache__/, *.pyc); no git repository initialized yet

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Repository Audit | DONE |
| 1 | Backend Foundation | DONE (28 tests passing) |
| 2 | Qwen AI Service | DONE (23 mocked tests passing; real qwen3.7-plus call verified) |
| 3 | Career Intelligence (careers list/detail, analyze, trial-plan) | DONE (26 Phase 3 tests; 77 total passing; live endpoints verified) |
| 4 | Next Best Action + Journey (onboarding, journey, progress, roadmap) | DONE (39 Phase 4 tests; 116 total passing; real-Qwen live flow verified) |
| 5 | MCP Integration (2 FastMCP servers, 11 tools, Pattern B search) | DONE (50 Phase 5 tests; 166 total passing; real Qwen + real MCP verified) |
| 6 | Opportunities + Sports (4 endpoints, deterministic matching) | DONE (63 Phase 6 tests; 229 total passing; real Qwen + real MCP live smoke 65/65) |
| 7 | Testing + Integration (frontend switch, E2E, security) | DONE (229 backend tests; npm build + lint clean; 9/9 pages verified; all 14 API endpoints pass; CORS + security checks pass) |
| 8 | Coach Chat + Job Readiness (2 endpoints, rate limiting, deterministic scoring) | DONE (27 new tests; 256 total passing; real Qwen smoke verified; frontend job-readiness page added) |
| 9 | Full QA + Security Hardening (endpoint QA, build/lint, E2E browser test, log sanitisation) | DONE (256 backend tests; 25/25 endpoint QA; 11/11 browser pages; npm build + lint clean; security verified) |
| 10 | Deployment Prep (Dockerfile, render.yaml, seed hook, .gitignore) | DONE (Dockerfile verified, render.yaml ready, seed_if_empty hook wired, root .gitignore created; deployment itself is manual) |
