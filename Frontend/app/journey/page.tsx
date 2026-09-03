"use client"

import { TalkToAlumniSection } from "@/components/alumni/TalkToAlumniSection"

import Link from "next/link"
import { useJourney } from "@/hooks/useJourney"
import { isOnboardingComplete } from "@/lib/session"
import { JourneyTimeline } from "@/components/journey/JourneyTimeline"
import { RoadmapSteps } from "@/components/journey/RoadmapSteps"
import { NBA } from "@/components/shared/NBA"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { PageTransition } from "@/components/layout/PageTransition"
import { ArrowRight, Compass, Navigation } from "lucide-react"

import { useState } from "react"

export default function JourneyPage() {
  const { journey, loading, error, refetch, completeMilestone } = useJourney()
  const [completing, setCompleting] = useState(false)
  const [completingStepId, setCompletingStepId] = useState<number | null>(null)

  const handleStartStep = async (stepId?: number) => {
    try {
      setCompleting(true)
      if (stepId) setCompletingStepId(stepId)
      await completeMilestone(stepId ?? journey?.current_milestone_id)
    } catch (err) {
      console.error(err)
    } finally {
      setCompleting(false)
      setCompletingStepId(null)
    }
  }

  return (
    <PageTransition>
      <div className="bg-[#05080E] min-h-screen pt-12 pb-24">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 space-y-12">
          
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-bold tracking-widest text-indigo-400 uppercase">
              <Navigation className="h-3.5 w-3.5" />
              <span>Personalized Pathway</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
              Your Career Intelligence <span className="text-indigo-400">Map</span>
            </h1>
            <p className="text-slate-400 max-w-2xl mx-auto text-lg">
              One student. One direction. One clear next step based on ground truth.
            </p>
          </div>

          {loading ? (
            <div className="pt-12"><LoadingState message="Loading your personalised journey state..." /></div>
          ) : !journey ? (
            <div className="relative rounded-[2rem] border border-slate-800 bg-slate-900/50 p-8 sm:p-16 text-center shadow-2xl space-y-8 overflow-hidden backdrop-blur-sm max-w-2xl mx-auto mt-12">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.1),transparent)] pointer-events-none" />
              
              <div className="relative z-10 mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shadow-[0_0_30px_rgba(99,102,241,0.2)]">
                <Compass className="h-10 w-10 animate-pulse-slow" />
              </div>
              <div className="relative z-10 space-y-4">
                <h2 className="text-2xl sm:text-3xl font-extrabold text-white">Initialize Your Pathway</h2>
                <p className="text-base text-slate-400 max-w-md mx-auto">
                  Complete the profile setup to receive your tailored roadmap, verified Pakistani career intelligence, and your first Next Best Action.
                </p>
              </div>
              <div className="relative z-10 pt-4">
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2 rounded-full bg-white px-8 py-4 text-base font-bold text-slate-950 shadow-[0_0_20px_rgba(255,255,255,0.2)] hover:bg-slate-200 transition-all hover:scale-105"
                >
                  Start My Journey
                  <ArrowRight className="h-5 w-5" />
                </Link>
              </div>
            </div>
          ) : error || !journey ? (
            <div className="pt-12"><ErrorState message={error || "Could not load journey"} onRetry={refetch} /></div>
          ) : (

            <div className="space-y-16 pt-8">
              {/* 1. THE Centerpiece: Next Best Action Card */}
              <section className="relative z-20">
                <NBA 
                  title={journey.next_best_action.title}
                  description={journey.next_best_action.description}
                  actionLabel="Mark as Completed"
                  onComplete={() => handleStartStep()}
                  loading={completing && completingStepId === null}
                />
              </section>

              {/* 2. Horizontal Stage Progression Timeline */}
              <section className="relative z-10">
                <JourneyTimeline currentStage={journey.stage} />
              </section>

              {/* 3. The Next 3 Steps */}
              <section className="relative z-10">
                <div className="mb-6 flex items-center gap-3">
                  <div className="h-px bg-slate-800 flex-1" />
                  <h3 className="text-sm font-bold tracking-widest text-slate-500 uppercase">Upcoming Path</h3>
                  <div className="h-px bg-slate-800 flex-1" />
                </div>
                <RoadmapSteps 
                  steps={journey.next_steps} 
                  onCompleteStep={(stepId) => handleStartStep(stepId)}
                  completingStepId={completingStepId}
                />
              </section>

              {/* 4. Talk to Alumni - Future Feature Entry Point */}
              <section className="relative z-10 pt-4">
                <TalkToAlumniSection />
              </section>
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}
