"use client"

import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { useCareerAnalysis } from "@/hooks/useCareerAnalysis"
import { TrialPlanView } from "@/components/career/TrialPlanView"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { ErrorState } from "@/components/shared/ErrorState"
import { Button } from "@/components/ui/button"
import { PageTransition } from "@/components/layout/PageTransition"

export default function TrialPlanPage() {
  const params = useParams()
  const slug = Array.isArray(params?.slug) ? params.slug[0] : (params?.slug as string) || "software-engineering"
  const { trialPlan, career, loading, error, refetch } = useCareerAnalysis(slug, {
    includeAnalysis: false,
    includeTrialPlan: true,
  })

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10 space-y-8">
        <div className="flex items-center gap-3">
          <Button asChild variant="ghost" size="sm" className="gap-2 -ml-2 text-muted-foreground hover:text-white">
            <Link href={`/careers/${slug}/reality-check`}>
              <ArrowLeft className="h-4 w-4" />
              Back to Reality Check
            </Link>
          </Button>
          <span className="text-slate-600">•</span>
          <Button asChild variant="ghost" size="sm" className="gap-2 text-muted-foreground hover:text-white">
            <Link href="/journey">
              Return to My Journey
            </Link>
          </Button>
        </div>

        <SectionHeader
          badge="Action Trial"
          title={`7-Day ${career?.name || "Career"} Exploration`}
          subtitle="Test the field for one week before making permanent educational commitments."
        />

        {loading ? (
          <div className="max-w-5xl mx-auto px-2 py-6 animate-pulse space-y-8">
            {/* Progress bar skeleton */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 space-y-3">
              <div className="flex justify-between">
                <div className="h-4 w-32 bg-gray-700 rounded" />
                <div className="h-4 w-20 bg-gray-800 rounded" />
              </div>
              <div className="h-2 w-full bg-gray-800 rounded-full" />
            </div>

            {/* Daily cards grid skeleton — 2 columns */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 space-y-4">
                  <div className="flex justify-between items-center">
                    <div className="h-4 w-20 bg-gray-800 rounded-md" />
                    <div className="h-3 w-16 bg-gray-800 rounded" />
                  </div>
                  <div className="h-6 w-3/4 bg-gray-700 rounded" />
                  <div className="space-y-2.5 pt-2">
                    {[1, 2, 3].map((t) => (
                      <div key={t} className="h-10 bg-gray-800/40 rounded-xl" />
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Subtle message */}
            <p className="text-center text-gray-500 text-sm mt-8">
              Generating your custom 7-day trial plan based on Pakistan market data...
            </p>
          </div>
        ) : error || !trialPlan ? (
          <ErrorState message={error || "Could not load trial plan"} onRetry={refetch} />
        ) : (
          <TrialPlanView plan={trialPlan} />
        )}
      </div>
    </PageTransition>
  )
}
