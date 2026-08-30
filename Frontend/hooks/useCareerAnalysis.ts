"use client"

import { useState, useEffect, useCallback } from "react"
import { analyzeCareer, getTrialPlan, getCareer } from "@/lib/api/careers"
import type { Career, CareerRealityResponse, CareerTrialPlan } from "@/lib/types/career.types"

export function useCareerAnalysis(slug: string) {
  const [career, setCareer] = useState<Career | null>(null)
  const [analysis, setAnalysis] = useState<CareerRealityResponse | null>(null)
  const [trialPlan, setTrialPlan] = useState<CareerTrialPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (!slug) return
    try {
      setLoading(true)
      setError(null)
      const [c, a, t] = await Promise.all([
        getCareer(slug).catch(() => null),
        analyzeCareer(slug),
        getTrialPlan(slug).catch(() => null),
      ])
      if (c) setCareer(c)
      setAnalysis(a)
      if (t) setTrialPlan(t)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze career")
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { career, analysis, trialPlan, loading, error, refetch: fetchData }
}
