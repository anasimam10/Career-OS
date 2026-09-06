"use client"

import React from "react"
import { cn } from "@/lib/utils/cn"
import type { EducationStage } from "@/lib/types/journey.types"
import { Check, GraduationCap, BookOpen, School, Award, Briefcase } from "lucide-react"

interface Step1EducationProps {
  value: EducationStage
  onChange: (val: EducationStage) => void
}

interface AcademicLevelOption {
  label: string
  stage: EducationStage
  tag: string
  description: string
  icon: React.ComponentType<{ className?: string }>
}

const ACADEMIC_LEVELS: AcademicLevelOption[] = [
  {
    label: "O-Level / Matric",
    stage: "HIGH_SCHOOL",
    tag: "Secondary",
    description: "Grade 9–10 or O-Levels foundation",
    icon: BookOpen,
  },
  {
    label: "A-Level / Intermediate",
    stage: "CAREER_DISCOVERY",
    tag: "Higher Secondary",
    description: "FSc / FA / ICS / I.Com or A-Levels (Grade 11–12)",
    icon: GraduationCap,
  },
  {
    label: "University (Years 1–2)",
    stage: "UNIVERSITY",
    tag: "Undergraduate",
    description: "Early undergraduate semesters & core coursework",
    icon: School,
  },
  {
    label: "University (Years 3–4)",
    stage: "FINAL_YEAR",
    tag: "Final Year / Senior",
    description: "Senior undergraduate, thesis & pre-grad preparation",
    icon: Award,
  },
  {
    label: "Graduated / Entry-Level",
    stage: "JOB_PREPARATION",
    tag: "Career Launch",
    description: "Completed studies, actively pursuing entry-level & graduate roles",
    icon: Briefcase,
  },
]

export function Step1Education({ value, onChange }: Step1EducationProps) {
  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA] mb-3 shadow-sm">
          <GraduationCap className="h-3.5 w-3.5" />
          <span>Step 1: Academic Stage</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F1F5F9]">
          What is your current education level/stage?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8] leading-relaxed">
          Your milestone roadmap and eligibility scoring adapt to where you currently are.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-6">
        {ACADEMIC_LEVELS.map((opt, idx) => {
          const isSelected = value === opt.stage
          const isLast = idx === ACADEMIC_LEVELS.length - 1
          const Icon = opt.icon

          return (
            <button
              key={opt.stage}
              type="button"
              onClick={() => onChange(opt.stage)}
              className={cn(
                "flex items-start gap-3.5 p-4 sm:p-4.5 rounded-[14px] border text-left transition-all duration-200 group relative",
                isLast && "sm:col-span-2",
                isSelected
                  ? "border-[#3B82F6] bg-[#3B82F6]/10 text-[#F1F5F9] shadow-[0_0_18px_rgba(59,130,246,0.18)] ring-1 ring-[#3B82F6]"
                  : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/50 hover:bg-[#1C2539] hover:text-[#F1F5F9]"
              )}
            >
              <div
                className={cn(
                  "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border transition-colors mt-0.5",
                  isSelected
                    ? "border-[#3B82F6]/50 bg-[#3B82F6]/20 text-[#60A5FA]"
                    : "border-[#2A3650] bg-[#1C2539]/60 text-[#64748B] group-hover:border-[#3B82F6]/30 group-hover:text-[#94A3B8]"
                )}
              >
                <Icon className="h-5 w-5" />
              </div>

              <div className="flex-1 min-w-0 pr-1">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span
                    className={cn(
                      "text-sm font-bold tracking-tight",
                      isSelected ? "text-[#F1F5F9]" : "text-[#E2E8F0]"
                    )}
                  >
                    {opt.label}
                  </span>
                  <span
                    className={cn(
                      "text-[10px] font-semibold px-2 py-0.5 rounded-full border transition-colors",
                      isSelected
                        ? "bg-[#3B82F6]/20 border-[#3B82F6]/40 text-[#93C5FD]"
                        : "bg-[#1E293B] border-[#2A3650] text-[#64748B] group-hover:text-[#94A3B8]"
                    )}
                  >
                    {opt.tag}
                  </span>
                </div>
                <p className="text-xs text-[#94A3B8] leading-relaxed">
                  {opt.description}
                </p>
              </div>

              <div
                className={cn(
                  "h-5 w-5 rounded-full border flex items-center justify-center transition-all shrink-0 mt-1",
                  isSelected
                    ? "border-[#3B82F6] bg-[#3B82F6] text-white shadow-sm"
                    : "border-[#334155] bg-[#0B0F1A] group-hover:border-[#475569]"
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
