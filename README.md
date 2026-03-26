# Job Search Intelligence

An AI-powered job search pipeline that discovers, screens, scores, and ranks opportunities across 10+ job boards — then generates fabrication-safe application materials.

**[Read the full engineering write-up on LinkedIn →](https://www.linkedin.com/in/grygorii-t/recent-activity/all/)**

## The Problem

Job boards are designed for volume, not signal. A senior engineer's daily reality: 50+ descriptions to read, every company to Google, tech stacks to cross-reference, salary ranges to verify, Glassdoor ratings to check, careers pages to confirm the role actually exists. Most of that time is wasted on ghost postings (21-40% of listings), staffing agency spam, and roles that don't match.

This system automates the entire pipeline — from discovery through screening to application material generation — with explicit quality gates at every stage.

## Architecture

```
Discovery          Screening           Scoring             Generation
──────────         ─────────           ───────             ──────────
10 job boards  →   12-gate pipeline →  Keyword (60%) +  →  Context assembly
  Indeed             Defense check      Semantic (40%)      (deterministic)
  Glassdoor          Agency filter      cosine similarity       ↓
  Google Jobs        Ghost detection                        LLM generation
  Greenhouse         Tech stack match                       (constrained)
  Ashby              Salary floor                               ↓
  Wellfound          Red keywords                           Output validation
  Hacker News        LLM override                           (deterministic)
  Climatebase        ...                                        ↓
  Levels.fyi                                                Resume + cover
  Otta                                                      letter (.docx)
      ↓                   ↓                  ↓
  SQLite DB         60-70% filtered     Top matches         Fabrication-safe
                    before dashboard    ranked by fit       (every claim verified)
```

## 12-Gate Screening Pipeline

Jobs pass through sequential gates. First failure = short-circuit rejection. No wasted processing.

| Gate | Check | Action on Fail |
|------|-------|----------------|
| 0A | Company research database | Skip if already declined |
| 0B | Defense/government contractor | Auto-reject |
| 0C | Staffing agency detection | Auto-reject |
| 0D | Ghost job signals (age, re-posts, vague JD) | Auto-reject |
| 0E | Tech stack mismatch | Auto-reject |
| 0F | Compensation below floor | Auto-reject |
| 0G | Red keywords (dealbreakers) | Auto-reject |
| 0H | Yellow keywords (review needed) | LLM override decision |
| 0I | Alignment score threshold | Auto-reject if below minimum |
| 0J | Role type classification | Skip if outside target roles |
| Culture | Company culture signals | Flag for review |
| Override | LLM resolver for edge cases | Final PASS/FAIL/REVIEW |

## Dual-Method Alignment Scoring

Two scoring methods run independently, then blend:

**Keyword matching (60% weight):** GREEN/YELLOW/RED keyword profiles per role type. Exact and partial matches against job description text. Fast, deterministic, interpretable.

**Semantic similarity (40% weight):** Sentence-transformer embeddings compare resume sections against JD requirements. Cosine similarity catches what keywords miss — "data pipeline" matches "ETL automation", "API development" matches "backend services."

Combined score ranks every job that survives the screening pipeline.

## 3-Layer Resume Generation

The LLM is sandwiched between two deterministic Python layers. It can't fabricate.

1. **Context Assembly (Python):** Pulls verified achievements from the achievement bank. Assembles role-specific context. No LLM involved.
2. **Constrained Generation (LLM):** Claude or Ollama generates tailored bullets within strict constraints. Can only reference pre-verified achievements and tools.
3. **Output Validation (Python):** Tier 3 blocklist catches unverified tool claims. Cross-references every bullet against the achievement database. Rejects anything that can't survive an interview.

## Ghost Job Detection

Multi-signal analysis flags suspicious postings:

- Posting age > 45 days
- Re-posted multiple times with same description
- Missing salary information on senior roles
- Vague job descriptions (low specificity score)
- "Urgently hiring" tag on old postings
- Role absent from company's own careers page (3-phase verification: ATS detection → direct URL probe → search API fallback)

## Tech Stack

**Core:** Python 3.13, FastAPI, SQLite, SQLAlchemy

**Frontend:** Jinja2 + HTMX + Tailwind CSS (server-rendered, partial page updates)

**AI/ML:** Anthropic Claude API, Ollama (local LLM option), sentence-transformers, scikit-learn

**Scraping:** python-jobspy (multi-site), BeautifulSoup, aiohttp + custom ATS scrapers (Greenhouse, Ashby, Wellfound, HN)

**Document Generation:** python-docx, LibreOffice (PDF conversion)

**Notifications:** Telegram bot (daily opportunity alerts)

**Scheduling:** Windows Task Scheduler integration for automated daily scrapes

## Project Structure

```
src/
  intelligence/      Multi-source job discovery + scraping (40 files)
  dashboard/         FastAPI web UI + HTMX frontend (20 files)
  screening/         12-gate pipeline + orchestration
  generation/        3-layer fabrication-safe resume generation
  database/          SQLite persistence + migrations
  enrichment/        Glassdoor ratings, career page verification, ghost detection
  ai/                LLM routing (Claude / Ollama), cover letter pipeline
  messaging/         Telegram bot integration
  integrations/      External pipelines, notifications
  utils/             Logging, config, error handling
scripts/
  scheduled_tasks/   Daily/weekly automation jobs
  setup/             Installation + initialization
config/              Keyword profiles, achievement bank
tests/               Unit + integration + feature tests (50+ files)
```

## Getting Started

```bash
# Clone
git clone https://github.com/gtykhon/job_search_intelligence.git
cd job_search_intelligence

# Environment
cp .env.example .env
# Edit .env with your API keys (Anthropic, Ollama endpoint, etc.)

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/setup/initialize_database.py

# Launch dashboard
python -m uvicorn src.dashboard.app:app --reload --port 8000

# Run a scrape
python scripts/scheduled_tasks/daily_jobspy_detection.py
```

## Key Technical Decisions

**SQLite over PostgreSQL:** Single-user system, no concurrent write pressure, zero-config deployment. WAL mode handles the read concurrency from dashboard queries during scrape runs.

**HTMX over React:** Server-rendered partials eliminate the SPA build chain. Job cards update via SSE without full page reloads. The entire frontend is Jinja2 templates + ~200 lines of HTMX attributes.

**BackgroundTasks over Celery:** Scraping jobs run as FastAPI BackgroundTasks. No Redis, no broker, no worker processes. Good enough for single-user throughput.

**Ollama as LLM fallback:** Claude API for high-quality scoring and generation. Ollama with local models for bulk classification and keyword extraction. Keeps API costs predictable.

**Deterministic sandwich for generation:** LLM-only resume generation hallucinates tools and inflates metrics. Wrapping the LLM between Python-only context assembly and Python-only validation eliminates fabrication. The LLM is powerful but constrained.

## Project Context

This is a production system I built and use daily for my own job search. The architecture reflects real constraints: scraping 10 sources without getting rate-limited, screening hundreds of jobs without manual review, and generating application materials that won't embarrass me in an interview.



## Author

**Grygorii T.** — [LinkedIn](https://linkedin.com/in/grygorii-t) | [GitHub](https://github.com/gtykhon)
