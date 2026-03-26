"""
Resume Routing Models -- Data structures for resume version selection.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ResumeWeightTemplate:
    """Section weight template for a resume version."""
    section_weights: Dict[str, float] = field(default_factory=dict)
    compress_sections: List[str] = field(default_factory=list)
    expand_sections: List[str] = field(default_factory=list)


@dataclass
class ResumeVersion:
    """A resume version tailored for a specific role type."""
    version_id: str
    role_type: str
    label: str
    base_text: Optional[str] = None
    weight_template: ResumeWeightTemplate = field(default_factory=ResumeWeightTemplate)
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'version_id': self.version_id,
            'role_type': self.role_type,
            'label': self.label,
            'active': self.active,
            'weight_template': {
                'section_weights': self.weight_template.section_weights,
                'compress_sections': self.weight_template.compress_sections,
                'expand_sections': self.weight_template.expand_sections,
            },
        }


# -- Default version definitions --

DEFAULT_VERSIONS = {
    'engineering': ResumeVersion(
        version_id='RV-001',
        role_type='engineering',
        label='Engineering / Software Development',
        weight_template=ResumeWeightTemplate(
            section_weights={
                'technical_skills': 1.0, 'experience': 1.0, 'projects': 0.9,
                'education': 0.6, 'certifications': 0.7, 'summary': 0.8,
            },
            expand_sections=['technical_skills', 'projects'],
            compress_sections=['education'],
        ),
    ),
    'analyst': ResumeVersion(
        version_id='RV-002',
        role_type='analyst',
        label='Data Analyst / Data Science',
        weight_template=ResumeWeightTemplate(
            section_weights={
                'technical_skills': 0.9, 'experience': 1.0, 'projects': 0.8,
                'education': 0.7, 'certifications': 0.6, 'summary': 0.9,
            },
            expand_sections=['experience', 'summary'],
            compress_sections=['certifications'],
        ),
    ),
    'bsa': ResumeVersion(
        version_id='RV-BSA',
        role_type='bsa',
        label='Business Systems Analyst',
        weight_template=ResumeWeightTemplate(
            section_weights={
                'technical_skills': 0.7, 'experience': 1.0, 'projects': 0.6,
                'education': 0.7, 'certifications': 0.8, 'summary': 1.0,
            },
            expand_sections=['experience', 'summary', 'certifications'],
            compress_sections=['projects'],
        ),
    ),
    'leadership': ResumeVersion(
        version_id='RV-003',
        role_type='leadership',
        label='Leadership / Management',
        weight_template=ResumeWeightTemplate(
            section_weights={
                'technical_skills': 0.5, 'experience': 1.0, 'projects': 0.4,
                'education': 0.8, 'certifications': 0.7, 'summary': 1.0,
            },
            expand_sections=['experience', 'summary', 'education'],
            compress_sections=['technical_skills', 'projects'],
        ),
    ),
}
