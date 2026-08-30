"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, MessageSquare, Target, Sparkles, ShieldCheck, CheckCircle2, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-[#090e1a] text-white pt-14 pb-20 md:pt-24 md:pb-32">
      {/* Background ambient lighting and subtle perspective grid */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(37,99,235,0.25),rgba(255,255,255,0))] pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />

      <div className="relative mx-auto max-w-5xl px-4 sm:px-6 text-center">
        {/* Category Pill */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-xs font-semibold tracking-wider text-blue-300 uppercase mb-8 backdrop-blur-sm"
        >
          <Sparkles className="h-3.5 w-3.5 text-blue-400" />
          <span>AI-POWERED STUDENT CAREER JOURNEY</span>
        </motion.div>

        {/* Hero Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl leading-[1.1] text-white"
        >
          MAKE A SMARTER <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-white via-slate-100 to-blue-200 bg-clip-text text-transparent">
            CAREER DECISION.
          </span>
          <span className="block mt-2 text-blue-400 font-black">
            KNOW WHAT COMES NEXT.
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="mt-6 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed"
        >
          An AI-powered student career journey that helps you explore options,
          understand the reality of a field, and take your next step with confidence.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Button
            asChild
            size="lg"
            className="w-full sm:w-auto gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold h-13 px-8 text-base shadow-[0_0_25px_rgba(37,99,235,0.4)] hover:shadow-[0_0_35px_rgba(37,99,235,0.6)] transition-all"
          >
            <Link href="/mentor">
              <MessageSquare className="h-5 w-5" />
              <span>Talk to AI Mentor</span>
            </Link>
          </Button>

          <Button
            asChild
            variant="outline"
            size="lg"
            className="w-full sm:w-auto gap-2 border-slate-700 bg-slate-900/60 text-slate-200 hover:bg-slate-800 hover:text-white h-13 px-8 text-base backdrop-blur-sm"
          >
            <Link href="/careers">
              <Target className="h-5 w-5 text-blue-400" />
              <span>Reality-Check a Career</span>
            </Link>
          </Button>
        </motion.div>

        {/* Floating Pathway Concept (Grounded Visual Cue) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-14 max-w-3xl mx-auto rounded-2xl border border-slate-800 bg-slate-900/80 p-4 sm:p-5 backdrop-blur-md shadow-2xl"
        >
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-3 text-slate-300">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400 font-bold text-xs">
                1
              </div>
              <span className="font-medium">Discover Your Interests</span>
            </div>
            <ChevronRight className="h-4 w-4 text-slate-600 hidden sm:block" />
            
            <div className="flex items-center gap-3 text-slate-300">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400 font-bold text-xs">
                2
              </div>
              <span className="font-medium">Run Reality Check</span>
            </div>
            <ChevronRight className="h-4 w-4 text-slate-600 hidden sm:block" />

            <div className="flex items-center gap-3 rounded-xl bg-blue-600/20 border border-blue-500/40 px-3 py-1.5 text-blue-200">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500 text-white font-bold text-xs">
                3
              </div>
              <span className="font-bold">Execute One Next Step</span>
            </div>
          </div>
        </motion.div>

        {/* Trust Badges */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="mt-10 pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400 font-medium"
        >
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Pakistan-Specific Career Realities</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-blue-400" />
            <span>AI Guided by Your Personal Stage</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-4 w-4 text-amber-400" />
            <span>One Step at a Time</span>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
