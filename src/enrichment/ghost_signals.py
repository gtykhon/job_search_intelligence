"""
Ghost Signal Collector -- Multi-layer ghost job detection.

Replicates WhenThisJobWasPosted + GhostCheck methodology using free sources:

Signal sources (all free):
  1. JSON-LD datePosted extraction from job page
  2. Wayback Machine CDX API -- URL first-capture date
  3. Repost detection -- description hashing + rapidfuzz near-duplicate
  4. Ghost language patterns (expanded)
  5. Vague description scoring (specificity markers vs generic phrases)
  6. ATS career page cross-reference (Greenhouse, Lever, Workday patterns)

Composite ghost score: weighted 0.0-1.0 heuristic.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# -- Ghost language (expanded) --

GHOST_LANGUAGE = {
    "talent community", "talent pipeline", "future opportunities",
    "no immediate openings", "building our team for", "pool of candidates",
    "general application", "we are always looking", "evergreen requisition",
    "proactive sourcing", "talent pool", "ongoing recruitment",
    "continuous hiring", "we're always hiring", "rolling basis",
    "no specific opening", "speculative application",
}

# -- Vague description signals --

VAGUE_PHRASES = {
    "dynamic environment", "motivated self-starter", "fast-paced",
    "exciting opportunity", "competitive compensation", "great benefits",
    "industry leader", "growing company", "collaborative culture",
    "make an impact", "work hard play hard", "like a family",
    "flexible work", "cutting-edge", "innovative solutions",
    "wear many hats", "various duties as assigned", "other duties",
}

SPECIFICITY_MARKERS = {
    # Tech stacks, tools, versions
    r'python\s*3', r'react\s*\d+', r'typescript', r'kubernetes',
    r'postgresql', r'terraform', r'docker', r'airflow', r'dbt',
    r'aws|gcp|azure', r'ci/cd', r'graphql', r'grpc',
    # Team/org details
    r'team of \d+', r'reporting to', r'direct reports',
    r'series [a-e]', r'\d+ engineers', r'squad',
    # Project details
    r'microservices', r'data pipeline', r'real.time',
    r'distributed system', r'event.driven', r'api gateway',
    # Quantified impact
    r'\d+\s*%', r'\$[\d,.]+', r'\d+[MmKk]\+?\s+(users|requests|records|events)',
}

# -- ATS URL patterns --

ATS_PATTERNS = {
    'greenhouse': r'boards\.greenhouse\.io/[\w-]+',
    'lever': r'jobs\.lever\.co/[\w-]+',
    'workday': r'[\w-]+\.wd\d+\.myworkdayjobs\.com',
    'ashby': r'jobs\.ashbyhq\.com/[\w-]+',
    'bamboohr': r'[\w-]+\.bamboohr\.com/careers',
    'icims': r'[\w-]+\.icims\.com/jobs',
    'smartrecruiters': r'[\w-]+\.smartrecruiters\.com',
    'jazz': r'[\w-]+\.applytojob\.com',
}


@dataclass
class GhostSignals:
    """Collected ghost signals for a single job posting."""
    posting_age_days: Optional[int] = None
    has_salary: bool = False
    applicant_count: Optional[int] = None
    is_reposted: bool = False
    repost_count: int = 0
    description_specificity: float = 0.5  # 0=vague, 1=specific
    on_company_careers_page: Optional[bool] = None  # None = not checked
    easy_apply: bool = False
    ghost_language_hits: List[str] = field(default_factory=list)
    json_ld_date: Optional[str] = None
    wayback_first_seen: Optional[str] = None
    wayback_vs_posted_days: Optional[int] = None  # positive = repost signal
    description_hash: str = ""
    near_duplicate_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'posting_age_days': self.posting_age_days,
            'has_salary': self.has_salary,
            'applicant_count': self.applicant_count,
            'is_reposted': self.is_reposted,
            'repost_count': self.repost_count,
            'description_specificity': round(self.description_specificity, 2),
            'on_company_careers_page': self.on_company_careers_page,
            'easy_apply': self.easy_apply,
            'ghost_language_hits': self.ghost_language_hits,
            'json_ld_date': self.json_ld_date,
            'wayback_first_seen': self.wayback_first_seen,
            'wayback_vs_posted_days': self.wayback_vs_posted_days,
            'description_hash': self.description_hash,
        }


def compute_ghost_score(s: GhostSignals) -> float:
    """
    Weighted composite ghost score (0.0 = definitely real, 1.0 = definitely ghost).

    Weights per GhostCheck methodology + WhenThisJobWasPosted repost detection.
    """
    score = 0.0

    # Posting age
    if s.posting_age_days is not None:
        if s.posting_age_days > 45:
            score += 0.25
        elif s.posting_age_days > 30:
            score += 0.15

    # No salary listed (weak signal)
    if not s.has_salary:
        score += 0.05

    # High applicant count (LinkedIn signal)
    if s.applicant_count is not None:
        if s.applicant_count > 500:
            score += 0.20
        elif s.applicant_count > 200:
            score += 0.15

    # Reposted (strong signal)
    if s.is_reposted:
        score += 0.20

    # Repost count compounds the signal
    if s.repost_count >= 3:
        score += 0.15
    elif s.repost_count >= 2:
        score += 0.08

    # Vague description
    if s.description_specificity < 0.3:
        score += 0.10
    elif s.description_specificity < 0.2:
        score += 0.15

    # Not found on company careers page (strong signal)
    if s.on_company_careers_page is False:
        score += 0.20

    # Easy Apply (very weak signal)
    if s.easy_apply:
        score += 0.03

    # Ghost language in JD
    if len(s.ghost_language_hits) > 0:
        score += 0.15

    # Wayback vs posted date discrepancy (repost detection -- strongest signal)
    if s.wayback_vs_posted_days is not None and s.wayback_vs_posted_days > 30:
        score += 0.20

    return min(score, 1.0)


class GhostSignalCollector:
    """
    Collects ghost signals from multiple free sources.

    Operates in two modes:
      - Lightweight (default): local analysis only -- JD text, dates, hashing
      - Full enrichment: adds Wayback Machine and JSON-LD HTTP calls
    """

    def __init__(self, enable_http_checks: bool = False):
        self.enable_http_checks = enable_http_checks

    def collect_local_signals(self, job) -> GhostSignals:
        """Collect signals from local data only (no HTTP calls)."""
        signals = GhostSignals()

        # 1. Posting age
        posted_date = getattr(job, 'posted_date', None)
        if posted_date:
            if isinstance(posted_date, str):
                try:
                    posted_date = datetime.fromisoformat(posted_date)
                except ValueError:
                    posted_date = None
            if posted_date:
                signals.posting_age_days = (datetime.now() - posted_date).days

        # 2. Salary check
        salary_min = getattr(job, 'salary_min', None)
        salary_max = getattr(job, 'salary_max', None)
        signals.has_salary = salary_min is not None or salary_max is not None

        # 3. Applicant count
        num_applicants = getattr(job, 'num_applicants', None)
        if num_applicants is None:
            raw = getattr(job, 'raw_data', None) or {}
            num_applicants = raw.get('num_applicants')
        if num_applicants is not None:
            signals.applicant_count = int(num_applicants)

        # 4. Easy apply detection
        raw = getattr(job, 'raw_data', None) or {}
        signals.easy_apply = bool(raw.get('easy_apply') or raw.get('is_easy_apply'))

        # 5. Ghost language
        jd_lower = (getattr(job, 'description', '') or '').lower()
        signals.ghost_language_hits = [p for p in GHOST_LANGUAGE if p in jd_lower]

        # 6. Description specificity
        signals.description_specificity = self._score_specificity(jd_lower)

        # 7. Description hash (for repost detection)
        signals.description_hash = self._hash_description(jd_lower)

        # 8. Repost detection from raw_data (if scraper provided it)
        if raw.get('is_reposted'):
            signals.is_reposted = True

        return signals

    async def collect_all_signals(self, job) -> GhostSignals:
        """Collect all signals including HTTP-based checks."""
        signals = self.collect_local_signals(job)

        if self.enable_http_checks:
            job_url = getattr(job, 'job_url', None)
            if job_url:
                # JSON-LD extraction
                json_ld_date = await self._extract_json_ld_date(job_url)
                if json_ld_date:
                    signals.json_ld_date = json_ld_date

                # Wayback Machine CDX
                wayback_date = await self._wayback_first_seen(job_url)
                if wayback_date:
                    signals.wayback_first_seen = wayback_date

                    # Detect repost: Wayback saw it much earlier than posted date claims
                    if signals.posting_age_days is not None:
                        try:
                            wb_dt = datetime.strptime(wayback_date[:8], '%Y%m%d')
                            posted_dt = datetime.now() - timedelta(days=signals.posting_age_days)
                            diff = (posted_dt - wb_dt).days
                            if diff > 0:
                                signals.wayback_vs_posted_days = diff
                                if diff > 30:
                                    signals.is_reposted = True
                        except (ValueError, TypeError):
                            pass

        return signals

    def detect_reposts(
        self, job, existing_hashes: Dict[str, List[str]]
    ) -> GhostSignals:
        """
        Detect reposts by comparing against existing description hashes.

        existing_hashes: dict mapping description_hash -> list of job IDs.
        Uses exact hash match. For fuzzy matching, use detect_near_duplicates().
        """
        signals = self.collect_local_signals(job)

        if signals.description_hash in existing_hashes:
            prior_ids = existing_hashes[signals.description_hash]
            signals.is_reposted = True
            signals.repost_count = len(prior_ids)
            signals.near_duplicate_ids = prior_ids[:5]

        return signals

    def detect_near_duplicates(
        self, description: str, existing_descriptions: Dict[str, str],
        threshold: int = 85,
    ) -> List[str]:
        """
        Fuzzy match a description against existing ones.

        Uses rapidfuzz token_set_ratio (installed as optional dependency).
        Returns list of matching job IDs with similarity >= threshold.
        """
        try:
            from rapidfuzz import fuzz
        except ImportError:
            logger.debug("rapidfuzz not installed -- skipping near-duplicate detection")
            return []

        matches = []
        for job_id, existing in existing_descriptions.items():
            similarity = fuzz.token_set_ratio(description.lower(), existing.lower())
            if similarity >= threshold:
                matches.append(job_id)

        return matches

    # -- Internal helpers --

    def _score_specificity(self, jd_lower: str) -> float:
        """Score description specificity (0 = very vague, 1 = very specific)."""
        if not jd_lower or len(jd_lower) < 50:
            return 0.1

        vague_count = sum(1 for p in VAGUE_PHRASES if p in jd_lower)
        specific_count = sum(1 for p in SPECIFICITY_MARKERS if re.search(p, jd_lower))

        total = vague_count + specific_count
        if total == 0:
            return 0.5

        specificity = specific_count / total
        return round(min(specificity, 1.0), 2)

    def _hash_description(self, jd_lower: str) -> str:
        """Create a stable hash of the job description for repost detection."""
        normalized = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', jd_lower)
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    async def _extract_json_ld_date(self, url: str) -> Optional[str]:
        """Extract datePosted from JSON-LD structured data on job page."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    follow_redirects=True,
                    timeout=10.0,
                )
            if resp.status_code != 200:
                return None

            for match in re.finditer(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                resp.text, re.DOTALL,
            ):
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'JobPosting':
                                return item.get('datePosted')
                    elif data.get('@type') == 'JobPosting':
                        return data.get('datePosted')
                except (json.JSONDecodeError, AttributeError):
                    continue

        except ImportError:
            logger.debug("httpx not installed -- skipping JSON-LD extraction")
        except Exception as e:
            logger.debug("JSON-LD extraction failed for %s: %s", url, e)

        return None

    async def _wayback_first_seen(self, url: str) -> Optional[str]:
        """Query Wayback Machine CDX API for URL first-capture timestamp."""
        try:
            import httpx
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=1"
            async with httpx.AsyncClient() as client:
                resp = await client.get(cdx_url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1:
                    return data[1][1]  # timestamp column
        except ImportError:
            logger.debug("httpx not installed -- skipping Wayback check")
        except Exception as e:
            logger.debug("Wayback CDX query failed for %s: %s", url, e)

        return None


# -- Singleton --

_collector: Optional[GhostSignalCollector] = None


def get_ghost_signal_collector(enable_http: bool = False) -> GhostSignalCollector:
    """Get or create the global ghost signal collector."""
    global _collector
    if _collector is None:
        import os
        http_enabled = os.getenv('GHOST_HTTP_CHECKS_ENABLED', 'false').lower() == 'true'
        _collector = GhostSignalCollector(enable_http_checks=http_enabled or enable_http)
    return _collector
