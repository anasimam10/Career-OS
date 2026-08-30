import { CoachChat } from "@/components/mentor/CoachChat"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { PageTransition } from "@/components/layout/PageTransition"

export default function MentorPage() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10 space-y-8">
        <SectionHeader
          badge="AI Mentor"
          title="Your Personal Career Coach"
          subtitle="Ask any question about careers, university entrance, internships, or sports pathways in Pakistan."
        />

        <CoachChat />
      </div>
    </PageTransition>
  )
}
