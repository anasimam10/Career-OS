import { apiGet, apiPut } from "./client"
import { USE_MOCK } from "@/lib/mock"
import { getSession, updateSession } from "@/lib/session"

export interface StudentProfileData {
  id: number
  name: string
  email: string
  city?: string | null
  education_stage: string
  career_goal?: string | null
  sports_interest?: string | null
  motivation_tags: string[]
  interests: string[]
  skills: Array<{ name: string; level: string }>
  job_readiness_score: number
  completed_milestone_ids: number[]
  next_best_action?: any
  created_at?: string | null
  updated_at?: string | null
}

export interface UpdateStudentProfilePayload {
  name?: string
  city?: string
  education_stage?: string
  career_goal?: string
  sports_interest?: string
  motivation_tags?: string[]
  interests?: string[]
  skills?: Array<{ name: string; level: string }>
}

const MOCK_PROFILE: StudentProfileData = {
  id: 1,
  name: "Demo Student",
  email: "demo@ahcareers.local",
  city: "Karachi",
  education_stage: "UNIVERSITY",
  career_goal: "software-engineering",
  sports_interest: "Cricket",
  motivation_tags: ["Tech Passion", "High Growth", "Market Demand"],
  interests: ["Software Development", "Machine Learning", "System Design"],
  skills: [
    { name: "Python", level: "intermediate" },
    { name: "Problem Solving", level: "intermediate" },
    { name: "Data Structures", level: "beginner" },
  ],
  job_readiness_score: 0.65,
  completed_milestone_ids: [1, 2],
  next_best_action: {
    title: "Complete Mock Technical Interview",
    description: "Validate your technical interview readiness with real Qwen evaluation.",
    stage: "UNIVERSITY",
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

export async function getStudentProfile(): Promise<StudentProfileData> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 400))
    const s = getSession()
    return {
      ...MOCK_PROFILE,
      name: s?.name || MOCK_PROFILE.name,
      city: s?.city || MOCK_PROFILE.city,
    }
  }

  return apiGet<StudentProfileData>("/students/me")
}

export async function updateStudentProfile(
  payload: UpdateStudentProfilePayload
): Promise<StudentProfileData> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 600))
    if (payload.city || payload.name) {
      updateSession({
        city: payload.city,
        name: payload.name,
      })
    }
    return {
      ...MOCK_PROFILE,
      ...payload,
    }
  }

  const result = await apiPut<StudentProfileData>("/students/me", payload)
  if (result) {
    updateSession({
      name: result.name,
      city: result.city || undefined,
    })
  }
  return result
}
