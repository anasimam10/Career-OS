import { CareerMetricBar } from "./CareerMetricBar"
import { MotivationBar } from "./MotivationBar"
import { CareerVerdict } from "./CareerVerdict"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import type { CareerRealityResponse } from "@/lib/types/career.types"

export function RealityCheckPanel({
  data,
  careerSlug,
}: {
  data: CareerRealityResponse
  careerSlug: string
}) {
  const { reality, verdict } = data

  return (
    <div className="space-y-8">
      {/* 4 Metric Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <CareerMetricBar label="Market Demand" level={reality.demand_level} />
        <CareerMetricBar label="Competition" level={reality.competition_level} />
        <CareerMetricBar label="Learning Difficulty" level={reality.difficulty_level} />
        <CareerMetricBar label="Pakistan Opportunity" level={reality.demand_level} />
      </div>

      {/* Rewards & Risks Side-by-Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-bold text-foreground">
              Rewards in Pakistan
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {reality.rewards.map((r, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-bold text-foreground">
              Realities & Risks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {reality.risks.map((r, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-amber-600 font-bold">!</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Motivation Reflection Component */}
      <MotivationBar />

      {/* Primary AI Verdict Card */}
      <CareerVerdict verdict={verdict} careerSlug={careerSlug} />
    </div>
  )
}
