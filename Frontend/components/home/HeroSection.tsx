"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import Image from "next/image"
import { ArrowRight } from "lucide-react"

export function HeroSection() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 80) {
        setScrolled(true)
      } else {
        setScrolled(false)
      }
    }

    window.addEventListener("scroll", handleScroll, { passive: true })
    handleScroll() // Initial check
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <section className="relative bg-[#0B0F1A] text-[#F1F5F9] pt-14 pb-20 md:pt-24 md:pb-28 overflow-hidden">
      {/* Ambient Grid Pattern */}
      <div className="hero-grid-pattern absolute inset-0 pointer-events-none z-0 opacity-60" />

      {/* Ambient Radial Vignette Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-blue-600/10 rounded-full blur-[140px] pointer-events-none z-0" />

      <div className="relative z-10 mx-auto max-w-[1140px] px-4 sm:px-6 lg:px-8 w-full">
        {/* Centered Text Header */}
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
          {/* Eyebrow badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-[#1E2D42] bg-[#111827]/80 backdrop-blur-sm text-xs font-medium tracking-wider text-[#94A3B8] mb-6 shadow-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-[#2563EB]" />
            <span>For students across Pakistan.</span>
          </div>

          {/* H1 — large, bold with silver/white gradient title */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-b from-white via-[#E2E8F0] to-[#94A3B8] leading-[1.12] pb-2">
            Know your path before you commit.
          </h1>

          {/* Subline */}
          <p className="text-base sm:text-lg md:text-xl text-[#94A3B8] leading-relaxed max-w-2xl mx-auto mt-4">
            AI-guided career intelligence built around Pakistan&apos;s real job market.
          </p>

          {/* Centered CTAs */}
          <div className="mt-8 flex flex-col sm:flex-row gap-3.5 items-center justify-center w-full sm:w-auto">
            <Link
              href="/onboarding"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] active:scale-[0.98] px-7 py-3.5 text-sm font-semibold text-white transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-600/40 w-full sm:w-auto"
            >
              <span>Start My Journey</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/careers"
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-[#2A3A54] bg-[#111827]/60 hover:bg-[#1C2539] px-7 py-3.5 text-sm font-semibold text-[#F1F5F9] transition-all w-full sm:w-auto"
            >
              <span>Explore careers &rarr;</span>
            </Link>
          </div>
        </div>

        {/* Centered Showcase Visual with 3D Perspective Scroll Tilt */}
        <div className="hero-perspective-wrapper mt-12 sm:mt-16 md:mt-20 max-w-[1024px] mx-auto">
          <div
            className={`hero-perspective-card relative w-full rounded-2xl border border-[#23334D]/80 bg-[#0F1424]/90 p-2 sm:p-3 shadow-[0_30px_70px_-20px_rgba(0,0,0,0.8)] backdrop-blur-md ${
              scrolled
                ? "scrolled shadow-[0_40px_90px_-15px_rgba(37,99,235,0.18)]"
                : ""
            }`}
          >
            {/* Architectural Corner Ticks */}
            <div className="absolute top-1.5 left-1.5 w-2.5 h-2.5 border-t border-l border-[#3B82F6]/40 pointer-events-none" />
            <div className="absolute top-1.5 right-1.5 w-2.5 h-2.5 border-t border-r border-[#3B82F6]/40 pointer-events-none" />
            <div className="absolute bottom-1.5 left-1.5 w-2.5 h-2.5 border-b border-l border-[#3B82F6]/40 pointer-events-none" />
            <div className="absolute bottom-1.5 right-1.5 w-2.5 h-2.5 border-b border-r border-[#3B82F6]/40 pointer-events-none" />

            <div className="relative w-full rounded-xl overflow-hidden bg-[#0A0E17]">
              <Image
                src="/images/career-os-hero-visual.jpg"
                alt="Career OS visual pathway: transforming scattered educational advice and ungrounded rumors into a structured, sequential career journey in Pakistan"
                width={1024}
                height={571}
                priority
                quality={90}
                className="w-full h-auto object-contain rounded-xl block select-none pointer-events-none"
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 90vw, 1024px"
              />

              {/* Micro-bevel edge hairline to accentuate physical depth */}
              <div className="absolute inset-0 rounded-xl border border-white/[0.05] pointer-events-none" />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}



