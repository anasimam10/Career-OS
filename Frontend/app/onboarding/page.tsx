import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard"
import { PageTransition } from "@/components/layout/PageTransition"

export default function OnboardingPage() {
  return (
    <PageTransition>
      <div className="relative min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 overflow-hidden bg-[#05080E]">
        {/* Cinematic Grid Background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#08101C_1px,transparent_1px),linear-gradient(to_bottom,#08101C_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20 pointer-events-none" />
        
        {/* Glow */}
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
        <div className="absolute -top-48 left-1/2 -translate-x-1/2 w-full max-w-lg h-64 bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative z-10 w-full">
          <OnboardingWizard />
        </div>
      </div>
    </PageTransition>
  )
}
