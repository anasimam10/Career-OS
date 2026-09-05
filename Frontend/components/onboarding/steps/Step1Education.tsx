"use client"

import React from "react"
import { cn } from "@/lib/utils/cn"
import type { EducationStage } from "@/lib/types/journey.types"
import { Check, GraduationCap } from "lucide-react"

interface Step1EducationProps {
  value: EducationStage
  onChange: (val: EducationStage) => void
}

const ACADEMIC_LEVELS: { label: string; stage: EducationStage; description: string }[] = [
  {
    label: "O-Level / Matric",
    stage: "HIGH_SCHOOL",
    description: "Grade 9–10 or O-Levels foundation",
  },
  {
    label: "A-Level / Intermediate",
    stage: "HIGH_SCHOOL",
    description: "FSc / FA / ICS / I.Com or A-Levels",
  },
  {
    label: "University (Years 1–2)",
    stage: "UNIVERSITY",
    description: "Early undergraduate semesters & core coursework",
  },
  {
    label: "University (Years 3–4)",
    stage: "FINAL_YEAR",
    description: "Senior undergraduate, thesis & pre-grad prep",
  },
  {
    label: "Graduated / Entry-Level",
    stage: "CAREER_DISCOVERY",
    description: "Completed studies, launching into professional roles",
  },
]

export function Step1Education({ value, onChange }: Step1EducationProps) {
  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA] mb-3">
          <GraduationCap className="h-3.5 w-3.5" />
          <span>Step 1: Academic Stage</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F1F5F9]">
          What is your current education level/stage?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          Your milestone roadmap and eligibility scoring adapt to where you currently are.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-6">
        {ACADEMIC_LEVELS.map((opt, idx) => {
          const isSelected = value === opt.stage && (idx === 0 ? true : value !== "HIGH_SCHOOL" || idx === 1)
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onChange(opt.stage)}
              className={cn(
                "flex flex-col justify-between p-4.5 rounded-[12px] border text-left transition-all duration-200 group relative",
                isSelected
                  ? "border-[#3B82F6] bg-[#3B82F6]/10 text-[#F1F5F9] shadow-[0_0_16px_rgba(59,130,246,0.2)]"
                  : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/60 hover:bg-[#1C2539] hover:text-[#F1F5F9]"
              )}
            >
              <div className="flex items-center justify-between w-full">
                <span className={cn("text-sm font-bold", isSelected ? "text-[#F1F5F9]" : "text-[#E2E8F0]")}>
                  {opt.label}
                </span>
                <div
                  className={cn(
                    "h-5 w-5 rounded-full border flex items-center justify-center transition-colors shrink-0",
                    isSelected
                      ? "border-[#3B82F6] bg-[#3B82F6] text-white"
                      : "border-[#2A3650] bg-[#0B0F1A]"
                  )}
                >
                  {isSelected && <Check className="h-3 w-3 text-white stroke-[3px]" />}
                </div>
              </div>
              <span className="text-xs text-[#64748B] group-hover:text-[#94A3B8] transition-colors mt-2">
                {opt.description}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
