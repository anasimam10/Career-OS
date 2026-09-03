import { MOTIVATION_OPTIONS } from "@/lib/mock/onboarding.mock"
import { Sparkles, CheckCircle2, Circle } from "lucide-react"

interface Step4MotivationProps {
  selected: string[]
  onToggle: (tag: string) => void
}

const DESC_MAP: Record<string, string> = {
  "I genuinely love this subject": "I'd still choose this path without outside pressure.",
  "High salary potential": "Financial independence and strong earnings are a priority.",
  "Job security": "I want a stable career path with lower risk.",
  "Family expectations": "My parents or family guided me toward this.",
  "Peer influence": "Friends and people I know are doing this.",
  "Want to help people": "I want to make a meaningful social impact.",
  "Creative expression": "I want to build, design, and create things.",
  "Entrepreneurship": "I want to start my own business eventually.",
}

export function Step4Motivation({ selected, onToggle }: Step4MotivationProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Why are you choosing this field?
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          There is no right answer. Be honest. This helps us understand what&apos;s really influencing your decision.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        {MOTIVATION_OPTIONS.map((opt) => {
          const isSelected = selected.includes(opt)
          return (
            <button
              key={opt}
              onClick={() => onToggle(opt)}
              className={`relative flex flex-col items-start p-5 rounded-2xl border text-left transition-all duration-300 group ${
                isSelected
                  ? "border-indigo-500 bg-indigo-950/20 shadow-[inset_0_0_15px_rgba(99,102,241,0.15)] -translate-y-0.5"
                  : "border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-800"
              }`}
            >
              <div className={`mb-3 transition-colors ${isSelected ? 'text-indigo-400' : 'text-slate-600'}`}>
                <Sparkles className="h-4 w-4" />
              </div>
              
              <h3 className={`text-sm font-bold mb-1.5 transition-colors ${isSelected ? 'text-indigo-50' : 'text-slate-200'}`}>
                {opt}
              </h3>
              
              <p className={`text-xs leading-relaxed transition-colors mb-6 ${isSelected ? 'text-indigo-200/80' : 'text-slate-500'}`}>
                {DESC_MAP[opt] || "This is an important factor for me."}
              </p>
              
              <div className="absolute bottom-4 right-4">
                {isSelected ? (
                  <CheckCircle2 className="h-5 w-5 text-indigo-500 animate-in zoom-in duration-200" />
                ) : (
                  <Circle className="h-5 w-5 text-slate-700 group-hover:text-slate-600 transition-colors" />
                )}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

