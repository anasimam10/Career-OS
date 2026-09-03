"use client"

import { useState, useEffect, useCallback } from "react"
import { getJourney, markProgress } from "@/lib/api/journey"
import { clearSession } from "@/lib/session"
import type { JourneyResponse, NextBestAction } from "@/lib/types/journey.types"

export function useJourney() {
  const [journey, setJourney] = useState<JourneyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJourney = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getJourney()
      setJourney(data)
    } catch (err: any) {
      if (err?.statusCode === 404 || (err?.message && (err.message.includes("404") || err.message.includes("not found")))) {
        clearSession()
        setJourney(null)
      }
      setError(err instanceof Error ? err.message : "Failed to load journey")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchJourney()
  }, [fetchJourney])

  const completeMilestone = async (milestoneId?: number) => {
    try {
      const targetId = milestoneId ?? journey?.current_milestone_id ?? 0
      const res = await markProgress(targetId)
      await fetchJourney()
      return res
    } catch (err) {
      throw err instanceof Error ? err : new Error("Failed to update milestone")
    }
  }

  return { journey, loading, error, refetch: fetchJourney, completeMilestone }
}
