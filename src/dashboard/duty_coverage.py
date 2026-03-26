"""
Duty Coverage Scoring System.

Evaluates how well a candidate's experience covers the duties
described in a job posting using the XYZ Framework and weighted
duty category analysis.

XYZ Framework:
  X (WHAT)   = accomplishment with scope
  Y (HOW)    = methodology/tools used
  Z (RESULT) = measurable business impact

Coverage Tiers:
  Strong   (80-100%): minimal repositioning needed
  Moderate (50-79%):  light repositioning with skill transfer
  Weak     (25-49%):  heavy repositioning required
  Minimal  (<25%):    exclude or use alternative positioning

Usage:
    engine = DutyCoverageEngine(resume_text="...")
    result = engine.score(job_description="...")
    print(result.tier, result.coverage_pct, result.space_allocation)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Duty categories and weights
# ---------------------------------------------------------------------------

class DutyCategory(str, Enum):
    CORE_TECHNICAL          = "core_technical"       # 40-60% weight
    IMPLEMENTATION_PROCESS  = "implementation"        # 20-30% weight
    LEADERSHIP_COLLABORATION = "leadership"           # 15-25% weight
    INDUSTRY_DOMAIN         = "domain"               # 5-15% weight
    CULTURAL_SOFT           = "cultural"             # 5-15% weight


# (min_weight, max_weight) as fractions of total score
CATEGORY_WEIGHTS: Dict[DutyCategory, Tuple[float, float]] = {
    DutyCategory.CORE_TECHNICAL:           (0.40, 0.60),
    DutyCategory.IMPLEMENTATION_PROCESS:   (0.20, 0.30),
    DutyCategory.LEADERSHIP_COLLABORATION: (0.15, 0.25),
    DutyCategory.INDUSTRY_DOMAIN:          (0.05, 0.15),
    DutyCategory.CULTURAL_SOFT:            (0.05, 0.15),
}

# Midpoint weights used for scoring
_CATEGORY_MIDPOINT: Dict[DutyCategory, float] = {
    cat: (lo + hi) / 2 for cat, (lo, hi) in CATEGORY_WEIGHTS.items()
}

# Coverage tier thresholds
COVERAGE_TIERS: Dict[str, Tuple[float, float]] = {
    "Strong":   (80.0, 100.0),
    "Moderate": (50.0,  79.9),
    "Weak":     (25.0,  49.9),
    "Minimal":  ( 0.0,  24.9),
}

# Space allocation mapping per tier
SPACE_ALLOCATION: Dict[str, str] = {
    "Strong":   "expand",
    "Moderate": "maintain",
    "Weak":     "trim",
    "Minimal":  "exclude",
}

# ---------------------------------------------------------------------------
# Keyword sets per category for classification
# ---------------------------------------------------------------------------

_CATEGORY_SIGNALS: Dict[DutyCategory, List[str]] = {
    DutyCategory.CORE_TECHNICAL: [
        "python", "sql", "java", "javascript", "typescript", "golang", "rust",
        "api", "rest", "graphql", "microservices", "architecture", "design",
        "algorithm", "data structure", "machine learning", "ml", "ai", "nlp",
        "etl", "pipeline", "database", "schema", "query", "index",
        "aws", "azure", "gcp", "cloud", "docker", "kubernetes",
        "react", "angular", "vue", "node", "django", "flask", "fastapi",
        "spark", "kafka", "airflow", "dbt", "snowflake", "databricks",
        "pytorch", "tensorflow", "scikit", "pandas", "numpy",
        "ci/cd", "devops", "infrastructure", "terraform", "ansible",
        "build", "implement", "develop", "engineer", "code", "program",
        "system", "platform", "framework", "library", "tool",
    ],
    DutyCategory.IMPLEMENTATION_PROCESS: [
        "deploy", "release", "ship", "deliver", "execute", "implement",
        "test", "unit test", "integration test", "qa", "quality",
        "monitor", "observe", "logging", "metrics", "alerting",
        "maintain", "support", "operate", "run", "manage",
        "process", "workflow", "automation", "script",
        "agile", "scrum", "sprint", "kanban", "jira",
        "documentation", "spec", "requirement", "requirement",
        "debug", "troubleshoot", "resolve", "fix", "optimize",
    ],
    DutyCategory.LEADERSHIP_COLLABORATION: [
        "lead", "mentor", "coach", "guide", "manage",
        "team", "cross-functional", "stakeholder", "partner",
        "communicate", "present", "report", "align",
        "hire", "recruit", "interview", "onboard",
        "roadmap", "strategy", "prioritize", "plan",
        "influence", "drive", "own", "accountable",
        "collaborate", "coordinate", "facilitate",
    ],
    DutyCategory.INDUSTRY_DOMAIN: [
        "fintech", "finance", "banking", "payments", "compliance",
        "healthcare", "hipaa", "ehr", "clinical",
        "e-commerce", "retail", "supply chain",
        "saas", "b2b", "b2c", "enterprise",
        "government", "federal", "regulatory",
        "security", "soc2", "gdpr", "pci",
        "media", "content", "advertising",
        "domain", "industry", "vertical", "sector",
    ],
    DutyCategory.CULTURAL_SOFT: [
        "ownership", "initiative", "proactive", "self-starter",
        "adaptable", "flexible", "growth mindset",
        "passionate", "motivated", "driven",
        "communication", "written", "verbal",
        "problem-solving", "analytical", "creative",
        "fast-paced", "ambiguous", "autonomous",
        "remote", "distributed", "async",
    ],
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class XYZStatement:
    """A single achievement extracted from a resume in XYZ format."""
    what: str            # X: accomplishment with scope
    how: str             # Y: methodology/tools used
    result: str          # Z: business impact / metric
    category: DutyCategory
    source_line: str     # original text for audit trail
    confidence: float = 0.0  # 0-1, how confident the extraction is


@dataclass
class DutyCoverageResult:
    """Full output of the duty coverage analysis."""
    coverage_pct: float                    # 0-100 overall
    tier: str                              # "Strong" | "Moderate" | "Weak" | "Minimal"
    category_scores: Dict[str, float]      # category name -> 0-100 score
    matched_duties: List[str]              # JD duties covered by resume
    uncovered_duties: List[str]            # JD duties with no match
    space_allocation: Dict[str, str]       # category -> "expand"|"maintain"|"trim"|"exclude"
    xyz_statements: List[XYZStatement]     # extracted from resume
    repositioning_intensity: str           # "minimal" | "light" | "heavy" | "exclude"

    def summary(self) -> str:
        return (
            f"Coverage: {self.coverage_pct:.1f}% ({self.tier}) | "
            f"Matched: {len(self.matched_duties)} duties | "
            f"Uncovered: {len(self.uncovered_duties)} | "
            f"Repositioning: {self.repositioning_intensity}"
        )


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class DutyCoverageEngine:
    """
    Scores how well a candidate's resume covers a job description's duties.

    Parameters
    ----------
    candidate_profile_text : str
        The full resume text (plain text, not formatted).
    """

    # Patterns for extracting action-result statements from resume bullets
    _BULLET_RE = re.compile(
        r"^\s*(?:[-*\u2022]|\d+[.)]) (.+)",
        re.MULTILINE,
    )
    _METRIC_RE = re.compile(
        r"(\d+[\d,.]*\s*(?:%|percent|x|X|\$|million|billion|k\b|hours?|days?|weeks?))",
        re.IGNORECASE,
    )
    # Duty extraction: lines that contain action verbs
    _DUTY_RE = re.compile(
        r"^[\s\-\u2022*]*([A-Z][a-zA-Z\s,/()&+]{15,})",
        re.MULTILINE,
    )

    def __init__(self, candidate_profile_text: str):
        self.resume_text = candidate_profile_text
        self._resume_lower = candidate_profile_text.lower()
        self._xyz_cache: Optional[List[XYZStatement]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, job_description: str) -> DutyCoverageResult:
        """
        Compute duty coverage of *job_description* against the resume.
        """
        jd_lower = job_description.lower()

        # 1. Extract duties from JD
        jd_duties = self._extract_duties(job_description)

        # 2. Extract XYZ statements from resume
        xyz_statements = self._extract_xyz_statements()

        # 3. Match duties to resume evidence
        matched, uncovered = self._match_duties(jd_duties, xyz_statements)

        # 4. Compute per-category scores
        category_scores = self._compute_category_scores(jd_lower, jd_duties, matched)

        # 5. Weighted overall score
        coverage_pct = self._weighted_coverage(category_scores)

        # 6. Determine tier and space allocation
        tier = self._coverage_tier(coverage_pct)
        space_alloc = {
            cat.value: SPACE_ALLOCATION.get(
                self._coverage_tier(score), "maintain"
            )
            for cat, score in category_scores.items()
        }

        # 7. Repositioning intensity
        intensity = {
            "Strong":   "minimal",
            "Moderate": "light",
            "Weak":     "heavy",
            "Minimal":  "exclude",
        }.get(tier, "light")

        return DutyCoverageResult(
            coverage_pct=round(coverage_pct, 1),
            tier=tier,
            category_scores={cat.value: round(score, 1) for cat, score in category_scores.items()},
            matched_duties=matched,
            uncovered_duties=uncovered,
            space_allocation=space_alloc,
            xyz_statements=xyz_statements,
            repositioning_intensity=intensity,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_xyz_statements(self) -> List[XYZStatement]:
        """Extract achievement bullets from resume as XYZ statements."""
        if self._xyz_cache is not None:
            return self._xyz_cache

        statements: List[XYZStatement] = []
        bullet_lines = self._BULLET_RE.findall(self.resume_text)

        # Also grab non-bulleted lines that look like achievements
        for line in self.resume_text.splitlines():
            line = line.strip()
            if len(line) > 30 and line not in bullet_lines:
                if re.match(r"[A-Z][a-z]+ ", line):  # starts with capitalized verb
                    bullet_lines.append(line)

        for line in bullet_lines:
            if len(line) < 20:
                continue

            # X: the line itself describes WHAT
            what = line[:120].strip()

            # Y: extract tool/method keywords
            how_kws = []
            for cat_kws in _CATEGORY_SIGNALS.values():
                how_kws.extend(kw for kw in cat_kws if kw in line.lower())
            how = ", ".join(how_kws[:5]) if how_kws else "general methodology"

            # Z: extract metric if present
            metrics = self._METRIC_RE.findall(line)
            result = ", ".join(metrics[:2]) if metrics else "business impact"

            category = self._categorize_text(line)
            confidence = 0.9 if metrics else 0.6

            statements.append(XYZStatement(
                what=what,
                how=how,
                result=result,
                category=category,
                source_line=line,
                confidence=confidence,
            ))

        self._xyz_cache = statements
        return statements

    def _extract_duties(self, jd_text: str) -> List[str]:
        """Extract duty/responsibility lines from a JD."""
        duties: List[str] = []

        # Grab bullet lines
        for line in self._BULLET_RE.findall(jd_text):
            line = line.strip()
            if 15 < len(line) < 300:
                duties.append(line)

        # Grab lines that start with action verbs
        for line in jd_text.splitlines():
            line = line.strip()
            if 20 < len(line) < 300 and re.match(r"[A-Z][a-z]+\b", line):
                if line not in duties:
                    duties.append(line)

        return duties[:50]  # cap at 50 duties for performance

    def _match_duties(
        self,
        duties: List[str],
        xyz_statements: List[XYZStatement],
    ) -> Tuple[List[str], List[str]]:
        """
        Match JD duties to resume XYZ statements.
        Returns (matched_duties, uncovered_duties).
        """
        resume_signals = set()
        for stmt in xyz_statements:
            for word in re.findall(r"\b[a-z]{3,}\b", stmt.source_line.lower()):
                resume_signals.add(word)

        matched: List[str] = []
        uncovered: List[str] = []

        for duty in duties:
            duty_words = set(re.findall(r"\b[a-z]{3,}\b", duty.lower()))
            # Remove common stopwords
            duty_words -= {"the", "and", "for", "with", "that", "this", "will",
                           "are", "have", "has", "our", "you", "your", "their"}
            overlap = duty_words & resume_signals
            # Match if >= 25% of meaningful duty words appear in resume
            if duty_words and len(overlap) / len(duty_words) >= 0.25:
                matched.append(duty)
            else:
                uncovered.append(duty)

        return matched, uncovered

    def _compute_category_scores(
        self,
        jd_lower: str,
        jd_duties: List[str],
        matched_duties: List[str],
    ) -> Dict[DutyCategory, float]:
        """
        Score each duty category based on presence in JD and coverage in resume.
        """
        scores: Dict[DutyCategory, float] = {}

        for cat, signals in _CATEGORY_SIGNALS.items():
            # How many signals appear in JD?
            jd_hits = sum(1 for s in signals if s in jd_lower)
            # How many signals appear in resume?
            resume_hits = sum(1 for s in signals if s in self._resume_lower)

            if jd_hits == 0:
                # Category not relevant to this JD — give neutral score
                scores[cat] = 75.0
                continue

            # Coverage ratio for this category
            coverage_ratio = min(resume_hits / max(jd_hits, 1), 1.0)
            scores[cat] = round(coverage_ratio * 100, 1)

        return scores

    def _weighted_coverage(self, category_scores: Dict[DutyCategory, float]) -> float:
        """Compute weighted average using category midpoint weights."""
        total_weight = sum(_CATEGORY_MIDPOINT.values())
        weighted_sum = sum(
            score * _CATEGORY_MIDPOINT.get(cat, 0.1)
            for cat, score in category_scores.items()
        )
        return min(weighted_sum / total_weight, 100.0)

    def _coverage_tier(self, pct: float) -> str:
        for tier, (lo, hi) in COVERAGE_TIERS.items():
            if lo <= pct <= hi:
                return tier
        return "Minimal"

    def _categorize_text(self, text: str) -> DutyCategory:
        """Classify a text snippet into a DutyCategory."""
        text_lower = text.lower()
        scores: Dict[DutyCategory, int] = {cat: 0 for cat in DutyCategory}
        for cat, signals in _CATEGORY_SIGNALS.items():
            scores[cat] = sum(1 for s in signals if s in text_lower)
        return max(scores, key=lambda c: scores[c])
