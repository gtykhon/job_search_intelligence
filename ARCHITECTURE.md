# job_search_intelligence — System Architecture

> AI-powered job intelligence platform combining multi-source scraping, 12-gate screening, semantic scoring, and interactive dashboards.

**Last updated:** 2026-03-21

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Core Subsystems](#4-core-subsystems)
   - [4.1 Web Dashboard (FastAPI)](#41-web-dashboard-fastapi)
   - [4.2 Job Scraping & Discovery](#42-job-scraping--discovery)
   - [4.4 Screening Pipeline (12-Gate)](#44-screening-pipeline-12-gate)
   - [4.5 Enrichment & Verification](#45-enrichment--verification)
   - [4.6 Scoring & Classification](#46-scoring--classification)
   - [4.7 AI & LLM Layer](#47-ai--llm-layer)
   - [4.8 Resume Generation Pipeline (3-Layer)](#48-resume-generation-pipeline-3-layer)
   - [4.9 Application Package Generation (Legacy)](#49-application-package-generation-legacy)
   - [4.10 Tracking & Analytics](#410-tracking--analytics)
   - [4.11 Messaging & Notifications](#411-messaging--notifications)
   - [4.12 Company Intelligence](#412-company-intelligence)
5. [Database Architecture](#5-database-architecture)
6. [External Services & APIs](#6-external-services--apis)
7. [Scheduled Tasks & Automation](#7-scheduled-tasks--automation)
8. [Data Flow Pipelines](#8-data-flow-pipelines)
9. [Configuration](#9-configuration)
10. [Entry Points](#10-entry-points)
11. [Key Architectural Patterns](#11-key-architectural-patterns)
12. [Dependencies](#12-dependencies)
13. [Testing](#13-testing)

---

## 1. System Overview

**job_search_intelligence** is a production-ready job search automation platform built for data/ML engineers. It discovers jobs from multiple sources, filters them through a rigorous multi-stage gate pipeline, scores them against a resume, enriches them with company intelligence, generates tailored application packages, and presents everything through interactive web dashboards.

### Key Capabilities

| Capability | Implementation |
|---|---|
| Multi-source job scraping | JobSpy (Indeed, LinkedIn, Glassdoor, Google) + niche scrapers |
| 12-gate screening pipeline | Sequential gates with short-circuit, LLM override resolution |
| Dual-method alignment scoring | Keyword matching (weighted) + semantic embeddings (cosine similarity) |
| Company intelligence | Glassdoor ratings, career page verification, defense contractor exclusion |
| Fabrication-safe resume generation | 3-layer pipeline: deterministic context → constrained LLM → deterministic validation |
| AI-powered generation | Ollama (local) + Claude (cloud) for resumes, cover letters, interview prep |
| Application packages | DOCX/PDF export with quality gate validation |
| Two-tier classification | Regex keyword (always-on) + optional LLM upgrade for job categorization |
| Ghost job detection | Multi-signal analysis (phrase patterns, posting age, re-posts) |
| Web dashboards | FastAPI dashboard with job listings, scoring, ghost detection, resume generation |
| Automation | Windows Task Scheduler for daily scraping, weekly analysis, notifications |
| Notifications | Telegram bot integration for daily summaries and alerts |

### Technology Stack

- **Backend:** Python 3.13, FastAPI, SQLite, SQLAlchemy
- **Frontend:** Jinja2 templates, HTMX, Tailwind CSS
- **AI/ML:** Ollama (local LLM), Anthropic Claude API, sentence-transformers, scikit-learn
- **Scraping:** python-jobspy, BeautifulSoup, requests/aiohttp
- **Messaging:** Telethon (Telegram)
- **Export:** python-docx, LibreOffice (PDF conversion)

---

## 2. High-Level Architecture

```
                                 ┌─────────────────────────────────────────────┐
                                 │            USER INTERFACES                   │
                                 │                                              │
                                 │  FastAPI Dashboard (:8889)                   │
                                 │  ├─ Job listings, scoring, applications      │
                                 │  ├─ Ghost detection, career page verify      │
                                 │  └─ Settings, tools, job board strategy      │
                                 └──────────────────┬──────────────────────────┘
                                                    │
                     ┌──────────────────────────────┼──────────────────────────────┐
                     │                              │                              │
              ┌──────▼──────┐              ┌───────▼────────┐             ┌───────▼────────┐
              │  DISCOVERY  │              │   PROCESSING   │             │   GENERATION   │
              │             │              │                │             │                │
              │ JobSpy      │──────────▶   │ 12-Gate Screen │──────────▶  │ AI Generator   │
              │ HN Scraper  │              │ Alignment Score│             │ Resume Tailor  │
              │ Greenhouse  │              │ Semantic Class. │             │ Cover Letter   │
              │ Ashby       │              │ Ghost Detect   │             │ Quality Gates  │
              │ Wellfound   │              │ Enrichment     │             │ DOCX/PDF Export│
              │ Climatebase │              │                │             │                │
              └──────┬──────┘              └───────┬────────┘             └───────┬────────┘
                     │                              │                              │
                     └──────────────────────────────┼──────────────────────────────┘
                                                    │
                     ┌──────────────────────────────┼──────────────────────────────┐
                     │                              │                              │
              ┌──────▼──────┐              ┌───────▼────────┐             ┌───────▼────────┐
              │  DATA LAYER │              │ EXTERNAL APIS  │             │  AUTOMATION    │
              │             │              │                │             │                │
              │ job_tracker │              │ Glassdoor/Rapid│             │ Task Scheduler │
              │   .db       │              │ Serper.dev     │             │ Daily scrape   │
              │ company_    │              │ Anthropic      │             │ Weekly analysis│
              │  research.db│              │ Ollama (local) │             │ Telegram alerts│
              │ linkedin_   │              │ Telegram API   │             │                │
              │  intel.db   │              │                │             │                │
              └─────────────┘              └────────────────┘             └────────────────┘
```

---

## 3. Directory Structure

```
job_search_intelligence/
├── requirements.txt                 # Python dependencies (~170 packages)
├── .env                             # Environment config (secrets, API keys)
├── ARCHITECTURE.md                  # This document
├── README.md                        # Project overview
├── STRUCTURE.md                     # File organization guide
│
├── src/                             # Core application code
│   ├── dashboard/                   # FastAPI web dashboard
│   │   ├── app.py                   # FastAPI server (routes, handlers)
│   │   ├── db.py                    # DashboardDB — SQLite bridge, migrations
│   │   ├── scoring.py               # AlignmentScorer — keyword + LLM scoring
│   │   ├── scraper_runner.py        # Dashboard scrape pipeline (classify + score)
│   │   ├── pipeline_metrics.py      # Pipeline run metrics (CPU/RAM monitoring)
│   │   ├── semantic_classifier.py   # Job classification (keyword + optional LLM)
│   │   ├── ai_generator.py          # Multi-provider AI (Ollama + Claude)
│   │   ├── generator.py             # Template-based package generation
│   │   ├── docx_generator.py        # DOCX/PDF export
│   │   ├── quality_gates.py         # 12-point pre-application validation
│   │   ├── ghost_detector.py        # Ghost job detection
│   │   ├── platform_rules.py        # Platform-specific formatting
│   │   ├── auth_audit.py            # Auth info leak detection
│   │   ├── consistency_checker.py   # Cross-platform consistency
│   │   ├── duty_coverage.py         # Resume duty → job requirement mapping
│   │   ├── real_time_dashboard.py   # real-time monitor (excluded module)
│   │   ├── database_field_explorer.py # DB explorer (excluded module)
│   │   └── templates/               # Jinja2 HTML templates
│   │       ├── base.html            # Layout with nav, Tailwind, HTMX
│   │       ├── index.html           # Job listings table
│   │       ├── job_detail.html      # Single job view
│   │       ├── tools.html           # Dashboards, APIs, job board strategy
│   │       ├── settings.html        # Resume, AI provider, scoring config
│   │       └── ...
│   │
│   ├── intelligence/                # Job discovery & LinkedIn intelligence
│   │   ├── jobspy_scraper.py        # Primary multi-site scraper
│   │   ├── models.py                # JobListing, ScrapingRequest, enums
│   │   ├── job_database.py          # SQLite persistence layer
│   │   ├── semantic_scorer.py       # Sentence-transformer scoring
│   │   ├── role_classifier.py       # ML-based role classification
│   │   ├── keyword_profile.py       # GREEN/YELLOW/RED keyword management
│   │   ├── salary_extractor.py      # Salary range extraction from text
│   │   ├── smart_opportunity_detector.py  # Multi-type opportunity detection
│   │   ├── real_linkedin_api_client.py    # LinkedIn Voyager API
│   │   ├── real_linkedin_data_collector.py # Profile/connection collection
│   │   ├── enhanced_linkedin_analyzer.py  # Profile analysis
│   │   ├── integrated_job_search_intelligence.py # Unified orchestrator
│   │   ├── greenhouse_scraper.py    # ATS: Greenhouse
│   │   ├── ashby_scraper.py         # ATS: Ashby
│   │   ├── wellfound_scraper.py     # Startup board
│   │   ├── hn_scraper.py            # Hacker News jobs
│   │   ├── climatebase_scraper.py   # Climate tech jobs
│   │   ├── climatetechlist_scraper.py # Climate-focused listings
│   │   ├── async_helpers.py         # Retry, circuit breaker
│   │   ├── scraping_errors.py       # Custom error types
│   │   └── company_research/        # Company intelligence
│   │       ├── verifier.py          # Company verification + cache
│   │       └── audience_classifier.py # Audience segmentation
│   │
│   ├── generation/                  # 3-layer fabrication-safe resume generation
│   │   ├── context_builder.py      # Layer 1: deterministic context assembly
│   │   ├── output_validator.py     # Layer 3: post-generation validation
│   │   └── tier3_blocklist.py      # Tier 1/2/3 tool classification & blocklist
│   │
│   ├── screening/                   # 12-gate screening pipeline
│   │   ├── pipeline.py              # Sequential execution engine
│   │   ├── base_gate.py             # Abstract gate interface
│   │   ├── models.py                # GateResult, GateVerdict, ScreeningResult
│   │   ├── gate_registry.py         # @register_gate decorator
│   │   ├── override_resolver.py     # LLM-based override decisions
│   │   ├── data/                    # Gate keyword lists & data
│   │   │   ├── known_lists.py       # Hardcoded default lists (defense primes, clearance, gov signals, staffing, etc.)
│   │   │   └── list_provider.py     # Dynamic list loader (DB override → hardcoded fallback)
│   │   └── gates/                   # Individual gate implementations
│   │       ├── gate_0a_company_research.py  # Company research cache
│   │       ├── gate_0b_defense_exclusion.py # Defense/government exclusion (dynamic lists)
│   │       ├── gate_0c_staffing_agency.py   # Staffing agency detection (dynamic lists)
│   │       ├── gate_0d_ghost_job.py         # Ghost job detection
│   │       ├── gate_0e_tech_stack.py        # Tech stack matching
│   │       ├── gate_0f_compensation.py      # Salary floor validation
│   │       ├── gate_0g_red_keywords.py      # RED keyword rejection
│   │       ├── gate_0h_yellow_review.py     # YELLOW keyword + LLM override
│   │       ├── gate_0i_alignment_score.py   # Resume alignment threshold
│   │       ├── gate_0j_role_type.py         # Role type matching
│   │       └── gate_culture.py              # Company culture gate
│   │
│   ├── enrichment/                  # Post-discovery enrichment
│   │   ├── glassdoor_client.py      # Glassdoor ratings via RapidAPI
│   │   ├── career_page_checker.py   # 3-phase career page verification
│   │   ├── ghost_signals.py         # Ghost job feature extraction
│   │   └── voyager_enrichment.py    # LinkedIn Voyager enrichment
│   │
│   ├── tracking/                    # Metrics & analytics tracking
│   │   ├── comprehensive_profile_metrics.py  # Profile metrics collection
│   │   ├── weekly_metrics_collector.py       # Weekly snapshots
│   │   ├── enhanced_linkedin_metrics_collector.py # Enhanced trending
│   │   ├── follower_change_tracker.py        # Follower delta tracking
│   │   ├── outcomes_tracker.py               # Application outcomes
│   │   ├── weekly_dashboard_generator.py     # HTML report generation
│   │   └── weekly_tracking_config.py         # Automation config
│   │
│   ├── analytics/                   # Market & predictive analytics
│   │   ├── job_market_analytics.py           # Salary, skills, geographic
│   │   ├── predictive_analytics.py           # Career trajectory modeling
│   │   ├── advanced_analytics_engine.py      # Multi-dimensional analysis
│   │   ├── advanced_analytics_generator.py   # Report generation
│   │   └── rate_limiting_analysis.py         # API rate limit monitoring
│   │
│   ├── ai/                          # AI & LLM orchestration
│   │   ├── router.py                # Smart routing (Claude ↔ Llama)
│   │   ├── llm_summarizer.py        # Job description summarizer
│   │   ├── cover_letter/            # Cover letter pipeline
│   │   └── resume_routing/          # Resume extraction & routing
│   │
│   ├── integrations/                # External system integration
│   │   ├── external_job_pipeline.py # Cross-system pipeline
│   │   ├── data_exchange.py         # JSON import/export
│   │   ├── notifications.py         # Email dispatch
│   │   ├── notifications_simple.py  # Simplified notifier
│   │   ├── monitoring.py            # System health monitoring
│   │   └── unified_dashboard.py     # Multi-source unified view
│   │
│   ├── messaging/                   # Notification channels
│   │   └── telegram_messenger.py    # Telegram bot (sync + async)
│   │
│   └── utils/                       # Shared utilities
│       ├── logging_config.py        # Centralized logging
│       ├── unicode_logging.py       # Unicode-safe formatter
│       ├── text_sanitizer.py        # UTF-8 sanitization
│       ├── error_handling.py        # Global error handling, retry
│       ├── output_manager.py        # Output formatting
│       ├── job_search_configurator.py # Search parameter management
│       └── ultra_safe_config.py     # Safe config loading
│
├── scripts/                         # Executable scripts & automation
│   ├── main.py                      # CLI entry point
│   ├── launch_dashboard.py          # dashboard launcher
│   ├── start_dashboard.py           # Alt dashboard launcher
│   ├── launch_intelligence_scheduler.py # Intelligence task scheduler
│   ├── launch_intelligence_system.py    # Full system launcher
│   └── scheduled_tasks/             # Automated tasks
│       ├── daily_jobspy_detection.py      # Primary daily scraper
│       ├── daily_opportunity_detection.py # Opportunity classification
│       ├── daily_market_analysis.py       # Market trend analysis
│       ├── daily_network_insights.py      # Network analysis
│       ├── daily_summary.py               # Daily report
│       ├── dashboard_scrape_task.py       # Dashboard data collection
│       ├── weekly_intelligence_orchestrator.py # Weekly analysis
│       ├── weekly_predictive_analytics.py     # Career modeling
│       ├── weekly_content_tracking.py         # Content performance
│       ├── daily_content_performance.py       # Live LinkedIn scrape → Telegram + DB
│       ├── run_daily_content_performance.bat  # Batch launcher for Task Scheduler
│       └── biweekly_deep_analysis.py          # Deep analysis
│
├── config/                          # Configuration files
│   ├── job_search_config.json       # Search parameters
│   ├── intelligent_search_config.json # AI search config
│   ├── user_preferences.json        # User settings
│   ├── achievement_bank.json        # Pre-verified achievements for generation pipeline
│   ├── keyword_profiles/            # Keyword categorization
│   │   └── default.yaml             # GREEN/YELLOW/RED lists
│   ├── profile_intelligence.json    # Extracted skills/experience
│   └── real_linkedin_profile.json   # Cached LinkedIn profile
│
├── data/                            # Database & data storage
│   ├── job_tracker.db               # Primary job database
│   ├── job_search.db     # LinkedIn data
│   ├── company_research.db          # Company verification cache
│   └── job_pipeline_integration.db  # Cross-system integration
│
├── reports/                         # Generated reports
│   ├── daily/                       # Daily scraping reports
│   └── weekly/                      # Weekly analysis reports
│
├── logs/                            # Application logs
├── cache/                           # Runtime caches
├── output/                          # Generated application packages
├── tests/                           # Test suite
└── docs/                            # Additional documentation
    ├── ARCHITECTURE.md              # System design (legacy)
    ├── QUICK_START.md               # 5-minute setup
    ├── DATABASE_GUIDE.md            # Schema & API reference
    ├── DASHBOARD_GUIDE.md           # UI usage
    ├── JOBSPY_INTEGRATION.md        # Scraper documentation
    └── TROUBLESHOOTING.md           # Common issues & fixes
```

---

## 4. Core Subsystems

### 4.1 Web Dashboard (FastAPI)

**Module:** `src/dashboard/app.py`
**Port:** 8888
**Stack:** FastAPI + Jinja2 + HTMX + Tailwind CSS

The primary user interface. Serves HTML pages with HTMX for partial-page updates.

**Routes:**

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Job listings table with sorting, filtering, pagination |
| `/job/{id}` | GET | Detailed job view with scores, company intel, enrichment data |
| `/job/{id}/generate` | POST | Trigger application package generation |
| `/job/{id}/ghost-check` | POST | Run ghost job detection |
| `/job/{id}/verify-career` | POST | Run career page verification |
| `/tools` | GET | Dashboards, APIs, external services, job board strategy |
| `/settings` | GET/POST | Resume text, AI provider, scoring config, scraping sources |
| `/api/job/{id}/score` | GET | Score individual job (keyword or LLM, per `scoring_llm_model`) |
| `/api/score-jobs` | POST | Batch score all unscored jobs |
| `/api/scrape-jobs` | POST | Trigger scraping pipeline from dashboard |
| `/api/scrape-progress` | GET (SSE) | Real-time scraping progress via Server-Sent Events |
| `/api/scrape-cancel` | POST | Cancel a running scrape (sets `threading.Event`, raises `ScrapeCancelled`) |
| `/api/task-cancel/{task_id}` | POST | Generic task cancellation (score, rescore, enrich, verify, classify) |
| `/api/task-progress/{task_id}` | GET (SSE) | Real-time progress for any background task via Server-Sent Events |
| `/api/settings/pipeline` | POST | Save pipeline gate toggles, classification settings |
| `/api/settings/scraping` | POST | Save scraping source toggles + default search params |
| `/api/settings/generation-thresholds` | POST | Save 3-layer pipeline thresholds |
| `/api/settings/scoring-model` | POST | Save LLM model for skill extraction |
| `/api/settings/gate-lists/{name}` | POST | Save a gate keyword list (defense primes, clearance, gov signals, etc.) |
| `/api/settings/gate-lists/{name}/reset` | POST | Reset a gate list to hardcoded defaults |
| `/api/pipeline-runs` | GET | Pipeline run history with resource metrics (JSON) |
| `/api/health` | GET | Server health check with uptime |
| `/api/server/restart` | POST | Restart dashboard server (spawns new process) |
| `/api/jobs` | GET | JSON API for job data |

**Key Components:**
- `DashboardDB` — SQLite bridge with connection pooling, migrations, CRUD operations
- `AlignmentScorer` — Keyword + optional LLM scoring with blended semantic similarity
- `SemanticClassifier` — Regex keyword classifier (always-on) + optional LLM upgrade
- `AIGenerator` — Multi-provider AI for resume/cover letter generation
- `GhostDetector` — Phrase-pattern ghost job detection
- `QualityGates` — 12-point pre-application validation
- `ScrapeRunner` — Dashboard scraping pipeline (JobSpy + niche scrapers → dedup → screen → classify → score) with stop/cancel support, batch scoring optimizations, and elapsed timing
- `ListProvider` — Dynamic gate list loader (`list_provider.py`): DB override → hardcoded fallback for all 7 screening keyword lists
- **Generation Pipeline** — 3-layer fabrication-safe resume generation (context → LLM → validation)

**Settings Tabs:**

| Tab | Key Settings | Storage Keys |
|---|---|---|
| Generation | AI model, constrained pipeline thresholds | `gen_min_score_to_generate`, `gen_score_delta_floor_pct`, `gen_achievement_top_n`, `gen_achievement_coverage_min`, `gen_tool_overlap_boost`, `gen_request_timeout`, `gen_max_tokens` |
| Pipeline | Gate toggles, LLM resolver, classification | `pipeline_gate_0a`–`0j`, `pipeline_llm_resolver`, `pipeline_llm_classifier_enabled`, `pipeline_classifier_model` |
| Scraping | Source toggles (10 sources), default search params | `scraping_source_indeed`…`scraping_source_hackernews`, `scraping_keywords`, `scraping_location`, `scraping_max_results`, `scraping_posted_days`, `scraping_remote_only` |
| Filters | Salary floors, remote mode, Glassdoor | `filter_salary_hard_floor`, `filter_remote_mode`, `glassdoor_api_enabled` |
| Scoring | LLM model for skill extraction | `scoring_llm_model` |
| Gate Lists | Editable screening gate keyword lists (7 sub-tabs) | `gate_list_DEFENSE_PRIMES`, `gate_list_CLEARANCE_KEYWORDS`, `gate_list_GOV_EMPLOYER_SIGNALS`, `gate_list_STAFFING_AGENCIES`, `gate_list_STAFFING_SIGNALS`, `gate_list_DIRECT_HIRE_ALLOWLIST`, `gate_list_HARD_EXCLUDE_COMPANIES` |
| Resume | Resume text, resume version management | `resume_text` |

**Template Architecture:**
```
base.html
├── dashboard.html    (job listings + scraping pipeline UI)
├── job_detail.html   (single job)
├── tools.html        (dashboards + job boards)
├── settings.html     (configuration + server controls)
└── partials/         (HTMX fragments)
```

### 4.2 Job Scraping & Discovery

**Two scraping systems** operate independently:

1. **Scheduled Pipeline** (`scripts/scheduled_tasks/daily_jobspy_detection.py`) — Runs daily at 8AM via Windows Task Scheduler. Scrapes all 10 sources independently with full enrichment pipeline.
2. **Dashboard Pipeline** (`src/dashboard/scraper_runner.py`) — Triggered from the dashboard UI "Start Scraping" button. Configurable sources/params with real-time SSE progress.

**Primary Module:** `src/intelligence/jobspy_scraper.py`

The `JobSpyScraper` class wraps the `python-jobspy` library for aggregator sites. The `ScrapeRunner` classifies sources into two engines:

```python
# JobSpy aggregator sites (via python-jobspy library)
JOBSPY_SITES = {"indeed", "linkedin", "glassdoor", "google", "zip_recruiter"}

# Niche/direct scrapers (custom implementations)
NICHE_SITES = {"greenhouse", "ashby", "wellfound", "climatebase", "hackernews"}
```

**Data Model:** `src/intelligence/models.py`
```python
@dataclass
class JobListing:
    title: str
    company: str
    location: str
    description: str
    job_url: str
    salary_min: Optional[float]
    salary_max: Optional[float]
    source_site: str
    job_type: Optional[JobType]       # FULL_TIME, CONTRACT, etc.
    remote_type: Optional[RemoteType] # REMOTE, HYBRID, ONSITE
    posted_date: Optional[datetime]
    experience_level: Optional[ExperienceLevel]
```

**Deduplication:** Jobs are deduplicated by `job_url` (UNIQUE constraint in SQLite). Re-scraping the same URL updates metadata but doesn't create duplicates.

**Niche Scrapers:**

| Scraper | Source | Method |
|---|---|---|
| `hn_scraper.py` | Hacker News "Who is Hiring" | HN API + comment parsing |
| `greenhouse_scraper.py` | Greenhouse ATS | JSON API |
| `ashby_scraper.py` | Ashby ATS | JSON API |
| `wellfound_scraper.py` | Wellfound (ex-AngelList) | Web scraping |
| `climatebase_scraper.py` | Climatebase | Web scraping |
| `climatetechlist_scraper.py` | ClimateTechList | Web scraping |

### 4.4 Screening Pipeline (12-Gate)

**Module:** `src/screening/pipeline.py`

A sequential gate pipeline that filters jobs. Each gate receives a job and returns a `GateResult` with a `GateVerdict` (PASS, FAIL, REVIEW, SKIP). The pipeline short-circuits on the first FAIL.

```
Job In → Gate 0A → Gate 0B → ... → Gate 0J → Gate Culture → Job Out (or rejected)
```

**Gate Execution Order:**

| Order | Gate | Module | Logic |
|---|---|---|---|
| 10 | Company Research | `gate_0a_company_research.py` | Lookup company in research cache; attach metadata |
| 20 | Defense/Gov Exclusion | `gate_0b_defense_exclusion.py` | FAIL if defense prime, clearance keywords, or gov employer signals (FEMA, federal depts, etc.) — dynamic lists from DB |
| 30 | Staffing Agency | `gate_0c_staffing_agency.py` | FAIL if staffing firm or JD signals; allowlist for known direct employers — dynamic lists from DB |
| 40 | Ghost Job | `gate_0d_ghost_job.py` | FAIL if ghost signals exceed threshold |
| 50 | Tech Stack | `gate_0e_tech_stack.py` | FAIL if required tech doesn't match profile |
| 60 | Compensation | `gate_0f_compensation.py` | FAIL if salary below configured floor |
| 70 | RED Keywords | `gate_0g_red_keywords.py` | FAIL if description contains RED keywords |
| 80 | YELLOW Keywords | `gate_0h_yellow_review.py` | REVIEW if YELLOW keywords found; LLM override available |
| 90 | Alignment Score | `gate_0i_alignment_score.py` | FAIL if alignment score below threshold |
| 100 | Role Type | `gate_0j_role_type.py` | FAIL if role type doesn't match preferences |
| 110 | Culture | `gate_culture.py` | REVIEW/FAIL based on Glassdoor culture metrics |

**Override Resolution:** `src/screening/override_resolver.py`

When a gate returns REVIEW, the `OverrideResolver` can use an LLM (Ollama/Claude) to make a PASS/FAIL decision based on the full job context.

**Dynamic Gate Lists:** `src/screening/data/list_provider.py`

Gate 0B and 0C load their keyword lists dynamically at evaluation time via `get_gate_list(name)`. This checks the DB first (key pattern: `gate_list_{NAME}`), falling back to hardcoded defaults in `known_lists.py`. Users can edit all 7 lists from Settings → Gate Lists tab:

| List | Gate | Purpose |
|---|---|---|
| `DEFENSE_PRIMES` | 0B | Defense contractor company names (substring match) |
| `CLEARANCE_KEYWORDS` | 0B | Security clearance keywords in JDs (instant fail) |
| `GOV_EMPLOYER_SIGNALS` | 0B | Government/federal agency signals (word-boundary safe for short acronyms) |
| `STAFFING_AGENCIES` | 0C | Known staffing/recruiting firms (substring match) |
| `STAFFING_SIGNALS` | 0C | Staffing patterns in JDs (multi-word phrases) |
| `DIRECT_HIRE_ALLOWLIST` | 0C | Companies that bypass staffing checks (false-positive fixes) |
| `HARD_EXCLUDE_COMPANIES` | 0C | Always-exclude companies regardless of role |

**Gate Interface:**
```python
class BaseGate(ABC):
    @abstractmethod
    def evaluate(self, job: JobListing, context: dict) -> GateResult:
        """Evaluate a job against this gate's criteria."""
        pass
```

### 4.5 Enrichment & Verification

Post-screening enrichment adds intelligence to passing jobs:

#### Glassdoor Client (`src/enrichment/glassdoor_client.py`)

```python
class GlassdoorClient:
    def lookup_company(self, company_name: str) -> dict:
        """Fetch company ratings from Glassdoor via RapidAPI."""
        # Normalizes company name, queries jobs/search + companies/reviews
        # Returns: overall_rating, ceo_approval, work_life_balance,
        #          compensation_rating, career_opportunities, etc.
        # Tracks API usage in api_usage_log table
```

#### Career Page Checker (`src/enrichment/career_page_checker.py`)

3-phase verification to confirm a job listing is real:

```
Phase 1: ATS Detection
  └─ Check if job_url points to known ATS (Greenhouse, Lever, Ashby, Workday)
  └─ If ATS → VERIFIED (ATS listings are almost always real)

Phase 2: Direct Probe
  └─ HTTP HEAD/GET the job URL
  └─ Check for 200 OK, job-related content in page
  └─ If found → VERIFIED

Phase 3: Serper Search API (fallback)
  └─ Search "company_name careers site:company_domain"
  └─ Match job title against search results
  └─ If matched → VERIFIED, else → UNVERIFIED
```

#### Ghost Signals (`src/enrichment/ghost_signals.py`)

Extracts features that indicate a job posting may be fake:
- Re-post frequency (same job posted multiple times)
- Vague description language
- Missing salary information
- Posting age > 30 days
- Generic company descriptions

### 4.6 Scoring & Classification

#### Alignment Scoring (`src/dashboard/scoring.py`)

Two scoring modes, configurable via **Settings → Scoring → Skill Extraction Model**:

**Mode 1: Keyword-only** (`AlignmentScorer.score()`)
```python
class AlignmentScorer:
    def score(self, job_description: str, job_title: str) -> AlignmentResult:
        """Score job-resume alignment using weighted keyword matching."""
        # Instant (~0.1s). Matches skills from curated keyword sets.
        # Categories: technical_skills, experience, domain_knowledge,
        #             soft_skills, duty_coverage
        # Role-type classification: engineering, data, devops, management, analyst
        # Returns: overall_score (0-100), recommendation, categories with matched/gaps
```

**Mode 2: LLM-powered** (`AlignmentScorer.score_with_llm()`)
```python
def score_with_llm(self, job_description, job_title, db=None,
                   model="llama3.1:8b", provider="ollama") -> AlignmentResult:
    """LLM extracts skills from JD, fuzzy-matches against resume keywords."""
    # Supports Ollama (local) and Claude (Anthropic API)
    # Catches nuanced skills that keyword matching misses
    # Anti-hallucination: validates extracted skills against source text
    # Caches results in llm_skill_cache table
    # Falls back to keyword scoring on failure
```

#### LLM Skill Extractor (`src/dashboard/llm_skill_extractor.py`)

```python
class LLMSkillExtractor:
    """Extract structured skill lists from job descriptions using LLM."""
    # Providers: Ollama (local) or Claude (Anthropic API)
    # Prompt: zero-hallucination extraction with validation
    # Output: SkillExtractionResult (technical_skills, soft_skills)
    # Matching: fuzzy matching via SequenceMatcher (threshold: 0.75)
    # Performance: Ollama ~20s/job (with num_ctx:8192), Claude ~2s/job
```

**Configurable model** via `scoring_llm_model` setting:
- `keyword` — instant keyword-only (default)
- `llama3.1:8b`, `qwen3:4b`, etc. — local Ollama models
- `claude:claude-3-5-haiku-20241022` — fast cloud (~$0.001/job)
- `claude:claude-sonnet-4-20250514` — best quality (~$0.005/job)

#### Skill Management (Interactive)

- **Gap skills** (red tags): Click to add to your skills → stored in `user_added_skills`
- **Matched skills** (green tags): Click to exclude → stored in `user_removed_skills`
- Both persist in `dashboard_settings` and survive page refresh
- Re-score to see updated alignment after changes

#### Semantic Scoring (`src/intelligence/semantic_scorer.py`)

```python
class SemanticAlignmentScorer:
    """Sentence-transformer cosine similarity scorer."""
    # Model: all-MiniLM-L6-v2 (~80MB, ~300ms cold start)
    # Resume embedding is cached — recomputed only when resume text changes
    # JD embeddings computed on-demand (not cached)
    # Blended into AlignmentScorer: 0.60×keyword + 0.40×semantic
    #
    # Batch mode: model.encode(all_descriptions, batch_size=64) encodes
    #   all JDs in ~5 forward passes instead of N individual ones (~64× throughput)
    #
    # Score interpretation:
    #   >= 70  Strong semantic alignment
    #   50–70  Moderate alignment
    #   < 50   Weak alignment (different domain/role)
```

#### Job Classification (`src/dashboard/semantic_classifier.py`)

Two-tier classification system. Keyword classifier always runs; LLM is an opt-in upgrade.

**Tier 1: Keyword Classifier** (`classify_keyword()`) — Always on, <1ms
```python
def classify_keyword(self, title: str, description: str) -> ClassificationResult:
    """Regex-based classifier covering all 11 categories."""
    # Step 1: _quick_title_filter() — regex pre-filter for obvious non-matches
    # Step 2: Full regex patterns per category (250+ patterns)
    # Output: ClassificationResult with category, confidence, is_relevant
    # Backend: "keyword"
    # Sufficient for pipeline — gates handle precision filtering
```

**Tier 2: LLM Classifier** (`classify()`) — Optional, 7-20s/job
```python
def classify(self, title: str, description: str) -> ClassificationResult:
    """LLM-based classification via Ollama with Claude fallback."""
    # Providers: Ollama (local), Claude (cloud)
    # 11 categories: software_data_engineering, data_analysis_business_analysis,
    #   analytics_engineering, physical_infrastructure, sales_marketing,
    #   legal_finance_hr, research_science, security_operations,
    #   product_design, executive_management, other
    # Backend: "ollama" or "claude"
```

**Classification in scrape pipeline** (`scraper_runner.py`):
```python
# Always: keyword classification (instant regex)
result = classifier.classify_keyword(title, desc)
# If pipeline_llm_classifier_enabled=true: LLM upgrade
if llm_enabled:
    llm_result = classifier.classify(title, desc)  # overrides keyword
```

**Settings:** Configured in Settings → Pipeline tab.
- Keyword classifier: always on (green "Always On" badge, no toggle)
- LLM classifier: opt-in toggle (disabled by default) + model dropdown
- `pipeline_llm_classifier_enabled` — "true"/"false"
- `pipeline_classifier_model` — "ollama:llama3.1:8b", "claude:claude-3-5-haiku-20241022", etc.

**Classification → Resume Routing:** Category determines which resume version is used during generation via `VERSION_MAP` in `context_builder.py`.

### 4.7 AI & LLM Layer

#### AI Router (`src/ai/router.py`)

Smart routing between local and cloud LLMs:

```python
class AIRouter:
    def route(self, task: str, complexity: TaskComplexity) -> AIProvider:
        """Route to optimal provider based on task complexity."""
        # LOW complexity → Ollama (free, fast)
        # MEDIUM complexity → Ollama with fallback to Claude
        # HIGH complexity → Claude directly
        # Circuit breaker prevents cascading failures
```

#### AI Generator (`src/dashboard/ai_generator.py`)

```python
class AIGenerator:
    def generate_package(self, job: dict, resume: str, provider: AIProvider) -> dict:
        """Generate tailored resume + cover letter."""
        # Providers: OLLAMA (local), CLAUDE_SONNET (cloud), CLAUDE_HAIKU (fast)
        # Returns: tailored_resume, cover_letter, interview_prep, key_points
        # Tracks token usage and cost in api_usage_log
```

**Cost Tracking:**
- Claude Sonnet: $3/M input + $15/M output tokens
- Claude Haiku: $0.25/M input + $1.25/M output tokens
- Ollama: $0 (local inference)

### 4.8 Resume Generation Pipeline (3-Layer)

**Module:** `src/generation/`

A fabrication-safe resume generation pipeline with three deterministic-LLM-deterministic layers. The LLM (Layer 2) is sandwiched between two Python-only layers that constrain its input and validate its output. Nothing the LLM outputs can bypass the tool blocklist or formatting checks.

**Anti-Fabrication System (2026-03-21):** The constrained pipeline enforces strict rules preventing the LLM from rewriting bullet content. Key constraints:
- **Job titles are immutable** — "Senior Data Engineer" cannot become "Systems Engineer" or "Test Engineer"
- **Core activity preservation** — "built ETL pipeline" cannot become "built testing framework" or "built analytical pipeline"
- **Synonym-only mirroring** — Only true synonyms allowed (e.g., "ETL pipeline" → "data pipeline"), not buzzword substitution
- **Buzzword repetition cap** — No single adjective (analytical, comprehensive, systematic) may appear >3 times
- **Post-generation buzzword stripping** — `_strip_buzzword_spam()` automatically replaces over-repeated words with original resume phrasing
- **Cover letter hybrid format** — Prose+bullets with STAR expansion, honest fit paragraph, company-specific salutation
- **Cover letter metric isolation** — Cover letter must NOT repeat any metrics already used in the resume
- **AI terminology rules** — Claude Code → "agentic coding"; Claude API → "programmatic LLM integration"; "context engineering" replaces "prompt engineering"; use "augmented by" / "directed [tool] to" framing

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — Deterministic Context Assembly (context_builder.py)      │
│                                                                     │
│  Job DB row ──► VERSION_MAP routing ──► Tool tier classification    │
│  alignment_details ──► Tier 1/2/3 split ──► Achievement selection  │
│  User skill overrides ──► GenerationContext dataclass               │
│                                                                     │
│  Output: GenerationContext (hard constraints for Layer 2)            │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 2 — Constrained LLM Generation (ai_generator.py)            │
│                                                                     │
│  GenerationContext ──► System prompt with tool whitelist             │
│  ──► LLM generates resume using ONLY verified_tools_for_job         │
│  ──► Selected achievements as source material (select, don't write) │
│  ──► JD keywords for synonym-only mirroring (no buzzword replace)   │
│  ──► 10 HARD RULES: immutable titles, core activity preservation,   │
│       no metric invention, no buzzword blanket-replace               │
│  ──► Cover letter: Hybrid prose+bullets (Opening prose, 2-4 STAR    │
│       expansion bullets with bold keys, Honest Fit, Closing prose)  │
│                                                                     │
│  Output: Generated resume text + cover letter draft                 │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3 — Deterministic Output Validation (output_validator.py)    │
│                                                                     │
│  Check 1: Tier 3 tool scan (word-boundary regex for blocked tools)  │
│  Check 2: Name format (canonical name, no ALL CAPS)                 │
│  Check 3: ZIP code (20877 not 20878)                                │
│  Check 4: Contact info (email, LinkedIn URL)                        │
│  Check 5: Score delta (re-score generated text against JD)          │
│  Check 6: Buzzword spam (strip over-repeated adjectives)            │
│                                                                     │
│  Output: {fabrication_errors[], formatting_warnings[],              │
│           score_degraded, post_gen_score}                           │
└─────────────────────────────────────────────────────────────────────┘
```

#### Layer 1: Context Builder (`src/generation/context_builder.py`)

```python
def build_generation_context(db, job_id: int, resume_text: str) -> GenerationContext:
    """
    Reads all pre-computed pipeline data for the job. Makes NO API calls.

    Steps:
    1. Load job row from DB (alignment_score, job_category, description, etc.)
    2. Route to base resume version via VERSION_MAP
    3. Extract matched keywords from alignment_details JSON
    4. Fetch user skill overrides (user_added_skills, user_removed_skills)
    5. Tier classification — split JD tools into claimable vs blocked
    6. Select achievements by coverage from achievement_bank.json
    7. Load configurable thresholds from dashboard_settings
    8. Determine if human review is required
    """
```

**Resume Version Routing (`VERSION_MAP`):**

| Job Category | Resume Version | Track |
|---|---|---|
| `software_data_engineering` | RV-001 | Engineering |
| `data_analysis_business_analysis` | RV-002 | Analytics |
| `analytics_engineering` | RV-002 | Analytics |
| `executive_management` | RV-003 | Architecture Leadership |
| `business_analyst` | RV-004 | BSA |
| All others | RV-001 | Default (Engineering) |

**GenerationContext dataclass** — Everything the LLM needs, and the hard constraints it must respect:
- `verified_tools_for_job` — Tier 1 + Tier 2 tools that matched JD (whitelist)
- `blocked_tools_in_jd` — Tier 3 tools found in JD (LLM must NOT include)
- `selected_achievements` — Pre-selected by coverage score for this job category
- `gap_flags` — Tier 3 tools the JD requires (acknowledge gap, don't fabricate)
- `jd_keywords` — Top 20 keywords for synonym-only mirroring (no buzzword substitution)
- `requires_human_review` — True if gap_flags non-empty or score < threshold

**LLM Constraint Enforcement (10 Hard Rules):**
1. No technology not in VERIFIED TOOLS
2. No new bullets not derived from ACHIEVEMENT BULLETS
3. No metric not present in source bullet text
4. No production experience with BLOCKED TOOLS implied
5. **Job titles are immutable** — employment records, not marketing copy
6. No education credentials not in base resume
7. No "vibe coding" (use "AI-augmented development")
8. **Core activity preservation** — original action verb + object must survive
9. **No blanket buzzword replacement** — synonym-only swaps
10. **Adjective repetition cap** — no single adjective >3 times in entire resume

**Cover Letter Rules (Hybrid Prose+Bullets Format):**

Based on recruiter feedback and 2026 hiring data showing hybrid format has the highest response rate for technical roles:

1. **Opening paragraph (2–3 sentences, prose):** Specific role + why THIS company (reference something concrete — engineering blog, product launch, data challenge). No generic openers ("I am excited to apply...")
2. **Body (2–4 bullet points with bold key phrases):** Each bullet EXPANDS one resume achievement into a mini-STAR narrative:
   - Bold the key phrase at the start of each bullet
   - Add the organizational PROBLEM that existed before
   - Include cross-functional collaboration required
   - Name the downstream business outcome BEYOND the technical metric
3. **Honest Fit paragraph (prose):** Acknowledge specific gaps between candidate experience and JD requirements, show self-awareness
4. **Closing paragraph (2–3 sentences, prose):** Connect experience to their needs + sign off with full name + [DRAFT FLAG: Human review required]

**Content Rules:**
- Total length: 200–400 words. Maximum 4 body bullets
- Cover letter must NOT repeat any metrics used in the resume
- Company name in salutation ("Dear [Company] Hiring Team,")
- Full name in sign-off ("Sincerely, Grygorii T.")

#### Tool Tier System (`src/generation/tier3_blocklist.py`)

Three-tier tool classification determines what the LLM can and cannot claim:

| Tier | Definition | Count | Examples | Resume Policy |
|---|---|---|---|---|
| **Tier 1** (Production) | 10+ years hands-on | ~15 | Python, SQL, Azure, pandas, git | Always claim |
| **Tier 2** (Verified) | Personal projects, full ownership | ~25 | FastAPI, SQLite, Ollama, React | Claim for matching roles |
| **Tier 3** (Blocked) | No hands-on — fabrication risk | ~40 | Snowflake, dbt, Airflow, Spark, Kafka, AWS, Kubernetes | NEVER claim |

**GCP API Exception:** Google Sheets/Drive/Gmail/Docs APIs are Tier 2 (API-level personal project usage) despite "GCP" being Tier 3 (platform-level).

```python
def filter_claimable(tools: list[str]) -> tuple[list[str], list[str]]:
    """Split tools into (claimable [T1+T2], blocked [T3])."""

def is_claimable(tool: str) -> bool:
    """Return True if tool can be claimed. Checks GCP API exception first."""
```

#### Layer 3: Output Validator (`src/generation/output_validator.py`)

```python
def validate_generated_output(generated: str, context: GenerationContext, db=None) -> dict:
    """
    Post-generation validation. All checks are deterministic Python — no LLM.

    Returns:
      fabrication_errors: list[str]  — BLOCKING: Tier 3 tool found in output
      formatting_warnings: list[str] — Non-blocking: name format, missing contact info
      score_degraded: bool           — Post-gen score < base_score × delta_floor
      post_gen_score: float          — Re-scored alignment of generated text vs JD
    """
```

**Score Delta Check:** Re-instantiates `AlignmentScorer` with the generated resume text, scores it against the full JD, and flags if the score dropped below the configurable floor (default 90% of base score).

#### Achievement Bank (`config/achievement_bank.json`)

Pre-verified achievement bullets with coverage scores per job category. Selected by `select_achievements_by_coverage()`:
1. Filter to achievements with `coverage[job_category] >= coverage_min`
2. Boost score by `+overlap_boost` for each verified tool overlap with JD
3. Sort descending, return top N

#### Configurable Thresholds (Settings → Generation tab)

| Setting | DB Key | Default | Purpose |
|---|---|---|---|
| Min score to generate | `gen_min_score_to_generate` | 65 | Below this → requires human review |
| Score delta floor | `gen_score_delta_floor_pct` | 90% | Post-gen score must be ≥ base × this |
| Achievement top N | `gen_achievement_top_n` | 4 | Max achievements per resume |
| Coverage minimum | `gen_achievement_coverage_min` | 65 | Min coverage score to include |
| Tool overlap boost | `gen_tool_overlap_boost` | 5 | Points per overlapping tool |
| Request timeout | `gen_request_timeout` | 180s | LLM generation timeout |
| Max tokens | `gen_max_tokens` | 4096 | LLM max output tokens |

### 4.9 Application Package Generation (Legacy)

> *Note: This is the original generation pipeline. The 3-layer pipeline (§4.8) is the newer fabrication-safe replacement that handles both resume generation AND cover letters with anti-fabrication constraints. This legacy pipeline still handles interview prep and DOCX/PDF export.*

**Pipeline:**
```
Job + Resume
    ↓
AI Generator (tailored resume + cover letter)
    ↓
Quality Gates (12-point validation)
    ├─ Tech keyword density check
    ├─ Salary expectations alignment
    ├─ Description completeness
    ├─ Ghost job warning
    ├─ Auth info leak audit
    ├─ Platform formatting rules
    ├─ Cross-platform consistency
    └─ Duty coverage mapping
    ↓
DOCX Generator
    ├─ resume_tailored.docx
    ├─ cover_letter.docx
    └─ interview_prep.docx
    ↓
PDF Converter (LibreOffice)
    ├─ resume_tailored.pdf
    └─ cover_letter.pdf
```

**Key Modules:**
- `src/dashboard/generator.py` — Template-based generation (no AI)
- `src/dashboard/ai_generator.py` — AI-powered generation (constrained + sectional pipelines, anti-fabrication rules, `_strip_buzzword_spam()` post-processor)
- `src/dashboard/docx_generator.py` — DOCX/PDF export
- `src/dashboard/quality_gates.py` — Pre-application validation (15 quality gates)
- `src/dashboard/auth_audit.py` — Checks for leaked personal info
- `src/dashboard/duty_coverage.py` — Maps resume bullets to job requirements
- `src/dashboard/platform_rules.py` — Platform-specific formatting

**Generation Progress Tracking:**
- `_set_progress(job_id, stage, percent, message)` — Updates real-time progress
- `GET /api/generation-progress/{job_id}` — SSE endpoint for progress streaming
- Sectional pipeline reports per-section progress via `progress_cb` callback
- Constrained pipeline reports 6 stages: init → context → generating → validating → saving → done
- Frontend shows color-coded progress bar with stage labels and percentage

### 4.10 Tracking

#### Application Outcomes (`src/tracking/outcomes_tracker.py`)

Tracks the full application lifecycle:
```
Applied → Screening → Interview → Offer → Accepted/Rejected
```

#### Weekly Metrics (`src/tracking/weekly_metrics_collector.py`)

Collects weekly snapshots:
- Jobs discovered, screened, applied
- Response rates by source
- Score distribution changes
- Pipeline conversion rates

### 4.11 Messaging & Notifications

**Module:** `src/messaging/telegram_messenger.py`

```python
class TelegramMessenger:
    def send_message(self, text: str) -> bool
    def send_daily_summary(self, stats: dict) -> bool
    def send_job_alert(self, job: JobListing) -> bool
    # Async variants available
    async def send_message_async(self, text: str) -> bool
```

**Configuration (`.env`):**
```
TELEGRAM_BOT_TOKEN=bot123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

### 4.12 Company Intelligence

#### Company Verifier (`src/intelligence/company_research/verifier.py`)

```python
class CompanyVerifier:
    def verify(self, company_name: str) -> CompanyResearchResult:
        """Multi-source company verification with SQLite cache."""
        # Checks: Is it real? Defense contractor? Staffing agency?
        # Sources: Glassdoor, LinkedIn, web search
        # Cache: company_research.db (avoids re-querying)
```

#### Audience Classifier (`src/intelligence/company_research/audience_classifier.py`)

Classifies companies by audience segment (B2B, B2C, B2B2C, Internal, Government) to help prioritize applications.

---

## 5. Database Architecture

### Primary Database: `data/job_tracker.db`

#### `jobs` Table (Core)

```sql
CREATE TABLE jobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    company       TEXT NOT NULL,
    location      TEXT,
    description   TEXT,
    job_url       TEXT UNIQUE,               -- Deduplication key
    job_type      TEXT,                       -- full_time, contract, etc.
    remote_type   TEXT,                       -- remote, hybrid, onsite
    salary_min    REAL,
    salary_max    REAL,
    source_site   TEXT,                       -- indeed, linkedin, etc.

    -- Scoring
    alignment_score          REAL,            -- 0-100 keyword score
    semantic_alignment_score REAL,            -- 0-1 cosine similarity
    job_category             TEXT,            -- data_engineer, ml_engineer, etc.
    category_confidence      REAL,            -- 0-1 classification confidence
    role_type_label          TEXT,            -- IC, Manager, Lead, etc.

    -- Company Intelligence
    company_rating           REAL,            -- Glassdoor overall rating
    company_industry         TEXT,
    company_glassdoor_json   TEXT,            -- Full Glassdoor breakdown (JSON)
    career_page_verified     INTEGER,         -- 0/1
    career_page_json         TEXT,            -- Verification details (JSON)

    -- Lifecycle
    is_active     INTEGER DEFAULT 1,          -- Soft delete (0 = hidden)
    scraped_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_date   TIMESTAMP,
    applied_date  TIMESTAMP,
    status        TEXT DEFAULT 'new'           -- new, reviewing, applied, rejected, etc.
);
```

#### `application_packages` Table

```sql
CREATE TABLE application_packages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id        INTEGER REFERENCES jobs(id),
    resume_text   TEXT,
    cover_letter  TEXT,
    interview_prep TEXT,
    ai_provider   TEXT,                       -- ollama, claude_sonnet, etc.
    ai_model      TEXT,
    quality_score REAL,                       -- Quality gate aggregate score
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `application_responses` Table

```sql
CREATE TABLE application_responses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id        INTEGER REFERENCES jobs(id),
    response_type TEXT,                       -- screening, interview, offer, rejection
    response_date TIMESTAMP,
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `search_history` Table

```sql
CREATE TABLE search_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    query         TEXT NOT NULL,
    location      TEXT,
    results_count INTEGER,
    source        TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `api_usage_log` Table

```sql
CREATE TABLE api_usage_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    service       TEXT NOT NULL,               -- glassdoor, serper, anthropic
    endpoint      TEXT,                        -- Specific API endpoint
    tokens_used   INTEGER DEFAULT 0,
    cost_estimate REAL DEFAULT 0.0,
    success       INTEGER DEFAULT 1,           -- 1=success, 0=error
    error_message TEXT,
    created_at    TEXT NOT NULL
);
```

#### `settings` Table

```sql
CREATE TABLE settings (          -- actually "dashboard_settings"
    key   TEXT PRIMARY KEY,
    value TEXT
);
-- Key groups:
--   Resume:       resume_text
--   Scoring:      scoring_llm_model, user_added_skills, user_removed_skills
--   Pipeline:     pipeline_gate_0a..0j, pipeline_gate_culture, pipeline_llm_resolver,
--                 pipeline_llm_classifier_enabled, pipeline_classifier_model
--   Generation:   gen_min_score_to_generate, gen_score_delta_floor_pct,
--                 gen_achievement_top_n, gen_achievement_coverage_min,
--                 gen_tool_overlap_boost, gen_request_timeout, gen_max_tokens
--   Filters:      filter_salary_hard_floor, filter_salary_soft_floor,
--                 filter_min_llm_alignment, filter_remote_mode
--   External:     glassdoor_api_enabled
```

#### `pipeline_runs` Table

```sql
CREATE TABLE pipeline_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type        TEXT NOT NULL,          -- scrape, score, classify, generate, rescore
    started_at      TEXT,
    finished_at     TEXT,
    elapsed_seconds REAL,
    steps_json      TEXT,                   -- JSON array [{name, duration_s, items}]
    summary_json    TEXT,                   -- JSON dict {new_jobs, duplicates, scored, ...}
    cpu_min         REAL,                   -- Min CPU % during run
    cpu_max         REAL,                   -- Max CPU % during run
    cpu_avg         REAL,                   -- Avg CPU % during run
    ram_min_mb      REAL,                   -- Min process RSS (MB)
    ram_max_mb      REAL,                   -- Max process RSS (MB)
    ram_avg_mb      REAL,                   -- Avg process RSS (MB)
    ram_percent_max REAL,                   -- System-wide RAM % peak
    sample_count    INTEGER DEFAULT 0       -- Number of resource samples taken
);
```

### Secondary Databases

| Database | Purpose | Key Tables |
|---|---|---|
| `company_research.db` | Company verification cache | `company_research` (name, data_json, verified_at) |
| `job_search.db` | LinkedIn profile & connection data | `profiles`, `connections`, `metrics` |
| `job_pipeline_integration.db` | Cross-system data exchange | `integration_log`, `data_exchange` |

---

## 6. External Services & APIs

| Service | Purpose | Auth | Rate Limits | Cost | Module |
|---|---|---|---|---|---|
| **JobSpy** | Multi-source scraping | None (library) | ~100 req/day per source | Free | `jobspy_scraper.py` |
| **Glassdoor (RapidAPI)** | Company ratings | `RAPIDAPI_KEY` | Varies by plan | Per-request | `glassdoor_client.py` |
| **Serper.dev** | Google search fallback | `SERPER_API_KEY` | 2,500 free/month | $0 (free tier) | `career_page_checker.py` |
| **Anthropic Claude** | Cloud LLM (Sonnet/Haiku) | `ANTHROPIC_API_KEY` | Token-based | $3-15/M tokens | `ai_generator.py` |
| **Ollama** | Local LLM inference | None (local) | Unlimited | $0 (GPU time) | `semantic_classifier.py` |
| **Telegram API** | Bot notifications | `TELEGRAM_BOT_TOKEN` | 30 msg/sec | Free | `telegram_messenger.py` |
| **LinkedIn Voyager** | Profile enrichment | Session cookie | Aggressive limiting | Free (unofficial) | `real_linkedin_api_client.py` |

### API Usage Tracking

All external API calls are logged to `api_usage_log` with:
- Service name, endpoint, success/failure
- Tokens used (for LLM calls)
- Estimated cost
- Timestamp

Viewable on the Tools page dashboard and Real-Time Monitor.

---

## 7. Scheduled Tasks & Automation

### Windows Task Scheduler Tasks

| Task | Script | Schedule | Purpose |
|---|---|---|---|
| Daily Job Scrape | `daily_jobspy_detection.py` | Daily 8:00 AM | Scrape all sources, run screening, score, notify |
| Daily Opportunity | `daily_opportunity_detection.py` | Daily 9:00 AM | Classify and rank new opportunities |
| Daily Market | `daily_market_analysis.py` | Daily 10:00 AM | Market trend analysis |
| Daily Summary | `daily_summary.py` | Daily 6:00 PM | Telegram summary of day's findings |
| Dashboard Scrape | `dashboard_scrape_task.py` | Daily | Collect dashboard metrics |
| Content Performance | `daily_content_performance.py` | Daily 9:00 AM | Scrape LinkedIn posts/views → Telegram + DB |
| Weekly Intel | `weekly_intelligence_orchestrator.py` | Sunday | Comprehensive weekly analysis |
| Weekly Predictive | `weekly_predictive_analytics.py` | Sunday | Career trajectory modeling |
| Bi-weekly Deep | `biweekly_deep_analysis.py` | Bi-weekly | In-depth analysis report |

### Daily Job Scrape Pipeline (`daily_jobspy_detection.py`)

```
1. Load search config (keywords, locations, salary range)
2. Scrape all enabled sources via JobSpy
3. Deduplicate against existing DB (by job_url)
4. Save to job_tracker.db
5. Classify roles — keyword (always) + LLM (if enabled)
6. Score new jobs (keyword 60% + semantic 40%)
7. Run 12-gate screening pipeline
8. Enrich with Glassdoor ratings (if configured)
9. Verify career pages (3-phase)
10. Generate daily report (reports/daily/)
11. Send Telegram notification
```

### Dashboard Scrape Pipeline (`scraper_runner.py`)

```
1. User clicks "Start Scraping" on dashboard (configurable sources, keywords, location)
   - Form values (keywords, location, max_results, posted_days, remote_only) are
     persisted to DB on submit → pre-fill the form on next visit
2. ScrapeRunner classifies selected sources into JobSpy vs niche
3. JobSpy sites: scrape_jobs() via python-jobspy → DataFrame → _dataframe_to_dicts()
4. Niche sites: _scrape_niche_source() → custom scraper → List[JobListing] → .to_dict()
   - Niche keyword pre-filter: results from Greenhouse/Ashby/etc. are filtered by
     search keywords before scoring (these scrapers return ALL jobs from a company)
5. Dedup against DB (by job_url) → save new jobs
6. _screen_scraped_jobs(): 12-gate screening pipeline (tag rejections in DB)
7. _classify_new_jobs():
   a. Always: classify_keyword(title, desc)   — regex, <1ms
   b. If pipeline_llm_classifier_enabled:
      classify(title, desc)                    — Ollama/Claude, overrides keyword
8. _score_new_jobs() — with 4 performance optimizations:
   a. DutyCoverageEngine is cached at module level (avoids re-init per job)
   b. Jobs with keyword score below skip threshold bypass semantic scoring
   c. Batch embeddings: model.encode(all_descriptions, batch_size=64) — ~5 forward
      passes for 300 jobs instead of 300 individual ones (~64× throughput)
   d. AlignmentScorer.score(desc, title) — keyword (60%) + semantic (40%)
   e. Reports progress every 5 jobs to keep SSE alive
9. Progress callbacks stream via SSE → dashboard UI updates in real-time
   - Every _report() call includes [Xs] elapsed time since pipeline start
10. User can click Stop button → POST /api/scrape-cancel → sets threading.Event →
    _check_cancel() raises ScrapeCancelled → pipeline aborts cleanly
```

**Progress UI features:**
- Pipeline stage pills (Init → Scraping → Dedup → Save → Screen → Classify → Score → Done)
- Color-coded states: gray (pending) → blue+pulse (active) → green (complete) → red (error) → amber (cancelled)
- Live elapsed time counter with per-step `[Xs]` timing in activity log
- Per-source results grid (fills in as each source completes)
- Progress bar with percentage
- **Stop button** — red button appears during scraping; cancels pipeline cleanly via `threading.Event`

### Generic Task Progress & Cancellation System

All manually-triggered dashboard processes (score, rescore, enrich, verify, classify) use a unified background task system:

**Backend infrastructure (`app.py`):**
- `_task_cancel_events: dict[str, threading.Event]` — per-task cancellation signals
- `_set_task_progress(task_id, stage, percent, message)` / `_get_task_progress(task_id)` — shared progress state
- `TaskCancelled` exception — raised by `_check_task_cancel(task_id)` in task loops
- `POST /api/task-cancel/{task_id}` — generic cancel endpoint (sets event, updates progress to "cancelled")
- `GET /api/task-progress/{task_id}` — SSE endpoint streaming progress updates

**Frontend (`dashboard.html`):**
- `startTask(taskId, apiUrl, btnEl)` — creates progress bar UI, fires POST, starts SSE listener
- `stopTask(taskId)` — sends cancel POST, shows "Stopping..." feedback
- `listenTaskProgress(taskId, container, btnEl)` — SSE listener with color-coded stages
- Progress bar includes: label, elapsed timer, percentage, progress bar, message, stop button
- Terminal states (done/error/cancelled) remove stop button and re-enable action button

**Supported tasks:** `score-jobs`, `rescore-jobs`, `enrich-ratings`, `verify-career-pages`, `classify-jobs`

---

## 8. Data Flow Pipelines

### Job Discovery → Dashboard Pipeline

```
External Sources (Indeed, LinkedIn, Glassdoor, Google, HN, etc.)
    │
    ▼
JobSpy Scraper / Niche Scrapers
    │  Returns: List[JobListing]
    ▼
Deduplication (job_url UNIQUE)
    │  Skips existing URLs
    ▼
SQLite Persistence (job_tracker.db)
    │
    ▼
Classification (scraper_runner._classify_new_jobs)
    ├─ Keyword classifier (always on, regex, <1ms)
    └─ LLM classifier (optional upgrade, Ollama/Claude, 7-20s)
    │  Stores: job_category, category_confidence
    ▼
Scoring Engine (with batch optimizations)
    ├─ Keyword alignment (60% weight, cached DutyCoverageEngine)
    ├─ Skip threshold — low keyword scores bypass semantic scoring
    └─ Semantic similarity (40% weight, all-MiniLM-L6-v2, batch-encoded)
    │
    ▼
12-Gate Screening Pipeline
    │  Sequential execution, short-circuit on FAIL
    │  Gates: company research → defense → staffing → ghost →
    │         tech stack → compensation → red keywords →
    │         yellow review → alignment → role type → culture
    ▼
Enrichment Layer
    ├─ Glassdoor ratings (RapidAPI)
    ├─ Career page verification (ATS → probe → Serper)
    └─ Ghost signal extraction
    │
    ▼
FastAPI Dashboard (http://host:8888)
    ├─ Job listings with sorting/filtering
    ├─ Detailed job view with all intelligence
    ├─ Individual job scoring button (keyword or LLM-powered)
    ├─ 3-layer fabrication-safe resume generation
    ├─ Application package generation (cover letter, interview prep)
    └─ Export (DOCX/PDF)
```

### Resume Generation Pipeline (3-Layer)

```
User clicks "Generate" on scored job
    │
    ▼
Layer 1: Context Assembly (deterministic)
    ├─ Load job row (alignment_score, job_category, description)
    ├─ VERSION_MAP → base resume version (RV-001 through RV-004)
    ├─ Tier classification: JD tools → claimable (T1+T2) vs blocked (T3)
    ├─ User skill overrides (added/removed via dashboard)
    ├─ Achievement selection from bank (coverage-scored, tool-boosted)
    └─ Output: GenerationContext (hard constraints)
    │
    ▼
Layer 2: Constrained LLM Generation
    ├─ System prompt with verified_tools whitelist
    ├─ Selected achievements as source material
    ├─ JD keywords for language mirroring
    └─ Output: Generated resume text
    │
    ▼
Layer 3: Output Validation (deterministic)
    ├─ Tier 3 blocklist scan (word-boundary regex for 40+ blocked tools)
    ├─ Formatting: canonical name, ZIP 20877, email, LinkedIn
    ├─ Score delta: re-score generated text vs JD (must be ≥ 90% of base)
    └─ Output: {fabrication_errors, formatting_warnings, score_degraded}
    │
    ▼
Dashboard: Show validation results
    ├─ fabrication_errors → BLOCK (hard fail, cannot submit)
    ├─ formatting_warnings → WARN (show to user, non-blocking)
    └─ score_degraded → FLAG (needs review)
```

### Application Package Pipeline

```
User selects job on dashboard
    │
    ▼
Resume text loaded from settings
    │
    ▼
AI Generator (Ollama or Claude)
    ├─ Tailored resume sections
    ├─ Custom cover letter
    └─ Interview preparation notes
    │
    ▼
Quality Gates (12 checks)
    ├─ Tech keyword density
    ├─ Auth info leak audit
    ├─ Platform format rules
    ├─ Duty coverage mapping
    └─ ... (8 more checks)
    │
    ▼
DOCX Generation
    ├─ resume_tailored.docx
    ├─ cover_letter.docx
    └─ interview_prep.docx
    │
    ▼
PDF Conversion (LibreOffice)
    │
    ▼
Stored in application_packages table
    │
    ▼
Download from dashboard
```

---

## 9. Configuration

### Environment Variables (`.env`)

```bash
# External APIs
RAPIDAPI_KEY=...              # Glassdoor via RapidAPI
SERPER_API_KEY=...            # Serper.dev Google search
ANTHROPIC_API_KEY=...         # Claude API

# Telegram
TELEGRAM_BOT_TOKEN=...       # Bot token from BotFather
TELEGRAM_CHAT_ID=...         # Target chat/group ID

# LinkedIn (optional)
LINKEDIN_SESSION_COOKIE=...  # Voyager API auth

# Local AI
OLLAMA_HOST=http://localhost:11434  # Ollama server URL
```

### Search Configuration (`config/job_search_config.py`)

`SEARCH_TERMS` defines target roles; `JOBSPY_SEARCH_QUERIES` maps them to scraper queries.

**Target roles:**
- **Data Engineering (primary):** Senior Data Engineer, Staff Data Engineer, Principal Data Engineer, Data Platform Engineer, Data Infrastructure Engineer
- **Backend/Systems:** Senior Backend Engineer, Senior Python Engineer, Staff/Principal Software Engineer, Senior Systems Engineer
- **Cloud/Infrastructure:** Senior Cloud Engineer, Cloud Platform Engineer, Senior DevOps Engineer, Platform Engineer, SRE
- **Analytics:** Senior Data Analyst, Senior Business Analyst
- **Product/Leadership:** Senior Product Engineer, Technical Lead - Data, Engineering Manager - Data

### Keyword Profiles (`config/keyword_profiles/default.yaml`)

```yaml
green_keywords:
  technical:
    - "data pipeline"
    - "dbt"
    - "airflow"
    - "spark"
    - "kafka"
  domain:
    - "climate tech"
    - "renewable energy"

yellow_keywords:
  - "on-site preferred"
  - "clearance preferred"
  - "travel required"

red_keywords:
  - "active TS/SCI clearance required"
  - "polygraph required"
  - "defense contractor"
  - "must work on-site 5 days"
```

### Gate Screening Lists (`src/screening/data/`)

**Storage:** DB-first with hardcoded fallback. Editable from Settings → Gate Lists tab.

- **`known_lists.py`** — Hardcoded default sets (used as fallback when no DB override exists)
- **`list_provider.py`** — Dynamic loader: checks `gate_list_{NAME}` in DB (JSON array), falls back to `known_lists.py`
- **DB key pattern:** `gate_list_DEFENSE_PRIMES`, `gate_list_GOV_EMPLOYER_SIGNALS`, etc.
- **7 editable lists:** Defense Primes, Clearance Keywords, Gov Employer Signals, Staffing Agencies, Staffing Signals, Direct-Hire Allowlist, Hard Exclude Companies
- **Matching rules:** Short signals (<5 chars like "fema", "nsa") use `\b`word-boundary regex; longer phrases use substring matching

---

## 10. Entry Points

### Interactive Use

| Entry Point | Command | Purpose |
|---|---|---|
| Web Dashboard | `python -m uvicorn src.dashboard.app:app --host 0.0.0.0 --port 8889` | Primary web UI |
| CLI | `python scripts/main.py` | Command-line interface |

### Automated Use

| Entry Point | Trigger | Purpose |
|---|---|---|
| `daily_jobspy_detection.py` | Windows Task Scheduler (daily) | Scrape + screen + score |
| `daily_summary.py` | Windows Task Scheduler (daily) | Telegram daily report |
| `weekly_intelligence_orchestrator.py` | Windows Task Scheduler (weekly) | Comprehensive analysis |

---

## 11. Key Architectural Patterns

### Gate Pattern (Screening)
Each screening criterion is encapsulated as an independent gate implementing `BaseGate.evaluate()`. Gates are registered via `@register_gate` decorator and executed sequentially by `ScreeningPipeline`. Short-circuit on first FAIL prevents unnecessary computation.

### Multi-Provider AI (Router)
The `AIRouter` selects between Ollama (free, local) and Claude (paid, cloud) based on task complexity. A circuit breaker prevents cascading failures when a provider is down. All providers implement the same generation interface.

### Cache-Driven Enrichment
Company research, Glassdoor ratings, and career page verification results are cached in SQLite databases. Subsequent lookups for the same company hit the cache instead of making expensive API calls.

### Layered Scoring
Jobs receive two scores that are blended (60/40):
1. **Keyword alignment (60%)** — Exact and fuzzy keyword matching against resume (`AlignmentScorer.score()`)
2. **Semantic similarity (40%)** — `all-MiniLM-L6-v2` sentence-transformer cosine similarity (`SemanticAlignmentScorer`)

Additionally, the **individual job scoring button** (`/api/job/{id}/score`) supports LLM-powered skill extraction via `AlignmentScorer.score_with_llm()`, configured by `scoring_llm_model` in Settings → Scoring. This extracts nuanced skills that keyword matching misses, with anti-hallucination validation and caching in `llm_skill_cache`.

**Batch scoring performance optimizations:**
- **DutyCoverageEngine caching** — Engine instance cached at module level, avoiding expensive re-init per job
- **Skip threshold** — Jobs scoring below a keyword threshold skip semantic scoring entirely
- **Batch embeddings** — `model.encode(all_descriptions, batch_size=64)` processes all JDs in ~5 forward passes instead of N individual ones
- **Niche keyword pre-filter** — Niche scraper results (Greenhouse, Ashby, etc.) are filtered by search keywords before entering the scoring pipeline

### Two-Tier Classification
Classification uses a layered approach matching the scoring pattern:
1. **Keyword classifier (always on)** — Instant regex-based, <1ms, 11 categories
2. **LLM classifier (opt-in)** — Ollama/Claude upgrade, 7-20s/job, higher accuracy
Category only affects resume version routing at generation time — gates handle all precision filtering.

### 3-Layer Fabrication Prevention
Resume generation sandwiches the LLM between two deterministic Python layers:
1. **Layer 1 (Deterministic)** — Builds constrained context from pre-computed pipeline data
2. **Layer 2 (Constrained LLM)** — Generates resume within tool whitelist boundaries
3. **Layer 3 (Deterministic)** — Validates output: Tier 3 blocklist scan, formatting, score delta check

### Pipeline Resource Monitoring
Every pipeline run (scrape, batch score, rescore) is wrapped in a `PipelineRunTracker` that samples CPU and RAM at 2-second intervals via `psutil`. On completion, min/max/avg resource usage is persisted to `pipeline_runs`. The Tools page shows a 30-day aggregate dashboard and an expandable recent runs table with per-step breakdowns.

### Soft Delete
Jobs are never physically deleted. The `is_active` column (default 1) is set to 0 when a user dismisses a job, preserving history for analytics.

---

## 12. Dependencies

### Core Framework
| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.109.0 | Web framework |
| `uvicorn` | 0.34.2 | ASGI server |
| `jinja2` | 3.1.6 | Template rendering |
| `python-dotenv` | 0.21.1 | .env loading |

### Data & Storage
| Package | Version | Purpose |
|---|---|---|
| `pandas` | 2.3.1 | Data manipulation |
| `sqlalchemy` | 2.0.43 | ORM (optional use) |
| `plotly` | 6.3.1 | Interactive charts |
| `xlsxwriter` | 3.2.9 | Excel export |
| `pyarrow` | 23.0.1 | Columnar data processing |

### Scraping & HTTP
| Package | Version | Purpose |
|---|---|---|
| `python-jobspy` | 1.1.76 | Multi-site job scraping |
| `beautifulsoup4` | 4.13.4 | HTML parsing |
| `requests` | 2.32.4 | HTTP client |
| `aiohttp` | 3.12.15 | Async HTTP |

### AI & ML
| Package | Version | Purpose |
|---|---|---|
| `anthropic` | 0.60.0 | Claude API client |
| `openai` | 1.100.0 | OpenAI API client |
| `scikit-learn` | >=1.4.0 | ML algorithms |
| `sentence-transformers` | — | Embedding models |

### Document Generation
| Package | Version | Purpose |
|---|---|---|
| `python-docx` | 1.1.2 | DOCX generation |
| LibreOffice (system) | — | PDF conversion |

### Messaging
| Package | Version | Purpose |
|---|---|---|
| `Telethon` | 1.40.0 | Telegram client |
| `twilio` | 8.13.0 | SMS/voice (optional) |

---

## 13. Testing

### Test Structure

```
tests/
├── test_scoring.py          # AlignmentScorer unit tests
├── test_gates.py            # Individual gate tests
├── test_pipeline.py         # Full screening pipeline
├── test_ghost_detector.py   # Ghost job detection
├── test_classifier.py       # Semantic classification
└── test_db.py               # Database operations

test_constrained_10jobs.py   # Generation pipeline: settings + 10 random jobs through L1+L3
                             # Tests: threshold loading, context building, output validation

scripts/testing/
├── test_gate_pipeline.py    # Integration: full gate flow
├── test_db_migrations.py    # Database migration testing
├── test_enrichment.py       # Glassdoor + career page tests
└── test_end_to_end.py       # Full pipeline test
```

### Running Tests

```bash
# Unit tests
pytest tests/ -v

# Integration tests
python scripts/testing/test_gate_pipeline.py
python scripts/testing/test_enrichment.py

# Full system validation
python scripts/testing/test_end_to_end.py
```

---

*This document is auto-maintained. For the latest state, check the codebase directly.*
