"""
Authentication Audit Protocol.

Validates generated career content (cover letters, resume bullets) for
authenticity violations BEFORE delivery. This is content authentication —
NOT LinkedIn login authentication.

Four violation categories:
  1. METRIC_CROSS_PROJECT    — metric appears in content but not traceable to resume
  2. TIMELINE_MISMATCH       — tech/role claim conflicts with employment dates
  3. SCOPE_INFLATION         — inflated action verbs beyond what resume supports
  4. UNAUTHORIZED_TECH_COMBO — technology combination not evidenced in resume

Usage:
    engine = AuthAuditEngine()
    result = engine.audit(cover_letter=text, resume_text=resume)
    if not result.passed:
        for v in result.violations:
            print(v.severity, v.description)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ViolationType(str, Enum):
    METRIC_CROSS_PROJECT     = "metric_cross_project"
    TIMELINE_MISMATCH        = "timeline_mismatch"
    SCOPE_INFLATION          = "scope_inflation"
    UNAUTHORIZED_TECH_COMBO  = "unauthorized_tech_combo"


@dataclass
class AuthViolation:
    violation_type: ViolationType
    severity: str          # "critical" | "warning"
    description: str
    evidence: str          # quoted text fragment
    suggestion: str


@dataclass
class AuthAuditResult:
    passed: bool
    violations: List[AuthViolation] = field(default_factory=list)
    authenticity_score: float = 100.0   # 0-100; 100 = fully authentic
    summary: str = ""

    def critical_violations(self) -> List[AuthViolation]:
        return [v for v in self.violations if v.severity == "critical"]

    def warning_violations(self) -> List[AuthViolation]:
        return [v for v in self.violations if v.severity == "warning"]


class AuthAuditEngine:
    """
    Detects authenticity violations in career content.

    Compares cover letter claims against the resume to find metrics,
    scope language, or technology combinations that are not supported
    by the resume text.
    """

    # Scope inflation: {inflated_word: [acceptable_alternatives]}
    SCOPE_WORDS: Dict[str, List[str]] = {
        "architected":  ["designed", "built", "implemented", "contributed to"],
        "owned":        ["managed", "supported", "led", "was responsible for"],
        "spearheaded":  ["led", "initiated", "drove", "supported"],
        "transformed":  ["improved", "enhanced", "updated", "modified"],
        "revolutionized": ["improved", "modernized", "updated"],
        "single-handedly": ["contributed", "helped", "supported"],
    }

    # Known verified Azure services (per project knowledge base)
    VERIFIED_AZURE: frozenset = frozenset({
        "azure form recognizer",
        "azure blob storage",
        "azure web apps",
        "azure devops",
        "azure active directory",
    })

    # Azure services NOT verified in known stack
    UNVERIFIED_AZURE: frozenset = frozenset({
        "azure key vault",
        "azure functions",
        "azure cosmos db",
        "azure synapse",
        "azure databricks",
        "azure machine learning",
    })

    _METRIC_RE = re.compile(
        r"(\d[\d,.]* *(?:%|percent|x\b|\$[\d,]+|million|billion|k\b|"
        r"hours?|days?|weeks?|minutes?|seconds?))",
        re.IGNORECASE,
    )

    def audit(
        self,
        cover_letter: str,
        resume_text: str,
        employment_history: Optional[List[Dict]] = None,
    ) -> AuthAuditResult:
        """
        Run all four audit checks. Returns an AuthAuditResult.

        Parameters
        ----------
        cover_letter      : generated cover letter text to validate
        resume_text       : plain-text resume (ground truth)
        employment_history: optional list of {employer, start, end, technologies}
                            dicts for timeline checking
        """
        violations: List[AuthViolation] = []

        violations.extend(self._check_metric_origin(cover_letter, resume_text))
        violations.extend(self._check_scope_inflation(cover_letter, resume_text))
        violations.extend(self._check_tool_combos(cover_letter, resume_text))

        if employment_history:
            violations.extend(self._check_timeline(cover_letter, employment_history))

        # Score: start at 100, deduct per violation
        deductions = sum(15 if v.severity == "critical" else 7 for v in violations)
        score = max(0.0, 100.0 - deductions)

        # Pass if no critical violations
        critical = [v for v in violations if v.severity == "critical"]
        passed = len(critical) == 0

        summary_parts = []
        if not violations:
            summary_parts.append("All authenticity checks passed.")
        else:
            summary_parts.append(
                f"{len(violations)} violation(s): "
                f"{len(critical)} critical, {len(violations)-len(critical)} warning."
            )

        return AuthAuditResult(
            passed=passed,
            violations=violations,
            authenticity_score=round(score, 1),
            summary=" ".join(summary_parts),
        )

    # ------------------------------------------------------------------
    # Check 1: Metric origin
    # ------------------------------------------------------------------

    def _check_metric_origin(
        self, cover_letter: str, resume_text: str
    ) -> List[AuthViolation]:
        """
        Detect metrics in the cover letter that don't appear in the resume.
        E.g. cover letter claims '80% cost reduction' but resume only has '40%'.
        """
        violations: List[AuthViolation] = []
        resume_lower = resume_text.lower()

        cl_metrics = self._METRIC_RE.findall(cover_letter)
        for metric in cl_metrics:
            normalized = metric.lower().strip()
            # Check if this metric (or a close variant) appears in the resume
            if not self._metric_in_resume(normalized, resume_lower):
                violations.append(AuthViolation(
                    violation_type=ViolationType.METRIC_CROSS_PROJECT,
                    severity="critical",
                    description=(
                        f"Metric '{metric}' appears in cover letter but is not "
                        f"traceable to resume. Risk of cross-project metric transfer."
                    ),
                    evidence=self._excerpt(cover_letter, metric),
                    suggestion=(
                        f"Verify this metric is from a project you can discuss in an "
                        f"interview. If correct, add it to your resume first."
                    ),
                ))
        return violations

    def _metric_in_resume(self, metric: str, resume_lower: str) -> bool:
        """Check if a metric value appears in the resume (fuzzy match)."""
        # Extract the numeric core (e.g. "40" from "40%")
        nums = re.findall(r"\d[\d,.]*", metric)
        if not nums:
            return True  # can't verify, assume OK
        for num in nums:
            if num in resume_lower:
                return True
        return False

    # ------------------------------------------------------------------
    # Check 2: Timeline mismatch
    # ------------------------------------------------------------------

    def _check_timeline(
        self, cover_letter: str, employment_history: List[Dict]
    ) -> List[AuthViolation]:
        """
        Check that technologies mentioned in the cover letter align with
        employment dates when history is provided.
        """
        violations: List[AuthViolation] = []

        # Simple heuristic: look for year references in cover letter and compare
        # against when specific technologies were in use
        years_in_cl = set(re.findall(r"\b(20\d{2})\b", cover_letter))

        for entry in employment_history:
            techs = entry.get("technologies", [])
            start = str(entry.get("start", ""))
            end = str(entry.get("end", "now"))

            for year in years_in_cl:
                if start and year < start[:4]:
                    violations.append(AuthViolation(
                        violation_type=ViolationType.TIMELINE_MISMATCH,
                        severity="warning",
                        description=(
                            f"Cover letter references year {year} but employment at "
                            f"'{entry.get('employer', 'unknown')}' started {start}."
                        ),
                        evidence=f"Year {year} in cover letter",
                        suggestion="Verify all date references align with your employment history.",
                    ))
                    break

        return violations

    # ------------------------------------------------------------------
    # Check 3: Scope inflation
    # ------------------------------------------------------------------

    def _check_scope_inflation(
        self, cover_letter: str, resume_text: str
    ) -> List[AuthViolation]:
        """
        Detect inflated scope language in cover letter that the resume
        doesn't support.
        """
        violations: List[AuthViolation] = []
        cl_lower = cover_letter.lower()
        resume_lower = resume_text.lower()

        for inflated_word, alternatives in self.SCOPE_WORDS.items():
            if inflated_word not in cl_lower:
                continue
            # Check if the resume also uses this word (if yes, it's verified)
            if inflated_word in resume_lower:
                continue
            # Check if resume supports the claim via any alternative
            resume_supports = any(alt in resume_lower for alt in alternatives)
            if not resume_supports:
                violations.append(AuthViolation(
                    violation_type=ViolationType.SCOPE_INFLATION,
                    severity="warning",
                    description=(
                        f"Cover letter uses '{inflated_word}' but this word does not "
                        f"appear in the resume and no supporting evidence found."
                    ),
                    evidence=self._excerpt(cover_letter, inflated_word),
                    suggestion=(
                        f"Consider replacing '{inflated_word}' with one of: "
                        f"{', '.join(alternatives[:3])}. Or add evidence to resume first."
                    ),
                ))

        return violations

    # ------------------------------------------------------------------
    # Check 4: Unauthorized tech combinations
    # ------------------------------------------------------------------

    def _check_tool_combos(
        self, cover_letter: str, resume_text: str
    ) -> List[AuthViolation]:
        """
        Detect technology references in the cover letter that aren't in the resume,
        with special attention to the known UNVERIFIED Azure services.
        """
        violations: List[AuthViolation] = []
        cl_lower = cover_letter.lower()
        resume_lower = resume_text.lower()

        # Check unverified Azure services
        for service in self.UNVERIFIED_AZURE:
            if service in cl_lower and service not in resume_lower:
                violations.append(AuthViolation(
                    violation_type=ViolationType.UNAUTHORIZED_TECH_COMBO,
                    severity="critical",
                    description=(
                        f"'{service.title()}' referenced in cover letter but NOT found "
                        f"in resume. This service is not in the verified Azure stack "
                        f"(Form Recognizer, Blob Storage, Web Apps, DevOps)."
                    ),
                    evidence=self._excerpt(cover_letter, service),
                    suggestion=(
                        f"Remove '{service.title()}' or verify actual hands-on experience "
                        f"and add to resume with context first."
                    ),
                ))

        return violations

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _excerpt(self, text: str, keyword: str, context: int = 80) -> str:
        """Return a short excerpt around the keyword."""
        idx = text.lower().find(keyword.lower())
        if idx == -1:
            return keyword
        start = max(0, idx - context // 2)
        end = min(len(text), idx + len(keyword) + context // 2)
        return f"...{text[start:end].strip()}..."
