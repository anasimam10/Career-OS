import { AlertCircle, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

export function ErrorState({
  message = "Something went wrong. Please try again.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center rounded-2xl border border-destructive/20 bg-destructive/5 my-4">
      <AlertCircle className="h-8 w-8 text-destructive mb-3" />
      <h4 className="text-base font-semibold text-foreground">Service Notice</h4>
      <p className="mt-1 text-sm text-muted-foreground max-w-md">{message}</p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" size="sm" className="mt-4 gap-2">
          <RotateCcw className="h-3.5 w-3.5" />
          Try Again
        </Button>
      )}
    </div>
  )
}
