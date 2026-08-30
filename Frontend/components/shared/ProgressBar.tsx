import { cn } from "@/lib/utils/cn"

interface ProgressBarProps {
  label: string
  value: number // 0-100
  sublabel?: string
  className?: string
  color?: "primary" | "emerald" | "amber" | "rose"
}

export function ProgressBar({
  label,
  value,
  sublabel,
  className,
  color = "primary",
}: ProgressBarProps) {
  const colorMap = {
    primary: "bg-primary",
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
    rose: "bg-rose-500",
  }

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex justify-between text-xs font-medium">
        <span className="text-foreground">{label}</span>
        <span className="text-muted-foreground">{sublabel || `${value}%`}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className={cn("h-full transition-all duration-500 ease-out", colorMap[color])}
          style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
        />
      </div>
    </div>
  )
}
