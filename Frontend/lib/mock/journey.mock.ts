import type { JourneyResponse, NextBestAction } from "@/lib/types/journey.types"

export const MOCK_NBA: NextBestAction = {
  title: "Build Your Python Fundamentals",
  description:
    "Python is widely used across software development, data analysis, and automation. Completing foundational concepts this week gives you a practical base for subsequent milestones.",
  steps: [
    "Install Python 3.12 and VS Code (30 minutes)",
    "Complete introductory syntax and data types exercises",
    "Write and run your first 3 simple script programs",
  ],
  estimated_time: "3–4 hours this week",
  why_this_matters: "This supports the software engineering path you're currently exploring.",
  stage: "SKILL_BUILDING",
}

export const MOCK_JOURNEY: JourneyResponse = {
  stage: "CAREER_DISCOVERY",
  current_step: "Explore and decide on a career field",
  next_steps: [
    {
      title: "Complete Career Reality Check",
      description: "Run the AI analysis for Software Engineering to see if it matches your profile.",
      stage: "CAREER_DISCOVERY",
      estimated_duration: "15 minutes",
    },
    {
      title: "Start 7-Day Trial",
      description: "Test the field for one week before committing.",
      stage: "CAREER_DECISION",
      estimated_duration: "7 days",
    },
    {
      title: "Learn Python Basics",
      description: "The foundational skill for software engineering.",
      stage: "SKILL_BUILDING",
      estimated_duration: "2 weeks",
    },
  ],
  next_best_action: MOCK_NBA,
}
