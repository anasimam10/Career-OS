"use client"

import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { useCareerAnalysis } from "@/hooks/useCareerAnalysis"
import { RealityCheckPanel } from "@/components/career/RealityCheckPanel"
import { SectionHeader } from "@/components/shared/SectionHeader"
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
          <div className="max-w-4xl mx-auto px-2 py-6 animate-pulse">
            {/* Header skeleton */}
            <div className="h-4 w-32 bg-gray-800 rounded mb-3" />
            <div className="h-8 w-64 bg-gray-700 rounded mb-2" />
            <div className="h-4 w-48 bg-gray-800 rounded mb-10" />

            {/* Stat cards skeleton — 3 columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-gray-800/50 rounded-xl p-5 h-28" />
              ))}
            </div>

            {/* Content blocks skeleton */}
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-gray-800/30 rounded-xl p-6 mb-4">
                <div className="h-4 w-40 bg-gray-700 rounded mb-3" />
                <div className="h-3 w-full bg-gray-800 rounded mb-2" />
                <div className="h-3 w-5/6 bg-gray-800 rounded mb-2" />
                <div className="h-3 w-4/6 bg-gray-800 rounded" />
              </div>
            ))}

            {/* Subtle message */}
            <p className="text-center text-gray-500 text-sm mt-8">
              Analyzing Pakistan market data for this career...
            </p>
          </div>
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
