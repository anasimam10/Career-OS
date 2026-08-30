import { useState } from "react"
import { EDUCATION_STAGE_OPTIONS } from "@/lib/mock/onboarding.mock"
import { cn } from "@/lib/utils/cn"
import type { EducationStage } from "@/lib/types/journey.types"

interface Step1EducationProps {
  value: EducationStage
  onChange: (val: EducationStage) => void
}

export function Step1Education({ value, onChange }: Step1EducationProps) {
  // Track by index because multiple options share the same backend value
  // (e.g. "O-Level / Matric" and "A-Level / Intermediate" are both HIGH_SCHOOL).
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          What are you currently studying?
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          This helps the AI recommend steps tailored to your academic level.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {EDUCATION_STAGE_OPTIONS.map((opt, idx) => {
          const isSelected = selectedIdx === idx
          return (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setSelectedIdx(idx)
                onChange(opt.value as EducationStage)
              }}
              className={cn(
                "flex items-center justify-between p-4 rounded-2xl border text-left text-sm font-medium transition-all",
                isSelected
                  ? "border-primary bg-primary/5 text-primary font-semibold ring-2 ring-primary/20 shadow-sm"
                  : "border-border bg-card text-foreground hover:border-primary/40 hover:bg-muted/50"
              )}
            >
              <span>{opt.label}</span>
              <div
                className={cn(
                  "h-4 w-4 rounded-full border flex items-center justify-center",
                  isSelected ? "border-primary bg-primary text-white" : "border-muted-foreground/40"
                )}
              >
                {isSelected && <div className="h-1.5 w-1.5 rounded-full bg-white" />}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
