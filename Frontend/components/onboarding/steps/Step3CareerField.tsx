import { CAREER_FIELD_OPTIONS } from "@/lib/mock/onboarding.mock"
import { OnboardingChip } from "../OnboardingChip"

interface Step3CareerFieldProps {
  selected: string[]
  onToggle: (field: string) => void
}

export function Step3CareerField({ selected, onToggle }: Step3CareerFieldProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          What career fields are you considering?
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Pick 1–3 fields you are curious about or considering pursuing in Pakistan.
        </p>
      </div>

      <div className="flex flex-wrap gap-2.5">
        {CAREER_FIELD_OPTIONS.map((field) => (
          <OnboardingChip
            key={field}
            label={field}
            selected={selected.includes(field)}
            onClick={() => onToggle(field)}
          />
        ))}
      </div>
    </div>
  )
}
