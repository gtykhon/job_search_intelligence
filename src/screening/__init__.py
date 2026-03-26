"""
Screening Gate Pipeline
========================
Sequential gate evaluation for pre-qualifying job listings before expensive AI processing.

Ported from job_search project — adapted for job_search_intelligence dashboard integration.

Gates execute in order (cheapest/fastest first). First FAIL short-circuits the pipeline.
Gate errors default to PASS (never reject due to internal errors).

Usage:
    from src.screening import get_screening_pipeline

    pipeline = get_screening_pipeline()
    result = await pipeline.screen_job(job)
    if result.passed:
        # proceed with AI processing
"""

from .models import GateResult, GateVerdict, ScreeningResult
from .base_gate import BaseGate
from .pipeline import ScreeningPipeline
from .gate_registry import register_gate, get_registered_gates
from .override_resolver import OverrideResolver, get_override_resolver

__all__ = [
    "GateResult",
    "GateVerdict",
    "ScreeningResult",
    "BaseGate",
    "ScreeningPipeline",
    "OverrideResolver",
    "get_override_resolver",
    "register_gate",
    "get_registered_gates",
    "get_screening_pipeline",
    "reset_screening_pipeline",
]


_pipeline = None


def get_screening_pipeline(config=None, enable_all=False, with_resolver=False):
    """
    Get or create the global screening pipeline with all registered gates.

    Args:
        with_resolver: Attach the LLM OverrideResolver (llama3.1:8b via Ollama).
                       When True, OVERRIDE_REQUIRED cases are auto-resolved by the
                       LLM instead of being hard-stopped as rejects.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    # Import gates to trigger registration
    from .gates import gate_0a_company_research  # noqa: F401
    from .gates import gate_0b_defense_exclusion  # noqa: F401
    from .gates import gate_0c_staffing_agency    # noqa: F401
    from .gates import gate_0d_ghost_job          # noqa: F401
    from .gates import gate_0e_tech_stack         # noqa: F401
    from .gates import gate_0f_compensation       # noqa: F401
    from .gates import gate_culture               # noqa: F401

    try:
        from .gates import gate_0g_red_keywords     # noqa: F401
        from .gates import gate_0h_yellow_review    # noqa: F401
        from .gates import gate_0i_alignment_score  # noqa: F401
        from .gates import gate_0j_role_type        # noqa: F401
    except ImportError:
        pass  # Gates not yet available — non-critical

    gate_classes = get_registered_gates()
    gates = [cls(config=config) for cls in gate_classes]

    resolver = None
    if with_resolver:
        resolver = get_override_resolver()
        if resolver.is_available():
            import logging
            logging.getLogger(__name__).info(
                "OverrideResolver ACTIVE — model=%s  min_alignment=%d",
                resolver.model, resolver.min_alignment,
            )
        else:
            logging.getLogger(__name__).warning(
                "OverrideResolver requested but Ollama not reachable — "
                "OVERRIDE_REQUIRED cases will be hard-rejected"
            )

    _pipeline = ScreeningPipeline(gates=gates, override_resolver=resolver)
    return _pipeline


def reset_screening_pipeline():
    """Force recreation of the pipeline (e.g. after config changes)."""
    global _pipeline
    _pipeline = None
