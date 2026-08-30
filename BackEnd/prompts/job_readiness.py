"""
Job Readiness AI analysis prompt (Phase 8).

Qwen's role is limited to:
- explaining the biggest gap (2-3 sentences),
- producing a next best action,
- suggesting up to 3 concrete recommendations.

The overall_score, score_label, and component_scores are NEVER sent to
Qwen — they are deterministic backend values that Qwen cannot alter.
"""

from __future__ import annotations

from prompts.system_prompt import build_system_prompt

JOB_READINESS_RULES = """
JOB READINESS ANALYSIS RULES:
1. The student's component scores have already been calculated by the backend. Do NOT recalculate or modify them.
2. gap_explanation: Write 2-3 sentences about the student's biggest gap (the lowest-scoring component).
3. next_best_action: Produce a single actionable NextBestAction targeting the biggest gap.
4. recommendations: List up to 3 concrete, Pakistan-relevant suggestions to improve the lowest-scoring area.
5. Never invent specific companies, internships, scholarships, deadlines, salaries, or URLs.
6. Keep language concise and motivating.
7. Return valid JSON only. No preamble or markdown.
"""


def build_job_readiness_system_prompt(
    student_profile_json: str,
    component_scores_json: str,
    biggest_gap: str,
) -> str:
    """Build the system prompt for the job readiness AI analysis call."""
    context_data = (
        f"BIGGEST GAP: {biggest_gap}\n\n"
        f"COMPONENT SCORES (read-only, do not modify):\n{component_scores_json}"
    )
    return build_system_prompt(
        schema_name="JobReadinessAIAnalysis",
        student_profile_json=student_profile_json,
        structured_data_json=context_data,
        extra_rules=JOB_READINESS_RULES,
    )
