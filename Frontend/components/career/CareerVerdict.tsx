import Link from "next/link"
import { CheckCircle2, AlertTriangle, ArrowRight, Sparkles } from "lucide-react"
import type { CareerVerdict as VerdictType } from "@/lib/types/career.types"
import { cn } from "@/lib/utils/cn"

export function CareerVerdict({
  verdict,
  careerSlug,
}: {
  verdict: VerdictType
  careerSlug: string
}) {
  const isGood = verdict.verdict === "GOOD_FIT"
  const isExploring = verdict.verdict === "WORTH_EXPLORING"

  const badgeClass = isGood 
    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" 
    : isExploring 
    ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/30" 
    : "bg-amber-500/10 text-amber-400 border-amber-500/30"

  return (
    <div className="relative rounded-[2rem] border border-indigo-500/30 bg-slate-900/60 overflow-hidden backdrop-blur-md shadow-[0_0_50px_rgba(79,70,229,0.1)]">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(79,70,229,0.15),transparent_70%)] pointer-events-none" />
      
      <div className="relative z-10 p-6 sm:p-10 border-b border-slate-800/80">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
              AI Recommendation
            </span>
          </div>
          <span className={cn("inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold tracking-wider uppercase border", badgeClass)}>
            {verdict.verdict.replace("_", " ")}
          </span>
        </div>
        
        <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mb-4">
          {verdict.headline}
        </h3>
        <p className="text-base text-slate-300 leading-relaxed max-w-3xl">
          {verdict.reasoning}
        </p>
      </div>

      <div className="relative z-10 p-6 sm:p-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-widest text-emerald-400 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Your Strengths
            </h4>
            <ul className="space-y-3 text-sm text-slate-300">
              {verdict.student_strengths_match.map((s, idx) => (
                <li key={idx} className="flex items-start gap-2.5">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span className="leading-relaxed">{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-widest text-amber-500 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Gaps to Address
            </h4>
            <ul className="space-y-3 text-sm text-slate-300">
              {verdict.gaps_to_address.map((g, idx) => (
                <li key={idx} className="flex items-start gap-2.5">
                  <span className="text-amber-500 font-bold">•</span>
                  <span className="leading-relaxed">{g}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="relative z-10 p-6 sm:px-10 sm:py-8 border-t border-slate-800/80 bg-slate-900/50 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="text-sm text-slate-400">
          Suggested action: <strong className="text-white font-semibold">{verdict.suggested_trial || "7-Day Trial"}</strong>
        </div>
        
        <Link 
          href={`/careers/${careerSlug}/trial`}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-8 py-3.5 text-sm font-bold text-white shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:bg-indigo-500 transition-all hover:scale-105 group"
        >
          Start 7-Day Trial
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </div>
  )
}
