"use client"

import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Sparkles } from "lucide-react"
import { useCareerAnalysis } from "@/hooks/useCareerAnalysis"
import { RealityCheckPanel } from "@/components/career/RealityCheckPanel"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { Button } from "@/components/ui/button"
import { PageTransition } from "@/components/layout/PageTransition"

export default function RealityCheckPage() {
  const params = useParams()
  const slug = Array.isArray(params?.slug) ? params.slug[0] : (params?.slug as string) || "software-engineering"
  const { career, analysis, loading, error, refetch } = useCareerAnalysis(slug, {
    includeAnalysis: true,
    includeTrialPlan: false,
  })

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10 space-y-8">
        <Button asChild variant="ghost" size="sm" className="gap-2 -ml-2 text-muted-foreground">
          <Link href="/careers">
            <ArrowLeft className="h-4 w-4" />
            Back to Careers
          </Link>
        </Button>

        <SectionHeader
          badge="Career Reality Check"
          title={`Is ${career?.name || "This Field"} Right for You?`}
          subtitle="An honest analysis comparing demand, difficulty, and your personal motivation in Pakistan."
        />

        {loading ? (
          <LoadingState message="Analyzing Pakistani market data & generating AI verdict..." />
        ) : error || !analysis ? (
          <ErrorState message={error || "Could not load analysis"} onRetry={refetch} />
        ) : (
          <RealityCheckPanel
            data={analysis}
            careerSlug={slug}
            topUniversities={career?.top_pk_universities}
          />
        )}
      </div>
    </PageTransition>
  )
}
