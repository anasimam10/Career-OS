import { Check } from "lucide-react"
import { STAGE_ORDER, STAGE_LABELS, type EducationStage } from "@/lib/types/journey.types"
import { cn } from "@/lib/utils/cn"

export function JourneyTimeline({ currentStage }: { currentStage: EducationStage }) {
  const currentIndex = STAGE_ORDER.indexOf(currentStage)

  return (
    <div className="rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground block">
            Your Long-Term Pathway
          </span>
          <h3 className="text-xl font-bold tracking-tight text-foreground mt-0.5">
            Stage: {STAGE_LABELS[currentStage]}
          </h3>
        </div>
        <div className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
          <span className="h-2 w-2 rounded-full bg-primary animate-ping" />
          <span>YOU ARE HERE</span>
        </div>
      </div>

      {/* Horizontal on tablet+, scrolling on mobile */}
      <div className="overflow-x-auto pb-4 pt-2">
        <div className="flex items-center min-w-[700px] justify-between relative">
          {/* Background progress track */}
          <div className="absolute top-4 left-4 right-4 h-0.5 bg-border -z-0" />

          {STAGE_ORDER.map((stage, idx) => {
            const isCompleted = idx < currentIndex
            const isCurrent = idx === currentIndex
            const isFuture = idx > currentIndex

            return (
              <div key={stage} className="flex flex-col items-center gap-2 relative z-10">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold transition-all",
                    isCompleted
                      ? "border-emerald-600 bg-emerald-600 text-white"
                      : isCurrent
                      ? "border-primary bg-primary text-white ring-4 ring-primary/20 scale-110 shadow-sm"
                      : "border-border bg-card text-muted-foreground"
                  )}
                >
                  {isCompleted ? <Check className="h-4 w-4 stroke-[3]" /> : idx + 1}
                </div>
                <span
                  className={cn(
                    "text-[11px] font-medium text-center whitespace-nowrap",
                    isCurrent
                      ? "text-primary font-bold"
                      : isCompleted
                      ? "text-foreground"
                      : "text-muted-foreground/70"
                  )}
                >
                  {STAGE_LABELS[stage]}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
