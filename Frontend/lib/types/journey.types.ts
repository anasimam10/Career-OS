export type EducationStage =
  | "HIGH_SCHOOL"
  | "CAREER_DISCOVERY"
  | "CAREER_DECISION"
  | "UNIVERSITY"
  | "SKILL_BUILDING"
  | "PROJECTS"
  | "INTERNSHIP"
  | "FINAL_YEAR"
  | "JOB_PREPARATION"
  | "FIRST_JOB"

export type MilestoneStatus = "pending" | "active" | "done" | "skipped"

export interface NextBestAction {
  title: string
  description: string
  steps: string[]
  estimated_time: string
  why_this_matters: string
  stage: string
}

export interface Milestone {
  id: number
  title: string
  description: string
  stage: EducationStage
  status: MilestoneStatus
  order_index: number
  completed_at: string | null
}

export interface JourneyStep {
  id?: number
  title: string
  description: string
  stage: EducationStage
  estimated_duration?: string
  status?: "pending" | "active" | "completed" | "done" | "skipped" | "locked"
  phase?: string
}

export type MilestoneStateStatus = "locked" | "active" | "completed"

export interface MilestoneItem {
  id: number
  title: string
  description: string
  status: MilestoneStateStatus
  phase: number
  order: number
}

export interface JourneyResponse {
  milestones: MilestoneItem[]
  current_milestone_id?: number | null
  completed_count: number
  total_count: number
  stage?: EducationStage
  current_step?: string
  next_steps?: JourneyStep[]
  next_best_action?: NextBestAction
}

export interface ProgressResponse {
  new_stage: EducationStage
  next_best_action: NextBestAction
}

export interface RoadmapResponse {
  roadmap_id: number
  current_step: string
  visible_steps: JourneyStep[]
}

export const STAGE_LABELS: Record<EducationStage, string> = {
  HIGH_SCHOOL: "High School",
  CAREER_DISCOVERY: "Discover",
  CAREER_DECISION: "Decide",
  UNIVERSITY: "University",
  SKILL_BUILDING: "Build Skills",
  PROJECTS: "Projects",
  INTERNSHIP: "Internship",
  FINAL_YEAR: "Final Year",
  JOB_PREPARATION: "Job Prep",
  FIRST_JOB: "First Job",
}

export const STAGE_ORDER: EducationStage[] = [
  "HIGH_SCHOOL",
  "CAREER_DISCOVERY",
  "CAREER_DECISION",
  "UNIVERSITY",
  "SKILL_BUILDING",
  "PROJECTS",
  "INTERNSHIP",
  "FINAL_YEAR",
  "JOB_PREPARATION",
  "FIRST_JOB",
]
