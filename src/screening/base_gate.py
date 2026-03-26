"""
Abstract base class for screening gates
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from .models import GateVerdict, GateResult


class BaseGate(ABC):
    """
    Abstract base class for all screening gates.

    Each gate evaluates a job listing against specific criteria and returns
    a GateVerdict indicating pass, fail, or override_required.

    Gates are executed sequentially by the pipeline in order of their
    `order` property. The first failure short-circuits the pipeline.
    """

    def __init__(self, config: Any = None, timeout_seconds: float = 10.0):
        self.config = config
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(f"{__name__}.{self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this gate (e.g., '0B_defense_exclusion')"""
        ...

    @property
    @abstractmethod
    def order(self) -> int:
        """Execution order. Lower numbers run first."""
        ...

    @property
    def enabled(self) -> bool:
        """Whether this gate is enabled. Override to check config."""
        return True

    @abstractmethod
    async def _evaluate(self, job) -> GateVerdict:
        """
        Core evaluation logic. Subclasses implement this.

        Args:
            job: The job listing to evaluate

        Returns:
            GateVerdict with the evaluation result
        """
        ...

    async def evaluate(self, job) -> GateVerdict:
        """
        Execute the gate evaluation with timeout and timing.

        Wraps _evaluate() with:
        - Timing measurement
        - Timeout enforcement
        - Error handling (gate errors result in PASS to avoid false rejections)
        """
        start = time.perf_counter()
        try:
            verdict = await asyncio.wait_for(
                self._evaluate(job),
                timeout=self.timeout_seconds,
            )
            verdict.processing_time_ms = (time.perf_counter() - start) * 1000
            verdict.gate_name = self.name
            self.logger.debug(
                "Gate %s: %s - %s (%.1fms)",
                self.name, verdict.result.value, verdict.reason,
                verdict.processing_time_ms,
            )
            return verdict

        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.logger.warning(
                "Gate %s timed out after %.0fms - passing job",
                self.name, elapsed_ms,
            )
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.PASS,
                reason=f"Gate timed out after {self.timeout_seconds}s - defaulting to pass",
                confidence=0.0,
                processing_time_ms=elapsed_ms,
                metadata={"timeout": True},
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.logger.error(
                "Gate %s error: %s - passing job", self.name, e, exc_info=True,
            )
            return GateVerdict(
                gate_name=self.name,
                result=GateResult.PASS,
                reason=f"Gate error: {e} - defaulting to pass",
                confidence=0.0,
                processing_time_ms=elapsed_ms,
                metadata={"error": str(e)},
            )
