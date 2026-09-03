import { MockInterviewSetup } from "@/components/mock-interview/MockInterviewSetup"
import { PageTransition } from "@/components/layout/PageTransition"

export default function MockInterviewPage() {
  return (
    <PageTransition>
      <div className="bg-[#05080E] min-h-screen pt-16 pb-24">
        <MockInterviewSetup />
      </div>
    </PageTransition>
  )
}
