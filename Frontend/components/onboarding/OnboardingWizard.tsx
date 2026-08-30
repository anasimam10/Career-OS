"use client"

import { useRouter } from "next/navigation"
import { ArrowLeft, ArrowRight, Sparkles } from "lucide-react"
import { useOnboarding } from "@/hooks/useOnboarding"
import { StepIndicator } from "./StepIndicator"
import { Step1Education } from "./steps/Step1Education"
import { Step2Interests } from "./steps/Step2Interests"
import { Step3CareerField } from "./steps/Step3CareerField"
import { Step4Motivation } from "./steps/Step4Motivation"
import { Step5Sports } from "./steps/Step5Sports"
import { Step6Future } from "./steps/Step6Future"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/shared/ErrorState"

export function OnboardingWizard() {
  const router = useRouter()
  const {
    step,
    totalSteps,
    data,
    loading,
    error,
    nextStep,
    prevStep,
    updateData,
    toggleArrayItem,
    submit,
  } = useOnboarding()

  const handleFinish = async () => {
    try {
      await submit()
      router.push("/journey")
    } catch {
      // error handled in hook
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:py-12">
      <StepIndicator currentStep={step} totalSteps={totalSteps} />

      <div className="min-h-[360px] rounded-3xl border border-border bg-card p-6 sm:p-10 shadow-sm">
        {step === 1 && (
          <Step1Education
            value={data.education_stage}
            onChange={(val) => updateData({ education_stage: val })}
          />
        )}
        {step === 2 && (
          <Step2Interests
            selected={data.interests}
            onToggle={(val) => toggleArrayItem("interests", val)}
          />
        )}
        {step === 3 && (
          <Step3CareerField
            selected={data.career_interests}
            onToggle={(val) => toggleArrayItem("career_interests", val)}
          />
        )}
        {step === 4 && (
          <Step4Motivation
            selected={data.motivation_tags}
            onToggle={(val) => toggleArrayItem("motivation_tags", val)}
          />
        )}
        {step === 5 && (
          <Step5Sports
            selected={data.sports_interest}
            onSelect={(val) => updateData({ sports_interest: val })}
          />
        )}
        {step === 6 && (
          <Step6Future
            selectedGoals={data.future_goals}
            city={data.city}
            onToggleGoal={(val) => toggleArrayItem("future_goals", val)}
            onCityChange={(val) => updateData({ city: val })}
          />
        )}

        {error && <ErrorState message={error} />}

        {/* Navigation Buttons */}
        <div className="mt-10 flex items-center justify-between pt-6 border-t border-border">
          {step > 1 ? (
            <Button
              variant="outline"
              onClick={prevStep}
              disabled={loading}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Previous
            </Button>
          ) : (
            <div />
          )}

          {step < totalSteps ? (
            <Button onClick={nextStep} className="gap-2">
              Next Step
              <ArrowRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={handleFinish}
              disabled={loading}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <Sparkles className="h-4 w-4" />
              {loading ? "Generating Your Next Step..." : "Build My Journey"}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
