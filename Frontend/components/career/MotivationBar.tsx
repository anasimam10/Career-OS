import { Sparkles, HeartHandshake, Compass, AlertCircle } from "lucide-react"

interface MotivationBarProps {
  items?: string[]
  reflectionText?: string
}

export function MotivationBar({ items, reflectionText }: MotivationBarProps) {
  const displayTags = items && items.length > 0 ? items : [
    "Genuine passion for the discipline",
    "Long-term financial independence",
    "Desire to build practical solutions in Pakistan",
  ]

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/40 overflow-hidden backdrop-blur-sm">
      <div className="border-b border-slate-800/80 bg-slate-800/30 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
              Self-Reported Motivation Analysis
            </div>
            <h3 className="text-lg font-bold text-white tracking-wide">
              Why Are You Considering This Pathway?
            </h3>
          </div>
        </div>
      </div>
      
      <div className="p-6 space-y-6">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">
            Your Declared Drivers
          </div>
          <div className="flex flex-wrap gap-2.5">
            {displayTags.map((tag, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-2 rounded-lg border border-indigo-500/20 bg-indigo-500/10 px-3.5 py-2 text-xs font-medium text-indigo-300"
              >
                <Compass className="h-3.5 w-3.5 text-indigo-400" />
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-700 bg-slate-800/50 p-5 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
            <HeartHandshake className="h-4 w-4 text-indigo-400" />
            <span>AI Qualitative Synthesis</span>
          </div>
          <p className="text-sm text-slate-400 leading-relaxed">
            {reflectionText ||
              "Your selections indicate intrinsic curiosity combined with a pragmatic goal for financial security. In the Pakistani job market, aligning intrinsic problem-solving skills with practical portfolio building produces the highest resilience."}
          </p>
        </div>

        <div className="flex items-start gap-3 rounded-xl bg-amber-500/5 p-4 border border-amber-500/20 text-xs text-amber-500/90 leading-relaxed">
          <AlertCircle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
          <span>
            <strong className="text-amber-400">Qualitative Reflection:</strong> Based entirely on your self-reported preferences during onboarding. Not a clinical diagnosis and strictly separated from database market facts.
          </span>
        </div>
      </div>
    </div>
  )
}
