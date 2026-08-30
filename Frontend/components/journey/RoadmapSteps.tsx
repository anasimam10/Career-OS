import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Clock } from "lucide-react"
import type { JourneyStep } from "@/lib/types/journey.types"

export function RoadmapSteps({ steps }: { steps: JourneyStep[] }) {
  // Architecture rule: strictly max 3 steps shown
  const visibleSteps = steps.slice(0, 3)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold tracking-tight text-foreground">
          Your Next 3 Steps
        </h3>
        <span className="text-xs text-muted-foreground">
          Remaining steps unlocked as you progress
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {visibleSteps.map((step, idx) => (
          <Card key={idx} className="border-border/80 hover:border-primary/40 transition-all">
            <CardHeader className="p-5 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-primary">Step {idx + 1}</span>
                <span className="flex items-center gap-1 text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {step.estimated_duration}
                </span>
              </div>
              <CardTitle className="text-base font-bold text-foreground">
                {step.title}
              </CardTitle>
              <CardDescription className="text-xs leading-relaxed">
                {step.description}
              </CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  )
}
