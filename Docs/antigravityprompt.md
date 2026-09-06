# CAREER OS — SMART JOURNEY CTAs + UNIVERSITIES PAGE
## Antigravity Implementation Prompt
**Priority: P0 — both issues visible to judges on the two most important pages**

---

## READ BEFORE TOUCHING ANYTHING

Open and fully read these files first. Do not write a single line until you have:

1. `Frontend/app/journey/page.tsx` — understand the full milestone data structure the API returns. Specifically find: what fields each milestone object has, whether there is an `action_url`, `action_type`, `link`, or `cta` field in the API response. Write down the exact milestone object shape.

2. `Frontend/components/journey/MilestoneCard.tsx` (or wherever milestone cards are rendered) — find the exact JSX that renders the current "View Learning Roadmaps →" button. Find the `href` and label. This is what you are replacing.

3. `Frontend/lib/api.ts` or `Frontend/utils/api.ts` — find the base URL constant. You will need it for the universities page.

4. `BackEnd/routers/universities.py` — confirm the GET endpoint path, confirm it returns a list of university objects, and document the exact fields returned (name, province, city, type, ranking, programs, entry_test, merit — whatever is there). Do not assume. Read the actual router.

5. `BackEnd/models/university.py` or wherever the University model is defined — document every field name exactly.

6. `Frontend/app/` — list every existing route folder. Confirm `/universities` does NOT exist yet.

---

## TASK 1 — SMART CONTEXTUAL CTAs FOR JOURNEY MILESTONES

### The Problem
Every milestone shows the same "View Learning Roadmaps →" button pointing to `/opportunities`. This is wrong for almost every milestone:
- A "Create a README.md" task should link to GitHub, not Opportunities
- A "Practice a mock interview" task should link to `/mock-interview`
- A "Browse university programs" task should link to `/universities`
- A "Build a LinkedIn profile" task should link to LinkedIn
- A reflective task like "Write down your career goals" needs no link at all

### Design Decision: 3-Tier CTA Resolution System

Do NOT hardcode a simple title-to-URL map. Qwen generates personalized milestone titles that vary per student. Instead, implement a 3-tier resolution system in order of priority:

**Tier 1 — API field (highest priority)**
If the milestone object from the backend already includes an `action_url`, `cta_url`, `link`, or similar field, use it directly. Check the actual API response shape when you read the file. If it exists, use it. If it doesn't, skip to Tier 2.

**Tier 2 — Keyword pattern matching (primary approach)**
Analyze the milestone `title` and `description` fields using keyword patterns. This handles Qwen-generated titles that differ per student.

**Tier 3 — Phase-based fallback (safety net)**
If no keyword matches, fall back to a safe default based on the milestone's phase number.

---

### Implementation

Create this file: `Frontend/lib/milestoneCta.ts`

```typescript
export type CtaType = "internal" | "external" | "none";

export interface MilestoneCta {
  label: string;
  url: string;
  type: CtaType; // "external" opens in new tab with external icon
}

// ─── Tier 2: Keyword pattern matching ────────────────────────────────────────

interface PatternRule {
  keywords: string[];         // match any of these (case-insensitive)
  cta: MilestoneCta;
}

const PATTERN_RULES: PatternRule[] = [
  // GitHub / code / portfolio tasks
  {
    keywords: ["readme", "github", "repository", "repo", "push", "commit",
               "portfolio", "project", "deploy", "vercel", "netlify",
               "open source", "pull request", "clone"],
    cta: { label: "Open GitHub", url: "https://github.com", type: "external" },
  },

  // LinkedIn / professional profile tasks
  {
    keywords: ["linkedin", "professional profile", "network profile",
               "connect with professionals", "professional network"],
    cta: { label: "Open LinkedIn", url: "https://www.linkedin.com", type: "external" },
  },

  // CV / resume tasks
  {
    keywords: ["cv", "resume", "curriculum vitae", "cover letter",
               "job readiness", "ats", "application document"],
    cta: { label: "Check Job Readiness", url: "/job-readiness", type: "internal" },
  },

  // Mock interview tasks
  {
    keywords: ["mock interview", "interview practice", "interview prep",
               "practice interview", "interview question", "technical interview",
               "hr interview", "behavioral interview"],
    cta: { label: "Start Mock Interview", url: "/mock-interview", type: "internal" },
  },

  // University / degree tasks
  {
    keywords: ["university", "universities", "degree", "program", "admission",
               "entry test", "merit", "ecat", "mdcat", "sat", "nust",
               "lums", "iba", "pu", "ku", "ust", "fast", "nu-fast",
               "explore programs", "higher education", "hec", "bachelor"],
    cta: { label: "Browse Universities", url: "/universities", type: "internal" },
  },

  // Career exploration tasks
  {
    keywords: ["explore career", "career exploration", "discover career",
               "career path", "career options", "choose a career",
               "career interests", "career research"],
    cta: { label: "Explore Careers", url: "/careers", type: "internal" },
  },

  // Reality check / market research tasks
  {
    keywords: ["reality check", "market demand", "salary", "job market",
               "pkr", "earning potential", "career reality", "work conditions",
               "industry outlook", "market research"],
    cta: {
      label: "Run Reality Check",
      // Resolved dynamically with career slug if available — see below
      url: "/careers",
      type: "internal",
    },
  },

  // 7-day trial tasks
  {
    keywords: ["7-day trial", "7 day trial", "career trial", "trial week",
               "day 1", "day-by-day", "hands-on trial", "test drive"],
    cta: {
      label: "Start 7-Day Trial",
      url: "/careers",
      type: "internal",
    },
  },

  // Opportunities / internship / job application tasks
  {
    keywords: ["internship", "job application", "apply for", "scholarship",
               "opportunity", "fellowship", "apprenticeship", "rozee",
               "linkedin jobs", "submit application"],
    cta: { label: "Browse Opportunities", url: "/opportunities", type: "internal" },
  },

  // Learning / courses / skill building tasks
  {
    keywords: ["learn", "course", "tutorial", "skill", "practice exercise",
               "study", "resource", "roadmap", "upskill", "certification"],
    cta: { label: "Find Learning Resources", url: "/opportunities", type: "internal" },
  },

  // Project / build tasks (not GitHub-specific)
  {
    keywords: ["build a project", "create a project", "small project",
               "mini project", "exercise", "coding challenge", "project idea"],
    cta: { label: "Find Project Ideas", url: "/opportunities", type: "internal" },
  },

  // Profile / personal branding tasks
  {
    keywords: ["profile", "personal brand", "update your profile",
               "career portfolio", "complete your profile"],
    cta: { label: "View My Profile", url: "/profile", type: "internal" },
  },

  // Sports tasks
  {
    keywords: ["sports", "athletic", "cricket", "football", "badminton",
               "squash", "trial", "tryout", "sports scholarship"],
    cta: { label: "Browse Sports Opportunities", url: "/sports", type: "internal" },
  },

  // Reflection / planning tasks — no external link needed
  {
    keywords: ["reflect", "write down", "journal", "note", "plan your",
               "think about", "identify your goals", "set your goals",
               "decision", "finalize", "commit to"],
    cta: { label: "", url: "", type: "none" },
  },
];

// ─── Tier 3: Phase-based fallback ────────────────────────────────────────────

const PHASE_FALLBACKS: Record<number, MilestoneCta> = {
  1: { label: "Explore Careers", url: "/careers", type: "internal" },
  2: { label: "Browse Universities", url: "/universities", type: "internal" },
  3: { label: "Find Learning Resources", url: "/opportunities", type: "internal" },
  4: { label: "Check Job Readiness", url: "/job-readiness", type: "internal" },
};

// ─── Main resolver ─────────────────────────────────────────────────────────────

export function resolveMilestoneCta(
  milestone: {
    title: string;
    description?: string;
    phase?: number;
    // Add any API-provided CTA fields here if they exist:
    action_url?: string;
    action_label?: string;
    action_type?: string;
    link?: string;
  },
  careerSlug?: string | null
): MilestoneCta | null {
  // Tier 1: Use API-provided CTA if available
  if (milestone.action_url) {
    return {
      label: milestone.action_label || "Continue",
      url: milestone.action_url,
      type: (milestone.action_type as CtaType) || "internal",
    };
  }
  if (milestone.link) {
    const isExternal = milestone.link.startsWith("http");
    return {
      label: "Continue",
      url: milestone.link,
      type: isExternal ? "external" : "internal",
    };
  }

  // Tier 2: Keyword pattern matching
  const searchText = `${milestone.title} ${milestone.description || ""}`.toLowerCase();

  for (const rule of PATTERN_RULES) {
    if (rule.keywords.some((kw) => searchText.includes(kw.toLowerCase()))) {
      // For reality-check and trial milestones, inject career slug if known
      if (rule.cta.url === "/careers" && careerSlug) {
        if (searchText.includes("reality check")) {
          return { ...rule.cta, url: `/careers/${careerSlug}/reality-check` };
        }
        if (searchText.includes("trial")) {
          return { ...rule.cta, url: `/careers/${careerSlug}/trial` };
        }
      }
      // type: "none" means no link shown
      if (rule.cta.type === "none") return null;
      return rule.cta;
    }
  }

  // Tier 3: Phase fallback
  if (milestone.phase && PHASE_FALLBACKS[milestone.phase]) {
    return PHASE_FALLBACKS[milestone.phase];
  }

  // Final fallback: no CTA
  return null;
}
```

---

### Update the Milestone Card Component

Open the milestone card file. Find the current CTA button/link. Replace the entire CTA section with:

```tsx
import { resolveMilestoneCta } from "@/lib/milestoneCta";
import { ArrowUpRight, ExternalLink, CheckCircle2, Loader2 } from "lucide-react";
import Link from "next/link";

// Inside the component, after resolving journey data:
// Pass careerSlug from the parent (journeyData?.career_goal_slug || student?.career_slug)
const cta = resolveMilestoneCta(milestone, careerSlug);

// ── Active milestone CTA ────────────────────────────────────────────────────
{milestone.status === "active" && (
  <div className="flex flex-wrap items-center gap-3 mt-5 pt-4 border-t border-white/5">

    {/* Action link — only shown if CTA resolved and is not type "none" */}
    {cta && (
      cta.type === "external" ? (
        <a
          href={cta.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
        >
          {cta.label}
          <ExternalLink className="w-3.5 h-3.5" aria-label="opens in new tab" />
        </a>
      ) : (
        <Link
          href={cta.url}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
        >
          {cta.label}
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      )
    )}

    {/* Mark as completed button — always on the right */}
    <button
      onClick={() => onComplete(milestone.id)}
      disabled={completing}
      aria-label={`Mark "${milestone.title}" as completed`}
      className="ml-auto inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold px-4 py-2 rounded-lg transition-all"
    >
      {completing ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          Saving...
        </>
      ) : (
        "Mark as completed"
      )}
    </button>
  </div>
)}

// ── Completed state ──────────────────────────────────────────────────────────
{milestone.status === "completed" && (
  <div className="flex items-center gap-2 mt-4 text-emerald-400 text-sm font-medium">
    <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
    Completed
  </div>
)}

// ── Locked state — no CTA, no link ───────────────────────────────────────────
// (render nothing for locked milestones)
```

**Critical:** The action link and "Mark as completed" are two separate elements. The link sends them to do the work. The button marks it done when they return. Never merge these into one button.

---

### Pass careerSlug from the journey page

In `Frontend/app/journey/page.tsx`, after fetching journey data, extract the career slug:

```tsx
// After: const journeyData = await fetchJourney(studentId);
const careerSlug =
  journeyData?.career_goal_slug ||
  journeyData?.student?.career_goal_slug ||
  journeyData?.career_slug ||
  null;

// Pass it down to each milestone card:
<MilestoneCard
  key={milestone.id}
  milestone={milestone}
  careerSlug={careerSlug}
  onComplete={handleComplete}
  completing={completingId === milestone.id}
/>
```

Check the actual API response structure to find the correct field name for the student's chosen career slug. It may be under `journeyData.student.career_goal`, or `journeyData.career_slug`, or somewhere else. Read the API response carefully.

---

## TASK 2 — CREATE /universities PAGE

### The Problem
The landing page has an "Explore Universities" card/button that errors because no `/universities` route exists in the frontend. The backend already has the data — `GET /api/v1/universities` returns 248 Pakistani universities with ranking, programs, and location data. There is just no frontend page for it.

### Step 1: Verify the backend endpoint

Before building the frontend, make one direct fetch to the backend:

```bash
curl https://ah-career-backend.onrender.com/api/v1/universities | python3 -m json.tool | head -100
```

Document the exact shape of one university object. You need to know the real field names. Expected fields (verify all of these):
- `id`, `name`, `city`, `province`, `type` (Public/Private/Semi-Government)
- `ranking` or `hec_ranking` (may be null for some)
- `programs` (array of program objects or count)
- `entry_tests` (array of test names like ECAT, MDCAT, etc.)
- `established`, `website` (if available)

If the programs are a separate endpoint (`/api/v1/universities/{id}/programs`), note this — you may need to fetch them on demand, not upfront.

### Step 2: Create the universities page

Create file: `Frontend/app/universities/page.tsx`

This is a client component. Structure:

```tsx
"use client";

import { useState, useEffect, useMemo } from "react";
import { Search, MapPin, BookOpen, Award, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import Link from "next/link";

// ── Types — update field names to match actual API response ──────────────────
interface Program {
  name: string;
  duration?: string;
  degree_type?: string; // BS, MS, PhD, etc.
}

interface University {
  id: number;
  name: string;
  city: string;
  province: string;
  type: "Public" | "Private" | "Semi-Government";
  ranking?: number | null;      // HEC ranking
  hec_ranking?: number | null;  // alternate field name
  programs?: Program[];
  program_count?: number;
  entry_tests?: string[];
  merit_percentage?: number | null;
  website?: string | null;
  established?: number | null;
}

// ── Constants ────────────────────────────────────────────────────────────────
const PROVINCES = ["All Provinces", "Punjab", "Sindh", "KPK", "Balochistan", "Islamabad", "AJK", "Gilgit-Baltistan"];
const TYPES = ["All Types", "Public", "Private", "Semi-Government"];
const SORT_OPTIONS = [
  { value: "ranking", label: "By Ranking" },
  { value: "name", label: "A–Z" },
  { value: "programs", label: "Most Programs" },
];

export default function UniversitiesPage() {
  const [universities, setUniversities] = useState<University[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [province, setProvince] = useState("All Provinces");
  const [type, setType] = useState("All Types");
  const [sort, setSort] = useState("ranking");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "https://ah-career-backend.onrender.com";
    fetch(`${API_BASE}/api/v1/universities`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load universities");
        return r.json();
      })
      .then((data) => {
        // Handle both { universities: [...] } and [...] response shapes
        setUniversities(Array.isArray(data) ? data : data.universities || data.data || []);
        setLoading(false);
      })
      .catch(() => {
        setError("Couldn't load universities. Please try again.");
        setLoading(false);
      });
  }, []);

  // ── Filter + sort ──────────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    let result = universities.filter((u) => {
      const matchSearch =
        !search ||
        u.name.toLowerCase().includes(search.toLowerCase()) ||
        u.city?.toLowerCase().includes(search.toLowerCase());
      const matchProvince = province === "All Provinces" || u.province === province;
      const matchType = type === "All Types" || u.type === type;
      return matchSearch && matchProvince && matchType;
    });

    result.sort((a, b) => {
      if (sort === "ranking") {
        const ra = a.ranking ?? a.hec_ranking ?? 9999;
        const rb = b.ranking ?? b.hec_ranking ?? 9999;
        return ra - rb;
      }
      if (sort === "name") return a.name.localeCompare(b.name);
      if (sort === "programs") {
        const pa = a.program_count ?? a.programs?.length ?? 0;
        const pb = b.program_count ?? b.programs?.length ?? 0;
        return pb - pa;
      }
      return 0;
    });

    return result;
  }, [universities, search, province, type, sort]);

  const getRank = (u: University) => u.ranking ?? u.hec_ranking ?? null;
  const getProgCount = (u: University) => u.program_count ?? u.programs?.length ?? null;

  // ── Loading skeleton ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="h-8 w-64 bg-gray-800 rounded animate-pulse mb-2" />
        <div className="h-4 w-48 bg-gray-700 rounded animate-pulse mb-10" />
        <div className="grid gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-800/60 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  // ── Error state ────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-20 text-center">
        <p className="text-gray-400 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 border border-gray-700 hover:border-gray-500 text-gray-300 text-sm rounded-lg transition-colors"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">

      {/* ── Page header ──────────────────────────────────────────────────── */}
      <p className="text-xs font-semibold tracking-widest text-blue-400 uppercase mb-2">
        Universities
      </p>
      <h1 className="text-3xl font-bold text-white mb-1">
        Pakistani Universities
      </h1>
      <p className="text-gray-400 text-sm mb-8">
        {universities.length} universities · verified degree programs, merit thresholds, and entry tests
      </p>

      {/* ── Filters ──────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3 mb-6">
        {/* Search */}
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search universities or cities..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 focus:border-blue-500 focus:outline-none text-sm text-white placeholder-gray-500 pl-9 pr-4 py-2.5 rounded-lg transition-colors"
          />
        </div>

        {/* Province filter */}
        <select
          value={province}
          onChange={(e) => setProvince(e.target.value)}
          className="bg-gray-900 border border-gray-800 focus:border-blue-500 focus:outline-none text-sm text-white px-3 py-2.5 rounded-lg transition-colors"
        >
          {PROVINCES.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>

        {/* Type filter */}
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="bg-gray-900 border border-gray-800 focus:border-blue-500 focus:outline-none text-sm text-white px-3 py-2.5 rounded-lg transition-colors"
        >
          {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>

        {/* Sort */}
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="bg-gray-900 border border-gray-800 focus:border-blue-500 focus:outline-none text-sm text-white px-3 py-2.5 rounded-lg transition-colors"
        >
          {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      {/* ── Results count ─────────────────────────────────────────────────── */}
      <p className="text-xs text-gray-500 mb-4">
        Showing {filtered.length} of {universities.length} universities
      </p>

      {/* ── Empty filter state ────────────────────────────────────────────── */}
      {filtered.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <p>No universities match your filters.</p>
          <button
            onClick={() => { setSearch(""); setProvince("All Provinces"); setType("All Types"); }}
            className="mt-3 text-blue-400 text-sm hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* ── University list ───────────────────────────────────────────────── */}
      <div className="flex flex-col gap-2">
        {filtered.map((uni) => {
          const rank = getRank(uni);
          const progCount = getProgCount(uni);
          const isExpanded = expandedId === uni.id;
          const hasPrograms = uni.programs && uni.programs.length > 0;

          return (
            <div
              key={uni.id}
              className={`bg-gray-900/60 border transition-all duration-200 rounded-xl overflow-hidden ${
                isExpanded ? "border-blue-500/40" : "border-gray-800 hover:border-gray-700"
              }`}
            >
              {/* ── Card row (always visible) ─────────────────────────────── */}
              <button
                onClick={() => setExpandedId(isExpanded ? null : uni.id)}
                className="w-full flex items-center gap-4 px-5 py-4 text-left"
                aria-expanded={isExpanded}
              >
                {/* Ranking badge */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold ${
                  rank && rank <= 10
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    : rank && rank <= 50
                    ? "bg-blue-500/15 text-blue-400 border border-blue-500/25"
                    : "bg-gray-800 text-gray-500 border border-gray-700"
                }`}>
                  {rank ? `#${rank}` : "—"}
                </div>

                {/* Name + location */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">{uni.name}</p>
                  <p className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3 h-3" aria-hidden="true" />
                    {uni.city}{uni.city && uni.province ? ", " : ""}{uni.province}
                  </p>
                </div>

                {/* Type badge */}
                <span className={`flex-shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border ${
                  uni.type === "Public"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : uni.type === "Private"
                    ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                    : "bg-gray-700/50 text-gray-400 border-gray-600/30"
                }`}>
                  {uni.type}
                </span>

                {/* Programs count */}
                {progCount !== null && (
                  <span className="flex-shrink-0 flex items-center gap-1 text-xs text-gray-400">
                    <BookOpen className="w-3.5 h-3.5" aria-hidden="true" />
                    {progCount} programs
                  </span>
                )}

                {/* Expand chevron */}
                <span className="flex-shrink-0 text-gray-500">
                  {isExpanded
                    ? <ChevronUp className="w-4 h-4" />
                    : <ChevronDown className="w-4 h-4" />
                  }
                </span>
              </button>

              {/* ── Expanded detail ──────────────────────────────────────── */}
              {isExpanded && (
                <div className="px-5 pb-5 border-t border-gray-800/60">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">

                    {/* Merit threshold */}
                    {uni.merit_percentage !== null && uni.merit_percentage !== undefined && (
                      <div>
                        <p className="text-[11px] text-gray-500 uppercase tracking-wide mb-1">Min. Merit</p>
                        <p className="text-sm font-semibold text-white">{uni.merit_percentage}%</p>
                      </div>
                    )}

                    {/* Entry tests */}
                    {uni.entry_tests && uni.entry_tests.length > 0 && (
                      <div className="col-span-2">
                        <p className="text-[11px] text-gray-500 uppercase tracking-wide mb-1">Entry Tests</p>
                        <div className="flex flex-wrap gap-1.5">
                          {uni.entry_tests.map((test) => (
                            <span key={test} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded border border-gray-700">
                              {test}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Established */}
                    {uni.established && (
                      <div>
                        <p className="text-[11px] text-gray-500 uppercase tracking-wide mb-1">Established</p>
                        <p className="text-sm font-semibold text-white">{uni.established}</p>
                      </div>
                    )}
                  </div>

                  {/* Programs list */}
                  {hasPrograms && (
                    <div className="mt-4">
                      <p className="text-[11px] text-gray-500 uppercase tracking-wide mb-2">Programs</p>
                      <div className="flex flex-wrap gap-1.5">
                        {uni.programs!.slice(0, 12).map((prog, i) => (
                          <span key={i} className="text-xs bg-gray-800/80 text-gray-300 px-2.5 py-1 rounded-lg border border-gray-700/60">
                            {typeof prog === "string" ? prog : prog.name}
                          </span>
                        ))}
                        {uni.programs!.length > 12 && (
                          <span className="text-xs text-gray-500 px-2 py-1">
                            +{uni.programs!.length - 12} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Website link */}
                  {uni.website && (
                    <a
                      href={uni.website.startsWith("http") ? uni.website : `https://${uni.website}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 mt-4 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      Visit university website
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Back link ─────────────────────────────────────────────────────── */}
      <div className="mt-10 pt-6 border-t border-gray-800">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
          ← Back to home
        </Link>
      </div>
    </div>
  );
}
```

### Step 3: Fix the landing page button

Find the "Explore Universities" button/card on the homepage (`Frontend/app/page.tsx`). Change its `href` from whatever broken URL it currently has to `/universities`:

```tsx
// Find: wherever "Explore Universities" or similar text renders
// Change: the href/link destination to "/universities"
<Link href="/universities">Explore Universities</Link>
```

If it is rendered as a card with an `onClick` that routes somewhere, change the router.push call:
```tsx
router.push("/universities");
```

---

## TASK 3 — VERIFY BOTH FIXES END TO END

### Journey CTA verification

After implementing, log the resolved CTA for each active milestone to the browser console during development:

```tsx
// Temporary debug — remove before commit
console.log("[CTA Debug]", milestone.title, "→", resolveMilestoneCta(milestone, careerSlug));
```

Walk through these test scenarios:
- Milestone title contains "README" → should resolve to GitHub external link
- Milestone title contains "mock interview" → should resolve to `/mock-interview` internal
- Milestone title contains "career reality" → should resolve to `/careers/[slug]/reality-check` if slug known
- Milestone title contains "university" or "degree" → should resolve to `/universities` internal
- Milestone title contains "LinkedIn" → should resolve to LinkedIn external link
- Milestone with completed status → no CTA rendered at all
- Milestone with locked status → no CTA rendered at all
- External links open in a new browser tab (not same tab)
- Internal links use Next.js `<Link>` (no full page reload)

Remove the console.log before committing.

### Universities page verification

```bash
# 1. Check the backend returns data
curl https://ah-career-backend.onrender.com/api/v1/universities | python3 -c "import sys,json; d=json.load(sys.stdin); print(type(d), len(d) if isinstance(d,list) else len(d.get('universities',d.get('data',[]))))"

# 2. Check one university object shape
curl https://ah-career-backend.onrender.com/api/v1/universities | python3 -c "import sys,json; d=json.load(sys.stdin); u=d[0] if isinstance(d,list) else d.get('universities',d.get('data',[]))[0]; print(json.dumps(u,indent=2))"
```

Update the TypeScript interface and any field name references in the component to match the actual API response. The component is written assuming common field names — you must verify and correct every field name before shipping.

Manual test checklist:
- [ ] Landing page "Explore Universities" click → goes to `/universities` (no error)
- [ ] Universities page loads and shows university cards (not blank, not error state)
- [ ] Search by university name filters results in real time
- [ ] Province dropdown filters correctly
- [ ] Type dropdown (Public/Private) filters correctly
- [ ] Ranking sort shows top-ranked first
- [ ] A-Z sort alphabetizes correctly
- [ ] Clicking a university card expands it to show programs, entry tests, merit
- [ ] Top 10 ranked universities show amber badge
- [ ] External website link opens in new tab
- [ ] Mobile: filters stack vertically, cards are readable on 375px viewport
- [ ] No horizontal overflow on mobile

---

## BUILD AND TYPECHECK

```bash
cd Frontend && npx tsc --noEmit
cd Frontend && npm run build
```

Both must pass with 0 errors before committing.

The build output should now show 15+ routes including the new `/universities` static route.

---

## DO NOT TOUCH

- `BackEnd/` — no backend changes. Use the existing `/api/v1/universities` endpoint exactly as it is.
- Any existing journey page functionality that currently works — only replace the CTA rendering
- Framer Motion animations — do not add or remove
- Navbar, footer, color scheme — not in scope for this task
- Any page other than journey, home page button, and the new universities page

---

## REPORT FORMAT

When complete:
1. List every file created or modified
2. For the CTA system: paste the console.log output showing resolved CTAs for at least 5 different milestone titles from a real student session
3. For universities: paste the first university object from the actual API response (so field name mapping can be verified)
4. Build result — route count should be 15+ now
5. Any field names in the actual API that differed from what was assumed in the component (so the TypeScript interface can be confirmed correct)
6. Any milestone titles encountered in the live DB that fell through to Phase fallback (Tier 3) rather than matching a pattern — so patterns can be improved