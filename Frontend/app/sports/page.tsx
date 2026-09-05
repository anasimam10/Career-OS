"use client"

import { useState, useEffect } from "react"
import { Search, ExternalLink, MapPin, Clock, Sparkles, Trophy } from "lucide-react"
import { getSports, matchSports } from "@/lib/api/sports"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { EmptyState } from "@/components/shared/EmptyState"
import { PageTransition } from "@/components/layout/PageTransition"
import { getSession } from "@/lib/session"
import type { SportsOpportunity, SportsOpportunityMatch, SportsMatchResponse } from "@/lib/types/sports.types"
import { cn } from "@/lib/utils/cn"

const SPORT_OPTIONS = ["All", "Cricket", "Football", "Badminton", "Hockey", "Tennis", "Squash", "Swimming", "Basketball"]
const TYPE_OPTIONS = [
  { value: "all", label: "All Types" },
  { value: "tournament", label: "Tournaments" },
  { value: "trial", label: "Trials" },
  { value: "scholarship", label: "Scholarships" },
  { value: "programme", label: "Programmes" },
]

export default function SportsPage() {
  const [sports, setSports] = useState<SportsOpportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSport, setSelectedSport] = useState("All")
  const [selectedType, setSelectedType] = useState("all")

  // Matching state — initialized from student's session if available
  const [matchLoading, setMatchLoading] = useState(false)
  const [matchResult, setMatchResult] = useState<SportsMatchResponse | null>(null)
  const [matchError, setMatchError] = useState<string | null>(null)
  const [matchSport, setMatchSport] = useState("Cricket")
  const [matchLocation, setMatchLocation] = useState(() => {
    if (typeof window !== "undefined") {
      const session = getSession()
      return session?.city || ""
    }
    return ""
  })
  const [matchLevel, setMatchLevel] = useState("")

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        setError(null)
        const list = await getSports({
          sport: selectedSport !== "All" ? selectedSport : undefined,
          type: selectedType !== "all" ? selectedType : undefined,
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
      <div className="bg-[#05080E] min-h-screen pt-12 pb-24 relative overflow-hidden">
        {/* High energy background abstract */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-amber-500/10 blur-[150px] rounded-full pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-red-500/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="mx-auto max-w-7xl px-4 sm:px-6 space-y-12 relative z-10">
          
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-4 py-1.5 text-xs font-bold tracking-widest text-amber-500 uppercase shadow-[0_0_15px_rgba(245,158,11,0.2)]">
              <Trophy className="h-3.5 w-3.5" />
              <span>Athletic Intelligence</span>
            </div>
            <h1 className="text-3xl md:text-5xl font-extrabold text-[#F1F5F9] tracking-tight">
              Sports opportunities in <span className="text-[#3B82F6]">Pakistan</span>
            </h1>
            <p className="text-slate-400 max-w-2xl mx-auto text-lg">
              Tournaments, trials, scholarships, and university sports programmes across Pakistan.
            </p>
          </div>

          {/* AI Match Section */}
          <div className="rounded-[2rem] border border-amber-500/20 bg-slate-900/60 overflow-hidden backdrop-blur-md shadow-2xl">
            <div className="bg-amber-500/5 border-b border-amber-500/10 p-6 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20 text-amber-500">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">AI Sports Opportunity Match</h2>
                <p className="text-sm text-amber-200/60">Find the right stage for your skills.</p>
              </div>
            </div>
            
            <div className="p-6 md:p-8 space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block">Target Sport</label>
                  <select
                    value={matchSport}
                    onChange={(e) => setMatchSport(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all"
                  >
                    {SPORT_OPTIONS.filter(s => s !== "All").map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block">Location (City)</label>
                  <input
                    type="text"
                    placeholder="e.g. Lahore, Karachi"
                    value={matchLocation}
                    onChange={(e) => setMatchLocation(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all placeholder:text-slate-600"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block">Current Level</label>
                  <select
                    value={matchLevel}
                    onChange={(e) => setMatchLevel(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all"
                  >
                    <option value="">Any Level</option>
                    <option value="school">School</option>
                    <option value="college">College</option>
                    <option value="university">University</option>
                    <option value="club">Club</option>
                    <option value="professional">Professional</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-800/80">
                <button
                  onClick={handleMatch}
                  disabled={matchLoading || !matchSport}
                  className="px-8 py-3.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold uppercase tracking-wider text-sm transition-all shadow-[0_0_20px_rgba(245,158,11,0.3)] disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
                >
                  {matchLoading ? "Scanning Database..." : "Run AI Match"}
                </button>
              </div>

              {matchError && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
                  {matchError}
                </div>
              )}

              {matchResult && (
                <div className="mt-8 pt-8 border-t border-slate-800/80 animate-in fade-in slide-in-from-bottom-4">
                  <div className="flex items-center gap-3 mb-6">
                    <h3 className="text-xl font-bold text-white">AI Analysis & Matches</h3>
                    <span className="px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase border border-emerald-500/30">
                      {matchResult.matches.length} Found
                    </span>
                  </div>
                  
                  <p className="text-slate-300 bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 text-sm leading-relaxed mb-8">
                    {matchResult.summary || matchResult.message || "Match analysis complete."}
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {matchResult.matches.map((match: SportsOpportunityMatch, idx: number) => (
                      <div key={idx} className="rounded-2xl border border-amber-500/20 bg-slate-800/80 p-5 flex flex-col relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="flex justify-between items-start mb-4 relative z-10">
                          <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-400 text-[10px] font-bold uppercase tracking-wider">
                            Match Score: {match.match_score}/10
                          </span>
                        </div>
                        <h4 className="font-bold text-white text-lg mb-2 relative z-10">{match.title}</h4>
                        <div className="text-sm text-slate-400 space-y-1.5 mb-4 relative z-10">
                          <div className="flex items-center gap-1.5">
                            <MapPin className="h-3.5 w-3.5 text-slate-500" /> {match.organization}
                          </div>
                          {match.deadline && (
                            <div className="flex items-center gap-1.5">
                              <Clock className="h-3.5 w-3.5 text-slate-500" /> {new Date(match.deadline).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                        <p className="text-xs text-amber-200/70 border-t border-amber-500/20 pt-3 mt-auto relative z-10">
                          {match.next_action}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Database Explorer */}
          <div className="space-y-6 pt-12">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-white uppercase italic">Full Database</h2>
              <div className="h-px bg-slate-800 flex-1" />
            </div>

            <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-slate-900/60 p-4 sm:p-6 rounded-2xl border border-slate-800 backdrop-blur-md">
              <div className="flex flex-wrap gap-2 w-full md:w-auto">
                {SPORT_OPTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSelectedSport(s)}
                    className={cn(
                      "rounded-lg px-4 py-2 text-[10px] font-bold uppercase tracking-widest transition-all",
                      selectedSport === s
                        ? "bg-amber-500 text-slate-950 shadow-[0_0_15px_rgba(245,158,11,0.4)]"
                        : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
                    )}
                  >
                    {s}
                  </button>
                ))}
              </div>

              <div className="flex gap-2 w-full md:w-auto">
                {TYPE_OPTIONS.map((t) => (
                  <button
                    key={t.value}
                    onClick={() => setSelectedType(t.value)}
                    className={cn(
                      "rounded-lg px-4 py-2 text-[10px] font-bold uppercase tracking-widest transition-all",
                      selectedType === t.value
                        ? "bg-slate-700 text-white border border-slate-600"
                        : "bg-transparent text-slate-500 border border-slate-800 hover:border-slate-600 hover:text-slate-300"
                    )}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="pt-8"><LoadingState message="Loading sports opportunities..." /></div>
            ) : error ? (
              <div className="pt-8"><ErrorState message={error} /></div>
            ) : sports.length === 0 ? (
              <div className="pt-8"><EmptyState title="No opportunities found" description="Try adjusting your filters." /></div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {sports.map((sport) => (
                  <div key={sport.id} className="group flex flex-col rounded-2xl border border-slate-800 bg-slate-900/40 overflow-hidden hover:border-amber-500/50 transition-all hover:bg-slate-900/80 backdrop-blur-sm">
                    <div className="p-6 pb-4">
                      <div className="flex justify-between items-start gap-2 mb-4">
                        <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 text-[10px] font-bold uppercase tracking-widest border border-slate-700">
                          {sport.sport}
                        </span>
                        <span className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-500 text-[10px] font-bold uppercase tracking-widest border border-amber-500/20">
                          {sport.type}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-white group-hover:text-amber-400 transition-colors mb-2">
                        {sport.title}
                      </h3>
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {sport.description}
                      </p>
                    </div>
                    
                    <div className="p-6 pt-0 mt-auto space-y-3">
                      <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                        <MapPin className="h-3.5 w-3.5" />
                        {sport.location}
                      </div>
                      {sport.deadline && (
                        <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                          <Clock className="h-3.5 w-3.5" />
                          Deadline: {new Date(sport.deadline).toLocaleDateString()}
                        </div>
                      )}
                    </div>

                    <div className="p-6 pt-4 border-t border-slate-800/80 mt-2">
                      <a
                        href={sport.source_url || "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between w-full p-3 rounded-xl bg-slate-800 text-sm font-bold text-slate-300 hover:bg-amber-500 hover:text-slate-950 transition-all group/btn"
                      >
                        <span>View Details</span>
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </PageTransition>
  )
}
