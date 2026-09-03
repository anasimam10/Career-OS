"use client"

import React, { useState } from "react"
import { Users, GraduationCap, Sparkles, Clock, ArrowRight, X, CheckCircle2, Bell, ShieldCheck, BookOpen } from "lucide-react"

export function TalkToAlumniSection() {
  const [isOpen, setIsOpen] = useState(false)
  const [notified, setNotified] = useState(false)

  return (
    <>
      {/* Visual Entry Point Card */}
      <div className="relative overflow-hidden rounded-3xl border border-indigo-500/20 bg-gradient-to-b from-slate-900/80 to-slate-950 p-8 sm:p-10 shadow-2xl backdrop-blur-md">
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-amber-500/5 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="flex items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-400">
                <Clock className="h-3 w-3" />
                Coming Soon
              </span>
              <span className="text-xs font-medium text-slate-500">• Future Roadmap</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Users className="h-5 w-5" />
              </div>
              <h3 className="text-2xl font-bold tracking-tight text-white">
                Talk to Alumni
              </h3>
            </div>

            <p className="text-base text-slate-300 font-medium leading-relaxed">
              &ldquo;Learn directly from people who have taken the path you&apos;re exploring.&rdquo;
            </p>

            <p className="text-sm text-slate-400 leading-relaxed">
              Connect with graduates from top Pakistani universities and industry professionals to gain candid advice on admissions, entrance tests, campus culture, and early-career realities.
            </p>
          </div>

          <div className="shrink-0">
            <button
              onClick={() => setIsOpen(true)}
              className="inline-flex items-center gap-2 rounded-2xl border border-indigo-500/30 bg-indigo-600/20 px-6 py-3.5 text-sm font-bold text-indigo-300 shadow-lg shadow-indigo-950/50 hover:bg-indigo-600 hover:text-white transition-all hover:scale-105 active:scale-95 cursor-pointer"
            >
              <span>Explore Network Preview</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Informational Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-2xl overflow-hidden rounded-3xl border border-slate-800 bg-[#0B0F17] p-6 sm:p-8 shadow-2xl space-y-6">
            
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1.5">
                <div className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-0.5 text-xs font-semibold text-amber-400">
                  <Sparkles className="h-3 w-3" />
                  Upcoming Feature Preview
                </div>
                <h2 className="text-2xl font-extrabold text-white tracking-tight">
                  Talk to Alumni Network
                </h2>
                <p className="text-sm text-slate-400">
                  Direct mentorship connecting prospective students with verified Pakistani alumni.
                </p>
              </div>

              <button
                onClick={() => setIsOpen(false)}
                className="rounded-full p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Feature Pillars */}
            <div className="grid gap-4 sm:grid-cols-2 pt-2">
              <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-2">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                  <ShieldCheck className="h-4 w-4" />
                  <span>Verified Credentials</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Only graduates with verified degrees from recognized Pakistani institutions (NUST, FAST, LUMS, IBA, GIKI, etc.) participate.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-2">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                  <GraduationCap className="h-4 w-4" />
                  <span>Pathway Matching</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Matched specifically by your chosen Career Field, target programs, and local city constraints.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-2">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                  <BookOpen className="h-4 w-4" />
                  <span>Ground-Truth Advice</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Honest perspectives on entry test preparation, GPA expectations, and real campus placement rates without PR spin.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-2">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                  <Users className="h-4 w-4" />
                  <span>Safe & Grounded</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Structured advisory sessions aligned with Career OS student progression milestones and ethics guidelines.
                </p>
              </div>
            </div>

            {/* Notification / Interest Capture */}
            <div className="rounded-2xl border border-indigo-500/20 bg-indigo-950/30 p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="space-y-1 text-center sm:text-left">
                <div className="text-sm font-bold text-white">Want early access when this launches?</div>
                <p className="text-xs text-indigo-200/80">
                  We are currently onboarding alumni cohorts across computing, engineering, business, and health sciences.
                </p>
              </div>

              {notified ? (
                <div className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500/20 border border-emerald-500/40 px-4 py-2 text-xs font-bold text-emerald-300">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Interest Registered</span>
                </div>
              ) : (
                <button
                  onClick={() => setNotified(true)}
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition-all active:scale-95 shrink-0 shadow-md cursor-pointer"
                >
                  <Bell className="h-3.5 w-3.5" />
                  <span>Notify My Account</span>
                </button>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-xl border border-slate-800 bg-slate-900 px-5 py-2 text-xs font-bold text-slate-300 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
              >
                Back to Pathway
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
