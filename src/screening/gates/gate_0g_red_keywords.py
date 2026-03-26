"""
Gate 0G -- Red Keyword Exclusion

Hard exclusion gate based on keyword profile traffic-light system.
- Loads the configured keyword profile (default: "default")
- Scans job title, description, and company name for RED keywords
- Any RED keyword match -> instant FAIL, no override path
"""

import logging

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate

logger = logging.getLogger(__name__)


@register_gate
class RedKeywordExclusionGate(BaseGate):

    @property
    def name(self) -> str:
        return "0G_red_keyword_exclusion"

    @property
    def order(self) -> int:
        return 15

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0g', True)

    async def _evaluate(self, job) -> GateVerdict:
        try:
            from src.intelligence.keyword_profile import KeywordProfileManager
        except ImportError:
            logger.warning(
                "keyword_profile module not available; Gate 0G skipping (pass-through)"
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

        if classification.traffic_light == "RED":
            # Annotate the job object if the attribute slots exist
            if hasattr(job, 'keyword_classification'):
                job.keyword_classification = "RED"
            if hasattr(job, 'yellow_keyword_matches'):
                job.yellow_keyword_matches = []

            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=classification.reason,
                confidence=1.0,
                override_eligible=False,
                metadata={"red_matches": classification.red_matches},
            )

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason="No hard-exclude RED keywords detected",
            confidence=1.0,
            metadata={
                "traffic_light": classification.traffic_light,
                "green_matches": classification.green_matches,
            },
        )
