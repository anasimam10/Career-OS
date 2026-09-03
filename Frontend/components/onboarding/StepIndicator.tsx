import { cn } from "@/lib/utils/cn"

interface StepIndicatorProps {
  currentStep: number
  totalSteps: number
}

export function StepIndicator({ currentStep, totalSteps }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center space-x-2">
      {Array.from({ length: totalSteps }).map((_, i) => {
        const stepNum = i + 1
        const isActive = currentStep === stepNum
        const isPast = currentStep > stepNum

        return (
          <div key={i} className="flex items-center">
            <div
              className={cn(
                "h-1.5 rounded-full transition-all duration-500",
                isActive ? "w-8 bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]" : 
                isPast ? "w-4 bg-indigo-500/50" : "w-2 bg-slate-800"
              )}
            />
            {i < totalSteps - 1 && (
              <div className="w-1.5" /> /* Gap between dots */
            )}
          </div>
        )
      })}
    </div>
  )
}
