"""
Data models for the screening gate pipeline
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class GateResult(Enum):
    """Possible outcomes of a gate evaluation"""
    PASS = "pass"
    FAIL = "fail"
    OVERRIDE_REQUIRED = "override_required"


@dataclass
class GateVerdict:
    """Result of a single gate evaluation"""
    gate_name: str
    result: GateResult
    reason: str
    confidence: float = 1.0
    evidence: Optional[str] = None
    override_eligible: bool = False
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScreeningResult:
    """Result of running a job through the full screening pipeline"""
    job_id: Optional[str] = None
    passed: bool = False
    failed_gate: Optional[str] = None
    reason: Optional[str] = None
    verdicts: List[GateVerdict] = field(default_factory=list)
    total_time_ms: float = 0.0
    override_eligible: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'job_id': self.job_id,
            'passed': self.passed,
            'failed_gate': self.failed_gate,
            'reason': self.reason,
            'verdicts': [
                {
                    'gate_name': v.gate_name,
                    'result': v.result.value,
                    'reason': v.reason,
                    'confidence': v.confidence,
                    'evidence': v.evidence,
                    'override_eligible': v.override_eligible,
                    'processing_time_ms': v.processing_time_ms,
                    'metadata': v.metadata,
                }
                for v in self.verdicts
            ],
            'total_time_ms': self.total_time_ms,
            'override_eligible': self.override_eligible,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }
