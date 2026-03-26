"""
Gate 0I -- Alignment Score Floor

Filters jobs with very low alignment scores relative to the candidate profile.

Score used (in priority order):
  1. Blended score  = 0.60 × keyword_score + 0.40 × semantic_score
     (when semantic_alignment_score is available on the job object)
  2. keyword alignment_score alone
  3. semantic_alignment_score alone (when keyword score is absent)
  4. Neither present → PASS (cannot evaluate)

Thresholds (configurable via ScreeningConfig):
  - Hard floor (align_hard_floor):  score < 40  → FAIL   (severe mismatch)
  - Soft floor (align_soft_floor):  score < 60  → OVERRIDE_REQUIRED (marginal match)
  - No score data:                  score is None → PASS  (cannot evaluate)

Gate runs at order=55 — after tech stack (50), before compensation (60).
"""

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate

_DEFAULT_HARD_FLOOR = 40
_DEFAULT_SOFT_FLOOR = 60

# Blend weights: keyword score is the anchor, semantic adds semantic context
_KW_WEIGHT = 0.60
_SEM_WEIGHT = 0.40


@register_gate
class AlignmentScoreGate(BaseGate):

    @property
    def name(self) -> str:
        return "0I_alignment_score"

    @property
    def order(self) -> int:
        return 55

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0i', True)

    async def _evaluate(self, job) -> GateVerdict:
        kw_score = getattr(job, 'alignment_score', None)
        sem_score = getattr(job, 'semantic_alignment_score', None)

        # Coerce available scores to float
        def _safe_float(v):
            if v is None:
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        kw_score = _safe_float(kw_score)
        sem_score = _safe_float(sem_score)

        # Determine effective score and label
        if kw_score is not None and sem_score is not None:
            score = round(kw_score * _KW_WEIGHT + sem_score * _SEM_WEIGHT, 1)
            score_label = f"blended({kw_score:.1f}×{_KW_WEIGHT}+{sem_score:.1f}×{_SEM_WEIGHT})"
        elif kw_score is not None:
            score = kw_score
            score_label = "keyword"
        elif sem_score is not None:
            score = sem_score
            score_label = "semantic"
        else:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.PASS,
                reason="No alignment score available — cannot evaluate",
                confidence=0.0,
                metadata={"alignment_score": None, "semantic_alignment_score": None},
            )

        hard_floor = _DEFAULT_HARD_FLOOR
        soft_floor = _DEFAULT_SOFT_FLOOR
        if self.config:
            hard_floor = getattr(self.config, 'align_hard_floor', _DEFAULT_HARD_FLOOR)
            soft_floor = getattr(self.config, 'align_soft_floor', _DEFAULT_SOFT_FLOOR)

        base_meta = {
            "alignment_score": kw_score,
            "semantic_alignment_score": sem_score,
            "effective_score": score,
            "score_type": score_label,
        }

        if score < hard_floor:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Alignment {score:.1f} ({score_label}) below hard floor {hard_floor} — severe mismatch",
                confidence=0.90,
                override_eligible=False,
                metadata={**base_meta, "floor": hard_floor},
            )

        if score < soft_floor:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.OVERRIDE_REQUIRED,
                reason=f"Alignment {score:.1f} ({score_label}) below target floor {soft_floor} — marginal match",
                confidence=0.80,
                override_eligible=True,
                metadata={**base_meta, "floor": soft_floor},
            )

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason=f"Alignment score {score:.1f} ({score_label}) — acceptable match",
            metadata=base_meta,
        )
