"""
Audience Classifier.

Determines the likely audience type for a job application based on
hiring manager title and job description context. The audience type
drives tone selection in cover letter generation.

Audience Types:
  C_SUITE  — CTO, CEO, CPO, CISO — strategic tone, business impact focus
  VP       — VP Eng, VP Product   — technical credibility + business impact
  MANAGER  — Hiring Manager, TL   — operational tone, team fit, delivery
  IC       — Senior IC, Staff     — technical depth, craft, peer credibility
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AudienceType(str, Enum):
    C_SUITE = "c_suite"
    VP      = "vp"
    MANAGER = "manager"
    IC      = "ic"


@dataclass
class AudienceClassification:
    audience_type: AudienceType
    technical_depth: str       # "high" | "medium" | "low"
    hiring_influence: str      # "direct" | "indirect" | "unknown"
    tone_guidance: str         # injected into cover letter generation prompt
    formality_level: int       # 1 (casual) to 5 (formal)


# Keyword signals per audience type (checked against lowercased title)
_C_SUITE_SIGNALS = [
    "chief", "cto", "ceo", "coo", "cpo", "ciso", "c-level",
    "president", "founder", "co-founder",
]
_VP_SIGNALS = [
    "vp", "vice president", "svp", "evp", "head of engineering",
    "head of product", "head of data", "director of engineering",
    "engineering director",
]
_MANAGER_SIGNALS = [
    "manager", "engineering manager", "hiring manager",
    "team lead", "tech lead", "technical lead",
    "squad lead", "group manager",
]
_IC_SIGNALS = [
    "staff", "principal", "senior", "lead engineer", "individual contributor",
    "engineer", "developer", "scientist", "analyst",
]

_TONE_GUIDANCE: dict[AudienceType, str] = {
    AudienceType.C_SUITE: (
        "Use strategic language. Lead with business impact and competitive advantage. "
        "Quantify ROI and organizational outcomes. Avoid deep technical jargon. "
        "Connect engineering decisions to business strategy."
    ),
    AudienceType.VP: (
        "Balance technical credibility with business impact. "
        "Show architectural thinking and delivery track record. "
        "Reference team leadership and cross-functional collaboration."
    ),
    AudienceType.MANAGER: (
        "Emphasize team fit, delivery reliability, and collaboration. "
        "Show specific technical contributions with measurable outcomes. "
        "Address day-to-day operational concerns."
    ),
    AudienceType.IC: (
        "Lead with technical depth and craft. Demonstrate system design thinking. "
        "Reference specific technologies, trade-offs navigated, and scale challenges. "
        "Peer-to-peer credibility is key."
    ),
}


class AudienceClassifier:
    """Classifies the hiring audience from title and JD context."""

    def classify(
        self,
        hiring_manager_title: Optional[str],
        job_description: str,
        company_size: Optional[str] = None,
    ) -> AudienceClassification:
        """
        Classify the audience type.

        Parameters
        ----------
        hiring_manager_title : optional title string (e.g. "VP of Engineering")
        job_description      : full JD text for fallback context
        company_size         : optional size hint ("startup", "mid", "enterprise")
        """
        title_lower = (hiring_manager_title or "").lower()
        jd_lower = job_description.lower()

        audience = self._classify_from_title(title_lower)
        if audience is None:
            audience = self._classify_from_jd(jd_lower)

        tech_depth = self._tech_depth(audience, jd_lower)
        influence = self._hiring_influence(audience)
        formality = self._formality_level(audience, company_size)

        return AudienceClassification(
            audience_type=audience,
            technical_depth=tech_depth,
            hiring_influence=influence,
            tone_guidance=_TONE_GUIDANCE[audience],
            formality_level=formality,
        )

    def _classify_from_title(self, title: str) -> Optional[AudienceType]:
        if any(s in title for s in _C_SUITE_SIGNALS):
            return AudienceType.C_SUITE
        if any(s in title for s in _VP_SIGNALS):
            return AudienceType.VP
        if any(s in title for s in _MANAGER_SIGNALS):
            return AudienceType.MANAGER
        if any(s in title for s in _IC_SIGNALS):
            return AudienceType.IC
        return None

    def _classify_from_jd(self, jd: str) -> AudienceType:
        """Fallback: infer from JD language."""
        if re.search(r"\b(executive|strategic|org|organization|board)\b", jd):
            return AudienceType.VP
        if re.search(r"\b(mentor|lead|architect|staff|principal)\b", jd):
            return AudienceType.IC
        if re.search(r"\b(manager|team lead|manage people|direct reports)\b", jd):
            return AudienceType.MANAGER
        return AudienceType.MANAGER   # safe default

    def _tech_depth(self, audience: AudienceType, jd: str) -> str:
        if audience in (AudienceType.IC,):
            return "high"
        if audience in (AudienceType.VP,):
            return "medium"
        tech_count = len(re.findall(
            r"\b(python|java|sql|kubernetes|docker|aws|azure|gcp|react|go|rust)\b",
            jd,
        ))
        if tech_count >= 5:
            return "high"
        if tech_count >= 2:
            return "medium"
        return "low"

    def _hiring_influence(self, audience: AudienceType) -> str:
        return {
            AudienceType.C_SUITE: "indirect",
            AudienceType.VP:      "direct",
            AudienceType.MANAGER: "direct",
            AudienceType.IC:      "indirect",
        }.get(audience, "unknown")

    def _formality_level(self, audience: AudienceType, company_size: Optional[str]) -> int:
        base = {
            AudienceType.C_SUITE: 4,
            AudienceType.VP:      4,
            AudienceType.MANAGER: 3,
            AudienceType.IC:      3,
        }.get(audience, 3)
        if company_size == "startup":
            return max(1, base - 1)
        return base
