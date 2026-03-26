"""
Application Package Generator — Template-based resume and cover letter generation.

Generates tailored .txt files for job applications using keyword matching
against the job description. No AI API calls; pure template-based output.
AI-powered generation can layer on top later.
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .scoring import TECH_KEYWORDS, JD_TECH_KEYWORDS

logger = logging.getLogger(__name__)

# Project-root-relative default output directory
_DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "packages"


# ── Public API ──────────────────────────────────────────────────────────


def generate_application_package(
    job: dict,
    resume_text: str,
    output_dir: Path | None = None,
) -> dict:
    """Generate a tailored resume and cover letter package for a job application.

    Args:
        job: Job dict with keys such as ``title``, ``company``, ``description``,
             ``location``, and ``id`` (or ``job_id``).
        resume_text: The full text of the user's master resume.
        output_dir: Base directory for generated packages.  Defaults to
                     ``<project_root>/data/packages/``.

    Returns:
        A dict with ``resume_path`` (Path), ``cover_letter_path`` (Path), and
        ``status`` (str — ``"success"`` or ``"error"``).  On error the paths
        are ``None`` and an ``error`` key contains the message.
    """
    if output_dir is None:
        output_dir = _DEFAULT_OUTPUT_DIR

    try:
        # Validate required fields
        title = job.get("title", "Unknown Position")
        company = job.get("company", "Unknown Company")
        description = job.get("description", "")
        location = job.get("location", "")
        job_id = job.get("id") or job.get("job_id", "0")

        if not description:
            logger.warning("Job description is empty for %s at %s", title, company)

        if not resume_text.strip():
            raise ValueError("Resume text cannot be empty")

        # Build output directory
        company_slug = _slugify(company)
        package_dir = Path(output_dir) / f"{company_slug}_{job_id}"
        package_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Package directory created: %s", package_dir)

        # Skill analysis
        matched_skills, missing_skills = _match_skills(resume_text, description)
        key_requirements = _extract_key_requirements(description)

        # Generate resume
        resume_content = _build_tailored_resume(
            resume_text, title, company, matched_skills, missing_skills, key_requirements,
        )
        resume_path = package_dir / "resume.txt"
        resume_path.write_text(resume_content, encoding="utf-8")
        logger.info("Resume written to %s", resume_path)

        # Generate cover letter
        cover_letter_content = _build_cover_letter(
            title, company, location, description,
            resume_text, matched_skills, key_requirements,
        )
        cover_letter_path = package_dir / "cover_letter.txt"
        cover_letter_path.write_text(cover_letter_content, encoding="utf-8")
        logger.info("Cover letter written to %s", cover_letter_path)

        return {
            "resume_path": resume_path,
            "cover_letter_path": cover_letter_path,
            "status": "success",
        }

    except Exception as exc:
        logger.exception("Failed to generate application package: %s", exc)
        return {
            "resume_path": None,
            "cover_letter_path": None,
            "status": "error",
            "error": str(exc),
        }


# ── Skill / Requirement Extraction ─────────────────────────────────────


def _extract_key_requirements(job_description: str) -> List[str]:
    """Pull the top requirements from a job description.

    Looks for bullet-pointed or numbered items inside common *requirements*
    sections.  Falls back to extracting any bullet lines if no explicit
    section header is found.

    Returns:
        A list of requirement strings (cleaned, deduplicated, max 10).
    """
    jd_lower = job_description.lower()

    # Try to isolate a requirements/qualifications section
    section_match = re.search(
        r"(?:required|requirements|must[\s-]have|qualifications|what you.?ll need)"
        r"[:\s]*\n(.*?)(?=\n\s*(?:preferred|nice[\s-]to[\s-]have|bonus|benefits|about us|perks|\Z))",
        jd_lower,
        re.DOTALL,
    )
    section = section_match.group(1) if section_match else job_description

    # Extract bullet / numbered list items
    bullets = re.findall(
        r"(?:^|\n)\s*(?:[-*\u2022\u25E6]|\d+[.)]\s)\s*(.+)",
        section,
    )

    if not bullets:
        # Fallback: split into sentences and keep ones that sound like requirements
        sentences = re.split(r"[.\n]+", section)
        bullets = [
            s.strip() for s in sentences
            if len(s.strip()) > 15 and any(
                kw in s.lower()
                for kw in ("experience", "proficiency", "knowledge", "ability",
                           "skill", "familiar", "degree", "understanding")
            )
        ]

    # Clean up and deduplicate
    seen: set[str] = set()
    requirements: List[str] = []
    for item in bullets:
        cleaned = item.strip().rstrip(".").strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            requirements.append(cleaned)

    return requirements[:10]


def _match_skills(
    resume_text: str,
    job_description: str,
) -> Tuple[List[str], List[str]]:
    """Compare skills found in the resume against those in the job description.

    Uses :data:`TECH_KEYWORDS` from the scoring module for extraction.

    Returns:
        ``(matched_skills, missing_skills)`` — each a sorted list of strings.
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    job_skills = {kw for kw in JD_TECH_KEYWORDS if kw in jd_lower}
    resume_skills = {kw for kw in TECH_KEYWORDS if kw in resume_lower}

    matched = sorted(job_skills & resume_skills)
    missing = sorted(job_skills - resume_skills)

    logger.debug(
        "Skill match: %d matched, %d missing out of %d job skills",
        len(matched), len(missing), len(job_skills),
    )
    return matched, missing


# ── Template Builders ───────────────────────────────────────────────────


def _build_tailored_resume(
    resume_text: str,
    title: str,
    company: str,
    matched_skills: List[str],
    missing_skills: List[str],
    key_requirements: List[str],
) -> str:
    """Build a tailored resume text that highlights relevant skills.

    Prepends a targeted summary section to the original resume, calling out
    the skills and requirements that align with the specific role.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    header_lines = [
        f"TAILORED RESUME — {title} at {company}",
        f"Generated: {today}",
        "=" * 60,
        "",
    ]

    # Targeted summary
    summary_lines = ["TARGETED SUMMARY", "-" * 40]
    summary_lines.append(
        f"Experienced professional seeking the {title} role at {company}."
    )
    if matched_skills:
        summary_lines.append(
            f"Key matching skills: {', '.join(matched_skills[:8])}."
        )
    if key_requirements:
        summary_lines.append("")
        summary_lines.append("Relevant qualifications:")
        for req in key_requirements[:5]:
            summary_lines.append(f"  - {req}")
    summary_lines.append("")

    # Skills highlight
    skills_lines = ["SKILLS ALIGNMENT", "-" * 40]
    if matched_skills:
        skills_lines.append(f"Matched ({len(matched_skills)}): {', '.join(matched_skills)}")
    if missing_skills:
        skills_lines.append(f"To develop ({len(missing_skills)}): {', '.join(missing_skills)}")
    skills_lines.append("")

    # Original resume
    resume_lines = [
        "FULL RESUME",
        "-" * 40,
        resume_text.strip(),
    ]

    return "\n".join(header_lines + summary_lines + skills_lines + resume_lines) + "\n"


def _build_cover_letter(
    title: str,
    company: str,
    location: str,
    job_description: str,
    resume_text: str,
    matched_skills: List[str],
    key_requirements: List[str],
) -> str:
    """Build a 4-paragraph cover letter from templates.

    Paragraph structure:
        1. Opening — reference the specific role and company, express interest.
        2. Relevant experience — match 2-3 key requirements with resume experience.
        3. Technical alignment — mention specific overlapping technologies/skills.
        4. Closing — express enthusiasm and availability.
    """
    today = datetime.now().strftime("%B %d, %Y")

    # ── Header ──────────────────────────────────────────────────────
    header = (
        f"{today}\n"
        f"\n"
        f"Re: {title}\n"
        f"{company}"
    )
    if location:
        header += f" — {location}"
    header += "\n"

    # ── Paragraph 1: Opening ────────────────────────────────────────
    p1 = (
        f"Dear Hiring Manager,\n"
        f"\n"
        f"I am writing to express my strong interest in the {title} position at "
        f"{company}. After reviewing the role requirements, I am confident that "
        f"my background and skills make me a well-qualified candidate for this "
        f"opportunity."
    )

    # ── Paragraph 2: Relevant experience ────────────────────────────
    experience_points = _build_experience_paragraph(
        key_requirements, resume_text, title,
    )
    p2 = (
        f"Throughout my career, I have developed expertise directly relevant to "
        f"this role. {experience_points}"
    )

    # ── Paragraph 3: Technical alignment ────────────────────────────
    if matched_skills:
        skills_display = ", ".join(matched_skills[:6])
        remaining = len(matched_skills) - 6
        if remaining > 0:
            skills_display += f", and {remaining} additional technologies"
        p3 = (
            f"On the technical side, my experience includes {skills_display}. "
            f"These skills align closely with the technical requirements outlined "
            f"in the job description, and I am eager to apply them to the "
            f"challenges at {company}."
        )
    else:
        p3 = (
            f"While my technical background may differ from the specific stack "
            f"listed in the job description, I have a strong track record of "
            f"quickly ramping up on new technologies and contributing "
            f"meaningfully from day one."
        )

    # ── Paragraph 4: Closing ────────────────────────────────────────
    p4 = (
        f"I am enthusiastic about the opportunity to contribute to {company} "
        f"and would welcome the chance to discuss how my experience aligns with "
        f"your team's goals. I am available for an interview at your earliest "
        f"convenience and look forward to hearing from you.\n"
        f"\n"
        f"Sincerely,\n"
        f"[Your Name]"
    )

    return "\n\n".join([header, p1, p2, p3, p4]) + "\n"


def _build_experience_paragraph(
    key_requirements: List[str],
    resume_text: str,
    title: str,
) -> str:
    """Match 2-3 key requirements to sentences in the resume.

    Returns a string of 2-3 sentences that connect resume experience to the
    job requirements.
    """
    resume_lower = resume_text.lower()
    points: List[str] = []

    for req in key_requirements:
        if len(points) >= 3:
            break
        # Check that at least a few significant words from the requirement
        # appear in the resume
        words = [w for w in re.findall(r"[a-z]{4,}", req.lower()) if len(w) > 3]
        overlap = sum(1 for w in words if w in resume_lower)
        if overlap >= max(1, len(words) // 3):
            points.append(
                f"In particular, I bring direct experience with "
                f"{req.rstrip('.').lower()}, as reflected in my professional history."
            )

    if not points:
        points.append(
            f"My professional background includes experience relevant to the "
            f"core responsibilities of the {title} role, and I am prepared to "
            f"make an immediate impact."
        )

    return " ".join(points)


# ── Utilities ───────────────────────────────────────────────────────────


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug.

    Lowercases, replaces non-alphanumeric characters with hyphens, collapses
    consecutive hyphens, and strips leading/trailing hyphens.

    >>> _slugify("Acme Corp.")
    'acme-corp'
    >>> _slugify("My  Company -- Inc")
    'my-company-inc'
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")
