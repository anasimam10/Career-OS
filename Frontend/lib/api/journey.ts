import { apiGet, apiPost } from "./client"
import { USE_MOCK } from "@/lib/mock"
import { MOCK_JOURNEY, MOCK_NBA } from "@/lib/mock/journey.mock"
import type { JourneyResponse, ProgressResponse, RoadmapResponse } from "@/lib/types/journey.types"

const MAX_VISIBLE_STEPS = 3

export async function getJourney(studentId?: number | string): Promise<JourneyResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 400))
    return {
      ...MOCK_JOURNEY,
      next_steps: (MOCK_JOURNEY.next_steps || []).slice(0, MAX_VISIBLE_STEPS),
    }
  }
  const endpoint = studentId ? `/journey/${studentId}` : "/journey"
  const headers = studentId ? { "X-Student-Id": String(studentId) } : undefined
  const data = await apiGet<JourneyResponse>(endpoint, { headers })
  return {
    ...data,
    next_steps: (data.next_steps || []).slice(0, MAX_VISIBLE_STEPS),
  }
}

export async function completeMilestone(
  studentId: number | string,
  milestoneId: number
): Promise<JourneyResponse> {
  return apiPost<JourneyResponse>(
    `/journey/${studentId}/milestones/${milestoneId}/complete`,
    {}
  )
}

export async function markProgress(milestoneId: number, studentId?: number): Promise<ProgressResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 600))
    return {
      new_stage: "SKILL_BUILDING",
      next_best_action: MOCK_JOURNEY.next_best_action || MOCK_NBA,
    }
  }
  const headers = studentId ? { "X-Student-Id": String(studentId) } : undefined
  return apiPost<ProgressResponse>(
    "/progress",
    {
      milestone_id: milestoneId,
      milestoneId: milestoneId,
      student_id: studentId,
      studentId: studentId,
      status: "completed",
    },
    { headers }
  )
}

export async function createRoadmap(careerSlug: string, targetStage: string): Promise<RoadmapResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 800))
    return {
      roadmap_id: 1,
      current_step: MOCK_JOURNEY.current_step || "",
      visible_steps: (MOCK_JOURNEY.next_steps || []).slice(0, MAX_VISIBLE_STEPS),
    }
  }
  return apiPost<RoadmapResponse>("/roadmap", {
    career_slug: careerSlug,
    target_stage: targetStage,
  })
}
