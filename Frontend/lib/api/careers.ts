import { apiGet, apiPost } from "./client"
import { USE_MOCK } from "@/lib/mock"
import {
  MOCK_CAREER_LIST,
  MOCK_CAREERS,
  MOCK_REALITY_CHECK,
  MOCK_TRIAL_PLAN,
} from "@/lib/mock/careers.mock"
import type {
  CareerListItem,
  Career,
  CareerRealityResponse,
  CareerTrialPlan,
} from "@/lib/types/career.types"

// MOCK DATA — replace with real API when backend is ready
export async function getCareers(): Promise<CareerListItem[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 400))
    return MOCK_CAREER_LIST
  }
  return apiGet<CareerListItem[]>("/careers")
}

export async function getCareer(slug: string): Promise<Career> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300))
    const career = MOCK_CAREERS[slug]
    if (!career) throw new Error(`Career "${slug}" not found`)
    return career
  }
  return apiGet<Career>(`/careers/${slug}`)
}

export async function analyzeCareer(
  careerSlug: string
): Promise<CareerRealityResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 1200)) // simulate AI delay
    const result = MOCK_REALITY_CHECK[careerSlug] ?? MOCK_REALITY_CHECK["software-engineering"]
    return result
  }
  return apiPost<CareerRealityResponse>("/career/analyze", { career_slug: careerSlug })
}

export async function getTrialPlan(
  careerSlug: string
): Promise<CareerTrialPlan> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 1000))
    const plan = MOCK_TRIAL_PLAN[careerSlug] ?? MOCK_TRIAL_PLAN["software-engineering"]
    return plan
  }
  return apiPost<CareerTrialPlan>("/career/trial-plan", { career_slug: careerSlug })
}
