"""
Gate 0B -- Defense / Government Exclusion

Hard exclusion gate -- no override path.
- Known defense prime contractors -> instant fail
- Clearance keywords in job description -> fail
- Government employer signals -> fail
- Optional USASpending.gov contract check -> fail if active DOD contracts

MATCHING RULES:
  Short acronyms (< 5 chars: nsa, cia, dia, nga, fbi, etc.) use WORD-BOUNDARY
  regex matching to prevent false positives from common English words:
    "compensation" contains "nsa", "financial" contains "cia",
    "india"/"bangalore" contain "dia"/"nga", "remediation" contains "dia".
  Longer phrases (>= 5 chars) use plain substring matching — safe at that length.
"""

import re

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate
from ..data.list_provider import get_gate_list


def _build_short_patterns(signals: set) -> dict:
    """Compile word-boundary patterns for short acronyms (< 5 chars)."""
    return {
        sig: re.compile(r"\b" + re.escape(sig) + r"\b")
        for sig in signals
        if len(sig) < 5
    }


def _signal_in_text(signal: str, text: str, short_patterns: dict) -> bool:
    """
    Match a GOV_EMPLOYER_SIGNAL against text.
    Short signals (< 5 chars) use word-boundary regex.
    Long phrases use plain substring match.
    """
    if signal in short_patterns:
        return bool(short_patterns[signal].search(text))
    return signal in text


@register_gate
class DefenseExclusionGate(BaseGate):

    @property
    def name(self) -> str:
        return "0B_defense_exclusion"

    @property
    def order(self) -> int:
        return 20

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0b', True)

    async def _evaluate(self, job) -> GateVerdict:
        company = getattr(job, 'company', '') or ''
        company_lower = company.lower().strip()
        description = getattr(job, 'description', '') or ''
        jd_lower = description.lower()

        # Load lists dynamically (DB overrides, fallback to hardcoded)
        defense_primes = get_gate_list("DEFENSE_PRIMES")
        clearance_keywords = get_gate_list("CLEARANCE_KEYWORDS")
        gov_employer_signals = get_gate_list("GOV_EMPLOYER_SIGNALS")
        short_patterns = _build_short_patterns(gov_employer_signals)

        # 1. Check known defense primes (instant, no API needed)
        for prime in defense_primes:
            if prime in company_lower:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason=f"Known defense prime contractor: {company}",
                    confidence=1.0,
                    override_eligible=False,
                    metadata={"matched_prime": prime},
                )

        # 2. Check clearance keywords in job description
        triggered_clearance = [
            kw for kw in clearance_keywords if kw in jd_lower
        ]
        if triggered_clearance:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Security clearance required: {', '.join(triggered_clearance[:3])}",
                confidence=0.95,
                evidence=f"Keywords found: {triggered_clearance}",
                override_eligible=False,
            )

        # 3. Check clearance_required field (if available from scraper)
        #
        # SCRAPER ARTIFACT GUARD:
        #   Some platforms (e.g. Greenhouse) set clearance_required="required"
        #   as a generic form-field value even on non-clearance jobs.
        #   Strategy:
        #     a) Ignore falsy values ("no", "false", "none", "0", "n/a", etc.)
        #     b) For the remaining truthy values, require JD corroboration:
        #          - "yes" / "true" / "active" (explicit yes) → FAIL immediately
        #          - any specific clearance level ("secret", "ts", "sci", …) → FAIL
        #          - generic "required" / other → only FAIL if JD also has
        #            government/defense context (otherwise likely artifact)
        clearance_req = getattr(job, 'clearance_required', None)
        _FALSY_CLEARANCE = {
            'no', 'false', 'none', '0', '', 'n/a', 'not required',
            'not applicable', 'na', 'null',
        }
        _STRONG_AFFIRMATIVES = {
            'yes', 'true', '1', 'active', 'current', 'required and active',
            'secret', 'top secret', 'ts', 'ts/sci', 'sci', 'confidential',
            'dod', 'interim', 'public trust',
        }

        if clearance_req:
            cr_val = str(clearance_req).lower().strip()
            if cr_val not in _FALSY_CLEARANCE:
                if cr_val in _STRONG_AFFIRMATIVES:
                    # Unambiguously affirmative → hard fail
                    return GateVerdict(
                        gate_name=self.name,
                        result=GateResult.FAIL,
                        reason=f"Clearance requirement flagged by scraper: {clearance_req}",
                        confidence=1.0,
                        override_eligible=False,
                    )
                else:
                    # Generic truthy value (e.g. "required") — require JD corroboration.
                    # Use multi-word phrases only to avoid matching "intelligence of AI",
                    # "our agency", "federal express", etc.
                    _GOV_CONTEXT_PHRASES = {
                        'security clearance', 'clearance required', 'clearance preferred',
                        'defense contractor', 'government contractor', 'federal agency',
                        'government agency', 'department of defense', 'intelligence community',
                        'national security', 'classified work', 'classified information',
                        'homeland security', 'military contract', 'federal client',
                        'government client', 'ic contractor', 'federal government',
                        'public trust clearance', 'dod contract',
                        'fema funded', 'fema grant', 'fema program',
                        'government services', 'federal funding',
                    }
                    has_gov_context = any(phrase in jd_lower for phrase in _GOV_CONTEXT_PHRASES)
                    if has_gov_context:
                        return GateVerdict(
                            gate_name=self.name,
                            result=GateResult.FAIL,
                            reason=f"Clearance field set with gov context in JD: {clearance_req}",
                            confidence=0.85,
                            override_eligible=False,
                        )

        # 4. Check government employer signals (word-boundary safe)
        gov_signals = [
            s for s in gov_employer_signals
            if _signal_in_text(s, company_lower, short_patterns)
            or _signal_in_text(s, jd_lower, short_patterns)
        ]
        if gov_signals:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Government employer signals: {', '.join(gov_signals[:3])}",
                confidence=0.85,
                override_eligible=False,
            )

        # 5. Optional: USASpending.gov DOD contract check
        if self.config and getattr(self.config, 'enable_usaspending', False):
            has_contracts = await self._check_usaspending(company)
            if has_contracts:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason=f"{company} has active DOD contracts (USASpending.gov)",
                    confidence=0.80,
                    override_eligible=False,
                )

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason="No defense/government signals detected",
        )

    async def _check_usaspending(self, company: str) -> bool:
        """
        Check USASpending.gov API for DOD contract history.
        Returns True if active DOD contracts found.
        Non-fatal on failure -- returns False.
        """
        try:
            import aiohttp

            timeout_sec = getattr(self.config, 'usaspending_timeout', 5.0)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.usaspending.gov/api/v2/search/spending_by_award/",
                    json={
                        "filters": {
                            "recipient_search_text": [company],
                            "award_type_codes": ["A", "B", "C", "D"],
                            "agencies": [
                                {
                                    "type": "awarding",
                                    "tier": "toptier",
                                    "name": "Department of Defense",
                                }
                            ],
                        },
                        "fields": ["Award ID", "Recipient Name", "Award Amount"],
                        "limit": 1,
                    },
                    timeout=aiohttp.ClientTimeout(total=timeout_sec),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return bool(data.get("results"))
        except Exception as e:
            self.logger.warning("USASpending API check failed for %s: %s", company, e)

        return False
