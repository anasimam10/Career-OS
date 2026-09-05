"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils/cn"
import type { Skill } from "@/lib/types/student.types"
import { Wrench, Check, Plus, X } from "lucide-react"

interface Step5SkillsProps {
  skills: Skill[]
  onChange: (skills: Skill[]) => void
}

const COMMON_SKILLS = [
  "Problem Solving",
  "Communication",
  "Python",
  "JavaScript",
  "Data Analysis",
  "MS Excel",
  "SQL",
  "Git & GitHub",
  "Graphic Design",
  "Public Speaking",
  "Content Writing",
  "Financial Accounting",
  "Critical Thinking",
  "HTML & CSS",
]

export function Step5Skills({ skills, onChange }: Step5SkillsProps) {
  const [customSkillName, setCustomSkillName] = useState("")
  const [customSkillLevel, setCustomSkillLevel] = useState<"beginner" | "intermediate" | "advanced">("beginner")

  const isSelected = (name: string) => skills.some((s) => s.name.toLowerCase() === name.toLowerCase())

  const toggleSkill = (name: string) => {
    if (isSelected(name)) {
      onChange(skills.filter((s) => s.name.toLowerCase() !== name.toLowerCase()))
    } else {
      onChange([...skills, { name, level: "intermediate" }])
    }
  }

  const updateLevel = (name: string, level: "beginner" | "intermediate" | "advanced") => {
    onChange(
      skills.map((s) => (s.name.toLowerCase() === name.toLowerCase() ? { ...s, level } : s))
    )
  }

  const handleAddCustom = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    const trimmed = customSkillName.trim()
    if (!trimmed) return
    if (!isSelected(trimmed)) {
      onChange([...skills, { name: trimmed, level: customSkillLevel }])
    }
    setCustomSkillName("")
  }

  const removeSkill = (name: string) => {
    onChange(skills.filter((s) => s.name.toLowerCase() !== name.toLowerCase()))
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA] mb-3">
          <Wrench className="h-3.5 w-3.5" />
          <span>Step 5: Skills</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F1F5F9]">
          What skills do you already have?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          Select any tools, technologies, or soft skills you have started learning. Don&apos;t worry if you are just getting started.
        </p>
      </div>

      {/* Suggested Common Skills */}
      <div className="space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-[#64748B]">
          Common Skills (Click to select)
        </span>
        <div className="flex flex-wrap gap-2.5">
          {COMMON_SKILLS.map((skillName) => {
            const active = isSelected(skillName)
            return (
              <button
                key={skillName}
                type="button"
                onClick={() => toggleSkill(skillName)}
                className={cn(
                  "inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-semibold transition-all duration-200 border",
                  active
                    ? "border-[#3B82F6] bg-[#3B82F6]/15 text-[#60A5FA] shadow-[0_0_12px_rgba(59,130,246,0.25)]"
                    : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/50 hover:bg-[#1C2539] hover:text-[#F1F5F9]"
                )}
              >
                {active && <Check className="h-3.5 w-3.5 text-[#3B82F6] stroke-[3px]" />}
                <span>{skillName}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Custom Skill Input */}
      <div className="pt-2">
        <form onSubmit={handleAddCustom} className="flex flex-col sm:flex-row gap-2 max-w-lg">
          <input
            type="text"
            value={customSkillName}
            onChange={(e) => setCustomSkillName(e.target.value)}
            placeholder="Other skill (e.g. Flutter, SEO, Figma)..."
            className="flex-1 h-10 px-3.5 rounded-[8px] border border-[#2A3650] bg-[#111827] text-xs text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
          />
          <div className="flex gap-2">
            <select
              value={customSkillLevel}
              onChange={(e) => setCustomSkillLevel(e.target.value as any)}
              className="h-10 px-3 rounded-[8px] border border-[#2A3650] bg-[#111827] text-xs text-[#94A3B8] focus:outline-none focus:border-[#3B82F6]"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
            <button
              type="button"
              onClick={handleAddCustom}
              className="inline-flex items-center gap-1 h-10 px-4 rounded-[8px] bg-[#1C2539] border border-[#2A3650] hover:border-[#3B82F6] text-xs font-semibold text-[#F1F5F9] transition-colors whitespace-nowrap"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Skill</span>
            </button>
          </div>
        </form>
      </div>

      {/* Configured Skill Badges with Proficiency Selector */}
      {skills.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-[#1E2D42]">
          <span className="text-xs text-[#64748B]">Your Active Skills ({skills.length}):</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {skills.map((s) => (
              <div
                key={s.name}
                className="flex items-center justify-between p-2.5 rounded-[8px] bg-[#1C2539]/60 border border-[#2A3650]"
              >
                <span className="text-xs font-semibold text-[#F1F5F9] truncate mr-2">{s.name}</span>
                <div className="flex items-center gap-2 shrink-0">
                  <select
                    value={s.level}
                    onChange={(e) => updateLevel(s.name, e.target.value as any)}
                    className="h-7 px-2 text-[11px] rounded border border-[#2A3650] bg-[#111827] text-[#94A3B8] focus:outline-none"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                  <button
                    type="button"
                    onClick={() => removeSkill(s.name)}
                    className="p-1 hover:text-rose-400 text-[#64748B] transition-colors"
                    aria-label={`Remove ${s.name}`}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
