"use client"

import { useState } from "react"
import { Check } from "lucide-react"

interface Option {
  id: string
  text: string
}

interface InterviewQuestionProps {
  questionNumber: number
  totalQuestions: number
  questionText: string
  options: Option[]
  onNext: (selectedId: string) => void
  isLast: boolean
}

export function InterviewQuestion({
  questionNumber,
  totalQuestions,
  questionText,
  options,
  onNext,
  isLast
}: InterviewQuestionProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  
  const progressPercent = ((questionNumber - 1) / totalQuestions) * 100

  return (
    <div className="max-w-3xl mx-auto space-y-12">
      {/* Header & Progress */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-sm font-bold tracking-widest text-slate-500 uppercase">
          <span>Career OS</span>
          <span>Mock Interview</span>
        </div>
        
        <div className="text-indigo-400 font-medium">
          Question {questionNumber} of {totalQuestions}
        </div>
        
        <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-indigo-500 transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <h2 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight">
        {questionText}
      </h2>

      {/* Options */}
      <div className="space-y-3">
        {options.map((option) => {
          const isSelected = selectedId === option.id
          return (
            <button
              key={option.id}
              onClick={() => setSelectedId(option.id)}
              className={`w-full flex items-center gap-4 p-5 rounded-2xl border text-left transition-all ${
                isSelected 
                  ? "border-indigo-500 bg-indigo-500/10 shadow-[0_0_20px_rgba(99,102,241,0.1)]" 
                  : "border-slate-800 bg-slate-900/50 hover:bg-slate-800"
              }`}
            >
              <div className={`flex items-center justify-center h-8 w-8 rounded-full border text-sm font-bold ${
                isSelected 
                  ? "bg-indigo-500 border-indigo-500 text-white" 
                  : "border-slate-600 text-slate-400"
              }`}>
                {isSelected ? <Check className="h-4 w-4" /> : option.id}
              </div>
              <span className={`text-lg ${isSelected ? "text-white" : "text-slate-300"}`}>
                {option.text}
              </span>
            </button>
          )
        })}
      </div>

      {/* Actions */}
      <div className="pt-8 border-t border-slate-800 flex justify-end">
        <button
          disabled={!selectedId}
          onClick={() => selectedId && onNext(selectedId)}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 px-8 py-4 text-base font-bold text-slate-950 shadow-[0_0_20px_rgba(245,158,11,0.2)] hover:bg-amber-400 transition-all disabled:opacity-50 disabled:hover:bg-amber-500"
        >
          {isLast ? "Finish Interview" : "Next Question"}
        </button>
      </div>
    </div>
  )
}
