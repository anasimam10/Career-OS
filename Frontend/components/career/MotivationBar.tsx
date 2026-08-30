import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { ProgressBar } from "@/components/shared/ProgressBar"
import { Sparkles } from "lucide-react"

export function MotivationBar() {
  const factors = [
    { label: "Genuine Interest", value: 80, color: "emerald" as const },
    { label: "Salary Potential", value: 60, color: "primary" as const },
    { label: "Peer Influence", value: 40, color: "amber" as const },
    { label: "Family Expectations", value: 20, color: "rose" as const },
  ]

  return (
    <Card className="border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Motivation Reflection
          </span>
        </div>
        <CardTitle className="text-lg font-bold">WHY ARE YOU CONSIDERING THIS FIELD?</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-xs text-muted-foreground italic">
          * AI reflection based on your answers (not a clinical or psychological diagnosis)
        </p>

        <div className="space-y-3">
          {factors.map((f, i) => (
            <ProgressBar
              key={i}
              label={f.label}
              value={f.value}
              color={f.color}
            />
          ))}
        </div>

        <div className="rounded-xl bg-muted/60 p-3.5 text-xs text-foreground leading-relaxed border border-border/40">
          <strong>Reflection:</strong> You appear genuinely interested in technology, but salary and peer influence are also affecting your decision.
        </div>
      </CardContent>
    </Card>
  )
}
