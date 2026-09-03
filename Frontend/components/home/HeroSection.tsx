"use client"

import React from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Target, Activity } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative min-h-[90vh] flex items-center bg-[#05080E] text-white pt-20 pb-16 overflow-hidden">
      {/* Cinematic Background Gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_70%_20%,rgba(99,102,241,0.15),rgba(5,8,14,0))] pointer-events-none" />
      <div className="absolute top-1/4 right-0 w-96 h-96 bg-indigo-600/20 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Left Column - Narrative */}
          <div className="lg:col-span-7 z-10 text-left">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-slate-800 bg-slate-900/50 text-xs font-medium tracking-widest text-indigo-400 uppercase mb-6 backdrop-blur-md">
                <Target className="h-3.5 w-3.5" />
                <span>Pakistan&apos;s Premium Career Engine</span>
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-tight">
                Architect Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-blue-300">Future.</span>
              </h1>
              
              <p className="text-lg sm:text-xl text-slate-400 mb-10 max-w-2xl leading-relaxed">
                Ground truth labour data, university pathways, and elite sports opportunities. Verified specifically for the Pakistani market.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 sm:items-center">
                <Link
                  href="/onboarding"
                  className="group relative inline-flex items-center justify-center gap-3 rounded-full bg-white px-8 py-4 text-sm font-bold text-slate-950 shadow-[0_0_30px_rgba(255,255,255,0.15)] transition-all hover:bg-slate-100 hover:scale-105"
                >
                  Start Your Journey
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
                <Link
                  href="/careers"
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-700 bg-slate-800/50 px-8 py-4 text-sm font-bold text-white transition-all hover:bg-slate-800 hover:border-slate-600"
                >
                  <Activity className="h-4 w-4" />
                  Explore Reality Checks
                </Link>
              </div>
            </motion.div>
          </div>

          {/* Right Column - Data Vis abstraction */}
          <div className="lg:col-span-5 relative hidden lg:block">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative w-full aspect-square"
            >
              {/* Abstract Rings */}
              <div className="absolute inset-0 rounded-full border-[1px] border-indigo-500/10 animate-[spin_60s_linear_infinite]" />
              <div className="absolute inset-4 rounded-full border-[1px] border-slate-700/30 animate-[spin_40s_linear_infinite_reverse]" />
              <div className="absolute inset-12 rounded-full border-[1px] border-indigo-400/20 border-dashed animate-[spin_30s_linear_infinite]" />
              
              {/* Core Node */}
              <div className="absolute inset-0 m-auto h-32 w-32 rounded-full bg-indigo-600/10 border border-indigo-500/30 backdrop-blur-md flex items-center justify-center shadow-[0_0_40px_rgba(79,70,229,0.2)]">
                <div className="h-12 w-12 rounded-full bg-indigo-500/20 flex items-center justify-center">
                  <div className="h-3 w-3 rounded-full bg-indigo-400 animate-pulse" />
                </div>
              </div>

              {/* Orbital Nodes */}
              <div className="absolute top-0 right-1/4 h-12 w-12 rounded-2xl bg-slate-900 border border-slate-700 flex items-center justify-center shadow-lg transform rotate-12 animate-pulse-slow">
                 <span className="text-[10px] font-bold text-emerald-400">92%</span>
              </div>
              <div className="absolute bottom-1/4 left-0 h-10 w-24 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center shadow-lg -rotate-6">
                 <span className="text-[10px] font-bold text-slate-300">PKE Verified</span>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  )
}
