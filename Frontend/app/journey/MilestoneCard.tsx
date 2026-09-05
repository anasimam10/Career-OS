"use client"

import React from "react"
import Link from "next/link"
import { CheckCircle2, Lock, Loader2, AlertCircle, ArrowUpRight } from "lucide-react"
import type { JourneyStep } from "@/lib/types/journey.types"
import { resolveMilestoneCTA } from "@/lib/constants/journeyCta"

export type MilestoneCardState = "completed" | "active" | "locked"

interface MilestoneCardProps {
  step: JourneyStep
  phaseIndex: number
  phaseLabel?: string
  state: MilestoneCardState
  careerSlug?: string
  onComplete?: (stepId?: number) => void
  isCompleting?: boolean
  error?: string | null
}

export function MilestoneCard({
  step,
  phaseIndex,
  phaseLabel,
  state,
  careerSlug = "software-engineering",
  onComplete,
  isCompleting = false,
  error = null,
}: MilestoneCardProps) {
  const displayPhase = phaseLabel || `Phase ${phaseIndex} · ${step.title.split(" ")[0] || "Step"}`
  const cta = resolveMilestoneCTA(step.title, careerSlug)

  return (
    <div
      id={`milestone-${step.id ?? phaseIndex}`}
      className={`relative rounded-[16px] border p-6 transition-all duration-300 flex flex-col justify-between min-h-[220px] ${
        state === "completed"
          ? "border-l-4 border-l-emerald-500 border-[#2A3650] bg-[#111827]"
          : state === "active"
          ? "border-blue-500 border-2 bg-[#111827] shadow-[0_0_24px_rgba(59,130,246,0.18)] ring-1 ring-blue-500/30"
          : "opacity-40 border-[#2A3650]/60 bg-[#111827]/50 select-none"
      }`}
    >
      <div>
        {/* Phase Header */}
        <div className="flex items-center justify-between text-xs font-semibold text-[#94A3B8] mb-3">
          <div className="flex items-center gap-2">
            {state === "completed" ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            ) : state === "active" ? (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
              </span>
            ) : (
              <Lock className="h-3.5 w-3.5 text-[#64748B] shrink-0" />
            )}
            <span className={state === "completed" ? "text-emerald-400" : state === "active" ? "text-blue-400" : "text-[#64748B]"}>
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
          <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
            <CheckCircle2 className="w-4 h-4" />
            <span>Completed</span>
          </div>
        ) : state === "active" ? (
          <div className="flex items-center gap-3">
            {cta && (
              <Link
                href={cta.href}
                className="inline-flex items-center gap-2 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
              >
                <span>{cta.label}</span>
                <ArrowUpRight className="w-4 h-4" />
              </Link>
            )}
            <button
              type="button"
              onClick={() => onComplete && onComplete(step.id)}
              disabled={isCompleting}
              className="ml-auto inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
            >
              {isCompleting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>Mark as completed</span>
              )}
            </button>
          </div>
        ) : null}
      </div>
    </div>
  )
}
