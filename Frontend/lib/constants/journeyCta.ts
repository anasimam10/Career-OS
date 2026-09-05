export interface MilestoneCTA {
  label: string
  href: string
  icon?: string
}

/**
 * Prompt-specified exact milestone CTA lookup table.
 * Each milestone has its own dedicated destination route and contextual action label.
 */
export const MILESTONE_CTA_MAP: Record<string, { label: string; href: string; icon?: string }> = {
  // Phase 1 — Discovery & Exploration
  "Explore Career Pathways": {
    label: "Browse Careers",
    href: "/careers",
  },
  "Career Reality Check": {
    label: "Run Reality Check",
    href: "/careers", // smart fallback; dynamically replaced if slug available
  },
  "7-Day Career Trial": {
    label: "Start 7-Day Trial",
    href: "/careers", // smart fallback; dynamically replaced if slug available
  },

  // Phase 2 — Academic & Foundations
  "Explore Degrees & Programs": {
    label: "Browse Universities",
    href: "/careers", // smart fallback; dynamically replaced if slug available
  },
  "Core Technical Foundation": {
    label: "Find Learning Resources",
    href: "/opportunities",
  },

  // Phase 3 — Real-World Experience
  "Build Practical Projects": {
    label: "Find Project Briefs",
    href: "/opportunities",
  },
  "Apply to Student Opportunities": {
    label: "Browse Opportunities",
    href: "/opportunities",
  },

  // Phase 4 — Job Readiness
  "Resume & CV Preparation": {
    label: "Check Job Readiness",
    href: "/job-readiness",
  },
  "Targeted Mock Interview": {
    label: "Start Mock Interview",
    href: "/mock-interview",
  },
  "Decision & Career Launch": {
    label: "View My Profile",
    href: "/profile",
  },
}

/**
 * Additional mappings for database and mock milestone titles to guarantee 100% resolution.
 */
const EXTENDED_TITLE_MAP: Record<string, { label: string; href: string }> = {
  "Explore careers that match your interests": {
    label: "Browse Careers",
    href: "/careers",
  },
  "Complete a Career Reality Check": {
    label: "Run Reality Check",
    href: "/careers",
  },
  "Complete the 7-Day Career Trial": {
    label: "Start 7-Day Trial",
    href: "/careers",
  },
  "Compare your top career options": {
    label: "Browse Careers",
    href: "/careers",
  },
  "Finalize your career direction": {
    label: "View My Profile",
    href: "/profile",
  },
  "Learn the first required skill for your career": {
    label: "Find Learning Resources",
    href: "/opportunities",
  },
  "Practice with small exercises": {
    label: "Find Learning Resources",
    href: "/opportunities",
  },
  "Review the required skills for your career": {
    label: "Browse Careers",
    href: "/careers",
  },
  "Build your first project": {
    label: "Find Project Briefs",
    href: "/opportunities",
  },
  "Document and share your project": {
    label: "Find Project Briefs",
    href: "/opportunities",
  },
  "Prepare a professional CV": {
    label: "Check Job Readiness",
    href: "/job-readiness",
  },
  "Become internship-ready": {
    label: "Browse Opportunities",
    href: "/opportunities",
  },
  "Complete your final-year project": {
    label: "Find Project Briefs",
    href: "/opportunities",
  },
  "Practice for interviews": {
    label: "Start Mock Interview",
    href: "/mock-interview",
  },
  "Build a weekly job-search routine": {
    label: "Browse Opportunities",
    href: "/opportunities",
  },
  "Apply to verified entry-level roles & opportunities": {
    label: "Browse Opportunities",
    href: "/opportunities",
  },
  "Verify your final job readiness score": {
    label: "Check Job Readiness",
    href: "/job-readiness",
  },
  "Set 90-day goals for your first job": {
    label: "View My Profile",
    href: "/profile",
  },
}

/**
 * Smart slug-aware CTA resolver that checks exact table keys, extended DB titles,
 * and semantic fallback to ensure no generic or broken route is ever rendered.
 */
export function resolveMilestoneCTA(
  title: string,
  careerSlug?: string | null
): MilestoneCTA {
  const cleanSlug = careerSlug ? careerSlug.trim().toLowerCase().replace(/\s+/g, "-") : null

  // 1. Direct prompt specification match
  if (MILESTONE_CTA_MAP[title]) {
    const base = MILESTONE_CTA_MAP[title]
    if (title === "Career Reality Check" || title === "Explore Degrees & Programs") {
      return {
        label: base.label,
        href: cleanSlug ? `/careers/${cleanSlug}/reality-check` : "/careers",
      }
    }
    if (title === "7-Day Career Trial") {
      return {
        label: base.label,
        href: cleanSlug ? `/careers/${cleanSlug}/trial` : "/careers",
      }
    }
    return { ...base }
  }

  // 2. Extended database title match
  if (EXTENDED_TITLE_MAP[title]) {
    const base = EXTENDED_TITLE_MAP[title]
    if (title.includes("Reality Check")) {
      return {
        label: base.label,
        href: cleanSlug ? `/careers/${cleanSlug}/reality-check` : "/careers",
      }
    }
    if (title.includes("Career Trial") || title.includes("7-Day")) {
      return {
        label: base.label,
        href: cleanSlug ? `/careers/${cleanSlug}/trial` : "/careers",
      }
    }
    return { ...base }
  }

  // 3. Normalized semantic fallback
  const t = title.toLowerCase()

  if (t.includes("reality check")) {
    return {
      label: "Run Reality Check",
      href: cleanSlug ? `/careers/${cleanSlug}/reality-check` : "/careers",
    }
  }

  if (t.includes("7-day") || t.includes("trial")) {
    return {
      label: "Start 7-Day Trial",
      href: cleanSlug ? `/careers/${cleanSlug}/trial` : "/careers",
    }
  }

  if (t.includes("degree") || t.includes("program") || t.includes("university")) {
    return {
      label: "Browse Universities",
      href: cleanSlug ? `/careers/${cleanSlug}/reality-check` : "/careers",
    }
  }

  if (t.includes("mock") || t.includes("interview")) {
    return {
      label: "Start Mock Interview",
      href: "/mock-interview",
    }
  }

  if (t.includes("resume") || t.includes("cv") || t.includes("readiness")) {
    return {
      label: "Check Job Readiness",
      href: "/job-readiness",
    }
  }

  if (t.includes("project") || t.includes("brief")) {
    return {
      label: "Find Project Briefs",
      href: "/opportunities",
    }
  }

  if (t.includes("opportunity") || t.includes("scholarship") || t.includes("internship") || t.includes("routine")) {
    return {
      label: "Browse Opportunities",
      href: "/opportunities",
    }
  }

  if (t.includes("skill") || t.includes("foundation") || t.includes("learn") || t.includes("exercise")) {
    return {
      label: "Find Learning Resources",
      href: "/opportunities",
    }
  }

  if (t.includes("launch") || t.includes("direction") || t.includes("profile") || t.includes("decision") || t.includes("goal")) {
    return {
      label: "View My Profile",
      href: "/profile",
    }
  }

  return {
    label: "Browse Careers",
    href: "/careers",
  }
}
