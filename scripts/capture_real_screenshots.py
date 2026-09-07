"""
Capture real, authentic, high-resolution screenshots from the live Career OS application
using Playwright with domcontentloaded + timeout.
"""

import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://career-os-seven-flame.vercel.app"
OUT_DIR = Path("Docs/presentation_assets")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def take_shot(page, name, url, clip=None, wait_ms=2000, pre_action=None):
    print(f"Capturing {name} from {url} ...", flush=True)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(wait_ms)
        if pre_action:
            pre_action(page)
            page.wait_for_timeout(1000)
        out_file = OUT_DIR / name
        if clip:
            page.screenshot(path=str(out_file), clip=clip)
        else:
            page.screenshot(path=str(out_file))
        print(f"  [OK] Saved {name} ({out_file.stat().st_size} bytes)", flush=True)
    except Exception as e:
        print(f"  [FAIL] Failed {name}: {e}", flush=True)

def capture_all():
    print(f"Using browser at: {CHROME_PATH}", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"]
        )
        
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.5
        )
        page = context.new_page()

        # 1. Homepage Hero
        take_shot(
            page, "01_hero_home.png", f"{BASE_URL}/",
            clip={"x": 0, "y": 0, "width": 1440, "height": 780},
            wait_ms=1500
        )

        # 2. Onboarding Step 1 (Education)
        take_shot(
            page, "02_onboarding_step1.png", f"{BASE_URL}/onboarding",
            clip={"x": 200, "y": 40, "width": 1040, "height": 820},
            wait_ms=1500
        )

        # 3. Onboarding Step 2 (Location)
        def select_edu_and_next(p):
            try:
                card = p.locator("div:has-text('Intermediate'), button:has-text('Intermediate')").first
                if card.is_visible():
                    card.click()
                    p.wait_for_timeout(500)
                nxt = p.locator("button:has-text('Next Step')").first
                if nxt.is_visible():
                    nxt.click()
            except Exception as e:
                print("Step 2 pre-action note:", e)

        take_shot(
            page, "03_onboarding_location.png", f"{BASE_URL}/onboarding",
            clip={"x": 200, "y": 40, "width": 1040, "height": 820},
            wait_ms=1500,
            pre_action=select_edu_and_next
        )

        # 4. Careers Directory
        take_shot(
            page, "04_careers_directory.png", f"{BASE_URL}/careers",
            clip={"x": 100, "y": 40, "width": 1240, "height": 820},
            wait_ms=2000
        )

        # 5. Reality Check for Software Engineering
        def wait_for_data(p):
            try:
                p.wait_for_selector('.animate-pulse', state='detached', timeout=15000)
            except Exception as e:
                print('Note waiting for pulse:', e)
            p.wait_for_timeout(2000)

        take_shot(
            page, "05_reality_check.png", f"{BASE_URL}/careers/software-engineering/reality-check",
            clip={"x": 80, "y": 40, "width": 1280, "height": 840},
            wait_ms=1000,
            pre_action=wait_for_data
        )

        # 6. 7-Day Career Trial
        take_shot(
            page, "06_seven_day_trial.png", f"{BASE_URL}/careers/software-engineering/trial",
            clip={"x": 80, "y": 40, "width": 1280, "height": 840},
            wait_ms=1000,
            pre_action=wait_for_data
        )

        # 7. Universities Directory
        take_shot(
            page, "07_universities.png", f"{BASE_URL}/universities",
            clip={"x": 80, "y": 40, "width": 1280, "height": 840},
            wait_ms=2500
        )

        # 8. Opportunities Directory
        take_shot(
            page, "08_opportunities.png", f"{BASE_URL}/opportunities",
            clip={"x": 80, "y": 40, "width": 1280, "height": 840},
            wait_ms=2500
        )

        # 9. Mock Interview Setup
        take_shot(
            page, "09_mock_interview.png", f"{BASE_URL}/mock-interview",
            clip={"x": 120, "y": 40, "width": 1200, "height": 820},
            wait_ms=2000
        )

        # 10. Sports Opportunities
        take_shot(
            page, "10_sports.png", f"{BASE_URL}/sports",
            clip={"x": 80, "y": 40, "width": 1280, "height": 840},
            wait_ms=2500
        )

        # 11. Alumni Coming Soon Preview
        take_shot(
            page, "11_alumni.png", f"{BASE_URL}/alumni",
            clip={"x": 120, "y": 40, "width": 1200, "height": 820},
            wait_ms=1500
        )

        # 12. Job Readiness
        take_shot(
            page, "12_job_readiness.png", f"{BASE_URL}/job-readiness",
            clip={"x": 100, "y": 40, "width": 1240, "height": 840},
            wait_ms=2500
        )

        # 13. Journey with active student
        page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        page.evaluate("() => { localStorage.setItem('career_os_student_id', '1'); localStorage.setItem('career_os_user_id', '1'); }")
        take_shot(
            page, "13_journey.png", f"{BASE_URL}/journey",
            clip={"x": 80, "y": 40, "width": 1280, "height": 840},
            wait_ms=5000
        )

        browser.close()
        print("Done capturing screenshots!", flush=True)

if __name__ == "__main__":
    capture_all()
