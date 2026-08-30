import { Check } from "lucide-react"
import { cn } from "@/lib/utils/cn"

interface OnboardingChipProps {
  label: string
  selected: boolean
  onClick: () => void
  disabled?: boolean
}

export function OnboardingChip({
  label,
  selected,
  onClick,
  disabled = false,
}: OnboardingChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 active:scale-95",
        selected
          ? "bg-primary text-primary-foreground shadow-sm font-semibold ring-2 ring-primary ring-offset-1"
          : "bg-card border border-border text-foreground hover:border-primary/50 hover:bg-primary/5"
      )}
    >
      {selected && <Check className="h-3.5 w-3.5 stroke-[3]" />}
      <span>{label}</span>
    </button>
  )
}
