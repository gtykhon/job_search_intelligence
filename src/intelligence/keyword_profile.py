"""
Traffic Light Keyword Classification Framework.

Classifies job opportunities using a GREEN/YELLOW/RED system:
  GREEN  — strong cultural/role fit signals; boost in search terms
  YELLOW — conditional signals requiring manual review above threshold
  RED    — hard misalignment; auto-exclude via screening gate

Usage:
    manager = KeywordProfileManager()
    profile = manager.load("default")
    classification = manager.classify_job(job_listing, profile)
    # classification.traffic_light in ("GREEN", "YELLOW", "RED")
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_PROFILES_DIR = Path(__file__).parent.parent.parent / "config" / "keyword_profiles"


@dataclass
class KeywordProfile:
    name: str
    green: List[str] = field(default_factory=list)
    yellow: List[str] = field(default_factory=list)
    red: List[str] = field(default_factory=list)
    yellow_threshold: int = 2
    description: str = ""

    def as_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "green": self.green,
            "yellow": self.yellow,
            "red": self.red,
            "yellow_threshold": self.yellow_threshold,
        }


@dataclass
class KeywordClassification:
    traffic_light: str  # "GREEN" | "YELLOW" | "RED"
    red_matches: List[str] = field(default_factory=list)
    yellow_matches: List[str] = field(default_factory=list)
    green_matches: List[str] = field(default_factory=list)
    reason: str = ""

    @property
    def is_green(self) -> bool:
        return self.traffic_light == "GREEN"

    @property
    def is_yellow(self) -> bool:
        return self.traffic_light == "YELLOW"

    @property
    def is_red(self) -> bool:
        return self.traffic_light == "RED"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _keyword_in_text(keyword: str, text: str) -> bool:
    pattern = re.compile(
        r"(?<![a-zA-Z0-9])" + re.escape(keyword.lower()) + r"(?![a-zA-Z0-9])"
    )
    return bool(pattern.search(_normalize(text)))


class KeywordProfileManager:
    """Loads, saves, and applies keyword profiles stored as YAML files."""

    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir or _DEFAULT_PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def load(self, profile_name: str = "default") -> KeywordProfile:
        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not installed; returning empty keyword profile")
            return KeywordProfile(name=profile_name)

        yaml_path = self.profiles_dir / f"{profile_name}.yaml"
        if not yaml_path.exists():
            logger.warning(
                "Keyword profile '%s' not found at %s; using empty profile",
                profile_name, yaml_path,
            )
            return KeywordProfile(name=profile_name)

        with yaml_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        return KeywordProfile(
            name=data.get("name", profile_name),
            description=data.get("description", ""),
            green=data.get("green", []),
            yellow=data.get("yellow", []),
            red=data.get("red", []),
            yellow_threshold=int(data.get("yellow_threshold", 2)),
        )

    def save(self, profile: KeywordProfile) -> Path:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to save keyword profiles") from exc

        yaml_path = self.profiles_dir / f"{profile.name}.yaml"
        with yaml_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(profile.as_dict(), fh, default_flow_style=False, allow_unicode=True)
        logger.info("Saved keyword profile '%s' to %s", profile.name, yaml_path)
        return yaml_path

    def list_profiles(self) -> List[str]:
        return [p.stem for p in self.profiles_dir.glob("*.yaml")]

    def classify_job(self, job, profile: KeywordProfile) -> KeywordClassification:
        """
        Classify a job listing against the keyword profile.

        Scans job title, description, and company name.
        RED match -> immediate RED (hard exclude).
        YELLOW matches >= threshold -> YELLOW (manual review).
        Otherwise -> GREEN.
        """
        text_parts = []
        for attr in ("title", "description", "company_name", "company"):
            val = getattr(job, attr, None)
            if val:
                text_parts.append(str(val))
        full_text = " ".join(text_parts)

        red_hits = [kw for kw in profile.red if _keyword_in_text(kw, full_text)]
        if red_hits:
            return KeywordClassification(
                traffic_light="RED",
                red_matches=red_hits,
                reason=f"Hard-exclude keyword(s) detected: {', '.join(red_hits)}",
            )

        yellow_hits = [kw for kw in profile.yellow if _keyword_in_text(kw, full_text)]
        green_hits = [kw for kw in profile.green if _keyword_in_text(kw, full_text)]

        if len(yellow_hits) >= profile.yellow_threshold:
            return KeywordClassification(
                traffic_light="YELLOW",
                yellow_matches=yellow_hits,
                green_matches=green_hits,
                reason=(
                    f"{len(yellow_hits)} caution keyword(s) exceed threshold "
                    f"({profile.yellow_threshold}): {', '.join(yellow_hits)}"
                ),
            )

        return KeywordClassification(
            traffic_light="GREEN",
            yellow_matches=yellow_hits,
            green_matches=green_hits,
            reason="No disqualifying keywords detected.",
        )
