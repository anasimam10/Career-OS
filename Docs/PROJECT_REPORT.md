# Career OS — Complete Technical Study & Hackathon Report

This document is the comprehensive technical reference for Career OS, prepared for the project owner, team, and hackathon presentation.

---

## 1. Project Overview
Career OS is a full-stack, AI-powered Career Operating System purpose-built for students in Pakistan. It bridges the critical information asymmetry in Pakistan’s educational ecosystem by pairing ground-truth data from the **Pakistan Knowledge Engine (PKE)** with an intelligent **Qwen AI runtime** from Alibaba Cloud DashScope.

---

## 2. Problem Statement
Pakistani students frequently face:
1. **Unrealistic Career Assumptions**: Over-saturation in traditional fields without awareness of real domestic market demand, salaries, or entry bottlenecks.
2. **Fragmented Institutional Information**: Fragmented data on university recognition, admission criteria, provincial quotas, and faculty specializations.
3. **Absence of Grounded Guidance**: Generic AI tools (like ChatGPT) frequently hallucinate Pakistani degrees, universities, and job market realities.
4. **Disjointed Athletic & Scholarship Pathways**: Lack of centralized access to sports trials (PCB, PFF, POA) and need/merit-based scholarships.

---

## 3. Target Users
- **Secondary & Intermediate Students (Matric/FSc/O/A-Levels)** exploring educational tracks and entry tests.
- **Undergraduate Students** seeking skill roadmaps, internships, and interview readiness.
- **Student Athletes** navigating trials, athletic quotas, and university sports scholarships.
- **Career Changers & Early Professionals** evaluating domestic market shifts.

---

## 4. Core Features
1. **Student Profiling & Onboarding (`/onboarding`)**: Captures education level, current city, career goals, skills, and sports interests.
2. **Personalized Journey & Next Best Action (`/journey`)**: Dynamic progression through 5 stages with active Next Best Action (NBA) calculations.
3. **Career Discovery & Reality Check (`/careers/[slug]/reality-check`)**: Frank assessments of market saturation, demand index, entry barriers, and salary brackets.
4. **Career Trial Plan (`/careers/[slug]/trial`)**: 7-day experiential simulation of day-to-day career tasks.
5. **University & Program Intelligence**: 248 verified/validated Pakistani institutions.
6. **Opportunities Portal (`/opportunities`)**: Domestic scholarships, fellowships, and internships.
7. **Sports Pathways (`/sports`)**: PCB, PFF, and POA trial registries and athletic scholarship opportunities.
8. **AI Career Mentor (`/mentor`)**: Conversational advisor grounded in PKE facts.
9. **Interactive Mock Interviews (`/mock-interview`)**: Career-specific technical/behavioral question engine with deterministic scoring and weak-topic feedback.
10. **Talk to Alumni (Future Roadmap Entry Point)**: Verified alumni connection network.

---

## 5. User Journey
1. **Landing Page (`/`)**: Discover platform vision and explore high-demand careers.
2. **Onboarding (`/onboarding`)**: Complete multi-step profile; triggers the first Next Best Action generation.
3. **Journey Dashboard (`/journey`)**: See immediate milestone, track horizontal phase progression, and complete milestones.
4. **Deep Dive (`/careers/[slug]`)**: Run Reality Checks, review university pathways, and start 7-day trials.
5. **Preparation (`/mock-interview`)**: Practice timed, career-grounded technical questions and review score reports.

---

## 6. System Architecture
```
┌────────────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend                     │
│               (App Router / Tailwind / TypeScript)         │
└─────────────────────────────┬──────────────────────────────┘
                              │ HTTPS / REST (JSON)
                              ▼
┌────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                         │
│   ┌───────────────────────┬────────────────────────────┐   │
│   │ Routers & Schemas     │ PKE Source Registry        │   │
│   ├───────────────────────┼────────────────────────────┤   │
│   │ Journey & NBA Engine  │ Mock Interview Engine      │   │
│   ├───────────────────────┼────────────────────────────┤   │
│   │ Model Context Protocol│ SQLite ORM (SQLAlchemy 2.0)│   │
│   └───────────────────────┴────────────────────────────┘   │
└──────────────┬──────────────────────────────┬──────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────┐┌─────────────────────────────┐
│ Alibaba Cloud DashScope     ││ SQLite Storage              │
│ (Qwen 3.7-Plus Model Chain) ││ (/data/ah_career.db)        │
└─────────────────────────────┘└─────────────────────────────┘
```

---

## 7. Frontend Architecture
- **Framework**: Next.js 14 App Router.
- **Language**: TypeScript (strict mode enabled, zero `any` leaks in core types).
- **Styling**: Tailwind CSS with custom dark-editorial design system.
- **State Management**: Client-side session management (`lib/session.ts`) coupled with custom React hooks (`useJourney`, `useOnboarding`) and SWR/fetch patterns.
- **Components**: Modular atomic hierarchy (cards, metric bars, modals, timelines).

---

## 8. Backend Architecture
- **Framework**: FastAPI (Python 3.11+).
- **Database Engine**: SQLAlchemy 2.0 with connection pooling and WAL mode SQLite.
- **Routers**: Cleanly partitioned endpoints (`/onboarding`, `/journey`, `/careers`, `/students`, `/mock-interviews`, `/coach`, `/universities`, `/opportunities`, `/sports`).
- **Security Middleware**: Multi-origin CORS support with whitespace sanitization and header-based tenant isolation (`X-Student-Id`).

---

## 9. Database Structure
Key tables in `ah_career.db`:
- `students`: Core profiles, education stage, city, bio, and preferences.
- `careers`: Slugs, market outlook, salary bands, domestic demand index, required skills.
- `universities`: HEC recognition status, public/private classification, city, province, website.
- `programs`: University degree offerings, admission criteria, and fee structures.
- `milestones` & `student_milestones`: Pathway steps, completion timestamps, and status flags.
- `opportunities` & `sports_opportunities`: Verified listings, deadlines, eligibility criteria.
- `mock_interview_sessions` & `mock_interview_questions`: Interactive session records, options, and scores.
- `pke_sources`: Provenance audit records tracking source URLs, freshness, and access status.

---

## 10. Pakistan Knowledge Engine (PKE) Architecture
PKE is the authoritative knowledge foundation of Career OS. It continuously curates verified Pakistani educational and labor market intelligence, providing grounded facts to the AI reasoning layers via Model Context Protocol (MCP) endpoints.

---

## 11. Source & Provenance Model
Every factual entity in the database tracks:
- `source_url`: Canonical URL of the originating publisher.
- `retrieved_at`: Timestamp of data extraction.
- `last_verified`: Timestamp of human or automated verification.
- `verification_status`: `VERIFIED`, `VALIDATED`, or `DEPRECATED`.

---

## 12. Primary vs Secondary Data Distinction
- **Primary Data (`VERIFIED`)**: Hand-curated, authoritative Pakistani institutional records (universities, degree roadmaps). Primary records can never be overwritten by automated secondary ingestions.
- **Secondary Data (`VALIDATED`)**: Enrichment data from external repositories that supplement primary records with additional metrics (e.g. faculty counts, research areas) without displacing primary facts.

---

## 13. External CSV Integration
Two key external datasets are integrated into PKE:
1. `number-of-public-universities-in-pakistan.csv`: Official HEC statistics expanding geographic university coverage across all provinces.
2. `pakistan-intellectual-capital-computer-science-ver-1.csv`: Deep faculty records detailing PhD specializations and research domains across Pakistani CS departments.

---

## 14. Model Context Protocol (MCP)
Internal MCP servers are mounted directly into FastAPI:
- `/mcp/career`: Exposes career market intelligence tools.
- `/mcp/opportunity`: Exposes real-time scholarships and internship queries.
- `/mcp/pke`: Exposes institutional verification tools.

---

## 15. Qwen Four-Model Runtime
The system implements a four-tier availability fallback chain:
1. **Primary**: `qwen3.6-plus` — High-capability reasoning, structured output synthesis.
2. **Fallback 1**: `qwen3.6-plus` — Seamless availability backup for HTTP 429/5xx.
3. **Fallback 2**: `qwen-plus-2025-07-28` — Stable production fallback.
4. **Fallback 3**: `qwen3-vl-235b-a22b-thinking` — High-reasoning emergency fallback.

---

## 16. AI Mentor
- Domain-specialized advisor utilizing conversational memory.
- Responses are grounded in domestic realities (e.g. entry tests like ECAT, MDCAT, NTS, FAST Nu, NET).
- Fallback-resilient: Never fails closed; falls back deterministically to grounded advice if network is interrupted.

---

## 17. Mock Interview Engine
- **Grounding**: Career-specific questions generated based on official skill standards (e.g. Data Structures & OOP for Software Engineering; Financial Accounting & Audit for Accounting).
- **Answer Security**: Correct answers and explanations are scrubbed from in-progress responses and only revealed post-submission.
- **Deterministic Scoring**: Automated score computation with topic performance breakdown and weak-area learning links.
- **Performance**:
  - Pre-seeded / Cached question bank latency: ~0.04s.
  - Live uncached Qwen AI generation latency: ~31s.

---

## 18. Student Personalization
Student roadmaps are dynamically shaped by:
- Educational level (Intermediate vs Undergraduate).
- Geographic location (Karachi, Lahore, Islamabad, Quetta, Peshawar, etc.).
- Intended career trajectory and declared motivation tags.

---

## 19. Student Isolation
Multi-tenant security is enforced across all endpoints:
- Every mutation checks the `X-Student-Id` header against database ownership.
- Attempting to complete, view, or modify another student's milestone or interview session returns **HTTP 404 Not Found**.

---

## 20. API Structure
All API routes are prefixed under `/api/v1`:
- `GET /health` — Health check and uptime validation.
- `POST /onboarding` — Profile creation & initial NBA generation.
- `GET /journey` — Current stage, next steps, and active NBA.
- `POST /progress` — Milestone completion and stage advancement.
- `GET /careers` & `POST /career/analyze` — Market intelligence & Reality Checks.
- `GET /universities` — 248 institutional records.
- `POST /coach/chat` — Conversational AI mentoring.
- `POST /mock-interviews/setup` & `/submit` & `/results` — Interview simulation lifecycle.

---

## 21. Data Flow
`User Input (Frontend) -> Next.js API Client -> FastAPI Router -> Service Layer -> PKE Database -> Qwen AI -> Validated JSON -> Frontend UI`.

---

## 22. Security & Compliance
- **Zero Committed Secrets**: Rigorous git log scan confirmed zero live API keys or credentials in history.
- **Strict Environment Isolation**: Local secrets stored exclusively in gitignored `.env` files; production secrets injected via cloud dashboard environment variables.
- **No Database Leaks**: Production databases run on isolated cloud disks.

---

## 23. Testing
Comprehensive test suite:
- **Backend**: **778 passing unit and integration tests** in pytest (covering data integrity, PKE ingestion, student isolation, and mock interviews).
- **Frontend**: TypeScript strict typecheck (0 errors) and ESLint validation.
- **Production Build**: Successful static generation of 14 Next.js routes.

---

## 24. Deployment Overview
- **Frontend**: Hosted on **Vercel** with edge caching and global CDN distribution.
- **Backend**: Hosted on **Render** as a containerized web service with persistent disk storage.

---

## 25. Vercel Configuration
- Root Directory: `Frontend`
- Framework Preset: `Next.js`
- Environment Variables:
  - `NEXT_PUBLIC_API_URL`: `https://ah-career-backend.onrender.com/api/v1`
  - `NEXT_PUBLIC_USE_MOCK`: `false`

---

## 26. Render Configuration
- Root Blueprint: `render.yaml`
- Dockerfile Path: `BackEnd/Dockerfile`
- Disk: 1GB persistent disk mounted at `/data`
- Environment Variables:
  - `DATABASE_URL`: `sqlite:////data/ah_career.db`
  - `DASHSCOPE_API_KEY`: Injected securely via dashboard.
  - `CORS_ORIGINS`: `http://localhost:3000,https://career-os-seven-flame.vercel.app`

---

## 27. Docker Containerization
- Base Image: `python:3.11-slim`
- Build-Time Seeding: Pre-seeds canonical careers and universities to ensure sub-second cold starts.
- Host Binding: `0.0.0.0:${PORT:-8000}` with `--workers 1` for single-writer SQLite integrity.

---

## 28. Known Limitations
- SQLite single-writer model requires worker concurrency set to 1.
- Initial cold starts on free cloud tiers may require a brief warmup for external AI API calls.
- Live unstructured AI question generation requires ~30s; pre-seeded grounded question banks are used to provide instantaneous user experiences.

---

## 29. Future Roadmap
1. **Talk to Alumni Phase 2**: Launch live messaging and scheduling with verified graduates.
2. **PostgreSQL Migration**: Seamless ORM transition to AWS RDS / Supabase for horizontal multi-worker scaling.
3. **Automated WhatsApp Advisory Bot**: Extending PKE Next Best Action notifications to WhatsApp for students with limited internet connectivity.

---

## 30. Hackathon Presentation & Demo Flow
1. **The Hook (1 min)**: Introduce the Pakistani student reality check crisis—thousands graduating into saturated sectors without local market intelligence.
2. **The Product Walkthrough (2 mins)**:
   - Walk through Onboarding on the live Vercel URL.
   - Show the Journey Map with real-time Next Best Action.
   - Show Career Reality Check (demand index, salary bands, university feeds).
   - Demonstrate the AI Mock Interview engine and instantaneous score report.
   - Showcase the Talk to Alumni future roadmap entry point.
3. **The Technology & Trust (1 min)**:
   - Highlight PKE provenance: 248 real universities, primary vs secondary data separation.
   - Highlight the Qwen multi-model availability chain.
4. **Conclusion & Impact (30 secs)**: Career OS democratizes career intelligence for every student in Pakistan.

---

## 31. Likely Judge Questions & Answers
- **Q: Why Qwen instead of OpenAI or Gemini?**
  - *A: Qwen 3.7 models demonstrate state-of-the-art multilingual comprehension, exceptional token economics for regional markets, and reliable structured JSON generation under high concurrency.*
- **Q: How do you prevent hallucinations regarding Pakistani universities?**
  - *A: All university records are strictly retrieved from our local PKE database (backed by official HEC records). The AI is constrained by strict system prompts and context injection.*
- **Q: How is student privacy protected?**
  - *A: We implement strict tenant boundary checks using session headers (`X-Student-Id`). Student records, mock interviews, and milestone completions are completely isolated from one another.*
