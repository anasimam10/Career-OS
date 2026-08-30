import { INTEREST_OPTIONS } from "@/lib/mock/onboarding.mock"
import { OnboardingChip } from "../OnboardingChip"

interface Step2InterestsProps {
  selected: string[]
  onToggle: (interest: string) => void
}

export function Step2Interests({ selected, onToggle }: Step2InterestsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          What subjects or interests do you enjoy?
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Select all that apply. Don&apos;t worry, you can always change these later.
        </p>
      </div>

      <div className="flex flex-wrap gap-2.5">
        {INTEREST_OPTIONS.map((interest) => (
          <OnboardingChip
            key={interest}
            label={interest}
            selected={selected.includes(interest)}
            onClick={() => onToggle(interest)}
          />
        ))}
      </div>
    </div>
  )
}
