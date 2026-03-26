"""
Enrichment modules for job listing analysis.

- Ghost signal detection (repost, vague JD, wayback, etc.)
"""

from .ghost_signals import GhostSignalCollector, GhostSignals, compute_ghost_score

__all__ = ["GhostSignalCollector", "GhostSignals", "compute_ghost_score"]
