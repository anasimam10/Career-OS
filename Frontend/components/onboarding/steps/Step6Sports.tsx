"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils/cn"
import { Trophy, Check, XCircle } from "lucide-react"

interface Step6SportsProps {
  value: string | null
  onChange: (sport: string | null) => void
}

const PAKISTAN_SPORTS = [
  "Cricket",
  "Football",
  "Badminton",
  "Hockey",
  "Tennis",
  "Squash",
  "Swimming",
  "Basketball",
  "Athletics",
  "Volleyball",
  "Table Tennis",
]

export function Step6Sports({ value, onChange }: Step6SportsProps) {
  const [isInterested, setIsInterested] = useState<boolean>(() => value !== null && value !== "No sport")

  const handleToggleInterest = (interested: boolean) => {
    setIsInterested(interested)
    if (!interested) {
      onChange(null)
    } else if (!value || value === "No sport") {
      onChange("Cricket") // default to primary sport if none selected yet
    }
  }

  const handleSelectSport = (sport: string) => {
    onChange(sport)
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-semibold text-[#60A5FA] mb-3">
          <Trophy className="h-3.5 w-3.5" />
          <span>Step 6: Sports Pathway</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F1F5F9]">
          Are you interested in sports or pursuing a sports pathway?
        </h2>
        <p className="mt-2 text-sm text-[#94A3B8]">
          Sports participation can unlock university admission quotas, athletic trials, and sports scholarships in Pakistan.
        </p>
      </div>

      {/* Two Primary Choices */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        <button
          type="button"
          onClick={() => handleToggleInterest(false)}
          className={cn(
            "flex flex-col justify-between p-5 rounded-[12px] border text-left transition-all duration-200 group relative",
            !isInterested
              ? "border-[#3B82F6] bg-[#3B82F6]/10 text-[#F1F5F9] shadow-[0_0_16px_rgba(59,130,246,0.2)]"
              : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/50 hover:bg-[#1C2539]"
          )}
        >
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-[#64748B]" />
              <span className="text-sm font-bold text-[#F1F5F9]">No, focus on academics</span>
            </div>
            <div
              className={cn(
                "h-5 w-5 rounded-full border flex items-center justify-center transition-colors shrink-0",
                !isInterested ? "border-[#3B82F6] bg-[#3B82F6] text-white" : "border-[#2A3650] bg-[#0B0F1A]"
              )}
            >
              {!isInterested && <Check className="h-3 w-3 text-white stroke-[3px]" />}
            </div>
          </div>
          <p className="text-xs text-[#64748B] mt-2">
            Proceed with regular academic and career pathways without athletic quotas.
          </p>
        </button>

        <button
          type="button"
          onClick={() => handleToggleInterest(true)}
          className={cn(
            "flex flex-col justify-between p-5 rounded-[12px] border text-left transition-all duration-200 group relative",
            isInterested
              ? "border-[#3B82F6] bg-[#3B82F6]/10 text-[#F1F5F9] shadow-[0_0_16px_rgba(59,130,246,0.2)]"
              : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#3B82F6]/50 hover:bg-[#1C2539]"
          )}
        >
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Trophy className="h-4 w-4 text-[#EAB308]" />
              <span className="text-sm font-bold text-[#F1F5F9]">Yes, I play or want to explore sports</span>
            </div>
            <div
              className={cn(
                "h-5 w-5 rounded-full border flex items-center justify-center transition-colors shrink-0",
                isInterested ? "border-[#3B82F6] bg-[#3B82F6] text-white" : "border-[#2A3650] bg-[#0B0F1A]"
              )}
            >
              {isInterested && <Check className="h-3 w-3 text-white stroke-[3px]" />}
            </div>
          </div>
          <p className="text-xs text-[#64748B] mt-2">
            Receive university sports quota alerts, club trials, and athletic tournament info.
          </p>
        </button>
      </div>

      {/* Sport Selector if Interested */}
      {isInterested && (
        <div className="space-y-3 pt-3 border-t border-[#1E2D42] animate-in fade-in duration-300">
          <span className="text-xs font-bold uppercase tracking-wider text-[#64748B]">
            Select Your Primary Sport of Interest:
          </span>
          <div className="flex flex-wrap gap-2.5">
            {PAKISTAN_SPORTS.map((sport) => {
              const selected = value === sport
              return (
                <button
                  key={sport}
                  type="button"
                  onClick={() => handleSelectSport(sport)}
                  className={cn(
                    "inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold transition-all duration-200 border",
                    selected
                      ? "border-[#EAB308] bg-[#EAB308]/15 text-[#FDE047] shadow-[0_0_12px_rgba(234,179,8,0.25)]"
                      : "border-[#2A3650] bg-[#111827] text-[#94A3B8] hover:border-[#EAB308]/50 hover:bg-[#1C2539] hover:text-[#F1F5F9]"
                  )}
                >
                  {selected && <Check className="h-3.5 w-3.5 text-[#EAB308] stroke-[3px]" />}
                  <span>{sport}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
