export interface JobReadinessResponse {
  overall_score: number
  score_label: string
  component_scores: Record<string, number>
  biggest_gap: string
  gap_explanation: string
  next_best_action: {
    title: string
    description: string
    steps: string[]
    estimated_time: string
    why_this_matters: string
    stage: string
  }
  recommendations: string[]
  disclaimer: string
}
