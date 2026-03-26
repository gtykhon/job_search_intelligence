from playwright.sync_api import sync_playwright
from pathlib import Path

STORAGE_PATH = Path(__file__).parent / "glassdoor_storage.json"

def main():
    print("Opening Chromium for Glassdoor login...")
    print("1) Log in to Glassdoor in the opened browser")
    print("2) Navigate to any normal page (e.g., company search)")
    print("3) When finished, come back to this terminal and press ENTER")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.glassdoor.com/profile/login_input.htm", wait_until="load")

        input("\nWhen you are fully logged in and Glassdoor looks normal, press ENTER here...")

        context.storage_state(path=str(STORAGE_PATH))
        print(f"\nSaved Glassdoor session to {STORAGE_PATH}")

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
