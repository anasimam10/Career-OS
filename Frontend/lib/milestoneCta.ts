export type CtaType = "internal" | "external" | "none";

export interface MilestoneCta {
  label: string;
  url: string;
  type: CtaType; // "external" opens in new tab with external icon
}

// ─── Tier 2: Keyword pattern matching ────────────────────────────────────────

interface PatternRule {
  keywords: string[]; // match any of these (case-insensitive)
  cta: MilestoneCta;
}

const PATTERN_RULES: PatternRule[] = [
  // Reflection / planning / decision tasks — checked first so phrases like "commit to" or "finalize" don't trigger code rules
  {
    keywords: [
      "reflect",
      "write down",
      "journal",
      "note",
      "plan your",
      "think about",
      "identify your goals",
      "set your goals",
      "set 90-day goals",
      "decision",
      "finalize",
      "commit to",
    ],
    cta: { label: "", url: "", type: "none" },
  },

  // CV / resume tasks — checked before project/code tasks
  {
    keywords: [
      "cv",
      "resume",
      "curriculum vitae",
      "cover letter",
      "job readiness",
      "ats",
      "application document",
      "professional cv",
    ],
    cta: { label: "Check Job Readiness", url: "/job-readiness", type: "internal" },
  },

  // Mock interview tasks
  {
    keywords: [
      "mock interview",
      "interview practice",
      "interview prep",
      "practice interview",
      "interview question",
      "technical interview",
      "hr interview",
      "behavioral interview",
      "practice for interviews",
      "interview",
    ],
    cta: { label: "Start Mock Interview", url: "/mock-interview", type: "internal" },
  },

  // Reality check / market research tasks
  {
    keywords: [
      "reality check",
      "market demand",
      "salary",
      "job market",
      "pkr",
      "earning potential",
      "career reality",
      "work conditions",
      "industry outlook",
      "market research",
    ],
    cta: {
      label: "Run Reality Check",
      url: "/careers",
      type: "internal",
    },
  },

  // 7-day trial tasks
  {
    keywords: [
      "7-day trial",
      "7 day trial",
      "career trial",
      "trial week",
      "day 1",
      "day-by-day",
      "hands-on trial",
      "test drive",
      "trial",
    ],
    cta: {
      label: "Start 7-Day Trial",
      url: "/careers",
      type: "internal",
    },
  },

  // University / degree tasks
  {
    keywords: [
      "university",
      "universities",
      "degree",
      "program",
      "admission",
      "entry test",
      "merit",
      "ecat",
      "mdcat",
      "sat",
      "nust",
      "lums",
      "iba",
      "pu",
      "ku",
      "ust",
      "fast",
      "nu-fast",
      "explore programs",
      "higher education",
      "hec",
      "bachelor",
    ],
    cta: { label: "Browse Universities", url: "/universities", type: "internal" },
  },

  // Career exploration tasks
  {
    keywords: [
      "explore career",
      "career exploration",
      "discover career",
      "career path",
      "career options",
      "choose a career",
      "career interests",
      "career research",
      "compare your top career",
    ],
    cta: { label: "Explore Careers", url: "/careers", type: "internal" },
  },

  // GitHub / code / repository / portfolio tasks
  {
    keywords: [
      "readme",
      "github",
      "repository",
      "repo",
      "push",
      "git commit",
      "portfolio",
      "deploy",
      "vercel",
      "netlify",
      "open source",
      "pull request",
      "clone",
    ],
    cta: { label: "Open GitHub", url: "https://github.com", type: "external" },
  },

  // LinkedIn / professional profile tasks
  {
    keywords: [
      "linkedin",
      "professional profile",
      "network profile",
      "connect with professionals",
      "professional network",
    ],
    cta: { label: "Open LinkedIn", url: "https://www.linkedin.com", type: "external" },
  },

  // Opportunities / internship / job application tasks
  {
    keywords: [
      "internship",
      "job application",
      "apply for",
      "scholarship",
      "opportunity",
      "fellowship",
      "apprenticeship",
      "rozee",
      "linkedin jobs",
      "submit application",
      "job-search",
      "job search",
      "entry-level",
    ],
    cta: { label: "Browse Opportunities", url: "/opportunities", type: "internal" },
  },

  // Learning / courses / skill building tasks
  {
    keywords: [
      "learn",
      "course",
      "tutorial",
      "skill",
      "practice exercise",
      "study",
      "resource",
      "roadmap",
      "upskill",
      "certification",
      "exercises",
    ],
    cta: { label: "Find Learning Resources", url: "/opportunities", type: "internal" },
  },

  // Project / build tasks (not GitHub-specific)
  {
    keywords: [
      "build a project",
      "create a project",
      "small project",
      "mini project",
      "exercise",
      "coding challenge",
      "project idea",
      "project briefs",
      "first project",
      "project",
    ],
    cta: { label: "Find Project Ideas", url: "/opportunities", type: "internal" },
  },

  // Profile / personal branding tasks
  {
    keywords: [
      "profile",
      "personal brand",
      "update your profile",
      "career portfolio",
      "complete your profile",
    ],
    cta: { label: "View My Profile", url: "/profile", type: "internal" },
  },

  // Sports tasks
  {
    keywords: [
      "sports",
      "athletic",
      "cricket",
      "football",
      "badminton",
      "squash",
      "trial",
      "tryout",
      "sports scholarship",
    ],
    cta: { label: "Browse Sports Opportunities", url: "/sports", type: "internal" },
  },
];

// ─── Tier 3: Phase-based fallback ────────────────────────────────────────────

const PHASE_FALLBACKS: Record<number, MilestoneCta> = {
  1: { label: "Explore Careers", url: "/careers", type: "internal" },
  2: { label: "Browse Universities", url: "/universities", type: "internal" },
  3: { label: "Find Learning Resources", url: "/opportunities", type: "internal" },
  4: { label: "Check Job Readiness", url: "/job-readiness", type: "internal" },
  5: { label: "Browse Opportunities", url: "/opportunities", type: "internal" },
};

function matchesKeyword(text: string, keyword: string): boolean {
  const kw = keyword.trim().toLowerCase();
  if (kw.length <= 4) {
    const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(`(^|[^a-zA-Z0-9])${escaped}([^a-zA-Z0-9]|$)`, "i").test(text);
  }
  return text.includes(kw);
}

// ─── Main resolver ─────────────────────────────────────────────────────────────

export function resolveMilestoneCta(
  milestone: {
    title: string;
    description?: string;
    phase?: number;
    // API-provided CTA fields
    action_url?: string | null;
    action_label?: string | null;
    action_type?: string | null;
    link?: string | null;
  },
  careerSlug?: string | null
): MilestoneCta | null {
  // Tier 1: Use API-provided CTA if available
  if (milestone.action_url) {
    const isExternal = milestone.action_url.startsWith("http");
    const inferredType: CtaType =
      milestone.action_type === "external" || milestone.action_type === "internal" || milestone.action_type === "none"
        ? milestone.action_type
        : isExternal
        ? "external"
        : "internal";

    if (inferredType === "none") return null;

    return {
      label: milestone.action_label || "Continue",
      url: milestone.action_url,
      type: inferredType,
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
  const cleanSlug = careerSlug ? careerSlug.trim().toLowerCase().replace(/\s+/g, "-") : null;

  for (const rule of PATTERN_RULES) {
    if (rule.keywords.some((kw) => matchesKeyword(searchText, kw))) {
      // For reality-check and trial milestones, inject career slug if known
      if (rule.cta.url === "/careers" && cleanSlug) {
        if (searchText.includes("reality check")) {
          return { ...rule.cta, url: `/careers/${cleanSlug}/reality-check` };
        }
        if (searchText.includes("trial")) {
          return { ...rule.cta, url: `/careers/${cleanSlug}/trial` };
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
