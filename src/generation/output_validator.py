"""
Layer 3 — Post-generation output validator.
Runs after constrained_generate() returns.
Deterministic Python checks — no LLM involved.

v2 changes:
  - Score delta now scores GENERATED RESUME TEXT against full JD (was scoring keywords vs title)
  - Added jd_full_text to GenerationContext for this purpose

Adapted to actual AlignmentScorer API:
  - AlignmentScorer.__init__(resume_text) sets the resume internally
  - AlignmentScorer.score(job_description, job_title) scores against that resume
  - So we instantiate with generated text as "resume" and score against the JD
"""

import os
import re
import logging
from src.generation.context_builder import GenerationContext
from src.generation.tier3_blocklist import TIER_3_NEVER_CLAIM

logger = logging.getLogger(__name__)

# Formatting constants — from RESUME_FORMATTING_STANDARDS_2025.md
REQUIRED_NAME = os.getenv('USER_FULL_NAME', 'User Name')
REQUIRED_ZIP = os.getenv('USER_ZIP', '12345')
WRONG_ZIP = str(int(os.getenv('USER_ZIP', '12345')) + 1)
WRONG_NAME_PATTERN = re.compile(r"[A-Z\s]+", re.IGNORECASE)
REQUIRED_EMAIL = os.getenv('CONTACT_EMAIL', 'user@example.com')
REQUIRED_LINKEDIN = os.getenv('USER_LINKEDIN', 'linkedin.com/in/user')

# Default score degradation threshold (overridden by dashboard_settings via db param)
SCORE_DELTA_FLOOR = 0.90


def _get_score_delta_floor(db=None) -> float:
    """Load score delta floor from dashboard_settings, falling back to default."""
    if db is None:
        return SCORE_DELTA_FLOOR
    try:
        pct = int(db.get_setting("gen_score_delta_floor_pct", "90"))
        return pct / 100.0
    except Exception:
        return SCORE_DELTA_FLOOR


def validate_generated_output(generated: str, context: GenerationContext, db=None) -> dict:
    """
    Validate generated resume text against:
    1. Tier 3 blocklist — detect any blocked tool that appeared in output
    2. Formatting rules — name, zip, email, no ALL CAPS header
    3. Score delta — generated shouldn't score materially lower than base

    Args:
        generated: The tailored_resume string returned by constrained_generate()
        context: The GenerationContext used for generation

    Returns:
        dict with keys:
          fabrication_errors: list[str] — empty if clean
          formatting_warnings: list[str] — non-blocking but surfaced in dashboard
          score_degraded: bool — True if post-gen score < base_score * SCORE_DELTA_FLOOR
          post_gen_score: float — re-scored alignment value
    """
    fabrication_errors = []
    formatting_warnings = []

    if not generated:
        return {
            "fabrication_errors": ["EMPTY_OUTPUT: Generated resume is empty"],
            "formatting_warnings": [],
            "score_degraded": False,
            "post_gen_score": 0.0,
        }

    generated_lower = generated.lower()

    # ── Check 1: Tier 3 tool detector ─────────────────────────────────────────
    # Scan for any Tier 3 tool that appears in the generated text.
    # Use word-boundary matching to avoid false positives (e.g. "spark" in "sparked").
    for tool in TIER_3_NEVER_CLAIM:
        pattern = r'\b' + re.escape(tool.lower()) + r'\b'
        if re.search(pattern, generated_lower):
            fabrication_errors.append(
                f"TIER3_FABRICATION: '{tool}' found in output but not in verified stack"
            )

    # ── Check 2: Name format ──────────────────────────────────────────────────
    if REQUIRED_NAME not in generated:
        if WRONG_NAME_PATTERN.search(generated):
            formatting_warnings.append(
                f"NAME_FORMAT: Name appears in ALL CAPS. Must be: {REQUIRED_NAME}"
            )
        else:
            formatting_warnings.append(
                f"NAME_FORMAT: Canonical name '{REQUIRED_NAME}' not found in output"
            )

    # ── Check 3: ZIP code ─────────────────────────────────────────────────────
    if WRONG_ZIP in generated:
        fabrication_errors.append(
            f"WRONG_ZIP: '{WRONG_ZIP}' found in output. Must be '{REQUIRED_ZIP}' (Gaithersburg)"
        )

    if REQUIRED_ZIP not in generated:
        formatting_warnings.append(f"MISSING_ZIP: '{REQUIRED_ZIP}' not found in resume header")

    # ── Check 4: Contact info ─────────────────────────────────────────────────
    if REQUIRED_EMAIL not in generated:
        formatting_warnings.append(f"MISSING_EMAIL: '{REQUIRED_EMAIL}' not found in header")

    if REQUIRED_LINKEDIN not in generated:
        formatting_warnings.append(f"MISSING_LINKEDIN: '{REQUIRED_LINKEDIN}' not found")

    # ── Check 5: Score delta ──────────────────────────────────────────────────
    # v2 FIX: Now scores the GENERATED RESUME against the full JD text.
    # We instantiate AlignmentScorer with the generated text as "resume_text",
    # then call score(job_description=jd, job_title=title) to check alignment.
    score_degraded = False
    post_gen_score = context.alignment_score  # Default to base if scorer unavailable

    try:
        if context.jd_full_text:
            from src.dashboard.scoring import AlignmentScorer
            # AlignmentScorer uses resume_text internally for matching
            scorer = AlignmentScorer(resume_text=generated)
            result = scorer.score(
                job_description=context.jd_full_text,
                job_title=context.job_title
            )
            post_gen_score = result.overall_score

            delta_floor = _get_score_delta_floor(db)
            floor = context.alignment_score * delta_floor
            if post_gen_score < floor:
                score_degraded = True
                formatting_warnings.append(
                    f"SCORE_DEGRADED: Post-generation score {post_gen_score:.1f} < "
                    f"floor {floor:.1f} (base was {context.alignment_score:.1f})"
                )
        else:
            logger.warning(
                f"Job {context.job_id}: jd_full_text empty, skipping score delta check"
            )
    except Exception as e:
        logger.warning(f"Score delta check failed for job {context.job_id}: {e}")

    # ── Summary log ──────────────────────────────────────────────────────────
    if fabrication_errors:
        logger.error(
            f"Job {context.job_id}: {len(fabrication_errors)} FABRICATION ERROR(S): "
            f"{fabrication_errors}"
        )
    if formatting_warnings:
        logger.warning(
            f"Job {context.job_id}: {len(formatting_warnings)} formatting warning(s): "
            f"{formatting_warnings}"
        )

    return {
        "fabrication_errors": fabrication_errors,
        "formatting_warnings": formatting_warnings,
        "score_degraded": score_degraded,
        "post_gen_score": post_gen_score,
    }
