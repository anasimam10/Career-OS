"use client"

import { useJourney } from "@/hooks/useJourney"
import { JourneyTimeline } from "@/components/journey/JourneyTimeline"
import { NextStepCard } from "@/components/journey/NextStepCard"
import { RoadmapSteps } from "@/components/journey/RoadmapSteps"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { PageTransition } from "@/components/layout/PageTransition"

export default function JourneyPage() {
  const { journey, loading, error, refetch, completeMilestone } = useJourney()

  const handleStartStep = async () => {
    // Advances progress and refreshes NBA
    try {
      await completeMilestone(1)
    } catch {
      // handled
    }
  }

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10 space-y-10">
        <SectionHeader
          badge="My Journey"
          title="Your Career Pathway"
          subtitle="One student. One direction. One clear next step."
        />

        {loading ? (
          <LoadingState message="Loading your personalised journey state..." />
        ) : error || !journey ? (
          <ErrorState message={error || "Could not load journey"} onRetry={refetch} />
        ) : (
          <>
            {/* 1. THE Centerpiece: Next Best Action Card */}
            <section className="space-y-3">
              <NextStepCard nba={journey.next_best_action} onComplete={handleStartStep} />
            </section>

            {/* 2. Horizontal Stage Progression Timeline */}
            <section className="pt-4">
              <JourneyTimeline currentStage={journey.stage} />
            </section>

            {/* 3. The Next 3 Steps (Max 3 as enforced by architecture) */}
            <section className="pt-4">
              <RoadmapSteps steps={journey.next_steps} />
            </section>
          </>
        )}
      </div>
    </PageTransition>
  )
}
