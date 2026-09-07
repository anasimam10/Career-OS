"use client"

import React from "react"
import { HeroSection } from "@/components/home/HeroSection"
import { FeaturesSection } from "@/components/home/FeaturesSection"
import { PageTransition } from "@/components/layout/PageTransition"

export default function HomePage() {
  return (
    <PageTransition>
      <div className="bg-[#0B0F1A] min-h-screen">
        <HeroSection />
        <FeaturesSection />
      </div>
    </PageTransition>
  )
}


