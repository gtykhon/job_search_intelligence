"""
Career Page Checker — Verify job postings against company career pages.

Three-phase verification:
  Phase 1: ATS Direct Lookup (free, structured)
    - Greenhouse Job Board API: boards-api.greenhouse.io
    - Lever Public API: api.lever.co
  Phase 2: Career Page Discovery + Probe (free)
    - Resolve company domain (from job URL or known patterns)
    - Probe common career page URLs (/careers, /jobs, etc.)
    - Lightweight title search on discovered page
  Phase 3: Search API Fallback (low cost, optional)
    - Serper.dev Google search API (2,500 free queries)

Populates GhostSignals.on_company_careers_page for ghost scoring.

Env vars:
  SERPER_API_KEY          — Serper.dev API key (optional, Phase 3)
  CAREER_CHECK_ENABLED    — Master switch (default: true)
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ── ATS URL patterns → board slug extraction ─────────────────────────────────

ATS_EXTRACTORS = {
    "greenhouse": {
        "url_pattern": re.compile(r"boards\.greenhouse\.io/([\w-]+)"),
        "api_url": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    },
    "lever": {
        "url_pattern": re.compile(r"jobs\.lever\.co/([\w-]+)"),
        "api_url": "https://api.lever.co/v0/postings/{slug}",
    },
}

# Common career page URL patterns to probe
CAREER_PAGE_PATHS = [
    "/careers",
    "/jobs",
    "/careers/openings",
    "/about/careers",
    "/join-us",
    "/work-with-us",
    "/open-positions",
    "/opportunities",
]

# ATS-hosted career page patterns (subdomain-based)
ATS_SUBDOMAIN_PATTERNS = [
    "careers.{domain}",
    "jobs.{domain}",
]

# Alternative domain patterns to try when .com is blocked/missing
ALT_DOMAIN_PATTERNS = [
    "{slug}.jobs",              # .jobs TLD (e.g., noblis.jobs)
    "www.{domain}",             # some sites require www
]


@dataclass
class CareerPageResult:
    """Result of career page verification for a single job."""
    found_on_career_page: Optional[bool] = None  # None = could not check
    verification_method: str = ""  # "greenhouse_api", "lever_api", "career_page_probe", "serper_search"
    career_page_url: Optional[str] = None
    matched_title: Optional[str] = None  # title found on career page
    match_confidence: float = 0.0  # 0-1 fuzzy match score
    ats_platform: Optional[str] = None
    board_slug: Optional[str] = None
    total_open_jobs: Optional[int] = None  # how many jobs the company has open
    checked_at: Optional[str] = None
    error: Optional[str] = None
    company_careers_url: Optional[str] = None  # actual company careers page (not ATS board)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "found_on_career_page": self.found_on_career_page,
            "verification_method": self.verification_method,
            "career_page_url": self.career_page_url,
            "matched_title": self.matched_title,
            "match_confidence": round(self.match_confidence, 2),
            "ats_platform": self.ats_platform,
            "board_slug": self.board_slug,
            "total_open_jobs": self.total_open_jobs,
            "checked_at": self.checked_at,
            "error": self.error,
            "company_careers_url": self.company_careers_url,
        }


# ── In-memory cache ──────────────────────────────────────────────────────────

_cache: Dict[str, CareerPageResult] = {}
_CACHE_TTL = timedelta(hours=24)
_cache_timestamps: Dict[str, datetime] = {}

# Cache for company domain → career page URL discovery
_career_page_cache: Dict[str, Optional[str]] = {}


class CareerPageChecker:
    """
    Verifies job postings against company career pages.

    Runs three phases in order, stopping at the first conclusive result.
    """

    def __init__(self, serper_api_key: str = "", enabled: bool = True):
        self.serper_api_key = serper_api_key
        self.enabled = enabled

    def _track_serper(self, endpoint: str = "search", success: bool = True, error: str = ""):
        """Log Serper API usage to the dashboard database."""
        try:
            from src.dashboard.db import DashboardDB
            db = DashboardDB()
            db.log_api_usage("serper", endpoint, success=success, error_message=error)
        except Exception:
            pass

    async def verify_job(
        self,
        job_title: str,
        company_name: str,
        job_url: str = "",
        company_domain: str = "",
        force: bool = False,
    ) -> CareerPageResult:
        """
        Verify a job posting against the company's career page.

        Tries Phase 1 (ATS API) → Phase 2 (career page probe) → Phase 3 (search).
        """
        if not self.enabled:
            return CareerPageResult(error="Career page checking disabled")

        cache_key = self._cache_key(job_title, company_name)
        if not force:
            cached = _cache.get(cache_key)
            if cached and datetime.now() - _cache_timestamps.get(cache_key, datetime.min) < _CACHE_TTL:
                return cached

        result = CareerPageResult(checked_at=datetime.now().isoformat())

        try:
            import aiohttp
        except ImportError:
            result.error = "aiohttp not installed"
            return result

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15.0)
        ) as session:
            # Helper: resolve company careers URL via Serper and attach to result
            async def _enrich_with_company_url(res: CareerPageResult) -> CareerPageResult:
                if self.serper_api_key and not res.company_careers_url:
                    resolved = await self._resolve_company_careers(session, company_name, job_title)
                    if resolved:
                        careers_url, is_exact_match = resolved
                        res.company_careers_url = careers_url
                        # If the result says "not found" but we have a company URL,
                        # check if it's a specific job posting (not just /careers).
                        # A URL like jobs.company.com/job/12345/Title is clearly
                        # a direct posting — override to FOUND.
                        if res.found_on_career_page is not True:
                            is_specific = is_exact_match or self._url_looks_like_job_posting(
                                careers_url, job_title
                            )
                            if is_specific:
                                logger.info(
                                    "Overriding career page result to FOUND — "
                                    "resolved specific job posting at %s", careers_url
                                )
                                res.found_on_career_page = True
                                res.verification_method = "serper_search"
                                res.career_page_url = careers_url
                                res.match_confidence = 0.90
                return res

            # Phase 1: ATS direct lookup
            ats_result = await self._phase1_ats_lookup(session, job_title, job_url, company_name)
            if ats_result and ats_result.found_on_career_page is not None:
                ats_result.checked_at = result.checked_at
                await _enrich_with_company_url(ats_result)
                _cache[cache_key] = ats_result
                _cache_timestamps[cache_key] = datetime.now()
                return ats_result

            # Phase 2: Career page probe
            domain = company_domain or self._extract_domain(job_url, company_name)
            if domain:
                probe_result = await self._phase2_career_page_probe(session, job_title, domain)
                if probe_result and probe_result.found_on_career_page is not None:
                    probe_result.checked_at = result.checked_at
                    await _enrich_with_company_url(probe_result)
                    _cache[cache_key] = probe_result
                    _cache_timestamps[cache_key] = datetime.now()
                    return probe_result

            # Phase 3: Search API fallback (works even without domain)
            if self.serper_api_key:
                search_result = await self._phase3_search_api(session, job_title, company_name, domain)
                if search_result and search_result.found_on_career_page is not None:
                    search_result.checked_at = result.checked_at
                    await _enrich_with_company_url(search_result)
                    _cache[cache_key] = search_result
                    _cache_timestamps[cache_key] = datetime.now()
                    return search_result

        # Could not verify
        result.error = "No verification method succeeded"
        _cache[cache_key] = result
        _cache_timestamps[cache_key] = datetime.now()
        return result

    # ── Phase 1: ATS Direct Lookup ────────────────────────────────────────────

    async def _phase1_ats_lookup(
        self, session, job_title: str, job_url: str, company_name: str
    ) -> Optional[CareerPageResult]:
        """Check Greenhouse and Lever public APIs for the job title."""
        for ats_name, config in ATS_EXTRACTORS.items():
            slug = self._extract_ats_slug(job_url, config["url_pattern"])
            if not slug:
                # Try to guess the slug from company name
                slug = self._guess_slug(company_name)

            if not slug:
                continue

            try:
                api_url = config["api_url"].format(slug=slug)
                async with session.get(api_url) as resp:
                    if resp.status == 404:
                        # Board doesn't exist — try next ATS
                        continue
                    if resp.status != 200:
                        logger.debug("%s API returned %d for slug '%s'", ats_name, resp.status, slug)
                        continue

                    data = await resp.json()

                    # Parse job list
                    if ats_name == "greenhouse":
                        jobs = data.get("jobs", [])
                        titles = [(j.get("title", ""), j.get("absolute_url", "")) for j in jobs]
                    elif ats_name == "lever":
                        jobs = data if isinstance(data, list) else []
                        titles = [(j.get("text", ""), j.get("hostedUrl", "")) for j in jobs]
                    else:
                        continue

                    if not titles:
                        return CareerPageResult(
                            found_on_career_page=False,
                            verification_method=f"{ats_name}_api",
                            ats_platform=ats_name,
                            board_slug=slug,
                            total_open_jobs=0,
                            career_page_url=api_url.replace("/v1/boards/", "/").replace("/v0/postings/", "/"),
                        )

                    # Fuzzy match job title
                    best_match, best_score, best_url = self._fuzzy_match_title(job_title, titles)

                    return CareerPageResult(
                        found_on_career_page=best_score >= 75,
                        verification_method=f"{ats_name}_api",
                        career_page_url=best_url or api_url,
                        matched_title=best_match if best_score >= 75 else None,
                        match_confidence=best_score / 100.0,
                        ats_platform=ats_name,
                        board_slug=slug,
                        total_open_jobs=len(titles),
                    )

            except Exception as exc:
                logger.debug("%s API lookup failed for '%s': %s", ats_name, slug, exc)
                continue

        return None

    # ── Phase 2: Career Page Discovery + Probe ────────────────────────────────

    async def _phase2_career_page_probe(
        self, session, job_title: str, domain: str
    ) -> Optional[CareerPageResult]:
        """Discover career page and search for job title."""
        career_url = await self._discover_career_page(session, domain)
        if not career_url:
            return None

        try:
            async with session.get(
                career_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; JobVerifier/1.0)"},
                allow_redirects=True,
            ) as resp:
                if resp.status != 200:
                    return None

                text = await resp.text()
                text_lower = text.lower()

                # If page is very short, it's likely a JS-rendered SPA
                # — treat as inconclusive so Phase 3 (search) can try
                visible_text_len = len(re.sub(r'<[^>]+>', '', text).strip())
                if visible_text_len < 500:
                    logger.debug("Career page %s has only %d chars of visible text (likely JS SPA), skipping",
                                 career_url, visible_text_len)
                    return None

                # Check if job title appears on the page
                title_lower = job_title.lower().strip()
                # Try exact match first
                if title_lower in text_lower:
                    return CareerPageResult(
                        found_on_career_page=True,
                        verification_method="career_page_probe",
                        career_page_url=career_url,
                        matched_title=job_title,
                        match_confidence=1.0,
                    )

                # Try fuzzy: split title into key words and check presence
                title_words = [w for w in title_lower.split() if len(w) > 3]
                if title_words:
                    word_hits = sum(1 for w in title_words if w in text_lower)
                    ratio = word_hits / len(title_words)
                    if ratio >= 0.7:
                        return CareerPageResult(
                            found_on_career_page=True,
                            verification_method="career_page_probe",
                            career_page_url=career_url,
                            match_confidence=ratio,
                        )

                # Title not found on career page
                return CareerPageResult(
                    found_on_career_page=False,
                    verification_method="career_page_probe",
                    career_page_url=career_url,
                    match_confidence=0.0,
                )

        except Exception as exc:
            logger.debug("Career page probe failed for %s: %s", career_url, exc)
            return None

    async def _discover_career_page(self, session, domain: str) -> Optional[str]:
        """Find the career page URL for a domain by probing common paths."""
        # Check cache
        if domain in _career_page_cache:
            return _career_page_cache[domain]

        # Extract slug (domain without TLD) for .jobs check
        slug = domain.split(".")[0] if "." in domain else domain

        # Try subdomain patterns first
        for pattern in ATS_SUBDOMAIN_PATTERNS:
            url = f"https://{pattern.format(domain=domain)}"
            if await self._url_exists(session, url):
                _career_page_cache[domain] = url
                return url

        # Try path patterns on both bare domain and www
        bases = [f"https://{domain}", f"https://www.{domain}"]
        for base in bases:
            for path in CAREER_PAGE_PATHS:
                url = f"{base}{path}"
                if await self._url_exists(session, url):
                    _career_page_cache[domain] = url
                    return url

        # Try alternative domain patterns (.jobs TLD, etc.)
        for pattern in ALT_DOMAIN_PATTERNS:
            url = f"https://{pattern.format(domain=domain, slug=slug)}"
            if await self._url_exists(session, url):
                _career_page_cache[domain] = url
                return url

        _career_page_cache[domain] = None
        return None

    async def _url_exists(self, session, url: str) -> bool:
        """Check if a URL returns 200 (HEAD first, then GET fallback for 403/405)."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            async with session.head(url, headers=headers, allow_redirects=True) as resp:
                if resp.status == 200:
                    return True
                if resp.status in (403, 405):
                    # Some sites block HEAD — try GET
                    async with session.get(url, headers=headers, allow_redirects=True) as resp2:
                        return resp2.status == 200
                return False
        except Exception:
            return False

    # ── Company Careers URL Resolution ────────────────────────────────────────

    async def _resolve_company_careers(self, session, company_name: str, job_title: str = "") -> Optional[Tuple[str, bool]]:
        """Use Serper to find the specific job listing on the company's own website.

        Returns (url, is_exact_job_match) or None.
        is_exact_job_match=True means Strategy 1 found the specific job posting.
        """
        job_boards = (
            "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
            "monster.com", "dice.com", "greenhouse.io", "lever.co", "ashbyhq.com",
            "wellfound.com", "usajobs.gov", "boards.greenhouse.io", "job-boards.greenhouse.io",
            "jobs.lever.co", "theladders.com", "simplyhired.com", "careerbuilder.com",
            "salary.com", "builtin.com", "flexjobs.com", "remote.co", "weworkremotely.com",
            "stackoverflow.com", "hired.com", "angel.co", "jobvite.com", "workday.com",
            "icims.com", "smartrecruiters.com", "myworkdayjobs.com", "ultipro.com",
            "remotive.com", "otta.com", "levels.fyi", "triplebyte.com", "talent.com",
            "jooble.org", "neuvoo.com", "lensa.com", "adzuna.com", "reed.co.uk",
            "totaljobs.com", "cwjobs.co.uk", "nextleveljobs.eu",
        )

        async def _serper(query: str) -> list:
            try:
                async with session.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": 5},
                ) as resp:
                    if resp.status != 200:
                        self._track_serper("resolve_careers", success=False)
                        return []
                    data = await resp.json()
                    self._track_serper("resolve_careers", success=True)
                    return data.get("organic", [])
            except Exception as exc:
                logger.debug("Serper lookup failed: %s", exc)
                self._track_serper("resolve_careers", success=False, error=str(exc))
                return []

        def _get_domain(url: str) -> str:
            try:
                from urllib.parse import urlparse
                return urlparse(url).netloc.lower()
            except Exception:
                return url.lower()

        company_slug = company_name.lower().split()[0]

        # Strategy 1: find the specific job on the company site (strict — domain must match)
        if job_title:
            results = await _serper(f'"{job_title}" {company_name} apply')
            for r in results:
                link = r.get("link", "")
                if company_slug in _get_domain(link):
                    return (link, True)  # exact job match on company site

        # Strategy 2: company careers page (broader — allow any non-job-board)
        results = await _serper(f"{company_name} careers jobs")
        for r in results:
            link = r.get("link", "")
            if company_slug in _get_domain(link):
                return (link, False)  # generic careers page
        for r in results:
            link = r.get("link", "")
            if not any(jb in link.lower() for jb in job_boards):
                return (link, False)
        return None

    # ── Phase 3: Search API Fallback ──────────────────────────────────────────

    async def _phase3_search_api(
        self, session, job_title: str, company_name: str, domain: str
    ) -> Optional[CareerPageResult]:
        """Use Serper.dev to search for the job — site-scoped first, then broader."""
        if not self.serper_api_key:
            return None

        async def _serper_query(query: str) -> list:
            try:
                async with session.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": 5},
                ) as resp:
                    if resp.status != 200:
                        logger.debug("Serper API returned %d for query: %s", resp.status, query)
                        self._track_serper("phase3_search", success=False)
                        return []
                    data = await resp.json()
                    self._track_serper("phase3_search", success=True)
                    return data.get("organic", [])
            except Exception as exc:
                logger.debug("Serper query failed: %s", exc)
                self._track_serper("phase3_search", success=False, error=str(exc))
                return []

        try:
            # Strategy 1: exact title on company domain (if we have one)
            results = []
            if domain:
                results = await _serper_query(f'"{job_title}" site:{domain}')

            # Strategy 2: exact title + company name (broader — catches .jobs, LinkedIn, etc.)
            if not results:
                results = await _serper_query(f'"{job_title}" {company_name} careers')

            if results:
                # Check if any result is on the company's own domain (strong signal)
                company_slug = domain.split(".")[0].lower() if domain else company_name.lower().split()[0]
                company_results = [
                    r for r in results
                    if company_slug in r.get("link", "").lower()
                    and not any(jb in r.get("link", "") for jb in (
                        "linkedin.com", "indeed.com", "glassdoor.com",
                        "ziprecruiter.com", "monster.com", "dice.com",
                    ))
                ]
                if company_results:
                    top = company_results[0]
                    return CareerPageResult(
                        found_on_career_page=True,
                        verification_method="serper_search",
                        career_page_url=top.get("link", ""),
                        matched_title=top.get("title", ""),
                        match_confidence=0.90,
                    )

                # Found on job boards but NOT on company site — weak negative signal
                # (job exists publicly but company doesn't show it on their own page)
                top = results[0]
                return CareerPageResult(
                    found_on_career_page=False,
                    verification_method="serper_search",
                    career_page_url=top.get("link", ""),
                    matched_title=top.get("title", ""),
                    match_confidence=0.0,
                    error="Found on job boards but not on company career page",
                )
            else:
                return CareerPageResult(
                    found_on_career_page=False,
                    verification_method="serper_search",
                    match_confidence=0.0,
                )

        except Exception as exc:
            logger.debug("Serper search failed: %s", exc)
            return None

    # ── Sync wrapper ──────────────────────────────────────────────────────────

    def verify_job_sync(
        self,
        job_title: str,
        company_name: str,
        job_url: str = "",
        company_domain: str = "",
    ) -> CareerPageResult:
        """Synchronous wrapper around verify_job."""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.verify_job(job_title, company_name, job_url, company_domain)
                )
            finally:
                loop.close()
        except Exception as exc:
            logger.debug("verify_job_sync failed: %s", exc)
            return CareerPageResult(error=str(exc))

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_ats_slug(url: str, pattern: re.Pattern) -> Optional[str]:
        """Extract board slug from a job URL using an ATS pattern."""
        if not url:
            return None
        match = pattern.search(url)
        return match.group(1) if match else None

    @staticmethod
    def _guess_slug(company_name: str) -> Optional[str]:
        """Guess ATS board slug from company name."""
        if not company_name:
            return None
        # Normalize: lowercase, strip legal suffixes, replace spaces with hyphens
        slug = company_name.lower().strip()
        slug = re.sub(r",?\s*\b(inc\.?|llc|corp\.?|ltd\.?|co\.?)\b\.?", "", slug, flags=re.IGNORECASE)
        slug = re.sub(r"\s*\([^)]*\)", "", slug)  # remove parentheticals
        slug = re.sub(r"[^a-z0-9]+", "", slug).strip()  # keep only alphanum
        return slug if slug else None

    @staticmethod
    def _extract_domain(job_url: str, company_name: str) -> Optional[str]:
        """Extract or guess the company domain from the job URL or name."""
        if job_url:
            parsed = urlparse(job_url)
            host = parsed.hostname or ""
            # If it's a job board URL (linkedin, indeed), can't extract company domain
            if any(jb in host for jb in ("linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com")):
                pass
            elif host:
                # Could be company site or ATS
                if any(ats in host for ats in ("greenhouse.io", "lever.co", "myworkdayjobs.com", "ashbyhq.com")):
                    pass
                else:
                    return host

        # Fallback: guess domain from company name
        if company_name:
            name = company_name.lower().strip()
            # Strip legal suffixes
            name = re.sub(r",?\s*\b(inc\.?|llc|corp\.?|ltd\.?|co\.?|incorporated|limited)\b\.?", "", name, flags=re.IGNORECASE)
            name = re.sub(r"\s*\([^)]*\)", "", name)  # remove parentheticals
            name = name.strip().strip(",").strip()
            # Remove common modifiers that aren't part of the domain
            name = re.sub(r"\b(web services|technologies|technology|solutions|consulting|group|holdings)\b", "", name, flags=re.IGNORECASE)
            name = name.strip()
            # Simple: try {name}.com
            # For single-word names: "SAIC" → "saic.com", "Amazon" → "amazon.com"
            # For multi-word: "Goldman Sachs" → "goldmansachs.com"
            slug = re.sub(r"[^a-z0-9]+", "", name)
            if slug and len(slug) >= 2:
                return f"{slug}.com"

        return None

    @staticmethod
    def _fuzzy_match_title(
        target: str, candidates: List[Tuple[str, str]]
    ) -> Tuple[str, float, str]:
        """
        Fuzzy match a job title against a list of (title, url) candidates.
        Returns (best_title, best_score, best_url).
        """
        try:
            from rapidfuzz import fuzz
        except ImportError:
            # Fallback to simple substring matching
            target_lower = target.lower().strip()
            for title, url in candidates:
                if target_lower in title.lower() or title.lower() in target_lower:
                    return title, 90.0, url
            return ("", 0.0, "")

        best_title = ""
        best_score = 0.0
        best_url = ""
        target_lower = target.lower().strip()

        for title, url in candidates:
            score = fuzz.token_set_ratio(target_lower, title.lower().strip())
            if score > best_score:
                best_score = score
                best_title = title
                best_url = url

        return best_title, best_score, best_url

    @staticmethod
    def _url_looks_like_job_posting(url: str, job_title: str = "") -> bool:
        """Heuristic: does this URL look like a specific job posting, not a generic careers page?

        Checks for job ID patterns in the path and title keywords in the URL slug.
        e.g., jobs.cvshealth.com/us/en/job/R0838696/Senior-DevSecOps-Engineer → True
              cvshealth.com/careers → False
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.lower().rstrip("/")

            # Generic career page paths — NOT a specific posting
            generic_paths = {"/careers", "/jobs", "/join-us", "/work-with-us",
                            "/open-positions", "/opportunities", "/about/careers"}
            if path in generic_paths or not path or path == "/":
                return False

            # Job ID pattern in URL (e.g., /R0838696, /12345, /job/abc-123)
            if re.search(r'/[A-Z]?\d{4,}', parsed.path):
                return True

            # URL contains "job/" or "position/" with further path segments
            if re.search(r'/(job|position|posting|opening|requisition)/', path):
                return True

            # Title keywords in URL slug (≥3 significant words match)
            if job_title:
                title_words = [w.lower() for w in job_title.split() if len(w) > 3]
                url_lower = url.lower().replace("-", " ").replace("_", " ")
                hits = sum(1 for w in title_words if w in url_lower)
                if title_words and hits >= min(3, len(title_words)):
                    return True

            return False
        except Exception:
            return False

    @staticmethod
    def _cache_key(job_title: str, company_name: str) -> str:
        raw = f"{job_title.lower().strip()}|{company_name.lower().strip()}"
        return hashlib.md5(raw.encode()).hexdigest()


# ── Singleton ─────────────────────────────────────────────────────────────────

_checker: Optional[CareerPageChecker] = None


def get_career_page_checker() -> CareerPageChecker:
    """Get or create the global CareerPageChecker (configured from env)."""
    global _checker
    if _checker is None:
        import os
        _checker = CareerPageChecker(
            serper_api_key=os.getenv("SERPER_API_KEY", ""),
            enabled=os.getenv("CAREER_CHECK_ENABLED", "true").lower() != "false",
        )
    return _checker
