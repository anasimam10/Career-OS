# Career OS
## Career Operating System

Career OS is an intelligent, Pakistan-focused Career Operating System that transforms fragmented career and education information into clear, evidence-driven pathways. Built for students, university applicants, and early-career professionals, it combines verified academic data, Pakistan-specific career and salary intelligence, university and opportunity discovery, career trials, sports pathways, learning resources, and a grounded AI mentor into one personalized system. Career OS turns complex choices into practical next steps through contextual guidance and a personalized Next Best Action (NBA).

---

## What It Does

- **Personalized Onboarding**: Guided multi-step profiling capturing education stage, city, career goals, baseline skills, and sports interests.
- **Career Discovery & Reality Check**: Unvarnished market demand analysis, local employer realities, and starting-to-peak PKR salary bands across 22 Pakistani career pathways.
- **Career Pathways & Journey**: Actionable 7-day career trial micro-curriculums and milestone-driven progression roadmaps that recalculate Next Best Actions upon completion.
- **Universities & Programs**: Searchable registry covering 248 Pakistani universities and 174 degree programs across all provinces with entrance test prerequisites.
- **Opportunities & Scholarships**: 31 verified regional scholarships (HEC, PEEF, Ehsaas), corporate internships, and trainee fellowships.
- **Sports Pathways**: 18 dedicated athletic listings across PCB academies, departmental trials (WAPDA, Army), and university sports quota admissions.
- **Learning Resources**: 75 curated technical and foundational roadmaps mapped directly to required career skills.
- **Grounded AI Mentor**: Conversational counseling powered by Qwen, strictly constrained by local Pakistani education and employment facts.
- **Mock Interviews**: Interactive technical screening sessions with secure evaluation rubrics, deterministic scoring, and direct learning resource remediation.
- **Talk to Alumni (Coming Soon)**: Future verified community gateway previewing 1-on-1 mentorship with graduates from top Pakistani institutions.

---

## How It Works

```
Next.js 14 Client (Vercel)
  ↓ [REST API + X-Student-Id]
FastAPI Application (Render / Docker)
  ↓ [Tool-Mediated Context]
Pakistan Knowledge Engine (PKE) & MCP SSE Servers
  ↓ [Strict JSON Contracts]
Alibaba Cloud Qwen Model Chain (qwen3.6-plus primary)
  ↓
Grounded, Hallucination-Free Personalized Student Experience
```

---

## Technology

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Framer Motion
- **Backend**: FastAPI (Python 3.13), SQLAlchemy 2.0, Pydantic v2, SQLite (WAL mode)
- **AI Runtime**: Alibaba Cloud DashScope Qwen Model Chain (`qwen3.6-plus` primary with multi-model availability fallbacks: `qwen-plus-2025-07-28`, `qwen3-vl-235b-a22b-thinking`, `qwen-turbo`)
- **Knowledge Architecture**: Model Context Protocol (MCP) SSE servers, Pakistan Knowledge Engine (PKE)

---

## Data & Trust

- **Pakistan-Specific**: All institutional data, fee ranges, entrance criteria, and salaries reflect real Pakistani conditions.
- **PKE Source Registry**: Tracks 40 verified primary provenance sources (HEC, PEC, PMDC, PCB, universities).
- **Primary vs. Secondary**: Authoritative primary PKE records always take precedence; external datasets (`number-of-public-universities-in-pakistan.csv` and `pakistan-intellectual-capital-computer-science-ver-1.csv`) act purely as secondary supporting evidence with zero-overwrite guarantees.
- **Zero Fabrication**: AI outputs are strictly constrained to retrieved context; the system will never invent universities, cutoffs, or deadlines.

---

## Live Demo

- **Frontend (Vercel)**: [https://career-os-seven-flame.vercel.app](https://career-os-seven-flame.vercel.app)

---

## Backend

- **Backend API (Render)**: [https://ah-career-backend.onrender.com](https://ah-career-backend.onrender.com)
- **Interactive Swagger Docs**: [https://ah-career-backend.onrender.com/docs](https://ah-career-backend.onrender.com/docs)
- **Health Check Probe**: [https://ah-career-backend.onrender.com/health](https://ah-career-backend.onrender.com/health)

---

## GitHub

- **Public Repository**: [https://github.com/anasimam10/Career-OS](https://github.com/anasimam10/Career-OS)

---

## Run Locally

### Backend Setup
```bash
cd BackEnd
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
*API serves on `http://127.0.0.1:8000` (Swagger docs at `/docs`).*

### Frontend Setup
```bash
cd Frontend
npm install
npm run dev
```
*App serves on `http://localhost:3000`.*

---

## Deployment

- **Frontend**: Automatically deployed to **Vercel** on pushes to `main`.
- **Backend**: Containerized with **Docker** and deployed as a persistent Web Service on **Render**.
