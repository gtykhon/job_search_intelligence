"""
Greenhouse Job Board Scraper

Scrapes job postings from the free, public Greenhouse Job Board API.
No authentication required — these are public company career pages.

API endpoints:
  - List jobs:   GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true&pay_transparency=true
  - Job detail:  GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}

Rate-limits are generous; we add a 0.5s delay between companies as courtesy.
"""

import re
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import aiohttp

from .models import JobListing, JobSite, RemoteType, ExperienceLevel

logger = logging.getLogger(__name__)

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"

# ── Curated board tokens ────────────────────────────────────────────────────
# Not every token maps to a live Greenhouse board — 404s are silently skipped.

BOARD_TOKENS: Dict[str, str] = {
    # Developer tools & platforms
    "gitlab": "GitLab",
    "cloudflare": "Cloudflare",
    "twitch": "Twitch",
    "figma": "Figma",
    "notion": "Notion",
    "airtable": "Airtable",
    "retool": "Retool",
    "vercel": "Vercel",
    "supabase": "Supabase",
    "planetscale": "PlanetScale",
    "neon": "Neon",
    "linear": "Linear",
    "posthog": "PostHog",
    "cal": "Cal.com",
    "highlight-io": "Highlight",
    "axiom": "Axiom",
    "replit": "Replit",
    "render": "Render",
    "fly": "Fly.io",
    "railway": "Railway",
    # Data & orchestration
    "dagster": "Dagster",
    "prefecthq": "Prefect",
    "modal": "Modal",
    "anyscale": "Anyscale",
    "dbt-labs": "dbt Labs",
    "airbyte": "Airbyte",
    "meltano": "Meltano",
    "rudderstack": "RudderStack",
    "segment": "Segment",
    # Fintech
    "brex": "Brex",
    "ramp": "Ramp",
    "mercury": "Mercury",
    "plaid": "Plaid",
    "stripe": "Stripe",
    "coinbase": "Coinbase",
    # Data infrastructure
    "databricks": "Databricks",
    "snowflakecomputing": "Snowflake",
    "hashicorp": "HashiCorp",
    "elastic": "Elastic",
    "grafanalabs": "Grafana Labs",
    "temporal": "Temporal",
    "cockroachlabs": "Cockroach Labs",
    "singlestore": "SingleStore",
    "timescale": "Timescale",
    "clickhouse": "ClickHouse",
    "materialize": "Materialize",
    "starburst": "Starburst",
    "duckdb": "DuckDB",
    "motherduck": "MotherDuck",
    # AI / ML / vector
    "weaviate": "Weaviate",
    "pinecone": "Pinecone",
    "qdrant": "Qdrant",
    "cohere": "Cohere",
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "huggingface": "Hugging Face",
    "together": "Together AI",
    "mistral": "Mistral AI",
}


# ── Role filter keywords ───────────────────────────────────────────────────

TITLE_KEYWORDS = re.compile(
    r"(?i)\b("
    r"engineer|developer|architect|scientist|analyst|sre|swe|devops|"
    r"data|machine.?learning|ml\b|ai\b|python|backend|back.?end|"
    r"full.?stack|platform|infrastructure|cloud|"
    r"software|systems|reliability|applied|research|"
    r"quant|nlp|llm|deep.?learning|computer.?vision|mlops|"
    r"frontend|front.?end"
    r")\b"
)

CLEARANCE_KEYWORDS = re.compile(
    r"(?i)\b("
    r"security.?clearance|secret|top.?secret|ts/sci|"
    r"public.?trust|dod|government.?clearance|sci|"
    r"clearance.?required|cleared|polygraph"
    r")\b"
)


# ── HTML stripping ──────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"&\w+;", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── Parsing helpers ─────────────────────────────────────────────────────────

def _parse_remote_type(location_name: str, offices: List[Dict]) -> Optional[RemoteType]:
    """Detect remote/hybrid/onsite from Greenhouse location and office data."""
    loc_lower = location_name.lower() if location_name else ""

    if "remote" in loc_lower and "hybrid" in loc_lower:
        return RemoteType.HYBRID
    if "remote" in loc_lower:
        return RemoteType.REMOTE
    if "hybrid" in loc_lower:
        return RemoteType.HYBRID

    # Check office names for hints
    for office in offices:
        name = (office.get("name") or "").lower()
        if "remote" in name:
            return RemoteType.REMOTE
        if "hybrid" in name:
            return RemoteType.HYBRID

    # If there are physical offices and no remote signal, assume on-site
    if offices:
        return RemoteType.ON_SITE

    return None


def _parse_salary(pay: Optional[Dict]) -> Tuple[Optional[float], Optional[float], str, str]:
    """
    Parse the Greenhouse pay_transparency pay object.

    Returns (salary_min, salary_max, currency, period).
    The API returns amounts in cents (or sub-units), so divide by 100.
    """
    if not pay:
        return None, None, "USD", "yearly"

    currency = pay.get("currency", "USD") or "USD"

    # Determine period from interval
    interval = (pay.get("interval") or "").lower()
    period_map = {
        "year": "yearly",
        "month": "monthly",
        "week": "weekly",
        "hour": "hourly",
    }
    period = period_map.get(interval, "yearly")

    min_cents = pay.get("min")
    max_cents = pay.get("max")

    salary_min = float(min_cents) / 100.0 if min_cents is not None else None
    salary_max = float(max_cents) / 100.0 if max_cents is not None else None

    return salary_min, salary_max, currency, period


def _parse_experience_level(title: str) -> Optional[ExperienceLevel]:
    """Infer experience level from job title."""
    lower = title.lower()
    if re.search(r"\b(principal|staff|distinguished)\b", lower):
        return ExperienceLevel.SENIOR
    if re.search(r"\b(senior|sr\.?|lead)\b", lower):
        return ExperienceLevel.SENIOR
    if re.search(r"\b(mid|intermediate|ii|iii)\b", lower):
        return ExperienceLevel.MID
    if re.search(r"\b(junior|jr\.?|entry|intern|new.?grad|associate|i\b)", lower):
        return ExperienceLevel.ENTRY
    if re.search(r"\b(director|vp|vice.?president|head of|chief)\b", lower):
        return ExperienceLevel.DIRECTOR
    return None


def _detect_clearance(text: str) -> Optional[str]:
    """Check description for security clearance requirements."""
    match = CLEARANCE_KEYWORDS.search(text)
    if not match:
        return None
    token = match.group(0).lower()
    if "ts/sci" in token or "top secret" in token.replace(" ", ""):
        return "top_secret"
    if "secret" in token:
        return "secret"
    if "public trust" in token.replace(" ", ""):
        return "public_trust"
    return "required"


def _build_location_string(location_name: str, offices: List[Dict]) -> str:
    """Build a human-readable location from Greenhouse fields."""
    if location_name:
        return location_name

    if offices:
        names = [o.get("name", "") for o in offices if o.get("name")]
        if names:
            return " / ".join(names[:3])

    return "See posting"


# ── Async fetching ──────────────────────────────────────────────────────────

async def _fetch_board_jobs(
    session: aiohttp.ClientSession,
    board_token: str,
    company_name: str,
) -> List[Dict[str, Any]]:
    """Fetch all jobs from a single Greenhouse board. Returns raw job dicts."""
    url = f"{GREENHOUSE_API_BASE}/{board_token}/jobs?content=true&pay_transparency=true"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status == 404:
                logger.debug(f"No Greenhouse board for {company_name} ({board_token})")
                return []
            if resp.status == 429:
                logger.warning(f"Rate-limited on {company_name} board — skipping")
                return []
            if resp.status != 200:
                logger.warning(f"HTTP {resp.status} for {company_name} board")
                return []

            data = await resp.json()
            jobs = data.get("jobs", [])
            if jobs:
                logger.info(f"Fetched {len(jobs)} jobs from {company_name} ({board_token})")
            return jobs

    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {company_name} board")
        return []
    except Exception as e:
        logger.error(f"Error fetching {company_name} board: {e}")
        return []


# ── Job parsing ─────────────────────────────────────────────────────────────

def _parse_job(
    raw: Dict[str, Any],
    board_token: str,
    company_name: str,
) -> Optional[JobListing]:
    """Parse a single Greenhouse job dict into a JobListing."""
    title = raw.get("title", "").strip()
    if not title:
        return None

    # Filter by role keywords
    if not TITLE_KEYWORDS.search(title):
        return None

    # Location
    location_obj = raw.get("location", {}) or {}
    location_name = location_obj.get("name", "")
    offices = raw.get("offices", []) or []
    location = _build_location_string(location_name, offices)

    # Description
    raw_content = raw.get("content", "")
    description = _strip_html(raw_content) if raw_content else ""

    # Salary from pay_transparency fields
    pay_input_ranges = raw.get("pay_input_ranges", [])
    salary_min, salary_max, salary_currency, salary_period = None, None, "USD", "yearly"
    if pay_input_ranges:
        # Use the first pay range (usually the primary one)
        salary_min, salary_max, salary_currency, salary_period = _parse_salary(
            pay_input_ranges[0]
        )
    else:
        # Try top-level pay field (older API format)
        salary_min, salary_max, salary_currency, salary_period = _parse_salary(
            raw.get("pay")
        )

    # Remote type
    remote_type = _parse_remote_type(location_name, offices)

    # Experience level
    experience_level = _parse_experience_level(title)

    # Clearance
    clearance = _detect_clearance(description)

    # Posted date
    posted_date = None
    updated_at = raw.get("updated_at") or raw.get("created_at")
    if updated_at:
        try:
            posted_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except (ValueError, TypeError):
            pass

    # Job URL — Greenhouse public job page
    job_id = raw.get("id", "")
    job_url = raw.get("absolute_url", "")
    if not job_url:
        job_url = f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}"

    # Departments
    departments = raw.get("departments", []) or []
    dept_names = [d.get("name", "") for d in departments if d.get("name")]

    return JobListing(
        title=title[:200],
        company=company_name,
        location=location[:200],
        description=description[:5000],
        job_url=job_url,
        job_id=f"gh-{board_token}-{job_id}",
        remote_type=remote_type,
        experience_level=experience_level,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
        salary_period=salary_period,
        posted_date=posted_date,
        source_site=JobSite.GREENHOUSE,
        clearance_required=clearance,
        company_url=f"https://boards.greenhouse.io/{board_token}",
        company_industry="Technology",
        raw_data={
            "source": "greenhouse",
            "board_token": board_token,
            "greenhouse_job_id": job_id,
            "departments": dept_names,
            "offices": [o.get("name") for o in offices if o.get("name")],
        },
    )


# ── Public API ──────────────────────────────────────────────────────────────

async def scrape_greenhouse_jobs_async(
    board_tokens: Optional[Dict[str, str]] = None,
    delay_between_boards: float = 0.5,
    title_filter: Optional[re.Pattern] = None,
) -> List[JobListing]:
    """
    Scrape jobs from Greenhouse public job board API (async).

    Args:
        board_tokens: Dict mapping board_token -> company display name.
                      Defaults to the curated BOARD_TOKENS list.
        delay_between_boards: Seconds to wait between API calls (rate-limit courtesy).
        title_filter: Optional compiled regex to override the default TITLE_KEYWORDS filter.

    Returns:
        List of parsed JobListing objects with source_site=GREENHOUSE.
    """
    tokens = board_tokens or BOARD_TOKENS
    if title_filter is not None:
        global TITLE_KEYWORDS
        TITLE_KEYWORDS = title_filter

    all_jobs: List[JobListing] = []
    boards_with_jobs = 0
    boards_skipped = 0

    logger.info(f"Starting Greenhouse scrape across {len(tokens)} boards")

    async with aiohttp.ClientSession(
        headers={"Accept": "application/json", "User-Agent": "JobSearchBot/1.0"},
    ) as session:
        for board_token, company_name in tokens.items():
            raw_jobs = await _fetch_board_jobs(session, board_token, company_name)

            if not raw_jobs:
                boards_skipped += 1
                await asyncio.sleep(delay_between_boards)
                continue

            boards_with_jobs += 1
            parsed_count = 0

            for raw_job in raw_jobs:
                try:
                    listing = _parse_job(raw_job, board_token, company_name)
                    if listing:
                        all_jobs.append(listing)
                        parsed_count += 1
                except Exception as e:
                    logger.debug(
                        f"Failed to parse Greenhouse job from {company_name}: {e}"
                    )

            logger.info(
                f"  {company_name}: {parsed_count} matching roles out of {len(raw_jobs)} total"
            )
            await asyncio.sleep(delay_between_boards)

    logger.info(
        f"Greenhouse scrape complete: {len(all_jobs)} jobs from "
        f"{boards_with_jobs} boards ({boards_skipped} boards skipped/empty)"
    )
    return all_jobs


def scrape_greenhouse_jobs(
    board_tokens: Optional[Dict[str, str]] = None,
    delay_between_boards: float = 0.5,
    title_filter: Optional[re.Pattern] = None,
) -> List[JobListing]:
    """
    Synchronous wrapper around the async Greenhouse scraper.

    Safe to call from non-async code. Creates its own event loop if needed.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already inside an event loop — create a new one in a thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                asyncio.run,
                scrape_greenhouse_jobs_async(board_tokens, delay_between_boards, title_filter),
            )
            return future.result()
    else:
        return asyncio.run(
            scrape_greenhouse_jobs_async(board_tokens, delay_between_boards, title_filter)
        )


# ── CLI entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    jobs = scrape_greenhouse_jobs()
    print(f"\nFound {len(jobs)} matching jobs across Greenhouse boards\n")

    for i, job in enumerate(jobs[:25], 1):
        salary = job.get_salary_range_string()
        remote = f" [{job.remote_type.value}]" if job.remote_type else ""
        level = f" ({job.experience_level.value})" if job.experience_level else ""
        clearance = f" [CLEARANCE: {job.clearance_required}]" if job.clearance_required else ""
        print(f"{i:>3}. {job.title}{level}")
        print(f"     {job.company} | {job.location}{remote}{clearance}")
        print(f"     {salary}")
        print(f"     {job.job_url}")
        print()
