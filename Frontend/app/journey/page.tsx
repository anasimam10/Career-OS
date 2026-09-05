"use client"

import React, { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { CheckCircle2, Lock, ArrowRight, Loader2, AlertCircle, RefreshCw } from "lucide-react"
import { getJourney, completeMilestone } from "@/lib/api/journey"
import type { JourneyResponse, MilestoneItem } from "@/lib/types/journey.types"
import { PageTransition } from "@/components/layout/PageTransition"

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
    const id = localStorage.getItem("career_os_student_id")
    if (!id) {
      router.push("/onboarding")
      return
    }
    setStudentId(id)
  }, [router])

  // 2. Fetch journey data once studentId is available
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
        setError("Could not load your journey.")
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
      // Authoritative replacement of entire state
      setJourneyData(updatedJourney)

      // Auto-scroll to next active milestone
      const nextActive = updatedJourney.milestones?.find((m) => m.status === "active")
      if (nextActive) {
        setTimeout(() => {
          document
            .getElementById(`milestone-${nextActive.id}`)
            ?.scrollIntoView({ behavior: "smooth", block: "center" })
        }, 200)
      }
    } catch (err: any) {
      if (err?.statusCode === 400 || (err?.raw && err?.raw?.detail === "already_completed")) {
        return // silently ignore duplicate
      }
      setCompletionError("Could not save. Please try again.")
    } finally {
      setCompletingId(null)
    }
  }

  const milestones: MilestoneItem[] = journeyData?.milestones || []
  const activeMilestone = milestones.find((m) => m.status === "active")
  const upcomingMilestones = milestones.filter(
    (m) => m.status === "locked" && (!activeMilestone || m.id !== activeMilestone.id)
  )
  const completedMilestones = milestones.filter((m) => m.status === "completed")

  const totalCount = journeyData?.total_count || milestones.length
  const completedCount = journeyData?.completed_count || completedMilestones.length
  const isJourneyComplete = totalCount > 0 && completedCount === totalCount

  return (
    <PageTransition>
      <div className="bg-[#0B0F1A] min-h-screen pt-10 pb-24 text-[#F1F5F9]">
        <div className="mx-auto max-w-[1100px] px-4 sm:px-6 space-y-10">
          {/* Header */}
          <div className="space-y-3">
            <span className="text-xs font-medium tracking-wider text-[#94A3B8] uppercase">
              Your journey
            </span>
            <h1 className="text-3xl md:text-5xl font-extrabold text-[#F1F5F9] tracking-tight">
              Your next steps
            </h1>

            {/* Progress indicator */}
            {!loading && !error && milestones.length > 0 && (
              <div className="pt-2 max-w-md space-y-2">
                <div className="flex justify-between items-center text-xs font-semibold text-[#94A3B8]">
                  <span>
                    {completedCount} of {totalCount} milestones completed
                  </span>
                  <span>{Math.round((completedCount / totalCount) * 100)}%</span>
                </div>
                <div className="h-1.5 w-full bg-[#1C2539] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#2563EB] rounded-full transition-all duration-500"
                    style={{
                      width: `${totalCount > 0 ? (completedCount / totalCount) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Loading Skeleton */}
          {loading ? (
            <div className="space-y-4 pt-4" aria-busy="true" aria-label="Loading your journey">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-28 w-full rounded-[12px] border border-[#1E2D42] bg-[#111827] p-6 animate-pulse flex flex-col justify-between"
                >
                  <div className="space-y-2.5">
                    <div className="h-3.5 w-28 bg-[#1C2539] rounded" />
                    <div className="h-4.5 w-3/5 bg-[#1C2539] rounded" />
                    <div className="h-3 w-4/5 bg-[#1C2539] rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            /* Error State with Retry Button */
            <div className="text-center py-12 space-y-4 rounded-2xl border border-rose-900/50 bg-rose-950/20 p-8 max-w-lg mx-auto">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-950 text-rose-400">
                <AlertCircle className="h-6 w-6" />
              </div>
              <p className="text-sm font-medium text-[#F1F5F9]">
                {error || "Could not load your journey."}
              </p>
              <div className="flex justify-center gap-3">
                <button
                  type="button"
                  onClick={() => studentId && fetchJourneyData(studentId)}
                  className="inline-flex items-center gap-2 rounded-[8px] bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-5 py-2.5 text-xs font-semibold transition-colors"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Retry</span>
                </button>
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2 rounded-[8px] bg-[#1C2539] hover:bg-[#2A3650] text-[#F1F5F9] px-4 py-2.5 text-xs font-semibold border border-[#2A3650]"
                >
                  <span>Go to Onboarding</span>
                </Link>
              </div>
            </div>
          ) : milestones.length === 0 ? (
            /* Empty State */
            <div className="text-center py-14 space-y-4 rounded-2xl border border-[#1E2D42] bg-[#111827] p-8 max-w-lg mx-auto">
              <p className="text-[#94A3B8] text-sm">Your journey isn&apos;t set up yet.</p>
              <Link
                href="/onboarding"
                className="inline-flex items-center gap-2 rounded-[8px] bg-[#2563EB] hover:bg-[#1D4ED8] px-5 py-2.5 text-sm font-semibold text-white transition-colors"
              >
                <span>Start profile →</span>
              </Link>
            </div>
          ) : isJourneyComplete ? (
            /* Journey Complete State */
            <div className="text-center py-14 space-y-3 rounded-2xl border border-[#10B981]/30 bg-[#111827] p-8 max-w-lg mx-auto">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#10B981]/20 text-[#10B981]">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <p className="text-xl font-bold text-[#F1F5F9]">Journey complete.</p>
              <p className="text-sm text-[#94A3B8] max-w-md mx-auto">
                You&apos;ve finished all milestones. Check your job readiness score.
              </p>
              <div className="pt-3">
                <Link
                  href="/job-readiness"
                  className="inline-flex items-center gap-2 rounded-[8px] bg-[#2563EB] hover:bg-[#1D4ED8] px-6 py-2.5 text-sm font-semibold text-white transition-colors"
                >
                  <span>Check readiness →</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          ) : (
            /* Active Journey Milestones Content */
            <div className="space-y-10 pt-2">
              {completionError && (
                <div className="flex items-center gap-2 rounded-[8px] border border-rose-900/60 bg-rose-950/40 p-4 text-xs text-rose-300">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{completionError}</span>
                </div>
              )}

              {/* Section 1: Current Active Step */}
              {activeMilestone && (
                <section className="space-y-3">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Current step
                  </h2>
                  <div
                    id={`milestone-${activeMilestone.id}`}
                    className="rounded-[12px] border border-[#1E2D42] border-l-[3px] border-l-[#2563EB] bg-[#111827] p-6 shadow-md transition-all space-y-4"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                      <div className="space-y-1.5">
                        <span className="text-xs font-medium text-[#3B82F6]">
                          Phase {activeMilestone.phase}
                        </span>
                        <h3 className="text-lg font-bold text-[#F1F5F9]">
                          {activeMilestone.title}
                        </h3>
                        {activeMilestone.description && (
                          <p className="text-sm text-[#94A3B8] max-w-2xl leading-relaxed">
                            {activeMilestone.description}
                          </p>
                        )}
                      </div>
                      <span className="self-start inline-flex items-center rounded-[4px] bg-[#2563EB]/15 px-2.5 py-1 text-[11px] font-medium text-[#60A5FA]">
                        Active
                      </span>
                    </div>

                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={() => handleComplete(activeMilestone.id)}
                        disabled={completingId !== null}
                        className="inline-flex items-center gap-2 rounded-[8px] bg-[#2563EB] hover:bg-[#1D4ED8] active:scale-[0.98] text-white px-5 py-2.5 text-sm font-semibold transition-all disabled:opacity-50 cursor-pointer"
                      >
                        {completingId === activeMilestone.id ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Marking completed...</span>
                          </>
                        ) : (
                          <span>Mark as completed</span>
                        )}
                      </button>
                    </div>
                  </div>
                </section>
              )}

              {/* Section 2: Up Next */}
              {upcomingMilestones.length > 0 && (
                <section className="space-y-3">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Up next
                  </h2>
                  <div className="space-y-3">
                    {upcomingMilestones.map((milestone) => (
                      <div
                        key={milestone.id}
                        id={`milestone-${milestone.id}`}
                        className="rounded-[12px] border border-[#1E2D42]/60 bg-[#111827]/50 p-5 opacity-45 pointer-events-none flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                      >
                        <div className="space-y-1">
                          <span className="text-[11px] font-medium text-[#64748B]">
                            Phase {milestone.phase}
                          </span>
                          <h3 className="text-base font-semibold text-[#94A3B8]">
                            {milestone.title}
                          </h3>
                          {milestone.description && (
                            <p className="text-xs text-[#64748B] max-w-xl">
                              {milestone.description}
                            </p>
                          )}
                        </div>
                        <span className="self-start sm:self-center inline-flex items-center gap-1 rounded-[4px] bg-[#1C2539] px-2.5 py-1 text-[11px] font-medium text-[#64748B]">
                          <Lock className="h-3 w-3" />
                          <span>Locked</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Section 3: Completed Milestones */}
              {completedMilestones.length > 0 && (
                <section className="space-y-3 pt-4 border-t border-[#1E2D42]/60">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                    Completed ({completedMilestones.length})
                  </h2>
                  <div className="space-y-2.5">
                    {completedMilestones.map((milestone) => (
                      <div
                        key={milestone.id}
                        id={`milestone-${milestone.id}`}
                        className="rounded-[12px] border border-[#1E2D42]/80 border-l-[3px] border-l-[#10B981] bg-[#111827]/80 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <div className="flex items-start sm:items-center gap-3">
                          <CheckCircle2 className="h-5 w-5 text-[#10B981] shrink-0 mt-0.5 sm:mt-0" />
                          <div>
                            <span className="text-[10px] font-medium text-[#10B981]">
                              Phase {milestone.phase}
                            </span>
                            <h3 className="text-sm font-semibold text-[#F1F5F9]">
                              {milestone.title}
                            </h3>
                          </div>
                        </div>
                        <span className="self-start sm:self-center inline-flex items-center rounded-[4px] bg-[#10B981]/15 px-2 py-0.5 text-[11px] font-medium text-[#10B981]">
                          Completed ✓
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}
