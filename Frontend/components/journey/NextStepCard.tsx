"use client"

import Link from "next/link"
import { Sparkles, Clock, ArrowRight, CheckCircle2 } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { NextBestAction } from "@/lib/types/journey.types"

export function NextStepCard({
  nba,
  onComplete,
}: {
  nba: NextBestAction
  onComplete?: () => void
}) {
  return (
    <div className="relative">
      {/* Subtle pulse ring around the NBA card to establish visual priority */}
      <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-primary/30 to-emerald-500/30 blur-sm -z-10 animate-pulse" />

      <Card className="border-2 border-primary bg-card shadow-nba rounded-3xl overflow-hidden">
        <CardHeader className="bg-primary/5 pb-4 border-b border-primary/10">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-primary animate-ping" />
              <Badge variant="default" className="bg-primary text-primary-foreground font-bold text-xs uppercase tracking-wider">
                Your Next Step
              </Badge>
            </div>
            <div className="flex items-center gap-1 text-xs font-semibold text-muted-foreground">
              <Clock className="h-3.5 w-3.5" />
              <span>{nba.estimated_time}</span>
            </div>
          </div>
          <CardTitle className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground mt-3">
            {nba.title}
          </CardTitle>
        </CardHeader>

        <CardContent className="p-6 sm:p-8 space-y-6">
          <p className="text-base text-foreground/90 leading-relaxed font-normal">
            {nba.description}
          </p>

          {/* Action checklist */}
          <div className="rounded-2xl bg-muted/50 p-4 sm:p-5 border border-border/60 space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground block">
              Action Checklist
            </span>
            <ul className="space-y-2.5">
              {nba.steps.map((step, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-foreground">
                  <div className="mt-0.5 h-4 w-4 rounded-full border border-primary text-primary flex items-center justify-center shrink-0">
                    <span className="text-[10px] font-bold">{idx + 1}</span>
                  </div>
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Why this matters callout */}
          <div className="flex items-start gap-3 rounded-xl bg-emerald-50/60 p-3.5 text-xs text-emerald-950 border border-emerald-200/50">
            <Sparkles className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold text-emerald-900">Why this matters: </strong>
              <span>{nba.why_this_matters}</span>
            </div>
          </div>
        </CardContent>

        <CardFooter className="p-6 sm:p-8 pt-0 flex flex-col sm:flex-row items-center justify-between gap-4">
          <Button asChild variant="outline" size="sm" className="w-full sm:w-auto text-xs">
            <Link href="/mentor">Ask AI Mentor About This</Link>
          </Button>

          <Button
            size="lg"
            onClick={onComplete}
            className="w-full sm:w-auto gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-bold shadow-md hover:shadow-lg"
          >
            <span>Start Step</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
