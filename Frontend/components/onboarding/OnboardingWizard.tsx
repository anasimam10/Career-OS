"use client"

import React, { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { ArrowLeft, ArrowRight, Loader2, AlertCircle, Sparkles } from "lucide-react"
import { useOnboarding } from "@/hooks/useOnboarding"
import { StepIndicator } from "./StepIndicator"
import { Step1Education } from "./steps/Step1Education"
import { Step2Location } from "./steps/Step2Location"

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
      setSessionNotice("Your session expired — let's set you up again")
    }
  }, [searchParams])

  const handleFinish = async () => {
    try {
      const res = await submit()
      if (res?.student_id && typeof window !== "undefined") {
        localStorage.setItem("career_os_student_id", String(res.student_id))
      }
      router.push("/journey")
    } catch {
      // Error state captured by useOnboarding
    }
  }

  return (
    <div className="mx-auto max-w-[720px] px-4 py-8 sm:py-12">
      {/* Session Expired Banner if redirected */}
      {sessionNotice && (
        <div className="mb-6 flex items-center gap-2.5 rounded-[8px] border border-amber-500/40 bg-amber-500/10 p-4 text-sm font-semibold text-amber-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-amber-400" />
          <span>{sessionNotice}</span>
        </div>
      )}

      {/* Progress Step Indicator */}
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
              city={data.city}
              province={data.province}
              targetField={data.target_field}
              onCityChange={(val) => updateData({ city: val })}
              onProvinceChange={(val) => updateData({ province: val })}
              onTargetFieldChange={(val) => updateData({ target_field: val })}
            />
          )}

          {error && (
            <div className="mt-6 flex items-center gap-2 rounded-[6px] border border-rose-900/60 bg-rose-950/30 p-3.5 text-xs text-rose-400">
              <AlertCircle className="h-4 w-4 shrink-0" />
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
              className="inline-flex items-center gap-2 rounded-[6px] border border-[#2A3650] bg-transparent hover:bg-[#1C2539] px-5 py-2.5 text-sm font-medium text-[#94A3B8] hover:text-[#F1F5F9] transition-colors disabled:opacity-50"
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
              className="inline-flex items-center gap-2 rounded-[6px] bg-[#3B82F6] hover:bg-[#2563EB] px-6 py-3 text-sm font-bold text-white transition-all shadow-sm"
            >
              <span>Continue</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleFinish}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-[6px] bg-[#3B82F6] hover:bg-[#2563EB] px-6 py-3 text-sm font-bold text-white transition-all shadow-md disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-white" />
                  <span>Setting Up Journey...</span>
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
