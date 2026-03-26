"""
Hacker News "Who is Hiring" Scraper

Fetches job postings from the monthly "Ask HN: Who is Hiring?" threads
using the free HN Algolia API. Zero scraping risk — fully public API.

API endpoints:
  - Find threads: hn.algolia.com/api/v1/search?query="who+is+hiring"&tags=story
  - Fetch comments: hn.algolia.com/api/v1/search?tags=comment,story_{ID}&hitsPerPage=500

Job posting format (pipe-delimited first line):
  Company | Role | Location | Remote/Onsite | Compensation
"""

import re
import html
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from .models import JobListing, JobSite, RemoteType

logger = logging.getLogger(__name__)

# Prefer curl_cffi; fall back to requests
try:
    from curl_cffi import requests as http_client
except ImportError:
    import requests as http_client  # type: ignore[no-redef]

ALGOLIA_BASE = "https://hn.algolia.com/api/v1"


# ── API calls ────────────────────────────────────────────────────────────────

def _find_latest_thread(months_back: int = 2) -> Optional[Dict[str, Any]]:
    """Find the most recent 'Who is Hiring' thread."""
    cutoff = int((datetime.utcnow() - timedelta(days=months_back * 31)).timestamp())
    url = (
        f"{ALGOLIA_BASE}/search"
        f"?query=%22who+is+hiring%22"
        f"&tags=story"
        f"&numericFilters=created_at_i>{cutoff}"
        f"&hitsPerPage=5"
    )
    try:
        resp = http_client.get(url, timeout=15)
        data = resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch HN threads: {e}")
        return None

    # Filter for official threads by 'whoishiring' user
    for hit in data.get("hits", []):
        if hit.get("author") == "whoishiring" and "who is hiring" in hit.get("title", "").lower():
            logger.info(f"Found HN thread: {hit['title']} ({hit.get('num_comments', '?')} comments)")
            return hit

    # Fallback: just take the first match
    hits = data.get("hits", [])
    if hits:
        logger.info(f"Found HN thread (non-official): {hits[0]['title']}")
        return hits[0]

    return None


def _fetch_comments(story_id: str, max_pages: int = 3) -> List[Dict[str, Any]]:
    """Fetch all top-level comments (job postings) from a thread."""
    all_comments = []
    story_id_int = int(story_id)

    for page in range(max_pages):
        url = (
            f"{ALGOLIA_BASE}/search"
            f"?tags=comment,story_{story_id}"
            f"&hitsPerPage=500"
            f"&page={page}"
        )
        try:
            resp = http_client.get(url, timeout=15)
            data = resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch HN comments page {page}: {e}")
            break

        hits = data.get("hits", [])
        if not hits:
            break

        # Only keep top-level comments (parent_id == story_id)
        for hit in hits:
            parent = hit.get("parent_id")
            if parent is not None and int(parent) == story_id_int:
                all_comments.append(hit)

        # Check if we have all pages
        if data.get("nbPages", 0) <= page + 1:
            break

    logger.info(f"Fetched {len(all_comments)} top-level job postings from HN thread")
    return all_comments


# ── Parsing ──────────────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '\n', text)
    text = html.unescape(text)
    return text.strip()


def _parse_remote_type(text: str) -> Optional[RemoteType]:
    """Detect remote/onsite/hybrid from text."""
    lower = text.lower()
    if "remote" in lower and "hybrid" in lower:
        return RemoteType.HYBRID
    if "remote" in lower:
        return RemoteType.REMOTE
    if "onsite" in lower or "on-site" in lower or "in-office" in lower:
        return RemoteType.ON_SITE
    return None


def _parse_salary(text: str) -> Tuple[Optional[float], Optional[float]]:
    """Extract salary range from text like '$133-157K' or '$160k-$250k'."""
    # Pattern: $NNNk-$NNNk or $NNN,NNN-$NNN,NNN
    patterns = [
        r'\$(\d{2,3})[kK]\s*[-–—to]+\s*\$?(\d{2,3})[kK]',
        r'\$(\d{3},?\d{3})\s*[-–—to]+\s*\$?(\d{3},?\d{3})',
        r'\$(\d{2,3})[kK]',
    ]

    for pat in patterns:
        match = re.search(pat, text)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                low = float(groups[0].replace(',', ''))
                high = float(groups[1].replace(',', ''))
                if low < 1000:
                    low *= 1000
                if high < 1000:
                    high *= 1000
                return low, high
            elif len(groups) == 1:
                val = float(groups[0].replace(',', ''))
                if val < 1000:
                    val *= 1000
                return val, None
    return None, None


def _parse_comment(comment: Dict[str, Any]) -> Optional[JobListing]:
    """Parse a single HN comment into a JobListing."""
    raw_text = comment.get("comment_text", "")
    if not raw_text:
        return None

    clean = _strip_html(raw_text)
    lines = [l.strip() for l in clean.split('\n') if l.strip()]
    if not lines:
        return None

    first_line = lines[0]

    # Parse pipe-delimited header: Company | Role | Location | ...
    parts = [p.strip() for p in first_line.split('|')]

    if len(parts) >= 2:
        company = parts[0]
        title = parts[1]
        location = parts[2] if len(parts) > 2 else ""
    else:
        # No pipe format — use first line as title, try to extract company
        company = first_line.split(' - ')[0].strip() if ' - ' in first_line else "Unknown"
        title = first_line
        location = ""

    # Skip very short or non-job comments
    if len(clean) < 50:
        return None

    # Build description from remaining lines
    description = '\n'.join(lines[1:]) if len(lines) > 1 else clean

    # Detect remote type from all parts
    all_parts_text = ' '.join(parts) if len(parts) >= 2 else first_line
    remote_type = _parse_remote_type(all_parts_text + ' ' + description[:200])

    # Extract salary
    salary_min, salary_max = _parse_salary(all_parts_text + ' ' + description[:500])

    # Extract URLs for "apply" link
    url_match = re.search(r'https?://[^\s<>"]+', raw_text)
    job_url = url_match.group(0).rstrip('.,;)') if url_match else ""

    # If no URL found, link to the HN comment
    if not job_url:
        job_url = f"https://news.ycombinator.com/item?id={comment.get('objectID', '')}"

    # Parse posted date
    posted_date = None
    created_at = comment.get("created_at")
    if created_at:
        try:
            posted_date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, TypeError):
            pass

    return JobListing(
        title=title[:200],
        company=company[:100],
        location=location[:100] if location else "See posting",
        description=description[:5000],
        job_url=job_url,
        job_id=f"hn-{comment.get('objectID', '')}",
        remote_type=remote_type,
        salary_min=salary_min,
        salary_max=salary_max,
        posted_date=posted_date,
        source_site=JobSite.HACKER_NEWS,
        raw_data={
            "source": "hackernews",
            "hn_comment_id": comment.get("objectID"),
            "hn_author": comment.get("author"),
            "hn_story_id": comment.get("story_id"),
            "hn_story_title": comment.get("story_title"),
        },
    )


# ── Public API ───────────────────────────────────────────────────────────────

def scrape_hn_jobs(
    months_back: int = 2,
    min_description_length: int = 80,
) -> List[JobListing]:
    """
    Scrape jobs from the latest HN "Who is Hiring" thread.

    Args:
        months_back: How many months back to search for threads.
        min_description_length: Minimum comment length to consider.

    Returns:
        List of parsed JobListing objects.
    """
    thread = _find_latest_thread(months_back)
    if not thread:
        logger.warning("No HN 'Who is Hiring' thread found")
        return []

    story_id = thread["objectID"]
    comments = _fetch_comments(story_id)

    jobs = []
    for comment in comments:
        try:
            job = _parse_comment(comment)
            if job and len(job.description) >= min_description_length:
                jobs.append(job)
        except Exception as e:
            logger.debug(f"Failed to parse HN comment: {e}")

    logger.info(f"Parsed {len(jobs)} job postings from HN 'Who is Hiring'")
    return jobs


if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    logging.basicConfig(level=logging.INFO)
    jobs = scrape_hn_jobs()
    print(f"\nFound {len(jobs)} jobs\n")
    for i, job in enumerate(jobs[:10], 1):
        salary = job.get_salary_range_string()
        remote = f" [{job.remote_type.value}]" if job.remote_type else ""
        print(f"{i}. {job.title}")
        print(f"   🏢 {job.company} | {job.location}{remote}")
        print(f"   💰 {salary}")
        print(f"   🔗 {job.job_url}")
        print()
