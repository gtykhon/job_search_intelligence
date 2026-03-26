"""
12-Point Quality Gate System for Job Application Packages.

Inspired by a technical manual's pre-delivery verification checklist,
this module validates resume + cover letter + job alignment before
an application package is finalized.

Gates are categorized by severity:
  - critical: Must pass or the package is rejected.
  - warning:  Should pass; flagged for human review.
  - info:     Advisory only; does not affect pass/fail.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Optional imports (graceful degradation) ─────────────────────────
try:
    from src.dashboard.ghost_detector import detect_ghost_job, GHOST_PHRASES
except ImportError:
    detect_ghost_job = None  # type: ignore[assignment]
    GHOST_PHRASES = []
    logger.debug("ghost_detector not available; Gate 5 & 9 will skip.")

try:
    from config.job_search_config import IGNORED_COMPANIES, is_excluded_company
except ImportError:
    IGNORED_COMPANIES: List[str] = []  # type: ignore[no-redef]

    def is_excluded_company(company_name: str) -> bool:  # type: ignore[misc]
        return False

    logger.debug("job_search_config not available; Gate 12 will skip.")

try:
    from src.dashboard.platform_rules import Platform, PlatformFormatValidator
    _PLATFORM_RULES_AVAILABLE = True
except ImportError:
    Platform = None  # type: ignore[assignment,misc]
    PlatformFormatValidator = None  # type: ignore[assignment]
    _PLATFORM_RULES_AVAILABLE = False
    logger.debug("platform_rules not available; platform formatting gate will skip.")

try:
    from src.dashboard.auth_audit import AuthAuditEngine, AuthAuditResult
    _AUTH_AUDIT_AVAILABLE = True
except ImportError:
    AuthAuditEngine = None  # type: ignore[assignment,misc]
    AuthAuditResult = None  # type: ignore[assignment,misc]
    _AUTH_AUDIT_AVAILABLE = False
    logger.debug("auth_audit not available; auth audit gate will skip.")

try:
    from src.dashboard.consistency_checker import CrossPlatformConsistencyChecker
    _CONSISTENCY_CHECKER_AVAILABLE = True
except ImportError:
    CrossPlatformConsistencyChecker = None  # type: ignore[assignment,misc]
    _CONSISTENCY_CHECKER_AVAILABLE = False
    logger.debug("consistency_checker not available; consistency gate will skip.")


# ── Configuration defaults ──────────────────────────────────────────

DEFAULT_SALARY_FLOOR = 145_000
DEFAULT_COVER_LETTER_MIN_WORDS = 250
DEFAULT_COVER_LETTER_MAX_WORDS = 800
DEFAULT_DESCRIPTION_MIN_LENGTH = 200
DEFAULT_ALIGNMENT_THRESHOLD = 50
DEFAULT_GHOST_CONFIDENCE_THRESHOLD = 25

# Technology keywords used by Gate 1 (Tool Authentication).
# Kept lowercase for case-insensitive matching.
TECH_KEYWORDS = [
    "python", "sql", "java", "javascript", "typescript", "go", "golang",
    "rust", "scala", "ruby", "c++", "c#", "r",
    "aws", "azure", "gcp", "google cloud",
    "docker", "kubernetes", "k8s", "terraform", "ansible", "pulumi",
    "spark", "kafka", "airflow", "dbt", "snowflake", "databricks",
    "redshift", "bigquery", "postgres", "postgresql", "mysql", "mongodb",
    "redis", "elasticsearch", "neo4j", "dynamodb", "cassandra",
    "react", "angular", "vue", "node", "django", "flask", "fastapi",
    "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy",
    "jenkins", "github actions", "ci/cd", "circleci", "gitlab",
    "linux", "bash", "powershell", "git",
    "tableau", "looker", "power bi", "grafana",
    "rest", "graphql", "grpc", "protobuf",
    "celery", "rabbitmq", "sqs", "kinesis",
    "s3", "ec2", "lambda", "ecs", "eks", "fargate",
    "datadog", "new relic", "splunk", "prometheus",
    "fivetran", "airbyte", "meltano", "prefect", "dagster",
    "delta lake", "iceberg", "hudi", "parquet", "avro",
]

# Resume section markers for Gate 11 (Resume Completeness).
RESUME_SECTIONS = {
    "experience": [
        r"experience", r"work\s+history", r"professional\s+background",
        r"employment",
    ],
    "skills": [
        r"skills", r"technologies", r"tech\s+stack", r"competencies",
        r"proficiencies",
    ],
    "education": [
        r"education", r"academic", r"degree", r"university", r"college",
        r"certification",
    ],
}


# ── Data classes ────────────────────────────────────────────────────


@dataclass
class QualityGateResult:
    """Outcome of a single quality gate check."""

    gate_name: str
    passed: bool
    severity: str  # "critical" | "warning" | "info"
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class QualityReport:
    """Aggregate report across all quality gates."""

    total_gates: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    results: List[QualityGateResult] = field(default_factory=list)
    overall_passed: bool = True
    score: int = 100  # 0-100

    def _recalculate(self) -> None:
        """Recompute summary fields from *results*."""
        self.total_gates = len(self.results)
        self.passed = sum(1 for r in self.results if r.passed)
        self.failed = sum(
            1 for r in self.results
            if not r.passed and r.severity in ("critical", "warning")
        )
        self.warnings = sum(
            1 for r in self.results
            if not r.passed and r.severity == "warning"
        )

        # overall_passed is False if any *critical* gate fails.
        self.overall_passed = all(
            r.passed for r in self.results if r.severity == "critical"
        )

        # Scoring: critical fail = -15 pts, warning fail = -8 pts,
        # info fail = -3 pts.  Floor at 0.
        deductions = 0
        for r in self.results:
            if not r.passed:
                if r.severity == "critical":
                    deductions += 15
                elif r.severity == "warning":
                    deductions += 8
                else:
                    deductions += 3
        self.score = max(0, 100 - deductions)


# ── Helpers ─────────────────────────────────────────────────────────


def _extract_tech_keywords(text: str) -> set:
    """Return the set of recognized tech keywords found in *text*."""
    text_lower = text.lower()
    found: set = set()
    for kw in TECH_KEYWORDS:
        # Word-boundary match to avoid substring false positives
        # (e.g. "go" inside "google").  For multi-word keywords we
        # just check substring presence.
        if " " in kw:
            if kw in text_lower:
                found.add(kw)
        else:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                found.add(kw)
    return found


def _extract_dollar_figures(text: str) -> List[str]:
    """Return dollar-amount strings like '$1.2M', '$500K', '$150,000'."""
    return re.findall(r"\$[\d,]+(?:\.\d+)?[KkMmBb]?", text)


def _extract_percentages(text: str) -> List[str]:
    """Return percentage strings like '35%', '2.5%'."""
    return re.findall(r"\d+(?:\.\d+)?%", text)


def _extract_titles(text: str) -> List[str]:
    """Heuristically extract job titles from text.

    Looks for capitalized phrases that commonly appear as titles.
    """
    title_patterns = [
        r"(?:Senior|Staff|Principal|Lead|Junior|Associate|Director|Manager|VP|Head)"
        r"(?:\s+(?:of\s+)?(?:\w+)){1,4}(?:\s+(?:Engineer|Developer|Analyst|Architect"
        r"|Scientist|Designer|Consultant|Administrator|Specialist|Coordinator))",
    ]
    titles: List[str] = []
    for pat in title_patterns:
        titles.extend(m.group(0).strip() for m in re.finditer(pat, text))
    return titles


def _find_long_overlapping_phrases(
    text_a: str, text_b: str, *, min_words: int = 6
) -> List[str]:
    """Return phrases of >= *min_words* consecutive words shared between texts."""
    words_a = text_a.lower().split()
    words_b_text = " ".join(text_b.lower().split())
    overlaps: List[str] = []

    for start in range(len(words_a) - min_words + 1):
        phrase = " ".join(words_a[start : start + min_words])
        if phrase in words_b_text:
            overlaps.append(phrase)

    return overlaps


# ── Individual gate implementations ────────────────────────────────


def _gate_tool_authentication(
    cover_letter: str, resume: str, **_: Any
) -> QualityGateResult:
    """Gate 1 — Tools mentioned in cover letter must exist in resume."""
    cl_techs = _extract_tech_keywords(cover_letter)
    resume_techs = _extract_tech_keywords(resume)

    unverified = cl_techs - resume_techs
    if unverified:
        return QualityGateResult(
            gate_name="Tool Authentication",
            passed=False,
            severity="critical",
            message=(
                f"Cover letter mentions {len(unverified)} tech(s) not in resume: "
                f"{', '.join(sorted(unverified))}"
            ),
            details={
                "unverified_techs": sorted(unverified),
                "cover_letter_techs": sorted(cl_techs),
                "resume_techs": sorted(resume_techs),
            },
        )
    return QualityGateResult(
        gate_name="Tool Authentication",
        passed=True,
        severity="critical",
        message=f"All {len(cl_techs)} tech keywords verified in resume.",
        details={"verified_techs": sorted(cl_techs)},
    )


def _gate_no_repetition(
    cover_letter: str, resume: str, **_: Any
) -> QualityGateResult:
    """Gate 2 — Cover letter must not parrot dollar figures, %, or long phrases."""
    issues: List[str] = []

    # Shared dollar figures
    cl_dollars = set(_extract_dollar_figures(cover_letter))
    resume_dollars = set(_extract_dollar_figures(resume))
    shared_dollars = cl_dollars & resume_dollars
    if shared_dollars:
        issues.append(f"Repeated dollar figures: {', '.join(sorted(shared_dollars))}")

    # Shared percentages
    cl_pcts = set(_extract_percentages(cover_letter))
    resume_pcts = set(_extract_percentages(resume))
    shared_pcts = cl_pcts & resume_pcts
    if shared_pcts:
        issues.append(f"Repeated percentages: {', '.join(sorted(shared_pcts))}")

    # Long overlapping phrases (>5 consecutive words)
    overlaps = _find_long_overlapping_phrases(cover_letter, resume, min_words=6)
    if overlaps:
        display = overlaps[:3]
        issues.append(
            f"{len(overlaps)} long phrase(s) copied from resume, e.g. "
            f"'{display[0]}'"
        )

    if issues:
        return QualityGateResult(
            gate_name="No-Repetition Rule",
            passed=False,
            severity="critical",
            message="; ".join(issues),
            details={
                "shared_dollars": sorted(shared_dollars) if shared_dollars else [],
                "shared_pcts": sorted(shared_pcts) if shared_pcts else [],
                "overlapping_phrases": overlaps[:5],
            },
        )
    return QualityGateResult(
        gate_name="No-Repetition Rule",
        passed=True,
        severity="critical",
        message="No repeated metrics or long phrases between resume and cover letter.",
    )


def _gate_title_consistency(
    cover_letter: str, resume: str, **_: Any
) -> QualityGateResult:
    """Gate 3 — Titles in cover letter should match resume (no inflation)."""
    cl_titles = _extract_titles(cover_letter)
    resume_titles = _extract_titles(resume)

    if not cl_titles:
        return QualityGateResult(
            gate_name="Title Consistency",
            passed=True,
            severity="critical",
            message="No job titles detected in cover letter to verify.",
        )

    resume_titles_lower = {t.lower() for t in resume_titles}
    inflated: List[str] = []
    for title in cl_titles:
        if title.lower() not in resume_titles_lower:
            inflated.append(title)

    if inflated:
        return QualityGateResult(
            gate_name="Title Consistency",
            passed=False,
            severity="critical",
            message=(
                f"Cover letter title(s) not in resume: "
                f"{', '.join(inflated)}"
            ),
            details={
                "cover_letter_titles": cl_titles,
                "resume_titles": resume_titles,
                "mismatched": inflated,
            },
        )
    return QualityGateResult(
        gate_name="Title Consistency",
        passed=True,
        severity="critical",
        message="All cover letter titles match resume.",
    )


def _gate_company_role_alignment(
    cover_letter: str, job: Dict[str, Any], **_: Any
) -> QualityGateResult:
    """Gate 4 — Cover letter should reference correct company and role."""
    company = (job.get("company") or job.get("company_name") or "").strip()
    title = (job.get("title") or job.get("job_title") or "").strip()
    issues: List[str] = []

    if company and company.lower() not in cover_letter.lower():
        issues.append(f"Company name '{company}' not found in cover letter")
    if title and title.lower() not in cover_letter.lower():
        issues.append(f"Job title '{title}' not found in cover letter")

    if issues:
        return QualityGateResult(
            gate_name="Company-Role Alignment",
            passed=False,
            severity="warning",
            message="; ".join(issues),
            details={"company": company, "title": title},
        )
    return QualityGateResult(
        gate_name="Company-Role Alignment",
        passed=True,
        severity="warning",
        message="Cover letter references correct company and role.",
    )


def _gate_ghost_job(job: Dict[str, Any], **_: Any) -> QualityGateResult:
    """Gate 5 — Flag likely ghost/stale postings."""
    if detect_ghost_job is None:
        return QualityGateResult(
            gate_name="Ghost Job Check",
            passed=True,
            severity="warning",
            message="Ghost detector unavailable; skipped.",
        )

    result = detect_ghost_job(job)
    if result.confidence > DEFAULT_GHOST_CONFIDENCE_THRESHOLD:
        return QualityGateResult(
            gate_name="Ghost Job Check",
            passed=False,
            severity="warning",
            message=f"Possible ghost job ({result.confidence}% confidence). "
                    f"{result.summary}",
            details={
                "confidence": result.confidence,
                "reasons": result.reasons,
                "signals_found": result.signals_found,
            },
        )
    return QualityGateResult(
        gate_name="Ghost Job Check",
        passed=True,
        severity="warning",
        message=f"Ghost confidence {result.confidence}% (below threshold).",
    )


def _gate_alignment_score(
    alignment_result: Optional[Dict[str, Any]] = None, **_: Any
) -> QualityGateResult:
    """Gate 6 — Alignment score should meet minimum threshold."""
    if alignment_result is None:
        return QualityGateResult(
            gate_name="Alignment Score Threshold",
            passed=True,
            severity="warning",
            message="No alignment result provided; skipped.",
        )

    score = alignment_result.get("alignment_score", alignment_result.get("score", 0))
    threshold = DEFAULT_ALIGNMENT_THRESHOLD

    if score < threshold:
        return QualityGateResult(
            gate_name="Alignment Score Threshold",
            passed=False,
            severity="warning",
            message=f"Alignment score {score} is below threshold {threshold}.",
            details={"alignment_score": score, "threshold": threshold},
        )
    return QualityGateResult(
        gate_name="Alignment Score Threshold",
        passed=True,
        severity="warning",
        message=f"Alignment score {score} meets threshold ({threshold}).",
    )


def _gate_salary_floor(
    job: Dict[str, Any],
    salary_floor: int = DEFAULT_SALARY_FLOOR,
    **_: Any,
) -> QualityGateResult:
    """Gate 7 — Salary minimum should meet floor."""
    salary_min = job.get("salary_min") or job.get("salary_minimum")
    if salary_min is None:
        return QualityGateResult(
            gate_name="Salary Floor Check",
            passed=True,
            severity="info",
            message="No salary information; skipped.",
        )

    try:
        salary_min = int(salary_min)
    except (ValueError, TypeError):
        return QualityGateResult(
            gate_name="Salary Floor Check",
            passed=True,
            severity="info",
            message=f"Non-numeric salary_min '{salary_min}'; skipped.",
        )

    if salary_min < salary_floor:
        return QualityGateResult(
            gate_name="Salary Floor Check",
            passed=False,
            severity="info",
            message=f"Salary minimum ${salary_min:,} is below floor ${salary_floor:,}.",
            details={"salary_min": salary_min, "salary_floor": salary_floor},
        )
    return QualityGateResult(
        gate_name="Salary Floor Check",
        passed=True,
        severity="info",
        message=f"Salary minimum ${salary_min:,} meets floor ${salary_floor:,}.",
    )


def _gate_remote_preference(job: Dict[str, Any], **_: Any) -> QualityGateResult:
    """Gate 8 — Flag on-site positions when preference is remote."""
    work_type = (
        job.get("work_type")
        or job.get("workplace_type")
        or job.get("remote_type")
        or ""
    ).lower()
    location = (job.get("location") or "").lower()

    is_remote = any(kw in work_type for kw in ("remote", "telecommute"))
    is_hybrid = "hybrid" in work_type
    location_remote = "remote" in location

    if is_remote or location_remote:
        return QualityGateResult(
            gate_name="Remote Preference",
            passed=True,
            severity="info",
            message="Position is remote.",
        )
    if is_hybrid:
        return QualityGateResult(
            gate_name="Remote Preference",
            passed=True,
            severity="info",
            message="Position is hybrid (acceptable).",
        )
    if work_type in ("on-site", "onsite", "in-office", "in office"):
        return QualityGateResult(
            gate_name="Remote Preference",
            passed=False,
            severity="info",
            message=f"Position is on-site (work_type='{work_type}').",
            details={"work_type": work_type, "location": location},
        )
    # Ambiguous — don't fail
    return QualityGateResult(
        gate_name="Remote Preference",
        passed=True,
        severity="info",
        message=f"Work type unclear ('{work_type}'); not flagged.",
    )


def _gate_description_quality(job: Dict[str, Any], **_: Any) -> QualityGateResult:
    """Gate 9 — Job description should be substantial and not ghost-like."""
    description = job.get("description") or ""
    issues: List[str] = []

    if len(description) < DEFAULT_DESCRIPTION_MIN_LENGTH:
        issues.append(
            f"Description too short ({len(description)} chars, "
            f"minimum {DEFAULT_DESCRIPTION_MIN_LENGTH})"
        )

    # Check for ghost language patterns
    if GHOST_PHRASES:
        ghost_matches = [
            pat.split(r"\s+")[0].replace("\\", "")
            for pat in GHOST_PHRASES
            if re.search(pat, description, re.IGNORECASE)
        ]
        if ghost_matches:
            issues.append(
                f"Ghost language detected: {', '.join(ghost_matches[:3])}"
            )

    if issues:
        return QualityGateResult(
            gate_name="Description Quality",
            passed=False,
            severity="warning",
            message="; ".join(issues),
            details={"description_length": len(description)},
        )
    return QualityGateResult(
        gate_name="Description Quality",
        passed=True,
        severity="warning",
        message=f"Description quality OK ({len(description)} chars).",
    )


def _gate_cover_letter_length(cover_letter: str, **_: Any) -> QualityGateResult:
    """Gate 10 — Cover letter should be 250-800 words."""
    word_count = len(cover_letter.split())
    min_words = DEFAULT_COVER_LETTER_MIN_WORDS
    max_words = DEFAULT_COVER_LETTER_MAX_WORDS

    if word_count < min_words:
        return QualityGateResult(
            gate_name="Cover Letter Length",
            passed=False,
            severity="warning",
            message=f"Cover letter too short ({word_count} words, minimum {min_words}).",
            details={"word_count": word_count, "min": min_words, "max": max_words},
        )
    if word_count > max_words:
        return QualityGateResult(
            gate_name="Cover Letter Length",
            passed=False,
            severity="warning",
            message=f"Cover letter too long ({word_count} words, maximum {max_words}).",
            details={"word_count": word_count, "min": min_words, "max": max_words},
        )
    return QualityGateResult(
        gate_name="Cover Letter Length",
        passed=True,
        severity="warning",
        message=f"Cover letter length OK ({word_count} words).",
    )


def _gate_resume_completeness(resume: str, **_: Any) -> QualityGateResult:
    """Gate 11 — Resume should contain key sections."""
    resume_lower = resume.lower()
    missing: List[str] = []

    for section, patterns in RESUME_SECTIONS.items():
        if not any(re.search(pat, resume_lower) for pat in patterns):
            missing.append(section)

    if missing:
        return QualityGateResult(
            gate_name="Resume Completeness",
            passed=False,
            severity="warning",
            message=f"Resume missing sections: {', '.join(missing)}.",
            details={"missing_sections": missing},
        )
    return QualityGateResult(
        gate_name="Resume Completeness",
        passed=True,
        severity="warning",
        message="Resume contains all expected sections.",
    )


def _gate_excluded_company(job: Dict[str, Any], **_: Any) -> QualityGateResult:
    """Gate 12 — Company must not be on the exclusion list."""
    company = (job.get("company") or job.get("company_name") or "").strip()
    if not company:
        return QualityGateResult(
            gate_name="Excluded Company Check",
            passed=True,
            severity="critical",
            message="No company name provided; skipped.",
        )

    if is_excluded_company(company):
        return QualityGateResult(
            gate_name="Excluded Company Check",
            passed=False,
            severity="critical",
            message=f"'{company}' is on the exclusion list.",
            details={"company": company},
        )
    return QualityGateResult(
        gate_name="Excluded Company Check",
        passed=True,
        severity="critical",
        message=f"'{company}' is not excluded.",
    )


def _gate_platform_formatting(
    cover_letter: str,
    target_platform: str = "resume",
    **_: Any,
) -> QualityGateResult:
    """Gate 13 — Cover letter format must match the target platform's requirements."""
    if not _PLATFORM_RULES_AVAILABLE:
        return QualityGateResult(
            gate_name="Platform Formatting",
            passed=True,
            severity="critical",
            message="platform_rules module unavailable; gate skipped.",
        )

    if not cover_letter:
        return QualityGateResult(
            gate_name="Platform Formatting",
            passed=True,
            severity="critical",
            message="No cover letter provided; platform formatting gate skipped.",
        )

    try:
        platform = Platform.from_string(target_platform)
    except ValueError as exc:
        return QualityGateResult(
            gate_name="Platform Formatting",
            passed=True,
            severity="critical",
            message=f"Unknown target platform '{target_platform}'; gate skipped. ({exc})",
        )

    validator = PlatformFormatValidator()
    result = validator.validate(cover_letter, platform)

    if not result.passed:
        return QualityGateResult(
            gate_name="Platform Formatting",
            passed=False,
            severity="critical",
            message=result.summary(),
            details={
                "platform": platform.value,
                "violations": result.violations,
                "suggestions": result.suggestions,
            },
        )

    # Also check for platform mismatch (e.g. LinkedIn narrative sent to Indeed)
    is_mismatch, mismatch_msg = validator.detect_platform_mismatch(cover_letter, platform)
    if is_mismatch:
        return QualityGateResult(
            gate_name="Platform Formatting",
            passed=False,
            severity="critical",
            message=mismatch_msg,
            details={"platform": platform.value, "mismatch": True},
        )

    return QualityGateResult(
        gate_name="Platform Formatting",
        passed=True,
        severity="critical",
        message=result.summary(),
        details={"platform": platform.value},
    )


def _gate_authentication_audit(
    cover_letter: str,
    resume: str,
    employment_history: Optional[List] = None,
    **_: Any,
) -> QualityGateResult:
    """Gate 14 — Authenticity audit: cover letter claims must trace to resume."""
    if not _AUTH_AUDIT_AVAILABLE:
        return QualityGateResult(
            gate_name="Authentication Audit",
            passed=True,
            severity="critical",
            message="auth_audit module unavailable; gate skipped.",
        )

    if not cover_letter or not resume:
        return QualityGateResult(
            gate_name="Authentication Audit",
            passed=True,
            severity="critical",
            message="Cover letter or resume missing; authentication audit skipped.",
        )

    result = AuthAuditEngine().audit(cover_letter, resume, employment_history)

    if not result.passed:
        critical = result.critical_violations()
        descriptions = "; ".join(v.description[:120] for v in critical[:3])
        return QualityGateResult(
            gate_name="Authentication Audit",
            passed=False,
            severity="critical",
            message=(
                f"Auth audit failed ({len(critical)} critical violation(s)): {descriptions}"
            ),
            details={
                "authenticity_score": result.authenticity_score,
                "violations": [
                    {
                        "type": v.violation_type.value,
                        "severity": v.severity,
                        "description": v.description,
                        "suggestion": v.suggestion,
                    }
                    for v in result.violations
                ],
            },
        )

    if result.warning_violations():
        warnings = result.warning_violations()
        return QualityGateResult(
            gate_name="Authentication Audit",
            passed=True,
            severity="critical",
            message=(
                f"Auth audit passed (score {result.authenticity_score}) with "
                f"{len(warnings)} warning(s)."
            ),
            details={"authenticity_score": result.authenticity_score},
        )

    return QualityGateResult(
        gate_name="Authentication Audit",
        passed=True,
        severity="critical",
        message=f"Auth audit passed. Authenticity score: {result.authenticity_score}/100.",
        details={"authenticity_score": result.authenticity_score},
    )


def _gate_cross_platform_consistency(
    cover_letter: str,
    resume: str,
    linkedin_snapshot: Optional[str] = None,
    **_: Any,
) -> QualityGateResult:
    """Gate 15 — Cross-platform consistency: resume, cover letter, and LinkedIn must agree."""
    if not _CONSISTENCY_CHECKER_AVAILABLE:
        return QualityGateResult(
            gate_name="Cross-Platform Consistency",
            passed=True,
            severity="warning",
            message="consistency_checker module unavailable; gate skipped.",
        )

    if not cover_letter or not resume:
        return QualityGateResult(
            gate_name="Cross-Platform Consistency",
            passed=True,
            severity="warning",
            message="Cover letter or resume missing; consistency gate skipped.",
        )

    report = CrossPlatformConsistencyChecker().check(resume, cover_letter, linkedin_snapshot)

    if not report.passed:
        issues = [i for i in report.inconsistencies if i.severity.value == "critical"]
        descriptions = "; ".join(i.description[:120] for i in issues[:3])
        return QualityGateResult(
            gate_name="Cross-Platform Consistency",
            passed=False,
            severity="warning",
            message=(
                f"Consistency check failed ({report.critical_count} critical issue(s)): "
                f"{descriptions}"
            ),
            details={
                "critical_count": report.critical_count,
                "warning_count": report.warning_count,
                "inconsistencies": [
                    {
                        "field": i.field,
                        "severity": i.severity.value,
                        "description": i.description,
                        "document_a": i.document_a,
                        "document_b": i.document_b,
                    }
                    for i in report.inconsistencies
                ],
            },
        )

    if report.warning_count:
        return QualityGateResult(
            gate_name="Cross-Platform Consistency",
            passed=True,
            severity="warning",
            message=(
                f"Consistency check passed with {report.warning_count} warning(s). "
                f"{report.summary()}"
            ),
            details={
                "warning_count": report.warning_count,
                "inconsistencies": [
                    {"field": i.field, "severity": i.severity.value, "description": i.description}
                    for i in report.inconsistencies
                ],
            },
        )

    return QualityGateResult(
        gate_name="Cross-Platform Consistency",
        passed=True,
        severity="warning",
        message=report.summary(),
    )


# ── Orchestrator ────────────────────────────────────────────────────

# Ordered list of gate functions. Each receives keyword args and picks
# what it needs via **_.
_GATE_FUNCTIONS: List[Callable[..., QualityGateResult]] = [
    _gate_tool_authentication,       # 1
    _gate_no_repetition,             # 2
    _gate_title_consistency,         # 3
    _gate_company_role_alignment,    # 4
    _gate_ghost_job,                 # 5
    _gate_alignment_score,           # 6
    _gate_salary_floor,              # 7
    _gate_remote_preference,         # 8
    _gate_description_quality,       # 9
    _gate_cover_letter_length,       # 10
    _gate_resume_completeness,       # 11
    _gate_excluded_company,          # 12
    _gate_platform_formatting,       # 13
    _gate_authentication_audit,      # 14
    _gate_cross_platform_consistency, # 15
]


def run_quality_gates(
    job: Dict[str, Any],
    resume_text: str,
    cover_letter_text: str,
    alignment_result: Optional[Dict[str, Any]] = None,
    *,
    salary_floor: int = DEFAULT_SALARY_FLOOR,
    target_platform: str = "resume",
    employment_history: Optional[List] = None,
    linkedin_snapshot: Optional[str] = None,
) -> QualityReport:
    """
    Execute all 12 quality gates and return an aggregate report.

    Args:
        job: Job posting dict (keys: company, title, description,
             salary_min, work_type, location, etc.).
        resume_text: Full text of the candidate's resume.
        cover_letter_text: Full text of the generated cover letter.
        alignment_result: Optional dict from alignment scoring
            (expects 'alignment_score' or 'score' key).
        salary_floor: Minimum acceptable salary (default $145,000).

    Returns:
        QualityReport with per-gate results and overall score.
    """
    report = QualityReport()

    kwargs = {
        "job": job,
        "resume": resume_text,
        "cover_letter": cover_letter_text,
        "alignment_result": alignment_result,
        "salary_floor": salary_floor,
        "target_platform": target_platform,
        "employment_history": employment_history,
        "linkedin_snapshot": linkedin_snapshot,
    }

    for gate_fn in _GATE_FUNCTIONS:
        try:
            result = gate_fn(**kwargs)
        except Exception as exc:
            logger.exception("Gate %s raised an exception", gate_fn.__name__)
            result = QualityGateResult(
                gate_name=gate_fn.__name__.replace("_gate_", "").replace("_", " ").title(),
                passed=False,
                severity="warning",
                message=f"Gate raised an exception: {exc}",
                details={"exception": str(exc)},
            )
        report.results.append(result)

    report._recalculate()
    return report
