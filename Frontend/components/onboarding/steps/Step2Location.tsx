import { MapPin, Navigation } from "lucide-react"

interface Step2LocationProps {
  city: string
  onCityChange: (city: string) => void
}

const CITIES = [
  { id: "Karachi", label: "Karachi", desc: "The commercial hub" },
  { id: "Lahore", label: "Lahore", desc: "The cultural heart" },
  { id: "Islamabad", label: "Islamabad", desc: "The capital city" },
  { id: "Other", label: "Other City", desc: "Elsewhere in Pakistan" }
]

export function Step2Location({ city, onCityChange }: Step2LocationProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Where are you based?
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          We use this to find relevant university campuses, local internships, and sports trials.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        {CITIES.map((c) => {
          const isSelected = city === c.id || (c.id === "Other" && city && !CITIES.map(x=>x.id).includes(city))
          return (
            <button
              key={c.id}
              onClick={() => onCityChange(c.id)}
              className={`relative flex flex-col items-start p-5 rounded-2xl border text-left transition-all overflow-hidden group ${
                isSelected
                  ? "border-indigo-500 bg-indigo-950/30 shadow-[0_0_20px_-5px_rgba(99,102,241,0.3)]"
                  : "border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-800"
              }`}
            >
              {/* Abstract subtle geographic visual */}
              <div className={`absolute -right-4 -bottom-4 opacity-10 transition-transform duration-700 group-hover:scale-110 ${isSelected ? 'text-indigo-500 opacity-20' : 'text-slate-500'}`}>
                <Navigation className="h-24 w-24" />
              </div>
              
              <div className="relative z-10 flex items-center justify-between w-full">
                <div className={`flex h-8 w-8 items-center justify-center rounded-full border ${isSelected ? 'bg-indigo-600 border-indigo-400 text-white' : 'bg-slate-800 border-slate-700 text-slate-400'}`}>
                  <MapPin className="h-4 w-4" />
                </div>
                {isSelected && (
                  <div className="h-2 w-2 rounded-full bg-indigo-500 animate-pulse shadow-[0_0_8px_rgba(99,102,241,1)]" />
                )}
              </div>
              
              <div className="relative z-10 mt-4">
                <h3 className={`text-lg font-bold ${isSelected ? 'text-white' : 'text-slate-200'}`}>
                  {c.label}
                </h3>
                <p className={`text-xs mt-1 ${isSelected ? 'text-indigo-200' : 'text-slate-500'}`}>
                  {c.desc}
                </p>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
