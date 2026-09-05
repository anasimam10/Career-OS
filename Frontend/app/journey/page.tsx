"use client"

import { useState } from "react"
import Link from "next/link"
import { useJourney } from "@/hooks/useJourney"
import { JourneyTimeline } from "@/components/journey/JourneyTimeline"
import { RoadmapSteps } from "@/components/journey/RoadmapSteps"
import { NBA } from "@/components/shared/NBA"
import { PageTransition } from "@/components/layout/PageTransition"
import { ArrowRight, Compass, RefreshCw, AlertCircle, Sparkles } from "lucide-react"

export default function JourneyPage() {
  const { journey, loading, error, sessionMissing, refetch, completeMilestone } = useJourney()
  const [completingStepId, setCompletingStepId] = useState<number | null>(null)
  const [stepError, setStepError] = useState<{ stepId: number; message: string } | null>(null)

  const handleCompleteMilestone = async (stepId?: number) => {
    const targetId = stepId ?? journey?.current_milestone_id ?? 0
    try {
      setCompletingStepId(targetId)
      setStepError(null)
      await completeMilestone(targetId)

      // Auto-scroll to the next active milestone
      setTimeout(() => {
        const nextActiveCard = document.querySelector('[class*="border-[#3B82F6]"]')
        if (nextActiveCard) {
          nextActiveCard.scrollIntoView({ behavior: "smooth", block: "center" })
        }
      }, 150)
    } catch (err: any) {
      setStepError({
        stepId: targetId,
        message: err instanceof Error ? err.message : "Failed to mark milestone completed. Please try again.",
      })
    } finally {
      setCompletingStepId(null)
    }
  }

  return (
    <PageTransition>
      <div className="bg-[#0B0F1A] min-h-screen pt-10 pb-24 text-[#F1F5F9]">
        <div className="mx-auto max-w-[1100px] px-4 sm:px-6 space-y-12">
          
          {/* Header */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#3B82F6]/30 bg-[#3B82F6]/10 px-3.5 py-1 text-xs font-semibold tracking-wider text-[#60A5FA] uppercase">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Personalized Pathway</span>
            </div>
            <h1 className="text-3xl md:text-5xl font-extrabold text-[#F1F5F9] tracking-tight">
              Your Career Journey
            </h1>
            <p className="text-[#94A3B8] max-w-xl mx-auto text-base">
              One student. One direction. One clear next step based on ground truth.
            </p>
          </div>

          {/* Loading Skeleton State */}
          {loading ? (
            <div className="space-y-10 pt-4" aria-busy="true" aria-label="Loading your journey">
              {/* NBA Skeleton */}
              <div className="h-44 rounded-3xl bg-[#111827] border border-[#2A3650] p-8 animate-pulse space-y-4">
                <div className="h-4 w-32 bg-[#1C2539] rounded" />
                <div className="h-7 w-2/3 bg-[#1C2539] rounded" />
                <div className="h-4 w-full max-w-lg bg-[#1C2539] rounded" />
              </div>

              {/* Milestones Skeleton Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-56 rounded-[16px] border border-[#2A3650] bg-[#111827] p-6 animate-pulse flex flex-col justify-between"
                  >
                    <div className="space-y-3">
                      <div className="h-3.5 w-24 bg-[#1C2539] rounded" />
                      <div className="h-5 w-4/5 bg-[#1C2539] rounded" />
                      <div className="h-3 w-full bg-[#1C2539] rounded" />
                      <div className="h-3 w-3/4 bg-[#1C2539] rounded" />
                    </div>
                    <div className="h-11 w-full bg-[#1C2539] rounded-[6px]" />
                  </div>
                ))}
              </div>
            </div>
          ) : sessionMissing || !journey ? (
            /* Empty State (No journey started / Session missing) */
            <div className="rounded-3xl border border-[#2A3650] bg-[#111827] p-8 sm:p-14 text-center shadow-2xl space-y-6 max-w-xl mx-auto mt-8">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[#3B82F6]/10 border border-[#3B82F6]/20 text-[#3B82F6]">
                <Compass className="h-8 w-8" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold text-[#F1F5F9]">
                  You haven&apos;t started a journey yet.
                </h2>
                <p className="text-sm text-[#94A3B8] max-w-md mx-auto">
                  Complete the quick setup to receive your tailored roadmap, verified Pakistani career intelligence, and your first milestone.
                </p>
              </div>
              <div className="pt-2">
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2 rounded-[6px] bg-[#3B82F6] hover:bg-[#2563EB] px-6 py-3 text-sm font-bold text-white transition-all shadow-md hover:shadow-lg"
                >
                  <span>Set Up My Journey</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          ) : error && !journey ? (
            /* Error State with Retry Button */
            <div className="rounded-2xl border border-rose-900/50 bg-rose-950/20 p-8 text-center max-w-lg mx-auto space-y-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-950 text-rose-400">
                <AlertCircle className="h-6 w-6" />
              </div>
              <p className="text-sm text-[#F1F5F9] font-medium">
                {error || "Couldn't load your journey — try again"}
              </p>
              <div className="flex justify-center gap-3">
                <button
                  type="button"
                  onClick={() => refetch()}
                  className="inline-flex items-center gap-2 rounded-[6px] bg-[#1C2539] hover:bg-[#2A3650] text-[#F1F5F9] px-4 py-2 text-xs font-semibold border border-[#2A3650]"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Retry</span>
                </button>
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2 rounded-[6px] bg-[#3B82F6] hover:bg-[#2563EB] text-white px-4 py-2 text-xs font-bold"
                >
                  <span>Go to Onboarding</span>
                </Link>
              </div>
            </div>
          ) : (
            /* Active Journey Content */
            <div className="space-y-14 pt-4">
              {/* 1. Next Best Action (NBA) Card */}
              {journey.next_best_action && (
                <section>
                  <NBA
                    title={journey.next_best_action.title}
                    description={journey.next_best_action.description}
                    actionLabel="Mark as Completed"
                    onComplete={() => handleCompleteMilestone()}
                    loading={completingStepId !== null}
                  />
                </section>
              )}

              {/* 2. Stage Progression Timeline */}
              <section>
                <JourneyTimeline currentStage={journey.stage} />
              </section>

              {/* 3. Upcoming Milestones Path (using MilestoneCard via RoadmapSteps) */}
              <section className="space-y-6">
                <div className="flex items-center gap-3">
                  <div className="h-px bg-[#2A3650] flex-1" />
                  <h2 className="text-xs font-bold tracking-wider text-[#64748B] uppercase">
                    Upcoming Path
                  </h2>
                  <div className="h-px bg-[#2A3650] flex-1" />
                </div>

                <RoadmapSteps
                  steps={journey.next_steps}
                  onCompleteStep={handleCompleteMilestone}
                  completingStepId={completingStepId}
                  stepError={stepError}
                />
              </section>
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}
