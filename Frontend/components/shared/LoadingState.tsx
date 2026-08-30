import { Skeleton } from "@/components/ui/skeleton"

export function LoadingState({ message = "Loading guidance..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 space-y-4">
      <div className="flex space-x-2">
        <div className="h-3 w-3 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
        <div className="h-3 w-3 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
        <div className="h-3 w-3 rounded-full bg-primary animate-bounce" />
      </div>
      <p className="text-sm font-medium text-muted-foreground">{message}</p>
    </div>
  )
}
