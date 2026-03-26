"""
Role Type Classifier — sklearn TF-IDF + LogisticRegression.

Classifies job titles into broad role buckets to catch non-engineering
roles early (before expensive downstream gate processing).

Classes:
  ENGINEERING_IC  — SWE, DE, SRE, platform, backend, fullstack, ML engineer
  SALES           — AE, SDR, BDR, solutions consultant, GTM, customer success
  MANAGEMENT      — EM, Director, VP, Head of, C-suite
  DESIGN          — UX, product designer, design lead
  OPERATIONS      — PM, analyst, BizOps, project manager, HR, finance, legal
  OTHER           — catch-all for ambiguous titles

Fallback strategy (when model not trained / sklearn unavailable):
  Uses heuristic word-boundary keyword matching — same keyword sets
  used as training bootstrap labels.

Training: run  scripts/train_role_classifier.py  once to create the model file.
Model file: models/role_classifier.joblib
"""

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

ROLE_LABELS = [
    "ENGINEERING_IC",
    "SALES",
    "MANAGEMENT",
    "DESIGN",
    "OPERATIONS",
    "OTHER",
]

DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "role_classifier.joblib"


# ── Heuristic keyword sets ──────────────────────────────────────────────
# Used as both runtime fallback AND bootstrap training labels.
# Patterns are word-boundary matched (case-insensitive).

HEURISTIC_KEYWORDS: Dict[str, list] = {
    "ENGINEERING_IC": [
        "software engineer", "software developer", "data engineer",
        "backend engineer", "frontend engineer", "fullstack engineer",
        "full stack engineer", "full-stack engineer",
        "platform engineer", "infrastructure engineer",
        "site reliability engineer", "sre", "devops engineer",
        "ml engineer", "machine learning engineer", "ai engineer",
        "analytics engineer", "analytics engineering", "data platform engineer",
        "staff engineer", "principal engineer", "senior engineer",
        "python developer", "python engineer", "api engineer",
        "cloud engineer", "security engineer", "data scientist",
        "solutions architect",   # technical implementation role
    ],
    "SALES": [
        "account executive", "account manager",
        "sales development representative", "sdr", "bdr",
        "business development representative",
        "sales engineer",   # pre-sales, not IC engineering
        "solutions engineer",   # pre-sales variant
        "inside sales", "outbound sales", "field sales",
        "sales representative", "sales manager", "sales specialist",
        "customer success manager", "customer success",
        "go-to-market", "gtm",
        "revenue operations", "revops",
        "growth manager", "partnerships manager",
    ],
    "MANAGEMENT": [
        "engineering manager", "em ",
        "director of engineering", "engineering director",
        "vp of engineering", "vp engineering", "vice president",
        "head of engineering", "head of data", "head of platform",
        "cto", "chief technology", "chief data",
        "director of data", "vp of data",
        "director, software", "director, data",
        "director, platform",
        "technical program manager",  # management-track TPM
    ],
    "DESIGN": [
        "ux designer", "ux researcher", "ui designer",
        "product designer", "visual designer", "design lead",
        "interaction designer", "service designer",
        "senior designer",
    ],
    "OPERATIONS": [
        "product manager", "product owner", "senior pm",
        "project manager", "program manager",
        "business analyst", "data analyst", "reporting analyst",
        "operations manager", "business operations",
        "hr manager", "recruiter", "talent acquisition",
        "finance manager", "financial analyst", "accountant",
        "marketing manager", "content manager", "seo",
        "office manager", "administrative",
        "compliance analyst", "risk analyst",
        "procurement manager",
        # Mobile/wrong-discipline IC roles — not Python/data engineering
        "mobile developer", "mobile engineer", "mobile architect",
        "mobile devops", "ios developer", "android developer",
    ],
}

# Pre-compiled word-boundary patterns per label
_HEURISTIC_PATTERNS: Dict[str, list] = {}

def _get_heuristic_patterns() -> Dict[str, list]:
    global _HEURISTIC_PATTERNS
    if not _HEURISTIC_PATTERNS:
        for label, keywords in HEURISTIC_KEYWORDS.items():
            _HEURISTIC_PATTERNS[label] = [
                re.compile(
                    r"(?<![a-zA-Z0-9])" + re.escape(kw.lower()) + r"(?![a-zA-Z0-9])"
                )
                for kw in keywords
            ]
    return _HEURISTIC_PATTERNS


# ── Result dataclass ────────────────────────────────────────────────────
@dataclass
class RoleClassification:
    label: str                         # one of ROLE_LABELS
    confidence: float                  # 0.0 – 1.0
    probabilities: Dict[str, float] = field(default_factory=dict)
    source: str = "heuristic"          # "model" | "heuristic" | "unavailable"
    matched_keyword: str = ""


# ── Main classifier class ───────────────────────────────────────────────
class RoleClassifier:
    """
    Sklearn TF-IDF + LogisticRegression role classifier with heuristic fallback.

    Usage:
        clf = RoleClassifier()
        result = clf.predict("Senior Software Engineer")
        print(result.label, result.confidence)
    """

    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self._model_path = model_path
        self._pipeline = None       # sklearn Pipeline, loaded lazily
        self._sklearn_ok: Optional[bool] = None
        self._model_loaded: Optional[bool] = None

    # ── sklearn availability check ───────────────────────────────────
    def _check_sklearn(self) -> bool:
        if self._sklearn_ok is None:
            try:
                import sklearn  # noqa: F401
                import joblib   # noqa: F401
                self._sklearn_ok = True
            except ImportError:
                self._sklearn_ok = False
                logger.debug("sklearn/joblib not available; role classifier uses heuristic only")
        return self._sklearn_ok

    # ── model lazy-load ──────────────────────────────────────────────
    def _load_model(self) -> bool:
        if self._model_loaded is not None:
            return self._model_loaded
        self._model_loaded = False

        if not self._check_sklearn():
            return False
        if not self._model_path.exists():
            logger.info(
                "Role classifier model not found at %s. "
                "Run scripts/train_role_classifier.py to train. "
                "Using heuristic fallback.",
                self._model_path,
            )
            return False

        try:
            import joblib
            self._pipeline = joblib.load(self._model_path)
            self._model_loaded = True
            logger.debug("Role classifier model loaded from %s", self._model_path)
        except Exception as e:
            logger.warning("Failed to load role classifier model: %s", e)

        return self._model_loaded

    def is_model_loaded(self) -> bool:
        return self._load_model()

    # ── Main prediction ──────────────────────────────────────────────
    def predict(self, title: str, description: str = "") -> RoleClassification:
        """
        Classify a job title into a role bucket.

        Args:
            title:       Job title string (required)
            description: First 300 characters of JD (optional, improves accuracy)

        Returns:
            RoleClassification with label and confidence
        """
        text = title.strip()
        if description:
            # Prefix title twice to give it more weight over description snippet
            text = f"{title} {title} {description[:300]}"

        if self._load_model():
            return self._model_predict(text)
        return self._heuristic_predict(title)

    def _model_predict(self, text: str) -> RoleClassification:
        try:
            proba = self._pipeline.predict_proba([text])[0]
            classes = self._pipeline.classes_
            idx = proba.argmax()
            label = classes[idx]
            confidence = float(proba[idx])
            return RoleClassification(
                label=label,
                confidence=confidence,
                probabilities={c: float(p) for c, p in zip(classes, proba)},
                source="model",
            )
        except Exception as e:
            logger.warning("Model prediction failed: %s — falling back to heuristic", e)
            return self._heuristic_predict(text)

    def _heuristic_predict(self, title: str) -> RoleClassification:
        """Keyword-based fallback using word-boundary regex matching."""
        title_lower = title.lower()
        patterns = _get_heuristic_patterns()

        matches: Dict[str, str] = {}  # label → first matched keyword

        for label, compiled in patterns.items():
            for pat in compiled:
                if pat.search(title_lower):
                    matches[label] = pat.pattern
                    break

        if not matches:
            return RoleClassification(
                label="OTHER",
                confidence=0.50,
                source="heuristic",
                matched_keyword="",
            )

        # If exactly one label matched, return it with high confidence
        if len(matches) == 1:
            label = next(iter(matches))
            return RoleClassification(
                label=label,
                confidence=0.82,
                source="heuristic",
                matched_keyword=matches[label],
            )

        # Multiple labels matched (e.g. "Sales Engineering Manager"):
        # Priority order: MANAGEMENT > SALES > ENGINEERING_IC > OPERATIONS > DESIGN > OTHER
        priority = ["MANAGEMENT", "SALES", "ENGINEERING_IC", "OPERATIONS", "DESIGN", "OTHER"]
        for lbl in priority:
            if lbl in matches:
                return RoleClassification(
                    label=lbl,
                    confidence=0.65,  # lower confidence when ambiguous
                    source="heuristic",
                    matched_keyword=matches[lbl],
                )

        return RoleClassification(label="OTHER", confidence=0.50, source="heuristic")


# ── Module-level singleton ──────────────────────────────────────────────
_classifier: Optional[RoleClassifier] = None


def get_role_classifier() -> RoleClassifier:
    """Return the module-level shared RoleClassifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = RoleClassifier()
    return _classifier
