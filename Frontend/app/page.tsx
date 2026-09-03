"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { HeroSection } from "@/components/home/HeroSection"
import { FeaturesSection } from "@/components/home/FeaturesSection"
import { TalkToAlumniSection } from "@/components/alumni/TalkToAlumniSection"
import { PageTransition } from "@/components/layout/PageTransition"
import { getSession, clearSession } from "@/lib/session"
import { getStudentProfile } from "@/lib/api/students"

export default function HomePage() {
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    async function checkStudentStatus() {
      const session = getSession()
      if (!session || !session.student_id || !session.onboarding_completed) {
        clearSession()
        router.replace("/onboarding")
        return
      }

      // Verify the student actually exists in the database
      try {
        await getStudentProfile()
        setChecking(false)
      } catch {
        // If student does not exist in DB (e.g. wiped or invalid id), purge stale session and send to onboarding
        clearSession()
        router.replace("/onboarding")
      }
    }

    checkStudentStatus()
  }, [router])

  if (checking) {
    return (
      <div className="bg-[#05080E] min-h-screen flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      </div>
    )
  }

  return (
    <PageTransition>
      <div className="space-y-8 pb-16">
        <HeroSection />
        <FeaturesSection />
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <TalkToAlumniSection />
        </div>
      </div>
    </PageTransition>
  )
}
