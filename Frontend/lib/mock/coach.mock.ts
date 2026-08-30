import type { CoachResponse } from "@/lib/types/coach.types"

export const MOCK_COACH_RESPONSES: Record<string, CoachResponse> = {
  default: {
    message:
      "Based on your profile, you're at a great point to start exploring Software Engineering seriously. Your interest in technology is genuine, and that's the most important foundation. Here's what I'd suggest focusing on this week.",
    quick_actions: [
      "What should I do next?",
      "Am I ready for an internship?",
      "Help me choose between two fields",
    ],
    suggested_resource: null,
  },
  next_step: {
    message:
      "Your next step is clear: start with Python basics. It's the single most valuable skill you can build right now, and it unlocks everything else — data science, web development, automation. Spend 3–4 hours this week on the official Python tutorial at python.org.",
    quick_actions: [
      "How long will Python take to learn?",
      "What comes after Python?",
      "Should I do a Python course or self-study?",
    ],
    suggested_resource: null,
  },
  internship: {
    message:
      "Looking at your current stage, you're not quite ready for a competitive internship yet — and that's completely normal. You need two more things first: a completed beginner project (something you built yourself, no matter how small) and basic Git knowledge. Once you have those, I'll help you find and apply to internships that match your level.",
    quick_actions: [
      "What kind of project should I build?",
      "How do I learn Git?",
      "Show me entry-level opportunities",
    ],
    suggested_resource: null,
  },
}

export function getMockCoachResponse(message: string): CoachResponse {
  const lower = message.toLowerCase()
  if (lower.includes("next") || lower.includes("do")) return MOCK_COACH_RESPONSES.next_step
  if (lower.includes("intern")) return MOCK_COACH_RESPONSES.internship
  return MOCK_COACH_RESPONSES.default
}
