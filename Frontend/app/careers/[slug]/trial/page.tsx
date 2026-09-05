"use client"

import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Sparkles } from "lucide-react"
import { useCareerAnalysis } from "@/hooks/useCareerAnalysis"
import { TrialPlanView } from "@/components/career/TrialPlanView"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { Button } from "@/components/ui/button"
import { PageTransition } from "@/components/layout/PageTransition"

export default function TrialPlanPage() {
  const params = useParams()
  const slug = Array.isArray(params?.slug) ? params.slug[0] : (params?.slug as string) || "software-engineering"
  const { trialPlan, career, loading, error, refetch } = useCareerAnalysis(slug)

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
          <LoadingState message="Generating your custom 7-day trial plan..." />
        ) : error || !trialPlan ? (
          <ErrorState message={error || "Could not load trial plan"} onRetry={refetch} />
        ) : (
          <TrialPlanView plan={trialPlan} />
        )}
      </div>
    </PageTransition>
  )
}
