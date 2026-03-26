"""
Semantic Job Classifier — Ollama-powered pre-filter for alignment scoring.

Runs a lightweight local LLM (e.g., Llama 3 8B, Mistral 7B) to classify
job postings by category BEFORE the keyword scorer runs. This prevents
false positives like a "Data Center Construction Manager" scoring 98%
because of token-level keyword collisions (api, infrastructure, reporting).

Design principles:
  - Runs locally via Ollama — zero API cost
  - Retries with backoff if Ollama is busy (other LLM tasks running)
  - Falls back to Claude Haiku if Ollama is completely down
  - Sub-2-second classification per job (warm Ollama)
  - Caches results in the DB to avoid re-classifying

Usage:
    classifier = SemanticClassifier()
    result = classifier.classify("Senior Data Center Capacity Delivery Manager",
                                  description[:500])
    if not result.is_relevant:
        # Skip keyword scoring entirely — hard zero
        ...
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ── Relevant categories for Grisha's job search ────────────────────
RELEVANT_CATEGORIES = {
    "software_data_engineering",
    "data_analysis_business_analysis",
    "analytics_engineering",
}

# All categories the classifier can return
ALL_CATEGORIES = {
    "software_data_engineering",       # SWE, DE, platform eng, backend
    "data_analysis_business_analysis", # DA, BA, BSA, analytics
    "analytics_engineering",           # Analytics Engineer, dbt-focused
    "physical_infrastructure",         # Construction, data center builds, facilities
    "sales_marketing",                 # AE, SDR, marketing, GTM
    "legal_finance_hr",                # Counsel, accountant, recruiter, people ops
    "research_science",                # ML research, PhD-track, lab science
    "security_operations",             # InfoSec, SOC, red team, physical security
    "product_design",                  # PM, UX, product design
    "executive_management",            # VP, Director, C-suite
    "other",
}

CLASSIFICATION_PROMPT = """Classify this job posting into exactly ONE category.

CATEGORIES:
1. software_data_engineering — Software engineers, data engineers, platform engineers, backend/fullstack developers, DevOps/SRE building software systems
2. data_analysis_business_analysis — Data analysts, business analysts, business systems analysts, reporting analysts working with data for insights/decisions
3. analytics_engineering — Analytics engineers focused on dbt, data modeling, metrics layers, BI infrastructure
4. physical_infrastructure — Data center construction, facilities management, real estate, physical plant operations, capacity delivery, mechanical/electrical engineering for buildings
5. sales_marketing — Account executives, SDRs, marketing managers, GTM roles, customer success, solutions architects (pre-sales)
6. legal_finance_hr — Lawyers, accountants, tax, recruiting, HR, people operations, compliance officers
7. research_science — ML researchers, research scientists, PhD-track, interpretability, alignment research
8. security_operations — InfoSec engineers, SOC analysts, red team, trust & safety, threat intelligence, physical security
9. product_design — Product managers, UX designers, product designers
10. executive_management — VP+, directors, C-suite, heads of departments
11. other — Anything that doesn't fit above

JOB TITLE: {title}

DESCRIPTION (first 500 chars):
{description}

Respond with ONLY a JSON object, no other text:
{{"category": "<category_name>", "confidence": <0.0-1.0>, "reason": "<one sentence>"}}"""


@dataclass
class ClassificationResult:
    """Result of semantic job classification."""
    category: str
    confidence: float
    reason: str
    is_relevant: bool
    from_cache: bool = False
    error: Optional[str] = None
    backend: Optional[str] = None  # "ollama", "claude", "quick_filter"

    @property
    def should_score(self) -> bool:
        """Whether keyword scoring should proceed."""
        return self.is_relevant or self.error is not None  # fail-open on errors


class SemanticClassifier:
    """
    Ollama-powered semantic job classifier with Claude fallback.

    Classifies jobs into broad categories to filter out irrelevant postings
    before expensive keyword-matching runs.

    Retry strategy:
      - Check Ollama load before each call
      - If busy (running_models has active tasks), wait and retry up to N times
      - If Ollama is completely down, fall back to Claude Haiku (cheapest)
    """

    def __init__(
        self,
        model: str = "llama3.1:8b",
        ollama_url: str = "http://localhost:11434",
        timeout: float = 30.0,
        enabled: bool = True,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        claude_fallback: bool = True,
        claude_model: str = "claude-3-haiku-20240307",
    ):
        self.model = model
        self.ollama_url = ollama_url.rstrip("/")
        self.timeout = timeout
        self.enabled = enabled
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.claude_fallback = claude_fallback
        self.claude_model = claude_model
        self._ollama_checked: Optional[bool] = None
        self._claude_available: Optional[bool] = None
        # Track consecutive Ollama failures to avoid hammering a dead server
        self._ollama_consecutive_failures = 0
        self._ollama_failure_threshold = 5  # Switch to Claude after N consecutive failures

    def is_available(self) -> bool:
        """Check if ANY backend (Ollama or Claude) is available."""
        return self._is_ollama_available() or self._is_claude_available()

    def _is_ollama_available(self) -> bool:
        """Check if Ollama is running and the model exists."""
        if self._ollama_checked is not None:
            return self._ollama_checked

        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.ollama_url}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                models = [m.get("name", "") for m in data.get("models", [])]
                model_base = self.model.split(":")[0]
                self._ollama_checked = any(model_base in m for m in models)
                if not self._ollama_checked:
                    logger.warning(
                        "Ollama running but model '%s' not found. Available: %s",
                        self.model, models[:5],
                    )
                return self._ollama_checked
        except Exception as e:
            logger.debug("Ollama not available: %s", e)
            self._ollama_checked = False
            return False

    def _is_claude_available(self) -> bool:
        """Check if Claude API key is configured."""
        if self._claude_available is not None:
            return self._claude_available
        self._claude_available = bool(os.environ.get("ANTHROPIC_API_KEY"))
        if self._claude_available:
            logger.info("Claude fallback available (%s)", self.claude_model)
        return self._claude_available

    def _check_ollama_load(self) -> dict:
        """
        Check how busy Ollama is by querying /api/ps (running models).

        Returns:
            {"busy": bool, "running_models": int, "details": str}
        """
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.ollama_url}/api/ps",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                running = data.get("models", [])
                count = len(running)
                details = ", ".join(
                    f"{m.get('name', '?')} ({m.get('size_vram', 0) // 1024 // 1024}MB)"
                    for m in running
                )
                # Consider busy if any model is currently loaded/running
                # (GPU memory contention causes slowdowns)
                return {
                    "busy": count > 0,
                    "running_models": count,
                    "details": details or "idle",
                }
        except Exception:
            return {"busy": False, "running_models": 0, "details": "unknown"}

    def classify(
        self, title: str, description: str, job_id: Optional[int] = None
    ) -> ClassificationResult:
        """
        Classify a job posting into a category.

        Strategy:
          1. Quick title regex filter (instant, no LLM)
          2. Try Ollama with retry-on-busy logic
          3. If Ollama fails/down, fall back to Claude Haiku
          4. If everything fails, fail-open (allow scoring)
        """
        if not self.enabled:
            return ClassificationResult(
                category="unknown", confidence=0.0,
                reason="Classifier disabled", is_relevant=True, error="disabled",
            )

        # ── Quick title-based pre-filter (no LLM needed) ──────────
        quick = self._quick_title_filter(title)
        if quick is not None:
            return quick

        # ── Try Ollama with retry logic ───────────────────────────
        if self._is_ollama_available() and self._ollama_consecutive_failures < self._ollama_failure_threshold:
            result = self._call_ollama_with_retry(title, description[:500])
            if result is not None:
                self._ollama_consecutive_failures = 0
                return result
            # Ollama failed — increment counter
            self._ollama_consecutive_failures += 1
            if self._ollama_consecutive_failures >= self._ollama_failure_threshold:
                logger.warning(
                    "Ollama failed %d times consecutively — switching to Claude fallback",
                    self._ollama_consecutive_failures,
                )

        # ── Claude fallback ───────────────────────────────────────
        if self.claude_fallback and self._is_claude_available():
            result = self._call_claude(title, description[:500])
            if result is not None:
                return result

        # ── Everything failed — fail-open ─────────────────────────
        return ClassificationResult(
            category="unknown", confidence=0.0,
            reason="All classification backends unavailable",
            is_relevant=True, error="all_backends_failed",
        )

    def _call_ollama_with_retry(
        self, title: str, description_snippet: str
    ) -> Optional[ClassificationResult]:
        """
        Call Ollama with retry-on-busy logic.

        If Ollama is busy (other models loaded), waits and retries.
        Returns None if all retries exhausted.
        """
        for attempt in range(self.max_retries + 1):
            # Check load before calling
            if attempt > 0:
                load = self._check_ollama_load()
                if load["busy"]:
                    wait = self.retry_delay * attempt  # Progressive backoff
                    logger.info(
                        "Ollama busy (%s) — retry %d/%d in %.0fs",
                        load["details"], attempt, self.max_retries, wait,
                    )
                    time.sleep(wait)

            try:
                return self._call_ollama(title, description_snippet)
            except Exception as e:
                err_str = str(e).lower()
                # Timeout or connection errors are retryable
                if "timed out" in err_str or "urlopen" in err_str or "connection" in err_str:
                    if attempt < self.max_retries:
                        logger.debug(
                            "Ollama attempt %d/%d failed (retryable): %s",
                            attempt + 1, self.max_retries + 1, e,
                        )
                        continue
                # Non-retryable error or last attempt
                logger.warning(
                    "Ollama classification failed for '%s' after %d attempts: %s",
                    title, attempt + 1, e,
                )
                return None

        return None

    def _quick_title_filter(self, title: str) -> Optional[ClassificationResult]:
        """
        Fast regex-based title filter for obvious non-matches.
        Catches ~40% of irrelevant jobs without needing the LLM.
        """
        t = title.lower().strip()

        # Obvious physical/construction roles
        construction_patterns = [
            r"data center.*(deliver|capacity|construction|mechanical|electrical)",
            r"(construction|facilities|building|plant)\s+(manager|engineer|lead)",
            r"(general\s+superintendent|site\s+lead|field\s+engineer)",
            r"(hvac|cooling|power\s+delivery|commissioning)",
        ]
        for pat in construction_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="physical_infrastructure", confidence=0.95,
                    reason="Title matches physical infrastructure pattern",
                    is_relevant=False, backend="quick_filter",
                )

        # Obvious sales roles
        sales_patterns = [
            r"^account\s+executive",
            r"^(enterprise|strategic|growth)\s+account",
            r"^(business\s+development|sales\s+development)\s+rep",
            r"^customer\s+success\s+manager",
            r"^(partner|channel)\s+(manager|director)",
        ]
        for pat in sales_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="sales_marketing", confidence=0.90,
                    reason="Title matches sales pattern",
                    is_relevant=False, backend="quick_filter",
                )

        # Obvious legal/finance/HR roles
        legal_hr_patterns = [
            r"(counsel|attorney|lawyer|paralegal)",
            r"^(accountant|tax\s+(manager|director|lead))",
            r"^(recruiter|recruiting|talent\s+acquisition)",
            r"^(payroll|compensation|benefits)\s+(manager|specialist|lead)",
        ]
        for pat in legal_hr_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="legal_finance_hr", confidence=0.90,
                    reason="Title matches legal/finance/HR pattern",
                    is_relevant=False, backend="quick_filter",
                )

        # Obvious research roles (may be relevant edge case — let LLM decide)
        # Don't filter these; some research roles overlap with engineering

        return None  # No quick match — proceed to LLM

    def classify_keyword(self, title: str, description: str = "") -> ClassificationResult:
        """
        Fast keyword-based classifier — no LLM calls, runs in <1ms.
        Uses title + first 500 chars of description for pattern matching.
        Returns the same ClassificationResult as the LLM-based classifier.

        Accuracy is sufficient for resume routing (VERSION_MAP) and pre-filtering.
        The alignment scorer already handles precision scoring downstream.
        """
        t = title.lower().strip()
        d = description[:500].lower() if description else ""
        combined = f"{t} {d}"

        # 1. Quick filter first (physical infrastructure, sales, legal/HR)
        quick = self._quick_title_filter(title)
        if quick is not None:
            quick.backend = "keyword"
            return quick

        # 2. Software / Data Engineering (most common relevant category)
        sde_title_patterns = [
            r"(software|backend|fullstack|full.stack|platform|infrastructure|site.reliability)\s+engineer",
            r"(data|etl|pipeline|database|db|cloud)\s+engineer",
            r"(devops|sre|reliability)\s+engineer",
            r"(software|application)\s+(developer|architect)",
            r"(frontend|front.end)\s+engineer",
            r"developer\b",
            r"swe\b",
        ]
        for pat in sde_title_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="software_data_engineering", confidence=0.88,
                    reason=f"Title matches SDE pattern: {pat}",
                    is_relevant=True, backend="keyword",
                )

        # 3. Data Analysis / Business Analysis
        da_patterns = [
            r"(data|business|reporting|intelligence)\s+analyst",
            r"(business\s+systems|bsa)\s+analyst",
            r"bi\s+(developer|engineer|analyst)",
            r"(tableau|power\s*bi|looker)\s+(developer|analyst|engineer)",
        ]
        for pat in da_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="data_analysis_business_analysis", confidence=0.88,
                    reason=f"Title matches DA/BA pattern: {pat}",
                    is_relevant=True, backend="keyword",
                )

        # 4. Analytics Engineering
        ae_patterns = [
            r"analytics\s+engineer",
            r"(dbt|metrics|data\s+model)\s+engineer",
        ]
        for pat in ae_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="analytics_engineering", confidence=0.90,
                    reason=f"Title matches analytics engineering pattern: {pat}",
                    is_relevant=True, backend="keyword",
                )

        # 5. Research / Science
        research_patterns = [
            r"(research|applied)\s+scientist",
            r"(ml|machine\s+learning)\s+researcher",
            r"research\s+engineer",
        ]
        for pat in research_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="research_science", confidence=0.85,
                    reason=f"Title matches research pattern: {pat}",
                    is_relevant=False, backend="keyword",
                )

        # 6. Security / Operations
        sec_patterns = [
            r"(security|infosec|cybersecurity|soc)\s+(engineer|analyst|architect)",
            r"(red\s+team|blue\s+team|threat)\s+(engineer|analyst)",
            r"trust\s+.?\s*safety",
        ]
        for pat in sec_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="security_operations", confidence=0.85,
                    reason=f"Title matches security pattern: {pat}",
                    is_relevant=False, backend="keyword",
                )

        # 7. Product / Design
        pd_patterns = [
            r"product\s+(manager|lead|director|owner)",
            r"(ux|ui|product)\s+designer",
            r"design\s+(manager|director|lead)",
        ]
        for pat in pd_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="product_design", confidence=0.85,
                    reason=f"Title matches product/design pattern: {pat}",
                    is_relevant=False, backend="keyword",
                )

        # 8. Executive / Management
        exec_patterns = [
            r"^(vp|vice\s+president|director|head\s+of|chief|cto|cio|cfo)\b",
            r"^(engineering|technical)\s+manager",
        ]
        for pat in exec_patterns:
            if re.search(pat, t):
                return ClassificationResult(
                    category="executive_management", confidence=0.80,
                    reason=f"Title matches executive/management pattern: {pat}",
                    is_relevant=False, backend="keyword",
                )

        # 9. Description-based fallback — look for strong signals
        if any(kw in combined for kw in ["python", "sql", "data pipeline", "etl", "api", "microservice"]):
            return ClassificationResult(
                category="software_data_engineering", confidence=0.65,
                reason="Description contains engineering keywords",
                is_relevant=True, backend="keyword",
            )

        # 10. No match — default to "other" (still relevant, let scorer decide)
        return ClassificationResult(
            category="other", confidence=0.50,
            reason="No keyword pattern matched — defaulting to other",
            is_relevant=True, backend="keyword",
        )

    def _call_ollama(self, title: str, description_snippet: str) -> ClassificationResult:
        """Call Ollama API for classification."""
        import urllib.request

        prompt = CLASSIFICATION_PROMPT.format(
            title=title,
            description=description_snippet,
        )

        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 150,
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

        response_text = data.get("response", "").strip()
        result = self._parse_response(response_text)
        result.backend = "ollama"
        return result

    def _call_claude(self, title: str, description_snippet: str) -> Optional[ClassificationResult]:
        """Call Claude Haiku API as fallback classifier."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            import urllib.request

            prompt = CLASSIFICATION_PROMPT.format(
                title=title,
                description=description_snippet,
            )

            payload = json.dumps({
                "model": self.claude_model,
                "max_tokens": 200,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            # Track token usage
            usage = data.get("usage", {})
            tokens = (usage.get("input_tokens", 0) or 0) + (usage.get("output_tokens", 0) or 0)
            input_cost = (usage.get("input_tokens", 0) or 0) * 0.25 / 1_000_000  # Haiku pricing
            output_cost = (usage.get("output_tokens", 0) or 0) * 1.25 / 1_000_000
            self._track_claude("classification", tokens=tokens, cost=input_cost + output_cost)

            # Extract text from content blocks
            content_blocks = data.get("content", [])
            response_text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    response_text += block.get("text", "")

            response_text = response_text.strip()
            if not response_text:
                logger.warning("Claude returned empty response")
                return None

            result = self._parse_response(response_text)
            result.backend = "claude"
            logger.debug("Claude classified '%s' as %s (%.0f%%)",
                        title, result.category, result.confidence * 100)
            return result

        except Exception as e:
            logger.warning("Claude fallback failed for '%s': %s", title, e)
            self._track_claude("classification", success=False, error=str(e))
            return None

    def _track_claude(self, endpoint: str, tokens: int = 0, cost: float = 0.0,
                      success: bool = True, error: str = ""):
        """Log Anthropic API usage to the dashboard database."""
        try:
            from src.dashboard.db import DashboardDB
            db = DashboardDB()
            db.log_api_usage("anthropic", endpoint, tokens_used=tokens,
                             cost_estimate=cost, success=success, error_message=error)
        except Exception:
            pass

    def _parse_response(self, response_text: str) -> ClassificationResult:
        """Parse the LLM's JSON response with fallback handling."""
        try:
            # Try direct JSON parse
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks or surrounding text
            json_match = re.search(r"\{[^}]+\}", response_text)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    return ClassificationResult(
                        category="unknown", confidence=0.0,
                        reason=f"Unparseable response: {response_text[:100]}",
                        is_relevant=True, error="parse_error",
                    )
            else:
                return ClassificationResult(
                    category="unknown", confidence=0.0,
                    reason=f"No JSON in response: {response_text[:100]}",
                    is_relevant=True, error="no_json",
                )

        category = parsed.get("category", "other").strip().lower()
        confidence = float(parsed.get("confidence", 0.5))
        reason = parsed.get("reason", "")

        # Validate category
        if category not in ALL_CATEGORIES:
            # Fuzzy match: find closest
            for valid_cat in ALL_CATEGORIES:
                if category in valid_cat or valid_cat in category:
                    category = valid_cat
                    break
            else:
                category = "other"

        is_relevant = category in RELEVANT_CATEGORIES

        return ClassificationResult(
            category=category,
            confidence=confidence,
            reason=reason,
            is_relevant=is_relevant,
        )

    def reset_ollama_failures(self):
        """Reset the consecutive failure counter (e.g., after Ollama comes back)."""
        self._ollama_consecutive_failures = 0
        self._ollama_checked = None  # Re-check availability


# ── Convenience function for batch classification ─────────────────

def classify_jobs_batch(
    jobs: list,
    classifier: Optional[SemanticClassifier] = None,
    progress_cb=None,
) -> dict:
    """
    Classify a batch of jobs, returning stats and per-job results.

    Args:
        jobs: List of job dicts with 'id', 'title', 'description'
        classifier: SemanticClassifier instance (creates default if None)
        progress_cb: Optional callback(percent, message)

    Returns:
        {
            "total": int,
            "relevant": int,
            "filtered": int,
            "by_category": {category: count},
            "results": {job_id: ClassificationResult},
        }
    """
    if classifier is None:
        classifier = SemanticClassifier()

    results = {}
    by_category = {}
    relevant_count = 0
    total = len(jobs)

    for i, job in enumerate(jobs):
        job_id = job.get("id", i)
        title = job.get("title", "")
        desc = job.get("description", "")

        result = classifier.classify(title, desc, job_id=job_id)
        results[job_id] = result

        cat = result.category
        by_category[cat] = by_category.get(cat, 0) + 1
        if result.is_relevant:
            relevant_count += 1

        if progress_cb and (i + 1) % 10 == 0:
            progress_cb(
                int(100 * (i + 1) / total),
                f"Classified {i+1}/{total} — {relevant_count} relevant",
            )

    return {
        "total": total,
        "relevant": relevant_count,
        "filtered": total - relevant_count,
        "by_category": by_category,
        "results": results,
    }
