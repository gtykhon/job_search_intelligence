"""
Layer 1 — GenerationContext builder.
Reads pre-computed pipeline data from job_tracker.db and constructs a
constrained context object for ai_generator.py.

All data used here was computed during the screening/scoring/enrichment
pipeline. This module does NOT make new API calls.

v2 changes:
  - VERSION_MAP: added data_analyst, business_analyst, architecture_leadership
  - build_generation_context(): fixed set arithmetic for user_removed_skills

Adapted to actual DB schema:
  - llm_skill_cache uses content_hash (not job_id) — we search by matching hash
  - dashboard_settings table (not settings)
  - AlignmentScorer.score() takes (job_description, job_title) — not resume_text
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.generation.tier3_blocklist import filter_claimable, TIER_3_NEVER_CLAIM

logger = logging.getLogger(__name__)

ACHIEVEMENT_BANK_PATH = Path(__file__).parent.parent.parent / "config" / "achievement_bank.json"

# Maps job_category (from semantic_classifier.py) to resume version ID.
# Resume version IDs correspond to versions in RESUME_VERSION_DATABASE.md
#
# v2 FIX: added data_analyst → RV-002, business_analyst → RV-004,
# architecture_leadership → RV-003.
# In v1, data_analyst fell through to "other" → RV-001 (wrong track).
VERSION_MAP: dict[str, str] = {
    # ── Actual SemanticClassifier output categories ───────────────────
    "software_data_engineering":         "RV-001",   # Engineering track (most common)
    "data_analysis_business_analysis":   "RV-002",   # Analytics track
    "analytics_engineering":             "RV-002",   # Analytics track (dbt-focused)
    "physical_infrastructure":           "RV-001",   # Default (shouldn't generate for these)
    "sales_marketing":                   "RV-001",   # Default
    "legal_finance_hr":                  "RV-001",   # Default
    "research_science":                  "RV-001",   # Engineering track (closest match)
    "security_operations":               "RV-001",   # Default
    "product_design":                    "RV-001",   # Default
    "executive_management":              "RV-003",   # Architecture Leadership track
    # ── Legacy / manual override categories ───────────────────────────
    "data_engineer":                     "RV-001",   # Engineering track
    "ml_engineer":                       "RV-001",   # Engineering track
    "software_engineer":                 "RV-001",   # Engineering track
    "devops":                            "RV-001",   # Engineering track
    "data_analyst":                      "RV-002",   # Analyst track
    "business_analyst":                  "RV-004",   # BSA track
    "architecture_leadership":           "RV-003",   # Architecture Leadership
    "other":                             "RV-001",   # Default to engineering
    "unknown":                           "RV-001",   # Unclassified — default
}

# Default thresholds — overridden at runtime by dashboard_settings if available.
MIN_SCORE_TO_GENERATE: float = 65.0
ACHIEVEMENT_TOP_N: int = 4
ACHIEVEMENT_COVERAGE_MIN: int = 65
TOOL_OVERLAP_BOOST: int = 5


def _load_gen_thresholds(db=None) -> dict:
    """Load generation thresholds from dashboard_settings, falling back to defaults."""
    defaults = {
        "min_score_to_generate": MIN_SCORE_TO_GENERATE,
        "achievement_top_n": ACHIEVEMENT_TOP_N,
        "achievement_coverage_min": ACHIEVEMENT_COVERAGE_MIN,
        "tool_overlap_boost": TOOL_OVERLAP_BOOST,
    }
    if db is None:
        return defaults
    try:
        return {
            "min_score_to_generate": float(db.get_setting("gen_min_score_to_generate", str(int(MIN_SCORE_TO_GENERATE)))),
            "achievement_top_n": int(db.get_setting("gen_achievement_top_n", str(ACHIEVEMENT_TOP_N))),
            "achievement_coverage_min": int(db.get_setting("gen_achievement_coverage_min", str(ACHIEVEMENT_COVERAGE_MIN))),
            "tool_overlap_boost": int(db.get_setting("gen_tool_overlap_boost", str(TOOL_OVERLAP_BOOST))),
        }
    except Exception as e:
        logger.warning(f"Failed to load gen thresholds from DB: {e}")
        return defaults


@dataclass
class GenerationContext:
    """
    All data the AI generator needs — and the hard constraints it must respect.
    Nothing outside this object may appear in the generated resume.
    """
    # Job metadata
    job_id: int
    job_title: str
    company: str
    job_category: str           # from semantic_classifier.py
    alignment_score: float      # from AlignmentScorer (0-100)

    # Resume routing
    base_resume_version: str    # e.g. "RV-001"
    base_resume_text: str       # Full text of the base resume for this version

    # Tool constraints — hard boundaries for LLM
    verified_tools_for_job: list[str]     # Tier 1 + Tier 2 tools that matched JD
    blocked_tools_in_jd: list[str]        # Tier 3 tools found in JD — LLM must NOT include
    user_added_skills: list[str]          # User manually added via dashboard skill mgmt
    user_removed_skills: list[str]        # User manually excluded via dashboard

    # Achievement selection — LLM must only draw from these
    selected_achievements: list[dict]     # Ordered by coverage for this job_category

    # JD data
    jd_keywords: list[str]               # Keywords to mirror in language
    jd_summary: str                       # LLM-generated summary (from llm_summarizer.py if available)
    gap_flags: list[str]                  # Tier 3 tools the JD requires — acknowledge gap, don't fabricate

    # Fields with defaults must come after fields without defaults
    jd_full_text: str = ""                # v2: Full JD text for score delta validation
    requires_human_review: bool = False   # Set True if gap_flags non-empty or score < threshold
    cover_letter_instructions: dict = field(default_factory=dict)


def load_achievement_bank() -> dict:
    """Load and parse config/achievement_bank.json."""
    if not ACHIEVEMENT_BANK_PATH.exists():
        raise FileNotFoundError(
            f"Achievement bank not found at {ACHIEVEMENT_BANK_PATH}. "
            "Create config/achievement_bank.json per RESUME_GENERATION_PIPELINE_SPEC.md Task 1."
        )
    with open(ACHIEVEMENT_BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def select_achievements_by_coverage(
    job_category: str,
    verified_tools_in_jd: list[str],
    top_n: int = 4,
    coverage_min: int = 65,
    overlap_boost: int = 5,
) -> list[dict]:
    """
    Select the top N achievements from the bank ordered by coverage for this job_category.

    Selection logic:
    1. Filter to achievements with coverage[job_category] >= coverage_min
    2. Boost score by +overlap_boost for each verified_tool overlap
    3. Sort descending by boosted score
    4. Return top_n
    """
    bank = load_achievement_bank()
    blocked_ids = {b["id"] for b in bank.get("blocked_achievements", [])}

    scored = []
    for achievement in bank["achievements"]:
        if achievement["id"] in blocked_ids:
            continue

        base_coverage = achievement.get("coverage", {}).get(job_category, 0)
        if base_coverage < coverage_min:
            continue

        # Tool overlap boost
        achievement_tools = set(achievement.get("verified_tools", []))
        jd_tools_set = set(t.lower() for t in verified_tools_in_jd)
        overlap = len(achievement_tools & jd_tools_set)
        boosted_score = base_coverage + (overlap * overlap_boost)

        scored.append((boosted_score, achievement))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:top_n]]


def get_user_skill_overrides(db) -> tuple[list[str], list[str]]:
    """
    Fetch user_added_skills and user_removed_skills from dashboard_settings.
    These are set interactively via the job detail skill management UI.

    Uses DashboardDB.get_setting() which reads from dashboard_settings table.
    """
    try:
        added_raw = db.get_setting("user_added_skills", "[]")
        removed_raw = db.get_setting("user_removed_skills", "[]")

        added = json.loads(added_raw) if added_raw else []
        removed = json.loads(removed_raw) if removed_raw else []
        return added, removed
    except Exception as e:
        logger.warning(f"Skill override lookup failed: {e}")
        return [], []


def _get_matched_keywords_from_alignment(db, job_id: int) -> list[str]:
    """
    Extract matched keywords from alignment_details JSON stored for this job.
    Falls back to empty list if not available.
    """
    try:
        with db.get_connection() as conn:
            row = conn.execute(
                "SELECT alignment_details FROM jobs WHERE id = ?",
                (job_id,)
            ).fetchone()
            if row and row["alignment_details"]:
                details = json.loads(row["alignment_details"])
                # alignment_details stores category scores with matched_items
                matched = []
                if isinstance(details, dict):
                    for cat in details.get("categories", []):
                        matched.extend(cat.get("matched", []))
                return matched
    except Exception as e:
        logger.warning(f"Failed to extract matched keywords for job {job_id}: {e}")
    return []


def build_generation_context(db, job_id: int, resume_text: str) -> GenerationContext:
    """
    Main entry point for Layer 1.

    Reads all pre-computed pipeline data for the job and constructs a
    GenerationContext with hard tool constraints and pre-selected achievements.

    Args:
        db: DashboardDB instance (from src/dashboard/db.py)
        job_id: ID from jobs table
        resume_text: Full text of the canonical base resume (from settings)

    Returns:
        GenerationContext ready to pass into constrained_generate()

    Raises:
        ValueError: If job not found
    """
    # 1. Load job row — all pre-computed data
    job = db.get_job(job_id)

    if not job:
        raise ValueError(f"Job {job_id} not found in database.")

    alignment_score = job.get("alignment_score") or 0.0
    job_category = job.get("job_category") or "other"

    # 2. Route to base resume version
    base_version = VERSION_MAP.get(job_category, "RV-001")

    # 3. Get tool/skill data from alignment details or llm_skill_cache
    # Try alignment_details first (always available after scoring)
    all_jd_tools = _get_matched_keywords_from_alignment(db, job_id)
    if all_jd_tools:
        logger.info(f"Job {job_id}: using alignment_details ({len(all_jd_tools)} tools)")
    else:
        # Fallback: try to extract skills from description using basic keyword matching
        from src.dashboard.scoring import TECH_KEYWORDS, JD_TECH_KEYWORDS, _keyword_in_text
        description = (job.get("description") or "").lower()
        all_jd_tools = [kw for kw in JD_TECH_KEYWORDS if _keyword_in_text(kw, description)]
        logger.info(f"Job {job_id}: alignment_details empty, extracted {len(all_jd_tools)} tools from JD")

    # 4. Apply user overrides from interactive dashboard
    user_added, user_removed = get_user_skill_overrides(db)

    # 5. Tier classification — split JD tools into claimable vs blocked
    claimable, blocked = filter_claimable(all_jd_tools)

    # Apply user overrides
    # v2 FIX: parentheses ensure user_removed applies to BOTH claimable AND user_added.
    # v1 bug: `set(claimable) | set(user_added) - set(user_removed)` only removed from user_added
    # due to Python operator precedence (set difference binds tighter than union).
    final_verified = list((set(claimable) | set(user_added)) - set(user_removed))

    # 6. Identify gap_flags — Tier 3 tools the JD requires
    gap_flags = [t for t in blocked if t.lower() in TIER_3_NEVER_CLAIM]

    # 7. Load configurable thresholds from dashboard_settings
    thresholds = _load_gen_thresholds(db)

    # 8. Select achievements by coverage (using configurable thresholds)
    selected_achievements = select_achievements_by_coverage(
        job_category=job_category,
        verified_tools_in_jd=final_verified,
        top_n=thresholds["achievement_top_n"],
        coverage_min=thresholds["achievement_coverage_min"],
        overlap_boost=thresholds["tool_overlap_boost"],
    )

    # 9. Extract JD keywords for language mirroring
    jd_keywords = all_jd_tools[:20]  # Top 20 for prompt efficiency

    # 10. Determine if human review is required
    requires_review = bool(gap_flags) or alignment_score < thresholds["min_score_to_generate"]

    return GenerationContext(
        job_id=job_id,
        job_title=job.get("title", ""),
        company=job.get("company", ""),
        job_category=job_category,
        alignment_score=alignment_score,
        base_resume_version=base_version,
        base_resume_text=resume_text,
        verified_tools_for_job=final_verified,
        blocked_tools_in_jd=blocked,
        user_added_skills=user_added,
        user_removed_skills=user_removed,
        selected_achievements=selected_achievements,
        jd_keywords=jd_keywords,
        jd_summary="",  # Populated by ai_generator if llm_summarizer result available
        jd_full_text=job.get("description") or "",  # v2: pass full JD for score delta in Layer 3
        gap_flags=gap_flags,
        requires_human_review=requires_review,
    )
