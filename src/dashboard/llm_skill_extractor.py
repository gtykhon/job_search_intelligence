"""
LLM-based skill extraction for job scoring.

Uses Ollama (llama3.1:8b by default) to extract structured skill lists
from job descriptions and resumes, then fuzzy-matches them for scoring.

Falls back gracefully to keyword matching when Ollama is unavailable.
"""

import hashlib
import json
import logging
import re
import urllib.request
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ── Prompts ────────────────────────────────────────────────────────

JD_EXTRACTION_PROMPT = """You are a precise skill extractor. Your job is to extract ONLY skills that are **explicitly written** in this job posting text.

Return ONLY valid JSON in this exact format:
{{
  "technical_skills": [{{"name": "skill name"}}, ...],
  "soft_skills": [{{"name": "skill name"}}, ...]
}}

CRITICAL RULES — FOLLOW EXACTLY:
1. **ZERO HALLUCINATION**: Only extract a skill if you can point to the exact word or phrase in the text. If "Python" does not appear in the text, do NOT include "Python". If "CI/CD" does not appear, do NOT include "CI/CD". When in doubt, leave it out.
2. Extract specific technologies, tools, frameworks, languages, platforms, methodologies, and certifications that are explicitly named.
3. Pay close attention to parenthetical examples like "(e.g., Python, Terraform)" or "(such as Kafka, Redis)" — extract EACH technology listed inside these parentheses.
4. Use short canonical names: "Python" not "Python programming language", "Kubernetes" not "container orchestration with Kubernetes".
5. Keep acronyms exactly as written: CI/CD, SDLC, SAST, REST, GraphQL, etc.
6. Do NOT extract:
   - Skills you think the job probably needs but that aren't written in the text
   - Generic phrases: "best practices", "high-impact initiatives", "cutting-edge technology"
   - Single abstract words that are not technical skills: "trust", "safety", "privacy", "governance" (unless they are part of a named tool/framework like "Trust & Safety platform")
   - Business/domain concepts: "account prioritization", "data enrichment", "performance narrative"
   - Company-internal product names unless they are well-known industry tools
   - Anything from benefits, compensation, or EEO sections
7. Soft skills: ONLY extract those **explicitly stated as requirements**. Do NOT generate a generic list. If the JD doesn't mention "leadership", don't include it.
8. If the job description is very short or vague with few specific technologies, return a SHORT list. It is correct to return an empty or near-empty list for non-technical roles. Do NOT pad the list.
9. Extract technologies mentioned ANYWHERE in the text — including in role descriptions, team descriptions, and "about the role" sections, not just bullet-point requirements. For example, "primarily written in Go" means Go is a required skill. "powered by ClickHouse" means ClickHouse is relevant.
10. Extract ALL specific named technologies. Common ones to watch for: programming languages (Python, Go, Java, Rust, TypeScript, etc.), databases (PostgreSQL, MySQL, Redis, ClickHouse, etc.), cloud platforms (AWS, GCP, Azure), tools (Docker, Kubernetes, Terraform), and APIs/protocols (REST, GraphQL, gRPC).
11. When technologies are listed together (e.g., "Go, Python, Rust, or Java"), extract EVERY item in the list — not just the first one or two.
12. If "machine learning" or "ML" appears in the text, extract "Machine Learning" as a skill.

Job Title: {title}

Job Description:
{description}"""

RESUME_EXTRACTION_PROMPT = """Extract all technical skills from this resume.
Return ONLY valid JSON in this exact format:
{{
  "technical_skills": [{{"name": "skill name"}}, ...],
  "soft_skills": [{{"name": "skill name"}}, ...]
}}

Rules:
- Extract specific technologies, tools, frameworks, methodologies the person has used
- Include acronyms as-is (e.g., CI/CD, ETL, REST API)
- Use short canonical names
- Only include skills the person has actually demonstrated/used, not aspirational ones

Resume:
{text}"""


@dataclass
class SkillExtractionResult:
    """Result of LLM skill extraction."""
    technical_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    source: str = "llm"  # "llm" or "cache"

    def to_dict(self) -> dict:
        return {
            "technical_skills": self.technical_skills,
            "soft_skills": self.soft_skills,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SkillExtractionResult":
        return cls(
            technical_skills=d.get("technical_skills", []),
            soft_skills=d.get("soft_skills", []),
            source=d.get("source", "cache"),
        )


@dataclass
class SkillMatchResult:
    """Result of matching JD skills against resume skills."""
    matched: List[Tuple[str, str]]    # (jd_skill, resume_skill) pairs
    jd_only: List[str]                # Skills in JD but not in resume (gaps)
    resume_only: List[str]            # Skills in resume but not in JD
    match_ratio: float                # 0.0 - 1.0

    @property
    def matched_names(self) -> List[str]:
        """JD skill names that were matched."""
        return [jd for jd, _ in self.matched]

    @property
    def gap_names(self) -> List[str]:
        """JD skill names that are gaps."""
        return self.jd_only


class LLMSkillExtractor:
    """Extract skills from text using Ollama (local) or Claude (Anthropic API)."""

    # Claude model constants
    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_API_VERSION = "2023-06-01"

    def __init__(
        self,
        model: str = "llama3.1:8b",
        ollama_url: str = "http://localhost:11434",
        timeout: float = 180.0,
        similarity_threshold: float = 0.75,
        provider: str = "ollama",
    ):
        self.model = model
        self.ollama_url = ollama_url.rstrip("/")
        self.timeout = timeout
        self.similarity_threshold = similarity_threshold
        self.provider = provider  # "ollama" or "claude"
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if the configured provider/model is available."""
        if self._available is not None:
            return self._available

        if self.provider == "claude":
            import os
            self._available = bool(os.environ.get("ANTHROPIC_API_KEY"))
            if not self._available:
                logger.debug("Claude not available: ANTHROPIC_API_KEY not set")
            return self._available

        # Ollama
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/tags", method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                models = [m.get("name", "") for m in data.get("models", [])]
                model_base = self.model.split(":")[0]
                self._available = any(model_base in m for m in models)
                return self._available
        except Exception as e:
            logger.debug("Ollama not available: %s", e)
            self._available = False
            return False

    def _is_ollama_busy(self) -> bool:
        """Check if Ollama is currently processing another request."""
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/ps", method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                running = data.get("models", [])
                return len(running) > 0
        except Exception:
            return False

    def extract_skills(
        self, text: str, text_type: str = "jd", title: str = ""
    ) -> SkillExtractionResult:
        """Extract skills from text using LLM.

        Args:
            text: Job description or resume text.
            text_type: "jd" for job description, "resume" for resume.
            title: Job title (only used for JD extraction).

        Returns:
            SkillExtractionResult with extracted skills.

        Raises:
            Exception if LLM call fails.
        """
        if text_type == "jd":
            # Strip benefits section before sending to LLM
            from src.dashboard.scoring import AlignmentScorer
            cleaned = AlignmentScorer._strip_benefits_section(text)
            prompt = JD_EXTRACTION_PROMPT.format(
                title=title or "Unknown",
                description=cleaned[:6000],
            )
        else:
            prompt = RESUME_EXTRACTION_PROMPT.format(
                text=text[:6000],
            )

        if self.provider == "claude":
            response_text = self._call_claude(prompt)
        else:
            response_text = self._call_ollama(prompt)

        response_text = response_text.strip()
        result = self._parse_response(response_text)

        # Post-processing: validate extracted skills against source text
        if text_type == "jd":
            result = self._validate_extraction(result, text)

        return result

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API and return the response text."""
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 1500,
                "num_ctx": 8192,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())

        return data.get("response", "")

    def _call_claude(self, prompt: str) -> str:
        """Call Anthropic Claude Messages API and return the response text."""
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        payload = json.dumps({
            "model": self.model,
            "max_tokens": 2000,
            "system": "You are a precise skill extractor. Return ONLY valid JSON.",
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }).encode("utf-8")

        req = urllib.request.Request(
            self.ANTHROPIC_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": self.ANTHROPIC_API_VERSION,
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())

        # Extract text from content blocks
        content_blocks = data.get("content", [])
        text_parts = [
            block.get("text", "")
            for block in content_blocks
            if block.get("type") == "text"
        ]
        response_text = "\n".join(text_parts)

        # Log usage
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        logger.info("Claude skill extraction: %s — %d input + %d output tokens",
                     self.model, input_tokens, output_tokens)

        return response_text

    def _parse_response(self, response_text: str) -> SkillExtractionResult:
        """Parse LLM JSON response into SkillExtractionResult."""
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            match = re.search(r'\{[\s\S]*\}', response_text)
            if match:
                parsed = json.loads(match.group())
            else:
                logger.warning("Could not parse LLM response: %s", response_text[:200])
                return SkillExtractionResult()

        tech = []
        for item in parsed.get("technical_skills", []):
            name = item.get("name", "") if isinstance(item, dict) else str(item)
            if name:
                tech.append(name.strip())

        soft = []
        for item in parsed.get("soft_skills", []):
            name = item.get("name", "") if isinstance(item, dict) else str(item)
            if name:
                soft.append(name.strip())

        return SkillExtractionResult(
            technical_skills=tech,
            soft_skills=soft,
            source="llm",
        )

    # Words that are NOT technical skills even if they appear in JD text
    _NON_SKILL_WORDS = {
        "trust", "safety", "privacy", "governance", "compliance", "strategy",
        "leadership", "communication", "mentoring", "collaboration",
        "innovation", "passion", "creativity", "accountability",
        "transparency", "integrity", "diversity", "inclusion",
        "payments", "fintech", "crypto", "web3",  # business domains, not skills
    }

    def _validate_extraction(
        self, result: SkillExtractionResult, source_text: str
    ) -> SkillExtractionResult:
        """Validate LLM-extracted skills actually appear in the source text.

        Removes hallucinated skills that the LLM invented but aren't in the JD.
        Uses fuzzy matching to handle minor variations (e.g., "Kubernetes" vs "kubernetes",
        "CI/CD" vs "ci/cd pipeline").
        """
        text_lower = source_text.lower()
        validated_tech = []
        removed = []

        for skill in result.technical_skills:
            skill_lower = skill.lower().strip()

            # Skip single-word non-technical terms
            if skill_lower in self._NON_SKILL_WORDS:
                removed.append(skill)
                continue

            # Direct substring check (handles most cases)
            if skill_lower in text_lower:
                validated_tech.append(skill)
                continue

            # Check individual words for multi-word skills
            # e.g., "React Native" — check if both "react" and "native" appear
            words = skill_lower.split()
            if len(words) >= 2:
                # For multi-word skills, require the key word (longest one) to appear
                key_word = max(words, key=len)
                if key_word in text_lower and len(key_word) >= 3:
                    validated_tech.append(skill)
                    continue

            # Check common variations
            # "Node.js" <-> "nodejs" <-> "node"
            variants = [
                skill_lower.replace(".", ""),       # Node.js -> Nodejs
                skill_lower.replace(".js", ""),      # Node.js -> Node
                skill_lower.replace(" ", ""),         # CI/CD pipeline -> CI/CDpipeline
                skill_lower.replace("-", " "),        # object-oriented -> object oriented
                skill_lower.replace("/", ""),         # CI/CD -> CICD
            ]
            found = False
            for v in variants:
                if v in text_lower and len(v) >= 2:
                    found = True
                    break
            if found:
                validated_tech.append(skill)
                continue

            # Skill is not in the text — it's hallucinated
            removed.append(skill)

        if removed:
            logger.info("Removed %d hallucinated skills: %s", len(removed), removed)

        return SkillExtractionResult(
            technical_skills=validated_tech,
            soft_skills=result.soft_skills,  # Don't validate soft skills as strictly
            source=result.source,
        )

    def match_skills(
        self,
        jd_skills: SkillExtractionResult,
        resume_skills: SkillExtractionResult,
    ) -> Dict[str, SkillMatchResult]:
        """Fuzzy-match JD skills against resume skills.

        Returns dict with "technical" and "soft" SkillMatchResult.
        """
        return {
            "technical": self._match_lists(
                jd_skills.technical_skills,
                resume_skills.technical_skills,
            ),
            "soft": self._match_lists(
                jd_skills.soft_skills,
                resume_skills.soft_skills,
            ),
        }

    def _match_lists(
        self, jd_list: List[str], resume_list: List[str],
    ) -> SkillMatchResult:
        """Fuzzy-match two skill lists."""
        if not jd_list:
            return SkillMatchResult(
                matched=[], jd_only=[], resume_only=resume_list,
                match_ratio=1.0,
            )

        # Normalize for comparison
        jd_normalized = {s: s.lower().strip() for s in jd_list}
        resume_normalized = {s: s.lower().strip() for s in resume_list}

        matched: List[Tuple[str, str]] = []
        used_resume: Set[str] = set()

        for jd_skill, jd_norm in jd_normalized.items():
            best_match = None
            best_ratio = 0.0

            for resume_skill, res_norm in resume_normalized.items():
                if resume_skill in used_resume:
                    continue

                # Exact match (case-insensitive)
                if jd_norm == res_norm:
                    best_match = resume_skill
                    best_ratio = 1.0
                    break

                # Check if one contains the other
                if jd_norm in res_norm or res_norm in jd_norm:
                    ratio = 0.9
                    if ratio > best_ratio:
                        best_match = resume_skill
                        best_ratio = ratio
                    continue

                # Fuzzy match
                ratio = SequenceMatcher(None, jd_norm, res_norm).ratio()
                if ratio > best_ratio:
                    best_match = resume_skill
                    best_ratio = ratio

            if best_match and best_ratio >= self.similarity_threshold:
                matched.append((jd_skill, best_match))
                used_resume.add(best_match)

        jd_only = [s for s in jd_list if s not in {m[0] for m in matched}]
        resume_only = [s for s in resume_list if s not in used_resume]
        match_ratio = len(matched) / len(jd_list) if jd_list else 1.0

        return SkillMatchResult(
            matched=matched,
            jd_only=jd_only,
            resume_only=resume_only,
            match_ratio=match_ratio,
        )


def content_hash(text: str, text_type: str) -> str:
    """Create a cache key hash from text content."""
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    return hashlib.sha256(f"{text_type}:{normalized}".encode()).hexdigest()[:32]
