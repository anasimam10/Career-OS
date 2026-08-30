import Link from "next/link"
import { Calendar, CheckCircle2, MessageSquare, ArrowRight } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { CareerTrialPlan } from "@/lib/types/career.types"

export function TrialPlanView({ plan }: { plan: CareerTrialPlan }) {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {plan.days.map((day, idx) => (
          <Card key={idx} className="border-border hover:shadow-card-hover transition-all">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-primary">
                  <Calendar className="h-3.5 w-3.5" />
                  {day.day_range}
                </span>
              </div>
              <CardTitle className="text-lg font-bold text-foreground mt-1">
                {day.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2.5 text-sm text-muted-foreground">
                {day.tasks.map((task, tIdx) => (
                  <li key={tIdx} className="flex items-start gap-2.5">
                    <div className="mt-0.5 h-4 w-4 rounded-full border border-primary/40 flex items-center justify-center shrink-0">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary/60" />
                    </div>
                    <span>{task}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* End-of-Trial Reflection Card */}
      <Card className="border-2 border-emerald-500/20 bg-emerald-50/20">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2 text-emerald-700">
            <MessageSquare className="h-4 w-4" />
            <span className="text-xs font-bold uppercase tracking-wider">
              Day 7 Reflection Prompt
            </span>
          </div>
          <CardTitle className="text-lg font-bold text-foreground">
            How to evaluate your trial
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground leading-relaxed italic">
            &ldquo;{plan.reflection_prompt}&rdquo;
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">
              Ready to commit or have questions? Talk to your AI mentor.
            </p>
            <Button asChild className="w-full sm:w-auto gap-2 bg-emerald-600 hover:bg-emerald-700 text-white">
              <Link href="/mentor">
                Ask AI Mentor for Advice
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
