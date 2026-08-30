import { apiGet, apiPost } from "./client"
import { USE_MOCK } from "@/lib/mock"
import { MOCK_JOURNEY } from "@/lib/mock/journey.mock"
import type { JourneyResponse, ProgressResponse, RoadmapResponse } from "@/lib/types/journey.types"

const MAX_VISIBLE_STEPS = 3

export async function getJourney(): Promise<JourneyResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 400))
    return {
      ...MOCK_JOURNEY,
      next_steps: MOCK_JOURNEY.next_steps.slice(0, MAX_VISIBLE_STEPS),
    }
  }
  const data = await apiGet<JourneyResponse>("/journey")
  // Architecture rule: never show more than 3 visible steps
  return { ...data, next_steps: data.next_steps.slice(0, MAX_VISIBLE_STEPS) }
}

export async function markProgress(milestoneId: number): Promise<ProgressResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 600))
    return {
      new_stage: "SKILL_BUILDING",
      next_best_action: MOCK_JOURNEY.next_best_action,
    }
  }
  return apiPost<ProgressResponse>("/progress", { milestone_id: milestoneId, status: "done" })
}

export async function createRoadmap(careerSlug: string, targetStage: string): Promise<RoadmapResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 800))
    return {
      roadmap_id: 1,
      current_step: MOCK_JOURNEY.current_step,
      visible_steps: MOCK_JOURNEY.next_steps.slice(0, MAX_VISIBLE_STEPS),
    }
  }
  return apiPost<RoadmapResponse>("/roadmap", {
    career_slug: careerSlug,
    target_stage: targetStage,
  })
}
