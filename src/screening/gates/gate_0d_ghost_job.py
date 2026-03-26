"""
Gate 0D -- Ghost Job Verification (Enhanced)

Multi-layer ghost job detection combining:
  - Posting age (>45 days -> fail, >30 days -> flag)
  - Applicant flood (>500 fail, >200 flag)
  - Ghost language patterns in JD (expanded set)
  - Description specificity scoring (vague -> flag)
  - Repost detection via description hashing
  - Composite ghost score (weighted 0.0-1.0)
  - Optional: Wayback Machine + JSON-LD HTTP enrichment

Gate 0D produces a composite ghost_score and attaches it to job metadata
for downstream reporting, regardless of pass/fail decision.
"""

from datetime import datetime

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate


# Inline ghost language for legacy fallback
GHOST_LANGUAGE = {
    "talent community", "talent pipeline", "future opportunities",
    "no immediate openings", "building our team for", "pool of candidates",
    "general application", "we are always looking", "evergreen requisition",
    "proactive sourcing", "talent pool", "ongoing recruitment",
}


@register_gate
class GhostJobGate(BaseGate):

    @property
    def name(self) -> str:
        return "0D_ghost_job"

    @property
    def order(self) -> int:
        return 40

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0d', True)

    async def _evaluate(self, job) -> GateVerdict:
        max_age = 45
        max_applicants = 500
        flag_applicants = 200
        ghost_score_fail = 0.60
        ghost_score_flag = 0.40
        enable_http = False

        if self.config:
            max_age = getattr(self.config, 'ghost_posting_age_days', 45)
            max_applicants = getattr(self.config, 'ghost_applicant_threshold', 500)
            flag_applicants = getattr(self.config, 'ghost_flag_applicant_threshold', 200)
            ghost_score_fail = getattr(self.config, 'ghost_score_fail_threshold', 0.60)
            ghost_score_flag = getattr(self.config, 'ghost_score_flag_threshold', 0.40)
            enable_http = getattr(self.config, 'ghost_http_checks_enabled', False)

        # Try to use the enrichment module for composite scoring
        try:
            from src.enrichment.ghost_signals import (
                GhostSignalCollector, compute_ghost_score,
            )
            collector = GhostSignalCollector(enable_http_checks=enable_http)

            if enable_http:
                signals = await collector.collect_all_signals(job)
            else:
                signals = collector.collect_local_signals(job)

            ghost_score = compute_ghost_score(signals)

            # Attach ghost score + signals to raw_data for downstream use
            raw = getattr(job, 'raw_data', None)
            if raw is not None and isinstance(raw, dict):
                raw['ghost_score'] = round(ghost_score, 3)
                raw['ghost_signals'] = signals.to_dict()
                raw['description_hash'] = signals.description_hash

        except ImportError:
            # Enrichment module not available -- fall back to legacy logic
            self.logger.debug("Enrichment module unavailable, using legacy ghost detection")
            return await self._evaluate_legacy(job, max_age, max_applicants)

        # -- Decision logic based on composite score --

        # Hard fail on high composite ghost score
        if ghost_score >= ghost_score_fail:
            reasons = []
            if signals.posting_age_days and signals.posting_age_days > max_age:
                reasons.append(f"age={signals.posting_age_days}d")
            if signals.applicant_count and signals.applicant_count > flag_applicants:
                reasons.append(f"applicants={signals.applicant_count}")
            if signals.ghost_language_hits:
                reasons.append(f"ghost_language={signals.ghost_language_hits[0]}")
            if signals.is_reposted:
                reasons.append(f"reposted (x{signals.repost_count})")
            if signals.description_specificity < 0.3:
                reasons.append(f"vague_jd={signals.description_specificity:.0%}")

            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Ghost score {ghost_score:.0%}: {', '.join(reasons) or 'multiple signals'}",
                confidence=min(0.60 + ghost_score * 0.3, 0.95),
                evidence=f"Signals: {signals.to_dict()}",
                metadata={'ghost_score': ghost_score},
            )

        # Flag for review on moderate ghost score
        if ghost_score >= ghost_score_flag:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.OVERRIDE_REQUIRED,
                reason=f"Moderate ghost score {ghost_score:.0%} - review recommended",
                confidence=0.55,
                override_eligible=True,
                metadata={'ghost_score': ghost_score},
            )

        # Individual hard-fail checks (even if composite score is low)

        # Posting age hard fail
        if signals.posting_age_days is not None and signals.posting_age_days > max_age:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Posting is {signals.posting_age_days} days old (threshold: {max_age})",
                confidence=0.85,
                evidence=f"ghost_score={ghost_score:.0%}",
                metadata={'ghost_score': ghost_score},
            )

        # Applicant flood hard fail
        if signals.applicant_count is not None and signals.applicant_count > max_applicants:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"High applicant count: {signals.applicant_count} (ghost signal)",
                confidence=0.75,
                metadata={'ghost_score': ghost_score},
            )

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason=f"Posting verified - ghost score {ghost_score:.0%}",
            metadata={'ghost_score': ghost_score},
        )

    async def _evaluate_legacy(self, job, max_age, max_applicants) -> GateVerdict:
        """Legacy ghost detection (no enrichment module)."""
        # 1. Posting age check
        posted_date = getattr(job, 'posted_date', None)
        if posted_date:
            if isinstance(posted_date, str):
                try:
                    posted_date = datetime.fromisoformat(posted_date)
                except ValueError:
                    posted_date = None
            if posted_date:
                age_days = (datetime.now() - posted_date).days
                if age_days > max_age:
                    return GateVerdict(
                        gate_name=self.name,
                        result=GateResult.FAIL,
                        reason=f"Posting is {age_days} days old (threshold: {max_age})",
                        confidence=0.85,
                    )

        # 2. Applicant count
        num_applicants = getattr(job, 'num_applicants', None)
        if num_applicants is None:
            num_applicants = (getattr(job, 'raw_data', None) or {}).get('num_applicants')
        if num_applicants and int(num_applicants) > max_applicants:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"High applicant count: {num_applicants}",
                confidence=0.75,
            )

        # 3. Ghost language
        jd_lower = (getattr(job, 'description', '') or '').lower()
        ghost_hits = [p for p in GHOST_LANGUAGE if p in jd_lower]
        if ghost_hits:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Ghost language detected: {', '.join(ghost_hits[:3])}",
                confidence=0.70,
            )

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason="Posting verified as active",
        )
