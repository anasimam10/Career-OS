import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://career-os-seven-flame.vercel.app"
OUT_DIR = Path("Docs/presentation_assets")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def capture_skills():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME_PATH, headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
        page.goto(f"{BASE_URL}/onboarding", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        # Step 1 -> Click Intermediate -> Next
        page.locator("div:has-text('Intermediate'), button:has-text('Intermediate')").first.click()
        page.wait_for_timeout(500)
        page.locator("button:has-text('Next Step')").first.click()
        page.wait_for_timeout(800)

        # Step 2 -> Province/City -> Next
        page.locator("button:has-text('Next Step')").first.click()
        page.wait_for_timeout(800)

        # Step 3 -> Career Field -> Click first or Next
        try:
            page.locator("div:has-text('Software'), button:has-text('Software')").first.click()
            page.wait_for_timeout(500)
        except Exception:
            pass
        page.locator("button:has-text('Next Step')").first.click()
        page.wait_for_timeout(800)

        # Step 4 -> Interests -> Next
        page.locator("button:has-text('Next Step')").first.click()
        page.wait_for_timeout(800)

        # Step 5 -> Skills!
        page.screenshot(path=str(OUT_DIR / "03b_onboarding_skills.png"), clip={"x": 200, "y": 40, "width": 1040, "height": 820})
        print("[OK] Saved 03b_onboarding_skills.png")
        browser.close()

if __name__ == "__main__":
    capture_skills()
