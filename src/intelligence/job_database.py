"""
Job Tracking Database Schema and Management
SQLite database for tracking job postings, applications, and search history
"""

import re
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def _clean_description(text: Optional[str]) -> Optional[str]:
    """Strip HTML tags, Markdown artifacts, and normalize whitespace.

    Centralised cleaner so every scraper benefits regardless of
    whether it does its own HTML/Markdown stripping.
    """
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
    text = re.sub(r"\*{2,3}(.+?)\*{2,3}", r"\1", text)
    text = re.sub(r"_{2,3}(.+?)_{2,3}", r"\1", text)
    text = re.sub(r"\\([*\-\.#\[\]\(\)&!>`~|])", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"^\\?\*\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # ── Whitespace normalization ──
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class JobDatabase:
    """Manages SQLite database for job tracking"""
    
    def __init__(self, db_path: str = "data/job_tracker.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Jobs table - stores all scraped jobs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_url TEXT UNIQUE NOT NULL,
                    job_id TEXT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    
                    -- Job details
                    job_type TEXT,
                    remote_type TEXT,
                    experience_level TEXT,
                    
                    -- Salary information
                    salary_min REAL,
                    salary_max REAL,
                    salary_currency TEXT DEFAULT 'USD',
                    salary_period TEXT DEFAULT 'yearly',
                    
                    -- Dates
                    posted_date TEXT,
                    scraped_date TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    
                    -- Source
                    source_site TEXT NOT NULL,
                    
                    -- DC area specific
                    clearance_required TEXT,
                    metro_accessible INTEGER,
                    
                    -- Company info
                    company_url TEXT,
                    company_industry TEXT,
                    company_num_employees TEXT,
                    company_staff_count INTEGER,
                    company_rating REAL,
                    company_reviews_count INTEGER,

                    -- Voyager enrichment (applicant & poster data)
                    applicant_count INTEGER,
                    hiring_manager_name TEXT,
                    hiring_manager_title TEXT,
                    hiring_manager_url TEXT,
                    listed_at_ms INTEGER,
                    original_listed_at_ms INTEGER,

                    -- Metadata
                    is_active INTEGER DEFAULT 1,
                    views_count INTEGER DEFAULT 0,
                    
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Applications table - track job applications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    
                    -- Application status
                    status TEXT NOT NULL DEFAULT 'interested',
                    -- Status options: interested, applied, interviewing, offer, rejected, accepted, withdrawn
                    
                    applied_date TEXT,
                    response_date TEXT,
                    
                    -- Application details
                    resume_version TEXT,
                    cover_letter TEXT,
                    contact_name TEXT,
                    contact_email TEXT,
                    
                    -- Follow-up tracking
                    follow_up_date TEXT,
                    follow_up_count INTEGER DEFAULT 0,
                    
                    -- Notes
                    notes TEXT,
                    
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            ''')
            
            # Search history table - track search queries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    
                    keywords TEXT NOT NULL,
                    location TEXT,
                    job_sites TEXT,  -- JSON array
                    
                    results_count INTEGER,
                    new_jobs_count INTEGER,
                    
                    search_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Job matches table - track match scores and recommendations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    
                    match_score REAL,
                    match_reason TEXT,
                    
                    skills_matched TEXT,  -- JSON array
                    skills_missing TEXT,  -- JSON array
                    
                    created_at TEXT NOT NULL,
                    
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(job_url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_salary ON jobs(salary_min, salary_max)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_posted ON jobs(posted_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source_site)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active)')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id)')

            # F5: Application outcomes table for lessons-learned feedback loop
            cursor.execute('''
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
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_outcomes_applied_date
                    ON application_outcomes(applied_date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_outcomes_outcome
                    ON application_outcomes(outcome)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_outcomes_platform
                    ON application_outcomes(platform)
            ''')

            # F6: Company research cache table
            cursor.execute('''
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
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_cache_name
                    ON company_research_cache(company_name)
            ''')

            logger.info("✅ Database initialized successfully")
    
    def save_job(self, job_data: Dict[str, Any]) -> int:
        """
        Save or update a job posting
        Returns job_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()

            # Clean HTML from description before storing
            if 'description' in job_data and job_data['description']:
                job_data['description'] = _clean_description(job_data['description'])

            # Check if job exists
            cursor.execute('SELECT id, first_seen FROM jobs WHERE job_url = ?', (job_data['job_url'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing job
                job_id = existing['id']
                first_seen = existing['first_seen']
                
                cursor.execute('''
                    UPDATE jobs SET
                        title = ?,
                        company = ?,
                        location = ?,
                        description = ?,
                        job_type = ?,
                        remote_type = ?,
                        salary_min = ?,
                        salary_max = ?,
                        posted_date = ?,
                        last_seen = ?,
                        source_site = ?,
                        clearance_required = ?,
                        metro_accessible = ?,
                        company_url = ?,
                        company_industry = ?,
                        company_rating = ?,
                        company_staff_count = COALESCE(?, company_staff_count),
                        applicant_count = COALESCE(?, applicant_count),
                        hiring_manager_name = COALESCE(?, hiring_manager_name),
                        hiring_manager_title = COALESCE(?, hiring_manager_title),
                        hiring_manager_url = COALESCE(?, hiring_manager_url),
                        listed_at_ms = COALESCE(?, listed_at_ms),
                        original_listed_at_ms = COALESCE(?, original_listed_at_ms),
                        updated_at = ?
                    WHERE id = ?
                ''', (
                    job_data.get('title'),
                    job_data.get('company'),
                    job_data.get('location'),
                    job_data.get('description'),
                    job_data.get('job_type'),
                    job_data.get('remote_type'),
                    job_data.get('salary_min'),
                    job_data.get('salary_max'),
                    job_data.get('posted_date'),
                    now,
                    job_data.get('source_site'),
                    job_data.get('clearance_required'),
                    job_data.get('metro_accessible'),
                    job_data.get('company_url'),
                    job_data.get('company_industry'),
                    job_data.get('company_rating'),
                    job_data.get('company_staff_count'),
                    job_data.get('applicant_count'),
                    job_data.get('hiring_manager_name'),
                    job_data.get('hiring_manager_title'),
                    job_data.get('hiring_manager_url'),
                    job_data.get('listed_at_ms'),
                    job_data.get('original_listed_at_ms'),
                    now,
                    job_id
                ))
                
                logger.debug(f"Updated job {job_id}: {job_data.get('title')}")
                
            else:
                # Insert new job
                cursor.execute('''
                    INSERT INTO jobs (
                        job_url, job_id, title, company, location, description,
                        job_type, remote_type, experience_level,
                        salary_min, salary_max, salary_currency, salary_period,
                        posted_date, scraped_date, first_seen, last_seen,
                        source_site, clearance_required, metro_accessible,
                        company_url, company_industry, company_num_employees,
                        company_staff_count,
                        company_rating, company_reviews_count,
                        applicant_count, hiring_manager_name, hiring_manager_title,
                        hiring_manager_url, listed_at_ms, original_listed_at_ms,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_data['job_url'],
                    job_data.get('job_id'),
                    job_data['title'],
                    job_data['company'],
                    job_data.get('location'),
                    job_data.get('description'),
                    job_data.get('job_type'),
                    job_data.get('remote_type'),
                    job_data.get('experience_level'),
                    job_data.get('salary_min'),
                    job_data.get('salary_max'),
                    job_data.get('salary_currency', 'USD'),
                    job_data.get('salary_period', 'yearly'),
                    job_data.get('posted_date'),
                    now,
                    now,
                    now,
                    job_data.get('source_site'),
                    job_data.get('clearance_required'),
                    job_data.get('metro_accessible'),
                    job_data.get('company_url'),
                    job_data.get('company_industry'),
                    job_data.get('company_num_employees'),
                    job_data.get('company_staff_count'),
                    job_data.get('company_rating'),
                    job_data.get('company_reviews_count'),
                    job_data.get('applicant_count'),
                    job_data.get('hiring_manager_name'),
                    job_data.get('hiring_manager_title'),
                    job_data.get('hiring_manager_url'),
                    job_data.get('listed_at_ms'),
                    job_data.get('original_listed_at_ms'),
                    now,
                    now
                ))
                
                job_id = cursor.lastrowid
                logger.debug(f"Saved new job {job_id}: {job_data['title']}")
            
            return job_id
    
    def save_search_history(self, keywords: str, location: str, job_sites: List[str], 
                           results_count: int, new_jobs_count: int) -> int:
        """Save search history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            import json
            cursor.execute('''
                INSERT INTO search_history (
                    keywords, location, job_sites, results_count, new_jobs_count,
                    search_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                keywords,
                location,
                json.dumps(job_sites),
                results_count,
                new_jobs_count,
                now,
                now
            ))
            
            return cursor.lastrowid
    
    def get_recent_jobs(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs scraped in the last N days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                SELECT * FROM jobs
                WHERE scraped_date >= ? AND is_active = 1
                ORDER BY posted_date DESC, scraped_date DESC
                LIMIT ?
            ''', (cutoff_date, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total jobs
            cursor.execute('SELECT COUNT(*) as count FROM jobs WHERE is_active = 1')
            stats['total_jobs'] = cursor.fetchone()['count']
            
            # Jobs by source
            cursor.execute('''
                SELECT source_site, COUNT(*) as count
                FROM jobs WHERE is_active = 1
                GROUP BY source_site
                ORDER BY count DESC
            ''')
            stats['by_source'] = {row['source_site']: row['count'] for row in cursor.fetchall()}
            
            # Jobs with salary
            cursor.execute('''
                SELECT COUNT(*) as count FROM jobs
                WHERE is_active = 1 AND (salary_min IS NOT NULL OR salary_max IS NOT NULL)
            ''')
            stats['with_salary'] = cursor.fetchone()['count']
            
            # Average salary
            cursor.execute('''
                SELECT AVG(salary_min) as avg_min, AVG(salary_max) as avg_max
                FROM jobs WHERE is_active = 1 AND salary_min IS NOT NULL
            ''')
            row = cursor.fetchone()
            stats['avg_salary_min'] = row['avg_min']
            stats['avg_salary_max'] = row['avg_max']
            
            # Applications count
            cursor.execute('SELECT COUNT(*) as count FROM applications')
            stats['total_applications'] = cursor.fetchone()['count']
            
            # Applications by status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM applications
                GROUP BY status
                ORDER BY count DESC
            ''')
            stats['applications_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

            return stats

    def update_job_field(self, job_id, field_name: str, value) -> bool:
        """Update a single field on a job record. Creates column if it doesn't exist."""
        try:
            with self.get_connection() as conn:
                # Try direct update first
                try:
                    conn.execute(
                        f"UPDATE jobs SET {field_name} = ? WHERE id = ? OR job_url = ?",
                        (value, job_id, str(job_id))
                    )
                    return True
                except Exception:
                    # Column may not exist — add it
                    try:
                        conn.execute(f"ALTER TABLE jobs ADD COLUMN {field_name} TEXT")
                        conn.execute(
                            f"UPDATE jobs SET {field_name} = ? WHERE id = ? OR job_url = ?",
                            (value, job_id, str(job_id))
                        )
                        return True
                    except Exception:
                        return False
        except Exception:
            return False


if __name__ == "__main__":
    # Test the database
    logging.basicConfig(level=logging.INFO)
    
    db = JobDatabase()
    
    # Test job insertion
    test_job = {
        'job_url': 'https://example.com/job/123',
        'title': 'Senior Python Developer',
        'company': 'Tech Corp',
        'location': 'Washington, DC',
        'description': 'Great opportunity...',
        'salary_min': 120000,
        'salary_max': 180000,
        'source_site': 'indeed',
        'remote_type': 'hybrid'
    }
    
    job_id = db.save_job(test_job)
    print(f"✅ Saved test job with ID: {job_id}")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"\n📊 Database Statistics:")
    print(f"Total Jobs: {stats['total_jobs']}")
    print(f"With Salary: {stats['with_salary']}")
    print(f"Applications: {stats['total_applications']}")
