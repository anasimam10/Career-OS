"use client"

import React, { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
  CheckCircle2,
  Lock,
  ArrowRight,
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
  ChevronRight,
} from "lucide-react"
import { getJourney, completeMilestone } from "@/lib/api/journey"
import type { JourneyResponse, MilestoneItem } from "@/lib/types/journey.types"
import { PageTransition } from "@/components/layout/PageTransition"
import { cn } from "@/lib/utils/cn"

const PHASE_METADATA: Record<number, { title: string; subtitle: string; icon: React.ElementType }> = {
  1: {
    title: "Exploration & Reality Check",
    subtitle: "Explore in-demand careers, verify Pakistani market realities, and test-drive hands-on work.",
    icon: Compass,
  },
  2: {
    title: "Career Decision & Discovery",
    subtitle: "Compare fields side-by-side and discover verified Pakistani university programs.",
    icon: Target,
  },
  3: {
    title: "Skill Building & Resources",
    subtitle: "Master required technical competencies with curated roadmaps and regular exercises.",
    icon: Layers,
  },
  4: {
    title: "Opportunities & Interview Readiness",
    subtitle: "Apply for scholarships and internships, refine your CV, and practice with AI mock interviews.",
    icon: Briefcase,
  },
  5: {
    title: "First Job & Professional Growth",
    subtitle: "Establish early career momentum with 90-day workplace goals and deliberate skill growth.",
    icon: GraduationCap,
  },
}

function resolveAction(milestone: MilestoneItem): { label: string; url: string } | null {
  if (milestone.action_label && milestone.action_url) {
    return { label: milestone.action_label, url: milestone.action_url }
  }
  const title = milestone.title.toLowerCase()
  if (title.includes("reality check")) {
    return { label: "Start Reality Check →", url: "/careers" }
  }
  if (title.includes("7-day") || title.includes("trial")) {
    return { label: "Start 7-Day Trial →", url: "/careers/software-engineering/trial" }
  }
  if (title.includes("explore") || title.includes("compare")) {
    return { label: "Explore Careers →", url: "/careers" }
  }
  if (title.includes("interview")) {
    return { label: "Start Mock Interview →", url: "/mock-interview" }
  }
  if (title.includes("skill") || title.includes("learn") || title.includes("practice")) {
    return { label: "View Learning Roadmaps →", url: "/opportunities" }
  }
  if (title.includes("cv") || title.includes("routine") || title.includes("readiness")) {
    return { label: "Check Job Readiness →", url: "/job-readiness" }
  }
  if (title.includes("goal") || title.includes("finalize")) {
    return { label: "View Profile →", url: "/profile" }
  }
  return null
}

export default function JourneyPage() {
  const router = useRouter()
  const [studentId, setStudentId] = useState<string | null>(null)
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
  }, [router])

  // 2. Fetch journey data
  const fetchJourneyData = (sid: string) => {
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
  }

  useEffect(() => {
    if (!studentId) return
    fetchJourneyData(studentId)
  }, [studentId])

  // 3. Milestone completion handler
  const handleComplete = async (milestoneId: number) => {
    if (!studentId || completingId !== null) return
    setCompletingId(milestoneId)
    setCompletionError(null)

    try {
      const updatedJourney = await completeMilestone(studentId, milestoneId)
      setJourneyData(updatedJourney)

      // Auto-scroll to newly active milestone
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

  const milestones: MilestoneItem[] = journeyData?.milestones || []
  const completedCount = journeyData?.completed_count ?? milestones.filter((m) => m.status === "completed").length
  const totalCount = journeyData?.total_count || milestones.length
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0
  const isAllComplete = totalCount > 0 && completedCount === totalCount

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

  return (
    <PageTransition>
      <div className="bg-[#0B0F1A] min-h-screen pt-10 pb-28 text-[#F1F5F9]">
        <div className="mx-auto max-w-[1100px] px-4 sm:px-6 space-y-10">
          
          {/* Header & Overall Pathway Progress */}
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA]">
              <Sparkles className="h-3.5 w-3.5 text-[#3B82F6]" />
              <span>Full Career Pathway</span>
            </div>

            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div className="space-y-2">
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-[#F1F5F9] tracking-tight">
                  My Career Journey
                </h1>
                <p className="text-sm sm:text-base text-[#94A3B8] max-w-2xl leading-relaxed">
                  Your personalized, end-to-end roadmap connecting career exploration, hands-on trials, skills, and interview readiness.
                </p>
              </div>

              {!loading && !error && totalCount > 0 && (
                <div className="shrink-0 bg-[#111827] border border-[#1E2D42] rounded-2xl p-4 sm:p-5 w-full md:w-80 shadow-lg space-y-2.5">
                  <div className="flex justify-between items-center text-xs font-bold">
                    <span className="text-[#94A3B8]">Overall Progress</span>
                    <span className="text-[#3B82F6] font-extrabold text-sm">{progressPercent}%</span>
                  </div>
                  <div className="h-2.5 w-full bg-[#1C2539] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[#2563EB] to-[#3B82F6] rounded-full transition-all duration-700 ease-out"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                  <div className="flex justify-between items-center text-[11px] text-[#64748B] font-medium">
                    <span>{completedCount} of {totalCount} milestones completed</span>
                    {isAllComplete && <span className="text-[#10B981] font-semibold">Ready for Job ✓</span>}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Error Banner */}
          {completionError && (
            <div className="flex items-center gap-3 rounded-xl border border-rose-900/60 bg-rose-950/40 p-4 text-xs font-medium text-rose-300 animate-fade-in">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{completionError}</span>
            </div>
          )}

          {/* Loading Skeleton */}
          {loading ? (
            <div className="space-y-8 pt-4" aria-busy="true" aria-label="Loading career journey">
              {[1, 2, 3].map((p) => (
                <div key={p} className="space-y-4">
                  <div className="h-5 w-48 bg-[#1C2539] rounded animate-pulse" />
                  <div className="space-y-3">
                    {[1, 2].map((i) => (
                      <div
                        key={i}
                        className="h-28 rounded-2xl border border-[#1E2D42] bg-[#111827] p-6 animate-pulse flex flex-col justify-between"
                      >
                        <div className="space-y-2.5">
                          <div className="h-3 w-32 bg-[#1C2539] rounded" />
                          <div className="h-4 w-3/5 bg-[#1C2539] rounded" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
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
                  className="inline-flex items-center gap-2 rounded-xl bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-5 py-2.5 text-xs font-bold transition-all shadow-md cursor-pointer"
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
                className="inline-flex items-center gap-2 rounded-xl bg-[#2563EB] hover:bg-[#1D4ED8] px-6 py-3 text-sm font-bold text-white transition-all shadow-md"
              >
                <span>Start My Journey</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          ) : (
            /* Full Multi-Phase Journey Pathway */
            <div className="space-y-12 pt-2">
              {phases.map(({ phase, items }) => {
                const meta = PHASE_METADATA[phase] || {
                  title: `Phase ${phase}`,
                  subtitle: "Advance your milestones toward graduation and career placement.",
                  icon: Layers,
                }
                const PhaseIcon = meta.icon
                const phaseCompleted = items.every((m) => m.status === "completed")
                const hasActive = items.some((m) => m.status === "active")

                return (
                  <section key={phase} className="space-y-4">
                    {/* Phase Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-[#1E2D42]">
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            "flex h-8 w-8 items-center justify-center rounded-lg border text-xs font-bold transition-colors",
                            phaseCompleted
                              ? "border-[#10B981]/40 bg-[#10B981]/10 text-[#10B981]"
                              : hasActive
                              ? "border-[#3B82F6]/60 bg-[#3B82F6]/15 text-[#3B82F6]"
                              : "border-[#1E2D42] bg-[#1C2539] text-[#64748B]"
                          )}
                        >
                          <PhaseIcon className="h-4 w-4" />
                        </div>
                        <div>
                          <h2 className="text-base sm:text-lg font-bold text-[#F1F5F9] tracking-tight">
                            Phase {phase}: {meta.title}
                          </h2>
                          <p className="text-xs text-[#94A3B8] hidden sm:block">
                            {meta.subtitle}
                          </p>
                        </div>
                      </div>

                      <div className="self-start sm:self-center">
                        {phaseCompleted ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#10B981]/15 px-3 py-1 text-[11px] font-bold text-[#10B981]">
                            <CheckCircle2 className="h-3 w-3" />
                            <span>Phase Complete</span>
                          </span>
                        ) : hasActive ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#3B82F6]/15 px-3 py-1 text-[11px] font-bold text-[#60A5FA]">
                            <span className="h-1.5 w-1.5 rounded-full bg-[#3B82F6] animate-pulse" />
                            <span>In Progress</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#1C2539] px-2.5 py-0.5 text-[11px] font-semibold text-[#64748B]">
                            <Lock className="h-3 w-3" />
                            <span>Upcoming</span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Milestone Cards in Phase */}
                    <div className="space-y-3 pl-1 sm:pl-2">
                      {items.map((milestone) => {
                        const isCompleted = milestone.status === "completed"
                        const isActive = milestone.status === "active"
                        const isLocked = milestone.status === "locked"
                        const action = resolveAction(milestone)

                        return (
                          <div
                            key={milestone.id}
                            id={`milestone-${milestone.id}`}
                            className={cn(
                              "relative rounded-2xl border transition-all duration-300 p-5 sm:p-6",
                              isActive && [
                                "border-[#3B82F6] border-l-[5px] bg-[#111827] shadow-[0_0_25px_rgba(59,130,246,0.18)]",
                                "ring-1 ring-[#3B82F6]/30",
                              ],
                              isCompleted && [
                                "border-[#1E2D42]/80 border-l-[4px] border-l-[#10B981] bg-[#111827]/80 hover:border-[#2A3A54]",
                              ],
                              isLocked && [
                                "border-[#1E2D42]/60 bg-[#111827]/40 opacity-55 hover:opacity-75 transition-opacity",
                              ]
                            )}
                          >
                            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                              <div className="flex items-start gap-3.5 flex-1">
                                {/* State Icon */}
                                <div className="mt-0.5 shrink-0">
                                  {isCompleted ? (
                                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#10B981]/20 text-[#10B981]">
                                      <CheckCircle2 className="h-4 w-4 stroke-[2.5px]" />
                                    </div>
                                  ) : isActive ? (
                                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#3B82F6]/20 text-[#3B82F6] shadow-sm">
                                      <span className="h-2.5 w-2.5 rounded-full bg-[#3B82F6] animate-ping" />
                                    </div>
                                  ) : (
                                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#1C2539] text-[#64748B]">
                                      <Lock className="h-3.5 w-3.5" />
                                    </div>
                                  )}
                                </div>

                                <div className="space-y-1.5 flex-1">
                                  <div className="flex items-center gap-2">
                                    <span className="text-[11px] font-semibold text-[#64748B] uppercase tracking-wider">
                                      Step {milestone.order}
                                    </span>
                                    {isActive && (
                                      <span className="inline-flex items-center rounded px-2 py-0.5 text-[10px] font-bold bg-[#3B82F6]/20 text-[#60A5FA]">
                                        Current Step
                                      </span>
                                    )}
                                    {isCompleted && (
                                      <span className="inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold bg-[#10B981]/15 text-[#10B981]">
                                        Completed ✓
                                      </span>
                                    )}
                                  </div>

                                  <h3
                                    className={cn(
                                      "text-base sm:text-lg font-bold tracking-tight",
                                      isActive
                                        ? "text-[#F1F5F9]"
                                        : isCompleted
                                        ? "text-[#E2E8F0]"
                                        : "text-[#94A3B8]"
                                    )}
                                  >
                                    {milestone.title}
                                  </h3>

                                  {milestone.description && (
                                    <p
                                      className={cn(
                                        "text-xs sm:text-sm leading-relaxed max-w-2xl",
                                        isActive
                                          ? "text-[#94A3B8]"
                                          : isCompleted
                                          ? "text-[#64748B]"
                                          : "text-[#64748B]"
                                      )}
                                    >
                                      {milestone.description}
                                    </p>
                                  )}
                                </div>
                              </div>

                              {/* Right Badge Status */}
                              <div className="self-start sm:self-center shrink-0">
                                {isLocked && (
                                  <span className="inline-flex items-center gap-1 rounded-lg bg-[#1C2539] px-3 py-1 text-[11px] font-medium text-[#64748B] border border-[#2A3650]/40">
                                    <Lock className="h-3 w-3" />
                                    <span>Locked</span>
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Active Step Actions */}
                            {isActive && (
                              <div className="mt-5 pt-4 border-t border-[#1E2D42] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                                <div className="flex flex-wrap items-center gap-3">
                                  {action && (
                                    <Link
                                      href={action.url}
                                      className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#2563EB] hover:bg-[#1D4ED8] active:scale-[0.98] text-white px-5 py-2.5 text-xs sm:text-sm font-bold transition-all shadow-md shadow-blue-900/30 group cursor-pointer"
                                    >
                                      <span>{action.label}</span>
                                      <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                                    </Link>
                                  )}

                                  <button
                                    type="button"
                                    onClick={() => handleComplete(milestone.id)}
                                    disabled={completingId !== null}
                                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#2A3650] bg-[#1C2539] hover:bg-[#2A3A54] hover:text-white text-[#E2E8F0] px-4 py-2.5 text-xs sm:text-sm font-semibold transition-all disabled:opacity-50 cursor-pointer"
                                  >
                                    {completingId === milestone.id ? (
                                      <>
                                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                        <span>Marking completed...</span>
                                      </>
                                    ) : (
                                      <>
                                        <FileCheck className="h-3.5 w-3.5 text-[#10B981]" />
                                        <span>Mark as completed</span>
                                      </>
                                    )}
                                  </button>
                                </div>

                                <div className="text-[11px] text-[#64748B] sm:text-right">
                                  <span>Complete this step to unlock the next milestone</span>
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </section>
                )
              })}

              {/* Terminal Readiness Card */}
              {isAllComplete && (
                <div className="text-center py-14 space-y-4 rounded-3xl border border-[#10B981]/40 bg-[#111827] p-8 max-w-xl mx-auto shadow-2xl">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#10B981]/20 text-[#10B981]">
                    <CheckCircle2 className="h-8 w-8" />
                  </div>
                  <h3 className="text-2xl font-black text-[#F1F5F9]">All Milestones Completed!</h3>
                  <p className="text-sm text-[#94A3B8] max-w-md mx-auto leading-relaxed">
                    You have successfully navigated your entire pathway from exploration to job preparation. Check your final job readiness score.
                  </p>
                  <div className="pt-2">
                    <Link
                      href="/job-readiness"
                      className="inline-flex items-center gap-2 rounded-xl bg-[#2563EB] hover:bg-[#1D4ED8] px-6 py-3 text-sm font-bold text-white transition-all shadow-lg shadow-blue-900/40"
                    >
                      <span>Check Job Readiness Score</span>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}
