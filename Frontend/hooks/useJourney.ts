"use client"

import { useState, useEffect, useCallback } from "react"
import { getJourney, markProgress } from "@/lib/api/journey"
import { clearSession, getStudentId } from "@/lib/session"
import type { JourneyResponse, JourneyStep } from "@/lib/types/journey.types"

export function useJourney() {
  const [journey, setJourney] = useState<JourneyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sessionMissing, setSessionMissing] = useState(false)

  const fetchJourney = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setLoading(true)
      setError(null)

      const studentId = getStudentId()
      if (!studentId && process.env.NEXT_PUBLIC_USE_MOCK !== "true") {
        setSessionMissing(true)
        setJourney(null)
        setLoading(false)
        return
      }

      setSessionMissing(false)
      const data = await getJourney(studentId || undefined)
      setJourney(data)
    } catch (err: any) {
      if (
        err?.statusCode === 404 ||
        (err?.message && (err.message.includes("404") || err.message.includes("not found")))
      ) {
        clearSession()
        setSessionMissing(true)
        setJourney(null)
        setError("Your session expired — let's set you up again")
      } else {
        setError(err instanceof Error ? err.message : "Couldn't load your journey — try again")
      }
    } finally {
      if (!isSilent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchJourney()
  }, [fetchJourney])

  const completeMilestone = async (milestoneId?: number) => {
    const studentId = getStudentId() || undefined
    const targetId = milestoneId ?? journey?.current_milestone_id ?? 0

    try {
      const res = await markProgress(targetId, studentId)

      // Advance local state immediately to avoid full page reload or flicker
      setJourney((prev) => {
        if (!prev) return prev
        const steps = [...(prev.next_steps || [])]
        const currentIndex = steps.findIndex((s) => s.id === targetId)

        let updatedSteps: JourneyStep[]
        if (currentIndex !== -1) {
          updatedSteps = steps.map((step, idx) => {
            if (idx === currentIndex) {
              return { ...step, status: "completed" as const }
            }
            if (idx === currentIndex + 1) {
              return { ...step, status: "active" as const }
            }
            if (idx > currentIndex + 1) {
              return { ...step, status: "locked" as const }
            }
            return step
          })
        } else {
          // If first step was completed
          updatedSteps = steps.map((step, idx) => {
            if (idx === 0) return { ...step, status: "completed" as const }
            if (idx === 1) return { ...step, status: "active" as const }
            return { ...step, status: "locked" as const }
          })
        }

        const nextActive = updatedSteps.find((s) => s.status === "active")

        return {
          ...prev,
          stage: res.new_stage || prev.stage,
          next_best_action: res.next_best_action || prev.next_best_action,
          current_milestone_id: nextActive?.id ?? prev.current_milestone_id,
          next_steps: updatedSteps,
        }
      })

      // Silently refresh in background
      fetchJourney(true)
      return res
    } catch (err) {
      throw err instanceof Error ? err : new Error("Failed to update milestone")
    }
  }

  return {
    journey,
    loading,
    error,
    sessionMissing,
    refetch: () => fetchJourney(false),
    completeMilestone,
  }
}
