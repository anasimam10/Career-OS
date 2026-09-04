# CAREER OS — FORENSIC TECHNICAL & PRODUCT STUDY REPORT
**Document Version:** 2.0 (Submission-Lock Release)  
**System Designation:** Pakistan Career & Education Operating System (Career OS)  
**Production Frontend:** [https://career-os-seven-flame.vercel.app](https://career-os-seven-flame.vercel.app)  
**Production Backend:** [https://ah-career-backend.onrender.com](https://ah-career-backend.onrender.com)  
**API Documentation (Swagger):** [https://ah-career-backend.onrender.com/docs](https://ah-career-backend.onrender.com/docs)  
**Source Code Repository:** [https://github.com/anasimam10/Career-OS](https://github.com/anasimam10/Career-OS)  

---

## 1. EXECUTIVE SUMMARY

**Career OS** is a full-stack, enterprise-grade Career Operating System engineered specifically for the Pakistani education and labor ecosystem. Pakistani youth constitute over 64% of the national population, yet face severe structural information friction: obsolete university prospectuses, ungrounded societal hype cycles, opaque admission criteria, unverified scholarship solicitations, and near-total neglect of structured athletic pathways.

Career OS bridges this structural gap by combining:
1. **Pakistan Knowledge Engine (PKE)**: A high-integrity data ingestion, normalization, and provenance tracking engine that grounds all facts in verified Pakistani primary institutional data.
2. **Model Context Protocol (MCP)**: Strict tool-mediated retrieval barriers that isolate LLMs from hallucinating career figures, admissions criteria, or university stats.
3. **Qwen Multi-Model Fallback Chain**: A production AI runtime powered by Alibaba Cloud DashScope (`qwen3.6-plus` primary), operating under strict JSON Schema contracts with deterministic model fallbacks.
4. **Interactive Action Engine**: Personalized 7-step onboarding, deterministic 7-day career trial plans, milestone-driven progression roadmaps, job readiness diagnostics, interactive mock interviews, and athletic opportunities.

**Current Deployment Status**:
- **Frontend**: Live on **Vercel** (`Next.js 14 App Router`, Edge CDN, fully responsive).
- **Backend**: Live on **Render** (`FastAPI 0.115+`, Docker Container, Uvicorn, SQLite persistent disk).
- **Test Coverage**: 778 automated backend unit/integration tests passing (100% green); clean TypeScript compiler and production build verification.

---

## 2. PROBLEM STATEMENT

### The Problem
Pakistani high-school and undergraduate students navigate career decisions in an environment characterized by pervasive misinformation. The traditional counseling model relies on word-of-mouth anecdotes, commercial admission agencies, or unvetted social media forums.

### Concrete Impact
- **Educational Malinvestment**: Tens of thousands of students enroll in generic degree programs without understanding market saturation, starting compensation, or local employer expectations in Karachi, Lahore, Islamabad, or Peshawar.
- **Lost Opportunities**: Billions of rupees in genuine regional scholarships (HEC, Ehsaas, PEEF, university endowments) lapse unclaimed due to opaque deadlines and discovery barriers.
- **Athletic Dead-Ends**: Talented student athletes possess no unified discovery engine for departmental trials (PCB, WAPDA, HEC, Army) or university sports quota admissions.

### Current Gap
Existing global platforms (LinkedIn, Coursera, Glassdoor) are calibrated to Western or multinational enterprise markets. They do not capture Pakistani entry test dynamics (ECAT, MDCAT, NUST NET, FAST NU), local rupee salary realities, or regional industrial clusters.

### The Career OS Solution
Career OS provides an end-to-end, localized operating system where every piece of data—salaries, entry criteria, degree pathways, opportunities, and learning milestones—is strictly grounded in verified Pakistani institutional data, verified provenance URLs, and deterministic Next Best Actions (NBA).

---

## 3. TARGET USERS

### Primary Users
1. **Intermediate / A-Level Students (Ages 16–19)**:
   - Navigating field selection (Pre-Engineering, Pre-Medical, ICS, General Science).
   - Evaluating target universities (NUST, FAST-NUCES, GIKI, LUMS, IBA, UET, NED, COMSATS).
   - Preparing for entrance test formats and understanding realistic campus culture.
2. **Undergraduate Students (Ages 19–24)**:
   - Transitioning from academic coursework to professional employment.
   - Requiring actionable skill roadmaps, tech stack readiness, and localized mock interview practice.
   - Seeking verified internships, trainee programs, and local fellowships.
3. **Student Athletes & Sports Aspirants**:
   - Exploring dual-career academic scholarships and institutional team trials across Pakistan.

### Secondary Users
- **Academic & Career Counselors**: Requiring an unvarnished, empirical reference baseline for labor market statistics.
- **University Placements Offices**: Reviewing industry competency benchmarks.

---

## 4. PRODUCT VISION: A "CAREER OPERATING SYSTEM"

Career OS is fundamentally designed as an **Operating System**, not an informational content blog or a generic chat wrapper:
- **Stateful Execution**: The user does not simply consume static text; they maintain a stateful student session (`X-Student-Id`) with an evolving journey stage (`HIGH_SCHOOL` → `EXPLORING` → `SKILL_BUILDING` → `APPLICATION_PREP` → `CAREER_LAUNCH`).
- **Deterministic Roadmapping**: The system calculates a personalized Next Best Action (NBA) grounded in student inputs.
- **PKE Kernel**: The backend serves as a protected operating kernel where external sources are staged, verified, deduplicated, and served via MCP tools.
- **Ground Truth Grounding**: The AI cannot invent universities, careers, or opportunities; it can only interpret and synthesize data supplied from the verified kernel.

---

## 5. MAIN FEATURES

### Primary / Core Features
1. **Personalized 7-Step Onboarding Wizard**:
   - Captures education stage, city, academic interests, target careers, sports passions, motivations, and baseline skills.
   - Automatically initializes a personalized profile and seeds their initial milestone roadmap.
2. **Grounded Career Explorer (22 Real Pakistan Careers)**:
   - Covers Software Engineering, Data Science, AI/ML, Cloud Architecture, Cyber Security, Mechanical, Electrical, Civil, Robotics, Biotechnology, Medicine, Accounting/Finance, FinTech, Digital Marketing, Product Management, UI/UX, Sports Management, and more.
   - Displays real salary ranges in PKR (starting, median, top-tier), market demand level, top domestic employers, and required tools.
3. **Career Reality Check & 7-Day Trial Plan**:
   - Algorithmic evaluation comparing the student’s current profile against career demands.
   - Generates a structured day-by-day 7-day micro-curriculum to test real aptitude before committing tuition.
4. **Dynamic Student Journey & Next Best Action (NBA)**:
   - Tracks current milestone, completed milestones, and upcoming pathway phases.
   - Recalculates the student’s Next Best Action upon milestone completion.
5. **Grounded AI Mentor (Coach Chat)**:
   - Interactive conversational assistant powered by `qwen3.6-plus` via DashScope.
   - Strictly grounded in Pakistani labor and education context; cites specific universities, entry tests, and employer realities.
6. **AI Mock Interview Engine**:
   - Provides role-tailored technical and behavioral interview sessions.
   - Evaluates answers using structured scoring rubrics and maps weaknesses directly to learning resources.
7. **Curated Learning Resources (75 Verified Resources)**:
   - Maps roadmaps, documentation, and free certifications directly to target skill competencies.
8. **Institutional Opportunities & Sports Engine (31 Opps + 18 Sports Listings)**:
   - Verified scholarships, fellowships, internships, and national athletic trials across Pakistan.

### Secondary / Supporting Features
- **Job Readiness Diagnostic**: Rapid self-assessment evaluating portfolio, resume, and technical preparedness.
- **University & Program Discovery**: Access to 248 institutions and 174 degree programs with provincial filtering.
- **Talk to Alumni (Future Frontend Gateway)**: Dedicated community section previewing direct verified mentorship connections.

---

## 6. COMPLETE USER JOURNEY

```
1. Landing Page (Hero & Features Overview)
   ↓
2. Onboarding Wizard (Education, City, Careers, Skills, Sports)
   ↓
3. Profile Creation (Unique X-Student-Id generated & saved in session)
   ↓
4. Career Discovery (/careers -> View Pakistani market demand & PKR salary bands)
   ↓
5. Career Reality Check (/careers/[slug]/reality-check -> Candid fit assessment)
   ↓
6. 7-Day Career Trial (/careers/[slug]/trial -> Actionable 7-day curriculum)
   ↓
7. Personalized Journey (/journey -> Track milestones & complete Next Best Action)
   ↓
8. Opportunity Matching (/opportunities -> Filter local scholarships & internships)
   ↓
9. AI Mentor Consultation (/mentor -> Grounded advisory chat via Qwen 3.6-plus)
   ↓
10. Mock Interview Practice (/mock-interview -> Live technical screening & feedback)
    ↓
11. Athletic Pathway Exploration (/sports -> University trials & sports quotas)
    ↓
12. Alumni Mentorship Exploration (/alumni -> Verified alumni community portal)
```

---

## 7. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                  │
│                 Next.js 14 App Router (Vercel CDN)                      │
│        Tailwind CSS • Framer Motion • LocalStorage Session Context      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTPS / REST (X-Student-Id)
┌────────────────────────────────────▼────────────────────────────────────┐
│                          API GATEWAY LAYER                              │
│                    FastAPI 0.115+ (Render Container)                    │
│             CORS Middleware • Route Validation • Error Boundary         │
└──────┬─────────────────────────────┬─────────────────────────────┬──────┘
       │                             │                             │
┌──────▼──────────────┐       ┌──────▼──────────────┐       ┌──────▼──────┐
│  CORE SERVICES      │       │  PKE RETRIEVAL      │       │  MCP SSE    │
│  - Onboarding       │       │  - Source Registry  │       │  SERVERS    │
│  - Journey & NBA    │       │  - University FTS   │       │  - Career   │
│  - Career Analysis  │       │  - Secondary CSV    │       │  - Opps     │
│  - Mock Interview   │       │  - Normalization    │       │  - PKE      │
└──────┬──────────────┘       └──────┬──────────────┘       └──────┬──────┘
       │                             │                             │
┌──────▼─────────────────────────────▼─────────────────────────────▼──────┐
│                       AI RUNTIME SUBSYSTEM                              │
│         Alibaba Cloud DashScope (Singapore Compatible Mode)             │
│   Primary: qwen3.6-plus                                                 │
│   Fallback 1: qwen-plus-2025-07-28                                      │
│   Fallback 2: qwen3-vl-235b-a22b-thinking                               │
│   Fallback 3: qwen-turbo                                                │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                         PERSISTENCE LAYER                               │
│                   SQLite Database (Mounted Volume)                      │
│      248 Universities • 174 Programs • 22 Careers • 40 Sources         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. FRONTEND ARCHITECTURE

- **Framework**: Next.js 14.2.5 utilizing the App Router architecture.
- **Client/Server Boundaries**: Interactive client components declared with `"use client"` for reactive state (wizards, timelines, chat streams); layouts and static routes optimized for fast initial rendering.
- **Session Handling**: Pure client-side session management via `Frontend/lib/session.ts`. Stores `student_id`, `name`, and `city` in `localStorage`. Automatically dispatches `X-Student-Id` header on all API queries.
- **URL Normalization**: Robust `getBaseUrl()` utility in `Frontend/lib/api/client.ts` normalizes `NEXT_PUBLIC_API_URL`, automatically stripping trailing slashes and ensuring the `/api/v1` path prefix is always preserved in production.
- **UI & Styling**: Vanilla Tailwind CSS with custom design system tokens (deep navy background `#05080E`, indigo accents, translucent glassmorphism panels, and framer-motion page transitions).

---

## 9. BACKEND ARCHITECTURE

- **Framework**: FastAPI (Python 3.13) with asynchronous Uvicorn server.
- **Router Modularization**: 14 dedicated routers (`onboarding`, `careers`, `journey`, `opportunities`, `sports`, `coach`, `job_readiness`, `universities`, `alumni`, `learning`, `mock_interviews`, `students`, `admin`, `health`).
- **Dependency Flow**: Clean dependency injection via `database.get_db` and `routers.deps.get_current_student_id`.
- **Validation**: Strict Pydantic models validate all incoming payloads and serialize outgoing contracts.
- **Error Handling**: Custom global exception handlers sanitize internal stack traces and return predictable error envelopes (`{"detail": "..."}` or `{"error": "..."}`).

---

## 10. DATABASE ARCHITECTURE

The persistence layer uses SQLAlchemy ORM backed by SQLite (with production support for PostgreSQL):
1. `Student`: Unique identity, education stage, city, academic interests, sports tags, motivation tags.
2. `StudentSkill`: Relational skill matrix mapping skill names and proficiencies to student IDs.
3. `Career`: Detailed occupational profiles, salaries (PKR), job growth outlook, core competencies.
4. `University`: 248 institutions across all Pakistani provinces with sector, city, accreditation status.
5. `Program`: 174 degree programs mapped to university records, fee bands, and career slugs.
6. `JourneyState` & `StudentMilestone`: Progression tracker recording milestone completions and personalized rationale.
7. `NextBestAction`: Ephemeral or cached next best recommendation linked to student stage.
8. `Opportunity` & `StudentOpportunityMatch`: Verified scholarships and internships with criteria matching.
9. `SportsOpportunity`: Athletic listings, university sports quota admissions, and departmental trials.
10. `MockInterviewSession` & `MockInterviewQuestion`: Interactive interview transcripts, scores, and feedback.
11. `PKESource` & `PKEStagingRecord`: Provenance registry tracking raw sources, reachability, and staged extractions.

---

## 11. STUDENT IDENTITY & ISOLATION

- **Zero-Login Friction**: To maximize accessibility for Pakistani students, authentication utilizes a deterministic session token model without requiring invasive passwords.
- **The `X-Student-Id` Contract**: Every authenticated request passes `X-Student-Id: <id>`.
- **Tenant Isolation**: All milestone updates, journey fetches, mock interview evaluations, and profile edits execute queries filtered strictly by `student_id`. A request from Student 5 attempting to modify Milestone 10 belonging to Student 4 returns an immediate **HTTP 404 / 403 Forbidden**.
- **Fresh Enrollment**: Passing `X-Student-Id: new` during onboarding triggers automatic student record allocation in the database.

---

## 12. PAKISTAN KNOWLEDGE ENGINE (PKE)

The Pakistan Knowledge Engine is the data integrity backbone of Career OS:
1. **Source Registry**: Maintains 40 vetted institutional sources (HEC, PEC, PMC/PMDC, PCB, Board of Intermediate & Secondary Education, top university portals).
2. **Ingestion & Fetching**: Fetches raw content, computes SHA-256 hashes to detect content modifications, and tracks HTTP status.
3. **Normalization**: Enforces standardized schemas for salaries, deadlines, admission criteria, and provinces.
4. **Deduplication**: Resolves university aliases (e.g. "FAST", "FAST-NUCES", "National University of Computer and Emerging Sciences" resolve to the single canonical entity).
5. **Staging Review**: New raw extractions enter a quarantine staging table (`PKEStagingRecord`) until deterministic validation confirms zero missing required fields before promoting to live tables.

---

## 13. PRIMARY VS SECONDARY DATA POLICY

Career OS implements a strict data authority hierarchy:
- **Primary PKE Data**: Authoritative data directly verified against official university websites, HEC accreditations, and direct institutional announcements. These records take 100% precedence and can never be overwritten by secondary imports.
- **External Secondary Datasets**: Used strictly for supporting enrichment:
  1. `number-of-public-universities-in-pakistan.csv` (11 rows): Regional distribution and historical founding data.
  2. `pakistan-intellectual-capital-computer-science-ver-1.csv` (2,092 rows): National faculty dataset providing empirical insights into computer science department strengths and PhD credentials.
- **Zero-Overwrite Rule**: Secondary datasets only enrich missing non-essential metadata; existing validated primary records remain unmutated.

---

## 14. UNIVERSITY & PROGRAM COVERAGE

- **Universities**: 248 verified institutions across Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan, Islamabad Capital Territory, Azad Jammu & Kashmir, and Gilgit-Baltistan.
- **Degree Programs**: 174 structured degree programs across computing, engineering, business, medical sciences, and arts.
- **Full-Text Search (FTS)**: Rapid retrieval by university name, city, province, and program discipline.

---

## 15. MODEL CONTEXT PROTOCOL (MCP)

Career OS embeds MCP SSE servers (`Mcp/career_server.py`, `Mcp/opportunity_server.py`, `Mcp/pke_server.py`) mounted directly under `/mcp`:
- **Tool-Mediated Access**: The AI cannot query raw database tables directly. It calls structured tools (`search_careers`, `get_career_details`, `match_opportunities`, `search_knowledge`).
- **Enforced Filtering**: The MCP tools automatically filter out expired deadlines, unverified opportunities, and out-of-region entries before presenting facts to the LLM.
- **Provenance Injection**: Every fact returned through MCP carries its `source_url` and `retrieved_at` timestamp.

---

## 16. QWEN AI ARCHITECTURE

### Production Model Configuration
- **Provider**: Alibaba Cloud DashScope (Singapore Region Compatible Mode).
- **Primary Model**: `qwen3.6-plus` (Verified active and responsive).
- **Retired Models**: `qwen3.7-plus` was removed and retired after quota expiration; it is not called anywhere in the runtime.
- **Four-Model Fallback Chain**:
  1. `qwen3.6-plus` (Primary high-reasoning model)
  2. `qwen-plus-2025-07-28` (Secondary fallback)
  3. `qwen3-vl-235b-a22b-thinking` (Deep reasoning fallback)
  4. `qwen-turbo` (High-speed capacity backup)
- **Fallback Trigger Policy**: Fallback occurs **only** on model-availability failures (HTTP 429 rate limit, quota exhaustion, 404 not found, or 5xx provider outages). Client errors (400, 401, 422) fail fast without switching models.
- **Gemini Status**: Google Gemini / Antigravity is used exclusively as an **external developer IDE coding assistant** during development; it is **NOT** part of the Career OS production runtime.

---

## 17. AI MENTOR PIPELINE

```
Student Message + Conversation History
  ↓
Student Profile Injected (Education Stage, City, Target Career)
  ↓
MCP Tool Retrieval (Grounded PKE Knowledge & Real Pakistan Facts)
  ↓
Qwen 3.6-plus Generation (Strict Temperature & Guardrails)
  ↓
Pydantic Schema Validation (Next Best Action Extraction)
  ↓
Grounded UI Response with Verified Actionable Guidance
```

---

## 18. MOCK INTERVIEW ENGINE

- **Dual-Path Architecture**:
  1. **Pre-Seeded / Cached Questions**: High-speed, instantaneous question sets for common Pakistani software and data roles, preventing latency.
  2. **Live Qwen Generation**: Dynamic question generation tailored to niche career paths when uncached.
- **Answer Security**: Ideal answers and evaluation criteria are stored securely on the backend; the client never receives the grading rubric during the active interview.
- **Deterministic Scoring**: Answers are evaluated against a standardized 0–100 rubric analyzing conceptual clarity, practical examples, and communication, with constructive feedback pointing directly to Career OS learning resources.

---

## 19. CAREER PATHWAY FEATURES

- **Reality Check**: Analyzes student skills and education against local employer demand, highlighting competitive advantages and realistic market hurdles.
- **7-Day Trial Plan**: Breaks a daunting career transition into seven bite-sized daily challenges (e.g. Day 1: Development Environment Setup; Day 3: Build a Basic Script; Day 7: Mini Capstone).
- **Milestone Engine**: As students mark milestones complete, the system marks the progress in the database and computes the next milestone.

---

## 20. OPPORTUNITIES & SCHOLARSHIPS

- 31 verified active opportunities spanning national merit scholarships (HEC Indigenous, PEEF, Ehsaas, USAID-Pak), corporate trainee programs, and local tech bootcamps.
- Matched dynamically by city and education level.

---

## 21. SPORTS PATHWAY SUBSYSTEM

- 18 dedicated athletic listings across cricket, football, hockey, squash, and athletics.
- Connects students with institutional trials (PCB academies, departmental squads) and universities offering dedicated athletic admission quotas (NUST, LUMS, UET).

---

## 22. LEARNING RESOURCES REPOSITORY

- 75 curated, free-to-access resources directly mapped to skill tags (e.g. Python, SQL, Docker, React, Financial Modeling).
- Integrated into mock interview feedback loops to recommend specific remediation material.

---

## 23. PROFILE & ENROLLMENT

- Captured during onboarding and fully editable at `/profile`.
- Allows students to update their education stage, city, and target careers as their aspirations evolve.

---

## 24. ALUMNI MENTORSHIP STATUS

- **Current State**: Visual community gateway and frontend roadmap feature accessible at `/alumni` and in the top navigation bar.
- **Backend Implementation**: Fully static frontend template; no automated fake alumni profiles or simulated chats are fabricated, maintaining total trust and transparency.

---

## 25. SECURITY & SECRETS MANAGEMENT

- **Public Repository Safety**: Verified that zero production secrets, API keys, or private database files are committed to Git.
- **Sanitized Logging**: All server logs pass through secret-redaction filters (`_SECRET_PATTERN`) preventing API key leaks in console dumps.
- **Client Security**: Frontend bundles strictly expose public environment variables (`NEXT_PUBLIC_API_URL`); all private DashScope keys and JWT secrets remain sealed inside the Render backend environment.

---

## 26. TESTING & VERIFICATION

- **Backend Test Suite**: **778 passed, 0 failed** (100% pass rate across 35 test suites in 85s).
- **Frontend Typecheck**: `tsc --noEmit` passed with **0 errors**.
- **Frontend Production Build**: `npm run build` compiled cleanly with all 14 routes statically generated.
- **Live Integration Tests**: End-to-end multi-step user flow (onboarding → profile → journey → progress → cross-student isolation) verified live against the production Render API with HTTP 200 OK responses.

---

## 27. DEPLOYMENT & INFRASTRUCTURE

- **Frontend**: Deployed to Vercel connected to GitHub repository `main` branch. Environment variable `NEXT_PUBLIC_API_URL=https://ah-career-backend.onrender.com/api/v1`.
- **Backend**: Deployed to Render via Docker container. Built from `BackEnd/Dockerfile` with persistent disk mounted at `/data/ah_career.db`.
- **Health Checks**: Platform health check probes mounted at both `GET /` and `GET /health`, returning HTTP 200 OK for automated Render deploy verification.

---

## 28. KNOWN SYSTEM LIMITATIONS

1. **Uncached AI Latency**: Real-time Qwen generation for specialized interview questions or mentor chats can take 3–5 seconds depending on DashScope regional API transit.
2. **Alumni Subsystem**: Community alumni messaging is a frontend portal only; live 1-on-1 alumni chat is slated for future development.
3. **Database Concurrency**: Current production deployment utilizes SQLite on a persistent disk. Highly concurrent enterprise scaling will require migration to managed PostgreSQL.

---

## 29. FUTURE PRODUCT ROADMAP

- **Phase 1 (Post-Hackathon)**: Live verified Alumni matching network with scheduled mentor sessions.
- **Phase 2**: Regional Urdu / Roman Urdu speech-to-text integration for voice-assisted mock interviews.
- **Phase 3**: Direct employer portal allowing Pakistani companies to post verified entry-level trainee opportunities.

---

## 30. VERIFIED PROJECT METRICS

| Metric Category | Verified Count | Primary Source |
| :--- | :--- | :--- |
| **Universities Covered** | **248** | `data/seed/universities.json` (HEC recognized) |
| **Degree Programs** | **174** | `data/seed/programs.json` |
| **Pakistani Career Pathways** | **22** | `data/seed/careers.json` |
| **Curated Learning Resources** | **75** | `data/seed/learning_resources.json` |
| **Institutional Opportunities** | **31** | `data/seed/opportunities.json` |
| **Sports & Athletic Listings** | **18** | `data/seed/sports_opportunities.json` |
| **PKE Provenance Sources** | **40** | `data/seed/pke_sources.json` |
| **External Public Uni Data** | **11 rows** | `data/external/number-of-public-universities-in-pakistan.csv` |
| **External CS Faculty Data** | **2,092 records** | `data/external/pakistan-intellectual-capital-computer-science-ver-1.csv` |
| **Backend Test Suite** | **778 passing** | `pytest -q` (0 failures) |
| **Frontend Production Routes** | **14 routes** | `next build` (Static & Dynamic) |

---

## 31. FINAL TECHNICAL SUMMARY

Career OS demonstrates that generative AI in education achieves maximum utility only when coupled with deterministic, localized data governance. By architecting an operating system grounded in the **Pakistan Knowledge Engine**, mediated by **Model Context Protocol** servers, resiliently powered by **Qwen 3.6-plus multi-model fallback chains**, and delivered through a high-performance **Next.js 14** client, Career OS provides Pakistani youth with a trustworthy, dignified, and empirical career navigation infrastructure.
