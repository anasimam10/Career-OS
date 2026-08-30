"use client"

import { useState } from "react"
import { ClipboardCheck, AlertTriangle, Lightbulb, ArrowRight, RefreshCw } from "lucide-react"
import { getJobReadiness } from "@/lib/api/job-readiness"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { PageTransition } from "@/components/layout/PageTransition"
import type { JobReadinessResponse } from "@/lib/types/job-readiness.types"

const COMPONENT_LABELS: Record<string, string> = {
  skills: "Skills",
  projects: "Projects",
  internship: "Internship",
  cv: "CV / Portfolio",
  interview: "Interview Prep",
}

export default function JobReadinessPage() {
  const [data, setData] = useState<JobReadinessResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCheck = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getJobReadiness()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get job readiness score")
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageTransition>
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-8">
        <SectionHeader
          title="Job Readiness Check"
          subtitle="See how prepared you are for the job market based on your journey progress."
          badge="Career Prep"
        />

        {!data && !loading && (
          <Card>
            <CardContent className="flex flex-col items-center gap-4 py-12">
              <ClipboardCheck className="h-12 w-12 text-muted-foreground" />
              <p className="text-muted-foreground text-center max-w-md">
                Click below to analyze your job readiness based on your profile, skills, and completed milestones.
              </p>
              <Button onClick={handleCheck} size="lg">
                Check My Readiness
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        )}

        {loading && <LoadingState message="Analyzing your job readiness..." />}
        {error && <ErrorState message={error} />}

        {data && (
          <div className="space-y-6">
            {/* Overall Score */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <span className="text-4xl font-bold">{data.score_label}</span>
                  <span className="text-lg text-muted-foreground">Job Readiness</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Progress value={data.overall_score * 100} className="h-3" />
                <p className="text-sm text-muted-foreground italic">
                  {data.disclaimer}
                </p>
              </CardContent>
            </Card>

            {/* Component Scores */}
            <Card>
              <CardHeader>
                <CardTitle>Component Scores</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(data.component_scores).map(([key, score]) => (
                  <div key={key} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className={key === data.biggest_gap ? "font-bold text-red-600" : "font-medium"}>
                        {COMPONENT_LABELS[key] || key}
                        {key === data.biggest_gap && (
                          <Badge variant="destructive" className="ml-2 text-xs">Biggest Gap</Badge>
                        )}
                      </span>
                      <span className="text-muted-foreground">{Math.round(score * 100)}%</span>
                    </div>
                    <Progress
                      value={score * 100}
                      className="h-2"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Gap Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-500" />
                  Gap Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed">{data.gap_explanation}</p>
              </CardContent>
            </Card>

            {/* Next Best Action */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-emerald-500" />
                  Recommended Next Action
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <h3 className="font-semibold text-lg">{data.next_best_action.title}</h3>
                <p className="text-sm text-muted-foreground">{data.next_best_action.description}</p>
                {data.next_best_action.steps.length > 0 && (
                  <ul className="space-y-1">
                    {data.next_best_action.steps.map((step, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-primary font-bold">{i + 1}.</span>
                        {step}
                      </li>
                    ))}
                  </ul>
                )}
                <p className="text-xs text-muted-foreground">
                  Estimated time: {data.next_best_action.estimated_time}
                </p>
              </CardContent>
            </Card>

            {/* Recommendations */}
            {data.recommendations.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {data.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <ArrowRight className="h-4 w-4 mt-0.5 text-primary shrink-0" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Recheck Button */}
            <div className="flex justify-center">
              <Button variant="outline" onClick={handleCheck} disabled={loading}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Recheck
              </Button>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  )
}
