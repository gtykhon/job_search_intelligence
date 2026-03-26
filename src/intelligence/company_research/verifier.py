"""
Company Verifier with SQLite caching.

Wraps the auto_company_research stub with:
  - SQLite-backed caching (avoids redundant requests)
  - Async interface compatible with the screening pipeline
  - Graceful degradation when Playwright is unavailable

Cache TTL: 7 days by default.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(__file__).parent.parent.parent.parent / "data" / "job_search.db"
_CACHE_TTL_DAYS = 7


@dataclass
class CompanyResearchResult:
    company_name: str
    decision_status: str           # "approved" | "declined" | "review" | "unknown"
    defense_status: Optional[str] = None
    glassdoor_rating: Optional[float] = None
    glassdoor_reviews: int = 0
    culture_score: Optional[float] = None
    decline_reason: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    from_cache: bool = False
    research_date: Optional[str] = None


class CompanyVerifier:
    """
    Looks up company research from cache or runs live research.

    Integration point: called from gate_0a_company_research.py
    and from CoverLetterPipeline._research_hiring_manager().
    """

    def __init__(self, db_path: Optional[str] = None, ttl_days: int = _CACHE_TTL_DAYS):
        self.db_path = str(db_path or _DEFAULT_DB)
        self.ttl_days = ttl_days
        self._ensure_cache_table()

    async def research(self, company_name: str, position: str = "") -> CompanyResearchResult:
        """
        Return company research for *company_name*.
        Checks cache first; falls back to live research.
        """
        cached = self._check_cache(company_name)
        if cached:
            logger.debug("Company cache hit for '%s'", company_name)
            return cached

        logger.info("Running company research for '%s'", company_name)
        result = await self._run_research(company_name, position)
        self._save_to_cache(result)
        return result

    def research_sync(self, company_name: str, position: str = "") -> CompanyResearchResult:
        """Synchronous wrapper for use in non-async contexts."""
        cached = self._check_cache(company_name)
        if cached:
            return cached
        # Run basic sync research (no Playwright)
        return self._basic_research(company_name)

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _check_cache(self, company_name: str) -> Optional[CompanyResearchResult]:
        """Return cached result if still within TTL, else None."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM company_research_cache WHERE company_name = ? COLLATE NOCASE",
                    (company_name,),
                ).fetchone()
        except Exception as e:
            logger.debug("Cache lookup failed: %s", e)
            return None

        if not row:
            return None

        # Check TTL
        research_date = row["research_date"] or ""
        try:
            rd = datetime.fromisoformat(research_date[:19])
            if datetime.utcnow() - rd > timedelta(days=self.ttl_days):
                logger.debug("Cache expired for '%s'", company_name)
                return None
        except (ValueError, TypeError):
            pass

        glassdoor = {}
        if row["glassdoor_json"]:
            try:
                glassdoor = json.loads(row["glassdoor_json"])
            except json.JSONDecodeError:
                pass

        return CompanyResearchResult(
            company_name=row["company_name"],
            decision_status=row["decision_status"],
            defense_status=row["defense_status"],
            glassdoor_rating=glassdoor.get("rating"),
            glassdoor_reviews=glassdoor.get("reviews", 0),
            decline_reason=row["decline_reason"],
            raw_data=glassdoor,
            from_cache=True,
            research_date=row["research_date"],
        )

    def _save_to_cache(self, result: CompanyResearchResult) -> None:
        """Upsert a research result into the cache."""
        now = datetime.utcnow().isoformat()
        expires = (datetime.utcnow() + timedelta(days=self.ttl_days)).isoformat()
        glassdoor_json = json.dumps(result.raw_data) if result.raw_data else None

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO company_research_cache
                        (company_name, decision_status, defense_status,
                         glassdoor_json, decline_reason, research_date, expires_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(company_name) DO UPDATE SET
                        decision_status = excluded.decision_status,
                        defense_status  = excluded.defense_status,
                        glassdoor_json  = excluded.glassdoor_json,
                        decline_reason  = excluded.decline_reason,
                        research_date   = excluded.research_date,
                        expires_at      = excluded.expires_at
                    """,
                    (
                        result.company_name,
                        result.decision_status,
                        result.defense_status,
                        glassdoor_json,
                        result.decline_reason,
                        result.research_date or now,
                        expires,
                        now,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.warning("Could not save company research to cache: %s", e)

    # ------------------------------------------------------------------
    # Live research
    # ------------------------------------------------------------------

    async def _run_research(self, company_name: str, position: str) -> CompanyResearchResult:
        """
        Attempt live research using the auto_company_research stub.
        Falls back to basic research if Playwright is unavailable.
        """
        try:
            import sys
            from pathlib import Path as _Path
            # Try to use the existing stub
            stub_path = str(
                _Path(__file__).parent.parent.parent.parent
                / "features_to_built" / "auto_company_research"
            )
            if stub_path not in sys.path:
                sys.path.insert(0, stub_path)
            from company_verification_system import CompanyVerificationSystem  # type: ignore[import]
            verifier = CompanyVerificationSystem()
            raw = verifier.verify_company(company_name)
            return CompanyResearchResult(
                company_name=company_name,
                decision_status=raw.get("decision", "unknown"),
                defense_status=raw.get("defense_status"),
                decline_reason=raw.get("decline_reason"),
                raw_data=raw,
                research_date=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            logger.debug("Live company research unavailable (%s), using basic", e)
            return self._basic_research(company_name)

    def _basic_research(self, company_name: str) -> CompanyResearchResult:
        """
        Minimal research using only company name heuristics.
        Used as fallback when Playwright or the stub is unavailable.
        """
        name_lower = company_name.lower()
        defense_keywords = [
            "defense", "aerospace", "lockheed", "raytheon", "northrop",
            "l3harris", "bae systems", "general dynamics", "booz allen",
            "leidos", "saic", "caci", "perspecta",
        ]
        staffing_keywords = [
            "staffing", "recruiting", "solutions llc", "consulting group",
            "talent", "manpower", "adecco", "robert half",
        ]

        if any(kw in name_lower for kw in defense_keywords):
            return CompanyResearchResult(
                company_name=company_name,
                decision_status="declined",
                defense_status="defense_contractor",
                decline_reason="Defense/aerospace contractor detected by name heuristic.",
                research_date=datetime.utcnow().isoformat(),
            )

        if any(kw in name_lower for kw in staffing_keywords):
            return CompanyResearchResult(
                company_name=company_name,
                decision_status="review",
                decline_reason="Possible staffing agency detected by name heuristic.",
                research_date=datetime.utcnow().isoformat(),
            )

        return CompanyResearchResult(
            company_name=company_name,
            decision_status="unknown",
            research_date=datetime.utcnow().isoformat(),
        )

    def _ensure_cache_table(self) -> None:
        """Create cache table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS company_research_cache (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name    TEXT UNIQUE NOT NULL,
                        decision_status TEXT NOT NULL DEFAULT 'unknown',
                        defense_status  TEXT,
                        glassdoor_json  TEXT,
                        scoring_json    TEXT,
                        decline_reason  TEXT,
                        research_date   TEXT NOT NULL DEFAULT (datetime('now')),
                        expires_at      TEXT,
                        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_company_cache_name
                        ON company_research_cache(company_name)
                """)
                conn.commit()
        except Exception as e:
            logger.warning("Could not ensure company research cache table: %s", e)
