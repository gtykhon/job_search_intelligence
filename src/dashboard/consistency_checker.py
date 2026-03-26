"""
Cross-Platform Consistency Checker.

Validates that key facts are consistent across resume, LinkedIn profile
snapshot, and cover letter. Catches drift between materials that could
cause interview-stage authenticity failures.

Checked fields:
  - Education credentials (BBA Managerial Finance)
  - Azure service stack (Form Recognizer, Blob Storage, Web Apps — NOT Key Vault)
  - Contact information consistency
  - Scope language consistency (leading vs supporting)

Severity:
  CRITICAL — factual contradiction (wrong degree, unverified technology)
  WARNING  — phrasing mismatch (scope language differs between docs)
  INFO     — cosmetic difference (capitalization)

Usage:
    checker = CrossPlatformConsistencyChecker()
    report = checker.check(resume_text, cover_letter_text, linkedin_snapshot)
    if not report.passed:
        for issue in report.inconsistencies:
            print(issue.severity, issue.field, issue.description)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class InconsistencySeverity(str, Enum):
    CRITICAL = "critical"
    WARNING  = "warning"
    INFO     = "info"


@dataclass
class Inconsistency:
    field: str
    severity: InconsistencySeverity
    source_a: str
    source_b: str
    document_a: str
    document_b: str
    description: str


@dataclass
class ConsistencyReport:
    passed: bool                          # True if no CRITICAL inconsistencies
    inconsistencies: List[Inconsistency] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0

    def summary(self) -> str:
        if self.passed and not self.inconsistencies:
            return "All cross-platform consistency checks passed."
        parts = []
        if self.critical_count:
            parts.append(f"{self.critical_count} critical")
        if self.warning_count:
            parts.append(f"{self.warning_count} warning")
        return f"Consistency issues: {', '.join(parts)}."


class CrossPlatformConsistencyChecker:
    """
    Field-level consistency validator for multi-document job search materials.
    """

    # Ground truth: verified Azure services in known tech stack
    VERIFIED_AZURE: frozenset = frozenset({
        "azure form recognizer",
        "azure blob storage",
        "azure web apps",
        "azure devops",
        "azure active directory",
    })

    # Azure services NOT in verified stack — flag as CRITICAL if found
    UNVERIFIED_AZURE: frozenset = frozenset({
        "azure key vault",
        "azure functions",
        "azure cosmos",
        "azure synapse",
        "azure databricks",
    })

    # Canonical education
    CANONICAL_DEGREE = "bba"
    CANONICAL_FIELD  = "managerial finance"

    # Scope inflation pairs
    SCOPE_PAIRS: List[Tuple[str, str]] = [
        ("led",        "supported"),
        ("architected","implemented"),
        ("owned",      "contributed"),
        ("designed",   "assisted"),
    ]

    def check(
        self,
        resume_text: str,
        cover_letter_text: str,
        linkedin_snapshot: Optional[str] = None,
    ) -> ConsistencyReport:
        """
        Run all consistency checks across provided documents.
        linkedin_snapshot is optional — checks are skipped if not provided.
        """
        docs = {
            "resume": resume_text,
            "cover_letter": cover_letter_text,
        }
        if linkedin_snapshot:
            docs["linkedin"] = linkedin_snapshot

        inconsistencies: List[Inconsistency] = []

        inconsistencies.extend(self._check_education(docs))
        inconsistencies.extend(self._check_azure_services(docs))
        inconsistencies.extend(self._check_scope_language(
            resume_text, cover_letter_text
        ))
        if linkedin_snapshot:
            inconsistencies.extend(self._check_contact_info(docs))

        critical = sum(1 for i in inconsistencies if i.severity == InconsistencySeverity.CRITICAL)
        warnings = sum(1 for i in inconsistencies if i.severity == InconsistencySeverity.WARNING)

        return ConsistencyReport(
            passed=critical == 0,
            inconsistencies=inconsistencies,
            critical_count=critical,
            warning_count=warnings,
        )

    # ------------------------------------------------------------------
    # Education
    # ------------------------------------------------------------------

    def _check_education(self, docs: dict) -> List[Inconsistency]:
        inconsistencies: List[Inconsistency] = []
        # Extract degree mentions per document
        degree_re = re.compile(
            r"\b(b\.?b\.?a\.?|b\.?s\.?|b\.?a\.?|bachelor[s]?|m\.?b\.?a\.?|master[s]?|ph\.?d\.?)\b",
            re.IGNORECASE,
        )
        field_re = re.compile(
            r"(managerial finance|finance|computer science|information systems|"
            r"software engineering|business administration)",
            re.IGNORECASE,
        )

        degrees = {}
        fields = {}
        for doc_name, text in docs.items():
            d = degree_re.findall(text)
            f = field_re.findall(text)
            degrees[doc_name] = [x.upper().replace(".", "") for x in d] if d else []
            fields[doc_name] = [x.lower() for x in f] if f else []

        # Cross-check: if two docs both mention degrees, they should agree
        doc_names = list(docs.keys())
        for i in range(len(doc_names)):
            for j in range(i + 1, len(doc_names)):
                a, b = doc_names[i], doc_names[j]
                a_degrees = set(degrees.get(a, []))
                b_degrees = set(degrees.get(b, []))
                if a_degrees and b_degrees and not (a_degrees & b_degrees):
                    inconsistencies.append(Inconsistency(
                        field="education_degree",
                        severity=InconsistencySeverity.CRITICAL,
                        source_a=", ".join(a_degrees),
                        source_b=", ".join(b_degrees),
                        document_a=a,
                        document_b=b,
                        description=(
                            f"Degree mismatch: {a} shows {a_degrees}, "
                            f"{b} shows {b_degrees}."
                        ),
                    ))

        return inconsistencies

    # ------------------------------------------------------------------
    # Azure services
    # ------------------------------------------------------------------

    def _check_azure_services(self, docs: dict) -> List[Inconsistency]:
        inconsistencies: List[Inconsistency] = []

        for doc_name, text in docs.items():
            text_lower = text.lower()
            for service in self.UNVERIFIED_AZURE:
                if service in text_lower:
                    inconsistencies.append(Inconsistency(
                        field="azure_services",
                        severity=InconsistencySeverity.CRITICAL,
                        source_a=service.title(),
                        source_b="Not in verified stack",
                        document_a=doc_name,
                        document_b="verified_stack",
                        description=(
                            f"'{service.title()}' found in {doc_name} but is NOT in "
                            f"the verified Azure stack (Form Recognizer, Blob Storage, "
                            f"Web Apps, DevOps). Risk of interview failure."
                        ),
                    ))

        return inconsistencies

    # ------------------------------------------------------------------
    # Contact info
    # ------------------------------------------------------------------

    def _check_contact_info(self, docs: dict) -> List[Inconsistency]:
        inconsistencies: List[Inconsistency] = []
        email_re = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
        phone_re = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")

        emails: dict = {n: set(email_re.findall(t)) for n, t in docs.items()}
        phones: dict = {n: set(phone_re.findall(t)) for n, t in docs.items()}

        doc_names = list(docs.keys())
        for i in range(len(doc_names)):
            for j in range(i + 1, len(doc_names)):
                a, b = doc_names[i], doc_names[j]
                e_a = emails.get(a, set())
                e_b = emails.get(b, set())
                if e_a and e_b and not (e_a & e_b):
                    inconsistencies.append(Inconsistency(
                        field="contact_email",
                        severity=InconsistencySeverity.CRITICAL,
                        source_a=", ".join(e_a),
                        source_b=", ".join(e_b),
                        document_a=a,
                        document_b=b,
                        description=f"Email mismatch between {a} and {b}.",
                    ))
                p_a = phones.get(a, set())
                p_b = phones.get(b, set())
                if p_a and p_b and not (p_a & p_b):
                    inconsistencies.append(Inconsistency(
                        field="contact_phone",
                        severity=InconsistencySeverity.WARNING,
                        source_a=", ".join(p_a),
                        source_b=", ".join(p_b),
                        document_a=a,
                        document_b=b,
                        description=f"Phone number mismatch between {a} and {b}.",
                    ))
        return inconsistencies

    # ------------------------------------------------------------------
    # Scope language
    # ------------------------------------------------------------------

    def _check_scope_language(
        self, resume: str, cover_letter: str
    ) -> List[Inconsistency]:
        """
        Warn when cover letter uses stronger scope language than resume supports.
        E.g. CL says 'led' but resume only says 'supported'.
        """
        inconsistencies: List[Inconsistency] = []
        resume_lower = resume.lower()
        cl_lower = cover_letter.lower()

        for strong_word, weak_word in self.SCOPE_PAIRS:
            cl_has_strong   = re.search(r"\b" + strong_word + r"\b", cl_lower)
            resume_has_strong = re.search(r"\b" + strong_word + r"\b", resume_lower)
            resume_has_weak   = re.search(r"\b" + weak_word + r"\b", resume_lower)

            if cl_has_strong and not resume_has_strong and resume_has_weak:
                inconsistencies.append(Inconsistency(
                    field="scope_language",
                    severity=InconsistencySeverity.WARNING,
                    source_a=f"'{strong_word}' (cover letter)",
                    source_b=f"'{weak_word}' (resume)",
                    document_a="cover_letter",
                    document_b="resume",
                    description=(
                        f"Cover letter uses '{strong_word}' but resume uses "
                        f"'{weak_word}' for similar context. Verify scope is accurate."
                    ),
                ))

        return inconsistencies
