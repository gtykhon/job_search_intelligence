# 🔍 JobSpy Integration Guide

> **Complete guide to multi-source job scraping with JobSpy**

This guide covers the JobSpy integration that powers real job scraping from Indeed, LinkedIn, Glassdoor, and Google Jobs.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Job Sites](#job-sites)
- [Scraping Requests](#scraping-requests)
- [Configuration](#configuration)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Data Models](#data-models)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What is JobSpy?

[JobSpy](https://github.com/Bunsly/JobSpy) is a Python library that scrapes job postings from multiple sources with built-in anti-scraping bypass mechanisms. Our system wraps JobSpy with:

- **Async support** for concurrent operations
- **Database integration** for persistent storage
- **Smart filtering** for salary and location
- **Retry logic** with circuit breaker pattern
- **Comprehensive error handling**

### Why JobSpy?

**Problems with Direct Scraping:**
- ❌ LinkedIn blocks automated scraping
- ❌ Glassdoor has sophisticated anti-bot measures
- ❌ Indeed changes HTML structure frequently
- ❌ Chrome driver setup complexity

**JobSpy Solutions:**
- ✅ Built-in anti-scraping bypass
- ✅ Standardized data format across sites
- ✅ Active maintenance and updates
- ✅ Simple Python API

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│  daily_jobspy_detection.py (Main Script)                │
│  • Defines search requests                              │
│  • Configures scraper                                   │
│  • Filters and saves results                            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  JobSpyScraper (src/intelligence/jobspy_scraper.py)     │
│  • Wraps JobSpy library                                 │
│  • Converts between data models                         │
│  • Handles async operations                             │
│  • Applies rate limiting                                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  JobSpy Library (python-jobspy)                         │
│  • Scrapes job sites                                    │
│  • Bypasses anti-scraping                               │
│  • Returns pandas DataFrame                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Job Sites: Indeed | LinkedIn | Glassdoor | Google Jobs │
└─────────────────────────────────────────────────────────┘
```

### File Structure

```
src/intelligence/
├── jobspy_scraper.py       # JobSpy wrapper
├── models.py               # Data models & enums
├── job_database.py         # Database integration
├── async_helpers.py        # Retry logic
└── scraping_errors.py      # Custom exceptions

scripts/scheduled_tasks/
└── daily_jobspy_detection.py  # Main scraper script
```

---

## Job Sites

### Supported Sites

| Site | Status | Results per Query | Notes |
|------|--------|------------------|-------|
| **Indeed** | ✅ Working | 25-50 | Best results, most reliable |
| **LinkedIn** | ✅ Working | 20-45 | Good quality, occasional location errors |
| **Glassdoor** | ⚠️ Partial | 10-20 | Location parsing issues |
| **Google Jobs** | ⚠️ Limited | ~10 | Limited to 10 results per query |
| **ZipRecruiter** | ❌ Not Enabled | N/A | Supported by JobSpy but not configured |

### Site-Specific Details

#### Indeed
- **Pros:** Most reliable, highest volume, good salary data
- **Cons:** Some duplicate listings
- **Configuration:** No special config needed
- **Average results:** 30-40 jobs per search

#### LinkedIn
- **Pros:** High-quality jobs, good company data
- **Cons:** Occasional "Invalid country string" errors on remote jobs
- **Configuration:** Works best with specific locations (avoid generic "Remote")
- **Average results:** 20-30 jobs per search

#### Glassdoor
- **Pros:** Includes company reviews and ratings
- **Cons:** Location parsing issues (400 status codes)
- **Configuration:** Needs precise location format (city, state format)
- **Average results:** 10-15 jobs per search
- **Known issues:** "Location not parsed" errors

#### Google Jobs
- **Pros:** Aggregates from multiple sources
- **Cons:** Limited to 10 results, "initial cursor not found" warnings
- **Configuration:** No special config needed
- **Average results:** ~10 jobs per search

---

## Scraping Requests

### ScrapingRequest Model

Defines what to search for:

```python
from src.intelligence.models import ScrapingRequest, JobSite, JobType, RemoteType

request = ScrapingRequest(
    keywords="Python Developer",           # Job title/keywords
    location="Washington, DC",            # City, state format
    job_sites=[                           # Which sites to scrape
        JobSite.INDEED,
        JobSite.LINKEDIN,
        JobSite.GLASSDOOR
    ],
    radius_miles=25,                      # Search radius
    job_type=JobType.FULL_TIME,          # Full-time, part-time, etc.
    remote_type=RemoteType.HYBRID,       # Remote, hybrid, on-site
    posted_since_days=7,                 # Jobs posted in last N days
    max_results=25                        # Max results per site
)
```

### Request Parameters

#### Keywords (Required)
- **Type:** `str`
- **Description:** Job title or keywords to search
- **Examples:**
  - `"Python Developer"`
  - `"Machine Learning Engineer"`
  - `"Senior Software Engineer"`
  - `"Data Scientist Python"`

**Tips:**
- Be specific but not too narrow
- Include seniority level if desired
- Combine role + skill for better results

#### Location (Required)
- **Type:** `str`
- **Description:** City and state for search
- **Format:** `"City, State"` or `"City, ST"`
- **Examples:**
  - `"Washington, DC"`
  - `"Arlington, VA"`
  - `"New York, NY"`
  - `"Remote"` (use cautiously)

**Tips:**
- Use city, state format for best results
- Avoid generic "Remote" (causes LinkedIn errors)
- Include nearby cities for broader search

#### Job Sites (Required)
- **Type:** `List[JobSite]`
- **Description:** Which sites to scrape
- **Options:**
  - `JobSite.INDEED` - Most reliable
  - `JobSite.LINKEDIN` - High quality
  - `JobSite.GLASSDOOR` - Has issues
  - `JobSite.GOOGLE_JOBS` - Limited results
  - `JobSite.ZIP_RECRUITER` - Not configured

**Tips:**
- Start with Indeed + LinkedIn
- Add Glassdoor cautiously (location issues)
- Google Jobs provides limited results

#### Radius Miles (Optional)
- **Type:** `int`
- **Default:** `25`
- **Description:** Search radius from location
- **Examples:** `10`, `25`, `50`, `100`

#### Job Type (Optional)
- **Type:** `JobType` enum
- **Default:** `None` (all types)
- **Options:**
  - `JobType.FULL_TIME`
  - `JobType.PART_TIME`
  - `JobType.CONTRACT`
  - `JobType.TEMPORARY`
  - `JobType.INTERNSHIP`

#### Remote Type (Optional)
- **Type:** `RemoteType` enum
- **Default:** `None` (all types)
- **Options:**
  - `RemoteType.REMOTE` - Fully remote
  - `RemoteType.HYBRID` - Mix of remote/on-site
  - `RemoteType.ON_SITE` - In-office only

**Warning:** Using `RemoteType.REMOTE` with LinkedIn may cause "Invalid country string" errors. Consider using specific locations instead.

#### Posted Since Days (Optional)
- **Type:** `int`
- **Default:** `None` (all dates)
- **Description:** Only jobs posted in last N days
- **Examples:** `1`, `7`, `14`, `30`

#### Max Results (Optional)
- **Type:** `int`
- **Default:** `25`
- **Description:** Maximum results per site
- **Range:** Typically 10-50

**Note:** Actual results may be less than max_results due to deduplication and site limitations.

---

## Configuration

### JobSpyScraper Config

Configure rate limiting and workers:

```python
from src.intelligence.jobspy_scraper import JobSpyScraper

scraper = JobSpyScraper(config={
    'max_workers': 3,              # Concurrent workers
    'request_delay': 2.0,          # Delay between requests (seconds)
    'requests_per_minute': 30      # Max requests per minute
})
```

### Config Parameters

#### max_workers
- **Type:** `int`
- **Default:** `3`
- **Description:** Number of concurrent scraping workers
- **Recommendation:** Keep at 2-4 to avoid rate limiting

#### request_delay
- **Type:** `float`
- **Default:** `2.0`
- **Description:** Delay between requests in seconds
- **Recommendation:** Use 1.5-3.0 for safer scraping

#### requests_per_minute
- **Type:** `int`
- **Default:** `30`
- **Description:** Maximum requests per minute across all workers
- **Recommendation:** Keep at 20-40 to avoid blocks

---

## Rate Limiting

### Built-in Rate Limiting

JobSpyScraper implements multiple rate limiting strategies:

#### 1. Request Delay
```python
await asyncio.sleep(self.request_delay)  # 2.0 seconds default
```

#### 2. Requests Per Minute
```python
time_since_last = time.time() - self.last_request_time
if time_since_last < (60.0 / self.requests_per_minute):
    await asyncio.sleep((60.0 / self.requests_per_minute) - time_since_last)
```

#### 3. Site-Specific Limits

| Site | Internal Limit | Our Limit |
|------|---------------|-----------|
| Indeed | ~60 req/min | 30 req/min |
| LinkedIn | Unknown | 30 req/min |
| Glassdoor | ~40 req/min | 30 req/min |
| Google Jobs | Unknown | 30 req/min |

### Recommendations

**Conservative (Recommended):**
```python
config = {
    'max_workers': 2,
    'request_delay': 3.0,
    'requests_per_minute': 20
}
```

**Balanced:**
```python
config = {
    'max_workers': 3,
    'request_delay': 2.0,
    'requests_per_minute': 30
}
```

**Aggressive (Not Recommended):**
```python
config = {
    'max_workers': 5,
    'request_delay': 1.0,
    'requests_per_minute': 50
}
```

---

## Error Handling

### Retry Logic

Uses circuit breaker pattern with exponential backoff:

```python
from src.intelligence.async_helpers import retry_with_circuit_breaker

@retry_with_circuit_breaker(max_attempts=3, delay=2.0, backoff=2.0)
async def scrape_jobs(self, request: ScrapingRequest) -> List[JobListing]:
    # Scraping logic
    pass
```

**Retry behavior:**
- **Attempt 1:** Immediate
- **Attempt 2:** After 2 seconds
- **Attempt 3:** After 4 seconds (2.0 * 2.0)

### Exception Types

#### ScrapingError
```python
from src.intelligence.scraping_errors import ScrapingError

try:
    jobs = await scraper.scrape_jobs(request)
except ScrapingError as e:
    print(f"Scraping failed: {e}")
    print(f"URL: {e.url}")
```

**Raised when:**
- Site returns error status
- Invalid response format
- Network timeout

#### ExternalServiceError
```python
from src.intelligence.scraping_errors import ExternalServiceError

try:
    jobs = await scraper.scrape_jobs(request)
except ExternalServiceError as e:
    print(f"External service error: {e}")
```

**Raised when:**
- JobSpy library failure
- Site unavailable
- Anti-scraping detection

### Error Recovery

**Partial failures:**
```python
# If one site fails, continue with others
results = []
for site in [JobSite.INDEED, JobSite.LINKEDIN]:
    try:
        jobs = await scraper.scrape_jobs(ScrapingRequest(
            keywords="Python Dev",
            location="DC",
            job_sites=[site]
        ))
        results.extend(jobs)
    except ScrapingError:
        logging.warning(f"Failed to scrape {site.value}, continuing...")
        continue
```

---

## Data Models

### JobListing

Complete job data model:

```python
@dataclass
class JobListing:
    # Basic info
    title: str
    company: str
    location: str
    job_url: str
    
    # Detailed info
    description: Optional[str] = None
    job_type: Optional[JobType] = None
    remote_type: Optional[RemoteType] = None
    
    # Salary
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "USD"
    
    # Dates
    posted_date: Optional[datetime] = None
    scraped_date: datetime = field(default_factory=datetime.now)
    
    # Source
    source_site: Optional[JobSite] = None
    
    # Company data
    company_rating: Optional[float] = None
    company_reviews_count: Optional[int] = None
    company_industry: Optional[str] = None
    
    # Special requirements
    clearance_required: bool = False
    metro_accessible: bool = False
```

### Job Site Enum

```python
class JobSite(Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    GOOGLE_JOBS = "google_jobs"
    ZIP_RECRUITER = "zip_recruiter"
    CUSTOM = "custom"
```

### Job Type Enum

```python
class JobType(Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
```

### Remote Type Enum

```python
class RemoteType(Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on-site"
```

---

## Examples

### Example 1: Basic Search

```python
from src.intelligence.jobspy_scraper import JobSpyScraper
from src.intelligence.models import ScrapingRequest, JobSite

# Create scraper
scraper = JobSpyScraper()

# Create search request
request = ScrapingRequest(
    keywords="Python Developer",
    location="Washington, DC",
    job_sites=[JobSite.INDEED, JobSite.LINKEDIN],
    max_results=25
)

# Scrape jobs
jobs = await scraper.scrape_jobs(request)
print(f"Found {len(jobs)} jobs")
```

### Example 2: Filtered Search

```python
# Search for remote senior roles with salary info
request = ScrapingRequest(
    keywords="Senior Python Engineer",
    location="Arlington, VA",
    job_sites=[JobSite.INDEED, JobSite.LINKEDIN],
    remote_type=RemoteType.REMOTE,
    posted_since_days=7,
    max_results=50
)

jobs = await scraper.scrape_jobs(request)

# Filter by salary
high_paying = [j for j in jobs if j.salary_min and j.salary_min >= 150000]
print(f"Found {len(high_paying)} jobs over $150K")
```

### Example 3: Multiple Searches

```python
# Search multiple locations
locations = ["Washington, DC", "Arlington, VA", "Herndon, VA"]
all_jobs = []

for location in locations:
    request = ScrapingRequest(
        keywords="Machine Learning Engineer",
        location=location,
        job_sites=[JobSite.INDEED],
        max_results=20
    )
    jobs = await scraper.scrape_jobs(request)
    all_jobs.extend(jobs)

print(f"Total jobs across {len(locations)} locations: {len(all_jobs)}")
```

### Example 4: Complete Script

```python
import asyncio
from src.intelligence.jobspy_scraper import JobSpyScraper
from src.intelligence.models import ScrapingRequest, JobSite
from src.intelligence.job_database import JobDatabase

async def main():
    # Setup
    scraper = JobSpyScraper(config={
        'max_workers': 3,
        'request_delay': 2.0,
        'requests_per_minute': 30
    })
    db = JobDatabase()
    
    # Define searches
    searches = [
        ScrapingRequest(
            keywords="Python Developer",
            location="Washington, DC",
            job_sites=[JobSite.INDEED, JobSite.LINKEDIN],
            posted_since_days=7,
            max_results=25
        ),
        ScrapingRequest(
            keywords="Data Scientist",
            location="Arlington, VA",
            job_sites=[JobSite.INDEED],
            posted_since_days=7,
            max_results=25
        )
    ]
    
    # Scrape and save
    for request in searches:
        try:
            jobs = await scraper.scrape_jobs(request)
            for job in jobs:
                db.save_job(job)
            print(f"Saved {len(jobs)} jobs from search: {request.keywords}")
        except Exception as e:
            print(f"Search failed: {e}")
    
    # Stats
    stats = db.get_statistics()
    print(f"Total jobs in database: {stats['total_jobs']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Troubleshooting

### Common Issues

#### "Invalid country string: 'bulgaria'" (LinkedIn)

**Cause:** LinkedIn remote job listings with international locations

**Solution:**
- Use specific locations instead of generic "Remote"
- Add exception handling for LinkedIn searches
- Use Indeed for remote job searches

```python
try:
    jobs = await scraper.scrape_jobs(request)
except ExternalServiceError as e:
    if "Invalid country string" in str(e):
        logging.warning("LinkedIn location error, skipping...")
```

#### "Location not parsed" (Glassdoor)

**Cause:** Glassdoor requires specific location format

**Solution:**
- Use "City, ST" format (e.g., "Washington, DC")
- Avoid long location strings
- Try disabling Glassdoor if persistent

```python
request = ScrapingRequest(
    keywords="Python Dev",
    location="Washington, DC",  # Good
    # location="Washington DC Metro Area",  # Bad - too long
    job_sites=[JobSite.INDEED, JobSite.LINKEDIN]  # Skip Glassdoor
)
```

#### Google Jobs: "initial cursor not found"

**Cause:** Google Jobs API limitation

**Impact:** Limited to ~10 results per query, but not an error

**Solution:**
- Expect fewer results from Google Jobs
- Use multiple specific searches instead of broad ones
- Primarily rely on Indeed/LinkedIn

#### Too Many Requests / Rate Limiting

**Symptoms:**
- Empty results
- HTTP 429 errors
- "Too many requests" messages

**Solution:**
```python
# More conservative config
scraper = JobSpyScraper(config={
    'max_workers': 2,          # Reduce workers
    'request_delay': 3.0,      # Increase delay
    'requests_per_minute': 20  # Lower rate
})
```

#### No Results

**Possible causes:**
- Keywords too specific
- Location too narrow
- posted_since_days too restrictive
- All sites blocked

**Debug:**
```python
# Test each site individually
for site in [JobSite.INDEED, JobSite.LINKEDIN]:
    request = ScrapingRequest(
        keywords="Python",  # Broaden keywords
        location="Washington, DC",
        job_sites=[site],
        max_results=10
    )
    jobs = await scraper.scrape_jobs(request)
    print(f"{site.value}: {len(jobs)} jobs")
```

---

## Best Practices

### 1. Start Conservative

Use reliable sites with safe settings:

```python
request = ScrapingRequest(
    keywords="Your Search",
    location="Your Location",
    job_sites=[JobSite.INDEED, JobSite.LINKEDIN],  # Most reliable
    posted_since_days=7,                           # Recent only
    max_results=25                                  # Moderate limit
)
```

### 2. Handle Errors Gracefully

```python
for site in job_sites:
    try:
        jobs = await scraper.scrape_jobs(request)
        # Process jobs
    except ScrapingError as e:
        logging.error(f"{site} failed: {e}")
        continue  # Continue with other sites
```

### 3. Save to Database

```python
from src.intelligence.job_database import JobDatabase

db = JobDatabase()
for job in jobs:
    db.save_job(job)  # Auto-deduplication by URL
```

### 4. Monitor and Log

```python
import logging

logging.info(f"Starting scrape: {request.keywords}")
jobs = await scraper.scrape_jobs(request)
logging.info(f"Found {len(jobs)} jobs")
```

### 5. Use Salary Filtering

```python
MIN_SALARY = 100000
high_paying = [j for j in jobs if j.salary_min and j.salary_min >= MIN_SALARY]
```

---

## Additional Resources

- **JobSpy GitHub:** https://github.com/Bunsly/JobSpy
- **JobSpy Documentation:** https://github.com/Bunsly/JobSpy#readme
- **Our Database Guide:** [DATABASE_GUIDE.md](DATABASE_GUIDE.md)
- **Dashboard Guide:** [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)

---

**Need help?** Open an issue on GitHub or contact the maintainers.
