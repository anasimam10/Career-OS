"use client"

import { useState } from "react"
import { Check, ChevronDown, ChevronUp, Flag, MapPin, Target } from "lucide-react"
import { STAGE_ORDER, STAGE_LABELS, type EducationStage } from "@/lib/types/journey.types"
import { cn } from "@/lib/utils/cn"

export function JourneyTimeline({ currentStage }: { currentStage: EducationStage }) {
  const [showAllMobile, setShowAllMobile] = useState(false)
  const currentIndex = Math.max(0, STAGE_ORDER.indexOf(currentStage))

  return (
    <div className="relative rounded-3xl border border-slate-800 bg-slate-900/60 p-6 sm:p-10 shadow-2xl overflow-hidden backdrop-blur-md">
      {/* Tactical Map Grid Background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:2rem_2rem] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,#000_20%,transparent_100%)] opacity-20 pointer-events-none" />
      
      <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between mb-12 gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-indigo-400 mb-3">
            <Target className="h-3 w-3" />
            <span>Tactical Map Overview</span>
          </div>
          <h3 className="text-2xl font-bold tracking-tight text-white">
            Current Position: <span className="text-indigo-400">{STAGE_LABELS[currentStage]}</span>
          </h3>
        </div>
        <div className="flex items-center gap-3 text-xs font-semibold text-slate-400">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-indigo-500" />
            <span>Active Sector</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-slate-700" />
            <span>Unexplored</span>
          </div>
        </div>
      </div>

      {/* ── DESKTOP SPATIAL MAP (Hidden on md) ────────────────────── */}
      <div className="hidden md:block relative w-full h-32">
        {/* Continuous Path Line */}
        <div className="absolute top-1/2 left-0 right-0 h-px bg-slate-800 -translate-y-1/2" />
        <div 
          className="absolute top-1/2 left-0 h-px bg-indigo-500 -translate-y-1/2 transition-all duration-1000 shadow-[0_0_10px_rgba(99,102,241,0.5)]" 
          style={{ width: `${(currentIndex / (STAGE_ORDER.length - 1)) * 100}%` }} 
        />

        <div className="absolute inset-0 flex justify-between items-center px-4">
          {STAGE_ORDER.map((stage, idx) => {
            const isCompleted = idx < currentIndex
            const isCurrent = idx === currentIndex
            const isFuture = idx > currentIndex
            
            return (
              <div key={stage} className="relative flex flex-col items-center group w-8">
                {/* Connector Node */}
                <div 
                  className={cn(
                    "relative z-10 h-6 w-6 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                    isCurrent ? "bg-indigo-950 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.4)] scale-125" :
                    isCompleted ? "bg-slate-900 border-indigo-500/50" :
                    "bg-slate-950 border-slate-800"
                  )}
                >
                  {isCurrent ? (
                    <div className="h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
                  ) : isCompleted ? (
                    <Check className="h-3 w-3 text-indigo-400" />
                  ) : (
                    <div className="h-1.5 w-1.5 rounded-full bg-slate-700" />
                  )}
                </div>

                {/* Spatial Label */}
                <div className={cn(
                  "absolute top-8 w-32 text-center transition-all duration-300",
                  isCurrent ? "text-indigo-300 scale-105 font-bold" :
                  isCompleted ? "text-slate-500 font-medium" :
                  "text-slate-600 font-medium opacity-50 group-hover:opacity-100"
                )}>
                  <div className="text-[10px] uppercase tracking-wider mb-0.5 opacity-60">Sector {idx + 1}</div>
                  <div className="text-xs leading-tight">{STAGE_LABELS[stage]}</div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── MOBILE VERTICAL TACTICAL VIEW (md:hidden) ────────────────────── */}
      <div className="md:hidden space-y-4">
        <button
          type="button"
          onClick={() => setShowAllMobile(!showAllMobile)}
          className="w-full flex items-center justify-between p-4 rounded-xl border border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-800 transition"
        >
          <div className="flex items-center gap-3">
             <MapPin className="h-4 w-4 text-indigo-400" />
             <span className="text-sm font-bold">Toggle Full Sector Map</span>
          </div>
          {showAllMobile ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        <div className="relative pl-6 border-l border-slate-800 py-4">
            {STAGE_ORDER.map((stage, idx) => {
              const isCompleted = idx < currentIndex
              const isCurrent = idx === currentIndex
              const isFuture = idx > currentIndex
              
              if (!showAllMobile && !isCurrent && !isFuture && idx !== currentIndex - 1) return null;
              if (!showAllMobile && isFuture && idx !== currentIndex + 1) return null;

              return (
                <div
                  key={stage}
                  className={cn(
                    "relative mb-8 last:mb-0 transition-all duration-500",
                    !isCurrent && !showAllMobile ? "opacity-50" : "opacity-100"
                  )}
                >
                   {/* Vertical Line Overlay (for active trail) */}
                   {isCompleted && (
                     <div className="absolute -left-[25px] top-0 bottom-[-32px] w-px bg-indigo-500/50" />
                   )}
                   
                   {/* Node indicator */}
                   <div 
                     className={cn(
                       "absolute -left-[31px] top-1 h-3 w-3 rounded-full border-2",
                       isCurrent ? "border-indigo-500 bg-indigo-950 shadow-[0_0_10px_rgba(99,102,241,0.5)]" :
                       isCompleted ? "border-indigo-500/50 bg-slate-900" :
                       "border-slate-700 bg-slate-950"
                     )}
                   >
                     {isCurrent && <div className="absolute inset-0 m-auto h-1 w-1 rounded-full bg-indigo-400 animate-pulse" />}
                   </div>

                   <div className={cn(
                     "pl-4",
                     isCurrent ? "text-indigo-300" :
                     isCompleted ? "text-slate-400" :
                     "text-slate-600"
                   )}>
                      <div className="text-[10px] font-bold uppercase tracking-wider mb-1 opacity-70">
                        Sector {idx + 1}
                      </div>
                      <div className={cn(
                        "text-sm",
                        isCurrent ? "font-bold text-white" : "font-medium"
                      )}>
                        {STAGE_LABELS[stage]}
                      </div>
                   </div>
                </div>
              )
            })}
        </div>
      </div>

    </div>
  )
}
