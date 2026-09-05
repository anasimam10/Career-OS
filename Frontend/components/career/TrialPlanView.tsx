"use client"

import React, { useState } from "react"
import Link from "next/link"
import { Calendar, CheckCircle2, ArrowRight, Map, Briefcase, Check } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { CareerTrialPlan } from "@/lib/types/career.types"
import { cn } from "@/lib/utils/cn"

export function TrialPlanView({ plan }: { plan: CareerTrialPlan }) {
  const [completedTasks, setCompletedTasks] = useState<Record<string, boolean>>({})

  const toggleTask = (key: string) => {
    setCompletedTasks((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const totalTasks = plan.days.reduce((acc, d) => acc + d.tasks.length, 0)
  const doneCount = Object.values(completedTasks).filter(Boolean).length
  const progressPct = totalTasks > 0 ? Math.round((doneCount / totalTasks) * 100) : 0

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Progress tracker bar */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400">
              <Calendar className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold text-white">7-Day Hands-on Progress</div>
              <div className="text-xs text-slate-400">Complete tasks to validate if this career matches your working style.</div>
            </div>
          </div>
          <div className="text-xs font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/30 px-3 py-1.5 rounded-lg shrink-0 text-center">
            {doneCount} of {totalTasks} tasks completed ({progressPct}%)
          </div>
        </div>
        <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 transition-all duration-300 rounded-full"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Daily Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {plan.days.map((day, dIdx) => (
          <div
            key={dIdx}
            className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 backdrop-blur-sm hover:border-slate-700 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 border border-blue-500/30 px-2.5 py-0.5 rounded-md">
                  <Calendar className="h-3 w-3" />
                  {day.day_range}
                </span>
                <span className="text-xs text-slate-500">
                  {day.tasks.filter((_, tIdx) => completedTasks[`${dIdx}-${tIdx}`]).length}/{day.tasks.length} done
                </span>
              </div>

              <h3 className="text-lg font-bold text-white mb-4">
                {day.title}
              </h3>

              <ul className="space-y-3">
                {day.tasks.map((task, tIdx) => {
                  const key = `${dIdx}-${tIdx}`
                  const isDone = Boolean(completedTasks[key])
                  return (
                    <li
                      key={tIdx}
                      onClick={() => toggleTask(key)}
                      className={cn(
                        "flex items-start gap-3 p-2.5 rounded-xl border transition-all cursor-pointer select-none text-xs leading-relaxed",
                        isDone
                          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300 line-through"
                          : "border-slate-800/80 bg-slate-950/40 text-slate-300 hover:border-blue-500/30 hover:bg-slate-900/60"
                      )}
                    >
                      <div
                        className={cn(
                          "mt-0.5 h-4 w-4 rounded-md border flex items-center justify-center shrink-0 transition-colors",
                          isDone
                            ? "border-emerald-500 bg-emerald-500 text-white"
                            : "border-slate-600 bg-slate-800"
                        )}
                      >
                        {isDone && <Check className="h-3 w-3 stroke-[3]" />}
                      </div>
                      <span className="flex-1">{task}</span>
                    </li>
                  )
                })}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* End-of-Trial Reflection Card */}
      <div className="rounded-3xl border border-emerald-500/30 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-md relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-transparent pointer-events-none" />
        
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle2 className="h-5 w-5" />
            <span className="text-xs font-bold uppercase tracking-wider">
              Day 7 Evaluation & Next Steps
            </span>
          </div>

          <h3 className="text-xl font-bold text-white">
            Evaluate Your Trial Experience
          </h3>

          <p className="text-sm text-slate-300 leading-relaxed italic border-l-2 border-emerald-500/50 pl-4 py-1">
            &ldquo;{plan.reflection_prompt}&rdquo;
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-800">
            <p className="text-xs text-slate-400">
              Finished exploring? Update your career pathway milestones or find verified Pakistani programs.
            </p>
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
              <Button asChild variant="outline" className="w-full sm:w-auto gap-2 border-slate-700 bg-slate-800 hover:bg-slate-700 text-white text-xs">
                <Link href="/opportunities">
                  <Briefcase className="h-3.5 w-3.5" />
                  Explore Opportunities
                </Link>
              </Button>
              <Button asChild className="w-full sm:w-auto gap-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold">
                <Link href="/journey">
                  <Map className="h-3.5 w-3.5" />
                  Continue My Journey
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
