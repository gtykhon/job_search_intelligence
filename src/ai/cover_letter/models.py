"""
Cover Letter Models -- Data structures for the cover letter pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class RoleClassification(Enum):
    """Role type classification for tone/format selection."""
    ENGINEERING = "engineering"
    ANALYST = "analyst"
    BSA = "bsa"
    LEADERSHIP = "leadership"


@dataclass
class CoverLetterRequest:
    """Input to the cover letter pipeline."""
    resume_text: str
    job_description: str
    job_title: str
    company: str
    user_name: str = ""
    hiring_manager_name: Optional[str] = None
    tone: str = "professional"
    company_context: Optional[Dict[str, Any]] = None  # enriched company data
    target_platform: str = "resume"  # "resume" | "indeed" | "linkedin"


@dataclass
class ForbiddenPhraseViolation:
    """A detected forbidden phrase in the cover letter."""
    phrase: str
    location: str  # paragraph or line where found


@dataclass
class RepetitionViolation:
    """A detected repetition between resume and cover letter."""
    shared_text: str
    source: str  # "metric" or "phrase"


@dataclass
class ChecklistItem:
    """Individual checklist verification item."""
    name: str
    passed: bool
    detail: str = ""


@dataclass
class CoverLetterResult:
    """Output from the cover letter pipeline."""
    cover_letter: str
    role_classification: RoleClassification
    word_count: int
    paragraph_count: int
    checklist_passed: bool
    checklist_items: List[ChecklistItem] = field(default_factory=list)
    forbidden_violations: List[ForbiddenPhraseViolation] = field(default_factory=list)
    repetition_violations: List[RepetitionViolation] = field(default_factory=list)
    connection_points: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'cover_letter': self.cover_letter,
            'role_classification': self.role_classification.value,
            'word_count': self.word_count,
            'paragraph_count': self.paragraph_count,
            'checklist_passed': self.checklist_passed,
            'checklist_items': [
                {'name': c.name, 'passed': c.passed, 'detail': c.detail}
                for c in self.checklist_items
            ],
            'forbidden_violations': [
                {'phrase': v.phrase, 'location': v.location}
                for v in self.forbidden_violations
            ],
            'repetition_violations': [
                {'shared_text': v.shared_text, 'source': v.source}
                for v in self.repetition_violations
            ],
            'connection_points': self.connection_points,
            'metadata': self.metadata,
        }
