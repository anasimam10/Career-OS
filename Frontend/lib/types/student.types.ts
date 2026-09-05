import type { EducationStage } from "./journey.types"

export interface Skill {
  name: string
  level: "beginner" | "intermediate" | "advanced"
}

export interface OnboardingPayload {
  education_stage: EducationStage
  interests: string[]
  career_interests: string[]
  sports_interest: string | null
  motivation_tags: string[]
  skills: Skill[]
  city: string
  province?: string
}

export interface OnboardingResponse {
  profile_updated: boolean
  next_best_action: import("./journey.types").NextBestAction
  student_id?: number
}


export interface StudentProfile {
  student_id: number
  name: string
  education_stage: EducationStage
  career_goal: string | null
  sports_interest: string | null
  city: string | null
  interests: string[]
  skills: Skill[]
}
