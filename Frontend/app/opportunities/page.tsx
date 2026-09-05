"use client"

import { useState, useEffect, useCallback } from "react"
import { Search, ExternalLink, MapPin, Clock, Sparkles } from "lucide-react"
import { getOpportunities, matchOpportunities } from "@/lib/api/opportunities"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { EmptyState } from "@/components/shared/EmptyState"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { PageTransition } from "@/components/layout/PageTransition"
import { getSession } from "@/lib/session"
import type { Opportunity, OpportunityMatch, OpportunityMatchResponse } from "@/lib/types/opportunity.types"

const PAKISTANI_CITIES = [
  "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad",
  "Multan", "Peshawar", "Quetta", "Sialkot", "Gujranwala",
  "Hyderabad", "Abbottabad", "Other",
]

const TYPE_OPTIONS = [
  { value: "", label: "All Types" },
  { value: "internship", label: "Internships" },
  { value: "job", label: "Jobs" },
  { value: "scholarship", label: "Scholarships" },
  { value: "education", label: "Education" },
]

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [selectedType, setSelectedType] = useState("")

  // Matching state — defaults to active student's persisted city
  const [matchLoading, setMatchLoading] = useState(false)
  const [matchResult, setMatchResult] = useState<OpportunityMatchResponse | null>(null)
  const [matchError, setMatchError] = useState<string | null>(null)
  const [matchCity, setMatchCity] = useState(() => {
    if (typeof window !== "undefined") {
      const session = getSession()
      return session?.city || "Karachi"
    }
    return "Karachi"
  })
  const [matchType, setMatchType] = useState<"internship" | "job">("internship")

  const loadOpportunities = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const list = await getOpportunities(
        selectedType ? { type: selectedType } : undefined
      )
      setOpportunities(list)
    } catch {
      setError("Couldn't load opportunities right now.")
    } finally {
      setLoading(false)
    }
  }, [selectedType])

  useEffect(() => {
    loadOpportunities()
  }, [loadOpportunities])

  const handleMatch = async () => {
    try {
      setMatchLoading(true)
      setMatchError(null)
      const result = await matchOpportunities({
        city: matchCity,
        opportunity_type: matchType,
      })
      setMatchResult(result)
    } catch {
      setMatchError("Couldn't match opportunities right now.")
    } finally {
      setMatchLoading(false)
    }
  }

  const filtered = opportunities.filter((o) =>
    o.title.toLowerCase().includes(search.toLowerCase()) ||
    (o.organization ?? "").toLowerCase().includes(search.toLowerCase())
  )

  return (
    <PageTransition>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 space-y-10">
        <SectionHeader
          badge="Opportunities"
          title="Pakistani Internships, Jobs & Scholarships"
          subtitle="Browse verified opportunities or let AI rank the best matches for your profile."
        />

        {/* AI Match Section */}
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="h-5 w-5 text-primary" />
              AI-Powered Opportunity Match
            </CardTitle>
            <CardDescription>
              Find matches for your profile.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <label className="text-xs font-semibold text-muted-foreground mb-1 block">City</label>
                <select
                  value={matchCity}
                  onChange={(e) => setMatchCity(e.target.value)}
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
                >
                  {PAKISTANI_CITIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <label className="text-xs font-semibold text-muted-foreground mb-1 block">Type</label>
                <div className="flex gap-2">
                  {(["internship", "job"] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setMatchType(t)}
                      className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition-all ${
                        matchType === t
                          ? "bg-primary text-primary-foreground shadow-sm"
                          : "bg-muted text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {t.charAt(0).toUpperCase() + t.slice(1)}s
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <Button onClick={handleMatch} disabled={matchLoading} className="w-full sm:w-auto">
              {matchLoading ? "Matching..." : "Find My Best Matches"}
            </Button>
          </CardContent>
          {matchError && (
            <CardContent>
              <ErrorState message={matchError} />
            </CardContent>
          )}
          {matchResult && (
            <CardContent className="space-y-4">
              {matchResult.matches.length === 0 ? (
                <p className="text-sm text-muted-foreground">{matchResult.message || "No matching opportunities found."}</p>
              ) : (
                <>
                  {matchResult.summary && (
                    <p className="text-sm text-foreground">{matchResult.summary}</p>
                  )}
                  {matchResult.note && (
                    <p className="text-xs text-muted-foreground italic">{matchResult.note}</p>
                  )}
                  <div className="space-y-3">
                    {matchResult.matches.map((m) => (
                      <MatchCard key={m.opportunity_id} match={m} />
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Data quality: <Badge variant="outline" className="text-[10px]">{matchResult.data_quality}</Badge>
                  </p>
                </>
              )}
            </CardContent>
          )}
        </Card>

        {/* Browse All Section */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-foreground">Browse All Opportunities</h2>

          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="relative w-full sm:max-w-md">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by title or organisation..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {TYPE_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setSelectedType(t.value)}
                  className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition-all ${
                    selectedType === t.value
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pt-2" aria-busy="true">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="h-56 rounded-[12px] border border-border/60 bg-muted/20 p-6 animate-pulse flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="h-4 w-20 bg-muted rounded" />
                    <div className="h-5 w-4/5 bg-muted rounded" />
                    <div className="h-3.5 w-full bg-muted rounded" />
                  </div>
                  <div className="h-4 w-1/2 bg-muted rounded" />
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-12 space-y-3">
              <p className="text-sm text-muted-foreground">{error}</p>
              <Button variant="outline" size="sm" onClick={() => loadOpportunities()}>
                Try again
              </Button>
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              title="No opportunities found"
              description="Try adjusting your filters or check back soon for new verified opportunities."
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {filtered.map((opp) => (
                <OpportunityCard key={opp.id} opportunity={opp} />
              ))}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}

function OpportunityCard({ opportunity: o }: { opportunity: Opportunity }) {
  const typeColors: Record<string, string> = {
    internship: "bg-blue-100 text-blue-800",
    job: "bg-emerald-100 text-emerald-800",
    scholarship: "bg-purple-100 text-purple-800",
    education: "bg-amber-100 text-amber-800",
  }

  return (
    <Card className="hover:shadow-card-hover transition-all border-border/80">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2 mb-1">
          <Badge variant="outline" className={`text-[11px] ${typeColors[o.type] || ""}`}>
            {o.type}
          </Badge>
          {o.data_freshness === "unverified" && (
            <Badge variant="outline" className="text-[10px] text-amber-600 border-amber-300">
              Unverified
            </Badge>
          )}
        </div>
        <CardTitle className="text-base leading-tight">{o.title}</CardTitle>
        {o.organization && (
          <CardDescription className="font-medium">{o.organization}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-2 text-xs text-muted-foreground">
        {o.location && (
          <div className="flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5" />
            <span>{o.location}</span>
          </div>
        )}
        {o.deadline && (
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>Deadline: {new Date(o.deadline).toLocaleDateString("en-PK", { day: "numeric", month: "short", year: "numeric" })}</span>
          </div>
        )}
        {o.required_skills.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {o.required_skills.slice(0, 4).map((s) => (
              <Badge key={s} variant="secondary" className="text-[10px]">{s}</Badge>
            ))}
            {o.required_skills.length > 4 && (
              <Badge variant="secondary" className="text-[10px]">+{o.required_skills.length - 4}</Badge>
            )}
          </div>
        )}
      </CardContent>
      {o.source_url && (
        <CardFooter className="pt-0">
          <a
            href={o.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            View Source <ExternalLink className="h-3 w-3" />
          </a>
        </CardFooter>
      )}
    </Card>
  )
}

function MatchCard({ match: m }: { match: OpportunityMatch }) {
  const scorePercent = Math.round(m.match_score * 100)

  return (
    <Card className="border-border/60">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm font-bold">{m.title}</CardTitle>
          <Badge
            variant={scorePercent >= 70 ? "success" : scorePercent >= 40 ? "warning" : "outline"}
            className="text-xs font-bold"
          >
            {scorePercent}% match
          </Badge>
        </div>
        <CardDescription className="text-xs">{m.organization}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        {m.match_reasons.length > 0 && (
          <div>
            <span className="font-semibold text-emerald-700">Matched: </span>
            <span className="text-muted-foreground">{m.match_reasons.join(", ")}</span>
          </div>
        )}
        {m.missing_requirements.length > 0 && (
          <div>
            <span className="font-semibold text-amber-700">Missing: </span>
            <span className="text-muted-foreground">{m.missing_requirements.join(", ")}</span>
          </div>
        )}
        <p className="text-foreground font-medium pt-1">{m.next_action}</p>
        {m.deadline && (
          <p className="text-muted-foreground">
            Deadline: {new Date(m.deadline).toLocaleDateString("en-PK", { day: "numeric", month: "short", year: "numeric" })}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
