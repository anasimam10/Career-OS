"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils/cn"
import type { EducationStage } from "@/lib/types/journey.types"
import { Check } from "lucide-react"

interface Step1EducationProps {
  value: EducationStage
  onChange: (val: EducationStage) => void
}

const ACADEMIC_LEVELS = [
  { label: "O-Level / Matric", stage: "HIGH_SCHOOL" as EducationStage },
  { label: "A-Level / Intermediate", stage: "HIGH_SCHOOL" as EducationStage },
  { label: "University (Years 1–2)", stage: "UNIVERSITY" as EducationStage },
  { label: "University (Years 3–4)", stage: "FINAL_YEAR" as EducationStage },
  { label: "Graduated / Entry-Level", stage: "CAREER_DISCOVERY" as EducationStage },
]

export function Step1Education({ value, onChange }: Step1EducationProps) {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(() => {
    const idx = ACADEMIC_LEVELS.findIndex((opt) => opt.stage === value)
    return idx !== -1 ? idx : 0
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F1F5F9]">
          What is your current academic level?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          This personalizes your milestone roadmap and labour intelligence to where you are.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-6">
        {ACADEMIC_LEVELS.map((opt, idx) => {
          const isSelected = selectedIdx === idx
          return (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setSelectedIdx(idx)
                onChange(opt.stage)
              }}
              className={cn(
                "flex items-center justify-between p-4 rounded-[12px] border text-left text-sm font-semibold transition-all duration-200",
                isSelected
                  ? "border-[#3B82F6] bg-[#3B82F6]/10 text-[#F1F5F9] shadow-[0_0_16px_rgba(59,130,246,0.2)]"
                  : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/60 hover:bg-[#1C2539] hover:text-[#F1F5F9]"
              )}
            >
              <span>{opt.label}</span>
              <div
                className={cn(
                  "h-5 w-5 rounded-full border flex items-center justify-center transition-colors",
                  isSelected
                    ? "border-[#3B82F6] bg-[#3B82F6] text-white"
                    : "border-[#2A3650] bg-[#0B0F1A]"
                )}
              >
                {isSelected && <Check className="h-3 w-3 text-white stroke-[3px]" />}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
