export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 p-3 rounded-2xl bg-muted/60 w-fit text-muted-foreground">
      <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
      <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
      <div className="h-2 w-2 rounded-full bg-primary animate-bounce" />
    </div>
  )
}
