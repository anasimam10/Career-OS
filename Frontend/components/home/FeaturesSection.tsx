"use client"

import React from "react"
import Link from "next/link"
import {
  Compass,
  Calendar,
  Route,
  GraduationCap,
  Briefcase,
  MessageSquare,
  ArrowRight,
} from "lucide-react"
import { TalkToAlumniSection } from "@/components/alumni/TalkToAlumniSection"

const FEATURES = [
  {
    icon: Compass,
    title: "Career Reality Check",
    description: "Verified Pakistani salaries, market demand levels, and honest entry hurdles before committing.",
    href: "/careers",
  },
  {
    icon: Calendar,
    title: "7-Day Career Trials",
    description: "Hands-on daily tasks to test real workflows and determine if a field truly suits you.",
    href: "/careers",
  },
  {
    icon: Route,
    title: "Full Pathway Stepper",
    description: "Structured multi-phase milestones guiding you from current academics to your first job.",
    href: "/journey",
  },
  {
    icon: GraduationCap,
    title: "248 Universities & Programs",
    description: "Accredited HEC institutions with entry test requirements, degree types, and eligibility rules.",
    href: "/universities",
  },
  {
    icon: Briefcase,
    title: "Verified Opportunities",
    description: "Real scholarships, exchange programs, and internships with deadlines and requirements.",
    href: "/opportunities",
  },
  {
    icon: MessageSquare,
    title: "AI Mock Interviews",
    description: "Role-specific practice powered by Qwen Plus with instant scoring and feedback.",
    href: "/mock-interview",
  },
]

export function FeaturesSection() {
  return (
    <section className="bg-[#0B0F1A] border-t border-[#1E2D42] py-16 md:py-24">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 space-y-16">
        
        {/* Section Header */}
        <div className="space-y-3 text-center max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F1F5F9] tracking-tight">
            Everything you need to navigate your career in Pakistan
          </h2>
          <p className="text-sm sm:text-base text-[#94A3B8]">
            Built with verified Pakistani labor data, university records, and real student pathways.
          </p>
        </div>

        {/* 6-Card Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((feature, idx) => {
            const Icon = feature.icon
            return (
              <Link
                key={idx}
                href={feature.href}
                className="group rounded-[14px] border border-[#1E2D42] bg-[#111827] p-6 flex flex-col justify-between hover:border-[#3B82F6]/50 hover:bg-[#1C2539]/50 transition-all"
              >
                <div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-[8px] bg-[#1C2539] text-[#3B82F6] mb-4 border border-[#1E2D42] group-hover:border-[#3B82F6]/40 transition-colors">
                    <Icon className="h-5 w-5" strokeWidth={2} />
                  </div>
                  <h3 className="text-base font-bold text-[#F1F5F9] mb-2 group-hover:text-[#60A5FA] transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-[#94A3B8] leading-relaxed">
                    {feature.description}
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#1E2D42]/60 flex items-center justify-between text-xs font-semibold text-[#3B82F6] group-hover:text-[#60A5FA]">
                  <span>Explore</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            )
          })}
        </div>

        {/* Talk to Alumni Component */}
        <TalkToAlumniSection />
      </div>
    </section>
  )
}
