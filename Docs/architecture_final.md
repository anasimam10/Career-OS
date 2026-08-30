# A&H Career — Final CTO Architecture
## Phases 8, 9, 10 — Implementation, Testing, and Deployment Specification

**Document authority:** This is the single authoritative specification for all remaining development.  
**Intended audience:** Qoder (implementation), the development team (review).  
**Rule:** Qoder must inspect the actual repository before writing any code. Where actual code contradicts this document, trust the code and document the deviation.

---

## 1. Product Definition

A&H Career is a Pakistan-first AI career and sports mentor. It guides students from high school through their first job via a persistent, personalised journey. The central output at every session is a single **Next Best Action** — never a flood of tasks.

**Core constraints that must never change:**
- Frontend never calls Qwen directly.
- `ai_service.py` is the only Qwen integration point in the backend.
- Every structured AI output is Pydantic-validated before it reaches the frontend.
- The LLM reasons and personalises; it never becomes the source of factual opportunity data.
- Stage transitions are deterministic (not AI-driven).
- Opportunity data comes from the database, not from model general knowledge.

**Model fallback chain (extended to four models 2026-08-30):**
- `qwen3.7-plus` is the PRIMARY model — used for every call when healthy; never load-balanced, never randomly chosen.
- Ordered fallback chain: `qwen3.7-plus` → `qwen3.6-plus` → `qwen-plus-2025-07-28` → `qwen3-vl-235b-a22b-thinking` (single ordered list `QWEN_FALLBACK_MODELS`). A fallback is tried ONLY when the previous model fails with an eligible model-availability error (HTTP 429 rate/quota limit, 404 model not found, >= 500 provider capacity).
- Non-eligible failures (401/403 auth, 400 bad request, connection errors, Pydantic validation failures, unconfigured service) NEVER switch models — a broken configuration is not fixed by another model.
- Hard limits: max 4 models per call, max 3 fallback transitions, no recursion, the chain never restarts at the primary. Pattern A worst case 8 API calls (2 per model); Pattern B one tool-loop per model.
- Startup configuration validation (`REQUIRED_QWEN_MODELS` in `config.py`, checked in `main.py`): all four mandated models must be present in the resolved chain — a configuration check only, never a live API call.
- Pattern B/MCP compatibility: CONFIRMED for all four models (standard Chat Completions tool calling — same API surface; every model verified live, including one real tool-calling call each).
- Pattern A compatibility: CONFIRMED for all four models (json_object → JSON parse → Pydantic; every model verified live, including the thinking VL model qwen3-vl-235b-a22b-thinking).
- Future Qwen models: added through the ordered `QWEN_FALLBACK_MODELS` configuration only (`_model_chain()` in `ai_service.py` resolves it) — no router or service changes.

---

## 2. Current Implemented State (Phases 1–7)

The following are **complete and verified**. Do not rewrite them.

| Phase | Feature | Status |
|---|---|---|
| 1 | FastAPI, SQLAlchemy, SQLite, 9 tables, Pydantic, repo layer, health endpoint, CORS, tests | ✅ Complete |
| 2 | Qwen integration (qwen3.7-plus, Pattern A, json_object, Pydantic validation, retry, error handling) | ✅ Complete |
| 3 | `GET /careers`, `GET /careers/{slug}`, `POST /career/analyze`, `POST /career/trial-plan` | ✅ Complete |
| 4 | `POST /onboarding`, `GET /journey`, `POST /progress`, `POST /roadmap`, NBA, stage transitions | ✅ Complete |
| 5 | MCP Server 1 (Career/Education, `/mcp/career/sse`), MCP Server 2 (Opportunities/Sports, `/mcp/opportunity/sse`) | ✅ Complete |
| 6 | `GET /opportunities`, `POST /opportunities/match`, `GET /sports`, `POST /sports/match` | ✅ Complete |
| 7 | Frontend ↔ backend integration, NEXT_PUBLIC_USE_MOCK=false, snake_case/camelCase fix | ✅ Complete |

**Verified baseline: 229 tests, 229 passing, 0 failed.**

**Existing credential location:** `BackEnd/.env` — never move, never expose.

---

## 3. Existing Architecture (Reference)

```
Next.js 14 Frontend
       ↓ REST JSON (JWT in Authorization header)
FastAPI Backend  ← BackEnd/
    ├── routers/          (auth, onboarding, careers, journey, opportunities, sports, ...)
    ├── services/         (ai_service.py, career_service.py, ...)
    ├── models/           (SQLAlchemy ORM)
    ├── schemas/          (Pydantic request + response models)
    ├── prompts/          (prompt templates)
    └── tests/
       ↓
SQLite (BackEnd/bano_qabil.db or similar)
       ↓
ai_service.py
       ↓
Qwen API (qwen3.7-plus, Singapore region, DashScope)
       ↕ (Pattern B only)
MCP Servers (FastMCP, SSE)
    /mcp/career/sse
    /mcp/opportunity/sse
```

---

## 4. Phase 8 — Coach Chat + Job Readiness

**Objective:** Implement the two remaining MVP features. No new architecture. No new Qwen clients. Reuse `ai_service.py` for all AI calls.

---

## 5. Coach Chat Architecture

### 5.1 Endpoint

```
POST /api/v1/coach/chat
```

**Current status:** Frontend exists and sends requests. Backend returns 404. This is the only thing to fix.

### 5.2 Request schema (match existing frontend exactly)

```python
class CoachChatRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []
    # Each dict: {"role": "user"|"assistant", "content": str}
```

**Validation rules:**
- `message` must not be empty or whitespace-only.
- `conversation_history` is bounded to the most recent **5 messages** before the current message. The service trims to 5 if the frontend sends more. This keeps token cost bounded.
- Total history + message must not exceed 2000 characters combined before sending to Qwen. Truncate oldest history entries if needed.

### 5.3 Response schema (match existing frontend exactly)

```python
class CoachResponse(BaseModel):
    message: str
    quick_actions: list[str] = []      # backend enforces max 3
    suggested_resource: Optional[str] = None  # DB resource or null only
```

**If schema already exists in `BackEnd/schemas/responses.py`, use it as-is. Do not redefine.**

### 5.4 Data flow

```
POST /api/v1/coach/chat
       ↓
coach_router.py → rate_limit_check(student_id)
       ↓
coach_service.build_context(student_id, message, history)
    Fetches from DB:
    - student.education_stage
    - student.career_goal
    - student_profile.interests
    - student_profile.skills
    - student_profile.next_best_action (the last stored NBA)
    - active roadmap: current_stage, current_step_title
    - active milestones: the 1-3 currently active ones (title, status)
    - last 5 messages from conversation_history (trimmed from request)
    - if career_goal set: career record from DB (demand_level, required_skills, pk_opportunities)
    - opportunities: only if student has active opportunity matches in DB; otherwise omit entirely
       ↓
coach_service.build_prompt(context)
    Uses BackEnd/prompts/coach.py template
       ↓
ai_service.call_structured(prompt, CoachResponse schema)
       ↓
Pydantic validation
    - trim quick_actions to max 3
    - verify suggested_resource is None or a real DB-sourced string
       ↓
Return CoachResponse to frontend
```

### 5.5 Coach system prompt rules

The system prompt in `BackEnd/prompts/coach.py` must include these hard rules:

```
You are a Pakistan-focused career and sports mentor.
You are supporting the student described below.
Output must be valid JSON matching this schema:
{"message": "...", "quick_actions": ["...", "...", "..."], "suggested_resource": null}

RULES:
1. quick_actions must contain at most 3 short (< 10 words each) follow-up questions or actions.
2. suggested_resource must be null unless a verified resource was provided in the context.
3. Never invent Pakistani universities, jobs, internships, scholarships, deadlines, salaries, URLs, or tournament details.
4. If no verified opportunity data was provided, do not mention specific opportunities.
5. General career advice, motivation, and educational guidance are always allowed.
6. Keep the response concise — 2 to 4 short paragraphs maximum.
7. Always output valid JSON only. No preamble or markdown.
```

### 5.6 Rate limiting — in-memory for MVP

```python
# BackEnd/services/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta
import threading

class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter. Not persistent across restarts.
    For MVP/hackathon use only.
    Production replacement: Redis with sliding window.
    """
    def __init__(self, max_requests: int = 20, window_hours: int = 1):
        self.max_requests = max_requests
        self.window = timedelta(hours=window_hours)
        self._store: dict[int, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, student_id: int) -> bool:
        now = datetime.utcnow()
        cutoff = now - self.window
        with self._lock:
            self._store[student_id] = [
                t for t in self._store[student_id] if t > cutoff
            ]
            if len(self._store[student_id]) >= self.max_requests:
                return False
            self._store[student_id].append(now)
            return True

# Singleton instance
rate_limiter = InMemoryRateLimiter(max_requests=20, window_hours=1)
```

**When rate limit is hit:** Return HTTP 429 with body `{"detail": "Too many requests. Please wait before sending another message."}`. Do not call Qwen.

**Production note:** The in-memory limiter resets on server restart and does not work across multiple processes/instances. For production, replace with Redis using the same interface. The `InMemoryRateLimiter` should be behind an interface so this swap requires no changes to `coach_router.py`.

### 5.7 Files to create

```
BackEnd/routers/coach.py
BackEnd/services/coach_service.py
BackEnd/prompts/coach.py
BackEnd/services/rate_limiter.py   (if not already present)
```

Register `coach_router` in `BackEnd/main.py` — match the pattern used by existing routers.

---

## 6. Job Readiness Architecture

### 6.1 Endpoint

```
POST /api/v1/job-readiness
```

**Request:**
```python
class JobReadinessRequest(BaseModel):
    # No required input — uses authenticated student's data from DB
    pass
```
The student is identified from the JWT token, exactly as all other authenticated endpoints do.

### 6.2 Scoring — fully deterministic, Qwen cannot modify

```
Skills        30%  (0.0–1.0)
Projects      20%  (0.0–1.0)
Internship    20%  (0.0–1.0)
CV            15%  (0.0–1.0)
Interview     15%  (0.0–1.0)

overall_score = sum of (component_score * weight)
score_label   = f"{round(overall_score * 100)}%"
```

**These weights are hardcoded constants, not configurable. Qwen never sees the formula or intermediate scores. Qwen receives only the final component scores and the student profile.**

### 6.3 Data mapping for each component

Qoder must inspect the actual DB schema. The following is the MVP-safe mapping:

**Skills (30%):**
- Source: `student_profiles.skills` (JSON array of `{name, level}`)
- Scoring:
  - 0 skills → 0.0
  - 1–2 skills, all beginner → 0.25
  - 3+ skills or any intermediate → 0.5
  - 5+ skills with at least 1 intermediate/advanced → 0.75
  - 7+ skills with 2+ intermediate/advanced → 1.0
- If `career_goal` is set, check whether required skills for that career (from `careers` table) are covered. Each required skill present adds a bonus weight.

**Projects (20%):**
- Source: `milestones` table — count milestones with `stage = 'PROJECTS'` and `status = 'done'`.
- Scoring:
  - 0 done → 0.0
  - 1 done → 0.4
  - 2 done → 0.7
  - 3+ done → 1.0
- If the projects milestone stage does not exist yet in the roadmap, use 0.0.

**Internship (20%):**
- Source: `milestones` table — any milestone with `stage = 'INTERNSHIP'` and `status = 'done'`.
- Scoring:
  - None done → 0.0
  - At least one done → 1.0
- Fallback: if student's `education_stage` is before `INTERNSHIP`, this component is 0.0 and is labelled "not yet applicable" in the response.

**CV (15%):**
- Source: Check `milestones` for any milestone with title containing "CV", "resume", "portfolio" (case-insensitive) and `status = 'done'`.
- Scoring:
  - None → 0.0
  - One → 0.75
  - Two or more → 1.0
- If no such milestones exist in the student's roadmap: 0.0.

**Interview (15%):**
- Source: Check `milestones` for any milestone with title containing "interview", "mock" (case-insensitive) and `status = 'done'`.
- Scoring:
  - 0 → 0.0
  - 1 → 0.33
  - 2 → 0.67
  - 3+ → 1.0

**Important:** Document these mappings in a comment at the top of `job_readiness_service.py` so future maintainers understand the approximations. The comment must clearly state these are MVP approximations, not validated assessments.

### 6.4 Qwen's role in job readiness

After the deterministic score is calculated, Qwen is called **once** with:
- The component scores (as computed values, not as editable inputs)
- The student profile (stage, career goal, skills list)
- The biggest_gap component name (determined deterministically as the component with the lowest score)

Qwen produces:
```python
class JobReadinessAIAnalysis(BaseModel):
    gap_explanation: str          # 2-3 sentences about the biggest gap
    next_best_action: NextBestAction
    recommendations: list[str]    # max 3 concrete suggestions
```

The `overall_score`, `score_label`, and `component_scores` in the final response **always come from the deterministic calculation**. They are never replaced or modified by Qwen's output.

### 6.5 Response schema

```python
class JobReadiness(BaseModel):
    overall_score: float              # 0.0 to 1.0, deterministic
    score_label: str                  # e.g. "74%"
    component_scores: dict[str, float] # {"skills": 0.8, "projects": 0.6, ...}
    biggest_gap: str                  # component name, deterministic
    gap_explanation: str              # from Qwen
    next_best_action: NextBestAction  # from Qwen
    recommendations: list[str]        # from Qwen, max 3
    disclaimer: str                   # ALWAYS present, hardcoded

DISCLAIMER_TEXT = (
    "This job readiness score is a product indicator based on your tracked "
    "milestones and profile data. It is not a scientifically validated "
    "assessment of your employability. Use it as a general guide only."
)
```

The `disclaimer` field must always be populated with `DISCLAIMER_TEXT`. It must never be empty or AI-generated.

### 6.6 Qwen failure handling for job readiness

If Qwen fails or returns invalid JSON:
- Return the deterministic score, component_scores, biggest_gap, and disclaimer.
- Set `gap_explanation` to a hardcoded fallback: `"AI analysis is temporarily unavailable. Focus on your lowest-scoring component."`
- Set `recommendations` to `[]`.
- Set `next_best_action` to a hardcoded fallback pointing to the lowest-scoring component.
- Return HTTP 200 with the partial response — never HTTP 500 for job readiness.

### 6.7 Files to create

```
BackEnd/routers/job_readiness.py
BackEnd/services/job_readiness_service.py
BackEnd/prompts/job_readiness.py
```

---

## 7. Phase 8 Testing Specification

All new tests are **additive**. The 229 existing tests must remain passing.

### 7.1 Coach tests — `BackEnd/tests/test_coach.py`

```python
# Required test cases:

def test_coach_valid_request():
    # POST /api/v1/coach/chat with valid message + history
    # Assert: 200, response matches CoachResponse schema
    # Assert: message is non-empty string
    # Assert: quick_actions is list of max 3 items
    # Assert: suggested_resource is None or string (never a made-up URL)

def test_coach_response_schema_validation():
    # Mock ai_service to return valid CoachResponse JSON
    # Assert: Pydantic validation succeeds
    # Assert: returned JSON matches CoachResponse exactly

def test_coach_history_bounded_to_5():
    # Send conversation_history with 8 entries
    # Assert: service only sends 5 most recent to Qwen
    # (Verify via mock capture of ai_service call arguments)

def test_coach_context_injection():
    # Mock a student with known profile
    # Assert: student's education_stage appears in the prompt sent to Qwen

def test_coach_quick_actions_max_3():
    # Mock ai_service to return quick_actions with 5 items
    # Assert: endpoint returns only 3

def test_coach_no_invented_resource():
    # Mock ai_service to return suggested_resource="https://fake.com/..."
    # The service must either validate this against DB or set it to None
    # Assert: suggested_resource is None when not found in DB

def test_coach_invalid_ai_response():
    # Mock ai_service to raise ValidationError (bad JSON from Qwen)
    # Assert: 503 or graceful fallback, not 500 with traceback

def test_coach_ai_failure():
    # Mock ai_service to raise APIError
    # Assert: 503 with user-friendly message, no secret in response

def test_coach_rate_limit():
    # Send 21 requests as the same student
    # Assert: 21st returns 429
    # Assert: 429 body contains "Too many requests" message

def test_coach_missing_student():
    # Use an invalid/expired JWT
    # Assert: 401 Unauthorized

def test_coach_empty_message():
    # Send message=""
    # Assert: 422 Unprocessable Entity

def test_coach_secret_not_in_response():
    # Assert: response body does not contain DASHSCOPE_API_KEY value
    # Assert: response body does not contain SECRET_KEY value
```

### 7.2 Job Readiness tests — `BackEnd/tests/test_job_readiness.py`

```python
def test_job_readiness_deterministic_score():
    # Create student A with known profile
    # Call endpoint twice
    # Assert: both calls return identical overall_score
    # Assert: component_scores are identical

def test_job_readiness_weights_30_20_20_15_15():
    # Create student with known component scores
    # Manually compute expected score using weights
    # Assert: returned overall_score matches to 4 decimal places

def test_job_readiness_score_range():
    # Assert: 0.0 <= overall_score <= 1.0

def test_job_readiness_score_label():
    # Assert: score_label == f"{round(overall_score * 100)}%"

def test_job_readiness_biggest_gap():
    # Create student where skills=0.2 and all others higher
    # Assert: biggest_gap == "skills"

def test_qwen_cannot_change_score():
    # Mock ai_service to return a different score in its output
    # Assert: endpoint still returns the deterministically calculated score

def test_job_readiness_ai_analysis_valid():
    # Mock ai_service to return valid JobReadinessAIAnalysis
    # Assert: gap_explanation, recommendations, next_best_action present

def test_job_readiness_ai_invalid_response():
    # Mock ai_service to raise ValidationError
    # Assert: still returns 200 with deterministic scores
    # Assert: gap_explanation is fallback text
    # Assert: recommendations == []

def test_job_readiness_ai_unavailable():
    # Mock ai_service to raise APIConnectionError
    # Assert: 200 with deterministic scores + hardcoded fallback text

def test_job_readiness_disclaimer_always_present():
    # Assert: disclaimer field is present and non-empty in ALL responses
    # (including AI failure responses)
    # Assert: disclaimer contains the required text

def test_job_readiness_incomplete_profile():
    # Student with no skills, no milestones
    # Assert: overall_score == 0.0
    # Assert: response still valid (no 500)

def test_job_readiness_no_fabricated_achievements():
    # Mock ai_service to return recommendations mentioning a specific Pakistani company
    # Verify that the company name is not accepted if not in DB context
    # (This is a documentation/design test — ensure the prompt prohibits fabrication)
```

---

## 8. Phase 9 — Full System QA

### 8.1 Regression rule

After every code change:
```bash
cd BackEnd && pytest --tb=short -q
```
**Must return: all previously passing tests still passing. Zero regressions permitted.**

If a test becomes failing after a change that did not intend to modify its behavior, the change must be reverted or the test fixed (not deleted, not weakened).

### 8.2 Backend QA checklist

Run manually or automate where possible:

```
[ ] GET  /api/v1/health                     → 200 {"status":"ok"}
[ ] POST /api/v1/auth/register              → 201, returns token
[ ] POST /api/v1/auth/login                 → 200, returns token
[ ] POST /api/v1/onboarding                 → 200, returns NextBestAction
[ ] GET  /api/v1/careers                    → 200, list of careers
[ ] GET  /api/v1/careers/{slug}             → 200, career detail
[ ] GET  /api/v1/careers/invalid-slug       → 404
[ ] POST /api/v1/career/analyze             → 200, CareerReality + CareerVerdict
[ ] POST /api/v1/career/trial-plan          → 200, CareerTrialPlan
[ ] GET  /api/v1/journey                    → 200, ≤3 visible steps
[ ] POST /api/v1/roadmap                    → 200, roadmap created
[ ] POST /api/v1/progress                   → 200, milestone updated
[ ] GET  /api/v1/opportunities              → 200, list
[ ] POST /api/v1/opportunities/match        → 200, ranked list
[ ] GET  /api/v1/sports                     → 200, list
[ ] POST /api/v1/sports/match               → 200, ranked list
[ ] POST /api/v1/coach/chat                 → 200, CoachResponse
[ ] POST /api/v1/job-readiness              → 200, JobReadiness + disclaimer
[ ] GET  /api/v1/health (no auth)           → 200 (health must be public)
[ ] Any protected endpoint, no token        → 401
[ ] Any protected endpoint, expired token   → 401
[ ] Cross-origin request from allowed origin → works
[ ] Cross-origin from disallowed origin     → blocked
[ ] CORS preflight OPTIONS                  → correct headers
[ ] POST /coach/chat, 21 requests           → 21st returns 429
```

### 8.3 Failed conditions — expected behavior

| Failure | Expected behavior |
|---|---|
| Qwen timeout | Return 503 with `{"detail": "AI service temporarily unavailable"}` or cached fallback where available. Never raise unhandled exception. |
| Qwen rate limit (429 from DashScope) | Retry once after 2s. If still fails, return 503. Log the event (sanitised, no key). |
| Malformed JSON from Qwen | Retry with stricter prompt once. If still fails, return 503 or partial response depending on endpoint. |
| Pydantic validation failure | Log raw response (sanitised). Retry once. If still fails, 503. |
| MCP server timeout | Fall back to direct DB query. Return data with `{"data_quality": "unranked"}` flag. |
| MCP server unreachable | Same as timeout — DB fallback. |
| Empty opportunity result | Return `{"opportunities": [], "message": "No matching opportunities found right now."}`. Never call Qwen to invent opportunities. |
| Stale opportunity data (last_verified > 30 days) | Return data with `{"data_freshness": "unverified", "last_verified": "..."}` flag. |
| Invalid career slug | 404 with `{"detail": "Career not found"}`. |
| Invalid milestone ID | 404 or 422. |
| Invalid student ID in JWT | 401. |
| Malformed request body | 422 with Pydantic field-level errors. |
| Database unavailable | 503. Log error internally. Never expose DB error to client. |
| Missing environment variables at startup | Application must fail to start with a clear error message listing the missing variables. Use a startup validation check in `main.py`. |

### 8.4 End-to-end demo script

Run this scripted journey manually before declaring Phase 9 complete. All steps must complete without blocking errors, fabricated data, or raw backend error messages shown in the browser.

```
Step  1: Open frontend URL in a fresh browser (incognito)
Step  2: Register a new account
         Expected: Registration succeeds, redirect to onboarding
Step  3: Complete onboarding (select education stage, career interest, sports interest, motivation)
         Expected: Next Best Action displayed
Step  4: Navigate to Career Explorer
         Expected: List of Pakistani careers loads
Step  5: Click a career (e.g., Software Engineering)
         Expected: Career detail page loads, demand/competition/skills shown
Step  6: Click "Reality Check"
         Expected: CareerReality + CareerVerdict displayed with reasoning
Step  7: Click "7-Day Trial Plan"
         Expected: 7-day plan with day-by-day tasks displayed
Step  8: Navigate to Journey
         Expected: Current stage shown, max 3 next steps shown (not full roadmap)
Step  9: View Roadmap
         Expected: Roadmap for chosen career shown
Step 10: Mark a milestone as complete
         Expected: Progress saved, NBA updates
Step 11: Navigate to Opportunities
         Expected: List of opportunities loads
Step 12: Click "Match to my profile"
         Expected: Ranked opportunity matches with scores and gaps
Step 13: Navigate to Sports
         Expected: Sports opportunities load
Step 14: Match to sports profile
         Expected: Ranked sports matches
Step 15: Open Coach Chat
         Expected: Chat interface loads, no 404
Step 16: Send a message: "How can I improve my Python skills?"
         Expected: Coach responds with message + up to 3 quick_actions
         Expected: No invented opportunities, no fake URLs in response
Step 17: Click a quick action
         Expected: Quick action sent as next message, coach responds
Step 18: Navigate to Job Readiness
         Expected: Score displayed with all components, disclaimer visible
         Expected: Score is a percentage, disclaimer text present
Step 19: Verify browser console
         Expected: No CORS errors, no 404s, no 500s
Step 20: Verify network tab
         Expected: No API key visible in any request/response
```

### 8.5 Qwen integration QA

```
[ ] Pattern A: send real request to qwen3.7-plus with json_object format → valid JSON response
[ ] Pattern A: Pydantic validation succeeds on real response
[ ] Pattern A: retry triggers correctly on simulated first failure
[ ] Pattern B (MCP): Qwen actually calls MCP tool (verify in logs)
[ ] Pattern B: tool result appears in Qwen's final response
[ ] Pattern B: MCP fallback triggers when SSE server is stopped
[ ] Token count: verify typical coach/NBA calls stay under 2000 input tokens
```

### 8.6 MCP QA

```
[ ] /mcp/career/sse — SSE endpoint responds to GET
[ ] get_career(slug) — returns career data from DB
[ ] get_career_reality(slug) — returns reality data
[ ] get_required_skills(career_slug, stage) — returns skills list
[ ] get_university_opportunities(field, city) — returns results or empty list
[ ] get_scholarships(criteria) — returns results or empty list
[ ] /mcp/opportunity/sse — SSE endpoint responds
[ ] search_internships(skills, city) — returns DB results
[ ] search_jobs(skills, city, experience_level) — returns DB results
[ ] match_opportunity(student_profile, opportunity_id) — returns score + gaps
[ ] search_sports_opportunities(sport, city) — returns results
[ ] search_sports_scholarships(sport, level) — returns results
[ ] search_university_sports(sport, city) — returns results
[ ] All tools: when DB has no results, return [] not error
[ ] Qwen Pattern B: confirm tool calls appear in responses API output
```

### 8.7 Frontend QA

```
[ ] All pages load without console errors in real backend mode (NEXT_PUBLIC_USE_MOCK=false)
[ ] No mock data appears in any response
[ ] Loading states shown correctly (spinner/skeleton during API calls)
[ ] Empty states shown correctly (when no opportunities, no alumni, etc.)
[ ] Error states shown correctly (when API returns error)
[ ] Navigation works between all pages
[ ] Frontend build passes: `npm run build` exits 0
[ ] Frontend lint passes: `npm run lint` exits 0
[ ] No API key visible in frontend bundle: `grep -r "DASHSCOPE" .next/` returns nothing
[ ] NEXT_PUBLIC_USE_MOCK not set to true in production build
```

---

## 9. Security Specification

### 9.1 Secrets

- `DASHSCOPE_API_KEY` lives only in `BackEnd/.env`. Never in `FrontEnd/`, never in git, never in logs.
- `SECRET_KEY` (JWT signing key) lives only in `BackEnd/.env`.
- Both must be in `.gitignore`. Verify: `git ls-files BackEnd/.env` returns nothing.
- `NEXT_PUBLIC_*` variables are bundled into the frontend JavaScript and are public. Never put any secret in a `NEXT_PUBLIC_*` variable.

### 9.2 Log sanitisation

All logging in `ai_service.py` and anywhere that handles Qwen responses must sanitise before logging:
```python
import re

def sanitise_for_log(text: str) -> str:
    """Remove anything that looks like an API key from log output."""
    return re.sub(r'sk-[A-Za-z0-9]{20,}', '[REDACTED]', text)
```

Never log the raw `DASHSCOPE_API_KEY`. Never log full student profiles (log student_id only).

### 9.3 Student data isolation

Every database query that returns student-specific data must filter by `student_id` extracted from the JWT. Example:

```python
# CORRECT
db.query(Roadmap).filter(Roadmap.student_id == current_student.id).first()

# WRONG — never do this
db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
```

Tests for this: attempt to access another student's roadmap using a valid JWT for student A — must return 404 or 403, never the other student's data.

### 9.4 Input validation

All request bodies are validated by Pydantic before any service call. SQLAlchemy ORM prevents SQL injection by design. No raw SQL strings with f-string interpolation are permitted anywhere.

### 9.5 CORS

Development: `http://localhost:3000`  
Production: set via `CORS_ORIGINS` environment variable (comma-separated list of allowed origins).

```python
# BackEnd/config.py
cors_origins: list[str] = Field(
    default=["http://localhost:3000"],
    description="Comma-separated list of allowed CORS origins"
)

# BackEnd/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

In production, `CORS_ORIGINS` must be set to the exact Vercel frontend URL (e.g., `https://ah-career.vercel.app`). Never use `*` in production.

### 9.6 AI-generated database writes

No endpoint may write to the database using AI-generated content without deterministic validation. Opportunity data is never created or modified from Qwen output. The only AI outputs that reach the database are: `next_best_action` stored in `student_profiles` (as a JSON blob, validated by Pydantic before storage).

### 9.7 Opportunity data integrity

The `opportunities` and `sports_opportunities` tables are write-protected at the application layer — no public API endpoint allows inserting into them. They are populated only by seed scripts.

---

## 10. Deployment Architecture

### 10.1 Target architecture

```
User Browser
     ↓ HTTPS
Vercel (Next.js frontend)
     ↓ HTTPS API calls (NEXT_PUBLIC_API_URL)
Render (FastAPI backend, $7/month Starter)
     ↓
SQLite on Render Persistent Disk ($1/month, 1GB)
     ↓
Qwen API (DashScope, Singapore)
     ↕
MCP servers (same Render service, mounted in FastAPI)
```

### 10.2 Platform decisions (verified against current 2026 availability)

**Frontend: Vercel**
- Free tier. No cold starts for static/SSR pages.
- Auto-deploys from GitHub main branch.
- HTTPS provided automatically.
- Set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_USE_MOCK` as environment variables in Vercel dashboard.
- Domain: `<project>.vercel.app` (free, no custom domain required for hackathon).

**Backend: Render Starter ($7/month)**
- Free tier is NOT suitable: it has an ephemeral filesystem (SQLite data lost on every restart/redeploy) and 30–60s cold starts.
- Starter plan ($7/month): always-on, no sleep.
- Persistent Disk: add a 1GB disk for $1/month. Mount at `/data`. Store SQLite at `/data/bano_qabil.db`.
- HTTPS provided automatically at `<service>.onrender.com`.
- Deploy via Dockerfile or Python buildpack (Dockerfile is more reliable).
- Set all `BackEnd/.env` variables as Render environment variables.

**Total cost: $8/month** — acceptable for a hackathon demo.

**Alternative if cost is a hard constraint:** Use Render free tier with the seed database pre-seeded at deploy time (accept that student data resets on restart). For a judged demo where the demo flow is scripted, this is workable if you accept re-seeding before the demo.

### 10.3 SQLite on Render

- Render free tier: ephemeral filesystem. SQLite data lost on restart. **Not acceptable for production.**
- Render Starter + Persistent Disk: SQLite persists across restarts and redeploys. **Acceptable for hackathon.**
- Set `DATABASE_URL=sqlite:////data/bano_qabil.db` (note four slashes — absolute path).
- The seed script must run on first deploy if the database is empty.

```python
# BackEnd/main.py — startup seed check
@app.on_event("startup")
async def startup():
    from BackEnd.database import engine, Base
    Base.metadata.create_all(bind=engine)
    from BackEnd.data.seed_db import seed_if_empty
    seed_if_empty()
```

```python
# BackEnd/data/seed_db.py
def seed_if_empty():
    """Load seed data only if the DB is empty. Safe to call on every startup."""
    db = SessionLocal()
    try:
        if db.query(Career).count() == 0:
            load_seed_data(db)
            db.commit()
    finally:
        db.close()
```

**Do not use PostgreSQL for the MVP.** SQLite on a persistent disk is sufficient, simpler, and cheaper. PostgreSQL migration can be done post-hackathon with minimal code changes (only `DATABASE_URL` and connection pooling config need updating; SQLAlchemy abstracts the rest).

---

## 11. HTTPS

**Frontend (Vercel):** HTTPS is automatic. All Vercel deployments use `https://`.

**Backend (Render):** HTTPS is automatic. All Render services get `https://<service>.onrender.com` with a valid TLS certificate managed by Render.

**Frontend → backend communication:** Set in Vercel:
```
NEXT_PUBLIC_API_URL=https://<backend>.onrender.com/api/v1
```

No self-signed certificates. No manual certificate management. Both platforms handle TLS automatically.

---

## 12. Environment Configuration

### 12.1 Backend environment variables (Render dashboard)

```bash
# AI — keep server-side only
DASHSCOPE_API_KEY=sk-...
DASHSCOPE_WORKSPACE_ID=ws-...
DASHSCOPE_BASE_URL=https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.7-plus
QWEN_FALLBACK_MODELS=qwen3.6-plus,qwen-plus-2025-07-28,qwen3-vl-235b-a22b-thinking
# Database
DATABASE_URL=sqlite:////data/bano_qabil.db

# Auth
SECRET_KEY=<random-256-bit-hex-string>

# CORS — set to exact Vercel URL after frontend is deployed
CORS_ORIGINS=https://ah-career.vercel.app

# Logging
LOG_LEVEL=INFO
```

### 12.2 Frontend environment variables (Vercel dashboard)

```bash
# Public — these appear in the browser bundle. Never put secrets here.
NEXT_PUBLIC_API_URL=https://<backend>.onrender.com/api/v1
NEXT_PUBLIC_USE_MOCK=false
```

### 12.3 Startup validation

Add to `BackEnd/main.py`:
```python
REQUIRED_ENV_VARS = [
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_WORKSPACE_ID",
    "SECRET_KEY",
    "DATABASE_URL",
]

for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"Required environment variable {var} is not set. Aborting startup.")
```

This prevents silent failures where the app starts but all AI calls fail because the key is missing.

---

## 13. Production Build

### 13.1 Frontend (Vercel — automatic)

Vercel runs these automatically on deploy:
```bash
npm install
npm run build
```

Verify locally before pushing:
```bash
cd FrontEnd
npm run build     # must exit 0
npm run lint      # must exit 0
```

### 13.2 Backend (Render — Dockerfile recommended)

Create `BackEnd/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**Do not use `--reload` in production.** One worker is correct for SQLite (no concurrent write contention). If the platform provides a `PORT` variable, use it:

```dockerfile
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
```

### 13.3 Render configuration (`BackEnd/render.yaml`, optional)

```yaml
services:
  - type: web
    name: ah-career-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
    disk:
      name: ah-career-data
      mountPath: /data
      sizeGB: 1
```

---

## 14. Deployment Health Check

**The deployment is not complete until this passes:**

```bash
curl https://<backend>.onrender.com/api/v1/health
# Expected: 200 {"status": "ok"}
```

Run from a different machine or network — not from the server itself.

---

## 15. Deployment Smoke Test

After both frontend and backend are deployed, run this from a machine that has never run the project locally:

```bash
# 1. Backend health
curl https://<backend>.onrender.com/api/v1/health

# 2. Careers list
curl https://<backend>.onrender.com/api/v1/careers

# 3. Open frontend in browser
# https://ah-career.vercel.app

# 4. Complete onboarding flow in the browser
# 5. Send a coach chat message
# 6. Check job readiness
# 7. Open browser DevTools → Network tab → verify no DASHSCOPE_API_KEY in any response
# 8. Open browser DevTools → Console → verify no CORS errors
```

---

## 16. Deployment Failure Handling

| Failure | Production behavior |
|---|---|
| Backend cold start (Starter plan — should not happen) | If it does, frontend shows loading state. Retry logic in frontend. |
| Qwen timeout in production | Same as dev: 503 with user-friendly message. Never expose DashScope errors. |
| Qwen unavailable | Cached NBA from `student_profiles.next_best_action` shown for journey/NBA endpoints. Coach returns 503. |
| MCP unreachable | DB fallback with `data_quality: "unranked"` flag. |
| Database unavailable (disk detached) | 503 on all endpoints. Alert visible in Render dashboard. |
| Frontend/Vercel unavailable | Handled by Vercel's own CDN redundancy. |
| Missing production env vars | App fails to start (startup validation). Render will show build failure. Fix env vars in dashboard and redeploy. |

**No secrets in public error responses.** All 500/503 responses return only `{"detail": "..."}` — never tracebacks, never env var values, never API keys.

```python
# BackEnd/main.py — global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {type(exc).__name__}: {sanitise_for_log(str(exc))}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."}
    )
```

---

## 17. Final Folder Structure

Based on the actual existing structure. Do not rename working directories.

```
a-h-career/
├── BackEnd/
│   ├── .env                          (never commit)
│   ├── .env.example                  (commit — no real values)
│   ├── Dockerfile                    (NEW — for Render deployment)
│   ├── render.yaml                   (NEW — optional)
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── student.py
│   │   ├── career.py
│   │   ├── roadmap.py
│   │   ├── opportunity.py
│   │   └── alumni.py
│   ├── schemas/
│   │   ├── requests.py
│   │   └── responses.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── onboarding.py
│   │   ├── careers.py
│   │   ├── journey.py
│   │   ├── opportunities.py
│   │   ├── sports.py
│   │   ├── alumni.py
│   │   ├── coach.py                  (NEW)
│   │   └── job_readiness.py          (NEW)
│   ├── services/
│   │   ├── ai_service.py             (existing — do not rewrite)
│   │   ├── career_service.py
│   │   ├── roadmap_service.py
│   │   ├── opportunity_service.py
│   │   ├── matching_service.py
│   │   ├── coach_service.py          (NEW)
│   │   ├── job_readiness_service.py  (NEW)
│   │   └── rate_limiter.py           (NEW)
│   ├── prompts/
│   │   ├── system_prompt.py
│   │   ├── career_analysis.py
│   │   ├── next_best_action.py
│   │   ├── trial_plan.py
│   │   ├── coach.py                  (NEW)
│   │   └── job_readiness.py          (NEW)
│   ├── data/
│   │   ├── seed/
│   │   │   ├── careers.json
│   │   │   ├── universities.json
│   │   │   ├── opportunities.json
│   │   │   ├── sports_opportunities.json
│   │   │   └── alumni.json
│   │   └── seed_db.py
│   └── tests/
│       ├── test_health.py            (existing)
│       ├── test_auth.py              (existing)
│       ├── test_careers.py           (existing)
│       ├── test_journey.py           (existing)
│       ├── test_opportunities.py     (existing)
│       ├── test_sports.py            (existing)
│       ├── test_ai_service.py        (existing)
│       ├── test_mcp.py               (existing)
│       ├── test_coach.py             (NEW)
│       └── test_job_readiness.py     (NEW)
├── FrontEnd/
│   ├── app/
│   ├── components/
│   ├── lib/
│   │   └── api.ts                    (existing — centralised API calls)
│   ├── .env.local                    (never commit)
│   ├── .env.local.example            (commit — no real values)
│   └── package.json
├── mcp/
│   ├── career_server.py              (existing)
│   └── opportunity_server.py         (existing)
├── Docs/
│   ├── architecture_final.md         (this document)
│   └── api_contracts.md              (existing)
└── .gitignore
```

---

## 18. Credit and Token Efficiency Strategy

**Qoder credits target: 1,500 remaining.**

### What to give Qoder as single tasks (high efficiency):

1. **"Implement `BackEnd/routers/coach.py` and `BackEnd/services/coach_service.py` and `BackEnd/prompts/coach.py` and `BackEnd/services/rate_limiter.py` exactly as specified in sections 5.1–5.7 of architecture_final.md. Do not modify any existing files except to register the coach router in main.py."**

2. **"Implement `BackEnd/routers/job_readiness.py` and `BackEnd/services/job_readiness_service.py` and `BackEnd/prompts/job_readiness.py` exactly as specified in sections 6.1–6.7 of architecture_final.md. The deterministic scoring function must match the weights 30/20/20/15/15 exactly."**

3. **"Write `BackEnd/tests/test_coach.py` with all 12 test cases specified in section 7.1 of architecture_final.md. Mock `ai_service.call_structured` using `unittest.mock.patch`."**

4. **"Write `BackEnd/tests/test_job_readiness.py` with all 12 test cases specified in section 7.2. Mock `ai_service.call_structured`."**

5. **"Create `BackEnd/Dockerfile` and `BackEnd/render.yaml` as specified in section 13."**

6. **"Add the startup env var validation and the global exception handler from section 12.3 and 16 to `BackEnd/main.py`."**

### What NOT to give Qoder:

- Frontend UI changes — that is Antigravity's role.
- Rewriting existing passing services.
- Redesigning the architecture.
- Generating seed data (do this manually — it's research, not coding).
- Debugging by giving Qoder "find the bug" — always provide the specific error and file location.

### Qwen token efficiency:

- Coach prompt: bound to student profile (200 tokens) + 5 history messages (500 tokens) + career context (200 tokens) + instructions (200 tokens) ≈ 1,100 input tokens per call. Acceptable.
- Job readiness: smaller prompt — component scores + profile + instructions ≈ 600 input tokens.
- All test mocks: do not call real Qwen in unit tests. Use `@patch("BackEnd.services.ai_service.call_structured")`.
- Real Qwen calls in tests: only in integration tests tagged `@pytest.mark.integration` — run these manually, not in CI.

---

## 19. Full End-to-End Flow (Production)

```
User opens https://ah-career.vercel.app
    ↓ Vercel serves Next.js static assets (HTTPS, CDN)
User registers / logs in
    ↓ POST https://<backend>.onrender.com/api/v1/auth/register
    ↓ JWT returned, stored in frontend state
User completes onboarding
    ↓ POST /api/v1/onboarding
    ↓ BackEnd reads profile → calls ai_service → Qwen qwen3.7-plus
    ↓ NextBestAction returned, stored in DB
User browses careers
    ↓ GET /api/v1/careers → DB query, no AI
User runs Reality Check
    ↓ POST /api/v1/career/analyze
    ↓ CareerService fetches career from DB → ai_service → Qwen
    ↓ CareerReality + CareerVerdict returned (Pydantic validated)
User views journey, marks milestones
    ↓ GET /api/v1/journey → DB query
    ↓ POST /api/v1/progress → DB update → NBA recalculation → Qwen
User matches opportunities
    ↓ POST /api/v1/opportunities/match
    ↓ MCP server called via Qwen Pattern B → DB query → results
    ↓ AI ranks + explains → Pydantic validated → OpportunityMatch[]
User chats with coach
    ↓ POST /api/v1/coach/chat
    ↓ Rate limit check (20/hour, in-memory)
    ↓ coach_service builds context from DB
    ↓ ai_service → Qwen → CoachResponse (Pydantic validated)
    ↓ quick_actions trimmed to max 3
User checks Job Readiness
    ↓ POST /api/v1/job-readiness
    ↓ job_readiness_service computes deterministic score from DB
    ↓ ai_service → Qwen (for gap explanation only)
    ↓ JobReadiness returned with hardcoded disclaimer
```

---

## 20. Definition of Done — Complete Project

The project is complete when every item below is checked.

### Core functionality
- [ ] Onboarding works (stage, interests, career, sports, motivation)
- [ ] Next Best Action returned after onboarding and after each milestone
- [ ] Career list loads from DB
- [ ] Career detail loads from DB
- [ ] Career Reality Check calls Qwen, returns validated CareerReality + CareerVerdict
- [ ] 7-Day Trial Plan generated by Qwen
- [ ] Journey shows current stage and max 3 next steps
- [ ] Roadmap created for chosen career
- [ ] Milestone progress saved and triggers NBA recalculation
- [ ] Opportunities list from DB
- [ ] Opportunity matching (AI-ranked via MCP + Pydantic validated)
- [ ] Sports opportunities from DB
- [ ] Sports matching (AI-ranked via MCP + Pydantic validated)
- [ ] Coach Chat: POST /api/v1/coach/chat returns 200 (not 404)
- [ ] Coach response has message + max 3 quick_actions + no invented resources
- [ ] Rate limit: 21st coach request returns 429
- [ ] Job Readiness score is deterministic (30/20/20/15/15 weights)
- [ ] Job Readiness disclaimer always present

### AI
- [ ] qwen3.7-plus confirmed working in production environment
- [ ] Pattern A (json_object) working for all structured endpoints
- [ ] Pattern B (MCP/Responses API) working for opportunity/sports matching
- [ ] Pydantic validation on every AI output
- [ ] Retry logic working (simulated failure + retry)
- [ ] AI failure returns 503 or partial response, never unhandled 500
- [ ] No fabricated opportunity data confirmed in smoke test

### MCP
- [ ] `/mcp/career/sse` responding
- [ ] `/mcp/opportunity/sse` responding
- [ ] All tools in both servers functioning
- [ ] Qwen actually calls tools in Pattern B (verified in logs)
- [ ] MCP fallback to DB works when SSE unavailable

### Testing
- [ ] All 229 original tests still passing
- [ ] All new coach tests passing (minimum 12)
- [ ] All new job readiness tests passing (minimum 12)
- [ ] Zero regressions
- [ ] Frontend `npm run build` exits 0
- [ ] Frontend `npm run lint` exits 0
- [ ] End-to-end demo script passes (20 steps, section 8.4)

### Security
- [ ] `git ls-files BackEnd/.env` returns nothing
- [ ] `grep -r "DASHSCOPE" FrontEnd/.next/` returns nothing
- [ ] CORS restricted to specific origin (not `*`)
- [ ] Rate limiting active on coach endpoint
- [ ] Student data isolation verified (cross-student access returns 403/404)
- [ ] Global exception handler installed (no tracebacks in API responses)
- [ ] Log sanitisation active (no API keys in logs)

### Deployment
- [ ] Frontend deployed to Vercel, accessible at `https://*.vercel.app`
- [ ] Backend deployed to Render Starter, accessible at `https://*.onrender.com`
- [ ] Persistent disk attached to Render service, SQLite at `/data/bano_qabil.db`
- [ ] Seed data loaded on first startup
- [ ] `GET /api/v1/health` returns 200 from public URL
- [ ] `NEXT_PUBLIC_API_URL` pointing to production backend URL
- [ ] `NEXT_PUBLIC_USE_MOCK=false` in production
- [ ] `CORS_ORIGINS` set to production frontend URL
- [ ] External-machine smoke test passed (section 15)
- [ ] No cold starts on Render Starter plan (verify 2 consecutive requests respond in < 3s)

---

## 21. Exact Implementation Order

### Step 1 — Coach Chat (Qoder Task 1)
Files: `coach.py` (router), `coach_service.py`, `prompts/coach.py`, `rate_limiter.py`
Register router in `main.py`.
Target: `POST /api/v1/coach/chat` returns 200, not 404.
Test: run full pytest, all 229 tests still passing.

### Step 2 — Coach Tests (Qoder Task 2)
File: `tests/test_coach.py`
All 12 test cases from section 7.1.
Target: all new tests passing, zero regressions.

### Step 3 — Job Readiness (Qoder Task 3)
Files: `job_readiness.py` (router), `job_readiness_service.py`, `prompts/job_readiness.py`
Register router in `main.py`.
Target: `POST /api/v1/job-readiness` returns 200 with deterministic score.
Test: all tests passing.

### Step 4 — Job Readiness Tests (Qoder Task 4)
File: `tests/test_job_readiness.py`
All 12 test cases from section 7.2.
Target: all tests passing.

### Step 5 — Security hardening (Qoder Task 5)
Files: `main.py` (startup validation + global exception handler), `services/ai_service.py` (log sanitisation)
Target: startup fails with clear error if env vars missing. No traceback in error responses.
Test: all tests passing.

### Step 6 — End-to-end QA (manual — not Qoder)
Run the 20-step demo script (section 8.4) locally.
Fix any bugs found. These fixes may require small Qoder tasks — scope each one narrowly.
Target: all 20 steps pass with no blocking errors.

### Step 7 — Deployment prep (Qoder Task 6)
Files: `Dockerfile`, `render.yaml`, `data/seed_db.py` (startup seed check), `main.py` (startup hook)
Target: `docker build` and `docker run` works locally.

### Step 8 — Deploy backend (manual)
Push to GitHub → Render auto-deploys.
Set all env vars in Render dashboard.
Verify: `curl https://<backend>.onrender.com/api/v1/health` → 200.

### Step 9 — Deploy frontend (manual)
Push to GitHub → Vercel auto-deploys.
Set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_USE_MOCK=false` in Vercel dashboard.
Verify: site opens in browser.

### Step 10 — External smoke test (manual)
From a different machine/network: run all steps in section 15.
Fix any deployment-specific bugs (CORS, env vars, disk path).
Target: full smoke test passes.

---

## 22. Qoder Task Boundaries — Summary

| Task | Description | Do not touch |
|---|---|---|
| Task 1 | Implement coach router, service, prompt, rate limiter | Existing routers, ai_service.py |
| Task 2 | Write test_coach.py (12 tests, mock ai_service) | All existing test files |
| Task 3 | Implement job_readiness router, service, prompt | Existing routers, ai_service.py |
| Task 4 | Write test_job_readiness.py (12 tests, mock ai_service) | All existing test files |
| Task 5 | Add startup validation + global exception handler + log sanitisation | Core business logic, schemas |
| Task 6 | Write Dockerfile, render.yaml, startup seed hook | Existing models, services |

**Rule for every Qoder task:** Begin by reading the relevant files in the actual repository. If actual code conflicts with this document, preserve the actual working code and note the deviation in a comment. Never silently change working architecture to match documentation.

---

*Document version: Final. Author: CTO/Architecture role. Project: A&H Career. Target completion: September 3, 2026.*
