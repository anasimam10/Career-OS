import Link from "next/link"
import { ArrowRight, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { type CareerListItem } from "@/lib/types/career.types"
import { cn } from "@/lib/utils/cn"

const FIELD_DESCRIPTIONS: Record<string, string> = {
  "Technology": "High-growth software exports, domestic tech houses, and remote engineering roles.",
  "Healthcare": "Hospital clinical training, PMDC licensing, and public/private healthcare demands.",
  "Business": "Corporate finance, audit firms, supply chain, and banking across business hubs.",
  "Engineering": "Civil infrastructure, power systems, industrial manufacturing, and PEC registration.",
  "Design": "User experience, product design, and creative advertising agencies.",
  "Media & Communications": "Broadcast journalism, digital media strategy, and corporate communication.",
}

export function CareerCard({ career }: { career: CareerListItem }) {
  const isHighDemand = career.demand_level === "HIGH"
  const isMediumDemand = career.demand_level === "MEDIUM"

  const demandClass = isHighDemand
    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
    : isMediumDemand
    ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/30"
    : "bg-slate-800/50 text-slate-400 border-slate-700"

  const DemandIcon = isHighDemand ? TrendingUp : isMediumDemand ? Minus : TrendingDown

  const description =
    FIELD_DESCRIPTIONS[career.field] ||
    `Verified Pakistan labour statistics, required entry exams, and top universities for ${career.name}.`

  return (
    <div className="group relative flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm transition-all hover:border-slate-700 hover:bg-slate-900/60 overflow-hidden">
      {/* Subtle background abstract motif */}
      <div className="absolute -right-12 -top-12 h-32 w-32 rounded-full bg-indigo-500/5 blur-2xl transition-all group-hover:bg-indigo-500/10 pointer-events-none" />
      
      <div className="relative z-10 space-y-4">
        <div className="flex items-start justify-between gap-2">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            {career.field}
          </span>
          <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase border", demandClass)}>
            <DemandIcon className="h-3 w-3" />
            {career.demand_level}
          </span>
        </div>
        
        <div>
          <h3 className="text-xl font-bold text-white group-hover:text-indigo-300 transition-colors">
            {career.name}
          </h3>
          <p className="text-sm text-slate-400 leading-relaxed mt-2 line-clamp-2">
            {description}
          </p>
        </div>
      </div>

      <div className="relative z-10 pt-5 mt-auto flex flex-col gap-2">
        <Link 
          href={`/careers/${career.slug}/reality-check`}
          className="flex items-center justify-between w-full p-2.5 px-3.5 rounded-xl border border-blue-500/30 bg-blue-600/10 text-xs font-semibold text-blue-300 hover:bg-blue-600 hover:text-white transition-all group/btn"
        >
          <span>Run Reality Check</span>
          <div className="h-5 w-5 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 group-hover/btn:bg-white group-hover/btn:text-blue-600 transition-colors">
            <ArrowRight className="h-3 w-3" />
          </div>
        </Link>

        <Link
          href={`/careers/${career.slug}/trial`}
          className="flex items-center justify-center gap-1.5 w-full py-2 rounded-lg border border-slate-800 bg-slate-900/60 text-[11px] font-medium text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors"
        >
          <span>Start 7-Day Trial →</span>
        </Link>
      </div>
    </div>
  )
}

