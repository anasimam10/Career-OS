/**
 * Opportunities API (Phase 7).
 *
 * Endpoints:
 * - GET  /opportunities         — list (database only)
 * - POST /opportunities/match   — Pattern B AI-ranked matches
 */

import { apiGet, apiPost } from "./client"
import type {
  Opportunity,
  OpportunityMatchRequest,
  OpportunityMatchResponse,
} from "@/lib/types/opportunity.types"

/** Build query string from optional filter values. */
function buildQuery(params: Record<string, string | undefined>): string {
  const entries: [string, string][] = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== ""
  ) as [string, string][]
  if (entries.length === 0) return ""
  return "?" + new URLSearchParams(entries).toString()
}

export interface OpportunityFilters {
  type?: string
  city?: string
  field?: string
  skills?: string
}

export async function getOpportunities(
  filters?: OpportunityFilters
): Promise<Opportunity[]> {
  const qs = buildQuery({
    type: filters?.type,
    city: filters?.city,
    field: filters?.field,
    skills: filters?.skills,
  })
  const data = await apiGet<Opportunity[] | { opportunities: Opportunity[]; message: string }>(
    `/opportunities${qs}`
  )
  // Backend returns the §10 empty envelope when no records match.
  if (Array.isArray(data)) return data
  return data.opportunities
}

export async function matchOpportunities(
  request: OpportunityMatchRequest
): Promise<OpportunityMatchResponse> {
  return apiPost<OpportunityMatchResponse>("/opportunities/match", request)
}
