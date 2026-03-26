"""
Dashboard Scraper Runner — runs the JobSpy scraping pipeline from the dashboard.

Provides:
  - Configurable search (keywords, location, sites, days)
  - Real-time progress callbacks
  - Deduplication against existing DB
  - Auto-scoring of new jobs
"""

from __future__ import annotations

import asyncio
import logging
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ScrapeConfig:
    """Configuration for a scraping run."""
    keywords: str = "data engineer"
    location: str = "United States"
    sites: List[str] = field(default_factory=lambda: [
        "indeed", "linkedin", "glassdoor", "google", "zip_recruiter",
        "greenhouse", "ashby", "wellfound", "climatebase", "hackernews",
    ])
    max_results: int = 30
    posted_since_days: int = 7
    remote_only: bool = False


@dataclass
class ScrapeResult:
    """Result of a scraping run."""
    total_scraped: int = 0
    new_jobs: int = 0
    duplicates: int = 0
    errors: List[str] = field(default_factory=list)
    elapsed_seconds: float = 0
    jobs_by_source: Dict[str, int] = field(default_factory=dict)


# ── Type alias for progress callbacks ────────────────────────────
# progress_cb(stage: str, percent: int, message: str)
ProgressCallback = Callable[[str, int, str], None]


class ScrapeCancelled(Exception):
    """Raised when the user cancels a scraping run."""
    pass


class ScrapeRunner:
    """Run the full scraping pipeline from the dashboard."""

    def __init__(self, db, progress_cb: Optional[ProgressCallback] = None,
                 cancel_event: Optional[threading.Event] = None):
        """
        Args:
            db: DashboardDB instance (for checking dupes and saving jobs).
            progress_cb: Optional callback(stage, percent, message).
            cancel_event: Optional threading.Event — set to cancel the run.
        """
        self.db = db
        self._progress = progress_cb or (lambda s, p, m: None)
        self._cancel = cancel_event
        self._t0: float = 0.0            # Pipeline start time
        self._stage_t0: float = 0.0      # Current stage start time
        self._last_stage: str = ""       # Track stage transitions

    def _check_cancel(self):
        """Raise ScrapeCancelled if the cancel event is set."""
        if self._cancel and self._cancel.is_set():
            raise ScrapeCancelled("Scraping cancelled by user")

    def _report(self, stage: str, pct: int, msg: str):
        self._check_cancel()
        now = time.time()
        # Track stage transitions to show per-stage elapsed time
        if stage != self._last_stage:
            if self._last_stage and self._stage_t0:
                stage_elapsed = now - self._stage_t0
                logger.info("[scrape] Stage '%s' completed in %.1fs",
                            self._last_stage, stage_elapsed)
            self._stage_t0 = now
            self._last_stage = stage
        # Add elapsed time to message for UI
        elapsed = now - self._t0 if self._t0 else 0
        timed_msg = f"[{elapsed:.0f}s] {msg}"
        self._progress(stage, pct, timed_msg)
        logger.info("[scrape %d%% %.0fs] %s: %s", pct, elapsed, stage, msg)

    def run(self, config: ScrapeConfig) -> ScrapeResult:
        """Run scraping synchronously (call from a background thread)."""
        t0 = time.time()
        self._t0 = t0
        self._stage_t0 = t0
        self._last_stage = ""
        result = ScrapeResult()

        # Start pipeline metrics tracking (CPU/RAM monitoring)
        run_tracker = None
        try:
            from src.dashboard.pipeline_metrics import PipelineRunTracker
            run_tracker = PipelineRunTracker(self.db, run_type="scrape")
            run_tracker.start()
        except Exception as e:
            logger.debug("Pipeline metrics tracking unavailable: %s", e)

        try:
            return self._run_pipeline(config, result, t0, run_tracker)
        except ScrapeCancelled:
            result.elapsed_seconds = time.time() - t0
            result.errors.append("Cancelled by user")
            self._progress("cancelled", 0,
                           f"Cancelled after {result.elapsed_seconds:.0f}s "
                           f"({result.new_jobs} new jobs saved so far)")
            if run_tracker:
                try:
                    run_tracker.finish(summary={
                        "total_scraped": result.total_scraped,
                        "new_jobs": result.new_jobs,
                        "duplicates": result.duplicates,
                        "scored": 0,
                        "sources": result.jobs_by_source,
                        "errors": len(result.errors),
                        "cancelled": True,
                    })
                except Exception:
                    pass
            return result

    def _run_pipeline(self, config, result, t0, run_tracker):
        """Internal pipeline — separated so ScrapeCancelled can be caught."""

        # ── Classify sites into JobSpy vs niche scrapers ──────────
        JOBSPY_SITES = {"indeed", "linkedin", "glassdoor", "google", "zip_recruiter"}
        NICHE_SITES = {"greenhouse", "ashby", "wellfound", "climatebase", "hackernews"}

        jobspy_sites = [s for s in config.sites if s in JOBSPY_SITES]
        niche_sites = [s for s in config.sites if s in NICHE_SITES]
        total_sites = len(jobspy_sites) + len(niche_sites)

        # ── Step 1: Initialize JobSpy (if any JobSpy sites selected) ─
        scrape_jobs = None
        if jobspy_sites:
            self._report("init", 5, "Initializing JobSpy scraper...")
            try:
                from jobspy import scrape_jobs
            except ImportError:
                result.errors.append("python-jobspy not installed (pip install python-jobspy)")
                self._report("init", 5, "JobSpy not available — skipping aggregator sites")
                jobspy_sites = []

        # ── Step 2a: Scrape JobSpy sites ─────────────────────────────
        all_jobs = []
        site_idx = 0

        for i, site in enumerate(jobspy_sites):
            pct = 10 + int(60 * site_idx / max(total_sites, 1))
            site_idx += 1
            self._report("scraping", pct, f"Scraping {site}... ({site_idx}/{total_sites})")

            try:
                scrape_kwargs = {
                    "site_name": [site],
                    "search_term": config.keywords,
                    "location": config.location,
                    "results_wanted": config.max_results,
                    "hours_old": config.posted_since_days * 24,
                    "country_indeed": "USA",
                }
                if config.remote_only:
                    scrape_kwargs["is_remote"] = True
                df = scrape_jobs(**scrape_kwargs)
                if df is not None and not df.empty:
                    jobs = self._dataframe_to_dicts(df, site)
                    all_jobs.extend(jobs)
                    result.jobs_by_source[site] = len(jobs)
                    self._report(
                        "scraping", pct + 5,
                        f"{site}: found {len(jobs)} jobs",
                    )
                else:
                    result.jobs_by_source[site] = 0
                    self._report("scraping", pct + 5, f"{site}: no results")
            except Exception as exc:
                err = f"{site}: {exc}"
                result.errors.append(err)
                logger.warning("Scrape error for %s: %s", site, exc)
                self._report("scraping", pct + 5, f"{site}: error — {exc}")

        # ── Step 2b: Scrape niche sources (custom scrapers) ──────────
        for site in niche_sites:
            pct = 10 + int(60 * site_idx / max(total_sites, 1))
            site_idx += 1
            self._report("scraping", pct, f"Scraping {site}... ({site_idx}/{total_sites})")

            try:
                niche_jobs = self._scrape_niche_source(site)
                if niche_jobs:
                    # Pre-filter niche results by search keywords to remove
                    # irrelevant jobs (e.g. "Marketing Manager" when searching
                    # for "data engineer"). Saves ~20s/job in scoring later.
                    raw_count = len(niche_jobs)
                    niche_jobs = self._filter_niche_jobs_by_keywords(
                        niche_jobs, config.keywords
                    )
                    filtered_out = raw_count - len(niche_jobs)
                    all_jobs.extend(niche_jobs)
                    result.jobs_by_source[site] = len(niche_jobs)
                    filter_msg = f" ({filtered_out} irrelevant filtered)" if filtered_out else ""
                    self._report(
                        "scraping", pct + 5,
                        f"{site}: {len(niche_jobs)} relevant jobs{filter_msg}",
                    )
                else:
                    result.jobs_by_source[site] = 0
                    self._report("scraping", pct + 5, f"{site}: no results")
            except Exception as exc:
                err = f"{site}: {exc}"
                result.errors.append(err)
                logger.warning("Scrape error for %s: %s", site, exc)
                self._report("scraping", pct + 5, f"{site}: error — {exc}")

        result.total_scraped = len(all_jobs)
        if run_tracker:
            run_tracker.record_step("scraping", items_processed=len(all_jobs))
        if not all_jobs:
            self._report("done", 100, "No jobs found across any source.")
            result.elapsed_seconds = time.time() - t0
            if run_tracker:
                run_tracker.finish(summary={"total_scraped": 0, "new_jobs": 0})
            return result

        # ── Step 3: Deduplicate against DB ─────────────────────────
        self._report("dedup", 75, f"Deduplicating {len(all_jobs)} jobs...")
        new_jobs = self._deduplicate(all_jobs)
        result.new_jobs = len(new_jobs)
        result.duplicates = result.total_scraped - result.new_jobs
        self._report(
            "dedup", 80,
            f"{result.new_jobs} new, {result.duplicates} duplicates skipped",
        )
        if run_tracker:
            run_tracker.record_step("dedup", items_processed=len(new_jobs))

        # ── Step 4: Save new jobs to DB ────────────────────────────
        if new_jobs:
            self._report("saving", 82, f"Saving {len(new_jobs)} new jobs...")
            saved = self._save_jobs(new_jobs)
            self._report("saving", 84, f"Saved {saved} jobs to database")

        # ── Step 4.1: Keyword/gate screening ──────────────────────
        if new_jobs:
            self._report("screening", 85, f"Screening {len(new_jobs)} jobs through 12-gate pipeline...")
            passed_jobs, rejected_jobs = self._screen_scraped_jobs(new_jobs)
            self._report(
                "screening", 88,
                f"Screening complete: {len(passed_jobs)} passed, {len(rejected_jobs)} rejected",
            )
            if run_tracker:
                run_tracker.record_step("screening", items_processed=len(passed_jobs))

        # ── Step 4.5: Semantic classification (pre-filter) ────────
        if new_jobs:
            self._report("classifying", 89, f"Classifying {len(new_jobs)} jobs...")
            classified = self._classify_new_jobs(new_jobs)
            self._report("classifying", 91, f"Classified {classified} jobs")
            if run_tracker:
                run_tracker.record_step("classifying", items_processed=classified)

        # ── Step 5: Auto-score if resume available ─────────────────
        resume = self.db.get_setting("resume_text", "")
        scored = 0
        if resume and new_jobs:
            self._report("scoring", 92, "Scoring new jobs...")
            scored = self._score_new_jobs(resume)
            self._report("scoring", 98, f"Scored {scored} new jobs")
        else:
            self._report("scoring", 98, "Skipped scoring (no resume)")
        if run_tracker:
            run_tracker.record_step("scoring", items_processed=scored)

        # ── Done ───────────────────────────────────────────────────
        result.elapsed_seconds = time.time() - t0
        self._report(
            "done", 100,
            f"Complete: {result.new_jobs} new jobs in {result.elapsed_seconds:.1f}s",
        )

        # Finalize pipeline metrics
        if run_tracker:
            try:
                run_tracker.finish(summary={
                    "total_scraped": result.total_scraped,
                    "new_jobs": result.new_jobs,
                    "duplicates": result.duplicates,
                    "scored": scored,
                    "sources": result.jobs_by_source,
                    "errors": len(result.errors),
                })
            except Exception as e:
                logger.debug("Failed to finalize pipeline metrics: %s", e)

        return result

    # ── Niche job keyword relevance filter ────────────────────────
    @staticmethod
    def _filter_niche_jobs_by_keywords(jobs: List[Dict[str, Any]], keywords: str) -> List[Dict[str, Any]]:
        """Filter niche scraper results by search keywords.

        Niche scrapers (Greenhouse, Ashby) return ALL jobs from curated
        companies — many are irrelevant (e.g. "Marketing Manager" when
        searching for "data engineer"). This filter keeps only jobs whose
        title or description contains at least one search keyword.

        This prevents hundreds of irrelevant jobs from being scored
        (each scoring costs ~20s for semantic embedding).
        """
        if not keywords or not jobs:
            return jobs

        # Split search query into individual terms and normalize
        search_terms = [t.strip().lower() for t in keywords.split() if len(t.strip()) >= 2]
        if not search_terms:
            return jobs

        # Also create bigrams for multi-word searches like "data engineer"
        bigrams = []
        words = keywords.lower().split()
        for i in range(len(words) - 1):
            bigrams.append(f"{words[i]} {words[i+1]}")

        filtered = []
        for job in jobs:
            title = (job.get("title") or "").lower()
            desc = (job.get("description") or "").lower()[:1000]  # Only check first 1000 chars
            text = f"{title} {desc}"

            # Check if any search term or bigram appears in the job
            if any(term in text for term in search_terms) or \
               any(bg in text for bg in bigrams):
                filtered.append(job)

        removed = len(jobs) - len(filtered)
        if removed > 0:
            logger.info(
                "Niche keyword filter: kept %d/%d jobs (removed %d irrelevant for '%s')",
                len(filtered), len(jobs), removed, keywords,
            )
        return filtered

    # ── Private helpers ────────────────────────────────────────────

    def _scrape_niche_source(self, site: str) -> List[Dict[str, Any]]:
        """Run a niche (non-JobSpy) scraper and return list of job dicts.

        Each niche scraper returns List[JobListing] objects from
        src.intelligence.models. We call .to_dict() to normalize them
        into the same format used by _dataframe_to_dicts().
        """
        jobs: List = []

        if site == "greenhouse":
            from src.intelligence.greenhouse_scraper import scrape_greenhouse_jobs
            listings = scrape_greenhouse_jobs()
            jobs = [j.to_dict() for j in listings]

        elif site == "ashby":
            from src.intelligence.ashby_scraper import scrape_ashby_jobs
            listings = scrape_ashby_jobs()
            jobs = [j.to_dict() for j in listings]

        elif site == "wellfound":
            from src.intelligence.wellfound_scraper import scrape_wellfound_jobs
            listings = scrape_wellfound_jobs()
            jobs = [j.to_dict() for j in listings]

        elif site == "climatebase":
            from src.intelligence.climatebase_scraper import scrape_climatebase_jobs
            listings = scrape_climatebase_jobs()
            jobs = [j.to_dict() for j in listings]

        elif site == "hackernews":
            from src.intelligence.hn_scraper import scrape_hn_jobs
            listings = scrape_hn_jobs(months_back=2, min_description_length=80)
            jobs = [j.to_dict() for j in listings]

        else:
            logger.warning("Unknown niche source: %s", site)
            return []

        logger.info("Niche scraper '%s' returned %d jobs", site, len(jobs))
        return jobs

    def _dataframe_to_dicts(self, df, source_site: str) -> List[Dict[str, Any]]:
        """Convert a JobSpy DataFrame to list of dicts for our DB."""
        import pandas as pd

        jobs = []
        for _, row in df.iterrows():
            job_url = str(row.get("job_url", "") or "")
            if not job_url or job_url == "nan":
                continue

            title = str(row.get("title", "") or "")
            company = str(row.get("company_name", "") or row.get("company", "") or "")
            if not title or not company:
                continue

            # Parse salary
            salary_min = None
            salary_max = None
            try:
                sal_min = row.get("min_amount")
                sal_max = row.get("max_amount")
                if pd.notna(sal_min):
                    salary_min = float(sal_min)
                if pd.notna(sal_max):
                    salary_max = float(sal_max)
            except (ValueError, TypeError):
                pass

            # Remote type
            remote_raw = str(row.get("is_remote", "") or "").lower()
            if remote_raw in ("true", "1", "yes"):
                remote_type = "remote"
            else:
                loc = str(row.get("location", "") or "").lower()
                if "remote" in loc:
                    remote_type = "remote"
                elif "hybrid" in loc:
                    remote_type = "hybrid"
                else:
                    remote_type = "on_site"

            # Description
            desc = str(row.get("description", "") or "")
            if desc == "nan":
                desc = ""

            # Posted date
            posted_date = None
            try:
                pd_val = row.get("date_posted")
                if pd.notna(pd_val):
                    posted_date = str(pd_val)
            except Exception:
                pass

            jobs.append({
                "job_url": job_url,
                "job_id": str(row.get("id", "") or ""),
                "title": title,
                "company": company,
                "location": str(row.get("location", "") or ""),
                "description": desc,
                "job_type": str(row.get("job_type", "") or "") or None,
                "remote_type": remote_type,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_currency": "USD",
                "salary_period": str(row.get("salary_period", "yearly") or "yearly"),
                "posted_date": posted_date,
                "source_site": source_site,
                "company_url": str(row.get("company_url", "") or "") or None,
                "company_industry": str(row.get("company_industry", "") or "") or None,
                "company_num_employees": str(row.get("company_num_employees", "") or "") or None,
                "company_staff_count": None,
                "company_rating": float(row.get("company_rating")) if pd.notna(row.get("company_rating")) else None,
                "company_reviews_count": int(row.get("company_reviews_count")) if pd.notna(row.get("company_reviews_count")) else None,
                "applicant_count": None,
                "hiring_manager_name": None,
                "hiring_manager_title": None,
                "hiring_manager_url": None,
                "listed_at_ms": None,
                "original_listed_at_ms": None,
            })

        return jobs

    def _deduplicate(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove jobs already in the database (by job_url)."""
        from src.intelligence.job_database import JobDatabase

        job_db = JobDatabase(str(self.db.db_path))

        new = []
        for job in jobs:
            url = job.get("job_url", "")
            if not url:
                continue
            with job_db.get_connection() as conn:
                row = conn.execute(
                    "SELECT id FROM jobs WHERE job_url = ?", (url,)
                ).fetchone()
            if not row:
                new.append(job)
        return new

    def _save_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """Save jobs into job_tracker.db using JobDatabase."""
        from src.intelligence.job_database import JobDatabase

        job_db = JobDatabase(str(self.db.db_path))
        saved = 0
        for job in jobs:
            try:
                job_db.save_job(job)
                saved += 1
            except Exception as exc:
                logger.warning("Failed to save job %s: %s", job.get("title"), exc)
        return saved

    def _build_pipeline_config(self):
        """
        Build a pipeline config namespace from dashboard settings.
        Falls back to safe defaults if settings are unavailable.
        """
        import types
        try:
            def _b(key, default="true"):
                return getattr(self, 'db', None) and \
                       self.db.get_setting(key, default) == "true" or default == "true"

            hard_floor = 130_000
            soft_floor = 140_000
            min_align  = 60
            remote_mode = "remote_preferred"
            aws_ethical = True

            if hasattr(self, 'db'):
                try:
                    hard_floor  = int(self.db.get_setting("filter_salary_hard_floor",  "130000"))
                    soft_floor  = int(self.db.get_setting("filter_salary_soft_floor",  "140000"))
                    min_align   = int(self.db.get_setting("filter_min_llm_alignment",  "60"))
                    remote_mode = self.db.get_setting("filter_remote_mode", "remote_preferred")
                    aws_ethical = self.db.get_setting("filter_aws_ethical", "true") == "true"
                except (ValueError, TypeError):
                    pass

            def gate(key):
                if not hasattr(self, 'db'):
                    return True
                return self.db.get_setting(key, "true") == "true"

            return types.SimpleNamespace(
                enable_gate_0a       = gate("pipeline_gate_0a"),
                enable_gate_0b       = gate("pipeline_gate_0b"),
                enable_gate_0c       = gate("pipeline_gate_0c"),
                enable_gate_0d       = gate("pipeline_gate_0d"),
                enable_gate_0e       = gate("pipeline_gate_0e"),
                enable_gate_0f       = gate("pipeline_gate_0f"),
                enable_gate_0g       = gate("pipeline_gate_0g"),
                enable_gate_0h       = gate("pipeline_gate_0h"),
                enable_gate_0i       = gate("pipeline_gate_0i"),
                enable_gate_0j       = gate("pipeline_gate_0j"),
                enable_gate_culture  = gate("pipeline_gate_culture"),
                salary_hard_floor    = hard_floor,
                salary_soft_floor    = soft_floor,
                require_remote       = remote_mode != "any",
                aws_ethical_exclusion= aws_ethical,
                min_alignment        = min_align,
            )
        except Exception as exc:
            logger.warning("Could not build pipeline config from settings: %s — using defaults", exc)
            import types
            return types.SimpleNamespace()

    def _screen_scraped_jobs(self, jobs: list) -> tuple:
        """
        Run scraped jobs through the keyword + gate screening pipeline.
        Returns (passed_jobs, rejected_jobs).
        Non-critical — if screening fails, all jobs pass through.
        """
        try:
            import asyncio
            from src.screening import get_screening_pipeline, reset_screening_pipeline

            config = self._build_pipeline_config()
            with_resolver = (
                hasattr(self, 'db') and
                self.db.get_setting("pipeline_llm_resolver", "false") == "true"
            )

            reset_screening_pipeline()
            pipeline = get_screening_pipeline(config=config, with_resolver=with_resolver)
            if with_resolver:
                logger.info("LLM Override Resolver ENABLED for this scrape run")

            passed, rejected = [], []
            total = len(jobs)
            for idx, job in enumerate(jobs):
                job_label = f"{job.get('company', '?')[:20]} - {job.get('title', '?')[:30]}"
                try:
                    loop = asyncio.new_event_loop()
                    result = loop.run_until_complete(pipeline.screen_job(job))
                    loop.close()
                    if result.passed:
                        passed.append(job)
                    else:
                        rejected.append(job)
                        # Tag the rejection reason in the DB if possible
                        try:
                            from src.screening.models import GateResult as _GR
                            first_fail = next(
                                (v for v in result.verdicts
                                 if v.result in (_GR.FAIL, _GR.OVERRIDE_REQUIRED)),
                                None
                            )
                            if first_fail and hasattr(self, 'db'):
                                from src.intelligence.job_database import JobDatabase
                                job_db = JobDatabase(str(self.db.db_path))
                                job_db.update_job_field(
                                    job.get('id') or job.get('job_url'),
                                    'screening_status',
                                    f'REJECTED:{first_fail.gate_name}:{first_fail.reason[:100]}'
                                )
                        except Exception:
                            pass
                except Exception:
                    passed.append(job)
                # Report per-job screening progress
                if (idx + 1) % 3 == 0 or idx == total - 1:
                    pct = 85 + int(3 * (idx + 1) / max(total, 1))
                    self._report(
                        "screening", pct,
                        f"Screening ({idx + 1}/{total}): {job_label} "
                        f"[{len(passed)} pass, {len(rejected)} reject]",
                    )
            logger.info(
                "Screening: %d passed, %d rejected out of %d jobs",
                len(passed), len(rejected), len(jobs)
            )
            return passed, rejected
        except Exception as exc:
            logger.warning("Screening pipeline failed (non-critical), all jobs pass: %s", exc)
            return jobs, []

    def _classify_new_jobs(self, jobs: list) -> int:
        """Run job classification on newly saved jobs.

        Always runs the instant keyword classifier (regex-based).
        If pipeline_llm_classifier_enabled is true, upgrades each result
        using the LLM model specified in pipeline_classifier_model.
        """
        try:
            from src.dashboard.semantic_classifier import SemanticClassifier
        except ImportError:
            logger.debug("semantic_classifier not available")
            return 0

        # Check if LLM upgrade is enabled
        llm_enabled = self.db.get_setting("pipeline_llm_classifier_enabled", "false") == "true"
        classifier_model_setting = self.db.get_setting("pipeline_classifier_model", "ollama:llama3.1:8b")

        classifier = None
        if llm_enabled:
            # Parse model setting (format: "provider:model_name")
            if ":" in classifier_model_setting:
                provider, model_name = classifier_model_setting.split(":", 1)
            else:
                provider, model_name = "ollama", classifier_model_setting

            classifier = SemanticClassifier(
                model=model_name,
                claude_model=model_name if provider == "claude" else "claude-3-haiku-20240307",
                claude_fallback=(provider == "claude"),
            )
            logger.info("LLM classifier enabled (%s:%s) — will upgrade keyword results", provider, model_name)
        else:
            # Need a classifier instance for classify_keyword()
            classifier = SemanticClassifier()
            logger.info("Keyword-only classification (LLM upgrade disabled)")

        try:
            classified = 0
            total = len(jobs)
            for idx, job in enumerate(jobs):
                title = job.get("title", "")
                desc = job.get("description", "")
                job_label = f"{job.get('company', '?')[:20]} - {title[:30]}"

                # Step 1: Always run keyword classifier (instant)
                result = classifier.classify_keyword(title, desc)

                # Step 2: If LLM enabled, upgrade with LLM classification
                if llm_enabled:
                    try:
                        llm_result = classifier.classify(title, desc)
                        result = llm_result  # LLM result overrides keyword
                    except Exception as e:
                        logger.warning("LLM classification failed for '%s', keeping keyword result: %s", title, e)

                # Store classification in DB
                try:
                    with self.db.get_connection() as conn:
                        conn.execute(
                            "UPDATE jobs SET job_category = ?, category_confidence = ? "
                            "WHERE job_url = ?",
                            (result.category, result.confidence, job.get("job_url")),
                        )
                    classified += 1
                except Exception:
                    pass  # Column may not exist yet

                # Report per-job classification progress
                if (idx + 1) % 3 == 0 or idx == total - 1:
                    pct = 89 + int(2 * (idx + 1) / max(total, 1))
                    self._report(
                        "classifying", pct,
                        f"Classifying ({idx + 1}/{total}): {job_label} -> {result.category}",
                    )
            return classified
        except Exception as e:
            logger.warning("Classification step failed: %s", e)
            return 0

    def _score_new_jobs(self, resume_text: str) -> int:
        """Score unscored jobs using batch-optimized alignment scorer.

        Two-phase approach for ~100x speedup on semantic scoring:
          Phase 1: Keyword scoring (fast, ~5ms/job) — runs individually
          Phase 2: Batch semantic embedding (one model.encode() call for all eligible jobs)
        """
        try:
            from src.dashboard.scoring import AlignmentScorer

            scorer = AlignmentScorer()
            scorer.set_resume(resume_text)

            unscored = self.db.get_unscored_jobs(days=30, limit=500)
            total = len(unscored)
            if total == 0:
                self._report("scoring", 98, "No unscored jobs to process")
                return 0

            # ── Phase 1: Keyword scoring (fast) ───────────────────────
            self._report("scoring", 92, f"Phase 1: Keyword scoring {total} jobs...")
            keyword_results = []
            descriptions = []
            titles = []
            valid_jobs = []

            for i, job in enumerate(unscored):
                desc = job.get("description", "")
                title = job.get("title", "")
                if not desc or len(desc) < 50:
                    continue

                try:
                    result = scorer.score_keyword_only(desc, title)
                    keyword_results.append(result)
                    descriptions.append(desc)
                    titles.append(title)
                    valid_jobs.append(job)
                except Exception as e:
                    logger.warning("Keyword scoring failed for job %s: %s", job.get("id"), e)

                # Progress for keyword phase (92-95%)
                if (i + 1) % 10 == 0 or i == total - 1:
                    pct = 92 + int(3 * (i + 1) / max(total, 1))
                    self._report(
                        "scoring", pct,
                        f"Keyword scoring ({i + 1}/{total})...",
                    )

            if not valid_jobs:
                self._report("scoring", 98, "No valid jobs to score")
                return 0

            # ── Phase 2: Batch semantic embedding ─────────────────────
            self._report("scoring", 95,
                         f"Phase 2: Batch semantic embedding {len(valid_jobs)} jobs...")
            try:
                sem_applied = scorer.apply_batch_semantic(
                    keyword_results, descriptions, titles, keyword_threshold=25.0
                )
                self._report("scoring", 97,
                             f"Semantic scores applied to {sem_applied}/{len(valid_jobs)} jobs")
            except Exception as e:
                logger.warning("Batch semantic scoring failed (non-critical): %s", e)

            # ── Phase 3: Save all results to DB ──────────────────────
            scored = 0
            for i, (job, result) in enumerate(zip(valid_jobs, keyword_results)):
                job_label = f"{job.get('company', '?')[:20]} - {job.get('title', '?')[:30]}"
                try:
                    self.db.update_alignment_score(
                        job["id"],
                        result.overall_score,
                        result.to_dict(),
                        semantic_score=result.semantic_score,
                    )
                    scored += 1
                except Exception:
                    pass
                # Progress for save phase (97-98%)
                if (i + 1) % 20 == 0 or i == len(valid_jobs) - 1:
                    pct = 97 + int(1 * (i + 1) / max(len(valid_jobs), 1))
                    self._report(
                        "scoring", pct,
                        f"Saved ({i + 1}/{len(valid_jobs)}): {job_label} -> {result.overall_score:.0f}pts",
                    )

            return scored
        except Exception as exc:
            logger.warning("Scoring failed: %s", exc)
            return 0
