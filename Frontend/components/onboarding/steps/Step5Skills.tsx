import { INTEREST_OPTIONS } from "@/lib/mock/onboarding.mock"

interface Step5SkillsProps {
  selected: string[]
  onToggle: (interest: string) => void
}

export function Step5Skills({ selected, onToggle }: Step5SkillsProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          What are you naturally good at?
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Select all that apply. We use this to identify your core strengths.
        </p>
      </div>

      <div className="flex flex-wrap gap-3 mt-6">
        {INTEREST_OPTIONS.map((interest) => {
          const isSelected = selected.includes(interest)
          return (
            <button
              key={interest}
              onClick={() => onToggle(interest)}
              className={`px-4 py-2.5 rounded-full text-sm font-medium transition-all duration-300 border ${
                isSelected
                  ? "bg-indigo-600 border-indigo-500 text-white shadow-[0_0_15px_rgba(99,102,241,0.4)]"
                  : "bg-slate-900/50 border-slate-700 text-slate-300 hover:border-slate-500 hover:bg-slate-800"
              }`}
            >
              {interest}
            </button>
          )
        })}
      </div>
    </div>
  )
}
