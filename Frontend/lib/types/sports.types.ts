/**
 * Sports opportunity and sports-match types (Phase 7).
 * These align with the backend Pydantic schemas in schemas/shared.py and schemas/responses.py.
 */

export interface SportsOpportunity {
  id: number
  sport: string
  type: "tournament" | "trial" | "scholarship" | "programme"
  title: string
  organization: string | null
  location: string | null
  deadline: string | null
  eligibility: Record<string, unknown>
  description: string | null
  source_url: string | null
  last_verified: string | null
  data_freshness: string | null
}

export interface SportsOpportunityMatch {
  opportunity_id: number
  sport: string
  title: string
  organization: string
  match_score: number
  eligibility_met: string[]
  eligibility_missing: string[]
  next_action: string
  deadline: string | null
  source_url: string
  data_freshness: string | null
}

export interface SportsMatchResponse {
  matches: SportsOpportunityMatch[]
  data_quality: string
  summary: string | null
  note: string | null
  message: string | null
}

export interface SportsMatchRequest {
  sport: string
  location?: string | null
  level?: string | null
}
