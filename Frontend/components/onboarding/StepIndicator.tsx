import React from "react"
import { cn } from "@/lib/utils/cn"

interface StepIndicatorProps {
  currentStep: number
  totalSteps: number
}

export function StepIndicator({ currentStep, totalSteps }: StepIndicatorProps) {
  return (
    <div className="flex flex-col items-center justify-center space-y-2">
      <span className="text-xs font-semibold tracking-wider text-[#94A3B8] uppercase">
        Step {currentStep} of {totalSteps}
      </span>
      <div className="flex items-center space-x-2">
        {Array.from({ length: totalSteps }).map((_, i) => {
          const stepNum = i + 1
          const isActive = currentStep === stepNum
          const isPast = currentStep > stepNum

          return (
            <div
              key={i}
              className={cn(
                "h-1.5 rounded-full transition-all duration-300",
                isActive
                  ? "w-8 bg-[#3B82F6] shadow-[0_0_8px_rgba(59,130,246,0.6)]"
                  : isPast
                  ? "w-4 bg-[#3B82F6]/60"
                  : "w-2.5 bg-[#2A3650]"
              )}
            />
          )
        })}
      </div>
    </div>
  )
}
