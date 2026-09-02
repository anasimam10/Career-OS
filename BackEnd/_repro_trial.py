"""Reproduce the 7-Day Trial page error: the exact request the frontend makes."""

import json
import sys

import httpx

BASE = "http://127.0.0.1:8000/api/v1"

with httpx.Client(timeout=300.0) as client:
    # 1. The career the flow would land on
    r = client.get(f"{BASE}/careers/software-engineering")
    print("GET /careers/software-engineering:", r.status_code)

    # 2. The exact trial-plan request the frontend sends
    r = client.post(f"{BASE}/career/trial-plan", json={"career_slug": "software-engineering"})
    print("POST /career/trial-plan:", r.status_code)
    try:
        body = r.json()
    except Exception:
        body = r.text
    if isinstance(body, dict):
        print("  career_slug:", body.get("career_slug"))
        print("  duration_days:", body.get("duration_days"))
        days = body.get("days")
        print("  days type:", type(days).__name__, "len:", len(days) if isinstance(days, list) else "n/a")
        if isinstance(days, list) and days:
            print("  day[0] keys:", sorted(days[0].keys()) if isinstance(days[0], dict) else days[0])
            for i, d in enumerate(days):
                if isinstance(d, dict):
                    print(
                        f"    day[{i}]: day_range={d.get('day_range')!r} "
                        f"title={d.get('title')!r} tasks={type(d.get('tasks')).__name__}"
                        f"({len(d.get('tasks') or []) if isinstance(d.get('tasks'), list) else '?'})"
                    )
        print("  reflection_prompt:", (body.get("reflection_prompt") or "")[:80])
        if r.status_code != 200:
            print("  FULL BODY:", json.dumps(body, ensure_ascii=False)[:2000])
    else:
        print("  BODY:", str(body)[:2000])
