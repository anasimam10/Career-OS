import type { DemandLevel, CompetitionLevel, DifficultyLevel } from "@/lib/types/career.types"
import { TrendingUp, Users, Award } from "lucide-react"
import { cn } from "@/lib/utils/cn"

interface CareerMetricBarProps {
  label: string
  level: DemandLevel | CompetitionLevel | DifficultyLevel
  description?: string
  evidenceCount?: number
}

export function CareerMetricBar({ label, level, description, evidenceCount }: CareerMetricBarProps) {
  const isDemand = label.toLowerCase().includes("demand")
  const isCompetition = label.toLowerCase().includes("competition")
  
  // High demand is positive (emerald/indigo); high competition is demanding (amber); high difficulty is notable (indigo)
  const getBadgeStyle = () => {
    if (isDemand) {
      if (level === "HIGH") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
      if (level === "MEDIUM") return "bg-indigo-500/10 text-indigo-400 border-indigo-500/30"
      return "bg-slate-800/50 text-slate-400 border-slate-700"
    }
    if (isCompetition) {
      if (level === "HIGH") return "bg-amber-500/10 text-amber-400 border-amber-500/30"
      if (level === "MEDIUM") return "bg-slate-800/50 text-slate-300 border-slate-700"
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
    }
    // Difficulty
    if (level === "HIGH") return "bg-indigo-500/10 text-indigo-400 border-indigo-500/30"
    if (level === "MEDIUM") return "bg-slate-800/50 text-slate-300 border-slate-700"
    return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
  }

  const getIcon = () => {
    if (isDemand) return <TrendingUp className="h-4 w-4 text-emerald-500" />
    if (isCompetition) return <Users className="h-4 w-4 text-amber-500" />
    return <Award className="h-4 w-4 text-indigo-500" />
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-sm hover:border-slate-700 transition-colors">
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800/80 border border-slate-700">
            {getIcon()}
          </div>
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            {label}
          </span>
        </div>
        <span
          className={cn("inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase border", getBadgeStyle())}
        >
          {level}
        </span>
      </div>
      
      {description && (
        <p className="text-xs text-slate-400 leading-relaxed pt-2 border-t border-slate-800/50">
          {description}
        </p>
      )}

      {evidenceCount !== undefined && evidenceCount > 0 && (
        <div className="mt-3 flex items-center gap-2 text-[10px] font-medium text-slate-500">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
          <span>Backed by {evidenceCount} verified Pakistan data records</span>
        </div>
      )}
    </div>
  )
}
