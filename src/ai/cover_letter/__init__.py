"""
Cover Letter Pipeline -- 5-step constrained generation.

Steps:
  1. Research hiring manager / extract connection points
  2. Classify role -> RoleClassification
  3. Authentication check -- verify claims grounded in resume
  4. Generate constrained cover letter (canonical 4-paragraph structure)
  5. Enforce no-repetition -- no shared metrics or >5-word phrases with resume
"""

from .models import (
    RoleClassification,
    CoverLetterRequest,
    CoverLetterResult,
    ChecklistItem,
    ForbiddenPhraseViolation,
    RepetitionViolation,
)
from .pipeline import CoverLetterPipeline, get_cover_letter_pipeline
from .checklist import PreSubmissionChecklist
from .templates import FORBIDDEN_PHRASES, CANONICAL_STRUCTURE

__all__ = [
    "RoleClassification",
    "CoverLetterRequest",
    "CoverLetterResult",
    "ChecklistItem",
    "ForbiddenPhraseViolation",
    "RepetitionViolation",
    "CoverLetterPipeline",
    "get_cover_letter_pipeline",
    "PreSubmissionChecklist",
    "FORBIDDEN_PHRASES",
    "CANONICAL_STRUCTURE",
]
