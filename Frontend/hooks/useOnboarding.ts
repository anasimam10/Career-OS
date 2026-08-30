"use client"

import { useState } from "react"
import { submitOnboarding } from "@/lib/api/onboarding"
import { updateSession } from "@/lib/session"
import type { OnboardingPayload, OnboardingResponse, Skill } from "@/lib/types/student.types"
import type { EducationStage } from "@/lib/types/journey.types"

export interface OnboardingState {
  education_stage: EducationStage
  interests: string[]
  career_interests: string[]
  motivation_tags: string[]
  sports_interest: string | null
  future_goals: string[]
  skills: Skill[]
  city: string
}

const initialState: OnboardingState = {
  education_stage: "HIGH_SCHOOL",
  interests: [],
  career_interests: [],
  motivation_tags: [],
  sports_interest: null,
  future_goals: [],
  skills: [],
  city: "Karachi",
}

export function useOnboarding() {
  const [step, setStep] = useState(1)
  const [data, setData] = useState<OnboardingState>(initialState)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<OnboardingResponse | null>(null)

  const totalSteps = 6

  const nextStep = () => setStep((s) => Math.min(s + 1, totalSteps))
  const prevStep = () => setStep((s) => Math.max(s - 1, 1))

  const updateData = (updates: Partial<OnboardingState>) => {
    setData((prev) => ({ ...prev, ...updates }))
  }

  const toggleArrayItem = (key: "interests" | "career_interests" | "motivation_tags" | "future_goals", value: string) => {
    setData((prev) => {
      const arr = prev[key]
      return {
        ...prev,
        [key]: arr.includes(value) ? arr.filter((x) => x !== value) : [...arr, value],
      }
    })
  }

  const submit = async () => {
    try {
      setLoading(true)
      setError(null)
      const payload: OnboardingPayload = {
        education_stage: data.education_stage,
        interests: data.interests,
        career_interests: data.career_interests,
        sports_interest: data.sports_interest === "No sport" ? null : data.sports_interest,
        motivation_tags: data.motivation_tags,
        skills: data.skills,
        city: data.city || "Karachi",
      }
      const res = await submitOnboarding(payload)
      updateSession({ onboarding_completed: true })
      setResult(res)
      return res
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit onboarding")
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    step,
    totalSteps,
    data,
    loading,
    error,
    result,
    nextStep,
    prevStep,
    updateData,
    toggleArrayItem,
    submit,
  }
}
