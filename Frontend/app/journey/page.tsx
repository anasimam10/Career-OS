"use client"

import React, { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
  CheckCircle2,
  ArrowRight,
  ArrowUpRight,
  Loader2,
  AlertCircle,
  RefreshCw,
  Sparkles,
  Compass,
  FileCheck,
  Target,
  GraduationCap,
  Briefcase,
  Layers,
  MapPin,
  Trophy,
  ChevronRight,
  Circle,
  Clock,
  ExternalLink,
} from "lucide-react"
import { getJourney, completeMilestone } from "@/lib/api/journey"
import type { JourneyResponse, MilestoneItem } from "@/lib/types/journey.types"
import { PageTransition } from "@/components/layout/PageTransition"
import { TalkToAlumniSection } from "@/components/alumni/TalkToAlumniSection"
import { getSession } from "@/lib/session"
import { cn } from "@/lib/utils/cn"
import { resolveMilestoneCta } from "@/lib/milestoneCta"

const PHASE_METADATA: Record<number, { title: string; subtitle: string; icon: React.ElementType }> = {
  1: {
    title: "Exploration & Reality Check",
    subtitle: "Explore target careers, evaluate Pakistan market realities, and test-drive hands-on work.",
    icon: Compass,
  },
  2: {
    title: "Career Decision & Discovery",
    subtitle: "Compare fields side-by-side and discover verified Pakistani university programs.",
    icon: Target,
  },
  3: {
    title: "Skill Building & Resources",
    subtitle: "Master required technical competencies with curated roadmaps and hands-on practice.",
    icon: Layers,
  },
  4: {
    title: "Opportunities & Interview Readiness",
    subtitle: "Apply for scholarships and internships, refine your CV, and practice with AI mock interviews.",
    icon: Briefcase,
  },
  5: {
    title: "First Job & Placement",
    subtitle: "Turn your preparation into verified applications, placement readiness audits, and your first job.",
    icon: GraduationCap,
  },
}

export default function JourneyPage() {
  const router = useRouter()
  const [studentId, setStudentId] = useState<string | null>(null)
  const [localSession, setLocalSession] = useState<{
    career_goal?: string
    city?: string
    education_stage?: string
    sports_interest?: string
  } | null>(null)
  const [journeyData, setJourneyData] = useState<JourneyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [completingId, setCompletingId] = useState<number | null>(null)
  const [completionError, setCompletionError] = useState<string | null>(null)

  // 1. Session check on mount
  useEffect(() => {
    const id = typeof window !== "undefined" ? localStorage.getItem("career_os_student_id") : null
    if (!id) {
      router.push("/onboarding")
      return
    }
    setStudentId(id)
    const sess = getSession()
    if (sess) {
      setLocalSession(sess)
    }
  }, [router])

  // 2. Fetch journey data
  const fetchJourneyData = React.useCallback((sid: string) => {
    setLoading(true)
    setError(null)
    getJourney(sid)
      .then((data) => {
        setJourneyData(data)
        setError(null)
      })
      .catch((err: any) => {
        if (err?.statusCode === 404) {
          localStorage.removeItem("career_os_student_id")
          router.push("/onboarding")
          return
        }
        setError("Could not load your career roadmap.")
      })
      .finally(() => setLoading(false))
  }, [router])

  useEffect(() => {
    if (!studentId) return
    fetchJourneyData(studentId)
  }, [studentId, fetchJourneyData])

  // 3. Milestone completion handler
  const handleComplete = async (milestoneId: number) => {
    if (!studentId || completingId !== null) return
    setCompletingId(milestoneId)
    setCompletionError(null)

    try {
      const updatedJourney = await completeMilestone(studentId, milestoneId)
      setJourneyData(updatedJourney)

      // Smooth scroll to next active milestone
      const nextActive = updatedJourney.milestones?.find((m) => m.status === "active")
      if (nextActive) {
        setTimeout(() => {
          document
            .getElementById(`milestone-${nextActive.id}`)
            ?.scrollIntoView({ behavior: "smooth", block: "center" })
        }, 250)
      }
    } catch (err: any) {
      if (err?.statusCode === 400 || err?.raw?.detail === "already_completed") {
        return
      }
      setCompletionError("Could not save milestone completion. Please try again.")
    } finally {
      setCompletingId(null)
    }
  }

  const milestones: MilestoneItem[] = useMemo(
    () => journeyData?.milestones || [],
    [journeyData?.milestones]
  )
  const completedCount = journeyData?.completed_count ?? milestones.filter((m) => m.status === "completed").length
  const totalCount = journeyData?.total_count || milestones.length
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0
  const isAllComplete = totalCount > 0 && completedCount === totalCount

  // Active (Current) and Up Next milestones
  const activeMilestone = useMemo(
    () => milestones.find((m) => m.status === "active") || null,
    [milestones]
  )

  const upNextMilestone = useMemo(() => {
    if (!activeMilestone) return null
    const activeIdx = milestones.findIndex((m) => m.id === activeMilestone.id)
    if (activeIdx !== -1 && activeIdx + 1 < milestones.length) {
      return milestones[activeIdx + 1]
    }
    return null
  }, [milestones, activeMilestone])

  // Group milestones by Phase
  const phases = useMemo(() => {
    const grouped: Record<number, MilestoneItem[]> = {}
    milestones.forEach((m) => {
      const p = m.phase || 1
      if (!grouped[p]) grouped[p] = []
      grouped[p].push(m)
    })
    return Object.entries(grouped)
      .map(([phaseStr, items]) => ({
        phase: Number(phaseStr),
        items: items.sort((a, b) => a.order - b.order),
      }))
      .sort((a, b) => a.phase - b.phase)
  }, [milestones])

  const careerSlug =
    journeyData?.career_slug ||
    (journeyData as any)?.career_goal_slug ||
    (journeyData as any)?.student?.career_goal_slug ||
    localSession?.career_goal?.toLowerCase().replace(/\s+/g, "-") ||
    "software-engineering"
  const careerName = journeyData?.career_name || localSession?.career_goal || "Career Pathway"
  const userCity = journeyData?.city || localSession?.city || "Pakistan"
  const userStage =
    journeyData?.education_stage_label ||
    (localSession?.education_stage
      ? localSession.education_stage.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
      : "Undergraduate")
  const userSport = journeyData?.sports_interest || localSession?.sports_interest

  return (
    <PageTransition>
      <div className="bg-[#0B0F1A] min-h-screen pt-8 pb-28 text-[#F1F5F9]">
        <div className="mx-auto max-w-[1040px] px-4 sm:px-6 space-y-8">

          {/* ========================================================================= */}
          {/* SECTION A: CURRENT CONTEXT HEADER                                          */}
          {/* ========================================================================= */}
          <header className="rounded-3xl border border-[#1E2D42] bg-[#111827]/90 p-6 sm:p-8 backdrop-blur-md relative overflow-hidden shadow-xl">
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/5 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-400">
                    <Sparkles className="h-3.5 w-3.5 text-blue-400" />
                    Your journey
                  </span>

                  <span className="inline-flex items-center gap-1 rounded-full border border-[#1E2D42] bg-[#1C2539] px-2.5 py-0.5 text-xs text-[#94A3B8]">
                    <MapPin className="h-3 w-3 text-blue-400" />
                    {userCity}
                  </span>

                  <span className="inline-flex items-center rounded-full border border-[#1E2D42] bg-[#1C2539] px-2.5 py-0.5 text-xs text-[#94A3B8]">
                    {userStage}
                  </span>

                  {userSport && (
                    <Link
                      href="/sports"
                      className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                    >
                      <Trophy className="h-3 w-3 text-emerald-400" />
                      Sports Pathway: {userSport}
                    </Link>
                  )}
                </div>

                <h1 className="text-3xl sm:text-4xl font-black text-[#F1F5F9] tracking-tight">
                  Your next steps
                </h1>

                <p className="text-xs sm:text-sm text-[#94A3B8] max-w-xl leading-relaxed">
                  Personalized roadmap for <span className="text-slate-200 font-semibold">{careerName}</span> connecting exploration, hands-on trials, degree programs, skills, and placement readiness in Pakistan.
                </p>
              </div>

              {/* Progress Tracker Card */}
              {loading ? (
                <div className="shrink-0 bg-[#0B0F1A]/80 border border-[#1E2D42] rounded-2xl p-5 w-full md:w-72 shadow-md space-y-3 animate-pulse">
                  <div className="flex justify-between items-center text-xs">
                    <div className="h-3 w-28 bg-[#1C2539] rounded" />
                    <div className="h-3 w-8 bg-[#1C2539] rounded" />
                  </div>
                  <div className="h-2 w-full bg-[#1C2539] rounded-full" />
                  <div className="h-3 w-36 bg-[#1C2539] rounded" />
                </div>
              ) : !error && totalCount > 0 ? (
                <div className="shrink-0 bg-[#0B0F1A]/80 border border-[#1E2D42] rounded-2xl p-5 w-full md:w-72 shadow-md space-y-3">
                  <div className="flex justify-between items-center text-xs font-bold">
                    <span className="text-[#94A3B8] uppercase tracking-wider text-[11px]">Pathway Progress</span>
                    <span className="text-blue-400 font-extrabold text-sm">{progressPercent}%</span>
                  </div>

                  <div className="h-2 w-full bg-[#1C2539] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-600 via-blue-500 to-emerald-400 rounded-full transition-all duration-700 ease-out"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>

                  <div className="flex justify-between items-center text-[11px] text-[#64748B] font-medium">
                    <span>{completedCount} of {totalCount} steps completed</span>
                    {isAllComplete && <span className="text-[#10B981] font-semibold">Ready for Job ✓</span>}
                  </div>
                </div>
              ) : null}
            </div>
          </header>

          {/* ========================================================================= */}
          {/* TASK 5d: PROGRESS SUMMARY BAR                                             */}
          {/* ========================================================================= */}
          {!loading && !error && totalCount > 0 && (
            <div className="flex items-center gap-4 p-4 bg-gray-900/60 border border-gray-800 rounded-xl">
              <div>
                <span className="text-2xl font-bold text-white">{completedCount}</span>
                <span className="text-gray-500 text-sm"> / {totalCount} milestones</span>
              </div>

              <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-emerald-500 rounded-full transition-all duration-700"
                  style={{ width: `${(completedCount / totalCount) * 100}%` }}
                />
              </div>

              <span className="text-sm font-semibold text-gray-400">
                {Math.round((completedCount / totalCount) * 100)}%
              </span>
            </div>
          )}

          {/* Error Banner */}
          {completionError && (
            <div className="flex items-center gap-3 rounded-2xl border border-rose-900/60 bg-rose-950/40 p-4 text-xs font-medium text-rose-300 animate-fade-in">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{completionError}</span>
            </div>
          )}

          {/* Loading Skeleton */}
          {loading ? (
            <div className="space-y-8 pt-4" aria-busy="true" aria-label="Loading career journey">
              <div className="h-44 rounded-3xl border border-[#1E2D42] bg-[#111827] p-8 animate-pulse space-y-4">
                <div className="h-4 w-32 bg-[#1C2539] rounded" />
                <div className="h-6 w-3/5 bg-[#1C2539] rounded" />
                <div className="h-4 w-4/5 bg-[#1C2539] rounded" />
              </div>
              <div className="space-y-4">
                {[1, 2, 3].map((p) => (
                  <div key={p} className="h-24 rounded-2xl border border-[#1E2D42] bg-[#111827] p-6 animate-pulse" />
                ))}
              </div>
            </div>
          ) : error ? (
            /* Error State with Retry Button */
            <div className="text-center py-16 space-y-5 rounded-3xl border border-rose-900/50 bg-rose-950/20 p-8 max-w-lg mx-auto">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-950 text-rose-400">
                <AlertCircle className="h-6 w-6" />
              </div>
              <p className="text-sm font-semibold text-[#F1F5F9]">{error}</p>
              <div className="flex justify-center gap-3">
                <button
                  type="button"
                  onClick={() => studentId && fetchJourneyData(studentId)}
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 text-xs font-bold transition-all shadow-md cursor-pointer"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Retry</span>
                </button>
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2 rounded-xl bg-[#1C2539] hover:bg-[#2A3650] text-[#F1F5F9] px-4 py-2.5 text-xs font-semibold border border-[#2A3650]"
                >
                  <span>Re-onboard</span>
                </Link>
              </div>
            </div>
          ) : milestones.length === 0 ? (
            /* Empty State */
            <div className="text-center py-16 space-y-4 rounded-3xl border border-[#1E2D42] bg-[#111827] p-8 max-w-lg mx-auto">
              <p className="text-[#94A3B8] text-sm">Your roadmap is not initialized yet.</p>
              <Link
                href="/onboarding"
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 px-6 py-3 text-sm font-bold text-white transition-all shadow-md"
              >
                <span>Start My Journey</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          ) : isAllComplete ? (
            /* ========================================================================= */
            /* SECTION 16: TERMINAL CAREER DASHBOARD (POST-COMPLETION LAUNCHPAD)         */
            /* ========================================================================= */
            <div className="space-y-8 animate-fade-in">
              <div className="rounded-3xl border border-emerald-500/30 bg-gradient-to-b from-emerald-500/10 via-[#111827] to-[#111827] p-8 sm:p-10 text-center relative overflow-hidden shadow-2xl">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 mb-4">
                  <CheckCircle2 className="h-9 w-9 stroke-[2.5]" />
                </div>
                <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 text-xs font-bold text-emerald-400 mb-3">
                  Core Pathway Completed
                </div>
                <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-3">
                  You&apos;re Prepared for {careerName}
                </h2>
                <p className="text-sm text-slate-300 max-w-xl mx-auto leading-relaxed mb-6">
                  You have completed the foundational milestones from career reality testing to skill readiness. Now turn your preparation into applications and placement.
                </p>

                <div className="pt-2 flex flex-wrap items-center justify-center gap-4">
                  <Link
                    href="/opportunities"
                    className="inline-flex items-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 text-sm font-bold transition-all shadow-lg shadow-blue-900/30"
                  >
                    <Briefcase className="h-4 w-4" />
                    <span>Explore Verified Opportunities</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    href="/mock-interview"
                    className="inline-flex items-center gap-2 rounded-xl border border-[#2A3A54] bg-[#1C2539] hover:bg-[#2563EB] hover:border-blue-500 text-white px-6 py-3 text-sm font-semibold transition-all"
                  >
                    <span>Practice AI Mock Interview</span>
                  </Link>
                </div>
              </div>

              {/* Action Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="rounded-2xl border border-[#1E2D42] bg-[#111827] p-6 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/15 text-blue-400">
                      <Briefcase className="h-4 w-4" />
                    </div>
                    <h3 className="text-base font-bold text-white">Entry-Level Roles & Internships</h3>
                    <p className="text-xs text-[#94A3B8] leading-relaxed">
                      Discover verified Pakistani opportunities aligned with your completed skills.
                    </p>
                  </div>
                  <Link
                    href="/opportunities"
                    className="text-xs font-semibold text-blue-400 hover:text-blue-300 inline-flex items-center gap-1.5 pt-2"
                  >
                    <span>Browse Opportunities</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>

                <div className="rounded-2xl border border-[#1E2D42] bg-[#111827] p-6 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-400">
                      <GraduationCap className="h-4 w-4" />
                    </div>
                    <h3 className="text-base font-bold text-white">Mock Interview Practice</h3>
                    <p className="text-xs text-[#94A3B8] leading-relaxed">
                      Practice realistic behavioral and technical interview questions powered by Qwen.
                    </p>
                  </div>
                  <Link
                    href="/mock-interview"
                    className="text-xs font-semibold text-blue-400 hover:text-blue-300 inline-flex items-center gap-1.5 pt-2"
                  >
                    <span>Start Interview</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>

                <div className="rounded-2xl border border-[#1E2D42] bg-[#111827] p-6 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                    <h3 className="text-base font-bold text-white">Job Readiness Audit</h3>
                    <p className="text-xs text-[#94A3B8] leading-relaxed">
                      Check your placement readiness score and final resume recommendations.
                    </p>
                  </div>
                  <Link
                    href="/job-readiness"
                    className="text-xs font-semibold text-blue-400 hover:text-blue-300 inline-flex items-center gap-1.5 pt-2"
                  >
                    <span>View Readiness Score</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            /* ========================================================================= */
            /* SECTIONS C & D: CURRENT FOCUS HERO & UP NEXT SPOTLIGHT                     */
            /* ========================================================================= */
            <div className="space-y-10">
              {activeMilestone && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Current Focus Card (2 Columns) */}
                  {(() => {
                    const cta = resolveMilestoneCta(activeMilestone, careerSlug)
                    return (
                      <div className="lg:col-span-2 rounded-3xl border-2 border-blue-500/70 bg-gradient-to-br from-blue-950/40 via-[#111827] to-[#111827] p-6 sm:p-8 shadow-[0_0_40px_rgba(59,130,246,0.18)] relative overflow-hidden flex flex-col justify-between gap-6">
                        <div className="space-y-4">
                          <div className="flex items-center justify-between gap-3">
                            <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/40 bg-blue-500/20 px-3 py-1 text-xs font-bold text-blue-300">
                              <span className="h-2 w-2 rounded-full bg-blue-400 animate-ping" />
                              <span>CURRENT FOCUS · STEP {activeMilestone.order}</span>
                            </div>

                            <span className="text-xs text-[#94A3B8] font-medium flex items-center gap-1">
                              <Clock className="h-3 w-3 text-blue-400" />
                              Phase {activeMilestone.phase}
                            </span>
                          </div>

                          <h2 className="text-2xl sm:text-3xl font-black text-[#F1F5F9] tracking-tight">
                            {activeMilestone.title}
                          </h2>

                          {activeMilestone.description && (
                            <p className="text-sm text-slate-300 leading-relaxed max-w-xl">
                              {activeMilestone.description}
                            </p>
                          )}
                        </div>

                        {/* Action Buttons: Primary Feature CTA + Secondary Completion Button */}
                        <div className="pt-4 border-t border-[#1E2D42] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
                          <div className="flex flex-wrap items-center gap-3">
                            {cta && (
                              cta.type === "external" ? (
                                <a
                                  href={cta.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-[0.98] text-white px-6 py-3 text-sm font-bold transition-all shadow-lg shadow-blue-900/30 group cursor-pointer"
                                >
                                  <span>{cta.label}</span>
                                  <ExternalLink className="h-4 w-4" aria-label="opens in new tab" />
                                </a>
                              ) : (
                                <Link
                                  href={cta.url}
                                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-[0.98] text-white px-6 py-3 text-sm font-bold transition-all shadow-lg shadow-blue-900/30 group cursor-pointer"
                                >
                                  <span>{cta.label}</span>
                                  <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                                </Link>
                              )
                            )}

                            <button
                              type="button"
                              onClick={() => handleComplete(activeMilestone.id)}
                              disabled={completingId !== null}
                              aria-label={`Mark "${activeMilestone.title}" as completed`}
                              className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#2A3650] bg-[#1C2539] hover:bg-[#2A3A54] hover:text-white text-[#E2E8F0] px-4 py-3 text-xs sm:text-sm font-semibold transition-all disabled:opacity-50 cursor-pointer"
                            >
                              {completingId === activeMilestone.id ? (
                                <>
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                  <span>Saving...</span>
                                </>
                              ) : (
                                <>
                                  <FileCheck className="h-3.5 w-3.5 text-emerald-400" />
                                  <span>Mark as completed</span>
                                </>
                              )}
                            </button>
                          </div>

                          <span className="text-[11px] text-[#64748B] sm:text-right">
                            Completing advances you to the next step
                          </span>
                        </div>
                      </div>
                    )
                  })()}

                  {/* Up Next Card (1 Column) */}
                  <div className="rounded-3xl border border-[#1E2D42] bg-[#111827]/80 p-6 sm:p-7 flex flex-col justify-between gap-4">
                    <div className="space-y-3">
                      <div className="inline-flex items-center gap-1.5 rounded-full border border-[#1E2D42] bg-[#1C2539] px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-[#94A3B8]">
                        <ChevronRight className="h-3 w-3 text-blue-400" />
                        <span>Up Next</span>
                      </div>

                      {upNextMilestone ? (
                        <>
                          <h3 className="text-lg font-bold text-white tracking-tight">
                            {upNextMilestone.title}
                          </h3>
                          <p className="text-xs text-[#94A3B8] leading-relaxed line-clamp-3">
                            {upNextMilestone.description || "The next step in your sequence once you complete your current focus."}
                          </p>
                        </>
                      ) : (
                        <>
                          <h3 className="text-lg font-bold text-white tracking-tight">
                            Final Step in Progress
                          </h3>
                          <p className="text-xs text-[#94A3B8] leading-relaxed">
                            You are on the final step of your core pathway. Complete it to unlock full job readiness.
                          </p>
                        </>
                      )}
                    </div>

                    {upNextMilestone && (
                      <div className="pt-3 border-t border-[#1E2D42]">
                        <span className="text-[11px] text-[#64748B] font-medium">
                          Unlocks automatically after completing step {activeMilestone.order}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ========================================================================= */}
              {/* SECTION B, E, F: CONNECTED VERTICAL CAREER PATHWAY                        */}
              {/* ========================================================================= */}
              <div className="space-y-6 pt-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#1E2D42]">
                  <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">
                      Full Career Pathway
                    </h2>
                    <p className="text-xs text-[#94A3B8]">
                      Chronological progression from foundational discovery to professional placement.
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-[#64748B]">
                    {completedCount} / {totalCount} completed
                  </span>
                </div>

                <div className="space-y-10">
                  {phases.map(({ phase, items }) => {
                    const meta = PHASE_METADATA[phase] || {
                      title: `Phase ${phase}`,
                      subtitle: "Advance your milestones toward graduation and placement.",
                      icon: Layers,
                    }
                    const PhaseIcon = meta.icon
                    const phaseCompleted = items.every((m) => m.status === "completed")
                    const hasActive = items.some((m) => m.status === "active")

                    return (
                      <div key={phase} className="space-y-4">
                        {/* Phase Header */}
                        <div className="flex items-center justify-between gap-3 pb-2 border-b border-[#1E2D42]/60">
                          <div className="flex items-center gap-3">
                            <div
                              className={cn(
                                "flex h-8 w-8 items-center justify-center rounded-xl border text-xs font-bold transition-colors",
                                phaseCompleted
                                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                                  : hasActive
                                  ? "border-blue-500/60 bg-blue-500/15 text-blue-400"
                                  : "border-[#1E2D42] bg-[#1C2539] text-[#64748B]"
                              )}
                            >
                              <PhaseIcon className="h-4 w-4" />
                            </div>
                            <div>
                              <h3 className="text-sm sm:text-base font-bold text-[#F1F5F9] tracking-tight">
                                Phase {phase}: {meta.title}
                              </h3>
                              <p className="text-[11px] text-[#94A3B8] hidden sm:block">
                                {meta.subtitle}
                              </p>
                            </div>
                          </div>

                          <div>
                            {phaseCompleted ? (
                              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-bold text-emerald-400 border border-emerald-500/20">
                                <CheckCircle2 className="h-3 w-3" />
                                <span>Completed</span>
                              </span>
                            ) : hasActive ? (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/25">
                                <span className="relative flex h-2 w-2">
                                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                                </span>
                                In Progress
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 rounded-full bg-[#1C2539] px-2.5 py-0.5 text-[11px] font-semibold text-[#64748B]">
                                <span>Upcoming</span>
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Connected Vertical Timeline Spine */}
                        <div className="relative pl-6 sm:pl-8 flex flex-col gap-4">
                          {/* Continuous Vertical Spine Line */}
                          <div
                            className={cn(
                              "absolute left-2.5 sm:left-3.5 top-3 bottom-3 w-[2px]",
                              phaseCompleted
                                ? "bg-emerald-500/40"
                                : hasActive
                                ? "bg-blue-500/40"
                                : "bg-gray-800"
                            )}
                          />

                          {items.map((milestone) => {
                            const isCompleted = milestone.status === "completed"
                            const isActive = milestone.status === "active"
                            const isUpcoming = milestone.status === "locked"
                            const cta = resolveMilestoneCta(milestone, careerSlug)

                            return (
                              <div
                                key={milestone.id}
                                id={`milestone-${milestone.id}`}
                                className={cn(
                                  "relative rounded-2xl border transition-all duration-300 p-4 sm:p-5",
                                  isActive && [
                                    "border-blue-500 bg-[#111827] shadow-[0_0_25px_rgba(59,130,246,0.18)] ring-1 ring-blue-500/30",
                                  ],
                                  isCompleted && [
                                    "border-[#1E2D42]/80 bg-[#111827]/70 hover:border-[#2A3A54]",
                                  ],
                                  isUpcoming && [
                                    "border-[#1E2D42]/50 bg-[#111827]/40 opacity-70",
                                  ]
                                )}
                              >
                                {/* Spine Node Indicator on line */}
                                <div className="absolute -left-[27px] sm:-left-[31px] top-5">
                                  {isCompleted ? (
                                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white shadow-sm ring-4 ring-[#0B0F1A]">
                                      <CheckCircle2 className="h-3 w-3 stroke-[3]" />
                                    </div>
                                  ) : isActive ? (
                                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 text-white shadow-[0_0_12px_rgba(59,130,246,0.8)] ring-4 ring-[#0B0F1A]">
                                      <span className="h-2 w-2 rounded-full bg-white animate-ping" />
                                    </div>
                                  ) : (
                                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#1C2539] border border-[#2A3650] text-[#64748B] ring-4 ring-[#0B0F1A]">
                                      <Circle className="h-2 w-2 fill-current" />
                                    </div>
                                  )}
                                </div>

                                <div className="flex flex-col justify-between gap-3">
                                  <div className="space-y-1.5 flex-1">
                                    <div className="flex items-center gap-2">
                                      <span className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider">
                                        Step {milestone.order}
                                      </span>
                                      {isActive && (
                                        <span className="inline-flex items-center rounded px-2 py-0.5 text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                          Current Focus
                                        </span>
                                      )}
                                      {isCompleted && (
                                        <span className="inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                          Completed ✓
                                        </span>
                                      )}
                                      {isUpcoming && (
                                        <span className="inline-flex items-center rounded px-2 py-0.5 text-[10px] font-medium bg-[#1C2539] text-[#64748B]">
                                          Upcoming
                                        </span>
                                      )}
                                    </div>

                                    <h4
                                      className={cn(
                                        "text-base font-bold tracking-tight",
                                        isActive
                                          ? "text-white"
                                          : isCompleted
                                          ? "text-slate-200"
                                          : "text-[#94A3B8]"
                                      )}
                                    >
                                      {milestone.title}
                                    </h4>

                                    {milestone.description && (
                                      <p className="text-xs text-[#94A3B8] leading-relaxed max-w-2xl">
                                        {milestone.description}
                                      </p>
                                    )}
                                  </div>

                                  {/* Milestone Contextual Action Area */}
                                  {isActive && (
                                    <div className="flex flex-wrap items-center gap-3 mt-3 pt-3 border-t border-[#1E2D42]/60">
                                      {cta && (
                                        cta.type === "external" ? (
                                          <a
                                            href={cta.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
                                          >
                                            <span>{cta.label}</span>
                                            <ExternalLink className="w-3.5 h-3.5" aria-label="opens in new tab" />
                                          </a>
                                        ) : (
                                          <Link
                                            href={cta.url}
                                            className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
                                          >
                                            <span>{cta.label}</span>
                                            <ArrowUpRight className="w-3.5 h-3.5" />
                                          </Link>
                                        )
                                      )}
                                      <button
                                        type="button"
                                        onClick={() => handleComplete(milestone.id)}
                                        disabled={completingId !== null}
                                        aria-label={`Mark "${milestone.title}" as completed`}
                                        className="ml-auto inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold px-4 py-2 rounded-lg transition-all cursor-pointer"
                                      >
                                        {completingId === milestone.id ? (
                                          <>
                                            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                                            <span>Saving...</span>
                                          </>
                                        ) : (
                                          <span>Mark as completed</span>
                                        )}
                                      </button>
                                    </div>
                                  )}

                                  {isCompleted && (
                                    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-[#1E2D42]/40 text-emerald-400 text-sm font-medium">
                                      <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
                                      <span>Completed</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SECTION 17: TALK TO ALUMNI (COMING SOON FUTURE PREVIEW)                   */}
          {/* ========================================================================= */}
          <section className="pt-6 border-t border-[#1E2D42]">
            <TalkToAlumniSection />
          </section>

        </div>
      </div>
    </PageTransition>
  )
}
