# Career OS

Career OS is a Pakistan-focused AI Career Operating System that helps students discover career pathways, evaluate careers realistically, explore universities and opportunities, build learning journeys, access sports pathways, and prepare through AI-powered mock interviews.

---

## Key Features

- **Personalized Student Onboarding**: Guided multi-step profiling capturing education stage, city, career goals, skills, and sports interests.
- **Career Discovery & Reality Check**: Objective labor market demand analysis, market saturation indices, and entry bottlenecks across Pakistani hubs.
- **University & Program Pathways**: Comprehensive coverage of 248 Pakistani universities, degree prerequisites, and faculty specializations.
- **Pakistan-Specific Opportunities**: Grounded registry of verified domestic internships, scholarships, and fellowships.
- **Sports & Athletics Pathways**: PCB, PFF, and POA athletic trials, quota allocations, and university sports scholarships.
- **Learning Resources**: Curated technical and foundational curriculum linked directly to career milestones.
- **Grounded AI Career Mentor**: Intelligent conversational guidance powered by Qwen and grounded in verified Pakistani institutional data.
- **AI Mock Interviews**: Career-specific technical and behavioral interview practice with deterministic scoring, question grounding, and answer security.
- **Student Journey & Progress**: Real-time Next Best Action (NBA) engine with progressive disclosure across educational stages.
- **Talk to Alumni (Coming Soon)**: Verified 1-on-1 mentorship connecting prospective students with graduates from top Pakistani universities.

---

## Technology

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Framer Motion
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0, SQLite (WAL mode, single-writer safe)
- **AI Runtime**: Alibaba Cloud DashScope Qwen Model Chain (`qwen3.7-plus` primary with multi-model availability fallbacks)
- **Architecture**: Model Context Protocol (MCP) servers mounted over SSE, Pakistan Knowledge Engine (PKE)

---

## Data & Trust

- **Source-Backed Data**: Built upon official Higher Education Commission (HEC) public university data, Pakistan Intellectual Capital (PIC) CS faculty research, and verified domestic opportunity registries.
- **PKE Provenance Architecture**: Strict separation between authoritative primary PKE records (`VERIFIED`) and secondary external enrichment (`VALIDATED`). External datasets act as secondary evidence and never overwrite or downgrade primary facts.
- **Strictly Grounded AI**: Qwen serves as the sole runtime AI; AI outputs are strictly grounded against PKE records to prevent hallucination.

---

## Run Locally

### 1. Backend

```bash
cd BackEnd
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd Frontend
npm install
npm run dev
```
- **Frontend App**: `http://localhost:3000`

---

## Deployment

- **Frontend**: Deployed on [Vercel](https://career-os-seven-flame.vercel.app)
- **Backend**: Deployed on [Render](https://ah-career-backend.onrender.com) (with persistent disk at `/data`)

---

## Repository

- **Public GitHub**: [https://github.com/anasimam10/Career-OS](https://github.com/anasimam10/Career-OS)
