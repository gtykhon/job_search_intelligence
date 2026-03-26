"""
Gate Culture -- Glassdoor + Layoff Signals

Rating thresholds:
- < 3.5 -> auto-decline
- 3.5-3.9 -> flag (OVERRIDE_REQUIRED)
- >= 4.0 -> pass
- Missing data -> pass (no penalty)

Layoff recency:
- Layoffs within 18 months -> OVERRIDE_REQUIRED
"""

from datetime import datetime

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate


LAYOFF_SIGNALS = {
    "layoff", "laid off", "reduction in force", "rif", "restructuring",
    "downsizing", "workforce reduction", "eliminated positions",
}


@register_gate
class CultureGlassdoorGate(BaseGate):

    @property
    def name(self) -> str:
        return "culture_glassdoor"

    @property
    def order(self) -> int:
        return 70

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_culture', True)

    async def _evaluate(self, job) -> GateVerdict:
        auto_decline = 3.5
        flag_threshold = 3.9
        layoff_months = 18

        if self.config:
            auto_decline = getattr(self.config, 'glassdoor_auto_decline_threshold', 3.5)
            flag_threshold = getattr(self.config, 'glassdoor_flag_threshold', 3.9)
            layoff_months = getattr(self.config, 'layoff_recency_months', 18)

        # Get enriched company data (from prior enrichment/scraping)
        enriched = getattr(job, 'enriched_company_data', None) or {}
        if isinstance(enriched, dict):
            cached = enriched.get('cached_research', {})
        else:
            cached = {}

        # 1. Try to get Glassdoor rating from existing data
        rating = self._get_glassdoor_rating(job, enriched, cached)

        # 2. If no rating found, try live API enrichment (free tier via RapidAPI)
        if rating is None:
            api_data = await self._fetch_glassdoor_api(getattr(job, 'company', '') or '')
            if api_data:
                rating = api_data.get('glassdoor_rating')
                # Persist enrichment data to job for downstream use
                raw = getattr(job, 'raw_data', None)
                if raw is not None and isinstance(raw, dict):
                    raw['glassdoor_enrichment'] = api_data

        # 3. Evaluate rating
        if rating is not None:
            if rating < auto_decline:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason=f"Glassdoor rating {rating:.1f} below threshold {auto_decline}",
                    confidence=0.80,
                    metadata={"glassdoor_rating": rating},
                )
            if rating < flag_threshold:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.OVERRIDE_REQUIRED,
                    reason=f"Glassdoor rating {rating:.1f} - review recommended",
                    confidence=0.70,
                    override_eligible=True,
                    metadata={"glassdoor_rating": rating},
                )

        # 4. Layoff recency check
        layoff_date = self._get_layoff_date(enriched, cached)
        if layoff_date:
            months_since = (datetime.now() - layoff_date).days / 30
            if months_since <= layoff_months:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.OVERRIDE_REQUIRED,
                    reason=f"Recent layoffs ({months_since:.0f} months ago) - review recommended",
                    confidence=0.65,
                    override_eligible=True,
                    metadata={"layoff_date": str(layoff_date.date()), "months_since": months_since},
                )

        # 5. Check JD for layoff language
        description = getattr(job, 'description', '') or ''
        jd_lower = description.lower()
        layoff_hits = [s for s in LAYOFF_SIGNALS if s in jd_lower]
        if layoff_hits:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.OVERRIDE_REQUIRED,
                reason=f"Layoff language detected in JD: {', '.join(layoff_hits[:2])}",
                confidence=0.55,
                override_eligible=True,
            )

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason="Culture and stability checks passed",
            metadata={"glassdoor_rating": rating},
        )

    async def _fetch_glassdoor_api(self, company_name: str) -> dict:
        """Attempt live Glassdoor lookup via OpenWeb Ninja (RapidAPI free tier)."""
        if not company_name:
            return None
        try:
            from src.enrichment.glassdoor_client import get_glassdoor_client
            client = get_glassdoor_client()
            return await client.lookup_company(company_name)
        except ImportError:
            self.logger.debug("Glassdoor enrichment module not available")
            return None
        except Exception as exc:
            self.logger.debug("Glassdoor API fetch failed for %s: %s", company_name, exc)
            return None

    def _get_glassdoor_rating(self, job, enriched: dict, cached: dict) -> float:
        """Extract Glassdoor rating from available data sources."""
        # Check enriched company data
        rating = enriched.get('glassdoor_rating')
        if rating is not None:
            return float(rating)

        # Check cached research
        rating = cached.get('glassdoor_rating')
        if rating is not None:
            return float(rating)

        # Check raw_data from scraper or prior enrichment
        raw = getattr(job, 'raw_data', None) or {}
        rating = raw.get('glassdoor_rating')
        if rating is not None:
            return float(rating)

        # Fallback: read company_rating directly from the job object
        # (populated from Indeed/JobSpy scrape or by enrich-ratings endpoint)
        rating = getattr(job, 'company_rating', None)
        if rating is not None and float(rating) > 0:
            return float(rating)

        # Also check raw_data for company_rating (dict form)
        rating = raw.get('company_rating')
        if rating is not None and float(rating) > 0:
            return float(rating)

        return None

    def _get_layoff_date(self, enriched: dict, cached: dict) -> datetime:
        """Extract most recent layoff date from available data."""
        for source in [enriched, cached]:
            layoff_date = source.get('last_layoff_date')
            if layoff_date:
                if isinstance(layoff_date, datetime):
                    return layoff_date
                try:
                    return datetime.fromisoformat(str(layoff_date))
                except (ValueError, TypeError):
                    pass
        return None
