"""
Platform Formatting Rules & Validator.

Defines formatting requirements per target platform and validates
content before it is delivered as an application package.

INCIDENT NOTE (October 2025):
    A cover letter was generated using LinkedIn narrative paragraph style
    and submitted to an Indeed profile. Indeed's ATS parser expects
    bullet-format content — narrative paragraphs rendered as a wall of
    text and resulted in a rejected application.

    This module is the prevention mechanism. Run the validator BEFORE
    any content generation to catch platform mismatches early and
    avoid wasting AI tokens on incorrectly formatted output.

Supported platforms:
  - indeed    : bullets REQUIRED, narrative NOT allowed, 600-word max
  - linkedin  : narrative allowed, bullets optional, 800-word max
  - resume    : narrative allowed, HTML tags forbidden, 600-word max
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class Platform(str, Enum):
    INDEED   = "indeed"
    LINKEDIN = "linkedin"
    RESUME   = "resume"

    @classmethod
    def from_string(cls, value: str) -> "Platform":
        """Case-insensitive lookup; raises ValueError if unknown."""
        try:
            return cls(value.lower().strip())
        except ValueError:
            known = ", ".join(m.value for m in cls)
            raise ValueError(f"Unknown platform '{value}'. Known platforms: {known}")


@dataclass
class PlatformRule:
    platform: Platform
    requires_bullets: bool
    allows_narrative: bool
    max_word_count: int
    forbidden_formats: List[str] = field(default_factory=list)
    required_sections: List[str] = field(default_factory=list)
    description: str = ""


PLATFORM_RULES: Dict[Platform, PlatformRule] = {
    Platform.INDEED: PlatformRule(
        platform=Platform.INDEED,
        requires_bullets=True,
        allows_narrative=False,
        max_word_count=600,
        forbidden_formats=["markdown_headers", "long_paragraphs"],
        required_sections=[],
        description=(
            "Indeed requires bullet-point formatting. Narrative paragraphs "
            "are not parsed correctly by Indeed's ATS. Use 2-5 bullets per "
            "position. Mobile-first: 6-second scanning rule applies."
        ),
    ),
    Platform.LINKEDIN: PlatformRule(
        platform=Platform.LINKEDIN,
        requires_bullets=False,
        allows_narrative=True,
        max_word_count=800,
        forbidden_formats=[],
        required_sections=[],
        description=(
            "LinkedIn allows narrative paragraphs and storytelling. "
            "Bullets are optional. Max visible without 'see more': ~200-300 chars."
        ),
    ),
    Platform.RESUME: PlatformRule(
        platform=Platform.RESUME,
        requires_bullets=False,
        allows_narrative=True,
        max_word_count=600,
        forbidden_formats=["html_tags", "markdown_headers"],
        required_sections=[],
        description=(
            "Resume cover letters should be plain text with standard formatting. "
            "No HTML tags or markdown headers. Narrative paragraphs are standard."
        ),
    ),
}


@dataclass
class PlatformValidationResult:
    passed: bool
    platform: Platform
    violations: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.passed:
            return f"[{self.platform.value.upper()}] Format validation passed."
        joined = "; ".join(self.violations)
        return f"[{self.platform.value.upper()}] Format validation FAILED: {joined}"


class PlatformFormatValidator:
    """
    Validates cover letter / profile content against platform-specific rules.

    Example::

        validator = PlatformFormatValidator()
        result = validator.validate(cover_letter_text, Platform.INDEED)
        if not result.passed:
            raise ValueError(result.summary())
    """

    _BULLET_PATTERN = re.compile(
        r"^[\s]*(?:[-*\u2022]|\d+[.)]) .+",
        re.MULTILINE,
    )
    _LONG_PARAGRAPH_PATTERN = re.compile(
        r"(?:[A-Z][^.!?\n]{20,}[.!?][\s]){2,}",
        re.DOTALL,
    )
    _MARKDOWN_HEADER_PATTERN = re.compile(r"^#{1,6}\s+.+", re.MULTILINE)
    _HTML_TAG_PATTERN = re.compile(r"<[a-zA-Z][^>]*>|</[a-zA-Z]+>")

    def validate(self, content: str, platform: Platform) -> PlatformValidationResult:
        """Validate content against the rules for the given platform."""
        rule = PLATFORM_RULES[platform]
        violations: List[str] = []
        suggestions: List[str] = []

        # 1. Word count
        word_count = len(content.split())
        if word_count > rule.max_word_count:
            violations.append(
                f"Word count {word_count} exceeds {platform.value} limit "
                f"of {rule.max_word_count} words."
            )
            suggestions.append(f"Reduce to <= {rule.max_word_count} words.")

        # 2. Bullet requirement (Indeed)
        if rule.requires_bullets:
            bullet_lines = self._BULLET_PATTERN.findall(content)
            if not bullet_lines:
                violations.append(
                    f"{platform.value.capitalize()} REQUIRES bullet-point formatting "
                    f"(-, *, bullet, or numbered list). No bullets detected."
                )
                suggestions.append(
                    "Reformat using 2-5 bullets per section. "
                    "Each bullet: action verb + achievement + metric."
                )

        # 3. Narrative paragraph check (Indeed disallows long paragraphs)
        if not rule.allows_narrative:
            long_paras = self._LONG_PARAGRAPH_PATTERN.findall(content)
            if long_paras:
                violations.append(
                    f"{platform.value.capitalize()} does not support narrative paragraphs. "
                    f"Found {len(long_paras)} long paragraph block(s)."
                )
                suggestions.append("Convert paragraphs to concise bullet points.")

        # 4. Forbidden format checks
        if "markdown_headers" in rule.forbidden_formats:
            headers = self._MARKDOWN_HEADER_PATTERN.findall(content)
            if headers:
                violations.append(
                    f"Markdown headers (# H1, ## H2, etc.) are not allowed for "
                    f"{platform.value}. Found {len(headers)}."
                )
                suggestions.append("Remove markdown headers; use plain text section labels.")

        if "html_tags" in rule.forbidden_formats:
            tags = self._HTML_TAG_PATTERN.findall(content)
            if tags:
                unique_tags = list(set(tags))[:5]
                violations.append(
                    f"HTML tags are not allowed for {platform.value}. "
                    f"Found: {', '.join(unique_tags)}"
                )
                suggestions.append("Strip all HTML tags and use plain text only.")

        if "long_paragraphs" in rule.forbidden_formats:
            long_paras = self._LONG_PARAGRAPH_PATTERN.findall(content)
            if long_paras:
                violations.append(
                    f"Long narrative paragraphs detected ({len(long_paras)} block(s)). "
                    f"{platform.value.capitalize()} requires concise bullet points."
                )

        return PlatformValidationResult(
            passed=len(violations) == 0,
            platform=platform,
            violations=violations,
            suggestions=suggestions,
        )

    def detect_platform_mismatch(
        self,
        content: str,
        declared_platform: Platform,
    ) -> Tuple[bool, str]:
        """
        Detect if content appears formatted for a DIFFERENT platform than declared.

        Classic October 2025 incident: LinkedIn narrative paragraphs submitted to Indeed.
        Returns (is_mismatch, explanation).
        """
        has_bullets = bool(self._BULLET_PATTERN.search(content))
        has_long_para = bool(self._LONG_PARAGRAPH_PATTERN.search(content))
        word_count = len(content.split())

        # Detect narrative style: no bullets AND substantial text content
        is_narrative = not has_bullets and word_count >= 30

        if declared_platform == Platform.INDEED:
            if is_narrative or (has_long_para and not has_bullets):
                return (
                    True,
                    "Content appears to be narrative style (no bullet points detected) "
                    "but target platform is Indeed (requires bullets). "
                    "This matches the October 2025 platform confusion incident pattern.",
                )
        return False, ""
