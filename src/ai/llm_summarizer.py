"""
LLM Summarizer

Generates compact executive summaries using the configured AI provider.
Supports OpenAI-compatible and Anthropic APIs, with safe fallbacks.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
import os
import requests

from src.config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class LLMSummarizer:
    """Simple wrapper around configured LLM provider to summarize weekly reports."""

    config: AppConfig

    def _build_prompt(self, report_data: Dict[str, Any]) -> str:
        metrics = report_data.get("key_metrics", {})
        insights = report_data.get("insights", [])
        top_companies = report_data.get("top_companies", [])

        lines = []
        lines.append("You are an executive assistant summarizing LinkedIn network intelligence.")
        lines.append("Write a concise, 4-6 sentence summary highlighting performance, opportunities, and a concrete next step.")
        lines.append("Avoid marketing fluff. Be specific and actionable. Use plain language.")
        lines.append("")
        lines.append("Key Metrics:")
        lines.append(f"- Connections: {metrics.get('total_connections', 0)}")
        lines.append(f"- Leadership: {metrics.get('leadership_engagement', '0%')}")
        lines.append(f"- Fortune 500: {metrics.get('f500_penetration', '0%')}")
        lines.append(f"- Companies: {metrics.get('unique_companies', 0)}")
        lines.append(f"- Avg Strength: {metrics.get('avg_connection_strength', 0.0)} / 3.0")

        if top_companies:
            top = ", ".join([c for c, _ in top_companies[:5]])
            lines.append(f"Top Companies: {top}")

        if insights:
            lines.append("Top Insights:")
            for ins in insights[:3]:
                lines.append(f"- {ins}")

        lines.append("")
        lines.append("Return only the final summary paragraph(s). Maximum 700 characters.")
        return "\n".join(lines)

    def _fallback_summary(self, report_data: Dict[str, Any]) -> str:
        """Heuristic summary used when an external LLM is unavailable.

        Keeps the shape of the AI output, but is fully deterministic and based
        only on the provided metrics/insights so that reports never show blank
        AI sections when the provider fails or is misconfigured.
        """
        metrics = report_data.get("key_metrics", {}) or {}
        insights = report_data.get("insights", []) or []
        top_companies = report_data.get("top_companies", []) or []

        total_connections = metrics.get("total_connections", 0)
        leadership = metrics.get("leadership_engagement", "0%")
        f500 = metrics.get("f500_penetration", "0%")
        unique_companies = metrics.get("unique_companies", 0)
        avg_strength = metrics.get("avg_connection_strength", 0.0)

        top_names = [c for c, _ in top_companies[:3] if c]
        insight_snippets = [str(i) for i in insights[:2] if i]

        parts = []
        parts.append(
            f"This week your LinkedIn network shows {total_connections} total connections "
            f"with leadership engagement around {leadership} and Fortune 500 presence near {f500}."
        )
        parts.append(
            f"Your relationships span roughly {unique_companies} companies with an average connection strength of {avg_strength}/3.0."
        )
        if top_names:
            parts.append(
                f"Most of your influence is concentrated at {', '.join(top_names)}, which should remain priority targets."
            )
        if insight_snippets:
            parts.append(
                "Key themes this week include: " + "; ".join(insight_snippets) + "."
            )
        parts.append(
            "In the coming week, focus on a small list of high-value conversations and one or two concrete outreach campaigns."
        )
        return " ".join(parts)

    def _call_anthropic(self, prompt: str) -> Optional[str]:
        api_key = self.config.ai.api_key
        if not api_key:
            return None
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        model = self.config.ai.model or "claude-3-5-sonnet-20240620"
        body = {
            "model": model,
            "max_tokens": 500,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=self.config.ai.timeout or 30)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", [])
            if content and isinstance(content, list):
                # Anthropic returns a list of blocks
                text_parts = [blk.get("text", "") for blk in content if isinstance(blk, dict)]
                text = "\n".join([t for t in text_parts if t]).strip()
                return text or None
        except Exception as e:
            logger.warning(f"LLM (Anthropic) failed: {e}")
        return None

    def _call_openai(self, prompt: str, base_url: Optional[str] = None) -> Optional[str]:
        api_key = self.config.ai.api_key
        # Local providers may not require API keys; allow empty key when base_url is custom
        headers = {"content-type": "application/json"}
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"

        url = (base_url.rstrip("/") if base_url else "https://api.openai.com") + "/v1/chat/completions"
        model = self.config.ai.model or "gpt-4o-mini"
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a concise executive assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.ai.temperature or 0.2,
            "max_tokens": 500,
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=self.config.ai.timeout or 30)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            if choices and choices[0].get("message"):
                text = choices[0]["message"].get("content", "").strip()
                return text or None
        except Exception as e:
            logger.warning(f"LLM (OpenAI-compatible) failed: {e}")
        return None

    def _call_llm(self, prompt: str) -> Optional[str]:
        provider = (self.config.ai.provider or "openai").lower()
        if provider == "claude":
            return self._call_anthropic(prompt)
        if provider == "openai":
            return self._call_openai(prompt)
        # Attempt OpenAI-compatible endpoints for local providers
        if provider in {"ollama", "lmstudio", "textgen", "localai", "custom"}:
            base = None
            if provider == "ollama":
                base = self.config.ai.ollama_host
            elif provider == "lmstudio":
                base = self.config.ai.lmstudio_host
            elif provider == "textgen":
                base = self.config.ai.textgen_host
            elif provider == "localai":
                base = self.config.ai.localai_host
            else:
                base = self.config.ai.custom_host
            return self._call_openai(prompt, base_url=base)
        # Fallback
        return None

    def generate_weekly_summary(self, report_data: Dict[str, Any]) -> Optional[str]:
        if not getattr(self.config.ai, "enabled", False):
            return None
        # Optional feature flag
        if os.getenv("AI_SUMMARY_ENABLED", "true").lower() != "true":
            return None
        prompt = self._build_prompt(report_data)
        text = self._call_llm(prompt)
        if not text:
            logger.warning("AI summary provider unavailable; falling back to deterministic summary.")
            text = self._fallback_summary(report_data)
        # Trim overly long responses for Telegram
        text = text.strip()
        if len(text) > 900:
            text = text[:900].rstrip() + "…"
        return text
