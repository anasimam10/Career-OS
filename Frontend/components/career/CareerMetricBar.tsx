import { Badge } from "@/components/ui/badge"
import type { DemandLevel, CompetitionLevel, DifficultyLevel } from "@/lib/types/career.types"

interface CareerMetricBarProps {
  label: string
  level: DemandLevel | CompetitionLevel | DifficultyLevel
  description?: string
}

export function CareerMetricBar({ label, level, description }: CareerMetricBarProps) {
  const levelVariant =
    level === "HIGH" ? "high" : level === "MEDIUM" ? "medium" : "low"

  const progressWidth =
    level === "HIGH" ? "w-full" : level === "MEDIUM" ? "w-2/3" : "w-1/3"

  const colorClass =
    level === "HIGH"
      ? "bg-rose-500"
      : level === "MEDIUM"
      ? "bg-amber-500"
      : "bg-emerald-500"

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        <Badge variant={levelVariant} className="text-xs font-bold">
          {level}
        </Badge>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div className={`h-full rounded-full ${colorClass} ${progressWidth} transition-all duration-500`} />
      </div>
      {description && (
        <p className="text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  )
}
