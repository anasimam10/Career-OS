import { HeroSection } from "@/components/home/HeroSection"
import { FeaturesSection } from "@/components/home/FeaturesSection"
import { PageTransition } from "@/components/layout/PageTransition"

export default function HomePage() {
  return (
    <PageTransition>
      <div className="space-y-8 pb-16">
        <HeroSection />
        <FeaturesSection />
      </div>
    </PageTransition>
  )
}
