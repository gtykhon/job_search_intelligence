"""
Levels.fyi Job Scraper

Scrapes verified active job listings from levels.fyi/jobs using their
Next.js SSR data route for the initial seed, then the encrypted search
API for full pagination.

Data access:
  - SSR route:  levels.fyi/_next/data/{buildId}/en-us/jobs.json  (plain JSON)
  - Search API: api.levels.fyi/v1/job/search?...  (AES-ECB encrypted)

The search API encrypts responses with AES-ECB using a key derived from
MD5("levelstothemoon!!"). Response is base64-decoded → AES-ECB decrypted →
zlib-inflated → JSON parsed.

Rate limit: ~25 requests per 60 seconds on the API.
"""

import base64
import hashlib
import json
import logging
import re
import time
import zlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import JobListing, JobSite, JobType, RemoteType, ExperienceLevel

logger = logging.getLogger(__name__)

# Prefer curl_cffi for TLS impersonation
try:
    from curl_cffi import requests as http_client
    _IMPERSONATE = "chrome124"
except ImportError:
    import requests as http_client  # type: ignore[no-redef]
    _IMPERSONATE = None

# Try pycryptodome for AES decryption
try:
    from Crypto.Cipher import AES
    HAS_CRYPTO = True
except ImportError:
    try:
        from Cryptodome.Cipher import AES  # type: ignore[no-redef]
        HAS_CRYPTO = True
    except ImportError:
        HAS_CRYPTO = False

LEVELS_BASE = "https://www.levels.fyi"
LEVELS_API = "https://api.levels.fyi"

# Encryption key for API responses
_ENC_SECRET = b"levelstothemoon!!"
_ENC_KEY = hashlib.md5(_ENC_SECRET).hexdigest()[:16].encode("utf-8")

# Headers to mimic browser
_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.levels.fyi/jobs",
    "Origin": "https://www.levels.fyi",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

# Default search role slugs
DEFAULT_JOB_FAMILIES = [
    "software-engineer",
    "data-engineer",
    "machine-learning-engineer",
    "data-scientist",
]


# ── API Decryption ──────────────────────────────────────────────────────────

def _decrypt_response(encrypted_text: str) -> Optional[Dict]:
    """Decrypt a Levels.fyi API response.

    Process: base64 decode → AES-ECB decrypt → strip PKCS7 padding →
             zlib decompress → JSON parse.
    """
    if not HAS_CRYPTO:
        logger.warning("pycryptodome not installed — cannot decrypt Levels.fyi API responses")
        return None

    try:
        raw = base64.b64decode(encrypted_text)
        cipher = AES.new(_ENC_KEY, AES.MODE_ECB)
        decrypted = cipher.decrypt(raw)

        # Strip PKCS7 padding
        pad_len = decrypted[-1]
        if 0 < pad_len <= 16:
            decrypted = decrypted[:-pad_len]

        # Zlib decompress
        decompressed = zlib.decompress(decrypted)
        return json.loads(decompressed)
    except Exception as e:
        logger.debug(f"Decryption failed: {e}")
        return None


# ── SSR Data Route (plain JSON, no encryption) ─────────────────────────────

def _get_build_id() -> Optional[str]:
    """Extract the Next.js buildId from the homepage."""
    try:
        kwargs: Dict[str, Any] = {"timeout": 15, "headers": _HEADERS}
        if _IMPERSONATE:
            kwargs["impersonate"] = _IMPERSONATE

        resp = http_client.get(f"{LEVELS_BASE}/jobs", **kwargs)
        if resp.status_code != 200:
            return None

        # Look for buildId in __NEXT_DATA__
        match = re.search(r'"buildId"\s*:\s*"([^"]+)"', resp.text)
        if match:
            return match.group(1)
    except Exception as e:
        logger.debug(f"Failed to get buildId: {e}")
    return None


def _fetch_ssr_jobs() -> List[Dict]:
    """Fetch jobs from the Next.js SSR data route (plain JSON)."""
    build_id = _get_build_id()
    if not build_id:
        logger.warning("Could not extract Levels.fyi buildId")
        return []

    url = f"{LEVELS_BASE}/_next/data/{build_id}/en-us/jobs.json"
    try:
        kwargs: Dict[str, Any] = {"timeout": 15, "headers": _HEADERS}
        if _IMPERSONATE:
            kwargs["impersonate"] = _IMPERSONATE

        resp = http_client.get(url, **kwargs)
        if resp.status_code != 200:
            logger.warning(f"SSR route returned {resp.status_code}")
            return []

        data = resp.json()
        page_props = data.get("pageProps", {})

        # Data lives at pageProps.initialJobsData.results
        initial_data = page_props.get("initialJobsData", {})
        companies = initial_data.get("results") or page_props.get("companies") or page_props.get("results") or []

        # Extract company-job pairs from the result
        jobs = []
        if isinstance(companies, list):
            for company in companies:
                company_info = {
                    "companyName": company.get("companyName", ""),
                    "companySlug": company.get("companySlug", ""),
                    "companyType": company.get("companyType", ""),
                    "employeeCount": company.get("employeeCount"),
                    "shortDescription": company.get("shortDescription", ""),
                }
                for job in company.get("jobs", []):
                    job.update(company_info)
                    jobs.append(job)

        logger.info(f"SSR route returned {len(jobs)} jobs from {len(companies)} companies")
        return jobs
    except Exception as e:
        logger.warning(f"SSR fetch failed: {e}")
        return []


# ── Encrypted Search API ────────────────────────────────────────────────────

def _fetch_api_jobs(
    job_family_slugs: Optional[List[str]] = None,
    work_arrangements: Optional[List[str]] = None,
    min_compensation: Optional[int] = None,
    limit: int = 10,
    limit_per_company: int = 5,
    offset: int = 0,
    sort_by: str = "date_published",
) -> Tuple[List[Dict], int]:
    """Fetch jobs from the encrypted search API.

    Returns:
        Tuple of (jobs_list, total_companies_count).
    """
    if not HAS_CRYPTO:
        return [], 0

    params = {
        "limit": limit,
        "limitPerCompany": limit_per_company,
        "offset": offset,
        "sortBy": sort_by,
    }
    if job_family_slugs:
        for slug in job_family_slugs:
            params.setdefault("jobFamilySlugs", []).append(slug)  # type: ignore
    if work_arrangements:
        for wa in work_arrangements:
            params.setdefault("workArrangements", []).append(wa)  # type: ignore
    if min_compensation:
        params["minBaseCompensation"] = min_compensation

    try:
        kwargs: Dict[str, Any] = {"timeout": 20, "headers": _HEADERS, "params": params}
        if _IMPERSONATE:
            kwargs["impersonate"] = _IMPERSONATE

        resp = http_client.get(f"{LEVELS_API}/v1/job/search", **kwargs)
        if resp.status_code == 429:
            logger.warning("Levels.fyi API rate limited — backing off")
            return [], 0
        if resp.status_code != 200:
            logger.debug(f"API returned {resp.status_code}")
            return [], 0

        # Response is {"payload": "<encrypted>"} or plain JSON
        resp_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None
        if resp_data and "payload" in resp_data:
            data = _decrypt_response(resp_data["payload"])
        elif resp_data and "results" in resp_data:
            data = resp_data  # Plain JSON (no encryption)
        else:
            data = _decrypt_response(resp.text)

        if not data:
            return [], 0

        total = data.get("total", 0) or data.get("totalCompanies", 0)
        companies = data.get("results") or data.get("companies") or []

        jobs = []
        for company in companies:
            company_info = {
                "companyName": company.get("companyName", ""),
                "companySlug": company.get("companySlug", ""),
                "companyType": company.get("companyType", ""),
                "employeeCount": company.get("employeeCount"),
                "shortDescription": company.get("shortDescription", ""),
            }
            for job in company.get("jobs", []):
                job.update(company_info)
                jobs.append(job)

        return jobs, total
    except Exception as e:
        logger.warning(f"API fetch failed: {e}")
        return [], 0


# ── Job Parsing ─────────────────────────────────────────────────────────────

def _parse_remote_type(job_data: Dict) -> Optional[RemoteType]:
    """Parse work arrangement from Levels.fyi data."""
    wa = (job_data.get("workArrangement") or "").lower()
    if wa == "remote":
        return RemoteType.REMOTE
    if wa == "hybrid":
        return RemoteType.HYBRID
    if wa == "office":
        return RemoteType.ON_SITE
    return None


def _parse_experience_level(job_data: Dict) -> Optional[ExperienceLevel]:
    """Parse standard level into ExperienceLevel."""
    level = (job_data.get("standardLevel") or "").lower()
    if level in ("internship", "entry"):
        return ExperienceLevel.ENTRY
    if level in ("mid_staff",):
        return ExperienceLevel.MID
    if level in ("senior", "principal"):
        return ExperienceLevel.SENIOR
    if level in ("director",):
        return ExperienceLevel.DIRECTOR
    if level in ("executive", "manager"):
        return ExperienceLevel.EXECUTIVE
    return None


def _parse_levels_job(job_data: Dict) -> Optional[JobListing]:
    """Parse a Levels.fyi job object into a JobListing."""
    title = job_data.get("title", "").strip()
    if not title:
        return None

    company = job_data.get("companyName", "").strip()
    if not company:
        return None

    # Location
    locations = job_data.get("locations") or []
    if isinstance(locations, list):
        location = ", ".join(str(loc) for loc in locations[:3])
    else:
        location = str(locations)

    # Description — Levels.fyi listing pages are sparse,
    # build from available metadata
    desc_parts = []
    company_desc = job_data.get("shortDescription", "")
    if company_desc:
        desc_parts.append(f"Company: {company_desc}")

    company_type = job_data.get("companyType", "")
    employee_count = job_data.get("employeeCount")
    if company_type or employee_count:
        meta = []
        if company_type:
            meta.append(company_type.title())
        if employee_count:
            meta.append(f"{employee_count:,} employees")
        desc_parts.append(f"({', '.join(meta)})")

    if location:
        desc_parts.append(f"Location: {location}")

    wa = job_data.get("workArrangement", "")
    if wa:
        desc_parts.append(f"Work: {wa}")

    level = job_data.get("standardLevel", "")
    if level:
        desc_parts.append(f"Level: {level.replace('_', ' ').title()}")

    # Salary info in description
    min_total = job_data.get("minTotalSalary")
    max_total = job_data.get("maxTotalSalary")
    if min_total and max_total:
        currency = job_data.get("baseSalaryCurrency", "USD")
        desc_parts.append(f"Total Comp: ${min_total:,.0f} - ${max_total:,.0f} {currency}")

    description = " | ".join(desc_parts) if desc_parts else title

    # Job URL — use applicationUrl if available, else construct
    app_url = job_data.get("applicationUrl", "")
    job_id_val = job_data.get("id", "")
    company_slug = job_data.get("companySlug", "")

    # The canonical URL on levels.fyi
    if company_slug:
        job_url = f"{LEVELS_BASE}/companies/{company_slug}/jobs"
    elif app_url:
        job_url = app_url
    else:
        job_url = f"{LEVELS_BASE}/jobs"

    # Prefer the direct application URL for the actual link
    if app_url:
        job_url = app_url

    if not job_url:
        return None

    # Salary — use base salary for comparison, total for display
    salary_min = job_data.get("minBaseSalary")
    salary_max = job_data.get("maxBaseSalary")
    salary_currency = job_data.get("baseSalaryCurrency", "USD")

    # If no base salary, use total comp
    if not salary_min and not salary_max:
        salary_min = job_data.get("minTotalSalary")
        salary_max = job_data.get("maxTotalSalary")

    try:
        salary_min = float(salary_min) if salary_min else None
        salary_max = float(salary_max) if salary_max else None
    except (ValueError, TypeError):
        salary_min, salary_max = None, None

    # Remote type
    remote_type = _parse_remote_type(job_data)

    # Experience level
    experience_level = _parse_experience_level(job_data)

    # Posted date
    posted_date = None
    posting_date = job_data.get("postingDate")
    if posting_date:
        try:
            posted_date = datetime.fromisoformat(
                str(posting_date).replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except (ValueError, TypeError):
            pass

    return JobListing(
        title=title[:200],
        company=company[:100],
        location=location[:100] if location else "See posting",
        description=description[:5000],
        job_url=job_url,
        job_id=f"lvl-{job_id_val}" if job_id_val else f"lvl-{company_slug}-{title[:30]}",
        remote_type=remote_type,
        experience_level=experience_level,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
        posted_date=posted_date,
        source_site=JobSite.LEVELS_FYI,
        company_num_employees=str(employee_count) if employee_count else None,
        raw_data={
            "source": "levels_fyi",
            "levels_id": str(job_id_val),
            "company_slug": company_slug,
            "company_type": company_type,
            "work_arrangement": wa,
            "standard_level": level,
            "application_url": app_url,
            "min_total_comp": min_total,
            "max_total_comp": max_total,
        },
    )


# ── Public API ──────────────────────────────────────────────────────────────

def scrape_levelsfyi_jobs(
    job_families: Optional[List[str]] = None,
    work_arrangements: Optional[List[str]] = None,
    min_compensation: Optional[int] = None,
    max_pages: int = 5,
    companies_per_page: int = 10,
    jobs_per_company: int = 5,
    use_api: bool = True,
) -> List[JobListing]:
    """
    Scrape verified active jobs from Levels.fyi.

    Args:
        job_families: Job family slugs to filter (e.g., ["data-engineer"]).
                      Defaults to DEFAULT_JOB_FAMILIES.
        work_arrangements: Filter by ["remote", "hybrid", "office"].
        min_compensation: Minimum base salary filter.
        max_pages: Maximum pagination pages (API only).
        companies_per_page: Companies per API page.
        jobs_per_company: Max jobs per company.
        use_api: If True and pycryptodome available, use encrypted API
                 for full results. If False, use SSR route only.

    Returns:
        List of parsed JobListing objects.
    """
    if not job_families:
        job_families = DEFAULT_JOB_FAMILIES

    all_jobs: List[JobListing] = []
    seen_ids: set = set()

    # Strategy 1: Try encrypted API (full data with pagination)
    if use_api and HAS_CRYPTO:
        logger.info("Levels.fyi: trying encrypted search API")
        for page in range(max_pages):
            offset = page * companies_per_page
            raw_jobs, total = _fetch_api_jobs(
                job_family_slugs=job_families,
                work_arrangements=work_arrangements,
                min_compensation=min_compensation,
                limit=companies_per_page,
                limit_per_company=jobs_per_company,
                offset=offset,
            )

            if not raw_jobs:
                if page == 0:
                    logger.info("API returned no results — falling back to SSR")
                break

            page_count = 0
            for raw_job in raw_jobs:
                try:
                    job = _parse_levels_job(raw_job)
                    if job and job.job_id not in seen_ids:
                        all_jobs.append(job)
                        seen_ids.add(job.job_id)
                        page_count += 1
                except Exception as e:
                    logger.debug(f"Failed to parse Levels.fyi job: {e}")

            logger.info(f"Levels.fyi API page {page}: {page_count} jobs (total so far: {len(all_jobs)})")

            if offset + companies_per_page >= total:
                break  # No more pages

            # Rate limit: 25 req / 60s → ~2.5s between requests
            time.sleep(3.0)

    # Strategy 2: SSR route (always works, limited to ~8 companies / ~25 jobs)
    if not all_jobs:
        logger.info("Levels.fyi: using SSR data route (plain JSON, ~25 jobs)")
        raw_jobs = _fetch_ssr_jobs()
        for raw_job in raw_jobs:
            try:
                job = _parse_levels_job(raw_job)
                if job and job.job_id not in seen_ids:
                    all_jobs.append(job)
                    seen_ids.add(job.job_id)
            except Exception as e:
                logger.debug(f"Failed to parse Levels.fyi SSR job: {e}")

    logger.info(f"Levels.fyi scraper: {len(all_jobs)} total jobs")
    return all_jobs


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(level=logging.INFO)

    print(f"AES decryption available: {HAS_CRYPTO}")
    jobs = scrape_levelsfyi_jobs(max_pages=2, companies_per_page=5)
    print(f"\nFound {len(jobs)} jobs\n")
    for i, job in enumerate(jobs[:15], 1):
        salary = job.get_salary_range_string()
        remote = f" [{job.remote_type.value}]" if job.remote_type else ""
        total_comp = job.raw_data.get("min_total_comp")
        max_comp = job.raw_data.get("max_total_comp")
        comp_str = ""
        if total_comp and max_comp:
            comp_str = f" | Total: ${total_comp:,.0f}-${max_comp:,.0f}"
        print(f"{i}. {job.title}")
        print(f"   {job.company} | {job.location}{remote}")
        print(f"   Base: {salary}{comp_str}")
        print(f"   {job.job_url}")
        print()
