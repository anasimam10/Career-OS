"use client"

import { useState } from "react"
import { submitOnboarding } from "@/lib/api/onboarding"
import { saveNewStudentSession, updateSession } from "@/lib/session"
import type { OnboardingPayload, OnboardingResponse } from "@/lib/types/student.types"
import type { EducationStage } from "@/lib/types/journey.types"

export interface OnboardingState {
  education_stage: EducationStage
  city: string
  province: string
  target_field: string
}

const initialState: OnboardingState = {
  education_stage: "HIGH_SCHOOL",
  city: "Karachi",
  province: "Sindh",
  target_field: "Software Engineering",
}

export function useOnboarding() {
  const [step, setStep] = useState(1)
  const [data, setData] = useState<OnboardingState>(initialState)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<OnboardingResponse | null>(null)

  const totalSteps = 2

  const nextStep = () => setStep((s) => Math.min(s + 1, totalSteps))
  const prevStep = () => setStep((s) => Math.max(s - 1, 1))

  const updateData = (updates: Partial<OnboardingState>) => {
    setData((prev) => ({ ...prev, ...updates }))
  }

  const submit = async () => {
    try {
      setLoading(true)
      setError(null)
      const interests =
        data.target_field &&
        data.target_field !== "I'm not sure yet" &&
        data.target_field !== "Not sure yet"
          ? [data.target_field]
          : []

      const payload: OnboardingPayload = {
        education_stage: data.education_stage,
        interests: interests,
        career_interests: interests,
        sports_interest: null,
        motivation_tags: [],
        skills: [],
        city: data.city || "Karachi",
        province: data.province || "Sindh",
      }

      const res = await submitOnboarding(payload)
      const finalId = res.student_id || 1
      saveNewStudentSession(finalId, "Student", payload.city)
      if (typeof window !== "undefined") {
        localStorage.setItem("career_os_student_id", String(finalId))
      }

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
    submit,
  }
}
