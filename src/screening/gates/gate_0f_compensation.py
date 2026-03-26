"""
Gate 0F -- Compensation and Work Model

Compensation thresholds:
- Hard floor: $130K (never proceed below this)
- Soft floor: $140K (override eligible; was $145K — narrowed window reduces FPs
  for strong-fit companies at $140-145K like VSP Vision, Lightning AI)
- Missing salary data: pass with warning

Work model:
- Remote -> pass
- Hybrid -> OVERRIDE_REQUIRED
- On-site -> fail
"""

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate


REMOTE_SIGNALS = {
    "remote", "work from home", "wfh", "fully remote", "100% remote",
    "remote position", "remote role", "work remotely",
}

ONSITE_SIGNALS = {
    "on-site required", "onsite required", "on site required",
    "in-office required", "in-office only", "must work in office",
    "must be local", "no remote", "no remote work", "not remote",
    "office-based", "in-person required", "on site only",
    "required to be in office", "required to work on-site",
    "100% on-site", "5 days a week in office", "fully on-site",
}

# Signals that confirm the job IS remote — if present, skip on-site text scan entirely.
CONFIRMED_REMOTE_SIGNALS = {
    "fully remote", "100% remote", "remote position", "remote role",
    "remote job", "work from home", "wfh", "work remotely",
    "remote-first", "remote first", "distributed team",
    "remote (us)", "remote us", "remote - us", "remote only",
}

HYBRID_SIGNALS = {
    "hybrid", "2 days in office", "3 days in office", "flexible remote",
    "partial remote", "2-3 days", "3 days on-site", "in-office 2",
}

# Non-US location signals — used only when job is NOT confirmed remote.
# Keyed against the *location* field (lowercased). Substring match is safe at these lengths.
NON_US_LOCATION_SIGNALS = {
    # Indian metro areas and state/country names
    "bengaluru", "bangalore", "mumbai", "delhi", "hyderabad",
    "pune", "chennai", "kolkata", "noida", "gurgaon", "gurugram",
    ", india", "india,", "(india)", " india ",
    # European cities / countries
    "london", "united kingdom", ", uk", "(uk)", " uk,",
    "germany", "france", "netherlands", "amsterdam", "berlin", "paris",
    "dublin", "ireland",
    # APAC
    "singapore", "hong kong", "australia", "sydney", "melbourne",
    "china", "beijing", "shanghai",
    # Middle East
    "dubai", "united arab emirates",
    # Philippines / other offshore hubs
    "manila", "philippines", "pakistan", "lahore", "karachi", "islamabad",
}


@register_gate
class CompensationWorkModelGate(BaseGate):

    @property
    def name(self) -> str:
        return "0F_compensation_work_model"

    @property
    def order(self) -> int:
        return 60

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0f', True)

    async def _evaluate(self, job) -> GateVerdict:
        hard_floor = 130_000
        soft_floor = 140_000    # lowered from $145K — narrows OVERRIDE window
        require_remote = True

        if self.config:
            hard_floor = getattr(self.config, 'salary_hard_floor', 130_000)
            soft_floor = getattr(self.config, 'salary_soft_floor', 140_000)
            require_remote = getattr(self.config, 'require_remote', True)

        description = getattr(job, 'description', '') or ''
        jd_lower = description.lower()

        # 1. Geography check — fail non-US, non-remote postings
        geo_verdict = self._check_geography(job)
        if geo_verdict:
            return geo_verdict

        # 2. Work model check (if remote-only preference is enabled)
        if require_remote:
            work_model_verdict = self._check_work_model(job, jd_lower)
            if work_model_verdict:
                return work_model_verdict

        # 3. Compensation check
        salary_max = getattr(job, 'salary_max', None) or getattr(job, 'salary_min', None)

        # 3a. Salary extraction fallback — parse from JD text when scraper fields are null
        salary_source = "scraper"
        if salary_max is None and description:
            try:
                from src.intelligence.salary_extractor import get_salary_extractor
                extracted = get_salary_extractor().extract(description)
                if extracted is not None:
                    salary_max = extracted.salary_max
                    # Store as already-normalised yearly so period doesn't double-convert
                    salary_max = extracted.yearly_max
                    salary_source = f"extracted_from_jd ({extracted.raw_text[:40]})"
            except Exception:
                pass  # extraction failure is non-fatal — fall through to missing-salary pass

        if salary_max is not None:
            # When extracted from JD, value is already normalised to yearly
            period = "yearly" if salary_source.startswith("extracted") \
                     else getattr(job, 'salary_period', 'yearly')
            yearly_salary = self._normalize_to_yearly(salary_max, period)

            if yearly_salary < hard_floor:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason=f"Salary ${yearly_salary:,.0f} below hard floor ${hard_floor:,.0f}",
                    confidence=0.95,
                    override_eligible=False,
                    metadata={"salary": yearly_salary, "floor": hard_floor},
                )

            if yearly_salary < soft_floor:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.OVERRIDE_REQUIRED,
                    reason=f"Salary ${yearly_salary:,.0f} below target floor ${soft_floor:,.0f}",
                    confidence=0.85,
                    override_eligible=True,
                    metadata={"salary": yearly_salary, "floor": soft_floor},
                )

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason="Compensation and work model verified",
            metadata={
                "salary_max": getattr(job, 'salary_max', None),
                "salary_min": getattr(job, 'salary_min', None),
                "has_salary_data": salary_max is not None,
                "salary_source": salary_source,
            },
        )

    def _check_geography(self, job):
        """
        Fail jobs located outside the US when the role is not confirmed remote.

        Priority:
          1. remote_type field = "remote"  → skip (already passes work model)
          2. Location field contains CONFIRMED_REMOTE_SIGNALS or "remote" → skip
          3. Location field contains NON_US_LOCATION_SIGNALS → FAIL
        """
        # Step 1: confirmed remote via scraper field → skip geography check
        remote_type = getattr(job, 'remote_type', None)
        if remote_type:
            rt_val = remote_type.value if hasattr(remote_type, 'value') else str(remote_type)
            if rt_val in ("remote", "fully_remote", "remote_ok", "true"):
                return None

        location = (getattr(job, 'location', '') or '').lower()

        # Step 2: location says "remote" explicitly → skip
        if any(s in location for s in CONFIRMED_REMOTE_SIGNALS) or \
                any(s in location for s in ("remote", "distributed", "work from home")):
            return None

        # Step 3: scan for non-US signals in location field
        matched = next(
            (s for s in NON_US_LOCATION_SIGNALS if s in location),
            None,
        )
        if matched:
            display_loc = location.strip().title()
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Non-US location: {display_loc} — target is US remote or DMV",
                confidence=0.90,
                metadata={"location": location, "matched_signal": matched},
            )

        return None  # No geography issue detected

    def _check_work_model(self, job, jd_lower: str):
        """
        Check work model against remote-only preference.

        Priority order:
          1. remote_type field from scraper (most reliable)
             - "remote"      → PASS immediately, skip text scan
             - "on_site"     → FAIL
             - "hybrid"      → OVERRIDE_REQUIRED
          2. Location field  — if it contains a confirmed-remote phrase → PASS
          3. JD text scan    — only when scraper gave no signal
             Uses tightened ONSITE_SIGNALS to avoid benefits-section false
             positives ("in-office perks", "in-office events", etc.)
        """
        # ── Step 1: trust the scraper's remote_type field ──────────────
        remote_type = getattr(job, 'remote_type', None)
        if remote_type:
            rt_val = remote_type.value if hasattr(remote_type, 'value') else str(remote_type)
            if rt_val in ("remote", "fully_remote", "remote_ok", "true"):
                return None   # confirmed remote — no issue, skip text scan
            if rt_val == "on_site":
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason="On-site required - remote-only preference",
                    confidence=0.95,
                )
            if rt_val == "hybrid":
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.OVERRIDE_REQUIRED,
                    reason="Hybrid role - remote-only preference",
                    confidence=0.80,
                    override_eligible=True,
                )

        # ── Step 2: check location field for explicit remote wording ───
        location = (getattr(job, 'location', '') or '').lower()
        if any(s in location for s in CONFIRMED_REMOTE_SIGNALS) or \
                any(s in location for s in ("remote", "distributed", "work from home")):
            return None   # location confirms remote

        # ── Step 3: JD text scan (fallback when scraper has no signal) ─
        is_confirmed_remote = any(s in jd_lower for s in CONFIRMED_REMOTE_SIGNALS)
        if is_confirmed_remote:
            return None   # JD explicitly says remote

        is_remote = any(s in jd_lower for s in REMOTE_SIGNALS)
        is_onsite = any(s in jd_lower for s in ONSITE_SIGNALS)
        is_hybrid = any(s in jd_lower for s in HYBRID_SIGNALS)

        if is_hybrid and not is_remote:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.OVERRIDE_REQUIRED,
                reason="Hybrid role - remote-only preference",
                confidence=0.70,
                override_eligible=True,
            )

        if is_onsite and not is_remote and not is_hybrid:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason="On-site required - remote-only preference",
                confidence=0.85,
            )

        return None  # No work model issue detected

    def _normalize_to_yearly(self, salary: float, period: str) -> float:
        """Normalize salary to yearly equivalent."""
        period = (period or "yearly").lower()
        if period == "hourly":
            return salary * 2080  # 40 hrs/week * 52 weeks
        if period == "monthly":
            return salary * 12
        if period == "weekly":
            return salary * 52
        return salary  # already yearly
