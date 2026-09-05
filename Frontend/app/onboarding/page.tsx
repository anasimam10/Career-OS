import React, { Suspense } from "react"
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard"
import { PageTransition } from "@/components/layout/PageTransition"

export default function OnboardingPage() {
  return (
    <PageTransition>
      <div className="relative min-h-[calc(100vh-4rem)] flex items-center justify-center py-10 bg-[#0B0F1A]">
        <div className="relative z-10 w-full">
          <Suspense fallback={<div className="text-center text-sm text-[#94A3B8] py-12">Loading...</div>}>
            <OnboardingWizard />
          </Suspense>
        </div>
      </div>
    </PageTransition>
  )
}
