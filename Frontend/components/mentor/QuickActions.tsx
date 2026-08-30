import { ArrowUpRight } from "lucide-react"

interface QuickActionsProps {
  actions: string[]
  onSelect: (action: string) => void
  disabled?: boolean
}

export function QuickActions({
  actions,
  onSelect,
  disabled = false,
}: QuickActionsProps) {
  if (!actions.length) return null

  return (
    <div className="space-y-2">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">
        Suggested Questions
      </span>
      <div className="flex flex-wrap gap-2">
        {actions.map((action, idx) => (
          <button
            key={idx}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(action)}
            className="inline-flex items-center gap-1 rounded-full border border-border/80 bg-background px-3 py-1.5 text-xs font-medium text-foreground hover:border-primary/50 hover:bg-primary/5 hover:text-primary transition-all active:scale-95 disabled:opacity-50"
          >
            <span>{action}</span>
            <ArrowUpRight className="h-3 w-3 opacity-60" />
          </button>
        ))}
      </div>
    </div>
  )
}
