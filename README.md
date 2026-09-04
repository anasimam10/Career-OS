# Career OS
### Pakistan's Career Operating System

Career OS is a Pakistan-focused Career Operating System that guides students from high school uncertainty to their first job through a structured, personalized journey.

---

## Who It Is For

Career OS is built for **students, university applicants, and early-career individuals across Pakistan** who need structured, reliable direction during critical educational and career transitions.

---

## The Real Problem

Students today are not suffering from a lack of career information—they are overwhelmed by it. 

Every day, young Pakistanis face a barrage of YouTube career videos, viral social media advice, peer pressure, family and societal expectations, salary hype, and conflicting opinions. University program criteria and scholarship deadlines remain scattered across dozens of disjointed portals.

The fundamental issue is clear:
> **Students have too much scattered information, but no clear, personalized pathway from where they are now to where they want to go.**

Without personalized guidance, students experience FOMO, make high-stakes academic choices based on rumors or short-term trends, and remain uncertain about what practical step to take next.

---

## The Solution

Career OS replaces fragmented searches with **one continuous, personalized operating system**. 

Rather than offering generic advice, the platform takes into account a student's:
- **Education Stage** (Matric, FSc/A-Levels, Undergraduate, Fresh Graduate)
- **City & Region** (access to local campuses and regional opportunities)
- **Interests & Motivations**
- **Baseline Skills**
- **Career Goals & Milestone Progress**

Career OS turns career decision-making into a structured, step-by-step roadmap with clear next actions.

---

## The End-to-End Pathway

Career OS is designed to guide a student along an end-to-end journey from high school toward their first job:

```
HIGH SCHOOL / INTERMEDIATE
  ↓
FIELD & CAREER EXPLORATION
  ↓
REALITY CHECK (Market Demand & PKR Salaries)
  ↓
UNIVERSITY & PROGRAM DISCOVERY
  ↓
7-DAY CAREER TRIALS
  ↓
SKILL DEVELOPMENT & LEARNING RESOURCES
  ↓
SCHOLARSHIPS & OPPORTUNITIES
  ↓
EXPERIENCE & SPORTS PATHWAYS
  ↓
INTERVIEW PREPARATION (Qwen-Powered Mock Screening)
  ↓
FIRST JOB
```

---

## What We Built

We engineered a responsive, full-stack web application tailored specifically to the realities of Pakistan's education and labor market:

- **Personalized Onboarding & Student Journey**: Multi-step profiling that establishes the student's baseline, displays their current stage, and tracks progress toward milestones.
- **Career Discovery & Reality Checks**: Grounded Pakistan labor market intelligence across 22 career pathways, providing realistic local employer expectations, actual work conditions, and starting-to-peak PKR salary bands.
- **University & Program Directory**: Searchable directory covering 248 Pakistani universities and 174 degree programs across all provinces, including verified entrance test requirements.
- **Practical 7-Day Career Trials**: Actionable, day-by-day micro-tasks allowing students to test-drive real industry work before investing years into a degree.
- **Curated Learning Resources**: Technical and foundational skill roadmaps mapped directly to in-demand career competencies.
- **Scholarships & Opportunities Registry**: Verified listings of national and regional financial aid (HEC, PEEF, Ehsaas), corporate internships, and trainee programs.
- **Sports & Athletic Pathways**: Dedicated listings across PCB regional academies, departmental athletic trials (WAPDA, Armed Forces), and university sports quotas.
- **Course-Aware Mock Interview System**: Interactive technical interview practice powered by Alibaba Qwen, providing domain-specific questions, structured rubric evaluations, and actionable feedback for skill gaps.
- **Talk to Alumni (Future Preview)**: A frontend entry point previewing future verified mentorship and community networking with graduates from top Pakistani institutions.

---

## The Differentiator

Career OS does not simply provide more information; it **organizes that information into a personalized pathway and actionable next steps**. 

It transforms anxiety and uncertainty into a coherent, confidence-building roadmap from the classroom to the workforce.

---

## Live Links

- **Live Application (Vercel)**: [https://career-os-seven-flame.vercel.app](https://career-os-seven-flame.vercel.app)
- **Backend API (Render)**: [https://ah-career-backend.onrender.com](https://ah-career-backend.onrender.com)
- **Interactive API Docs (Swagger)**: [https://ah-career-backend.onrender.com/docs](https://ah-career-backend.onrender.com/docs)
- **API Health Check**: [https://ah-career-backend.onrender.com/health](https://ah-career-backend.onrender.com/health)
- **GitHub Repository**: [https://github.com/anasimam10/Career-OS](https://github.com/anasimam10/Career-OS)

---

## Quick Local Setup

### Backend (FastAPI + Python 3.11+)
```bash
cd BackEnd
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
*API runs at `http://127.0.0.1:8000` with Swagger docs at `/docs`.*

### Frontend (Next.js 14 + Node 18+)
```bash
cd Frontend
npm install
npm run dev
```
*Application runs at `http://localhost:3000`.*
