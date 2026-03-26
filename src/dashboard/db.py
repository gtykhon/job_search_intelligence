"""
SQLite Bridge — Dashboard database layer.

Reads from job_tracker.db, adds alignment scoring columns,
manages dashboard settings and application package tracking.
"""

import re
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Default DB path
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "job_tracker.db"


class DashboardDB:
    """SQLite bridge for the dashboard."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._run_migrations()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _run_migrations(self):
        """Add dashboard-specific columns and tables."""
        with self.get_connection() as conn:
            c = conn.cursor()

            # Add alignment_score and alignment_details to jobs table
            existing = {
                row[1] for row in c.execute("PRAGMA table_info(jobs)").fetchall()
            }
            if "alignment_score" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN alignment_score REAL")
                logger.info("Added alignment_score column to jobs table")
            if "alignment_details" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN alignment_details TEXT")
                logger.info("Added alignment_details column to jobs table")
            if "job_category" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN job_category TEXT")
                logger.info("Added job_category column to jobs table")
            if "category_confidence" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN category_confidence REAL")
                logger.info("Added category_confidence column to jobs table")
            if "semantic_alignment_score" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN semantic_alignment_score REAL")
                logger.info("Added semantic_alignment_score column to jobs table")
            if "role_type_label" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN role_type_label TEXT")
                logger.info("Added role_type_label column to jobs table")
            if "company_glassdoor_json" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN company_glassdoor_json TEXT")
                logger.info("Added company_glassdoor_json column to jobs table")
            if "company_rating_fetched_at" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN company_rating_fetched_at TEXT")
                logger.info("Added company_rating_fetched_at column to jobs table")
            if "company_rating_source" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN company_rating_source TEXT")
                logger.info("Added company_rating_source column to jobs table")

            # Career page verification columns
            if "career_page_verified" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN career_page_verified INTEGER")  # 1=found, 0=not found, NULL=unchecked
                logger.info("Added career_page_verified column to jobs table")
            if "career_page_json" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN career_page_json TEXT")
                logger.info("Added career_page_json column to jobs table")
            if "career_page_checked_at" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN career_page_checked_at TEXT")
                logger.info("Added career_page_checked_at column to jobs table")
            if "status" not in existing:
                c.execute("ALTER TABLE jobs ADD COLUMN status TEXT")
                logger.info("Added status column to jobs table")

            # LLM skill extraction cache
            c.execute("""
                CREATE TABLE IF NOT EXISTS llm_skill_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT NOT NULL UNIQUE,
                    text_type TEXT NOT NULL,
                    extracted_skills TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # Dashboard settings table
            c.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Application packages table
            c.execute("""
                CREATE TABLE IF NOT EXISTS application_packages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    resume_text TEXT,
                    cover_letter_text TEXT,
                    resume_version TEXT,
                    status TEXT DEFAULT 'pending',
                    generated_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            """)

            # Add ai_model and ai_provider to application_packages
            ap_existing = {
                row[1] for row in c.execute("PRAGMA table_info(application_packages)").fetchall()
            }
            if "ai_model" not in ap_existing:
                c.execute("ALTER TABLE application_packages ADD COLUMN ai_model TEXT")
                logger.info("Added ai_model column to application_packages table")
            if "ai_provider" not in ap_existing:
                c.execute("ALTER TABLE application_packages ADD COLUMN ai_provider TEXT")
                logger.info("Added ai_provider column to application_packages table")
            if "generation_metadata" not in ap_existing:
                c.execute("ALTER TABLE application_packages ADD COLUMN generation_metadata TEXT")
                logger.info("Added generation_metadata column to application_packages table")
            if "cover_letter_status" not in ap_existing:
                c.execute("ALTER TABLE application_packages ADD COLUMN cover_letter_status TEXT DEFAULT 'DRAFT_NEEDS_EDIT'")
                logger.info("Added cover_letter_status column to application_packages table")

            # Generation log table — tracks constrained generation pipeline results
            c.execute("""
                CREATE TABLE IF NOT EXISTS generation_log (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id              INTEGER REFERENCES jobs(id),
                    resume_version      TEXT,
                    job_category        TEXT,
                    verified_tools      TEXT,
                    blocked_tools       TEXT,
                    gap_flags           TEXT,
                    fabrication_errors  TEXT,
                    formatting_warnings TEXT,
                    score_before        REAL,
                    score_after         REAL,
                    requires_review     INTEGER,
                    validation_passed   INTEGER,
                    provider            TEXT,
                    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Application responses table
            c.execute("""
                CREATE TABLE IF NOT EXISTS application_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    source_site TEXT,
                    response_type TEXT DEFAULT 'none',
                    responded_at TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            """)

            # API usage tracking table
            c.execute("""
                CREATE TABLE IF NOT EXISTS api_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    endpoint TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    cost_estimate REAL DEFAULT 0.0,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Pipeline run metrics table — tracks resource usage per pipeline run
            c.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_type        TEXT NOT NULL,
                    started_at      TEXT,
                    finished_at     TEXT,
                    elapsed_seconds REAL,
                    steps_json      TEXT,
                    summary_json    TEXT,
                    cpu_min         REAL,
                    cpu_max         REAL,
                    cpu_avg         REAL,
                    ram_min_mb      REAL,
                    ram_max_mb      REAL,
                    ram_avg_mb      REAL,
                    ram_percent_max REAL,
                    sample_count    INTEGER DEFAULT 0
                )
            """)

            # Set defaults
            now = datetime.now().isoformat()
            defaults = {
                "auto_generate": "false",
                "resume_text": "",
            }
            for key, value in defaults.items():
                c.execute(
                    "INSERT OR IGNORE INTO dashboard_settings (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, value, now),
                )

            # One-time migration: strip HTML + Markdown from all existing descriptions
            # v2 re-runs to also strip Markdown artifacts (\*, **, etc.)
            migrated = self._get_meta(c, "descriptions_cleaned_v2")
            if not migrated:
                self._clean_all_descriptions(c)
                self._set_meta(c, "descriptions_cleaned_v2", "1")

    @staticmethod
    def _get_meta(cursor, key: str) -> Optional[str]:
        """Read a value from dashboard_settings (used for migration flags)."""
        row = cursor.execute(
            "SELECT value FROM dashboard_settings WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None

    @staticmethod
    def _set_meta(cursor, key: str, value: str):
        cursor.execute(
            "INSERT OR REPLACE INTO dashboard_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat()),
        )

    @staticmethod
    def _clean_html(text: str) -> str:
        """Strip HTML tags, Markdown artifacts, and decode entities."""
        if not text:
            return text
        # ── HTML cleanup ──
        if "<" in text:
            text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
            text = re.sub(r"</(?:p|div|li|tr|h[1-6])>", "\n", text, flags=re.IGNORECASE)
            text = re.sub(r"<(?:p|div|li|tr|h[1-6])\b[^>]*>", "", text, flags=re.IGNORECASE)
            text = re.sub(r"<li\b[^>]*>", "• ", text, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
        # ── HTML entities ──
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&rsquo;|&lsquo;|&#8217;|&#8216;", "'", text)
        text = re.sub(r"&rdquo;|&ldquo;|&#8220;|&#8221;", '"', text)
        text = re.sub(r"&mdash;|&#8212;", "—", text)
        text = re.sub(r"&ndash;|&#8211;", "–", text)
        text = re.sub(r"&#\d+;", "", text)
        text = re.sub(r"&\w+;", "", text)
        # ── Markdown artifacts ──
        # Bold/italic: **text**, __text__, *text*, _text_
        text = re.sub(r"\*{2,3}(.+?)\*{2,3}", r"\1", text)
        text = re.sub(r"_{2,3}(.+?)_{2,3}", r"\1", text)
        # Escaped characters: \*, \-, \., \#, \[, \], \(, \)
        text = re.sub(r"\\([*\-\.#\[\]\(\)&!>`~|])", r"\1", text)
        # Markdown headers: ## Header
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # Markdown links: [text](url) → text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        # Markdown images: ![alt](url) → alt
        text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)
        # Markdown bullet with backslash: \* item
        text = re.sub(r"^\\?\*\s+", "• ", text, flags=re.MULTILINE)
        # Inline code backticks
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Horizontal rules: --- or ***
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
        # ── Whitespace normalization ──
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _clean_all_descriptions(self, cursor):
        """Batch-clean all existing job descriptions."""
        rows = cursor.execute(
            "SELECT id, description FROM jobs WHERE description IS NOT NULL"
        ).fetchall()
        if not rows:
            return
        cleaned = 0
        for row in rows:
            clean = self._clean_html(row[1])
            if clean != row[1]:
                cursor.execute(
                    "UPDATE jobs SET description = ? WHERE id = ?",
                    (clean, row[0]),
                )
                cleaned += 1
        logger.info(f"🧹 Cleaned HTML from {cleaned}/{len(rows)} job descriptions")

    # ── Settings ────────────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM dashboard_settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO dashboard_settings (key, value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (key, value, datetime.now().isoformat()),
            )

    # ── Job Queries ─────────────────────────────────────────────────

    def get_jobs(
        self,
        days: int = 7,
        limit: int = 200,
        source: Optional[str] = None,
        remote_only: bool = False,
        search: Optional[str] = None,
        sort: str = "remote_first",
        min_score: Optional[int] = None,
        min_salary: Optional[int] = None,
        seniority: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get jobs with remote-first sorting by default."""
        with self.get_connection() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            conditions = ["scraped_date >= ?", "is_active = 1"]
            params: list = [cutoff]

            # Exclude jobs posted beyond the selected date range (if posted_date is known)
            conditions.append(
                "(posted_date IS NULL OR posted_date >= ?)"
            )
            params.append(cutoff)

            if source:
                conditions.append("source_site = ?")
                params.append(source)
            if remote_only:
                conditions.append("remote_type = 'remote'")
            if search:
                conditions.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
                term = f"%{search}%"
                params.extend([term, term, term])
            if min_score is not None and min_score > 0:
                conditions.append("alignment_score >= ?")
                params.append(min_score)
            if min_salary is not None and min_salary > 0:
                conditions.append("COALESCE(salary_max, salary_min, 0) >= ?")
                params.append(min_salary)
            if seniority:
                conditions.append("experience_level = ?")
                params.append(seniority)
            if location:
                if location == "remote":
                    conditions.append("remote_type = 'remote'")
                elif location == "hybrid":
                    conditions.append("remote_type = 'hybrid'")
                elif location == "us":
                    conditions.append(
                        "(location LIKE '%United States%' OR location LIKE '%, US%'"
                        " OR location LIKE '%USA%' OR location LIKE '%, CA%'"
                        " OR location LIKE '%, NY%' OR location LIKE '%, WA%'"
                        " OR location LIKE '%, TX%' OR location LIKE '%, VA%'"
                        " OR location LIKE '%San Francisco%' OR location LIKE '%New York%'"
                        " OR location LIKE '%Seattle%' OR location LIKE '%Remote - USA%'"
                        " OR location LIKE '%Remote, US%')"
                    )
                elif location == "uk":
                    conditions.append(
                        "(location LIKE '%United Kingdom%' OR location LIKE '%, UK%'"
                        " OR location LIKE '%London%' OR location LIKE '%England%')"
                    )
                elif location == "canada":
                    conditions.append(
                        "(location LIKE '%Canada%' OR location LIKE '%Toronto%'"
                        " OR location LIKE '%Vancouver%' OR location LIKE '%Montreal%')"
                    )
                elif location == "europe":
                    conditions.append(
                        "(location LIKE '%Germany%' OR location LIKE '%France%'"
                        " OR location LIKE '%Netherlands%' OR location LIKE '%Spain%'"
                        " OR location LIKE '%Ireland%' OR location LIKE '%Berlin%'"
                        " OR location LIKE '%Amsterdam%' OR location LIKE '%Europe%')"
                    )
            if status:
                if status == "new":
                    # Jobs with no response tracking entry
                    conditions.append(
                        "id NOT IN (SELECT job_id FROM application_responses WHERE response_type != 'none')"
                    )
                else:
                    conditions.append(
                        "id IN (SELECT job_id FROM application_responses WHERE response_type = ?)"
                    )
                    params.append(status)

            where = " AND ".join(conditions)

            # Sort order: remote first, then by alignment score, then salary
            if sort == "remote_first":
                order = """
                    CASE WHEN remote_type = 'remote' THEN 0
                         WHEN remote_type = 'hybrid' THEN 1
                         ELSE 2 END ASC,
                    COALESCE(alignment_score, 0) DESC,
                    COALESCE(salary_max, 0) DESC,
                    scraped_date DESC
                """
            elif sort == "score":
                order = "COALESCE(alignment_score, 0) DESC, scraped_date DESC"
            elif sort == "salary":
                order = "COALESCE(salary_max, 0) DESC, scraped_date DESC"
            elif sort == "culture":
                order = "COALESCE(company_rating, 0) DESC, COALESCE(alignment_score, 0) DESC, scraped_date DESC"
            elif sort == "date":
                order = "scraped_date DESC"
            else:
                order = "scraped_date DESC"

            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM jobs WHERE {where} ORDER BY {order} LIMIT ?",
                params,
            ).fetchall()
            return [dict(r) for r in rows]

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return dict(row) if row else None

    def get_job_count(self, days: int = 7) -> int:
        with self.get_connection() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM jobs WHERE scraped_date >= ? AND is_active = 1",
                (cutoff,),
            ).fetchone()
            return row["cnt"]

    def get_sources(self) -> List[str]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT source_site FROM jobs WHERE is_active = 1 ORDER BY source_site"
            ).fetchall()
            return [r["source_site"] for r in rows if r["source_site"]]

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            age_filter = " AND (posted_date IS NULL OR posted_date >= ?)"
            base = f"FROM jobs WHERE scraped_date >= ? AND is_active = 1{age_filter}"

            total = conn.execute(
                f"SELECT COUNT(*) as c {base}",
                (cutoff, cutoff),
            ).fetchone()["c"]

            remote = conn.execute(
                f"SELECT COUNT(*) as c {base} AND remote_type = 'remote'",
                (cutoff, cutoff),
            ).fetchone()["c"]

            with_salary = conn.execute(
                f"SELECT COUNT(*) as c {base} AND salary_min IS NOT NULL",
                (cutoff, cutoff),
            ).fetchone()["c"]

            scored = conn.execute(
                f"SELECT COUNT(*) as c {base} AND alignment_score IS NOT NULL",
                (cutoff, cutoff),
            ).fetchone()["c"]

            avg_score = conn.execute(
                f"SELECT AVG(alignment_score) as a {base} AND alignment_score IS NOT NULL",
                (cutoff, cutoff),
            ).fetchone()["a"]

            by_source = {}
            for row in conn.execute(
                f"SELECT source_site, COUNT(*) as c {base} GROUP BY source_site ORDER BY c DESC",
                (cutoff, cutoff),
            ).fetchall():
                by_source[row["source_site"]] = row["c"]

            db_total = conn.execute(
                "SELECT COUNT(*) as c FROM jobs WHERE is_active = 1"
            ).fetchone()["c"]

            return {
                "total": total,
                "remote": remote,
                "with_salary": with_salary,
                "scored": scored,
                "avg_score": round(avg_score, 1) if avg_score else None,
                "by_source": by_source,
                "db_total": db_total,
            }

    # ── LLM Skill Cache ──────────────────────────────────────────────

    def get_cached_skills(self, content_hash: str) -> Optional[Dict]:
        """Get cached LLM skill extraction result, or None if not cached."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT extracted_skills FROM llm_skill_cache WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
            if row:
                return json.loads(row["extracted_skills"])
            return None

    def cache_skills(
        self, content_hash: str, text_type: str, skills: Dict, model: str
    ):
        """Cache LLM skill extraction result."""
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO llm_skill_cache
                   (content_hash, text_type, extracted_skills, model, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    content_hash,
                    text_type,
                    json.dumps(skills),
                    model,
                    datetime.now().isoformat(),
                ),
            )

    # ── Alignment Score ─────────────────────────────────────────────

    def update_alignment_score(
        self,
        job_id: int,
        score: float,
        details: Optional[Dict] = None,
        semantic_score: Optional[float] = None,
    ):
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE jobs
                   SET alignment_score = ?,
                       alignment_details = ?,
                       semantic_alignment_score = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (
                    score,
                    json.dumps(details) if details else None,
                    semantic_score,
                    datetime.now().isoformat(),
                    job_id,
                ),
            )

    def update_career_page_verification(
        self,
        job_id: int,
        verified: Optional[bool],
        details: Optional[Dict] = None,
    ):
        """Update career page verification result for a job."""
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE jobs
                   SET career_page_verified = ?,
                       career_page_json = ?,
                       career_page_checked_at = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (
                    1 if verified is True else (0 if verified is False else None),
                    json.dumps(details) if details else None,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    job_id,
                ),
            )

    def get_unscored_jobs(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """Get jobs that haven't been scored yet."""
        with self.get_connection() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                """SELECT id, title, company, description, remote_type
                   FROM jobs
                   WHERE scraped_date >= ? AND is_active = 1
                     AND alignment_score IS NULL
                     AND description IS NOT NULL AND LENGTH(description) > 50
                   ORDER BY scraped_date DESC
                   LIMIT ?""",
                (cutoff, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Application Packages ────────────────────────────────────────

    def create_application_package(self, job_id: int) -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            c = conn.execute(
                """INSERT INTO application_packages (job_id, status, created_at, updated_at)
                   VALUES (?, 'pending', ?, ?)""",
                (job_id, now, now),
            )
            return c.lastrowid

    def update_application_package(
        self,
        pkg_id: int,
        resume_text: Optional[str] = None,
        cover_letter_text: Optional[str] = None,
        status: str = "generated",
        ai_model: Optional[str] = None,
        ai_provider: Optional[str] = None,
    ):
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE application_packages
                   SET resume_text = COALESCE(?, resume_text),
                       cover_letter_text = COALESCE(?, cover_letter_text),
                       status = ?,
                       generated_at = ?,
                       updated_at = ?,
                       ai_model = COALESCE(?, ai_model),
                       ai_provider = COALESCE(?, ai_provider)
                   WHERE id = ?""",
                (resume_text, cover_letter_text, status, now, now, ai_model, ai_provider, pkg_id),
            )

    def get_application_package(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM application_packages WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
                (job_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_job_ids_with_packages(self) -> Dict[int, str]:
        """Return {job_id: status} for all jobs that have generated packages."""
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT job_id, status FROM application_packages
                   WHERE status = 'generated'
                   GROUP BY job_id""",
            ).fetchall()
            return {r["job_id"]: r["status"] for r in rows}

    def get_packages_by_status(self, status: str = "pending") -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT ap.*, j.title, j.company, j.description
                   FROM application_packages ap
                   JOIN jobs j ON j.id = ap.job_id
                   WHERE ap.status = ?
                   ORDER BY ap.created_at DESC""",
                (status,),
            ).fetchall()
            return [dict(r) for r in rows]

    def set_package_ready(self, job_id: int, package_id: int, generation_log: dict) -> None:
        """
        Set job status to 'package_ready' and log generation metadata.
        Called after clean validation (no fabrication_errors).
        Never called if fabrication_errors is non-empty.
        """
        with self.get_connection() as conn:
            # Update job status
            conn.execute(
                "UPDATE jobs SET status = 'package_ready' WHERE id = ?",
                (job_id,)
            )

            # Write generation log
            conn.execute("""
                INSERT INTO generation_log
                (job_id, resume_version, job_category, verified_tools, blocked_tools,
                 gap_flags, fabrication_errors, formatting_warnings, score_before,
                 score_after, requires_review, validation_passed, provider)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                generation_log.get("base_resume_version"),
                generation_log.get("job_category"),
                json.dumps(generation_log.get("verified_tools_used", [])),
                json.dumps(generation_log.get("blocked_tools_in_jd", [])),
                json.dumps(generation_log.get("gap_flags", [])),
                json.dumps(generation_log.get("fabrication_errors", [])),
                json.dumps(generation_log.get("formatting_warnings", [])),
                generation_log.get("score_before", 0),
                generation_log.get("post_gen_score", 0),
                1 if generation_log.get("requires_human_review") else 0,
                1 if generation_log.get("validation_passed") else 0,
                generation_log.get("provider", "unknown"),
            ))

    # ── Application Responses ────────────────────────────────────────

    def record_response(self, job_id: int, response_type: str, notes: str = "") -> int:
        """Create a response record for a job application."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            # Look up source_site from the jobs table
            job = conn.execute(
                "SELECT source_site FROM jobs WHERE id = ?", (job_id,)
            ).fetchone()
            source_site = job["source_site"] if job else None

            c = conn.execute(
                """INSERT INTO application_responses
                   (job_id, source_site, response_type, responded_at, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (job_id, source_site, response_type, now, notes, now, now),
            )
            return c.lastrowid

    def get_response(self, job_id: int) -> Optional[Dict]:
        """Get the latest response for a job."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM application_responses WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
                (job_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_responses_for_jobs(self, job_ids: List[int]) -> Dict[int, Dict]:
        """Get latest response for multiple jobs at once (bulk lookup)."""
        if not job_ids:
            return {}
        with self.get_connection() as conn:
            placeholders = ",".join("?" * len(job_ids))
            rows = conn.execute(
                f"""SELECT ar.* FROM application_responses ar
                    INNER JOIN (
                        SELECT job_id, MAX(created_at) as max_created
                        FROM application_responses
                        WHERE job_id IN ({placeholders})
                        GROUP BY job_id
                    ) latest ON ar.job_id = latest.job_id AND ar.created_at = latest.max_created""",
                job_ids,
            ).fetchall()
            return {row["job_id"]: dict(row) for row in rows}

    def get_response_rates(self, days: int = 30) -> Dict:
        """Calculate response rates by source_site over the given period."""
        with self.get_connection() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            # Total applications per source (from responses table which has source_site)
            totals = {}
            for row in conn.execute(
                """SELECT source_site, COUNT(DISTINCT job_id) as c
                   FROM application_responses
                   WHERE created_at >= ? AND source_site IS NOT NULL
                   GROUP BY source_site""",
                (cutoff,),
            ).fetchall():
                totals[row["source_site"]] = row["c"]

            # Responded counts per source (non-'none' responses)
            responded = {}
            for row in conn.execute(
                """SELECT source_site, COUNT(DISTINCT job_id) as c
                   FROM application_responses
                   WHERE created_at >= ? AND response_type != 'none'
                     AND source_site IS NOT NULL
                   GROUP BY source_site""",
                (cutoff,),
            ).fetchall():
                responded[row["source_site"]] = row["c"]

            result = {}
            for site, total in totals.items():
                resp = responded.get(site, 0)
                result[site] = {
                    "total": total,
                    "responded": resp,
                    "rate": round((resp / total) * 100, 1) if total else 0.0,
                }
            return result

    def get_response_summary(self) -> Dict:
        """Overall response stats: total applications, responses, rate, avg time."""
        with self.get_connection() as conn:
            total_apps = conn.execute(
                "SELECT COUNT(*) as c FROM application_packages"
            ).fetchone()["c"]

            total_responses = conn.execute(
                "SELECT COUNT(*) as c FROM application_responses WHERE response_type != 'none'"
            ).fetchone()["c"]

            rate = round((total_responses / total_apps) * 100, 1) if total_apps else 0.0

            # Average time to response (days between application creation and response)
            avg_row = conn.execute(
                """SELECT AVG(
                       julianday(ar.responded_at) - julianday(ap.created_at)
                   ) as avg_days
                   FROM application_responses ar
                   JOIN application_packages ap ON ap.job_id = ar.job_id
                   WHERE ar.response_type != 'none'
                     AND ar.responded_at IS NOT NULL"""
            ).fetchone()
            avg_days = round(avg_row["avg_days"], 1) if avg_row["avg_days"] else None

            return {
                "total_applications": total_apps,
                "total_responses": total_responses,
                "response_rate": rate,
                "avg_days_to_response": avg_days,
            }

    # ── API Usage Tracking ──────────────────────────────────────────

    def log_api_usage(
        self,
        service: str,
        endpoint: str = "",
        tokens_used: int = 0,
        cost_estimate: float = 0.0,
        success: bool = True,
        error_message: str = "",
    ):
        """Log an API call for usage tracking."""
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO api_usage_log
                   (service, endpoint, tokens_used, cost_estimate, success, error_message, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (service, endpoint, tokens_used, cost_estimate, 1 if success else 0,
                 error_message, datetime.now().isoformat()),
            )

    def get_api_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get API usage summary for the given period."""
        with self.get_connection() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            services = {}
            for row in conn.execute(
                """SELECT service,
                          COUNT(*) as total_calls,
                          SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                          SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                          SUM(tokens_used) as total_tokens,
                          SUM(cost_estimate) as total_cost
                   FROM api_usage_log
                   WHERE created_at >= ?
                   GROUP BY service""",
                (cutoff,),
            ).fetchall():
                services[row["service"]] = {
                    "total_calls": row["total_calls"],
                    "successful": row["successful"],
                    "failed": row["failed"],
                    "total_tokens": row["total_tokens"] or 0,
                    "total_cost": round(row["total_cost"] or 0, 4),
                }
            return services

    def get_api_usage_daily(self, service: str, days: int = 30) -> List[Dict]:
        """Get daily API usage for a specific service."""
        with self.get_connection() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                """SELECT DATE(created_at) as date,
                          COUNT(*) as calls,
                          SUM(tokens_used) as tokens,
                          SUM(cost_estimate) as cost
                   FROM api_usage_log
                   WHERE service = ? AND created_at >= ?
                   GROUP BY DATE(created_at)
                   ORDER BY date""",
                (service, cutoff),
            ).fetchall()
            return [dict(r) for r in rows]
