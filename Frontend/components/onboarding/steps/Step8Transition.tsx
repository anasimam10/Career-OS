import { Sparkles, Activity } from "lucide-react"

export function Step8Transition() {
  return (
    <div className="flex flex-col items-center justify-center text-center space-y-6 animate-in zoom-in-95 fade-in duration-700 min-h-[300px]">
      <div className="relative">
        <div className="absolute inset-0 bg-indigo-500 blur-3xl opacity-20 rounded-full" />
        <div className="relative h-20 w-20 bg-slate-900 border border-indigo-500/50 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(99,102,241,0.3)] mb-8">
          <Activity className="h-8 w-8 text-indigo-400 animate-pulse" />
        </div>
      </div>
      
      <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
        We have a starting point.
      </h2>
      <p className="mt-4 text-lg text-slate-400 max-w-md mx-auto">
        Your profile is set. We&apos;re preparing your personalized milestones and Next Best Action.
      </p>
    </div>
  )
}
