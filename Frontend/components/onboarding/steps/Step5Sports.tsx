import { SPORTS_OPTIONS } from "@/lib/mock/onboarding.mock"
import { OnboardingChip } from "../OnboardingChip"

interface Step5SportsProps {
  selected: string | null
  onSelect: (sport: string | null) => void
}

export function Step5Sports({ selected, onSelect }: Step5SportsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          Do you have a sport you enjoy or compete in?
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Sports can open university trials, scholarships, and team opportunities in Pakistan.
        </p>
      </div>

      <div className="flex flex-wrap gap-2.5">
        {SPORTS_OPTIONS.map((sport) => (
          <OnboardingChip
            key={sport}
            label={sport}
            selected={selected === sport}
            onClick={() => onSelect(selected === sport ? null : sport)}
          />
        ))}
      </div>
    </div>
  )
}
