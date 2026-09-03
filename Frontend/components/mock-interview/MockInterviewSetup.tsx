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
    <div className="max-w-2xl mx-auto space-y-8 p-8 rounded-[2rem] border border-slate-800 bg-slate-900/50 backdrop-blur-sm shadow-2xl">
      <div className="space-y-4 text-center">
        <div className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-bold text-amber-400 uppercase tracking-widest">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Interactive Assessment</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white">Practice before the real interview.</h1>
        <p className="text-slate-400 text-sm max-w-md mx-auto">
          Choose what you&apos;re preparing for, answer a short set of questions, and find out where you need more practice.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">Career / Field</label>
          <input
            required
            type="text"
            value={careerContext}
            onChange={(e) => setCareerContext(e.target.value)}
            placeholder="e.g. Software Engineering"
            disabled={loading}
            className="w-full px-4 py-3 rounded-xl border border-slate-700 bg-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50"
          />
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] text-slate-500 mr-1">Popular:</span>
            {SUGGESTIONS.map((item) => (
              <button
                key={item}
                type="button"
                disabled={loading}
                onClick={() => setCareerContext(item)}
                className="rounded-lg border border-slate-800 bg-slate-800/60 px-2.5 py-1 text-[11px] font-medium text-slate-400 hover:text-white hover:border-slate-700 transition"
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">Difficulty</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            disabled={loading}
            className="w-full px-4 py-3 rounded-xl border border-slate-700 bg-slate-800 text-white focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50"
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
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
