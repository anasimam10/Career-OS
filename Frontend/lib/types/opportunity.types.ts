/**
 * Opportunity and opportunity-match types (Phase 7).
 * These align with the backend Pydantic schemas in schemas/shared.py and schemas/responses.py.
 */

export interface Opportunity {
  id: number
  type: "internship" | "job" | "scholarship" | "education"
  title: string
  organization: string | null
  location: string | null
  deadline: string | null
  required_skills: string[]
  description: string | null
  source_url: string | null
  last_verified: string | null
  data_freshness: string | null
}

export interface OpportunityMatch {
  opportunity_id: number
  title: string
  organization: string
  match_score: number
  match_reasons: string[]
  missing_requirements: string[]
  next_action: string
  deadline: string | null
  source_url: string
  data_freshness: string | null
}

export interface OpportunityMatchResponse {
  matches: OpportunityMatch[]
  data_quality: string
  summary: string | null
  note: string | null
  message: string | null
}

export interface OpportunityMatchRequest {
  city: string
  opportunity_type?: "internship" | "job"
  field?: string | null
  skills?: string[] | null
}
