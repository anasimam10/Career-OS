"use client"

import { useState, useEffect, useCallback } from "react"
import { analyzeCareer, getTrialPlan, getCareer } from "@/lib/api/careers"
import type { Career, CareerRealityResponse, CareerTrialPlan } from "@/lib/types/career.types"

interface UseCareerAnalysisOptions {
  includeAnalysis?: boolean
  includeTrialPlan?: boolean
}

export function useCareerAnalysis(
  slug: string,
  options: UseCareerAnalysisOptions = { includeAnalysis: true, includeTrialPlan: true }
) {
  const [career, setCareer] = useState<Career | null>(null)
  const [analysis, setAnalysis] = useState<CareerRealityResponse | null>(null)
  const [trialPlan, setTrialPlan] = useState<CareerTrialPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { includeAnalysis = true, includeTrialPlan = true } = options

  const fetchData = useCallback(async () => {
    if (!slug) return
    try {
      setLoading(true)
      setError(null)

      const promises: [
        Promise<Career | null>,
        Promise<CareerRealityResponse | null>,
        Promise<CareerTrialPlan | null>
      ] = [
        getCareer(slug).catch(() => null),
        includeAnalysis ? analyzeCareer(slug) : Promise.resolve(null),
        includeTrialPlan ? getTrialPlan(slug).catch(() => null) : Promise.resolve(null),
      ]

      const [c, a, t] = await Promise.all(promises)
      if (c) setCareer(c)
      if (a) setAnalysis(a)
      if (t) setTrialPlan(t)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze career")
    } finally {
      setLoading(false)
    }
  }, [slug, includeAnalysis, includeTrialPlan])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { career, analysis, trialPlan, loading, error, refetch: fetchData }
}
