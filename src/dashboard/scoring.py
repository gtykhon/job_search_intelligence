"""
Alignment Scoring — Local lightweight scoring engine.

Scores job descriptions against the user's resume/skills profile.
Runs entirely locally (no AI API calls) using keyword matching.
Ported from job_search/src/integrations/ai/scoring/engine.py.
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)

try:
    from src.dashboard.duty_coverage import DutyCoverageEngine, DutyCoverageResult
    _DUTY_COVERAGE_AVAILABLE = True
except ImportError:
    DutyCoverageEngine = None  # type: ignore[assignment,misc]
    DutyCoverageResult = None  # type: ignore[assignment]
    _DUTY_COVERAGE_AVAILABLE = False

try:
    from src.intelligence.semantic_scorer import get_semantic_scorer as _get_semantic_scorer
    _SEMANTIC_AVAILABLE = True
except ImportError:
    _get_semantic_scorer = None  # type: ignore[assignment]
    _SEMANTIC_AVAILABLE = False


class ProficiencyLevel(Enum):
    EXPERT = "expert"
    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"
    BASIC = "basic"
    MINIMAL = "minimal"

    @classmethod
    def from_score(cls, score: float) -> "ProficiencyLevel":
        if score >= 90: return cls.EXPERT
        if score >= 75: return cls.ADVANCED
        if score >= 50: return cls.INTERMEDIATE
        if score >= 25: return cls.BASIC
        return cls.MINIMAL


class Recommendation(Enum):
    PROCEED = "proceed"
    FLAG = "flag"
    NO_PROCEED = "no_proceed"


@dataclass
class CategoryScore:
    category: str
    score: float
    weight: float
    weighted_score: float
    proficiency: ProficiencyLevel
    matched_items: List[str] = field(default_factory=list)
    gap_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "score": self.score,
            "weight": self.weight,
            "proficiency": self.proficiency.value,
            "matched": self.matched_items,
            "gaps": self.gap_items,
        }


@dataclass
class AlignmentResult:
    overall_score: float
    recommendation: Recommendation
    interpretation: str
    categories: List[CategoryScore] = field(default_factory=list)
    critical_gaps: List[str] = field(default_factory=list)
    duty_coverage_pct: Optional[float] = None
    duty_coverage_tier: Optional[str] = None
    space_allocation: Optional[dict] = None
    semantic_score: Optional[float] = None      # sentence-transformer cosine×100
    blended_score: Optional[float] = None       # 0.60×keyword + 0.40×semantic

    def to_dict(self) -> Dict:
        return {
            "overall_score": self.overall_score,
            "recommendation": self.recommendation.value,
            "interpretation": self.interpretation,
            "categories": [c.to_dict() for c in self.categories],
            "critical_gaps": self.critical_gaps,
        }


# Weight templates per role type
WEIGHT_TEMPLATES = {
    "engineering": {
        "technical_skills": 0.45,
        "experience": 0.25,
        "domain_knowledge": 0.15,
        "soft_skills": 0.10,
        "education": 0.05,
    },
    "analyst": {
        "technical_skills": 0.35,
        "experience": 0.25,
        "domain_knowledge": 0.20,
        "soft_skills": 0.10,
        "education": 0.10,
    },
}

# Keywords that need word-boundary matching regardless of length
# (e.g., "rest" matches "restore", "access" matches "accessible")
_WORD_BOUNDARY_KEYWORDS = {
    "access", "rest", "async", "excel", "fitz", "agile", "scrum",
    "lead", "react", "docker", "linux", "celery", "poetry", "jira",
    "go", "r", "c", "rust", "swift", "dart", "ruby", "scala", "bash",
    "spark", "kafka", "redis", "flask", "django", "spring", "rails",
    "vue", "next", "nest", "helm", "kong", "vault",
    # Security acronyms (short/ambiguous — need word boundaries)
    "sca", "sso", "mfa", "waf", "ids", "ips", "vpn", "tls", "ssl",
    "pki", "cve", "edr", "xdr", "siem", "soar", "nist", "rbac", "ldap",
    "iast", "rasp", "cvss",
}

# Technical skills — user's verified resume skills (Tier 1 & Tier 2)
# Used to identify what the user CAN match against.
TECH_KEYWORDS = {
    "access", "agile", "alembic", "api", "async", "azure", "azure blob storage",
    "azure devops", "azure form recognizer", "celery", "ci/cd", "claude api", "compliance",
    "data engineering", "data warehouse", "docker", "etl", "etl pipeline", "excel", "fastapi",
    "fitz", "git", "javascript", "jinja2", "jira", "langflow", "linux", "llm",
    "machine learning", "microservices", "microsoft access", "n8n", "node.js", "nodejs",
    "ocr", "ollama", "oracle", "pandas", "pdf", "poetry", "postgres", "postgresql",
    "power bi", "pymupdf", "python", "r", "rag", "react", "rest", "rpa", "scrum", "sql",
    "sqlite", "tableau", "tesseract", "uipath", "vba", "vs code", "whisper",
}

# Broad industry tech vocabulary for extracting skills FROM JOB DESCRIPTIONS.
# Includes common technologies the user may NOT have — needed for gap detection.
JD_TECH_KEYWORDS = TECH_KEYWORDS | {
    # Languages the user doesn't have
    "java", "go", "golang", "rust", "c++", "c#", "typescript", "scala",
    "kotlin", "swift", "ruby", "perl", "php", "haskell", "elixir", "dart",
    "objective-c", "groovy", "lua", "matlab", "bash", "shell",
    # Cloud platforms
    "aws", "gcp", "google cloud", "amazon web services",
    "s3", "ec2", "lambda", "ecs", "eks", "fargate", "sagemaker",
    "bigquery", "cloud functions", "cloud run", "dataflow",
    # Container & orchestration
    "kubernetes", "k8s", "openshift", "terraform", "ansible",
    "puppet", "chef", "vagrant", "helm", "istio",
    # Databases & data stores
    "mongodb", "mysql", "mariadb", "cassandra", "dynamodb", "couchdb",
    "redis", "memcached", "elasticsearch", "neo4j", "snowflake",
    "redshift", "databricks", "delta lake",
    # Big data & streaming
    "spark", "hadoop", "kafka", "flink", "airflow", "dbt",
    "hive", "presto", "trino",
    # Frameworks & libraries
    "spring", "spring boot", "django", "flask", "express",
    "angular", "vue", "svelte", "next.js", "nuxt",
    "rails", "ruby on rails", ".net", "asp.net", "blazor",
    "graphql", "grpc", "protobuf",
    # ML/AI expanded
    "tensorflow", "pytorch", "keras", "scikit-learn", "hugging face",
    "mlflow", "kubeflow", "opencv", "spacy", "nltk",
    "deep learning", "neural network", "transformers",
    # DevOps & CI/CD
    "jenkins", "github actions", "gitlab ci", "circleci", "argocd",
    "prometheus", "grafana", "datadog", "splunk", "new relic",
    "nginx", "apache", "traefik", "kong",
    # Security — Application Security (AppSec)
    "oauth", "saml", "jwt", "vault", "iam",
    "sast", "dast", "mast", "iast", "rasp",
    "sonarqube", "checkmarx", "fortify", "veracode", "snyk", "semgrep",
    "owasp", "owasp top 10", "secure coding", "code review",
    # Security — DevSecOps / SDLC
    "devsecops", "sdlc", "secure sdlc", "shift left",
    "sca", "software composition analysis", "dependency scanning",
    "container security", "image scanning", "trivy", "aqua", "prisma cloud",
    "secrets management", "secret scanning",
    # Security — Vulnerability Management
    "vulnerability scanning", "vulnerability management", "vulnerability remediation",
    "penetration testing", "pen testing", "red team", "blue team", "purple team",
    "cve", "cvss", "nist", "cis benchmarks",
    "nessus", "qualys", "rapid7", "tenable",
    # Security — Security Operations
    "siem", "soar", "xdr", "edr",
    "incident response", "threat detection", "threat modeling",
    "crowdstrike", "sentinel", "palo alto",
    # Security — Identity & Access Management
    "sso", "mfa", "zero trust", "rbac", "ldap", "active directory",
    "okta", "auth0", "keycloak",
    # Security — Compliance Frameworks
    "soc 2", "iso 27001", "fedramp", "hipaa", "pci dss", "gdpr",
    "nist 800-53", "cmmc", "fisma",
    "cybersecurity", "information security", "infosec",
    # Security — Infrastructure Security
    "waf", "ids", "ips", "firewall", "vpn",
    "tls", "ssl", "encryption", "pki", "certificate management",
    "network security", "endpoint security", "cloud security",
    # Mobile
    "react native", "flutter", "android", "ios",
    # Messaging & queues
    "rabbitmq", "sqs", "sns", "pub/sub", "nats",
    # Product & PM tools
    "product management", "figma", "sketch",
    "confluence", "notion",
}

# Soft skills — synonym-aware matching.
# Each canonical skill maps to a list of phrases that should all be treated
# as equivalent.  If *any* synonym appears in the text, the canonical skill
# is considered present.
SOFT_SKILL_SYNONYMS: Dict[str, List[str]] = {
    "leadership":             ["leadership", "lead", "led teams", "led a team", "team lead",
                               "managed a team", "direct reports", "supervised"],
    "communication":          ["communication", "communicating", "written communication",
                               "verbal communication", "presenting", "presentations",
                               "public speaking"],
    "collaboration":          ["collaboration", "collaborative", "collaborating",
                               "cross-functional teams", "team-oriented", "teamwork",
                               "team player", "partnered with", "worked closely",
                               "worked with stakeholders", "interdisciplinary"],
    "teamwork":               ["teamwork", "team player", "team-oriented",
                               "collaborative", "collaboration", "cross-functional teams"],
    "mentoring":              ["mentoring", "mentored", "coaching", "coached",
                               "training junior", "onboarding", "knowledge sharing"],
    "problem solving":        ["problem solving", "problem-solving", "troubleshooting",
                               "root cause analysis", "debugging", "analytical thinking",
                               "critical thinking"],
    "analytical":             ["analytical", "analysis", "data-driven", "quantitative",
                               "metrics-driven", "data analysis", "statistical"],
    "stakeholder management": ["stakeholder management", "stakeholder engagement",
                               "client-facing", "client management", "executive reporting",
                               "managing expectations", "stakeholders"],
    "cross-functional":       ["cross-functional", "cross functional", "interdisciplinary",
                               "multi-team", "matrixed", "collaborative teams"],
    "agile":                  ["agile", "agile methodology", "agile environment",
                               "agile development", "sprint", "sprints", "kanban"],
    "scrum":                  ["scrum", "scrum master", "sprint planning",
                               "daily standup", "retrospective"],
    "project management":     ["project management", "program management",
                               "project planning", "project delivery", "pmp",
                               "managing projects", "project lifecycle"],
    "knowledge transfer":     ["knowledge transfer", "knowledge sharing", "documentation",
                               "training materials", "runbooks", "onboarding docs"],
    "documentation":          ["documentation", "documenting", "technical writing",
                               "technical documentation", "runbooks", "wiki",
                               "confluence", "readme"],
    "technical training":     ["technical training", "training sessions", "workshops",
                               "led training", "conducted training", "tech talks"],
    "requirements gathering": ["requirements gathering", "requirements analysis",
                               "business requirements", "user stories",
                               "functional requirements", "elicitation"],
}

# Flat set for backward compatibility (used by other modules if needed)
SOFT_SKILLS = set(SOFT_SKILL_SYNONYMS.keys())

# Domain keywords — derived from master experience verified engagements
DOMAIN_KEYWORDS = {
    # Verified domain experience (Tier 1)
    "fintech", "financial", "banking", "mortgage", "lending",
    "federal", "government", "regulatory", "compliance",
    "securities", "capital markets", "credit", "loan",
    "budget", "fiscal", "audit",
    "analytics", "data platform", "real-time",
    "devops", "infrastructure",
    "machine learning", "ai", "automation", "cloud",
    "api", "microservices",
    # Verified adjacent domains
    "etl", "data pipeline", "reporting", "data warehouse",
    "document processing", "ocr",
}


# Domain context validation — ambiguous keywords need adjacent term verification
DOMAIN_CONTEXT_MAP = {
    "credit": {
        "valid": {"fintech", "lending", "loan", "mortgage", "banking",
                  "credit risk", "credit score", "credit bureau", "credit operations"},
        "penalty": {"academic credit", "tax credit", "credit union teller"},
    },
    "infrastructure": {
        "valid": {"cloud", "aws", "azure", "kubernetes", "terraform",
                  "devops", "deployment", "ci/cd", "platform", "docker"},
        "penalty": {"physical infrastructure", "construction", "building",
                    "hvac", "electrical", "mechanical", "data center build",
                    "cooling", "commissioning"},
    },
    "compliance": {
        "valid": {"data", "regulatory", "automation", "reporting",
                  "engineering", "fintech", "pipeline", "python"},
        "penalty": {"compliance officer", "legal counsel", "audit manager",
                    "chief compliance"},
    },
}


# Non-target role functions — detected by JD keywords, apply score penalty
NON_TARGET_FUNCTION_SIGNALS = {
    "implementation_engineering": [
        "implementation engineer", "integrations engineer", "onboarding",
        "partner integration", "customer engineering", "launch timelines",
        "post-live", "go-live", "b2b partners", "b2b integration",
        "technical account", "customer-facing deployment",
    ],
    "solutions_architecture": [
        "solutions architect", "solutions engineer", "pre-sales",
        "proof of concept", "poc", "demo environment", "rfp",
        "sales engineer", "customer demos",
    ],
    "technical_account_management": [
        "technical account manager", "tam ", "customer success engineer",
        "customer support engineer", "post-sale", "renewal",
        "customer health", "escalation management",
    ],
    "devops_sre": [
        "site reliability", "sre ", "on-call rotation", "incident response",
        "pagerduty", "runbook", "toil reduction",
    ],
    "frontend_engineering": [
        "frontend engineer", "front-end engineer", "ui engineer",
        "react developer", "angular developer", "vue developer",
        "css ", "responsive design", "web developer",
    ],
}
ROLE_FUNCTION_PENALTY = 20  # points deducted for non-target function

# Title equivalence groups for experience scoring
TITLE_GROUPS = {
    "data_engineering": {
        "data engineer", "analytics engineer", "etl developer",
        "data platform engineer", "pipeline engineer", "data architect",
        "ml engineer", "machine learning engineer",
    },
    "data_analysis": {
        "data analyst", "business intelligence analyst", "bi developer",
        "bi analyst", "reporting analyst", "insights analyst",
        "quantitative analyst",
    },
    "business_analysis": {
        "business analyst", "business systems analyst", "systems analyst",
        "requirements analyst", "process analyst",
    },
    "implementation": {
        "implementation engineer", "integrations engineer",
        "solutions engineer", "technical account manager",
        "customer engineer", "onboarding engineer",
    },
    "leadership": {
        "engineering manager", "technical manager", "director of engineering",
        "vp of engineering", "head of data", "team lead",
    },
}
TARGET_TITLE_GROUPS = {"data_engineering", "data_analysis", "business_analysis"}


def _keyword_in_text(kw: str, text: str) -> bool:
    """Match keyword in text, using word-boundary regex for short/ambiguous keywords."""
    if len(kw) <= 3 or kw in _WORD_BOUNDARY_KEYWORDS:
        return bool(re.search(r'\b' + re.escape(kw) + r'\b', text))
    return kw in text


def get_user_added_skills() -> Set[str]:
    """Load user-added skills from DB settings (persisted across restarts)."""
    try:
        from src.dashboard.db import DashboardDB
        import json as _json
        db = DashboardDB()
        raw = db.get_setting("user_added_skills", "[]")
        return set(_json.loads(raw))
    except Exception:
        return set()


def get_user_removed_skills() -> Set[str]:
    """Load user-excluded skills from DB settings (skills user says they don't have)."""
    try:
        from src.dashboard.db import DashboardDB
        import json as _json
        db = DashboardDB()
        raw = db.get_setting("user_removed_skills", "[]")
        return set(_json.loads(raw))
    except Exception:
        return set()


class AlignmentScorer:
    """Local alignment scoring engine."""

    def __init__(self, resume_text: str = "", enable_semantic_filter: bool = True):
        self.resume_text = resume_text
        self._resume_skills: Optional[Set[str]] = None
        self._classifier = None
        self._duty_engine = None  # Cached DutyCoverageEngine (created once per resume)
        self._semantic_filter_enabled = enable_semantic_filter
        # Merge user-added skills into TECH_KEYWORDS at init
        self._user_skills = get_user_added_skills()
        # Load user-excluded skills (skills user says they don't have)
        self._removed_skills = get_user_removed_skills()
        if self._user_skills:
            logger.debug("Loaded %d user-added skills: %s",
                         len(self._user_skills), self._user_skills)
        if self._removed_skills:
            logger.debug("Loaded %d user-excluded skills: %s",
                         len(self._removed_skills), self._removed_skills)

    @property
    def classifier(self):
        if self._classifier is None and self._semantic_filter_enabled:
            try:
                from src.dashboard.semantic_classifier import SemanticClassifier
                self._classifier = SemanticClassifier()
            except ImportError:
                logger.debug("semantic_classifier not available; skipping pre-filter")
                self._semantic_filter_enabled = False
        return self._classifier

    def set_resume(self, resume_text: str):
        self.resume_text = resume_text
        self._resume_skills = None
        self._duty_engine = None  # Invalidate cached engine

    @property
    def duty_engine(self):
        """Cached DutyCoverageEngine — created once per resume, reused for all jobs."""
        if self._duty_engine is None and _DUTY_COVERAGE_AVAILABLE and self.resume_text:
            try:
                self._duty_engine = DutyCoverageEngine(self.resume_text)
            except Exception as e:
                logger.debug("Failed to create DutyCoverageEngine: %s", e)
        return self._duty_engine

    @property
    def resume_skills(self) -> Set[str]:
        if self._resume_skills is None:
            # Include user-added skills in the vocabulary
            vocab = TECH_KEYWORDS | self._user_skills
            self._resume_skills = self._extract_skills(self.resume_text, vocab)
            # User-added skills are always considered "present" in resume
            # (user clicked "I have this skill")
            self._resume_skills |= self._user_skills
            # Remove skills the user has explicitly excluded
            # (user says "I don't have this skill")
            if self._removed_skills:
                self._resume_skills -= self._removed_skills
        return self._resume_skills

    def score(self, job_description: str, job_title: str = "") -> AlignmentResult:
        """Score a job description against the resume."""
        if not self.resume_text:
            return AlignmentResult(
                overall_score=0,
                recommendation=Recommendation.NO_PROCEED,
                interpretation="No resume configured",
            )

        # ── Semantic pre-filter: flag category mismatches but still score ──
        _category_warning: Optional[str] = None
        if self.classifier is not None:
            try:
                classification = self.classifier.classify(job_title, job_description)
                if not classification.should_score:
                    _category_warning = (
                        f"Category flag: {classification.category} "
                        f"({classification.confidence:.0%}). "
                        f"{classification.reason}"
                    )
            except Exception as e:
                logger.debug("Semantic pre-filter error (fail-open): %s", e)

        role_type = self._classify_role(job_title, job_description)
        weights = WEIGHT_TEMPLATES.get(role_type, WEIGHT_TEMPLATES["engineering"])

        job_skills = self._extract_skills(job_description, JD_TECH_KEYWORDS)
        job_required = self._extract_required_skills(job_description)
        job_preferred = self._extract_preferred_skills(job_description)
        resume_lower = self.resume_text.lower()
        jd_lower = job_description.lower()

        categories = []
        for category, weight in weights.items():
            cat = self._score_category(
                category, weight, resume_lower, jd_lower,
                self.resume_skills, job_skills, job_required, job_title,
                job_preferred=job_preferred,
            )
            categories.append(cat)

        # Weighted overall
        total_weight = sum(c.weight for c in categories)
        overall = sum(c.weighted_score for c in categories) / total_weight if total_weight else 0
        overall = min(max(overall, 0), 100)

        # Role function penalty — detect non-target job functions
        _function_flag = self._detect_non_target_function(jd_lower, job_title)
        if _function_flag:
            overall = max(overall - ROLE_FUNCTION_PENALTY, 0)

        critical_gaps = sorted(job_required - self.resume_skills)
        if _function_flag:
            critical_gaps.insert(0, f"Role function: {_function_flag}")
        if _category_warning:
            critical_gaps.insert(0, _category_warning)
        recommendation = self._recommend(overall, critical_gaps)
        interpretation = self._interpret(overall, categories, critical_gaps)

        result = AlignmentResult(
            overall_score=round(overall, 1),
            recommendation=recommendation,
            interpretation=interpretation,
            categories=categories,
            critical_gaps=critical_gaps[:10],
        )

        # Duty coverage scoring (F2) — uses cached engine
        if self.duty_engine is not None:
            try:
                _dc_result = self.duty_engine.score(job_description)
                result.duty_coverage_pct = _dc_result.coverage_pct
                result.duty_coverage_tier = _dc_result.tier
                result.space_allocation = _dc_result.space_allocation
            except Exception as _e:
                logger.debug("Duty coverage scoring failed (non-critical): %s", _e)

        # Semantic alignment scoring (optional — sentence-transformers)
        # Skip semantic scoring for low-keyword-score jobs (< 25) — not worth the
        # ~20s embedding cost when keyword match is already very poor.
        _SEMANTIC_KEYWORD_THRESHOLD = 25
        if (
            _SEMANTIC_AVAILABLE
            and self.resume_text
            and _get_semantic_scorer is not None
            and result.overall_score >= _SEMANTIC_KEYWORD_THRESHOLD
        ):
            try:
                _sem_scorer = _get_semantic_scorer(resume_text=self.resume_text)
                if _sem_scorer.is_available():
                    _sem = _sem_scorer.score(job_description, job_title)
                    if _sem is not None:
                        result.semantic_score = _sem.score_0_100
                        # Blend: keyword score anchors, semantic adds context
                        result.blended_score = round(
                            result.overall_score * 0.60 + _sem.score_0_100 * 0.40, 1
                        )
                        logger.debug(
                            "Semantic score: %.1f  |  blended: %.1f  (keyword: %.1f)",
                            _sem.score_0_100, result.blended_score, result.overall_score,
                        )
            except Exception as _se:
                logger.debug("Semantic scoring failed (non-critical): %s", _se)
        elif result.overall_score < _SEMANTIC_KEYWORD_THRESHOLD:
            logger.debug(
                "Skipping semantic scoring — keyword score %.1f < %d threshold",
                result.overall_score, _SEMANTIC_KEYWORD_THRESHOLD,
            )

        return result

    # ── Batch scoring (keyword + batch semantic) ─────────────────────
    def score_keyword_only(self, job_description: str, job_title: str = "") -> AlignmentResult:
        """Score using only keyword matching — no semantic embedding.

        Used by batch scoring to separate the fast keyword phase from the
        expensive semantic phase, enabling batch embedding afterwards.
        """
        if not self.resume_text:
            return AlignmentResult(
                overall_score=0,
                recommendation=Recommendation.NO_PROCEED,
                interpretation="No resume configured",
            )

        # Keyword-only pre-filter (NO LLM calls — use classify_keyword instead
        # of classify to avoid ~1s Ollama call per job)
        _category_warning: Optional[str] = None
        if self.classifier is not None:
            try:
                classification = self.classifier.classify_keyword(job_title, job_description)
                if not classification.should_score:
                    _category_warning = (
                        f"Category flag: {classification.category} "
                        f"({classification.confidence:.0%}). "
                        f"{classification.reason}"
                    )
            except Exception as e:
                logger.debug("Keyword pre-filter error (fail-open): %s", e)

        role_type = self._classify_role(job_title, job_description)
        weights = WEIGHT_TEMPLATES.get(role_type, WEIGHT_TEMPLATES["engineering"])

        job_skills = self._extract_skills(job_description, JD_TECH_KEYWORDS)
        job_required = self._extract_required_skills(job_description)
        job_preferred = self._extract_preferred_skills(job_description)
        resume_lower = self.resume_text.lower()
        jd_lower = job_description.lower()

        categories = []
        for category, weight in weights.items():
            cat = self._score_category(
                category, weight, resume_lower, jd_lower,
                self.resume_skills, job_skills, job_required, job_title,
                job_preferred=job_preferred,
            )
            categories.append(cat)

        total_weight = sum(c.weight for c in categories)
        overall = sum(c.weighted_score for c in categories) / total_weight if total_weight else 0
        overall = min(max(overall, 0), 100)

        # Role function penalty
        _function_flag = self._detect_non_target_function(jd_lower, job_title)
        if _function_flag:
            overall = max(overall - ROLE_FUNCTION_PENALTY, 0)

        critical_gaps = sorted(job_required - self.resume_skills)
        if _function_flag:
            critical_gaps.insert(0, f"Role function: {_function_flag}")
        if _category_warning:
            critical_gaps.insert(0, _category_warning)
        recommendation = self._recommend(overall, critical_gaps)
        interpretation = self._interpret(overall, categories, critical_gaps)

        result = AlignmentResult(
            overall_score=round(overall, 1),
            recommendation=recommendation,
            interpretation=interpretation,
            categories=categories,
            critical_gaps=critical_gaps[:10],
        )

        # Duty coverage (fast, no embedding) — uses cached engine
        if self.duty_engine is not None:
            try:
                _dc_result = self.duty_engine.score(job_description)
                result.duty_coverage_pct = _dc_result.coverage_pct
                result.duty_coverage_tier = _dc_result.tier
                result.space_allocation = _dc_result.space_allocation
            except Exception as _e:
                logger.debug("Duty coverage scoring failed (non-critical): %s", _e)

        return result

    def apply_batch_semantic(
        self,
        results: list,
        descriptions: list,
        titles: list,
        keyword_threshold: float = 25.0,
    ) -> int:
        """Apply batch semantic scoring to pre-computed keyword results.

        Only jobs with keyword score >= threshold get semantic embeddings.
        Uses score_batch() for massive speedup (~100x vs one-at-a-time).

        Args:
            results: List of AlignmentResult from score_keyword_only()
            descriptions: Corresponding job descriptions
            titles: Corresponding job titles
            keyword_threshold: Min keyword score to warrant semantic scoring

        Returns:
            Number of results that received semantic scores
        """
        if not _SEMANTIC_AVAILABLE or not self.resume_text or _get_semantic_scorer is None:
            logger.debug("Semantic scoring unavailable — skipping batch semantic")
            return 0

        sem_scorer = _get_semantic_scorer(resume_text=self.resume_text)
        if not sem_scorer.is_available():
            return 0

        # Collect indices of jobs that pass the keyword threshold
        eligible_indices = []
        eligible_descs = []
        eligible_titles = []
        for i, result in enumerate(results):
            if result.overall_score >= keyword_threshold:
                eligible_indices.append(i)
                eligible_descs.append(descriptions[i])
                eligible_titles.append(titles[i])

        if not eligible_indices:
            logger.info("Batch semantic: 0/%d jobs above keyword threshold %.0f",
                        len(results), keyword_threshold)
            return 0

        logger.info(
            "Batch semantic: encoding %d/%d eligible jobs (keyword >= %.0f)...",
            len(eligible_indices), len(results), keyword_threshold,
        )

        # Batch encode all eligible JDs at once
        semantic_scores = sem_scorer.score_batch(eligible_descs, eligible_titles)

        applied = 0
        for idx, sem_score in zip(eligible_indices, semantic_scores):
            if sem_score is not None:
                results[idx].semantic_score = sem_score.score_0_100
                results[idx].blended_score = round(
                    results[idx].overall_score * 0.60 + sem_score.score_0_100 * 0.40, 1
                )
                applied += 1

        logger.info(
            "Batch semantic: applied %d scores (%d skipped below threshold)",
            applied, len(results) - len(eligible_indices),
        )
        return applied

    def score_with_llm(self, job_description: str, job_title: str = "", db=None,
                       model: str = None, provider: str = "ollama") -> AlignmentResult:
        """Score using LLM-based skill extraction with keyword fallback.

        Uses Ollama or Claude to extract skills from the JD, then
        fuzzy-matches them. Falls back to keyword scoring on any failure.

        Args:
            job_description: The job description text.
            job_title: The job title.
            db: DashboardDB instance for caching (optional).
            model: Model name (e.g. "llama3.1:8b" or "claude-sonnet-4-20250514").
            provider: "ollama" or "claude".
        """
        try:
            return self._score_with_llm_impl(job_description, job_title, db,
                                             model=model, provider=provider)
        except Exception as e:
            logger.warning("LLM scoring failed, falling back to keyword: %s", e)
            return self.score(job_description, job_title)

    def _score_with_llm_impl(self, job_description: str, job_title: str, db,
                             model: str = None, provider: str = "ollama") -> AlignmentResult:
        """Internal LLM scoring implementation.

        Uses LLM to extract skills FROM THE JD (catches things keyword dicts miss),
        then matches against the resume's curated TECH_KEYWORDS (more reliable than
        LLM resume extraction). Falls back to keyword scoring on failure.
        """
        from src.dashboard.llm_skill_extractor import (
            LLMSkillExtractor, SkillExtractionResult, SkillMatchResult, content_hash,
        )

        if model:
            extractor = LLMSkillExtractor(model=model, provider=provider)
        else:
            extractor = LLMSkillExtractor()
        if not extractor.is_available():
            logger.info("LLM not available for scoring (provider=%s), falling back to keyword", provider)
            return self.score(job_description, job_title)

        # ── Extract JD skills via LLM (with caching) ──
        jd_hash = content_hash(job_description, "jd")
        jd_skills = None
        if db:
            cached = db.get_cached_skills(jd_hash)
            if cached:
                jd_skills = SkillExtractionResult.from_dict(cached)
                jd_skills.source = "cache"
                logger.info("JD skills loaded from cache (%d tech, %d soft)",
                            len(jd_skills.technical_skills), len(jd_skills.soft_skills))

        if jd_skills is None:
            logger.info("Extracting JD skills via LLM...")
            jd_skills = extractor.extract_skills(job_description, "jd", title=job_title)
            if db:
                db.cache_skills(jd_hash, "jd", jd_skills.to_dict(), extractor.model)
            logger.info("JD skills extracted: %d tech, %d soft — %s",
                        len(jd_skills.technical_skills), len(jd_skills.soft_skills),
                        jd_skills.technical_skills)

        # ── Safeguard: if LLM extracted too few skills from a substantial JD,
        #    supplement with keyword-based extraction to avoid inflated scores ──
        jd_lower = job_description.lower()
        if len(jd_skills.technical_skills) <= 3 and len(job_description) > 1000:
            keyword_skills = [kw for kw in JD_TECH_KEYWORDS
                              if _keyword_in_text(kw, jd_lower)]
            # Add keyword-found skills that LLM missed
            llm_lower = {s.lower() for s in jd_skills.technical_skills}
            supplemented = []
            for kw in keyword_skills:
                if kw.lower() not in llm_lower:
                    supplemented.append(kw)
                    llm_lower.add(kw.lower())
            if supplemented:
                logger.info("LLM extracted too few skills (%d), supplementing with %d keyword skills: %s",
                            len(jd_skills.technical_skills), len(supplemented), supplemented)
                jd_skills.technical_skills.extend(supplemented)
                # Update cache with supplemented list
                if db:
                    db.cache_skills(jd_hash, "jd", jd_skills.to_dict(), extractor.model)

        # ── Match LLM-extracted JD skills against resume's keyword-based skills ──
        # Use keyword matching for resume (curated TECH_KEYWORDS is more reliable)
        resume_keyword_skills = list(self.resume_skills)  # From TECH_KEYWORDS
        resume_as_extraction = SkillExtractionResult(
            technical_skills=resume_keyword_skills,
            soft_skills=list(SOFT_SKILLS),  # All soft skills the user claims
            source="keywords",
        )

        match_results = extractor.match_skills(jd_skills, resume_as_extraction)
        tech_match = match_results["technical"]
        soft_match = match_results["soft"]

        logger.info("LLM match: %d/%d tech matched (%.0f%%), gaps: %s",
                    len(tech_match.matched), len(jd_skills.technical_skills),
                    tech_match.match_ratio * 100, tech_match.gap_names)

        # ── Build category scores ──
        role_type = self._classify_role(job_title, job_description)
        weights = WEIGHT_TEMPLATES.get(role_type, WEIGHT_TEMPLATES["engineering"])
        resume_lower = self.resume_text.lower()
        jd_lower = job_description.lower()

        categories = []
        for category, weight in weights.items():
            if category == "technical_skills":
                tech_score = tech_match.match_ratio * 100 if jd_skills.technical_skills else 50
                categories.append(CategoryScore(
                    category="technical_skills",
                    score=round(tech_score, 1),
                    weight=weight,
                    weighted_score=round(tech_score * weight, 1),
                    proficiency=ProficiencyLevel.from_score(tech_score),
                    matched_items=tech_match.matched_names,
                    gap_items=tech_match.gap_names,
                ))
            elif category == "soft_skills":
                # Use keyword-based soft skill scoring (synonym-aware, more reliable)
                cat = self._score_soft(weight, resume_lower, jd_lower)
                categories.append(cat)
            else:
                # Experience, domain, education — use existing keyword methods
                cat = self._score_category(
                    category, weight, resume_lower, jd_lower,
                    self.resume_skills, set(), set(), job_title,
                )
                categories.append(cat)

        # ── Compute overall ──
        total_weight = sum(c.weight for c in categories)
        overall = sum(c.weighted_score for c in categories) / total_weight if total_weight else 0
        overall = min(max(overall, 0), 100)

        critical_gaps = tech_match.gap_names[:10]
        recommendation = self._recommend(overall, critical_gaps)
        interpretation = self._interpret(overall, categories, critical_gaps)

        return AlignmentResult(
            overall_score=round(overall, 1),
            recommendation=recommendation,
            interpretation=interpretation,
            categories=categories,
            critical_gaps=critical_gaps,
        )

    def _classify_role(self, title: str, description: str) -> str:
        title_lower = title.lower()
        # BSA track
        if re.search(r"business\s+systems\s+analyst|systems\s+analyst|\bbsa\b", title_lower):
            return "bsa"
        if re.search(r"(credit|loan|mortgage|operations)\s+(operations\s+)?analyst", title_lower):
            return "bsa"
        # Analyst track
        if re.search(r"(data|business|reporting|intelligence|financial)\s+analyst", title_lower):
            return "analyst"
        if "analyst" in title_lower:
            return "analyst"
        # Leadership track
        if re.search(r"(engineering|technical|software)\s+manager", title_lower):
            return "leadership"
        if re.search(r"\b(director|vp|head\s+of)\b", title_lower):
            return "leadership"
        return "engineering"

    @staticmethod
    def _detect_non_target_function(jd_lower: str, job_title: str) -> Optional[str]:
        """Detect if the JD describes a non-target role function.
        Returns the function name if detected, None otherwise.
        Requires 2+ signal keywords to trigger (avoids false positives).
        """
        title_lower = job_title.lower()
        for function_name, signals in NON_TARGET_FUNCTION_SIGNALS.items():
            hits = sum(1 for s in signals if s in jd_lower or s in title_lower)
            if hits >= 2:
                return function_name.replace("_", " ")
        return None

    @staticmethod
    def _get_title_group(title: str) -> Optional[str]:
        """Find which title equivalence group a job title belongs to."""
        title_lower = title.lower()
        for group, titles in TITLE_GROUPS.items():
            if any(t in title_lower for t in titles):
                return group
        return None

    def _score_category(
        self, category, weight, resume_lower, jd_lower,
        resume_skills, job_skills, job_required, job_title,
        job_preferred=None,
    ) -> CategoryScore:
        if category == "technical_skills":
            return self._score_technical(weight, resume_skills, job_skills, job_required, job_preferred)
        elif category == "experience":
            return self._score_experience(weight, resume_lower, jd_lower, job_title)
        elif category == "domain_knowledge":
            return self._score_domain(weight, resume_lower, jd_lower)
        elif category == "soft_skills":
            return self._score_soft(weight, resume_lower, jd_lower)
        elif category == "education":
            return self._score_education(weight, resume_lower, jd_lower)
        return CategoryScore(
            category=category, score=50, weight=weight,
            weighted_score=50 * weight, proficiency=ProficiencyLevel.INTERMEDIATE,
        )

    def _score_technical(self, weight, resume_skills, job_skills, job_required, job_preferred=None):
        if not job_skills:
            return CategoryScore(
                category="technical_skills", score=50, weight=weight,
                weighted_score=50 * weight, proficiency=ProficiencyLevel.INTERMEDIATE,
            )
        PREFERRED_WEIGHT = 0.30

        required_matched = resume_skills & job_required if job_required else set()
        preferred_skills = (job_preferred or set()) | (job_skills - job_required)
        preferred_matched = resume_skills & preferred_skills

        effective_matches = len(required_matched) + len(preferred_matched) * PREFERRED_WEIGHT
        effective_total = len(job_required) + len(preferred_skills) * PREFERRED_WEIGHT
        score = min((effective_matches / effective_total) * 100, 100) if effective_total > 0 else 50

        all_matched = required_matched | preferred_matched
        gaps = job_required - resume_skills
        return CategoryScore(
            category="technical_skills", score=round(score, 1), weight=weight,
            weighted_score=round(score * weight, 1),
            proficiency=ProficiencyLevel.from_score(score),
            matched_items=sorted(all_matched), gap_items=sorted(gaps),
        )

    def _score_experience(self, weight, resume_lower, jd_lower, job_title):
        score = 50.0
        matched, gaps = [], []
        resume_years = self._extract_max_years(resume_lower)
        req_years = self._extract_required_years(jd_lower)
        if req_years > 0:
            if resume_years >= req_years:
                score += 25
                matched.append(f"{resume_years}+ years")
            else:
                score -= (req_years - resume_years) * 5
                gaps.append(f"Needs {req_years}y, has ~{resume_years}")
        if job_title:
            # Title group matching — cross-group = 0 credit, same group = full
            jd_group = self._get_title_group(job_title)
            if jd_group and jd_group not in TARGET_TITLE_GROUPS:
                # Non-target title group (implementation, leadership, etc.)
                gaps.append("Title mismatch")
            elif jd_group:
                # Check if user's resume mentions any title from the same group
                same_group_titles = TITLE_GROUPS.get(jd_group, set())
                if any(t in resume_lower for t in same_group_titles):
                    score += 25
                    matched.append("Title alignment")
                else:
                    gaps.append("Title mismatch")
            else:
                # Unknown group — fallback to word overlap
                title_words = set(job_title.lower().split())
                ratio = sum(1 for w in title_words if w in resume_lower) / max(len(title_words), 1)
                score += ratio * 25
                if ratio > 0.5:
                    matched.append("Title alignment")
        score = min(max(score, 0), 100)
        return CategoryScore(
            category="experience", score=round(score, 1), weight=weight,
            weighted_score=round(score * weight, 1),
            proficiency=ProficiencyLevel.from_score(score),
            matched_items=matched, gap_items=gaps,
        )

    def _score_domain(self, weight, resume_lower, jd_lower):
        # Augment resume text with user-added skills for domain matching
        augmented_resume = resume_lower
        if self._user_skills:
            augmented_resume = resume_lower + " " + " ".join(self._user_skills)
        domain = [kw for kw in DOMAIN_KEYWORDS if _keyword_in_text(kw, jd_lower)]
        if not domain:
            return CategoryScore(
                category="domain_knowledge", score=50, weight=weight,
                weighted_score=50 * weight, proficiency=ProficiencyLevel.INTERMEDIATE,
            )
        matched = [kw for kw in domain if _keyword_in_text(kw, augmented_resume)]
        gaps = [kw for kw in domain if not _keyword_in_text(kw, augmented_resume)]

        # Domain context penalty: if an ambiguous keyword matches but the JD
        # context suggests a different domain, reduce effective match count.
        context_penalty = 0
        for kw in matched:
            if kw in DOMAIN_CONTEXT_MAP:
                ctx = DOMAIN_CONTEXT_MAP[kw]
                has_valid = any(adj in jd_lower for adj in ctx["valid"])
                has_penalty = any(adj in jd_lower for adj in ctx["penalty"])
                if has_penalty and not has_valid:
                    context_penalty += 1

        effective_matched = max(len(matched) - context_penalty, 0)
        score = min((effective_matched / len(domain)) * 100, 100)
        return CategoryScore(
            category="domain_knowledge", score=round(score, 1), weight=weight,
            weighted_score=round(score * weight, 1),
            proficiency=ProficiencyLevel.from_score(score),
            matched_items=matched, gap_items=gaps,
        )

    @staticmethod
    def _has_synonym(text: str, canonical: str) -> bool:
        """Check if any synonym of *canonical* appears in *text*."""
        synonyms = SOFT_SKILL_SYNONYMS.get(canonical, [canonical])
        return any(syn in text for syn in synonyms)

    def _score_soft(self, weight, resume_lower, jd_lower):
        # A canonical skill is "required" if any of its synonyms appear in the JD
        job_soft = {s for s in SOFT_SKILL_SYNONYMS if self._has_synonym(jd_lower, s)}
        if not job_soft:
            return CategoryScore(
                category="soft_skills", score=60, weight=weight,
                weighted_score=60 * weight, proficiency=ProficiencyLevel.INTERMEDIATE,
            )
        # Augment resume text with user-added skills
        augmented = resume_lower
        if self._user_skills:
            augmented = resume_lower + " " + " ".join(self._user_skills)
        # A skill is "matched" if any synonym appears in the resume or user-added skills
        matched = {s for s in job_soft if self._has_synonym(augmented, s)}
        gaps = job_soft - matched
        score = min((len(matched) / len(job_soft)) * 100, 100)
        return CategoryScore(
            category="soft_skills", score=round(score, 1), weight=weight,
            weighted_score=round(score * weight, 1),
            proficiency=ProficiencyLevel.from_score(score),
            matched_items=sorted(matched), gap_items=sorted(gaps),
        )

    def _score_education(self, weight, resume_lower, jd_lower):
        degrees = {"phd": 100, "doctorate": 100, "masters": 85, "ms ": 85,
                    "mba": 85, "bachelors": 70, "bs ": 70, "ba ": 70}
        resume_deg = max((v for d, v in degrees.items() if d in resume_lower), default=0)
        req_deg = max((v for d, v in degrees.items() if d in jd_lower), default=0)
        if req_deg > 0:
            score = 90 if resume_deg >= req_deg else max(30, resume_deg / req_deg * 80)
        elif resume_deg > 0:
            score = 75
        else:
            score = 50
        return CategoryScore(
            category="education", score=round(score, 1), weight=weight,
            weighted_score=round(score * weight, 1),
            proficiency=ProficiencyLevel.from_score(score),
        )

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _strip_benefits_section(text: str) -> str:
        """Remove benefits/boilerplate sections that cause false-positive skill matches."""
        # Cut everything after common benefits headers
        patterns = [
            r"(?:great )?benefits (?:for|include|package)",
            r"our (?:people|colleagues|comprehensive)",
            r"we take pride in our.+?benefits",
            r"in addition to our competitive",
            r"(?:^|\n)\s*benefits\s*(?:\n|$)",
        ]
        text_lower = text.lower()
        earliest = len(text_lower)
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m and m.start() < earliest:
                earliest = m.start()
        return text[:earliest] if earliest < len(text_lower) else text

    @staticmethod
    def _extract_skills(text: str, vocabulary: Set[str] = None) -> Set[str]:
        """Extract skills from text using the given vocabulary (defaults to TECH_KEYWORDS).

        Strips benefits/boilerplate sections first to avoid false positives
        (e.g. 'retiree medical access' matching the 'access' keyword).
        """
        cleaned = AlignmentScorer._strip_benefits_section(text)
        text_lower = cleaned.lower()
        vocab = vocabulary if vocabulary is not None else TECH_KEYWORDS
        return {kw for kw in vocab if _keyword_in_text(kw, text_lower)}

    @staticmethod
    def _extract_required_skills(job_description: str) -> Set[str]:
        cleaned = AlignmentScorer._strip_benefits_section(job_description)
        jd_lower = cleaned.lower()
        section = ""
        match = re.search(
            r"(?:required|requirements|must have|qualifications).*?(?=preferred|nice to have|bonus|\Z)",
            jd_lower, re.DOTALL,
        )
        if match:
            section = match.group()
        else:
            section = jd_lower
        return {kw for kw in JD_TECH_KEYWORDS if _keyword_in_text(kw, section)}

    @staticmethod
    def _extract_preferred_skills(job_description: str) -> Set[str]:
        """Extract skills from preferred/nice-to-have sections only."""
        cleaned = AlignmentScorer._strip_benefits_section(job_description)
        jd_lower = cleaned.lower()
        match = re.search(
            r"(?:preferred|nice to have|bonus|desired)\s*(?:qualifications|skills|experience)?.*?(?=\Z)",
            jd_lower, re.DOTALL,
        )
        if not match:
            return set()
        section = match.group()
        return {kw for kw in JD_TECH_KEYWORDS if _keyword_in_text(kw, section)}

    @staticmethod
    def _extract_max_years(text: str) -> int:
        ranges = re.findall(r"\((\d{4})\s*[-\u2013\u2014]\s*(\d{4}|present)\)", text)
        max_y = 0
        for start, end in ranges:
            end_year = 2026 if end.lower() == "present" else int(end)
            max_y = max(max_y, end_year - int(start))
        for y in re.findall(r"(\d+)\+?\s*years", text):
            max_y = max(max_y, int(y))
        return max_y

    @staticmethod
    def _extract_required_years(text: str) -> int:
        matches = re.findall(r"(\d+)\+?\s*years?\s*(?:of\s+)?experience", text)
        return max((int(m) for m in matches), default=0)

    @staticmethod
    def _recommend(overall: float, gaps: list) -> Recommendation:
        if overall >= 70 and len(gaps) <= 2:
            return Recommendation.PROCEED
        if overall >= 50 or len(gaps) <= 3:
            return Recommendation.FLAG
        return Recommendation.NO_PROCEED

    @staticmethod
    def _interpret(overall, categories, gaps) -> str:
        level = ProficiencyLevel.from_score(overall)
        parts = [f"{overall:.0f}% ({level.value})"]
        if gaps:
            parts.append(f"Gaps: {', '.join(gaps[:3])}")
        if categories:
            strongest = max(categories, key=lambda c: c.score)
            weakest = min(categories, key=lambda c: c.score)
            parts.append(f"Strong: {strongest.category.replace('_', ' ')} ({strongest.score:.0f}%)")
            if weakest.category != strongest.category:
                parts.append(f"Weak: {weakest.category.replace('_', ' ')} ({weakest.score:.0f}%)")
        return " | ".join(parts)
