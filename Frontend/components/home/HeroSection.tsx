"use client"

import React from "react"
import Link from "next/link"
import { ArrowRight, Compass } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative bg-[#0B0F1A] text-[#F1F5F9] pt-20 pb-16 md:pt-28 md:pb-24">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 w-full text-center md:text-left">
        <div className="max-w-2xl space-y-6">
          {/* Eyebrow — small, muted, sentence case */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#1E2D42] bg-[#111827] text-xs font-medium tracking-wider text-[#94A3B8]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#2563EB]" />
            <span>For students across Pakistan.</span>
          </div>

          {/* H1 — large, bold, white */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-[#F1F5F9] leading-[1.15]">
            Know your path before you commit.
          </h1>

          {/* Subline — 1 line, muted */}
          <p className="text-base sm:text-lg text-[#94A3B8] leading-relaxed max-w-xl">
            AI-guided career intelligence built around Pakistan&apos;s real job market.
          </p>

          {/* CTAs */}
          <div className="pt-2 flex flex-col sm:flex-row gap-4 items-center md:items-start justify-center md:justify-start">
            <Link
              href="/onboarding"
              className="inline-flex items-center justify-center gap-2 rounded-[8px] bg-[#2563EB] hover:bg-[#1D4ED8] active:scale-[0.98] px-6 py-3 text-sm font-semibold text-white transition-all shadow-md w-full sm:w-auto"
            >
              <span>Start My Journey</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/careers"
              className="inline-flex items-center justify-center gap-2 rounded-[8px] border border-[#2A3A54] bg-transparent hover:bg-[#1C2539] px-6 py-3 text-sm font-semibold text-[#F1F5F9] transition-colors w-full sm:w-auto"
            >
              <span>Explore careers →</span>
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
