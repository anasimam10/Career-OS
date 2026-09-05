"use client"

import React from "react"
import { cn } from "@/lib/utils/cn"
import { Heart, Check, Sparkles } from "lucide-react"

interface Step7MotivationProps {
  selected: string[]
  additionalNotes?: string
  onToggle: (tag: string) => void
  onNotesChange: (notes: string) => void
}

export const MOTIVATION_FACTORS: { label: string; description: string }[] = [
  {
    label: "I genuinely love this subject",
    description: "Deep intellectual curiosity and natural passion for the field",
  },
  {
    label: "High salary potential",
    description: "Financial independence, strong market compensation & earnings",
  },
  {
    label: "Job opportunities & market demand",
    description: "Abundant job openings, remote work options & global demand",
  },
  {
    label: "Career stability & security",
    description: "Reliable long-term employment with lower career disruption risk",
  },
  {
    label: "Family expectations & guidance",
    description: "Respecting family guidance and advice from mentors/parents",
  },
  {
    label: "Want to help people & social impact",
    description: "Making a tangible positive contribution to Pakistan and society",
  },
  {
    label: "Creative expression & building",
    description: "Designing, innovating, coding, or building new solutions",
  },
  {
    label: "Still figuring it out",
    description: "Exploring options honestly to find what truly resonates",
  },
]

export function Step7Motivation({
  selected,
  additionalNotes = "",
  onToggle,
  onNotesChange,
}: Step7MotivationProps) {
  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA] mb-3">
          <Heart className="h-3.5 w-3.5" />
          <span>Step 7: Motivation</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F1F5F9]">
          What is motivating you toward this path?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          There are no wrong answers. Being honest about your real drivers helps Career OS recommend actions that align with what matters most to you.
        </p>
      </div>

      {/* Selectable Motivation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-6">
        {MOTIVATION_FACTORS.map((factor) => {
          const isSelected = selected.includes(factor.label)
          return (
            <button
              key={factor.label}
              type="button"
              onClick={() => onToggle(factor.label)}
              className={cn(
                "flex flex-col justify-between p-4 rounded-[12px] border text-left transition-all duration-200 group relative",
                isSelected
                  ? "border-[#3B82F6] bg-[#3B82F6]/10 text-[#F1F5F9] shadow-[0_0_16px_rgba(59,130,246,0.2)]"
                  : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/60 hover:bg-[#1C2539] hover:text-[#F1F5F9]"
              )}
            >
              <div className="flex items-center justify-between w-full">
                <span className={cn("text-sm font-bold", isSelected ? "text-[#F1F5F9]" : "text-[#E2E8F0]")}>
                  {factor.label}
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
                {factor.description}
              </span>
            </button>
          )
        })}
      </div>

      {/* Optional Short Text Input */}
      <div className="space-y-2 pt-2 border-t border-[#1E2D42]">
        <label htmlFor="additional-notes" className="text-xs font-semibold text-[#94A3B8] flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-[#60A5FA]" />
          <span>Anything else you want us to know? <span className="text-[#64748B] font-normal">(Optional)</span></span>
        </label>
        <textarea
          id="additional-notes"
          value={additionalNotes}
          onChange={(e) => onNotesChange(e.target.value)}
          placeholder="e.g. Planning to apply for scholarships in Germany, or considering freelance software work while studying..."
          rows={2}
          className="w-full px-3.5 py-2.5 rounded-[8px] border border-[#2A3650] bg-[#111827] text-xs text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] resize-none"
        />
      </div>
    </div>
  )
}
