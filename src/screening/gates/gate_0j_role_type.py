"""
Gate 0J -- Role Type Classification

Classifies job titles into broad role buckets and rejects non-engineering roles
before any downstream gate processing (saves tech stack, alignment, and LLM work).

Order: 12 — runs immediately after company research (10), before RED keywords (15).

Decision logic:
  - ENGINEERING_IC         → PASS unconditionally
  - SALES / MANAGEMENT     → FAIL (no override) at high confidence
  - DESIGN / OPERATIONS    → FAIL (no override) at high confidence
  - Any label, low conf    → OVERRIDE_REQUIRED (uncertain classification)
  - OTHER                  → PASS (catch-all — don't block ambiguous titles)

Confidence threshold (default 0.75, configurable via role_type_confidence):
  - >= threshold AND excluded label  → FAIL
  - <  threshold AND excluded label  → OVERRIDE_REQUIRED

Model: sklearn TF-IDF + LogisticRegression loaded from models/role_classifier.joblib
Fallback: heuristic keyword table (no model file needed for operation)
"""

import logging

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate

logger = logging.getLogger(__name__)

# Labels that are hard-failed (engineering pipeline only)
_EXCLUDED_LABELS = {"SALES", "MANAGEMENT", "DESIGN", "OPERATIONS"}

# Labels that always pass (IC engineering + catch-all)
_ACCEPTED_LABELS = {"ENGINEERING_IC", "OTHER"}

# Default minimum confidence to act on a classification
_DEFAULT_CONFIDENCE_THRESHOLD = 0.75


@register_gate
class RoleTypeGate(BaseGate):
    """Gate 0J — role type classification using sklearn or heuristic fallback."""

    @property
    def name(self) -> str:
        return "0J_role_type"

    @property
    def order(self) -> int:
        return 12

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, "enable_gate_0j", True)

    async def _evaluate(self, job) -> GateVerdict:
        title = (getattr(job, "title", "") or "").strip()
        description = (getattr(job, "description", "") or "")

        if not title:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.PASS,
                reason="No title available — role type check skipped",
                confidence=0.0,
                metadata={"skipped": True},
            )

        try:
            from src.intelligence.role_classifier import get_role_classifier
        except ImportError:
            logger.warning("role_classifier module unavailable; Gate 0J skipping")
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.PASS,
                reason="role_classifier unavailable; gate skipped",
                confidence=0.0,
                metadata={"skipped": True},
            )

        threshold = _DEFAULT_CONFIDENCE_THRESHOLD
        if self.config:
            threshold = getattr(self.config, "role_type_confidence", threshold)

        classifier = get_role_classifier()
        classification = classifier.predict(title, description[:300])

        meta = {
            "role_label": classification.label,
            "confidence": classification.confidence,
            "source": classification.source,
            "matched_keyword": classification.matched_keyword,
            "threshold": threshold,
        }

        # Accepted labels → always PASS
        if classification.label in _ACCEPTED_LABELS:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.PASS,
                reason=f"Role type: {classification.label} ({classification.confidence:.0%}) — engineering IC",
                confidence=classification.confidence,
                metadata=meta,
            )

        # Excluded labels — check confidence level
        if classification.label in _EXCLUDED_LABELS:
            if classification.confidence >= threshold:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason=(
                        f"Non-engineering role: {classification.label} "
                        f"({classification.confidence:.0%} confidence) — "
                        f"pipeline targets engineering IC only"
                    ),
                    confidence=classification.confidence,
                    override_eligible=False,
                    metadata=meta,
                )
            else:
                # Low confidence — don't auto-reject; flag for review
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.OVERRIDE_REQUIRED,
                    reason=(
                        f"Possible non-engineering role: {classification.label} "
                        f"({classification.confidence:.0%} confidence, below threshold {threshold:.0%}) "
                        f"— verify title is an IC engineering role"
                    ),
                    confidence=classification.confidence,
                    override_eligible=True,
                    metadata=meta,
                )

        # Fallback: any other label → PASS
        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason=f"Role type: {classification.label} — no exclusion rule",
            confidence=classification.confidence,
            metadata=meta,
        )
