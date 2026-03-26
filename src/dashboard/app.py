"""
Job Intelligence Dashboard — FastAPI + Jinja2 + HTMX + Tailwind CSS

Permanent web dashboard for:
  - Viewing all scraped jobs (remote-first sorting)
  - Alignment scoring against resume
  - Auto/manual resume + cover letter generation
  - Application package management
"""

import json
import logging
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import StreamingResponse

# Add parent paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)

from src.dashboard.db import DashboardDB
from src.dashboard.scoring import AlignmentScorer
from src.dashboard.generator import generate_application_package
from src.dashboard.ghost_detector import detect_ghost_job, flag_ghost_jobs_batch
from src.dashboard.ai_generator import (
    AIGenerator, AIProvider, get_available_models, get_model_display_name,
)
from src.dashboard.quality_gates import run_quality_gates
from src.dashboard.docx_generator import generate_docx_package, convert_to_pdf

# ── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── App Setup ───────────────────────────────────────────────────────

app = FastAPI(title="Job Intelligence Dashboard", version="1.0.0")

DASHBOARD_DIR = Path(__file__).resolve().parent
_ENV_PATH = DASHBOARD_DIR.parent.parent.parent / ".env"  # project root .env
app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(DASHBOARD_DIR / "templates"))


# ── Job description formatter (bold headers + bullets) ─────────────
def _format_job_description(text: str) -> str:
    from markupsafe import escape, Markup
    if not text:
        return Markup("No description available.")
    lines = text.split("\n")
    n = len(lines)

    # --- Pass 1: identify headers ---
    is_header = [False] * n
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith(("•", "-", "–", "▪", "*", "►")):
            continue
        if len(stripped) <= 80 and not stripped.endswith((".", ",", ";", "!", "?")):
            # Next non-empty line should be longer (body text)
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j >= n or len(lines[j].strip()) > len(stripped):
                is_header[i] = True

    # --- Pass 2: identify list items ---
    # A "list section" starts after a header and contains lines that are
    # each surrounded by blank lines (blank-line-separated paragraphs).
    # The section ends when we hit a long paragraph (>3 sentences) or
    # a genuine new header (very short, clearly a section title).
    is_list_item = [False] * n
    in_section = False
    for i in range(n):
        stripped = lines[i].strip()
        if not stripped:
            continue
        if is_header[i] and not in_section:
            in_section = True
            continue
        if is_header[i] and in_section:
            # Short lines that look like headers but are inside a list
            # section are probably list items (e.g. "Maintain regular
            # communication with cross-functional stakeholders").
            # Only treat as a real header if very short (≤40 chars).
            if len(stripped) <= 40:
                in_section = True  # new sub-section
                continue
            else:
                # Reclassify as list item, not header
                is_header[i] = False
                is_list_item[i] = True
                continue
        if not in_section:
            continue
        # Check if this line is between blank lines
        prev_blank = (i == 0 or not lines[i - 1].strip())
        next_blank = (i + 1 >= n or not lines[i + 1].strip())
        if prev_blank and next_blank:
            # Heuristic: if it's very long (>300 chars) and has multiple
            # sentences, it's probably a body paragraph, not a list item
            if len(stripped) > 300 and stripped.count('.') > 3:
                in_section = False
            else:
                is_list_item[i] = True
        else:
            # Contiguous text block → end of list section
            in_section = False

    # --- Pass 3: render (collapse blank lines between list items) ---
    out = []
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        safe = str(escape(raw))
        if not stripped:
            # Skip blank lines between consecutive list items or after headers
            prev_is_list = (i > 0 and (is_list_item[i - 1] or is_header[i - 1]
                           or (lines[i - 1].strip().startswith(("•", "–", "▪", "►")))))
            # Look ahead to next non-blank line
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            next_is_list = (j < n and (is_list_item[j] or is_header[j]
                           or (lines[j].strip().startswith(("•", "–", "▪", "►")))))
            if prev_is_list and next_is_list:
                continue  # collapse between list items
            if next_is_list or (j < n and is_header[j]):
                continue  # collapse before headers/list items
            out.append(safe)
        elif is_header[i]:
            out.append(f"<strong>{str(escape(stripped))}</strong>")
        elif is_list_item[i]:
            out.append(f"  • {str(escape(stripped))}")
        elif stripped.startswith(("•", "–", "▪", "►")):
            out.append(safe)
        else:
            out.append(safe)

    return Markup("\n".join(out))

templates.env.filters["format_jd"] = _format_job_description


# Global instances
db = DashboardDB()
scorer = AlignmentScorer()

# Generation progress tracking (job_id -> {stage, percent, message})
import threading
import subprocess
_generation_progress: dict = {}
_progress_lock = threading.Lock()

# ── Unified Task Progress System ──────────────────────────────────
# Tracks progress for any long-running operation (scoring, enriching, reports, etc.)
_task_progress: dict = {}  # task_id -> {stage, percent, message, started, updated}
_task_lock = threading.Lock()

_task_cancel_events: dict[str, threading.Event] = {}  # task_id -> Event

def _set_task_progress(task_id: str, stage: str, percent: int, message: str):
    """Update progress for a named task."""
    with _task_lock:
        existing = _task_progress.get(task_id, {})
        _task_progress[task_id] = {
            "task_id": task_id,
            "stage": stage,
            "percent": min(percent, 100),
            "message": message,
            "started": existing.get("started", datetime.now().isoformat()),
            "updated": datetime.now().isoformat(),
        }

def _get_task_progress(task_id: str) -> dict:
    with _task_lock:
        return _task_progress.get(task_id, {}).copy()

def _clear_task(task_id: str):
    with _task_lock:
        _task_progress.pop(task_id, None)

def _get_cancel_event(task_id: str) -> threading.Event:
    """Get or create a cancel event for a task."""
    if task_id not in _task_cancel_events:
        _task_cancel_events[task_id] = threading.Event()
    return _task_cancel_events[task_id]

class TaskCancelled(Exception):
    """Raised when a task is cancelled by the user."""
    pass

def _check_task_cancel(task_id: str):
    """Check if a task has been cancelled; raise TaskCancelled if so."""
    evt = _task_cancel_events.get(task_id)
    if evt and evt.is_set():
        raise TaskCancelled(task_id)

# Load resume from settings on startup
_resume = db.get_setting("resume_text", "")
if _resume:
    scorer.set_resume(_resume)


# ── Template Helpers ────────────────────────────────────────────────

def _salary_str(job: dict) -> str:
    s_min, s_max = job.get("salary_min"), job.get("salary_max")
    if s_min and s_max:
        return f"${s_min:,.0f} - ${s_max:,.0f}"
    if s_min:
        return f"${s_min:,.0f}+"
    if s_max:
        return f"Up to ${s_max:,.0f}"
    return ""

def _score_color(score) -> str:
    if score is None:
        return "gray"
    if score >= 70:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"

def _score_badge(score) -> str:
    if score is None:
        return ""
    color = _score_color(score)
    colors = {
        "green": "bg-green-100 text-green-800",
        "yellow": "bg-yellow-100 text-yellow-800",
        "red": "bg-red-100 text-red-800",
        "gray": "bg-gray-100 text-gray-600",
    }
    css = colors.get(color, colors["gray"])
    return f'<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {css}">{score:.0f}%</span>'

def _remote_badge(remote_type) -> str:
    if not remote_type:
        return ""
    if remote_type == "remote":
        return '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">Remote</span>'
    if remote_type == "hybrid":
        return '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">Hybrid</span>'
    return '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">On-site</span>'

def _source_badge(source) -> str:
    if not source:
        return ""
    source_colors = {
        "indeed": "bg-indigo-100 text-indigo-700",
        "linkedin": "bg-sky-100 text-sky-700",
        "glassdoor": "bg-emerald-100 text-emerald-700",
        "google_jobs": "bg-orange-100 text-orange-700",
        "hackernews": "bg-orange-100 text-orange-800",
        "wellfound": "bg-pink-100 text-pink-700",
        "climatebase": "bg-teal-100 text-teal-700",
        "greenhouse": "bg-lime-100 text-lime-700",
        "ashby": "bg-cyan-100 text-cyan-700",
        "climatetechlist": "bg-emerald-100 text-emerald-800",
    }
    css = source_colors.get(source, "bg-gray-100 text-gray-600")
    label = source.replace("_", " ").title()
    return f'<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {css}">{label}</span>'

def _time_ago(date_str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str)
        delta = datetime.now() - dt
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        return "just now"
    except (ValueError, TypeError):
        return ""

def _scraped_at(job: dict) -> str:
    """Format the scraped_date as a readable timestamp, e.g. 'Mar 16, 2:34 PM'."""
    date_str = job.get("scraped_date")
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).replace(tzinfo=None)
        # Use %#d / %#I on Windows (no zero-pad), %-d / %-I on Linux/Mac
        import os
        no_pad = "#" if os.name == "nt" else "-"
        return dt.strftime(f"%b %{no_pad}d, %{no_pad}I:%M %p")
    except (ValueError, TypeError):
        return ""

def _job_age(job: dict) -> str:
    """Calculate how old a job posting is, preferring posted_date over scraped_date."""
    date_str = job.get("posted_date") or job.get("scraped_date")
    if not date_str:
        return "?"
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).replace(tzinfo=None)
        days = (datetime.now() - dt).days
        if days == 0:
            return "Today"
        if days == 1:
            return "1d"
        if days < 7:
            return f"{days}d"
        if days < 30:
            weeks = days // 7
            return f"{weeks}w"
        months = days // 30
        return f"{months}mo"
    except (ValueError, TypeError):
        return "?"

def _job_age_days(job: dict) -> int:
    """Get numeric age in days for sorting/coloring."""
    date_str = job.get("posted_date") or job.get("scraped_date")
    if not date_str:
        return 999
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).replace(tzinfo=None)
        return max(0, (datetime.now() - dt).days)
    except (ValueError, TypeError):
        return 999

def _age_color(days: int) -> str:
    if days <= 1:
        return "text-green-600"
    if days <= 3:
        return "text-blue-600"
    if days <= 7:
        return "text-gray-600"
    if days <= 14:
        return "text-yellow-600"
    return "text-red-500"

# Package output directory
PACKAGES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "packages"

# Register template globals
templates.env.globals.update({
    "salary_str": _salary_str,
    "score_color": _score_color,
    "score_badge": _score_badge,
    "remote_badge": _remote_badge,
    "source_badge": _source_badge,
    "time_ago": _time_ago,
    "job_age": _job_age,
    "job_age_days": _job_age_days,
    "age_color": _age_color,
    "scraped_at": _scraped_at,
    "ghost_check": detect_ghost_job,
    "now": lambda: datetime.now(),
    "format_jd": _format_job_description,
})


# ── Routes: Pages ───────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    days: int = Query(7, ge=1, le=90),
    source: Optional[str] = Query(None),
    remote_only: bool = Query(False),
    search: Optional[str] = Query(None),
    sort: str = Query("remote_first"),
    min_score: Optional[str] = Query(None),
    min_salary: Optional[str] = Query(None),
    seniority: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """Main dashboard page."""
    # Convert empty strings to None, then to int
    _min_score = int(min_score) if min_score and min_score.strip().isdigit() else None
    _min_salary = int(min_salary) if min_salary and min_salary.strip().isdigit() else None
    jobs = db.get_jobs(
        days=days, source=source, remote_only=remote_only,
        search=search, sort=sort, limit=200,
        min_score=_min_score, min_salary=_min_salary,
        seniority=seniority, location=location, status=status,
    )
    stats = db.get_stats(days=days)
    sources = db.get_sources()
    auto_generate = db.get_setting("auto_generate") == "true"
    has_resume = bool(db.get_setting("resume_text"))
    packages = db.get_job_ids_with_packages()

    # Bulk-load response statuses for all displayed jobs
    job_ids = [j["id"] for j in jobs]
    responses = db.get_responses_for_jobs(job_ids)

    scraping_defaults = _load_scraping_settings()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "jobs": jobs,
        "stats": stats,
        "sources": sources,
        "auto_generate": auto_generate,
        "has_resume": has_resume,
        "packages": packages,
        "responses": responses,
        "scraping": scraping_defaults,
        "filters": {
            "days": days,
            "source": source,
            "remote_only": remote_only,
            "search": search or "",
            "sort": sort,
            "min_score": _min_score,
            "min_salary": _min_salary,
            "seniority": seniority or "",
            "location": location or "",
            "status": status or "",
        },
    })


@app.get("/job/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int):
    """Job detail page."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Parse alignment details
    alignment = None
    if job.get("alignment_details"):
        try:
            alignment = json.loads(job["alignment_details"])
        except json.JSONDecodeError:
            pass

    # Parse Glassdoor breakdown JSON
    glassdoor = None
    if job.get("company_glassdoor_json"):
        try:
            glassdoor = json.loads(job["company_glassdoor_json"])
        except json.JSONDecodeError:
            pass

    # Parse career page verification JSON
    career_page = None
    if job.get("career_page_json"):
        try:
            career_page = json.loads(job["career_page_json"])
        except json.JSONDecodeError:
            pass

    package = db.get_application_package(job_id)
    response = db.get_response(job_id)

    # Parse generation metadata (from constrained pipeline)
    gen_meta = None
    if package and package.get("generation_metadata"):
        try:
            gen_meta = json.loads(package["generation_metadata"])
        except (json.JSONDecodeError, TypeError):
            pass

    # Ghost job detection
    ghost = detect_ghost_job(job)

    # Quality gates (if package exists)
    quality_report = None
    if package and package.get("status") == "generated":
        resume = package.get("resume_text", "")
        cover = package.get("cover_letter_text", "")
        if resume and cover:
            try:
                qr = run_quality_gates(job, resume, cover, alignment)
                quality_report = {
                    "total_gates": qr.total_gates,
                    "passed": qr.passed,
                    "failed": qr.failed,
                    "overall_passed": qr.overall_passed,
                    "results": [
                        {"gate_name": g.gate_name, "passed": g.passed,
                         "severity": g.severity, "message": g.message}
                        for g in qr.results
                    ],
                }
            except Exception as e:
                logger.warning(f"Quality gates failed for job {job_id}: {e}")

    # Available AI models for generation picker
    available = get_available_models()
    ai_models = [
        {"provider": m.provider.value, "model_name": m.model_name,
         "display_name": m.display_name, "speed": m.speed_rating}
        for m in available
    ]

    # Serper-resolved link to the job on the company's own website
    company_careers_url = None
    if career_page:
        company_careers_url = career_page.get("company_careers_url")

    # Auto-detect recommended resume track based on job title
    _track_scorer = AlignmentScorer(enable_semantic_filter=False)
    recommended_track = _track_scorer._classify_role(job.get("title", ""), job.get("description", ""))

    # Check for prior applications at the same company
    company_applications = []
    company_name = job.get("company", "")
    if company_name:
        with db.get_connection() as conn:
            rows = conn.execute(
                """SELECT j.id, j.title, ar.response_type, ar.created_at
                   FROM application_responses ar
                   JOIN jobs j ON j.id = ar.job_id
                   WHERE LOWER(j.company) = LOWER(?)
                     AND ar.response_type IN ('applied','phone_screen','interview','offer','rejected')
                     AND j.id != ?
                   ORDER BY ar.created_at DESC""",
                (company_name, job_id),
            ).fetchall()
            company_applications = [dict(r) for r in rows]

    # Load excluded skills so the template can filter them out of matched tags
    _excluded_raw = db.get_setting("user_removed_skills", "[]")
    _excluded_skills = set(json.loads(_excluded_raw))

    # Build back-link with preserved filters from query string
    filter_keys = ["days", "sort", "search", "remote_only", "min_score",
                    "min_salary", "seniority", "location", "status", "source"]
    filter_params = {k: request.query_params[k]
                     for k in filter_keys if k in request.query_params}
    back_url = "/?" + "&".join(f"{k}={v}" for k, v in filter_params.items()) if filter_params else "/"

    formatted_desc = _format_job_description(job.get("description", ""))

    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "job": job,
        "formatted_description": formatted_desc,
        "alignment": alignment,
        "glassdoor": glassdoor,
        "package": package,
        "gen_meta": gen_meta,
        "response": response,
        "ghost": ghost,
        "career_page": career_page,
        "quality_report": quality_report,
        "available_models": ai_models,
        "selected_ai_model": db.get_setting("ai_model", "template"),
        "selected_track": db.get_setting("resume_track", "engineering"),
        "recommended_track": recommended_track,
        "company_applications": company_applications,
        "company_careers_url": company_careers_url,
        "excluded_skills": _excluded_skills,
        "scoring_llm_model": db.get_setting("scoring_llm_model", "keyword"),
        "back_url": back_url,
    })


def _load_pipeline_settings() -> dict:
    """Load pipeline gate settings from DB with defaults."""
    def _bool(key, default="true"):
        return db.get_setting(key, default) == "true"
    return {
        "llm_resolver":  _bool("pipeline_llm_resolver",  "true"),
        "gate_0a":       _bool("pipeline_gate_0a",        "true"),
        "gate_0b":       _bool("pipeline_gate_0b",        "true"),
        "gate_0c":       _bool("pipeline_gate_0c",        "true"),
        "gate_0d":       _bool("pipeline_gate_0d",        "true"),
        "gate_0e":       _bool("pipeline_gate_0e",        "true"),
        "gate_0f":       _bool("pipeline_gate_0f",        "true"),
        "gate_0g":       _bool("pipeline_gate_0g",        "true"),
        "gate_0h":       _bool("pipeline_gate_0h",        "true"),
        "gate_0i":       _bool("pipeline_gate_0i",        "true"),
        "gate_0j":       _bool("pipeline_gate_0j",        "true"),
        "gate_culture":  _bool("pipeline_gate_culture",   "true"),
        # Classification settings — keyword always runs; LLM is opt-in upgrade
        "llm_classifier_enabled": _bool("pipeline_llm_classifier_enabled", "false"),
        "classifier_model": db.get_setting("pipeline_classifier_model", "ollama:llama3.1:8b"),
    }


def _load_filter_settings() -> dict:
    """Load filter/threshold settings from DB with defaults."""
    import os as _os
    # RapidAPI key: read from .env file (not DB — it's a secret)
    _env_key = _os.getenv("RAPIDAPI_KEY", "") or db.get_setting("rapidapi_key", "")
    return {
        "salary_hard_floor":      int(db.get_setting("filter_salary_hard_floor",  "130000")),
        "salary_soft_floor":      int(db.get_setting("filter_salary_soft_floor",  "140000")),
        "min_llm_alignment":      int(db.get_setting("filter_min_llm_alignment",  "60")),
        "remote_mode":            db.get_setting("filter_remote_mode", "remote_preferred"),
        "aws_ethical":            db.get_setting("filter_aws_ethical", "true") == "true",
        "rapidapi_key":           _env_key,
        "glassdoor_api_enabled":  db.get_setting("glassdoor_api_enabled", "false") == "true",
    }


def _load_gate_lists() -> dict:
    """Load all gate keyword lists for the settings UI."""
    from src.screening.data.list_provider import (
        get_all_gate_lists, LIST_LABELS, LIST_DESCRIPTIONS, LIST_GATES,
    )
    all_lists = get_all_gate_lists()
    return {
        name: {
            "entries": items,
            "label": LIST_LABELS[name],
            "description": LIST_DESCRIPTIONS[name],
            "gate": LIST_GATES[name],
            "count": len(items),
        }
        for name, items in all_lists.items()
    }


def _load_scraping_settings() -> dict:
    """Load scraping default settings from DB with all-sources-enabled defaults."""
    # All known sources: JobSpy aggregators + niche custom scrapers
    ALL_SOURCES = [
        # JobSpy aggregators
        ("indeed",        "Indeed",        "Largest US job aggregator. High volume, reliable scraping.",                     "jobspy"),
        ("linkedin",      "LinkedIn",      "Professional network. Throttles unauthenticated access.",                       "jobspy"),
        ("glassdoor",     "Glassdoor",     "Reviews + jobs. Moderate volume, good salary data.",                            "jobspy"),
        ("google",        "Google Jobs",   "Google for Jobs aggregator. Pulls from many sources.",                          "jobspy"),
        ("zip_recruiter", "ZipRecruiter",  "US job board. Good for SMB and mid-market roles.",                             "jobspy"),
        # Niche custom scrapers (ATS boards + community)
        ("greenhouse",    "Greenhouse",    "Direct ATS boards from 50+ tech cos (Anthropic, Stripe, Cloudflare...).",       "niche"),
        ("ashby",         "Ashby",         "ATS boards from 50+ companies (Notion, Ramp, Figma, Linear...).",              "niche"),
        ("wellfound",     "Wellfound",     "AngelList successor. Startup-focused roles.",                                   "niche"),
        ("climatebase",   "Climatebase",   "Climate and sustainability tech jobs.",                                         "niche"),
        ("hackernews",    "Hacker News",   "Monthly 'Who is Hiring' threads. Community-sourced.",                           "niche"),
    ]
    sources = []
    for key, label, desc, engine in ALL_SOURCES:
        enabled = db.get_setting(f"scrape_site_{key}", "true") == "true"
        sources.append({"key": key, "label": label, "desc": desc, "engine": engine, "enabled": enabled})
    return {
        "sources": sources,
        "keywords":    db.get_setting("scrape_default_keywords",    "data engineer"),
        "location":    db.get_setting("scrape_default_location",    "United States"),
        "max_results": int(db.get_setting("scrape_default_max_results", "30")),
        "posted_days": int(db.get_setting("scrape_default_posted_days", "7")),
        "remote_only": db.get_setting("scrape_default_remote_only", "false") == "true",
    }


@app.get("/job-boards", response_class=HTMLResponse)
async def job_boards_page(request: Request):
    """Job boards and career sites overview."""
    import sqlite3 as _sqlite3
    source_counts = {}
    try:
        conn = _sqlite3.connect(db.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT source_site, COUNT(*) FROM jobs "
            "WHERE source_site IS NOT NULL GROUP BY source_site ORDER BY COUNT(*) DESC"
        )
        source_counts = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
    except Exception:
        pass
    return templates.TemplateResponse("job_boards.html", {
        "request": request,
        "source_counts": source_counts,
    })


# ── Streamlit Process Manager ────────────────────────────────────
_streamlit_procs: dict = {}  # key -> subprocess.Popen

# ── Excluded from open-source release (product feature) ──
# def _streamlit_status(key: str, port: int) -> str:
#     """Return 'running', 'stopped', or 'dead'."""
#     proc = _streamlit_procs.get(key)
#     if proc is None:
#         return "stopped"
#     if proc.poll() is not None:
#         # Process exited
#         del _streamlit_procs[key]
#         return "stopped"
#     # Double-check port is actually listening
#     import socket
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.settimeout(0.5)
#         if s.connect_ex(("127.0.0.1", port)) == 0:
#             return "running"
#     return "starting"


# ── Excluded from open-source release (product feature) ──
# @app.post("/api/streamlit/{action}/{key}")
# async def manage_streamlit(action: str, key: str):
#     """Start or stop a Streamlit dashboard."""
#     import socket
#
#     configs = {
#         "analytics": {"port": 8501, "script": "job_dashboard.py", "cwd": str(DASHBOARD_DIR.parent.parent)},
#         "monitor":   {"port": 8502, "script": "src/dashboard/real_time_dashboard.py", "cwd": str(DASHBOARD_DIR.parent.parent)},
#         "dbexplorer": {"port": 8503, "script": "src/dashboard/database_field_explorer.py", "cwd": str(DASHBOARD_DIR.parent.parent)},
#     }
#
#     if key not in configs:
#         return JSONResponse({"error": f"Unknown dashboard: {key}"}, status_code=400)
#
#     cfg = configs[key]
#     port = cfg["port"]
#
#     if action == "start":
#         # Already running?
#         if _streamlit_status(key, port) == "running":
#             return JSONResponse({"status": "running", "port": port})
#
#         # Kill stale proc if any
#         old = _streamlit_procs.pop(key, None)
#         if old and old.poll() is None:
#             old.terminate()
#
#         proc = subprocess.Popen(
#             [
#                 sys.executable, "-m", "streamlit", "run", cfg["script"],
#                 "--server.port", str(port),
#                 "--server.address", "0.0.0.0",
#                 "--server.headless", "true",
#                 "--browser.gatherUsageStats", "false",
#             ],
#             cwd=cfg["cwd"],
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
#         )
#         _streamlit_procs[key] = proc
#         return JSONResponse({"status": "starting", "port": port, "pid": proc.pid})
#
#     elif action == "stop":
#         proc = _streamlit_procs.pop(key, None)
#         if proc and proc.poll() is None:
#             proc.terminate()
#             try:
#                 proc.wait(timeout=5)
#             except subprocess.TimeoutExpired:
#                 proc.kill()
#         return JSONResponse({"status": "stopped"})
#
#     elif action == "status":
#         return JSONResponse({"status": _streamlit_status(key, port), "port": port})
#
#     return JSONResponse({"error": f"Unknown action: {action}"}, status_code=400)


# ── LinkedIn content performance helpers ──────────────────────────

# ── Excluded from open-source release (product feature) ──
# def _get_content_performance() -> dict:
#     """Read content performance data from job_search.db."""
#     intel_db = DASHBOARD_DIR.parent.parent / "data" / "job_search.db"
#     if not intel_db.exists():
#         return {}
#     try:
#         import sqlite3 as _sql
#         conn = _sql.connect(str(intel_db))
#         c = conn.cursor()
#
#         # Check tables exist
#         c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_profile_snapshots'")
#         if not c.fetchone():
#             conn.close()
#             return {}
#
#         # Latest snapshot
#         c.execute("SELECT * FROM daily_profile_snapshots ORDER BY snapshot_date DESC LIMIT 1")
#         row = c.fetchone()
#         if not row:
#             conn.close()
#             return {}
#         cols = [d[0] for d in c.description]
#         latest = dict(zip(cols, row))
#
#         # Previous snapshot for deltas
#         c.execute(
#             "SELECT * FROM daily_profile_snapshots WHERE snapshot_date < ? ORDER BY snapshot_date DESC LIMIT 1",
#             (latest["snapshot_date"],),
#         )
#         prev_row = c.fetchone()
#         prev = dict(zip(cols, prev_row)) if prev_row else None
#
#         # Snapshot history (last 30 days) for sparkline
#         c.execute(
#             "SELECT snapshot_date, profile_views, num_connections, follower_count, "
#             "total_impressions, total_likes, total_comments, total_shares "
#             "FROM daily_profile_snapshots ORDER BY snapshot_date DESC LIMIT 30"
#         )
#         history_rows = c.fetchall()
#         history_cols = [d[0] for d in c.description]
#         history = [dict(zip(history_cols, r)) for r in reversed(history_rows)]
#
#         # Per-post metrics for latest date
#         c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='post_metrics_history'")
#         posts = []
#         if c.fetchone():
#             c.execute(
#                 "SELECT activity_urn, text_preview, impressions, views, likes, comments, shares "
#                 "FROM post_metrics_history WHERE scraped_date = ? ORDER BY impressions DESC",
#                 (latest["snapshot_date"],),
#             )
#             for r in c.fetchall():
#                 posts.append({
#                     "urn": r[0], "text": r[1],
#                     "impressions": r[2] or 0, "views": r[3] or 0,
#                     "likes": r[4] or 0, "comments": r[5] or 0, "shares": r[6] or 0,
#                 })
#
#             # Per-post growth: compare with previous date for each post
#             if prev:
#                 c.execute(
#                     "SELECT activity_urn, impressions, likes, comments "
#                     "FROM post_metrics_history WHERE scraped_date = ?",
#                     (prev["snapshot_date"],),
#                 )
#                 prev_map = {r[0]: {"impressions": r[1], "likes": r[2], "comments": r[3]} for r in c.fetchall()}
#                 for p in posts:
#                     pm = prev_map.get(p["urn"])
#                     if pm:
#                         p["imp_delta"] = (p["impressions"] or 0) - (pm["impressions"] or 0)
#                         p["likes_delta"] = (p["likes"] or 0) - (pm["likes"] or 0)
#
#         conn.close()
#
#         return {
#             "latest": latest,
#             "prev": prev,
#             "history": history,
#             "posts": posts,
#         }
#     except Exception as e:
#         logger.debug("Content performance load error: %s", e)
#         return {}


# ── Excluded from open-source release (product feature) ──
# @app.get("/api/content-performance")
# async def api_content_performance():
#     """JSON API for content performance data."""
#     return _get_content_performance()


# ── Excluded from open-source release (product feature) ──
# @app.get("/linkedin", response_class=HTMLResponse)
# async def linkedin_page(request: Request):
#     """LinkedIn content performance analytics page."""
#     return templates.TemplateResponse("linkedin.html", {
#         "request": request,
#         "content_perf": _get_content_performance(),
#     })


# ── Excluded from open-source release (product feature) ──
# @app.get("/tools", response_class=HTMLResponse)
# async def tools_page(request: Request):
#     """Tools & dashboards overview page."""
#     api_usage = db.get_api_usage_summary(days=30)
#
#     # Get streamlit dashboard statuses
#     sl_status = {
#         "analytics": _streamlit_status("analytics", 8501),
#         "monitor": _streamlit_status("monitor", 8502),
#         "dbexplorer": _streamlit_status("dbexplorer", 8503),
#     }
#
#     # Pipeline run metrics
#     pipeline_stats = {"total_runs": 0}
#     recent_runs = []
#     try:
#         from src.dashboard.pipeline_metrics import get_run_stats, get_recent_runs
#         pipeline_stats = get_run_stats(db, days=30)
#         recent_runs = get_recent_runs(db, limit=10)
#     except Exception as e:
#         logger.debug("Pipeline metrics unavailable: %s", e)
#
#     return templates.TemplateResponse("tools.html", {
#         "request": request,
#         "rapidapi_key": os.getenv("RAPIDAPI_KEY", ""),
#         "serper_key": os.getenv("SERPER_API_KEY", ""),
#         "anthropic_key": os.getenv("ANTHROPIC_API_KEY", ""),
#         "api_usage": api_usage,
#         "sl_status": sl_status,
#         "pipeline_stats": pipeline_stats,
#         "recent_runs": recent_runs,
#     })


# ── Excluded from open-source release (product feature) ──
# @app.get("/analytics", response_class=HTMLResponse)
# async def analytics_page(request: Request):
#     """Comprehensive analytics dashboard."""
#     analytics = {}
#     try:
#         with db.get_connection() as conn:
#             # ── Application Funnel ────────────────────────────────
#             funnel = {}
#             for row in conn.execute(
#                 "SELECT response_type, COUNT(*) c FROM application_responses GROUP BY response_type"
#             ).fetchall():
#                 funnel[row[0]] = row[1]
#             analytics["funnel"] = funnel
#             analytics["total_applied"] = sum(v for k, v in funnel.items() if k != 'none')
#
#             # ── Response Rates by Source ──────────────────────────
#             source_rates = conn.execute("""
#                 SELECT j.source_site,
#                        COUNT(*) as total,
#                        SUM(CASE WHEN ar.response_type IN ('interview','phone_screen','offer') THEN 1 ELSE 0 END) as positive,
#                        SUM(CASE WHEN ar.response_type = 'rejected' THEN 1 ELSE 0 END) as rejected
#                 FROM application_responses ar
#                 JOIN jobs j ON j.id = ar.job_id
#                 WHERE ar.response_type != 'none'
#                 GROUP BY j.source_site
#                 ORDER BY total DESC
#             """).fetchall()
#             analytics["source_rates"] = [dict(r) for r in source_rates]
#
#             # ── Response Rate by Score Range ─────────────────────
#             score_rates = conn.execute("""
#                 SELECT
#                     CASE
#                         WHEN j.alignment_score >= 80 THEN '80-100%'
#                         WHEN j.alignment_score >= 60 THEN '60-79%'
#                         WHEN j.alignment_score >= 40 THEN '40-59%'
#                         ELSE '0-39%'
#                     END as score_range,
#                     COUNT(*) as total,
#                     SUM(CASE WHEN ar.response_type IN ('interview','phone_screen','offer') THEN 1 ELSE 0 END) as positive
#                 FROM application_responses ar
#                 JOIN jobs j ON j.id = ar.job_id
#                 WHERE ar.response_type IN ('applied','rejected','interview','phone_screen','offer')
#                   AND j.alignment_score IS NOT NULL
#                 GROUP BY score_range
#                 ORDER BY score_range
#             """).fetchall()
#             analytics["score_rates"] = [dict(r) for r in score_rates]
#
#             # ── Top Skill Gaps (most common across all scored jobs) ──
#             import json as _json
#             gap_counter = {}
#             for row in conn.execute(
#                 "SELECT alignment_details FROM jobs WHERE alignment_details IS NOT NULL"
#             ).fetchall():
#                 try:
#                     details = _json.loads(row[0])
#                     for cat in details.get("categories", []):
#                         for gap in cat.get("gaps", []):
#                             gap_counter[gap] = gap_counter.get(gap, 0) + 1
#                 except Exception:
#                     pass
#             top_gaps = sorted(gap_counter.items(), key=lambda x: -x[1])[:20]
#             analytics["top_gaps"] = top_gaps
#
#             # ── Score Distribution ────────────────────────────────
#             score_dist = conn.execute("""
#                 SELECT
#                     CASE
#                         WHEN alignment_score >= 90 THEN '90-100'
#                         WHEN alignment_score >= 80 THEN '80-89'
#                         WHEN alignment_score >= 70 THEN '70-79'
#                         WHEN alignment_score >= 60 THEN '60-69'
#                         WHEN alignment_score >= 50 THEN '50-59'
#                         WHEN alignment_score >= 40 THEN '40-49'
#                         ELSE '0-39'
#                     END as bucket,
#                     COUNT(*) as count
#                 FROM jobs WHERE alignment_score IS NOT NULL
#                 GROUP BY bucket ORDER BY bucket
#             """).fetchall()
#             analytics["score_dist"] = [dict(r) for r in score_dist]
#
#             # ── Jobs by Source ────────────────────────────────────
#             source_counts = conn.execute("""
#                 SELECT source_site, COUNT(*) c FROM jobs
#                 WHERE is_active = 1 GROUP BY source_site ORDER BY c DESC
#             """).fetchall()
#             analytics["source_counts"] = [dict(r) for r in source_counts]
#
#             # ── Jobs by Category ──────────────────────────────────
#             category_counts = conn.execute("""
#                 SELECT COALESCE(job_category, 'unclassified') as cat, COUNT(*) c
#                 FROM jobs WHERE is_active = 1 GROUP BY cat ORDER BY c DESC
#             """).fetchall()
#             analytics["category_counts"] = [dict(r) for r in category_counts]
#
#             # ── Application Timeline (by week) ────────────────────
#             app_timeline = conn.execute("""
#                 SELECT strftime('%Y-W%W', responded_at) as week,
#                        COUNT(*) as count,
#                        response_type
#                 FROM application_responses
#                 WHERE response_type != 'none' AND responded_at IS NOT NULL
#                 GROUP BY week, response_type
#                 ORDER BY week
#             """).fetchall()
#             analytics["app_timeline"] = [dict(r) for r in app_timeline]
#
#             # ── Ghost Job Stats ───────────────────────────────────
#             total_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1").fetchone()[0]
#             old_jobs = conn.execute("""
#                 SELECT COUNT(*) FROM jobs
#                 WHERE is_active = 1 AND posted_date IS NOT NULL
#                   AND julianday('now') - julianday(posted_date) > 30
#             """).fetchone()[0]
#             analytics["ghost_stats"] = {
#                 "total": total_jobs,
#                 "stale_30d": old_jobs,
#                 "stale_pct": round(old_jobs / max(total_jobs, 1) * 100, 1),
#             }
#
#             # ── Company Stats ─────────────────────────────────────
#             companies_with_ratings = conn.execute("""
#                 SELECT COUNT(DISTINCT company) FROM jobs
#                 WHERE company_glassdoor_json IS NOT NULL
#             """).fetchone()[0]
#             avg_rating = conn.execute("""
#                 SELECT AVG(CAST(json_extract(company_glassdoor_json, '$.overall_rating') AS REAL))
#                 FROM jobs WHERE company_glassdoor_json IS NOT NULL
#             """).fetchone()[0]
#             analytics["company_stats"] = {
#                 "with_ratings": companies_with_ratings,
#                 "avg_rating": round(avg_rating, 2) if avg_rating else None,
#             }
#
#             # ── Pipeline Performance (last 30 days) ──────────────
#             pipeline_perf = conn.execute("""
#                 SELECT run_type,
#                        COUNT(*) as runs,
#                        ROUND(AVG(elapsed_seconds), 1) as avg_time,
#                        ROUND(MAX(elapsed_seconds), 1) as max_time
#                 FROM pipeline_runs
#                 WHERE started_at >= datetime('now', '-30 days')
#                 GROUP BY run_type
#             """).fetchall()
#             analytics["pipeline_perf"] = [dict(r) for r in pipeline_perf]
#
#             # ── Salary Stats ──────────────────────────────────────
#             salary_stats = conn.execute("""
#                 SELECT
#                     COUNT(*) as with_salary,
#                     ROUND(AVG(salary_min)) as avg_min,
#                     ROUND(AVG(salary_max)) as avg_max,
#                     ROUND(MIN(salary_min)) as floor,
#                     ROUND(MAX(salary_max)) as ceiling
#                 FROM jobs WHERE salary_min > 0 AND is_active = 1
#             """).fetchone()
#             analytics["salary_stats"] = dict(salary_stats) if salary_stats else {}
#
#     except Exception as e:
#         logger.error("Analytics query failed: %s", e, exc_info=True)
#
#     return templates.TemplateResponse("analytics.html", {
#         "request": request,
#         "analytics": analytics,
#     })


@app.get("/api/pipeline-runs")
async def api_pipeline_runs(limit: int = 20, run_type: str = None):
    """JSON API for pipeline run history."""
    try:
        from src.dashboard.pipeline_metrics import get_recent_runs, get_run_stats
        runs = get_recent_runs(db, limit=limit, run_type=run_type)
        stats = get_run_stats(db, days=30)
        return {"runs": runs, "stats": stats}
    except Exception as e:
        return {"runs": [], "stats": {"total_runs": 0}, "error": str(e)}


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page."""
    resume_text = db.get_setting("resume_text", "")
    auto_generate = db.get_setting("auto_generate") == "true"
    ai_provider = db.get_setting("ai_provider", "template")
    ai_model = db.get_setting("ai_model", "template")
    resume_track = db.get_setting("resume_track", "engineering")

    # Get available models
    available = get_available_models()
    ai_models = [
        {"provider": m.provider.value, "model_name": m.model_name,
         "display_name": m.display_name, "speed": m.speed_rating}
        for m in available
    ]

    # Provider list
    providers = []
    if any(m.provider == AIProvider.OLLAMA for m in available):
        providers.append({"value": "ollama", "label": "Ollama (Local)"})
    if any(m.provider == AIProvider.CLAUDE for m in available):
        providers.append({"value": "claude", "label": "Claude (Anthropic)"})

    # Track-specific resumes
    resume_engineering = db.get_setting("resume_text_engineering", "")
    resume_analyst = db.get_setting("resume_text_analyst", "")
    resume_bsa = db.get_setting("resume_text_bsa", "")

    # Scoring engine keywords
    from src.dashboard.scoring import (
        TECH_KEYWORDS, JD_TECH_KEYWORDS, SOFT_SKILL_SYNONYMS,
        DOMAIN_KEYWORDS, WEIGHT_TEMPLATES,
    )

    # User-added skills and user-excluded skills
    user_added_skills = sorted(json.loads(db.get_setting("user_added_skills", "[]")))
    user_removed_skills = sorted(json.loads(db.get_setting("user_removed_skills", "[]")))

    # Scoring LLM model setting
    scoring_llm_model = db.get_setting("scoring_llm_model", "keyword")

    # Get Ollama models for scoring dropdown
    scoring_ollama_models = []
    try:
        import urllib.request as _ur
        with _ur.urlopen("http://localhost:11434/api/tags", timeout=3) as resp:
            _data = json.loads(resp.read())
            scoring_ollama_models = [m["name"] for m in _data.get("models", [])]
    except Exception:
        pass

    # Check if Claude is available for scoring
    scoring_claude_models = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        scoring_claude_models = [
            {"value": "claude:claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku (fast, ~$0.001/job)"},
            {"value": "claude:claude-sonnet-4-20250514", "label": "Claude Sonnet 4 (best, ~$0.005/job)"},
        ]

    # Server uptime
    uptime = datetime.now() - _server_started_at
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        uptime_str = f"Up {hours}h {minutes}m"
    elif minutes > 0:
        uptime_str = f"Up {minutes}m {seconds}s"
    else:
        uptime_str = f"Up {seconds}s"

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "server_uptime": uptime_str,
        "resume_text": resume_text,
        "resume_engineering": resume_engineering,
        "resume_analyst": resume_analyst,
        "resume_bsa": resume_bsa,
        "auto_generate": auto_generate,
        "ai_provider": ai_provider,
        "ai_model": ai_model,
        "resume_track": resume_track,
        "ai_models": ai_models,
        "ai_providers": providers,
        "pipeline": _load_pipeline_settings(),
        "filters":  _load_filter_settings(),
        "gen_thresholds": _load_generation_thresholds(),
        # Scoring engine
        "tech_keywords": TECH_KEYWORDS,
        "jd_tech_keywords": JD_TECH_KEYWORDS,
        "soft_skill_synonyms": SOFT_SKILL_SYNONYMS,
        "domain_keywords": DOMAIN_KEYWORDS,
        "weight_templates": WEIGHT_TEMPLATES,
        "user_added_skills": user_added_skills,
        "user_removed_skills": user_removed_skills,
        "scoring_llm_model": scoring_llm_model,
        "scoring_ollama_models": scoring_ollama_models,
        "scoring_claude_models": scoring_claude_models,
        "scraping": _load_scraping_settings(),
        # Gate lists for editable screening dictionaries
        "gate_lists": _load_gate_lists(),
    })


# ── Routes: HTMX Actions ───────────────────────────────────────────

@app.post("/api/settings/resume", response_class=HTMLResponse)
async def save_resume(
    request: Request,
    resume_text: str = Form(...),
    track: str = Form(""),
):
    """Save resume text (generic or track-specific) and update scorer."""
    if track and track in ("engineering", "analyst", "bsa"):
        key = f"resume_text_{track}"
        db.set_setting(key, resume_text)
        label = track.upper()
        return HTMLResponse(
            f'<div class="text-green-600 font-medium" id="save-status">'
            f'{label} track resume saved ({len(resume_text):,} chars).</div>'
        )
    else:
        db.set_setting("resume_text", resume_text)
        scorer.set_resume(resume_text)
        return HTMLResponse(
            '<div class="text-green-600 font-medium" id="save-status">'
            'Resume saved successfully. Scores will update on next scoring run.</div>'
        )


@app.post("/api/settings/auto-generate", response_class=HTMLResponse)
async def toggle_auto_generate(request: Request):
    """Toggle auto-generate setting."""
    current = db.get_setting("auto_generate") == "true"
    new_val = "false" if current else "true"
    db.set_setting("auto_generate", new_val)
    checked = "checked" if new_val == "true" else ""
    label = "ON" if new_val == "true" else "OFF"
    color = "text-green-600" if new_val == "true" else "text-gray-500"
    return HTMLResponse(
        f'<span class="{color} font-semibold text-sm">{label}</span>'
    )


@app.post("/api/settings/ai-model", response_class=HTMLResponse)
async def save_ai_settings(
    request: Request,
    ai_provider: str = Form("template"),
    ai_model: str = Form("template"),
    resume_track: str = Form("engineering"),
):
    """Save AI model and resume track settings."""
    db.set_setting("ai_provider", ai_provider)
    db.set_setting("ai_model", ai_model)
    db.set_setting("resume_track", resume_track)
    model_label = get_model_display_name(ai_provider, ai_model) if ai_model != "template" else "Template (No AI)"
    return HTMLResponse(
        f'<div class="text-green-600 text-sm font-medium">'
        f'Saved: {model_label} / {resume_track.title()} track</div>'
    )


@app.post("/api/settings/generation-thresholds", response_class=HTMLResponse)
async def save_generation_thresholds(request: Request):
    """Save constrained pipeline threshold settings."""
    form = await request.form()
    try:
        db.set_setting("gen_min_score_to_generate",
                        str(max(0, min(100, int(form.get("min_score_to_generate", "65"))))))
        db.set_setting("gen_score_delta_floor_pct",
                        str(max(50, min(100, int(form.get("score_delta_floor_pct", "90"))))))
        db.set_setting("gen_achievement_top_n",
                        str(max(1, min(10, int(form.get("achievement_top_n", "4"))))))
        db.set_setting("gen_achievement_coverage_min",
                        str(max(0, min(100, int(form.get("achievement_coverage_min", "65"))))))
        db.set_setting("gen_tool_overlap_boost",
                        str(max(0, min(20, int(form.get("tool_overlap_boost", "5"))))))
        db.set_setting("gen_request_timeout",
                        str(max(30, min(600, int(form.get("request_timeout", "180"))))))
        db.set_setting("gen_max_tokens",
                        str(max(1024, min(8192, int(form.get("max_tokens", "4096"))))))
        return HTMLResponse(
            '<span class="text-green-600 font-medium text-sm">Thresholds saved.</span>'
        )
    except Exception as e:
        return HTMLResponse(
            f'<span class="text-red-600 font-medium text-sm">Error: {e}</span>'
        )


def _load_generation_thresholds() -> dict:
    """Load generation pipeline thresholds from DB with defaults."""
    return {
        "min_score_to_generate": int(db.get_setting("gen_min_score_to_generate", "65")),
        "score_delta_floor_pct": int(db.get_setting("gen_score_delta_floor_pct", "90")),
        "achievement_top_n": int(db.get_setting("gen_achievement_top_n", "4")),
        "achievement_coverage_min": int(db.get_setting("gen_achievement_coverage_min", "65")),
        "tool_overlap_boost": int(db.get_setting("gen_tool_overlap_boost", "5")),
        "request_timeout": int(db.get_setting("gen_request_timeout", "180")),
        "max_tokens": int(db.get_setting("gen_max_tokens", "4096")),
    }


@app.post("/api/settings/scoring-model", response_class=HTMLResponse)
async def save_scoring_model(
    request: Request,
    scoring_llm_model: str = Form("keyword"),
):
    """Save the LLM model used for skill extraction during scoring."""
    db.set_setting("scoring_llm_model", scoring_llm_model)
    if scoring_llm_model == "keyword":
        label = "Keyword-only (no LLM)"
    else:
        label = scoring_llm_model
    return HTMLResponse(
        f'<div class="text-green-600 text-sm font-medium">'
        f'Scoring model saved: {label}</div>'
    )


@app.post("/api/settings/pipeline", response_class=HTMLResponse)
async def save_pipeline_settings(request: Request):
    """Save pipeline gate toggles and LLM resolver flag."""
    form = await request.form()
    def _get_bool(key: str, default: str = "false") -> str:
        return "true" if form.get(key, default) == "true" else "false"

    db.set_setting("pipeline_llm_resolver", _get_bool("llm_resolver"))
    for gate in ("gate_0a", "gate_0b", "gate_0c", "gate_0d", "gate_0e",
                 "gate_0f", "gate_0g", "gate_0h", "gate_0i", "gate_0j", "gate_culture"):
        db.set_setting(f"pipeline_{gate}", _get_bool(gate, "true"))

    # Classification settings — keyword always runs; LLM is opt-in upgrade
    db.set_setting("pipeline_llm_classifier_enabled", _get_bool("llm_classifier_enabled", "false"))
    classifier_model = form.get("classifier_model", "ollama:llama3.1:8b")
    db.set_setting("pipeline_classifier_model", classifier_model)

    enabled_gates = [g for g in ("gate_0a", "gate_0b", "gate_0c", "gate_0d", "gate_0e",
                                  "gate_0f", "gate_0g", "gate_0h", "gate_0i", "gate_0j",
                                  "gate_culture")
                     if _get_bool(g, "true") == "true"]
    resolver_label = " + LLM resolver" if _get_bool("llm_resolver") == "true" else ""
    llm_classifier_label = " + LLM classifier" if _get_bool("llm_classifier_enabled", "false") == "true" else ""
    return HTMLResponse(
        f'<span class="text-green-600 font-medium">'
        f'Saved — {len(enabled_gates)}/11 gates active{resolver_label}{llm_classifier_label}</span>'
    )


@app.post("/api/settings/scraping", response_class=HTMLResponse)
async def save_scraping_settings(request: Request):
    """Save scraping source toggles and default search parameters."""
    form = await request.form()

    # Save source toggles
    all_sources = [
        "indeed", "linkedin", "glassdoor", "google", "zip_recruiter",
        "greenhouse", "ashby", "wellfound", "climatebase", "hackernews",
    ]
    enabled_sources = []
    for src in all_sources:
        val = "true" if form.get(f"site_{src}", "false") == "true" else "false"
        db.set_setting(f"scrape_site_{src}", val)
        if val == "true":
            enabled_sources.append(src)

    # Save default parameters
    db.set_setting("scrape_default_keywords", form.get("default_keywords", "data engineer").strip())
    db.set_setting("scrape_default_location", form.get("default_location", "United States").strip())
    db.set_setting("scrape_default_max_results", form.get("default_max_results", "30"))
    db.set_setting("scrape_default_posted_days", form.get("default_posted_days", "7"))
    db.set_setting("scrape_default_remote_only",
                   "true" if form.get("default_remote_only") == "true" else "false")

    return HTMLResponse(
        f'<span class="text-green-600 font-medium">'
        f'Saved — {len(enabled_sources)}/{len(all_sources)} sources enabled '
        f'({", ".join(enabled_sources)})</span>'
    )


@app.post("/api/settings/filters", response_class=HTMLResponse)
async def save_filter_settings(request: Request):
    """Save filter/threshold settings."""
    form = await request.form()
    try:
        hard = max(0, int(form.get("salary_hard_floor", "130000")))
        soft = max(0, int(form.get("salary_soft_floor", "140000")))
        align = max(0, min(100, int(form.get("min_llm_alignment", "60"))))
        remote = form.get("remote_mode", "remote_preferred")
        aws = "true" if form.get("aws_ethical", "false") == "true" else "false"

        db.set_setting("filter_salary_hard_floor", str(hard))
        db.set_setting("filter_salary_soft_floor", str(soft))
        db.set_setting("filter_min_llm_alignment", str(align))
        db.set_setting("filter_remote_mode", remote)
        db.set_setting("filter_aws_ethical", aws)

        # Glassdoor / RapidAPI settings
        rapidapi_key = (form.get("rapidapi_key") or "").strip()
        gd_enabled = "true" if form.get("glassdoor_api_enabled", "false") == "true" else "false"
        db.set_setting("glassdoor_api_enabled", gd_enabled)

        # Persist API key to .env file (not DB — it's a secret)
        if rapidapi_key:
            _update_env_key("RAPIDAPI_KEY", rapidapi_key)
            _update_env_key("GLASSDOOR_API_ENABLED", gd_enabled)
            import os as _os
            _os.environ["RAPIDAPI_KEY"] = rapidapi_key
            _os.environ["GLASSDOOR_API_ENABLED"] = gd_enabled
            # Reset client singleton so it picks up the new key
            try:
                import src.enrichment.glassdoor_client as _gdc
                _gdc._client = None
            except ImportError:
                pass

        gd_label = " + Glassdoor API enabled" if gd_enabled == "true" and rapidapi_key else ""
        return HTMLResponse(
            f'<span class="text-green-600 font-medium">'
            f'Saved — hard floor ${hard:,} / soft floor ${soft:,} / '
            f'LLM min {align} / {remote}{gd_label}</span>'
        )
    except (ValueError, TypeError) as e:
        return HTMLResponse(
            f'<span class="text-red-600 font-medium">Error saving: {e}</span>'
        )


# ── Scoring Engine Settings ────────────────────────────────────────

def _update_scoring_py(section: str, new_value: str) -> None:
    """Rewrite a keyword set in scoring.py by regenerating the block."""
    import re as _re
    scoring_path = Path(__file__).parent / "scoring.py"
    content = scoring_path.read_text(encoding="utf-8")

    if section == "TECH_KEYWORDS":
        # Replace the TECH_KEYWORDS block
        pattern = r'(TECH_KEYWORDS\s*=\s*\{)[^}]*(})'
        keywords = [k.strip() for k in new_value.split(",") if k.strip()]
        formatted = _format_keyword_set(keywords)
        content = _re.sub(pattern, f'TECH_KEYWORDS = {{\n{formatted}\n}}', content, count=1, flags=_re.DOTALL)

    elif section == "JD_TECH_KEYWORDS":
        # Replace JD_TECH_KEYWORDS — it's defined as TECH_KEYWORDS | {...}
        # We'll rewrite it to a standalone set for simplicity
        pattern = r'(JD_TECH_KEYWORDS\s*=\s*)TECH_KEYWORDS\s*\|\s*\{[^}]*\}'
        keywords = [k.strip() for k in new_value.split(",") if k.strip()]
        formatted = _format_keyword_set(keywords)
        content = _re.sub(pattern, f'JD_TECH_KEYWORDS = {{\n{formatted}\n}}', content, count=1, flags=_re.DOTALL)

    elif section == "DOMAIN_KEYWORDS":
        pattern = r'(DOMAIN_KEYWORDS\s*=\s*\{)[^}]*(})'
        keywords = [k.strip() for k in new_value.split(",") if k.strip()]
        formatted = _format_keyword_set(keywords)
        content = _re.sub(pattern, f'DOMAIN_KEYWORDS = {{\n{formatted}\n}}', content, count=1, flags=_re.DOTALL)

    scoring_path.write_text(content, encoding="utf-8")
    # Reload the module so changes take effect immediately
    _reload_scoring_module()


def _format_keyword_set(keywords: list) -> str:
    """Format keywords into a nicely indented Python set literal body."""
    sorted_kws = sorted(set(keywords))
    lines = []
    line = "    "
    for kw in sorted_kws:
        entry = f'"{kw}", '
        if len(line) + len(entry) > 95:
            lines.append(line.rstrip())
            line = "    "
        line += entry
    if line.strip():
        lines.append(line.rstrip())
    return "\n".join(lines)


def _reload_scoring_module():
    """Reload scoring module so updated keywords take effect without server restart."""
    import importlib
    import src.dashboard.scoring as scoring_mod
    importlib.reload(scoring_mod)
    # Update the global scorer if it exists
    global _scorer
    if '_scorer' in dir():
        try:
            resume_text = db.get_setting("resume_text", "")
            _scorer = scoring_mod.AlignmentScorer(resume_text)
        except Exception:
            pass


@app.post("/api/settings/scoring/tech-keywords", response_class=HTMLResponse)
async def save_tech_keywords(request: Request):
    """Save user's verified skills (TECH_KEYWORDS)."""
    form = await request.form()
    keywords_raw = form.get("keywords", "")
    try:
        _update_scoring_py("TECH_KEYWORDS", keywords_raw)
        count = len([k for k in keywords_raw.split(",") if k.strip()])
        return HTMLResponse(
            f'<span class="text-green-600 font-medium">✅ Saved {count} skills to scoring engine. '
            f'Use Re-score All on Dashboard to apply.</span>'
        )
    except Exception as e:
        logger.exception("Failed to save tech keywords")
        return HTMLResponse(f'<span class="text-red-600 font-medium">Error: {e}</span>')


@app.post("/api/settings/scoring/jd-keywords", response_class=HTMLResponse)
async def save_jd_keywords(request: Request):
    """Save job description vocabulary (JD_TECH_KEYWORDS)."""
    form = await request.form()
    keywords_raw = form.get("keywords", "")
    try:
        _update_scoring_py("JD_TECH_KEYWORDS", keywords_raw)
        count = len([k for k in keywords_raw.split(",") if k.strip()])
        return HTMLResponse(
            f'<span class="text-green-600 font-medium">✅ Saved {count} JD keywords to scoring engine. '
            f'Use Re-score All on Dashboard to apply.</span>'
        )
    except Exception as e:
        logger.exception("Failed to save JD keywords")
        return HTMLResponse(f'<span class="text-red-600 font-medium">Error: {e}</span>')


@app.post("/api/settings/scoring/domain-keywords", response_class=HTMLResponse)
async def save_domain_keywords(request: Request):
    """Save domain expertise keywords (DOMAIN_KEYWORDS)."""
    form = await request.form()
    keywords_raw = form.get("keywords", "")
    try:
        _update_scoring_py("DOMAIN_KEYWORDS", keywords_raw)
        count = len([k for k in keywords_raw.split(",") if k.strip()])
        return HTMLResponse(
            f'<span class="text-green-600 font-medium">✅ Saved {count} domain keywords to scoring engine. '
            f'Use Re-score All on Dashboard to apply.</span>'
        )
    except Exception as e:
        logger.exception("Failed to save domain keywords")
        return HTMLResponse(f'<span class="text-red-600 font-medium">Error: {e}</span>')


@app.post("/api/settings/scoring/soft-skills", response_class=HTMLResponse)
async def save_soft_skills(request: Request):
    """Save soft skills with synonyms."""
    form = await request.form()
    try:
        import re as _re
        scoring_path = Path(__file__).parent / "scoring.py"
        content = scoring_path.read_text(encoding="utf-8")

        # Build new synonyms dict from form
        new_synonyms = {}
        for key, value in form.items():
            if key.startswith("soft_"):
                skill_name = key[5:]  # remove 'soft_' prefix
                synonyms = [s.strip() for s in value.split(",") if s.strip()]
                if synonyms:
                    new_synonyms[skill_name] = synonyms

        # Format the new SOFT_SKILL_SYNONYMS block
        lines = ['SOFT_SKILL_SYNONYMS: Dict[str, List[str]] = {']
        for skill in sorted(new_synonyms.keys()):
            syns = new_synonyms[skill]
            syn_strs = ', '.join(f'"{s}"' for s in syns)
            padding = max(1, 26 - len(skill))
            lines.append(f'    "{skill}":{" " * padding}[{syn_strs}],')
        lines.append('}')
        new_block = "\n".join(lines)

        # Replace existing block
        pattern = r'SOFT_SKILL_SYNONYMS:\s*Dict\[str,\s*List\[str\]\]\s*=\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}'
        content = _re.sub(pattern, new_block, content, count=1, flags=_re.DOTALL)

        scoring_path.write_text(content, encoding="utf-8")
        _reload_scoring_module()

        return HTMLResponse(
            f'<span class="text-green-600 font-medium">✅ Saved {len(new_synonyms)} soft skills. '
            f'Use Re-score All on Dashboard to apply.</span>'
        )
    except Exception as e:
        logger.exception("Failed to save soft skills")
        return HTMLResponse(f'<span class="text-red-600 font-medium">Error: {e}</span>')


@app.post("/api/settings/scoring/weights", response_class=HTMLResponse)
async def save_weights(request: Request):
    """Save scoring weight templates."""
    form = await request.form()
    try:
        import re as _re
        scoring_path = Path(__file__).parent / "scoring.py"
        content = scoring_path.read_text(encoding="utf-8")

        # Parse form values into weight templates
        templates = {}
        for key, value in form.items():
            parts = key.split("_", 1)
            if len(parts) == 2:
                template_name = parts[0]
                category = parts[1]
                if template_name not in templates:
                    templates[template_name] = {}
                templates[template_name][category] = round(int(value) / 100, 2)

        # Format the new WEIGHT_TEMPLATES block
        lines = ['WEIGHT_TEMPLATES = {']
        for tname in sorted(templates.keys()):
            lines.append(f'    "{tname}": {{')
            for cat in sorted(templates[tname].keys()):
                lines.append(f'        "{cat}": {templates[tname][cat]},')
            lines.append('    },')
        lines.append('}')
        new_block = "\n".join(lines)

        pattern = r'WEIGHT_TEMPLATES\s*=\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}'
        content = _re.sub(pattern, new_block, content, count=1, flags=_re.DOTALL)

        scoring_path.write_text(content, encoding="utf-8")
        _reload_scoring_module()

        return HTMLResponse(
            '<span class="text-green-600 font-medium">✅ Weights saved. '
            'Use Re-score All on Dashboard to apply.</span>'
        )
    except Exception as e:
        logger.exception("Failed to save weights")
        return HTMLResponse(f'<span class="text-red-600 font-medium">Error: {e}</span>')


@app.post("/api/settings/gate-lists/{list_name}", response_class=HTMLResponse)
async def save_gate_list_endpoint(list_name: str, request: Request):
    """Save a gate keyword list from the settings UI."""
    from src.screening.data.list_provider import save_gate_list, VALID_LISTS
    if list_name not in VALID_LISTS:
        return HTMLResponse('<span class="text-red-600 font-medium">Invalid list name.</span>', 400)
    form = await request.form()
    keywords_raw = form.get("keywords", "")
    items = [k.strip().lower() for k in keywords_raw.split(",") if k.strip()]
    try:
        save_gate_list(list_name, items)
        return HTMLResponse(
            f'<span class="text-green-600 font-medium">Saved {len(items)} items. '
            f'Changes take effect on next screening run.</span>'
        )
    except Exception as e:
        logger.exception("Failed to save gate list %s", list_name)
        return HTMLResponse(f'<span class="text-red-600 font-medium">Error: {e}</span>')


@app.post("/api/settings/gate-lists/{list_name}/reset", response_class=HTMLResponse)
async def reset_gate_list_endpoint(list_name: str):
    """Reset a gate keyword list to its hardcoded defaults."""
    from src.screening.data.list_provider import reset_gate_list, VALID_LISTS
    from src.screening.data import known_lists
    if list_name not in VALID_LISTS:
        return HTMLResponse('<span class="text-red-600 font-medium">Invalid list name.</span>', 400)
    try:
        reset_gate_list(list_name)
        default_count = len(getattr(known_lists, list_name))
        return HTMLResponse(
            f'<span class="text-blue-600 font-medium">Reset to {default_count} defaults. '
            f'Reload page to see updated list.</span>'
        )
    except Exception as e:
        logger.exception("Failed to reset gate list %s", list_name)
        return HTMLResponse(f'<span class="text-red-600 font-medium">Error: {e}</span>')


def _update_env_key(key: str, value: str) -> None:
    """Update or add a key=value line in the .env file."""
    import re as _re
    env_path = _ENV_PATH
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = _re.compile(rf"^#?\s*{_re.escape(key)}\s*=.*", _re.MULTILINE)
        new_line = f"{key}={value}"
        if pattern.search(content):
            content = pattern.sub(new_line, content, count=1)
        else:
            content = content.rstrip("\n") + f"\n{new_line}\n"
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as _e:
        logger.warning("Could not update .env file: %s", _e)


@app.post("/api/response/{job_id}", response_class=HTMLResponse)
async def record_response(
    request: Request,
    job_id: int,
    response_type: str = Form("none"),
    notes: str = Form(""),
):
    """Record a response for a job application."""
    global _status_version
    try:
        db.record_response(job_id, response_type, notes)
        _status_version += 1

        # F5 — record outcome for lessons learned database
        try:
            from src.tracking.outcomes_tracker import OutcomesTracker, ApplicationOutcome
            tracker = OutcomesTracker()
            job = db.get_job(job_id)
            tracker.log_outcome(ApplicationOutcome(
                platform="dashboard",
                outcome=response_type,
                job_id=job_id,
                notes=(job.get("company", "") + " | " + job.get("title", "")) if job else "",
            ))
        except Exception as _e:
            logger.debug("Outcomes tracker (non-critical): %s", _e)

        return HTMLResponse(
            f'<div class="text-green-600 text-xs">Response updated: {response_type.replace("_", " ").title()}</div>'
        )
    except Exception as e:
        return HTMLResponse(f'<div class="text-red-600 text-xs">Error: {e}</div>')


@app.post("/api/score-jobs", response_class=HTMLResponse)
async def score_jobs(request: Request):
    """Score all unscored jobs against resume — runs in background with progress."""
    resume = db.get_setting("resume_text")
    if not resume:
        return HTMLResponse(
            '<div class="text-red-600">No resume configured. Go to Settings first.</div>'
        )

    task_id = "score-jobs"
    if _get_task_progress(task_id).get("stage") not in (None, "done", "error", ""):
        return HTMLResponse(
            '<div class="text-yellow-600 text-sm">Scoring already in progress...</div>'
        )

    def run_scoring():
        _get_cancel_event(task_id).clear()
        # Start pipeline metrics tracking
        run_tracker = None
        try:
            from src.dashboard.pipeline_metrics import PipelineRunTracker
            run_tracker = PipelineRunTracker(db, run_type="score")
            run_tracker.start()
        except Exception:
            pass

        try:
            import time as _time
            _t0 = _time.time()
            def _elapsed():
                return _time.time() - _t0

            _set_task_progress(task_id, "init", 5, "Loading resume and finding unscored jobs...")
            _scorer = AlignmentScorer()
            _scorer.set_resume(resume)
            unscored = db.get_unscored_jobs(days=30, limit=500)
            total = len(unscored)
            if total == 0:
                _set_task_progress(task_id, "done", 100, "All jobs already scored!")
                if run_tracker:
                    run_tracker.finish(summary={"total": 0, "scored": 0})
                return

            if run_tracker:
                run_tracker.record_step("scoring", items_processed=total)

            # ── Phase 1: Fast keyword scoring ─────────────────────────
            _set_task_progress(task_id, "scoring", 10,
                               f"[{_elapsed():.0f}s] Phase 1: Keyword scoring {total} jobs...")
            keyword_results = []
            descriptions = []
            titles = []
            valid_jobs = []
            for i, job in enumerate(unscored):
                _check_task_cancel(task_id)
                desc = job.get("description", "")
                if not desc or len(desc) < 50:
                    continue
                title = job.get("title", "")
                try:
                    result = _scorer.score_keyword_only(desc, title)
                    keyword_results.append(result)
                    descriptions.append(desc)
                    titles.append(title)
                    valid_jobs.append(job)
                except Exception as e:
                    logger.warning(f"Keyword scoring failed for job {job['id']}: {e}")

                pct = 10 + int(40 * (i + 1) / total)
                if (i + 1) % 10 == 0 or i == total - 1:
                    _set_task_progress(task_id, "scoring", pct,
                                       f"[{_elapsed():.0f}s] Keyword scoring {i+1}/{total}...")

            # ── Phase 2: Batch semantic embedding ─────────────────────
            _check_task_cancel(task_id)
            if valid_jobs:
                _set_task_progress(task_id, "scoring", 55,
                                   f"[{_elapsed():.0f}s] Phase 2: Batch semantic embedding {len(valid_jobs)} jobs...")
                try:
                    sem_applied = _scorer.apply_batch_semantic(
                        keyword_results, descriptions, titles, keyword_threshold=25.0
                    )
                    _set_task_progress(task_id, "scoring", 75,
                                       f"[{_elapsed():.0f}s] Semantic scores: {sem_applied}/{len(valid_jobs)} jobs")
                except Exception as e:
                    logger.warning(f"Batch semantic scoring failed (non-critical): {e}")

            # ── Phase 3: Save results to DB ──────────────────────────
            scored_count = 0
            for i, (job, result) in enumerate(zip(valid_jobs, keyword_results)):
                _check_task_cancel(task_id)
                try:
                    db.update_alignment_score(job["id"], result.overall_score, result.to_dict())
                    scored_count += 1
                except Exception as e:
                    logger.warning(f"Save failed for job {job['id']}: {e}")

                pct = 75 + int(20 * (i + 1) / len(valid_jobs))
                if (i + 1) % 10 == 0 or i == len(valid_jobs) - 1:
                    _set_task_progress(task_id, "scoring", pct,
                                       f"[{_elapsed():.0f}s] Saved {scored_count}/{i+1} of {len(valid_jobs)} jobs...")

            _set_task_progress(task_id, "done", 100,
                               f"[{_elapsed():.0f}s] Scored {scored_count} jobs. Refresh to see results.")
            if run_tracker:
                run_tracker.finish(summary={"total": total, "scored": scored_count})
        except TaskCancelled:
            _set_task_progress(task_id, "cancelled", 0, f"Scoring cancelled by user.")
            if run_tracker:
                run_tracker.finish(summary={"cancelled": True})
        except Exception as e:
            logger.error(f"Scoring task failed: {e}", exc_info=True)
            _set_task_progress(task_id, "error", 0, f"Scoring failed: {e}")
            if run_tracker:
                run_tracker.finish(summary={"error": str(e)})

    thread = threading.Thread(target=run_scoring, daemon=True)
    thread.start()
    return HTMLResponse(f'<div class="text-blue-600 text-sm" id="action-result">Scoring started...</div>')


@app.post("/api/rescore-all", response_class=HTMLResponse)
async def rescore_all_jobs(request: Request):
    """Re-score ALL jobs (including previously scored) with the latest scoring engine."""
    resume = db.get_setting("resume_text")
    if not resume:
        return HTMLResponse(
            '<div class="text-red-600">No resume configured. Go to Settings first.</div>'
        )

    task_id = "rescore-jobs"
    if _get_task_progress(task_id).get("stage") not in (None, "done", "error", ""):
        return HTMLResponse(
            '<div class="text-yellow-600 text-sm">Re-scoring already in progress...</div>'
        )

    def run_rescore():
        _get_cancel_event(task_id).clear()
        run_tracker = None
        try:
            from src.dashboard.pipeline_metrics import PipelineRunTracker
            run_tracker = PipelineRunTracker(db, run_type="rescore")
            run_tracker.start()
        except Exception:
            pass

        try:
            import time as _time
            _t0 = _time.time()
            def _elapsed():
                return _time.time() - _t0

            _set_task_progress(task_id, "init", 5, "Loading resume and fetching all jobs...")
            _scorer = AlignmentScorer()
            _scorer.set_resume(resume)

            with db.get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, title, description FROM jobs WHERE is_active = 1 "
                    "AND description IS NOT NULL AND LENGTH(description) > 50 "
                    "ORDER BY scraped_date DESC LIMIT 2000"
                ).fetchall()

            total = len(rows)
            if total == 0:
                _set_task_progress(task_id, "done", 100, "No jobs to re-score.")
                if run_tracker:
                    run_tracker.finish(summary={"total": 0, "rescored": 0})
                return

            if run_tracker:
                run_tracker.record_step("rescore", items_processed=total)

            # ── Phase 1: Fast keyword scoring ─────────────────────────
            _set_task_progress(task_id, "scoring", 10,
                               f"[{_elapsed():.0f}s] Phase 1: Keyword scoring {total} jobs...")
            keyword_results = []
            descriptions = []
            titles = []
            valid_rows = []
            for i, row in enumerate(rows):
                _check_task_cancel(task_id)
                try:
                    result = _scorer.score_keyword_only(row["description"], row["title"] or "")
                    keyword_results.append(result)
                    descriptions.append(row["description"])
                    titles.append(row["title"] or "")
                    valid_rows.append(row)
                except Exception as e:
                    logger.warning(f"Keyword re-scoring failed for job {row['id']}: {e}")

                pct = 10 + int(40 * (i + 1) / total)
                if (i + 1) % 10 == 0 or i == total - 1:
                    _set_task_progress(task_id, "scoring", pct,
                                       f"[{_elapsed():.0f}s] Keyword scoring {i+1}/{total}...")

            # ── Phase 2: Batch semantic embedding ─────────────────────
            _check_task_cancel(task_id)
            if valid_rows:
                _set_task_progress(task_id, "scoring", 55,
                                   f"[{_elapsed():.0f}s] Phase 2: Batch semantic embedding {len(valid_rows)} jobs...")
                try:
                    sem_applied = _scorer.apply_batch_semantic(
                        keyword_results, descriptions, titles, keyword_threshold=25.0
                    )
                    _set_task_progress(task_id, "scoring", 75,
                                       f"[{_elapsed():.0f}s] Semantic scores: {sem_applied}/{len(valid_rows)} jobs")
                except Exception as e:
                    logger.warning(f"Batch semantic re-scoring failed (non-critical): {e}")

            # ── Phase 3: Save results to DB ──────────────────────────
            rescored = 0
            for i, (row, result) in enumerate(zip(valid_rows, keyword_results)):
                _check_task_cancel(task_id)
                try:
                    db.update_alignment_score(row["id"], result.overall_score, result.to_dict())
                    rescored += 1
                except Exception as e:
                    logger.warning(f"Save failed for job {row['id']}: {e}")

                pct = 75 + int(20 * (i + 1) / len(valid_rows))
                if (i + 1) % 10 == 0 or i == len(valid_rows) - 1:
                    _set_task_progress(task_id, "scoring", pct,
                                       f"[{_elapsed():.0f}s] Saved {rescored}/{i+1} of {len(valid_rows)} jobs...")

            _set_task_progress(task_id, "done", 100,
                               f"[{_elapsed():.0f}s] Re-scored {rescored} jobs. Refresh to see results.")
            if run_tracker:
                run_tracker.finish(summary={"total": total, "rescored": rescored})
        except TaskCancelled:
            _set_task_progress(task_id, "cancelled", 0, "Re-scoring cancelled by user.")
            if run_tracker:
                run_tracker.finish(summary={"cancelled": True})
        except Exception as e:
            logger.error(f"Re-scoring task failed: {e}", exc_info=True)
            _set_task_progress(task_id, "error", 0, f"Re-scoring failed: {e}")
            if run_tracker:
                run_tracker.finish(summary={"error": str(e)})

    thread = threading.Thread(target=run_rescore, daemon=True)
    thread.start()
    return HTMLResponse(f'<div class="text-blue-600 text-sm" id="action-result">Re-scoring started...</div>')


@app.post("/api/enrich-ratings", response_class=HTMLResponse)
async def enrich_company_ratings(request: Request):
    """Enrich company Glassdoor ratings — runs in background, PROCEED-first priority."""
    task_id = "enrich-ratings"
    if _get_task_progress(task_id).get("stage") not in (None, "done", "error", ""):
        return HTMLResponse('<div class="text-yellow-600 text-sm">Enrichment already in progress...</div>')

    def run_enrichment():
        _get_cancel_event(task_id).clear()
        import time as _time
        import json as _json
        from datetime import datetime as _dt

        try:
            _set_task_progress(task_id, "init", 5, "Loading Glassdoor client...")

            # Load Glassdoor API client
            _gd_client = None
            _gd_enabled = False
            try:
                from src.enrichment.glassdoor_client import get_glassdoor_client as _get_gd
                _gd_client = _get_gd()
                _gd_enabled = _gd_client.enabled
            except Exception:
                pass

            if not _gd_enabled:
                _set_task_progress(
                    task_id, "error", 0,
                    "Glassdoor API not configured. Add RAPIDAPI_KEY to Settings → Filters."
                )
                return

            # ── Build priority-ordered company list ──────────────────────────
            # Tier 1: companies with high-scoring jobs (alignment_score >= 60)
            #         that have no rating yet — these are the "likely PROCEED" jobs
            # Tier 2: companies with any jobs but no rating yet
            # Tier 3: companies with stale ratings (fetched > 30 days ago) — refresh
            _set_task_progress(task_id, "init", 10, "Building priority company list...")
            with db.get_connection() as conn:
                # Tier 1+2: no rating yet, sorted by max alignment score DESC
                unrated = conn.execute(
                    """SELECT company,
                              COUNT(*) AS job_count,
                              MAX(COALESCE(alignment_score, 0)) AS best_score
                       FROM jobs
                       WHERE is_active = 1
                         AND (company_rating IS NULL OR company_rating = 0)
                         AND company IS NOT NULL AND LENGTH(company) > 1
                       GROUP BY company
                       ORDER BY best_score DESC, job_count DESC
                       LIMIT 200"""
                ).fetchall()
                # Tier 3: has a rating but fetched > 30 days ago
                stale = conn.execute(
                    """SELECT company,
                              COUNT(*) AS job_count,
                              MAX(COALESCE(alignment_score, 0)) AS best_score,
                              MAX(company_rating_fetched_at) AS fetched_at
                       FROM jobs
                       WHERE is_active = 1
                         AND company_rating IS NOT NULL AND company_rating > 0
                         AND (
                             company_rating_fetched_at IS NULL
                             OR company_rating_fetched_at < datetime('now', '-30 days')
                         )
                         AND company IS NOT NULL AND LENGTH(company) > 1
                       GROUP BY company
                       ORDER BY best_score DESC, job_count DESC
                       LIMIT 100"""
                ).fetchall()

            # Merge: unrated first, then stale, deduplicate
            seen = set()
            companies = []
            for row in list(unrated) + list(stale):
                if row["company"] not in seen:
                    seen.add(row["company"])
                    companies.append({
                        "company": row["company"],
                        "job_count": row["job_count"],
                        "best_score": row["best_score"],
                        "is_stale": row["company"] not in {r["company"] for r in unrated},
                    })

            if not companies:
                _set_task_progress(task_id, "done", 100,
                                   "All companies already have fresh ratings.")
                return

            batch = companies[:60]
            total = len(batch)
            tier1_count = sum(1 for c in batch if c["best_score"] >= 60)
            _set_task_progress(
                task_id, "enriching", 15,
                f"Enriching {total} companies ({tier1_count} high-priority, "
                f"{total - tier1_count} others)..."
            )

            enriched = 0
            refreshed = 0
            not_found = 0
            api_exhausted = False

            for i, item in enumerate(batch):
                _check_task_cancel(task_id)
                if api_exhausted:
                    break

                company = item["company"]
                is_stale = item["is_stale"]
                pct = 15 + int(80 * (i + 1) / total)
                _set_task_progress(
                    task_id, "enriching", pct,
                    f"[{i+1}/{total}] {company[:30]}... "
                    f"({enriched} new, {refreshed} refreshed)"
                )

                try:
                    gd_data = _gd_client.lookup_company_sync(company)

                    if gd_data is None:
                        # Check for credit exhaustion vs just not found
                        not_found += 1
                        _time.sleep(0.5)
                        continue

                    rating = gd_data.get("glassdoor_rating")
                    if not rating:
                        not_found += 1
                        _time.sleep(0.5)
                        continue

                    # Store overall rating + full JSON breakdown + metadata
                    gd_json = _json.dumps({
                        k: v for k, v in gd_data.items()
                        if not k.startswith("_")
                    })
                    fetched_at = _dt.utcnow().isoformat()

                    with db.get_connection() as conn:
                        updated = conn.execute(
                            """UPDATE jobs
                               SET company_rating            = ?,
                                   company_glassdoor_json    = ?,
                                   company_rating_fetched_at = ?,
                                   company_rating_source     = 'glassdoor_api'
                               WHERE company = ? AND is_active = 1""",
                            (float(rating), gd_json, fetched_at, company),
                        ).rowcount

                    if updated > 0:
                        if is_stale:
                            refreshed += 1
                        else:
                            enriched += 1
                        logger.info(
                            "Glassdoor enriched %s: %.1f (%d jobs%s)",
                            company, rating, updated,
                            ", refresh" if is_stale else "",
                        )

                    _time.sleep(1.2)  # ~50 req/min staying well under free-tier limits

                except Exception as exc:
                    err_str = str(exc).lower()
                    if "429" in err_str or "rate limit" in err_str or "quota" in err_str:
                        api_exhausted = True
                        logger.warning("Glassdoor API credits exhausted — stopping enrichment")
                        break
                    logger.debug("Rating lookup failed for %s: %s", company, exc)
                    _time.sleep(0.5)
                    continue

            # Final message
            parts = []
            if enriched:
                parts.append(f"{enriched} new")
            if refreshed:
                parts.append(f"{refreshed} refreshed")
            if not_found:
                parts.append(f"{not_found} not on Glassdoor")
            summary = ", ".join(parts) if parts else "none enriched"

            if api_exhausted:
                msg = (
                    f"API credits exhausted after {enriched + refreshed} companies ({summary}). "
                    "Historical ratings shown where available. Try again tomorrow."
                )
                _set_task_progress(task_id, "done", 100, msg)
            else:
                _set_task_progress(
                    task_id, "done", 100,
                    f"Done — {summary}. Refresh to see ratings."
                )

        except TaskCancelled:
            _set_task_progress(task_id, "cancelled", 0, "Enrichment cancelled by user.")
        except Exception as exc:
            logger.error("Enrichment task failed: %s", exc, exc_info=True)
            _set_task_progress(task_id, "error", 0, f"Enrichment failed: {exc}")

    thread = threading.Thread(target=run_enrichment, daemon=True)
    thread.start()
    return HTMLResponse(
        '<div class="text-blue-600 text-sm">'
        'Culture score enrichment started — high-scoring jobs first...</div>'
    )


@app.get("/api/job/{job_id}/verify-career-page")
async def api_verify_career_page(request: Request, job_id: int):
    """Verify a single job against the company's career page."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    title = job.get("title", "")
    company = job.get("company", "")
    job_url = job.get("job_url", "")

    try:
        from src.enrichment.career_page_checker import get_career_page_checker
        checker = get_career_page_checker()
        result = await checker.verify_job(title, company, job_url, force=True)
        details = result.to_dict()

        # Persist result
        db.update_career_page_verification(job_id, result.found_on_career_page, details)

        # Return HTML for HTMX / fetch
        method_labels = {
            "greenhouse_api": "Greenhouse API",
            "lever_api": "Lever API",
            "career_page_probe": "career page scan",
            "serper_search": "Google search",
        }
        method_label = method_labels.get(result.verification_method, result.verification_method)

        if result.found_on_career_page is True:
            icon = "✅"
            color = "green"
            view_url = result.company_careers_url or result.career_page_url
            if result.company_careers_url:
                msg = f'Verified on company site (<a href="{view_url}" target="_blank" class="underline">view</a>)'
            else:
                msg = f"Verified via {method_label}"
                if view_url:
                    msg += f' (<a href="{view_url}" target="_blank" class="underline">view</a>)'
            conf = result.match_confidence
            if conf and conf >= 0.75:
                msg += f' — {conf:.0%} confidence'
        elif result.found_on_career_page is False:
            icon = "⚠️"
            color = "red"
            msg = "Not found on company career page"
            if method_label:
                msg += f" (checked via {method_label})"
            if result.company_careers_url:
                msg += f'<br><span class="text-xs text-gray-500">Company careers: <a href="{result.company_careers_url}" target="_blank" class="underline text-blue-600">{result.company_careers_url.split("//")[-1].rstrip("/")}</a></span>'
            if result.error:
                msg += f'<br><span class="text-xs text-gray-500">{result.error}</span>'
        else:
            icon = "❓"
            color = "gray"
            msg = result.error or "Could not verify"

        html = (
            f'<div class="rounded-lg border p-3 bg-{color}-50 border-{color}-200 text-sm">'
            f'<span class="font-medium">{icon} {msg}</span>'
        )
        if result.total_open_jobs is not None:
            html += f'<br><span class="text-xs text-gray-500">{result.total_open_jobs} open positions at this company</span>'
        html += '</div>'

        return HTMLResponse(html)

    except Exception as exc:
        logger.error("Career page verification failed for job %d: %s", job_id, exc, exc_info=True)
        return HTMLResponse(
            f'<div class="text-red-600 text-sm">Verification failed: {exc}</div>'
        )


@app.post("/api/verify-career-pages", response_class=HTMLResponse)
async def verify_career_pages_bulk(request: Request):
    """Bulk verify jobs against company career pages — runs in background."""
    task_id = "verify-career-pages"
    if _get_task_progress(task_id).get("stage") not in (None, "done", "error", ""):
        return HTMLResponse('<div class="text-yellow-600 text-sm">Verification already in progress...</div>')

    def run_verification():
        _get_cancel_event(task_id).clear()
        import time as _time
        import json as _json

        try:
            _set_task_progress(task_id, "init", 5, "Loading career page checker...")

            from src.enrichment.career_page_checker import get_career_page_checker
            checker = get_career_page_checker()

            if not checker.enabled:
                _set_task_progress(task_id, "error", 0, "Career page checking is disabled.")
                return

            # Get jobs that haven't been checked yet, prioritize high-scoring ones
            _set_task_progress(task_id, "init", 10, "Finding unchecked jobs...")
            with db.get_connection() as conn:
                rows = conn.execute(
                    """SELECT id, title, company, job_url
                       FROM jobs
                       WHERE is_active = 1
                         AND career_page_verified IS NULL
                         AND title IS NOT NULL AND LENGTH(title) > 3
                         AND company IS NOT NULL AND LENGTH(company) > 1
                       ORDER BY COALESCE(alignment_score, 0) DESC"""
                ).fetchall()

            if not rows:
                _set_task_progress(task_id, "done", 100, "All jobs already verified.")
                return

            total = len(rows)
            verified_true = 0
            verified_false = 0
            errors = 0

            for i, row in enumerate(rows):
                _check_task_cancel(task_id)
                pct = 10 + int(85 * (i + 1) / total)
                _set_task_progress(
                    task_id, "verifying", pct,
                    f"[{i+1}/{total}] {row['company'][:25]}... "
                    f"({verified_true} found, {verified_false} not found)"
                )

                try:
                    result = checker.verify_job_sync(
                        row["title"], row["company"], row.get("job_url", "")
                    )
                    details = result.to_dict()
                    db.update_career_page_verification(
                        row["id"], result.found_on_career_page, details
                    )

                    if result.found_on_career_page is True:
                        verified_true += 1
                    elif result.found_on_career_page is False:
                        verified_false += 1
                    else:
                        errors += 1

                    _time.sleep(1.5)  # polite rate limiting

                except Exception as exc:
                    logger.debug("Career verification failed for job %d: %s", row["id"], exc)
                    errors += 1
                    _time.sleep(0.5)

            parts = []
            if verified_true:
                parts.append(f"{verified_true} confirmed")
            if verified_false:
                parts.append(f"{verified_false} not found")
            if errors:
                parts.append(f"{errors} could not check")
            summary = ", ".join(parts) if parts else "none verified"

            _set_task_progress(task_id, "done", 100, f"Done — {summary}. Refresh to see results.")

        except TaskCancelled:
            _set_task_progress(task_id, "cancelled", 0, "Verification cancelled by user.")
        except Exception as exc:
            logger.error("Career verification task failed: %s", exc, exc_info=True)
            _set_task_progress(task_id, "error", 0, f"Verification failed: {exc}")

    thread = threading.Thread(target=run_verification, daemon=True)
    thread.start()
    return HTMLResponse(
        '<div class="text-blue-600 text-sm">'
        'Career page verification started — high-scoring jobs first...</div>'
    )


@app.post("/api/generate-packages", response_class=HTMLResponse)
async def generate_packages(request: Request, job_ids: str = Form(...)):
    """Generate application packages for selected jobs."""
    try:
        ids = [int(x.strip()) for x in job_ids.split(",") if x.strip()]
    except ValueError:
        return HTMLResponse('<div class="text-red-600">Invalid job IDs</div>')

    if not ids:
        return HTMLResponse('<div class="text-yellow-600">No jobs selected</div>')

    created = 0
    for jid in ids:
        job = db.get_job(jid)
        if not job:
            continue
        existing = db.get_application_package(jid)
        if existing and existing["status"] in ("pending", "generated"):
            continue
        db.create_application_package(jid)
        created += 1

    # In a real implementation, this would trigger async AI generation
    # For now, we queue them as pending
    return HTMLResponse(
        f'<div class="text-green-600 font-medium">'
        f'Queued {created} application packages for generation. '
        f'<a href="/" class="underline">Refresh</a> to track progress.</div>'
    )


def _set_progress(job_id: int, stage: str, percent: int, message: str):
    """Update generation progress for a job."""
    with _progress_lock:
        _generation_progress[job_id] = {
            "stage": stage,
            "percent": percent,
            "message": message,
            "updated": datetime.now().isoformat(),
        }


def _clear_progress(job_id: int):
    """Clear progress for a completed generation."""
    with _progress_lock:
        _generation_progress.pop(job_id, None)


@app.get("/api/generation-progress/{job_id}")
async def generation_progress(job_id: int):
    """SSE endpoint for real-time generation progress."""
    import time

    async def event_stream():
        last_percent = -1
        stale_count = 0
        while True:
            with _progress_lock:
                progress = _generation_progress.get(job_id)

            if progress:
                if progress["percent"] != last_percent:
                    last_percent = progress["percent"]
                    stale_count = 0
                    data = json.dumps(progress)
                    yield f"data: {data}\n\n"
                    if progress["percent"] >= 100:
                        break
                else:
                    stale_count += 1
            else:
                stale_count += 1

            if stale_count > 120:  # 60 seconds with no update
                yield f"data: {json.dumps({'stage': 'timeout', 'percent': 0, 'message': 'Generation timed out'})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/generate-single/{job_id}", response_class=HTMLResponse)
async def generate_single_package(
    request: Request,
    job_id: int,
    ai_model: str = Form("template"),
    resume_track: str = Form("engineering"),
):
    """Generate application package for a single job — AI or template-based."""
    job = db.get_job(job_id)
    if not job:
        return HTMLResponse('<div class="text-red-600">Job not found</div>')

    # Load track-specific resume if available, fall back to generic
    resume = db.get_setting(f"resume_text_{resume_track}") or db.get_setting("resume_text")
    if not resume:
        return HTMLResponse(
            '<div class="text-red-600">No resume configured. Go to Settings first.</div>'
        )

    # Diagnostic: confirm resume is loaded and has real content
    track_source = f"resume_text_{resume_track}" if db.get_setting(f"resume_text_{resume_track}") else "resume_text (generic)"
    logger.info(
        "Resume loaded from '%s': %d chars, starts with: %s",
        track_source,
        len(resume),
        resume[:100].replace("\n", " "),
    )

    try:
        provider_name = None
        model_name = None

        # Parse "provider:model" or "template"
        if ai_model and ai_model != "template" and ":" in ai_model:
            provider_name, model_name = ai_model.split(":", 1)

        if provider_name and model_name:
            # AI-powered generation with sectional pipeline
            logger.info(f"AI generation: {provider_name}/{model_name} for job {job_id}")

            _set_progress(job_id, "init", 5, "Initializing AI model...")
            gen = AIGenerator(provider=provider_name, model=model_name)

            # Extract skills for cover letter
            from src.dashboard.scoring import TECH_KEYWORDS
            jd_lower = (job.get("description") or "").lower()
            resume_lower = resume.lower()
            matched = sorted(k for k in TECH_KEYWORDS if k in jd_lower and k in resume_lower)

            # Use sectional pipeline — generates each section independently
            def progress_cb(stage: str, pct: int, message: str):
                _set_progress(job_id, stage, pct, message)

            package = gen.generate_sectional_package(
                job=job,
                resume_text=resume,
                resume_track=resume_track,
                matched_skills=matched,
                progress_cb=progress_cb,
            )

            resume_content = package["resume_text"]
            cover_content = package["cover_letter_text"]
            validation_note = ""

            _set_progress(job_id, "saving", 95, "Saving text files...")

            # Save text files to disk (backward compat)
            from src.dashboard.generator import _slugify
            company_slug = _slugify(job.get("company", "unknown"))
            package_dir = PACKAGES_DIR / f"{company_slug}_{job_id}"
            package_dir.mkdir(parents=True, exist_ok=True)
            (package_dir / "resume.txt").write_text(resume_content, encoding="utf-8")
            (package_dir / "cover_letter.txt").write_text(cover_content, encoding="utf-8")

            _set_progress(job_id, "docx", 96, "Building DOCX documents...")

            # Generate DOCX files
            docx_result = generate_docx_package(
                resume_text=resume_content,
                cover_letter_text=cover_content,
                job=job,
                output_dir=package_dir,
            )
            _set_progress(job_id, "saving", 98, "Saving to database...")

            # Save to DB
            pkg_id = db.create_application_package(job_id)
            db.update_application_package(
                pkg_id,
                resume_text=resume_content,
                cover_letter_text=cover_content,
                status="generated",
                ai_model=model_name,
                ai_provider=provider_name,
            )
            model_display = get_model_display_name(provider_name, model_name)
            _set_progress(job_id, "done", 100, f"Complete — {model_display}")

            # Build file list for response
            files_msg = ""
            if docx_result.get("resume_docx"):
                files_msg += " DOCX resume"
            if docx_result.get("cover_letter_docx"):
                files_msg += " + cover letter"
            if docx_result.get("resume_pdf"):
                files_msg += " + PDFs"

            return HTMLResponse(
                f'<div class="text-green-600 font-medium">'
                f'AI package generated ({model_display} / {resume_track}){validation_note}.'
                f'{files_msg}. '
                f'<a href="/job/{job_id}" class="underline">Refresh to see files</a></div>'
            )
        else:
            # Template-based generation (fast — no progress needed)
            _set_progress(job_id, "template", 30, "Generating from template...")
            result = generate_application_package(job, resume, PACKAGES_DIR)
            if result["status"] == "success":
                resume_txt = Path(result["resume_path"]).read_text(encoding="utf-8") if result.get("resume_path") else None
                cl_txt = Path(result["cover_letter_path"]).read_text(encoding="utf-8") if result.get("cover_letter_path") else None

                # Generate DOCX from template output
                if resume_txt and cl_txt:
                    package_dir = Path(result["resume_path"]).parent if result.get("resume_path") else PACKAGES_DIR
                    generate_docx_package(resume_txt, cl_txt, job, package_dir)

                pkg_id = db.create_application_package(job_id)
                db.update_application_package(
                    pkg_id,
                    resume_text=resume_txt,
                    cover_letter_text=cl_txt,
                    status="generated",
                )
                _set_progress(job_id, "done", 100, "Complete — Template")
                return HTMLResponse(
                    f'<div class="text-green-600 font-medium">'
                    f'Template package generated for "{job["title"]}" at {job["company"]}. '
                    f'<a href="/job/{job_id}" class="underline">Refresh to see files</a></div>'
                )
            else:
                _clear_progress(job_id)
                return HTMLResponse(
                    f'<div class="text-red-600">Generation failed: {result.get("error", "unknown error")}</div>'
                )
    except Exception as e:
        logger.error(f"Package generation failed for job {job_id}: {e}", exc_info=True)
        _clear_progress(job_id)
        return HTMLResponse(f'<div class="text-red-600">Error: {e}</div>')


@app.post("/api/generate-constrained/{job_id}", response_class=HTMLResponse)
async def generate_constrained_package(
    request: Request,
    job_id: int,
    ai_model: str = Form("claude:claude-3-5-haiku-20241022"),
    resume_track: str = Form("engineering"),
):
    """Generate application package using the 3-layer constrained pipeline.

    This route uses the fabrication-safe pipeline:
    Layer 1: Build GenerationContext from pre-existing pipeline data
    Layer 2: Constrained LLM generation (achievement bank + tool constraints)
    Layer 3: Post-generation fabrication detection (Tier 3 blocklist scan)
    """
    job = db.get_job(job_id)
    if not job:
        return HTMLResponse('<div class="text-red-600">Job not found</div>')

    resume = db.get_setting(f"resume_text_{resume_track}") or db.get_setting("resume_text")
    if not resume:
        return HTMLResponse(
            '<div class="text-red-600">No resume configured. Go to Settings first.</div>'
        )

    try:
        # Parse provider:model
        provider_name, model_name = "claude", "claude-3-5-haiku-20241022"
        if ai_model and ":" in ai_model:
            provider_name, model_name = ai_model.split(":", 1)

        _set_progress(job_id, "init", 5, "Initializing AI model...")
        gen = AIGenerator(provider=provider_name, model=model_name)

        _set_progress(job_id, "context", 10, "Building generation context...")

        # Simulate progress during the long AI generation call
        import threading
        _gen_done = threading.Event()
        def _tick_progress():
            stages = [
                (15, "constraints", "Loading verified tools & blocked skills..."),
                (22, "generating", "Analyzing job requirements..."),
                (30, "generating", "Matching resume experience to JD..."),
                (38, "generating", "AI drafting professional summary..."),
                (45, "generating", "AI tailoring work experience bullets..."),
                (52, "generating", "AI selecting relevant technical skills..."),
                (58, "generating", "AI writing role-specific achievements..."),
                (64, "generating", "AI drafting cover letter opening..."),
                (70, "cover_letter", "AI writing cover letter body..."),
                (75, "cover_letter", "AI completing cover letter closing..."),
            ]
            for pct, stage, msg in stages:
                if _gen_done.wait(timeout=4):
                    return
                _set_progress(job_id, stage, pct, msg)

        ticker = threading.Thread(target=_tick_progress, daemon=True)
        ticker.start()

        result = gen.generate_constrained_package(
            job=job,
            resume_text=resume,
            db=db,
        )
        _gen_done.set()

        _set_progress(job_id, "validating", 80, "Running fabrication checks (Layer 3)...")

        resume_content = result.get("tailored_resume", "")
        cover_content = result.get("cover_letter_draft", "")

        if not resume_content:
            _clear_progress(job_id)
            return HTMLResponse(
                '<div class="text-red-600">Constrained generation returned empty resume. '
                'Check logs for details.</div>'
            )

        _set_progress(job_id, "saving", 88, "Saving text files...")

        # Save to disk
        from src.dashboard.generator import _slugify
        company_slug = _slugify(job.get("company", "unknown"))
        package_dir = PACKAGES_DIR / f"{company_slug}_{job_id}"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "resume.txt").write_text(resume_content, encoding="utf-8")
        if cover_content:
            (package_dir / "cover_letter.txt").write_text(cover_content, encoding="utf-8")

        _set_progress(job_id, "docx", 92, "Building DOCX documents...")

        # Generate DOCX files
        docx_result = generate_docx_package(
            resume_text=resume_content,
            cover_letter_text=cover_content,
            job=job,
            output_dir=package_dir,
        )

        # Save to DB
        pkg_id = db.create_application_package(job_id)
        db.update_application_package(
            pkg_id,
            resume_text=resume_content,
            cover_letter_text=cover_content,
            status="generated",
            ai_model=model_name,
            ai_provider=provider_name,
        )

        # Store generation metadata in the package
        try:
            with db.get_connection() as conn:
                conn.execute(
                    "UPDATE application_packages SET generation_metadata = ?, cover_letter_status = ? WHERE id = ?",
                    (
                        json.dumps({
                            "fabrication_errors": result.get("fabrication_errors", []),
                            "formatting_warnings": result.get("formatting_warnings", []),
                            "gap_flags": result.get("gap_flags", []),
                            "base_resume_version": result.get("base_resume_version"),
                            "verified_tools_used": result.get("verified_tools_used", []),
                            "blocked_tools_in_jd": result.get("blocked_tools_in_jd", []),
                            "requires_human_review": result.get("requires_human_review", False),
                            "validation_passed": result.get("validation_passed", False),
                        }),
                        "DRAFT_NEEDS_EDIT",
                        pkg_id,
                    ),
                )
        except Exception as meta_err:
            logger.warning(f"Failed to save generation metadata: {meta_err}")

        # Set job status based on validation results
        if result.get("validation_passed") and not result.get("requires_human_review"):
            db.set_package_ready(
                job_id=job_id,
                package_id=pkg_id,
                generation_log=result
            )
            status_badge = '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Package Ready</span>'
        else:
            with db.get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET status = 'reviewing' WHERE id = ?", (job_id,)
                )
            status_badge = '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Review Required</span>'

        # Build warnings HTML
        warnings_html = ""
        fab_errors = result.get("fabrication_errors", [])
        fmt_warnings = result.get("formatting_warnings", [])
        gap_flags = result.get("gap_flags", [])

        if fab_errors:
            warnings_html += '<div class="mt-2 text-xs text-red-600"><strong>Fabrication errors:</strong><ul class="list-disc ml-4">'
            for err in fab_errors:
                warnings_html += f'<li>{err}</li>'
            warnings_html += '</ul></div>'

        if gap_flags:
            warnings_html += f'<div class="mt-1 text-xs text-yellow-600">Tool gaps (excluded from resume): {", ".join(gap_flags)}</div>'

        if fmt_warnings:
            warnings_html += f'<div class="mt-1 text-xs text-gray-500">{len(fmt_warnings)} formatting warning(s)</div>'

        model_display = get_model_display_name(provider_name, model_name)
        _set_progress(job_id, "done", 100, f"Complete — {model_display} (constrained)")

        return HTMLResponse(
            f'<div class="text-green-600 font-medium">'
            f'Constrained package generated ({model_display} / {result.get("base_resume_version", "?")}) '
            f'{status_badge}'
            f'{warnings_html}'
            f'<a href="/job/{job_id}" class="underline ml-2">Refresh to see files</a></div>'
        )

    except RuntimeError as e:
        _clear_progress(job_id)
        return HTMLResponse(
            f'<div class="text-red-600">Generation failed: {str(e)}</div>',
        )
    except Exception as e:
        logger.error(f"Constrained generation failed for job {job_id}: {e}", exc_info=True)
        _clear_progress(job_id)
        return HTMLResponse(f'<div class="text-red-600">Error: {e}</div>')


@app.post("/api/confirm-review/{job_id}")
async def confirm_review(job_id: int):
    """Human confirms they have reviewed the package despite gap flags or warnings.
    Advances status to package_ready."""
    with db.get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status = 'package_ready' WHERE id = ?",
            (job_id,)
        )
    return HTMLResponse(
        '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Confirmed — Package Ready</span>'
    )


@app.get("/api/package/{job_id}/resume")
async def view_resume(job_id: int):
    """View or download generated resume file."""
    package = db.get_application_package(job_id)
    if not package or not package.get("resume_text"):
        raise HTTPException(404, "No resume generated for this job")
    return HTMLResponse(
        f'<html><head><title>Resume - Job {job_id}</title>'
        f'<style>body{{font-family:monospace;white-space:pre-wrap;max-width:800px;margin:40px auto;padding:20px;line-height:1.6;}}</style>'
        f'</head><body>{package["resume_text"]}</body></html>'
    )


@app.get("/api/package/{job_id}/cover-letter")
async def view_cover_letter(job_id: int):
    """View or download generated cover letter file."""
    package = db.get_application_package(job_id)
    if not package or not package.get("cover_letter_text"):
        raise HTTPException(404, "No cover letter generated for this job")
    return HTMLResponse(
        f'<html><head><title>Cover Letter - Job {job_id}</title>'
        f'<style>body{{font-family:Georgia,serif;white-space:pre-wrap;max-width:700px;margin:40px auto;padding:20px;line-height:1.8;}}</style>'
        f'</head><body>{package["cover_letter_text"]}</body></html>'
    )


@app.get("/api/package/{job_id}/download/{file_type}")
async def download_package_file(job_id: int, file_type: str):
    """Download resume or cover letter as .docx (or .txt fallback).

    Supported file_type values:
      - resume, resume-docx, resume-pdf
      - cover-letter, cover-letter-docx, cover-letter-pdf
    """
    package = db.get_application_package(job_id)
    if not package:
        raise HTTPException(404, "No package for this job")
    job = db.get_job(job_id)
    company = job["company"] if job else "unknown"

    # Check for DOCX files on disk first
    from src.dashboard.generator import _slugify
    company_slug = _slugify(company)
    package_dir = PACKAGES_DIR / f"{company_slug}_{job_id}"

    if file_type in ("resume", "resume-docx"):
        # Try DOCX first
        docx_files = list(package_dir.glob("*Resume*.docx")) if package_dir.exists() else []
        if docx_files:
            return FileResponse(
                str(docx_files[0]), filename=docx_files[0].name,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        # Fallback to txt
        content = package.get("resume_text", "")
        if not content:
            raise HTTPException(404, "No resume generated")
        import tempfile
        filename = f"GrygoriiT_Resume_{company_slug}.txt"
        tmp = Path(tempfile.gettempdir()) / filename
        tmp.write_text(content, encoding="utf-8")
        return FileResponse(str(tmp), filename=filename, media_type="text/plain")

    elif file_type in ("cover-letter", "cover-letter-docx"):
        docx_files = list(package_dir.glob("*CoverLetter*.docx")) if package_dir.exists() else []
        if docx_files:
            return FileResponse(
                str(docx_files[0]), filename=docx_files[0].name,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        content = package.get("cover_letter_text", "")
        if not content:
            raise HTTPException(404, "No cover letter generated")
        import tempfile
        filename = f"GrygoriiT_CoverLetter_{company_slug}.txt"
        tmp = Path(tempfile.gettempdir()) / filename
        tmp.write_text(content, encoding="utf-8")
        return FileResponse(str(tmp), filename=filename, media_type="text/plain")

    elif file_type == "resume-pdf":
        pdf_files = list(package_dir.glob("*Resume*.pdf")) if package_dir.exists() else []
        if not pdf_files:
            # Try to generate PDF on the fly
            docx_files = list(package_dir.glob("*Resume*.docx")) if package_dir.exists() else []
            if docx_files:
                pdf_path = convert_to_pdf(docx_files[0])
                if pdf_path:
                    return FileResponse(str(pdf_path), filename=pdf_path.name, media_type="application/pdf")
            raise HTTPException(404, "PDF not available — LibreOffice required for conversion")
        return FileResponse(str(pdf_files[0]), filename=pdf_files[0].name, media_type="application/pdf")

    elif file_type == "cover-letter-pdf":
        pdf_files = list(package_dir.glob("*CoverLetter*.pdf")) if package_dir.exists() else []
        if not pdf_files:
            docx_files = list(package_dir.glob("*CoverLetter*.docx")) if package_dir.exists() else []
            if docx_files:
                pdf_path = convert_to_pdf(docx_files[0])
                if pdf_path:
                    return FileResponse(str(pdf_path), filename=pdf_path.name, media_type="application/pdf")
            raise HTTPException(404, "PDF not available — LibreOffice required for conversion")
        return FileResponse(str(pdf_files[0]), filename=pdf_files[0].name, media_type="application/pdf")

    else:
        raise HTTPException(400, f"Invalid file type: {file_type}")


# ── API: JSON endpoints ────────────────────────────────────────────

@app.get("/api/stats")
async def api_stats(days: int = Query(7)):
    return db.get_stats(days=days)


@app.get("/api/jobs")
async def api_jobs(
    days: int = Query(7),
    source: Optional[str] = Query(None),
    remote_only: bool = Query(False),
    sort: str = Query("remote_first"),
    limit: int = Query(100),
):
    jobs = db.get_jobs(days=days, source=source, remote_only=remote_only, sort=sort, limit=limit)
    return {"count": len(jobs), "jobs": jobs}


@app.post("/api/skills/add", response_class=HTMLResponse)
async def api_add_skill(request: Request):
    """Add a skill to the user's verified skills dictionary."""
    form = await request.form()
    skill = form.get("skill", "").strip()
    if not skill:
        return HTMLResponse('<span class="text-red-600 text-xs">No skill provided</span>')

    # Load current user skills
    raw = db.get_setting("user_added_skills", "[]")
    skills = set(json.loads(raw))
    skill_lower = skill.lower()
    skills.add(skill_lower)
    db.set_setting("user_added_skills", json.dumps(sorted(skills)))

    logger.info("User added skill: '%s' (total user skills: %d)", skill_lower, len(skills))

    return HTMLResponse(
        f'<span class="px-1.5 py-0.5 rounded-md bg-green-50 text-green-700 border border-green-200 '
        f'text-xs cursor-default" title="Added to your skills">'
        f'✓ {skill}</span>'
    )


@app.post("/api/skills/remove", response_class=HTMLResponse)
async def api_remove_skill(request: Request):
    """Remove a skill from the user's verified skills dictionary."""
    form = await request.form()
    skill = form.get("skill", "").strip()
    if not skill:
        return HTMLResponse('<span class="text-red-600 text-xs">No skill provided</span>')

    raw = db.get_setting("user_added_skills", "[]")
    skills = set(json.loads(raw))
    skills.discard(skill.lower())
    db.set_setting("user_added_skills", json.dumps(sorted(skills)))

    logger.info("User removed skill: '%s' (total user skills: %d)", skill, len(skills))
    return HTMLResponse(
        f'<span class="text-xs text-gray-500">Removed: {skill}</span>'
    )


@app.get("/api/skills", response_class=HTMLResponse)
async def api_list_skills():
    """List all user-added skills."""
    raw = db.get_setting("user_added_skills", "[]")
    skills = sorted(json.loads(raw))
    if not skills:
        return HTMLResponse('<span class="text-xs text-gray-400">No custom skills added yet</span>')

    tags = " ".join(
        f'<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-blue-50 text-blue-700 '
        f'border border-blue-200 text-xs">{s}'
        f'<button onclick="removeSkill(\'{s}\', this)" class="text-blue-400 hover:text-red-500 ml-0.5">&times;</button>'
        f'</span>'
        for s in skills
    )
    return HTMLResponse(f'<div class="flex flex-wrap gap-1">{tags}</div>')


@app.post("/api/skills/exclude", response_class=HTMLResponse)
async def api_exclude_skill(request: Request):
    """Exclude a built-in skill from scoring (user says they don't have it)."""
    form = await request.form()
    skill = form.get("skill", "").strip()
    if not skill:
        return HTMLResponse('<span class="text-red-600 text-xs">No skill provided</span>')

    raw = db.get_setting("user_removed_skills", "[]")
    removed = set(json.loads(raw))
    skill_lower = skill.lower()
    removed.add(skill_lower)
    db.set_setting("user_removed_skills", json.dumps(sorted(removed)))

    logger.info("User excluded skill: '%s' (total excluded: %d)", skill_lower, len(removed))
    return HTMLResponse(
        f'<span class="text-xs text-gray-500">Excluded: {skill}</span>'
    )


@app.post("/api/skills/restore", response_class=HTMLResponse)
async def api_restore_skill(request: Request):
    """Restore a previously excluded skill back to the active skills list."""
    form = await request.form()
    skill = form.get("skill", "").strip()
    if not skill:
        return HTMLResponse('<span class="text-red-600 text-xs">No skill provided</span>')

    raw = db.get_setting("user_removed_skills", "[]")
    removed = set(json.loads(raw))
    removed.discard(skill.lower())
    db.set_setting("user_removed_skills", json.dumps(sorted(removed)))

    logger.info("User restored skill: '%s' (total excluded: %d)", skill, len(removed))
    return HTMLResponse(
        f'<span class="text-xs text-green-600">Restored: {skill}</span>'
    )


def _check_defense_exclusion(description: str, company: str) -> dict:
    """Lightweight defense/clearance check for Re-Score.

    Returns dict with 'is_defense': bool, 'reasons': list of strings.
    """
    import re as _re
    try:
        from src.screening.data.list_provider import get_gate_list
    except ImportError:
        return {"is_defense": False, "reasons": []}

    reasons = []
    jd_lower = description.lower()
    company_lower = (company or "").lower()

    defense_primes = get_gate_list("DEFENSE_PRIMES")
    clearance_keywords = get_gate_list("CLEARANCE_KEYWORDS")
    gov_employer_signals = get_gate_list("GOV_EMPLOYER_SIGNALS")

    # Check defense prime contractors
    for prime in defense_primes:
        if prime in company_lower:
            reasons.append(f"Defense contractor: {prime}")
            break

    # Check clearance keywords in JD
    for kw in clearance_keywords:
        if kw in jd_lower:
            reasons.append(f"Clearance: {kw}")
            if len(reasons) >= 3:
                break

    # Check government employer signals
    short_signals = {s for s in gov_employer_signals if len(s) < 5}
    long_signals = gov_employer_signals - short_signals
    for sig in long_signals:
        if sig in jd_lower:
            reasons.append(f"Gov signal: {sig}")
            if len(reasons) >= 4:
                break
    if len(reasons) < 4:
        for sig in short_signals:
            if _re.search(r'\b' + _re.escape(sig) + r'\b', jd_lower):
                reasons.append(f"Gov signal: {sig}")
                if len(reasons) >= 4:
                    break

    return {"is_defense": len(reasons) >= 1, "reasons": reasons}


@app.get("/api/job/{job_id}/score")
async def api_job_score(request: Request, job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    resume = db.get_setting("resume_text")
    if not resume:
        raise HTTPException(400, "No resume configured")

    # ── Role category hard-stop ─────────────────────────────────────
    AUTO_DECLINE_CATEGORIES = {
        "physical_infrastructure", "sales_marketing",
        "legal_finance_hr", "executive_management",
    }
    job_category = job.get("job_category", "") or ""
    if not job_category:
        try:
            from src.dashboard.semantic_classifier import SemanticClassifier
            _cls = SemanticClassifier()
            _cls_result = _cls.classify_keyword(
                job.get("title", ""), job.get("description", ""),
            )
            job_category = _cls_result.category
            with db.get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET job_category = ?, category_confidence = ? WHERE id = ?",
                    (job_category, _cls_result.confidence, job_id),
                )
        except Exception as _e:
            logger.debug("Category classification failed: %s", _e)

    if job_category in AUTO_DECLINE_CATEGORIES:
        from src.dashboard.scoring import AlignmentResult, Recommendation
        result = AlignmentResult(
            overall_score=0,
            recommendation=Recommendation.NO_PROCEED,
            interpretation=(
                f"Auto-declined: category '{job_category.replace('_', ' ')}' "
                f"is outside target roles (engineering / data / analytics)"
            ),
            categories=[],
            critical_gaps=[f"Category: {job_category.replace('_', ' ')}"],
        )
        db.update_alignment_score(job_id, 0, result.to_dict())
        if request.headers.get("HX-Request"):
            return HTMLResponse(
                f'<div class="rounded-lg border p-3 bg-red-50 border-red-200">'
                f'<div class="flex items-center justify-between mb-2">'
                f'<span class="text-lg font-bold text-red-700">0%</span>'
                f'<span class="px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800">AUTO-DECLINE</span>'
                f'</div>'
                f'<div class="text-xs text-red-600">{result.interpretation}</div>'
                f'</div>'
            )
        return result.to_dict()

    # Check for defense/clearance exclusion
    defense_check = _check_defense_exclusion(
        job.get("description", ""), job.get("company", ""),
    )

    # Use configured scoring model (Settings → Scoring → LLM Model)
    scoring_model = db.get_setting("scoring_llm_model", "keyword")
    fast_scorer = AlignmentScorer(enable_semantic_filter=False)
    fast_scorer.set_resume(resume)
    if scoring_model and scoring_model != "keyword":
        # Parse "claude:model-name" or plain Ollama model name
        if scoring_model.startswith("claude:"):
            _model_name = scoring_model.split(":", 1)[1]
            _provider = "claude"
        else:
            _model_name = scoring_model
            _provider = "ollama"
        result = fast_scorer.score_with_llm(
            job.get("description", ""), job.get("title", ""), db=db,
            model=_model_name, provider=_provider,
        )
    else:
        result = fast_scorer.score(
            job.get("description", ""), job.get("title", ""),
        )

    # Apply defense penalty if detected
    if defense_check["is_defense"]:
        # Cap the score and change recommendation
        original_score = result.overall_score
        result.overall_score = min(result.overall_score, 25.0)
        result.recommendation = result.recommendation.__class__("no_proceed")
        result.interpretation = (
            f"⚠️ DEFENSE/CLEARANCE JOB — Auto-capped from {original_score:.0f}%. "
            f"Detected: {'; '.join(defense_check['reasons'][:3])}"
        )
        # Add defense signals to critical gaps
        result.critical_gaps = ["🚫 Defense/Clearance Required"] + result.critical_gaps

    db.update_alignment_score(job_id, result.overall_score, result.to_dict())

    # If called via HTMX, return formatted HTML instead of JSON
    if request.headers.get("HX-Request"):
        data = result.to_dict()
        score = data.get("overall_score", 0)
        rec = data.get("recommendation", "")
        interp = data.get("interpretation", "")

        # Color based on score
        if score >= 70:
            score_color = "text-green-700"
            bg_color = "bg-green-50 border-green-200"
            rec_badge = '<span class="px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-800">PROCEED</span>'
        elif score >= 50:
            score_color = "text-yellow-700"
            bg_color = "bg-yellow-50 border-yellow-200"
            rec_badge = '<span class="px-2 py-0.5 rounded text-xs font-bold bg-yellow-100 text-yellow-800">REVIEW</span>'
        else:
            score_color = "text-red-700"
            bg_color = "bg-red-50 border-red-200"
            rec_badge = '<span class="px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800">SKIP</span>'

        # High-score audit flag
        audit_warning = ""
        if score >= 90:
            audit_warning = (
                '<div class="mt-2 px-2 py-1.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700">'
                'Warning: scores above 90% may reflect soft-skill inflation or generic keyword overlap '
                '— verify domain match and required vs preferred qualifications manually.'
                '</div>'
            )

        # Build category bars
        cats_html = ""
        for cat in data.get("categories", []):
            cat_name = cat["category"].replace("_", " ").title()
            cat_score = cat.get("score", 0)
            matched = cat.get("matched", [])
            gaps = cat.get("gaps", [])
            bar_color = "bg-green-500" if cat_score >= 70 else ("bg-yellow-500" if cat_score >= 50 else "bg-red-500")

            matched_tags = " ".join(
                f'<span class="px-1 py-0.5 rounded bg-green-50 text-green-700">{m}</span>'
                for m in matched[:5]
            ) if matched else ""
            gap_tags = " ".join(
                f'<span class="px-1 py-0.5 rounded bg-red-50 text-red-700">{g}</span>'
                for g in gaps[:3]
            ) if gaps else ""

            cats_html += f'''
            <div class="mb-2">
                <div class="flex justify-between text-xs mb-0.5">
                    <span class="text-gray-600">{cat_name} ({cat.get("weight", 0):.0%})</span>
                    <span class="font-medium {score_color}">{cat_score:.0f}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1.5">
                    <div class="h-1.5 rounded-full {bar_color}" style="width: {cat_score}%"></div>
                </div>
                <div class="mt-0.5 flex flex-wrap gap-0.5 text-xs">{matched_tags}{gap_tags}</div>
            </div>'''

        # Critical gaps (clickable to add to user's skills)
        critical = data.get("critical_gaps", [])
        critical_html = ""
        if critical:
            gap_tags = " ".join(
                f'<span class="px-1.5 py-0.5 rounded bg-red-50 text-red-700 cursor-pointer '
                f'hover:bg-green-50 hover:text-green-700 transition-colors" '
                f'title="Click to add to your skills" '
                f'onclick="addSkillFromGap(\'{g}\', this)">{g}</span>'
                for g in critical[:8]
            )
            critical_html = f'''
            <div class="mt-2 pt-2 border-t border-gray-100">
                <span class="text-xs font-medium text-red-600">Critical Gaps:</span>
                <div class="mt-1 flex flex-wrap gap-1 text-xs">{gap_tags}</div>
            </div>'''

        return HTMLResponse(
            f'<div class="rounded-lg border p-3 {bg_color}">'
            f'<div class="flex items-center justify-between mb-2">'
            f'<span class="text-lg font-bold {score_color}">{score:.0f}%</span>'
            f'{rec_badge}'
            f'</div>'
            f'<div class="text-xs text-gray-600 mb-2">{interp}</div>'
            f'{cats_html}'
            f'{audit_warning}'
            f'{critical_html}'
            f'<div class="mt-2 text-xs text-gray-400">'
            f'<a href="/job/{job_id}" class="text-blue-500 hover:underline">Refresh page</a> to see full alignment breakdown in sidebar.'
            f'</div>'
            f'</div>'
        )

    return result.to_dict()


@app.get("/api/response-rates")
async def api_response_rates(days: int = Query(30)):
    """Response rates by platform."""
    return db.get_response_rates(days=days)


@app.get("/api/response-summary")
async def api_response_summary():
    """Overall response tracking summary."""
    return db.get_response_summary()


@app.get("/api/models")
async def api_available_models():
    """List available AI models."""
    models = get_available_models()
    return [
        {"provider": m.provider.value, "model": m.model_name,
         "display_name": m.display_name, "speed": m.speed_rating}
        for m in models
    ]


# ── Status version (incremented on every job status change) ──────

_status_version = 0


@app.get("/api/status-version")
async def status_version():
    return {"version": _status_version}


# ── Server Controls ───────────────────────────────────────────────

_server_started_at = datetime.now()


@app.get("/api/health")
async def health_check():
    """Health check endpoint for restart polling."""
    uptime = datetime.now() - _server_started_at
    return {"status": "ok", "uptime_seconds": uptime.total_seconds()}


@app.post("/api/server/restart")
async def restart_server():
    """Restart the uvicorn server process.

    Spawns a new server process and then exits the current one.
    The new process inherits the same port/host configuration.
    """
    import subprocess

    # Get current server configuration
    port = 8888
    host = "0.0.0.0"

    # Spawn the replacement server process before exiting
    def _do_restart():
        import time as _time
        _time.sleep(0.5)  # Give the response time to flush

        # Start a new server process
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.dashboard.app:app",
             "--host", host, "--port", str(port)],
            cwd=str(Path(__file__).resolve().parent.parent.parent),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            if sys.platform == "win32" else 0,
        )
        _time.sleep(1)

        # Exit current process
        os._exit(0)

    restart_thread = threading.Thread(target=_do_restart, daemon=True)
    restart_thread.start()

    return {"status": "restarting", "message": "Server will restart momentarily"}


# ── Scraping Pipeline ──────────────────────────────────────────────

# Scraping progress tracking (separate from generation progress)
_scraping_progress: dict = {}  # "current" -> {stage, percent, message, updated}
_scraping_lock = threading.Lock()
_scraping_active = False
_scrape_cancel_event = threading.Event()  # signal to stop scraping


def _set_scrape_progress(stage: str, percent: int, message: str):
    with _scraping_lock:
        _scraping_progress["current"] = {
            "stage": stage,
            "percent": percent,
            "message": message,
            "updated": datetime.now().isoformat(),
        }


@app.post("/api/scrape-jobs", response_class=HTMLResponse)
async def trigger_scraping(
    request: Request,
    keywords: str = Form(None),
    location: str = Form(None),
    sites: str = Form(None),
    max_results: int = Form(None),
    posted_days: int = Form(None),
    remote_only: bool = Form(False),
):
    """Trigger a scraping run from the dashboard."""
    global _scraping_active

    # Fall back to saved settings if not provided
    scrape_defaults = _load_scraping_settings()
    if not keywords:
        keywords = scrape_defaults["keywords"]
    if not location:
        location = scrape_defaults["location"]
    if not sites:
        enabled = [s["key"] for s in scrape_defaults["sources"] if s["enabled"]]
        sites = ",".join(enabled) if enabled else "indeed,linkedin"
    if max_results is None:
        max_results = scrape_defaults["max_results"]
    if posted_days is None:
        posted_days = scrape_defaults["posted_days"]

    # Persist the user's choices so they pre-fill next time
    db.set_setting("scrape_default_keywords", keywords.strip())
    db.set_setting("scrape_default_location", location.strip())
    db.set_setting("scrape_default_max_results", str(max_results))
    db.set_setting("scrape_default_posted_days", str(posted_days))
    db.set_setting("scrape_default_remote_only", "true" if remote_only else "false")

    if _scraping_active:
        return HTMLResponse(
            '<div class="text-yellow-600 bg-yellow-50 border border-yellow-200 rounded p-3 text-sm">'
            'A scraping job is already running. Wait for it to finish.</div>'
        )

    from src.dashboard.scraper_runner import ScrapeConfig, ScrapeRunner

    config = ScrapeConfig(
        keywords=keywords.strip(),
        location=location.strip(),
        sites=[s.strip() for s in sites.split(",") if s.strip()],
        max_results=max_results,
        posted_since_days=posted_days,
        remote_only=remote_only,
    )

    def run_in_background():
        global _scraping_active
        _scraping_active = True
        _scrape_cancel_event.clear()
        try:
            runner = ScrapeRunner(db=db, progress_cb=_set_scrape_progress,
                                 cancel_event=_scrape_cancel_event)
            result = runner.run(config)
            # Store final result — don't overwrite if cancelled
            if not _scrape_cancel_event.is_set():
                _set_scrape_progress(
                    "done", 100,
                    f"Done: {result.new_jobs} new jobs, {result.duplicates} duplicates, "
                    f"{result.elapsed_seconds:.0f}s"
                    + (f" | Errors: {', '.join(result.errors)}" if result.errors else ""),
                )
        except Exception as exc:
            logger.error("Scraping failed: %s", exc)
            _set_scrape_progress("error", 0, f"Scraping failed: {exc}")
        finally:
            _scraping_active = False

    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()

    sites_label = ", ".join(config.sites)
    return HTMLResponse(
        f'<div class="text-blue-600 bg-blue-50 border border-blue-200 rounded p-3 text-sm">'
        f'Scraping started: "{config.keywords}" on {sites_label}. '
        f'Watch the progress bar below.</div>'
    )


@app.get("/api/scrape-progress")
async def scrape_progress():
    """SSE endpoint for real-time scraping progress."""

    async def event_stream():
        last_snapshot = ""
        stale = 0
        while True:
            with _scraping_lock:
                progress = _scraping_progress.get("current")

            if progress:
                # Detect any change: percent, stage, OR message
                snapshot = f"{progress.get('percent')}|{progress.get('stage')}|{progress.get('message')}"
                if snapshot != last_snapshot:
                    last_snapshot = snapshot
                    stale = 0
                    yield f"data: {json.dumps(progress)}\n\n"
                    if progress["percent"] >= 100 or progress.get("stage") in ("cancelled",):
                        break
                else:
                    stale += 1
            else:
                stale += 1

            if stale > 3600:  # 30 minutes with no update
                yield f"data: {json.dumps({'stage': 'timeout', 'percent': 0, 'message': 'Scraping timed out'})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/scrape-status")
async def scrape_status():
    """Quick poll endpoint for scraping status (non-SSE)."""
    with _scraping_lock:
        progress = _scraping_progress.get("current")
    return {
        "active": _scraping_active,
        "progress": progress,
    }


@app.post("/api/scrape-cancel")
async def scrape_cancel():
    """Cancel a running scraping job."""
    global _scraping_active
    if not _scraping_active:
        return {"status": "no_job", "message": "No scraping job is running."}
    _scrape_cancel_event.set()
    _set_scrape_progress("cancelled", 0, "Scraping cancelled by user")
    return {"status": "cancelled", "message": "Cancellation signal sent."}


# ── Task Cancel ────────────────────────────────────────────────────

@app.post("/api/task-cancel/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running background task."""
    progress = _get_task_progress(task_id)
    if not progress or progress.get("stage") in (None, "done", "error", "cancelled", ""):
        return {"status": "no_task", "message": f"No active task '{task_id}'."}
    evt = _get_cancel_event(task_id)
    evt.set()
    _set_task_progress(task_id, "cancelled", progress.get("percent", 0),
                       "Cancelled by user.")
    return {"status": "cancelled", "message": f"Cancellation signal sent for '{task_id}'."}


# ── Task Progress SSE ─────────────────────────────────────────────

@app.get("/api/task-progress/{task_id}")
async def task_progress_sse(task_id: str):
    """SSE endpoint for real-time task progress (scoring, enriching, reports)."""
    async def event_stream():
        last_pct = -1
        last_stage = ""
        stale = 0
        while True:
            progress = _get_task_progress(task_id)
            if progress:
                curr_pct = progress.get("percent", 0)
                curr_stage = progress.get("stage", "")
                if curr_pct != last_pct or curr_stage != last_stage:
                    last_pct = curr_pct
                    last_stage = curr_stage
                    stale = 0
                    yield f"data: {json.dumps(progress)}\n\n"
                    if curr_pct >= 100 or curr_stage in ("done", "error"):
                        break
                else:
                    stale += 1
            else:
                stale += 1
            if stale > 600:
                yield f"data: {json.dumps({'task_id': task_id, 'stage': 'timeout', 'percent': 0, 'message': 'Task timed out'})}\n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/task-status/{task_id}")
async def task_status_poll(task_id: str):
    """Quick poll endpoint for task status (non-SSE)."""
    return _get_task_progress(task_id) or {"task_id": task_id, "stage": "idle", "percent": 0, "message": ""}


# ── Report Runners ────────────────────────────────────────────────

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts" / "scheduled_tasks"


def _run_report_script(task_id: str, script_name: str, label: str):
    """Run a Python report script in a subprocess with progress tracking."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        _set_task_progress(task_id, "error", 0, f"Script not found: {script_name}")
        return

    _set_task_progress(task_id, "starting", 5, f"Starting {label}...")
    try:
        python_exe = sys.executable
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        _set_task_progress(task_id, "running", 15, f"Running {label}...")
        process = subprocess.Popen(
            [python_exe, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(script_path.parent.parent.parent),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        output_lines = []
        pct = 15
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                output_lines.append(line)
                # Advance progress based on output
                pct = min(pct + 1, 90)
                # Show last meaningful line
                if len(line) > 5:
                    _set_task_progress(task_id, "running", pct, line[:120])

        returncode = process.wait(timeout=300)
        if returncode == 0:
            last_lines = [l for l in output_lines[-5:] if l]
            summary = last_lines[-1] if last_lines else f"{label} completed."
            _set_task_progress(task_id, "done", 100, summary[:150])
        else:
            err_lines = [l for l in output_lines[-3:] if l]
            err_msg = err_lines[-1] if err_lines else f"Exit code {returncode}"
            _set_task_progress(task_id, "error", 0, f"{label} failed: {err_msg[:120]}")
    except subprocess.TimeoutExpired:
        process.kill()
        _set_task_progress(task_id, "error", 0, f"{label} timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Report runner failed for {script_name}: {e}", exc_info=True)
        _set_task_progress(task_id, "error", 0, f"{label} error: {e}")


@app.post("/api/run-report/{report_name}", response_class=HTMLResponse)
async def run_report(report_name: str):
    """Trigger a report task in the background."""
    reports = {
        "daily-summary": ("daily_summary.py", "Daily Summary Report"),
        "daily-jobspy": ("daily_jobspy_detection.py", "Daily JobSpy Detection"),
        "weekly-intelligence": ("weekly_intelligence_orchestrator.py", "Weekly Intelligence Report"),
        "dashboard-scrape": ("dashboard_scrape_task.py", "Dashboard Scrape Task"),
    }
    if report_name not in reports:
        return HTMLResponse(f'<div class="text-red-600 text-sm">Unknown report: {report_name}</div>')

    task_id = f"report-{report_name}"
    current = _get_task_progress(task_id)
    if current.get("stage") not in (None, "", "done", "error", "idle"):
        return HTMLResponse(f'<div class="text-yellow-600 text-sm">{reports[report_name][1]} is already running...</div>')

    script_name, label = reports[report_name]
    thread = threading.Thread(
        target=_run_report_script,
        args=(task_id, script_name, label),
        daemon=True,
    )
    thread.start()
    return HTMLResponse(f'<div class="text-blue-600 text-sm">{label} started...</div>')


@app.get("/api/reports-status")
async def reports_status():
    """Get status of all report tasks."""
    report_ids = ["report-daily-summary", "report-daily-jobspy",
                  "report-weekly-intelligence", "report-dashboard-scrape"]
    result = {}
    for task_id in report_ids:
        result[task_id] = _get_task_progress(task_id) or {"stage": "idle", "percent": 0, "message": ""}
    return result


# ── Semantic Classification ────────────────────────────────────────

@app.post("/api/classify-jobs", response_class=HTMLResponse)
async def classify_jobs(request: Request):
    """Run semantic classification on all unclassified jobs."""
    task_id = "classify-jobs"
    if _get_task_progress(task_id).get("stage") not in (None, "done", "error", ""):
        return HTMLResponse(
            '<div class="text-yellow-600 text-sm">Classification already running...</div>'
        )

    def run_classification():
        _get_cancel_event(task_id).clear()
        try:
            from src.dashboard.semantic_classifier import SemanticClassifier

            _set_task_progress(task_id, "init", 5, "Checking Ollama availability...")
            classifier = SemanticClassifier()

            if not classifier.is_available():
                _set_task_progress(task_id, "error", 0,
                    f"Ollama not available. Start it with: ollama serve && ollama pull {classifier.model}")
                return

            _set_task_progress(task_id, "loading", 10, "Finding unclassified jobs...")
            with db.get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, title, description FROM jobs "
                    "WHERE is_active = 1 AND (job_category IS NULL OR job_category = '') "
                    "AND description IS NOT NULL AND LENGTH(description) > 50 "
                    "ORDER BY scraped_date DESC LIMIT 500"
                ).fetchall()

            total = len(rows)
            if total == 0:
                _set_task_progress(task_id, "done", 100, "All jobs already classified!")
                return

            classified = 0
            relevant = 0
            for i, row in enumerate(rows):
                _check_task_cancel(task_id)
                result = classifier.classify(row["title"], row["description"])
                with db.get_connection() as conn:
                    conn.execute(
                        "UPDATE jobs SET job_category = ?, category_confidence = ? WHERE id = ?",
                        (result.category, result.confidence, row["id"]),
                    )
                classified += 1
                if result.is_relevant:
                    relevant += 1

                if (i + 1) % 5 == 0 or i == total - 1:
                    pct = 10 + int(85 * (i + 1) / total)
                    _set_task_progress(task_id, "classifying", pct,
                        f"Classified {classified}/{total} — {relevant} relevant, "
                        f"{classified - relevant} filtered")

            _set_task_progress(task_id, "done", 100,
                f"Classified {classified} jobs: {relevant} relevant, "
                f"{classified - relevant} filtered out. Refresh to see results.")

        except TaskCancelled:
            _set_task_progress(task_id, "cancelled", 0, "Classification cancelled by user.")
        except ImportError:
            _set_task_progress(task_id, "error", 0,
                "semantic_classifier.py not found in src/dashboard/")
        except Exception as e:
            logger.error("Classification failed: %s", e, exc_info=True)
            _set_task_progress(task_id, "error", 0, f"Classification failed: {e}")

    thread = threading.Thread(target=run_classification, daemon=True)
    thread.start()
    return HTMLResponse('<div class="text-blue-600 text-sm">Job classification started...</div>')


# ── Main ────────────────────────────────────────────────────────────

def start_dashboard(host: str = "0.0.0.0", port: int = 8888):
    """Start the dashboard server."""
    import uvicorn
    logger.info(f"Starting Job Intelligence Dashboard on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_dashboard()
