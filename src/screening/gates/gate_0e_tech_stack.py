"""
Gate 0E -- Tech Stack Alignment

RED keywords (auto-decline if required): Spark, PySpark, Databricks, SQL Server, Looker, BigQuery, etc.
AWS ethical exclusion: AWS-primary roles declined regardless of skill gap.
Tier classification: Tier 1 (preferred stack) -> Tier 2 (mixed) -> Tier 3 (avoid).
"""

from ..base_gate import BaseGate
from ..models import GateResult, GateVerdict
from ..gate_registry import register_gate


# Default RED keywords -- auto-decline if listed as required
DEFAULT_RED_KEYWORDS = {
    "spark", "pyspark", "databricks", "hadoop", "hive",
    "sql server", "t-sql", "ssrs", "ssis", "ssas",
    "looker", "bigquery", "workato",
}

# AWS-primary signals -> ethical exclusion + skill gap
AWS_PRIMARY_SIGNALS = {
    "aws certified required", "aws only", "aws expert", "aws required",
    "3+ years aws", "5+ years aws", "heavy aws", "aws native",
    "aws is the primary", "aws-centric",
}

# Context-dependent -- RED only if primary/required
CONTEXT_DEPENDENT = {"kubernetes", "terraform", "dbt", "snowflake"}

PRIMARY_REQUIREMENT_PATTERNS = [
    "3+ years {kw}", "5+ years {kw}", "{kw} required",
    "expert {kw}", "strong {kw} experience", "{kw} expert",
    "extensive {kw}", "deep {kw} experience",
]

# Tier 1 (preferred) signals for downstream prioritization
TIER_1_SIGNALS = {
    "open source", "airflow", "dbt", "postgres", "postgresql",
    "gcp", "google cloud", "azure", "multi-cloud", "cloud-agnostic",
    "vendor-agnostic", "apache", "fastapi", "django", "flask",
}


@register_gate
class TechStackGate(BaseGate):

    @property
    def name(self) -> str:
        return "0E_tech_stack"

    @property
    def order(self) -> int:
        return 50

    @property
    def enabled(self) -> bool:
        if self.config is None:
            return True
        return getattr(self.config, 'enable_gate_0e', True)

    async def _evaluate(self, job) -> GateVerdict:
        description = getattr(job, 'description', '') or ''
        jd_lower = description.lower()

        # Get configurable RED keywords or use defaults
        red_keywords = DEFAULT_RED_KEYWORDS
        if self.config and hasattr(self.config, 'red_keywords') and self.config.red_keywords:
            red_keywords = {kw.lower() for kw in self.config.red_keywords}

        # 1. Check RED keywords in requirements section
        red_hits = self._find_required_keywords(jd_lower, red_keywords)
        if red_hits:
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.FAIL,
                reason=f"Required skills outside verified stack: {', '.join(red_hits)}",
                confidence=0.90,
                evidence="No production experience documented for these tools",
                metadata={"red_hits": list(red_hits)},
            )

        # 2. AWS-primary ethical exclusion
        aws_ethical = True
        if self.config:
            aws_ethical = getattr(self.config, 'aws_ethical_exclusion', True)

        if aws_ethical:
            aws_signals = [s for s in AWS_PRIMARY_SIGNALS if s in jd_lower]
            if aws_signals:
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason=f"AWS-primary role (ethical exclusion + skill gap): {aws_signals[0]}",
                    confidence=0.90,
                    override_eligible=False,
                    metadata={"aws_signals": aws_signals},
                )

        # 3. Context-dependent RED check
        for keyword in CONTEXT_DEPENDENT:
            if self._is_primary_requirement(keyword, jd_lower):
                return GateVerdict(
                    gate_name=self.name,
                    result=GateResult.FAIL,
                    reason=f"{keyword} is a primary required skill (no production experience)",
                    confidence=0.75,
                    override_eligible=True,
                )

        # 4. Assign stack tier for downstream prioritization
        tier_1_hits = [s for s in TIER_1_SIGNALS if s in jd_lower]
        tier = 1 if tier_1_hits else 2

        # Attach tier to job metadata for downstream use
        raw = getattr(job, 'raw_data', None)
        if raw is not None and isinstance(raw, dict):
            raw['stack_tier'] = tier
            raw['stack_tier_signals'] = tier_1_hits

        return GateVerdict(
            gate_name=self.name,
            result=GateResult.PASS,
            reason=f"Stack tier {tier} - proceeding",
            metadata={"stack_tier": tier, "tier_1_signals": tier_1_hits},
        )

    def _find_required_keywords(self, jd_lower: str, red_keywords: set) -> set:
        """Find RED keywords that appear in requirements/required context."""
        hits = set()
        for kw in red_keywords:
            if kw not in jd_lower:
                continue
            if self._is_in_required_context(kw, jd_lower):
                hits.add(kw)
        return hits

    def _is_in_required_context(self, keyword: str, jd_lower: str) -> bool:
        """Check if keyword appears in a 'required' context rather than 'nice-to-have'."""
        idx = jd_lower.find(keyword)
        if idx == -1:
            return False

        start = max(0, idx - 200)
        end = min(len(jd_lower), idx + len(keyword) + 200)
        context = jd_lower[start:end]

        required_signals = [
            "required", "must have", "must possess", "requirements:",
            "qualifications:", "mandatory", "essential", "minimum",
        ]
        nice_to_have_signals = [
            "nice to have", "preferred", "bonus", "plus",
            "a plus", "desirable", "optional", "ideally",
        ]

        has_required = any(s in context for s in required_signals)
        has_nice = any(s in context for s in nice_to_have_signals)

        if has_nice and not has_required:
            return False

        return True

    def _is_primary_requirement(self, keyword: str, jd_lower: str) -> bool:
        """Check if a context-dependent keyword is a primary requirement."""
        for pattern in PRIMARY_REQUIREMENT_PATTERNS:
            if pattern.format(kw=keyword) in jd_lower:
                return True
        return False
