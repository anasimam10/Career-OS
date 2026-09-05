"use client"

import React from "react"
import { cn } from "@/lib/utils/cn"
import { Check, Target, Compass } from "lucide-react"

interface Step3CareerFieldProps {
  value: string
  onChange: (field: string) => void
}

export const CAREER_FIELDS: { label: string; description: string }[] = [
  {
    label: "Software Engineering",
    description: "Web, cloud, software architecture & development",
  },
  {
    label: "Data Science & AI",
    description: "Machine learning, data analytics, predictive models",
  },
  {
    label: "Business & Finance",
    description: "Corporate strategy, banking, fintech & investment",
  },
  {
    label: "Medicine & Healthcare",
    description: "MBBS, medical sciences, pharmacy, healthcare delivery",
  },
  {
    label: "Engineering (non-CS)",
    description: "Electrical, mechanical, civil & industrial systems",
  },
  {
    label: "Design & Creative",
    description: "UI/UX, product design, graphic media & typography",
  },
  {
    label: "Law",
    description: "Corporate law, litigation, judiciary & legal advisory",
  },
  {
    label: "Accounting & Commerce",
    description: "ACCA, CA, corporate audit, tax & financial reporting",
  },
  {
    label: "Marketing & Media",
    description: "Digital marketing, brand storytelling, public relations",
  },
  {
    label: "Teaching & Education",
    description: "Higher education, pedagogy, training & research",
  },
  {
    label: "I'm not sure yet",
    description: "Explore broad pathways and discover where you fit",
  },
]

export function Step3CareerField({ value, onChange }: Step3CareerFieldProps) {
  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA] mb-3">
          <Target className="h-3.5 w-3.5" />
          <span>Step 3: Academic / Career Field</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F1F5F9]">
          What field are you interested in targeting?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          Choose the career discipline you are most curious about. You can always explore other fields later.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-6">
        {CAREER_FIELDS.map((field) => {
          const isSelected = value === field.label
          const isUnsure = field.label === "I'm not sure yet"
          return (
            <button
              key={field.label}
              type="button"
              onClick={() => onChange(field.label)}
              className={cn(
                "flex flex-col justify-between p-4 rounded-[12px] border text-left transition-all duration-200 group relative",
                isUnsure && "sm:col-span-2 border-dashed",
                isSelected
                  ? "border-[#3B82F6] bg-[#3B82F6]/10 text-[#F1F5F9] shadow-[0_0_16px_rgba(59,130,246,0.2)]"
                  : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/60 hover:bg-[#1C2539] hover:text-[#F1F5F9]"
              )}
            >
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  {isUnsure && <Compass className="h-4 w-4 text-[#60A5FA]" />}
                  <span className={cn("text-sm font-bold", isSelected ? "text-[#F1F5F9]" : "text-[#E2E8F0]")}>
                    {field.label}
                  </span>
                </div>
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
              <span className="text-xs text-[#64748B] group-hover:text-[#94A3B8] transition-colors mt-1.5">
                {field.description}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
