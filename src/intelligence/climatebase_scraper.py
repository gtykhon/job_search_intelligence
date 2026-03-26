"""
Climatebase Job Scraper

Scrapes climate/sustainability job postings from climatebase.org.
The site is a Next.js app backed by Algolia search, with job data
embedded in the __NEXT_DATA__ JSON payload on listing pages.

IMPORTANT: The main domain (climatebase.org/jobs) serves data.
The subdomain (jobs.climatebase.org) returns 403 — do NOT use it.

URL patterns:
  - Listings: climatebase.org/jobs?l=&q=<query>&p=<page>
  - Detail:   climatebase.org/job/<id>/<slug>

Data fields per job (from __NEXT_DATA__):
  id, title, featured, salary_from, salary_to, salary_period,
  activation_date, employer_id, logo, locations[], name_of_employer,
  employer_short_description, sectors[], remote_preferences[],
  job_types[], objectID
"""

import json
import re
import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from .models import JobListing, JobSite, RemoteType

logger = logging.getLogger(__name__)

# Prefer curl_cffi for TLS impersonation
try:
    from curl_cffi import requests as http_client
    _IMPERSONATE = "chrome124"
except ImportError:
    import requests as http_client  # type: ignore[no-redef]
    _IMPERSONATE = None

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# Main domain — NOT jobs.climatebase.org (returns 403)
CLIMATEBASE_BASE = "https://climatebase.org"

# Default search queries for climate + tech intersection
DEFAULT_QUERIES = [
    "python",
    "software engineer",
    "data scientist",
    "machine learning",
    "backend",
]


# ── Page Fetching ────────────────────────────────────────────────────────────

def _fetch_page(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch a Climatebase page with TLS impersonation."""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    try:
        kwargs: Dict[str, Any] = {"timeout": timeout, "headers": headers}
        if _IMPERSONATE:
            kwargs["impersonate"] = _IMPERSONATE

        resp = http_client.get(url, **kwargs)
        if resp.status_code == 403:
            logger.warning(f"Climatebase returned 403 (blocked) for {url}")
            return None
        if resp.status_code != 200:
            logger.debug(f"Climatebase returned {resp.status_code} for {url}")
            return None
        return resp.text
    except Exception as e:
        logger.warning(f"Climatebase fetch failed for {url}: {e}")
        return None


# ── Data Extraction ──────────────────────────────────────────────────────────

def _extract_next_data(html: str) -> Optional[Dict[str, Any]]:
    """Extract __NEXT_DATA__ JSON from page HTML."""
    if HAS_BS4:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                return json.loads(script.string)
            except json.JSONDecodeError:
                pass

    # Regex fallback
    match = re.search(
        r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None


def _extract_jobs_from_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract job listings from __NEXT_DATA__ payload.

    Climatebase embeds jobs at props.pageProps.jobs as a flat array.
    Each object has: id, title, salary_from, salary_to, name_of_employer,
    locations[], remote_preferences[], sectors[], job_types[], objectID, etc.
    """
    jobs = []
    page_props = data.get("props", {}).get("pageProps", {})

    # Primary path: props.pageProps.jobs
    if "jobs" in page_props:
        raw_jobs = page_props["jobs"]
        if isinstance(raw_jobs, list):
            jobs.extend(raw_jobs)
        elif isinstance(raw_jobs, dict) and "data" in raw_jobs:
            jobs.extend(raw_jobs["data"])

    # Alternative: dehydrated React Query state
    if not jobs and "dehydratedState" in page_props:
        queries = page_props["dehydratedState"].get("queries", [])
        for query in queries:
            state = query.get("state", {})
            query_data = state.get("data", {})
            if isinstance(query_data, dict):
                for key in ("pages", "data", "jobs", "hits", "items"):
                    items = query_data.get(key)
                    if isinstance(items, list):
                        # Could be paginated (list of pages) or flat
                        for item in items:
                            if isinstance(item, dict) and "title" in item:
                                jobs.append(item)
                            elif isinstance(item, list):
                                jobs.extend(item)
            elif isinstance(query_data, list):
                jobs.extend(query_data)

    # Fallback: walk structure for job-like objects
    if not jobs:
        jobs = _find_job_objects(page_props)

    return jobs


def _find_job_objects(obj: Any, depth: int = 0) -> List[Dict[str, Any]]:
    """Recursively find objects that look like job listings."""
    if depth > 6:
        return []
    jobs = []
    if isinstance(obj, dict):
        # Climatebase uses name_of_employer instead of employer/company
        if "title" in obj and ("name_of_employer" in obj or "employer" in obj or "company" in obj):
            jobs.append(obj)
        else:
            for value in obj.values():
                jobs.extend(_find_job_objects(value, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            jobs.extend(_find_job_objects(item, depth + 1))
    return jobs


# ── Job Parsing ──────────────────────────────────────────────────────────────

def _parse_remote_type(job_data: Dict) -> Optional[RemoteType]:
    """Detect remote type from Climatebase remote_preferences array."""
    # Climatebase uses remote_preferences: ["Remote"], ["Hybrid"], ["In-person"]
    prefs = job_data.get("remote_preferences") or job_data.get("remotePreferences") or []
    if isinstance(prefs, list):
        prefs_lower = " ".join(str(p).lower() for p in prefs)
    elif isinstance(prefs, str):
        prefs_lower = prefs.lower()
    else:
        prefs_lower = ""

    if "remote" in prefs_lower and "hybrid" in prefs_lower:
        return RemoteType.HYBRID
    if "remote" in prefs_lower:
        return RemoteType.REMOTE
    if "in-person" in prefs_lower or "on-site" in prefs_lower or "onsite" in prefs_lower:
        return RemoteType.ON_SITE
    return None


def _parse_salary(job_data: Dict) -> tuple:
    """Extract salary from Climatebase salary_from / salary_to fields."""
    # Climatebase uses salary_from / salary_to directly
    s_min = job_data.get("salary_from") or job_data.get("salaryMin") or job_data.get("salary_min")
    s_max = job_data.get("salary_to") or job_data.get("salaryMax") or job_data.get("salary_max")
    try:
        s_min = float(s_min) if s_min else None
        s_max = float(s_max) if s_max else None
        if s_min or s_max:
            return s_min, s_max
    except (ValueError, TypeError):
        pass
    return None, None


def _slugify(text: str) -> str:
    """Convert a title to a URL slug."""
    slug = text.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:80]


def _parse_climatebase_job(job_data: Dict) -> Optional[JobListing]:
    """Parse a Climatebase job object into a JobListing."""
    title = job_data.get("title") or ""
    if not title:
        return None

    # Company: Climatebase uses name_of_employer
    company = (
        job_data.get("name_of_employer")
        or job_data.get("employer_name")
        or job_data.get("company")
        or ""
    )
    # Fallback: employer dict
    if not company:
        employer = job_data.get("employer") or {}
        if isinstance(employer, dict):
            company = employer.get("name", "")
        elif isinstance(employer, str):
            company = employer
    if not company:
        company = "Unknown"

    # Location: array of strings like ["Berlin, BE, DE"]
    locations = job_data.get("locations") or []
    if isinstance(locations, list):
        location_parts = []
        for loc in locations[:3]:
            if isinstance(loc, str):
                location_parts.append(loc)
            elif isinstance(loc, dict):
                location_parts.append(loc.get("name", "") or loc.get("city", ""))
        location = ", ".join(p for p in location_parts if p)
    elif isinstance(locations, str):
        location = locations
    else:
        location = ""

    # Description — listing pages don't include full description,
    # so use employer_short_description + sectors as a proxy
    description = job_data.get("description") or job_data.get("descriptionHtml") or ""
    if "<" in description:
        description = re.sub(r'<[^>]+>', ' ', description)
        description = re.sub(r'\s+', ' ', description).strip()

    # If no description, build one from available metadata
    if not description:
        parts = []
        emp_desc = job_data.get("employer_short_description") or ""
        if emp_desc:
            parts.append(f"Company: {emp_desc}")
        sectors = job_data.get("sectors") or []
        if sectors:
            parts.append(f"Sectors: {', '.join(str(s) for s in sectors)}")
        job_types = job_data.get("job_types") or []
        if job_types:
            parts.append(f"Type: {', '.join(str(t) for t in job_types)}")
        remote_prefs = job_data.get("remote_preferences") or []
        if remote_prefs:
            parts.append(f"Work: {', '.join(str(r) for r in remote_prefs)}")
        if location:
            parts.append(f"Location: {location}")
        description = " | ".join(parts) if parts else title

    # Job URL
    job_id_val = job_data.get("id") or job_data.get("objectID") or ""
    slug = _slugify(title)
    if job_id_val:
        job_url = f"{CLIMATEBASE_BASE}/job/{job_id_val}/{slug}"
    else:
        return None

    # Salary
    salary_min, salary_max = _parse_salary(job_data)

    # Remote type
    remote_type = _parse_remote_type(job_data)

    # Posted date — Climatebase uses activation_date
    posted_date = None
    for date_field in ("activation_date", "activationDate", "publishedAt", "createdAt"):
        raw_date = job_data.get(date_field)
        if raw_date:
            try:
                if isinstance(raw_date, (int, float)):
                    posted_date = datetime.fromtimestamp(
                        raw_date / 1000 if raw_date > 1e12 else raw_date
                    )
                else:
                    # Handle "2026-03-15" or "2026-03-15T00:00:00Z"
                    date_str = str(raw_date).replace("Z", "+00:00")
                    if len(date_str) == 10:  # "YYYY-MM-DD"
                        posted_date = datetime.strptime(date_str, "%Y-%m-%d")
                    else:
                        posted_date = datetime.fromisoformat(date_str).replace(tzinfo=None)
                break
            except (ValueError, TypeError, OSError):
                continue

    # Sectors
    sectors = job_data.get("sectors") or []
    if isinstance(sectors, list):
        sector_str = ", ".join(str(s) for s in sectors[:5] if s)
    else:
        sector_str = ""

    return JobListing(
        title=title[:200],
        company=company[:100],
        location=location[:100] if location else "See posting",
        description=description[:5000],
        job_url=job_url,
        job_id=f"cb-{job_id_val}",
        remote_type=remote_type,
        salary_min=salary_min,
        salary_max=salary_max,
        posted_date=posted_date,
        source_site=JobSite.CLIMATEBASE,
        raw_data={
            "source": "climatebase",
            "climatebase_id": str(job_id_val),
            "sectors": sector_str,
            "employer_desc": (job_data.get("employer_short_description") or "")[:200],
        },
    )


# ── Public API ───────────────────────────────────────────────────────────────

def scrape_climatebase_jobs(
    queries: Optional[List[str]] = None,
    max_pages_per_query: int = 3,
    min_description_length: int = 20,
    keyword_filter: Optional[List[str]] = None,
) -> List[JobListing]:
    """
    Scrape jobs from Climatebase job board.

    NOTE: Climatebase search/pagination is client-side only. The server
    always returns the same ~100 most recent jobs regardless of query or
    page parameters. We fetch once and optionally filter by keywords locally.

    Args:
        queries: Ignored (kept for API compat). Filtering is done locally.
        max_pages_per_query: Ignored (server returns same data for all pages).
        min_description_length: Minimum description length to keep.
        keyword_filter: Optional list of keywords to filter jobs locally.
                        If provided, only jobs with any keyword in title/sectors
                        are returned. If None, all jobs are returned.

    Returns:
        List of parsed JobListing objects. Empty list if site blocks access.
    """
    url = f"{CLIMATEBASE_BASE}/jobs"
    logger.info(f"Fetching Climatebase: {url}")

    html = _fetch_page(url)
    if not html:
        logger.warning("Climatebase blocked or empty")
        return []

    next_data = _extract_next_data(html)
    if not next_data:
        logger.warning("No __NEXT_DATA__ found on Climatebase")
        return []

    raw_jobs = _extract_jobs_from_data(next_data)
    if not raw_jobs:
        logger.warning("No jobs extracted from Climatebase __NEXT_DATA__")
        return []

    logger.info(f"Found {len(raw_jobs)} raw jobs in Climatebase __NEXT_DATA__")

    all_jobs: List[JobListing] = []
    seen_ids: set = set()

    for raw_job in raw_jobs:
        try:
            job = _parse_climatebase_job(raw_job)
            if job and job.job_id not in seen_ids:
                if len(job.description) >= min_description_length:
                    # Optional keyword filter
                    if keyword_filter:
                        text = f"{job.title} {job.raw_data.get('sectors', '')}".lower()
                        if not any(kw.lower() in text for kw in keyword_filter):
                            continue
                    all_jobs.append(job)
                    seen_ids.add(job.job_id)
        except Exception as e:
            logger.debug(f"Failed to parse Climatebase job: {e}")

    logger.info(f"Climatebase scraper: {len(all_jobs)} jobs parsed (from {len(raw_jobs)} raw)")
    return all_jobs


if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    logging.basicConfig(level=logging.INFO)
    jobs = scrape_climatebase_jobs(queries=["python"], max_pages_per_query=1)
    print(f"\nFound {len(jobs)} jobs\n")
    for i, job in enumerate(jobs[:10], 1):
        salary = job.get_salary_range_string()
        remote = f" [{job.remote_type.value}]" if job.remote_type else ""
        sectors = job.raw_data.get("sectors", "")
        print(f"{i}. {job.title}")
        print(f"   Company: {job.company} | {job.location}{remote}")
        print(f"   Salary: {salary}")
        if sectors:
            print(f"   Sectors: {sectors}")
        print(f"   URL: {job.job_url}")
        print()
