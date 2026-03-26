"""
Application Outcomes Tracker.

Records per-application outcomes and runs a weekly feedback loop
to detect underperforming campaigns and correlate outcomes with
material quality signals.

Diagnostic trigger:
  30+ applications with 0 interviews in the rolling window
  -> auto-flag for targeting/quality diagnostic

Usage:
    tracker = OutcomesTracker(db_path="data/job_search.db")
    tracker.log_outcome(ApplicationOutcome(
        platform="linkedin",
        outcome=OutcomeType.INTERVIEW,
        authenticity_score=92.0,
        hm_research_done=True,
    ))
    stats = tracker.get_stats(days=30)
    print(stats.interview_rate, stats.diagnostic_triggered)
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "job_search.db"

DIAGNOSTIC_TRIGGER_COUNT = 30   # applications before diagnostic fires
DIAGNOSTIC_WINDOW_DAYS   = 60   # rolling window in days


class OutcomeType(str, Enum):
    APPLIED        = "applied"
    REJECTED       = "rejected"
    SCREENING_CALL = "screening_call"
    INTERVIEW      = "interview"
    OFFER          = "offer"
    WITHDRAWN      = "withdrawn"


@dataclass
class ApplicationOutcome:
    platform: str
    outcome: OutcomeType
    job_id: Optional[int] = None
    authenticity_score: Optional[float] = None
    hm_research_done: bool = False
    applied_date: Optional[str] = None
    response_date: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class OutcomeStats:
    total_applications: int
    by_outcome: Dict[str, int]
    by_platform: Dict[str, int]
    interview_rate: float           # interviews / total_applications
    offer_rate: float               # offers / total_applications
    avg_authenticity_score: Optional[float]
    hm_research_rate: float         # fraction with HM research done
    diagnostic_triggered: bool
    diagnostic_message: Optional[str]
    window_days: int


class OutcomesTracker:
    """CRUD + analytics for the application_outcomes SQLite table."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or _DEFAULT_DB)
        self._ensure_table()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def log_outcome(self, outcome: ApplicationOutcome) -> int:
        """Insert an outcome record. Returns the new row id."""
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO application_outcomes
                    (job_id, platform, outcome, authenticity_score,
                     hm_research_done, applied_date, response_date, notes,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    outcome.job_id,
                    outcome.platform,
                    outcome.outcome.value if isinstance(outcome.outcome, OutcomeType) else outcome.outcome,
                    outcome.authenticity_score,
                    1 if outcome.hm_research_done else 0,
                    outcome.applied_date or now[:10],
                    outcome.response_date,
                    outcome.notes,
                    now,
                    now,
                ),
            )
            conn.commit()
            return cur.lastrowid  # type: ignore[return-value]

    def update_outcome(self, record_id: int, outcome: OutcomeType, response_date: Optional[str] = None) -> None:
        """Update the outcome of an existing record (e.g. applied -> interview)."""
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE application_outcomes
                SET outcome = ?, response_date = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    outcome.value if isinstance(outcome, OutcomeType) else outcome,
                    response_date,
                    now,
                    record_id,
                ),
            )
            conn.commit()

    def get_recent(self, days: int = 30) -> List[Dict]:
        """Return raw outcome rows from the last N days."""
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM application_outcomes WHERE created_at >= ? ORDER BY created_at DESC",
                (since,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_stats(self, days: int = 30) -> OutcomeStats:
        """Compute outcome statistics for the last N days."""
        rows = self.get_recent(days)
        total = len(rows)

        by_outcome: Dict[str, int] = {}
        by_platform: Dict[str, int] = {}
        auth_scores: List[float] = []
        hm_done = 0

        for row in rows:
            by_outcome[row["outcome"]] = by_outcome.get(row["outcome"], 0) + 1
            by_platform[row["platform"]] = by_platform.get(row["platform"], 0) + 1
            if row.get("authenticity_score") is not None:
                auth_scores.append(float(row["authenticity_score"]))
            if row.get("hm_research_done"):
                hm_done += 1

        interviews = by_outcome.get("interview", 0) + by_outcome.get("screening_call", 0)
        offers = by_outcome.get("offer", 0)

        interview_rate = interviews / total if total else 0.0
        offer_rate = offers / total if total else 0.0
        avg_auth = sum(auth_scores) / len(auth_scores) if auth_scores else None
        hm_rate = hm_done / total if total else 0.0

        diagnostic_msg = self._check_diagnostic_trigger(total, interviews, days)

        return OutcomeStats(
            total_applications=total,
            by_outcome=by_outcome,
            by_platform=by_platform,
            interview_rate=round(interview_rate, 3),
            offer_rate=round(offer_rate, 3),
            avg_authenticity_score=round(avg_auth, 1) if avg_auth else None,
            hm_research_rate=round(hm_rate, 3),
            diagnostic_triggered=diagnostic_msg is not None,
            diagnostic_message=diagnostic_msg,
            window_days=days,
        )

    def correlate_authenticity(self) -> Dict[str, Dict[str, float]]:
        """
        Correlate authenticity score bands with outcome rates.
        Returns { band: {outcome: rate} }.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT outcome, authenticity_score FROM application_outcomes "
                "WHERE authenticity_score IS NOT NULL"
            ).fetchall()

        bands: Dict[str, List[str]] = {
            "high (90-100)": [],
            "medium (70-89)": [],
            "low (<70)": [],
        }
        for row in rows:
            score = float(row["authenticity_score"])
            outcome = row["outcome"]
            if score >= 90:
                bands["high (90-100)"].append(outcome)
            elif score >= 70:
                bands["medium (70-89)"].append(outcome)
            else:
                bands["low (<70)"].append(outcome)

        result: Dict[str, Dict[str, float]] = {}
        for band, outcomes in bands.items():
            if not outcomes:
                result[band] = {}
                continue
            counts: Dict[str, int] = {}
            for o in outcomes:
                counts[o] = counts.get(o, 0) + 1
            total = len(outcomes)
            result[band] = {k: round(v / total, 3) for k, v in counts.items()}
        return result

    def correlate_hm_research(self) -> Dict[str, Dict[str, float]]:
        """Correlate HM research completion with positive outcomes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT outcome, hm_research_done FROM application_outcomes"
            ).fetchall()

        groups: Dict[str, List[str]] = {"with_research": [], "without_research": []}
        for row in rows:
            key = "with_research" if row["hm_research_done"] else "without_research"
            groups[key].append(row["outcome"])

        result: Dict[str, Dict[str, float]] = {}
        for group, outcomes in groups.items():
            if not outcomes:
                result[group] = {}
                continue
            counts: Dict[str, int] = {}
            for o in outcomes:
                counts[o] = counts.get(o, 0) + 1
            total = len(outcomes)
            result[group] = {k: round(v / total, 3) for k, v in counts.items()}
        return result

    def run_weekly_analysis(self) -> OutcomeStats:
        """Run the weekly diagnostic. Returns stats for the last 60 days."""
        stats = self.get_stats(days=DIAGNOSTIC_WINDOW_DAYS)
        if stats.diagnostic_triggered:
            logger.warning("OUTCOMES DIAGNOSTIC: %s", stats.diagnostic_message)
        return stats

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _check_diagnostic_trigger(
        self, total: int, interviews: int, days: int
    ) -> Optional[str]:
        """Return diagnostic message if trigger conditions are met."""
        if total >= DIAGNOSTIC_TRIGGER_COUNT and interviews == 0:
            return (
                f"DIAGNOSTIC TRIGGERED: {total} applications in {days} days with "
                f"0 interviews/screening calls. "
                f"Recommended actions: (1) audit duty coverage scores, "
                f"(2) review keyword targeting, (3) check authenticity audit results, "
                f"(4) verify compensation alignment."
            )
        return None

    def _ensure_table(self) -> None:
        """Create table if it doesn't exist (idempotent)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS application_outcomes (
                        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id              INTEGER,
                        platform            TEXT NOT NULL DEFAULT 'unknown',
                        outcome             TEXT NOT NULL,
                        authenticity_score  REAL,
                        hm_research_done    INTEGER DEFAULT 0,
                        applied_date        TEXT,
                        response_date       TEXT,
                        notes               TEXT,
                        created_at          TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_outcomes_applied_date
                        ON application_outcomes(applied_date)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_outcomes_outcome
                        ON application_outcomes(outcome)
                """)
                conn.commit()
        except Exception as e:
            logger.warning("Could not ensure outcomes table: %s", e)
