export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "Unknown"
  const date = new Date(dateStr)
  return date.toLocaleDateString("en-PK", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function formatScore(value: number): string {
  if (value >= 0.8) return "Excellent"
  if (value >= 0.6) return "Good"
  if (value >= 0.4) return "Fair"
  return "Needs Work"
}

export function formatDemandLevel(level: string): string {
  return level.charAt(0) + level.slice(1).toLowerCase()
}

export function clampArray<T>(arr: T[], max: number): T[] {
  return arr.slice(0, max)
}
