"use client"

import { Check, X, ArrowRight, BookOpen } from "lucide-react"

interface MockInterviewResultsProps {
  results: any
  onNewInterview: () => void
}

export function InterviewResults({ results, onNewInterview }: MockInterviewResultsProps) {
  const {
    score,
    total_correct,
    total_questions,
    performance_label,
    topic_performance,
    questions_review,
    next_best_action_text
  } = results

  return (
    <div className="max-w-4xl mx-auto space-y-16 py-8">
      
      {/* Hero Result */}
      <div className="text-center space-y-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">Interview complete.</h1>
        <div className="inline-block p-12 rounded-full border-8 border-indigo-500/20 bg-indigo-500/10 shadow-[0_0_50px_rgba(99,102,241,0.15)]">
          <div className="text-6xl font-black text-white">{Math.round(score)}%</div>
          <div className="text-indigo-400 font-bold mt-2">{total_correct} / {total_questions} correct</div>
        </div>
        <h2 className="text-2xl font-bold text-amber-400">{performance_label}</h2>
      </div>

      {/* Topic Performance */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-white border-b border-slate-800 pb-4">Topics to review</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {topic_performance.map((topic: any, idx: number) => (
            <div key={idx} className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-slate-200">{topic.topic}</span>
                <span className="text-sm font-medium text-slate-400">{topic.correct} / {topic.total}</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-indigo-500"
                  style={{ width: `${(topic.correct / topic.total) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Question Review */}
      <div className="space-y-8">
        <h3 className="text-xl font-bold text-white border-b border-slate-800 pb-4">Detailed Review</h3>
        <div className="space-y-6">
          {questions_review.map((q: any, idx: number) => {
            const isCorrect = q.selected_option_id === q.correct_option_id
            return (
              <div key={q.id} className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
                <div className="flex gap-4">
                  <div className="mt-1">
                    {isCorrect ? (
                      <div className="flex items-center justify-center h-8 w-8 rounded-full bg-green-500/20 text-green-400">
                        <Check className="h-5 w-5" />
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-8 w-8 rounded-full bg-red-500/20 text-red-400">
                        <X className="h-5 w-5" />
                      </div>
                    )}
                  </div>
                  <div className="space-y-4 flex-1">
                    <div className="text-sm font-bold text-slate-500 uppercase tracking-widest">{q.topic}</div>
                    <h4 className="text-xl font-bold text-white leading-snug">{q.question_text}</h4>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                      <div className={`p-4 rounded-xl border ${isCorrect ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
                        <div className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Your Answer</div>
                        <div className="text-slate-300 font-medium">
                          {q.options.find((o: any) => o.id === q.selected_option_id)?.text || "No answer"}
                        </div>
                      </div>
                      
                      {!isCorrect && (
                        <div className="p-4 rounded-xl border border-green-500/30 bg-green-500/5">
                          <div className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Correct Answer</div>
                          <div className="text-green-400 font-medium">
                            {q.options.find((o: any) => o.id === q.correct_option_id)?.text}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="p-5 bg-slate-950 rounded-xl text-slate-300 text-sm leading-relaxed border border-slate-800">
                      <span className="font-bold text-white block mb-2">Why?</span>
                      {q.explanation}
                    </div>

                    {!isCorrect && (q.resource_url || (q.source_resource_ids && q.source_resource_ids.length > 0)) && (
                      <div className="pt-2">
                        <a
                          href={q.resource_url || `/careers`}
                          target={q.resource_url ? "_blank" : "_self"}
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 font-bold text-sm"
                        >
                          <BookOpen className="h-4 w-4" />
                          {q.resource_title ? `Study: ${q.resource_title}` : "Review related resource"}
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Next Best Action */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950/30 border border-indigo-500/20 rounded-[2rem] p-8 sm:p-12 text-center space-y-6 shadow-2xl">
        <h3 className="text-sm font-bold tracking-widest text-indigo-400 uppercase">Next Best Action</h3>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white">{next_best_action_text}</h2>
        {results.next_best_action_url && (
          <div className="pt-1">
            <a
              href={results.next_best_action_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-amber-400 hover:text-amber-300 font-semibold text-sm underline underline-offset-4"
            >
              <BookOpen className="h-4 w-4" />
              Open Recommended Learning Resource
            </a>
          </div>
        )}
        <div className="pt-4">
          <button
            onClick={onNewInterview}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-8 py-4 text-base font-bold text-slate-950 shadow-[0_0_20px_rgba(255,255,255,0.2)] hover:bg-slate-200 transition-all hover:scale-105"
          >
            Start Another Interview
            <ArrowRight className="h-5 w-5" />
          </button>
        </div>
      </div>

    </div>
  )
}
