import { apiPost } from "./client"
import { USE_MOCK } from "@/lib/mock"
import { getMockCoachResponse } from "@/lib/mock/coach.mock"
import type { CoachChatPayload, CoachResponse } from "@/lib/types/coach.types"

export async function sendChatMessage(payload: CoachChatPayload): Promise<CoachResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 1500)) // simulate mentor thinking
    return getMockCoachResponse(payload.message)
  }
  return apiPost<CoachResponse>("/coach/chat", payload)
}
