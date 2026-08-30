import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard"
import { PageTransition } from "@/components/layout/PageTransition"

export default function OnboardingPage() {
  return (
    <PageTransition>
      <div className="py-8">
        <OnboardingWizard />
      </div>
    </PageTransition>
  )
}
