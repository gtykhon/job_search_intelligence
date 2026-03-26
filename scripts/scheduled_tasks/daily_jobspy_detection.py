#!/usr/bin/env python3
"""
Daily Opportunity Detection with JobSpy Integration
Fetches REAL job postings from LinkedIn, Indeed, Glassdoor
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

# Import centralized job search configuration when available
try:
    from config import job_search_config as job_config  # type: ignore
except Exception:
    job_config = None

if job_config is not None:
    IGNORED_COMPANIES = list(getattr(job_config, "IGNORED_COMPANIES", []))
    is_ignored_company = getattr(job_config, "is_ignored_company", None)
else:
    IGNORED_COMPANIES = []
    is_ignored_company = None

# Setup logging
log_dir = Path(parent_dir) / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'jobspy_opportunities.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import JobSpy scraper and database
from src.intelligence.jobspy_scraper import JobSpyScraper
from src.intelligence.models import ScrapingRequest, JobSite, JobListing, RemoteType
from src.intelligence.job_database import JobDatabase

# Import additional scrapers (all gracefully degrade if dependencies missing or sites block)
try:
    from src.intelligence.hn_scraper import scrape_hn_jobs
    HAS_HN_SCRAPER = True
except ImportError:
    HAS_HN_SCRAPER = False

try:
    from src.intelligence.wellfound_scraper import scrape_wellfound_jobs
    HAS_WELLFOUND_SCRAPER = True
except ImportError:
    HAS_WELLFOUND_SCRAPER = False

try:
    from src.intelligence.climatebase_scraper import scrape_climatebase_jobs
    HAS_CLIMATEBASE_SCRAPER = True
except ImportError:
    HAS_CLIMATEBASE_SCRAPER = False

try:
    from src.intelligence.greenhouse_scraper import scrape_greenhouse_jobs
    HAS_GREENHOUSE_SCRAPER = True
except ImportError:
    HAS_GREENHOUSE_SCRAPER = False

try:
    from src.intelligence.ashby_scraper import scrape_ashby_jobs
    HAS_ASHBY_SCRAPER = True
except ImportError:
    HAS_ASHBY_SCRAPER = False

try:
    from src.intelligence.climatetechlist_scraper import scrape_climatetechlist_jobs
    HAS_CLIMATETECHLIST_SCRAPER = True
except ImportError:
    HAS_CLIMATETECHLIST_SCRAPER = False

try:
    from src.intelligence.levelsfyi_scraper import scrape_levelsfyi_jobs
    HAS_LEVELSFYI_SCRAPER = True
except ImportError:
    HAS_LEVELSFYI_SCRAPER = False

try:
    from src.intelligence.otta_scraper import scrape_otta_jobs
    HAS_OTTA_SCRAPER = True
except ImportError:
    HAS_OTTA_SCRAPER = False


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


async def run_jobspy_opportunity_detection():
    """Run daily opportunity detection using JobSpy for real job postings"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("🎯 DAILY JOB OPPORTUNITY DETECTION - JobSpy Integration")
    logger.info(f"📅 {start_time.strftime('%A, %B %d, %Y at %I:%M %p')}")
    logger.info("=" * 80)
    
    # Initialize database
    db = JobDatabase()
    logger.info("💾 Database initialized")
    
    # Initialize JobSpy scraper
    scraper = JobSpyScraper(config={
        'max_workers': 3,
        'request_delay': 2.0,
        'requests_per_minute': 30
    })
    
    if not await scraper.initialize():
        logger.error("❌ Failed to initialize JobSpy scraper")
        return
    
    # Define search requests - Now includes Glassdoor and Google Jobs!
    search_requests = [
        ScrapingRequest(
            keywords="Python Developer",
            location="Washington, DC",
            job_sites=[JobSite.INDEED, JobSite.LINKEDIN, JobSite.GLASSDOOR],
            max_results=25,
            posted_since_days=7
        ),
        ScrapingRequest(
            keywords="Machine Learning Engineer",
            location="Washington, DC",
            job_sites=[JobSite.INDEED, JobSite.LINKEDIN, JobSite.GLASSDOOR],
            max_results=20,
            posted_since_days=7
        ),
        ScrapingRequest(
            keywords="Senior Software Engineer Python",
            location="Remote",
            job_sites=[JobSite.INDEED, JobSite.LINKEDIN, JobSite.GOOGLE_JOBS],
            max_results=20,
            posted_since_days=7,
            remote_type=RemoteType.REMOTE
        ),
        ScrapingRequest(
            keywords="Data Scientist Python",
            location="Washington, DC",
            job_sites=[JobSite.INDEED, JobSite.GLASSDOOR],
            max_results=15,
            posted_since_days=7
        ),
        ScrapingRequest(
            keywords="Senior Python Engineer",
            location="Washington, DC",
            job_sites=[JobSite.GOOGLE_JOBS],
            max_results=15,
            posted_since_days=7
        )
    ]

    # Override search requests using centralized job config when available
    if job_config is not None:
        try:
            keywords_list: List[str] = list(getattr(job_config, "SEARCH_TERMS", []))
            locations_list: List[str] = list(getattr(job_config, "LOCATIONS", []))

            if keywords_list and locations_list:
                remote_locations = [
                    loc for loc in locations_list if "remote" in str(loc).lower()
                ]
                remote_location = (
                    remote_locations[0]
                    if remote_locations
                    else locations_list[0]
                )
                primary_city = next(
                    (
                        loc
                        for loc in locations_list
                        if "remote" not in str(loc).lower()
                    ),
                    remote_location,
                )

                search_requests = [
                    ScrapingRequest(
                        keywords=keywords_list[0],
                        location=primary_city,
                        job_sites=[JobSite.INDEED, JobSite.LINKEDIN, JobSite.GLASSDOOR],
                        max_results=25,
                        posted_since_days=7,
                    ),
                    ScrapingRequest(
                        keywords=keywords_list[1]
                        if len(keywords_list) > 1
                        else keywords_list[0],
                        location=primary_city,
                        job_sites=[JobSite.INDEED, JobSite.LINKEDIN, JobSite.GLASSDOOR],
                        max_results=20,
                        posted_since_days=7,
                    ),
                    ScrapingRequest(
                        keywords=keywords_list[2]
                        if len(keywords_list) > 2
                        else keywords_list[0],
                        location=remote_location,
                        job_sites=[
                            JobSite.INDEED,
                            JobSite.LINKEDIN,
                            JobSite.GOOGLE_JOBS,
                        ],
                        max_results=20,
                        posted_since_days=7,
                        remote_type=RemoteType.REMOTE,
                    ),
                    ScrapingRequest(
                        keywords=keywords_list[3]
                        if len(keywords_list) > 3
                        else keywords_list[0],
                        location=primary_city,
                        job_sites=[JobSite.INDEED, JobSite.GLASSDOOR],
                        max_results=15,
                        posted_since_days=7,
                    ),
                    ScrapingRequest(
                        keywords=keywords_list[4]
                        if len(keywords_list) > 4
                        else keywords_list[0],
                        location=primary_city,
                        job_sites=[JobSite.GOOGLE_JOBS],
                        max_results=15,
                        posted_since_days=7,
                    ),
                ]
        except Exception as config_error:
            logger.warning(
                f"Failed to override JobSpy search requests from job_search_config: {config_error}"
            )
    
    all_jobs: List[JobListing] = []
    
    # Execute searches
    for i, request in enumerate(search_requests, 1):
        logger.info(f"\n🔍 Search {i}/{len(search_requests)}: {request.keywords} in {request.location}")
        
        try:
            jobs = await scraper.scrape_jobs(request)
            all_jobs.extend(jobs)
            logger.info(f"✅ Found {len(jobs)} jobs for '{request.keywords}'")
            
            # Save search history
            job_sites = [site.value for site in request.job_sites]
            db.save_search_history(
                keywords=request.keywords,
                location=request.location,
                job_sites=job_sites,
                results_count=len(jobs),
                new_jobs_count=0  # Will update after deduplication
            )
            
            # Small delay between searches
            if i < len(search_requests):
                await asyncio.sleep(3)
                
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            continue
    
    # ── Run additional scrapers (HN, Wellfound, Climatebase) ────────────────
    extra_sources = []

    if HAS_HN_SCRAPER:
        try:
            logger.info("\n🟠 Scraping Hacker News 'Who is Hiring'...")
            hn_jobs = scrape_hn_jobs(months_back=2, min_description_length=80)
            all_jobs.extend(hn_jobs)
            extra_sources.append(f"HN: {len(hn_jobs)}")
            logger.info(f"✅ HN scraper returned {len(hn_jobs)} jobs")
        except Exception as e:
            logger.warning(f"⚠️ HN scraper failed (non-fatal): {e}")

    if HAS_WELLFOUND_SCRAPER:
        try:
            logger.info("\n🟣 Scraping Wellfound (AngelList)...")
            wf_jobs = scrape_wellfound_jobs(max_pages_per_role=2)
            all_jobs.extend(wf_jobs)
            extra_sources.append(f"Wellfound: {len(wf_jobs)}")
            logger.info(f"✅ Wellfound scraper returned {len(wf_jobs)} jobs")
        except Exception as e:
            logger.warning(f"⚠️ Wellfound scraper failed (non-fatal): {e}")

    if HAS_CLIMATEBASE_SCRAPER:
        try:
            logger.info("\n🟢 Scraping Climatebase...")
            cb_jobs = scrape_climatebase_jobs(max_pages_per_query=2)
            all_jobs.extend(cb_jobs)
            extra_sources.append(f"Climatebase: {len(cb_jobs)}")
            logger.info(f"✅ Climatebase scraper returned {len(cb_jobs)} jobs")
        except Exception as e:
            logger.warning(f"⚠️ Climatebase scraper failed (non-fatal): {e}")

    if HAS_GREENHOUSE_SCRAPER:
        try:
            logger.info("\n🌿 Scraping Greenhouse job boards...")
            gh_jobs = scrape_greenhouse_jobs()
            all_jobs.extend(gh_jobs)
            extra_sources.append(f"Greenhouse: {len(gh_jobs)}")
            logger.info(f"✅ Greenhouse scraper returned {len(gh_jobs)} jobs")
        except Exception as e:
            logger.warning(f"⚠️ Greenhouse scraper failed (non-fatal): {e}")

    if HAS_ASHBY_SCRAPER:
        try:
            logger.info("\n🔷 Scraping Ashby job boards...")
            ab_jobs = scrape_ashby_jobs()
            all_jobs.extend(ab_jobs)
            extra_sources.append(f"Ashby: {len(ab_jobs)}")
            logger.info(f"✅ Ashby scraper returned {len(ab_jobs)} jobs")
        except Exception as e:
            logger.warning(f"⚠️ Ashby scraper failed (non-fatal): {e}")

    if HAS_LEVELSFYI_SCRAPER:
        try:
            logger.info("\n📊 Scraping Levels.fyi verified jobs...")
            lf_jobs = scrape_levelsfyi_jobs(max_pages=3)
            all_jobs.extend(lf_jobs)
            extra_sources.append(f"Levels.fyi: {len(lf_jobs)}")
            logger.info(f"✅ Levels.fyi scraper returned {len(lf_jobs)} jobs")
        except Exception as e:
            logger.warning(f"⚠️ Levels.fyi scraper failed (non-fatal): {e}")

    if HAS_OTTA_SCRAPER:
        try:
            logger.info("\n🟡 Scraping Otta / Welcome to the Jungle...")
            otta_jobs = scrape_otta_jobs(max_pages_per_query=2)
            all_jobs.extend(otta_jobs)
            extra_sources.append(f"Otta: {len(otta_jobs)}")
            logger.info(f"✅ Otta scraper returned {len(otta_jobs)} jobs")
        except Exception as e:
            logger.warning(f"⚠️ Otta scraper failed (non-fatal): {e}")

    # ClimateTechList disabled — site renders jobs client-side only (no SSR data, no API).
    # Would need headless browser. Greenhouse + Ashby cover the same companies better.
    # if HAS_CLIMATETECHLIST_SCRAPER:
    #     try:
    #         logger.info("\n🌍 Scraping ClimateTechList...")
    #         ctl_jobs = scrape_climatetechlist_jobs()
    #         all_jobs.extend(ctl_jobs)
    #         extra_sources.append(f"ClimateTechList: {len(ctl_jobs)}")
    #         logger.info(f"✅ ClimateTechList scraper returned {len(ctl_jobs)} jobs")
    #     except Exception as e:
    #         logger.warning(f"⚠️ ClimateTechList scraper failed (non-fatal): {e}")

    if extra_sources:
        logger.info(f"\n📦 Extra sources: {', '.join(extra_sources)}")

    # Remove duplicates by job_url
    unique_jobs = {job.job_url: job for job in all_jobs if job.job_url}.values()
    unique_jobs = list(unique_jobs)

    # Filter out ignored companies (Amazon, AWS, etc.) using centralized config
    if IGNORED_COMPANIES or is_ignored_company:
        before_count = len(unique_jobs)
        filtered_unique: List[JobListing] = []
        for job in unique_jobs:
            company = (job.company or "").strip()
            company_lower = company.lower()
            ignored = False
            try:
                if callable(is_ignored_company) and is_ignored_company(company):
                    ignored = True
                elif IGNORED_COMPANIES:
                    ignored = any(
                        ignore.lower() in company_lower for ignore in IGNORED_COMPANIES
                    )
            except Exception as e:
                logger.warning(f"Company filtering error for '{company}': {e}")
            if not ignored:
                filtered_unique.append(job)
        removed = before_count - len(filtered_unique)
        unique_jobs = filtered_unique
        if removed > 0:
            logger.info(
                "Filtered out %d jobs from ignored companies (e.g., Amazon/AWS)",
                removed,
            )
    
    logger.info(f"\n📊 SUMMARY: Found {len(unique_jobs)} unique job opportunities")
    
    # Apply salary filtering - only show jobs with salary >= $100K or no salary info
    MIN_SALARY = 100000  # $100K minimum

    # Override salary threshold from centralized job config when available
    if job_config is not None:
        try:
            min_salary_cfg = getattr(job_config, "MIN_SALARY", {})
            cfg_min = int(
                min_salary_cfg.get("senior")
                or min_salary_cfg.get("default")
                or MIN_SALARY
            )
            MIN_SALARY = cfg_min
        except Exception as config_error:
            logger.warning(
                f"Failed to derive MIN_SALARY from job_search_config: {config_error}"
            )
    
    filtered_jobs = []
    filtered_out_count = 0
    
    for job in unique_jobs:
        # Keep jobs with no salary info (they might be high-paying)
        if not job.salary_min and not job.salary_max:
            filtered_jobs.append(job)
        # Keep jobs where minimum salary >= $100K
        elif job.salary_min and job.salary_min >= MIN_SALARY:
            filtered_jobs.append(job)
        # Keep jobs where max salary >= $100K (even if min is lower)
        elif job.salary_max and job.salary_max >= MIN_SALARY:
            filtered_jobs.append(job)
        else:
            filtered_out_count += 1
    
    if filtered_out_count > 0:
        logger.info(f"🔍 Filtered out {filtered_out_count} jobs below ${MIN_SALARY:,} salary threshold")
    
    logger.info(f"✅ {len(filtered_jobs)} jobs meet salary requirements (${MIN_SALARY:,}+)")
    
    # Sort by posted date (most recent first)
    filtered_jobs.sort(key=lambda j: j.posted_date or datetime.min, reverse=True)
    
    # Use filtered jobs for the rest of the process
    unique_jobs = filtered_jobs
    
    # Save all jobs to database
    logger.info(f"\n💾 Saving {len(unique_jobs)} jobs to database...")
    new_jobs_count = 0
    
    for job in unique_jobs:
        try:
            job_data = job.to_dict()
            job_id = db.save_job(job_data)
            if job_id:
                new_jobs_count += 1
        except Exception as e:
            logger.warning(f"Failed to save job to database: {e}")
    
    logger.info(f"✅ Saved to database (check for new vs updated jobs)")
    
    # Display top opportunities
    logger.info("\n" + "=" * 80)
    logger.info("🏆 TOP JOB OPPORTUNITIES")
    logger.info("=" * 80)
    
    for i, job in enumerate(unique_jobs[:15], 1):
        logger.info(f"\n{i}. {job.title}")
        logger.info(f"   🏢 Company: {job.company}")
        logger.info(f"   📍 Location: {job.location}")
        logger.info(f"   💰 Salary: {job.get_salary_range_string()}")
        logger.info(f"   📅 Posted: {job.posted_date.strftime('%B %d, %Y') if job.posted_date else 'Recently'}")
        logger.info(f"   🌐 Source: {job.source_site.value}")
        logger.info(f"   🔗 Apply: {job.job_url}")
        
        if job.clearance_required:
            logger.info(f"   🔒 Clearance: {job.clearance_required}")
        if job.remote_type:
            logger.info(f"   🏠 Remote: {job.remote_type.value}")
    
    # Save to JSON file
    output_dir = Path(parent_dir) / "data" / "opportunities"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"jobs_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    
    jobs_data = [job.to_dict() for job in unique_jobs]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Saved {len(unique_jobs)} jobs to: {output_file}")
    
    # Generate summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("📈 STATISTICS")
    logger.info("=" * 80)
    
    stats = _generate_statistics(unique_jobs)
    
    logger.info(f"Total Jobs: {stats['total']}")
    logger.info(f"With Salary Info: {stats['with_salary']}")
    logger.info(f"Remote Jobs: {stats['remote']}")
    logger.info(f"Clearance Required: {stats['clearance']}")
    
    logger.info("\nBy Source:")
    for source, count in stats['by_source'].items():
        logger.info(f"  {source}: {count}")
    
    logger.info("\nBy Location (Top 5):")
    for location, count in list(stats['by_location'].items())[:5]:
        logger.info(f"  {location}: {count}")
    
    # Get database statistics
    logger.info("\n" + "=" * 80)
    logger.info("💾 DATABASE STATISTICS")
    logger.info("=" * 80)
    
    db_stats = db.get_statistics()
    logger.info(f"Total Jobs in Database: {db_stats['total_jobs']}")
    logger.info(f"Jobs with Salary Info: {db_stats['with_salary']}")
    
    if db_stats['avg_salary_min']:
        logger.info(f"Average Salary: ${db_stats['avg_salary_min']:,.0f} - ${db_stats['avg_salary_max']:,.0f}")
    
    logger.info("\nJobs by Source:")
    for source, count in db_stats['by_source'].items():
        logger.info(f"  {source}: {count}")
    
    if db_stats['total_applications'] > 0:
        logger.info(f"\nTotal Applications Tracked: {db_stats['total_applications']}")
        logger.info("Applications by Status:")
        for status, count in db_stats['applications_by_status'].items():
            logger.info(f"  {status}: {count}")

    # ── Telegram notification ──────────────────────────────────────
    duration_so_far = (datetime.now() - start_time).total_seconds()
    now_str = datetime.now().strftime("%b %d, %Y %I:%M %p")
    tg_lines = [
        f"<b>JobSpy Opportunity Detection — {now_str}</b>",
        "",
        f"<b>{len(unique_jobs)}</b> total jobs found ({new_jobs_count} new to DB)",
        f"Ran {len(search_requests)} searches in {duration_so_far:.0f}s",
        "",
    ]

    # Jobs by source
    if stats['by_source']:
        source_parts = ", ".join(f"{src}: {cnt}" for src, cnt in stats['by_source'].items())
        tg_lines.append(f"<b>By source:</b> {source_parts}")

    # Extra scraper sources
    if extra_sources:
        tg_lines.append(f"<b>Extra sources:</b> {', '.join(extra_sources)}")

    # Salary stats
    if stats['with_salary'] > 0:
        salary_jobs = [j for j in unique_jobs if j.salary_min or j.salary_max]
        salary_mins = [j.salary_min for j in salary_jobs if j.salary_min]
        salary_maxs = [j.salary_max for j in salary_jobs if j.salary_max]
        avg_min = sum(salary_mins) / len(salary_mins) if salary_mins else 0
        avg_max = sum(salary_maxs) / len(salary_maxs) if salary_maxs else 0
        tg_lines.append(f"<b>Salary info:</b> {stats['with_salary']} jobs, avg ${avg_min:,.0f}–${avg_max:,.0f}")

    # Remote count
    if stats['remote'] > 0:
        tg_lines.append(f"<b>Remote:</b> {stats['remote']} jobs")

    if filtered_out_count > 0:
        tg_lines.append(f"Filtered out {filtered_out_count} below ${MIN_SALARY:,}")

    tg_lines.append(f"\n<a href='http://localhost:8888'>Open Dashboard</a>")

    send_telegram_report("\n".join(tg_lines))

    # Cleanup
    await scraper.cleanup()
    
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n✅ Opportunity detection completed in {duration:.1f} seconds")
    logger.info("=" * 80)


def _generate_statistics(jobs: List[JobListing]) -> Dict[str, Any]:
    """Generate statistics from job listings"""
    stats = {
        'total': len(jobs),
        'with_salary': sum(1 for j in jobs if j.salary_min or j.salary_max),
        'remote': sum(1 for j in jobs if j.remote_type == RemoteType.REMOTE),
        'clearance': sum(1 for j in jobs if j.clearance_required),
        'by_source': {},
        'by_location': {}
    }
    
    # Count by source
    for job in jobs:
        source = job.source_site.value
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
    
    # Count by location
    for job in jobs:
        location = job.location
        stats['by_location'][location] = stats['by_location'].get(location, 0) + 1
    
    # Sort locations by count
    stats['by_location'] = dict(sorted(stats['by_location'].items(), key=lambda x: x[1], reverse=True))
    
    return stats


if __name__ == "__main__":
    try:
        asyncio.run(run_jobspy_opportunity_detection())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
