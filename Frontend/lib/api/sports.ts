/**
 * Sports API (Phase 7).
 *
 * Endpoints:
 * - GET  /sports         — list (database only)
 * - POST /sports/match   — Pattern B AI-ranked matches
 */

import { apiGet, apiPost } from "./client"
import type {
  SportsOpportunity,
  SportsMatchRequest,
  SportsMatchResponse,
} from "@/lib/types/sports.types"

/** Build query string from optional filter values. */
function buildQuery(params: Record<string, string | undefined>): string {
  const entries: [string, string][] = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== ""
  ) as [string, string][]
  if (entries.length === 0) return ""
  return "?" + new URLSearchParams(entries).toString()
}

export interface SportsFilters {
  sport?: string
  city?: string
  type?: string
}

export async function getSports(
  filters?: SportsFilters
): Promise<SportsOpportunity[]> {
  const qs = buildQuery({
    sport: filters?.sport,
    city: filters?.city,
    type: filters?.type,
  })
  const data = await apiGet<
    SportsOpportunity[] | { sports_opportunities: SportsOpportunity[]; message: string }
  >(`/sports${qs}`)
  // Backend returns the §10 empty envelope when no records match.
  if (Array.isArray(data)) return data
  return data.sports_opportunities
}

export async function matchSports(
  request: SportsMatchRequest
): Promise<SportsMatchResponse> {
  return apiPost<SportsMatchResponse>("/sports/match", request)
}
