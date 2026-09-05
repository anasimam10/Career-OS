import React from "react"
import type { JourneyStep } from "@/lib/types/journey.types"
import { MilestoneCard, type MilestoneCardState } from "@/app/journey/MilestoneCard"

interface RoadmapStepsProps {
  steps: JourneyStep[]
  onCompleteStep?: (stepId?: number) => void
  completingStepId?: number | null
  stepError?: { stepId: number; message: string } | null
}

export function RoadmapSteps({
  steps,
  onCompleteStep,
  completingStepId,
  stepError,
}: RoadmapStepsProps) {
  // Architecture rule: strictly max 3 steps shown
  const visibleSteps = steps.slice(0, 3)

  // Find the index of the first incomplete step
  const activeIndex = visibleSteps.findIndex(
    (s) => s.status !== "completed" && s.status !== "done"
  )

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {visibleSteps.map((step, idx) => {
        let state: MilestoneCardState = "locked"

        if (step.status === "completed" || step.status === "done") {
          state = "completed"
        } else if (idx === activeIndex || (activeIndex === -1 && idx === 0)) {
          state = "active"
        } else if (idx < activeIndex) {
          state = "completed"
        } else {
          state = "locked"
        }

        const isBusy = completingStepId === step.id
        const errorMessage = stepError && stepError.stepId === step.id ? stepError.message : null

        return (
          <MilestoneCard
            key={step.id ?? idx}
            step={step}
            phaseIndex={idx + 1}
            state={state}
            onComplete={onCompleteStep}
            isCompleting={isBusy}
            error={errorMessage}
          />
        )
      })}
    </div>
  )
}
