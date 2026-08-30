import { FUTURE_GOAL_OPTIONS } from "@/lib/mock/onboarding.mock"
import { OnboardingChip } from "../OnboardingChip"
import { Input } from "@/components/ui/input"

interface Step6FutureProps {
  selectedGoals: string[]
  city: string
  onToggleGoal: (goal: string) => void
  onCityChange: (city: string) => void
}

export function Step6Future({
  selectedGoals,
  city,
  onToggleGoal,
  onCityChange,
}: Step6FutureProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          What do you want from your future?
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Select your long-term goals and your current city in Pakistan.
        </p>
      </div>

      <div className="space-y-4">
        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
          Your Primary Goals
        </label>
        <div className="flex flex-wrap gap-2.5">
          {FUTURE_GOAL_OPTIONS.map((goal) => (
            <OnboardingChip
              key={goal}
              label={goal}
              selected={selectedGoals.includes(goal)}
              onClick={() => onToggleGoal(goal)}
            />
          ))}
        </div>
      </div>

      <div className="space-y-2 pt-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
          Current City in Pakistan
        </label>
        <Input
          placeholder="e.g. Karachi, Lahore, Islamabad, Peshawar..."
          value={city}
          onChange={(e) => onCityChange(e.target.value)}
          className="max-w-md"
        />
      </div>
    </div>
  )
}
