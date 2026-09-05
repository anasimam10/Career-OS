"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowRight, Sparkles, Loader2, CheckCircle2 } from "lucide-react"
import { setupMockInterview } from "@/lib/api/mock-interview"

const SUGGESTIONS = [
  "Software Engineering",
  "Accounting & Finance",
  "Data Science",
  "Cyber Security",
]

const LOADING_STAGES = [
  "Grounding in Pakistani industry requirements & skills...",
  "Curating targeted assessment questions...",
  "Verifying scoring rubric & learning resources...",
]

export function MockInterviewSetup() {
  const router = useRouter()
  const [careerContext, setCareerContext] = useState("")
  const [difficulty, setDifficulty] = useState("beginner")
  const [loading, setLoading] = useState(false)
  const [stageIndex, setStageIndex] = useState(0)

  useEffect(() => {
    let timer: NodeJS.Timeout
    if (loading) {
      timer = setInterval(() => {
        setStageIndex((prev) => (prev < LOADING_STAGES.length - 1 ? prev + 1 : prev))
      }, 1400)
    } else {
      setStageIndex(0)
    }
    return () => clearInterval(timer)
  }, [loading])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!careerContext.trim()) return

    try {
      setLoading(true)
      const session = await setupMockInterview(careerContext.trim(), difficulty)
      router.push(`/mock-interview/${session.id}`)
    } catch (error) {
      console.error(error)
      alert("Failed to start mock interview. Please try again.")
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 p-8 rounded-[20px] border border-[#2A3650] bg-[#111827] shadow-2xl">
      <div className="space-y-3 text-center">
        <span className="text-xs font-medium tracking-wider text-[#94A3B8] uppercase">
          Mock interview
        </span>
        <h1 className="text-3xl md:text-4xl font-extrabold text-[#F1F5F9]">
          Practice before the real interview
        </h1>
        <p className="text-[#94A3B8] text-sm max-w-md mx-auto">
          Answer targeted questions and find out where you need more preparation.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-[#F1F5F9]">Career / Field</label>
          <input
            required
            type="text"
            value={careerContext}
            onChange={(e) => setCareerContext(e.target.value)}
            placeholder="e.g. Software Engineering"
            disabled={loading}
            className="w-full px-4 py-2.5 rounded-[8px] border border-[#1E2D42] bg-[#0B0F1A] text-[#F1F5F9] placeholder-[#4B5563] focus:outline-none focus:border-[#2563EB] transition-colors disabled:opacity-50 text-sm"
          />
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] text-[#64748B] mr-1">Popular:</span>
            {SUGGESTIONS.map((item) => (
              <button
                key={item}
                type="button"
                disabled={loading}
                onClick={() => setCareerContext(item)}
                className="rounded-[6px] border border-[#1E2D42] bg-[#1C2539]/60 px-2.5 py-1 text-[11px] font-medium text-[#94A3B8] hover:text-[#F1F5F9] hover:border-[#2A3A54] transition"
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-[#F1F5F9]">Difficulty</label>
          <div className="grid grid-cols-3 gap-2.5">
            {(["beginner", "intermediate", "advanced"] as const).map((lvl) => (
              <button
                key={lvl}
                type="button"
                disabled={loading}
                onClick={() => setDifficulty(lvl)}
                className={`rounded-[8px] py-2.5 px-4 text-xs font-semibold capitalize transition-all border ${
                  difficulty === lvl
                    ? "bg-[#2563EB] border-[#2563EB] text-white shadow-sm"
                    : "bg-[#1C2539] border-[#1E2D42] text-[#94A3B8] hover:text-[#F1F5F9] hover:bg-[#1C2539]/80"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="space-y-3 rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 text-indigo-400 animate-spin flex-shrink-0" />
              <div className="text-xs font-semibold text-indigo-300">
                {LOADING_STAGES[stageIndex]}
              </div>
            </div>
            <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-amber-500 transition-all duration-500"
                style={{ width: `${((stageIndex + 1) / LOADING_STAGES.length) * 100}%` }}
              />
            </div>
          </div>
        ) : (
          <button
            type="submit"
            disabled={loading}
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 px-8 py-4 text-base font-bold text-slate-950 shadow-[0_0_20px_rgba(245,158,11,0.2)] hover:bg-amber-400 transition-all hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
          >
            Start an Interview
            <ArrowRight className="h-5 w-5" />
          </button>
        )}
      </form>
    </div>
  )
}
