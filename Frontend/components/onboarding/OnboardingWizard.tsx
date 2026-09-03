"use client"

import { useRouter } from "next/navigation"
import { ArrowLeft, ArrowRight, Sparkles } from "lucide-react"
import { useOnboarding } from "@/hooks/useOnboarding"
import { StepIndicator } from "./StepIndicator"
import { Step1Education } from "./steps/Step1Education"
import { Step2Location } from "./steps/Step2Location"
import { Step3CareerField } from "./steps/Step3CareerField"
import { Step4Motivation } from "./steps/Step4Motivation"
import { Step5Skills } from "./steps/Step5Skills"
import { Step6Future } from "./steps/Step6Future"
import { Step5Sports as Step7Sports } from "./steps/Step5Sports"
import { Step8Transition } from "./steps/Step8Transition"
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
      nextStep()
      await submit()
      setTimeout(() => {
        router.push("/journey")
      }, 1200)
    } catch {
      // If submission fails, revert transition step so student can see error and retry
      prevStep()
    }
  }

  // Hide navigation buttons on the final transition screen
  const isTransitionStep = step === 8

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:py-16">
      {!isTransitionStep && (
        <div className="mb-12">
          <StepIndicator currentStep={step} totalSteps={totalSteps - 1} />
        </div>
      )}

      <div className="min-h-[400px] relative rounded-[2rem] border border-slate-800/60 bg-slate-900/40 p-6 sm:p-12 shadow-2xl backdrop-blur-sm overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-1/2 bg-indigo-500/10 blur-[100px] pointer-events-none rounded-full" />
        
        <div className="relative z-10">
          {step === 1 && (
            <Step1Education
              value={data.education_stage}
              onChange={(val) => updateData({ education_stage: val })}
            />
          )}
          {step === 2 && (
            <Step2Location
              city={data.city}
              onCityChange={(val) => updateData({ city: val })}
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
            <Step5Skills
              selected={data.skills.map((s) => s.name)}
              onToggle={(val) => {
                const isSelected = data.skills.some((s) => s.name === val)
                if (isSelected) {
                  updateData({ skills: data.skills.filter((s) => s.name !== val) })
                } else {
                  updateData({ skills: [...data.skills, { name: val, level: "beginner" }] })
                }
              }}
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
          {step === 7 && (
            <Step7Sports
              selected={data.sports_interest}
              onSelect={(val) => updateData({ sports_interest: val })}
            />
          )}
          {step === 8 && (
            <Step8Transition />
          )}

          {error && <div className="mt-8"><ErrorState message={error} /></div>}
        </div>

        {/* Navigation Buttons */}
        <div className={`mt-12 flex items-center justify-between pt-6 border-t border-slate-800/60 relative z-10 transition-opacity duration-500 ${isTransitionStep ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
          {step > 1 && !isTransitionStep ? (
            <Button
              variant="outline"
              onClick={prevStep}
              disabled={loading}
              className="gap-2 border-slate-700 hover:bg-slate-800 hover:text-white"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          ) : (
            <div />
          )}

          {!isTransitionStep && (
            step < totalSteps - 1 ? (
              <Button onClick={nextStep} className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white">
                Continue
                <ArrowRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                onClick={handleFinish}
                disabled={loading}
                className="gap-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold"
              >
                <Sparkles className="h-4 w-4" />
                Finish
              </Button>
            )
          )}
        </div>
      </div>
    </div>
  )
}
