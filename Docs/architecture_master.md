# A&H Careers — Master Architecture Specification
## AI-Powered Student Career Journey for Pakistan

**Version:** 2.0 — Master Revision  
**Status:** Implementation-ready  
**Scope:** Hackathon MVP + long-term production architecture  
**Target:** Qoder implementation inside existing `A&H Career/` repository  
**Rule for Qoder:** Inspect the actual repository first. Preserve working code. Modify only what this document requires.

---

## Table of Contents

1. Product Definition
2. Goals and Non-Goals
3. High-Level Architecture
4. Component Responsibilities
5. Student Journey
6. AI Architecture
7. Qwen Integration
8. Data Trust Hierarchy
9. Pakistan Knowledge Base
10. Complete Database Schema
11. Source and Provenance Model
12. Web Ingestion Architecture
13. Social-Source Policy
14. Retrieval and Search Architecture
15. Caching
16. MCP Architecture
17. API Contract
18. AI and Pydantic Schemas
19. Next Best Action Architecture
20. Career Reality Check
21. AI Mentor
22. Opportunities
23. Sports
24. Alumni
25. Learning Resources
26. Security
27. Error Handling
28. Testing
29. Local Setup
30. Implementation Phases
31. Qoder Credit Strategy
32. Definition of Done
33. Future Expansion

---

## 1. Product Definition

A&H Careers is a Pakistan-first AI-powered career mentoring platform. Its purpose is to guide students from uncertainty toward a realistic career direction, and from there continuously through university, skill-building, internships, and first employment.

The product is a persistent mentor, not a chatbot. It remembers the student across sessions. It knows where the student is in their journey. It gives one clear next step, never a flood of tasks.

**The central product loop:**

```
Student Profile
    ↓
Understand Motivation
    ↓
Explore Careers
    ↓
Career Reality Check
    ↓
Career Verdict
    ↓
AI Mentor
    ↓
Next Best Action
    ↓
Student Action
    ↓
Progress Updated
    ↓
New Next Best Action
```

**The core UX principle:** Do not overwhelm the student. The backend may contain extensive knowledge. The student-facing output must remain small and focused — one direction, one next step, 1–3 visible actions at most.

**Pakistan-only in MVP.** All factual claims are grounded in verified Pakistani data. No foreign content is silently mixed in.

---

## 2. Goals and Non-Goals

### Goals

- Persistent, context-aware career mentoring for Pakistani students
- Data-grounded AI — LLM reasons over facts, never invents them
- Scalable Pakistan Knowledge Base covering education, careers, opportunities, sports, alumni, and learning resources
- Deterministic opportunity matching with AI explanation
- Candidate-constrained Next Best Action (LLM cannot invent actions)
- Web data ingestion with provenance, deduplication, and freshness tracking
- Clean local development — no deployment infrastructure required for this phase
- Long-term extensible schema that does not require rewrites as data grows
- Both a working hackathon demo and a foundation for continued development

### Non-Goals

- Deployment to cloud infrastructure (excluded from this phase)
- Social networking or student-to-student messaging
- Real-time notifications
- Video content hosting
- Payment processing
- Mobile app
- Foreign career markets
- Autonomous web crawling without admin initiation
- Bypassing platform authentication or access restrictions

---

## 3. High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Frontend  (Next.js 14 + TypeScript + Tailwind + shadcn) │
│  Existing Antigravity build — Frontend/                  │
└─────────────────────┬────────────────────────────────────┘
                      │ REST/JSON over HTTP
                      │ JWT Authorization header
┌─────────────────────▼────────────────────────────────────┐
│  API Layer  (FastAPI / Python)                           │
│  BackEnd/                                                │
│  ├── routers/          API endpoints                     │
│  ├── services/         Business + AI orchestration       │
│  ├── retrieval/        Knowledge retrieval layer         │
│  ├── ingestion/        Web ingestion subsystem           │
│  ├── schemas/          Pydantic request + response       │
│  ├── prompts/          Qwen prompt templates             │
│  └── tests/            Full test suite                   │
└──────┬───────────────────────────────┬───────────────────┘
       │                               │
┌──────▼──────────┐         ┌──────────▼──────────────────┐
│  SQLite DB      │         │  Qwen AI (DashScope)        │
│  (SQLAlchemy)   │         │  qwen3.7-plus               │
│                 │         │  Pattern A: json_object     │
│  Normalized     │         │  Pattern B: tool_calls/MCP  │
│  knowledge base │         │  web_search when enabled    │
└──────┬──────────┘         └──────────┬──────────────────┘
       │                               │
┌──────▼──────────┐         ┌──────────▼──────────────────┐
│  Retrieval      │         │  MCP Servers (SSE)          │
│  Layer          │◄────────│  Mcp/                       │
│  (deterministic)│         │  career_server.py           │
└─────────────────┘         │  opportunity_server.py      │
                            └─────────────────────────────┘
```

**Key architectural rules enforced in code, not just policy:**
- Frontend never calls Qwen directly
- `ai_service.py` is the only Qwen integration point
- Every structured AI output is Pydantic-validated before reaching the frontend
- MCP servers read from the normalized DB only — they do not perform live web retrieval
- Ingestion runs only through admin endpoints — never from student-facing requests
- Stage transitions are deterministic — Qwen cannot advance a student stage

---

## 4. Component Responsibilities

### Frontend (`Frontend/`)
Owned by Antigravity. Qoder does not redesign the frontend. Qoder may make minimal changes to connect real APIs, replace mock data, fix integration bugs, or adjust types.

**Responsibilities:** Render student-facing UI. Manage frontend state. Call backend REST endpoints. Display one current direction and 1–3 visible next steps. Never call Qwen directly.

### API Layer (`BackEnd/routers/`)
FastAPI routers. Receive validated requests, delegate to services, return validated responses.

**Responsibilities:** Auth. Input validation (Pydantic). Route to correct service. Return typed responses. Apply rate limiting where specified.

### Services (`BackEnd/services/`)
Business logic. The heart of the system.

**Responsibilities:** Career logic. Roadmap management. Journey state transitions. Opportunity matching (deterministic). Job readiness scoring (deterministic). AI orchestration (calls `ai_service.py`). Context assembly for Qwen calls.

### AI Service (`BackEnd/services/ai_service.py`)
**Single integration point for all Qwen calls.** No other file may instantiate a Qwen/DashScope client.

**Responsibilities:** Qwen client initialization. Pattern A calls (json_object). Pattern B calls (tool_calls / MCP). Retry logic. Pydantic validation of AI output. Secret-safe logging. Fallback on failure.

### Retrieval Layer (`BackEnd/retrieval/`)
Deterministic knowledge retrieval. Called by services before assembling AI context.

**Responsibilities:** Query the normalized knowledge base. Return bounded, relevant, verified records. Never return the entire knowledge base. Apply freshness filters. Respect verification status.

### Ingestion Subsystem (`BackEnd/ingestion/`)
Admin-only pipeline for adding knowledge to the database from external sources.

**Responsibilities:** URL retrieval. Content extraction (using Qwen as extractor, not truth source). Structured normalization. Validation. Deduplication. Verification status tracking. Provenance persistence.

### MCP Servers (`Mcp/`)
FastMCP servers exposing retrieval tools to Qwen via SSE.

**Responsibilities:** Expose search and retrieval tools for careers, opportunities, sports, alumni, and learning resources. Read only from normalized verified DB. Never perform live web retrieval.

### Data Layer
SQLite + SQLAlchemy. Normalized relational structure.

**Responsibilities:** Source of truth for all factual records. Stores student data, knowledge base, provenance, ingestion records, and journey state.

---

## 5. Student Journey

### Journey Stages (enum)

```
HIGH_SCHOOL
CAREER_DISCOVERY
CAREER_DECISION
UNIVERSITY
SKILL_BUILDING
PROJECTS
INTERNSHIP
FINAL_YEAR
JOB_PREPARATION
FIRST_JOB
```

### Valid Transitions

```
HIGH_SCHOOL           → CAREER_DISCOVERY
CAREER_DISCOVERY      → CAREER_DECISION
CAREER_DECISION       → UNIVERSITY | SKILL_BUILDING
UNIVERSITY            → SKILL_BUILDING
SKILL_BUILDING        → PROJECTS
PROJECTS              → INTERNSHIP | FINAL_YEAR
INTERNSHIP            → FINAL_YEAR | SKILL_BUILDING
FINAL_YEAR            → JOB_PREPARATION
JOB_PREPARATION       → FIRST_JOB
```

**Transitions are triggered only by:** completed milestone event, confirmed career decision event, explicit stage advancement event — all via backend service, never directly by Qwen.

### Career Pathway

```
HIGH_SCHOOL → CAREER_DISCOVERY → CAREER_DECISION → UNIVERSITY 
→ SKILL_BUILDING → PROJECTS → INTERNSHIP → FINAL_YEAR 
→ JOB_PREPARATION → FIRST_JOB
```

### Sports Pathway (secondary)

```
Interest Discovery → Sports Reality/Eligibility → Tournaments/Trials 
→ Sports Scholarships → University Sports Opportunities → Continued Development
```

Sports is architecturally supported. It shares the opportunities and matching infrastructure. It does not create a separate parallel journey state machine — a student may pursue sports alongside their career pathway.

---

## 6. AI Architecture

### What the LLM does

- Interpret student motivation (reflection, not diagnosis)
- Generate Career Verdict reasoning (Good Fit / Worth Exploring / Reconsider)
- Select ONE Next Best Action from a deterministic candidate list
- Produce personalized roadmap step descriptions
- Respond in the AI Mentor coach chat
- Generate Job Readiness gap explanation (score is deterministic)
- Generate Career Trial Plan structure
- Extract structured information from retrieved web content (ingestion only)

### What the LLM does NOT do

- Invent Pakistani universities, programs, organizations, or opportunities
- Generate salary figures, deadlines, or eligibility rules
- Advance student journey stages
- Create opportunity records
- Alter deterministic match scores
- Alter deterministic job readiness scores
- Create Next Best Action candidates (it selects from a provided list only)
- Determine data verification status

### AI context assembly rule

Before any Qwen call, the service layer assembles context:
1. Student profile (relevant fields only, not the full record)
2. Retrieved verified records from the retrieval layer (bounded — max defined per call type)
3. Candidate list if applicable (for NBA)
4. Instructions including hard grounding rules

The assembled context must be bounded. Token budgets per call type are defined in the prompt templates.

---

## 7. Qwen Integration

### Model

**Primary:** `qwen3.7-plus` (already configured in the project)

**Configuration:** All model references must use the environment variable `QWEN_MODEL`. Do not hard-code the model string in business logic files. If the model is replaced, only the env var changes.

### API Client

**Single file:** `BackEnd/services/ai_service.py`

**Library:** `openai` Python SDK (DashScope OpenAI-compatible endpoint)

**Credential:** `DASHSCOPE_API_KEY` in `BackEnd/.env` only. Never move it.

**Base URL:** `DASHSCOPE_BASE_URL` in `.env` (Singapore region endpoint)

### Pattern A — Structured JSON output (most endpoints)

```
model: QWEN_MODEL
messages: [system_prompt, user_context]
response_format: {"type": "json_object"}
```

System prompt must contain the word "JSON". Do not set `max_tokens` when using json_object (risks truncation). Parse response. Validate with Pydantic. On ValidationError: retry once with stricter prompt. On second failure: return deterministic fallback.

### Pattern B — Tool calls / MCP (opportunity and sports matching)

```
model: QWEN_MODEL
input: prompt_string
tools: [mcp_server_config]
```

Used when Qwen needs to dynamically select which data to retrieve. MCP transport: SSE. Max MCP servers: 10 per call. Use only when tool selection adds genuine value over pre-fetching.

### Web Search (when enabled)

`qwen3.7-plus` supports `web_search` as a tool. This is used **only within the ingestion subsystem** when an admin triggers a search-based discovery run. It is NOT used during student-facing requests. Student-facing requests retrieve from the normalized DB only.

### Environment variables

```
DASHSCOPE_API_KEY        — required, server-side only
DASHSCOPE_WORKSPACE_ID   — required, server-side only
DASHSCOPE_BASE_URL       — required, server-side only
QWEN_MODEL               — required, defaults to qwen3.7-plus
DATABASE_URL             — required
SECRET_KEY               — required (JWT signing)
CORS_ORIGINS             — required (comma-separated origins)
LOG_LEVEL                — optional, defaults to INFO
NEXT_PUBLIC_API_URL      — frontend, public
NEXT_PUBLIC_USE_MOCK     — frontend, must be false in real mode
```

Startup: validate all required variables. If any are missing, raise `RuntimeError` with clear message listing the missing variable. Do not start the application.

### Logging rules

- Never log `DASHSCOPE_API_KEY` value
- Never log full student profiles (log student_id only)
- Sanitize any string before logging: replace `sk-[A-Za-z0-9]{20,}` with `[REDACTED]`
- Log errors with enough context for debugging but no secrets

---

## 8. Data Trust Hierarchy

```
Tier 1 (highest): Verified structured Pakistan data in DB
                  (manually verified or officially confirmed)

Tier 2:           Approved official web-source data ingested through pipeline
                  (source type OFFICIAL_GOVERNMENT, OFFICIAL_UNIVERSITY, 
                   OFFICIAL_COMPANY, OFFICIAL_SPORTS)

Tier 3:           Approved secondary sources
                  (source type SECONDARY_PORTAL, reputable portals)

Tier 4:           AI interpretation of Tier 1–3 data
                  (Qwen reasoning over verified retrieved content)

Tier 5 (lowest):  Qwen pretrained/general knowledge
                  (never used for Pakistan-specific factual claims)
```

**Enforcement:**
- Student-facing endpoints retrieve only Tier 1–2 records with `verification_status IN ('VERIFIED', 'VALIDATED')`
- Tier 5 is used only for: general career advice, motivation reflection, conversational phrasing
- Any record created by AI output alone starts at `verification_status = 'CANDIDATE'` and requires human or system verification before reaching Tier 1–2
- The system prompt for every student-facing call includes: "You must never state a specific Pakistani university, organization, opportunity, deadline, salary, or URL unless it was provided in the context data. If the data was not provided, say so."

---

## 9. Pakistan Knowledge Base

The knowledge base is the normalized relational database. It covers:

### Education
- Universities, campuses, colleges
- Programs and departments
- Admission information and entry requirements
- Fees (where verified from official sources)
- Scholarships
- University sports programs

### Careers
- Career definitions, categories, fields
- Required skills and skill levels
- Demand, competition, and difficulty indicators
- Education requirements
- Pakistan-specific career opportunities
- Career risks and rewards
- Resources

### Opportunities (unified layer)
- Internships, jobs, scholarships, fellowships, competitions, training programs, apprenticeships, sports opportunities
- Source, URL, deadline, eligibility, location, verification status, freshness

### Sports
- Sports types
- Tournaments, trials, scholarships, university sports programs
- Eligibility requirements

### Alumni
- Verified/public career path information
- University, field, role, company, advice

### Learning Resources
- Courses, tutorials, videos, projects
- Skill, level, provider, URL, cost, duration, language

---

## 10. Complete Database Schema

All tables use SQLite with SQLAlchemy ORM. Integer primary keys autoincrement. Timestamps in UTC. JSON fields stored as TEXT containing valid JSON arrays or objects.

---

### `students`

Purpose: Core student identity record.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| name | TEXT | NOT NULL |
| email | TEXT | UNIQUE NOT NULL |
| password_hash | TEXT | NOT NULL |
| city | TEXT | |
| education_stage | TEXT | NOT NULL DEFAULT 'HIGH_SCHOOL' CHECK IN valid_stages |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Indexes: `email` (unique), `education_stage`

---

### `student_profiles`

Purpose: Evolving student context — updated continuously.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| student_id | INTEGER | UNIQUE NOT NULL FK students.id |
| interests | TEXT | JSON array of strings |
| skills | TEXT | JSON array of {name, level} |
| motivation_tags | TEXT | JSON array of strings |
| career_interests | TEXT | JSON array of strings |
| career_goal_id | INTEGER | FK careers.id NULLABLE |
| sports_interests | TEXT | JSON array of strings |
| sports_goal | TEXT | |
| next_best_action | TEXT | JSON blob — last validated NBA |
| job_readiness_score | REAL | DEFAULT 0.0 |
| completed_milestone_ids | TEXT | JSON array of integers |
| last_updated | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Indexes: `student_id` (unique), `career_goal_id`

---

### `journey_states`

Purpose: One active journey state record per student. Controls stage machine.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| student_id | INTEGER | UNIQUE NOT NULL FK students.id |
| current_stage | TEXT | NOT NULL |
| career_pathway_active | BOOLEAN | DEFAULT TRUE |
| sports_pathway_active | BOOLEAN | DEFAULT FALSE |
| roadmap_id | INTEGER | FK roadmaps.id NULLABLE |
| last_transition_at | TIMESTAMP | |
| last_transition_reason | TEXT | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Indexes: `student_id` (unique)

---

### `roadmaps`

Purpose: Long-term internal roadmap for a student/career combination.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| student_id | INTEGER | NOT NULL FK students.id |
| career_id | INTEGER | FK careers.id NULLABLE |
| all_stages_json | TEXT | Full hidden roadmap as JSON |
| current_stage | TEXT | NOT NULL |
| current_step_title | TEXT | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Indexes: `student_id`, `career_id`

---

### `milestones`

Purpose: Individual milestones within a roadmap.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| roadmap_id | INTEGER | NOT NULL FK roadmaps.id |
| title | TEXT | NOT NULL |
| description | TEXT | |
| stage | TEXT | NOT NULL |
| status | TEXT | NOT NULL DEFAULT 'pending' CHECK IN (pending, active, done, skipped) |
| order_index | INTEGER | NOT NULL |
| milestone_type | TEXT | DEFAULT 'general' — skill/project/interview/cv/internship/general |
| completed_at | TIMESTAMP | |

Indexes: `roadmap_id`, `stage`, `status`, `milestone_type`

---

### `next_best_actions`

Purpose: Persisted NBA history for a student.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| student_id | INTEGER | NOT NULL FK students.id |
| candidate_ids | TEXT | JSON array of candidate action IDs provided to Qwen |
| selected_candidate_id | TEXT | The candidate ID Qwen selected (must be in candidate_ids) |
| title | TEXT | NOT NULL |
| description | TEXT | |
| steps | TEXT | JSON array of step strings (max 3) |
| estimated_time | TEXT | |
| why_this_matters | TEXT | |
| stage | TEXT | journey stage this NBA serves |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| completed_at | TIMESTAMP | |

Indexes: `student_id`, `is_active`

---

### `careers`

Purpose: Career knowledge base. Pakistan-relevant career definitions.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| slug | TEXT | UNIQUE NOT NULL |
| name | TEXT | NOT NULL |
| field | TEXT | NOT NULL — e.g. Technology, Medicine |
| category | TEXT | — e.g. Engineering, Business |
| demand_level | TEXT | HIGH / MEDIUM / LOW |
| competition_level | TEXT | HIGH / MEDIUM / LOW |
| difficulty_level | TEXT | HIGH / MEDIUM / LOW |
| education_requirements | TEXT | JSON array |
| pk_opportunities_summary | TEXT | brief text |
| risks | TEXT | JSON array |
| rewards | TEXT | JSON array |
| resources | TEXT | JSON array of {name, url} |
| is_active | BOOLEAN | DEFAULT TRUE |
| source_id | INTEGER | FK sources.id NULLABLE |
| last_updated | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Indexes: `slug` (unique), `field`, `category`, `demand_level`

---

### `skills`

Purpose: Normalized skill registry.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| name | TEXT | UNIQUE NOT NULL |
| slug | TEXT | UNIQUE NOT NULL |
| category | TEXT | — technical/soft/domain |
| description | TEXT | |

Indexes: `slug` (unique), `name`

---

### `career_skills`

Purpose: Many-to-many: careers ↔ skills with level requirements.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| career_id | INTEGER | NOT NULL FK careers.id |
| skill_id | INTEGER | NOT NULL FK skills.id |
| required_level | TEXT | beginner / intermediate / advanced |
| is_essential | BOOLEAN | DEFAULT TRUE |
| stage | TEXT | which journey stage this skill becomes relevant |

Indexes: `career_id`, `skill_id`, UNIQUE(`career_id`, `skill_id`)

---

### `universities`

Purpose: Pakistani university records.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| name | TEXT | NOT NULL |
| short_name | TEXT | |
| slug | TEXT | UNIQUE NOT NULL |
| city | TEXT | |
| province | TEXT | |
| type | TEXT | PUBLIC / PRIVATE |
| hec_recognized | BOOLEAN | DEFAULT NULL — NULL means unknown |
| hec_category | TEXT | W1/W2/W3/X — NULL if unknown |
| website_url | TEXT | |
| admissions_url | TEXT | |
| source_id | INTEGER | FK sources.id |
| verification_status | TEXT | DEFAULT 'CANDIDATE' |
| last_verified | TIMESTAMP | |

Indexes: `slug` (unique), `city`, `type`, `hec_recognized`

---

### `campuses`

Purpose: University campuses (parent university may have multiple).

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| university_id | INTEGER | NOT NULL FK universities.id |
| name | TEXT | NOT NULL |
| city | TEXT | |
| is_main | BOOLEAN | DEFAULT FALSE |

Indexes: `university_id`, `city`

---

### `programs`

Purpose: Academic programs offered by universities.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| university_id | INTEGER | NOT NULL FK universities.id |
| campus_id | INTEGER | FK campuses.id NULLABLE |
| name | TEXT | NOT NULL |
| degree_type | TEXT | BS/BE/BBA/MS/MBA/PhD/Associate/Diploma |
| field | TEXT | |
| duration_years | REAL | |
| annual_fee_pkr | INTEGER | NULLABLE — verified only |
| admission_link | TEXT | |
| career_ids | TEXT | JSON array of career IDs this program leads to |
| source_id | INTEGER | FK sources.id |
| verification_status | TEXT | DEFAULT 'CANDIDATE' |
| last_verified | TIMESTAMP | |

Indexes: `university_id`, `field`, `degree_type`

---

### `opportunities`

Purpose: Unified opportunity layer covering internships, jobs, scholarships, fellowships, competitions, training, sports, and other.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| type | TEXT | NOT NULL — internship/job/scholarship/fellowship/competition/training/sports/other |
| title | TEXT | NOT NULL |
| organization | TEXT | |
| organization_type | TEXT | company/university/government/ngo/other |
| field | TEXT | |
| location | TEXT | |
| city | TEXT | |
| province | TEXT | |
| is_remote | BOOLEAN | DEFAULT FALSE |
| description | TEXT | |
| required_skills | TEXT | JSON array of skill slugs |
| required_education_stage | TEXT | journey stage minimum |
| required_degree_type | TEXT | |
| required_cgpa | REAL | NULLABLE |
| eligibility_notes | TEXT | |
| stipend_pkr | INTEGER | NULLABLE — verified only |
| deadline | DATE | NULLABLE |
| application_url | TEXT | |
| status | TEXT | DEFAULT 'ACTIVE' — ACTIVE/EXPIRING_SOON/EXPIRED/UNVERIFIED/STALE |
| source_id | INTEGER | FK sources.id NOT NULL |
| verification_status | TEXT | DEFAULT 'CANDIDATE' |
| retrieved_at | TIMESTAMP | |
| last_verified | TIMESTAMP | |
| content_hash | TEXT | for deduplication |
| dedup_key | TEXT | normalized dedup string |
| is_active | BOOLEAN | DEFAULT TRUE |

Indexes: `type`, `field`, `city`, `status`, `deadline`, `verification_status`, `dedup_key`, `is_active`

---

### `opportunity_details`

Purpose: Type-specific extended fields without polluting the main `opportunities` table.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| opportunity_id | INTEGER | UNIQUE NOT NULL FK opportunities.id |
| sport | TEXT | NULLABLE — for sports type |
| tournament_level | TEXT | NULLABLE — local/provincial/national/international |
| trial_date | DATE | NULLABLE |
| duration_weeks | INTEGER | NULLABLE — for training/internship |
| positions_available | INTEGER | NULLABLE |
| extension_fields | TEXT | JSON blob for any additional type-specific data |

Indexes: `opportunity_id` (unique), `sport`

---

### `sports`

Purpose: Sport reference data.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| name | TEXT | UNIQUE NOT NULL |
| slug | TEXT | UNIQUE NOT NULL |
| category | TEXT | team/individual |
| governing_body_pk | TEXT | |
| governing_body_url | TEXT | |

Indexes: `slug` (unique)

---

### `alumni`

Purpose: Verified/public alumni career path data.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| name | TEXT | NOT NULL |
| university_id | INTEGER | FK universities.id NULLABLE |
| university_name | TEXT | — stored directly if university not in DB |
| field | TEXT | |
| career_id | INTEGER | FK careers.id NULLABLE |
| current_role | TEXT | |
| current_company | TEXT | |
| career_path_summary | TEXT | |
| key_advice | TEXT | |
| tags | TEXT | JSON array of tags |
| is_verified | BOOLEAN | DEFAULT FALSE |
| source_id | INTEGER | FK sources.id |
| source_url | TEXT | — LinkedIn profile or public article where applicable |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Indexes: `field`, `career_id`, `university_id`, `is_verified`

---

### `learning_resources`

Purpose: Verified learning resources for skill building.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| skill_id | INTEGER | FK skills.id NULLABLE |
| skill_name | TEXT | — if not normalized to skills table |
| title | TEXT | NOT NULL |
| type | TEXT | course/tutorial/video/project/book/other |
| provider | TEXT | |
| url | TEXT | NOT NULL |
| language | TEXT | DEFAULT 'English' |
| level | TEXT | beginner/intermediate/advanced |
| is_free | BOOLEAN | NULLABLE — verified only |
| duration_hours | REAL | NULLABLE — verified only |
| source_id | INTEGER | FK sources.id |
| verification_status | TEXT | DEFAULT 'CANDIDATE' |
| last_verified | TIMESTAMP | |
| is_active | BOOLEAN | DEFAULT TRUE |

Indexes: `skill_id`, `type`, `level`, `is_free`

---

### `sources`

Purpose: Provenance registry for every externally sourced record.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| source_url | TEXT | UNIQUE NOT NULL |
| source_name | TEXT | |
| source_type | TEXT | NOT NULL — see §11 |
| domain | TEXT | |
| classification | TEXT | OFFICIAL / SECONDARY / SOCIAL / UNKNOWN |
| retrieval_method | TEXT | direct_fetch/web_search/api/manual |
| retrieved_at | TIMESTAMP | |
| last_verified | TIMESTAMP | |
| content_hash | TEXT | SHA256 of last retrieved content |
| verification_status | TEXT | DEFAULT 'DISCOVERED' — see §11 |
| confidence | REAL | 0.0–1.0 DEFAULT NULL |
| notes | TEXT | |

Indexes: `source_url` (unique), `domain`, `source_type`, `verification_status`

---

### `source_documents`

Purpose: Raw extracted content from sources, kept separate from normalized records.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| source_id | INTEGER | NOT NULL FK sources.id |
| raw_content | TEXT | original retrieved text/HTML excerpt |
| extracted_json | TEXT | Qwen's extraction output (NOT yet treated as truth) |
| extraction_model | TEXT | model name used |
| extraction_at | TIMESTAMP | |
| content_hash | TEXT | SHA256 of raw_content |
| processing_status | TEXT | PENDING/EXTRACTED/VALIDATED/FAILED |

Indexes: `source_id`, `processing_status`

---

### `ingestion_runs`

Purpose: Track each admin-initiated ingestion batch.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| trigger_type | TEXT | url_batch/search/refresh/manual |
| initiated_by | TEXT | admin identifier |
| started_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| completed_at | TIMESTAMP | |
| status | TEXT | RUNNING/COMPLETED/FAILED/PARTIAL |
| total_items | INTEGER | DEFAULT 0 |
| successful_items | INTEGER | DEFAULT 0 |
| failed_items | INTEGER | DEFAULT 0 |
| notes | TEXT | |

Indexes: `status`, `started_at`

---

### `ingestion_items`

Purpose: Individual items within an ingestion run.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| run_id | INTEGER | NOT NULL FK ingestion_runs.id |
| source_url | TEXT | NOT NULL |
| status | TEXT | PENDING/RETRIEVED/EXTRACTED/VALIDATED/STORED/FAILED/DUPLICATE |
| source_id | INTEGER | FK sources.id NULLABLE — set after source created |
| document_id | INTEGER | FK source_documents.id NULLABLE |
| opportunity_id | INTEGER | FK opportunities.id NULLABLE — set if record created |
| error_message | TEXT | |
| started_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |

Indexes: `run_id`, `status`

---

### `student_opportunity_matches`

Purpose: Cached deterministic match results per student per opportunity.

| Field | Type | Constraints |
|---|---|---|
| id | INTEGER | PK AUTOINCREMENT |
| student_id | INTEGER | NOT NULL FK students.id |
| opportunity_id | INTEGER | NOT NULL FK opportunities.id |
| match_score | REAL | NOT NULL — 0.0 to 1.0 — deterministic |
| component_scores | TEXT | JSON {skills, education, field, location, eligibility} |
| missing_requirements | TEXT | JSON array of strings |
| next_action | TEXT | |
| ai_explanation | TEXT | Qwen's explanation of the match (not the score) |
| matched_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Indexes: `student_id`, `opportunity_id`, UNIQUE(`student_id`, `opportunity_id`)

---

## 11. Source and Provenance Model

### Source types

```
OFFICIAL_GOVERNMENT       — HEC, Ministry of Education, Pakistan Sports Board
OFFICIAL_UNIVERSITY       — university.edu.pk or verified official domain
OFFICIAL_COMPANY          — company's own career page
OFFICIAL_SPORTS           — PSB, PCB, PFF, and recognized sports bodies
SECONDARY_PORTAL          — rozee.pk, indeed.pk, mustakbil.com, or similar
SOCIAL                    — LinkedIn, Instagram, Facebook public pages
UNKNOWN                   — not yet classified
```

### Verification status flow

```
DISCOVERED     — URL found but not yet retrieved
    ↓
EXTRACTED      — content retrieved and extracted by Qwen, not yet validated
    ↓
CANDIDATE      — extraction plausible, pending structural validation
    ↓
VALIDATED      — passed structural/schema validation, not yet officially confirmed
    ↓
VERIFIED       — confirmed against official source or manually approved
    ↓
STALE          — last_verified > 30 days, needs refresh
    ↓
EXPIRED        — deadline passed or record explicitly marked expired
    ↓
REJECTED       — failed validation, spam, or identified as unreliable
    ↓
UNAVAILABLE    — source URL no longer accessible
```

**Rule:** A model-generated record is NEVER automatically VERIFIED. It starts as CANDIDATE.

**Rule:** Student-facing opportunity queries filter to `verification_status IN ('VALIDATED', 'VERIFIED')` only. CANDIDATE records are not shown to students.

### Deduplication key

For opportunities, compute a normalized dedup key:

```python
dedup_key = normalize(organization) + "|" + normalize(title) + "|" + normalize(city) + "|" + str(deadline or "")
```

Where `normalize()` lowercases, strips whitespace, and removes punctuation.

When a duplicate is detected: associate the new source with the existing opportunity record rather than creating a duplicate. Do not silently discard the source.

---

## 12. Web Ingestion Architecture

### Access control

**Admin/developer only.** No student-facing endpoint may trigger ingestion. Ingestion endpoints are prefixed `/api/v1/admin/ingest/` and require admin authentication (separate from student JWT).

### Pipeline stages

```
1. DISCOVER
   Admin submits: URL list OR search query
   System creates ingestion_run + ingestion_items

2. RETRIEVE
   For each URL:
   - Fetch raw content (HTTP GET with User-Agent)
   - Compute content_hash
   - If content_hash unchanged since last run: skip extraction, mark UNCHANGED
   - Create/update source record
   - Store raw content in source_documents.raw_content

3. EXTRACT
   Pass raw content to Qwen with extraction prompt:
   - Qwen is told: extract only what is explicitly stated in the text
   - Qwen returns: structured JSON matching the extraction schema
   - Missing values → null (never inferred)
   - Store in source_documents.extracted_json
   - Mark status EXTRACTED

4. VALIDATE
   Structural validation with Pydantic extraction schema:
   - Required fields present?
   - Field types correct?
   - Deadline is a real date?
   - URL is a real URL?
   - If valid: mark CANDIDATE
   - If invalid: mark FAILED, log reason

5. NORMALIZE
   Map extracted fields to normalized DB structure:
   - skill names → skills table lookup/create
   - university names → universities table lookup (fuzzy match)
   - career names → careers table lookup
   - location → city/province normalization

6. DEDUPLICATE
   Compute dedup_key
   Check against existing opportunities
   If match found: associate source, update existing record, do not create duplicate
   If no match: proceed to persist

7. PERSIST
   Create opportunity record with verification_status = 'CANDIDATE'
   Link source_id
   Create student_opportunity_matches are NOT generated here — matching runs on demand

8. INDEX
   SQLite FTS (full-text search) index updated

9. ADMIN VERIFICATION (manual step)
   Admin reviews CANDIDATE records
   Marks trusted ones as VALIDATED or VERIFIED
   Only VALIDATED/VERIFIED records are visible to students
```

### Supported ingestion modes

**A. URL batch:** Admin POSTs a list of 10–50 URLs. Each processed as above.

**B. Search-based discovery:** Admin POSTs a search query. Qwen's web_search tool runs. Resulting URLs extracted. Each processed as above. Source type = SECONDARY or SOCIAL initially.

**C. Approved source refresh:** Re-fetch previously ingested sources where `last_verified < now - 7 days`. Content hash compared. Re-extract only if changed.

**D. Manual entry:** Admin POSTs a structured record directly. Source type = OFFICIAL (manually verified). Verification status = VERIFIED immediately.

### Ingestion extraction schema

The extraction prompt tells Qwen:

```
Extract ONLY information explicitly present in the provided text.
Return null for any field not explicitly stated.
Do not infer deadlines, eligibilities, salaries, or URLs.
Return valid JSON matching this schema: [schema provided]
```

This is the ONLY place Qwen is used to generate factual record fields. And even here, the result is CANDIDATE, not VERIFIED.

---

## 13. Social-Source Policy

Social sources (LinkedIn, Instagram, Facebook, other public pages) are permitted under these constraints:

- **Only publicly accessible pages.** No login bypass, no CAPTCHA bypass, no private account scraping.
- **Only via official APIs where available** (LinkedIn API with proper credentials, Facebook Graph API for public pages).
- **For public web pages:** use HTTP GET on publicly accessible URLs only, with appropriate User-Agent.
- **Trust level:** SOCIAL sources start at `classification = 'SOCIAL'` and `verification_status = 'CANDIDATE'`. They require independent verification before reaching VALIDATED.
- **Rate limiting:** Respect platform rate limits. Do not hammer social platforms.
- **No PII harvesting.** Do not store personal contact information, private messages, or information from private accounts.

Social sources are useful for: discovering internship/job postings shared on LinkedIn company pages, sports tournament announcements on official federation pages, scholarship announcements on university social accounts.

---

## 14. Retrieval and Search Architecture

### Retrieval layer location

`BackEnd/retrieval/` — a dedicated Python module called by services before assembling AI context.

### Retrieval principle

Do NOT send the entire knowledge base to Qwen. Retrieve only relevant, verified records. Return a bounded context.

### Retrieval services

```
BackEnd/retrieval/
├── career_retrieval.py        get_career(slug), search_careers(query, field), 
│                              get_career_skills(career_id), get_career_programs(career_id)
├── opportunity_retrieval.py   search_opportunities(type, skills, city, field, stage),
│                              get_opportunity(id), get_fresh_opportunities(type, limit)
├── university_retrieval.py    search_universities(field, city, type),
│                              get_university(id), get_programs(university_id, field)
├── sports_retrieval.py        search_sports_opportunities(sport, city, type),
│                              get_sport(slug)
├── alumni_retrieval.py        find_alumni(field, career_id, university_id),
│                              get_alumni(id)
├── learning_retrieval.py      get_resources_for_skill(skill_id, level),
│                              search_resources(skill_name)
└── student_retrieval.py       get_student_context(student_id),
                               get_active_milestones(student_id, limit=3)
```

Each retrieval function:
- Accepts typed parameters
- Queries SQLite through SQLAlchemy
- Applies freshness filters (`status != 'EXPIRED'`, `is_active = TRUE`)
- Applies verification filters (`verification_status IN ('VALIDATED', 'VERIFIED')`) for student-facing queries
- Returns a bounded result set (max defined per function)
- Returns a dataclass or typed dict — never raw SQLAlchemy rows to business logic

### Full-text search

Use SQLite FTS5 virtual tables for full-text search on:
- `careers.name`, `careers.field`, `careers.category`
- `opportunities.title`, `opportunities.organization`, `opportunities.description`
- `universities.name`
- `programs.name`
- `alumni.career_path_summary`
- `learning_resources.title`, `learning_resources.provider`

Create FTS tables as SQLite virtual tables:
```sql
CREATE VIRTUAL TABLE careers_fts USING fts5(name, field, category, content='careers', content_rowid='id');
```

Trigger-based synchronization: on INSERT/UPDATE/DELETE to the main table, update the FTS table.

### Context assembly — token budgets

Per AI call type, the retrieval layer enforces a maximum number of records before the context is sent to Qwen:

| Call type | Max records injected |
|---|---|
| Career Reality Check | 1 career + 10 opportunities + 5 skills |
| Next Best Action | student profile + 5 milestones + 3 opportunities + 1 career |
| Opportunity Matching | 10 opportunities per batch |
| Coach Chat | student profile + 1 career + 3 opportunities + 5 history messages |
| Job Readiness | student profile + milestone summary only |
| Career Trial Plan | 1 career + 5 skills |

---

## 15. Caching

### What to cache

- Career data (stable, seed-loaded): Python-level in-memory dict after first DB load. Invalidated on admin update.
- Skill data (very stable): same.
- Frequently requested career searches: SQLite query result cached in a simple TTL dict for 5 minutes.
- Student's last NBA: stored in `student_profiles.next_best_action` — served from DB without regenerating unless a trigger event occurs.
- Source documents content hash: prevents re-extraction if content unchanged.

### What NOT to cache

- Opportunity deadlines — always re-query for freshness
- Student profile — always read fresh from DB for AI calls
- Ingestion extraction results — never cache as truth

### Implementation

For MVP, use a simple Python `dict` with TTL for in-memory caching. No Redis required for local development. Design the cache interface so Redis can be substituted later without changing call sites:

```python
# BackEnd/cache.py
class SimpleCache:
    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any, ttl_seconds: int): ...
    def delete(self, key: str): ...
```

---

## 16. MCP Architecture

### Purpose

MCP servers expose retrieval tools to Qwen via SSE (Pattern B). They enable Qwen to dynamically select which data to retrieve during tool-calling interactions — primarily for opportunity and sports matching where the right query is determined by the student's context.

### When to use MCP vs direct retrieval

| Situation | Use MCP (Pattern B) |
|---|---|
| Qwen must choose which filter to apply | Yes |
| Fixed query known before the AI call | No — pre-fetch, inject into prompt |
| Conversational mention of a sports event Qwen wants to look up | Yes |
| Standard career detail lookup | No — retrieval layer, Pattern A |

### MCP servers

**Server 1: Pakistan Career & Education** (`/mcp/career/sse`)

Tools:
- `get_career(slug: str)` — full career detail
- `get_career_reality(slug: str)` — demand, competition, difficulty, skills, risks, rewards
- `get_required_skills(career_slug: str, stage: str)` — skills needed at a given stage
- `get_university_opportunities(field: str, city: str = None)` — programs and universities
- `get_scholarships(criteria: dict)` — scholarship opportunities matching criteria

**Server 2: Pakistan Opportunities & Sports** (`/mcp/opportunity/sse`)

Tools:
- `search_internships(skills: list, city: str = None, field: str = None)` — internship search
- `search_jobs(skills: list, city: str = None, experience_level: str = None)` — job search
- `match_opportunity(student_skills: list, opportunity_id: int)` — match score + gaps
- `search_sports_opportunities(sport: str, city: str = None, type: str = None)` — sports search
- `search_sports_scholarships(sport: str, level: str = None)` — sports scholarships
- `search_university_sports(sport: str, city: str = None)` — university sports programs
- `find_alumni(field: str, career_id: int = None, university_id: int = None)` — alumni search
- `get_learning_resources(skill: str, level: str = None)` — learning resource search

### MCP implementation rules

- All tools read from normalized verified DB only. No live web calls inside MCP tools.
- All tools apply `verification_status IN ('VALIDATED', 'VERIFIED')` filter.
- All tools apply freshness filter (`status != 'EXPIRED'`, `is_active = TRUE`).
- Tools return structured dicts, not raw SQLAlchemy objects.
- When a tool returns no results: return `[]` with a `note: "No matching records found."` — never raise an exception.
- Tools reuse the retrieval layer functions — no duplicate query logic.

### MCP server setup

Use `fastmcp` (Python). Mount as SSE endpoints inside the FastAPI application. This avoids a separate process:

```python
# Mcp/career_server.py
from mcp.server.fastmcp import FastMCP
from BackEnd.retrieval import career_retrieval, university_retrieval

mcp = FastMCP(name="PakistanCareer")

@mcp.tool()
def get_career(slug: str) -> dict:
    """Returns full career detail for a Pakistani career by slug."""
    return career_retrieval.get_career(slug)
```

Mount in `BackEnd/main.py`:
```python
from Mcp.career_server import mcp as career_mcp
app.mount("/mcp/career", career_mcp.sse_app())
```

---

## 17. API Contract

### Authentication

All student-facing endpoints (except `/auth/*` and `/api/v1/health`) require `Authorization: Bearer <token>` JWT header. JWT payload contains `student_id`. All DB queries filter by `student_id` extracted from JWT — never from request body.

Admin endpoints (`/api/v1/admin/*`) require a separate admin token. Define `ADMIN_TOKEN` in `.env`. For MVP, a fixed token is sufficient. Do not expose admin endpoints in the Swagger docs by default.

### Response envelope

All responses are typed Pydantic models. Errors use FastAPI's standard `HTTPException` mechanism, resulting in `{"detail": "..."}`. No raw tracebacks. No secret values in any error response.

### Endpoint definitions

---

**`GET /api/v1/health`** — public
- Response: `{"status": "ok", "db": "ok", "timestamp": "..."}`
- No auth required
- Failure: `{"status": "degraded", "detail": "..."}`

---

**`POST /api/v1/auth/register`**
- Request: `{name, email, password, city?}`
- Response: `{student_id, token, education_stage}`
- DB: INSERT students, INSERT student_profiles, INSERT journey_states
- Validation: email unique, password >= 8 chars
- Failure: 409 if email exists, 422 on validation error

**`POST /api/v1/auth/login`**
- Request: `{email, password}`
- Response: `{token, student_id, education_stage, name}`
- DB: SELECT + bcrypt verify
- Failure: 401 on wrong credentials

---

**`POST /api/v1/onboarding`**
- Request: `{education_stage, interests[], career_interests[], sports_interests[], motivation_tags[], skills[{name,level}], city?}`
- Response: `{profile_updated: true, next_best_action: NextBestAction}`
- DB: UPDATE student_profiles, UPDATE journey_states
- AI: assemble context → retrieval → Qwen Pattern A → validate NextBestAction → persist NBA
- Validation: education_stage must be valid enum
- Failure: 422 on validation, 503 if Qwen fails (return deterministic fallback NBA)

---

**`GET /api/v1/careers`**
- Query: `?field=&search=&limit=20&offset=0`
- Response: `{careers: [CareerSummary], total: int}`
- DB: FTS search or filtered query, no AI
- Returns only `is_active = TRUE` records

**`GET /api/v1/careers/{slug}`**
- Response: `CareerDetail` including skills, opportunities summary, program count
- DB: career + career_skills + programs count, no AI

**`POST /api/v1/career/analyze`**
- Request: `{career_slug}`
- Response: `{reality: CareerReality, verdict: CareerVerdict}`
- DB: career + skills + opportunities count + student profile
- AI: Retrieval → assemble context → Qwen Pattern A → validate CareerReality + CareerVerdict
- Failure: 404 if career not found, 503 if Qwen fails with partial deterministic response

**`POST /api/v1/career/trial-plan`**
- Request: `{career_slug}`
- Response: `CareerTrialPlan`
- DB: career + skills (for the career) + student profile
- AI: Qwen Pattern A → validate CareerTrialPlan

---

**`GET /api/v1/journey`**
- Response: `{stage, current_step, visible_next_steps: [max 3], next_best_action, career_goal?}`
- DB: journey_states + roadmap + milestones (active ones only, max 3) + student_profiles.next_best_action
- No AI

**`POST /api/v1/roadmap`**
- Request: `{career_slug}`
- Response: `{roadmap_id, current_step, visible_steps: [max 3]}`
- DB: create/replace roadmap + milestones
- AI: Qwen Pattern A generates roadmap JSON → validate Roadmap schema → persist

**`POST /api/v1/progress`**
- Request: `{milestone_id, status: "done"|"skipped"}`
- Response: `{new_stage?, next_best_action: NextBestAction}`
- DB: UPDATE milestone → check transition eligibility → maybe advance journey_state → persist NBA
- AI: retrieval → candidate generation → Qwen selects NBA → validate → persist
- Failure: 404 if milestone not found or not owned by student

---

**`GET /api/v1/opportunities`**
- Query: `?type=&city=&field=&skills=&limit=20&offset=0`
- Response: `{opportunities: [OpportunitySummary], total: int}`
- DB: filtered query with freshness + verification filters, no AI
- Returns: type, title, organization, deadline, location, match_score if cached for this student

**`POST /api/v1/opportunities/match`**
- Request: `{opportunity_ids?: [], limit?: 10}`
- Response: `{matches: [OpportunityMatch]}`
- DB: retrieve opportunities, retrieve student profile
- Logic: deterministic match score per opportunity
- AI (Pattern B via MCP): Qwen uses MCP tools to find relevant opps if no ids supplied, then produces explanation
- Returns: sorted by match_score desc

---

**`GET /api/v1/sports`**
- Query: `?sport=&city=&type=&limit=20`
- Response: `{opportunities: [SportsOpportunitySummary]}`
- DB: filtered query via opportunity_retrieval with type IN ('sports'), no AI

**`POST /api/v1/sports/match`**
- Request: `{sport?, location?}`
- Response: `{matches: [SportsOpportunityMatch]}`
- DB + AI (MCP Pattern B): same pipeline as opportunities/match, filtered to sports type

---

**`GET /api/v1/universities`**
- Query: `?field=&city=&type=&hec_recognized=&limit=20`
- Response: `{universities: [UniversitySummary], total: int}`
- DB: filtered query, no AI
- Returns only VALIDATED/VERIFIED universities

**`GET /api/v1/universities/{id}/programs`**
- Query: `?field=&degree_type=`
- Response: `{programs: [ProgramSummary]}`
- DB: programs for university filtered by field/degree_type

---

**`GET /api/v1/alumni`**
- Query: `?field=&career_id=&university_id=&limit=10`
- Response: `{alumni: [AlumniCard]}`
- DB: filtered query, is_verified = TRUE preferred, no AI

**`GET /api/v1/alumni/{id}`**
- Response: `AlumniDetail`
- DB: single alumni record

---

**`GET /api/v1/learning`**
- Query: `?skill=&level=&type=&is_free=`
- Response: `{resources: [LearningResource]}`
- DB: filtered query, no AI

---

**`POST /api/v1/coach/chat`**
- Request: `{message, conversation_history: [{role, content}]}`
- Validation: message non-empty, history trimmed to last 5 messages
- Response: `CoachResponse`
- Rate limit: 20 requests/hour/student (in-memory limiter)
- DB: retrieve student context (profile + journey + active milestones + career + relevant opps)
- AI: Pattern A → validate CoachResponse
- Constraint: quick_actions max 3 (enforced by service, not just AI)
- Constraint: suggested_resource null unless from DB context
- Failure: 429 on rate limit, 503 if Qwen fails

**`POST /api/v1/job-readiness`**
- Request: `{}` (uses student from JWT)
- Response: `JobReadiness`
- DB: student profile + milestones
- Logic: deterministic 5-component score (Skills 30%, Projects 20%, Internship 20%, CV 15%, Interview 15%) — Qwen does NOT alter scores
- AI: Pattern A for gap_explanation + recommendations only
- Response always includes `disclaimer` field (hardcoded text)
- Failure: return deterministic scores + fallback text if Qwen fails

---

### Admin ingestion endpoints

**`POST /api/v1/admin/ingest/url`**
- Admin auth required
- Request: `{urls: [str], source_type: str, run_label?: str}`
- Validation: max 50 URLs per request
- Response: `{run_id, queued_count}`
- Behavior: create ingestion_run + items, begin async processing (background task)

**`POST /api/v1/admin/ingest/search`**
- Admin auth required
- Request: `{query: str, limit?: int}`
- Behavior: use Qwen web_search to discover URLs, then process as URL batch

**`GET /api/v1/admin/ingest/runs/{id}`**
- Admin auth required
- Response: `IngestionRunStatus` with per-item statuses

**`POST /api/v1/admin/ingest/refresh`**
- Admin auth required
- Request: `{source_type?: str, max_items?: int}`
- Behavior: re-fetch sources with `last_verified < now - 7 days`

**`GET /api/v1/admin/data-quality`**
- Admin auth required
- Response: `{total_sources, verified_sources, candidate_records, stale_records, expired_opportunities, recent_run_summary}`

---

## 18. AI and Pydantic Schemas

All schemas defined in `BackEnd/schemas/responses.py`. Use these exact field names — frontend depends on them.

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date

class NextBestAction(BaseModel):
    candidate_id: str              # must match one of the provided candidate IDs
    title: str
    description: str               # 2–3 sentences max
    steps: list[str] = Field(max_length=3)  # max 3 concrete steps
    estimated_time: str            # e.g. "3–4 hours this week"
    why_this_matters: str          # 1 sentence
    stage: str                     # which journey stage this serves

class MotivationAnalysis(BaseModel):
    primary_motivation: str
    reflection_note: str           # honest, non-judgmental 2–3 sentences
    recommendation: str            # brief directional suggestion

class CareerSummary(BaseModel):
    id: int
    slug: str
    name: str
    field: str
    demand_level: Literal["HIGH", "MEDIUM", "LOW"]
    competition_level: Literal["HIGH", "MEDIUM", "LOW"]

class CareerReality(BaseModel):
    career_name: str
    demand_level: Literal["HIGH", "MEDIUM", "LOW"]
    competition_level: Literal["HIGH", "MEDIUM", "LOW"]
    difficulty_level: Literal["HIGH", "MEDIUM", "LOW"]
    required_skills: list[str]
    pk_opportunities_summary: str  # text — from DB field only
    risks: list[str]
    rewards: list[str]
    data_source: str               # e.g. "A&H Careers knowledge base, updated 2025"

class CareerVerdict(BaseModel):
    verdict: Literal["GOOD_FIT", "WORTH_EXPLORING", "RECONSIDER"]
    headline: str
    reasoning: str                 # 3–4 sentences
    student_strengths_match: list[str]
    gaps_to_address: list[str]
    suggested_trial: Optional[str] = None

class CareerTrialPlan(BaseModel):
    career_slug: str
    duration_days: int = 7
    days: list[dict]               # [{day_range: "1-2", title: str, tasks: [str]}]
    reflection_prompt: str

class Roadmap(BaseModel):
    student_id: int
    career_slug: str
    stages: list[dict]             # [{stage, title, milestones: [str], estimated_duration}]
    current_stage: str
    visible_next_steps: list[str] = Field(max_length=3)

class OpportunityMatch(BaseModel):
    opportunity_id: int
    title: str
    organization: str
    type: str
    match_score: float             # 0.0–1.0, deterministic
    match_reasons: list[str]       # from DB data only
    missing_requirements: list[str]
    next_action: str
    deadline: Optional[date] = None
    source_url: Optional[str] = None
    verification_status: str
    data_freshness: str            # FRESH / UNVERIFIED / STALE

class SportsOpportunityMatch(BaseModel):
    opportunity_id: int
    sport: str
    title: str
    organization: str
    match_score: float
    eligibility_met: list[str]
    eligibility_missing: list[str]
    next_action: str
    deadline: Optional[date] = None
    source_url: Optional[str] = None

class JobReadinessAIAnalysis(BaseModel):
    gap_explanation: str           # 2–3 sentences on the biggest gap
    next_best_action: NextBestAction
    recommendations: list[str] = Field(max_length=3)

class JobReadiness(BaseModel):
    overall_score: float           # 0.0–1.0, ALWAYS deterministic
    score_label: str               # "74%"
    component_scores: dict[str, float]  # skills/projects/internship/cv/interview
    biggest_gap: str               # component name, deterministic
    gap_explanation: str           # from Qwen or fallback
    next_best_action: NextBestAction
    recommendations: list[str]
    disclaimer: str                # ALWAYS hardcoded, never AI-generated

class CoachResponse(BaseModel):
    message: str
    quick_actions: list[str] = Field(max_length=3)
    suggested_resource: Optional[str] = None  # DB resource only, never invented

class AlumniCard(BaseModel):
    id: int
    name: str
    university_name: str
    field: str
    current_role: str
    current_company: str
    career_path_summary: str
    key_advice: str
    tags: list[str]

class IngestionRunStatus(BaseModel):
    run_id: int
    status: str
    total_items: int
    successful_items: int
    failed_items: int
    items: list[dict]
```

---

## 19. Next Best Action Architecture

This is the core differentiating feature. The pipeline is strictly controlled.

### Pipeline

```
1. CANDIDATE GENERATION (deterministic — no AI)
   The NBA service examines:
   - student's current journey stage
   - career goal
   - completed milestones
   - current roadmap step
   - available verified opportunities (from retrieval layer)
   - student skill gaps (career_skills vs student skills)
   
   Returns: 3–8 typed candidate objects, each with:
   {
     candidate_id: str,   # stable ID for validation
     title: str,
     description: str,
     steps: [str],
     estimated_time: str,
     why_this_matters: str,
     stage: str,
     source_type: str     # milestone/opportunity/skill/reflection
   }

2. CONTEXT ASSEMBLY
   - Student profile (bounded)
   - Retrieved career data (if career goal set)
   - 1–3 relevant opportunities (if applicable candidates)
   - The full candidate list as JSON

3. QWEN SELECTION (Pattern A)
   System prompt: "Select ONE candidate from the provided list.
   Return its candidate_id and personalize the title, description, steps,
   estimated_time, and why_this_matters for this student.
   You MUST return a candidate_id that exists in the provided list.
   Do not create a new action."

4. VALIDATION
   Pydantic validates NextBestAction schema.
   Service validates: returned candidate_id is in the original candidate list.
   If not: retry once with stricter prompt.
   If still invalid: take candidate[0] from the list, use it without AI personalization.

5. PERSISTENCE
   Store in next_best_actions table.
   Update student_profiles.next_best_action with the JSON blob.
   is_active = TRUE, previous NBA set is_active = FALSE.

6. RETURN
   Return NextBestAction to frontend.
```

### NBA trigger events

- Onboarding completed
- Milestone marked done
- Career selected/changed
- Journey stage advanced
- Student explicitly requests refresh via coach chat (if implemented)

### NBA is NOT regenerated on

- Every page view
- Every coach chat message
- Routine API calls

---

## 20. Career Reality Check

### Data sources (all from DB, no AI invention)

- `careers` table: demand_level, competition_level, difficulty_level, risks, rewards
- `career_skills` + `skills`: required skills and levels
- `programs` count per career (how many Pakistani universities offer it)
- `opportunities` count filtered by field (how many relevant opportunities in DB)
- Student profile: current skills, education_stage

### AI role

Qwen receives the structured data and produces:
- `CareerVerdict` (GOOD_FIT / WORTH_EXPLORING / RECONSIDER)
- `reasoning` paragraph
- `student_strengths_match` list
- `gaps_to_address` list

Qwen may NOT state specific salary figures, specific deadlines, specific company names, or specific URLs unless they were in the provided context.

### Fit calculation

A simple deterministic fit score is calculated before Qwen:
```
skill_overlap = (student skills matching career required skills) / total required skills
education_match = 1.0 if student stage >= minimum required stage, else 0.5
raw_fit = (skill_overlap * 0.6) + (education_match * 0.4)
```

This score is provided to Qwen but Qwen cannot alter it. Qwen uses it as a signal for its reasoning.

---

## 21. AI Mentor

### Context rules

The AI Mentor (coach/chat) receives:
- Student profile (education_stage, career_goal, skills list, motivation_tags)
- Journey state (current_stage, current_step)
- Active milestones (max 3)
- Last NBA (from student_profiles.next_best_action)
- Relevant career data (if career_goal set: demand_level, required_skills)
- Relevant opportunities (only if student has active opportunity matches)
- Last 5 conversation messages (trimmed from history in request)

### Hard constraints (enforced by service, not just prompt)

- quick_actions: trimmed to max 3 after Qwen response
- suggested_resource: set to None if Qwen returns a value that does not match a DB record URL
- Total input tokens for coach: service estimates and trims context if > 1800 tokens

### Response character

Concise. 2–4 short paragraphs. One recommended next step. No walls of text. No overwhelming lists. If the student asks about a Pakistani fact not in the context: "I don't have verified information about that right now. I'd recommend checking [general advice — e.g. the HEC website] directly."

---

## 22. Opportunities

### Unified layer

All opportunities share the `opportunities` table. Type field distinguishes them. Specialized fields live in `opportunity_details`. This avoids duplicating matching logic across separate internships/jobs/scholarships tables.

### Match score (deterministic)

```
skills_score     = overlap(student.skills, opportunity.required_skills)     * 0.35
education_score  = stage_compatible(student.stage, opp.required_education)  * 0.25
field_score      = field_match(student.career_goal, opp.field)              * 0.25
location_score   = city_match(student.city, opp.city, opp.is_remote)        * 0.15

match_score = sum of above, normalized to 0.0–1.0
```

### Freshness rules

- `deadline` in the past → status = EXPIRED, excluded from results
- `last_verified < now - 30 days` → status = STALE, flagged in response as `data_freshness: "STALE"`
- `verification_status NOT IN ('VALIDATED', 'VERIFIED')` → not shown to students

### Response

Each opportunity in the response includes:
- match_score
- match_reasons (from DB data only)
- missing_requirements
- next_action
- data_freshness indicator
- source_url (if available and OFFICIAL source)

---

## 23. Sports

Sports opportunities flow through the same `opportunities` table with `type = 'sports'`. Sport-specific fields (sport name, tournament_level, trial_date) live in `opportunity_details`.

The `sports` table is the sport reference registry. Sport slugs are used as consistent identifiers.

Matching follows the same deterministic pipeline as career opportunities. The sports pathway is activated on the student's journey_state (`sports_pathway_active = TRUE`) when the student expresses sports interest in onboarding or profile updates.

---

## 24. Alumni

Alumni data is stored in the `alumni` table. `is_verified = TRUE` records are preferred in retrieval. Records without verification are shown with a lower confidence indicator.

AI may summarize a career path from alumni data. AI may NOT invent an alumnus or fabricate a career path. If an alumnus record does not contain a specific field, return null/empty — do not let Qwen fill it in.

No social networking or messaging. Alumni are a discovery resource, not contacts.

---

## 25. Learning Resources

Resources are linked to skills via `skill_id` or `skill_name`. The retrieval layer finds resources matching a student's skill gap — skills required by their career goal that they do not yet have.

Resources are shown by the AI Mentor when the Next Best Action involves skill-building, and by the Journey view when a skill-building milestone is active.

`is_free`, `duration_hours`, and `url` are shown only when verified. `is_free = NULL` means "unknown" — do not assume free or paid.

---

## 26. Security

### Secret isolation

- `DASHSCOPE_API_KEY`, `DASHSCOPE_WORKSPACE_ID`, `SECRET_KEY`, `ADMIN_TOKEN` in `BackEnd/.env` only
- `BackEnd/.env` must be in `.gitignore`
- `git ls-files BackEnd/.env` must return nothing
- `NEXT_PUBLIC_*` variables are public — no secrets may ever go here
- Verify: `grep -r "DASHSCOPE" Frontend/.next/ 2>/dev/null` returns nothing

### Student data isolation

Every query returning student-specific data must filter by `student_id` from JWT. No endpoint may return another student's data. Tests must verify this.

### Input validation

All request bodies validated by Pydantic before any service call. SQLAlchemy ORM prevents SQL injection. No raw SQL string interpolation.

### Rate limiting

- Coach chat: 20 requests/hour/student — in-memory `InMemoryRateLimiter` (resets on restart)
- All other endpoints: no rate limiting in MVP
- Production note: replace with Redis-backed rate limiter

### CORS

`CORS_ORIGINS` env var (comma-separated). Parsed on startup. Never `*` in production.

### Log sanitisation

Before any string reaches logging: `re.sub(r'sk-[A-Za-z0-9]{20,}', '[REDACTED]', s)`

### Global exception handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"[{type(exc).__name__}] {sanitise_for_log(str(exc))}")
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})
```

### Admin endpoint isolation

Admin endpoints return 401 if `Authorization: Bearer` header does not match `ADMIN_TOKEN`. Admin endpoints are not included in public Swagger UI.

### Ingestion security

No student-facing request may write to `sources`, `source_documents`, `opportunities`, `ingestion_runs`, or `ingestion_items`. These tables are write-protected at the service layer — only `ingestion_service.py` and admin endpoints may write to them.

---

## 27. Error Handling

| Condition | Behavior |
|---|---|
| Qwen timeout | Retry once (2s delay). Second failure: return 503 with user message, log sanitised error |
| Qwen rate limit | Retry once after 5s. Still failing: 503 |
| Malformed JSON from Qwen | Retry with stricter prompt. Second failure: 503 or deterministic fallback depending on endpoint |
| Pydantic validation failure | Log raw response (sanitised). Retry. Second failure: fallback |
| NBA candidate_id not in list | Retry with stricter prompt. Second failure: use candidates[0] directly |
| MCP server unreachable | Fall back to direct retrieval layer call. Return `data_quality: "unranked"` |
| Empty opportunity result | Return `{opportunities: [], message: "No matching opportunities in our database right now."}` — never fabricate |
| Stale opportunity | Return with `data_freshness: "STALE"` flag — do not hide, do not fabricate fresh data |
| Expired deadline | Filter server-side, do not return to student |
| Invalid career slug | 404 `{"detail": "Career not found"}` |
| Invalid milestone (wrong student) | 404 |
| Missing env vars at startup | `RuntimeError` with list of missing vars — application does not start |
| Database unavailable | 503 `{"detail": "Service temporarily unavailable"}` — no DB error details in response |
| Admin endpoint, invalid token | 401 |

No response body may contain: API keys, JWT secrets, admin tokens, full database error messages, Python tracebacks.

---

## 28. Testing

### Test file structure

```
BackEnd/tests/
├── test_health.py
├── test_auth.py
├── test_careers.py
├── test_journey.py
├── test_nba.py
├── test_opportunities.py
├── test_sports.py
├── test_coach.py
├── test_job_readiness.py
├── test_alumni.py
├── test_learning.py
├── test_universities.py
├── test_ai_service.py
├── test_mcp.py
├── test_retrieval.py
├── test_ingestion.py
├── test_deduplication.py
├── test_freshness.py
├── test_security.py
└── conftest.py
```

### Test rules

- All standard tests mock external AI calls with `unittest.mock.patch("BackEnd.services.ai_service.call_structured")`
- Tests marked `@pytest.mark.integration` use real Qwen — run manually, not in automated suite
- No test deletes or weakens another test to get a green result
- All tests must pass before a phase is declared complete
- New tests are additive — never reduce the test count

### Required test categories

**Unit:** deterministic functions only — match score calculation, NBA candidate generation, job readiness score, freshness calculation, dedup key generation

**Integration:** service layer with mocked AI — onboarding, career analyze, NBA generation, opportunity matching, coach chat

**API tests:** every endpoint — happy path, validation errors, auth errors, 404 cases

**AI schema tests:** mock Qwen returning malformed JSON, missing fields, wrong types — verify fallback behavior

**Security tests:** cross-student data access returns 404, no secret in response body, CORS rejection

**Ingestion tests:** mock HTTP retrieval, extraction, dedup detection, persistence, status transitions

**Freshness tests:** expired opportunities filtered, stale flagged, STALE not hidden

**MCP tests:** each tool returns correct structure, empty results handled, no exception on not-found

---

## 29. Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Steps

```bash
# 1. Clone / open project
cd "A&H Career"

# 2. Backend environment
cd BackEnd
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 3. Create BackEnd/.env from example
cp .env.example .env
# Edit .env — fill in DASHSCOPE_API_KEY, DASHSCOPE_WORKSPACE_ID, SECRET_KEY, etc.

# 4. Initialize database and seed
python -c "from database import engine, Base; Base.metadata.create_all(bind=engine)"
python data/seed_db.py

# 5. Run backend
uvicorn main:app --reload --port 8000
# Verify: curl http://localhost:8000/api/v1/health → {"status":"ok"}
# Swagger: open http://localhost:8000/docs

# 6. Frontend environment
cd ../Frontend
cp .env.local.example .env.local
# Ensure NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
# Ensure NEXT_PUBLIC_USE_MOCK=false

npm install
npm run dev
# Open: http://localhost:3000

# 7. Run backend tests
cd ../BackEnd
pytest --tb=short -q
# Target: all tests passing

# 8. Verify Qwen connection (one-time)
python -c "
from services.ai_service import test_connection
test_connection()
"
```

---

## 30. Implementation Phases

Qoder implements in these phases, in order. Stop and report after each phase. Do not begin the next phase until the current phase's tests pass.

---

### Phase A — Repository Audit and Compatibility (Qoder Task A)

**Objective:** Understand the actual existing codebase before touching anything.

**Actions:**
1. Read the actual file structure
2. List all existing SQLAlchemy models and their fields
3. List all existing API endpoints
4. List all existing services
5. Identify what matches this architecture and what deviates
6. Produce a deviation report (not a rewrite — just a report)
7. Confirm which tests are currently passing

**Output:** A `Docs/phase-a-audit.md` file listing: existing tables, existing endpoints, deviations from this architecture, estimated work remaining.

**Do not write any application code in this phase.**

---

### Phase B — Data Model and Retrieval Layer (Qoder Task B)

**Objective:** Implement the normalized database schema and retrieval layer. This is the foundation everything else depends on.

**Files to create/modify:**
- `BackEnd/models/` — all models from §10
- `BackEnd/retrieval/` — all retrieval functions from §14
- `BackEnd/data/seed_db.py` — ensure `seed_if_empty()` exists
- `BackEnd/database.py` — FTS5 table creation if not present
- Migration: if existing tables differ, write an Alembic migration script

**Definition of done:** `pytest BackEnd/tests/test_retrieval.py` passes. All 9+ models importable. `seed_if_empty()` runs without error on empty DB.

---

### Phase C — Career Intelligence (Qoder Task C)

**Objective:** Career browse, detail, Reality Check, and Trial Plan working end-to-end.

**Files:**
- `BackEnd/routers/careers.py`
- `BackEnd/services/career_service.py`
- `BackEnd/prompts/career_analysis.py`
- `BackEnd/tests/test_careers.py`

**Definition of done:** All career endpoints return correct response shapes. `POST /career/analyze` returns validated `CareerReality + CareerVerdict`. `POST /career/trial-plan` returns `CareerTrialPlan`. Tests pass.

---

### Phase D — Student Journey (Qoder Task D)

**Objective:** Onboarding, journey view, roadmap, milestone progress, and stage transitions working.

**Files:**
- `BackEnd/routers/onboarding.py`, `journey.py`
- `BackEnd/services/roadmap_service.py`, `journey_service.py`
- `BackEnd/tests/test_journey.py`

**Definition of done:** A student can register, complete onboarding, view journey, create roadmap, mark milestones, and advance stage. All transitions are deterministic. Tests pass.

---

### Phase E — Next Best Action (Qoder Task E)

**Objective:** Full NBA pipeline — candidate generation, Qwen selection, validation, persistence.

**Files:**
- `BackEnd/services/nba_service.py`
- `BackEnd/prompts/next_best_action.py`
- `BackEnd/tests/test_nba.py`

**Definition of done:** NBA is generated after onboarding and after milestone completion. Returned `candidate_id` is always in the candidate list. Fallback to `candidates[0]` on Qwen failure. Tests pass.

---

### Phase F — AI Mentor / Coach Chat (Qoder Task F)

**Objective:** Coach chat endpoint working with bounded context, rate limiting, grounding rules.

**Files:**
- `BackEnd/routers/coach.py`
- `BackEnd/services/coach_service.py`
- `BackEnd/services/rate_limiter.py`
- `BackEnd/prompts/coach.py`
- `BackEnd/tests/test_coach.py`

**Definition of done:** `POST /coach/chat` returns 200. quick_actions max 3 enforced. Rate limit enforced. 503 on Qwen failure. Tests pass.

---

### Phase G — MCP (Qoder Task G)

**Objective:** Both MCP servers running as SSE, all tools functioning, Qwen Pattern B verified.

**Files:**
- `Mcp/career_server.py`
- `Mcp/opportunity_server.py`
- `BackEnd/main.py` — mount MCP servers
- `BackEnd/tests/test_mcp.py`

**Definition of done:** `/mcp/career/sse` and `/mcp/opportunity/sse` respond. All tools return correct structures. Empty results handled. Qwen Pattern B call in `POST /opportunities/match` verified by log inspection. Tests pass.

---

### Phase H — Web Ingestion (Qoder Task H)

**Objective:** Admin ingestion pipeline with provenance, deduplication, and status tracking.

**Files:**
- `BackEnd/ingestion/ingestion_service.py`
- `BackEnd/ingestion/extraction_service.py`
- `BackEnd/ingestion/dedup_service.py`
- `BackEnd/routers/admin.py`
- `BackEnd/prompts/extraction.py`
- `BackEnd/tests/test_ingestion.py`
- `BackEnd/tests/test_deduplication.py`

**Definition of done:** Admin can POST a URL list. Pipeline retrieves, extracts (Qwen), validates, deduplicates, and persists CANDIDATE records. Content hash prevents re-extraction of unchanged content. Tests pass (with mocked HTTP and Qwen calls).

---

### Phase I — Opportunities, Sports, Alumni, Learning Expansion (Qoder Task I)

**Objective:** All remaining student-facing features working end-to-end.

**Includes:**
- `POST /opportunities/match` — deterministic scoring + AI explanation
- `GET /sports`, `POST /sports/match`
- `GET /universities`, `GET /universities/{id}/programs`
- `GET /alumni`, `GET /alumni/{id}`
- `GET /learning`
- `POST /job-readiness` (deterministic scoring + Qwen gap analysis)
- `GET /api/v1/admin/data-quality`

**Tests:** test_opportunities.py, test_sports.py, test_alumni.py, test_learning.py, test_universities.py, test_job_readiness.py

**Definition of done:** All endpoints return correct shapes. Match scores are deterministic. Job readiness disclaimer always present. Tests pass.

---

### Phase J — Testing, Hardening, and QA (Qoder Task J)

**Objective:** Full test suite passing. Error paths covered. Security verified. Frontend integration verified.

**Actions:**
1. Run full test suite — all phases' tests
2. Verify all error/fallback paths from §27
3. Verify security requirements from §26
4. Run frontend with `NEXT_PUBLIC_USE_MOCK=false` — walk through all pages
5. Fix any integration issues found

**Definition of done:** All tests pass. Browser console shows no errors on any page. No secrets in any API response. All 17 items in §32 Definition of Done checked.

---

## 31. Qoder Credit Strategy

**Target: maximum 1,500 credits for remaining implementation.**

### Task batching rules

Give Qoder one coherent vertical slice per task — not individual files. A "vertical slice" means: model + retrieval function + service + router + tests for one feature. Coherent tasks produce less back-and-forth.

### Tasks worth a larger agent request

- Phase B (data model + retrieval layer) — give the full schema from §10 and retrieval spec from §14
- Phase H (ingestion) — complex enough to warrant a single large task with full spec
- Phase E (NBA) — critical path, give the full pipeline spec from §19

### Tasks that should be smaller

- Adding a router once the service exists
- Writing tests for a completed feature
- Fixing a specific bug (provide exact file + traceback)
- Adding a new field to a Pydantic schema

### What NOT to spend credits on

- Frontend redesign (Antigravity's responsibility)
- Rewriting working existing services
- Debugging without a specific error (provide the traceback first)
- Re-scanning the repository at the start of each session (Qoder should read the audit document instead)

### Preventing rewrites

At the start of each Qoder session:
1. Provide the current `DONE.md` contents
2. Explicitly state: "The following files are complete and should not be modified without a specific bug reason: [list]"
3. Reference this architecture document for decisions

### Mocking AI in tests

All tests must mock `ai_service.call_structured` and `ai_service.call_with_tools`. This prevents real Qwen calls during automated tests. Real Qwen is only called in `@pytest.mark.integration` tests, run manually before releases.

---

## 32. Definition of Done

The project is complete when all of the following are satisfied:

### Core functionality

- [ ] Student can register and receive JWT
- [ ] Onboarding persists profile, education_stage, interests, skills, motivation, career goal, sports interest
- [ ] Journey view shows current stage and max 3 visible next steps
- [ ] NBA generated after onboarding with candidate_id validation
- [ ] Career list browses from Pakistan knowledge base
- [ ] Career detail shows skills, demand, competition, difficulty
- [ ] Career Reality Check returns CareerReality + CareerVerdict (Qwen-grounded, DB-sourced facts)
- [ ] 7-Day Trial Plan generated by Qwen
- [ ] Roadmap created for career goal with milestone tracking
- [ ] Milestone progress saved and triggers new NBA
- [ ] Journey stage advances deterministically on correct events
- [ ] Opportunity list retrieves from DB (verified/validated only)
- [ ] Opportunity match score is deterministic (verified: call twice → same score)
- [ ] Sports opportunities discoverable
- [ ] Sports match score is deterministic
- [ ] Universities browsable by field and city
- [ ] Alumni discoverable by field and career
- [ ] Learning resources retrievable by skill
- [ ] Coach chat returns 200 (not 404), max 3 quick_actions, no invented resources
- [ ] Rate limit: 21st coach request returns 429
- [ ] Job readiness score is deterministic (verified: same profile → same score twice)
- [ ] Job readiness disclaimer always present
- [ ] Admin ingestion: POST URL list → CANDIDATE record created in DB
- [ ] Deduplication: same URL twice → one record, not two
- [ ] Content hash: unchanged source → no re-extraction

### AI rules

- [ ] No Pakistani university, opportunity, salary, or URL invented by Qwen
- [ ] Qwen cannot alter deterministic match scores or job readiness scores
- [ ] NBA candidate_id always in provided candidate list (verified in test)
- [ ] All Qwen outputs Pydantic-validated before reaching frontend

### MCP

- [ ] Both SSE endpoints respond
- [ ] All tools return correct structures
- [ ] Qwen Pattern B verified in integration test

### Testing

- [ ] Full test suite passes (all phases)
- [ ] Ingestion tests pass with mocked HTTP and Qwen
- [ ] Security test: cross-student data access returns 404
- [ ] Security test: no secret in any API response body
- [ ] Frontend `npm run build` exits 0
- [ ] Frontend `npm run lint` exits 0

### Local operation

- [ ] Backend starts cleanly with env var validation
- [ ] Frontend connects to backend at localhost:8000
- [ ] Seed data loads on empty DB
- [ ] Complete demo walk-through from registration → job readiness without errors

---

## 33. Future Expansion

The architecture is designed to support these expansions without rewrites:

**Vector/semantic search:** The retrieval layer has a stable interface. Embeddings can be computed for career/opportunity text and stored in a separate SQLite table (using sqlite-vec or similar). The retrieval functions become the integration point — no API or service changes needed.

**Managed PostgreSQL:** Replace `DATABASE_URL` with a PostgreSQL URL. SQLAlchemy abstracts the difference. FTS5 becomes `pg_trgm` or `tsvector`. Minor query adjustments only.

**Redis rate limiting:** The `InMemoryRateLimiter` is behind an interface. Replace the implementation with a Redis-backed one. No changes to coach_service or coach_router.

**Streaming coach responses:** Add `stream=True` to the Qwen call in `ai_service.py`. Add an SSE endpoint. Frontend subscribes. No architectural change.

**Alumni community submissions:** Add a `POST /api/v1/alumni/submit` endpoint that creates a record with `is_verified = FALSE` and `verification_status = 'CANDIDATE'`. Admin reviews and approves. No schema change.

**Additional ingestion sources:** Add source_type values and a source-specific retriever to `ingestion_service.py`. The pipeline is the same.

**Internship application tracking:** Add a `student_applications` table referencing `opportunities`. No existing table changes.

**Multiple career goal tracking:** student_profiles.career_goal_id can be extended to a many-to-many `student_career_goals` table. The roadmap model already supports multiple roadmaps per student.

---

*Document version: 2.0 — Master Revision*  
*Project: A&H Careers*  
*Prepared for: Qoder implementation*  
*Rule: Inspect actual repository first. Preserve working code. Deviate from this document only when actual working code conflicts with it, and document the deviation.*