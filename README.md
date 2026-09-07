# Career OS
### Pakistan's Career Operating System

**Career OS** is an enterprise-grade Career Operating System engineered specifically for the Pakistani education and labor ecosystem. It replaces fragmented searches, conflicting advice, and social media hype with a deterministic, personalized pathway guiding students from high school through university selection to their first job.

---

## Live Deployments & Verification

- **Production Frontend (Vercel)**: [https://career-os-seven-flame.vercel.app](https://career-os-seven-flame.vercel.app)
- **Production Backend (Render)**: [https://ah-career-backend.onrender.com](https://ah-career-backend.onrender.com)
- **Interactive API Documentation (Swagger)**: [https://ah-career-backend.onrender.com/docs](https://ah-career-backend.onrender.com/docs)
- **API Gateway Health Check**: [https://ah-career-backend.onrender.com/health](https://ah-career-backend.onrender.com/health)
- **GitHub Repository**: [https://github.com/anasimam10/Career-OS](https://github.com/anasimam10/Career-OS)

---

## The Problem & Solution

### The Challenge
Pakistani youth constitute over 64% of the national population, yet face severe structural information friction:
- **Scattered Information**: University criteria, merit cutoffs, and scholarship deadlines are fragmented across dozens of provincial and institutional portals.
- **Unrealistic Advice**: Social media and viral videos create false expectations around tech salaries, entry requirements, and job availability.
- **Neglected Pathways**: Athletic opportunities, vocational tracks, and regional quotas are poorly documented and largely inaccessible to students outside major metropolitan hubs.

### The Career OS Solution
Career OS provides **one continuous, personalized operating system** that grounds every recommendation in verified Pakistani institutional data and labor market facts. Recommendations adapt to the student's:
1. **Education Stage**: Matric, FSc / A-Levels, Undergraduate, or Fresh Graduate
2. **Geographic Reality**: Province, city, local campuses, and regional quotas
3. **Verified Pathways**: 248 universities, 210 degree programs, and 22 curated career tracks
4. **Actionable Progression**: Deterministic 7-day trials, milestone tracking, and mock interviews

---

## Core System Features

1. **Personalized 7-Step Onboarding**: Establishes student baseline, educational stage, career motivations, and target cities.
2. **Career Reality Checks**: In-depth intelligence across 22 career pathways, including verified Pakistani starting-to-peak PKR salary bands, local employer demand, and work conditions.
3. **University & Degree Catalog**: Directory covering 248 universities and 210 degree programs across all provinces, including entrance test requirements (MDCAT, ECAT, NAT, USAT) and verified criteria.
4. **7-Day Career Trials**: Actionable, structured day-by-day micro-tasks allowing students to test-drive careers before committing years to a degree.
5. **Curated Learning Roadmaps**: Foundational and technical competency roadmaps mapped directly to in-demand career skills.
6. **Scholarships & Opportunities Registry**: Verified listings of national and provincial aid (HEC, PEEF, Ehsaas, Sindh HEC), corporate internships, and trainee programs.
7. **Sports & Athletic Pathways**: Structured sports directory covering PCB regional academies, departmental athletic trials (WAPDA, Armed Forces), and university sports quotas.
8. **Qwen Multi-Model Fallback Architecture**: Production AI services powered by Alibaba Cloud DashScope (`qwen3.6-plus` primary), with deterministic multi-model fallback and strict JSON schema output validation.
9. **Model Context Protocol (MCP)**: Strict tool-mediated retrieval barriers isolating LLM generation from hallucinating career figures, admissions criteria, or university stats.
10. **Interactive Mock Interviews**: Technical and behavioral interview simulation with domain-specific questions, structured rubric evaluations, and actionable feedback.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Framer Motion, Radix UI, Lucide Icons |
| **Backend** | FastAPI (Python 3.11+), SQLite (WAL mode + JSONType), SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| **AI & LLM Runtime** | Alibaba Cloud Model Studio / DashScope (`qwen3.6-plus` primary), Model Context Protocol (MCP) |
| **Data & Seed Engine** | Python ETL, 8 normalized seed datasets (Universities, Programs, Careers, Scholarships, Sports) |
| **Testing & Quality** | Pytest (806 passing tests), Playwright automated browser validation, ESLint, TypeScript compiler |
| **Cloud Deployment** | Vercel (Edge CDN Frontend), Render (Docker Containerized Backend) |

---

## Project Structure

```text
Career-OS/
├── BackEnd/
│   ├── ingestion/          # PKE data ingestion and deduplication pipeline
│   ├── knowledge_engine/   # Source registry and staging services
│   ├── models/             # SQLAlchemy ORM models
│   ├── prompts/            # Grounded system prompts and schema definitions
│   ├── repositories/       # Data access layer
│   ├── retrieval/          # Visibility rules and full-text retrieval
│   ├── routers/            # FastAPI API route controllers (14 endpoints)
│   ├── schemas/            # Pydantic v2 request/response contracts
│   ├── services/           # Business logic (AI, Journey, Opportunity, Interview)
│   ├── tests/              # 806 automated pytest unit & integration tests
│   ├── config.py           # Typed settings from environment variables
│   ├── database.py         # SQLAlchemy engine and WAL mode session factory
│   ├── main.py             # Application entrypoint and MCP SSE transport mounts
│   └── requirements.txt    # Production Python dependencies
│
├── Frontend/
│   ├── app/                # Next.js 14 App Router routes (11 feature pages)
│   ├── components/         # Reusable UI, Layout, Journey, Career, and Home components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # API client, session management, and utilities
│   ├── public/             # Static assets (Career OS logo, Hero visual)
│   └── package.json        # Frontend scripts and dependencies
│
├── Mcp/                    # Model Context Protocol servers (Career, Opportunity, PKE)
├── data/                   # Production seed datasets (JSON) and seed_db.py loader
├── .gitignore              # Multi-tier exclusion rules
├── README.md               # Project documentation
└── render.yaml             # Infrastructure-as-code deployment blueprint
```

---

## Local Setup & Quickstart

### Prerequisites
- **Node.js** 18+ and **npm** 9+
- **Python** 3.11+
- **Git**

### 1. Backend Setup


cd BackEnd

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and supply your DASHSCOPE_API_KEY (optional for mock/offline runs)

# Seed the database (from repository root)
cd ..
python data/seed_db.py

# Start the FastAPI server
cd BackEnd
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

*API will be available at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.*

### 2. Frontend Setup

cd Frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local

# Start the development server
npm run dev


*Application will be available at `http://localhost:3000`.*



## Verification & Test Suite

### Backend Test Suite (806 Tests)

cd BackEnd
.venv\Scripts\python -m pytest -q


### Data Integrity Suite (47 Tests)

cd BackEnd
.venv\Scripts\python -m pytest tests/test_data_integrity.py -q


### Frontend Code Quality
cd Frontend
npm run lint
npm run build