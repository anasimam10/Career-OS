import { apiPost } from "./client"
import { USE_MOCK } from "@/lib/mock"
import type { JobReadinessResponse } from "@/lib/types/job-readiness.types"

export async function getJobReadiness(): Promise<JobReadinessResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 1500))
    return {
      overall_score: 0.45,
      score_label: "45%",
      component_scores: { skills: 0.5, projects: 0.4, internship: 0.0, cv: 0.75, interview: 0.33 },
      biggest_gap: "internship",
      gap_explanation: "Your biggest gap is internship experience. Without hands-on work experience, employers may hesitate.",
      next_best_action: {
        title: "Search for Internships",
        description: "Research and apply for at least one internship opportunity.",
        steps: ["Update your CV", "Search for internships", "Apply to 3 positions"],
        estimated_time: "2 weeks",
        why_this_matters: "Internship experience is crucial for landing your first job.",
        stage: "INTERNSHIP",
      },
      recommendations: [
        "Update your LinkedIn profile to attract recruiters",
        "Apply to local tech companies for summer internships",
        "Build a portfolio project to showcase your skills",
      ],
      disclaimer: "This job readiness score is a product indicator based on your tracked milestones and profile data. It is not a scientifically validated assessment of your employability. Use it as a general guide only.",
    }
  }
  return apiPost<JobReadinessResponse>("/job-readiness", {})
}
