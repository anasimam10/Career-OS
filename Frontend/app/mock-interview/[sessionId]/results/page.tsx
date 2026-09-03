"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { InterviewResults } from "@/components/mock-interview/InterviewResults"
import { PageTransition } from "@/components/layout/PageTransition"
import { LoadingState } from "@/components/shared/LoadingState"
import { ErrorState } from "@/components/shared/ErrorState"
import { getMockInterviewResults, type MockInterviewResults } from "@/lib/api/mock-interview"

export default function MockInterviewResultsPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = Array.isArray(params.sessionId) ? params.sessionId[0] : params.sessionId

  const [results, setResults] = useState<MockInterviewResults | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (sessionId) {
      fetchResults()
    }
  }, [sessionId])

  const fetchResults = async () => {
    if (!sessionId) return
    try {
      setLoading(true)
      const data = await getMockInterviewResults(sessionId)
      setResults(data)
    } catch (err: any) {
      setError(err.message || "Failed to load results")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-[#05080E] min-h-screen pt-24 pb-24">
        <LoadingState message="Calculating your results..." />
      </div>
    )
  }

  if (error || !results) {
    return (
      <div className="bg-[#05080E] min-h-screen pt-24 pb-24">
        <ErrorState message={error || "Failed to load results"} onRetry={fetchResults} />
      </div>
    )
  }

  return (
    <PageTransition>
      <div className="bg-[#05080E] min-h-screen pt-12 pb-24 px-4 sm:px-6">
        <InterviewResults 
          results={results} 
          onNewInterview={() => router.push("/mock-interview")}
        />
      </div>
    </PageTransition>
  )
}
