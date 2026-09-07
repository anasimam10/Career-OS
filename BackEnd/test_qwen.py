"""
Manual Qwen connectivity proof — NOT part of the pytest suite.

Usage:
    cd BackEnd
    .venv\\Scripts\\python.exe test_qwen.py

Makes exactly ONE real API call using the configured model (qwen-plus-2025-07-28)
and validates the response against the NextBestAction schema.
Never prints credentials.
"""

import sys

from schemas.shared import NextBestAction
from services.ai_service import AIService, AIServiceError


def main() -> int:
    service = AIService()

    if not service.is_configured():
        print(
            "FAILED: AI service is not configured "
            "(missing DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL in the environment)."
        )
        return 1

    prompt = (
        "Student context:\n"
        "- education_stage: HIGH_SCHOOL\n"
        "- interests: technology, mathematics\n"
        "- skills: Python (beginner)\n"
        "- city: Karachi\n\n"
        "Generate ONE Next Best Action for this student."
    )

    try:
        nba = service.call_structured(prompt, NextBestAction, operation="qwen_connectivity_proof")
    except AIServiceError as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return 1

    print("SUCCESS: Qwen responded and the output validated as NextBestAction.")
    print(f"  title          : {nba.title}")
    print(f"  estimated_time : {nba.estimated_time}")
    print(f"  stage          : {nba.stage}")
    print(f"  steps          : {len(nba.steps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
