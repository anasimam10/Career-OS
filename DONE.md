# A&H Career — DONE.md

**Last updated:** 2026-09-01 (Final master-doc implementation — universities/alumni/learning endpoints, retrieval layer + FTS5 + cache, 8-stage ingestion pipeline + admin API, MCP expanded to 13 tools, controlled starter dataset, 534 tests passing)

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

### Qwen Model Fallback Chain (2026-08-30 — COMPLETED)
- [x] `qwen3.7-plus` remains the PRIMARY model — used for every call when healthy; never load-balanced, never randomly chosen
- [x] `qwen3.6-plus` configured as the BACKUP (`QWEN_FALLBACK_MODEL` in `BackEnd/config.py`, `.env`, `.env.example`)
- [x] Fallback triggers ONLY on eligible model-availability failures: HTTP 429 (rate limit/quota), 404 (model unavailable), >= 500 (provider capacity)
- [x] Non-eligible failures NEVER switch models: 401/403 (auth — config bug), 400 (bad request), connection/transport errors, Pydantic validation failures, unconfigured service
- [x] Both patterns support the chain: Pattern A (`call_structured`) and Pattern B (`call_with_mcp`) — same retry budget per model, same Pydantic validation pipeline, identical response contract
- [x] Hard limits enforced: max 2 models per call, max 1 fallback transition, no recursion, no same-model retry on rate limits
- [x] Attempt budget documented: Pattern A worst case 4 API calls (2 primary + 2 fallback); Pattern B one tool-loop per model
- [x] Future-ready: `_model_chain()` in `ai_service.py` — additional backup models can be added by appending to the list; callers never change (public signatures unchanged)
- [x] Internal marker `_ModelUnavailableError(AIUnavailableError)` — callers only see the existing public contract, zero router/service changes needed
- [x] Safe fallback logging: model names + operation + error category only; no keys, no prompts, no profiles (sanitisation reused)
- [x] 35 new mocked tests (`tests/test_model_fallback.py`) covering all 13 required categories — zero API quota consumed
- [x] Real verification: qwen3.7-plus primary call SUCCESS + direct qwen3.6-plus call SUCCESS (both validated as NextBestAction)
- [x] One existing test updated (`test_rate_limit_raises_immediately_without_retry`) — old contract (rate limit = immediate raise) superseded by the specified fallback contract; preserved intent: no same-model retry
- [x] Security re-verified: secrets only in `BackEnd/.env` (188-file workspace scan), `.env.example` placeholders only, fallback logs sanitized

### Four-Model Qwen Fallback Chain (2026-08-30 — COMPLETED)
- [x] Chain extended to the mandated four-model order: `qwen3.7-plus` → `qwen3.6-plus` → `qwen-plus-2025-07-28` → `qwen3-vl-235b-a22b-thinking` — primary unchanged, deterministic, never load-balanced
- [x] Configuration switched to ONE ordered list: `QWEN_FALLBACK_MODELS=qwen3.6-plus,qwen-plus-2025-07-28,qwen3-vl-235b-a22b-thinking` (replaces the single-model `QWEN_FALLBACK_MODEL`) in `config.py`, `.env`, `.env.example`, `render.yaml` — no numbered per-model variables
- [x] `_model_chain()` parses the ordered list (empty entries, duplicates, and entries equal to the primary are dropped; empty setting disables the fallback) — future models are configuration-only additions
- [x] Fallback rules unchanged: eligible = HTTP 429 / 404 / >= 500 only; non-eligible (400/401/403, transport, validation, unconfigured) never switch models
- [x] Hard limits: max 4 models per call, max 3 fallback transitions, never restarts at the primary, no recursion; Pattern A worst case 8 API calls (2 per model); Pattern B one tool-loop per model
- [x] Startup configuration validation in `main.py` (`REQUIRED_QWEN_MODELS` in `config.py`): all four models must be present in the resolved chain — configuration check only, no live API calls
- [x] Compatibility verified with REAL live calls for all four models, both patterns (json_object + Pydantic AND tools + tool_choice=auto): qwen3.7-plus, qwen3.6-plus, qwen-plus-2025-07-28, qwen3-vl-235b-a22b-thinking all PASS (8 smoke calls; the fallback transition itself is mock-tested — never deliberately triggered, to preserve quota)
- [x] 20 new mocked tests (`tests/test_four_model_fallback.py`) — all 14 spec-mandated test names (2 parametrized) plus a startup-validation test; zero API quota consumed
- [x] Existing fallback tests updated to the four-model contract (`test_model_fallback.py`, `test_ai_service.py`) — coverage preserved and strengthened, none deleted or weakened
- [x] Full regression: 311 passed, 0 failed, 0 skipped (291 existing + 20 new); frontend lint 0 warnings/errors; build 11 pages
- [x] Security re-verified: `BackEnd/.env` not tracked by git; 165 source files + 197 `.next` files scanned — zero secret matches; multi-model fallback logs carry model names / operation / error category only

### Master-Doc Schema, Trust Filters & Starter Dataset (Phase 11 — COMPLETED)
- [x] New models (architecture_master §10): `models/university.py` (University, Campus, Program), `models/learning.py` (LearningResource), `models/source.py` (Source, SourceDocument, IngestionRun, IngestionItem) — 17 models total
- [x] Additive-only migration in `database.py` (`_migrate_missing_columns()`): PRAGMA check + `ALTER TABLE ADD COLUMN`, idempotent, live `ah_career.db` keeps working; existing rows backfilled `verification_status='VALIDATED'` (opportunities/sports) and `is_active=1` (careers)
- [x] Additive columns: Opportunity (+verification_status, status, source_id, content_hash, dedup_key, retrieved_at, field, province, is_remote, organization_type, required_education_stage, required_degree_type, required_cgpa, stipend_pkr, eligibility_notes), SportsOpportunity (+verification_status, source_id, content_hash, dedup_key, retrieved_at), Career (+category, is_active), Alumni (+university_id, career_id, source_id, source_url)
- [x] SQLite FTS5 (master §14) in `retrieval/fts.py`: six external-content virtual tables (careers/opportunities/universities/programs/alumni/learning_resources) kept in sync by INSERT/UPDATE/DELETE triggers + idempotent rebuild at startup; quoted-token MATCH expressions (user input can never break FTS syntax); automatic LIKE fallback when FTS5 is unavailable
- [x] Student-visibility trust gates (master §11/§22) via shared `retrieval/visibility.py`: `verification_status IN (VALIDATED, VERIFIED)` + `is_active` + non-expired deadline filters applied in opportunity_service listings, MCP opportunity/sports tools + `match_opportunity`, career_service, and the new retrieval layer
- [x] `routers/careers.py`: additive optional `search` + `field` query params (FTS-backed) — frontend unaffected
- [x] Test fixtures strengthened in place (`VALIDATED` statuses, dynamic deadlines `today + timedelta`) — 311-baseline test count preserved exactly
- [x] Controlled starter dataset: `universities.json` (24 real universities, VERIFIED manual-entry mode D), `programs.json` (45, career links resolved at seed time), `learning_resources.json` (12 famous public resources, VERIFIED), `alumni.json` (6 TEMPLATE, is_verified=false), `opportunities.json` expanded to 22 records (future deadlines, fresh last_verified), `sports_opportunities.json` expanded to 8 records — each catalogue keeps one deliberate inactive/expired negative example proving the visibility gates; `data/seed_db.py` extended (insert-only, curated seeds seeded as VALIDATED — ingestion-created records always start CANDIDATE)

### Retrieval Layer + Cache (Phase 12 — COMPLETED)
- [x] `BackEnd/retrieval/` package (master §14): career/opportunity/university/sports/alumni/learning/student retrieval modules — typed dicts, trust + freshness filters everywhere, bounded result sets; no caller ever sends the whole knowledge base to Qwen
- [x] `BackEnd/cache.py`: `SimpleCache` with per-entry TTL (master §15), wired into career + university retrieval searches; cleared per test in `conftest.py`
- [x] `tests/test_retrieval.py` — 51 tests (FTS indexing/search, cache TTL, per-module retrieval + trust gates); 362 total passing

### Universities / Alumni / Learning Endpoints (Phase 13 — COMPLETED)
- [x] `routers/universities.py`: `GET /universities` (field/city/type/hec_recognized filters, `{universities, total}` envelope) + `GET /universities/{id}/programs` (field/degree_type filters)
- [x] `routers/alumni.py`: `GET /alumni` (field/career_id/university_id filters, verified-first ordering) + `GET /alumni/{id}` (card + provenance)
- [x] `routers/learning.py`: `GET /learning` (skill/level/type/is_free filters) — verified-only, NULL means unknown, never "free"
- [x] Schemas added additively (`schemas/responses.py`): UniversitySummary/List, ProgramSummary/List, AlumniDetail, LearningResourceOut/List; `AlumniCard` extended with Optional fields + is_verified (existing column names kept for the frontend contract)
- [x] Tests: `test_universities.py` (16) + `test_alumni.py` (12) + `test_learning.py` (12) — 402 total passing

### MCP Expansion — 13 Tools (Phase 14 — COMPLETED)
- [x] `Mcp/opportunity_server.py`: `find_alumni(field, career_id?, university_id?)` + `get_learning_resources(skill, level?)` added (master §16 → 8 tools on the opportunity server; 13 project-wide), both reusing the Phase 12 retrieval layer — no duplicate query logic
- [x] `tests/test_mcp.py` extended: `TestAlumniAndLearningTools` (11 tests) + SSE eight-tools listing + alumni tool round-trip (62 tests in file) — 414 total passing

### Ingestion Pipeline + Admin API (Phase 15 — COMPLETED)
- [x] 8-stage pipeline (master §12) in `BackEnd/ingestion/`:
  - `dedup_service.py` — text normalization, `type|title|organization` dedup_key, SHA-256 content_hash
  - `extraction_service.py` — Pattern A via the protected `ai_service` with the extraction-only prompt (`prompts/extraction.py`: "Return null for any field not explicitly stated"); deterministic HTML→text cleanup, 40k-char bound
  - `ingestion_service.py` — DISCOVER → RETRIEVE (httpx GET, User-Agent, 15s timeout, 512 KiB cap, unchanged-hash skip) → EXTRACT → VALIDATE (title + valid type + parseable deadline) → NORMALIZE → DEDUPLICATE (duplicates associate the source, never create a second record) → PERSIST (`verification_status='CANDIDATE'` — never auto-verified) → INDEX (FTS triggers) + stage 9 manual verification + mode C refresh (stale when `COALESCE(last_verified, retrieved_at) < now - 7 days`) + per-run/per-item status tracking + data-quality counters
- [x] `routers/admin.py` — 5 endpoints behind a constant-time, FAIL-CLOSED bearer gate (`ADMIN_TOKEN`, empty default rejects everything), hidden from Swagger (`include_in_schema=False`): `POST /admin/ingest/url` (max 50 URLs), `POST /admin/ingest/refresh`, `GET /admin/ingest/runs/{id}`, `GET /admin/data-quality`, `POST /admin/opportunities/{id}/verify`
- [x] Config: `ADMIN_TOKEN` in `config.py` + `.env` (random value) + `.env.example` (documentation only)
- [x] Tests: `test_ingestion.py` (42) + `test_deduplication.py` (24) + `test_freshness.py` (16) + `test_security.py` (38 — admin auth incl. fail-closed, Swagger hiding, secret hygiene, ingestion write protection, CORS, log sanitisation) — 534 total passing; Qwen/HTTP fully mocked
- [x] Live-verified (2026-09-01): 401 without token, 200 with token, admin absent from `/openapi.json`

### Final Regression + Live E2E (Phase 16 — COMPLETED)
- [x] Full pytest: 534 passed, 0 failed, 0 skipped (311 baseline preserved + 223 new); frontend `npm run lint` (0 warnings/errors) + `npm run build` (11 pages)
- [x] Security: `BackEnd/.env` untracked + gitignored; workspace secret scans clean; no real tokens anywhere except `.env`
- [x] Live E2E script `BackEnd/live_e2e.py` (2026-09-01, real app on a free port, real `ah_career.db`): full student journey with REAL Qwen — onboarding NBA → careers → reality check → trial plan → journey (cached NBA, zero AI) → progress (NBA recalc + backend-validated stage transition HIGH_SCHOOL → CAREER_DISCOVERY) → journey refresh → opportunity match + sports match over the real MCP SSE transport → universities → alumni → learning → coach chat → job-readiness
- [x] Live E2E result: 61/62 checks passed with exactly 9 real Qwen operations (all qwen3.7-plus, attempts=1); the one flagged check was the E2E's own first sports query (cricket-in-Karachi — the seed catalogue honestly has no such records; corrected query cricket-in-Lahore re-verified 3/3 with `data_quality=ai_interpreted`, 2 ranked matches)
- [x] Real ingestion proof in the same run: `POST /admin/ingest/url` with https://www.python.org/jobs/ → run COMPLETED, item STORED, new record CANDIDATE with linked source + content hash, **hidden from `GET /opportunities` (bare and type=job filtered)**, reported by `GET /admin/data-quality` as candidate_records=1 — students never see unverified data

### Documented Deviations (protected working code wins — master's final rule)
- [x] Sports opportunities stay in `sports_opportunities` (not unified into `opportunities`); NBA stays in `student_profiles.next_best_action` (no `next_best_actions` table); journey state stays in `students.education_stage` + roadmaps (no `journey_states` table)
- [x] No `skills`/`career_skills` registry tables — `careers.required_skills` JSON is the source of truth; learning resources use `skill_name` (master's own allowance)
- [x] No `opportunity_details`/`sports` registry tables; auth endpoints deferred (frontend has no auth UI; demo-student session is the protected contract)
- [x] No Qwen web_search discovery mode (mode B) — mode A (URL batch), mode C (refresh), mode D (manual entry via seeds) are implemented
- [x] Ingestion runs execute synchronously within the admin request instead of background tasks (bounded: max 50 URLs, immediately queryable)
- [x] `data_freshness` keeps the "unverified" label (semantics = master's STALE > 30 days); AlumniCard keeps model column names per the existing frontend contract

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
- [x] Feature-level prompt: ingestion extraction — DONE (Phase 15, `prompts/extraction.py`)
- [x] Real-Qwen smoke test of /career/analyze and /career/trial-plan — DONE (Phase 6)
- [x] Real-Qwen smoke test of /coach/chat and /job-readiness — DONE (Phase 8)
- [x] Real-Qwen full-journey live E2E incl. ingestion extraction — DONE (Phase 16, `BackEnd/live_e2e.py`, 9 AI operations)

### MCP
- [x] Pakistan Career & Education MCP server — DONE (Phase 5, 5 tools)
- [x] Pakistan Opportunities & Sports MCP server — DONE (Phase 5, 6 tools; +`find_alumni` +`get_learning_resources` in Phase 14 → 8 tools; 13 project-wide)

### Data
- [x] Seed JSON files — DONE: careers.json (15), universities.json (24, VERIFIED manual-entry), programs.json (45), learning_resources.json (12, VERIFIED), alumni.json (6, TEMPLATE), opportunities.json (22), sports_opportunities.json (8) — opportunity/sports/alumni files carry honest TEMPLATE labels
- [x] Seed files for universities + alumni — DONE (Phase 11)
- [ ] Verified Pakistan-specific data replacing the remaining TEMPLATE labels (opportunities/sports/alumni) — data phase; universities/programs/learning are manual-entry VERIFIED facts already
- [x] Database seeding script — DONE for every seed file + demo student (`data/seed_db.py`, insert-only, never overwrites)

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
- [x] Root-level .gitignore (BackEnd/.gitignore also protects .env, *.db, __pycache__/, *.pyc); git repository initialized — `BackEnd/.env` verified untracked and ignored

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
| 11 | Master-Doc Schema, Trust Filters & Starter Dataset (models, migration, FTS5, verification gates, seed expansion) | DONE (additive migration verified on live DB; 6 FTS tables; 24/45/12/6/22/8 seed records; 362 total passing) |
| 12 | Retrieval Layer + Cache (master §14/§15) | DONE (7 retrieval modules + SimpleCache TTL; 51 tests in test_retrieval.py) |
| 13 | Universities / Alumni / Learning endpoints | DONE (5 new endpoints; 40 tests; 402 total passing) |
| 14 | MCP expansion — find_alumni + get_learning_resources | DONE (13 tools project-wide; 12 new MCP tests; 414 total passing) |
| 15 | Ingestion pipeline + admin API (master §12/§17) | DONE (8 stages + stage 9 verify + refresh; 5 admin endpoints, fail-closed auth; 120 new tests; 534 total passing) |
| 16 | Final regression + live E2E + docs | DONE (534 pytest; lint/build clean; security re-verified; live E2E 61/62 + corrected sports query 3/3 with 9+1 real Qwen operations; one real URL ingested as CANDIDATE, hidden from students) |
