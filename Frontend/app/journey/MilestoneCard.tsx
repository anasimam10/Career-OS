"use client"

import React from "react"
import { CheckCircle2, Lock, Loader2, AlertCircle } from "lucide-react"
import type { JourneyStep } from "@/lib/types/journey.types"

export type MilestoneCardState = "completed" | "active" | "locked"

interface MilestoneCardProps {
  step: JourneyStep
  phaseIndex: number
  phaseLabel?: string
  state: MilestoneCardState
  onComplete?: (stepId?: number) => void
  isCompleting?: boolean
  error?: string | null
}

export function MilestoneCard({
  step,
  phaseIndex,
  phaseLabel,
  state,
  onComplete,
  isCompleting = false,
  error = null,
}: MilestoneCardProps) {
  const displayPhase = phaseLabel || `Phase ${phaseIndex} · ${step.title.split(" ")[0] || "Step"}`

  return (
    <div
      id={`milestone-${step.id ?? phaseIndex}`}
      className={`relative rounded-[16px] border p-6 transition-all duration-300 flex flex-col justify-between min-h-[220px] ${
        state === "completed"
          ? "border-l-4 border-l-[#10B981] border-[#2A3650] bg-[#111827]"
          : state === "active"
          ? "border-[#3B82F6] border-2 bg-[#111827] shadow-[0_0_24px_rgba(59,130,246,0.18)] ring-1 ring-[#3B82F6]/30"
          : "opacity-40 border-[#2A3650]/60 bg-[#111827]/50 select-none"
      }`}
    >
      <div>
        {/* Phase Header */}
        <div className="flex items-center justify-between text-xs font-semibold text-[#94A3B8] mb-3">
          <div className="flex items-center gap-2">
            {state === "completed" ? (
              <CheckCircle2 className="h-4 w-4 text-[#10B981] shrink-0" />
            ) : state === "active" ? (
              <span className="flex h-2.5 w-2.5 rounded-full bg-[#3B82F6] animate-pulse" />
            ) : (
              <Lock className="h-3.5 w-3.5 text-[#64748B] shrink-0" />
            )}
            <span className={state === "completed" ? "text-[#10B981]" : state === "active" ? "text-[#60A5FA]" : "text-[#64748B]"}>
              {displayPhase}
            </span>
          </div>

          {step.estimated_duration && (
            <span className="text-[11px] font-medium text-[#64748B] bg-[#1C2539] px-2.5 py-0.5 rounded-[4px] border border-[#2A3650]">
              {step.estimated_duration}
            </span>
          )}
        </div>

        {/* Milestone Title */}
        <h3 className="text-lg font-bold text-[#F1F5F9] leading-snug mb-2">
          {step.title}
        </h3>

        {/* 1-Line Description */}
        <p className="text-sm text-[#94A3B8] line-clamp-2 leading-relaxed">
          {step.description}
        </p>

        {/* Inline Error (if failed) */}
        {error && (
          <div className="mt-3 flex items-center gap-1.5 text-xs text-rose-400 bg-rose-950/40 border border-rose-900/50 px-3 py-1.5 rounded-[6px]">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Button State */}
      <div className="pt-5 mt-4 border-t border-[#2A3650]/60">
        {state === "completed" ? (
          <button
            type="button"
            disabled
            className="w-full h-11 rounded-[6px] bg-[#1C2539] text-[#94A3B8] font-semibold text-xs tracking-wider uppercase flex items-center justify-center gap-1.5 cursor-not-allowed border border-[#2A3650]/50"
          >
            <span>Completed ✓</span>
          </button>
        ) : state === "active" ? (
          <button
            type="button"
            onClick={() => onComplete && onComplete(step.id)}
            disabled={isCompleting}
            className="w-full h-11 rounded-[6px] bg-[#3B82F6] hover:bg-[#2563EB] active:scale-[0.98] text-white font-bold text-sm flex items-center justify-center gap-2 transition-all duration-150 shadow-md hover:shadow-lg disabled:opacity-75 disabled:cursor-not-allowed"
          >
            {isCompleting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-white" />
                <span>Marking Complete...</span>
              </>
            ) : (
              <span>Mark as Completed</span>
            )}
          </button>
        ) : (
          <div className="h-11 flex items-center justify-center text-xs text-[#64748B] font-medium">
            Upcoming · Complete previous step to unlock
          </div>
        )}
      </div>
    </div>
  )
}
