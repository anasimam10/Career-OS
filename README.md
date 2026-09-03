# Career OS
> **Pakistan Career Operating System** — AI-powered guidance, verifiable education pathways, and market realities tailored for Pakistani students.

Career OS bridges the information gap for students across Pakistan by uniting the **Pakistan Knowledge Engine (PKE)** with an intelligent **Qwen AI model chain**. It provides personalized academic roadmaps, accredited university pathways, reality checks on domestic job markets, verified scholarship and sports trial listings, and interactive AI mock interviews grounded in local industry requirements.

---

## Core Capabilities

- **Personalized Student Journey (`/journey`)**: Dynamic Next Best Action (NBA) engine with progressive milestone disclosure across five stages: High School → Career Discovery → Skill Building → University / Vocational → Entry-Level Career.
- **Pakistan Knowledge Engine (PKE)**: Ground-truth intelligence spanning 248 verified/validated Pakistani universities, degree programs, labor market telemetry, scholarships, and Pakistan Intellectual Capital (PIC) computer science faculty data.
- **Career Reality Check (`/careers/[slug]/reality-check`)**: Frank assessments of domestic job market saturation, entry barriers, salary brackets, and regional demand across Karachi, Lahore, Islamabad, and nationwide.
- **Interactive AI Mock Interviews (`/mock-interview`)**: Domain-specific behavioral and technical interview practice grounded in official career competencies and curriculum resources.
- **AI Career Coach (`/mentor`)**: Intelligent career advisory powered by Qwen, grounded in verified local opportunities and admission criteria.
- **Verified Opportunities Portal (`/opportunities`)**: Real-time matching for internships, scholarships, and entry-level positions from verified Pakistani entities.
- **Sports & Athletics Pathways (`/sports`)**: PCB, PFF, and POA athletic trials, sports board quotas, and university athletic scholarships.

---

## Technology Stack & Architecture

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database & ORM**: SQLite (WAL mode, foreign keys enabled) with SQLAlchemy 2.0
- **AI Model Chain (DashScope / Alibaba Cloud)**:
  1. `qwen3.7-plus` (Primary reasoning & synthesis)
  2. `qwen3.6-plus` (Availability fallback)
  3. `qwen-plus-2025-07-28` (Secondary fallback)
  4. `qwen3-vl-235b-a22b-thinking` (High-reasoning emergency fallback)
- **Protocol**: Model Context Protocol (MCP) servers mounted over Server-Sent Events (SSE)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS with dark-editorial aesthetic
- **Icons & Animation**: Lucide React, Framer Motion

---

## Data Provenance & Knowledge Engine

1. **Primary PKE Data (Authoritative)**: Hand-curated, verified Pakistani institutions (43 universities, degree programs, verified opportunities) with `verification_status: "VERIFIED"`. Primary records are authoritative and never overwritten by external ingestion.
2. **External Secondary Datasets (Enrichment)**: Integrated from official Higher Education Commission (HEC) statistics and the Pakistan Intellectual Capital CS Faculty research dataset. Enriched records are marked `verification_status: "VALIDATED"`.
3. **MCP Grounding**: Domain servers (`mcp/career`, `mcp/opportunity`, `mcp/pke`) deliver verifiable context to AI endpoints, ensuring responses are backed by primary sources.

---

## Project Structure

```
.
├── BackEnd/                    # FastAPI backend service
│   ├── config.py               # Centralized configuration & environment loader
│   ├── database.py             # SQLite engine & database migrations
│   ├── main.py                 # FastAPI application & router mounting
│   ├── Dockerfile              # Production Docker image (Python 3.11-slim)
│   ├── render.yaml             # Render deployment blueprint
│   ├── data/external/          # Secondary CSV datasets (HEC & PIC)
│   ├── knowledge_engine/       # PKE staging, sources & registries
│   ├── models/                 # SQLAlchemy data models
│   ├── routers/                # API endpoints (/journey, /careers, /students, etc.)
│   ├── schemas/                # Pydantic request & response contracts
│   ├── scripts/                # Reproducible data ingestion & expansion scripts
│   ├── services/               # Core business logic (AI, journey, NBA, progress)
│   └── tests/                  # Pytest test suite (778 tests)
├── Frontend/                   # Next.js 14 web application
│   ├── app/                    # App Router pages (/journey, /careers, /profile, etc.)
│   ├── components/             # Reusable UI components (career, journey, shared)
│   ├── hooks/                  # React hooks (useJourney, useOnboarding)
│   └── lib/                    # API client, TypeScript types, session manager
├── Mcp/                        # Model Context Protocol server definitions
├── data/                       # Seed JSON datasets and seeder scripts
├── Docs/                       # System architecture & research documentation
├── .env.example                # Documented environment variable template
├── render.yaml                 # Root Render deployment blueprint
└── README.md                   # Project documentation
```

---

## Getting Started / How to Run Locally

### Prerequisites
- Python 3.11+ (Python 3.13 supported)
- Node.js 18+ and npm
- Git

---

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd BackEnd

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env and configure your DASHSCOPE_API_KEY

# Initialize database schema and seed data
python -m data.seed_db

# Start development server
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- **Backend API**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`

---

### 2. Frontend Setup

```bash
# In a separate terminal, navigate to the frontend directory
cd Frontend

# Install dependencies
npm install

# Configure environment
cp ../.env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
# Set NEXT_PUBLIC_USE_MOCK=false to connect to the live backend

# Start development server
npm run dev
```
- **Frontend App**: `http://localhost:3000` (or `http://127.0.0.1:3000`)
- **Journey Route**: `http://localhost:3000/journey`
- **Careers Route**: `http://localhost:3000/careers`

---

## Deployment Guide

### Deploy Backend → Render

1. Connect your GitHub repository to [Render](https://render.com).
2. Render will automatically detect the root [`render.yaml`](file:///e:/Uni%20work/A&H%20Career/render.yaml) blueprint.
3. Configure the following environment variables in the Render Dashboard:
   - `DASHSCOPE_API_KEY`: Your Alibaba Cloud Model Studio API key.
   - `CORS_ORIGINS`: Your deployed Vercel domain (e.g. `https://your-frontend.vercel.app`).
   - `DATABASE_URL`: `sqlite:////data/ah_career.db` (utilizing Render's persistent disk mounted at `/data`).
4. The service automatically builds using [BackEnd/Dockerfile](file:///e:/Uni%20work/A&H%20Career/BackEnd/Dockerfile), binds to `0.0.0.0:${PORT:-8000}`, and pre-seeds the initial dataset.

### Deploy Frontend → Vercel

1. Connect your GitHub repository to [Vercel](https://vercel.com).
2. Set **Root Directory** to `Frontend`.
3. Set Framework Preset to **Next.js**.
4. Configure Environment Variables in the Vercel Dashboard:
   - `NEXT_PUBLIC_API_URL`: Your Render backend URL (e.g. `https://your-backend.onrender.com/api/v1`).
   - `NEXT_PUBLIC_USE_MOCK`: `false` (enables live backend mode).
5. Deploy. The production build (`npm run build`) executes cleanly with all 13 routes optimized.

---

## Running Tests

### Backend Automated Test Suite
```bash
cd BackEnd
pytest -v
```
*(778 tests passing, covering journey progression, student isolation, PKE data integrity, and mock interview contracts).*

### Frontend Typecheck & Build Validation
```bash
cd Frontend
npm run build
```

---

## Security & Privacy

- **Zero Committed Secrets**: The repository contains no production credentials, API keys, private tokens, or user database dumps.
- **Strict Git Exclusions**: All active `.env` files, certificates (`*.pem`, `*.key`), and SQLite database files (`*.db`) are ignored by `.gitignore`.
- **Student Isolation**: All multi-student actions enforce header-based ownership checks (`X-Student-Id`), guaranteeing strict tenant boundaries.
