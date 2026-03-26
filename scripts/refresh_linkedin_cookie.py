#!/usr/bin/env python3
"""
Refresh LinkedIn li_at cookie using Playwright with Chrome's persistent profile.

Usage:
  python scripts/refresh_linkedin_cookie.py

Requirements:
  - Chrome must be CLOSED (Playwright needs exclusive access to the profile)
  - User must be logged into LinkedIn in Chrome
  - Writes the fresh li_at cookie to .env LINKEDIN_LI_AT

Can be called manually or from the daily content performance task
when the existing cookie is expired.
"""

import os
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CHROME_USER_DATA = os.getenv(
    "CHROME_USER_DATA_DIR",
    os.path.expanduser("~/.config/google-chrome") if os.name == 'nt' else os.path.expanduser("~/.config/google-chrome"),
)
ENV_FILE = PROJECT_ROOT / ".env"


PLAYWRIGHT_PROFILE = PROJECT_ROOT / "data" / "playwright_linkedin_profile"


def refresh_cookie() -> str:
    """Launch Playwright Chromium with a persistent profile, grab li_at cookie.

    First run: opens a visible browser for manual LinkedIn login.
    Subsequent runs: reuses the stored session (headless).

    Returns the li_at cookie value, or empty string on failure.
    """
    from playwright.sync_api import sync_playwright

    first_run = not PLAYWRIGHT_PROFILE.exists()
    headless = False  # always visible — needed for RDP/login

    logger.info(
        "Launching Playwright Chromium (%s)...",
        "VISIBLE — log in manually" if first_run else "headless",
    )

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PLAYWRIGHT_PROFILE),
                headless=headless,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 800},
            )
        except Exception as exc:
            logger.error("Playwright launch failed: %s", exc)
            return ""

        page = context.pages[0] if context.pages else context.new_page()

        logger.info("Loading linkedin.com...")
        try:
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            logger.warning("Page load issue: %s", exc)

        # If first run or on login page, wait for manual login
        current_url = page.url
        if first_run or "/login" in current_url or "/checkpoint" in current_url:
            logger.info("=" * 50)
            logger.info("Log in to LinkedIn in the browser window.")
            logger.info("Waiting up to 120 seconds for login...")
            logger.info("=" * 50)
            try:
                page.wait_for_url("**/feed/**", timeout=120000)
                logger.info("Login detected — grabbing cookies...")
            except Exception:
                logger.warning("Timeout waiting for login — checking cookies anyway...")

        # Extract li_at cookie
        cookies = context.cookies("https://www.linkedin.com")
        li_at = ""
        jsessionid = ""
        for c in cookies:
            if c["name"] == "li_at":
                li_at = c["value"]
            if c["name"] == "JSESSIONID":
                jsessionid = c["value"]

        context.close()

    if not li_at:
        logger.error("No li_at cookie found — are you logged into LinkedIn in Chrome?")
        return ""

    logger.info("Got li_at cookie (len=%d)", len(li_at))

    # Update .env file
    _update_env("LINKEDIN_LI_AT", li_at)
    if jsessionid:
        _update_env("LINKEDIN_JSESSIONID", jsessionid.strip('"'))

    # Verify it works
    import requests
    s = requests.Session()
    s.cookies.set("li_at", li_at, domain=".linkedin.com")
    s.cookies.set("JSESSIONID", jsessionid or "ajax:0000000000000000000", domain=".linkedin.com")
    s.headers.update({
        "csrf-token": (jsessionid or "ajax:0000000000000000000").strip('"'),
        "x-li-lang": "en_US",
        "x-restli-protocol-version": "2.0.0",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    r = s.get("https://www.linkedin.com/voyager/api/me", timeout=15, allow_redirects=False)
    if r.status_code == 200:
        me = r.json().get("miniProfile", {})
        logger.info("Verified: %s %s", me.get("firstName", ""), me.get("lastName", ""))
    else:
        logger.warning("Cookie verification returned %s — may be expired", r.status_code)

    return li_at


def _update_env(key: str, value: str):
    """Update or add a key in the .env file."""
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Updated %s in .env", key)


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    result = refresh_cookie()
    if result:
        print(f"Success — li_at cookie refreshed ({len(result)} chars)")
        sys.exit(0)
    else:
        print("Failed — see log above")
        sys.exit(1)
