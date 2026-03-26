"""
AI-powered resume and cover letter generator — multi-provider support.

Supports Ollama (local) and Claude (Anthropic API) for generating tailored
application materials.  Falls back to the template-based generator when the
AI provider is unavailable or returns an error.
"""

from __future__ import annotations

import enum
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

from .generator import generate_application_package  # template-based fallback

# Employer list read from env — keeps employment history out of source code.
# Set CANDIDATE_EMPLOYERS in .env as a comma-separated list.
_raw_employers = os.getenv("CANDIDATE_EMPLOYERS", "your previous employers")
CANDIDATE_EMPLOYERS = [e.strip() for e in _raw_employers.split(",") if e.strip()]
CANDIDATE_EMPLOYERS_STR = ", ".join(CANDIDATE_EMPLOYERS)

CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "")
CANDIDATE_NAME_SLUG = CANDIDATE_NAME.lower().replace(" ", "_").replace(".", "") if CANDIDATE_NAME else ""

# Lazy imports for constrained generation pipeline (avoid circular imports)
# from src.generation.context_builder import GenerationContext, build_generation_context
# from src.generation.tier3_blocklist import TIER_3_NEVER_CLAIM
# from src.generation.output_validator import validate_generated_output

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/v1/chat/completions"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"

REQUEST_TIMEOUT_SECONDS = 180  # Ollama large prompts and Claude API both need time


# ── Enums / Data Classes ──────────────────────────────────────────────────


class AIProvider(enum.Enum):
    """Supported AI provider backends."""

    OLLAMA = "ollama"
    CLAUDE = "claude"


@dataclass(frozen=True)
class AIModelConfig:
    """Metadata for a single AI model."""

    provider: AIProvider
    model_name: str
    display_name: str
    description: str
    speed_rating: str  # "fast", "medium", or "slow"


# ── Available Models ───────────────────────────────────────────────────────

AVAILABLE_MODELS: List[AIModelConfig] = [
    # Ollama — local models
    AIModelConfig(
        provider=AIProvider.OLLAMA,
        model_name="gemma3:4b",
        display_name="Gemma 3 4B (Local)",
        description="Google's compact model — good balance of speed and quality",
        speed_rating="fast",
    ),
    AIModelConfig(
        provider=AIProvider.OLLAMA,
        model_name="qwen3:4b",
        display_name="Qwen 3 4B (Local)",
        description="Alibaba's lightweight model — fast general-purpose generation",
        speed_rating="fast",
    ),
    AIModelConfig(
        provider=AIProvider.OLLAMA,
        model_name="qwen2.5-coder:7b",
        display_name="Qwen 2.5 Coder 7B (Local)",
        description="Code-optimised model — strong for technical resumes",
        speed_rating="fast",
    ),
    AIModelConfig(
        provider=AIProvider.OLLAMA,
        model_name="llama3.1:8b",
        display_name="Llama 3.1 8B (Local)",
        description="Meta's general-purpose model — reliable all-rounder",
        speed_rating="fast",
    ),
    AIModelConfig(
        provider=AIProvider.OLLAMA,
        model_name="deepseek-r1:8b",
        display_name="DeepSeek R1 8B (Local)",
        description="Reasoning-focused model — good for nuanced tailoring",
        speed_rating="medium",
    ),
    AIModelConfig(
        provider=AIProvider.OLLAMA,
        model_name="qwen2.5-coder:14b",
        display_name="Qwen 2.5 Coder 14B (Local)",
        description="Larger code model — higher quality, slower generation",
        speed_rating="medium",
    ),
    AIModelConfig(
        provider=AIProvider.OLLAMA,
        model_name="qwen2.5-coder:32b",
        display_name="Qwen 2.5 Coder 32B (Local)",
        description="Full-size code model — best local quality for technical roles",
        speed_rating="slow",
    ),
    AIModelConfig(
        provider=AIProvider.OLLAMA,
        model_name="deepseek-r1:32b",
        display_name="DeepSeek R1 32B (Local)",
        description="Large reasoning model — highest local quality, slowest",
        speed_rating="slow",
    ),
    # Claude — cloud models
    AIModelConfig(
        provider=AIProvider.CLAUDE,
        model_name="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku (Cloud)",
        description="Fast cloud model — great speed-to-quality ratio",
        speed_rating="fast",
    ),
    AIModelConfig(
        provider=AIProvider.CLAUDE,
        model_name="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4 (Cloud)",
        description="Premium cloud model — best overall quality",
        speed_rating="medium",
    ),
]

_MODEL_LOOKUP: Dict[tuple, AIModelConfig] = {
    (m.provider.value, m.model_name): m for m in AVAILABLE_MODELS
}


# ── Discovery ─────────────────────────────────────────────────────────────


def get_available_models() -> List[AIModelConfig]:
    """Return models that are actually usable right now.

    * For Ollama models, queries the local server to see which are installed.
    * For Claude models, checks whether ``ANTHROPIC_API_KEY`` is set.
    """
    available: List[AIModelConfig] = []

    # --- Ollama -----------------------------------------------------------
    installed_ollama: set[str] = set()
    try:
        resp = requests.get(OLLAMA_TAGS_URL, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        for model_info in data.get("models", []):
            name = model_info.get("name", "")
            installed_ollama.add(name)
            # Also add without ":latest" tag so "llama3.1:8b" matches
            # "llama3.1:8b" even if the server reports "llama3.1:8b".
            if ":" in name:
                installed_ollama.add(name)
            else:
                installed_ollama.add(f"{name}:latest")
        logger.debug("Ollama models found: %s", installed_ollama)
    except requests.RequestException:
        logger.info("Ollama server not reachable — skipping local models")

    for model_cfg in AVAILABLE_MODELS:
        if model_cfg.provider == AIProvider.OLLAMA:
            if model_cfg.model_name in installed_ollama:
                available.append(model_cfg)
        elif model_cfg.provider == AIProvider.CLAUDE:
            if os.environ.get("ANTHROPIC_API_KEY"):
                available.append(model_cfg)

    logger.info(
        "Available AI models: %d of %d configured",
        len(available),
        len(AVAILABLE_MODELS),
    )
    return available


def get_model_display_name(provider: str, model: str) -> str:
    """Return a human-friendly name for display in the dashboard.

    Falls back to ``"<model> (<provider>)"`` if the combination is unknown.
    """
    cfg = _MODEL_LOOKUP.get((provider, model))
    if cfg:
        return cfg.display_name
    return f"{model} ({provider})"


# ── Prompt Templates ───────────────────────────────────────────────────────

def _extract_candidate_name(resume_text: str) -> str:
    """Extract the candidate's name from resume text.

    Handles multiple formats:
    - Markdown headers: # GRYGORII T. — Track Reference
    - Plain text: GRYGORII T. (first line, all caps)
    - Known name patterns
    """
    # Check for known name pattern first (most reliable)
    text_lower = resume_text.lower()
    if CANDIDATE_NAME_SLUG and CANDIDATE_NAME_SLUG in text_lower:
        return CANDIDATE_NAME

    # Try to extract from markdown header: # NAME — description
    for line in resume_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Strip markdown header markers
        cleaned = line.lstrip("#").strip()
        # Check for em-dash separator (common in track documents)
        if "—" in cleaned:
            name_part = cleaned.split("—")[0].strip()
            if name_part and len(name_part) < 60:
                return name_part
        # Check for plain name line (all caps, short)
        if line.isupper() and len(line) < 60 and not line.startswith("#"):
            return line
        # First non-empty short line without markdown
        if not line.startswith("#") and not line.startswith("*") and len(line) < 60:
            return line

    return "the candidate"


def _extract_not_found_skills(resume_text: str) -> List[str]:
    """Extract skills/technologies explicitly marked as NOT FOUND or gaps.

    Parses markers like:
    - ``| AWS | ❌ NOT FOUND |``
    - ``| Kubernetes | ❌ NOT FOUND |``

    Returns a deduplicated list of lowercase skill names the candidate does NOT have.
    Only returns clean technology/skill names (short, no long phrases).
    """
    not_found: set[str] = set()

    for line in resume_text.split("\n"):
        stripped = line.strip()

        # Match table rows with ❌ NOT FOUND
        if "NOT FOUND" in stripped and "|" in stripped:
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            if cells:
                skill = cells[0].strip()
                # Clean up: remove markdown, emoji
                skill = re.sub(r"[❌⚠️*`]", "", skill).strip()
                # Skip if this is just "NOT FOUND" itself or too long
                if skill.upper() == "NOT FOUND" or len(skill) > 35:
                    continue
                # Remove parenthetical context like "(BigQuery, Cloud Functions, GKE)"
                base = re.sub(r"\(.*?\)", "", skill).strip()
                # Split compound entries like "Airflow / Dagster / Prefect"
                if "/" in base:
                    for sub in base.split("/"):
                        sub = sub.strip()
                        if sub and 2 < len(sub) < 35:
                            not_found.add(sub.lower())
                elif base and 2 < len(base) < 35:
                    not_found.add(base.lower())
                # Also extract items from parentheses
                paren_match = re.findall(r"\(([^)]+)\)", skill)
                for paren in paren_match:
                    for item in paren.split(","):
                        item = item.strip()
                        if item and 2 < len(item) < 35:
                            not_found.add(item.lower())

    return sorted(not_found)


def _condense_track_doc(resume_text: str) -> str:
    """Strip meta-information from a track reference document.

    The track docs contain authentication notes, tier tables, blocked items,
    interview survivability tips, and other metadata that confuses LLMs.
    This function extracts only the resume-ready content:
    - Contact info, education, professional summary
    - Employment history with achievements
    - A condensed skills list (Tier 1 and 2 only, no tables)

    Typically reduces ~27K chars to ~8-12K chars.
    """
    lines = resume_text.split("\n")
    output_lines: List[str] = []

    # Sections to SKIP entirely (meta-information, not resume content)
    SKIP_SECTION_HEADERS = {
        "authentication legend",
        "blocked",
        "demoted items",
        "interview survivability",
        "interview-critical",
        "soft skills",
        "quantified achievements",
        "authentication",
        "employment structure",
    }

    # Lines/patterns to drop individually
    SKIP_LINE_PATTERNS = [
        r"^>\s*⚠️",           # Warning callouts
        r"^\*\*Scope boundaries",
        r"^\*\*Interview evidence",
        r"^\*\*Interview framing",
        r"^\*\*Distinguishing characteristic",
        r"^Authentication:",
        r"^\*Authentication:",
        r"^Last Updated:",
        r"^Authentication Status:",
    ]
    skip_regexes = [re.compile(p, re.IGNORECASE) for p in SKIP_LINE_PATTERNS]

    in_skip_section = False
    current_section_level = 0

    for line in lines:
        stripped = line.strip()

        # Detect section headers (## or ###)
        if stripped.startswith("#"):
            header_text = stripped.lstrip("#").strip().lower()
            # Remove trailing markers like "(Engineering Track)"
            header_clean = re.sub(r"\(.*?\)", "", header_text).strip()
            # Remove em-dash suffixes
            if "—" in header_clean:
                header_clean = header_clean.split("—")[0].strip()

            level = len(stripped) - len(stripped.lstrip("#"))

            # Check if this section should be skipped
            should_skip = any(
                skip_key in header_clean
                for skip_key in SKIP_SECTION_HEADERS
            )

            if should_skip:
                in_skip_section = True
                current_section_level = level
                continue
            else:
                # New section at same or higher level ends the skip
                if in_skip_section and level <= current_section_level:
                    in_skip_section = False

        if in_skip_section:
            continue

        # Skip individual meta-lines
        if any(rx.search(stripped) for rx in skip_regexes):
            continue

        # Skip the authentication LEGEND table only (| Tier 1 | Hands-On Production | ...)
        # NOT skills data rows that happen to contain "Tier 1" as a value
        if stripped.startswith("|") and any(
            t in stripped.lower()
            for t in ["hands-on production", "research / personal", "conceptual / learning"]
        ):
            continue

        # Skip authentication-related lines
        if "authentication status" in stripped.lower():
            continue

        # Skip lines that are just table dividers
        if stripped and all(c in "-| " for c in stripped):
            continue

        # Keep everything else
        output_lines.append(line)

    condensed = "\n".join(output_lines).strip()

    # Clean up excessive blank lines
    condensed = re.sub(r"\n{4,}", "\n\n\n", condensed)

    # Remove empty table sections (header row + divider with no data rows)
    # Pattern: ### Header\n\n| Col1 | Col2 |\n\n (nothing follows)
    condensed = re.sub(
        r"### [^\n]+\n+\| [^\n]+\|\n+(?=###|\Z)",
        "",
        condensed,
    )

    logger.info(
        "Condensed track doc: %d chars → %d chars (%.0f%% reduction)",
        len(resume_text),
        len(condensed),
        (1 - len(condensed) / max(len(resume_text), 1)) * 100,
    )

    return condensed


_TRACK_GUIDANCE = {
    "engineering": (
        "Emphasise technical skills, systems you have built, architecture decisions, "
        "performance optimisations, and engineering leadership. Foreground languages, "
        "frameworks, cloud platforms, and infrastructure experience."
    ),
    "analyst": (
        "Emphasise data analysis, stakeholder management, business impact, KPI "
        "improvements, cross-functional collaboration, and data-driven decision making. "
        "Foreground SQL, dashboards, reporting, and analytical tools."
    ),
    "bsa": (
        "Emphasise requirements gathering, process improvement, system integration, "
        "user-acceptance testing, workflow mapping, and bridging business and technology "
        "teams. Foreground Agile/Scrum, JIRA, Confluence, and documentation skills."
    ),
}


def _build_resume_prompt(
    job: dict,
    resume_text: str,
    resume_track: str,
) -> str:
    """Construct the system + user prompt for resume generation.

    The master resume is condensed and placed in the SYSTEM prompt so the
    model treats it as ground truth. Skills marked NOT FOUND are listed
    explicitly so the model doesn't fabricate expertise.
    """
    title = job.get("title", "the advertised position")
    company = job.get("company", "the hiring company")
    description = job.get("description", "")

    track_guide = _TRACK_GUIDANCE.get(
        resume_track, _TRACK_GUIDANCE["engineering"]
    )

    candidate_name = _extract_candidate_name(resume_text)

    # Condense the track doc to remove meta-information
    condensed = _condense_track_doc(resume_text)

    # Extract skills the candidate explicitly does NOT have
    not_found = _extract_not_found_skills(resume_text)
    not_found_str = ", ".join(not_found) if not_found else "none listed"

    system = (
        f"You are rewriting the resume of {candidate_name} for a specific job application.\n\n"
        f"HERE IS THE CANDIDATE'S REAL RESUME — this is the ONLY source of truth:\n"
        f"{'='*60}\n"
        f"{condensed}\n"
        f"{'='*60}\n\n"
        "STRICT RULES — violating ANY of these makes the output UNUSABLE:\n"
        f"1. The candidate's name is {candidate_name}. Use EXACTLY this name.\n"
        "2. Every company, job title, date, and achievement MUST come from the resume above. "
        "   NEVER invent companies, titles, or achievements.\n"
        f"3. Real employers: {CANDIDATE_EMPLOYERS_STR}. "
        "   Use ONLY these.\n"
        "4. Reorder and rephrase bullets to match the target job, but keep all FACTS "
        "   identical — same companies, same numbers, same outcomes.\n"
        f"5. SKILLS THE CANDIDATE DOES NOT HAVE: {not_found_str}. "
        "   If the job requires any of these, list them under GROWTH AREAS at the end. "
        "   NEVER claim experience with these skills.\n"
        "6. Output plain text only. No markdown, no asterisks, no # headers.\n"
        "7. Structure: Name (ALL CAPS) → Contact → PROFESSIONAL SUMMARY → "
        "   TECHNICAL SKILLS → WORK EXPERIENCE → EDUCATION → GROWTH AREAS.\n"
        f"8. Resume track: {resume_track.upper()}. {track_guide}\n"
        "9. Keep the resume to 2 pages of content (roughly 600-900 words). "
        "   Select the 3-4 most relevant roles; summarize or omit the rest.\n"
    )

    user = (
        f"Rewrite {candidate_name}'s resume tailored for this role:\n\n"
        f"TARGET ROLE: {title} at {company}\n\n"
        f"JOB DESCRIPTION:\n{description}\n\n"
        f"Remember: use ONLY {candidate_name}'s real experience. "
        "Do NOT claim expertise in skills listed as NOT FOUND. "
        f"Start with {candidate_name.upper()} on the first line."
    )

    return system, user


def _build_cover_letter_prompt(
    job: dict,
    resume_text: str,
    matched_skills: List[str],
    key_requirements: List[str],
) -> tuple[str, str]:
    """Construct the system + user prompt for cover letter generation.

    Same strategy as resume: condensed resume in system prompt, explicit
    NOT FOUND skills to prevent fabrication.
    """
    title = job.get("title", "the advertised position")
    company = job.get("company", "the hiring company")
    location = job.get("location", "")

    skills_str = ", ".join(matched_skills) if matched_skills else "N/A"
    reqs_str = "\n".join(f"  - {r}" for r in key_requirements) if key_requirements else "N/A"

    candidate_name = _extract_candidate_name(resume_text)
    condensed = _condense_track_doc(resume_text)
    not_found = _extract_not_found_skills(resume_text)
    not_found_str = ", ".join(not_found) if not_found else "none listed"

    system = (
        f"You are writing a cover letter for {candidate_name}.\n\n"
        f"HERE IS THE CANDIDATE'S REAL RESUME — the ONLY source of truth:\n"
        f"{'='*60}\n"
        f"{condensed}\n"
        f"{'='*60}\n\n"
        "STRICT RULES:\n"
        f"1. The candidate's name is {candidate_name}. Sign off as 'Grygorii T.'.\n"
        "2. Every claim must reference REAL companies and projects from the resume above. "
        "   NEVER fabricate experience.\n"
        f"3. SKILLS THE CANDIDATE DOES NOT HAVE: {not_found_str}. "
        "   NEVER claim experience with these. If the job requires them, "
        "   acknowledge the gap honestly and express eagerness to learn.\n"
        "4. 4-paragraph structure:\n"
        "   - Opening: Reference the specific role and company. Connect career trajectory.\n"
        "   - Relevant Experience: Connect 2-3 REAL experiences to the job requirements. "
        f"     Reference actual companies ({CANDIDATE_EMPLOYERS_STR}) and real projects.\n"
        "   - Honest Fit: Where experience aligns AND where there are gaps. "
        "     Be specific about what you DO know and what you'd need to learn.\n"
        "   - Closing: Express genuine interest, professional sign-off.\n"
        "5. NO-REPETITION: Don't copy exact metrics from the resume. Discuss the same "
        "   work from a NARRATIVE angle.\n"
        "6. Start with 'Dear Hiring Team,'\n"
        "7. End with 'Sincerely,\\n\\nGrygorii T.'\n"
        "8. Output plain text only. No markdown. 4 paragraphs, 4-6 sentences each.\n"
    )

    user = (
        f"Write a cover letter for {candidate_name} applying to:\n\n"
        f"TARGET ROLE: {title} at {company}"
        + (f" ({location})" if location else "")
        + "\n\n"
        f"MATCHED SKILLS: {skills_str}\n\n"
        f"KEY REQUIREMENTS:\n{reqs_str}\n\n"
        f"SKILLS GAPS (candidate does NOT have): {not_found_str}\n\n"
        f"Use ONLY {candidate_name}'s real experience. "
        "Reference actual companies and projects. Be honest about gaps — "
        "do NOT claim expertise in skills the candidate doesn't have."
    )

    return system, user


# ── AI Generator Class ────────────────────────────────────────────────────


class AIGenerator:
    """Generate application materials using a specified AI provider and model.

    Falls back to template-based generation (``generator.py``) when the AI
    backend is unreachable or returns an error.
    """

    def __init__(self, provider: str, model: str) -> None:
        """
        Args:
            provider: ``"ollama"`` or ``"claude"``.
            model: The model identifier, e.g. ``"llama3.1:8b"`` or
                   ``"claude-sonnet-4-20250514"``.
        """
        try:
            self.provider = AIProvider(provider)
        except ValueError:
            raise ValueError(
                f"Unknown provider '{provider}'. Must be one of: "
                f"{[p.value for p in AIProvider]}"
            )
        self.model = model
        self.timeout_seconds = REQUEST_TIMEOUT_SECONDS
        self.max_tokens = 4096
        logger.info("AIGenerator initialised: provider=%s model=%s", provider, model)

    # ── Public Methods ────────────────────────────────────────────────

    def generate_sectional_package(
        self,
        job: dict,
        resume_text: str,
        resume_track: str = "engineering",
        matched_skills: Optional[List[str]] = None,
        progress_cb: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Generate resume and cover letter using the sectional pipeline.

        Each section (summary, skills, each work role, cover letter paragraphs)
        gets its own focused LLM call with per-section validation.

        Args:
            job: Job dict with title, company, description.
            resume_text: The track document text.
            resume_track: One of "engineering", "analyst", "bsa".
            matched_skills: Skills found in both resume and JD.
            progress_cb: Optional callback(stage, pct, message).

        Returns:
            {"resume_text": str, "cover_letter_text": str,
             "resume_obj": GeneratedResume, "cover_letter_obj": GeneratedCoverLetter}
        """
        from .sectional_pipeline import SectionalPipeline

        pipeline = SectionalPipeline(
            llm_caller=self._call_llm,
            progress_cb=progress_cb,
        )

        # Generate resume section by section
        resume_result = pipeline.generate_resume(
            track_text=resume_text,
            job=job,
            resume_track=resume_track,
        )

        # Generate cover letter paragraph by paragraph
        cover_result = pipeline.generate_cover_letter(
            track_text=resume_text,
            job=job,
            generated_resume=resume_result,
            matched_skills=matched_skills or [],
        )

        return {
            "resume_text": resume_result.full_text,
            "cover_letter_text": cover_result.full_text,
            "resume_obj": resume_result,
            "cover_letter_obj": cover_result,
        }

    def generate_resume(
        self,
        job: dict,
        resume_text: str,
        resume_track: str = "engineering",
    ) -> str:
        """Generate a tailored resume for the given job.

        Args:
            job: Job dict with ``title``, ``company``, ``description``, etc.
            resume_text: The user's master resume as plain text.
            resume_track: One of ``"engineering"``, ``"analyst"``, ``"bsa"``.

        Returns:
            The generated resume text.  On failure, returns template-based
            output and logs the error.
        """
        if resume_track not in _TRACK_GUIDANCE:
            logger.warning(
                "Unknown track '%s', defaulting to 'engineering'", resume_track
            )
            resume_track = "engineering"

        system_prompt, user_prompt = _build_resume_prompt(
            job, resume_text, resume_track
        )

        try:
            result = self._call_llm(system_prompt, user_prompt)
            if result:
                return result
        except Exception as exc:
            logger.error("AI resume generation failed: %s", exc)

        # Fallback — template-based
        logger.info("Falling back to template-based resume generation")
        return self._template_fallback_resume(job, resume_text)

    def generate_cover_letter(
        self,
        job: dict,
        resume_text: str,
        matched_skills: Optional[List[str]] = None,
        key_requirements: Optional[List[str]] = None,
    ) -> str:
        """Generate a tailored cover letter.

        Args:
            job: Job dict with ``title``, ``company``, ``description``, etc.
            resume_text: The user's master resume.
            matched_skills: Skills found in both resume and JD.
            key_requirements: Key requirements extracted from the JD.

        Returns:
            The generated cover letter text.  Falls back to template on error.
        """
        matched_skills = matched_skills or []
        key_requirements = key_requirements or []

        system_prompt, user_prompt = _build_cover_letter_prompt(
            job, resume_text, matched_skills, key_requirements
        )

        try:
            result = self._call_llm(system_prompt, user_prompt)
            if result:
                return result
        except Exception as exc:
            logger.error("AI cover letter generation failed: %s", exc)

        logger.info("Falling back to template-based cover letter generation")
        return self._template_fallback_cover_letter(job, resume_text)

    def constrained_generate(self, context) -> dict:
        """Generate a tailored resume package using hard achievement and tool constraints.

        The LLM may ONLY:
        - Reorder existing bullets to lead with most JD-relevant content
        - Mirror JD language/keywords onto existing authenticated bullets
        - Rewrite the professional summary to reflect the target role/company
        - Select which of the provided ACHIEVEMENT_BULLETS to include

        The LLM may NOT:
        - Add any technology not in VERIFIED_TOOLS
        - Create new bullets not present in ACHIEVEMENT_BULLETS
        - Add metrics not in the source material
        - Claim experience with any tool in BLOCKED_TOOLS

        Args:
            context: GenerationContext from context_builder.build_generation_context()

        Returns:
            dict with keys: tailored_resume, cover_letter_draft, interview_prep, key_points
        """
        # Build the achievement bullet list for the prompt
        achievement_bullets_text = ""
        for i, ach in enumerate(context.selected_achievements, 1):
            achievement_bullets_text += f"\n[ACHIEVEMENT {i}: {ach['label']}]\n"
            for bullet in ach.get("resume_bullets", []):
                achievement_bullets_text += f"  - {bullet}\n"
            if ach.get("scope_boundaries"):
                achievement_bullets_text += f"  SCOPE LIMITS: {'; '.join(ach['scope_boundaries'])}\n"

        gap_warning = ""
        if context.gap_flags:
            gap_warning = f"""
TOOL GAPS (acknowledge in cover letter if asked, do NOT fabricate in resume):
The JD mentions tools Grisha has not used hands-on: {', '.join(context.gap_flags)}
Do not include these in the resume. Do not imply experience with these tools.
"""

        system_prompt = f"""You are a resume tailoring assistant. Your task is CONSTRAINED.

CANDIDATE: Grygorii T.
TARGET ROLE: {context.job_title} at {context.company}
RESUME VERSION: {context.base_resume_version} (use base resume structure below)
ROLE CATEGORY: {context.job_category}
ALIGNMENT SCORE: {context.alignment_score:.0f}/100

{'='*55}
HARD CONSTRAINTS — VIOLATIONS ARE FABRICATION EVENTS
{'='*55}

VERIFIED TOOLS (only these may appear in the resume):
{', '.join(context.verified_tools_for_job) if context.verified_tools_for_job else 'Use tools from base resume only'}

BLOCKED TOOLS (never include, even if JD requires them):
{', '.join(context.blocked_tools_in_jd) if context.blocked_tools_in_jd else 'None detected'}

{gap_warning}

ACHIEVEMENT BULLETS (select and reorder from these only — do not invent new bullets):
{achievement_bullets_text}

JD KEYWORDS TO MIRROR (substitute into existing bullets where authentic):
{', '.join(context.jd_keywords)}

{'='*55}
BULLET REWRITING RULE (Recruiter feedback 2026-03-18)
{'='*55}
Every bullet must follow the three-layer formula:
  Layer 1 — WHAT: What was built or done
  Layer 2 — HOW MUCH: Quantified result (metric, percentage, dollar amount)
  Layer 3 — SO WHAT: Who benefited and what business outcome was enabled

Prioritize bullets that already have all three layers. When rewriting,
add Layer 3 context from the achievement's org_impact field if available.

Example:
  Bad: "Reduced processing time by 95%" (Layer 1 + 2 only)
  Good: "Reduced processing time by 95%, enabling the team to redirect
     40+ analyst-hours/week from manual reporting to strategic analysis" (all 3 layers)

{'='*55}
AI TOOLS PROMINENCE (Recruiter feedback 2026-03-18)
{'='*55}
If the base resume includes AI tools in the skills section, ensure these are
prominent and use the term "AI-augmented development" — NEVER "vibe coding".
Tools to surface when present: Claude Code, Claude Cowork, Claude API,
Copilot, Langflow.

AI tool framing rules:
- Claude Code → describe as "agentic coding" or "autonomous code generation and testing"
- Claude API → describe as "programmatic LLM integration" or "API-based AI automation"
- Claude Cowork → describe as "AI-assisted collaborative workflows"
- Use language like "augmented by", "accelerated by", "directed [tool] to"
  rather than "had AI build" or "AI-generated"
- The candidate is the ARCHITECT; AI tools are executors under their direction
- "prompt engineering" as standalone skill is outdated — use "context engineering"
  (designing the full information environment around an LLM)

{'='*55}
WHAT YOU MAY DO
{'='*55}
1. Reorder sections and bullets so most JD-relevant content appears first
2. SELECT which ACHIEVEMENT BULLETS to include (max 3-4 per role) — pick the ones
   that naturally align with the target job
3. Apply MINIMAL keyword mirroring — ONLY swap synonyms for words that mean the
   same thing. Example: "ETL pipeline" → "data pipeline" is OK (same thing).
   "Python script" → "automation script" is OK (same thing).
   You MUST NOT replace technical terms with unrelated JD buzzwords.
4. Rewrite the Professional Summary (3-5 sentences max) to target this role,
   but ONLY reference activities the candidate actually performed
5. Add Layer 3 organizational impact to bullets that only have Layers 1-2,
   but ONLY if the impact is inferable from the role context
6. Omit bullets that have no authentic connection to the target job — fewer
   honest bullets are better than stretched ones

{'='*55}
WHAT YOU MAY NOT DO — HARD RULES
{'='*55}
1. Add any technology not in VERIFIED TOOLS above
2. Create new bullets not derived from ACHIEVEMENT BULLETS above
3. Add any metric not present in the source bullet text
4. Imply production experience with BLOCKED TOOLS
5. Change job titles from the base resume. The titles are verified employment
   records. "Senior Data Engineer" MUST remain "Senior Data Engineer" — you
   cannot change it to "Systems Engineer", "Test Engineer", or any other title.
6. Add education credentials not in base resume
7. Use the phrase "vibe coding" anywhere
8. CHANGE THE CORE ACTIVITY of a bullet. If the original says "built ETL pipeline",
   the output must still say "built ETL pipeline" (or a true synonym like
   "built data pipeline"). You CANNOT change it to "built testing framework"
   or "built analytical pipeline" or "built validation system".
9. BLANKET-REPLACE technical terms with JD buzzwords. Common violations:
   BAD: "ETL pipeline" → "analytical pipeline" (not what was built)
   BAD: "ML document processing" → "analytical document processing" (ML is accurate)
   BAD: "Python automation" → "analytical automation" (Python is specific, analytical is vague)
   BAD: "data warehouse" → "analytical framework" (different thing)
   GOOD: "ETL pipeline" → "data pipeline" (true synonym)
   GOOD: "automated reports" → "automated reporting" (same thing, noun form)
   GOOD: Keep original wording when no true synonym exists
10. Repeat any single adjective (like "analytical", "comprehensive", "systematic")
    more than 3 times across the entire resume. Variety and specificity beat
    keyword repetition.

{'='*55}
FORMATTING RULES
{'='*55}
- Name: Title Case (NOT ALL CAPS) — use full legal name
- Location: Use format "City, State Zip" from resume
- Email: Use email from CONTACT_EMAIL environment variable
- Phone: Use phone from contact information
- LinkedIn: Use format linkedin.com/in/[your-profile-id]
- GitHub: Use format github.com/[username]
- No company name in header
- Section headers: bold, no bullet symbols in source text (user applies in Word)
- Skills: each category on its own line, bold label with colon

{'='*55}
COVER LETTER RULES
{'='*55}
The cover_letter_draft must follow these rules:

FORMAT: Hybrid prose+bullets (highest response rate for tech roles in 2026):
- Opening paragraph (2-3 sentences, prose): specific role + why THIS company +
  one sentence positioning relevant expertise. NO generic "I am excited to apply".
- Body (2-4 bullet points with bold key phrases): Each bullet EXPANDS one resume
  achievement into a STAR narrative. Each bullet is 2-3 sentences adding:
  (a) the organizational problem BEFORE you solved it,
  (b) cross-functional collaboration required,
  (c) downstream business outcome BEYOND the technical metric.
  Bold the key phrase at the start of each bullet.
- Honest Fit paragraph (prose): Acknowledge specific gaps between your experience
  and the JD. Be specific about what you'd need to learn. Show self-awareness.
- Closing paragraph (2-3 sentences, prose): Connect experience to their needs,
  express genuine interest, clear call to action.

CONTENT RULES:
1. Total length: 200-400 words. Maximum 4 body bullets.
2. Reference at least ONE real employer by name from the candidate's background
   to ground the narrative
3. Do NOT repeat metrics already used in the resume. If the resume uses
   "$2.3B+" or "300+ automated reports", the cover letter MUST use DIFFERENT
   metrics or angles from the candidate's experience
4. Every technical achievement must answer "what did this enable the
   ORGANIZATION to do?" — not just "what did I personally accomplish"
5. Sign off: Sincerely, [Full Name from Resume]
6. Add [DRAFT FLAG: Human review required] at the end

Return a JSON object with keys:
{{
  "tailored_resume": "<full resume text>",
  "cover_letter_draft": "<draft only — flagged for human edit>",
  "interview_prep": "<3-5 likely technical questions with talking points>",
  "key_points": ["<top 3 positioning decisions made>"],
  "gap_acknowledgment": "<if gap_flags non-empty, plain-text note about gaps for human review>"
}}"""

        user_message = f"""BASE RESUME:
{context.base_resume_text}

JOB DESCRIPTION SUMMARY:
{context.jd_summary if context.jd_summary else 'See JD keywords above for targeting signals.'}

Generate the tailored package following all constraints above."""

        try:
            raw_text = self._call_llm(system_prompt, user_message)
            if raw_text:
                # Try to parse as JSON
                import json as _json
                try:
                    # Find JSON in the response (LLM may wrap in markdown code blocks)
                    json_match = re.search(r'\{[\s\S]*\}', raw_text)
                    if json_match:
                        result = _json.loads(json_match.group())
                        # Post-generation: strip over-repeated adjectives
                        if "tailored_resume" in result:
                            result["tailored_resume"] = self._strip_buzzword_spam(
                                result["tailored_resume"], context.base_resume_text
                            )
                        return result
                except _json.JSONDecodeError:
                    logger.warning("Could not parse constrained_generate output as JSON, wrapping as resume")

                # If JSON parsing failed, treat the whole response as resume text
                return {
                    "tailored_resume": self._strip_buzzword_spam(raw_text, context.base_resume_text),
                    "cover_letter_draft": "",
                    "interview_prep": "",
                    "key_points": [],
                    "gap_acknowledgment": "",
                }
        except Exception as exc:
            logger.error("Constrained generation failed: %s", exc)

        # Return empty result on failure — caller handles this
        return {
            "tailored_resume": "",
            "cover_letter_draft": "",
            "interview_prep": "",
            "key_points": [],
            "gap_acknowledgment": "",
        }

    def generate_constrained_package(
        self,
        job: dict,
        resume_text: str,
        db=None,
    ) -> Dict[str, Any]:
        """Generate resume package using the 3-layer constrained pipeline.

        Layer 1: Build GenerationContext from pre-existing pipeline data
        Layer 2: Constrained LLM generation
        Layer 3: Post-generation fabrication detection

        Args:
            job: Job dict from jobs table (must include id)
            resume_text: Full text of the base resume from settings
            db: DashboardDB instance for reading pipeline data

        Returns:
            dict with: tailored_resume, cover_letter_draft, interview_prep,
                       key_points, gap_acknowledgment, requires_human_review,
                       gap_flags, base_resume_version, fabrication_errors,
                       validation_passed, formatting_warnings, post_gen_score,
                       cover_letter_status, cover_letter_instructions
        """
        from src.generation.context_builder import build_generation_context
        from src.generation.output_validator import validate_generated_output

        job_id = job.get("id")
        if not job_id:
            raise ValueError("job dict must include 'id' field")
        if not db:
            raise ValueError("db (DashboardDB instance) is required for constrained generation")

        # Load configurable thresholds from dashboard_settings
        try:
            self.timeout_seconds = int(db.get_setting("gen_request_timeout", str(REQUEST_TIMEOUT_SECONDS)))
            self.max_tokens = int(db.get_setting("gen_max_tokens", "4096"))
        except Exception:
            pass  # keep defaults

        # ─── LAYER 1: Build constrained context ─────────────────────────
        try:
            context = build_generation_context(
                db=db,
                job_id=job_id,
                resume_text=resume_text
            )
        except Exception as e:
            logger.error(f"Layer 1 context build failed for job {job_id}: {e}")
            raise RuntimeError(
                f"Cannot generate resume for job {job_id}: context builder failed. "
                f"Reason: {e}"
            )

        logger.info(
            f"Job {job_id} context: version={context.base_resume_version}, "
            f"verified_tools={len(context.verified_tools_for_job)}, "
            f"blocked_tools={len(context.blocked_tools_in_jd)}, "
            f"achievements={len(context.selected_achievements)}, "
            f"gap_flags={context.gap_flags}, "
            f"requires_review={context.requires_human_review}"
        )

        # ─── LAYER 2: Constrained generation ────────────────────────────
        raw_output = self.constrained_generate(context=context)

        # ─── LAYER 3: Post-generation validation ────────────────────────
        validation_result = validate_generated_output(
            generated=raw_output.get("tailored_resume", ""),
            context=context,
            db=db,
        )

        if validation_result["fabrication_errors"]:
            logger.error(
                f"Job {job_id}: FABRICATION DETECTED in generated output. "
                f"Errors: {validation_result['fabrication_errors']}"
            )
            raw_output["fabrication_errors"] = validation_result["fabrication_errors"]
            raw_output["requires_human_review"] = True
            raw_output["validation_passed"] = False
        else:
            raw_output["fabrication_errors"] = []
            raw_output["validation_passed"] = True

        # Attach context metadata for dashboard display and DB storage
        raw_output["requires_human_review"] = (
            context.requires_human_review or
            bool(validation_result["fabrication_errors"]) or
            validation_result.get("score_degraded", False)
        )
        raw_output["gap_flags"] = context.gap_flags
        raw_output["base_resume_version"] = context.base_resume_version
        raw_output["job_category"] = context.job_category
        raw_output["verified_tools_used"] = context.verified_tools_for_job
        raw_output["blocked_tools_in_jd"] = context.blocked_tools_in_jd
        raw_output["formatting_warnings"] = validation_result.get("formatting_warnings", [])
        raw_output["post_gen_score"] = validation_result.get("post_gen_score", 0)
        raw_output["score_before"] = context.alignment_score

        # Cover letter handling — always draft, never auto-apply
        raw_output["cover_letter_status"] = "DRAFT_NEEDS_EDIT"
        raw_output["cover_letter_instructions"] = {
            "rule_1": "No metric that appears in the resume may appear verbatim in the cover letter",
            "rule_2": "No phrase longer than 5 words may be shared between resume and cover letter",
            "rule_3": "Add organizational impact — who benefited and what business outcome was enabled",
            "rule_4": "Use narrative prose — not bullet points",
            "rule_5": "Do not start with 'I am writing to apply for...'",
            "format": "Traditional: name-left/date-right header, company address block, 3 paragraphs max",
        }

        return raw_output

    def validate_no_repetition(
        self,
        resume_text: str,
        cover_letter_text: str,
    ) -> Dict[str, Any]:
        """Check for duplicate metrics or phrasing between resume and cover letter.

        Returns:
            ``{"passed": bool, "issues": list[str]}``
        """
        issues: List[str] = []

        # --- Check 1: Shared numbers / metrics ---
        resume_metrics = self._extract_metrics(resume_text)
        cl_metrics = self._extract_metrics(cover_letter_text)
        shared_metrics = resume_metrics & cl_metrics

        for metric in sorted(shared_metrics):
            issues.append(
                f"Repeated metric '{metric}' appears in both resume and cover letter"
            )

        # --- Check 2: Consecutive word overlap (>5 words) ---
        resume_words = resume_text.lower().split()
        cl_words = cover_letter_text.lower().split()

        # Build set of n-grams from resume for fast lookup
        n = 6  # flag sequences of 6+ matching words
        resume_ngrams: set[str] = set()
        for i in range(len(resume_words) - n + 1):
            ngram = " ".join(resume_words[i : i + n])
            resume_ngrams.add(ngram)

        seen_overlaps: set[str] = set()
        for i in range(len(cl_words) - n + 1):
            ngram = " ".join(cl_words[i : i + n])
            if ngram in resume_ngrams and ngram not in seen_overlaps:
                seen_overlaps.add(ngram)
                issues.append(
                    f"Repeated phrase (>{n - 1} consecutive words): '...{ngram}...'"
                )

        passed = len(issues) == 0
        if not passed:
            logger.warning(
                "No-repetition check failed with %d issue(s)", len(issues)
            )
        else:
            logger.info("No-repetition check passed")

        return {"passed": passed, "issues": issues}

    # ── Post-Generation Cleanup ─────────────────────────────────────

    @staticmethod
    def _strip_buzzword_spam(generated: str, base_resume: str) -> str:
        """Remove adjectives the LLM inserted that don't appear in the base resume.

        If a filler adjective (e.g. "analytical", "comprehensive", "systematic")
        appears >3 times in the generated text but <=1 time in the base resume,
        it was injected by the LLM for keyword stuffing. Remove excess occurrences
        by deleting the adjective (+ trailing space) from bullet lines.
        """
        FILLER_ADJECTIVES = [
            "analytical", "comprehensive", "systematic", "strategic",
            "robust", "scalable", "innovative", "cutting-edge",
            "dynamic", "holistic", "enterprise-grade",
        ]
        result = generated
        for adj in FILLER_ADJECTIVES:
            base_count = len(re.findall(r'\b' + adj + r'\b', base_resume, re.IGNORECASE))
            gen_count = len(re.findall(r'\b' + adj + r'\b', result, re.IGNORECASE))
            if gen_count > 3 and base_count <= 1:
                excess = gen_count - 2  # keep at most 2
                logger.info(
                    "Stripping buzzword '%s': %d in generated vs %d in base (removing %d)",
                    adj, gen_count, base_count, excess,
                )
                # Remove "adjective " occurrences from the end, preserving first 2
                count_seen = 0
                lines = result.split('\n')
                for i in range(len(lines) - 1, -1, -1):
                    if count_seen >= excess:
                        break
                    line_lower = lines[i].lower()
                    if adj in line_lower:
                        # Remove the adjective + trailing space (case-insensitive)
                        new_line = re.sub(
                            r'\b' + adj + r'\s+', '', lines[i],
                            count=1, flags=re.IGNORECASE,
                        )
                        if new_line != lines[i]:
                            lines[i] = new_line
                            count_seen += 1
                result = '\n'.join(lines)
        return result

    # ── LLM Call Dispatchers ──────────────────────────────────────────

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Route the request to the correct provider and return generated text."""
        if self.provider == AIProvider.OLLAMA:
            return self._call_ollama(system_prompt, user_prompt)
        elif self.provider == AIProvider.CLAUDE:
            return self._call_claude(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call the Ollama OpenAI-compatible chat completions endpoint."""
        # Low temperature is CRITICAL — 0.7 causes hallucination/fabrication
        # with local models that struggle to follow "use only this data" prompts.
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.15,
            "stream": False,
        }

        # Diagnostic logging — essential to debug prompt issues
        logger.info(
            "Ollama request: model=%s, system_prompt=%d chars, user_prompt=%d chars, total=%d chars",
            self.model,
            len(system_prompt),
            len(user_prompt),
            len(system_prompt) + len(user_prompt),
        )
        # Log first 200 chars of user prompt to verify resume is included
        logger.info("User prompt starts with: %s", user_prompt[:200].replace("\n", " "))

        resp = requests.post(
            OLLAMA_CHAT_URL,
            json=payload,
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            logger.error("Ollama returned empty choices: %s", data)
            return None

        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            logger.error("Ollama returned empty content")
            return None

        logger.info(
            "Ollama generation complete (%d chars, model=%s)",
            len(content),
            self.model,
        )
        # Log first 200 chars of output to verify it uses real data
        logger.info("Output starts with: %s", content[:200].replace("\n", " "))
        return content

    def _call_claude(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call the Anthropic Messages API."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set — cannot call Claude")
            return None

        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": 0.15,  # Low temp critical — prevents hallucination/fabrication
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }

        logger.debug("Calling Claude (%s) ...", self.model)
        try:
            resp = requests.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self._track_claude_usage("generation", success=False, error=str(exc))
            raise

        # Track token usage from response
        usage = data.get("usage", {})
        tokens = (usage.get("input_tokens", 0) or 0) + (usage.get("output_tokens", 0) or 0)
        # Estimate cost: ~$3/M input + $15/M output for Sonnet
        input_cost = (usage.get("input_tokens", 0) or 0) * 3.0 / 1_000_000
        output_cost = (usage.get("output_tokens", 0) or 0) * 15.0 / 1_000_000
        self._track_claude_usage("generation", tokens=tokens, cost=input_cost + output_cost)

        content_blocks = data.get("content", [])
        if not content_blocks:
            logger.error("Claude returned empty content: %s", data)
            return None

        # Concatenate all text blocks
        text_parts = [
            block.get("text", "")
            for block in content_blocks
            if block.get("type") == "text"
        ]
        content = "\n".join(text_parts).strip()

        if not content:
            logger.error("Claude returned no text content")
            return None

        logger.info(
            "Claude generation complete (%d chars, model=%s)",
            len(content),
            self.model,
        )
        return content

    @staticmethod
    def _track_claude_usage(endpoint: str, tokens: int = 0, cost: float = 0.0,
                            success: bool = True, error: str = ""):
        """Log Anthropic API usage to the dashboard database."""
        try:
            from src.dashboard.db import DashboardDB
            db = DashboardDB()
            db.log_api_usage("anthropic", endpoint, tokens_used=tokens,
                             cost_estimate=cost, success=success, error_message=error)
        except Exception:
            pass

    # ── Output Validation ─────────────────────────────────────────────

    @staticmethod
    def validate_output_authenticity(
        generated_text: str,
        master_resume: str,
        doc_type: str = "resume",
    ) -> Dict[str, Any]:
        """Check that AI output uses real candidate data, not fabricated content.

        This catches:
        - Placeholder names (John Doe, Jane Smith)
        - Placeholder companies (ABC Corporation, XYZ University)
        - Missing real company references
        - NOT FOUND skills being claimed as expertise (fabrication)

        Returns:
            {"authentic": bool, "issues": list[str], "confidence": float,
             "fabricated_skills": list[str]}
        """
        issues: List[str] = []
        fabricated_skills: List[str] = []

        candidate_name = _extract_candidate_name(master_resume)
        master_lower = master_resume.lower()
        output_lower = generated_text.lower()

        # Check 1: Candidate name must appear in output
        if candidate_name:
            name_parts = candidate_name.lower().split()
            surname_found = any(
                part in output_lower
                for part in name_parts
                if len(part) > 3
            )
            if not surname_found:
                issues.append(
                    f"Candidate name '{candidate_name}' not found in output. "
                    "Model likely fabricated content."
                )

        # Check 2: Detect common placeholder names
        PLACEHOLDER_NAMES = [
            "john doe", "jane doe", "jane smith", "john smith",
            "first last", "your name", "[name]", "[your name]",
        ]
        for placeholder in PLACEHOLDER_NAMES:
            if placeholder in output_lower:
                issues.append(
                    f"Placeholder name '{placeholder}' detected — "
                    "model ignored the real candidate data."
                )

        # Check 3: Detect placeholder companies
        PLACEHOLDER_COMPANIES = [
            "abc corporation", "xyz university", "abc university",
            "def startups", "acme corp", "acme inc", "example corp",
            "sample company", "company name", "[company]",
            "123 main st", "anytown",
        ]
        for placeholder in PLACEHOLDER_COMPANIES:
            if placeholder in output_lower:
                issues.append(
                    f"Placeholder company/address '{placeholder}' detected — "
                    "model fabricated content."
                )

        # Check 4: At least some real companies from the resume appear in output
        KNOWN_COMPANIES = []
        for company in [e.lower() for e in CANDIDATE_EMPLOYERS]:
            if company in master_lower:
                KNOWN_COMPANIES.append(company)

        if KNOWN_COMPANIES and doc_type == "resume":
            found_companies = [c for c in KNOWN_COMPANIES if c in output_lower]
            if len(found_companies) < 2:
                issues.append(
                    f"Only {len(found_companies)} real companies found in output "
                    f"(expected at least 2 from: {', '.join(KNOWN_COMPANIES)}). "
                    "Model may have fabricated work experience."
                )

        # Check 5: NOT FOUND skills must NOT appear as claimed expertise
        not_found = _extract_not_found_skills(master_resume)
        # Phrases that indicate the output is CLAIMING expertise (not just mentioning)
        CLAIM_PATTERNS = [
            "experience with {skill}",
            "expertise in {skill}",
            "proficient in {skill}",
            "skilled in {skill}",
            "worked with {skill}",
            "using {skill}",
            "built with {skill}",
            "designed with {skill}",
            "implemented {skill}",
            "deployed {skill}",
            "managed {skill}",
            "leveraged {skill}",
            "utilized {skill}",
        ]
        # Also check for skill appearing in a TECHNICAL SKILLS or similar section
        # without being in a "growth areas" or "gaps" context
        GROWTH_CONTEXT = [
            "growth area", "to develop", "gap", "learning",
            "eager to learn", "would need to", "don't have",
            "do not have", "no experience", "not found",
        ]

        for skill in not_found:
            if skill not in output_lower:
                continue
            # Skill is mentioned — check if it's claimed vs acknowledged as gap
            # Find the surrounding context (100 chars around each mention)
            idx = 0
            while True:
                idx = output_lower.find(skill, idx)
                if idx == -1:
                    break
                context_start = max(0, idx - 100)
                context_end = min(len(output_lower), idx + len(skill) + 100)
                context = output_lower[context_start:context_end]

                # If the context mentions growth/gap/learning, it's OK
                in_growth_context = any(gc in context for gc in GROWTH_CONTEXT)
                if not in_growth_context:
                    # Check if it's in a claim pattern
                    is_claimed = any(
                        cp.format(skill=skill) in context
                        for cp in CLAIM_PATTERNS
                    )
                    # Also flag if skill appears in what looks like a skills list
                    # (surrounded by commas or other skills)
                    if is_claimed or (
                        "skill" in context and skill in context
                        and not any(gc in context for gc in GROWTH_CONTEXT)
                    ):
                        if skill not in fabricated_skills:
                            fabricated_skills.append(skill)
                            issues.append(
                                f"FABRICATED SKILL: '{skill}' is marked as NOT FOUND "
                                "in the track doc but appears as claimed expertise "
                                "in the output."
                            )
                idx += len(skill)

        # Calculate confidence
        if not issues:
            confidence = 1.0
        elif fabricated_skills:
            confidence = 0.0  # fabricated skills = zero confidence
        elif len(issues) == 1:
            confidence = 0.3
        else:
            confidence = 0.0

        authentic = len(issues) == 0

        if not authentic:
            logger.warning(
                "OUTPUT AUTHENTICITY FAILED (%d issues, %d fabricated skills): %s",
                len(issues),
                len(fabricated_skills),
                "; ".join(issues),
            )
        else:
            logger.info("Output authenticity check PASSED")

        return {
            "authentic": authentic,
            "issues": issues,
            "confidence": confidence,
            "fabricated_skills": fabricated_skills,
        }

    # ── Fallback Helpers ──────────────────────────────────────────────

    @staticmethod
    def _template_fallback_resume(job: dict, resume_text: str) -> str:
        """Use the template-based generator and extract the resume text.

        If the template generator also fails, returns a condensed version
        of the track doc (NOT the raw 27K reference document).
        """
        result = generate_application_package(job, resume_text)
        if result["status"] == "success" and result.get("resume_path"):
            try:
                return result["resume_path"].read_text(encoding="utf-8")
            except OSError as exc:
                logger.error("Could not read fallback resume: %s", exc)
        # Last resort — return condensed version, not the raw track doc
        return _condense_track_doc(resume_text)

    @staticmethod
    def _template_fallback_cover_letter(job: dict, resume_text: str) -> str:
        """Use the template-based generator and extract the cover letter text."""
        result = generate_application_package(job, resume_text)
        if result["status"] == "success" and result.get("cover_letter_path"):
            try:
                return result["cover_letter_path"].read_text(encoding="utf-8")
            except OSError as exc:
                logger.error("Could not read fallback cover letter: %s", exc)
        return ""  # no cover letter to return

    # ── Utility ───────────────────────────────────────────────────────

    @staticmethod
    def _extract_metrics(text: str) -> set[str]:
        """Extract numbers and metric-like tokens from text.

        Captures patterns such as ``$1.2M``, ``40%``, ``3x``, ``10,000``,
        ``15+ years``, and plain integers/floats that appear in context.
        """
        patterns = [
            r"\$[\d,.]+[MmBbKk]?",         # dollar amounts
            r"\d+(?:\.\d+)?%",              # percentages
            r"\d+(?:\.\d+)?[xX]",           # multipliers
            r"\d{1,3}(?:,\d{3})+",          # comma-separated numbers
            r"\d+\+?\s*(?:years?|yrs?)",    # years of experience
            r"\d+\+?\s*(?:engineers?|teams?|people|reports?|clients?)",  # team sizes
        ]
        combined = "|".join(f"({p})" for p in patterns)
        matches = re.findall(combined, text, re.IGNORECASE)
        # re.findall with groups returns tuples — flatten and filter blanks
        return {
            m.strip().lower()
            for group in matches
            for m in group
            if m.strip()
        }
