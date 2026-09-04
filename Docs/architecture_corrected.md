A&H Careers

# Bano Qabil — AI Career & Sports Mentor for Pakistan

## Complete Technical Architecture

---

## 1. Refined Technical Product Definition

**One student. One direction. One next step.**

A persistent AI mentor that guides Pakistani students from high school through their first job (and optionally through a sports pathway). The product's central output at every session is a single **Next Best Action** — never a flood of tasks. All recommendations are grounded in verified Pakistani data. The LLM reasons and personalises; it never fabricates facts.

**Two pathways run in parallel:**

- Career pathway: high school → career discovery → career decision → university → skill building → projects → internship → final year → job prep → first job
- Sports pathway: interest discovery → tournament/trial eligibility → scholarship matching → university sports programme opportunities

**Core design constraints:**

- Pakistan-only data in the MVP (no silent mixing of foreign content)
- No hallucinated opportunities — if data is unavailable, say so
- LLM output is always validated by Pydantic before it touches the frontend
- Student profile evolves continuously; the roadmap is hidden internally but only 1–3 steps are shown at a time

---

## 2. Architecture Overview

The three diagrams above show the full picture. The layers are:

**Frontend (Next.js 14)** — built by Antigravity, consumes a strict REST JSON API. Never calls Qwen directly. Never accesses the database. All UI state lives in the frontend; all persistent state lives in the backend.

**Backend (FastAPI / Python)** — owns all business logic. Receives requests, validates with Pydantic, queries the database, calls MCP tools when needed, assembles the prompt, calls Qwen, validates the structured JSON response, and returns it.

**Data layer** — SQLite with SQLAlchemy for MVP; seed JSON files for Pakistani careers, universities, sports opportunities, and alumni; Qwen API (Alibaba Model Studio, Singapore region) as the AI inference endpoint.

---

## 3. Qwen Integration Plan (verified against current docs)

**Current MVP model (confirmed):** `qwen3.7-plus` via Alibaba Cloud Model Studio / DashScope (Singapore region), configured in `BackEnd/.env` as `QWEN_MODEL=qwen3.7-plus`. The model name is always read from configuration — `qwen3.8-max` is no longer the fixed MVP model.

**For MCP (later phase):** Use an MCP-compatible Qwen model supported by the current Alibaba Cloud documentation. Pattern B/MCP is NOT implemented in Phase 2 — `BackEnd/services/ai_service.py` owns all AI-provider interaction (Pattern A is implemented; Pattern B will be added later through the same service).

**Authentication:** `DASHSCOPE_API_KEY` stored in `BackEnd/.env`, never in frontend, never committed. Set as environment variable on the server.

**Base URL for Singapore region:**

```
https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1

```

**Two call patterns your backend will use:**

**Pattern A — structured JSON output (most endpoints):** Use the standard OpenAI-compatible chat completions API with `response_format: {"type": "json_object"}`. Your system prompt must contain the word "JSON". Do not set `max_tokens` when structured output is enabled (it can truncate mid-JSON). Pydantic validates the parsed response immediately.

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen3.7-plus",  # from QWEN_MODEL in BackEnd/.env
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},   # must include "JSON"
        {"role": "user", "content": user_context_json}
    ],
    response_format={"type": "json_object"}
)
raw = response.choices[0].message.content
validated = MyPydanticModel.model_validate_json(raw)

```

**Pattern B — MCP tool calls (opportunity/sports search):** Use the Responses API (`client.responses.create`) with an MCP-compatible Qwen model. MCP transport is SSE for this implementation. Maximum 10 MCP servers per call. Your own MCP servers must expose an SSE endpoint.

```python
mcp_tool = {
    "type": "mcp",
    "server_protocol": "sse",
    "server_label": "pakistan_career",
    "server_description": "Pakistani career, university, and opportunity data",
    "server_url": "http://localhost:8001/career/sse",
}

response = client.responses.create(
    model="qwen3.7-plus",  # MCP-compatible model, from configuration
    input=prompt_string,
    tools=[mcp_tool]
)
result = response.output_text

```

**Important:** MCP via Responses API and structured JSON output via Chat Completions are two different API surfaces. For most endpoints use Pattern A (cheaper, faster, simpler). Use Pattern B only when the AI needs to call tools to retrieve data it cannot see in the prompt.

**Model version stability:** Pin the model in `BackEnd/.env` (`QWEN_MODEL=qwen3.7-plus` for the MVP) so behaviour doesn't change under you during the hackathon.

---

## 4. AI Architecture

### What is deterministic (never touch the LLM)

- Student profile CRUD
- Roadmap stage transitions (state machine, see §7)
- Opportunity retrieval from database
- Alumni search
- Pydantic schema validation
- Matching score calculation (simple weighted algorithm)
- Authentication and session management

### What the LLM does

- Analyse motivation and reflect it back without diagnosing
- Generate the Career Verdict (Good Fit / Worth Exploring / Reconsider) with reasoning
- Generate the Next Best Action from structured inputs
- Generate the 7-Day Career Trial plan dynamically
- Personalise roadmap step descriptions to the specific student
- Respond in the coaching chat
- Generate the Job Readiness assessment text
- Interpret a student's free-text description of their situation

### Data trust hierarchy (enforced in code, not just policy)

```
Priority 1 (highest): Verified structured data in SQLite
              ↓
Priority 2:   MCP tool results from your own servers (read from SQLite seed data)
              ↓
Priority 3:   AI interpretation of Priority 1/2 data
              ↓
Priority 4 (lowest): Qwen general knowledge

```

**Rule:** The system prompt explicitly instructs Qwen: "You must never state a specific opportunity, deadline, salary figure, or institution name unless it was provided in the context JSON. If no data was provided, say the information is not available rather than inventing it."

### System prompt design

One master system prompt template with variable injection slots:

```
You are a Pakistan-focused career and sports mentor.
Your job is to give ONE clear next step to Pakistani students.

STUDENT CONTEXT:
{student_profile_json}

AVAILABLE DATA:
{structured_data_json}

RULES:
- Never invent opportunity data. If no data was provided, say so.
- Always reason from Pakistan-specific context.
- Output valid JSON only in this schema: {schema_name}
- Keep advice motivating but realistic.
- Do not overwhelm. Give ONE next step at a time.

```

---

## 5. MCP Architecture

**Critical design decision:** Your MCP servers are wrappers over your own SQLite database. They do not call external APIs in the MVP. This means they are fast, reliable, and offline-safe. They expose data to Qwen that would otherwise be too large to fit in the prompt.

**When to use MCP vs a normal service call:**

| Situation Use MCP?                                         |                         |
| ---------------------------------------------------------- | ----------------------- |
| Qwen needs to search or filter a large dataset dynamically | Yes                     |
| Fixed lookup (e.g. get career by slug)                     | No — normal DB query    |
| Qwen needs to call a tool based on conversational context  | Yes                     |
| You know exactly what data to send before calling Qwen     | No — inject into prompt |

For the MVP, MCP is used in two places: opportunity/sports matching (where Qwen decides which filters to apply) and alumni discovery (where Qwen picks based on student profile). All other AI calls use Pattern A with data pre-injected into the prompt.

**MCP server setup:** Use `fastmcp` (Python package). Mount as SSE on a sub-path of your FastAPI app. This avoids running a separate process.

```python
# /mcp/career_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="PakistanCareer")

@mcp.tool()
def get_career_reality(career_slug: str) -> dict:
    """Returns demand, competition, skills, Pakistan opportunities for a career."""
    return db.query_career(career_slug)

@mcp.tool()
def search_internships(skills: list[str], city: str = None) -> list[dict]:
    """Searches verified Pakistani internship opportunities."""
    return db.search_opportunities(type="internship", skills=skills, city=city)

```

**Two MCP servers (all SSE, mounted in FastAPI):**

**Server 1: Pakistan Career & Education** (`/mcp/career/sse`)

- `get_career(slug)` — career details
- `get_career_reality(slug)` — demand, competition, skills, risks
- `get_required_skills(career_slug, stage)` — skills needed at a given stage
- `get_university_opportunities(field, city)` — university-based opportunities
- `get_scholarships(criteria)` — scholarship matching

**Server 2: Pakistan Opportunities & Sports** (`/mcp/opportunity/sse`)

- `search_internships(skills, city, field)` — internship search
- `search_jobs(skills, city, experience_level)` — job search
- `match_opportunity(student_profile, opportunity_id)` — match score + gaps
- `search_sports_opportunities(sport, city)` — tournaments, trials, teams
- `search_sports_scholarships(sport, level)` — sports-specific scholarships
- `search_university_sports(sport, city)` — university sports programmes

Alumni remains a normal FastAPI/SQLite service using direct database queries; it does not require a separate MCP server for the MVP.

---

## 6. Journey State Machine

The student's `education_stage` field is an enum. State transitions are triggered by explicit student actions (completing a milestone, confirming a decision) — never automatically by the AI.

```python
from enum import Enum

class EducationStage(str, Enum):
    HIGH_SCHOOL = "HIGH_SCHOOL"
    CAREER_DISCOVERY = "CAREER_DISCOVERY"
    CAREER_DECISION = "CAREER_DECISION"
    UNIVERSITY = "UNIVERSITY"
    SKILL_BUILDING = "SKILL_BUILDING"
    PROJECTS = "PROJECTS"
    INTERNSHIP = "INTERNSHIP"
    FINAL_YEAR = "FINAL_YEAR"
    JOB_PREPARATION = "JOB_PREPARATION"
    FIRST_JOB = "FIRST_JOB"

VALID_TRANSITIONS = {
    EducationStage.HIGH_SCHOOL: [EducationStage.CAREER_DISCOVERY],
    EducationStage.CAREER_DISCOVERY: [EducationStage.CAREER_DECISION],
    EducationStage.CAREER_DECISION: [EducationStage.UNIVERSITY, EducationStage.SKILL_BUILDING],
    # ... etc
}

```

This is a **database field + transition validation function** — not a separate state machine library. Keep it simple.

---

## 7. Complete Database Schema

```sql
-- Students table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    education_stage TEXT NOT NULL DEFAULT 'HIGH_SCHOOL',
    career_goal TEXT,
    sports_interest TEXT,
    motivation_tags TEXT,       -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student profile (evolving context)
CREATE TABLE student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER UNIQUE NOT NULL REFERENCES students(id),
    interests TEXT,             -- JSON array
    skills TEXT,                -- JSON array of {name, level}
    completed_milestone_ids TEXT, -- JSON array of ints
    job_readiness_score REAL DEFAULT 0.0,
    next_best_action TEXT,      -- JSON blob of last NBA
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Careers (seed data)
CREATE TABLE careers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    field TEXT NOT NULL,
    demand_level TEXT,          -- HIGH/MEDIUM/LOW
    competition_level TEXT,     -- HIGH/MEDIUM/LOW
    difficulty_level TEXT,
    required_skills TEXT,       -- JSON array
    pk_opportunities TEXT,      -- JSON array of descriptions
    top_pk_universities TEXT,   -- JSON array
    risks TEXT,                 -- JSON array
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roadmaps
CREATE TABLE roadmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    career_id INTEGER REFERENCES careers(id),
    current_stage TEXT NOT NULL,
    current_step_title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Milestones
CREATE TABLE milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id INTEGER NOT NULL REFERENCES roadmaps(id),
    title TEXT NOT NULL,
    description TEXT,
    stage TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending/active/done/skipped
    order_index INTEGER NOT NULL,
    completed_at TIMESTAMP
);

-- Alumni (seed + community submitted)
CREATE TABLE alumni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    university TEXT,
    field TEXT,
    role TEXT,
    company TEXT,
    career_path TEXT,           -- free text
    advice TEXT,                -- free text
    tags TEXT,                  -- JSON array for matching
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Opportunities (internships, jobs, scholarships, education)
CREATE TABLE opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,         -- internship/job/scholarship/education
    title TEXT NOT NULL,
    organization TEXT,
    location TEXT,
    deadline DATE,
    required_skills TEXT,       -- JSON array
    description TEXT,
    source_url TEXT,
    last_verified DATE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Sports opportunities
CREATE TABLE sports_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport TEXT NOT NULL,
    type TEXT NOT NULL,         -- tournament/trial/scholarship/programme
    title TEXT NOT NULL,
    organization TEXT,
    location TEXT,
    deadline DATE,
    eligibility TEXT,           -- JSON
    description TEXT,
    source_url TEXT,
    last_verified DATE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Opportunity matches (cached)
CREATE TABLE student_opportunity_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    opportunity_id INTEGER NOT NULL REFERENCES opportunities(id),
    match_score REAL,
    missing_requirements TEXT,  -- JSON array
    next_action TEXT,
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

---

## 8. Complete API Map

**Base path:** `/api/v1`

For the MVP, requests use the active demo-student/session context; full JWT authentication can be added later if time permits.

---

### Auth

**`POST /api/v1/auth/register`**

- Request: `{name, email, password}`
- Response: `{student_id, education_stage}`
- DB: insert student, create empty profile

**`POST /api/v1/auth/login`**

- Request: `{email, password}`
- Response: `{student_id, education_stage, name}`

---

### Onboarding

**`POST /api/v1/onboarding`**

- Purpose: Collect initial profile after registration. Called once.
- Request:

```json
{
  "education_stage": "HIGH_SCHOOL",
  "interests": ["technology", "mathematics"],
  "career_interests": ["software_engineering"],
  "sports_interest": "badminton",
  "motivation_tags": ["genuine_interest", "salary"],
  "skills": [{"name": "Python", "level": "beginner"}],
  "city": "Karachi"
}

```

- Response: `{profile_updated: true, next_best_action: NextBestAction}`
- AI: calls Qwen with profile to generate first Next Best Action
- Validation: all fields Pydantic-validated; `education_stage` must be valid enum

---

### Careers

**`GET /api/v1/careers`**

- Purpose: List all available careers (for discovery UI)
- Response: `[{slug, name, field, demand_level}]`
- DB only, no AI

**`GET /api/v1/careers/{slug}`**

- Response: full career object from DB

**`POST /api/v1/career/analyze`**

- Purpose: Run Career Reality Check for a specific career against the student's profile
- Request: `{career_slug}`
- Response: `CareerReality + CareerVerdict`
- AI: inject career data + student profile → Qwen → validated JSON
- MCP: optionally call `get_career_reality()` if richer data is needed

**`POST /api/v1/career/trial-plan`**

- Purpose: Generate a 7-day trial plan
- Request: `{career_slug}`
- Response: `CareerTrialPlan`
- AI: Qwen generates dynamic plan based on career + student skills

---

### Journey & Roadmap

**`GET /api/v1/journey`**

- Purpose: Return current student state — stage, active milestones (max 3), Next Best Action
- Response: `{stage, current_step, next_steps: [1..3], next_best_action}`
- DB only for milestones; Next Best Action from cache in profile

**`POST /api/v1/roadmap`**

- Purpose: Create or regenerate roadmap after career decision
- Request: `{career_slug, target_stage}`
- Response: `{roadmap_id, current_step, visible_steps: [1..3]}`
- AI: Qwen generates personalised roadmap JSON; the backend persists the current roadmap state through `roadmaps` and `milestones`

**`POST /api/v1/progress`**

- Purpose: Mark a milestone complete, advance stage if appropriate
- Request: `{milestone_id, status: "done"}`
- Response: `{new_stage, next_best_action}`
- DB: update milestone; trigger NBA recalculation

---

### Opportunities

**`GET /api/v1/opportunities`**

- Query params: `type, city, field, skills`
- Response: `[Opportunity]` — from DB only, no AI

**`POST /api/v1/opportunities/match`**

- Purpose: AI-ranked opportunity matches for the student
- Response: `[OpportunityMatch]` sorted by score
- AI (MCP Pattern B): Qwen calls `search_internships()` or `search_jobs()` via MCP, then scores matches

---

### Sports

**`GET /api/v1/sports`**

- Query params: `sport, city, type`
- Response: `[SportsOpportunity]` — from DB only

**`POST /api/v1/sports/match`**

- Purpose: Match student to relevant sports opportunities
- Request: `{sport, location, level}`
- Response: `[SportsOpportunityMatch]`
- AI (MCP Pattern B): calls `search_sports_opportunities()` via MCP

---

### Alumni

**`GET /api/v1/alumni`**

- Query params: `field, university, role`
- Response: `[AlumniCard]` — from DB

**`GET /api/v1/alumni/{id}`**

- Response: full alumni profile

---

### Job Readiness

**`POST /api/v1/job-readiness`**

- Purpose: Calculate and return job readiness score
- Response: `JobReadiness`
- Logic: weighted deterministic score (skills 30%, projects 20%, internship 20%, CV 15%, interview 15%) + AI-generated gap analysis text
- Note: result includes disclaimer text that this is a product indicator, not a scientific assessment

---

### Coach Chat

**`POST /api/v1/coach/chat`**

- Purpose: Conversational AI mentor
- Request: `{message, conversation_history: [{role, content}]}`
- Response: `CoachResponse`
- AI (Pattern A): full student profile + last 5 messages + structured data → Qwen → `CoachResponse` JSON
- Rate limit: 20 requests per hour per student (prevents credit drain)

---

## 9. Pydantic Response Schemas

These are the exact schemas Qwen must output, validated before the response leaves the backend.

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date

class NextBestAction(BaseModel):
    title: str                          # "Start the 7-Day CS Trial"
    description: str                    # 2-3 sentences max
    steps: list[str]                    # max 3 concrete steps
    estimated_time: str                 # "3–4 hours this week"
    why_this_matters: str               # 1 sentence
    stage: str                          # which roadmap stage this serves

class MotivationAnalysis(BaseModel):
    primary_motivation: str             # most prominent tag
    reflection_note: str                # honest, non-judgmental 2-3 sentences
    recommendation: str                 # brief directional suggestion

class CareerReality(BaseModel):
    career_name: str
    demand_level: Literal["HIGH", "MEDIUM", "LOW"]
    competition_level: Literal["HIGH", "MEDIUM", "LOW"]
    difficulty_level: Literal["HIGH", "MEDIUM", "LOW"]
    required_skills: list[str]
    pk_opportunities: list[str]         # all from DB, never invented
    risks: list[str]
    rewards: list[str]
    data_source: str                    # e.g. "BanoQabil career database, updated 2025"

class CareerVerdict(BaseModel):
    verdict: Literal["GOOD_FIT", "WORTH_EXPLORING", "RECONSIDER"]
    headline: str                       # one sentence summary
    reasoning: str                      # 3-4 sentences
    student_strengths_match: list[str]
    gaps_to_address: list[str]
    suggested_trial: Optional[str]

class CareerTrialPlan(BaseModel):
    career_slug: str
    duration_days: int                  # always 7 for MVP
    days: list[dict]                    # [{day_range: "1-2", title, tasks: [str]}]
    reflection_prompt: str              # end-of-trial question for the student

class Roadmap(BaseModel):
    student_id: int
    career_slug: str
    stages: list[dict]                  # [{stage, title, milestones: [str], estimated_duration}]
    current_stage: str
    visible_next_steps: list[str]       # max 3, shown to frontend

class OpportunityMatch(BaseModel):
    opportunity_id: int
    title: str
    organization: str
    match_score: float                  # 0.0 to 1.0
    match_reasons: list[str]           # from DB data only
    missing_requirements: list[str]
    next_action: str
    deadline: Optional[date]
    source_url: str

class SportsOpportunityMatch(BaseModel):
    opportunity_id: int
    sport: str
    title: str
    organization: str
    match_score: float
    eligibility_met: list[str]
    eligibility_missing: list[str]
    next_action: str
    deadline: Optional[date]
    source_url: str

class JobReadiness(BaseModel):
    overall_score: float                # 0.0 to 1.0
    score_label: str                    # e.g. "74%"
    component_scores: dict              # {skills: 0.8, projects: 0.6, ...}
    biggest_gap: str
    next_best_action: NextBestAction
    disclaimer: str                     # always included, non-negotiable

class CoachResponse(BaseModel):
    message: str                        # the mentor's response
    quick_actions: list[str]           # max 3 follow-up prompts the student can tap
    suggested_resource: Optional[str]  # a specific link from DB, never invented

class AlumniCard(BaseModel):
    id: int
    name: str
    university: str
    field: str
    role: str
    company: str
    career_path_summary: str
    key_advice: str
    tags: list[str]

```

---

## 10. Error Handling

**Qwen API failure:**

- Catch `openai.APIError`, `openai.APIConnectionError`, `openai.RateLimitError`
- Return HTTP 503 with `{error: "AI service temporarily unavailable", fallback_content: <cached_last_nba>}`
- Never fabricate a response. Show the last cached Next Best Action if one exists.

**MCP server failure:**

- If an MCP tool call fails, the backend catches the exception and retries once
- After retry failure: return opportunities from DB using a direct query, bypassing AI ranking
- Response includes `{data_quality: "unranked", note: "Live ranking is temporarily unavailable."}`

**Pydantic validation failure (AI returned bad JSON):**

- Log the raw response for debugging
- Retry the AI call once with a stricter prompt: "Your last response was not valid JSON. Output only the JSON object matching this schema: {schema}"
- After second failure: return HTTP 500 with `{error: "AI response could not be processed"}`
- Never pass un-validated AI output to the frontend

**Opportunity data outdated:**

- Every opportunity record has `last_verified`. If `last_verified < today - 30 days`, add a flag `{data_freshness: "unverified"}` to the response
- Frontend displays: "This opportunity was last verified [date]. Please confirm directly."

**No opportunities found:**

- Return `{opportunities: [], message: "No matching opportunities found in our database right now. Check back soon or explore related fields."}`
- Never ask Qwen to suggest opportunities from its general knowledge

**Invalid student input:**

- Pydantic raises `ValidationError` → return HTTP 422 with field-level errors
- Frontend shows inline validation messages

---

## 11. Folder Structure

```
bano-qabil/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # settings, env vars
│   ├── database.py                 # SQLAlchemy engine + session
│   ├── models/
│   │   ├── student.py
│   │   ├── career.py
│   │   ├── roadmap.py
│   │   ├── opportunity.py
│   │   └── alumni.py
│   ├── schemas/                    # Pydantic models
│   │   ├── requests.py             # inbound request schemas
│   │   └── responses.py            # ALL AI output schemas (as defined in §9)
│   ├── routers/
│   │   ├── auth.py
│   │   ├── onboarding.py
│   │   ├── careers.py
│   │   ├── journey.py
│   │   ├── opportunities.py
│   │   ├── sports.py
│   │   ├── alumni.py
│   │   ├── job_readiness.py
│   │   └── coach.py
│   ├── services/
│   │   ├── ai_service.py           # Qwen calls, prompt assembly, validation
│   │   ├── career_service.py
│   │   ├── roadmap_service.py
│   │   ├── opportunity_service.py
│   │   ├── matching_service.py     # deterministic match score logic
│   │   └── job_readiness_service.py
│   ├── prompts/
│   │   ├── system_prompt.py        # master system prompt template
│   │   ├── career_analysis.py
│   │   ├── next_best_action.py
│   │   ├── trial_plan.py
│   │   └── coach.py
│   └── tests/
│       ├── test_career.py
│       ├── test_ai_service.py
│       └── test_opportunities.py
├── mcp/
│   ├── career_server.py            # FastMCP server 1
│   └── opportunity_server.py       # FastMCP server 2 (career opportunities + sports)
├── data/
│   ├── seed/
│   │   ├── careers.json            # Pakistani career data
│   │   ├── universities.json       # Pakistani universities
│   │   ├── opportunities.json      # internships, jobs
│   │   ├── sports_opportunities.json
│   │   └── alumni.json
│   └── seed_db.py                  # script to populate SQLite from JSON
├── frontend/                       # Antigravity's Next.js app
│   ├── app/
│   ├── components/
│   └── lib/
│       └── api.ts                  # all API calls centralised here
├── docs/
│   ├── architecture.md             # this document
│   ├── api_contracts.md
│   └── seed_data_format.md
├── .env.example
├── .gitignore
└── requirements.txt

```

---

## 12. Security Model

**API keys:** `DASHSCOPE_API_KEY` in `.env`, never committed to git, never sent to frontend.

**Authentication:** For the MVP, use a simple demo-student session/context rather than a full registration and JWT system. Keep authenticated student identity behind the backend and ensure all student-specific data is scoped by `student_id`. Add full JWT authentication only if time permits.

**Database:** SQLite file not exposed via any endpoint. All queries through SQLAlchemy ORM (prevents SQL injection by default).

**CORS:** FastAPI CORS middleware configured to allow only the Next.js origin (`http://localhost:3000` in dev, production domain in prod).

**Rate limiting:** Coach chat capped at 20 requests/hour per student using a simple in-memory counter (upgrade to Redis if needed). Prevents runaway Qwen credit consumption.

**Data isolation:** Every DB query filters by `student_id` extracted from the JWT. Students can never access other students' data.

**Opportunity data integrity:** No endpoint allows creating opportunities from user input. Only seed scripts and admin tooling write to the opportunities table.

---

## 13. Antigravity Integration Contract

**API contract (Antigravity must respect these, never bypass):**

All API calls go to the FastAPI backend. The frontend never calls Qwen directly. Never calls the database directly.

**Base URL:** `http://localhost:8000/api/v1` (dev) — configure via `NEXT_PUBLIC_API_URL` env var.

**Auth flow:** For the MVP, use the active demo-student/session context. Full JWT authentication can be added later if time permits.

**Component expectations:**

```
OnboardingWizard → POST /onboarding → receives NextBestAction → show in NextStepCard
CareerExplorer → GET /careers → list → user picks → POST /career/analyze → CareerReality + CareerVerdict
CareerDecision → POST /career/trial-plan → show 7-day plan
JourneyView → GET /journey → show current step + 1-3 visible next steps (never the full roadmap)
CoachChat → POST /coach/chat (streaming preferred) → CoachResponse
OpportunityBoard → GET /opportunities → list → POST /opportunities/match → ranked list
SportsBoard → GET /sports → POST /sports/match → ranked list
JobReadinessDashboard → POST /job-readiness → JobReadiness (show disclaimer)

```

**Field naming:** All API responses use `snake_case`. Frontend converts to `camelCase` only at the component boundary (use a utility function, not ad-hoc field access).

**Error handling in frontend:** Every API call must handle `{error: string}` responses gracefully. Show user-friendly messages, never raw error strings.

**Do not add new query parameters or body fields to existing endpoints without backend approval.** The backend validates all inputs strictly with Pydantic.

**The** **`visible_next_steps`** **array from** **`/journey`** **must never show more than 3 items regardless of what the backend returns.**

---

## 14. Qoder Credit Strategy

With 2,600 credits, every agent request has a cost. Strategy:

**High-value agent tasks (use larger, focused requests):**

- "Implement the complete `ai_service.py` with Qwen Pattern A and Pattern B, error handling, retry logic, and Pydantic validation" — this is one coherent task that Qoder can do end-to-end
- "Implement the 2 MCP servers using FastMCP with these tool signatures: [paste exact signatures]" — give Qoder the exact function signatures from this document
- "Implement the SQLAlchemy models for all 9 tables using this schema: [paste DDL]"
- "Implement the `POST /api/v1/career/analyze` endpoint end-to-end: router → service → Qwen call → Pydantic validation → response"

**Cheaper, targeted tasks:**

- Adding a new field to a Pydantic schema
- Writing a specific test case
- Debugging a specific error (paste the traceback)
- Writing the seed data loader script

**Do NOT spend credits on:**

- Frontend/UI work (that's Antigravity)
- Writing this architecture document (that's Claude's role)
- Anything you can do yourself in 5 minutes (creating folders, writing `.env.example`)
- Rewriting working code (once a service passes tests, mark it done and lock it)

**To prevent Qoder from rewriting working code:** At the start of each Qoder session, paste a brief status note: "The following files are complete and should not be modified unless there's a bug: [list files]." Keep a `DONE.md` in the repo root listing completed components.

**Recommended task batching:** Give Qoder one complete vertical slice at a time (model + schema + service + router + test for one feature), not individual files. This produces more coherent code and fewer integration bugs.

---

## 15. VS Code Setup Instructions

Open VS Code. Open the integrated terminal with `Ctrl+`` ` (backtick).

**Step 1 — Create the project root:**

```bash
mkdir bano-qabil
cd bano-qabil

```

**Step 2 — Create the folder structure:**

```bash
mkdir -p backend/{models,schemas,routers,services,prompts,tests}
mkdir -p mcp data/seed docs frontend

```

**Step 3 — Create the Python virtual environment:**

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

```

**Step 4 — Create requirements.txt and install:**

```
fastapi
uvicorn[standard]
sqlalchemy
python-jose[cryptography]
passlib[bcrypt]
pydantic
openai
python-dotenv
fastmcp
httpx
pytest
pytest-asyncio

```

```bash
pip install -r requirements.txt

```

**Step 5 — Create .env:**

```bash
# Create .env in project root
touch .env

```

Add to `.env`:

```
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_WORKSPACE_ID=your-workspace-id
DASHSCOPE_BASE_URL=https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
SECRET_KEY=your-random-jwt-secret-here
DATABASE_URL=sqlite:///./bano_qabil.db

```

**Step 6 — Create .gitignore:**

```
.env
.venv/
__pycache__/
*.pyc
*.db
.DS_Store

```

**Step 7 — Verify FastAPI is working:**
Create `backend/main.py` with a hello world endpoint, then:

```bash
cd backend
uvicorn main:app --reload --port 8000

```

Open `http://localhost:8000/docs` — you should see the Swagger UI.

**Step 8 — Verify Qwen connection:**

```python
# test_qwen.py (run once, then delete)
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL").replace("{WorkspaceId}", os.getenv("DASHSCOPE_WORKSPACE_ID"))
)
response = client.chat.completions.create(
    model="qwen3.7-plus",  # from QWEN_MODEL in BackEnd/.env
    messages=[{"role": "user", "content": "Say hello in JSON format with key 'greeting'"}],
    response_format={"type": "json_object"}
)
print(response.choices[0].message.content)

```

```bash
python test_qwen.py

```

You should see `{"greeting": "Hello!"}` or similar.

---

## 16. Exact Implementation Order

### Phase 1 — Foundation (Day 1)

**Objective:** Working FastAPI app connected to SQLite, all models defined.
**Files:** `backend/main.py`, `backend/config.py`, `backend/database.py`, `backend/models/*.py`
**Test:** `GET /api/v1/health` returns `{status: "ok"}`; all tables created in SQLite
**Qoder task:** "Create all 9 SQLAlchemy models from this schema: [paste DDL]"

### Phase 2 — Auth + Student Profile (Day 1–2)

**Objective:** Register, login, JWT, onboarding endpoint.
**Files:** `backend/routers/auth.py`, `backend/routers/onboarding.py`, `backend/schemas/requests.py`
**Test:** Can register, login, receive token, call onboarding
**Qoder task:** "Implement JWT auth with bcrypt password hashing and the /auth/register and /auth/login endpoints"

### Phase 3 — Qwen Integration (Day 2)

**Objective:** `ai_service.py` working with both Pattern A and Pattern B, with full error handling.
**Files:** `backend/services/ai_service.py`, `backend/prompts/system_prompt.py`
**Test:** Call `ai_service.call_structured(prompt, schema)` and get a validated Pydantic object back
**Qoder task:** "Implement ai\_service.py with Pattern A (chat completions + json\_object) and Pattern B (responses API + MCP), retry logic, Pydantic validation, and graceful fallback"

### Phase 4 — Seed Data (Day 2–3)

**Objective:** Pakistani career, university, opportunity, sports, alumni data in the database.
**Files:** `data/seed/*.json`, `data/seed_db.py`
**Test:** `GET /api/v1/careers` returns at least 20 Pakistani careers
**This is your job, not Qoder's** — research and write the JSON seed files yourself. This is the Pakistan-specific data that makes the product real. Focus on: top 20 careers in Pakistan, top 15 universities per field, 30+ internship opportunities, 20 sports opportunities across 5 sports, 20 alumni profiles.

### Phase 5 — Career Intelligence (Day 3)

**Objective:** Career analysis, reality check, verdict, trial plan all working end-to-end.
**Files:** `backend/routers/careers.py`, `backend/services/career_service.py`, `backend/prompts/career_analysis.py`
**Test:** `POST /career/analyze` returns valid `CareerReality + CareerVerdict` for "software-engineering"

### Phase 6 — Roadmap & Next Best Action (Day 3–4)

**Objective:** Roadmap creation, journey view, milestone progress, NBA generation.
**Files:** `backend/routers/journey.py`, `backend/services/roadmap_service.py`, `backend/prompts/next_best_action.py`
**Test:** After onboarding, `GET /journey` returns stage + exactly 3 visible steps + NBA

### Phase 7 — MCP Servers (Day 4)

**Objective:** Both MCP servers running as SSE endpoints, registered in the FastAPI app.
**Files:** `mcp/*.py`
**Test:** Qwen can call `search_internships(skills=["Python"])` via MCP and return DB results
**Qoder task:** "Implement 2 FastMCP servers with these tool signatures, mounted as SSE in FastAPI"

### Phase 8 — Opportunities, Sports, Alumni (Day 4–5)

**Objective:** All matching endpoints working with AI ranking.
**Files:** `backend/routers/opportunities.py`, `backend/routers/sports.py`, `backend/routers/alumni.py`, `backend/services/matching_service.py`
**Test:** `POST /opportunities/match` returns ranked list with scores, gaps, and next actions

### Phase 9 — Job Readiness & Coach Chat (Day 5)

**Objective:** Job readiness score + coaching conversation working.
**Files:** `backend/routers/job_readiness.py`, `backend/routers/coach.py`, `backend/services/job_readiness_service.py`, `backend/prompts/coach.py`
**Test:** Coach chat maintains context across 3 turns; job readiness returns score + disclaimer

### Phase 10 — Testing & Hardening (Day 6–7 before Sep 3)

**Objective:** All happy paths tested, all error paths handled, demo script ready.
**Files:** `backend/tests/*.py`
**Test:** Run the full demo flow from registration → onboarding → career analysis → roadmap → opportunity match without any 500 errors
**Qoder task:** "Write pytest tests for these services: [paste service list]"

---

## 17. Definition of Done for MVP

The MVP is done when:

- [ ] A new student can register, complete onboarding, and receive their first Next Best Action
- [ ] Career Reality Check and Verdict work for at least 5 careers
- [ ] 7-Day Trial plan generates dynamically for any career
- [ ] Journey view shows stage + max 3 next steps (never the full roadmap)
- [ ] At least 20 Pakistani careers are in the seed database with real data
- [ ] At least 10 Pakistani internship opportunities are in the database
- [ ] At least 5 sports categories have opportunity data
- [ ] Opportunity matching returns match score + gap analysis + next action
- [ ] Alumni discovery shows relevant profiles
- [ ] Coach chat responds coherently to student questions
- [ ] Job readiness score calculates correctly with disclaimer
- [ ] All Qwen responses are Pydantic-validated before reaching the frontend
- [ ] Qwen API failures degrade gracefully (no 500 on AI timeout)
- [ ] No opportunity data is ever fabricated by the LLM
- [ ] The FastAPI `/docs` page shows all endpoints cleanly
- [ ] A complete demo run (15 minutes, scripted) works without errors

---

# First 10 Things You Should Do Today

1. **Create the folder structure.** Run the `mkdir` commands from §14 Step 1–2. Takes 2 minutes. Now the project exists.
2. **Set up your Python environment.** Create the venv, install requirements. Takes 5 minutes. Verify `fastapi`, `openai`, `sqlalchemy`, `pydantic` are importable.
3. **Get your Alibaba Cloud credentials.** Go to Alibaba Cloud Model Studio → API Keys → create a key for the Singapore region. Copy your WorkspaceId and API key. Save them in `.env`. This unblocks all AI work.
4. **Run the Qwen connection test** from §14 Step 8. Confirm you get a JSON response back. If this fails, everything else is blocked — fix it now, not on Day 5.
5. **Write** **`backend/database.py`** **and** **`backend/models/*.py`** — the 9 SQLAlchemy models from the schema in §7. This is a clean, self-contained Qoder task. Give Qoder the DDL and ask for SQLAlchemy 2.0 models with proper relationships.
6. **Write** **`backend/schemas/responses.py`** — paste all 9 Pydantic schemas from §9 exactly as shown. Do not modify them until Phase 3 is done. These schemas are the contract between Qwen and the frontend.
7. **Start the seed data JSON files.** Create `data/seed/careers.json` and populate 5 careers manually: Software Engineering, Medicine, Business/MBA, Teaching, and one sports career (Cricket Professional). Use real Pakistani data. This is research work, not coding — sit with a browser and fill it in.
8. **Create** **`backend/main.py`** with FastAPI app, CORS, and a `GET /api/v1/health` endpoint. Run `uvicorn main:app --reload`. Verify the Swagger docs open at `localhost:8000/docs`.
9. **Create** **`backend/services/ai_service.py`** — the most important file in the project. Implement Pattern A (chat completions with `json_object`) with the retry and Pydantic validation logic. Test it with a simple `NextBestAction` call before wiring it into any router.
10. **Write** **`backend/prompts/system_prompt.py`** — the master system prompt template. Keep it under 500 tokens. Test it by calling `ai_service.py` with a sample student profile and verifying the output validates against `NextBestAction`. This is the foundation every AI feature builds on.

---

*Architecture by Claude (CTO role). Implementation by Qoder. Frontend by Antigravity. Data by you. Pakistan-first.*