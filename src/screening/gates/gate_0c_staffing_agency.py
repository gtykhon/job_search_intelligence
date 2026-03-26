"""
Gate 0C -- Staffing Agency / Business Model Classification

Default behavior: DECLINE staffing/consulting placement firms.
Override eligible under specific conditions.
Amazon: hard exclude regardless of role type or compensation.
"""

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate
from ..data.list_provider import get_gate_list


@register_gate
class StaffingAgencyGate(BaseGate):

    @property
    def name(self) -> str:
        return "0C_staffing_agency"

    @property
    def order(self) -> int:
        return 30

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0c', True)

    async def _evaluate(self, job) -> GateVerdict:
        company = getattr(job, 'company', '') or ''
        company_lower = company.lower().strip()
        description = getattr(job, 'description', '') or ''
        jd_lower = description.lower()

        # Load lists dynamically (DB overrides, fallback to hardcoded)
        direct_hire_allowlist = get_gate_list("DIRECT_HIRE_ALLOWLIST")
        hard_exclude_companies = get_gate_list("HARD_EXCLUDE_COMPANIES")
        staffing_agencies = get_gate_list("STAFFING_AGENCIES")
        staffing_signals = get_gate_list("STAFFING_SIGNALS")

        # 0. Direct-hire allowlist — confirmed product companies whose JDs contain
        #    broad phrases (e.g. "vendor management") that trip staffing signals.
        #    Bypass all further staffing checks for these employers.
        for known_direct in direct_hire_allowlist:
            if known_direct in company_lower:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.PASS,
                    reason=f"Known direct employer (allowlist): {company}",
                    confidence=1.0,
                    metadata={"allowlisted": known_direct},
                )

        # 1. Hard-exclude companies (Amazon) -- no override
        for excluded in hard_exclude_companies:
            if excluded in company_lower:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason=f"Hard-excluded company: {company}",
                    confidence=1.0,
                    override_eligible=False,
                    metadata={"matched_exclusion": excluded},
                )

        # 2. Known staffing firm -- override eligible
        matched_agency = None
        for agency in staffing_agencies:
            if agency in company_lower:
                matched_agency = agency
                break

        # 3. Staffing signals in job description
        jd_signals = [s for s in staffing_signals if s in jd_lower]

        if matched_agency or jd_signals:
            evidence_parts = []
            if matched_agency:
                evidence_parts.append(f"Known staffing firm: {matched_agency}")
            if jd_signals:
                evidence_parts.append(f"JD signals: {', '.join(jd_signals[:3])}")

            return GateVerdict(
                gate_name=self.name,
                result=GateResult.OVERRIDE_REQUIRED,
                reason="Staffing agency or placement firm detected",
                confidence=0.9 if matched_agency else 0.7,
                evidence=" | ".join(evidence_parts),
                override_eligible=True,
                metadata={
                    "matched_agency": matched_agency,
                    "jd_signals": jd_signals,
                },
            )

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason="Direct employer - no staffing signals detected",
        )
