import { CareerMetricBar } from "./CareerMetricBar"
import { MotivationBar } from "./MotivationBar"
import { CareerVerdict } from "./CareerVerdict"
import { ShieldCheck, CheckCircle2, AlertTriangle, Database, Activity, GraduationCap, Building2 } from "lucide-react"
import type { CareerRealityResponse } from "@/lib/types/career.types"

export function RealityCheckPanel({
  data,
  careerSlug,
  topUniversities = [],
}: {
  data: CareerRealityResponse
  careerSlug: string
  topUniversities?: string[]
}) {
  const { reality, verdict } = data

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
      {/* Evidence Provenance Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-indigo-500/20 bg-indigo-500/5 px-6 py-4 text-xs text-slate-300 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-400">
             <Database className="h-4 w-4" />
          </div>
          <span className="leading-relaxed">
            <strong className="text-white tracking-wide">Verified Career Intelligence:</strong> Grounded in official labour market statistics & university records.
          </span>
        </div>
        {reality.data_source && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-900/80 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="h-3.5 w-3.5" />
            Source: {reality.data_source}
          </span>
        )}
      </div>

      {/* 3 Metric Categorical Evidence Signal Chips */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <CareerMetricBar
          label="Market Demand"
          level={reality.demand_level}
          description="Labour market expansion rate across major Pakistani economic hubs."
          evidenceCount={reality.pk_opportunities.length}
        />
        <CareerMetricBar
          label="Competition Level"
          level={reality.competition_level}
          description="Applicant density and academic barrier-to-entry in Pakistan."
        />
        <CareerMetricBar
          label="Technical Rigor"
          level={reality.difficulty_level}
          description="Curriculum intensity and hands-on apprenticeship requirements."
        />
      </div>

      {/* Rewards & Risks Side-by-Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        <div className="rounded-3xl border border-emerald-500/20 bg-slate-900/40 overflow-hidden relative group">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent pointer-events-none" />
          <div className="absolute top-0 right-0 p-6 opacity-20 group-hover:opacity-100 transition-opacity">
            <CheckCircle2 className="h-24 w-24 text-emerald-500 -mr-8 -mt-8" />
          </div>
          
          <div className="p-8 relative z-10">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white tracking-wide">
                Verified Upsides in Pakistan
              </h3>
            </div>
            
            <ul className="space-y-4 text-sm text-slate-300 relative z-10">
              {reality.rewards.map((r, i) => (
                <li key={i} className="flex items-start gap-3 leading-relaxed">
                  <div className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="rounded-3xl border border-amber-500/20 bg-slate-900/40 overflow-hidden relative group">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent pointer-events-none" />
          <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-30 transition-opacity">
            <AlertTriangle className="h-24 w-24 text-amber-500 -mr-8 -mt-8" />
          </div>
          
          <div className="p-8 relative z-10">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20 text-amber-500 border border-amber-500/30">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white tracking-wide">
                Realities & Known Bottlenecks
              </h3>
            </div>
            
            <ul className="space-y-4 text-sm text-slate-300 relative z-10">
              {reality.risks.map((r, i) => (
                <li key={i} className="flex items-start gap-3 leading-relaxed">
                  <div className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Top Pakistani Universities & Degree Pathways */}
      {topUniversities && topUniversities.length > 0 && (
        <div className="rounded-3xl border border-indigo-500/20 bg-slate-900/50 p-8 relative overflow-hidden backdrop-blur-md">
          <div className="flex items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                <GraduationCap className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white tracking-wide">
                  Accredited Pakistani University Pathways
                </h3>
                <p className="text-xs text-slate-400">
                  Leading HEC-recognized institutions offering verified degrees for this career
                </p>
              </div>
            </div>
            <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-indigo-400">
              <Building2 className="h-3.5 w-3.5" />
              {topUniversities.length} Institutions
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {topUniversities.map((uni, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-950/60 p-4 transition-all hover:border-indigo-500/40 hover:bg-slate-900/80 group"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-xs font-bold text-indigo-400 group-hover:bg-indigo-500/20">
                  {idx + 1}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold text-slate-200 group-hover:text-white truncate">
                    {uni}
                  </div>
                  <div className="text-[10px] text-emerald-400 flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 inline-block" />
                    HEC Recognized
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="pt-8">
        <MotivationBar />
      </div>

      <div className="pt-8">
        <CareerVerdict verdict={verdict} careerSlug={careerSlug} />
      </div>
    </div>
  )
}
