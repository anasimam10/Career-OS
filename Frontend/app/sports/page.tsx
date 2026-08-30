"use client"

import { useState, useEffect } from "react"
import { Search, ExternalLink, MapPin, Clock, Sparkles } from "lucide-react"
import { getSports, matchSports } from "@/lib/api/sports"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { EmptyState } from "@/components/shared/EmptyState"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { PageTransition } from "@/components/layout/PageTransition"
import type { SportsOpportunity, SportsOpportunityMatch, SportsMatchResponse } from "@/lib/types/sports.types"

const SPORT_OPTIONS = ["", "Cricket", "Football", "Badminton", "Hockey", "Tennis", "Squash", "Swimming", "Basketball"]
const TYPE_OPTIONS = [
  { value: "", label: "All Types" },
  { value: "tournament", label: "Tournaments" },
  { value: "trial", label: "Trials" },
  { value: "scholarship", label: "Scholarships" },
  { value: "programme", label: "Programmes" },
]

export default function SportsPage() {
  const [sports, setSports] = useState<SportsOpportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSport, setSelectedSport] = useState("")
  const [selectedType, setSelectedType] = useState("")

  // Matching state
  const [matchLoading, setMatchLoading] = useState(false)
  const [matchResult, setMatchResult] = useState<SportsMatchResponse | null>(null)
  const [matchError, setMatchError] = useState<string | null>(null)
  const [matchSport, setMatchSport] = useState("Cricket")
  const [matchLocation, setMatchLocation] = useState("")
  const [matchLevel, setMatchLevel] = useState("")

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        setError(null)
        const list = await getSports({
          sport: selectedSport || undefined,
          type: selectedType || undefined,
        })
        setSports(list)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load sports")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [selectedSport, selectedType])

  const handleMatch = async () => {
    try {
      setMatchLoading(true)
      setMatchError(null)
      const result = await matchSports({
        sport: matchSport,
        location: matchLocation || undefined,
        level: matchLevel || undefined,
      })
      setMatchResult(result)
    } catch (err) {
      setMatchError(err instanceof Error ? err.message : "Failed to match sports")
    } finally {
      setMatchLoading(false)
    }
  }

  return (
    <PageTransition>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 space-y-10">
        <SectionHeader
          badge="Sports"
          title="Sports Opportunities in Pakistan"
          subtitle="Tournaments, trials, scholarships, and university sports programmes — all verified."
        />

        {/* AI Match Section */}
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="h-5 w-5 text-primary" />
              AI Sports Match
            </CardTitle>
            <CardDescription>
              Find sports opportunities that match your sport, location, and level.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <label className="text-xs font-semibold text-muted-foreground mb-1 block">Sport</label>
                <div className="flex flex-wrap gap-2">
                  {SPORT_OPTIONS.filter(Boolean).map((s) => (
                    <button
                      key={s}
                      onClick={() => setMatchSport(s)}
                      className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-all ${
                        matchSport === s
                          ? "bg-primary text-primary-foreground shadow-sm"
                          : "bg-muted text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <label className="text-xs font-semibold text-muted-foreground mb-1 block">Location (optional)</label>
                <Input
                  value={matchLocation}
                  onChange={(e) => setMatchLocation(e.target.value)}
                  placeholder="e.g. Karachi, Lahore"
                />
              </div>
              <div className="flex-1">
                <label className="text-xs font-semibold text-muted-foreground mb-1 block">Level (optional)</label>
                <Input
                  value={matchLevel}
                  onChange={(e) => setMatchLevel(e.target.value)}
                  placeholder="e.g. beginner, intermediate, advanced"
                />
              </div>
            </div>
            <Button onClick={handleMatch} disabled={matchLoading} className="w-full sm:w-auto">
              {matchLoading ? "Matching..." : "Find Sports Matches"}
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
                <p className="text-sm text-muted-foreground">{matchResult.message || "No matching sports opportunities found."}</p>
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
                      <SportsMatchCard key={m.opportunity_id} match={m} />
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
          <h2 className="text-xl font-bold text-foreground">Browse All Sports Opportunities</h2>

          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {SPORT_OPTIONS.map((s) => (
                <button
                  key={s || "all"}
                  onClick={() => setSelectedSport(s)}
                  className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition-all ${
                    selectedSport === s
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {s || "All Sports"}
                </button>
              ))}
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
            <LoadingState message="Loading sports opportunities..." />
          ) : error ? (
            <ErrorState message={error} />
          ) : sports.length === 0 ? (
            <EmptyState
              title="No sports opportunities found"
              description="Try adjusting your filters or check back soon for new verified opportunities."
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {sports.map((s) => (
                <SportsCard key={s.id} sport={s} />
              ))}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}

function SportsCard({ sport: s }: { sport: SportsOpportunity }) {
  const typeColors: Record<string, string> = {
    tournament: "bg-blue-100 text-blue-800",
    trial: "bg-emerald-100 text-emerald-800",
    scholarship: "bg-purple-100 text-purple-800",
    programme: "bg-amber-100 text-amber-800",
  }

  return (
    <Card className="hover:shadow-card-hover transition-all border-border/80">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2 mb-1">
          <Badge variant="outline" className={`text-[11px] ${typeColors[s.type] || ""}`}>
            {s.type}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">{s.sport}</Badge>
        </div>
        <CardTitle className="text-base leading-tight">{s.title}</CardTitle>
        {s.organization && (
          <CardDescription className="font-medium">{s.organization}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-2 text-xs text-muted-foreground">
        {s.location && (
          <div className="flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5" />
            <span>{s.location}</span>
          </div>
        )}
        {s.deadline && (
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>Deadline: {new Date(s.deadline).toLocaleDateString("en-PK", { day: "numeric", month: "short", year: "numeric" })}</span>
          </div>
        )}
        {s.eligibility && Object.keys(s.eligibility).length > 0 && (
          <div className="pt-1">
            <span className="font-semibold">Eligibility: </span>
            <span>{Object.entries(s.eligibility).map(([k, v]) => `${k}: ${v}`).join(", ")}</span>
          </div>
        )}
      </CardContent>
      {s.source_url && (
        <CardFooter className="pt-0">
          <a
            href={s.source_url}
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

function SportsMatchCard({ match: m }: { match: SportsOpportunityMatch }) {
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
        <CardDescription className="text-xs">{m.organization} — {m.sport}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        {m.eligibility_met.length > 0 && (
          <div>
            <span className="font-semibold text-emerald-700">Eligibility met: </span>
            <span className="text-muted-foreground">{m.eligibility_met.join(", ")}</span>
          </div>
        )}
        {m.eligibility_missing.length > 0 && (
          <div>
            <span className="font-semibold text-amber-700">Missing: </span>
            <span className="text-muted-foreground">{m.eligibility_missing.join(", ")}</span>
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
