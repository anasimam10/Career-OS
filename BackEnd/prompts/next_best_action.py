"""
Next Best Action prompt (Phase 4).

Candidate-constrained selection: Qwen receives the deterministic candidate
list produced by candidate_service and may only SELECT one of them. It can
never invent an action, an opportunity, or a deadline — the master system
prompt (prompts/system_prompt.py) already forbids that, and these rules
restate the selection constraint for this call.
"""

from __future__ import annotations

from prompts.system_prompt import build_system_prompt

NBA_SELECTION_RULES = """
NEXT BEST ACTION SELECTION RULES:
- You must select exactly ONE candidate_id from the provided candidate list.
- Never invent a candidate_id. Never invent an action that is not in the list.
- Never invent an opportunity, organization, university, deadline, salary, or URL.
- Never create a different action. Choose only from the provided candidates.
- "why_this_matters" must be ONE concise sentence, personalized to the student
  using ONLY the supplied student context and the candidate's own reason.
  Never state facts that are not present in the supplied data.
- Keep the explanation concise.
- Return valid JSON only.
"""


def build_nba_system_prompt(
    student_profile_json: str,
    journey_state_json: str,
    candidates_json: str,
) -> str:
    """
    System prompt for the NBA selection call.

    Sections (all via the master template — no duplication):
    - student profile context,
    - the current journey state,
    - the valid candidate actions (the only selectable set),
    - the selection rules.
    """
    structured_data = (
        "CURRENT JOURNEY STATE:\n"
        f"{journey_state_json}\n\n"
        "VALID CANDIDATE ACTIONS (the ONLY selectable actions):\n"
        f"{candidates_json}"
    )
    return build_system_prompt(
        schema_name="NBASelection",
        student_profile_json=student_profile_json,
        structured_data_json=structured_data,
        extra_rules=NBA_SELECTION_RULES,
    )


def build_nba_user_prompt() -> str:
    return (
        "Select the single best next action for this student right now.\n\n"
        "Consider:\n"
        "- the student's current journey stage and career goal,\n"
        "- what the student has already completed,\n"
        "- each candidate's priority_score and reason.\n\n"
        "Return the selected candidate_id and one concise personalized "
        "why_this_matters sentence."
    )
