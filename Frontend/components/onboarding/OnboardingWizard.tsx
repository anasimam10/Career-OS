"use client"

import React, { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { ArrowLeft, ArrowRight, Loader2, AlertCircle, Sparkles } from "lucide-react"
import { useOnboarding } from "@/hooks/useOnboarding"
import { StepIndicator } from "./StepIndicator"
import { Step1Education } from "./steps/Step1Education"
import { Step2Location } from "./steps/Step2Location"
import { Step3CareerField } from "./steps/Step3CareerField"
import { Step4Interests } from "./steps/Step4Interests"
import { Step5Skills } from "./steps/Step5Skills"
import { Step6Sports } from "./steps/Step6Sports"
import { Step7Motivation } from "./steps/Step7Motivation"

export function OnboardingWizard() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [sessionNotice, setSessionNotice] = useState<string | null>(null)

  const {
    step,
    totalSteps,
    data,
    loading,
    error,
    nextStep,
    prevStep,
    updateData,
    submit,
  } = useOnboarding()

  useEffect(() => {
    const reason = searchParams.get("reason")
    if (reason === "expired") {
      setSessionNotice("Your session expired — let's set up your profile and roadmap again.")
    }
  }, [searchParams])

  const handleFinish = async () => {
    try {
      const res = await submit()
      if (res && res.student_id) {
        router.push("/journey")
      }
    } catch {
      // Error state captured by useOnboarding
    }
  }

  const toggleMotivationTag = (tag: string) => {
    const exists = data.motivation_tags.includes(tag)
    if (exists) {
      updateData({ motivation_tags: data.motivation_tags.filter((t) => t !== tag) })
    } else {
      updateData({ motivation_tags: [...data.motivation_tags, tag] })
    }
  }

  return (
    <div className="mx-auto max-w-[760px] px-4 py-6 sm:py-10">
      {/* Session Expired Banner if redirected */}
      {sessionNotice && (
        <div className="mb-6 flex items-center gap-2.5 rounded-[8px] border border-amber-500/40 bg-amber-500/10 p-4 text-sm font-semibold text-amber-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-amber-400" />
          <span>{sessionNotice}</span>
        </div>
      )}

      {/* Progress Step Indicator (Step X of 7) */}
      <div className="mb-8">
        <StepIndicator currentStep={step} totalSteps={totalSteps} />
      </div>

      {/* Wizard Card Container */}
      <div className="relative rounded-[20px] border border-[#2A3650] bg-[#111827] p-6 sm:p-10 shadow-2xl">
        <div>
          {step === 1 && (
            <Step1Education
              value={data.education_stage}
              onChange={(val) => updateData({ education_stage: val })}
            />
          )}

          {step === 2 && (
            <Step2Location
              province={data.province}
              city={data.city}
              onProvinceChange={(val) => updateData({ province: val })}
              onCityChange={(val) => updateData({ city: val })}
            />
          )}

          {step === 3 && (
            <Step3CareerField
              value={data.target_field}
              onChange={(val) => updateData({ target_field: val })}
            />
          )}

          {step === 4 && (
            <Step4Interests
              selected={data.interests}
              onChange={(val) => updateData({ interests: val })}
            />
          )}

          {step === 5 && (
            <Step5Skills
              skills={data.skills}
              onChange={(val) => updateData({ skills: val })}
            />
          )}

          {step === 6 && (
            <Step6Sports
              value={data.sports_interest}
              onChange={(val) => updateData({ sports_interest: val })}
            />
          )}

          {step === 7 && (
            <Step7Motivation
              selected={data.motivation_tags}
              additionalNotes={data.additional_notes}
              onToggle={toggleMotivationTag}
              onNotesChange={(val) => updateData({ additional_notes: val })}
            />
          )}

          {error && (
            <div className="mt-6 flex items-center gap-2 rounded-[8px] border border-rose-900/60 bg-rose-950/40 p-3.5 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Wizard Footer Navigation */}
        <div className="mt-10 flex items-center justify-between pt-6 border-t border-[#2A3650]">
          {step > 1 ? (
            <button
              type="button"
              onClick={prevStep}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-[8px] border border-[#2A3650] bg-transparent hover:bg-[#1C2539] px-5 py-2.5 text-sm font-semibold text-[#94A3B8] hover:text-[#F1F5F9] transition-colors disabled:opacity-50 min-h-[44px]"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back</span>
            </button>
          ) : (
            <div />
          )}

          {step < totalSteps ? (
            <button
              type="button"
              onClick={nextStep}
              className="inline-flex items-center gap-2 rounded-[8px] bg-[#2563EB] hover:bg-[#1D4ED8] px-6 py-2.5 text-sm font-bold text-white transition-all shadow-md active:scale-[0.98] min-h-[44px]"
            >
              <span>Continue</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleFinish}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-[8px] bg-[#2563EB] hover:bg-[#1D4ED8] px-6 py-2.5 text-sm font-bold text-white transition-all shadow-md active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed min-h-[44px]"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-white" />
                  <span>Bootstrapping Journey...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Start My Journey</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
