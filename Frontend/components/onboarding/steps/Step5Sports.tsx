import { SPORTS_OPTIONS } from "@/lib/mock/onboarding.mock"

interface Step5SportsProps {
  selected: string | null
  onSelect: (sport: string | null) => void
}

export function Step5Sports({ selected, onSelect }: Step5SportsProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Does sport have a place in your future?
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Sports can open university trials, scholarships, and team opportunities in Pakistan.
        </p>
      </div>

      <div className="flex flex-wrap gap-3 mt-6">
        {SPORTS_OPTIONS.map((sport) => {
          const isSelected = selected === sport
          return (
            <button
              key={sport}
              onClick={() => onSelect(isSelected ? null : sport)}
              className={`px-4 py-2.5 rounded-full text-sm font-medium transition-all duration-300 border ${
                isSelected
                  ? "bg-amber-500/20 border-amber-500 text-amber-100 shadow-[0_0_15px_rgba(245,158,11,0.2)]"
                  : "bg-slate-900/50 border-slate-700 text-slate-300 hover:border-slate-500 hover:bg-slate-800"
              }`}
            >
              {sport}
            </button>
          )
        })}
      </div>
    </div>
  )
}

