"""
Coach Chat system prompt (Phase 8).

Built on the master system prompt. Injects student context and
hard grounding rules so Qwen never invents factual data.
"""

from __future__ import annotations

from prompts.system_prompt import build_system_prompt

COACH_RULES = """
COACH RESPONSE RULES:
1. quick_actions must contain at most 3 short (< 10 words each) follow-up questions or actions.
2. suggested_resource must be null unless a verified resource title was provided in the AVAILABLE VERIFIED DATA section.
3. Never invent Pakistani universities, jobs, internships, scholarships, deadlines, salaries, URLs, or tournament details.
4. If no verified opportunity data was provided, do not mention specific opportunities.
5. General career advice, motivation, and educational guidance are always allowed.
6. Keep the response concise — 2 to 4 short paragraphs maximum.
7. Always output valid JSON only. No preamble or markdown.
"""


def build_coach_system_prompt(
    student_profile_json: str,
    context_data_json: str,
) -> str:
    """Build the coach system prompt with student context and verified data."""
    return build_system_prompt(
        schema_name="CoachResponse",
        student_profile_json=student_profile_json,
        structured_data_json=context_data_json,
        extra_rules=COACH_RULES,
    )


def build_coach_user_prompt(
    conversation_history_text: str,
    message: str,
) -> str:
    """Build the user message including trimmed conversation history."""
    parts = []
    if conversation_history_text:
        parts.append(f"CONVERSATION HISTORY:\n{conversation_history_text}")
    parts.append(f"STUDENT MESSAGE:\n{message}")
    parts.append(
        "Respond as a helpful Pakistan-focused career mentor. "
        "Return valid JSON matching the CoachResponse schema exactly."
    )
    return "\n\n".join(parts)
