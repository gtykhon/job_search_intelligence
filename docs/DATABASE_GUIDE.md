# 💾 Database Guide

> **Complete guide to the SQLite job tracking database**

This guide covers the database schema, Python API, and SQL queries for the job tracking system.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Database Schema](#database-schema)
- [Python API](#python-api)
- [SQL Queries](#sql-queries)
- [Data Integrity](#data-integrity)
- [Maintenance](#maintenance)
- [Examples](#examples)

---

## Overview

### Database Details

- **Type:** SQLite 3
- **Location:** `data/job_tracker.db`
- **Size:** ~50-100KB per 100 jobs
- **Engine:** SQLite3 (bundled with Python)

### Why SQLite?

✅ **Advantages:**
- Zero configuration
- Single file storage
- ACID compliance
- Fast for read-heavy workloads
- No server required
- Portable across platforms

❌ **Limitations:**
- Single writer at a time
- Not suitable for high-concurrency writes
- Limited to ~140TB database size (not a concern)

### Tables

1. **jobs** - Main job listings storage
2. **applications** - Application tracking
3. **search_history** - Search query logs
4. **job_matches** - Job scoring/matching (future)

---

## Database Schema

### jobs Table

Primary table for storing scraped job postings.

```sql
CREATE TABLE jobs (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Core Fields (Required)
    job_url TEXT NOT NULL UNIQUE,           -- Unique job URL
    title TEXT NOT NULL,                    -- Job title
    company TEXT NOT NULL,                  -- Company name
    location TEXT NOT NULL,                 -- Job location
    
    -- Detailed Information
    description TEXT,                       -- Full job description
    job_type TEXT,                          -- full-time, part-time, etc.
    remote_type TEXT,                       -- remote, hybrid, on-site
    
    -- Salary Information
    salary_min REAL,                        -- Minimum salary
    salary_max REAL,                        -- Maximum salary
    salary_currency TEXT DEFAULT 'USD',     -- Currency code
    
    -- Dates
    posted_date TEXT,                       -- When job was posted
    scraped_date TEXT NOT NULL,             -- When we found it
    first_seen TEXT NOT NULL,               -- First time seen
    last_seen TEXT NOT NULL,                -- Most recent scrape
    
    -- Source Information
    source_site TEXT,                       -- indeed, linkedin, etc.
    
    -- Company Intelligence
    company_url TEXT,                       -- Company website
    company_rating REAL,                    -- Rating (0-5)
    company_reviews_count INTEGER,          -- Number of reviews
    company_industry TEXT,                  -- Industry/sector
    company_size TEXT,                      -- Employee count range
    
    -- Contact Information
    contact_email TEXT,                     -- Contact email if available
    contact_phone TEXT,                     -- Contact phone if available
    
    -- Job Requirements
    experience_level TEXT,                  -- entry, mid, senior, etc.
    education_required TEXT,                -- Degree requirements
    clearance_required INTEGER DEFAULT 0,   -- Security clearance (0/1)
    
    -- Location Details
    metro_accessible INTEGER DEFAULT 0,     -- Metro accessible (0/1)
    latitude REAL,                          -- Latitude coordinate
    longitude REAL,                         -- Longitude coordinate
    
    -- Metadata
    is_active INTEGER DEFAULT 1,            -- Active listing (0/1)
    notes TEXT                              -- User notes
);
```

#### Key Fields Explained

**job_url** (TEXT, UNIQUE, NOT NULL)
- Primary deduplication field
- Full URL to job posting
- Example: `https://www.indeed.com/viewjob?jk=abc123`

**title** (TEXT, NOT NULL)
- Job title as listed by employer
- Examples: "Senior Python Developer", "ML Engineer"

**company** (TEXT, NOT NULL)
- Company name
- Normalized where possible

**location** (TEXT, NOT NULL)
- Job location string
- Format varies: "Washington, DC", "Remote", "Arlington, VA 22201"

**description** (TEXT)
- Full job description (HTML or plain text)
- Can be very long (10KB+)

**job_type** (TEXT)
- Values: `full-time`, `part-time`, `contract`, `temporary`, `internship`
- May be NULL if not specified

**remote_type** (TEXT)
- Values: `remote`, `hybrid`, `on-site`
- May be NULL

**salary_min / salary_max** (REAL)
- Numeric salary values
- Currency specified in salary_currency
- Example: 120000.0 for $120K

**posted_date** (TEXT)
- ISO 8601 format: `2024-12-11T14:30:00`
- May be NULL if not available

**scraped_date** (TEXT, NOT NULL)
- When we scraped this listing
- ISO 8601 format

**first_seen / last_seen** (TEXT, NOT NULL)
- Tracks job lifecycle
- Used for "still active" determination
- Both set to scraped_date on first insert
- last_seen updated on subsequent scrapes

**source_site** (TEXT)
- Values: `indeed`, `linkedin`, `glassdoor`, `google_jobs`

**clearance_required** (INTEGER, 0/1)
- 1 if security clearance mentioned
- Detected from keywords in description

**metro_accessible** (INTEGER, 0/1)
- 1 if near DC metro (specific to this project)
- Can be repurposed for other transit systems

---

### applications Table

Track application status and follow-ups.

```sql
CREATE TABLE applications (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Key
    job_id INTEGER NOT NULL,
    
    -- Application Info
    applied_date TEXT NOT NULL,             -- When applied
    status TEXT DEFAULT 'interested',       -- Application status
    
    -- Contact Information
    recruiter_name TEXT,                    -- Recruiter name
    recruiter_email TEXT,                   -- Recruiter email
    recruiter_phone TEXT,                   -- Recruiter phone
    
    -- Timeline
    interview_date TEXT,                    -- Interview scheduled
    follow_up_date TEXT,                    -- Next follow-up
    offer_date TEXT,                        -- Offer received
    
    -- Details
    application_notes TEXT,                 -- Notes about application
    resume_version TEXT,                    -- Which resume used
    cover_letter_sent INTEGER DEFAULT 0,    -- Cover letter sent (0/1)
    
    -- Outcome
    outcome TEXT,                           -- Final outcome
    outcome_date TEXT,                      -- When outcome determined
    
    -- Foreign Key Constraint
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

#### Application Status Values

- `interested` - Job saved but not applied
- `applied` - Application submitted
- `phone_screen` - Phone interview scheduled/completed
- `interviewing` - In interview process
- `offer` - Offer received
- `accepted` - Offer accepted
- `rejected` - Rejected by company
- `declined` - Declined by candidate
- `withdrawn` - Application withdrawn

---

### search_history Table

Log all search queries for analytics.

```sql
CREATE TABLE search_history (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Search Parameters
    keywords TEXT NOT NULL,                 -- Search keywords
    location TEXT NOT NULL,                 -- Search location
    job_sites TEXT NOT NULL,                -- Sites searched (JSON array)
    
    -- Results
    results_count INTEGER NOT NULL,         -- Number of results
    
    -- Filters Applied
    job_type TEXT,                          -- Job type filter
    remote_type TEXT,                       -- Remote type filter
    posted_since_days INTEGER,              -- Recency filter
    
    -- Metadata
    search_date TEXT NOT NULL,              -- When searched
    execution_time_seconds REAL             -- How long it took
);
```

**Purpose:** Track what you've searched to:
- Avoid duplicate searches
- Analyze which queries are most productive
- Monitor scraping performance over time

---

### job_matches Table

Store job scoring and matching (future feature).

```sql
CREATE TABLE job_matches (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Key
    job_id INTEGER NOT NULL,
    
    -- Scoring
    match_score REAL,                       -- 0.0 - 1.0 match score
    
    -- Match Reasons
    skills_matched TEXT,                    -- Skills that matched (JSON)
    keywords_matched TEXT,                  -- Keywords that matched (JSON)
    
    -- Metadata
    scored_date TEXT NOT NULL,              -- When scored
    scoring_model TEXT,                     -- Which model/algorithm
    
    -- Foreign Key Constraint
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

**Future feature** for AI-powered job matching based on resume and preferences.

---

## Python API

### JobDatabase Class

Located in `src/intelligence/job_database.py`

#### Initialization

```python
from src.intelligence.job_database import JobDatabase

# Default location (data/job_tracker.db)
db = JobDatabase()

# Custom location
db = JobDatabase(db_path="path/to/custom.db")
```

#### Context Manager

```python
# Automatically handles connection opening/closing
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
```

---

### Save Job

Insert or update job listing with automatic deduplication.

```python
from src.intelligence.models import JobListing

job = JobListing(
    title="Python Developer",
    company="Acme Corp",
    location="Washington, DC",
    job_url="https://example.com/job/123",
    salary_min=120000,
    salary_max=150000,
    # ... other fields
)

db.save_job(job)
```

**Behavior:**
- If job_url exists: Updates last_seen, keeps first_seen unchanged
- If job_url is new: Inserts with first_seen = last_seen = now
- Returns: None

**Deduplication:** Uses `job_url` as unique constraint

---

### Get Recent Jobs

Retrieve jobs from the last N days.

```python
# Get jobs from last 7 days
recent_jobs = db.get_recent_jobs(days=7, limit=50)

for job in recent_jobs:
    print(f"{job['title']} at {job['company']}")
    print(f"  Salary: ${job['salary_min']:,.0f} - ${job['salary_max']:,.0f}")
    print(f"  URL: {job['job_url']}")
```

**Parameters:**
- `days` (int): How many days back to look
- `limit` (int, optional): Max number of results

**Returns:** List of dictionaries with job data

---

### Get Statistics

Comprehensive database statistics.

```python
stats = db.get_statistics()

print(f"Total jobs: {stats['total_jobs']}")
print(f"Jobs with salary: {stats['jobs_with_salary']}")
print(f"Average salary: ${stats['avg_salary_min']:,.0f} - ${stats['avg_salary_max']:,.0f}")
print(f"\nJobs by source:")
for source, count in stats['jobs_by_source'].items():
    print(f"  {source}: {count}")
```

**Returns:** Dictionary with:
- `total_jobs` (int): Total job count
- `jobs_with_salary` (int): Jobs with salary data
- `avg_salary_min` (float): Average minimum salary
- `avg_salary_max` (float): Average maximum salary
- `jobs_by_source` (dict): Count by source site
- `applications_by_status` (dict): Application counts by status

---

### Save Search History

Log a search query.

```python
db.save_search_history(
    keywords="Python Developer",
    location="Washington, DC",
    job_sites=["indeed", "linkedin"],
    results_count=45,
    job_type="full-time",
    remote_type=None,
    posted_since_days=7,
    execution_time_seconds=12.5
)
```

**Purpose:** Track search effectiveness and avoid duplicates

---

### Get All Jobs

Retrieve all jobs (use carefully for large databases).

```python
all_jobs = db.get_all_jobs()
print(f"Total jobs: {len(all_jobs)}")
```

**Warning:** Can be memory-intensive with thousands of jobs. Consider using `get_recent_jobs()` or SQL queries with LIMIT.

---

### Custom Queries

Direct SQL access for advanced queries.

```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    
    # Custom query
    cursor.execute("""
        SELECT company, COUNT(*) as job_count
        FROM jobs
        WHERE salary_min >= 150000
        GROUP BY company
        ORDER BY job_count DESC
        LIMIT 10
    """)
    
    top_companies = cursor.fetchall()
    for company, count in top_companies:
        print(f"{company}: {count} jobs")
```

---

## SQL Queries

### Common Queries

#### Count Total Jobs

```sql
SELECT COUNT(*) FROM jobs;
```

#### Jobs by Source

```sql
SELECT source_site, COUNT(*) as count
FROM jobs
GROUP BY source_site
ORDER BY count DESC;
```

#### Average Salary

```sql
SELECT 
    AVG(salary_min) as avg_min,
    AVG(salary_max) as avg_max,
    COUNT(*) as count
FROM jobs
WHERE salary_min IS NOT NULL;
```

#### Recent High-Paying Jobs

```sql
SELECT title, company, location, salary_min, salary_max, job_url
FROM jobs
WHERE salary_min >= 150000
  AND scraped_date >= date('now', '-7 days')
ORDER BY salary_min DESC
LIMIT 20;
```

#### Top Hiring Companies

```sql
SELECT company, COUNT(*) as openings
FROM jobs
WHERE is_active = 1
GROUP BY company
ORDER BY openings DESC
LIMIT 10;
```

#### Remote Jobs

```sql
SELECT title, company, salary_min, salary_max, job_url
FROM jobs
WHERE remote_type = 'remote'
  AND salary_min >= 100000
ORDER BY scraped_date DESC;
```

#### Jobs by Location

```sql
SELECT location, COUNT(*) as count
FROM jobs
GROUP BY location
ORDER BY count DESC
LIMIT 10;
```

#### Jobs Seen Multiple Times

```sql
SELECT title, company, first_seen, last_seen,
       julianday(last_seen) - julianday(first_seen) as days_active
FROM jobs
WHERE first_seen != last_seen
ORDER BY days_active DESC;
```

---

### Advanced Queries

#### Salary Distribution

```sql
SELECT 
    CASE 
        WHEN salary_min < 80000 THEN '< $80K'
        WHEN salary_min < 100000 THEN '$80K - $100K'
        WHEN salary_min < 120000 THEN '$100K - $120K'
        WHEN salary_min < 150000 THEN '$120K - $150K'
        ELSE '> $150K'
    END as salary_range,
    COUNT(*) as count
FROM jobs
WHERE salary_min IS NOT NULL
GROUP BY salary_range
ORDER BY MIN(salary_min);
```

#### Companies with Highest Ratings

```sql
SELECT company, company_rating, company_reviews_count, COUNT(*) as job_count
FROM jobs
WHERE company_rating IS NOT NULL
GROUP BY company
HAVING company_reviews_count >= 10
ORDER BY company_rating DESC, company_reviews_count DESC
LIMIT 10;
```

#### Application Success Rate

```sql
SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM applications), 2) as percentage
FROM applications
GROUP BY status
ORDER BY count DESC;
```

#### Search Effectiveness

```sql
SELECT 
    keywords,
    COUNT(*) as search_count,
    AVG(results_count) as avg_results,
    MAX(results_count) as max_results
FROM search_history
GROUP BY keywords
ORDER BY avg_results DESC;
```

#### Jobs Requiring Clearance

```sql
SELECT title, company, location, salary_min, job_url
FROM jobs
WHERE clearance_required = 1
ORDER BY salary_min DESC;
```

---

## Data Integrity

### Unique Constraints

- **jobs.job_url** - Prevents duplicate job listings
- **jobs.id** - Primary key (auto-increment)

### Foreign Keys

- **applications.job_id** → **jobs.id**
- **job_matches.job_id** → **jobs.id**

### Indexes

Create indexes for common queries:

```sql
-- Index on source site for filtering
CREATE INDEX IF NOT EXISTS idx_jobs_source_site ON jobs(source_site);

-- Index on salary for filtering
CREATE INDEX IF NOT EXISTS idx_jobs_salary_min ON jobs(salary_min);

-- Index on scraped date for recent queries
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_date ON jobs(scraped_date);

-- Index on remote type
CREATE INDEX IF NOT EXISTS idx_jobs_remote_type ON jobs(remote_type);

-- Index on company for grouping
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
```

### Null Handling

Fields that can be NULL:
- description (some jobs don't provide)
- job_type (not always specified)
- remote_type (may be unclear)
- salary_min/salary_max (often not listed)
- company_rating (not available for all companies)
- Many other optional fields

**Best practice:** Use `IS NULL` or `IS NOT NULL` in WHERE clauses:

```sql
SELECT * FROM jobs WHERE salary_min IS NOT NULL;
```

---

## Maintenance

### Backup Database

```bash
# Simple file copy
cp data/job_tracker.db data/backups/job_tracker_$(date +%Y%m%d).db

# Using SQLite dump
sqlite3 data/job_tracker.db .dump > backup.sql
```

### Restore Database

```bash
# From backup file
cp data/backups/job_tracker_20241211.db data/job_tracker.db

# From SQL dump
sqlite3 data/job_tracker.db < backup.sql
```

### Vacuum Database

Reclaim unused space:

```sql
VACUUM;
```

```python
with db.get_connection() as conn:
    conn.execute("VACUUM")
```

### Clean Old Jobs

Remove jobs older than 90 days:

```sql
DELETE FROM jobs 
WHERE scraped_date < date('now', '-90 days');
```

```python
with db.get_connection() as conn:
    conn.execute("DELETE FROM jobs WHERE scraped_date < date('now', '-90 days')")
    conn.commit()
```

### Update Inactive Jobs

Mark jobs as inactive if not seen recently:

```sql
UPDATE jobs
SET is_active = 0
WHERE last_seen < date('now', '-30 days')
  AND is_active = 1;
```

---

## Examples

### Example 1: High-Paying Remote Jobs

```python
from src.intelligence.job_database import JobDatabase

db = JobDatabase()

with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, company, salary_min, salary_max, job_url
        FROM jobs
        WHERE remote_type = 'remote'
          AND salary_min >= 150000
        ORDER BY salary_min DESC
        LIMIT 20
    """)
    
    jobs = cursor.fetchall()
    
    print("Top 20 High-Paying Remote Jobs:")
    for title, company, sal_min, sal_max, url in jobs:
        print(f"\n{title} at {company}")
        print(f"Salary: ${sal_min:,.0f} - ${sal_max:,.0f}")
        print(f"URL: {url}")
```

### Example 2: Application Tracking

```python
# Add application
with db.get_connection() as conn:
    conn.execute("""
        INSERT INTO applications (job_id, applied_date, status, application_notes)
        VALUES (?, ?, ?, ?)
    """, (job_id, "2024-12-11", "applied", "Sent customized resume"))
    conn.commit()

# Update status
with db.get_connection() as conn:
    conn.execute("""
        UPDATE applications
        SET status = 'interviewing',
            interview_date = ?
        WHERE id = ?
    """, ("2024-12-15", application_id))
    conn.commit()

# Get applications
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.title, j.company, a.status, a.applied_date, a.interview_date
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status IN ('applied', 'interviewing')
        ORDER BY a.applied_date DESC
    """)
    
    for title, company, status, applied, interview in cursor.fetchall():
        print(f"{title} at {company} - {status}")
        print(f"  Applied: {applied}")
        if interview:
            print(f"  Interview: {interview}")
```

### Example 3: Search Analytics

```python
# Most productive searches
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT keywords, location,
               COUNT(*) as searches,
               AVG(results_count) as avg_results,
               SUM(results_count) as total_results
        FROM search_history
        GROUP BY keywords, location
        ORDER BY total_results DESC
        LIMIT 10
    """)
    
    print("Top 10 Most Productive Searches:")
    for kw, loc, count, avg, total in cursor.fetchall():
        print(f"\n{kw} in {loc}")
        print(f"  Searches: {count}")
        print(f"  Avg results: {avg:.1f}")
        print(f"  Total results: {total}")
```

### Example 4: Company Analysis

```python
# Companies with most openings and best ratings
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            company,
            COUNT(*) as job_count,
            AVG(company_rating) as avg_rating,
            AVG(salary_min) as avg_salary,
            MAX(salary_max) as max_salary
        FROM jobs
        WHERE is_active = 1
          AND company_rating IS NOT NULL
        GROUP BY company
        HAVING job_count >= 3
        ORDER BY avg_rating DESC, job_count DESC
        LIMIT 10
    """)
    
    print("Top Companies to Apply To:")
    for company, jobs, rating, avg_sal, max_sal in cursor.fetchall():
        print(f"\n{company}")
        print(f"  Rating: {rating:.1f}/5.0")
        print(f"  Open positions: {jobs}")
        print(f"  Avg salary: ${avg_sal:,.0f}")
        print(f"  Max salary: ${max_sal:,.0f}")
```

---

## Best Practices

### 1. Use Context Managers

```python
# Good - automatic cleanup
with db.get_connection() as conn:
    conn.execute("SELECT * FROM jobs")

# Bad - manual cleanup required
conn = db.get_connection()
conn.execute("SELECT * FROM jobs")
conn.close()  # Easy to forget
```

### 2. Parameterized Queries

```python
# Good - prevents SQL injection
cursor.execute("SELECT * FROM jobs WHERE company = ?", (company_name,))

# Bad - vulnerable to SQL injection
cursor.execute(f"SELECT * FROM jobs WHERE company = '{company_name}'")
```

### 3. Batch Inserts

```python
# Good - single transaction
jobs_data = [(job.title, job.company, job.url) for job in jobs]
with db.get_connection() as conn:
    conn.executemany("INSERT INTO jobs (title, company, job_url) VALUES (?, ?, ?)", jobs_data)
    conn.commit()

# Bad - multiple transactions
for job in jobs:
    db.save_job(job)  # Commits each time
```

### 4. Regular Backups

```python
import shutil
from datetime import datetime

def backup_database():
    source = "data/job_tracker.db"
    backup_dir = "data/backups"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = f"{backup_dir}/job_tracker_{timestamp}.db"
    
    shutil.copy2(source, destination)
    print(f"Backed up to {destination}")
```

---

## Troubleshooting

### Database Locked

**Error:** `sqlite3.OperationalError: database is locked`

**Cause:** Another process has the database open with a write lock

**Solution:**
- Close other connections
- Use context managers for automatic cleanup
- Reduce transaction time

### Too Many SQL Variables

**Error:** `sqlite3.OperationalError: too many SQL variables`

**Cause:** SQLite has default limit of 999 parameters

**Solution:**
```python
# Batch into chunks of 500
chunk_size = 500
for i in range(0, len(jobs), chunk_size):
    chunk = jobs[i:i + chunk_size]
    # Process chunk
```

### Slow Queries

**Solution:** Add indexes

```python
with db.get_connection() as conn:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_salary ON jobs(salary_min)")
    conn.commit()
```

---

## Additional Resources

- **SQLite Documentation:** https://www.sqlite.org/docs.html
- **Python sqlite3:** https://docs.python.org/3/library/sqlite3.html
- **Our JobSpy Guide:** [JOBSPY_INTEGRATION.md](JOBSPY_INTEGRATION.md)
- **Dashboard Guide:** [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)

---

**Need help?** Open an issue or contact the maintainers.
