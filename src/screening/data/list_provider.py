"""
Dynamic gate-list provider.

Reads gate keyword lists from the dashboard DB when available,
falling back to the hardcoded defaults in known_lists.py.
This allows users to edit gate lists from the Settings UI
without touching source code.

DB key pattern: gate_list_{LIST_NAME}
Value format:   JSON array of lowercase strings
"""

import json
import logging
from typing import Set

from . import known_lists

logger = logging.getLogger(__name__)

# Valid list names that can be loaded/saved
VALID_LISTS = {
    "DEFENSE_PRIMES",
    "CLEARANCE_KEYWORDS",
    "GOV_EMPLOYER_SIGNALS",
    "STAFFING_AGENCIES",
    "STAFFING_SIGNALS",
    "DIRECT_HIRE_ALLOWLIST",
    "HARD_EXCLUDE_COMPANIES",
}

# Human-readable labels for UI display
LIST_LABELS = {
    "DEFENSE_PRIMES":        "Defense Prime Contractors",
    "CLEARANCE_KEYWORDS":    "Clearance Keywords",
    "GOV_EMPLOYER_SIGNALS":  "Government Employer Signals",
    "STAFFING_AGENCIES":     "Staffing Agencies",
    "STAFFING_SIGNALS":      "Staffing Signals in JDs",
    "DIRECT_HIRE_ALLOWLIST": "Direct-Hire Allowlist",
    "HARD_EXCLUDE_COMPANIES": "Hard Exclude Companies",
}

# Descriptions for each list
LIST_DESCRIPTIONS = {
    "DEFENSE_PRIMES": "Known defense/intelligence prime contractors. Substring match on company name. Jobs from these companies are hard-excluded.",
    "CLEARANCE_KEYWORDS": "Security clearance requirement keywords found in job descriptions. If any appear, the job is excluded.",
    "GOV_EMPLOYER_SIGNALS": "Government employer signals matched against company name and job description. Short signals (<5 chars) use word-boundary matching to prevent false positives.",
    "STAFFING_AGENCIES": "Known staffing/consulting placement firms. Substring match on company name. These jobs require manual override to proceed.",
    "STAFFING_SIGNALS": "Text patterns in job descriptions suggesting staffing/contract placement. Multi-word patterns to reduce false positives.",
    "DIRECT_HIRE_ALLOWLIST": "Product companies confirmed as direct employers that were false-flagged by staffing signals. These bypass all staffing checks.",
    "HARD_EXCLUDE_COMPANIES": "Companies to always exclude regardless of role, compensation, or tech stack.",
}

# Which gate each list belongs to
LIST_GATES = {
    "DEFENSE_PRIMES":        "0B",
    "CLEARANCE_KEYWORDS":    "0B",
    "GOV_EMPLOYER_SIGNALS":  "0B",
    "STAFFING_AGENCIES":     "0C",
    "STAFFING_SIGNALS":      "0C",
    "DIRECT_HIRE_ALLOWLIST": "0C",
    "HARD_EXCLUDE_COMPANIES": "0C",
}


def _db():
    """Lazy import to avoid circular dependency with dashboard.db."""
    try:
        from src.dashboard.db import db
        return db
    except Exception:
        return None


def get_gate_list(list_name: str) -> Set[str]:
    """Load gate list from DB, falling back to hardcoded default."""
    if list_name not in VALID_LISTS:
        raise ValueError(f"Unknown gate list: {list_name}")

    database = _db()
    if database:
        try:
            stored = database.get_setting(f"gate_list_{list_name}", "")
            if stored:
                return set(json.loads(stored))
        except Exception as e:
            logger.warning("Failed to load gate list %s from DB: %s", list_name, e)

    return set(getattr(known_lists, list_name))


def save_gate_list(list_name: str, items: list):
    """Save gate list to DB."""
    if list_name not in VALID_LISTS:
        raise ValueError(f"Unknown gate list: {list_name}")

    database = _db()
    if not database:
        raise RuntimeError("Database not available")

    database.set_setting(f"gate_list_{list_name}", json.dumps(sorted(items)))


def reset_gate_list(list_name: str):
    """Remove DB override, reverting to hardcoded default."""
    if list_name not in VALID_LISTS:
        raise ValueError(f"Unknown gate list: {list_name}")

    database = _db()
    if not database:
        raise RuntimeError("Database not available")

    database.set_setting(f"gate_list_{list_name}", "")


# Ordered list for consistent UI rendering
ORDERED_LISTS = [
    "DEFENSE_PRIMES",
    "CLEARANCE_KEYWORDS",
    "GOV_EMPLOYER_SIGNALS",
    "STAFFING_AGENCIES",
    "STAFFING_SIGNALS",
    "DIRECT_HIRE_ALLOWLIST",
    "HARD_EXCLUDE_COMPANIES",
]


def get_all_gate_lists() -> dict:
    """Load all gate lists, for passing to template context. Ordered for UI."""
    return {name: sorted(get_gate_list(name)) for name in ORDERED_LISTS}
