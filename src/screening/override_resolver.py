"""
LLM Override Resolver — auto-resolves OVERRIDE_REQUIRED pipeline results.

When a gate returns OVERRIDE_REQUIRED (manual review needed), this module
uses a local Ollama LLM (llama3.1:8b) to make a structured proceed/reject
decision, eliminating the manual review queue for ambiguous cases.

Design:
  - Async, non-blocking: runs inside the existing async pipeline
  - Structured JSON output via Ollama /api/generate with format="json"
  - Never raises — any failure returns a conservative heuristic fallback
  - Decision is attached to ScreeningResult.metadata, never overwrites gate verdicts

Fallback chain:
  1. Ollama llama3.1:8b structured JSON → OverrideDecision
  2. Ollama unavailable / timeout → heuristic fallback (proceed=False, confidence=0.3)

Usage:
    resolver = OverrideResolver()
    decision = await resolver.resolve(job, screening_result)
    if decision.proceed and decision.confidence >= 0.70:
        # treat as PASS
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Candidate profile context embedded in every prompt
_CANDIDATE_PROFILE = """
- Target role: Senior Python / Data Engineer (IC, not management)
- Salary floor: $140,000/year (hard floor $130K)
- Work model: Remote-first strongly preferred; hybrid only if exceptional role
- Location: US-based or timezone-compatible remote
- Target industries: fintech, healthtech, SaaS, AI/ML product companies
- Exclusions: defense, clearance, government, sales, on-site 5 days/week
- Years experience: 8+ years Python, strong ETL/data engineering background
""".strip()


@dataclass
class OverrideDecision:
    proceed: bool
    confidence: float       # 0.0 – 1.0
    reasoning: str
    backend: str            # "ollama" | "heuristic"
    raw_response: str = ""  # full LLM response for audit


class OverrideResolver:
    """
    Uses Ollama to auto-resolve OVERRIDE_REQUIRED gate results.

    Attach to ScreeningPipeline via the override_resolver parameter.
    The pipeline calls resolve() after any OVERRIDE_REQUIRED verdict.
    """

    OLLAMA_BASE = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.1:8b"
    DEFAULT_TIMEOUT = 60.0    # seconds; llama3.1:8b cold-start on this machine ~30-45s
    MIN_CONFIDENCE = 0.55     # below this, fall back to heuristic

    def __init__(
        self,
        ollama_url: str = OLLAMA_BASE,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        enabled: bool = True,
        min_alignment: int = 60,   # skip LLM for jobs with kw_score below this floor
    ):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.enabled = enabled
        self.min_alignment = min_alignment
        self._available: Optional[bool] = None

    # ── Availability check ───────────────────────────────────────────
    def is_available(self) -> bool:
        """Check if Ollama is reachable (cached after first check)."""
        if self._available is not None:
            return self._available
        try:
            import urllib.request
            req = urllib.request.urlopen(f"{self.ollama_url}/api/tags", timeout=3)
            self._available = req.status == 200
        except Exception:
            self._available = False
            logger.debug("Ollama not reachable at %s — override resolver disabled", self.ollama_url)
        return self._available

    async def warm_up(self) -> bool:
        """
        Pre-warm the LLM model so the first real resolve() call isn't hit by cold-start latency.
        Sends a minimal no-op prompt and discards the response.
        Returns True if successful.
        """
        if not self.is_available():
            return False
        try:
            logger.info("Warming up %s (this may take 30-45s on first load)...", self.model)
            await self._call_ollama('{"warmup": true}')
            logger.info("LLM warm-up complete")
            return True
        except Exception as e:
            logger.warning("LLM warm-up failed (non-fatal): %s", e)
            return False

    # ── Main entry point ─────────────────────────────────────────────
    async def resolve(self, job: Any, screening_result: Any) -> OverrideDecision:
        """
        Auto-resolve an OVERRIDE_REQUIRED screening result.

        Args:
            job:               Job object (SimpleNamespace or similar)
            screening_result:  ScreeningResult from pipeline.screen_job()

        Returns:
            OverrideDecision with proceed flag, confidence, and reasoning
        """
        if not self.enabled:
            return self._heuristic("resolver disabled")

        if not self.is_available():
            return self._heuristic("Ollama not reachable")

        # Skip LLM for clearly misaligned jobs (e.g. kw=0 wrong-profession roles)
        kw_score = getattr(job, "alignment_score", None) or 0
        if kw_score < self.min_alignment:
            return self._heuristic(
                f"kw_score {kw_score} below min_alignment {self.min_alignment} — skipped"
            )

        try:
            prompt = self._build_prompt(job, screening_result)
            raw = await self._call_ollama(prompt)
            decision = self._parse_response(raw)
            if decision.confidence < self.MIN_CONFIDENCE:
                logger.debug(
                    "LLM confidence %.2f below threshold %.2f — using heuristic",
                    decision.confidence, self.MIN_CONFIDENCE,
                )
                return self._heuristic(f"low LLM confidence ({decision.confidence:.2f})")
            return decision
        except Exception as e:
            logger.warning("OverrideResolver failed: %s", e)
            return self._heuristic(str(e))

    # ── Prompt builder ───────────────────────────────────────────────
    def _build_prompt(self, job: Any, result: Any) -> str:
        title = getattr(job, "title", "") or ""
        company = getattr(job, "company", "") or ""
        location = getattr(job, "location", "") or ""
        sal_min = getattr(job, "salary_min", None)
        sal_max = getattr(job, "salary_max", None)
        remote = getattr(job, "remote_type", "unknown")
        align = getattr(job, "alignment_score", None)
        sem_align = getattr(job, "semantic_alignment_score", None)

        salary_str = "not listed"
        if sal_min or sal_max:
            lo = f"${int(sal_min):,}" if sal_min else "?"
            hi = f"${int(sal_max):,}" if sal_max else "?"
            salary_str = f"{lo} – {hi}"

        failed_gate = getattr(result, "failed_gate", "unknown")
        reason = getattr(result, "reason", "unknown")

        # JD snippet — first 400 chars gives enough role context without bloating the prompt
        jd_raw = (getattr(job, "description", "") or "").strip()
        jd_snippet = " ".join(jd_raw[:500].split())[:400]  # collapse whitespace, trim

        jd_section = ""
        if jd_snippet:
            jd_section = f"\nJOB DESCRIPTION SNIPPET:\n{jd_snippet}...\n"

        scores_str = ""
        if align is not None:
            scores_str += f"  Keyword alignment: {align}/100\n"
        if sem_align is not None:
            scores_str += f"  Semantic alignment: {sem_align:.0f}/100\n"

        return f"""You are a job application screening assistant.

CANDIDATE PROFILE:
{_CANDIDATE_PROFILE}

JOB BEING REVIEWED:
  Title:    {title}
  Company:  {company}
  Location: {location}
  Salary:   {salary_str}
  Remote:   {remote}
{scores_str}
AUTOMATED SCREENING RESULT:
  Status:      OVERRIDE_REQUIRED (needs manual review)
  Flagged by:  {failed_gate}
  Reason:      {reason}
{jd_section}
DECISION REQUIRED:
Given the candidate profile, the gate flag, and the job details above, should this application PROCEED or be REJECTED?

Rules:
- PROCEED only if the role is a strong technical IC fit AND the concern is minor/incorrect
- REJECT if the gate concern is legitimate (wrong role type, genuinely toxic culture, real staffing agency)
- Be conservative: when uncertain, REJECT

Respond with ONLY valid JSON, no other text:
{{"proceed": true or false, "confidence": 0.0 to 1.0, "reasoning": "one concise sentence explaining the decision"}}"""

    # ── Ollama call ──────────────────────────────────────────────────
    async def _call_ollama(self, prompt: str) -> str:
        """POST to Ollama /api/generate (async). Returns response text."""
        import aiohttp
        import asyncio

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,    # low temp for deterministic decisions
                "num_predict": 150,    # short output — just the JSON
            },
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Ollama returned HTTP {resp.status}")
                data = await resp.json()
                return data.get("response", "")

    # ── Response parsing ─────────────────────────────────────────────
    def _parse_response(self, text: str) -> OverrideDecision:
        """
        Extract JSON from LLM response.
        Uses a lenient extractor to handle model chattiness around the JSON.
        """
        # Try direct JSON parse first
        try:
            data = json.loads(text.strip())
            return self._dict_to_decision(data, text)
        except json.JSONDecodeError:
            pass

        # Find first {...} block in the response
        match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return self._dict_to_decision(data, text)
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse LLM JSON response: %r", text[:200])
        return self._heuristic("JSON parse failed")

    def _dict_to_decision(self, data: dict, raw: str) -> OverrideDecision:
        proceed = bool(data.get("proceed", False))
        raw_conf = data.get("confidence", 0.5)
        confidence = float(max(0.0, min(1.0, raw_conf)))
        reasoning = str(data.get("reasoning", data.get("reason", "")))[:300]
        return OverrideDecision(
            proceed=proceed,
            confidence=confidence,
            reasoning=reasoning,
            backend="ollama",
            raw_response=raw[:500],
        )

    # ── Heuristic fallback ───────────────────────────────────────────
    def _heuristic(self, reason: str) -> OverrideDecision:
        """Conservative fallback: don't proceed, flag for manual review."""
        return OverrideDecision(
            proceed=False,
            confidence=0.30,
            reasoning=f"Heuristic fallback ({reason}). Manual review required.",
            backend="heuristic",
        )


# ── Module-level singleton ──────────────────────────────────────────────
_resolver: Optional[OverrideResolver] = None


def get_override_resolver(
    enabled: bool = True,
    model: str = OverrideResolver.DEFAULT_MODEL,
) -> OverrideResolver:
    """Return the module-level shared OverrideResolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = OverrideResolver(enabled=enabled, model=model)
    return _resolver
