"""
Screening gate pipeline -- sequential gate execution with short-circuit on failure
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any, Tuple

from .base_gate import BaseGate
from .models import GateResult, GateVerdict, ScreeningResult


class ScreeningPipeline:
    """
    Sequential screening pipeline that runs jobs through a series of gates.

    - Gates execute in order (lowest `order` first)
    - First FAIL short-circuits the pipeline
    - OVERRIDE_REQUIRED is treated as FAIL unless override_resolver is attached
    - Disabled gates are skipped
    - Gate errors default to PASS (never reject due to internal errors)

    Optional: attach an OverrideResolver to auto-resolve OVERRIDE_REQUIRED results
    via a local LLM instead of requiring manual review.
    """

    def __init__(
        self,
        gates: Optional[List[BaseGate]] = None,
        override_resolver=None,    # OverrideResolver | None
    ):
        self.logger = logging.getLogger(__name__)
        self._gates: List[BaseGate] = []
        self._stats: Dict[str, Any] = {
            'total_screened': 0,
            'total_passed': 0,
            'total_failed': 0,
            'total_override_required': 0,
            'gate_stats': {},
        }

        self._override_resolver = override_resolver   # OverrideResolver | None

        if gates:
            self._gates = sorted(gates, key=lambda g: g.order)

        for gate in self._gates:
            self._stats['gate_stats'][gate.name] = {
                'evaluated': 0,
                'passed': 0,
                'failed': 0,
                'override_required': 0,
                'errors': 0,
                'total_time_ms': 0.0,
            }

    def add_gate(self, gate: BaseGate):
        """Add a gate and re-sort by order."""
        self._gates.append(gate)
        self._gates.sort(key=lambda g: g.order)
        if gate.name not in self._stats['gate_stats']:
            self._stats['gate_stats'][gate.name] = {
                'evaluated': 0,
                'passed': 0,
                'failed': 0,
                'override_required': 0,
                'errors': 0,
                'total_time_ms': 0.0,
            }

    async def screen_job(self, job) -> ScreeningResult:
        """
        Run a single job through all enabled gates sequentially.

        Short-circuits on the first FAIL or OVERRIDE_REQUIRED result.

        Returns:
            ScreeningResult with pass/fail status and all gate verdicts
        """
        start = time.perf_counter()
        verdicts: List[GateVerdict] = []

        for gate in self._gates:
            if not gate.enabled:
                continue

            verdict = await gate.evaluate(job)
            verdicts.append(verdict)

            # Update gate stats
            gate_stat = self._stats['gate_stats'].get(gate.name, {})
            gate_stat['evaluated'] = gate_stat.get('evaluated', 0) + 1
            gate_stat['total_time_ms'] = gate_stat.get('total_time_ms', 0.0) + verdict.processing_time_ms

            if verdict.result == GateResult.PASS:
                gate_stat['passed'] = gate_stat.get('passed', 0) + 1
            elif verdict.result == GateResult.FAIL:
                gate_stat['failed'] = gate_stat.get('failed', 0) + 1
                total_ms = (time.perf_counter() - start) * 1000
                self._stats['total_screened'] += 1
                self._stats['total_failed'] += 1
                return ScreeningResult(
                    job_id=getattr(job, 'job_id', None),
                    passed=False,
                    failed_gate=gate.name,
                    reason=verdict.reason,
                    verdicts=verdicts,
                    total_time_ms=total_ms,
                    override_eligible=verdict.override_eligible,
                )
            elif verdict.result == GateResult.OVERRIDE_REQUIRED:
                gate_stat['override_required'] = gate_stat.get('override_required', 0) + 1

                # ── LLM override resolution ──────────────────────────────────
                if self._override_resolver is not None:
                    try:
                        partial_result = ScreeningResult(
                            job_id=getattr(job, 'job_id', None),
                            passed=False,
                            failed_gate=gate.name,
                            reason=verdict.reason,
                            verdicts=verdicts,
                            total_time_ms=0,
                            override_eligible=True,
                        )
                        decision = await self._override_resolver.resolve(job, partial_result)
                        if decision.proceed and decision.confidence >= 0.70:
                            # LLM approved — continue pipeline from next gate
                            self.logger.info(
                                "Gate %s OVERRIDE_REQUIRED → LLM approved (%.0f%% confidence): %s",
                                gate.name, decision.confidence * 100, decision.reasoning,
                            )
                            verdict.metadata['override_decision'] = {
                                'proceed': True,
                                'confidence': decision.confidence,
                                'reasoning': decision.reasoning,
                                'backend': decision.backend,
                            }
                            continue   # resume the gate loop — do NOT short-circuit
                        else:
                            # LLM rejected or low confidence — attach decision to result
                            total_ms = (time.perf_counter() - start) * 1000
                            self._stats['total_screened'] += 1
                            self._stats['total_override_required'] += 1
                            result = ScreeningResult(
                                job_id=getattr(job, 'job_id', None),
                                passed=False,
                                failed_gate=gate.name,
                                reason=verdict.reason,
                                verdicts=verdicts,
                                total_time_ms=total_ms,
                                override_eligible=True,
                            )
                            result.metadata = {
                                'override_decision': {
                                    'proceed': False,
                                    'confidence': decision.confidence,
                                    'reasoning': decision.reasoning,
                                    'backend': decision.backend,
                                }
                            }
                            return result
                    except Exception as _exc:
                        self.logger.warning("Override resolver error: %s", _exc)
                        # Fall through to standard OVERRIDE_REQUIRED handling

                # ── Standard OVERRIDE_REQUIRED (no resolver or resolver failed) ──
                total_ms = (time.perf_counter() - start) * 1000
                self._stats['total_screened'] += 1
                self._stats['total_override_required'] += 1
                return ScreeningResult(
                    job_id=getattr(job, 'job_id', None),
                    passed=False,
                    failed_gate=gate.name,
                    reason=verdict.reason,
                    verdicts=verdicts,
                    total_time_ms=total_ms,
                    override_eligible=True,
                )

            if verdict.metadata.get('error') or verdict.metadata.get('timeout'):
                gate_stat['errors'] = gate_stat.get('errors', 0) + 1

        # All gates passed
        total_ms = (time.perf_counter() - start) * 1000
        self._stats['total_screened'] += 1
        self._stats['total_passed'] += 1

        return ScreeningResult(
            job_id=getattr(job, 'job_id', None),
            passed=True,
            verdicts=verdicts,
            total_time_ms=total_ms,
        )

    async def screen_jobs_batch(
        self,
        jobs: list,
        max_concurrent: int = 10,
    ) -> List[Tuple[Any, ScreeningResult]]:
        """
        Screen multiple jobs with controlled concurrency.

        Args:
            jobs: List of jobs to screen
            max_concurrent: Maximum concurrent screening tasks

        Returns:
            List of (job, ScreeningResult) tuples
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results: List[Tuple[Any, ScreeningResult]] = []

        async def _screen_one(job):
            async with semaphore:
                result = await self.screen_job(job)
                return job, result

        tasks = [_screen_one(job) for job in jobs]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for item in completed:
            if isinstance(item, Exception):
                self.logger.error("Batch screening error: %s", item)
                continue
            results.append(item)

        passed = sum(1 for _, r in results if r.passed)
        self.logger.info(
            "Batch screening: %d/%d passed (%d errors)",
            passed, len(results), len(jobs) - len(results),
        )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return pipeline statistics."""
        stats = dict(self._stats)
        stats['pass_rate'] = (
            self._stats['total_passed'] / max(self._stats['total_screened'], 1)
        )
        stats['gates_active'] = len([g for g in self._gates if g.enabled])
        stats['gates_total'] = len(self._gates)
        return stats

    def reset_stats(self):
        """Reset all statistics."""
        self._stats['total_screened'] = 0
        self._stats['total_passed'] = 0
        self._stats['total_failed'] = 0
        self._stats['total_override_required'] = 0
        for gate_name in self._stats['gate_stats']:
            self._stats['gate_stats'][gate_name] = {
                'evaluated': 0,
                'passed': 0,
                'failed': 0,
                'override_required': 0,
                'errors': 0,
                'total_time_ms': 0.0,
            }
