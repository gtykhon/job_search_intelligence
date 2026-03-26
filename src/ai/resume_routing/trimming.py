"""
Resume Trimming -- Section-level trimming and compression per role type.

Applies weight templates to adjust resume content emphasis.
"""

import re
import logging
from typing import Dict, List

from .models import ResumeVersion

logger = logging.getLogger(__name__)

# Section header patterns for detection
SECTION_PATTERNS = {
    'summary': r'(?i)^(summary|professional summary|objective|profile)',
    'experience': r'(?i)^(experience|work experience|employment|professional experience)',
    'technical_skills': r'(?i)^(skills|technical skills|core competencies|technologies)',
    'education': r'(?i)^(education|academic|degrees)',
    'projects': r'(?i)^(projects?|portfolio|personal projects|key projects)',
    'certifications': r'(?i)^(certifications?|licenses?|credentials)',
    'awards': r'(?i)^(awards?|honors?|achievements?)',
}

# AI/NLP specialty signals -- when detected, apply specialty trimming
AI_NLP_SIGNALS = {
    'machine learning', 'deep learning', 'nlp', 'natural language processing',
    'computer vision', 'neural network', 'transformer', 'llm', 'large language model',
    'pytorch', 'tensorflow', 'hugging face', 'bert', 'gpt',
}


def parse_sections(resume_text: str) -> Dict[str, str]:
    """Parse resume into named sections based on header patterns."""
    lines = resume_text.split('\n')
    sections: Dict[str, str] = {}
    current_section = 'header'
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        matched_section = None

        for section_name, pattern in SECTION_PATTERNS.items():
            if re.match(pattern, stripped):
                matched_section = section_name
                break

        if matched_section:
            if current_lines:
                sections[current_section] = '\n'.join(current_lines)
            current_section = matched_section
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_section] = '\n'.join(current_lines)

    return sections


def apply_trimming(resume_text: str, version: ResumeVersion) -> str:
    """
    Apply weight-based trimming to resume sections.

    - Sections in compress_sections: keep first 2-3 bullet points only
    - Sections in expand_sections: kept fully
    - Other sections: kept as-is
    """
    sections = parse_sections(resume_text)
    template = version.weight_template

    result_parts = []

    if 'header' in sections:
        result_parts.append(sections['header'])

    section_order = ['summary', 'experience', 'technical_skills', 'projects',
                     'education', 'certifications', 'awards']

    for section_name in section_order:
        if section_name not in sections:
            continue

        content = sections[section_name]

        if section_name in template.compress_sections:
            content = _compress_section(content)

        result_parts.append(content)

    for section_name, content in sections.items():
        if section_name not in section_order and section_name != 'header':
            result_parts.append(content)

    return '\n\n'.join(result_parts)


def detect_ai_nlp_specialty(resume_text: str) -> bool:
    """Detect if resume has AI/NLP specialty track."""
    text_lower = resume_text.lower()
    signal_count = sum(1 for s in AI_NLP_SIGNALS if s in text_lower)
    return signal_count >= 3


def apply_ai_nlp_trimming(resume_text: str) -> str:
    """
    AI/NLP specialty trimming: compress non-relevant roles, keep ML/NLP projects.

    Only applied when AI/NLP specialty is detected.
    """
    if not detect_ai_nlp_specialty(resume_text):
        return resume_text

    sections = parse_sections(resume_text)

    if 'experience' in sections:
        sections['experience'] = _compress_non_ai_roles(sections['experience'])

    result_parts = []
    for section_name in ['header', 'summary', 'experience', 'technical_skills',
                         'projects', 'education', 'certifications', 'awards']:
        if section_name in sections:
            result_parts.append(sections[section_name])

    return '\n\n'.join(result_parts)


def _compress_section(content: str) -> str:
    """Compress a section to its header + first 3 bullet points."""
    lines = content.split('\n')
    if not lines:
        return content

    result = [lines[0]]
    bullet_count = 0
    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith(('-', '*', '\u2022', '\u2013')) or re.match(r'^\d+\.', stripped):
            bullet_count += 1
            if bullet_count <= 3:
                result.append(line)
        elif bullet_count == 0:
            result.append(line)

    return '\n'.join(result)


def _compress_non_ai_roles(experience_content: str) -> str:
    """Keep AI/NLP-related roles fully, compress others."""
    lines = experience_content.split('\n')
    result = [lines[0]]

    current_role_lines: List[str] = []
    current_role_is_ai = False

    for line in lines[1:]:
        stripped = line.strip()

        if stripped and not stripped.startswith(('-', '*', '\u2022', '\u2013')) and len(stripped) > 5:
            if current_role_lines:
                if current_role_is_ai:
                    result.extend(current_role_lines)
                else:
                    result.extend(_keep_first_n_bullets(current_role_lines, 2))

            current_role_lines = [line]
            current_role_is_ai = any(s in stripped.lower() for s in AI_NLP_SIGNALS)
        else:
            current_role_lines.append(line)
            if any(s in stripped.lower() for s in AI_NLP_SIGNALS):
                current_role_is_ai = True

    if current_role_lines:
        if current_role_is_ai:
            result.extend(current_role_lines)
        else:
            result.extend(_keep_first_n_bullets(current_role_lines, 2))

    return '\n'.join(result)


def _keep_first_n_bullets(lines: List[str], n: int) -> List[str]:
    """Keep the role header and first N bullet points."""
    result = []
    bullet_count = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('-', '*', '\u2022', '\u2013')) or re.match(r'^\d+\.', stripped):
            bullet_count += 1
            if bullet_count <= n:
                result.append(line)
        else:
            result.append(line)
    return result
