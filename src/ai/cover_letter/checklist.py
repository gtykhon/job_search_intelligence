"""
Pre-Submission Checklist -- Validates cover letter before delivery.

Checks:
1. Company name appears in body
2. No forbidden phrases
3. Word count 280-420
4. Claims traceable to resume
5. At least one specific achievement with metric
6. Exactly 4 paragraphs
"""

import re
from typing import List, Tuple

from .models import (
    ChecklistItem,
    ForbiddenPhraseViolation,
    RepetitionViolation,
)
from .templates import FORBIDDEN_PHRASES


class PreSubmissionChecklist:
    """Validates a cover letter against quality constraints."""

    def run(
        self,
        cover_letter: str,
        company: str,
        resume_text: str,
    ) -> Tuple[bool, List[ChecklistItem], List[ForbiddenPhraseViolation], List[RepetitionViolation]]:
        """
        Run all checklist items. Returns (all_passed, items, forbidden_violations, repetition_violations).
        """
        items: List[ChecklistItem] = []
        forbidden_violations: List[ForbiddenPhraseViolation] = []
        repetition_violations: List[RepetitionViolation] = []

        # 1. Company name in body
        items.append(self._check_company_name(cover_letter, company))

        # 2. Forbidden phrases
        check, violations = self._check_forbidden_phrases(cover_letter)
        items.append(check)
        forbidden_violations.extend(violations)

        # 3. Word count
        items.append(self._check_word_count(cover_letter))

        # 4. Specific achievement with metric
        items.append(self._check_metric_present(cover_letter))

        # 5. Paragraph count
        items.append(self._check_paragraph_count(cover_letter))

        # 6. No repetition with resume
        check, reps = self._check_no_repetition(cover_letter, resume_text)
        items.append(check)
        repetition_violations.extend(reps)

        all_passed = all(item.passed for item in items)
        return all_passed, items, forbidden_violations, repetition_violations

    def _check_company_name(self, cover_letter: str, company: str) -> ChecklistItem:
        """Company name must appear in the body text."""
        lines = cover_letter.strip().split('\n')
        body = '\n'.join(lines[1:]) if len(lines) > 1 else cover_letter
        found = company.lower() in body.lower()
        return ChecklistItem(
            name="company_name_in_body",
            passed=found,
            detail=f"Company '{company}' {'found' if found else 'NOT found'} in letter body",
        )

    def _check_forbidden_phrases(
        self, cover_letter: str
    ) -> Tuple[ChecklistItem, List[ForbiddenPhraseViolation]]:
        """No forbidden phrases allowed."""
        cl_lower = cover_letter.lower()
        violations = []
        for phrase in FORBIDDEN_PHRASES:
            if phrase in cl_lower:
                paragraphs = [p.strip() for p in cover_letter.split('\n\n') if p.strip()]
                location = "unknown"
                for i, para in enumerate(paragraphs, 1):
                    if phrase in para.lower():
                        location = f"paragraph {i}"
                        break
                violations.append(ForbiddenPhraseViolation(phrase=phrase, location=location))

        passed = len(violations) == 0
        return (
            ChecklistItem(
                name="no_forbidden_phrases",
                passed=passed,
                detail=f"{len(violations)} forbidden phrase(s) found" if not passed else "No forbidden phrases",
            ),
            violations,
        )

    def _check_word_count(self, cover_letter: str) -> ChecklistItem:
        """Word count must be 280-420."""
        words = len(cover_letter.split())
        passed = 280 <= words <= 420
        return ChecklistItem(
            name="word_count",
            passed=passed,
            detail=f"Word count: {words} (target: 280-420)",
        )

    def _check_metric_present(self, cover_letter: str) -> ChecklistItem:
        """At least one specific achievement with a number/metric."""
        has_metric = bool(re.search(r'\d+[%xX]|\$[\d,.]+[MmKkBb]?|\d+\+|\d+\.\d+[xX]', cover_letter))
        return ChecklistItem(
            name="metric_present",
            passed=has_metric,
            detail="Specific metric found" if has_metric else "No specific metric/number found",
        )

    def _check_paragraph_count(self, cover_letter: str) -> ChecklistItem:
        """Must have exactly 4 paragraphs (excluding addressee/signature lines)."""
        paragraphs = [p.strip() for p in cover_letter.split('\n\n') if p.strip()]
        body_paragraphs = [p for p in paragraphs if len(p.split()) > 20]
        count = len(body_paragraphs)
        passed = count == 4
        return ChecklistItem(
            name="paragraph_count",
            passed=passed,
            detail=f"Body paragraphs: {count} (target: 4)",
        )

    def _check_no_repetition(
        self, cover_letter: str, resume_text: str
    ) -> Tuple[ChecklistItem, List[RepetitionViolation]]:
        """No shared metrics or >5-word phrases with resume."""
        violations = []

        # Check for shared metrics
        cl_metrics = set(re.findall(r'\d+[%xX]|\$[\d,.]+[MmKkBb]?', cover_letter))
        resume_metrics = set(re.findall(r'\d+[%xX]|\$[\d,.]+[MmKkBb]?', resume_text))
        shared_metrics = cl_metrics & resume_metrics
        for metric in shared_metrics:
            violations.append(RepetitionViolation(shared_text=metric, source="metric"))

        # Check for >5-word verbatim phrases
        cl_words = cover_letter.lower().split()
        resume_lower = resume_text.lower()
        window = 6
        for i in range(len(cl_words) - window + 1):
            phrase = ' '.join(cl_words[i:i + window])
            if phrase in resume_lower:
                common = {'in order to be able', 'as well as the ability'}
                if phrase not in common:
                    violations.append(RepetitionViolation(shared_text=phrase, source="phrase"))

        # Deduplicate
        seen = set()
        unique_violations = []
        for v in violations:
            key = (v.shared_text, v.source)
            if key not in seen:
                seen.add(key)
                unique_violations.append(v)

        passed = len(unique_violations) == 0
        return (
            ChecklistItem(
                name="no_repetition",
                passed=passed,
                detail=f"{len(unique_violations)} repetition(s) with resume" if not passed else "No repetition with resume",
            ),
            unique_violations,
        )
