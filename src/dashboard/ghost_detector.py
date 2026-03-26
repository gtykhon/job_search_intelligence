"""
Ghost Job Detector — Identifies likely ghost/stale job postings.

Signals used:
  1. Posting age > 45 days → ghost
  2. Applicant count > 500 → ghost (oversaturated)
  3. Ghost language patterns in description (e.g., "future opportunities",
     "talent pipeline", "always accepting", "evergreen")
  4. Reposted indicators (original_listed_at much older than listed_at)
  5. Generic/vague descriptions with no specifics

Returns a GhostResult with is_ghost flag, confidence (0-100),
and list of reasons.
"""

import json
import re
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ── Ghost Language Patterns ──────────────────────────────────────────

GHOST_PHRASES = [
    r"future\s+opportunit",
    r"talent\s+(pipeline|pool|communit)",
    r"always\s+accepting",
    r"evergreen\s+(requisition|position|role)",
    r"proactive(ly)?\s+(sourcing|recruiting)",
    r"no\s+immediate\s+opening",
    r"building\s+(our|a)\s+talent",
    r"ongoing\s+recruitment",
    r"continuous(ly)?\s+hiring",
    r"general\s+application",
    r"expression\s+of\s+interest",
    r"roster\s+(position|role)",
    r"we\s+are\s+not\s+currently\s+hiring",
    r"anticipat(ed|ing)\s+(future|upcoming)\s+(need|opening|role)",
]

VAGUE_DESCRIPTION_SIGNALS = [
    r"responsibilities\s+will\s+be\s+determined",
    r"duties\s+as\s+assigned",
    r"various\s+(tasks|duties|responsibilities)",
    r"perform\s+other\s+duties",
    r"tbd",
]


@dataclass
class GhostResult:
    """Result of ghost job analysis."""
    is_ghost: bool = False
    confidence: int = 0  # 0-100
    reasons: List[str] = field(default_factory=list)
    signals_found: int = 0

    @property
    def summary(self) -> str:
        if not self.is_ghost:
            return "Likely legitimate"
        return f"Ghost ({self.confidence}%): {'; '.join(self.reasons[:3])}"


def detect_ghost_job(job: Dict[str, Any]) -> GhostResult:
    """
    Analyze a job posting for ghost job signals.

    Args:
        job: Dict with keys like posted_date, scraped_date, description,
             applicant_count, listed_at_ms, original_listed_at_ms, etc.

    Returns:
        GhostResult with is_ghost, confidence, and reasons.
    """
    result = GhostResult()
    signals = 0
    max_signals = 0

    # ── Signal 1: Posting age > 45 days ──────────────────────────────
    max_signals += 3
    age_days = _get_posting_age_days(job)
    if age_days is not None:
        if age_days > 90:
            signals += 3
            result.reasons.append(f"Posted {age_days}d ago (>90d = very stale)")
        elif age_days > 60:
            signals += 2
            result.reasons.append(f"Posted {age_days}d ago (>60d = stale)")
        elif age_days > 45:
            signals += 1
            result.reasons.append(f"Posted {age_days}d ago (>45d = aging)")

    # ── Signal 2: High applicant count ───────────────────────────────
    max_signals += 3
    applicant_count = job.get("applicant_count")
    if applicant_count is not None and applicant_count > 0:
        if applicant_count > 1000:
            signals += 3
            result.reasons.append(f"{applicant_count} applicants (oversaturated)")
        elif applicant_count > 500:
            signals += 2
            result.reasons.append(f"{applicant_count} applicants (high volume)")
        elif applicant_count > 300:
            signals += 1
            result.reasons.append(f"{applicant_count} applicants (competitive)")

    # ── Signal 3: Ghost language in description ──────────────────────
    max_signals += 3
    description = (job.get("description") or "").lower()
    if description:
        ghost_matches = []
        for pattern in GHOST_PHRASES:
            if re.search(pattern, description, re.IGNORECASE):
                ghost_matches.append(pattern.split(r"\s+")[0].replace("\\", ""))

        if len(ghost_matches) >= 3:
            signals += 3
            result.reasons.append(f"Multiple ghost phrases: {', '.join(ghost_matches[:3])}")
        elif len(ghost_matches) >= 2:
            signals += 2
            result.reasons.append(f"Ghost phrases: {', '.join(ghost_matches[:2])}")
        elif len(ghost_matches) == 1:
            signals += 1
            result.reasons.append(f"Ghost phrase detected: {ghost_matches[0]}")

    # ── Signal 4: Repost detection ───────────────────────────────────
    max_signals += 2
    listed_ms = job.get("listed_at_ms")
    original_ms = job.get("original_listed_at_ms")
    if listed_ms and original_ms and listed_ms != original_ms:
        repost_gap_days = abs(listed_ms - original_ms) / (1000 * 60 * 60 * 24)
        if repost_gap_days > 90:
            signals += 2
            result.reasons.append(f"Reposted after {int(repost_gap_days)}d gap")
        elif repost_gap_days > 30:
            signals += 1
            result.reasons.append(f"Reposted after {int(repost_gap_days)}d gap")

    # ── Signal 5: Very short/vague description ───────────────────────
    max_signals += 1
    if description:
        # Under 200 chars is suspiciously short
        if len(description) < 200:
            signals += 1
            result.reasons.append("Very short description (<200 chars)")
        else:
            # Check for vague language
            vague_count = sum(
                1 for p in VAGUE_DESCRIPTION_SIGNALS
                if re.search(p, description, re.IGNORECASE)
            )
            if vague_count >= 2:
                signals += 1
                result.reasons.append("Vague/generic description")

    # ── Signal 6: Career page verification ───────────────────────────
    max_signals += 3
    career_verified = job.get("career_page_verified")
    if career_verified is not None:
        if career_verified == 0:  # Not found on career page
            signals += 3
            result.reasons.append("Not found on company career page")
        elif career_verified == 1:  # Confirmed on career page
            signals -= 1  # Reduce ghost score — this is a positive signal
    else:
        # Check career_page_json for inline results
        career_json = job.get("career_page_json")
        if career_json:
            try:
                career_data = json.loads(career_json) if isinstance(career_json, str) else career_json
                if career_data.get("found_on_career_page") is False:
                    signals += 3
                    result.reasons.append("Not found on company career page")
                elif career_data.get("found_on_career_page") is True:
                    signals -= 1
            except (json.JSONDecodeError, TypeError):
                pass

    # ── Calculate confidence ─────────────────────────────────────────
    signals = max(0, signals)  # floor at 0 after career page bonus
    result.signals_found = signals
    if max_signals > 0:
        result.confidence = min(100, int((signals / max_signals) * 100))

    # Ghost threshold: 25%+ confidence = ghost
    result.is_ghost = result.confidence >= 25

    return result


def _get_posting_age_days(job: Dict[str, Any]) -> Optional[int]:
    """Get posting age in days from the best available date field."""
    # Prefer original_listed_at_ms (LinkedIn original post date)
    original_ms = job.get("original_listed_at_ms")
    if original_ms:
        try:
            dt = datetime.fromtimestamp(int(original_ms) / 1000)
            return max(0, (datetime.now() - dt).days)
        except (ValueError, TypeError, OSError):
            pass

    # Then try posted_date
    posted = job.get("posted_date")
    if posted:
        try:
            dt = datetime.fromisoformat(str(posted).replace("Z", "+00:00")).replace(tzinfo=None)
            return max(0, (datetime.now() - dt).days)
        except (ValueError, TypeError):
            pass

    # Fall back to scraped_date (less reliable for "ghost" detection)
    scraped = job.get("scraped_date")
    if scraped:
        try:
            dt = datetime.fromisoformat(str(scraped).replace("Z", "+00:00")).replace(tzinfo=None)
            return max(0, (datetime.now() - dt).days)
        except (ValueError, TypeError):
            pass

    return None


def flag_ghost_jobs_batch(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run ghost detection on a batch of jobs.

    Returns summary stats and the list of ghost job IDs.
    """
    ghosts = []
    clean = []

    for job in jobs:
        result = detect_ghost_job(job)
        if result.is_ghost:
            ghosts.append({
                "id": job.get("id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "confidence": result.confidence,
                "reasons": result.reasons,
            })
        else:
            clean.append(job.get("id"))

    return {
        "total_analyzed": len(jobs),
        "ghost_count": len(ghosts),
        "clean_count": len(clean),
        "ghost_jobs": ghosts,
        "ghost_ids": [g["id"] for g in ghosts],
    }
