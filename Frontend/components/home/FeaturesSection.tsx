"use client"

import React from "react"
import Link from "next/link"
import { Map, Route, MessageSquare, ArrowRight } from "lucide-react"

const FEATURES = [
  {
    icon: Map,
    title: "Career Intelligence",
    description: "50+ careers with real Pakistani salary ranges and job market demand.",
  },
  {
    icon: Route,
    title: "Your Journey",
    description: "Step-by-step milestones from your current stage to first job.",
  },
  {
    icon: MessageSquare,
    title: "Mock Interviews",
    description: "Practice with AI before the real interview.",
  },
]

export function FeaturesSection() {
  return (
    <section className="bg-[#0B0F1A] border-t border-[#1E2D42] py-16 md:py-24">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 space-y-20">
        {/* 3-Column Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
          {FEATURES.map((feature, idx) => {
            const Icon = feature.icon
            return (
              <div
                key={idx}
                className="rounded-[12px] border border-[#1E2D42] bg-[#111827] p-6 sm:p-8 flex flex-col justify-between hover:border-[#2A3A54] transition-colors"
              >
                <div>
                  <div className="flex h-11 w-11 items-center justify-center rounded-[8px] bg-[#1C2539] text-[#2563EB] mb-5 border border-[#1E2D42]">
                    <Icon className="h-5 w-5 text-[#3B82F6]" strokeWidth={2} />
                  </div>
                  <h3 className="text-lg font-semibold text-[#F1F5F9] mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-[#94A3B8] leading-relaxed max-w-sm">
                    {feature.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {/* CTA Strip */}
        <div className="rounded-[16px] border border-[#1E2D42] bg-[#111827] p-8 sm:p-12 text-center space-y-6 max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F1F5F9]">
            Ready to start?
          </h2>
          <div>
            <Link
              href="/onboarding"
              className="inline-flex items-center gap-2 rounded-[8px] bg-[#2563EB] hover:bg-[#1D4ED8] active:scale-[0.98] px-6 py-3 text-sm font-semibold text-white transition-all shadow-md"
            >
              <span>Build your profile</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
