#!/usr/bin/env python3
"""
Dashboard Scrape Scheduled Task
================================
Uses the new dashboard ScrapeRunner (JobSpy) to scrape jobs, save to
job_tracker.db, auto-score, and send a Telegram summary.

Replaces the old daily_opportunity_detection + daily_jobspy_detection tasks
with a single, simpler flow that shares the same code as the dashboard UI.

Designed to be called from Windows Task Scheduler via the companion .bat file,
or directly:  python scripts/scheduled_tasks/dashboard_scrape_task.py
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List

# ── Path setup ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Import centralized job search configuration when available
try:
    from config import job_search_config as job_config  # type: ignore
except Exception:
    job_config = None

# ── Logging ────────────────────────────────────────────────────────
log_dir = PROJECT_ROOT / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "dashboard_scrape_task.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── Search Profiles ────────────────────────────────────────────────
# Each profile is a separate scraping run.  Keeps prompts small and
# lets us track which keywords bring results.

JOBSPY_SITES = ["indeed", "linkedin", "glassdoor", "google"]
NICHE_SITES = ["greenhouse", "ashby", "wellfound", "climatebase", "hackernews"]
ALL_SITES = JOBSPY_SITES + NICHE_SITES

DEFAULT_SEARCHES = [
    {"keywords": "data engineer", "location": "United States", "sites": ALL_SITES, "max_results": 30},
    {"keywords": "python developer", "location": "United States", "sites": ALL_SITES, "max_results": 25},
    {"keywords": "senior software engineer", "location": "Remote", "sites": ALL_SITES, "max_results": 25},
    {"keywords": "machine learning engineer", "location": "United States", "sites": ALL_SITES, "max_results": 20},
    {"keywords": "data scientist", "location": "United States", "sites": ALL_SITES, "max_results": 15},
]


def _build_searches_from_config() -> list:
    """Build search list from centralized job_search_config if available."""
    if job_config is None:
        return DEFAULT_SEARCHES

    try:
        keywords_list: List[str] = list(getattr(job_config, "SEARCH_TERMS", []))
        locations_list: List[str] = list(getattr(job_config, "LOCATIONS", []))
        if not keywords_list or not locations_list:
            return DEFAULT_SEARCHES

        remote_location = next(
            (loc for loc in locations_list if "remote" in str(loc).lower()),
            locations_list[0],
        )
        primary_city = next(
            (loc for loc in locations_list if "remote" not in str(loc).lower()),
            remote_location,
        )

        searches = []
        for kw in keywords_list[:6]:
            searches.append({
                "keywords": kw,
                "location": primary_city,
                "sites": ALL_SITES,
                "max_results": 25,
            })
        # Also add a remote-focused search for first keyword
        searches.append({
            "keywords": keywords_list[0],
            "location": remote_location,
            "sites": ALL_SITES,
            "max_results": 20,
            "remote_only": True,
        })
        return searches

    except Exception as exc:
        logger.warning("Failed to load config-based searches: %s", exc)
        return DEFAULT_SEARCHES


# ── Telegram ───────────────────────────────────────────────────────

def send_telegram_report(summary: str) -> bool:
    """Send a summary message to Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        logger.warning("Telegram not configured — skipping notification")
        return False

    try:
        import requests as req

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": summary,
            "parse_mode": "HTML",
        }
        resp = req.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        logger.info("Telegram notification sent")
        return True
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)
        return False


# ── Main ───────────────────────────────────────────────────────────

def run():
    start = datetime.now()
    logger.info("=" * 70)
    logger.info("DASHBOARD SCRAPE TASK — %s", start.strftime("%A %B %d, %Y %I:%M %p"))
    logger.info("=" * 70)

    from src.dashboard.db import DashboardDB
    from src.dashboard.scraper_runner import ScrapeConfig, ScrapeRunner

    db = DashboardDB()
    searches = _build_searches_from_config()

    total_new = 0
    total_dupes = 0
    total_scraped = 0
    all_errors = []
    per_search = []

    for i, search in enumerate(searches, 1):
        logger.info(
            "\n--- Search %d/%d: '%s' in %s ---",
            i, len(searches), search["keywords"], search["location"],
        )

        config = ScrapeConfig(
            keywords=search["keywords"],
            location=search["location"],
            sites=search.get("sites", ALL_SITES),
            max_results=search.get("max_results", 30),
            posted_since_days=search.get("posted_since_days", 7),
            remote_only=search.get("remote_only", False),
        )

        def log_progress(stage, pct, msg):
            logger.info("  [%3d%%] %s: %s", pct, stage, msg)

        runner = ScrapeRunner(db=db, progress_cb=log_progress)
        result = runner.run(config)

        total_new += result.new_jobs
        total_dupes += result.duplicates
        total_scraped += result.total_scraped
        all_errors.extend(result.errors)

        per_search.append({
            "keywords": search["keywords"],
            "new": result.new_jobs,
            "dupes": result.duplicates,
            "scraped": result.total_scraped,
            "sources": result.jobs_by_source,
        })

        logger.info(
            "  Result: %d new, %d dupes, %.1fs",
            result.new_jobs, result.duplicates, result.elapsed_seconds,
        )

    elapsed = (datetime.now() - start).total_seconds()

    # ── Summary ────────────────────────────────────────────────────
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info("Total scraped:    %d", total_scraped)
    logger.info("New jobs:         %d", total_new)
    logger.info("Duplicates:       %d", total_dupes)
    logger.info("Errors:           %d", len(all_errors))
    logger.info("Duration:         %.0fs", elapsed)

    if all_errors:
        logger.warning("Errors encountered:")
        for err in all_errors:
            logger.warning("  - %s", err)

    # ── Telegram notification ──────────────────────────────────────
    now_str = datetime.now().strftime("%b %d, %Y %I:%M %p")
    lines = [
        f"<b>Daily Job Scrape — {now_str}</b>",
        "",
        f"<b>{total_new}</b> new jobs found ({total_dupes} duplicates skipped)",
        f"Searched {len(searches)} keyword sets in {elapsed:.0f}s",
        "",
    ]
    for ps in per_search:
        if ps["new"] > 0:
            sources = ", ".join(f"{k}:{v}" for k, v in ps["sources"].items())
            lines.append(f"  • <b>{ps['keywords']}</b>: {ps['new']} new ({sources})")

    if all_errors:
        lines.append(f"\n⚠️ {len(all_errors)} error(s) — check logs")

    # Add dashboard stats
    try:
        stats = db.get_stats(days=7)
        lines.append("")
        lines.append(f"📊 DB: {stats.get('total', '?')} jobs (7d), {stats.get('remote', '?')} remote")
        if stats.get("avg_score"):
            lines.append(f"📈 Avg alignment: {stats['avg_score']:.0f}%")
    except Exception:
        pass

    lines.append(f"\n🔗 <a href='http://localhost:8888'>Open Dashboard</a>")

    send_telegram_report("\n".join(lines))

    logger.info("\nDone.")
    return total_new


if __name__ == "__main__":
    try:
        new_count = run()
        sys.exit(0 if new_count >= 0 else 1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)
