"use client"

import Link from "next/link"
import {
  MessageSquare,
  Target,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Activity,
  Briefcase,
  Trophy,
  ShieldCheck,
  Navigation,
} from "lucide-react"

export function FeaturesSection() {
  return (
    <div className="bg-[#05080E] border-t border-slate-800/80">
      <div className="space-y-32 max-w-7xl mx-auto px-4 sm:px-6 py-24">
        
        {/* ── 0. TRUST SECTION ──────────────────────────────── */}
        <section className="relative">
          <div className="absolute inset-0 bg-indigo-500/5 blur-[100px] rounded-full pointer-events-none" />
          <div className="text-center mb-16">
            <h2 className="text-sm font-bold tracking-widest text-indigo-400 uppercase">
              Built on Ground Truth
            </h2>
            <p className="mt-4 text-3xl sm:text-4xl font-extrabold text-white">
              Real Information. Real Pathways.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm transition-all hover:border-slate-700 hover:bg-slate-900/60 group">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-indigo-400 mb-5 group-hover:scale-110 transition-transform shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                <Target className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white">22 Reality Checks</h3>
              <p className="mt-2.5 text-xs text-slate-400 leading-relaxed">
                Unvarnished data on competition, demand, and starting salary ranges grounded in official Pakistan Bureau of Statistics benchmarks.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm transition-all hover:border-slate-700 hover:bg-slate-900/60 group">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-indigo-400 mb-5 group-hover:scale-110 transition-transform shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                <Navigation className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white">160+ Universities & 1,981 Faculty</h3>
              <p className="mt-2.5 text-xs text-slate-400 leading-relaxed">
                160+ HEC-recognized universities across Pakistan, enriched with Pakistan Intellectual Capital CS faculty profiles, PhD research specializations, and time-series data.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm transition-all hover:border-slate-700 hover:bg-slate-900/60 group">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-indigo-400 mb-5 group-hover:scale-110 transition-transform shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white">38 Opportunities</h3>
              <p className="mt-2.5 text-xs text-slate-400 leading-relaxed">
                Active software & business internships, HEC/Ehsaas/PEEF scholarships, and real industry placements verified right now.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm transition-all hover:border-slate-700 hover:bg-slate-900/60 group">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 text-amber-400 mb-5 group-hover:scale-110 transition-transform shadow-[0_0_15px_rgba(245,158,11,0.2)]">
                <Trophy className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white">18 Sports Trials</h3>
              <p className="mt-2.5 text-xs text-slate-400 leading-relaxed">
                PCB, PHF, and PSB verified athletic development pathways, national academy trials, and provincial sports quotas.
              </p>
            </div>
          </div>
        </section>

        {/* ── 1. DUALITY SECTION ─────────────────────────────── */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          {/* Left Column - Career vs Sport Narrative */}
          <div className="space-y-8">
            <div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-[1.1]">
                Two Distinct Paths. <br />
                <span className="text-indigo-400">One Intelligent Engine.</span>
              </h2>
              <p className="mt-6 text-lg text-slate-400 leading-relaxed max-w-xl">
                Whether you&apos;re aiming for a technical degree or pursuing professional sports trials, the engine adapts, filtering out the noise to show you exactly what matters.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/careers"
                className="group relative flex items-center justify-between p-6 rounded-2xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800/80 transition-all overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative z-10 flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-950 text-indigo-400 border border-indigo-900/50">
                    <Briefcase className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Career Pathways</h3>
                    <p className="text-sm text-slate-500">Degrees, skills & jobs</p>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-slate-600 group-hover:text-indigo-400 transition-colors relative z-10" />
              </Link>

              <Link
                href="/sports"
                className="group relative flex items-center justify-between p-6 rounded-2xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800/80 transition-all overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-amber-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative z-10 flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-950/50 text-amber-500 border border-amber-900/50">
                    <Trophy className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Sports Pathways</h3>
                    <p className="text-sm text-slate-500">Trials & tournaments</p>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-slate-600 group-hover:text-amber-500 transition-colors relative z-10" />
              </Link>
            </div>
          </div>

          {/* Right Column - Visual Abstract */}
          <div className="relative h-[400px] lg:h-[500px] rounded-[2rem] border border-slate-800/60 bg-slate-900/40 p-8 overflow-hidden flex items-center justify-center">
             <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),rgba(5,8,14,0))]" />
             
             {/* Abstract Engine Visual */}
             <div className="relative z-10 w-full max-w-sm">
                <div className="flex flex-col gap-6">
                  {/* Career Node */}
                  <div className="flex items-center gap-4 transform -translate-x-4">
                    <div className="h-[2px] w-12 bg-indigo-500/50" />
                    <div className="px-4 py-2 rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-sm font-medium backdrop-blur-md shadow-[0_0_15px_rgba(99,102,241,0.15)]">
                      Analyzing Market Demand
                    </div>
                  </div>
                  
                  {/* Central Node */}
                  <div className="flex items-center justify-center my-2">
                    <div className="h-16 w-16 rounded-full border border-slate-700 bg-slate-800/80 flex items-center justify-center shadow-xl z-20 relative">
                       <Activity className="h-6 w-6 text-white" />
                       <div className="absolute inset-0 rounded-full border border-indigo-500/30 animate-ping opacity-20" />
                    </div>
                  </div>

                  {/* Sport Node */}
                  <div className="flex items-center justify-end gap-4 transform translate-x-4">
                    <div className="px-4 py-2 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-300 text-sm font-medium backdrop-blur-md shadow-[0_0_15px_rgba(245,158,11,0.15)]">
                      Identifying Local Trials
                    </div>
                    <div className="h-[2px] w-12 bg-amber-500/50" />
                  </div>
                </div>
             </div>
          </div>
        </section>

        {/* ── 2. NEXT BEST ACTION HIGHLIGHT ─────────────────────────────── */}
        <section className="relative rounded-[3rem] border border-slate-800 bg-slate-900/60 overflow-hidden text-center py-24 px-6">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.1),transparent)] pointer-events-none" />
          
          <div className="relative z-10 max-w-3xl mx-auto space-y-8">
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-5 py-2 text-sm font-bold tracking-wider text-amber-500 uppercase">
              <Sparkles className="h-4 w-4" />
              <span>Signature Feature</span>
            </div>
            
            <h2 className="text-3xl sm:text-5xl font-extrabold text-white">
              Always Know Your <br />
              <span className="text-amber-500">Next Best Action.</span>
            </h2>
            
            <p className="text-lg text-slate-400 max-w-xl mx-auto">
              You don&apos;t need a massive 10-year plan that will break tomorrow. You just need to know the single highest-leverage move you can make today.
            </p>

            <div className="pt-8">
              <Link
                href="/onboarding"
                className="inline-flex items-center gap-2 h-14 px-8 rounded-full bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-base transition-transform hover:scale-105 shadow-[0_0_30px_rgba(245,158,11,0.3)]"
              >
                <span>Get Your Next Step</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
