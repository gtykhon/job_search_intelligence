"""
Resume Version Routing -- Selects the correct resume version based on role type.

Maps role classifications to resume versions with section-level trimming:
- RV-001: Engineering / Software Development
- RV-002: Data Analyst / Data Science
- RV-BSA: Business Systems Analyst
- RV-003: Leadership / Management
"""

from .models import ResumeVersion, ResumeWeightTemplate, DEFAULT_VERSIONS
from .router import ResumeVersionRouter, get_resume_version_router
from .trimming import apply_trimming, detect_ai_nlp_specialty, apply_ai_nlp_trimming

__all__ = [
    "ResumeVersion",
    "ResumeWeightTemplate",
    "DEFAULT_VERSIONS",
    "ResumeVersionRouter",
    "get_resume_version_router",
    "apply_trimming",
    "detect_ai_nlp_specialty",
    "apply_ai_nlp_trimming",
]
