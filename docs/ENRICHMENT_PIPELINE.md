# Enrichment Pipeline — Glassdoor, Career Page Verification, Ghost Detection

> **Complete reference for the job enrichment and verification systems**
> Updated: 2026-03-18

---

## Table of Contents

- [Overview](#overview)
- [1. Glassdoor Culture Scores](#1-glassdoor-culture-scores)
- [2. Career Page Verification](#2-career-page-verification)
- [3. Ghost Job Detection](#3-ghost-job-detection)
- [4. Alignment Scoring (Synonym-Aware)](#4-alignment-scoring-synonym-aware)
- [5. Database Schema](#5-database-schema)
- [6. API Endpoints](#6-api-endpoints)
- [7. Environment Variables](#7-environment-variables)
- [8. Troubleshooting](#8-troubleshooting)

---

## Overview

The enrichment pipeline adds intelligence layers on top of scraped job data:

```
Scraped Jobs (Indeed/LinkedIn/Greenhouse)
    │
    ├── Glassdoor Culture Scores    → company_rating, company_glassdoor_json
    ├── Career Page Verification     → career_page_verified, career_page_json
    ├── Ghost Job Detection          → ghost confidence + reasons
    └── Alignment Scoring            → alignment_score, alignment_details
```

All enrichment runs from the Dashboard UI via background tasks. Results persist to SQLite.

---

## 1. Glassdoor Culture Scores

### How It Works

**File**: `src/enrichment/glassdoor_client.py`

Two-step lookup via `glassdoor-real-time.p.rapidapi.com` (RapidAPI):

1. **Company Search**: `/jobs/search?query=<company>` → extracts `companyId` from `companyFilterOptions`
2. **Ratings Fetch**: `/companies/reviews?companyId=<id>` → extracts all rating dimensions

### Company Name Normalization

Complex company names like `"Perfect Path, LLC, d/b/a Trajector Services"` are progressively simplified:

```python
_normalize_company_name("Perfect Path, LLC, d/b/a Trajector Services")
# → ["Trajector Services", "Perfect Path", "Perfect Path LLC Trajector Services"]
```

**Normalization rules** (priority order):
1. **DBA extraction** — `d/b/a`, `doing business as`, `trading as` → extract public brand name
2. **Legal suffix stripping** — `Inc`, `LLC`, `Corp`, `Ltd`, `PLC`, etc. (always removed)
3. **Soft suffix stripping** — `Group`, `Holdings`, `Technologies`, `Services` (only when trailing)
4. **Parenthetical removal** — `(formerly Foo)`, `(US)`, `(Remote)`
5. **Raw name** as last resort

Each candidate is tried against the API in order, with substring matching against all candidate forms.

### Fields Returned

| Field | Type | Description |
|-------|------|-------------|
| `glassdoor_rating` | float | Overall rating (1.0-5.0) |
| `culture_rating` | float | Culture & Values |
| `work_life_balance` | float | Work-Life Balance |
| `compensation_rating` | float | Compensation & Benefits |
| `diversity_rating` | float | Diversity & Inclusion |
| `career_rating` | float | Career Opportunities |
| `senior_mgmt_rating` | float | Senior Management |
| `ceo_approval` | float | Recommend to Friend (0-1 scale) |
| `review_count` | int | Total reviews |

### Key Implementation Details

- **Async/Sync bridge**: `lookup_company_sync()` creates a fresh `asyncio.new_event_loop()` per call to avoid conflicts with uvicorn's event loop. Do NOT use `nest_asyncio` (not installed).
- **In-memory cache**: 6-hour TTL per company, keyed by MD5 of normalized name.
- **Rate limiting**: 1.2s sleep between API calls in bulk mode (~50 req/min).
- **DB storage**: Overall rating in `company_rating` (REAL), full breakdown in `company_glassdoor_json` (TEXT/JSON).

### Configuration

```
RAPIDAPI_KEY=your_key_here           # Required
GLASSDOOR_API_ENABLED=true           # Default: false
```

Set these in Dashboard → Settings → Filters → Culture Score section.

---

## 2. Career Page Verification

### How It Works

**File**: `src/enrichment/career_page_checker.py`

Three-phase verification, stopping at first conclusive result:

#### Phase 1: ATS Direct Lookup (Free, Structured)

For companies using Greenhouse or Lever, queries their **free public APIs**:

- **Greenhouse**: `GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs`
- **Lever**: `GET https://api.lever.co/v0/postings/{slug}`

Returns structured JSON of all open positions. Title matching via `rapidfuzz.fuzz.token_set_ratio` (threshold: 75).

The board slug is extracted from the job URL (e.g., `boards.greenhouse.io/coinbase` → slug `coinbase`) or guessed from the company name.

#### Phase 2: Career Page Discovery + Probe (Free)

1. **Resolve company domain**: Extract from job URL, or guess from company name (`"Amazon Web Services"` → `amazon.com`, `"SAIC"` → `saic.com`)
2. **Discover career page**: Probe common paths in order:
   - Subdomains: `careers.{domain}`, `jobs.{domain}`
   - Paths: `/careers`, `/jobs`, `/careers/openings`, `/about/careers`, `/join-us`, `/work-with-us`, `/open-positions`, `/opportunities`
3. **Title search**: Check if job title appears on the career page (exact match first, then keyword ratio >= 70%)

Uses HEAD request first, falls back to GET if server returns 403/405.

#### Phase 3: Search API Fallback (Optional, Low Cost)

If Serper.dev API key is configured, searches `"{job title}" site:{company.com}` via Google.

- **Free**: 2,500 queries (no credit card required)
- **Paid**: $1/1,000 additional queries

### Career Page Result Fields

| Field | Type | Description |
|-------|------|-------------|
| `found_on_career_page` | bool/None | True=found, False=not found, None=couldn't check |
| `verification_method` | str | `greenhouse_api`, `lever_api`, `career_page_probe`, `serper_search` |
| `career_page_url` | str | URL of the career page checked |
| `matched_title` | str | Title found on career page (if matched) |
| `match_confidence` | float | 0-1 fuzzy match score |
| `ats_platform` | str | Greenhouse, Lever, etc. |
| `total_open_jobs` | int | Total open positions at company |

### Integration with Ghost Detection

Career page results feed directly into `GhostSignals.on_company_careers_page`:
- **Not found on career page**: +0.20 ghost score (strong signal)
- **Found on career page**: -1 signal point in ghost_detector.py (reduces ghost confidence)

### Configuration

```
CAREER_CHECK_ENABLED=true            # Default: true
SERPER_API_KEY=your_key_here         # Optional (Phase 3 only)
```

---

## 3. Ghost Job Detection

### Two Detection Systems

The pipeline has two complementary ghost detection systems:

#### A. `src/enrichment/ghost_signals.py` (Enrichment Layer)

Used by the screening gates pipeline. Composite weighted score (0.0-1.0):

| Signal | Weight | Source |
|--------|--------|--------|
| Posting age > 45 days | +0.25 | Scraped date |
| No salary listed | +0.05 | Job metadata |
| Applicants > 500 | +0.20 | LinkedIn data |
| Applicants > 200 | +0.15 | LinkedIn data |
| Reposted | +0.20 | Description hash matching |
| Repost count >= 3 | +0.15 | Hash comparison |
| Vague description (specificity < 0.3) | +0.10 | NLP analysis |
| **Not on career page** | **+0.20** | Career page checker |
| Easy Apply | +0.03 | LinkedIn metadata |
| Ghost language detected | +0.15 | Pattern matching |
| Wayback vs posted date > 30d | +0.20 | Wayback Machine CDX API |

**Thresholds**: `ghost_score >= 0.60` = hard fail, `>= 0.40` = flag for review

#### B. `src/dashboard/ghost_detector.py` (Dashboard Layer)

Simpler system used in the job detail page UI. Signal-counting approach (0-100% confidence):

- Posting age (3 tiers: >90d, >60d, >45d)
- Applicant count (3 tiers: >1000, >500, >300)
- Ghost language patterns (regex-based)
- Repost detection (listed_at vs original_listed_at)
- Vague descriptions
- **Career page verification** (now integrated — +3 signals if not found, -1 if confirmed)

**Threshold**: 25%+ confidence = ghost warning shown in UI

### Ghost Language Patterns

```
"talent community", "talent pipeline", "future opportunities",
"no immediate openings", "building our team for", "pool of candidates",
"general application", "evergreen requisition", "proactive sourcing",
"continuous hiring", "rolling basis", "speculative application"
```

### Description Specificity Scoring

Measures concreteness of job description (0=vague, 1=specific):
- **Vague phrases**: "dynamic environment", "motivated self-starter", "competitive compensation"
- **Specificity markers**: `python 3`, `kubernetes`, `team of \d+`, `reporting to`, `\d+ engineers`

---

## 4. Alignment Scoring (Synonym-Aware)

### How It Works

**File**: `src/dashboard/scoring.py`

Local keyword-based scoring engine — no AI API calls. Scores jobs against the user's resume across 5 categories:

| Category | Weight (Engineering) | Weight (Analyst) |
|----------|---------------------|-------------------|
| Technical Skills | 0.45 | 0.35 |
| Experience | 0.25 | 0.25 |
| Domain Knowledge | 0.15 | 0.20 |
| Soft Skills | 0.10 | 0.10 |
| Education | 0.05 | 0.10 |

### Synonym-Aware Soft Skills (New)

Instead of exact keyword matching, soft skills use a **synonym dictionary**. If *any* synonym appears in the resume, the canonical skill is matched:

```python
"collaboration": ["collaboration", "collaborative", "collaborating",
                   "cross-functional teams", "team-oriented", "teamwork",
                   "team player", "partnered with", "worked closely",
                   "worked with stakeholders", "interdisciplinary"]
```

**16 canonical skills** with synonyms: leadership, communication, collaboration, teamwork, mentoring, problem solving, analytical, stakeholder management, cross-functional, agile, scrum, project management, knowledge transfer, documentation, technical training, requirements gathering.

### Scoring Flow

1. Classify role type (engineering vs analyst) from title
2. Extract tech keywords from job description + resume
3. Score each category (matched items / required items × 100)
4. Apply weights → weighted overall score
5. Identify critical gaps (required skills not in resume)
6. Generate recommendation: PROCEED (≥70%, ≤2 gaps), FLAG (≥50% or ≤3 gaps), NO_PROCEED

---

## 5. Database Schema

### Jobs Table — Enrichment Columns

```sql
-- Glassdoor enrichment
company_rating              REAL    -- Overall Glassdoor rating (1.0-5.0)
company_glassdoor_json      TEXT    -- Full JSON breakdown of all ratings
company_rating_fetched_at   TEXT    -- ISO timestamp of last fetch
company_rating_source       TEXT    -- 'glassdoor_api'

-- Career page verification
career_page_verified        INTEGER -- 1=found, 0=not found, NULL=unchecked
career_page_json            TEXT    -- Full CareerPageResult as JSON
career_page_checked_at      TEXT    -- ISO timestamp of last check

-- Alignment scoring
alignment_score             REAL    -- Overall score (0-100)
alignment_details           TEXT    -- Full AlignmentResult as JSON
semantic_alignment_score    REAL    -- Sentence-transformer cosine score
```

---

## 6. API Endpoints

### Single Job Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/job/{id}/score` | GET | Score/re-score a single job |
| `/api/job/{id}/verify-career-page` | GET | Verify job against career page |

### Bulk Operations (Background Tasks)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/score-jobs` | POST | Score all unscored jobs |
| `/api/rescore-all` | POST | Re-score ALL jobs with latest engine |
| `/api/enrich-ratings` | POST | Fetch Glassdoor ratings (priority-ordered) |
| `/api/verify-career-pages` | POST | Bulk verify career pages (up to 100 jobs) |

### Dashboard Buttons

| Button | Color | Endpoint | Notes |
|--------|-------|----------|-------|
| Score All Jobs | Amber | `/api/score-jobs` | Runs in background |
| Culture Score Ratings | Purple | `/api/enrich-ratings` | Requires RAPIDAPI_KEY |
| Verify Career Pages | Indigo | `/api/verify-career-pages` | Free, no API key needed |
| Classify Jobs | Cyan | `/api/classify-jobs` | Requires Ollama |

---

## 7. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RAPIDAPI_KEY` | For Glassdoor | - | RapidAPI key for glassdoor-real-time |
| `GLASSDOOR_API_ENABLED` | No | `false` | Enable Glassdoor enrichment |
| `CAREER_CHECK_ENABLED` | No | `true` | Enable career page verification |
| `SERPER_API_KEY` | No | - | Serper.dev key for search fallback |
| `GHOST_HTTP_CHECKS_ENABLED` | No | `false` | Enable Wayback Machine + JSON-LD checks |

---

## 8. Troubleshooting

### Glassdoor ratings not populating

1. **Check API key**: Settings → Filters → verify RAPIDAPI_KEY is set
2. **Check enabled**: `GLASSDOOR_API_ENABLED=true`
3. **Company name issues**: Complex names (DBA, LLC) should be handled by normalization. Check logs for "No Glassdoor company ID found"
4. **Rate limiting**: Free tier has daily limits. Wait and retry tomorrow
5. **Event loop errors**: If you see "Cannot run event loop" errors, ensure `lookup_company_sync()` uses `asyncio.new_event_loop()` (NOT `nest_asyncio`)

### Career page verification not working

1. **Company blocks requests**: Some companies (SAIC, etc.) return 403 for all automated requests. This is expected — the job will show as "Could not verify"
2. **Wrong domain guessed**: Multi-word company names may not resolve correctly. The system strips modifiers like "Web Services", "Technologies" before guessing
3. **ATS not detected**: Only Greenhouse and Lever APIs are supported in Phase 1. Other ATS platforms fall through to Phase 2 (URL probe)

### Ghost detection false positives

1. **Career page not found ≠ ghost**: Many legitimate companies block automated requests. The career page signal is one of many — it won't flag a job as ghost by itself
2. **Stale jobs**: Jobs older than 45 days get ghost signals regardless of legitimacy
3. **High applicant count**: A job with 500+ applicants isn't necessarily a ghost — just highly competitive

### Soft skills showing as gaps

After the synonym-aware update, re-score the job to pick up the new matching logic. Click "Score This Job" on the job detail page or run "Score All Jobs" from the dashboard.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Dashboard UI                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │Score Jobs│ │Culture   │ │Verify    │ │Classify│ │
│  │  (Amber) │ │Scores    │ │Career Pgs│ │Jobs    │ │
│  │          │ │ (Purple) │ │ (Indigo) │ │ (Cyan) │ │
│  └─────┬────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │
└────────┼───────────┼────────────┼────────────┼──────┘
         │           │            │            │
         ▼           ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐
   │scoring.py│ │glassdoor │ │career_page│ │semantic│
   │          │ │_client.py│ │_checker.py│ │_classi-│
   │Keyword + │ │RapidAPI  │ │Greenhouse │ │fier.py │
   │Synonym   │ │2-step    │ │Lever API  │ │Ollama  │
   │Matching  │ │lookup    │ │URL Probe  │ │        │
   └─────┬────┘ └────┬─────┘ └────┬──────┘ └───┬────┘
         │           │            │             │
         ▼           ▼            ▼             ▼
   ┌──────────────────────────────────────────────────┐
   │              SQLite (job_tracker.db)              │
   │  alignment_score │ company_rating │ career_page_  │
   │  alignment_details│ company_glassdoor │ verified   │
   │                   │ _json            │ career_page │
   │                   │                  │ _json       │
   └──────────────────────────────────────────────────┘
         │
         ▼
   ┌──────────────────────────────────────────────────┐
   │           Ghost Detection (2 systems)            │
   │  ghost_signals.py    │  ghost_detector.py        │
   │  (Enrichment gates)  │  (Dashboard UI display)   │
   │  Composite 0.0-1.0   │  Signal count 0-100%      │
   │  Uses career_page    │  Uses career_page_verified │
   │  _verified field      │  + career_page_json       │
   └──────────────────────────────────────────────────┘
```
