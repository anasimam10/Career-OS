import { apiPost } from "./client"
import { USE_MOCK } from "@/lib/mock"
import { MOCK_ONBOARDING_RESPONSE } from "@/lib/mock/onboarding.mock"
import type { OnboardingPayload, OnboardingResponse } from "@/lib/types/student.types"

export async function submitOnboarding(payload: OnboardingPayload): Promise<OnboardingResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 1200)) // simulate AI processing
    return MOCK_ONBOARDING_RESPONSE
  }
  return apiPost<OnboardingResponse>("/onboarding", payload)
}
