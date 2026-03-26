"""
Ashby Job Board Scraper

Fetches job postings from companies using Ashby's free public Posting API.
No authentication required — fully public endpoints.

API endpoint:
  GET https://api.ashbyhq.com/posting-api/job-board/{board_name}?includeCompensation=true

Returns JSON: {"jobs": [...], "apiVersion": ...}
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .models import JobListing, JobSite, RemoteType, JobType

logger = logging.getLogger(__name__)

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore[assignment]

ASHBY_API_BASE = "https://api.ashbyhq.com/posting-api/job-board"

# ── Curated tech company board names ────────────────────────────────────────

TECH_COMPANY_BOARDS: Dict[str, str] = {
    # Productivity / SaaS
    "notion": "Notion",
    "ramp": "Ramp",
    "brex": "Brex",
    "gusto": "Gusto",
    "lattice": "Lattice",
    "linear": "Linear",
    "loom": "Loom",
    "miro": "Miro",
    "calendly": "Calendly",
    "webflow": "Webflow",
    "airtable": "Airtable",
    # Developer tools / Infrastructure
    "vercel": "Vercel",
    "supabase": "Supabase",
    "clerk": "Clerk",
    "convex": "Convex",
    "neon": "Neon",
    "turso": "Turso",
    "planetscale": "PlanetScale",
    "prisma": "Prisma",
    "resend": "Resend",
    "trigger": "Trigger.dev",
    "inngest": "Inngest",
    "upstash": "Upstash",
    "tinybird": "Tinybird",
    # Data / Analytics
    "clickhouse": "ClickHouse",
    "weaviate": "Weaviate",
    "pinecone": "Pinecone",
    # AI / ML
    "cohere": "Cohere",
    "perplexity-ai": "Perplexity AI",
    "anthropic": "Anthropic",
    "stability-ai": "Stability AI",
    "hugging-face": "Hugging Face",
    "replicate": "Replicate",
    "together-ai": "Together AI",
    "anyscale": "Anyscale",
    "modal-labs": "Modal",
    # Data engineering
    "dbt-labs": "dbt Labs",
    "airbyte": "Airbyte",
    "dagster": "Dagster",
    "prefect": "Prefect",
    "temporal": "Temporal",
    # Cloud / DevOps
    "pulumi": "Pulumi",
    "fly": "Fly.io",
    "render": "Render",
    "railway": "Railway",
    # Observability / Developer experience
    "sentry": "Sentry",
    "highlight-io": "Highlight",
    "posthog": "PostHog",
    # Open source / Other
    "cal-com": "Cal.com",
    "appsmith": "Appsmith",
}

# ── Role keyword filters ────────────────────────────────────────────────────

ROLE_KEYWORDS = [
    # Engineering
    "engineer", "engineering", "developer", "software",
    "backend", "back-end", "frontend", "front-end", "fullstack", "full-stack",
    "platform", "infrastructure", "devops", "sre", "reliability",
    # Data
    "data", "analytics", "analyst", "database", "etl", "pipeline",
    "warehouse", "bi ", "business intelligence",
    # ML / AI
    "machine learning", "ml ", "ai ", "artificial intelligence",
    "deep learning", "nlp", "natural language", "computer vision",
    "research scientist", "applied scientist",
    # Python-adjacent
    "python", "django", "flask", "fastapi",
    # Security
    "security", "appsec", "infosec",
    # Leadership
    "cto", "vp engineering", "head of engineering",
    "engineering manager", "tech lead", "staff engineer",
    "principal engineer",
]

ROLE_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in ROLE_KEYWORDS),
    re.IGNORECASE,
)


# ── Parsing helpers ─────────────────────────────────────────────────────────

def _matches_role_filter(title: str) -> bool:
    """Return True if the job title matches any engineering/data/ML keyword."""
    return bool(ROLE_PATTERN.search(title))


def _parse_remote_type(job: Dict[str, Any]) -> Optional[RemoteType]:
    """Derive remote type from Ashby's isRemote and workplaceType fields."""
    is_remote = job.get("isRemote", False)
    workplace = (job.get("workplaceType") or "").lower()

    if workplace == "remote" or is_remote:
        return RemoteType.REMOTE
    if workplace == "hybrid":
        return RemoteType.HYBRID
    if workplace == "onsite" or workplace == "on-site":
        return RemoteType.ON_SITE

    # Fallback: if isRemote is explicitly False and no workplaceType
    if not is_remote and not workplace:
        return RemoteType.ON_SITE

    return None


def _parse_employment_type(employment_type: Optional[str]) -> Optional[JobType]:
    """Map Ashby's employmentType to our JobType enum."""
    if not employment_type:
        return None

    mapping = {
        "FullTime": JobType.FULL_TIME,
        "Full-Time": JobType.FULL_TIME,
        "PartTime": JobType.PART_TIME,
        "Part-Time": JobType.PART_TIME,
        "Contract": JobType.CONTRACT,
        "Temporary": JobType.TEMPORARY,
        "Intern": JobType.INTERNSHIP,
        "Internship": JobType.INTERNSHIP,
    }
    return mapping.get(employment_type)


def _parse_compensation(comp: Optional[Dict[str, Any]]) -> Tuple[
    Optional[float], Optional[float], str, str
]:
    """
    Parse Ashby compensation object into (min, max, currency, period).

    Ashby compensation format:
    {
        "compensationTierSummary": "$150K - $200K",
        "summaryComponents": [...],
        "compensationTiers": [{
            "title": "...",
            "tierFloor": 150000,
            "tierCeiling": 200000,
            "currency": "USD",
            "interval": "Year"
        }]
    }
    """
    if not comp:
        return None, None, "USD", "yearly"

    currency = "USD"
    period = "yearly"
    salary_min = None
    salary_max = None

    # Try structured tiers first
    tiers = comp.get("compensationTiers") or []
    if tiers:
        # Use the first tier (usually base salary)
        tier = tiers[0]
        salary_min = tier.get("tierFloor")
        salary_max = tier.get("tierCeiling")
        currency = tier.get("currency", "USD")
        interval = (tier.get("interval") or "").lower()
        if interval == "year":
            period = "yearly"
        elif interval == "month":
            period = "monthly"
        elif interval == "hour":
            period = "hourly"
        return salary_min, salary_max, currency, period

    # Fallback: parse the summary string
    summary = comp.get("compensationTierSummary", "")
    if summary:
        salary_min, salary_max = _parse_salary_from_text(summary)

    return salary_min, salary_max, currency, period


def _parse_salary_from_text(text: str) -> Tuple[Optional[float], Optional[float]]:
    """Extract salary range from text like '$150K - $200K' or '$130,000 - $180,000'."""
    patterns = [
        r'\$(\d{2,3})[kK]\s*[-–—to]+\s*\$?(\d{2,3})[kK]',
        r'\$(\d{1,3},?\d{3})\s*[-–—to]+\s*\$?(\d{1,3},?\d{3})',
        r'\$(\d{2,3})[kK]',
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                low = float(groups[0].replace(",", ""))
                high = float(groups[1].replace(",", ""))
                if low < 1000:
                    low *= 1000
                if high < 1000:
                    high *= 1000
                return low, high
            elif len(groups) == 1:
                val = float(groups[0].replace(",", ""))
                if val < 1000:
                    val *= 1000
                return val, None
    return None, None


def _parse_location(job: Dict[str, Any]) -> str:
    """Build a location string from Ashby's location fields."""
    # Ashby provides location as a string or structured object
    loc = job.get("location")
    if isinstance(loc, str) and loc:
        return loc

    # Some boards nest it differently
    address = job.get("address")
    if isinstance(address, dict):
        parts = []
        for key in ("city", "region", "country"):
            val = address.get(key)
            if val:
                parts.append(val)
        if parts:
            return ", ".join(parts)

    # Secondary location field
    secondary = job.get("secondaryLocations") or []
    if secondary:
        locs = []
        for s in secondary:
            if isinstance(s, str):
                locs.append(s)
            elif isinstance(s, dict) and s.get("location"):
                locs.append(s["location"])
        if locs:
            return "; ".join(locs)

    if job.get("isRemote"):
        return "Remote"

    return "See posting"


def _parse_posted_date(job: Dict[str, Any]) -> Optional[datetime]:
    """Parse the job's published/updated date."""
    for date_field in ("publishedAt", "updatedAt", "createdAt"):
        val = job.get(date_field)
        if val:
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                continue
    return None


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _build_job_listing(
    job: Dict[str, Any],
    company_name: str,
    board_name: str,
) -> JobListing:
    """Convert a single Ashby job object into a JobListing."""
    title = job.get("title", "Unknown Role")
    location = _parse_location(job)
    remote_type = _parse_remote_type(job)
    job_type = _parse_employment_type(job.get("employmentType"))

    # Description: Ashby provides HTML in "descriptionHtml" or plain in "descriptionPlain"
    description = job.get("descriptionPlain") or ""
    if not description:
        html_desc = job.get("descriptionHtml") or job.get("content") or ""
        description = _strip_html(html_desc)

    # Compensation
    comp = job.get("compensation") or job.get("compensationTierSummary")
    if isinstance(comp, str):
        # Sometimes it's just a summary string at top level
        salary_min, salary_max = _parse_salary_from_text(comp)
        salary_currency = "USD"
        salary_period = "yearly"
    elif isinstance(comp, dict):
        salary_min, salary_max, salary_currency, salary_period = _parse_compensation(comp)
    else:
        salary_min, salary_max, salary_currency, salary_period = None, None, "USD", "yearly"

    # Job URL: Ashby provides a hosted URL or we build one
    job_url = job.get("jobUrl") or job.get("hostedUrl") or ""
    if not job_url:
        job_id = job.get("id", "")
        job_url = f"https://jobs.ashbyhq.com/{board_name}/{job_id}"

    # Company page
    company_url = f"https://jobs.ashbyhq.com/{board_name}"

    posted_date = _parse_posted_date(job)

    return JobListing(
        title=title[:200],
        company=company_name,
        location=location[:200],
        description=description[:5000],
        job_url=job_url,
        job_id=f"ashby-{board_name}-{job.get('id', '')}",
        company_url=company_url,
        job_type=job_type,
        remote_type=remote_type,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
        salary_period=salary_period,
        posted_date=posted_date,
        source_site=JobSite.ASHBY,
        raw_data={
            "source": "ashby",
            "board_name": board_name,
            "ashby_id": job.get("id"),
            "department": job.get("department"),
            "team": job.get("team"),
            "employment_type": job.get("employmentType"),
            "workplace_type": job.get("workplaceType"),
            "is_remote": job.get("isRemote"),
        },
    )


# ── Async fetching ──────────────────────────────────────────────────────────

async def _fetch_board(
    session: aiohttp.ClientSession,
    board_name: str,
    company_name: str,
    filter_roles: bool = True,
) -> List[JobListing]:
    """Fetch and parse all jobs from a single Ashby board."""
    url = f"{ASHBY_API_BASE}/{board_name}?includeCompensation=true"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 404:
                logger.debug(f"Board not found: {board_name}")
                return []
            if resp.status == 429:
                logger.warning(f"Rate limited on board: {board_name}")
                return []
            if resp.status != 200:
                logger.warning(f"HTTP {resp.status} for board {board_name}")
                return []

            data = await resp.json()
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching board: {board_name}")
        return []
    except Exception as e:
        logger.error(f"Error fetching board {board_name}: {e}")
        return []

    raw_jobs = data.get("jobs", [])
    logger.debug(f"Board {board_name}: {len(raw_jobs)} total jobs")

    listings = []
    for job in raw_jobs:
        title = job.get("title", "")
        if filter_roles and not _matches_role_filter(title):
            continue

        try:
            listing = _build_job_listing(job, company_name, board_name)
            listings.append(listing)
        except Exception as e:
            logger.debug(f"Failed to parse job from {board_name}: {e}")

    return listings


async def _fetch_all_boards(
    boards: Dict[str, str],
    filter_roles: bool = True,
    rate_limit_delay: float = 0.5,
) -> List[JobListing]:
    """
    Fetch jobs from all boards with rate limiting between requests.

    We process boards sequentially with a delay to be respectful of the API,
    rather than blasting all requests concurrently.
    """
    if aiohttp is None:
        logger.error("aiohttp is required for Ashby scraper. Install with: pip install aiohttp")
        return []

    all_jobs: List[JobListing] = []

    async with aiohttp.ClientSession(
        headers={"Accept": "application/json", "User-Agent": "job-search-tool/1.0"},
    ) as session:
        for i, (board_name, company_name) in enumerate(boards.items()):
            if i > 0:
                await asyncio.sleep(rate_limit_delay)

            jobs = await _fetch_board(session, board_name, company_name, filter_roles)
            if jobs:
                logger.info(f"  {company_name}: {len(jobs)} matching roles")
                all_jobs.extend(jobs)

    return all_jobs


# ── Public API ──────────────────────────────────────────────────────────────

def scrape_ashby_jobs(
    boards: Optional[Dict[str, str]] = None,
    filter_roles: bool = True,
    rate_limit_delay: float = 0.5,
) -> List[JobListing]:
    """
    Scrape jobs from Ashby-powered job boards (synchronous wrapper).

    Args:
        boards: Dict mapping board_name -> display company name.
                Defaults to the curated TECH_COMPANY_BOARDS list.
        filter_roles: If True, only return engineering/data/ML roles.
        rate_limit_delay: Seconds to wait between API calls.

    Returns:
        List of parsed JobListing objects with source_site=JobSite.ASHBY.
    """
    if boards is None:
        boards = TECH_COMPANY_BOARDS

    logger.info(f"Scraping {len(boards)} Ashby job boards (filter_roles={filter_roles})")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already inside an async context — create a task via nest_asyncio or thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            jobs = pool.submit(
                asyncio.run,
                _fetch_all_boards(boards, filter_roles, rate_limit_delay),
            ).result()
    else:
        jobs = asyncio.run(
            _fetch_all_boards(boards, filter_roles, rate_limit_delay)
        )

    logger.info(f"Scraped {len(jobs)} jobs from Ashby boards")
    return jobs


async def scrape_ashby_jobs_async(
    boards: Optional[Dict[str, str]] = None,
    filter_roles: bool = True,
    rate_limit_delay: float = 0.5,
) -> List[JobListing]:
    """
    Scrape jobs from Ashby-powered job boards (async version).

    Args:
        boards: Dict mapping board_name -> display company name.
                Defaults to the curated TECH_COMPANY_BOARDS list.
        filter_roles: If True, only return engineering/data/ML roles.
        rate_limit_delay: Seconds to wait between API calls.

    Returns:
        List of parsed JobListing objects with source_site=JobSite.ASHBY.
    """
    if boards is None:
        boards = TECH_COMPANY_BOARDS

    logger.info(f"Scraping {len(boards)} Ashby job boards (filter_roles={filter_roles})")
    jobs = await _fetch_all_boards(boards, filter_roles, rate_limit_delay)
    logger.info(f"Scraped {len(jobs)} jobs from Ashby boards")
    return jobs


# ── CLI entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    jobs = scrape_ashby_jobs()
    print(f"\nFound {len(jobs)} matching jobs across {len(TECH_COMPANY_BOARDS)} companies\n")

    for i, job in enumerate(jobs[:25], 1):
        salary = job.get_salary_range_string()
        remote = f" [{job.remote_type.value}]" if job.remote_type else ""
        dept = job.raw_data.get("department") or ""
        dept_str = f" ({dept})" if dept else ""
        print(f"{i}. {job.title}{dept_str}")
        print(f"   Company: {job.company} | {job.location}{remote}")
        print(f"   Salary:  {salary}")
        print(f"   URL:     {job.job_url}")
        print()
