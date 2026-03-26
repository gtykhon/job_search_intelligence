"""
Smart AI Router for Claude and Local Llama Integration

Routes AI requests intelligently between providers based on:
- Task complexity
- Provider availability
- Cost optimization
- Performance metrics

Includes circuit breaker pattern for failed providers.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class AIProvider(Enum):
    CLAUDE = "claude"
    LLAMA_LOCAL = "llama_local"


class TaskComplexity(Enum):
    SIMPLE = "simple"      # Basic text processing, keyword extraction
    MEDIUM = "medium"      # Analysis, summarization, skill matching
    COMPLEX = "complex"    # Deep analysis, reasoning, job matching
    CREATIVE = "creative"  # Resume optimization, cover letter generation


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Provider is down, skip it
    HALF_OPEN = "half_open"  # Testing if provider recovered


@dataclass
class AIRequest:
    """AI processing request with metadata"""
    prompt: str
    task_type: str
    complexity: TaskComplexity = TaskComplexity.MEDIUM
    max_tokens: int = 1000
    temperature: float = 0.2
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Job search specific fields
    job_id: Optional[str] = None
    resume_id: Optional[str] = None
    operation: Optional[str] = None


@dataclass
class AIResponse:
    """AI processing response with performance metrics"""
    content: str
    provider: AIProvider
    model: str
    tokens_used: int
    processing_time: float
    cost_estimate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Job search specific fields
    confidence_score: Optional[float] = None
    extracted_skills: Optional[List[str]] = None
    relevance_score: Optional[float] = None


@dataclass
class ProviderConfig:
    """Configuration for AI provider"""
    enabled: bool = True
    priority: int = 1
    max_tokens_per_minute: int = 10000
    max_requests_per_minute: int = 60
    cost_per_token: float = 0.0
    timeout: int = 30
    retry_attempts: int = 3
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None


class CircuitBreaker:
    """Simple circuit breaker for AI provider resilience."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0.0

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def record_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN -- allow one attempt


class RateLimiter:
    """Token bucket rate limiter for AI providers"""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            current_time = time.time()
            self.requests = [
                req_time for req_time in self.requests
                if req_time > current_time - self.time_window
            ]
            if len(self.requests) >= self.max_requests:
                return False
            self.requests.append(current_time)
            return True


class SmartAIRouter:
    """
    Intelligent AI provider routing with fallbacks and performance optimization.

    Features:
    - Multi-provider support (Claude API, Local Llama via HTTP)
    - Automatic provider selection based on task complexity
    - Rate limiting and cost optimization
    - Circuit breaker pattern for failed providers
    - Performance monitoring and adaptive routing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.providers: Dict[AIProvider, ProviderConfig] = {}
        self.provider_stats: Dict[AIProvider, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[AIProvider, CircuitBreaker] = {}
        self.rate_limiters: Dict[AIProvider, RateLimiter] = {}
        self.logger = logging.getLogger(__name__)

        self._http_session = None
        self._claude_client = None

        self._initialize_providers()

        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'cost_total': 0.0,
            'provider_distribution': {},
        }

    async def initialize(self):
        """Initialize AI router resources."""
        try:
            import aiohttp
            connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300, use_dns_cache=True)
            self._http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=60),
            )
        except ImportError:
            self.logger.warning("aiohttp not installed -- local Llama provider unavailable")

        if AIProvider.CLAUDE in self.providers:
            claude_config = self.providers[AIProvider.CLAUDE]
            if claude_config.api_key:
                try:
                    from anthropic import AsyncAnthropic
                    self._claude_client = AsyncAnthropic(api_key=claude_config.api_key)
                except ImportError:
                    self.logger.warning("anthropic SDK not installed -- Claude provider unavailable")

        self.logger.info("AI Router initialized successfully")

    async def cleanup(self):
        """Cleanup AI router resources."""
        if self._http_session:
            await self._http_session.close()
        if self._claude_client:
            await self._claude_client.close()
        self.logger.info("AI Router cleanup completed")

    def _initialize_providers(self):
        """Initialize AI providers with configurations."""
        # Claude configuration
        claude_config = self.config.get('claude', {})
        api_key = claude_config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            self.providers[AIProvider.CLAUDE] = ProviderConfig(
                enabled=claude_config.get('enabled', True),
                priority=1,
                max_tokens_per_minute=8000,
                max_requests_per_minute=50,
                cost_per_token=0.000015,
                timeout=30,
                retry_attempts=3,
                api_key=api_key,
                model_name=claude_config.get('model', 'claude-sonnet-4-20250514'),
            )
            self.circuit_breakers[AIProvider.CLAUDE] = CircuitBreaker(
                failure_threshold=3, recovery_timeout=60,
            )

        # Local Llama configuration
        llama_config = self.config.get('llama', {})
        if llama_config.get('enabled', False):
            self.providers[AIProvider.LLAMA_LOCAL] = ProviderConfig(
                enabled=True,
                priority=2,
                max_tokens_per_minute=50000,
                max_requests_per_minute=100,
                cost_per_token=0.0,
                timeout=60,
                retry_attempts=2,
                endpoint=llama_config.get('endpoint', 'http://localhost:11434'),
                model_name=llama_config.get('model', 'llama3.1:8b'),
            )
            self.circuit_breakers[AIProvider.LLAMA_LOCAL] = CircuitBreaker(
                failure_threshold=5, recovery_timeout=30,
            )

        for provider in self.providers:
            self.provider_stats[provider] = {
                'requests': 0, 'successful': 0, 'failed': 0,
                'average_time': 0.0, 'total_cost': 0.0,
            }
            config = self.providers[provider]
            self.rate_limiters[provider] = RateLimiter(
                max_requests=config.max_requests_per_minute,
                time_window=60,
            )

    async def generate_content(self, prompt: str, task_type: str = "general",
                               complexity: TaskComplexity = TaskComplexity.MEDIUM,
                               max_tokens: int = 1000) -> str:
        """Simplified interface -- generate content and return text."""
        request = AIRequest(
            prompt=prompt,
            task_type=task_type,
            complexity=complexity,
            max_tokens=max_tokens,
        )
        response = await self.process_request(request)
        return response.content

    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process AI request with intelligent provider routing."""
        start_time = time.time()

        selected_provider = await self._select_provider(request)
        if not selected_provider:
            raise RuntimeError("No available AI providers")

        if not await self.rate_limiters[selected_provider].acquire():
            fallback = await self._select_fallback_provider(request, selected_provider)
            if fallback:
                selected_provider = fallback
            else:
                raise RuntimeError(f"Rate limited on {selected_provider.value}, no fallback available")

        try:
            response = await self._process_with_provider(request, selected_provider)
            processing_time = time.time() - start_time
            self._update_metrics(selected_provider, True, processing_time, response.tokens_used)
            return response
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_metrics(selected_provider, False, processing_time, 0)
            self.circuit_breakers[selected_provider].record_failure()

            fallback = await self._select_fallback_provider(request, selected_provider)
            if fallback:
                self.logger.warning("Trying fallback %s after %s failed", fallback.value, selected_provider.value)
                return await self._process_with_provider(request, fallback)

            raise RuntimeError(f"AI processing failed: {e}")

    async def _select_provider(self, request: AIRequest) -> Optional[AIProvider]:
        available = []
        for provider, config in self.providers.items():
            if not config.enabled:
                continue
            if not self.circuit_breakers[provider].can_execute():
                continue
            if self._is_provider_suitable(provider, request):
                available.append((provider, config.priority))

        if not available:
            return None

        available.sort(key=lambda x: (x[1], self.provider_stats[x[0]]['average_time']))
        return available[0][0]

    async def _select_fallback_provider(self, request: AIRequest,
                                        failed: AIProvider) -> Optional[AIProvider]:
        for provider, config in self.providers.items():
            if provider == failed or not config.enabled:
                continue
            if self.circuit_breakers[provider].can_execute():
                return provider
        return None

    def _is_provider_suitable(self, provider: AIProvider, request: AIRequest) -> bool:
        if request.complexity == TaskComplexity.SIMPLE:
            if provider == AIProvider.LLAMA_LOCAL:
                return True
            return AIProvider.LLAMA_LOCAL not in self.providers
        if request.complexity in (TaskComplexity.COMPLEX, TaskComplexity.CREATIVE):
            return provider == AIProvider.CLAUDE
        return True

    async def _process_with_provider(self, request: AIRequest, provider: AIProvider) -> AIResponse:
        if provider == AIProvider.CLAUDE:
            return await self._process_with_claude(request)
        elif provider == AIProvider.LLAMA_LOCAL:
            return await self._process_with_llama(request)
        raise ValueError(f"Unsupported provider: {provider}")

    async def _process_with_claude(self, request: AIRequest) -> AIResponse:
        if not self._claude_client:
            raise RuntimeError("Claude client not initialized")

        start = time.time()
        response = await self._claude_client.messages.create(
            model=self.providers[AIProvider.CLAUDE].model_name,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}],
        )
        processing_time = time.time() - start
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        self.circuit_breakers[AIProvider.CLAUDE].record_success()

        return AIResponse(
            content=response.content[0].text,
            provider=AIProvider.CLAUDE,
            model=self.providers[AIProvider.CLAUDE].model_name,
            tokens_used=tokens_used,
            processing_time=processing_time,
            cost_estimate=tokens_used * self.providers[AIProvider.CLAUDE].cost_per_token,
        )

    async def _process_with_llama(self, request: AIRequest) -> AIResponse:
        if not self._http_session:
            raise RuntimeError("HTTP session not initialized")

        import aiohttp

        llama_config = self.providers[AIProvider.LLAMA_LOCAL]
        start = time.time()

        payload = {
            "model": llama_config.model_name,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        async with self._http_session.post(
            f"{llama_config.endpoint}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=llama_config.timeout),
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Llama HTTP error {response.status}: {error_text}")

            result = await response.json()
            processing_time = time.time() - start
            content = result.get('response', '')
            if not content:
                raise RuntimeError("Empty response from Llama")

            tokens_used = len(request.prompt.split()) + len(content.split())

            self.circuit_breakers[AIProvider.LLAMA_LOCAL].record_success()

            return AIResponse(
                content=content,
                provider=AIProvider.LLAMA_LOCAL,
                model=llama_config.model_name,
                tokens_used=tokens_used,
                processing_time=processing_time,
                cost_estimate=0.0,
            )

    def _update_metrics(self, provider: AIProvider, success: bool,
                        processing_time: float, tokens_used: int):
        stats = self.provider_stats[provider]
        stats['requests'] += 1
        if success:
            stats['successful'] += 1
            if stats['average_time'] == 0:
                stats['average_time'] = processing_time
            else:
                stats['average_time'] = 0.9 * stats['average_time'] + 0.1 * processing_time
            stats['total_cost'] += tokens_used * self.providers[provider].cost_per_token
        else:
            stats['failed'] += 1

        self.performance_metrics['total_requests'] += 1
        if success:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1

    def get_performance_report(self) -> Dict[str, Any]:
        total = self.performance_metrics['total_requests']
        return {
            'global_metrics': {
                **self.performance_metrics,
                'success_rate': self.performance_metrics['successful_requests'] / max(total, 1) * 100,
            },
            'provider_stats': self.provider_stats,
            'circuit_breaker_states': {
                p.value: cb.state.value for p, cb in self.circuit_breakers.items()
            },
        }

    # -- Job search convenience methods --

    async def extract_job_skills(self, job_description: str) -> List[str]:
        request = AIRequest(
            prompt=f"Extract technical skills from this job description as a JSON list:\n\n{job_description}",
            task_type="skill_extraction",
            complexity=TaskComplexity.SIMPLE,
            max_tokens=500,
            temperature=0.1,
        )
        response = await self.process_request(request)
        try:
            import json
            skills = json.loads(response.content)
            return skills if isinstance(skills, list) else []
        except Exception:
            return [s.strip() for s in response.content.split(',')]

    async def calculate_job_relevance(self, resume_text: str, job_description: str) -> float:
        request = AIRequest(
            prompt=f"Score resume-job match (0.0-1.0):\n\nRESUME:\n{resume_text[:2000]}\n\nJOB:\n{job_description[:2000]}\n\nScore:",
            task_type="relevance_scoring",
            complexity=TaskComplexity.MEDIUM,
            max_tokens=50,
            temperature=0.1,
        )
        response = await self.process_request(request)
        try:
            return max(0.0, min(1.0, float(response.content.strip())))
        except Exception:
            return 0.5


# -- Singleton --

_router: Optional[SmartAIRouter] = None


def get_smart_ai_router(config: Optional[Dict[str, Any]] = None) -> SmartAIRouter:
    """Get or create the global AI router."""
    global _router
    if _router is None:
        _router = SmartAIRouter(config=config)
    return _router
