"""
Voyager API Enrichment — Enrich JobSpy-scraped jobs with Voyager API data.

After JobSpy scrapes basic job listings (title, company, salary, URL),
this module enriches them with data only available from LinkedIn's Voyager API:

  - applicantsCount (exact number of applicants)
  - jobPosterName / jobPosterTitle / jobPosterProfileUrl (hiring manager)
  - listedAt / originalListedAt (exact ms timestamps)
  - company staffCount (exact headcount, not bucketed)
  - Full job description (if truncated by JobSpy)

Rate limits: 3-7s random delay per call. Budget ~50-100 enrichments per session.
"""

import re
import time
import random
import logging
from typing import List, Optional, Dict, Any

from .models import JobListing, JobSite

logger = logging.getLogger(__name__)

# Safe delay range (seconds) — matches LinkedIn research recommendations
MIN_DELAY = 3.0
MAX_DELAY = 7.0


def _extract_linkedin_job_id(job_url: str) -> Optional[str]:
    """Extract numeric job ID from a LinkedIn job URL."""
    match = re.search(r'/jobs/view/(\d+)', job_url)
    if match:
        return match.group(1)
    # Also handle /jobs/collections/ URLs with currentJobId param
    match = re.search(r'currentJobId=(\d+)', job_url)
    if match:
        return match.group(1)
    return None


def enrich_jobs_with_voyager(
    jobs: List[JobListing],
    linkedin_api,
    max_enrichments: int = 50,
    linkedin_only: bool = True,
) -> int:
    """
    Enrich job listings in-place with Voyager API data.

    Args:
        jobs: List of JobListing objects to enrich (mutated in place).
        linkedin_api: Authenticated linkedin_api.Linkedin instance.
        max_enrichments: Max number of API calls to make this session.
        linkedin_only: If True, only enrich LinkedIn-sourced jobs
                       (Indeed/Glassdoor URLs won't work with Voyager).

    Returns:
        Number of jobs successfully enriched.
    """
    enriched_count = 0

    for job in jobs:
        if enriched_count >= max_enrichments:
            logger.info(f"Reached enrichment limit ({max_enrichments}), stopping")
            break

        # Skip non-LinkedIn jobs if flag set
        if linkedin_only and job.source_site != JobSite.LINKEDIN:
            continue

        # Extract LinkedIn job ID
        job_id = _extract_linkedin_job_id(job.job_url)
        if not job_id:
            continue

        # Already enriched?
        if job.applicant_count is not None or job.listed_at_ms is not None:
            continue

        try:
            # Rate limit
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            time.sleep(delay)

            # Call Voyager API
            data = linkedin_api.get_job(job_id)
            if not data:
                continue

            # Extract enrichment fields
            _apply_voyager_data(job, data)
            enriched_count += 1

            logger.debug(
                f"Enriched: {job.title} @ {job.company} — "
                f"applicants={job.applicant_count}, poster={job.hiring_manager_name}"
            )

        except Exception as e:
            logger.warning(f"Voyager enrichment failed for job {job_id}: {e}")
            # On rate limit or challenge, stop enriching
            error_str = str(e).lower()
            if "429" in error_str or "challenge" in error_str or "captcha" in error_str:
                logger.warning("Rate limit or challenge detected — stopping enrichment")
                break

    logger.info(f"Enriched {enriched_count} jobs with Voyager data")
    return enriched_count


def _apply_voyager_data(job: JobListing, data: Dict[str, Any]) -> None:
    """Apply Voyager API response fields to a JobListing object."""
    # Applicant count
    applicants = data.get("applicantsCount")
    if applicants is not None:
        try:
            job.applicant_count = int(applicants)
        except (ValueError, TypeError):
            pass

    # Exact timestamps (ms epoch)
    listed_at = data.get("listedAt")
    if listed_at is not None:
        job.listed_at_ms = int(listed_at)

    original_listed_at = data.get("originalListedAt")
    if original_listed_at is not None:
        job.original_listed_at_ms = int(original_listed_at)

    # Hiring manager / poster info (~40-60% of postings have this)
    poster_name = data.get("jobPosterName")
    if poster_name:
        job.hiring_manager_name = poster_name
        job.hiring_manager_title = data.get("jobPosterTitle")
        job.hiring_manager_url = data.get("jobPosterProfileUrl")

    # Company exact headcount
    company_data = data.get("companyDetails", {})
    if isinstance(company_data, dict):
        staff = company_data.get("staffCount")
        if staff is not None:
            try:
                job.company_staff_count = int(staff)
            except (ValueError, TypeError):
                pass

    # Full description (replace truncated one if we got a longer version)
    desc = data.get("description", {})
    if isinstance(desc, dict):
        full_text = desc.get("text", "")
    elif isinstance(desc, str):
        full_text = desc
    else:
        full_text = ""

    if full_text and len(full_text) > len(job.description or ""):
        job.description = full_text

    # Store raw Voyager response for debugging / future field discovery
    job.raw_data["voyager_enrichment"] = {
        "applicantsCount": applicants,
        "listedAt": listed_at,
        "originalListedAt": original_listed_at,
        "jobPosterName": poster_name,
        "jobPosterTitle": data.get("jobPosterTitle"),
        "jobPosterProfileUrl": data.get("jobPosterProfileUrl"),
    }
