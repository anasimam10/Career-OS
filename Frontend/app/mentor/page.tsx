import { CoachChat } from "@/components/mentor/CoachChat"
import { SectionHeader } from "@/components/shared/SectionHeader"
import { PageTransition } from "@/components/layout/PageTransition"

export default function MentorPage() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-10 space-y-8">
        <SectionHeader
          badge="Career Assistant"
          title="Ask About Careers in Pakistan"
          subtitle="Ask data-grounded questions about careers, university entrance, or internships in Pakistan."
        />

        <CoachChat />
      </div>
    </PageTransition>
  )
}
