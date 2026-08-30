# A&H Career — Implementation Status

**Audit date:** 2026-08-30 (last updated after Phase 9 — full QA, security hardening, 256 tests, 11/11 pages verified)
**Audited by:** Qoder (backend/AI/MCP engineer role)

---

## 1. Existing — What Already Works

### Frontend (Next.js 14)
- Complete Next.js 14.2.5 App Router application with TypeScript and Tailwind CSS
- 6 pages implemented: Home (`/`), Onboarding (`/onboarding`), Careers listing (`/careers`), Career detail (`/careers/[slug]`), Career reality check (`/careers/[slug]/reality-check`), Career trial (`/careers/[slug]/trial`), Journey (`/journey`), Mentor chat (`/mentor`)
- Full component library: NavBar, Footer, PageTransition, CareerCard, CareerMetricBar, CareerVerdict, MotivationBar, RealityCheckPanel, TrialPlanView, JourneyTimeline, NextStepCard, RoadmapSteps, CoachChat, ChatMessage, QuickActions, TypingIndicator, OnboardingWizard (6 steps), StepIndicator, shared states (Empty, Error, Loading), ProgressBar, SectionHeader
- UI primitives: badge, button, card, input, progress, separator, skeleton (shadcn-style)
- Mock data toggle system (`NEXT_PUBLIC_USE_MOCK=true`) — frontend runs fully standalone with mock data
- API client layer with snake_case → camelCase automatic conversion
- Session management via localStorage (demo student ID=1)
- Hooks: `useOnboarding`, `useCareerAnalysis`, `useCoachChat`, `useJourney`
- Framer Motion animations, Lucide icons, Radix UI primitives
- `node_modules` present — dependencies already installed

### Docs
- `architecture_corrected.md` — comprehensive 1,092-line architecture document covering product definition, system layers, Qwen integration (Pattern A + B), MCP architecture, database schema (9 tables), complete API map, Pydantic schemas, error handling, folder structure, security model, implementation order, and MVP definition of done
- `step2 Spec Qoder-AI-Coding-Hands-on-Lab-Guide.md` — reference lab guide (unrelated to this project's features; it is a Qoder demo guide for a Spring Boot order system)

---

## 2. Backend — What Exists and What Is Missing

### Completed (Phase 1)
- FastAPI application with CORS, logging, and global error handler (`BackEnd/main.py`)
- Environment configuration (`BackEnd/config.py`, `BackEnd/.env.example`)
- SQLAlchemy engine/session with SQLite WAL mode and foreign keys (`BackEnd/database.py`)
- All 9 SQLAlchemy models: `students`, `student_profiles`, `careers`, `roadmaps`, `milestones`, `alumni`, `opportunities`, `sports_opportunities`, `student_opportunity_matches` (`BackEnd/models/`)
- Pydantic schemas: shared enums, request payloads, response models (`BackEnd/schemas/`)
- Repository layer: BaseRepository, StudentRepository, CareerRepository (`BackEnd/repositories/`)
- Health endpoint: `GET /api/v1/health` → `{"status": "ok"}`
- Test suite: 28 tests (health, CORS, DB init, models, repositories, Pydantic validation) — all passing
- Python venv with pinned dependencies (`BackEnd/requirements.txt`)

### Completed (Phase 3 — Career Intelligence)
- Career router (`BackEnd/routers/careers.py`) with all four endpoints:
  - `GET /api/v1/careers` — list (database only, no AI)
  - `GET /api/v1/careers/{slug}` — full record (database only; 404 with `{error}` for unknown slug)
  - `POST /api/v1/career/analyze` — Career Reality Check (Qwen Pattern A)
  - `POST /api/v1/career/trial-plan` — 7-day trial plan (Qwen Pattern A)
- Career service (`BackEnd/services/career_service.py`)
  - Reuses Phase 1 repositories and the Phase 2 `ai_service` (no new client, no config duplication)
  - Trust hierarchy enforced in code: after Pydantic validation, CareerReality factual fields are overwritten with SQLite values; Qwen only contributes `rewards` + the verdict
  - `data_source` computed from real record metadata + honest template-data label
  - Trial plan contract pinned in code: `career_slug` from request, `duration_days = 7`
  - Demo student session context (id=1, matches `Frontend/lib/session.ts`); honest "not yet onboarded" context when the student is missing
  - Error mapping: 404 unknown career, 422 invalid request, 503 AI unavailable, 500 AI output unprocessable (architecture §10)
- Career prompts (`BackEnd/prompts/career_analysis.py`, `BackEnd/prompts/trial_plan.py`) — built on the master system prompt via `build_system_prompt()`; no policy duplication
- Seed data: `data/seed/careers.json` (15 careers, labeled TEMPLATE data converted from the frontend mock) + `data/seed_db.py` (insert-only, never overwrites; also creates the demo student)
- Phase 3 tests: `BackEnd/tests/test_career.py` (26 tests, Qwen fully mocked)
- Live-verified: server start, `/docs`, all four routes in Swagger, seeded GET responses

### Completed (Phase 4 — Next Best Action + Journey)
- Routers: `BackEnd/routers/onboarding.py` (`POST /onboarding`) and `BackEnd/routers/journey.py` (`GET /journey`, `POST /progress`, `POST /roadmap`), registered in `main.py`
- Journey state machine: `BackEnd/services/journey_state.py`
  - `VALID_TRANSITIONS` map — the three architecture §6 transitions plus the smallest sensible deterministic completion of the remaining stages (documented Phase 4 decision); FIRST_JOB is terminal
  - `parse_stage` / `is_valid_transition` / `next_stage_with_pending` — pure functions, no state-machine library
  - Stage changes happen ONLY through backend-validated milestone completion (progress_service) — never automatically, never by the AI
- Deterministic candidate generator: `BackEnd/services/candidate_service.py` — 3–8 candidates per call from stage templates + verified career data; the learn-a-skill candidate is derived from the career's DB `required_skills` minus the student's profile skills (nothing invented); completed milestone titles retire their candidates; no Qwen calls
- NBA engine: `BackEnd/services/nba_service.py` — candidate-constrained selection: Qwen returns ONLY `{candidate_id, why_this_matters}` (internal `NBASelection` wrapper; the public `NextBestAction` contract is unchanged); every other field is copied from the deterministic candidate in code; unknown candidate_id → ONE retry → deterministic highest-priority fallback; AI unavailability → same fallback (journey never dead-ends); result persisted in `student_profiles.next_best_action` as a JSON blob with candidate_id + completed-milestone snapshot + timestamp; `GET /journey` reuses the cache whenever the candidate pool and completed-milestone snapshot are unchanged (no Qwen on refresh)
- NBA prompt: `BackEnd/prompts/next_best_action.py` — student context + journey state + candidate list injected through `build_system_prompt()`; "select exactly ONE candidate_id" + no-invention rules
- Roadmap service: `BackEnd/services/roadmap_service.py` — deterministic stage milestone templates (shared with the candidate generator), idempotent instantiation (dedupe key = (stage, title) because several stages legitimately reuse template titles), `MAX_VISIBLE_STEPS = 3` progressive disclosure, `ensure_stage_milestones` used by onboarding to bootstrap the journey
- Onboarding service: `BackEnd/services/onboarding_service.py` — accepts the wizard payload exactly; display-name `career_interests` (e.g. "Software Engineering") resolved to verified career slugs; "Not sure yet" stays no-goal; creates the demo student (id=1) when missing; invalidates the cached NBA; bootstraps stage milestones
- Progress service: `BackEnd/services/progress_service.py` — validates ownership (foreign milestones return the same 404 as unknown ones), records `completed_at`, advances the stage only when the current stage is exhausted AND a valid transition leads to a stage with pending milestones, then force-recalculates the NBA
- Error contract: 404 unknown student/milestone/career, 422 invalid target stage / milestone status; onboarding and progress never return 503 for AI failures (deterministic fallback keeps the journey loop alive — documented deviation from the generic §10 mapping)
- Phase 4 tests: `BackEnd/tests/test_journey.py` (39 tests, Qwen fully mocked; grounding proven by asserting NBA content comes from the deterministic candidate, never from the AI)
- Live-verified with REAL qwen3.7-plus (2026-08-29): onboarding → NBA; journey → cached NBA + correct stage; roadmap → 3 visible steps; progress → NBA recalculated with a new personalized rationale; journey again → advanced current step. Qwen selected existing candidates in both real calls

### Completed (Phase 5 — MCP Integration)
- Two FastMCP servers mounted inside the FastAPI app over the SSE transport (`main.py`): `Mcp/career_server.py` → `/mcp/career/sse`, `Mcp/opportunity_server.py` → `/mcp/opportunity/sse`
- 11 MCP tools, all reading the same SQLite database through the shared session factory (`Mcp/db_access.py`):
  - Career server (5): `get_career`, `get_career_reality`, `get_required_skills`, `get_university_opportunities`, `get_scholarships`
  - Opportunity server (6): `search_internships`, `search_jobs`, `match_opportunity`, `search_sports_opportunities`, `search_sports_scholarships`, `search_university_sports`
- Shared helpers (`Mcp/records.py`): `city_matches` (Nationwide-aware, case-insensitive), deadline ordering, JSON parsing, uniform no-results message; every tool validates its inputs and returns `count`/`results` JSON
- Synchronous MCP client (`BackEnd/services/mcp_client.py`): SDK SSE client bridged with asyncio.run, one short-lived session per call, every transport failure converted to one controlled `MCPClientError`
- Pattern B search orchestration (`BackEnd/services/mcp_search_service.py`): `search_with_mcp()` drives the Qwen tool-calling loop (`ai_service.call_with_mcp`, added in Phase 5), retries ONCE on MCP failure, then falls back to a deterministic direct-database query (`data_quality: "unranked"` + note "Live ranking is temporarily unavailable."); ungrounded AI answers (no tool calls) are discarded in favour of the direct query
- Seed data: `data/seed/opportunities.json` (10 records) + `data/seed/sports_opportunities.json` (7 records), labeled TEMPLATE data, seeded by `data/seed_db.py`
- Phase 5 tests: `BackEnd/tests/test_mcp.py` (50 tests — tool behavior, input validation, Pattern B loop, retry/fallback policy, mounted-server integration; Qwen mocked, MCP transport exercised)
- Live-verified with REAL qwen3.7-plus + real MCP SSE protocol (2026-08-29)

### Completed (Phase 6 — Opportunities + Sports)
- Routers: `BackEnd/routers/opportunities.py` (`GET /opportunities`, `POST /opportunities/match`) and `BackEnd/routers/sports.py` (`GET /sports`, `POST /sports/match`), registered in `main.py`
- Deterministic scoring service (`BackEnd/services/matching_service.py`) — pure functions, no DB/AI access:
  - Opportunities: `match_score = matched_required_skills / total_required_skills` (case-insensitive; 1.0 when none listed) — mirrors the Phase 5 `match_opportunity` tool rule
  - Sports: `match_score = met_scored_requirements / total_scored` — only `level` (vs the requested player level) and `enrollment` (vs the student's education stage via `enrollment_category`) are scored; age requirements are surfaced in `eligibility_missing` with "(not verified from your profile)" but never scored
  - Architecture §10 freshness rule: `last_verified` older than 30 days → `data_freshness: "unverified"`
  - Ranked ordering (score desc, then soonest deadline); the unranked fallback keeps retrieval order
- Opportunity service (`BackEnd/services/opportunity_service.py`) — listing filters (type/city/field/skills with the at-least-one rule), Pattern B match orchestration, ungrounded-answer guard, direct-DB fallback retrieval, persistence into `student_opportunity_matches` with REPLACE semantics (delete + insert; errors logged and swallowed); sports matches never persisted (no table, by design)
- Documented Phase 6 decisions:
  - Match responses use an envelope `{matches, data_quality, summary, note, message}` instead of the bare `[OpportunityMatch]` list from architecture §8, so the §10 fallback metadata (`data_quality`, `note`) can be carried
  - `opportunity_type` on POST /opportunities/match is restricted to internship/job (only these have MCP search tools); scholarship/education records are browse-only via GET /opportunities
  - `skills` on the match request overrides the student profile skills when provided
  - Nationwide location records match every city (shared `city_matches` rule) and produce the "Open nationwide" match reason
- Error contract (architecture §10): 404 unknown student, 422 blank/missing/invalid fields, 503 total AI+MCP failure, 200 + `{opportunities: [], message}` envelope for no results
- Phase 6 tests: `BackEnd/tests/test_opportunities.py` (63 tests — unit scoring incl. freshness + ranking, router/listing filters + envelopes + 422s, match paths incl. unranked fallback, ungrounded-AI replacement, persistence replace semantics, and full-chain tests that run the real `call_with_mcp` loop with only the Qwen client + MCP transport mocked)
- Live-verified with REAL qwen3.7-plus + real MCP (2026-08-30, 65/65 smoke checks): both match endpoints returned `ai_interpreted` ranked matches with deterministic scores; opportunity matches persisted; sports matches not persisted; CORS, error paths, journey regression, and secrets scan all green

### Still Missing (Phase 10 — Deployment)
- Dockerfile for Render deployment
- render.yaml configuration
- Startup seed hook (seed_if_empty)
- Actual deployment to Render + Vercel

### Completed (Phase 7 — Frontend ↔ Backend Integration)
- Frontend switched from mock to real backend: `NEXT_PUBLIC_USE_MOCK=false` in `Frontend/.env.local`
- Fixed critical `camelizeKeys` bug in `Frontend/lib/api/client.ts` — the API client was converting snake_case response keys to camelCase, but all TypeScript types and components use snake_case; removed the conversion so backend snake_case passes through directly
- Created `Frontend/lib/types/opportunity.types.ts` and `Frontend/lib/types/sports.types.ts` — TypeScript interfaces aligned with backend Pydantic schemas
- Created `Frontend/lib/api/opportunities.ts` — `getOpportunities()` (GET with filters, handles §10 empty envelope) + `matchOpportunities()` (POST)
- Created `Frontend/lib/api/sports.ts` — `getSports()` (GET with filters, handles §10 empty envelope) + `matchSports()` (POST)
- Created `Frontend/app/opportunities/page.tsx` — browse section with type/search filters, AI match section with city + type selection
- Created `Frontend/app/sports/page.tsx` — browse section with sport/type filters, AI match section with sport + location + level
- Updated `Frontend/components/layout/NavBar.tsx` — added Opportunities (Briefcase icon) and Sports (Trophy icon) navigation links
- All 14 API endpoints verified: health, careers list, career detail, career analyze, trial plan, onboarding, journey, roadmap, progress, opportunities list, opportunities match, sports list, sports match, coach/chat (404 expected)
- CORS verified: `localhost:3000` allowed, unauthorized origins blocked (HTTP 400)
- Security verified: API keys not in responses, not in Swagger, not in frontend bundles; `.env` excluded by `.gitignore`
- `npm run build`: 10 pages (including /opportunities and /sports), compiled successfully
- `npm run lint`: 0 warnings, 0 errors
- Backend pytest: 229 passed, 0 failed — zero regressions

### Completed (Phase 8 — Coach Chat + Job Readiness)
- Coach router (`BackEnd/routers/coach.py`): `POST /api/v1/coach/chat` with rate limiting (20 req/hr), blank message validation, AI error handling
- Job readiness router (`BackEnd/routers/job_readiness.py`): `POST /api/v1/job-readiness` with 404 for missing student
- Coach service (`BackEnd/services/coach_service.py`): context building from DB (profile, roadmap, career, opportunities), history trimming (5 messages, 2000 chars), Qwen Pattern A, post-validation (quick_actions max 3, suggested_resource verified against DB)
- Job readiness service (`BackEnd/services/job_readiness_service.py`): deterministic 5-component scoring (Skills 30%, Projects 20%, Internship 20%, CV 15%, Interview 15%), AI gap analysis with graceful fallback, hardcoded disclaimer
- Rate limiter (`BackEnd/services/rate_limiter.py`): thread-safe InMemoryRateLimiter, singleton instance
- Prompts: `BackEnd/prompts/coach.py` and `BackEnd/prompts/job_readiness.py` — built on master system prompt
- Phase 8 tests: `test_coach.py` (13 tests) + `test_job_readiness.py` (14 tests) — 256 total passing
- Frontend: job readiness page (`Frontend/app/job-readiness/page.tsx`), API module, types, NavBar updated
- Real-Qwen smoke test: both endpoints verified with actual qwen3.7-plus calls

### Completed (Phase 9 — Full QA + Security Hardening)
- Startup environment variable validation in `main.py` — fails fast if DASHSCOPE_API_KEY, DASHSCOPE_WORKSPACE_ID, SECRET_KEY, or DATABASE_URL missing
- Log sanitisation in `main.py` and `ai_service.py` — `sanitise_for_log()` replaces `sk-*` patterns with `[REDACTED]`
- Global exception handler improved — sanitised logging, no stack traces in responses
- Backend endpoint QA: 25/25 checks passed (all endpoints + error paths + security)
- Security verified: no `sk-` in any API response, `.env` protected, no DASHSCOPE in frontend `.next/`
- Frontend build: 11 pages compiled successfully
- Frontend lint: 0 warnings, 0 errors
- Browser E2E: 11/11 pages pass with real backend data, zero console errors
- Backend pytest: 256 passed, 0 failed — zero regressions
- Browser verification: all 9 pages load with real data, no console errors, no undefined/blank fields, AI-dependent pages (Reality Check, Trial Plan, Opportunity Match, Sports Match) return valid results from real Qwen calls

---

## 3. Frontend — What Exists and What API/Data Assumptions It Makes

### Current State
Frontend is **fully functional** with mock data. Switching `NEXT_PUBLIC_USE_MOCK=false` will attempt real API calls.

### Expected API Endpoints (from `Frontend/lib/api/*.ts`)

| Method | Endpoint | Request Body | Response Type | File |
|--------|----------|-------------|---------------|------|
| GET | `/careers` | — | `CareerListItem[]` | `careers.ts` |
| GET | `/careers/{slug}` | — | `Career` | `careers.ts` |
| POST | `/career/analyze` | `{career_slug}` | `CareerRealityResponse` (reality + verdict) | `careers.ts` |
| POST | `/career/trial-plan` | `{career_slug}` | `CareerTrialPlan` | `careers.ts` |
| POST | `/onboarding` | `OnboardingPayload` | `OnboardingResponse` (profile_updated + NBA) | `onboarding.ts` |
| GET | `/journey` | — | `JourneyResponse` (stage, current_step, next_steps[], NBA) | `journey.ts` |
| POST | `/progress` | `{milestone_id, status: "done"}` | `ProgressResponse` (new_stage + NBA) | `journey.ts` |
| POST | `/roadmap` | `{career_slug, target_stage}` | `RoadmapResponse` | `journey.ts` |
| POST | `/coach/chat` | `CoachChatPayload` (message + conversation_history) | `CoachResponse` | `coach.ts` |

**Implemented so far (backend):** `GET /careers`, `GET /careers/{slug}`, `POST /career/analyze`, `POST /career/trial-plan` (Phase 3), `POST /onboarding`, `GET /journey`, `POST /progress`, `POST /roadmap` (Phase 4), `GET /opportunities`, `POST /opportunities/match`, `GET /sports`, `POST /sports/match` (Phase 6), plus `GET /health` (Phase 1). The existing frontend hooks (`useOnboarding`, `useJourney`) now have matching backend endpoints — switching `NEXT_PUBLIC_USE_MOCK=false` connects them. Frontend API modules for the Phase 6 endpoints (opportunities/sports) are Phase 7 scope.

### Base URL
`http://localhost:8000/api/v1` (from `NEXT_PUBLIC_API_URL` env var, default in `client.ts`)

### Type Definitions (from `Frontend/lib/types/`)
- **EducationStage**: 10 values — HIGH_SCHOOL, CAREER_DISCOVERY, CAREER_DECISION, UNIVERSITY, SKILL_BUILDING, PROJECTS, INTERNSHIP, FINAL_YEAR, JOB_PREPARATION, FIRST_JOB
- **CareerListItem**: `{slug, name, field, demand_level}`
- **Career**: adds `competition_level, difficulty_level, required_skills[], pk_opportunities[], top_pk_universities[], risks[], last_updated`
- **CareerReality**: `{career_name, demand_level, competition_level, difficulty_level, required_skills[], pk_opportunities[], risks[], rewards[], data_source}`
- **CareerVerdict**: `{verdict: GOOD_FIT|WORTH_EXPLORING|RECONSIDER, headline, reasoning, student_strengths_match[], gaps_to_address[], suggested_trial}`
- **CareerRealityResponse**: `{reality: CareerReality, verdict: CareerVerdict}`
- **CareerTrialPlan**: `{career_slug, duration_days, days: [{day_range, title, tasks[]}], reflection_prompt}`
- **NextBestAction**: `{title, description, steps[], estimated_time, why_this_matters, stage}`
- **JourneyResponse**: `{stage, current_step, next_steps: JourneyStep[], next_best_action}`
- **JourneyStep**: `{title, description, stage, estimated_duration}`
- **ProgressResponse**: `{new_stage, next_best_action}`
- **RoadmapResponse**: `{roadmap_id, current_step, visible_steps: JourneyStep[]}`
- **OnboardingPayload**: `{education_stage, interests[], career_interests[], sports_interest, motivation_tags[], skills: [{name, level}], city}`
- **OnboardingResponse**: `{profile_updated, next_best_action}`
- **CoachChatPayload**: `{message, conversation_history: [{role, content}]}`
- **CoachResponse**: `{message, quick_actions[], suggested_resource}`

### Key Frontend Assumptions
1. Backend returns **snake_case JSON** (frontend converts to camelCase at boundary)
2. Standard HTTP error responses with `{error: string}` body
3. Session identity is demo student (ID=1) — no auth headers sent
4. No auth endpoints called — registration/login not yet implemented in frontend API layer
5. `visible_next_steps` never exceeds 3 items (enforced by both frontend and architecture)

---

## 4. Database — What Exists and What Is Missing

### Exists
- SQLite database file (`BackEnd/ah_career.db`) with all 9 tables (created at startup / by the seeder)
- **Careers seed data**: `data/seed/careers.json` — 15 careers clearly labeled as TEMPLATE data (converted from the frontend mock; full records for software-engineering, data-science, medicine; list-level records for the other 12)
- **Opportunities seed data**: `data/seed/opportunities.json` — 10 records (4 internships, 2 jobs, 2 education, 2 scholarships) labeled TEMPLATE data
- **Sports seed data**: `data/seed/sports_opportunities.json` — 7 records (trials, tournaments, scholarships, programmes across Badminton, Cricket, Football, Hockey) labeled TEMPLATE data
- **Seeder**: `data/seed_db.py` — insert-only (never overwrites existing records), creates the demo student (id=1) with a profile
- **Live data**: 15 careers, 10 opportunities (9 active), 7 sports opportunities (6 active), 1 demo student; `student_opportunity_matches` populated by POST /opportunities/match (replace semantics)

### Missing
- `data/seed/universities.json`
- `data/seed/alumni.json`
- **Verified Pakistan-specific data** to replace the template labels (data phase)

---

## 5. Qwen — What Exists and What Is Missing

### Completed (Phase 2 — COMPLETE: 23 unit tests passing + real connectivity verified)
- Reusable AI service: `BackEnd/services/ai_service.py`
  - Pattern A only: Chat Completions with `response_format={"type": "json_object"}`
  - `call_structured(prompt, response_model, system_prompt=None, operation=...)` → validated Pydantic object
  - Centralized retry: maximum ONE retry (transport errors, malformed JSON, schema failures)
  - Controlled exceptions: `AIServiceError`, `AIValidationError`, `AIUnavailableError`
  - Handles: APIConnectionError, APITimeoutError, RateLimitError, APIError, empty/missing content, markdown-fenced JSON, think-tag reasoning blocks
  - Base URL normalization: scheme (`https://`) and `/compatible-mode/v1` path completed automatically when the configured value is a bare hostname
  - Configurable timeout (`AI_TIMEOUT_SECONDS`, default 60s)
  - Lazy singleton client (`get_ai_service()`) — never created per request
  - Secrets never logged or included in exceptions
- Master system prompt: `BackEnd/prompts/system_prompt.py`
  - Pakistan-focused mentor persona, data trust hierarchy, no-invention rules, JSON-only output
  - `build_system_prompt()` with injection slots (student profile, verified data, schema name, extra rules)
- Configuration: `DASHSCOPE_API_KEY`, `DASHSCOPE_WORKSPACE_ID`, `DASHSCOPE_BASE_URL`, `QWEN_MODEL` (default `qwen3.7-plus`) via `BackEnd/config.py` + `BackEnd/.env`
- `.env.example` with placeholders only (no real credentials)
- Mocked unit tests: `BackEnd/tests/test_ai_service.py` (23 tests — zero API quota)
- Manual real-connection proof script: `BackEnd/test_qwen.py` (one real call, validates `NextBestAction`, never prints credentials)

### Real connectivity — VERIFIED (2026-08-29)
- `BackEnd/test_qwen.py` executed with real credentials in `BackEnd/.env`
- Result: **SUCCESS** — `qwen3.7-plus` responded; output parsed as JSON and validated as `NextBestAction` via Pydantic
- One real API call used for the proof (connection-level failure was diagnosed and fixed via base-URL normalization before the successful call; no quota wasted on debugging)

### Missing (later phases)
- Nothing for MVP scope (all required prompts are done — career_analysis, trial_plan, next_best_action, coach, job_readiness)

### Completed later
- Pattern B (Qwen tool calling over MCP) — DONE in Phase 5 (`ai_service.call_with_mcp` + `mcp_search_service.search_with_mcp` with retry + deterministic fallback); consumed by Phase 6 opportunities/sports matching
- Real-Qwen smoke tests of the Phase 3 endpoints — DONE (2026-08-30, Phase 6 full-project test)

---

## 6. MCP — What Exists and What Is Missing

### Exists (Phase 5 — COMPLETE)
- Two FastMCP servers mounted inside FastAPI over the SSE transport:
  - `Mcp/career_server.py` → `/mcp/career/sse` (5 tools: `get_career`, `get_career_reality`, `get_required_skills`, `get_university_opportunities`, `get_scholarships`)
  - `Mcp/opportunity_server.py` → `/mcp/opportunity/sse` (6 tools: `search_internships`, `search_jobs`, `match_opportunity`, `search_sports_opportunities`, `search_sports_scholarships`, `search_university_sports`)
- Shared database access (`Mcp/db_access.py`) and serialization helpers (`Mcp/records.py`)
- Synchronous MCP client with controlled error handling (`BackEnd/services/mcp_client.py`)
- Pattern B orchestration with one retry + deterministic direct-DB fallback (`BackEnd/services/mcp_search_service.py`)
- 50 Phase 5 tests (`BackEnd/tests/test_mcp.py`); live-verified with real Qwen + real MCP SSE protocol

### Missing
- Nothing for the MVP scope (both architecture-specified servers exist). Third-party MCP servers are explicitly out of scope (architecture §9).

---

## 7. Data — What Is Already Present and What Needs Seeding

### Present
- `data/seed/careers.json` (15 careers, TEMPLATE), `data/seed/opportunities.json` (10 records, TEMPLATE), `data/seed/sports_opportunities.json` (7 records, TEMPLATE) + seeder `data/seed_db.py`
- Mock data in `Frontend/lib/mock/` contains sample structures for:
  - 15 career list items (realistic Pakistani fields)
  - 3 full career records (software-engineering, data-science, medicine) with Pakistani universities (FAST-NUCES, LUMS, NUST, etc.)
  - 1 complete reality check + verdict (software-engineering)
  - 1 complete 7-day trial plan (software-engineering)
  - Journey state with NBA, 3 next steps
  - 3 coach response patterns (default, next_step, internship)

### Needs Seeding
- 10–15 verified Pakistani career records (architecture target)
- Several high-quality opportunity records (internships, jobs, scholarships)
- Small sports dataset (tournaments, trials, scholarships across 5+ sports)
- A few alumni records
- All data must be Pakistan-specific with source metadata

---

## 8. API — Existing Endpoints and Missing Endpoints

### Existing Endpoints
- `GET /api/v1/health` → `{"status": "ok"}` (Phase 1, verified working)
- `GET /api/v1/careers`, `GET /api/v1/careers/{slug}` (Phase 3, verified)
- `POST /api/v1/career/analyze`, `POST /api/v1/career/trial-plan` (Phase 3, verified)
- `POST /api/v1/onboarding`, `GET /api/v1/journey`, `POST /api/v1/progress`, `POST /api/v1/roadmap` (Phase 4, verified live with real Qwen)
- `GET /api/v1/opportunities`, `POST /api/v1/opportunities/match`, `GET /api/v1/sports`, `POST /api/v1/sports/match` (Phase 6, verified live with real Qwen + real MCP 2026-08-30)

### Missing Endpoints (from architecture §8, aligned with frontend expectations)

| Priority | Endpoint | Purpose |
|----------|----------|--------|
| P2 | `POST /api/v1/auth/register` | Student registration |
| P2 | `POST /api/v1/auth/login` | Student login |
| P2 | `GET /api/v1/alumni` | Alumni discovery |

**Implemented:** All MVP endpoints (18 total) are live and verified.

---

## 9. Architecture Mismatches

### Minor Discrepancies Found
1. **Architecture file name**: Architecture doc is `architecture_corrected.md` (not `architecture.md` as referenced in some places). Treat `architecture_corrected.md` as authoritative.
2. **Qwen model reference**: Architecture mentions `qwen3.8-max` — this is a future model reference. Actual available models should be verified against the user's Alibaba Cloud account.
3. **Folder naming**: Architecture uses lowercase (`backend/`, `mcp/`, `data/`), actual directories are capitalized (`BackEnd/`, `Mcp/`, `data/`). **Decision needed**: Should backend code live inside `BackEnd/` (existing capital directory) or should we create lowercase `backend/` inside it? **Recommendation**: Use `BackEnd/` as the parent and create files directly inside it (e.g., `BackEnd/main.py`).
4. **Frontend mock data `MotivationAnalysis` type**: The frontend defines a `MotivationAnalysis` type with a `factors` field (array of `{label, value}`) that is not present in the architecture's Pydantic `MotivationAnalysis` schema (which has `primary_motivation, reflection_note, recommendation` only). This will need reconciliation when implementing the motivation analysis endpoint.
5. **No auth in frontend API layer**: The frontend has no auth API calls (no register/login endpoints). Architecture specifies auth endpoints. This is acceptable for MVP demo-student mode but will need addition later.

### No Critical Conflicts
The frontend types, API paths, and data shapes are **well-aligned** with the architecture. The mock data structures closely mirror the Pydantic schemas defined in architecture §9.

---

## 10. Recommended Implementation Order

Prioritized by product value and credit efficiency:

### Phase 1 — Backend Foundation (~250 credits)
- FastAPI app, config, SQLite + SQLAlchemy, core models (students, student_profiles, careers), Pydantic schemas, health endpoint, CORS, logging
- Seed data loader for careers table (use mock data as template)

### Phase 2 — Qwen Service — COMPLETE
- Reusable `ai_service.py` with Pattern A (structured JSON output)
- Environment configuration, retry logic, Pydantic validation, fallback
- Master system prompt template
- Proven: student context → Qwen → valid Pydantic object (23 mocked tests pass; real `qwen3.7-plus` call verified 2026-08-29)

### Phase 3 — Career Intelligence — COMPLETE
- `GET /careers`, `GET /careers/{slug}`, `POST /career/analyze`, `POST /career/trial-plan`
- Career service, career analysis + trial plan prompts, template seed data + seeder
- End-to-end verified with software-engineering (26 Phase 3 tests; 77 total passing; live endpoints verified 2026-08-29)
- One compatibility change: test engine in `tests/conftest.py` now uses `StaticPool` so the TestClient app thread sees the same in-memory database (previously thread-local pooling gave the app thread an empty DB for un-warmed sessions)

### Phase 4 — Next Best Action + Journey — COMPLETE
- `POST /onboarding`, `GET /journey`, `POST /progress`, `POST /roadmap`
- Journey state machine, deterministic candidate generator, candidate-constrained NBA engine (selection + validation + one retry + deterministic fallback + persistence), roadmap service with stage milestone templates
- 39 Phase 4 tests; 116 total passing (zero regressions); real-Qwen live flow verified 2026-08-29
- Documented Phase 4 decisions:
  - `city` is accepted (frontend contract) but not persisted — the architecture §7 schema has no city column
  - The full transition map beyond the three architecture-defined transitions is the smallest sensible deterministic completion (per Phase 4 spec §7)
  - NBA AI-unavailability falls back deterministically instead of returning 503 — the journey loop must never dead-end (progress/onboarding already mutated state before the AI call)
  - Milestone instantiation dedupes by (stage, title) because HIGH_SCHOOL and CAREER_DISCOVERY legitimately share template titles
  - `student_profiles.completed_milestone_ids` is intentionally unused — the `milestones` table is the single source of truth (no duplicate storage)

### Phase 5 — MCP Integration — COMPLETE
- Two FastMCP servers (career: 5 tools; opportunity: 6 tools) mounted over SSE inside FastAPI
- Synchronous MCP client with controlled errors; Pattern B search orchestration with ONE retry + deterministic direct-DB fallback (`data_quality: "unranked"`)
- Ungrounded AI answers (no tool calls) discarded in favour of the direct query
- Seed data for opportunities + sports (TEMPLATE); 50 Phase 5 tests; 166 total passing; real Qwen + real MCP verified live (2026-08-29)

### Phase 6 — Opportunities + Sports — COMPLETE
- `GET /opportunities` (filters: type/city/field/skills), `GET /sports` (filters: sport/city/type), both database-only with §10 empty envelopes
- `POST /opportunities/match`, `POST /sports/match` — Pattern B retrieval (Qwen + real MCP) + deterministic scoring; opportunity matches persisted (replace semantics), sports never persisted
- Documented Phase 6 decisions: match-response envelope `{matches, data_quality, summary, note, message}`; `opportunity_type` limited to internship/job on the match endpoint; request `skills` override the profile; sports age requirements surfaced but never scored
- 63 Phase 6 tests; 229 total passing (zero regressions); real Qwen + real MCP live smoke 65/65 (2026-08-30)

### Phase 7 — Testing + Integration (~100 credits) — COMPLETE
- Frontend mock → real backend switch (`NEXT_PUBLIC_USE_MOCK=false`)
- Fixed `camelizeKeys` snake_case/camelCase mismatch bug
- Created opportunities + sports frontend API modules, types, and pages
- End-to-end test of full student flow: all 9 pages, all 14 endpoints, all data renders correctly
- Security + CORS verification: all checks pass
- npm build + lint: clean (0 warnings, 0 errors)
- Backend pytest: 229 passed, 0 failed, zero regressions

---

## 11. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Qwen API key not configured | Resolved | Credentials saved in `BackEnd/.env`; real connectivity verified via `BackEnd/test_qwen.py` (SUCCESS, 2026-08-29) |
| Malformed DASHSCOPE_BASE_URL breaks client construction | Resolved | `ai_service.py` normalizes the base URL (adds `https://` scheme and `/compatible-mode/v1` path when missing); covered by unit tests |
| Model `qwen3.8-max` may not be available | Resolved | MVP model confirmed as `qwen3.7-plus` (free quota available); read from `QWEN_MODEL` config |
| No verified Pakistani seed data | High | Mock data provides structure templates; user must verify/expand factual data |
| Folder name mismatch (BackEnd vs backend) | Low | Use existing `BackEnd/` directory as-is |
| Credit budget tight (1,500 max) | Medium | Batch vertical slices, avoid re-analysis, no unnecessary refactoring |
| No git repository initialized | Low | Initialize git before Phase 1 to preserve work |
| Architecture doc references `architecture.md` but file is `architecture_corrected.md` | Low | Use `architecture_corrected.md` as source of truth |

---

## 12. Credit-Efficient Strategy

1. **Vertical slices**: Implement model + schema + service + router + test for each feature in one pass
2. **No re-analysis**: This audit covers the full repo; no need for another broad scan
3. **Reuse mock data as seed template**: The frontend mock data already has correct structure — convert directly to JSON seed files
4. **Skip auth for MVP**: Use demo-student session (architecture-approved); add JWT only if time permits
5. **One MCP server first**: Prove the pattern before expanding
6. **Minimal frontend changes**: Only swap `NEXT_PUBLIC_USE_MOCK=false` and fix any type mismatches discovered during integration
