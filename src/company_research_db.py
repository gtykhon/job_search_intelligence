import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


DB_PATH = "data/company_research.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE COLLATE NOCASE,
            normalized_name TEXT,
            tier INTEGER,
            decision_status TEXT,
            defense_status TEXT,
            culture_score INTEGER,
            wlb_score INTEGER,
            risk_level TEXT,
            glassdoor_overall REAL,
            glassdoor_reviews INTEGER,
            last_researched_at TEXT,
            decline_reason TEXT,
            avoided_flag INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def upsert_company_from_research(result: Any, tier: Optional[int] = None) -> None:
    """
    Persist a CompanyResearchResult into the database.

    This is designed to work with features_to_built.auto_company_research.CompanyResearchResult.
    """
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    name = getattr(result, "company_name", None) or ""
    decision_status = getattr(result, "decision_status", None)
    decision_value = getattr(decision_status, "value", None) if decision_status else None
    defense_status = getattr(result, "defense_status", None)
    defense_value = getattr(defense_status, "value", None) if defense_status else None
    scoring_result = getattr(result, "scoring_result", None)
    glassdoor_metrics = getattr(result, "glassdoor_metrics", None)

    culture_score = getattr(scoring_result, "culture_score", None) if scoring_result else None
    wlb_score = getattr(scoring_result, "wlb_score", None) if scoring_result else None
    risk_level = getattr(scoring_result, "risk_level", None) if scoring_result else None

    overall = getattr(glassdoor_metrics, "overall_rating", None) if glassdoor_metrics else None
    reviews = getattr(glassdoor_metrics, "total_reviews", None) if glassdoor_metrics else None

    decline_reason = getattr(result, "decline_reason", None)

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO companies (
            name, normalized_name, tier, decision_status, defense_status,
            culture_score, wlb_score, risk_level, glassdoor_overall,
            glassdoor_reviews, last_researched_at, decline_reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            tier=excluded.tier,
            decision_status=excluded.decision_status,
            defense_status=excluded.defense_status,
            culture_score=excluded.culture_score,
            wlb_score=excluded.wlb_score,
            risk_level=excluded.risk_level,
            glassdoor_overall=excluded.glassdoor_overall,
            glassdoor_reviews=excluded.glassdoor_reviews,
            last_researched_at=excluded.last_researched_at,
            decline_reason=excluded.decline_reason
        """,
        (
            name,
            name.lower(),
            tier,
            decision_value,
            defense_value,
            culture_score,
            wlb_score,
            risk_level,
            overall,
            reviews,
            now,
            decline_reason,
        ),
    )

    conn.commit()
    conn.close()


def mark_avoided_company(name: str) -> None:
    """Mark a company as avoided in the research database."""
    if not name:
        return
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO companies (name, normalized_name, avoided_flag, last_researched_at)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(name) DO UPDATE SET
            avoided_flag=1,
            last_researched_at=excluded.last_researched_at
        """,
        (name, name.lower(), now),
    )
    conn.commit()
    conn.close()


def get_company_record(name: str) -> Optional[Dict[str, Any]]:
    """Fetch a company record from the database by name."""
    if not name:
        return None
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT name, tier, decision_status, defense_status, culture_score, wlb_score, "
        "risk_level, glassdoor_overall, glassdoor_reviews, avoided_flag "
        "FROM companies WHERE name = ? COLLATE NOCASE",
        (name,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    (
        name,
        tier,
        decision_status,
        defense_status,
        culture_score,
        wlb_score,
        risk_level,
        glassdoor_overall,
        glassdoor_reviews,
        avoided_flag,
    ) = row
    return {
        "name": name,
        "tier": tier,
        "decision_status": decision_status,
        "defense_status": defense_status,
        "culture_score": culture_score,
        "wlb_score": wlb_score,
        "risk_level": risk_level,
        "glassdoor_overall": glassdoor_overall,
        "glassdoor_reviews": glassdoor_reviews,
        "avoided_flag": bool(avoided_flag),
    }
