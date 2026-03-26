"""
Wellfound (AngelList) Job Scraper

Scrapes startup job postings from Wellfound.com by parsing the
embedded Next.js __NEXT_DATA__ JSON payload from role search pages.

Wellfound uses DataDome anti-bot protection. This scraper:
  1. Tries proxy_manager if a proxy is configured (residential/ScrapFly)
  2. Falls back to curl_cffi TLS impersonation
  3. Degrades gracefully (returns empty list) if blocked

URL patterns:
  - Role search:  wellfound.com/role/<role-slug>
  - Remote roles: wellfound.com/role/r/<role-slug>
  - With location: wellfound.com/role/l/<role-slug>/<location-slug>
  - Pagination:   ?page=<number>
"""

import json
import re
import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import JobListing, JobSite, RemoteType

logger = logging.getLogger(__name__)

# Proxy manager for anti-bot bypass
try:
    from .proxy_manager import fetch_with_proxy, is_proxy_available
    HAS_PROXY = True
except ImportError:
    HAS_PROXY = False
    def is_proxy_available() -> bool: return False  # type: ignore[misc]

# Prefer curl_cffi for TLS impersonation (critical for DataDome bypass)
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

WELLFOUND_BASE = "https://wellfound.com"

# Default role slugs for tech job searches
DEFAULT_ROLE_SLUGS = [
    "python-developer",
    "software-engineer",
    "machine-learning-engineer",
    "data-scientist",
    "backend-engineer",
]


# ── Page Fetching ────────────────────────────────────────────────────────────

def _fetch_page(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch a Wellfound page, trying proxy first then direct."""
    # Strategy 1: Use proxy manager if configured (best for DataDome)
    if HAS_PROXY and is_proxy_available():
        logger.debug(f"Wellfound: trying proxy for {url}")
        result = fetch_with_proxy(url, timeout=timeout)
        if result and "__NEXT_DATA__" in result:
            return result
        elif result:
            logger.debug("Proxy returned content but no __NEXT_DATA__ — may be challenge page")

    # Strategy 2: Direct with TLS impersonation
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    try:
        kwargs: Dict[str, Any] = {"timeout": timeout, "headers": headers}
        if _IMPERSONATE:
            kwargs["impersonate"] = _IMPERSONATE

        resp = http_client.get(url, **kwargs)
        if resp.status_code == 403:
            logger.warning(f"Wellfound returned 403 (DataDome block) for {url}")
            return None
        if resp.status_code != 200:
            logger.debug(f"Wellfound returned {resp.status_code} for {url}")
            return None
        return resp.text
    except Exception as e:
        logger.warning(f"Wellfound fetch failed for {url}: {e}")
        return None


# ── __NEXT_DATA__ Parsing ────────────────────────────────────────────────────

def _extract_next_data(html: str) -> Optional[Dict[str, Any]]:
    """Extract the __NEXT_DATA__ JSON payload from page HTML."""
    if HAS_BS4:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                return json.loads(script.string)
            except json.JSONDecodeError:
                pass

    # Fallback: regex extraction
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


def _extract_jobs_from_next_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract job listings from the __NEXT_DATA__ Apollo state.

    Wellfound Apollo state structure:
      - StartupResult entities have name, slug, highlightedJobListings (refs)
      - JobListingSearchResult entities have title, description, compensation, etc.
      - The link is startup -> jobs (reverse), so we build a lookup.
    """
    # Navigate to Apollo state
    try:
        apollo_state = data["props"]["pageProps"]["apolloState"]["data"]
    except (KeyError, TypeError):
        try:
            apollo_state = data["props"]["pageProps"]
        except (KeyError, TypeError):
            logger.debug("Could not find Apollo state in __NEXT_DATA__")
            return []

    # Pass 1: Index startups and build job_id -> startup reverse lookup
    startups: Dict[str, Dict] = {}
    job_to_startup: Dict[str, Dict] = {}

    for key, value in apollo_state.items():
        if not isinstance(value, dict):
            continue
        if value.get("__typename") == "StartupResult":
            startups[key] = value
            # Map each highlighted job to this startup
            for ref in value.get("highlightedJobListings", []):
                if isinstance(ref, dict) and "__ref" in ref:
                    job_to_startup[ref["__ref"]] = value

    # Pass 2: Extract job listings, enriched with startup data
    jobs = []
    for key, value in apollo_state.items():
        if not isinstance(value, dict):
            continue

        typename = value.get("__typename", "")
        if typename in ("JobListing", "StartupJobPosting", "JobListingSearchResult"):
            # Enrich with startup/company info from reverse lookup
            startup = job_to_startup.get(key, {})
            if startup:
                value["_startup_name"] = startup.get("name", "")
                value["_startup_slug"] = startup.get("slug", "")
                value["_startup_logo"] = startup.get("logoUrl", "")
                value["_startup_size"] = startup.get("companySize", "")
                value["_startup_desc"] = startup.get("highConcept", "")
            jobs.append(value)
        elif all(f in value for f in ("title", "slug")) and "compensation" in str(value).lower():
            startup = job_to_startup.get(key, {})
            if startup:
                value["_startup_name"] = startup.get("name", "")
                value["_startup_slug"] = startup.get("slug", "")
            jobs.append(value)

    logger.debug(f"Apollo state: {len(startups)} startups, {len(jobs)} jobs, {len(job_to_startup)} linked")
    return jobs


def _resolve_ref(apollo_state: Dict, ref: Any) -> Any:
    """Resolve an Apollo state reference to its actual value."""
    if isinstance(ref, dict) and "__ref" in ref:
        return apollo_state.get(ref["__ref"], ref)
    return ref


# ── Job Parsing ──────────────────────────────────────────────────────────────

def _parse_remote_type(job_data: Dict) -> Optional[RemoteType]:
    """Detect remote type from Wellfound job data."""
    remote = job_data.get("remote", False)
    if isinstance(remote, bool) and remote:
        return RemoteType.REMOTE
    remote_str = str(remote).lower() if remote else ""
    if "remote" in remote_str:
        return RemoteType.REMOTE
    if "hybrid" in remote_str:
        return RemoteType.HYBRID
    return None


def _parse_salary(job_data: Dict) -> tuple:
    """Extract salary range from Wellfound compensation data."""
    comp = job_data.get("compensation")
    if isinstance(comp, dict):
        s_min = comp.get("salary_min") or comp.get("min") or comp.get("salaryMin")
        s_max = comp.get("salary_max") or comp.get("max") or comp.get("salaryMax")
        try:
            s_min = float(s_min) if s_min else None
            s_max = float(s_max) if s_max else None
            return s_min, s_max
        except (ValueError, TypeError):
            pass

    # Try extracting from text
    comp_str = str(comp) if comp else ""
    match = re.search(r'\$(\d[\d,]*)\s*[-–—]\s*\$(\d[\d,]*)', comp_str)
    if match:
        try:
            low = float(match.group(1).replace(',', ''))
            high = float(match.group(2).replace(',', ''))
            return low, high
        except ValueError:
            pass

    return None, None


def _parse_wellfound_job(job_data: Dict, apollo_state: Dict = None) -> Optional[JobListing]:
    """Parse a Wellfound job entity into a JobListing."""
    title = job_data.get("title") or job_data.get("name", "")
    if not title:
        return None

    # Company name: prefer enriched _startup_name from reverse lookup
    company_name = job_data.get("_startup_name", "")
    company_slug = job_data.get("_startup_slug", "")
    company_url = f"{WELLFOUND_BASE}/company/{company_slug}" if company_slug else ""

    # Fallback: resolve direct startup/company reference
    if not company_name:
        company_ref = job_data.get("startup") or job_data.get("company") or {}
        if apollo_state and isinstance(company_ref, dict) and "__ref" in company_ref:
            company_ref = apollo_state.get(company_ref["__ref"], {})
        if isinstance(company_ref, dict):
            company_name = company_ref.get("name", "")
            ref_slug = company_ref.get("slug", "")
            if ref_slug and not company_url:
                company_url = f"{WELLFOUND_BASE}/company/{ref_slug}"
                company_slug = ref_slug

    if not company_name:
        company_name = str(job_data.get("companyName", "Unknown"))

    # Location
    locations = job_data.get("locationNames") or job_data.get("locations") or []
    if isinstance(locations, list):
        location = ", ".join(str(l) for l in locations[:3]) if locations else ""
    else:
        location = str(locations)

    # Description — build from available fields if short/missing
    description = job_data.get("description") or job_data.get("descriptionHtml") or ""
    if "<" in description:
        description = re.sub(r'<[^>]+>', ' ', description)
        description = re.sub(r'\s+', ' ', description).strip()

    # Enrich short descriptions with startup context
    startup_desc = job_data.get("_startup_desc", "")
    if len(description) < 30 and startup_desc:
        description = f"{startup_desc}. {description}".strip()

    if not description or len(description) < 20:
        return None

    # Salary — parse Wellfound's "$100K – $150K • 0.1% – 0.5%" format
    salary_min, salary_max = _parse_salary(job_data)

    # Remote type — also check remoteConfig
    remote_type = _parse_remote_type(job_data)
    if not remote_type:
        rc = job_data.get("remoteConfig", {})
        if isinstance(rc, dict):
            kind = rc.get("kind", "").upper()
            if kind == "REMOTE":
                remote_type = RemoteType.REMOTE
            elif kind == "HYBRID" or rc.get("wfhFlexible"):
                remote_type = RemoteType.HYBRID

    # URL
    slug = job_data.get("slug", "")
    job_id_val = job_data.get("id", "")
    if slug and company_slug:
        job_url = f"{WELLFOUND_BASE}/company/{company_slug}/jobs/{slug}"
    elif slug:
        job_url = f"{WELLFOUND_BASE}/jobs/{slug}"
    elif job_id_val:
        job_url = f"{WELLFOUND_BASE}/jobs/{job_id_val}"
    else:
        job_url = ""

    if not job_url:
        return None

    # Posted date
    posted_date = None
    live_start = job_data.get("liveStartAt") or job_data.get("createdAt") or job_data.get("postedAt")
    if live_start:
        try:
            if isinstance(live_start, (int, float)):
                posted_date = datetime.fromtimestamp(live_start / 1000 if live_start > 1e12 else live_start)
            else:
                posted_date = datetime.fromisoformat(str(live_start).replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, TypeError, OSError):
            pass

    return JobListing(
        title=title[:200],
        company=company_name[:100],
        location=location[:100] if location else "See posting",
        description=description[:5000],
        job_url=job_url,
        job_id=f"wf-{job_id_val}" if job_id_val else f"wf-{slug}",
        company_url=company_url,
        remote_type=remote_type,
        salary_min=salary_min,
        salary_max=salary_max,
        posted_date=posted_date,
        source_site=JobSite.WELLFOUND,
        raw_data={
            "source": "wellfound",
            "wellfound_id": str(job_id_val),
            "wellfound_slug": slug,
        },
    )


# ── Public API ───────────────────────────────────────────────────────────────

def scrape_wellfound_jobs(
    role_slugs: Optional[List[str]] = None,
    remote_only: bool = False,
    max_pages_per_role: int = 3,
    min_description_length: int = 50,
) -> List[JobListing]:
    """
    Scrape jobs from Wellfound role search pages.

    Args:
        role_slugs: Role slugs to search (e.g., ["python-developer", "data-scientist"]).
                    Defaults to DEFAULT_ROLE_SLUGS.
        remote_only: If True, only fetch remote role pages.
        max_pages_per_role: Max pagination depth per role.
        min_description_length: Minimum description length to keep.

    Returns:
        List of parsed JobListing objects. Empty list if DataDome blocks access.
    """
    if not role_slugs:
        role_slugs = DEFAULT_ROLE_SLUGS

    all_jobs: List[JobListing] = []
    seen_urls: set = set()

    for role_slug in role_slugs:
        for page in range(1, max_pages_per_role + 1):
            # Build URL
            if remote_only:
                url = f"{WELLFOUND_BASE}/role/r/{role_slug}"
            else:
                url = f"{WELLFOUND_BASE}/role/{role_slug}"
            if page > 1:
                url += f"?page={page}"

            logger.info(f"Fetching Wellfound: {url}")

            html = _fetch_page(url)
            if not html:
                logger.warning(f"Wellfound blocked or empty for {role_slug} page {page}")
                break  # DataDome likely blocked — stop this role

            next_data = _extract_next_data(html)
            if not next_data:
                logger.debug(f"No __NEXT_DATA__ found on {url}")
                break

            # Get apollo state for reference resolution
            try:
                apollo_state = next_data["props"]["pageProps"]["apolloState"]["data"]
            except (KeyError, TypeError):
                apollo_state = {}

            raw_jobs = _extract_jobs_from_next_data(next_data)
            if not raw_jobs:
                logger.debug(f"No jobs extracted from {url}")
                break

            page_count = 0
            for raw_job in raw_jobs:
                try:
                    job = _parse_wellfound_job(raw_job, apollo_state)
                    if job and job.job_url not in seen_urls:
                        if len(job.description) >= min_description_length:
                            all_jobs.append(job)
                            seen_urls.add(job.job_url)
                            page_count += 1
                except Exception as e:
                    logger.debug(f"Failed to parse Wellfound job: {e}")

            logger.info(f"Parsed {page_count} jobs from Wellfound {role_slug} page {page}")

            if page_count == 0:
                break  # No more results

            # Rate limit between pages
            time.sleep(random.uniform(2.0, 4.0))

        # Rate limit between roles
        time.sleep(random.uniform(1.0, 3.0))

    logger.info(f"Wellfound scraper: {len(all_jobs)} total jobs scraped")
    return all_jobs


if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    logging.basicConfig(level=logging.INFO)
    jobs = scrape_wellfound_jobs(role_slugs=["python-developer"], max_pages_per_role=1)
    print(f"\nFound {len(jobs)} jobs\n")
    for i, job in enumerate(jobs[:10], 1):
        salary = job.get_salary_range_string()
        remote = f" [{job.remote_type.value}]" if job.remote_type else ""
        print(f"{i}. {job.title}")
        print(f"   Company: {job.company} | {job.location}{remote}")
        print(f"   Salary: {salary}")
        print(f"   URL: {job.job_url}")
        print()
