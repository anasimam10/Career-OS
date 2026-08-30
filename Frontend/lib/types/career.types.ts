export type DemandLevel = "HIGH" | "MEDIUM" | "LOW"
export type CompetitionLevel = "HIGH" | "MEDIUM" | "LOW"
export type DifficultyLevel = "HIGH" | "MEDIUM" | "LOW"
export type VerdictType = "GOOD_FIT" | "WORTH_EXPLORING" | "RECONSIDER"

export interface Career {
  slug: string
  name: string
  field: string
  demand_level: DemandLevel
  competition_level: CompetitionLevel
  difficulty_level: DifficultyLevel
  required_skills: string[]
  pk_opportunities: string[]
  top_pk_universities: string[]
  risks: string[]
  last_updated: string
}

export interface CareerListItem {
  slug: string
  name: string
  field: string
  demand_level: DemandLevel
}

export interface CareerReality {
  career_name: string
  demand_level: DemandLevel
  competition_level: CompetitionLevel
  difficulty_level: DifficultyLevel
  required_skills: string[]
  pk_opportunities: string[]
  risks: string[]
  rewards: string[]
  data_source: string
}

export interface CareerVerdict {
  verdict: VerdictType
  headline: string
  reasoning: string
  student_strengths_match: string[]
  gaps_to_address: string[]
  suggested_trial: string | null
}

export interface CareerRealityResponse {
  reality: CareerReality
  verdict: CareerVerdict
}

export interface TrialDay {
  day_range: string
  title: string
  tasks: string[]
}

export interface CareerTrialPlan {
  career_slug: string
  duration_days: number
  days: TrialDay[]
  reflection_prompt: string
}

export interface MotivationFactor {
  label: string
  value: number
}

export interface MotivationAnalysis {
  primary_motivation: string
  reflection_note: string
  recommendation: string
  factors: MotivationFactor[]
}
