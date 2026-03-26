"""
Sectional resume and cover letter generation pipeline.

Instead of one monolithic LLM call, this pipeline:
1. Parses the track document into structured sections
2. Inserts static parts (header, contact, education) automatically
3. Generates each resume section with a focused prompt and validation
4. Generates each cover letter paragraph with anti-repetition checks

This prevents skill inflation, fabrication, and resume/cover-letter duplication.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# Employer list read from env — keeps employment history out of source code.
_raw_employers = os.getenv("CANDIDATE_EMPLOYERS", "your previous employers")
CANDIDATE_EMPLOYERS = [e.strip() for e in _raw_employers.split(",") if e.strip()]
CANDIDATE_EMPLOYERS_STR = ", ".join(CANDIDATE_EMPLOYERS)

CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "")
CANDIDATE_NAME_SLUG = CANDIDATE_NAME.lower().replace(" ", "_").replace(".", "") if CANDIDATE_NAME else ""

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────────────


@dataclass
class ContactInfo:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""


@dataclass
class EducationEntry:
    degree: str = ""
    school: str = ""
    location: str = ""
    date: str = ""


@dataclass
class WorkRole:
    company: str = ""
    title: str = ""
    dates: str = ""
    location: str = ""
    bullets: List[str] = field(default_factory=list)
    stack: str = ""  # engineering stack line
    relevance_score: float = 0.0  # computed against JD


@dataclass
class SkillInventory:
    tier1: List[str] = field(default_factory=list)  # production, interview-survivable
    tier2: List[str] = field(default_factory=list)  # personal/staging projects
    not_found: List[str] = field(default_factory=list)  # explicit gaps


@dataclass
class ParsedTrack:
    contact: ContactInfo = field(default_factory=ContactInfo)
    education: List[EducationEntry] = field(default_factory=list)
    summary: str = ""
    roles: List[WorkRole] = field(default_factory=list)
    skills: SkillInventory = field(default_factory=SkillInventory)
    raw_skills_text: str = ""  # original skills section for reference


@dataclass
class GeneratedResume:
    full_text: str = ""
    header: str = ""
    summary: str = ""
    skills: str = ""
    experience: str = ""
    growth_areas: str = ""
    metrics_used: List[str] = field(default_factory=list)
    skills_claimed: List[str] = field(default_factory=list)


@dataclass
class GeneratedCoverLetter:
    full_text: str = ""
    opening: str = ""
    experience: str = ""
    fit: str = ""
    closing: str = ""


# ── Track Document Parser ────────────────────────────────────────────────


class TrackDocParser:
    """Parse a track reference document into structured data."""

    def parse(self, text: str) -> ParsedTrack:
        track = ParsedTrack()
        track.contact = self._parse_contact(text)
        track.education = self._parse_education(text)
        track.summary = self._parse_summary(text)
        track.roles = self._parse_roles(text)
        track.skills = self._parse_skills(text)
        track.raw_skills_text = self._extract_skills_section(text)

        logger.info(
            "Parsed track doc: %d roles, %d tier1 skills, %d tier2 skills, %d gaps",
            len(track.roles),
            len(track.skills.tier1),
            len(track.skills.tier2),
            len(track.skills.not_found),
        )
        return track

    def _parse_contact(self, text: str) -> ContactInfo:
        info = ContactInfo()
        # Extract name from first header
        if CANDIDATE_NAME_SLUG and CANDIDATE_NAME_SLUG in text.lower():
            info.name = CANDIDATE_NAME

        # Parse contact table
        for line in text.split("\n"):
            line_lower = line.lower().strip()
            if "| email" in line_lower or "| e-mail" in line_lower:
                info.email = self._extract_table_value(line)
            elif "| phone" in line_lower:
                info.phone = self._extract_table_value(line)
            elif "| location" in line_lower:
                info.location = self._extract_table_value(line)
            elif "| linkedin" in line_lower:
                info.linkedin = self._extract_table_value(line)
            elif "| github" in line_lower:
                info.github = self._extract_table_value(line)
        return info

    def _parse_education(self, text: str) -> List[EducationEntry]:
        entries = []
        # Find education section
        edu_match = re.search(
            r"## EDUCATION\s*\n+(.*?)(?=\n##|\Z)",
            text, re.DOTALL | re.IGNORECASE
        )
        if edu_match:
            block = edu_match.group(1).strip()
            # Parse "**Degree**\nSchool | Location | Date"
            degree_m = re.search(r"\*\*(.+?)\*\*", block)
            if degree_m:
                entry = EducationEntry(degree=degree_m.group(1))
                # Next non-empty line after degree has school info
                remaining = block[degree_m.end():].strip()
                # Take only first line (stop at warnings/notes)
                first_line = remaining.split("\n")[0].strip()
                parts = first_line.split("|")
                if len(parts) >= 3:
                    entry.school = parts[0].strip()
                    entry.location = parts[1].strip()
                    entry.date = parts[2].strip()
                elif len(parts) >= 1:
                    entry.school = parts[0].strip()
                entries.append(entry)
        return entries

    def _parse_summary(self, text: str) -> str:
        match = re.search(
            r"## PROFESSIONAL SUMMARY.*?\n+(.*?)(?=\n---|\n##)",
            text, re.DOTALL | re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
        return ""

    def _parse_roles(self, text: str) -> List[WorkRole]:
        roles = []
        # Split by ### headers that look like role entries
        role_pattern = re.compile(
            r"### (.+?) — (.+?)$\s*"
            r"\*\*(.+?)\*\*\s*\n"
            r"\*\*Title:\*\* (.+?)$",
            re.MULTILINE
        )
        # More flexible pattern for the actual format
        sections = re.split(r"\n### ", text)
        for section in sections[1:]:  # skip before first ###
            role = self._parse_single_role("### " + section)
            if role and role.company:
                roles.append(role)
        return roles

    def _parse_single_role(self, section: str) -> Optional[WorkRole]:
        role = WorkRole()
        lines = section.split("\n")
        if not lines:
            return None

        # First line: header like "Employer → Division — January 2022 to March 2024"
        header = lines[0].lstrip("#").strip()

        # Skip non-role sections
        skip_keywords = [
            "programming", "cloud", "data engineering", "ai / ml",
            "development tools", "api &", "architecture", "compliance",
            "authentication", "employment structure"
        ]
        if any(kw in header.lower() for kw in skip_keywords):
            return None

        # Parse company and dates from header
        if "—" in header:
            parts = header.split("—", 1)
            role.company = parts[0].strip()
            role.dates = parts[1].strip() if len(parts) > 1 else ""
        else:
            role.company = header

        # Find title and location in the body
        body = "\n".join(lines[1:])
        title_m = re.search(r"\*\*(?:Title|Engineering Title):\*\*\s*(.+?)$", body, re.MULTILINE)
        if title_m:
            role.title = title_m.group(1).strip()

        loc_m = re.search(r"\*\*(.+?(?:VA|DC|MD|NY).+?)\*\*", body)
        if loc_m:
            role.location = loc_m.group(1).strip()

        # Extract bullets (lines starting with -)
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("- ") and not stripped.startswith("- *"):
                bullet = stripped[2:].strip()
                # Skip scope boundary notes
                if any(skip in bullet.lower() for skip in [
                    "scope boundaries", "overall fastapi",
                    "did not build", "deployments were"
                ]):
                    continue
                role.bullets.append(bullet)

        # Extract stack
        stack_m = re.search(r"\*\*Engineering stack:\*\*\s*(.+?)$", body, re.MULTILINE)
        if stack_m:
            role.stack = stack_m.group(1).strip()

        return role if role.bullets else None

    def _parse_skills(self, text: str) -> SkillInventory:
        inv = SkillInventory()
        skills_section = self._extract_skills_section(text)
        if not skills_section:
            return inv

        for line in skills_section.split("\n"):
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            if len(cells) < 2:
                continue

            skill_name = cells[0].strip()
            # Skip header rows
            if skill_name.lower() in [
                "language", "technology", "capability", "tool", "pattern",
                "domain", "field", "value"
            ]:
                continue

            tier_cell = cells[1].lower() if len(cells) > 1 else ""

            if "not found" in tier_cell or "❌" in stripped:
                # Split compound entries
                clean = re.sub(r"[❌⚠️*`]", "", skill_name).strip()
                # Skip if skill name is just "NOT FOUND" itself
                if clean.upper() == "NOT FOUND" or len(clean) < 3:
                    continue
                base = re.sub(r"\(.*?\)", "", clean).strip()
                if "/" in base:
                    for sub in base.split("/"):
                        s = sub.strip()
                        if s and 2 < len(s) < 35:
                            inv.not_found.append(s.lower())
                elif base and 2 < len(base) < 35:
                    inv.not_found.append(base.lower())
                # Also extract parenthetical items
                for paren in re.findall(r"\(([^)]+)\)", skill_name):
                    for item in paren.split(","):
                        item = item.strip()
                        if item and 2 < len(item) < 35:
                            inv.not_found.append(item.lower())
            elif "tier 1" in tier_cell:
                clean = re.sub(r"[*`]", "", skill_name).strip()
                # Remove parenthetical notes for display
                display = re.sub(r"\s*\(.*?\)", "", clean).strip()
                if display and len(display) < 50:
                    inv.tier1.append(display)
            elif "tier 2" in tier_cell:
                clean = re.sub(r"[*`]", "", skill_name).strip()
                display = re.sub(r"\s*\(.*?\)", "", clean).strip()
                if display and len(display) < 50:
                    inv.tier2.append(display)

        # Deduplicate
        inv.not_found = sorted(set(inv.not_found))
        inv.tier1 = list(dict.fromkeys(inv.tier1))
        inv.tier2 = list(dict.fromkeys(inv.tier2))
        return inv

    def _extract_skills_section(self, text: str) -> str:
        match = re.search(
            r"## TECHNICAL SKILLS.*?\n(.*?)(?=\n## [A-Z]|\Z)",
            text, re.DOTALL | re.IGNORECASE
        )
        return match.group(1) if match else ""

    @staticmethod
    def _extract_table_value(line: str) -> str:
        cells = [c.strip() for c in line.split("|") if c.strip()]
        return cells[-1] if len(cells) >= 2 else ""


# ── Role Relevance Scorer ────────────────────────────────────────────────


def score_roles_for_job(
    roles: List[WorkRole],
    job_description: str,
    max_roles: int = 4,
) -> List[WorkRole]:
    """Score and select the most relevant roles for a job description.

    Uses keyword overlap between role bullets/stack and job description.
    Returns roles sorted by relevance score, limited to max_roles.
    """
    jd_words = set(re.findall(r"\b[a-z]{3,}\b", job_description.lower()))

    for role in roles:
        combined = " ".join(role.bullets) + " " + role.stack + " " + role.title
        role_words = set(re.findall(r"\b[a-z]{3,}\b", combined.lower()))
        overlap = jd_words & role_words
        # Boost for tech-specific terms
        tech_terms = {
            "python", "sql", "api", "azure", "gcp", "aws", "docker",
            "kubernetes", "terraform", "fastapi", "etl", "pipeline",
            "automation", "cloud", "data", "analytics", "machine",
            "learning", "integration", "microservices", "devops",
        }
        tech_overlap = overlap & tech_terms
        role.relevance_score = len(overlap) + len(tech_overlap) * 2

    sorted_roles = sorted(roles, key=lambda r: r.relevance_score, reverse=True)
    selected = sorted_roles[:max_roles]

    logger.info(
        "Role relevance: selected %d of %d roles. Top: %s (%.0f), Bottom: %s (%.0f)",
        len(selected), len(roles),
        selected[0].company if selected else "N/A",
        selected[0].relevance_score if selected else 0,
        selected[-1].company if selected else "N/A",
        selected[-1].relevance_score if selected else 0,
    )
    return selected


# ── Section Generators ───────────────────────────────────────────────────


def build_static_header(track: ParsedTrack) -> str:
    """Build the static header section — no AI needed."""
    c = track.contact
    lines = [
        c.name.upper() if c.name else "CANDIDATE NAME",
        "",
    ]
    contact_parts = []
    if c.email:
        contact_parts.append(f"Email: {c.email}")
    if c.phone:
        contact_parts.append(f"Phone: {c.phone}")
    if c.location:
        contact_parts.append(f"Location: {c.location}")
    if c.linkedin:
        contact_parts.append(f"LinkedIn: {c.linkedin}")
    if c.github:
        contact_parts.append(f"GitHub: {c.github}")
    lines.extend(contact_parts)
    return "\n".join(lines)


def build_static_education(track: ParsedTrack) -> str:
    """Build the education section — no AI needed."""
    if not track.education:
        return ""
    lines = ["EDUCATION", ""]
    for edu in track.education:
        lines.append(edu.degree)
        parts = [p for p in [edu.school, edu.location, edu.date] if p]
        if parts:
            lines.append(" | ".join(parts))
    return "\n".join(lines)


def build_summary_prompt(
    track: ParsedTrack,
    job_title: str,
    company: str,
    job_description: str,
    relevant_roles: Optional[List[WorkRole]] = None,
) -> Tuple[str, str]:
    """Build prompt for the PROFESSIONAL SUMMARY section."""
    tier1_str = ", ".join(track.skills.tier1[:20]) if track.skills.tier1 else "general technical skills"
    not_found_str = ", ".join(track.skills.not_found) if track.skills.not_found else "none"

    # Build grounding context from actual work history
    work_history_str = ""
    roles_for_context = relevant_roles or track.roles[:4]
    if roles_for_context:
        history_lines = []
        for role in roles_for_context[:4]:
            history_lines.append(f"  {role.title} at {role.company} ({role.dates})")
            for b in role.bullets[:3]:
                history_lines.append(f"    - {b}")
        work_history_str = "\n".join(history_lines)

    system = (
        f"You are writing ONLY the Professional Summary section of {track.contact.name}'s resume.\n\n"
        f"REAL SKILLS (Tier 1 — production): {tier1_str}\n"
        f"SKILLS THE CANDIDATE DOES NOT HAVE: {not_found_str}\n\n"
        f"CANDIDATE'S ACTUAL WORK HISTORY (use ONLY these facts):\n{work_history_str}\n\n"
        "RULES:\n"
        "1. Write exactly 3-4 sentences.\n"
        "2. Mention only skills from the REAL SKILLS list.\n"
        "3. NEVER mention skills from the DOES NOT HAVE list.\n"
        "4. Every claim MUST trace back to the ACTUAL WORK HISTORY above. "
        "Do not invent projects, outcomes, metrics, or technologies.\n"
        "5. Frame experience honestly — do not inflate. Use the candidate's actual years of experience (10+ years).\n"
        "6. Output plain text only. No markdown.\n"
        "7. Do NOT use phrases like 'microservices architecture' unless the candidate has built microservices in production. "
        f"The candidate built 2 FastAPI endpoints in a staging environment — that is NOT microservices expertise.\n"
        "8. You may mirror JD language for keywords that genuinely match the candidate's skills, "
        "but never fabricate experience to fill JD requirements.\n"
    )
    user = (
        f"Write a 3-4 sentence professional summary for {track.contact.name} "
        f"applying to: {job_title} at {company}.\n\n"
        f"Key job requirements from description:\n{job_description[:1500]}\n\n"
        "Be specific about what the candidate actually does well. Be honest about scope. "
        "Ground every statement in the ACTUAL WORK HISTORY provided."
    )
    return system, user


def build_skills_prompt(
    track: ParsedTrack,
    job_description: str,
) -> Tuple[str, str]:
    """Build prompt for the TECHNICAL SKILLS section."""
    tier1_str = "\n".join(f"  - {s}" for s in track.skills.tier1)
    tier2_str = "\n".join(f"  - {s}" for s in track.skills.tier2)
    not_found_str = "\n".join(f"  - {s}" for s in track.skills.not_found)

    system = (
        f"You are organizing the Technical Skills section of {track.contact.name}'s resume.\n\n"
        "PRODUCTION SKILLS (Tier 1 — can discuss in depth):\n"
        f"{tier1_str}\n\n"
        "PERSONAL/STAGING SKILLS (Tier 2 — can explain but limited production use):\n"
        f"{tier2_str}\n\n"
        "SKILLS THE CANDIDATE DOES NOT HAVE:\n"
        f"{not_found_str}\n\n"
        "RULES:\n"
        "1. Organize skills into 3-5 categories relevant to the target job.\n"
        "2. Include ONLY skills from Tier 1 and Tier 2 lists above.\n"
        "3. NEVER include skills from the DOES NOT HAVE list.\n"
        "4. Format: Category Name: skill1, skill2, skill3\n"
        "5. Put Tier 1 skills first in each category.\n"
        "6. Output plain text only. No markdown, no bullets.\n"
    )
    user = (
        f"Organize {track.contact.name}'s technical skills for this job:\n\n"
        f"JOB DESCRIPTION (first 1000 chars):\n{job_description[:1000]}\n\n"
        "Select and categorize the most relevant skills. Omit irrelevant ones."
    )
    return system, user


def build_role_prompt(
    role: WorkRole,
    track: ParsedTrack,
    job_description: str,
) -> Tuple[str, str]:
    """Build prompt for a single WORK EXPERIENCE role."""
    bullets_str = "\n".join(f"  - {b}" for b in role.bullets)
    not_found_str = ", ".join(track.skills.not_found) if track.skills.not_found else "none"

    system = (
        f"You are selecting and lightly tailoring work experience bullets for ONE role on {track.contact.name}'s resume.\n\n"
        f"ROLE: {role.title} at {role.company}\n"
        f"DATES: {role.dates}\n"
        f"LOCATION: {role.location}\n\n"
        f"ORIGINAL BULLETS (these are the ONLY facts you can use):\n{bullets_str}\n\n"
        f"TECH STACK USED AT THIS ROLE: {role.stack}\n\n"
        f"SKILLS THE CANDIDATE DOES NOT HAVE: {not_found_str}\n\n"
        "RULES:\n"
        "1. SELECT 3-5 of the most relevant bullets from the ORIGINAL BULLETS list above.\n"
        "2. You may apply keyword mirroring — substituting JD language where it authentically matches "
        "the existing bullet's content. The underlying FACT must remain identical: same numbers, "
        "same companies, same outcomes, same scope.\n"
        "3. You may add a 'SO WHAT' clause (who benefited, business outcome) ONLY if inferable "
        "from the role context (company, title, dates). Never invent impact.\n"
        "4. Every bullet in your output MUST correspond to a specific ORIGINAL BULLET above. "
        "If you cannot trace it back, do not include it.\n"
        "5. Do NOT invent new metrics, achievements, or projects not in the original bullets.\n"
        "6. Do NOT add technologies not in the TECH STACK for this role.\n"
        "7. Do NOT claim skills from the DOES NOT HAVE list.\n"
        "8. Format each bullet starting with a dash (-). No sub-bullets.\n"
        "9. Output ONLY the bullets. No headers, no company name, no dates.\n"
        "10. If a bullet cannot be authentically connected to the target job, OMIT it — "
        "do not stretch or fabricate connections.\n"
    )
    user = (
        f"Select the most relevant bullets for this role based on:\n\n"
        f"TARGET JOB:\n{job_description[:1000]}\n\n"
        "Choose bullets that naturally align with the job requirements. "
        "Apply keyword mirroring where authentic. Keep all facts identical to originals."
    )
    return system, user


def build_growth_areas_prompt(
    track: ParsedTrack,
    job_title: str,
    company: str,
    job_description: str,
) -> Tuple[str, str]:
    """Build prompt for the GROWTH AREAS section."""
    not_found_str = ", ".join(track.skills.not_found) if track.skills.not_found else "none"

    system = (
        f"You are writing the Growth Areas section of {track.contact.name}'s resume.\n"
        "This section honestly lists technologies the job requires that the candidate needs to learn.\n\n"
        f"SKILLS THE CANDIDATE DOES NOT HAVE: {not_found_str}\n\n"
        "RULES:\n"
        "1. Write 1-3 sentences.\n"
        "2. Only list gaps that the TARGET JOB actually requires.\n"
        "3. Frame positively — mention transferable skills and eagerness to learn.\n"
        "4. Output plain text only.\n"
    )
    user = (
        f"Write a brief Growth Areas section for {track.contact.name} "
        f"applying to {job_title} at {company}.\n\n"
        f"Job requirements:\n{job_description[:800]}\n\n"
        "Which skills from the DOES NOT HAVE list does this job actually require?"
    )
    return system, user


def build_cover_letter_section_prompts(
    track: ParsedTrack,
    job_title: str,
    company: str,
    location: str,
    job_description: str,
    generated_resume: GeneratedResume,
    matched_skills: List[str],
) -> List[Tuple[str, str, str]]:
    """Build prompts for each cover letter paragraph.

    Returns list of (section_name, system_prompt, user_prompt) tuples.
    """
    not_found_str = ", ".join(track.skills.not_found) if track.skills.not_found else "none"

    # Extract metrics from resume to avoid repeating
    resume_metrics = set(re.findall(
        r"\$[\d,.]+[MmBbKk]?|\d+(?:\.\d+)?%|\d+\+?\s*(?:years?|hrs?|hours?)",
        generated_resume.full_text,
        re.IGNORECASE,
    ))
    metrics_str = ", ".join(sorted(resume_metrics)[:15]) if resume_metrics else "none"

    base_system = (
        f"You are writing ONE paragraph of a cover letter for {track.contact.name}.\n"
        f"Applying to: {job_title} at {company}"
        + (f" ({location})" if location else "") + "\n\n"
        f"SKILLS THE CANDIDATE DOES NOT HAVE: {not_found_str}\n"
        f"METRICS ALREADY USED IN RESUME (do NOT repeat these): {metrics_str}\n\n"
        "GLOBAL RULES:\n"
        "- Write EXACTLY one paragraph, 3-5 sentences.\n"
        "- Output plain text only. No markdown.\n"
        "- Do NOT repeat metrics or exact phrases from the resume.\n"
        "- Do NOT claim skills from the DOES NOT HAVE list.\n"
        f"- Reference ONLY real companies from the candidate's background: {CANDIDATE_EMPLOYERS_STR}.\n"
    )

    sections = [
        (
            "opening",
            base_system + (
                "PARAGRAPH TYPE: OPENING\n"
                "- EXACTLY 2-3 sentences. No more.\n"
                "- Reference the specific role and company.\n"
                "- Connect the candidate's career trajectory to this opportunity.\n"
                "- Express genuine interest. Do NOT use generic phrases like 'I am excited to apply'.\n"
                "- Do NOT include any metrics or numbers.\n"
            ),
            f"Write the opening paragraph. Job description:\n{job_description[:800]}"
        ),
        (
            "experience",
            base_system + (
                "PARAGRAPH TYPE: EXPERIENCE BULLETS (hybrid format)\n"
                "- Write 2-3 bullet points, each 2-3 sentences.\n"
                "- Each bullet EXPANDS one resume achievement into a mini-STAR narrative.\n"
                "- Start each bullet with a bold key phrase (use **bold** markdown).\n"
                "- Each bullet must add context the resume cannot fit:\n"
                "  (a) the organizational PROBLEM that existed before,\n"
                "  (b) cross-functional collaboration required,\n"
                "  (c) downstream business outcome BEYOND the technical metric.\n"
                "- Reference actual companies and real projects.\n"
                "- Use DIFFERENT metrics/angles than the resume uses.\n"
                "- Format: bullet points with bold openings, not flowing prose.\n"
            ),
            (
                f"Write 2-3 experience bullets with bold key phrases.\n"
                f"Matched skills: {', '.join(matched_skills)}\n"
                f"Job description:\n{job_description[:800]}"
            ),
        ),
        (
            "fit",
            base_system + (
                "PARAGRAPH TYPE: HONEST FIT\n"
                "- Acknowledge what aligns well AND where there are gaps.\n"
                "- Be specific about what you'd need to learn.\n"
                "- Show self-awareness and eagerness to grow.\n"
                "- Do NOT minimize gaps or claim you can 'quickly learn anything'.\n"
                "- Reference specific transferable skills that bridge the gaps.\n"
            ),
            (
                f"Write the honest fit paragraph.\n"
                f"Skills gaps: {not_found_str}\n"
                f"Job description:\n{job_description[:600]}"
            ),
        ),
        (
            "closing",
            base_system + (
                "PARAGRAPH TYPE: CLOSING\n"
                "- Express genuine interest in the company's mission or product.\n"
                "- Thank them for considering the application.\n"
                "- Keep it brief — 2-3 sentences max.\n"
                "- Do NOT repeat anything from previous paragraphs.\n"
            ),
            f"Write the closing paragraph for an application to {company}."
        ),
    ]
    return sections


# ── Section Validators ───────────────────────────────────────────────────


def validate_no_forbidden_skills(
    text: str,
    not_found: List[str],
) -> List[str]:
    """Check that NOT FOUND skills aren't claimed as expertise."""
    issues = []
    text_lower = text.lower()

    claim_patterns = [
        "experience with {s}", "expertise in {s}", "proficient in {s}",
        "skilled in {s}", "worked with {s}", "built with {s}",
        "leveraged {s}", "utilized {s}", "using {s}",
    ]
    growth_context = [
        "growth area", "to develop", "gap", "learning",
        "eager to learn", "would need to", "don't have",
        "do not have", "no experience", "not found", "need to learn",
    ]

    for skill in not_found:
        if skill not in text_lower:
            continue
        # Find surrounding context
        idx = text_lower.find(skill)
        ctx_start = max(0, idx - 80)
        ctx_end = min(len(text_lower), idx + len(skill) + 80)
        context = text_lower[ctx_start:ctx_end]

        # OK if in growth/gap context
        if any(gc in context for gc in growth_context):
            continue

        # Check for claim patterns
        is_claimed = any(
            cp.format(s=skill) in context for cp in claim_patterns
        )
        if is_claimed:
            issues.append(f"Claimed NOT FOUND skill: '{skill}'")

    return issues


def validate_metrics_grounded(
    output: str,
    source_bullets: List[str],
) -> List[str]:
    """Check that metrics in output exist in source bullets."""
    issues = []
    source_text = " ".join(source_bullets).lower()

    # Extract dollar amounts and percentages from output
    output_metrics = re.findall(
        r"\$[\d,.]+[MmBbKk]?\+?|\d+(?:\.\d+)?%|\d+,\d{3}",
        output,
    )

    for metric in output_metrics:
        # Normalize: remove $ and commas for comparison
        normalized = metric.replace(",", "").replace("$", "").lower()
        if normalized not in source_text.replace(",", "").replace("$", ""):
            issues.append(f"Metric '{metric}' not found in source bullets")

    return issues


def validate_bullets_grounded(
    output: str,
    source_bullets: List[str],
    min_overlap: float = 0.35,
) -> List[str]:
    """Check that generated bullets are grounded in source material.

    Each output bullet must share at least min_overlap of its significant
    words (4+ chars) with at least one source bullet. Catches completely
    fabricated bullets while allowing legitimate keyword mirroring.
    """
    issues = []

    def _significant_words(text: str) -> set:
        """Extract words with 4+ chars, lowered."""
        return {w.lower().strip(".,;:!?()\"'") for w in text.split() if len(w) >= 4}

    # Split output into individual bullets
    output_bullets = [
        line.strip().lstrip("-•").strip()
        for line in output.strip().split("\n")
        if line.strip() and (line.strip().startswith("-") or line.strip().startswith("•"))
    ]

    source_word_sets = [_significant_words(b) for b in source_bullets]

    for ob in output_bullets:
        ob_words = _significant_words(ob)
        if not ob_words:
            continue

        # Find best-matching source bullet
        best_overlap = 0.0
        for sw_set in source_word_sets:
            if not sw_set:
                continue
            shared = ob_words & sw_set
            overlap = len(shared) / len(ob_words) if ob_words else 0
            best_overlap = max(best_overlap, overlap)

        if best_overlap < min_overlap:
            preview = ob[:80] + ("..." if len(ob) > 80 else "")
            issues.append(
                f"Potentially fabricated bullet (only {best_overlap:.0%} overlap with source): '{preview}'"
            )

    return issues


def validate_no_resume_repetition(
    cover_letter_text: str,
    resume_text: str,
) -> List[str]:
    """Check for repeated metrics and long phrases between resume and cover letter."""
    issues = []

    # Check shared metrics
    metric_pattern = r"\$[\d,.]+[MmBbKk]?\+?|\d+(?:\.\d+)?%"
    resume_metrics = set(re.findall(metric_pattern, resume_text))
    cl_metrics = set(re.findall(metric_pattern, cover_letter_text))
    shared = resume_metrics & cl_metrics

    for m in sorted(shared):
        issues.append(f"Repeated metric: '{m}'")

    # Check long phrase overlap (6+ consecutive words)
    resume_words = resume_text.lower().split()
    cl_words = cover_letter_text.lower().split()
    n = 6
    resume_ngrams = set()
    for i in range(len(resume_words) - n + 1):
        resume_ngrams.add(" ".join(resume_words[i:i + n]))

    for i in range(len(cl_words) - n + 1):
        ngram = " ".join(cl_words[i:i + n])
        if ngram in resume_ngrams:
            issues.append(f"Repeated phrase: '...{ngram}...'")

    return issues


# ── Sectional Pipeline ───────────────────────────────────────────────────


ProgressCallback = Callable[[str, int, str], None]  # (stage, percent, message)


class SectionalPipeline:
    """Generate resume and cover letter section by section.

    Each section gets its own focused LLM call with section-specific
    validation. Static parts (header, education) are inserted without AI.
    """

    def __init__(
        self,
        llm_caller: Callable[[str, str], Optional[str]],
        progress_cb: Optional[ProgressCallback] = None,
    ):
        """
        Args:
            llm_caller: Function that takes (system_prompt, user_prompt)
                        and returns generated text. This is the AIGenerator._call_llm method.
            progress_cb: Optional callback for progress updates.
        """
        self._raw_llm_caller = llm_caller
        self._progress = progress_cb or (lambda *a: None)
        self._parser = TrackDocParser()

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Safely call the LLM, catching connection errors."""
        try:
            return self._raw_llm_caller(system_prompt, user_prompt)
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            return None

    def generate_resume(
        self,
        track_text: str,
        job: dict,
        resume_track: str = "engineering",
    ) -> GeneratedResume:
        """Generate a tailored resume section by section."""
        title = job.get("title", "the role")
        company = job.get("company", "the company")
        description = job.get("description", "")

        # Step 1: Parse track document
        self._progress("parse", 5, "Parsing track document...")
        track = self._parser.parse(track_text)

        # Step 2: Score and select relevant roles
        self._progress("roles", 10, "Selecting relevant experience...")
        relevant_roles = score_roles_for_job(track.roles, description, max_roles=4)

        result = GeneratedResume()

        # Step 3: Static header (no AI)
        self._progress("header", 15, "Building header...")
        result.header = build_static_header(track)

        # Step 4: Professional summary (AI)
        self._progress("summary", 20, "Generating professional summary...")
        sys_p, usr_p = build_summary_prompt(track, title, company, description, relevant_roles)
        summary = self._call_llm(sys_p, usr_p)
        if summary:
            # Validate
            issues = validate_no_forbidden_skills(summary, track.skills.not_found)
            if issues:
                logger.warning("Summary validation failed: %s. Retrying with corrections...", issues)
                self._progress("summary_retry", 25, "Summary had issues — retrying...")
                corrective_usr_p = (
                    usr_p + "\n\nPREVIOUS ATTEMPT FAILED VALIDATION:\n"
                    + "\n".join(f"- {issue}" for issue in issues) + "\n"
                    "Fix these specific issues. Do NOT use any skill flagged above."
                )
                summary = self._call_llm(sys_p, corrective_usr_p)
            result.summary = summary.strip() if summary else track.summary
        else:
            result.summary = track.summary  # fallback to original

        # Step 5: Technical skills (AI)
        self._progress("skills", 30, "Organizing technical skills...")
        sys_p, usr_p = build_skills_prompt(track, description)
        skills = self._call_llm(sys_p, usr_p)
        if skills:
            issues = validate_no_forbidden_skills(skills, track.skills.not_found)
            if issues:
                logger.warning("Skills validation failed: %s. Retrying with corrections...", issues)
                self._progress("skills_retry", 35, "Skills had issues — retrying...")
                corrective_usr_p = (
                    usr_p + "\n\nPREVIOUS ATTEMPT FAILED VALIDATION:\n"
                    + "\n".join(f"- {issue}" for issue in issues) + "\n"
                    "Fix these specific issues. Do NOT include any skill flagged above."
                )
                skills = self._call_llm(sys_p, corrective_usr_p)
            result.skills = skills.strip() if skills else "Production: " + ", ".join(track.skills.tier1[:15])
        else:
            # Fallback: just list tier 1 skills
            result.skills = "Production: " + ", ".join(track.skills.tier1[:15])

        # Step 6: Work experience (AI — one call per role)
        experience_parts = []
        total_roles = len(relevant_roles)
        for i, role in enumerate(relevant_roles):
            pct = 40 + int((i / max(total_roles, 1)) * 30)
            self._progress(
                f"role_{i}",
                pct,
                f"Tailoring experience: {role.company.split('→')[-1].strip()}...",
            )

            sys_p, usr_p = build_role_prompt(role, track, description)
            bullets = self._call_llm(sys_p, usr_p)

            use_original = False
            if bullets:
                # Validate metrics are grounded
                metric_issues = validate_metrics_grounded(bullets, role.bullets)
                if metric_issues:
                    logger.warning(
                        "Role %s metrics issues: %s — falling back to originals",
                        role.company, metric_issues,
                    )
                    use_original = True

                # Validate bullets are grounded in source
                if not use_original:
                    grounding_issues = validate_bullets_grounded(bullets, role.bullets)
                    if grounding_issues:
                        logger.warning(
                            "Role %s grounding issues: %s — retrying...",
                            role.company, grounding_issues,
                        )
                        corrective_usr_p = (
                            usr_p + "\n\nPREVIOUS ATTEMPT FAILED VALIDATION — bullets were fabricated:\n"
                            + "\n".join(f"- {issue}" for issue in grounding_issues[:3]) + "\n"
                            "Every bullet MUST correspond to a specific ORIGINAL BULLET. "
                            "Select and mirror keywords only. Do NOT invent new achievements."
                        )
                        bullets = self._call_llm(sys_p, corrective_usr_p)
                        if bullets:
                            retry_issues = validate_bullets_grounded(bullets, role.bullets)
                            if retry_issues:
                                logger.warning(
                                    "Role %s still fabricated after retry — using originals",
                                    role.company,
                                )
                                use_original = True
                        else:
                            use_original = True

                # Validate no forbidden skills
                if not use_original and bullets:
                    skill_issues = validate_no_forbidden_skills(bullets, track.skills.not_found)
                    if skill_issues:
                        logger.warning(
                            "Role %s skill issues: %s — retrying...", role.company, skill_issues
                        )
                        corrective_usr_p = (
                            usr_p + "\n\nPREVIOUS ATTEMPT FAILED VALIDATION:\n"
                            + "\n".join(f"- {issue}" for issue in skill_issues) + "\n"
                            "Fix these specific issues. Do NOT use any skill flagged above."
                        )
                        bullets = self._call_llm(sys_p, corrective_usr_p)
                        if not bullets:
                            use_original = True
            else:
                use_original = True

            if use_original:
                # Fallback: use original bullets (safe, authenticated)
                final_bullets = "\n".join(f"- {b}" for b in role.bullets[:5])
            else:
                final_bullets = bullets.strip()

            role_block = (
                f"{role.title}\n"
                f"{role.company} | {role.dates}\n"
                f"{role.location}\n\n"
                f"{final_bullets}"
            )
            experience_parts.append(role_block)

        result.experience = "\n\n".join(experience_parts)

        # Step 7: Growth areas (AI)
        self._progress("growth", 75, "Identifying growth areas...")
        sys_p, usr_p = build_growth_areas_prompt(track, title, company, description)
        growth = self._call_llm(sys_p, usr_p)
        result.growth_areas = growth.strip() if growth else ""

        # Step 8: Education (static)
        education = build_static_education(track)

        # Step 9: Assemble
        self._progress("assemble", 80, "Assembling resume...")
        sections = [
            result.header,
            "",
            "PROFESSIONAL SUMMARY",
            "",
            result.summary,
            "",
            "TECHNICAL SKILLS",
            "",
            result.skills,
            "",
            "WORK EXPERIENCE",
            "",
            result.experience,
            "",
            education,
        ]
        if result.growth_areas:
            sections.extend(["", "GROWTH AREAS", "", result.growth_areas])

        result.full_text = "\n".join(sections)

        # Extract metrics used for cover letter dedup
        result.metrics_used = re.findall(
            r"\$[\d,.]+[MmBbKk]?\+?|\d+(?:\.\d+)?%",
            result.full_text,
        )

        logger.info(
            "Sectional resume generated: %d chars, %d roles, %d metrics",
            len(result.full_text),
            len(experience_parts),
            len(result.metrics_used),
        )
        return result

    def generate_cover_letter(
        self,
        track_text: str,
        job: dict,
        generated_resume: GeneratedResume,
        matched_skills: List[str],
    ) -> GeneratedCoverLetter:
        """Generate a cover letter paragraph by paragraph, validated against resume."""
        title = job.get("title", "the role")
        company = job.get("company", "the company")
        location = job.get("location", "")
        description = job.get("description", "")

        track = self._parser.parse(track_text)
        result = GeneratedCoverLetter()

        section_prompts = build_cover_letter_section_prompts(
            track, title, company, location, description,
            generated_resume, matched_skills,
        )

        section_names = ["opening", "experience", "fit", "closing"]
        section_pcts = [82, 87, 92, 95]
        section_labels = [
            "Writing cover letter opening...",
            "Writing relevant experience...",
            "Writing honest fit assessment...",
            "Writing closing...",
        ]

        paragraphs = []
        for i, (name, sys_p, usr_p) in enumerate(section_prompts):
            self._progress(f"cl_{name}", section_pcts[i], section_labels[i])
            paragraph = self._call_llm(sys_p, usr_p)

            if paragraph:
                # Clean up — remove any prefix labels the model might add
                cleaned = re.sub(
                    r"^(?:Opening|Paragraph \d|P\d|Relevant Experience|Honest Fit|Closing)[\s:]*",
                    "", paragraph.strip(), flags=re.IGNORECASE,
                )
                paragraphs.append(cleaned.strip())
                setattr(result, name, cleaned.strip())
            else:
                paragraphs.append("")

        # Assemble with salutation and sign-off
        self._progress("cl_assemble", 97, "Assembling cover letter...")
        body = "\n\n".join(p for p in paragraphs if p)

        salutation = f"Dear {company} Hiring Team," if company and company != "the company" else "Dear Hiring Team,"
        result.full_text = (
            f"{salutation}\n\n"
            f"{body}\n\n"
            f"Sincerely,\n\n"
            f"Grygorii T.\n\n"
            f"[DRAFT FLAG: Human review required]"
        )

        # Validate against resume for repetition
        repetition_issues = validate_no_resume_repetition(
            result.full_text, generated_resume.full_text
        )
        if repetition_issues:
            logger.warning(
                "Cover letter has %d repetition issues with resume: %s",
                len(repetition_issues),
                "; ".join(repetition_issues[:5]),
            )

        logger.info(
            "Sectional cover letter generated: %d chars, %d paragraphs",
            len(result.full_text),
            len(paragraphs),
        )
        return result
