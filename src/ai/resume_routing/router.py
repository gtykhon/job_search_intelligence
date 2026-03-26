"""
Resume Version Router -- Selects the correct resume version based on role type.

Uses RoleClassification from the cover letter pipeline for consistency.
"""

import logging
from typing import Optional, Dict

from .models import ResumeVersion, DEFAULT_VERSIONS
from .trimming import apply_trimming, apply_ai_nlp_trimming, detect_ai_nlp_specialty

logger = logging.getLogger(__name__)


class ResumeVersionRouter:
    """Routes to the appropriate resume version based on role classification."""

    def __init__(self, custom_versions: Optional[Dict[str, ResumeVersion]] = None):
        self.versions = custom_versions or dict(DEFAULT_VERSIONS)

    def select_version(self, role_type: str) -> ResumeVersion:
        """Select resume version for the given role type."""
        role_key = role_type.lower()
        if role_key in self.versions:
            version = self.versions[role_key]
            if version.active:
                logger.info("Selected resume version %s for role type '%s'",
                            version.version_id, role_type)
                return version

        logger.info("No active version for '%s', falling back to engineering", role_type)
        return self.versions.get('engineering', list(self.versions.values())[0])

    def select_and_trim(self, role_type: str, resume_text: str) -> str:
        """Select version and apply trimming to the resume."""
        version = self.select_version(role_type)

        # Apply standard weight-based trimming
        trimmed = apply_trimming(resume_text, version)

        # Apply AI/NLP specialty trimming if detected
        if detect_ai_nlp_specialty(resume_text):
            trimmed = apply_ai_nlp_trimming(trimmed)
            logger.info("Applied AI/NLP specialty trimming")

        return trimmed

    def get_version_ids(self) -> Dict[str, str]:
        """Return mapping of role_type -> version_id."""
        return {k: v.version_id for k, v in self.versions.items()}

    def add_version(self, version: ResumeVersion):
        """Add or replace a resume version."""
        self.versions[version.role_type] = version

    def deactivate_version(self, role_type: str):
        """Deactivate a version (will fall back to engineering)."""
        if role_type in self.versions:
            self.versions[role_type].active = False


# -- Singleton --

_router: Optional[ResumeVersionRouter] = None


def get_resume_version_router() -> ResumeVersionRouter:
    """Get or create the global resume version router."""
    global _router
    if _router is None:
        _router = ResumeVersionRouter()
    return _router
