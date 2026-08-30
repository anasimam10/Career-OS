import { MOTIVATION_OPTIONS } from "@/lib/mock/onboarding.mock"
import { OnboardingChip } from "../OnboardingChip"

interface Step4MotivationProps {
  selected: string[]
  onToggle: (tag: string) => void
}

export function Step4Motivation({ selected, onToggle }: Step4MotivationProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          Why are you considering this path?
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Be honest — the AI uses this to calculate genuine motivation vs. external pressure.
        </p>
      </div>

      <div className="flex flex-wrap gap-2.5">
        {MOTIVATION_OPTIONS.map((opt) => (
          <OnboardingChip
            key={opt}
            label={opt}
            selected={selected.includes(opt)}
            onClick={() => onToggle(opt)}
          />
        ))}
      </div>
    </div>
  )
}
