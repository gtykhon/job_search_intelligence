"""
Glassdoor Client — glassdoor-real-time.p.rapidapi.com (RapidAPI)

Two-step lookup:
  1. /jobs/search?query=<company> → extract companyId from companyFilterOptions
  2. /companies/reviews?companyId=<id> → extract ratings

The API key provided is free-tier from RapidAPI.

Env vars:
  RAPIDAPI_KEY           — RapidAPI key
  GLASSDOOR_API_ENABLED  — Master switch; set "true" to enable (default: false)
"""

import hashlib
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Company name normalization ────────────────────────────────────────────────

# Hard legal suffixes — always safe to strip (entity type designators)
_LEGAL_SUFFIXES = re.compile(
    r",?\s*\b("
    r"Inc\.?|Incorporated|LLC|L\.L\.C\.?|Corp\.?|Corporation|Co\.?"
    r"|Ltd\.?|Limited|PLC|P\.L\.C\.?|LP|L\.P\.?"
    r"|LLP|L\.L\.P\.?|PLLC|P\.L\.L\.C\.?"
    r")\b\.?,?",
    re.IGNORECASE,
)

# Soft suffixes — only strip when trailing (these can be part of a real name)
_TRAILING_SOFT_SUFFIXES = re.compile(
    r"\s+("
    r"Group|Holdings|Holding|Company|Enterprises?"
    r"|International|Intl\.?|Solutions|Services|Technologies|Technology"
    r")\s*$",
    re.IGNORECASE,
)

# d/b/a (doing business as) pattern — the DBA name is usually the public brand
_DBA_PATTERN = re.compile(
    r"(?:d/?b/?a|doing\s+business\s+as|trading\s+as|t/a)\s+(.+)",
    re.IGNORECASE,
)

# Parenthetical qualifiers like "(formerly Foo)" or "(a Subsidiary of Bar)"
_PAREN_QUALIFIER = re.compile(r"\s*\((?:formerly|prev(?:iously)?|now|a\s+subsidiary\s+of|part\s+of)[^)]*\)", re.IGNORECASE)

# Generic parenthetical — e.g. "(US)" or "(Remote)"
_PAREN_GENERIC = re.compile(r"\s*\([^)]*\)")


def _normalize_company_name(raw: str) -> List[str]:
    """
    Generate a priority-ordered list of candidate search names from a raw
    company string.  The first entry is the best guess; later entries are
    progressively simplified fallbacks.

    Example:
        "Perfect Path, LLC, d/b/a Trajector Services"
        → ["Trajector Services", "Perfect Path", "Perfect Path LLC Trajector Services"]
    """
    if not raw or not raw.strip():
        return []

    raw = raw.strip()
    candidates: list[str] = []
    seen: set[str] = set()

    def _clean(name: str) -> str:
        """Collapse whitespace, strip punctuation debris."""
        name = re.sub(r"\s+", " ", name).strip()
        # Remove trailing punctuation debris (e.g. trailing "&", ",", ".")
        name = re.sub(r"[\s,&.]+$", "", name).strip()
        return name

    def _add(name: str) -> None:
        name = _clean(name)
        if name and name.lower() not in seen and len(name) > 1:
            seen.add(name.lower())
            candidates.append(name)

    def _strip_suffixes(name: str) -> str:
        """Remove both hard legal suffixes and trailing soft suffixes."""
        name = _LEGAL_SUFFIXES.sub("", name)
        name = _TRAILING_SOFT_SUFFIXES.sub("", name)
        return _clean(name)

    # ── 1. Extract DBA name (highest priority — it's the public brand) ────
    dba_match = _DBA_PATTERN.search(raw)
    if dba_match:
        dba_name = dba_match.group(1).strip()
        _add(dba_name)
        # Also try DBA without suffixes
        _add(_strip_suffixes(dba_name))

    # ── 2. The part before d/b/a (the legal entity, cleaned) ─────────────
    if dba_match:
        legal_part = raw[:dba_match.start()].strip().strip(",").strip()
    else:
        legal_part = raw

    # Remove parenthetical qualifiers
    legal_clean = _PAREN_QUALIFIER.sub("", legal_part)
    legal_clean = _PAREN_GENERIC.sub("", legal_clean)
    # Strip legal suffixes
    _add(_strip_suffixes(legal_clean))

    # ── 3. Original cleaned (no suffixes) as fallback ─────────────────────
    full_clean = _strip_suffixes(raw)
    full_clean = _PAREN_QUALIFIER.sub("", full_clean).strip()
    full_clean = _DBA_PATTERN.sub("", full_clean).strip().strip(",").strip()
    _add(_clean(full_clean))

    # ── 4. Raw name as last resort ────────────────────────────────────────
    _add(raw)

    return candidates

RAPIDAPI_HOST = "glassdoor-real-time.p.rapidapi.com"

# In-memory session cache — avoids re-fetching same company within one run
_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = timedelta(hours=6)


class GlassdoorClient:
    """
    Fetches Glassdoor company ratings via glassdoor-real-time RapidAPI.

    Two-step: find company ID via job search, then fetch ratings.
    Returns overallRating, cultureAndValuesRating, workLifeBalanceRating, etc.
    """

    def __init__(self, api_key: str = "", enabled: bool = False):
        self.api_key = api_key
        self.enabled = enabled and bool(api_key)
        if enabled and not api_key:
            logger.warning(
                "GLASSDOOR_API_ENABLED=true but RAPIDAPI_KEY is not set. "
                "Add your key to Settings → Filters → Culture Score section."
            )

    def _track_usage(self, endpoint: str, success: bool = True, error: str = ""):
        """Log API usage to the dashboard database."""
        try:
            from src.dashboard.db import DashboardDB
            db = DashboardDB()
            db.log_api_usage("glassdoor", endpoint, success=success, error_message=error)
        except Exception:
            pass  # Never let tracking break the main flow

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def lookup_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Look up company on Glassdoor via RapidAPI.
        Returns dict with ``glassdoor_rating`` and other fields, or None.
        """
        if not self.enabled or not company_name:
            return None

        cache_key = self._cache_key(company_name)
        cached = _cache.get(cache_key)
        if cached and datetime.now() - cached.get("_fetched_at", datetime.min) < _CACHE_TTL:
            logger.debug("Glassdoor cache hit for %s", company_name)
            return cached

        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": RAPIDAPI_HOST,
        }

        try:
            try:
                import aiohttp
            except ImportError:
                logger.debug("aiohttp not installed — Glassdoor API unavailable")
                return None

            async with aiohttp.ClientSession() as session:
                # Step 1: find company ID via job search
                company_id = await self._find_company_id(session, headers, company_name)
                if not company_id:
                    logger.debug("No Glassdoor company ID found for: %s", company_name)
                    self._track_usage("jobs/search", success=False)
                    return None

                self._track_usage("jobs/search", success=True)

                # Step 2: fetch ratings
                result = await self._fetch_ratings(session, headers, company_id, company_name)
                self._track_usage("companies/reviews", success=result is not None)
                if result:
                    result["_fetched_at"] = datetime.now()
                    _cache[cache_key] = result
                    logger.info(
                        "Glassdoor ratings fetched for %s (id=%s): overall=%.1f",
                        company_name, company_id, result.get("glassdoor_rating", 0),
                    )
                return result

        except Exception as exc:
            logger.debug("Glassdoor lookup failed for %s: %s", company_name, exc)
            self._track_usage("lookup", success=False, error=str(exc))
            return None

    async def _find_company_id(self, session, headers, company_name: str) -> Optional[int]:
        """
        Search for company ID via /jobs/search endpoint.

        Uses progressive name simplification: tries the best-guess cleaned
        name first, then falls back to alternative forms (DBA → legal entity
        → raw name).  Stops as soon as a match is found.
        """
        import aiohttp

        candidates = _normalize_company_name(company_name)
        if not candidates:
            return None

        url = f"https://{RAPIDAPI_HOST}/jobs/search"

        for i, candidate in enumerate(candidates):
            try:
                params = {"query": candidate, "location": "United States", "limit": "5"}
                async with session.get(
                    url, headers=headers, params=params,
                    timeout=aiohttp.ClientTimeout(total=12.0),
                ) as resp:
                    if resp.status == 429:
                        logger.warning("Glassdoor rate-limited during company search")
                        return None
                    if resp.status != 200:
                        continue
                    data = await resp.json()

                companies = (data.get("data") or {}).get("companyFilterOptions", [])
                if not companies:
                    if i < len(candidates) - 1:
                        logger.debug(
                            "No Glassdoor results for '%s', trying next variant...",
                            candidate,
                        )
                    continue

                # Prefer exact/substring name match against any candidate form
                all_names_lower = [c.lower() for c in candidates]
                for c in companies:
                    short = (c.get("shortName") or "").lower().strip()
                    for name_l in all_names_lower:
                        if short == name_l or name_l in short or short in name_l:
                            logger.debug(
                                "Glassdoor match for '%s' → '%s' (id=%s, attempt=%d/%d)",
                                company_name, c.get("shortName"), c["id"],
                                i + 1, len(candidates),
                            )
                            return c["id"]

                # No substring match — accept first result from the best candidate
                best = companies[0]
                logger.debug(
                    "Glassdoor fuzzy match for '%s' → '%s' (id=%s, attempt=%d/%d)",
                    company_name, best.get("shortName"), best["id"],
                    i + 1, len(candidates),
                )
                return best["id"]

            except Exception as exc:
                logger.debug("Company ID lookup failed for '%s': %s", candidate, exc)
                continue

        logger.info("No Glassdoor company ID found after %d attempts for: %s",
                     len(candidates), company_name)
        return None

    async def _fetch_ratings(self, session, headers, company_id: int, company_name: str) -> Optional[Dict[str, Any]]:
        """Fetch ratings from /companies/reviews endpoint."""
        import aiohttp
        try:
            url = f"https://{RAPIDAPI_HOST}/companies/reviews"
            params = {"companyId": str(company_id), "limit": "1"}
            async with session.get(
                url, headers=headers, params=params,
                timeout=aiohttp.ClientTimeout(total=12.0),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

            rating_obj = (data.get("data") or {}).get("rating") or {}
            ratings = rating_obj.get("ratings") or {}

            overall = ratings.get("overallRating")
            if not overall:
                return None

            return {
                "company_name":       company_name,
                "company_id":         company_id,
                "glassdoor_rating":   float(overall),
                "culture_rating":     self._sf(ratings.get("cultureAndValuesRating")),
                "work_life_balance":  self._sf(ratings.get("workLifeBalanceRating")),
                "compensation_rating": self._sf(ratings.get("compensationAndBenefitsRating")),
                "diversity_rating":   self._sf(ratings.get("diversityAndInclusionRating")),
                "career_rating":      self._sf(ratings.get("careerOpportunitiesRating")),
                "senior_mgmt_rating": self._sf(ratings.get("seniorManagementRating")),
                "ceo_approval":       self._sf(ratings.get("recommendToFriendRating")),
                "review_count":       self._count_from_distribution(
                    rating_obj.get("ratingCountDistribution", {}).get("overall", {})
                ),
                "source": "glassdoor_real_time_rapidapi",
            }

        except Exception as exc:
            logger.debug("Ratings fetch failed for company_id=%s: %s", company_id, exc)
            return None

    # ------------------------------------------------------------------
    # Sync wrapper
    # ------------------------------------------------------------------

    def lookup_company_sync(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper around ``lookup_company``."""
        import asyncio
        try:
            # Always create a fresh event loop for the calling thread.
            # This avoids issues when called from a background thread while
            # uvicorn's main loop is running (nest_asyncio not available).
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.lookup_company(company_name))
            finally:
                loop.close()
        except Exception as exc:
            logger.debug("lookup_company_sync failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sf(self, val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _count_from_distribution(self, dist: dict) -> Optional[int]:
        """Sum up star counts to get total review count."""
        try:
            return sum(int(v) for v in dist.values() if v is not None)
        except Exception:
            return None

    def _cache_key(self, company_name: str) -> str:
        return hashlib.md5(company_name.lower().strip().encode()).hexdigest()


# ── Singleton ──────────────────────────────────────────────────────────────────

_client: Optional[GlassdoorClient] = None


def get_glassdoor_client() -> GlassdoorClient:
    """Return the global GlassdoorClient (configured from environment)."""
    global _client
    if _client is None:
        _client = GlassdoorClient(
            api_key=os.getenv("RAPIDAPI_KEY", ""),
            enabled=os.getenv("GLASSDOOR_API_ENABLED", "false").lower() == "true",
        )
    return _client
