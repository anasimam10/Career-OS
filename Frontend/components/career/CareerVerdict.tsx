import Link from "next/link"
import { CheckCircle2, AlertTriangle, ArrowRight, Sparkles } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { CareerVerdict as VerdictType } from "@/lib/types/career.types"

export function CareerVerdict({
  verdict,
  careerSlug,
}: {
  verdict: VerdictType
  careerSlug: string
}) {
  const isGood = verdict.verdict === "GOOD_FIT"
  const isExploring = verdict.verdict === "WORTH_EXPLORING"

  const badgeVariant = isGood ? "success" : isExploring ? "warning" : "destructive"

  return (
    <Card className="border-2 border-primary/20 bg-gradient-to-b from-primary/5 to-transparent overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              AI Recommendation
            </span>
          </div>
          <Badge variant={badgeVariant} className="font-bold text-xs">
            {verdict.verdict.replace("_", " ")}
          </Badge>
        </div>
        <CardTitle className="text-2xl font-bold tracking-tight text-foreground mt-2">
          {verdict.headline}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-muted-foreground leading-relaxed">
          {verdict.reasoning}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="rounded-2xl border border-emerald-200/80 bg-emerald-50/50 p-4 space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
              Your Strengths
            </h4>
            <ul className="space-y-1.5 text-xs text-emerald-950">
              {verdict.student_strengths_match.map((s, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span>✓</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-2xl border border-amber-200/80 bg-amber-50/50 p-4 space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800 flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
              Gaps to Address
            </h4>
            <ul className="space-y-1.5 text-xs text-amber-950">
              {verdict.gaps_to_address.map((g, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span>•</span>
                  <span>{g}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
      <CardFooter className="pt-2 pb-6 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-border/40">
        <div className="text-xs text-muted-foreground">
          Suggested action: <strong className="text-foreground">{verdict.suggested_trial || "7-Day Trial"}</strong>
        </div>
        <Button asChild size="lg" className="w-full sm:w-auto gap-2">
          <Link href={`/careers/${careerSlug}/trial`}>
            Start 7-Day Trial
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  )
}
