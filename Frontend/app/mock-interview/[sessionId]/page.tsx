"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { InterviewQuestion } from "@/components/mock-interview/InterviewQuestion"
import { PageTransition } from "@/components/layout/PageTransition"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import {
  getMockInterview,
  submitMockInterviewAnswer,
  completeMockInterview,
  type MockInterviewSession
} from "@/lib/api/mock-interview"

export default function MockInterviewSessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = Array.isArray(params.sessionId) ? params.sessionId[0] : params.sessionId

  const [session, setSession] = useState<MockInterviewSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Find the first unanswered question
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (sessionId) {
      fetchSession()
    }
  }, [sessionId])

  const fetchSession = async () => {
    if (!sessionId) return
    try {
      setLoading(true)
      const data = await getMockInterview(sessionId)
      if (data.status === "completed") {
        router.replace(`/mock-interview/${sessionId}/results`)
        return
      }
      
      setSession(data)
      
      // Find first unanswered
      const firstUnanswered = data.questions.findIndex((q) => !q.selected_option_id)
      if (firstUnanswered !== -1) {
        setCurrentIndex(firstUnanswered)
      } else {
        // If all answered but not completed
        setCurrentIndex(Math.max(0, data.questions.length - 1))
      }
    } catch (err: any) {
      setError(err.message || "Failed to load session")
    } finally {
      setLoading(false)
    }
  }

  const handleNext = async (selectedId: string) => {
    if (!session || !sessionId) return

    const currentQuestion = session.questions[currentIndex]
    
    // Submit answer
    try {
      await submitMockInterviewAnswer(sessionId, currentQuestion.id, selectedId)
      
      const isLast = currentIndex === session.questions.length - 1
      
      if (isLast) {
        // Complete interview
        await completeMockInterview(sessionId)
        router.push(`/mock-interview/${sessionId}/results`)
      } else {
        setCurrentIndex(currentIndex + 1)
      }
    } catch (err) {
      console.error(err)
      alert("Failed to save answer. Please try again.")
    }
  }

  if (loading) {
    return (
      <div className="bg-[#05080E] min-h-screen pt-24 pb-24">
        <LoadingState message="Loading your mock interview..." />
      </div>
    )
  }

  if (error || !session) {
    return (
      <div className="bg-[#05080E] min-h-screen pt-24 pb-24">
        <ErrorState message={error || "Failed to load session"} onRetry={fetchSession} />
      </div>
    )
  }

  const currentQuestion = session.questions[currentIndex]

  return (
    <PageTransition>
      <div className="bg-[#05080E] min-h-screen pt-12 pb-24 px-4 sm:px-6">
        <InterviewQuestion 
          questionNumber={currentIndex + 1}
          totalQuestions={session.total_questions}
          questionText={currentQuestion.question_text}
          options={currentQuestion.options}
          onNext={handleNext}
          isLast={currentIndex === session.questions.length - 1}
        />
      </div>
    </PageTransition>
  )
}
