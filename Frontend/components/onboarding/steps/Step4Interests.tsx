"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils/cn"
import { Sparkles, Check, Plus, X } from "lucide-react"

interface Step4InterestsProps {
  selected: string[]
  onChange: (interests: string[]) => void
}

const CATEGORIZED_INTERESTS: { category: string; items: string[] }[] = [
  {
    category: "STEM & Technology",
    items: ["Technology", "Computer Programming", "Mathematics", "Physics", "Biology", "Chemistry"],
  },
  {
    category: "Business & Society",
    items: ["Business", "Economics", "Finance", "Law & Governance", "Psychology"],
  },
  {
    category: "Creative & Media",
    items: ["Art & Design", "Literature & Writing", "Media & Video", "Music"],
  },
  {
    category: "Applied & Life",
    items: ["Environment", "Sports & Fitness", "Health & Wellness", "Community Impact"],
  },
]

export function Step4Interests({ selected, onChange }: Step4InterestsProps) {
  const [customInput, setCustomInput] = useState("")

  const toggleInterest = (item: string) => {
    if (selected.includes(item)) {
      onChange(selected.filter((i) => i !== item))
    } else {
      onChange([...selected, item])
    }
  }

  const handleAddCustom = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    const trimmed = customInput.trim()
    if (!trimmed) return
    if (!selected.includes(trimmed)) {
      onChange([...selected, trimmed])
    }
    setCustomInput("")
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA] mb-3">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Step 4: Interests</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F1F5F9]">
          What subjects or areas interest you?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          Select the subjects and domains you genuinely enjoy. This personalizes opportunities, scholarships, and career matching.
        </p>
      </div>

      <div className="space-y-5 mt-4">
        {CATEGORIZED_INTERESTS.map((group) => (
          <div key={group.category} className="space-y-2.5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#64748B]">
              {group.category}
            </span>
            <div className="flex flex-wrap gap-2">
              {group.items.map((item) => {
                const isSelected = selected.includes(item)
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleInterest(item)}
                    className={cn(
                      "inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-semibold transition-all duration-200 border",
                      isSelected
                        ? "border-[#3B82F6] bg-[#3B82F6]/15 text-[#60A5FA] shadow-[0_0_12px_rgba(59,130,246,0.25)]"
                        : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/50 hover:bg-[#1C2539] hover:text-[#F1F5F9]"
                    )}
                  >
                    {isSelected ? (
                      <Check className="h-3.5 w-3.5 text-[#3B82F6] stroke-[3px]" />
                    ) : null}
                    <span>{item}</span>
                  </button>
                )
              })}
            </div>
          </div>
        ))}

        {/* Custom Interest Input */}
        <div className="pt-2">
          <form onSubmit={handleAddCustom} className="flex gap-2 max-w-md">
            <input
              type="text"
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              placeholder="Other interest (e.g. Robotics, Debate)..."
              className="flex-1 h-10 px-3.5 rounded-[8px] border border-[#2A3650] bg-[#111827] text-xs text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
            />
            <button
              type="button"
              onClick={handleAddCustom}
              className="inline-flex items-center gap-1 h-10 px-4 rounded-[8px] bg-[#1C2539] border border-[#2A3650] hover:border-[#3B82F6] text-xs font-semibold text-[#F1F5F9] transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add</span>
            </button>
          </form>
        </div>

        {/* Selected count / tags */}
        {selected.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#1E2D42]">
            <span className="text-xs text-[#64748B]">Selected ({selected.length}):</span>
            {selected.map((item) => (
              <span
                key={item}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#1C2539] border border-[#2A3650] text-[11px] font-medium text-[#E2E8F0]"
              >
                <span>{item}</span>
                <button
                  type="button"
                  onClick={() => toggleInterest(item)}
                  className="hover:text-rose-400 ml-0.5"
                  aria-label={`Remove ${item}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
