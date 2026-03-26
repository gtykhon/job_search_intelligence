"""
ClimateTechList Job Scraper

Scrapes climate-tech job postings from climatetechlist.com.
The site is a Next.js application. We attempt multiple extraction strategies:

1. __NEXT_DATA__ JSON embedded in HTML (pageProps.jobs or similar)
2. Next.js internal data routes (/_next/data/{buildId}/jobs.json)
3. API endpoints (/api/jobs, etc.)
4. HTML parsing with BeautifulSoup as a last resort

URL patterns:
  - Listings: climatetechlist.com/jobs?search=<query>&remote=remote-only
  - Company:  climatetechlist.com/companies/<slug>
"""

import json
import re
import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs

from .models import JobListing, JobSite, RemoteType

logger = logging.getLogger(__name__)

# ── HTTP Client Setup ────────────────────────────────────────────────────────

try:
    from curl_cffi import requests as http_client
    _IMPERSONATE = "chrome124"
    _CLIENT = "curl_cffi"
except ImportError:
    try:
        import requests as http_client  # type: ignore[no-redef]
    except ImportError:
        http_client = None  # type: ignore[assignment]
    _IMPERSONATE = None
    _CLIENT = "requests"

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# ── Constants ─────────────────────────────────────────────────────────────────

CLIMATETECHLIST_BASE = "https://www.climatetechlist.com"

DEFAULT_QUERIES = [
    "Data",
    "Software Engineer",
    "Python",
    "Machine Learning",
    "Backend",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.climatetechlist.com/",
}

JSON_HEADERS = {
    **DEFAULT_HEADERS,
    "Accept": "application/json, text/plain, */*",
}


# ── Page Fetching ─────────────────────────────────────────────────────────────

def _fetch(url: str, timeout: int = 25, accept_json: bool = False) -> Optional[str]:
    """Fetch a URL with TLS impersonation. Returns response text or None."""
    if http_client is None:
        logger.error("No HTTP client available (install curl_cffi or requests)")
        return None

    headers = JSON_HEADERS if accept_json else DEFAULT_HEADERS
    try:
        kwargs: Dict[str, Any] = {"timeout": timeout, "headers": headers}
        if _IMPERSONATE:
            kwargs["impersonate"] = _IMPERSONATE

        resp = http_client.get(url, **kwargs)
        if resp.status_code == 403:
            logger.warning("ClimateTechList returned 403 (blocked) for %s", url)
            return None
        if resp.status_code == 404:
            logger.debug("ClimateTechList returned 404 for %s", url)
            return None
        if resp.status_code != 200:
            logger.debug("ClimateTechList returned %d for %s", resp.status_code, url)
            return None
        return resp.text
    except Exception as e:
        logger.warning("ClimateTechList fetch failed for %s: %s", url, e)
        return None


# ── __NEXT_DATA__ Extraction ──────────────────────────────────────────────────

def _extract_next_data(html: str) -> Optional[Dict[str, Any]]:
    """Extract __NEXT_DATA__ JSON from page HTML."""
    # Try BeautifulSoup first (more robust with malformed HTML)
    if HAS_BS4:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                return json.loads(script.string)
            except json.JSONDecodeError:
                logger.debug("Failed to parse __NEXT_DATA__ via BS4")

    # Regex fallback
    match = re.search(
        r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html, re.DOTALL,
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.debug("Failed to parse __NEXT_DATA__ via regex")

    return None


def _extract_build_id(data: Dict[str, Any]) -> Optional[str]:
    """Extract the Next.js buildId from __NEXT_DATA__."""
    return data.get("buildId")


# ── Strategy 1: Extract jobs from __NEXT_DATA__ ──────────────────────────────

def _extract_jobs_from_next_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Walk the __NEXT_DATA__ payload looking for job-like objects.

    ClimateTechList may structure data as:
      - props.pageProps.jobs (flat list)
      - props.pageProps.initialJobs
      - props.pageProps.data.jobs
      - props.pageProps.dehydratedState (React Query cache)
      - props.pageProps.companies (company-level with nested jobs)
    """
    page_props = data.get("props", {}).get("pageProps", {})
    jobs: List[Dict[str, Any]] = []

    # Direct job arrays
    for key in ("jobs", "initialJobs", "allJobs", "listings", "results"):
        candidate = page_props.get(key)
        if isinstance(candidate, list) and candidate:
            if _looks_like_job_list(candidate):
                logger.info("Found %d jobs at pageProps.%s", len(candidate), key)
                jobs.extend(candidate)
                return jobs

    # Nested under data/results
    for wrapper_key in ("data", "results", "jobsData"):
        wrapper = page_props.get(wrapper_key)
        if isinstance(wrapper, dict):
            for key in ("jobs", "items", "listings", "results", "nodes"):
                candidate = wrapper.get(key)
                if isinstance(candidate, list) and candidate:
                    if _looks_like_job_list(candidate):
                        logger.info("Found %d jobs at pageProps.%s.%s",
                                    len(candidate), wrapper_key, key)
                        jobs.extend(candidate)
                        return jobs

    # React Query dehydrated state
    if "dehydratedState" in page_props:
        dehydrated_jobs = _extract_from_dehydrated_state(page_props["dehydratedState"])
        if dehydrated_jobs:
            logger.info("Found %d jobs in dehydratedState", len(dehydrated_jobs))
            return dehydrated_jobs

    # Companies with nested job counts/listings
    companies = page_props.get("companies") or page_props.get("companiesWithJobs")
    if isinstance(companies, list):
        for company in companies:
            if isinstance(company, dict):
                company_jobs = company.get("jobs") or company.get("openings") or []
                if isinstance(company_jobs, list):
                    # Inject company info into each job
                    company_name = (company.get("name") or company.get("companyName")
                                    or company.get("company") or "")
                    company_slug = company.get("slug") or company.get("id") or ""
                    for job in company_jobs:
                        if isinstance(job, dict):
                            job.setdefault("company", company_name)
                            job.setdefault("companyName", company_name)
                            job.setdefault("companySlug", company_slug)
                            jobs.append(job)
        if jobs:
            logger.info("Found %d jobs nested under %d companies",
                        len(jobs), len(companies))
            return jobs

    # Deep recursive search as last resort
    found = _find_job_objects(page_props)
    if found:
        logger.info("Found %d job-like objects via recursive search", len(found))
    return found


def _looks_like_job_list(items: list) -> bool:
    """Check if a list looks like job listings (first item has title)."""
    if not items:
        return False
    first = items[0]
    if not isinstance(first, dict):
        return False
    return any(k in first for k in ("title", "jobTitle", "role", "position"))


def _extract_from_dehydrated_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract jobs from React Query dehydrated state."""
    jobs: List[Dict[str, Any]] = []
    queries = state.get("queries", [])
    for query in queries:
        query_data = query.get("state", {}).get("data", {})
        if isinstance(query_data, dict):
            for key in ("pages", "data", "jobs", "hits", "items", "results"):
                items = query_data.get(key)
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and _looks_like_job_entry(item):
                            jobs.append(item)
                        elif isinstance(item, list):
                            for sub in item:
                                if isinstance(sub, dict) and _looks_like_job_entry(sub):
                                    jobs.append(sub)
        elif isinstance(query_data, list):
            for item in query_data:
                if isinstance(item, dict) and _looks_like_job_entry(item):
                    jobs.append(item)
    return jobs


def _looks_like_job_entry(obj: Dict) -> bool:
    """Check if a dict looks like a job listing."""
    return any(k in obj for k in ("title", "jobTitle", "role", "position"))


def _find_job_objects(obj: Any, depth: int = 0) -> List[Dict[str, Any]]:
    """Recursively find objects that look like job listings."""
    if depth > 8:
        return []
    jobs: List[Dict[str, Any]] = []
    if isinstance(obj, dict):
        if _looks_like_job_entry(obj) and any(
            k in obj for k in ("company", "companyName", "employer", "organization",
                               "companySlug", "url", "link", "href")
        ):
            jobs.append(obj)
        else:
            for value in obj.values():
                jobs.extend(_find_job_objects(value, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            jobs.extend(_find_job_objects(item, depth + 1))
    return jobs


# ── Strategy 2: Next.js Data Routes ──────────────────────────────────────────

def _try_nextjs_data_routes(build_id: str, search: str = "") -> List[Dict[str, Any]]:
    """Try fetching data via Next.js internal data routes."""
    # Common patterns for Next.js data routes
    route_patterns = [
        f"/_next/data/{build_id}/jobs.json",
        f"/_next/data/{build_id}/jobs.json?search={quote_plus(search)}&remote=remote-only",
    ]

    for route in route_patterns:
        url = f"{CLIMATETECHLIST_BASE}{route}"
        logger.debug("Trying Next.js data route: %s", url)
        text = _fetch(url, accept_json=True)
        if not text:
            continue
        try:
            data = json.loads(text)
            page_props = data.get("pageProps", {})
            # Same extraction logic as __NEXT_DATA__ but one level up
            jobs = _extract_jobs_from_next_data({"props": {"pageProps": page_props}})
            if jobs:
                logger.info("Got %d jobs from Next.js data route %s", len(jobs), route)
                return jobs
        except json.JSONDecodeError:
            logger.debug("Invalid JSON from data route %s", route)

    return []


# ── Strategy 3: API Endpoints ────────────────────────────────────────────────

def _try_api_endpoints(search: str = "") -> List[Dict[str, Any]]:
    """Try common API endpoint patterns."""
    api_patterns = [
        f"/api/jobs?search={quote_plus(search)}&remote=remote-only",
        f"/api/jobs?q={quote_plus(search)}&remote=true",
        "/api/jobs",
        "/api/listings",
        f"/api/search?q={quote_plus(search)}",
    ]

    for route in api_patterns:
        url = f"{CLIMATETECHLIST_BASE}{route}"
        logger.debug("Trying API endpoint: %s", url)
        text = _fetch(url, accept_json=True)
        if not text:
            continue
        try:
            data = json.loads(text)
            jobs: List[Dict[str, Any]] = []

            if isinstance(data, list):
                jobs = [j for j in data if isinstance(j, dict) and _looks_like_job_entry(j)]
            elif isinstance(data, dict):
                for key in ("jobs", "data", "results", "items", "listings"):
                    candidate = data.get(key)
                    if isinstance(candidate, list):
                        jobs = [j for j in candidate if isinstance(j, dict)]
                        break
                if not jobs and _looks_like_job_entry(data):
                    jobs = [data]

            if jobs:
                logger.info("Got %d jobs from API endpoint %s", len(jobs), route)
                return jobs
        except json.JSONDecodeError:
            logger.debug("Invalid JSON from API %s", route)

    return []


# ── Strategy 4: HTML Parsing ─────────────────────────────────────────────────

def _parse_jobs_from_html(html: str) -> List[Dict[str, Any]]:
    """Parse job listings from rendered HTML as a last resort."""
    if not HAS_BS4:
        logger.warning("BeautifulSoup not available for HTML parsing fallback")
        return []

    soup = BeautifulSoup(html, "html.parser")
    jobs: List[Dict[str, Any]] = []

    # Look for common job card patterns
    # ClimateTechList likely uses cards/list items with links to job details
    selectors = [
        # Semantic selectors
        ('a[href*="/jobs/"]', 'a'),
        ('a[href*="/job/"]', 'a'),
        ('[data-testid*="job"]', None),
        # Structural selectors - job cards in a list
        ('li a[href*="job"]', 'a'),
        ('div[class*="job"] a', 'a'),
        ('tr a[href*="job"]', 'a'),
    ]

    job_links = []
    for selector, _tag in selectors:
        try:
            elements = soup.select(selector)
            if elements:
                job_links = elements
                logger.debug("Found %d elements with selector '%s'", len(elements), selector)
                break
        except Exception:
            continue

    if not job_links:
        # Broader search: find all links that might be job postings
        all_links = soup.find_all("a", href=True)
        job_links = [
            a for a in all_links
            if re.search(r'/jobs?/|/positions?/|/openings?/|/careers?/', a.get("href", ""))
            and a.get_text(strip=True)
        ]
        logger.debug("Found %d potential job links via broad search", len(job_links))

    seen_urls = set()
    for link in job_links:
        href = link.get("href", "")
        if not href or href in seen_urls:
            continue

        # Make URL absolute
        if href.startswith("/"):
            href = f"{CLIMATETECHLIST_BASE}{href}"
        elif not href.startswith("http"):
            continue

        seen_urls.add(href)

        # Extract text from the link and surrounding context
        text = link.get_text(separator=" ", strip=True)
        if not text or len(text) < 3:
            continue

        # Try to find the parent card/container for more info
        parent = link.find_parent(["li", "div", "tr", "article", "section"])
        parent_text = parent.get_text(separator="|", strip=True) if parent else text

        # Parse fields from the card text
        parts = [p.strip() for p in parent_text.split("|") if p.strip()]

        job_data: Dict[str, Any] = {
            "title": text,
            "url": href,
            "_source": "html",
        }

        # Try to extract company, location from sibling/child elements
        if parent:
            # Look for company name in specific elements
            for company_sel in ["[class*='company']", "[class*='org']", "span", "p"]:
                try:
                    company_el = parent.select_one(company_sel)
                    if company_el and company_el != link:
                        company_text = company_el.get_text(strip=True)
                        if company_text and company_text != text:
                            job_data["company"] = company_text
                            break
                except Exception:
                    continue

            # Location
            for loc_sel in ["[class*='location']", "[class*='loc']"]:
                try:
                    loc_el = parent.select_one(loc_sel)
                    if loc_el:
                        job_data["location"] = loc_el.get_text(strip=True)
                        break
                except Exception:
                    continue

            # Salary
            salary_match = re.search(
                r'\$[\d,]+(?:\s*[-–]\s*\$[\d,]+)?(?:\s*/\s*(?:yr|year|annually))?',
                parent_text,
            )
            if salary_match:
                job_data["salary_text"] = salary_match.group(0)

        # If we have at least a title and URL, keep it
        if job_data.get("title") and job_data.get("url"):
            jobs.append(job_data)

    logger.info("Parsed %d jobs from HTML", len(jobs))
    return jobs


# ── Job Parsing ───────────────────────────────────────────────────────────────

def _parse_remote_type(job_data: Dict) -> Optional[RemoteType]:
    """Detect remote type from job data."""
    # Check explicit remote fields
    for key in ("remote", "remoteType", "remote_type", "workType", "work_type",
                "locationType", "location_type"):
        val = job_data.get(key)
        if val is not None:
            val_str = str(val).lower()
            if val_str in ("true", "1", "remote", "remote-only", "fully_remote"):
                return RemoteType.REMOTE
            if "hybrid" in val_str:
                return RemoteType.HYBRID
            if val_str in ("false", "0", "onsite", "on-site", "in-person", "office"):
                return RemoteType.ON_SITE

    # Check location string for remote indicators
    location = str(job_data.get("location") or job_data.get("locationText") or "").lower()
    if "remote" in location:
        if "hybrid" in location:
            return RemoteType.HYBRID
        return RemoteType.REMOTE

    # Check tags/labels
    tags = job_data.get("tags") or job_data.get("labels") or []
    if isinstance(tags, list):
        tags_str = " ".join(str(t).lower() for t in tags)
        if "remote" in tags_str:
            return RemoteType.REMOTE

    return None


def _parse_salary(job_data: Dict) -> Tuple[Optional[float], Optional[float]]:
    """Extract salary range from job data."""
    # Direct numeric fields
    for min_key, max_key in [
        ("salaryMin", "salaryMax"),
        ("salary_min", "salary_max"),
        ("salaryFrom", "salaryTo"),
        ("salary_from", "salary_to"),
        ("minSalary", "maxSalary"),
        ("min_salary", "max_salary"),
        ("compensationMin", "compensationMax"),
    ]:
        s_min = job_data.get(min_key)
        s_max = job_data.get(max_key)
        if s_min is not None or s_max is not None:
            try:
                s_min = float(s_min) if s_min else None
                s_max = float(s_max) if s_max else None
                if s_min or s_max:
                    return s_min, s_max
            except (ValueError, TypeError):
                pass

    # Salary as a single string like "$120,000 - $150,000"
    salary_str = str(job_data.get("salary") or job_data.get("compensation")
                     or job_data.get("salary_text") or "")
    if salary_str:
        amounts = re.findall(r'\$?([\d,]+)', salary_str)
        if len(amounts) >= 2:
            try:
                return float(amounts[0].replace(",", "")), float(amounts[1].replace(",", ""))
            except ValueError:
                pass
        elif len(amounts) == 1:
            try:
                val = float(amounts[0].replace(",", ""))
                return val, None
            except ValueError:
                pass

    # Nested salary object
    salary_obj = job_data.get("salary") or job_data.get("compensation")
    if isinstance(salary_obj, dict):
        s_min = salary_obj.get("min") or salary_obj.get("from") or salary_obj.get("minimum")
        s_max = salary_obj.get("max") or salary_obj.get("to") or salary_obj.get("maximum")
        try:
            s_min = float(s_min) if s_min else None
            s_max = float(s_max) if s_max else None
            if s_min or s_max:
                return s_min, s_max
        except (ValueError, TypeError):
            pass

    return None, None


def _parse_posted_date(job_data: Dict) -> Optional[datetime]:
    """Extract posted date from various field formats."""
    for date_field in ("postedDate", "posted_date", "postedAt", "posted_at",
                       "publishedAt", "published_at", "createdAt", "created_at",
                       "date", "datePosted", "date_posted", "listDate",
                       "activationDate", "activation_date"):
        raw = job_data.get(date_field)
        if not raw:
            continue
        try:
            if isinstance(raw, (int, float)):
                # Epoch: seconds or milliseconds
                ts = raw / 1000 if raw > 1e12 else raw
                return datetime.fromtimestamp(ts)
            date_str = str(raw).strip()
            if not date_str:
                continue
            # ISO format
            date_str = date_str.replace("Z", "+00:00")
            if len(date_str) == 10:  # "YYYY-MM-DD"
                return datetime.strptime(date_str, "%Y-%m-%d")
            return datetime.fromisoformat(date_str).replace(tzinfo=None)
        except (ValueError, TypeError, OSError):
            continue
    return None


def _slugify(text: str) -> str:
    """Convert text to a URL slug."""
    slug = text.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:80]


def _build_job_url(job_data: Dict) -> Optional[str]:
    """Build the canonical job URL."""
    # Explicit URL field
    for key in ("url", "link", "href", "jobUrl", "job_url", "applyUrl", "apply_url"):
        val = job_data.get(key)
        if val and isinstance(val, str):
            if val.startswith("http"):
                return val
            if val.startswith("/"):
                return f"{CLIMATETECHLIST_BASE}{val}"

    # Build from slug/id
    slug = job_data.get("slug") or job_data.get("id") or ""
    if slug:
        return f"{CLIMATETECHLIST_BASE}/jobs/{slug}"

    # Build from title + company
    title = job_data.get("title") or job_data.get("jobTitle") or ""
    if title:
        return f"{CLIMATETECHLIST_BASE}/jobs/{_slugify(title)}"

    return None


def _parse_climatetechlist_job(job_data: Dict) -> Optional[JobListing]:
    """Parse a single job data dict into a JobListing."""
    # Title
    title = (job_data.get("title") or job_data.get("jobTitle")
             or job_data.get("role") or job_data.get("position") or "")
    if not title:
        return None

    # Company
    company = (job_data.get("company") or job_data.get("companyName")
               or job_data.get("company_name") or job_data.get("employer")
               or job_data.get("organization") or "")
    if isinstance(company, dict):
        company = company.get("name") or company.get("companyName") or ""
    if not company:
        company = "Unknown"

    # Location
    location_raw = (job_data.get("location") or job_data.get("locationText")
                    or job_data.get("location_text") or "")
    if isinstance(location_raw, list):
        location = ", ".join(str(loc) for loc in location_raw[:3] if loc)
    elif isinstance(location_raw, dict):
        location = location_raw.get("name") or location_raw.get("text") or ""
    else:
        location = str(location_raw) if location_raw else ""

    # Description
    description = (job_data.get("description") or job_data.get("summary")
                   or job_data.get("snippet") or job_data.get("excerpt") or "")
    if isinstance(description, str) and "<" in description:
        description = re.sub(r'<[^>]+>', ' ', description)
        description = re.sub(r'\s+', ' ', description).strip()
    if not description:
        # Build from available metadata
        parts = []
        if company and company != "Unknown":
            parts.append(f"Company: {company}")
        if location:
            parts.append(f"Location: {location}")
        dept = job_data.get("department") or job_data.get("team") or ""
        if dept:
            parts.append(f"Department: {dept}")
        description = " | ".join(parts) if parts else title

    # Job URL
    job_url = _build_job_url(job_data)
    if not job_url:
        return None

    # Job ID
    job_id_raw = (job_data.get("id") or job_data.get("jobId") or job_data.get("job_id")
                  or job_data.get("slug") or _slugify(title))
    job_id = f"ctl-{job_id_raw}"

    # Salary
    salary_min, salary_max = _parse_salary(job_data)

    # Remote type
    remote_type = _parse_remote_type(job_data)

    # Posted date
    posted_date = _parse_posted_date(job_data)

    # Company URL
    company_slug = job_data.get("companySlug") or job_data.get("company_slug") or ""
    company_url = None
    if company_slug:
        company_url = f"{CLIMATETECHLIST_BASE}/companies/{company_slug}"

    # Industry / category
    industry = ""
    for key in ("category", "industry", "sector", "department", "team"):
        val = job_data.get(key)
        if val:
            if isinstance(val, list):
                industry = ", ".join(str(v) for v in val[:5])
            else:
                industry = str(val)
            break

    return JobListing(
        title=title[:200],
        company=str(company)[:100],
        location=location[:100] if location else "See posting",
        description=description[:5000],
        job_url=job_url,
        job_id=job_id,
        remote_type=remote_type,
        salary_min=salary_min,
        salary_max=salary_max,
        posted_date=posted_date,
        source_site=JobSite.CLIMATETECHLIST,
        company_url=company_url,
        company_industry=industry if industry else None,
        raw_data={
            "source": "climatetechlist",
            "climatetechlist_id": str(job_id_raw),
            "_extraction_method": job_data.get("_source", "next_data"),
        },
    )


# ── Main Scraping Orchestrator ────────────────────────────────────────────────

def _fetch_and_extract(search: str, remote_only: bool = True) -> List[Dict[str, Any]]:
    """
    Orchestrate multi-strategy job extraction for a single search query.

    Strategy order:
      1. Fetch page HTML -> extract __NEXT_DATA__
      2. Try Next.js data routes using buildId
      3. Try API endpoints
      4. Fall back to HTML parsing
    """
    # Build search URL
    params = f"?search={quote_plus(search)}"
    if remote_only:
        params += "&remote=remote-only"
    page_url = f"{CLIMATETECHLIST_BASE}/jobs{params}"
    logger.info("Fetching ClimateTechList: %s", page_url)

    html = _fetch(page_url)
    if not html:
        logger.warning("ClimateTechList returned empty/blocked for %s", page_url)
        return []

    # ── Strategy 1: __NEXT_DATA__ ─────────────────────────────────────────
    next_data = _extract_next_data(html)
    build_id = None
    if next_data:
        build_id = _extract_build_id(next_data)
        logger.debug("Found __NEXT_DATA__ (buildId=%s)", build_id)

        jobs = _extract_jobs_from_next_data(next_data)
        if jobs:
            logger.info("Strategy 1 (__NEXT_DATA__): extracted %d jobs", len(jobs))
            return jobs

        # Log what we DID find for debugging
        page_props = next_data.get("props", {}).get("pageProps", {})
        top_keys = list(page_props.keys())[:20]
        logger.info("__NEXT_DATA__ pageProps keys (no jobs found): %s", top_keys)

    # ── Strategy 2: Next.js data routes ───────────────────────────────────
    if build_id:
        jobs = _try_nextjs_data_routes(build_id, search=search)
        if jobs:
            logger.info("Strategy 2 (Next.js data routes): extracted %d jobs", len(jobs))
            return jobs

    # ── Strategy 3: API endpoints ─────────────────────────────────────────
    jobs = _try_api_endpoints(search=search)
    if jobs:
        logger.info("Strategy 3 (API endpoints): extracted %d jobs", len(jobs))
        return jobs

    # ── Strategy 4: HTML parsing ──────────────────────────────────────────
    if html:
        jobs = _parse_jobs_from_html(html)
        if jobs:
            logger.info("Strategy 4 (HTML parsing): extracted %d jobs", len(jobs))
            return jobs

    logger.warning("All extraction strategies failed for search='%s'", search)
    return []


# ── Public API ────────────────────────────────────────────────────────────────

def scrape_climatetechlist_jobs(
    queries: Optional[List[str]] = None,
    remote_only: bool = True,
    max_results: int = 200,
    min_description_length: int = 10,
    keyword_filter: Optional[List[str]] = None,
) -> List[JobListing]:
    """
    Scrape jobs from ClimateTechList.

    Args:
        queries: Search terms to use. Defaults to data/engineering/python terms.
        remote_only: If True, filter to remote-only jobs.
        max_results: Maximum number of jobs to return across all queries.
        min_description_length: Minimum description length to keep a listing.
        keyword_filter: Optional list of keywords; if given, only jobs with a
                        keyword match in title/description/company are returned.

    Returns:
        List of parsed JobListing objects. Empty list if site is unreachable.
    """
    if queries is None:
        queries = DEFAULT_QUERIES

    all_jobs: List[JobListing] = []
    seen_ids: set = set()
    seen_urls: set = set()

    for i, query in enumerate(queries):
        if len(all_jobs) >= max_results:
            break

        # Rate limiting between queries
        if i > 0:
            delay = random.uniform(1.5, 3.5)
            logger.debug("Sleeping %.1fs between queries", delay)
            time.sleep(delay)

        raw_jobs = _fetch_and_extract(query, remote_only=remote_only)
        if not raw_jobs:
            continue

        for raw_job in raw_jobs:
            if len(all_jobs) >= max_results:
                break

            try:
                job = _parse_climatetechlist_job(raw_job)
                if job is None:
                    continue

                # Deduplicate by job_id and URL
                if job.job_id in seen_ids or job.job_url in seen_urls:
                    continue

                # Description length filter
                if len(job.description) < min_description_length:
                    continue

                # Optional keyword filter
                if keyword_filter:
                    search_text = f"{job.title} {job.company} {job.description}".lower()
                    if not any(kw.lower() in search_text for kw in keyword_filter):
                        continue

                all_jobs.append(job)
                seen_ids.add(job.job_id)
                seen_urls.add(job.job_url)

            except Exception as e:
                logger.debug("Failed to parse ClimateTechList job: %s", e)

    logger.info("ClimateTechList scraper: %d jobs total across %d queries",
                len(all_jobs), len(queries))
    return all_jobs


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    search_terms = sys.argv[1:] or ["Data"]
    jobs = scrape_climatetechlist_jobs(queries=search_terms, max_results=50)
    print(f"\nFound {len(jobs)} jobs\n")
    for i, job in enumerate(jobs[:15], 1):
        salary = job.get_salary_range_string()
        remote = f" [{job.remote_type.value}]" if job.remote_type else ""
        industry = job.company_industry or ""
        print(f"{i}. {job.title}")
        print(f"   Company: {job.company} | {job.location}{remote}")
        print(f"   Salary:  {salary}")
        if industry:
            print(f"   Sector:  {industry}")
        print(f"   URL:     {job.job_url}")
        print(f"   Method:  {job.raw_data.get('_extraction_method', '?')}")
        print()
