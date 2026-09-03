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
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Where are you right now?
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          This helps the AI recommend steps tailored to your academic level.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-6">
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
                "flex items-center justify-between p-4 rounded-2xl border text-left text-sm font-medium transition-all duration-300",
                isSelected
                  ? "border-indigo-500 bg-indigo-950/20 text-indigo-50 shadow-[0_0_15px_rgba(99,102,241,0.2)]"
                  : "border-slate-800 bg-slate-900/50 text-slate-300 hover:border-slate-600 hover:bg-slate-800"
              )}
            >
              <span>{opt.label}</span>
              <div
                className={cn(
                  "h-5 w-5 rounded-full border flex items-center justify-center transition-colors",
                  isSelected ? "border-indigo-400 bg-indigo-500" : "border-slate-700 bg-slate-900"
                )}
              >
                {isSelected && <div className="h-2 w-2 rounded-full bg-white shadow-sm" />}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

