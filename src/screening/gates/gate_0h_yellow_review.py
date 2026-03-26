"""
Gate 0H -- Yellow Keyword Review

Flags jobs that accumulate too many YELLOW (caution) keywords.
- Runs AFTER Gate 0G (order=17 vs 0G's order=15)
- Jobs reaching this gate have already cleared the RED hard-exclude check
- YELLOW threshold breach -> OVERRIDE_REQUIRED (manual review, not auto-reject)
"""

import logging

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate

logger = logging.getLogger(__name__)


@register_gate
class YellowKeywordReviewGate(BaseGate):

    @property
    def name(self) -> str:
        return "0H_yellow_keyword_review"

    @property
    def order(self) -> int:
        return 17

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0h', True)

    async def _evaluate(self, job) -> GateVerdict:
        try:
            from src.intelligence.keyword_profile import KeywordProfileManager
        except ImportError:
            logger.warning(
                "keyword_profile module not available; Gate 0H skipping (pass-through)"
            )
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.PASS,
                reason="keyword_profile module unavailable; gate skipped",
                confidence=0.0,
                metadata={"skipped": True},
            )

        profile_name = "default"
        if self.config is not None:
            profile_name = getattr(self.config, 'keyword_profile_name',
                                   self.config.get('keyword_profile_name', 'default')
                                   if isinstance(self.config, dict) else 'default')

        manager = KeywordProfileManager()
        profile = manager.load(profile_name)
        classification = manager.classify_job(job, profile)

        if classification.traffic_light == "YELLOW":
            # Annotate the job object if the attribute slots exist
            if hasattr(job, 'keyword_classification'):
                job.keyword_classification = "YELLOW"
            if hasattr(job, 'yellow_keyword_matches'):
                job.yellow_keyword_matches = classification.yellow_matches

            return GateVerdict(
                gate_name=self.name,
                result=GateResult.OVERRIDE_REQUIRED,
                reason=classification.reason,
                confidence=0.9,
                override_eligible=True,
                metadata={
                    "yellow_matches": classification.yellow_matches,
                    "green_matches": classification.green_matches,
                },
            )

        # GREEN or RED (RED already handled by Gate 0G at order=15) -> PASS
        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason="Caution keyword count below threshold",
            confidence=1.0,
            metadata={
                "traffic_light": classification.traffic_light,
                "yellow_matches": classification.yellow_matches,
            },
        )
