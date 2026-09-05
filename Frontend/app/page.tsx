"use client"

import React from "react"
import { HeroSection } from "@/components/home/HeroSection"
import { FeaturesSection } from "@/components/home/FeaturesSection"
import { TalkToAlumniSection } from "@/components/alumni/TalkToAlumniSection"
import { PageTransition } from "@/components/layout/PageTransition"

export default function HomePage() {
  return (
    <PageTransition>
      <div className="bg-[#0B0F1A] min-h-screen space-y-16 pb-20">
        <HeroSection />
        <FeaturesSection />
        <div className="max-w-[1100px] mx-auto px-4 sm:px-6">
          <TalkToAlumniSection />
        </div>
      </div>
    </PageTransition>
  )
}
