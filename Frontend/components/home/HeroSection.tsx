"use client"

import React from "react"
import Link from "next/link"
import { ArrowRight, Compass } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative bg-[#0B0F1A] text-[#F1F5F9] pt-20 pb-16 md:pt-28 md:pb-24">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 w-full text-center md:text-left">
        <div className="max-w-2xl space-y-6">
          {/* Eyebrow — small, muted */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#2A3650] bg-[#111827] text-xs font-semibold tracking-wider text-[#94A3B8]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3B82F6]" />
            <span>For Pakistani students</span>
          </div>

          {/* H1 — bold, large (no bold + italic) */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-[#F1F5F9] leading-[1.15]">
            Know your path before you commit.
          </h1>

          {/* Subhead — one line */}
          <p className="text-base sm:text-lg text-[#94A3B8] leading-relaxed">
            AI-mapped career intelligence built for Pakistan&apos;s real job market.
          </p>

          {/* CTAs */}
          <div className="pt-2 flex flex-col sm:flex-row gap-4 items-center md:items-start justify-center md:justify-start">
            <Link
              href="/onboarding"
              className="inline-flex items-center justify-center gap-2 rounded-[6px] bg-[#3B82F6] hover:bg-[#2563EB] active:scale-[0.99] px-6 py-3 text-sm font-bold text-white transition-all shadow-md hover:shadow-lg w-full sm:w-auto"
            >
              <span>Start My Journey</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/careers"
              className="inline-flex items-center justify-center gap-2 rounded-[6px] border border-[#3B82F6] bg-transparent hover:bg-[#3B82F6]/10 px-6 py-3 text-sm font-semibold text-[#60A5FA] transition-colors w-full sm:w-auto"
            >
              <Compass className="h-4 w-4 text-[#3B82F6]" />
              <span>Explore careers first</span>
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
