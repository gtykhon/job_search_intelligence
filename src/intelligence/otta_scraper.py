"""
Otta / Welcome to the Jungle (WTTJ) Job Scraper

Scrapes job listings from Welcome to the Jungle (formerly Otta, now merged)
using their public Algolia search API. No browser automation needed.

Otta (otta.com) redirects to welcometothejungle.com. All data is served
via Algolia with publicly exposed credentials (standard Algolia practice
for search-only API keys).

Algolia config:
  - App ID:    set via ALGOLIA_APP_ID env var
  - API Key:   set via ALGOLIA_API_KEY env var
  - Job Index: wttj_jobs_production_en
  - Referer:   https://www.welcometothejungle.com/

Available filters (Algolia facets):
  - contract_type: full_time, internship, freelance, part_time, etc.
  - remote: fulltime, partial, punctual, no, unknown
  - offices.country_code: US, GB, FR, DE, CA, etc.
  - new_profession.category_name: "Tech & Engineering", etc.
  - salary_currency: EUR, USD, GBP
"""

import json
import logging
import os
import re
import time
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import JobListing, JobSite, JobType, RemoteType

logger = logging.getLogger(__name__)

# Prefer curl_cffi; fall back to requests
try:
    from curl_cffi import requests as http_client
    _IMPERSONATE = "chrome124"
except ImportError:
    import requests as http_client  # type: ignore[no-redef]
    _IMPERSONATE = None

# ── Algolia Config ──────────────────────────────────────────────────────────

ALGOLIA_APP_ID = os.getenv("ALGOLIA_APP_ID", "")
ALGOLIA_API_KEY = os.getenv("ALGOLIA_API_KEY", "")
ALGOLIA_INDEX = "wttj_jobs_production_en"
ALGOLIA_URL = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{ALGOLIA_INDEX}/query"

WTTJ_BASE = "https://www.welcometothejungle.com"

_HEADERS = {
    "X-Algolia-Application-Id": ALGOLIA_APP_ID,
    "X-Algolia-API-Key": ALGOLIA_API_KEY,
    "Content-Type": "application/json",
    "Referer": f"{WTTJ_BASE}/",
    "Origin": WTTJ_BASE,
}

# Default search queries for data/ML/software engineering
DEFAULT_QUERIES = [
    "data engineer",
    "machine learning engineer",
    "software engineer",
    "analytics engineer",
    "backend engineer",
]

# Default country filter — US + remote-friendly English markets
DEFAULT_COUNTRIES = ["US", "GB", "CA"]


# ── Algolia API ─────────────────────────────────────────────────────────────

def _algolia_search(
    query: str = "",
    filters: str = "",
    hits_per_page: int = 50,
    page: int = 0,
) -> Optional[Dict]:
    """Execute an Algolia search query against WTTJ jobs index.

    Args:
        query: Free-text search query.
        filters: Algolia filter string (e.g., 'contract_type:full_time AND remote:fulltime').
        hits_per_page: Results per page (max 1000).
        page: Page number (0-indexed).

    Returns:
        Algolia response dict with 'hits', 'nbHits', 'nbPages', etc.
    """
    body = {
        "query": query,
        "hitsPerPage": hits_per_page,
        "page": page,
    }
    if filters:
        body["filters"] = filters

    # Request specific attributes to reduce response size
    body["attributesToRetrieve"] = [
        "name", "slug", "reference", "summary", "key_missions",
        "contract_type", "language",
        "salary_minimum", "salary_maximum", "salary_yearly_minimum",
        "salary_currency", "salary_period",
        "offices", "remote", "has_remote",
        "new_profession", "sectors", "benefits",
        "experience_level_minimum", "education_level",
        "organization", "published_at",
    ]

    try:
        kwargs: Dict[str, Any] = {
            "timeout": 15,
            "headers": _HEADERS,
        }
        if _IMPERSONATE:
            kwargs["impersonate"] = _IMPERSONATE

        resp = http_client.post(ALGOLIA_URL, json=body, **kwargs)
        if resp.status_code == 403:
            logger.warning("Algolia returned 403 — may need updated Referer header")
            return None
        if resp.status_code == 429:
            logger.warning("Algolia rate limited")
            return None
        if resp.status_code != 200:
            logger.debug(f"Algolia returned {resp.status_code}")
            return None

        return resp.json()
    except Exception as e:
        logger.warning(f"Algolia search failed: {e}")
        return None


# ── Job Parsing ─────────────────────────────────────────────────────────────

def _parse_remote_type(hit: Dict) -> Optional[RemoteType]:
    """Parse remote type from WTTJ remote field."""
    remote = (hit.get("remote") or "").lower()
    if remote == "fulltime":
        return RemoteType.REMOTE
    if remote in ("partial", "punctual"):
        return RemoteType.HYBRID
    if remote == "no":
        return RemoteType.ON_SITE
    return None


def _parse_contract_type(hit: Dict) -> Optional[JobType]:
    """Map WTTJ contract_type to JobType."""
    ct = (hit.get("contract_type") or "").lower()
    mapping = {
        "full_time": JobType.FULL_TIME,
        "part_time": JobType.PART_TIME,
        "freelance": JobType.CONTRACT,
        "temporary": JobType.TEMPORARY,
        "internship": JobType.INTERNSHIP,
        "apprenticeship": JobType.INTERNSHIP,
    }
    return mapping.get(ct)


def _parse_locations(hit: Dict) -> str:
    """Extract location string from offices array."""
    offices = hit.get("offices") or []
    if not offices:
        return ""

    locations = []
    seen = set()
    for office in offices[:5]:
        if isinstance(office, dict):
            city = office.get("city") or office.get("local_city") or ""
            state = office.get("state") or office.get("local_state") or ""
            country = office.get("country_code") or office.get("country") or ""
            parts = [p for p in [city, state, country] if p]
            loc_str = ", ".join(parts)
            if loc_str and loc_str not in seen:
                locations.append(loc_str)
                seen.add(loc_str)

    return " | ".join(locations) if locations else ""


def _parse_otta_job(hit: Dict) -> Optional[JobListing]:
    """Parse a WTTJ/Otta Algolia hit into a JobListing."""
    title = (hit.get("name") or "").strip()
    if not title:
        return None

    # Organization/company data
    org = hit.get("organization") or {}
    company = (org.get("name") or "").strip()
    if not company:
        return None
    company_slug = org.get("slug", "")
    company_desc = org.get("description") or org.get("summary") or ""
    company_employees = org.get("nb_employees")

    # Location
    location = _parse_locations(hit)

    # Description — build from summary + key_missions
    summary = hit.get("summary") or ""
    key_missions = hit.get("key_missions") or []
    desc_parts = []
    if summary:
        desc_parts.append(summary)
    if key_missions and isinstance(key_missions, list):
        missions_text = "\n".join(f"• {m}" for m in key_missions[:10] if isinstance(m, str))
        if missions_text:
            desc_parts.append(f"\nKey Responsibilities:\n{missions_text}")

    # Add company context if description is short
    if len(" ".join(desc_parts)) < 100 and company_desc:
        desc_parts.insert(0, f"About {company}: {company_desc[:300]}")

    # Add benefits
    benefits = hit.get("benefits") or []
    if benefits and isinstance(benefits, list):
        benefits_str = ", ".join(str(b) for b in benefits[:8])
        if benefits_str:
            desc_parts.append(f"\nBenefits: {benefits_str}")

    # Add profession/sector info
    profession = hit.get("new_profession") or {}
    if isinstance(profession, dict):
        cat = profession.get("category_name", "")
        subcat = profession.get("sub_category_name", "")
        pivot = profession.get("pivot_name", "")
        if cat or subcat:
            prof_str = " > ".join(p for p in [cat, subcat, pivot] if p)
            desc_parts.append(f"Category: {prof_str}")

    description = "\n".join(desc_parts) if desc_parts else title
    if not description or len(description) < 15:
        return None

    # Remove HTML if any
    if "<" in description:
        description = re.sub(r'<[^>]+>', ' ', description)
        description = re.sub(r'\s+', ' ', description).strip()

    # URL
    job_slug = hit.get("slug", "")
    if company_slug and job_slug:
        job_url = f"{WTTJ_BASE}/en/companies/{company_slug}/jobs/{job_slug}"
    elif job_slug:
        job_url = f"{WTTJ_BASE}/en/jobs/{job_slug}"
    else:
        return None

    # Salary
    salary_min = hit.get("salary_minimum") or hit.get("salary_yearly_minimum")
    salary_max = hit.get("salary_maximum")
    salary_currency = hit.get("salary_currency", "USD")
    try:
        salary_min = float(salary_min) if salary_min else None
        salary_max = float(salary_max) if salary_max else None
    except (ValueError, TypeError):
        salary_min, salary_max = None, None

    # Remote type
    remote_type = _parse_remote_type(hit)

    # Job type
    job_type = _parse_contract_type(hit)

    # Posted date
    posted_date = None
    published = hit.get("published_at")
    if published:
        try:
            posted_date = datetime.fromisoformat(
                str(published).replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except (ValueError, TypeError):
            pass

    # Reference ID
    reference = hit.get("reference") or hit.get("objectID") or job_slug

    # Sectors
    sectors = hit.get("sectors") or []
    sector_names = []
    if isinstance(sectors, list):
        for s in sectors[:5]:
            if isinstance(s, dict):
                sector_names.append(s.get("name", ""))
            elif isinstance(s, str):
                sector_names.append(s)

    return JobListing(
        title=title[:200],
        company=company[:100],
        location=location[:100] if location else "See posting",
        description=description[:5000],
        job_url=job_url,
        job_id=f"otta-{reference}",
        job_type=job_type,
        remote_type=remote_type,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency or "USD",
        posted_date=posted_date,
        source_site=JobSite.OTTA,
        company_description=company_desc[:500] if company_desc else None,
        company_num_employees=str(company_employees) if company_employees else None,
        raw_data={
            "source": "otta",
            "wttj_reference": reference,
            "wttj_slug": job_slug,
            "company_slug": company_slug,
            "sectors": ", ".join(sector_names),
            "benefits": ", ".join(str(b) for b in (benefits or [])[:10]),
            "experience_level": hit.get("experience_level_minimum", ""),
            "education_level": hit.get("education_level", ""),
        },
    )


# ── Public API ──────────────────────────────────────────────────────────────

def scrape_otta_jobs(
    queries: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
    contract_types: Optional[List[str]] = None,
    remote_only: bool = False,
    hits_per_page: int = 50,
    max_pages_per_query: int = 3,
    min_description_length: int = 30,
) -> List[JobListing]:
    """
    Scrape jobs from Otta / Welcome to the Jungle via Algolia API.

    Args:
        queries: Search queries. Defaults to DEFAULT_QUERIES.
        countries: Country codes to filter (e.g., ["US", "GB"]).
                   Defaults to DEFAULT_COUNTRIES.
        contract_types: Filter by contract type (e.g., ["full_time"]).
        remote_only: If True, only fetch remote jobs.
        hits_per_page: Results per API page (max 1000).
        max_pages_per_query: Max pages to fetch per query.
        min_description_length: Minimum description length.

    Returns:
        List of parsed JobListing objects.
    """
    if not queries:
        queries = DEFAULT_QUERIES
    if not countries:
        countries = DEFAULT_COUNTRIES

    # Build Algolia filter string
    filter_parts = []

    # Country filter
    if countries:
        country_filters = " OR ".join(
            f"offices.country_code:{c}" for c in countries
        )
        filter_parts.append(f"({country_filters})")

    # Contract type filter
    if contract_types:
        ct_filters = " OR ".join(
            f"contract_type:{ct}" for ct in contract_types
        )
        filter_parts.append(f"({ct_filters})")
    else:
        # Default: full_time only
        filter_parts.append("contract_type:full_time")

    # Remote filter
    if remote_only:
        filter_parts.append("remote:fulltime")

    filters = " AND ".join(filter_parts) if filter_parts else ""

    all_jobs: List[JobListing] = []
    seen_ids: set = set()

    for query in queries:
        for page in range(max_pages_per_query):
            logger.info(f"Otta/WTTJ: searching '{query}' page {page} (filter: {filters})")

            result = _algolia_search(
                query=query,
                filters=filters,
                hits_per_page=hits_per_page,
                page=page,
            )

            if not result:
                logger.warning(f"Otta/WTTJ: no result for '{query}' page {page}")
                break

            hits = result.get("hits", [])
            if not hits:
                break

            nb_pages = result.get("nbPages", 0)
            nb_hits = result.get("nbHits", 0)

            if page == 0:
                logger.info(f"Otta/WTTJ: '{query}' → {nb_hits} total hits across {nb_pages} pages")

            page_count = 0
            for hit in hits:
                try:
                    job = _parse_otta_job(hit)
                    if job and job.job_id not in seen_ids:
                        if len(job.description) >= min_description_length:
                            all_jobs.append(job)
                            seen_ids.add(job.job_id)
                            page_count += 1
                except Exception as e:
                    logger.debug(f"Failed to parse WTTJ job: {e}")

            logger.info(f"Otta/WTTJ: parsed {page_count} jobs from '{query}' page {page}")

            if page + 1 >= nb_pages:
                break  # No more pages

            # Rate limit between pages
            time.sleep(random.uniform(0.5, 1.5))

        # Rate limit between queries
        time.sleep(random.uniform(1.0, 2.0))

    logger.info(f"Otta/WTTJ scraper: {len(all_jobs)} total jobs")
    return all_jobs


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(level=logging.INFO)
    jobs = scrape_otta_jobs(
        queries=["data engineer"],
        countries=["US"],
        max_pages_per_query=1,
    )
    print(f"\nFound {len(jobs)} jobs\n")
    for i, job in enumerate(jobs[:15], 1):
        salary = job.get_salary_range_string()
        remote = f" [{job.remote_type.value}]" if job.remote_type else ""
        sectors = job.raw_data.get("sectors", "")
        benefits = job.raw_data.get("benefits", "")
        print(f"{i}. {job.title}")
        print(f"   {job.company} | {job.location}{remote}")
        print(f"   Salary: {salary}")
        if sectors:
            print(f"   Sectors: {sectors}")
        if benefits:
            print(f"   Benefits: {benefits[:80]}...")
        print(f"   {job.job_url}")
        print()
