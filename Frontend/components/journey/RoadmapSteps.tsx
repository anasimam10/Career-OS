import { CheckCircle2, Clock, ShieldAlert, Sparkles } from "lucide-react"
import type { JourneyStep } from "@/lib/types/journey.types"
import { Button } from "@/components/ui/button"

interface RoadmapStepsProps {
  steps: JourneyStep[]
  onCompleteStep?: (stepId?: number) => void
  completingStepId?: number | null
}

export function RoadmapSteps({ steps, onCompleteStep, completingStepId }: RoadmapStepsProps) {
  // Architecture rule: strictly max 3 steps shown
  const visibleSteps = steps.slice(0, 3)

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {visibleSteps.map((step, idx) => {
        const isCurrentActive = idx === 0
        const isBusy = completingStepId === step.id

        return (
          <div 
            key={step.id ?? idx} 
            className={`group relative rounded-2xl border p-6 backdrop-blur-sm transition-all overflow-hidden flex flex-col justify-between ${
              isCurrentActive 
                ? "border-indigo-500/40 bg-slate-900/70 shadow-[0_0_25px_rgba(99,102,241,0.15)]" 
                : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
            }`}
          >
            {/* Subtle glow on hover */}
            <div className="absolute inset-0 bg-indigo-500/0 group-hover:bg-indigo-500/5 transition-colors pointer-events-none" />
            
            <div className="relative z-10 space-y-4">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className={`font-bold uppercase tracking-wider ${isCurrentActive ? "text-amber-400" : "text-indigo-400"}`}>
                  Phase {idx + 1} {isCurrentActive && "• Active"}
                </span>
                <span className="flex items-center gap-1.5 text-slate-500 bg-slate-950 px-2 py-1 rounded-md border border-slate-800">
                  <Clock className="h-3 w-3" />
                  {step.estimated_duration}
                </span>
              </div>
              
              <h4 className="text-lg font-bold text-white group-hover:text-indigo-300 transition-colors">
                {step.title}
              </h4>
              
              <p className="text-sm text-slate-400 leading-relaxed">
                {step.description}
              </p>
            </div>

            {isCurrentActive && onCompleteStep && (
              <div className="relative z-10 pt-6 mt-4 border-t border-slate-800/60">
                <Button
                  onClick={() => onCompleteStep(step.id)}
                  disabled={isBusy}
                  size="sm"
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl h-9 transition-all shadow-[0_0_15px_rgba(99,102,241,0.3)]"
                >
                  {isBusy ? (
                    <div className="flex items-center gap-2">
                      <div className="h-3.5 w-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                      <span>Completing...</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      <span>Complete Phase {idx + 1}</span>
                    </div>
                  )}
                </Button>
              </div>
            )}
          </div>
        )
      })}

      {steps.length > 3 && (
        <div className="md:col-span-3 flex items-center justify-center p-4">
          <div className="inline-flex items-center gap-2 text-xs font-medium text-slate-500">
            <ShieldAlert className="h-4 w-4" />
            <span>Future sectors remain classified until current operations complete.</span>
          </div>
        </div>
      )}
    </div>
  )
}
