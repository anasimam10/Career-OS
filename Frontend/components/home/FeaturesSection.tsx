"use client"

import React from "react"
import { Map, Target, Briefcase, Mic } from "lucide-react"

const FEATURES = [
  {
    icon: Map,
    title: "Career Intelligence Map",
    description: "See demand, competition, and salary realities for 50+ careers in Pakistan.",
  },
  {
    icon: Target,
    title: "Personalized Journey",
    description: "Milestones tailored to your academic level and target field.",
  },
  {
    icon: Briefcase,
    title: "Job Readiness Score",
    description: "Know exactly where you stand before you apply.",
  },
  {
    icon: Mic,
    title: "Mock Interviews",
    description: "Practice with AI before the real thing.",
  },
]

export function FeaturesSection() {
  return (
    <section className="bg-[#0B0F1A] border-t border-[#2A3650]/60 py-16 md:py-20">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6">
        <div className="text-center mb-12 space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[#3B82F6]">
            Built on Ground Truth
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F1F5F9]">
            Everything you need to navigate your path
          </h2>
        </div>

        {/* 4-Card Feature Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((feature, idx) => {
            const Icon = feature.icon
            return (
              <div
                key={idx}
                className="rounded-[16px] border border-[#2A3650] bg-[#111827] p-6 flex flex-col justify-between hover:border-[#3B82F6]/50 transition-colors"
              >
                <div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-[10px] bg-[#1C2539] text-[#3B82F6] mb-5 border border-[#2A3650]">
                    <Icon className="h-8 w-8 text-[#3B82F6]" strokeWidth={1.75} />
                  </div>
                  <h3 className="text-lg font-bold text-[#F1F5F9] mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-[#94A3B8] leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
