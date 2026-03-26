"""
Salary Extractor — regex-based salary parser for JD free text.

When the scraper misses salary_min/salary_max fields (stored as NULL),
this extracts salary ranges from job description text.

Handles:
  "$155,000 – $195,000"         → (155000, 195000, yearly)
  "$150K - $200K"               → (150000, 200000, yearly)
  "Base salary: $155K"          → (155000, 155000, yearly)
  "Compensation up to $180K"    → (0, 180000, yearly)
  "$95/hr"                      → (95, 95, hourly)  → ~$197,600 yearly
  "140000-160000 per year"      → (140000, 160000, yearly)
  "150K to 190K annually"       → (150000, 190000, yearly)

Optional spaCy NER: if en_core_web_sm installed, MONEY entities are used
as a supplementary cross-check. Primary path is always regex.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# ── Amount normalisation ────────────────────────────────────────────────
def _parse_amount(raw: str) -> float:
    """Parse a salary token like "155,000" or "150K" → float."""
    raw = raw.replace(",", "").strip()
    if raw.lower().endswith("k"):
        return float(raw[:-1]) * 1_000
    return float(raw)


# ── Period thresholds (used when no explicit period keyword found) ──────
_HOURLY_MAX = 300         # values ≤ this are probably hourly
_MONTHLY_MIN = 3_000      # values 3k–30k without period hint → monthly
_MONTHLY_MAX = 30_000


def _infer_period(amount: float, context: str) -> str:
    ctx = context.lower()
    if any(w in ctx for w in ("/hr", "per hr", "per hour", "hourly", "/hour")):
        return "hourly"
    if any(w in ctx for w in ("/mo", "per mo", "per month", "monthly", "/month")):
        return "monthly"
    if any(w in ctx for w in (
        "/yr", "per yr", "per year", "annually", "annual", "yearly", "/year", "a year",
    )):
        return "yearly"
    # Magnitude inference
    if amount <= _HOURLY_MAX:
        return "hourly"
    if _MONTHLY_MIN <= amount <= _MONTHLY_MAX:
        return "monthly"
    return "yearly"


def _is_false_positive(raw: str, lo: float, hi: float) -> bool:
    """Reject clearly wrong extractions (dates, tiny numbers, etc.)."""
    if lo < 10 or hi < 10:
        return True
    # Both values look like calendar years and differ by < 5 → date range
    if 1990 <= lo <= 2035 and 1990 <= hi <= 2035 and abs(hi - lo) < 6:
        return True
    # lo > hi by a lot → malformed
    if lo > 0 and hi > 0 and lo > hi * 3:
        return True
    return False


# ── Regex patterns (priority order — most specific first) ──────────────
_CUR = r"(?:USD\s*)?\$?"    # optional currency prefix
_AMT = r"[\d,]+[Kk]?"       # amount token (e.g. 155,000 or 150K)
_SEP = r"\s*(?:[-\u2013\u2014]|to)\s*"  # range separator: - – — or "to"

_RAW_PATTERNS: List[Tuple[str, str]] = [
    # Full range with currency:  $155,000 – $195,000  or  $150K-$200K
    (
        rf"(?i){_CUR}({_AMT}){_SEP}{_CUR}({_AMT})"
        r"(?:\s*(?:USD|dollars?|per\s+year|annually|yearly|/yr|/year))?",
        "range",
    ),
    # Labeled single value:  "Base salary: $155K"  "Compensation: $180,000"
    (
        rf"(?i)(?:base\s+)?(?:salary|compensation|pay|total\s+comp"
        rf"|total\s+compensation|tc|target\s+compensation|remuneration)"
        rf"[\s:of]+{_CUR}({_AMT})"
        r"(?:\s*(?:/yr|/year|annually|yearly|per\s+year|/hr|hourly))?",
        "single_labeled",
    ),
    # Single value with explicit period:  "$95/hr"  or  "$150K per year"
    (
        rf"(?i){_CUR}({_AMT})\s*(?:per|/)\s*(year|yr|hour|hr|month|mo)",
        "single_with_period",
    ),
    # "up to $180K" / "maximum $200K"
    (
        rf"(?i)(?:up\s+to|as\s+much\s+as|maximum|max|not\s+to\s+exceed)\s+{_CUR}({_AMT})",
        "max_only",
    ),
    # Bare range without explicit $:  "155K-195K"  or  "140,000 to 160,000"
    # Require at least one value > 20k so we don't match "5-10 years"
    (
        rf"(?i)({_AMT}){_SEP}({_AMT})"
        r"(?:\s*(?:USD|dollars?|per\s+year|annually|/yr|/year))?",
        "range_no_currency",
    ),
]

_COMPILED: List[Tuple[re.Pattern, str]] = [
    (re.compile(p), tag) for p, tag in _RAW_PATTERNS
]


# ── Public dataclass ────────────────────────────────────────────────────
@dataclass
class SalaryRange:
    salary_min: float
    salary_max: float
    period: str           # "yearly" | "hourly" | "monthly"
    currency: str = "USD"
    confidence: float = 0.85
    source: str = "regex"
    raw_text: str = ""

    @property
    def yearly_max(self) -> float:
        """salary_max normalised to annual equivalent."""
        if self.period == "hourly":
            return self.salary_max * 2_080
        if self.period == "monthly":
            return self.salary_max * 12
        return self.salary_max

    @property
    def yearly_min(self) -> float:
        if self.period == "hourly":
            return self.salary_min * 2_080
        if self.period == "monthly":
            return self.salary_min * 12
        return self.salary_min


# ── Main extractor class ────────────────────────────────────────────────
class SalaryExtractor:
    """
    Extract salary ranges from job description free text.

    Primary path: compiled regex (no dependencies).
    Optional path: spaCy MONEY entities as a cross-check.
    """

    def __init__(self, use_spacy: bool = True):
        self._use_spacy = use_spacy
        self._nlp = None
        self._spacy_tried = False

    # ── spaCy lazy-load ─────────────────────────────────────────────
    def _load_spacy(self) -> bool:
        if self._spacy_tried:
            return self._nlp is not None
        self._spacy_tried = True
        try:
            import spacy                       # noqa: PLC0415
            self._nlp = spacy.load("en_core_web_sm")
            logger.debug("SalaryExtractor: spaCy en_core_web_sm loaded")
            return True
        except (ImportError, OSError):
            logger.debug("spaCy not available; salary extractor uses regex only")
            return False

    # ── Public API ──────────────────────────────────────────────────
    def extract(self, text: str) -> Optional[SalaryRange]:
        """
        Extract the best salary range found in text.
        Returns None if no salary information can be found.
        """
        if not text:
            return None
        # Salary almost always appears in the first 3000 characters
        search_text = text[:3_000]

        result = self._extract_regex(search_text)
        if result is not None:
            return result

        # spaCy supplementary — only when regex found nothing
        if self._use_spacy and self._load_spacy():
            return self._extract_spacy(search_text)

        return None

    # ── Regex extraction ────────────────────────────────────────────
    def _extract_regex(self, text: str) -> Optional[SalaryRange]:
        best: Optional[SalaryRange] = None

        for pattern, tag in _COMPILED:
            for m in pattern.finditer(text):
                groups = [g for g in m.groups() if g is not None]
                if not groups:
                    continue
                try:
                    raw_match = m.group(0)
                    ctx_start = max(0, m.start() - 50)
                    context = text[ctx_start: m.end() + 50]

                    candidate: Optional[SalaryRange] = None

                    if tag == "range":
                        lo = _parse_amount(groups[0])
                        hi = _parse_amount(groups[1])
                        if _is_false_positive(raw_match, lo, hi):
                            continue
                        period = _infer_period(hi, context)
                        candidate = SalaryRange(
                            salary_min=lo, salary_max=hi,
                            period=period, confidence=0.92, raw_text=raw_match,
                        )

                    elif tag == "single_labeled":
                        val = _parse_amount(groups[0])
                        if _is_false_positive(raw_match, val, val):
                            continue
                        period = _infer_period(val, context)
                        candidate = SalaryRange(
                            salary_min=val, salary_max=val,
                            period=period, confidence=0.87, raw_text=raw_match,
                        )

                    elif tag == "single_with_period":
                        val = _parse_amount(groups[0])
                        period_word = (groups[1] or "").lower()
                        period = (
                            "yearly" if period_word in ("year", "yr")
                            else "monthly" if period_word in ("month", "mo")
                            else "hourly"
                        )
                        candidate = SalaryRange(
                            salary_min=val, salary_max=val,
                            period=period, confidence=0.88, raw_text=raw_match,
                        )

                    elif tag == "max_only":
                        val = _parse_amount(groups[0])
                        if _is_false_positive(raw_match, val, val):
                            continue
                        period = _infer_period(val, context)
                        candidate = SalaryRange(
                            salary_min=0, salary_max=val,
                            period=period, confidence=0.75, raw_text=raw_match,
                        )

                    elif tag == "range_no_currency":
                        lo = _parse_amount(groups[0])
                        hi = _parse_amount(groups[1])
                        if _is_false_positive(raw_match, lo, hi):
                            continue
                        # Skip if neither value looks like a salary
                        if max(lo, hi) < 20_000 and max(lo, hi) > _HOURLY_MAX:
                            continue
                        period = _infer_period(hi, context)
                        candidate = SalaryRange(
                            salary_min=lo, salary_max=hi,
                            period=period, confidence=0.70, raw_text=raw_match,
                        )

                    if candidate is not None:
                        if best is None or candidate.confidence > best.confidence:
                            best = candidate

                except (ValueError, IndexError):
                    continue

        return best

    # ── spaCy supplementary ─────────────────────────────────────────
    def _extract_spacy(self, text: str) -> Optional[SalaryRange]:
        try:
            doc = self._nlp(text[:2_000])
            money_entities = [ent.text for ent in doc.ents if ent.label_ == "MONEY"]
            for ent_text in money_entities[:5]:
                result = self._extract_regex(ent_text)
                if result is not None:
                    result.source = "spacy_ner"
                    result.confidence = min(result.confidence, 0.75)
                    return result
        except Exception as e:
            logger.debug("spaCy MONEY extraction error: %s", e)
        return None


# ── Module-level singleton (one instance shared across gates) ───────────
_extractor: Optional[SalaryExtractor] = None


def get_salary_extractor() -> SalaryExtractor:
    """Return the module-level shared SalaryExtractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = SalaryExtractor()
    return _extractor
