"""
Gate 0A -- Company Research Database Check

Checks the local company research cache before any external API calls.
- DECLINED status -> immediate fail, surface prior reason
- Existing research -> reuse, skip re-research
- NOT FOUND -> pass, continue to subsequent gates
"""

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate

try:
    from src.intelligence.company_research.verifier import CompanyVerifier
    _COMPANY_VERIFIER_AVAILABLE = True
except ImportError:
    _COMPANY_VERIFIER_AVAILABLE = False


@register_gate
class CompanyResearchGate(BaseGate):

    @property
    def name(self) -> str:
        return "0A_company_research"

    @property
    def order(self) -> int:
        return 10

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0a', True)

    async def _evaluate(self, job) -> GateVerdict:
        company = getattr(job, 'company', '') or ''

        # F6: Run CompanyVerifier (with SQLite cache) as primary check
        if _COMPANY_VERIFIER_AVAILABLE and company:
            try:
                verifier = CompanyVerifier()
                verifier_result = verifier.research_sync(company)
                if verifier_result.decision_status == "declined":
                    decline_reason = verifier_result.decline_reason or "Previously declined"
                    # Attach to job for downstream use
                    if hasattr(job, 'enriched_company_data'):
                        job.enriched_company_data = job.enriched_company_data or {}
                        job.enriched_company_data['verifier_result'] = {
                            'decision_status': verifier_result.decision_status,
                            'defense_status': verifier_result.defense_status,
                            'decline_reason': decline_reason,
                        }
                    return GateVerdict(
                        gate_name=self.name,
                        result=GateResult.FAIL,
                        reason=f"Company declined by verifier: {decline_reason}",
                        evidence=f"Defense status: {verifier_result.defense_status or 'N/A'}",
                        metadata={'verifier_result': verifier_result.decision_status},
                    )
                # Attach research result to job for downstream use
                if hasattr(job, 'enriched_company_data'):
                    job.enriched_company_data = job.enriched_company_data or {}
                    job.enriched_company_data['verifier_result'] = {
                        'decision_status': verifier_result.decision_status,
                        'defense_status': verifier_result.defense_status,
                        'from_cache': verifier_result.from_cache,
                    }
            except Exception as _e:
                import logging as _logging
                _logging.getLogger(__name__).debug(
                    "CompanyVerifier check failed (non-critical): %s", _e
                )

        # Try to look up company in local research cache (legacy path)
        existing = await self._lookup_company(company)

        if existing is None:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.PASS,
                reason="Company not in research database - proceeding",
            )

        decision = existing.get('decision', 'unknown')

        if decision in ('exclude', 'declined'):
            decline_reason = existing.get('research_notes', {}).get(
                'decline_reason', 'Previously declined'
            )
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Company previously declined: {decline_reason}",
                evidence=f"Research date: {existing.get('last_researched', 'unknown')}",
                metadata={'cached_research': existing},
            )

        # Attach existing research to job for downstream use
        if hasattr(job, 'enriched_company_data') and existing.get('research_notes'):
            job.enriched_company_data = job.enriched_company_data or {}
            job.enriched_company_data['cached_research'] = existing.get('research_notes')

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason=f"Company found in research DB (status: {decision}) - reusing research",
            metadata={'cached_research': existing},
        )

    async def _lookup_company(self, company_name: str):
        """Look up company in the research database. Returns dict or None."""
        try:
            # Try dashboard DB first
            from src.dashboard.db import DashboardDB
            db = DashboardDB()
            # Check if company_research table exists
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='company_research'"
            )
            if cursor.fetchone():
                cursor = conn.execute(
                    "SELECT * FROM company_research WHERE LOWER(company_name) = LOWER(?)",
                    (company_name,),
                )
                row = cursor.fetchone()
                if row:
                    cols = [desc[0] for desc in cursor.description]
                    return dict(zip(cols, row))
            conn.close()
        except Exception:
            pass
        return None
