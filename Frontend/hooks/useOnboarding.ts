"use client"

import { useState } from "react"
import { submitOnboarding } from "@/lib/api/onboarding"
import { saveNewStudentSession } from "@/lib/session"
import type { OnboardingPayload, OnboardingResponse, Skill } from "@/lib/types/student.types"
import type { EducationStage } from "@/lib/types/journey.types"

export interface OnboardingState {
  education_stage: EducationStage
  province: string
  city: string
  target_field: string
  interests: string[]
  skills: Skill[]
  sports_interest: string | null
  motivation_tags: string[]
  additional_notes?: string
}

const initialState: OnboardingState = {
  education_stage: "HIGH_SCHOOL",
  province: "Sindh",
  city: "Karachi",
  target_field: "Software Engineering",
  interests: ["Technology", "Mathematics"],
  skills: [{ name: "Problem Solving", level: "beginner" }],
  sports_interest: null,
  motivation_tags: ["I genuinely love this subject"],
  additional_notes: "",
}

export function useOnboarding() {
  const [step, setStep] = useState(1)
  const [data, setData] = useState<OnboardingState>(initialState)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<OnboardingResponse | null>(null)

  const totalSteps = 7

  const validateStep = (currentStep: number): boolean => {
    setError(null)
    if (currentStep === 1) {
      if (!data.education_stage) {
        setError("Please select your current education stage.")
        return false
      }
    } else if (currentStep === 2) {
      if (!data.province || !data.city) {
        setError("Please select both your province and city.")
        return false
      }
    } else if (currentStep === 3) {
      if (!data.target_field) {
        setError("Please select a target field or choose 'I\\'m not sure yet'.")
        return false
      }
    } else if (currentStep === 4) {
      if (data.interests.length === 0) {
        setError("Please select at least one interest area.")
        return false
      }
    } else if (currentStep === 7) {
      if (data.motivation_tags.length === 0) {
        setError("Please select what is motivating you toward this path.")
        return false
      }
    }
    return true
  }

  const nextStep = () => {
    if (!validateStep(step)) return
    setStep((s) => Math.min(s + 1, totalSteps))
  }

  const prevStep = () => {
    setError(null)
    setStep((s) => Math.max(s - 1, 1))
  }

  const updateData = (updates: Partial<OnboardingState>) => {
    setData((prev) => ({ ...prev, ...updates }))
  }

  const submit = async () => {
    if (!validateStep(7)) return null

    try {
      setLoading(true)
      setError(null)

      const careerInterests =
        data.target_field &&
        data.target_field !== "I'm not sure yet" &&
        data.target_field !== "Not sure yet"
          ? [data.target_field]
          : []

      const allMotivations = [...data.motivation_tags]
      if (data.additional_notes && data.additional_notes.trim()) {
        allMotivations.push(data.additional_notes.trim())
      }

      const payload: OnboardingPayload = {
        education_stage: data.education_stage,
        interests: data.interests.length > 0 ? data.interests : ["Technology"],
        career_interests: careerInterests,
        sports_interest: data.sports_interest,
        motivation_tags: allMotivations.length > 0 ? allMotivations : ["Interest in the field"],
        skills: data.skills,
        city: data.city || "Karachi",
        province: data.province || "Sindh",
      }

      // Force creating a fresh student session for onboarding
      const res = await submitOnboarding(payload, { forceNew: true })
      const finalId = res.student_id || 1

      saveNewStudentSession(finalId, "Student", payload.city)
      if (typeof window !== "undefined") {
        localStorage.setItem("career_os_student_id", String(finalId))
      }

      setResult(res)
      return res
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to submit onboarding"
      setError(msg)
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
