import { FUTURE_GOAL_OPTIONS } from "@/lib/mock/onboarding.mock"

interface Step6FutureProps {
  selectedGoals: string[]
  city: string // Kept in interface to avoid breaking OnboardingWizard if it passes it, but won't use it
  onToggleGoal: (goal: string) => void
  onCityChange: (city: string) => void // Same here
}

export function Step6Future({
  selectedGoals,
  onToggleGoal,
}: Step6FutureProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          What would help you most right now?
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Select your primary goals. We&apos;ll prioritize opportunities that align with these.
        </p>
      </div>

      <div className="flex flex-col gap-3 mt-6">
        {FUTURE_GOAL_OPTIONS.map((goal) => {
          const isSelected = selectedGoals.includes(goal)
          return (
            <button
              key={goal}
              onClick={() => onToggleGoal(goal)}
              className={`text-left px-5 py-4 rounded-xl text-sm font-medium transition-all duration-300 border ${
                isSelected
                  ? "bg-indigo-600/20 border-indigo-500 text-indigo-50 shadow-[0_0_15px_rgba(99,102,241,0.2)]"
                  : "bg-slate-900/50 border-slate-700 text-slate-300 hover:border-slate-500 hover:bg-slate-800"
              }`}
            >
              {goal}
            </button>
          )
        })}
      </div>
    </div>
  )
}
