"""
JSON-LD Parser — Unauthenticated fallback for LinkedIn job data.

Parses structured data (Schema.org JobPosting) from public LinkedIn job pages.
No authentication required — works when Voyager API is rate-limited or unavailable.

Available fields from JSON-LD:
  - datePosted (date only, no time)
  - validThrough (expiration date)
  - title
  - description (full, HTML)
  - hiringOrganization (name, sameAs URL)
  - jobLocation (address)
  - employmentType
  - identifier (job ID)

NOT available from JSON-LD:
  - applicantsCount
  - hiring manager / poster info
  - exact listedAt timestamp (only date)
  - company headcount
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Prefer curl_cffi for TLS evasion; fall back to requests
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


def fetch_job_jsonld(job_url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """
    Fetch and parse JSON-LD structured data from a public LinkedIn job page.

    Args:
        job_url: Full LinkedIn job URL (e.g. https://www.linkedin.com/jobs/view/12345)
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON-LD dict or None if unavailable.
    """
    if not HAS_BS4:
        logger.warning("beautifulsoup4 not installed — cannot parse JSON-LD")
        return None

    try:
        kwargs: Dict[str, Any] = {"timeout": timeout}
        if _IMPERSONATE:
            kwargs["impersonate"] = _IMPERSONATE

        resp = http_client.get(job_url, **kwargs)
        if resp.status_code != 200:
            logger.debug(f"JSON-LD fetch returned {resp.status_code} for {job_url}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        script = soup.find("script", type="application/ld+json")
        if not script or not script.string:
            logger.debug(f"No JSON-LD block found on {job_url}")
            return None

        data = json.loads(script.string)
        return data

    except Exception as e:
        logger.debug(f"JSON-LD parse failed for {job_url}: {e}")
        return None


def extract_job_fields(ld: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract useful fields from a parsed JSON-LD JobPosting object.

    Returns a flat dict with keys matching JobListing field names where possible.
    """
    org = ld.get("hiringOrganization", {})
    location = ld.get("jobLocation", {})
    address = location.get("address", {}) if isinstance(location, dict) else {}
    identifier = ld.get("identifier", {})

    date_posted = None
    if ld.get("datePosted"):
        try:
            date_posted = datetime.strptime(ld["datePosted"], "%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    valid_through = None
    if ld.get("validThrough"):
        try:
            valid_through = datetime.strptime(
                ld["validThrough"][:10], "%Y-%m-%d"
            )
        except (ValueError, TypeError):
            pass

    return {
        "title": ld.get("title"),
        "description": ld.get("description"),  # HTML
        "date_posted": date_posted,
        "valid_through": valid_through,
        "company": org.get("name"),
        "company_url": org.get("sameAs"),
        "location": address.get("addressLocality", ""),
        "region": address.get("addressRegion", ""),
        "country": address.get("addressCountry"),
        "employment_type": ld.get("employmentType"),
        "job_id": identifier.get("value") if isinstance(identifier, dict) else None,
    }


def enrich_job_with_jsonld(job_url: str) -> Optional[Dict[str, Any]]:
    """
    Convenience: fetch + extract in one call.
    Returns extracted fields dict or None.
    """
    ld = fetch_job_jsonld(job_url)
    if not ld:
        return None
    return extract_job_fields(ld)
