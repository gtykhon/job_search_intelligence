# Enhanced Universal Guidelines for Robust Python Codebases

A comprehensive guide for building maintainable, scalable, and production-ready Python applications based on proven architectural patterns, real-world lessons learned, and enterprise-grade best practices.

*Updated with lessons learned from complex production systems including the Telegram Knowledge Base Extractor*

## 📋 Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [Configuration Management](#2-configuration-management)
3. [Module Design Patterns](#3-module-design-patterns)
4. [Error Handling Strategy](#4-error-handling-strategy)
5. [Async Programming](#5-async-programming)
6. [Data Structures](#6-data-structures)
7. [Resource Management](#7-resource-management) **🆕 ENHANCED**
8. [AI Integration Patterns](#8-ai-integration-patterns) **🆕 NEW**
9. [Performance Optimization](#9-performance-optimization) **🆕 ENHANCED**
10. [Testing Strategy](#10-testing-strategy)
11. [Documentation Standards](#11-documentation-standards)
12. [Security Practices](#12-security-practices)
13. [Monitoring & Observability](#13-monitoring--observability) **🆕 NEW**
14. [Task Scheduler Integration & OS-Specific Deployment](#14-task-scheduler-integration--os-specific-deployment) **🆕 NEW**
15. [Deployment Considerations](#15-deployment-considerations)

---

## 1. Project Architecture

### 📁 Enhanced Directory Structure

```
project-name/
├── main.py                    # Application entry point with graceful shutdown
├── requirements.txt           # Dependencies with security scanning
├── requirements-dev.txt       # Development dependencies
├── .env.template             # Environment variable template
├── .gitignore                # Comprehensive Git ignore rules
├── README.md                 # Project documentation
├── pyproject.toml            # Modern Python project configuration
├── src/                      # Source code
│   ├── __init__.py          # Package initialization
│   ├── config/              # 🆕 Configuration management
│   │   ├── __init__.py     # Config access and validation
│   │   ├── validation.py   # Configuration validation
│   │   └── environments.py # Environment-specific configs
│   ├── core/               # Core business logic
│   │   ├── __init__.py    # Core component registry
│   │   ├── application.py # Main application class
│   │   └── services/      # Business services
│   ├── resources/          # 🆕 Resource management
│   │   ├── __init__.py    # Resource manager exports
│   │   ├── manager.py     # Centralized resource manager
│   │   ├── database.py    # Database connection pooling
│   │   ├── session.py     # Session management
│   │   └── cleanup.py     # Resource cleanup utilities
│   ├── utils/              # Shared utilities
│   │   ├── __init__.py    # Utility exports
│   │   ├── error_handling.py      # 🆕 Comprehensive error handling
│   │   ├── async_helpers.py       # 🆕 Async/sync integration
│   │   ├── conflict_prevention.py # 🆕 Resource conflict prevention
│   │   ├── duplicate_prevention.py # 🆕 Deduplication systems
│   │   ├── performance_monitor.py # 🆕 Performance monitoring
│   │   └── logging_config.py      # 🆕 Structured logging
│   ├── integrations/       # 🆕 External service integrations
│   │   ├── __init__.py    # Integration registry
│   │   ├── ai/            # AI service integrations
│   │   ├── databases/     # Database integrations
│   │   └── notifications/ # Notification services
│   └── storage/            # Data persistence layer
│       ├── __init__.py    # Storage abstractions
│       ├── base.py        # Base storage classes
│       └── backends/      # Specific storage implementations
├── data/                   # Application data
│   ├── raw/               # Raw input data
│   ├── processed/         # Processed data
│   ├── exports/           # Export files
│   ├── sessions/          # 🆕 Session file isolation
│   ├── locks/             # 🆕 File lock management
│   ├── cache/             # 🆕 Performance caching
│   └── backups/           # 🆕 Automated backups
├── logs/                   # Application logs
│   ├── application/       # Main application logs
│   ├── resources/         # 🆕 Resource management logs
│   ├── performance/       # 🆕 Performance metrics
│   └── errors/            # 🆕 Error tracking logs
├── tests/                  # Test suite
│   ├── __init__.py       # Test package
│   ├── conftest.py       # Pytest configuration
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── performance/      # 🆕 Performance tests
│   ├── resources/        # 🆕 Resource management tests
│   └── fixtures/         # Test fixtures and data
├── docs/                   # Documentation
│   ├── api.md            # API documentation
│   ├── setup.md          # Setup guide
│   ├── architecture.md   # 🆕 Architecture documentation
│   ├── troubleshooting.md # Troubleshooting guide
│   └── performance.md    # 🆕 Performance optimization guide
└── scripts/                # Utility scripts
    ├── setup.py           # Environment setup
    ├── diagnose.py        # 🆕 System diagnostics
    ├── cleanup.py         # 🆕 Resource cleanup
    ├── performance_check.py # 🆕 Performance monitoring
    └── health_check.py    # 🆕 Health monitoring
```

### 🏗️ Enhanced Architectural Principles

#### **Resource-Centric Architecture**
```python
# ✅ Centralized resource management prevents conflicts
class ResourceManager:
    def __init__(self):
        self.db_pool = DatabaseConnectionPool()
        self.session_manager = SessionManager()
        self.cache_manager = CacheManager()
        self.conflict_prevention = ConflictPrevention()
    
    async def initialize(self):
        """Initialize all resources with dependency order"""
        await self.conflict_prevention.setup()
        await self.db_pool.initialize()
        await self.session_manager.initialize()
        await self.cache_manager.initialize()

# ❌ Avoid: Each component managing its own resources
class BadProcessor:
    def __init__(self):
        self.db = sqlite3.connect("app.db")  # Creates conflicts
        self.session = requests.Session()   # No cleanup
```

#### **Dependency Injection with Resource Sharing**
```python
class Application:
    def __init__(self, config: Config):
        self.config = config
        self.resource_manager = ResourceManager()
        
        # Inject shared resources to prevent conflicts
        self.extractor = TelegramExtractor(
            config=config,
            db_pool=self.resource_manager.db_pool,
            session_manager=self.resource_manager.session_manager
        )
        
        self.processor = AIProcessor(
            config=config,
            cache_manager=self.resource_manager.cache_manager
        )
    
    async def startup(self):
        """Startup sequence with proper resource initialization"""
        await self.resource_manager.initialize()
        await self.extractor.initialize()
        await self.processor.initialize()
```

#### **Event-Driven Architecture with Background Processing**
```python
from dataclasses import dataclass
from typing import Any, Dict
import asyncio

@dataclass
class Event:
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.background_queue = asyncio.Queue()
        self.running = False
    
    async def publish(self, event: Event, background: bool = False):
        """Publish event with optional background processing"""
        if background:
            await self.background_queue.put(event)
        else:
            await self._process_event(event)
    
    async def _background_processor(self):
        """Background event processing to prevent blocking"""
        while self.running:
            try:
                event = await asyncio.wait_for(
                    self.background_queue.get(), timeout=1.0
                )
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
```

---

## 2. Configuration Management

### 🔧 Enhanced Configuration Architecture

#### **Hierarchical Configuration with Validation**
```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    host: str
    port: int = 5432
    database: str = "myapp"
    username: str = ""
    password: str = ""
    pool_size: int = 10
    pool_timeout: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        if not self.username:
            raise ValueError("Database username is required")
        if self.pool_size < 1 or self.pool_size > 100:
            raise ValueError("Pool size must be between 1 and 100")
    
    def get_connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class AIConfig:
    provider: str = "claude"  # claude, openai, local
    api_key: str = ""
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 1000
    temperature: float = 0.2
    timeout: int = 30
    max_retries: int = 3
    fallback_enabled: bool = True
    
    # Local AI configuration
    local_endpoint: str = "http://localhost:11434"
    local_model: str = "llama2"
    
    def __post_init__(self):
        if self.provider == "claude" and not self.api_key.startswith("sk-ant-"):
            raise ValueError("Invalid Claude API key format")
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")

@dataclass
class ResourceConfig:
    max_database_connections: int = 10
    connection_timeout: int = 30
    cleanup_interval: int = 300  # seconds
    session_timeout: int = 3600
    cache_ttl: int = 3600
    background_workers: int = 2
    
    def __post_init__(self):
        if self.max_database_connections < 1:
            raise ValueError("Must have at least 1 database connection")

@dataclass
class MonitoringConfig:
    enabled: bool = True
    metrics_interval: int = 60
    health_check_interval: int = 30
    performance_monitoring: bool = True
    notification_enabled: bool = False
    notification_webhook: str = ""

@dataclass
class AppConfig:
    environment: Environment
    debug: bool = False
    log_level: str = "INFO"
    data_directory: Path = Path("data")
    
    # Component configurations
    database: DatabaseConfig
    ai: AIConfig
    resources: ResourceConfig
    monitoring: MonitoringConfig
    
    def __post_init__(self):
        self.data_directory.mkdir(parents=True, exist_ok=True)
        
        # Environment-specific validations
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("Debug mode not allowed in production")
            if self.log_level == "DEBUG":
                raise ValueError("Debug logging not recommended in production")
    
    def validate(self) -> List[str]:
        """Comprehensive configuration validation"""
        errors = []
        
        # Database validation
        try:
            self.database.__post_init__()
        except ValueError as e:
            errors.append(f"Database config: {e}")
        
        # AI validation
        try:
            self.ai.__post_init__()
        except ValueError as e:
            errors.append(f"AI config: {e}")
        
        # Resource validation
        try:
            self.resources.__post_init__()
        except ValueError as e:
            errors.append(f"Resource config: {e}")
        
        # Environment-specific checks
        if self.environment == Environment.PRODUCTION:
            if not self.ai.api_key:
                errors.append("AI API key required in production")
            if not self.monitoring.enabled:
                errors.append("Monitoring should be enabled in production")
        
        return errors
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'AppConfig':
        """Load configuration from environment variables"""
        if env_file:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        # Parse environment
        env = Environment(os.getenv('ENVIRONMENT', 'development'))
        
        # Load component configs
        database_config = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'myapp'),
            username=os.getenv('DB_USER', ''),
            password=os.getenv('DB_PASSWORD', ''),
            pool_size=int(os.getenv('DB_POOL_SIZE', 10))
        )
        
        ai_config = AIConfig(
            provider=os.getenv('AI_PROVIDER', 'claude'),
            api_key=os.getenv('AI_API_KEY', ''),
            model=os.getenv('AI_MODEL', 'claude-3-sonnet-20240229'),
            max_tokens=int(os.getenv('AI_MAX_TOKENS', 1000)),
            temperature=float(os.getenv('AI_TEMPERATURE', 0.2))
        )
        
        resource_config = ResourceConfig(
            max_database_connections=int(os.getenv('MAX_DB_CONNECTIONS', 10)),
            cleanup_interval=int(os.getenv('CLEANUP_INTERVAL', 300)),
            background_workers=int(os.getenv('BACKGROUND_WORKERS', 2))
        )
        
        monitoring_config = MonitoringConfig(
            enabled=os.getenv('MONITORING_ENABLED', 'true').lower() == 'true',
            performance_monitoring=os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
        )
        
        return cls(
            environment=env,
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            data_directory=Path(os.getenv('DATA_DIRECTORY', 'data')),
            database=database_config,
            ai=ai_config,
            resources=resource_config,
            monitoring=monitoring_config
        )

# Global configuration management
_config: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
        # Validate configuration on first access
        errors = _config.validate()
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    return _config

def reset_config():
    """Reset configuration (useful for testing)"""
    global _config
    _config = None
```

---

## 3. Module Design Patterns

### 🔨 Enhanced Abstract Base Classes

#### **Resource-Aware Base Classes**
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class ProcessingResult:
    status: ProcessingStatus
    data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = None

class BaseResourceAwareComponent(ABC):
    """
    Base class for components that need resource management
    """
    
    def __init__(self, config: Any, resource_manager: 'ResourceManager' = None):
        self.config = config
        self.resource_manager = resource_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_initialized = False
        self._shutdown_event = asyncio.Event()
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize component with resource dependencies"""
        pass
    
    @abstractmethod
    async def process(self, data: Any) -> ProcessingResult:
        """Process data with resource-aware error handling"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up component resources"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Component health check"""
        return {
            'component': self.__class__.__name__,
            'initialized': self._is_initialized,
            'healthy': True,
            'timestamp': datetime.now().isoformat()
        }
    
    @property
    def is_initialized(self) -> bool:
        return self._is_initialized
    
    def signal_shutdown(self):
        """Signal component to prepare for shutdown"""
        self._shutdown_event.set()

class BaseProcessor(BaseResourceAwareComponent):
    """Enhanced base processor with resource management"""
    
    def __init__(self, config: Any, resource_manager: 'ResourceManager' = None):
        super().__init__(config, resource_manager)
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'average_time': 0.0
        }
    
    async def process_batch(self, data_list: List[Any]) -> List[ProcessingResult]:
        """Process multiple items with resource-aware batching"""
        results = []
        batch_size = getattr(self.config, 'batch_size', 10)
        
        # Process in batches to manage resource usage
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            
            # Check for shutdown signal
            if self._shutdown_event.is_set():
                break
            
            # Process batch concurrently
            batch_tasks = [self.process(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions and update stats
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(ProcessingResult(
                        status=ProcessingStatus.FAILED,
                        error_message=str(result)
                    ))
                    self.processing_stats['failed'] += 1
                else:
                    results.append(result)
                    if result.status == ProcessingStatus.COMPLETED:
                        self.processing_stats['successful'] += 1
                    else:
                        self.processing_stats['failed'] += 1
                
                self.processing_stats['total_processed'] += 1
            
            # Yield control between batches
            await asyncio.sleep(0.01)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        total = self.processing_stats['total_processed']
        success_rate = (self.processing_stats['successful'] / total * 100) if total > 0 else 0
        
        return {
            **self.processing_stats,
            'success_rate': success_rate,
            'component': self.__class__.__name__
        }
```

### 🔌 Enhanced Plugin System

#### **Resource-Aware Plugin Registry**
```python
class PluginRegistry:
    def __init__(self, resource_manager: 'ResourceManager'):
        self.resource_manager = resource_manager
        self._plugins: Dict[str, Type[BaseResourceAwareComponent]] = {}
        self._instances: Dict[str, BaseResourceAwareComponent] = {}
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def register(self, name: str, plugin_class: Type[BaseResourceAwareComponent], 
                 metadata: Dict[str, Any] = None):
        """Register a plugin class with metadata"""
        self._plugins[name] = plugin_class
        self._plugin_metadata[name] = metadata or {}
        self.logger.debug(f"Registered plugin: {name}")
    
    async def get_plugin(self, name: str, config: Any) -> BaseResourceAwareComponent:
        """Get or create plugin instance with resource injection"""
        if name not in self._instances:
            if name not in self._plugins:
                raise ValueError(f"Unknown plugin: {name}")
            
            # Create instance with resource manager
            self._instances[name] = self._plugins[name](
                config=config,
                resource_manager=self.resource_manager
            )
            
            # Initialize the plugin
            await self._instances[name].initialize()
        
        return self._instances[name]
    
    async def cleanup_all(self):
        """Clean up all plugin instances"""
        for name, instance in self._instances.items():
            try:
                await instance.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up plugin {name}: {e}")
        
        self._instances.clear()
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List available plugins with metadata"""
        return [
            {
                'name': name,
                'class': plugin_class.__name__,
                'metadata': self._plugin_metadata.get(name, {}),
                'initialized': name in self._instances
            }
            for name, plugin_class in self._plugins.items()
        ]

# Auto-registration decorator
def register_plugin(name: str, metadata: Dict[str, Any] = None):
    """Decorator to auto-register plugins"""
    def decorator(cls):
        # Store registration info for later
        cls._plugin_name = name
        cls._plugin_metadata = metadata or {}
        return cls
    return decorator

# Usage
@register_plugin('email_processor', metadata={'version': '1.0', 'category': 'communication'})
class EmailProcessor(BaseProcessor):
    async def initialize(self) -> bool:
        # Use injected resource manager
        self.email_client = await self.resource_manager.get_email_client()
        self._is_initialized = True
        return True
    
    async def process(self, email_data: Dict) -> ProcessingResult:
        # Implementation with resource-aware processing
        pass
```

---

## 4. Error Handling Strategy

### 🚨 Advanced Error Handling Architecture

#### **Comprehensive Exception Hierarchy**
```python
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
import asyncio

class AppError(Exception):
    """Base application exception with context and retry information"""
    def __init__(self, message: str, error_code: str = None, 
                 context: Dict[str, Any] = None, retryable: bool = False):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.retryable = retryable
        self.timestamp = datetime.now()
        self.traceback_info = traceback.format_exc()

class ResourceError(AppError):
    """Resource-related errors (database, connections, etc.)"""
    def __init__(self, message: str, resource_type: str, resource_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.retryable = True  # Most resource errors are retryable

class ConfigurationError(AppError):
    """Configuration-related errors"""
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, retryable=False, **kwargs)  # Config errors usually not retryable
        self.config_key = config_key

class ProcessingError(AppError):
    """Data processing errors"""
    def __init__(self, message: str, processor: str = None, data_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.processor = processor
        self.data_id = data_id

class ExternalServiceError(AppError):
    """External service communication errors"""
    def __init__(self, message: str, service_name: str, status_code: int = None, 
                 response_body: str = None, **kwargs):
        super().__init__(message, retryable=True, **kwargs)
        self.service_name = service_name
        self.status_code = status_code
        self.response_body = response_body

class RateLimitError(ExternalServiceError):
    """Rate limiting errors with retry information"""
    def __init__(self, service_name: str, retry_after: int = None, **kwargs):
        super().__init__(f"Rate limit exceeded for {service_name}", service_name, **kwargs)
        self.retry_after = retry_after
        self.retryable = True

class DuplicateError(AppError):
    """Duplicate data detection"""
    def __init__(self, message: str, duplicate_id: str = None, original_id: str = None, **kwargs):
        super().__init__(message, retryable=False, **kwargs)
        self.duplicate_id = duplicate_id
        self.original_id = original_id
```

#### **Smart Retry Mechanism with Circuit Breaker**
```python
import asyncio
import time
from functools import wraps
from typing import Union, Type, Tuple, Callable, Any
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker pattern for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise ExternalServiceError("Circuit breaker is OPEN")
        
        try:
            result = func()
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

def retry_with_circuit_breaker(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    circuit_breaker: CircuitBreaker = None
):
    """Advanced retry decorator with circuit breaker and exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    # Check circuit breaker if provided
                    if circuit_breaker and circuit_breaker.state == CircuitState.OPEN:
                        if not circuit_breaker._should_attempt_reset():
                            raise ExternalServiceError("Circuit breaker is OPEN")
                        circuit_breaker.state = CircuitState.HALF_OPEN
                    
                    # Execute function
                    result = await func(*args, **kwargs)
                    
                    # Reset circuit breaker on success
                    if circuit_breaker:
                        circuit_breaker._on_success()
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # Update circuit breaker on failure
                    if circuit_breaker:
                        circuit_breaker._on_failure()
                    
                    # Check if we should retry
                    if not getattr(e, 'retryable', True):
                        raise  # Don't retry non-retryable errors
                    
                    if attempt == max_attempts - 1:
                        raise  # Last attempt, re-raise
                    
                    # Calculate delay with jitter
                    wait_time = delay * (backoff ** attempt)
                    jitter = wait_time * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)
                    actual_wait = wait_time + jitter
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {actual_wait:.2f}s: {e}",
                        extra={'exception': str(e), 'attempt': attempt + 1}
                    )
                    
                    await asyncio.sleep(actual_wait)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar implementation for sync functions
            pass
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
```

#### **Error Context and Autonomous Debugging**
```python
from contextlib import asynccontextmanager
import inspect
from typing import Generator, Any

@asynccontextmanager
async def error_context(operation: str, **context) -> Generator[None, None, None]:
    """Enhanced error context with autonomous debugging capabilities"""
    start_time = time.time()
    operation_id = f"{operation}_{int(time.time())}"
    
    # Enhanced context with call stack information
    frame = inspect.currentframe().f_back
    caller_info = {
        'file': frame.f_code.co_filename,
        'function': frame.f_code.co_name,
        'line': frame.f_lineno
    }
    
    full_context = {
        'operation_id': operation_id,
        'operation': operation,
        'caller_info': caller_info,
        **context
    }
    
    try:
        logger.info(f"Starting {operation}", extra=full_context)
        yield
        
        execution_time = time.time() - start_time
        logger.info(
            f"Completed {operation} in {execution_time:.2f}s", 
            extra={**full_context, 'execution_time': execution_time}
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Enhanced error information
        error_info = {
            **full_context,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'execution_time': execution_time,
            'traceback': traceback.format_exc()
        }
        
        # Autonomous debugging context
        if hasattr(e, 'context'):
            error_info['error_context'] = e.context
        
        # Add resource state information
        if 'resource_manager' in context:
            try:
                resource_state = await context['resource_manager'].get_state()
                error_info['resource_state'] = resource_state
            except:
                pass
        
        logger.error(f"Failed {operation} after {execution_time:.2f}s", extra=error_info)
        
        # Enhance exception with context if it's our custom exception
        if isinstance(e, AppError):
            e.context.update(error_info)
        else:
            # Wrap in our exception type
            raise ProcessingError(
                f"{operation} failed: {e}",
                context=error_info
            ) from e

# Usage with resource awareness
async def process_messages_with_context(messages: List[Dict], resource_manager):
    async with error_context(
        "message_processing", 
        message_count=len(messages),
        resource_manager=resource_manager
    ):
        results = []
        for message in messages:
            async with error_context(
                "single_message_processing",
                message_id=message.get('id'),
                message_channel=message.get('channel')
            ):
                result = await process_single_message(message)
                results.append(result)
        
        return results
```

---

## 5. Async Programming

### ⚡ Enhanced Async Patterns

#### **Resource-Aware Async Context Managers**
```python
import asyncio
import aiofiles
from typing import AsyncGenerator, Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

class AsyncResourceManager:
    """Enhanced async resource management with connection pooling"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)
        self.active_connections: Dict[str, Any] = {}
        self.connection_stats = {
            'total_created': 0,
            'total_closed': 0,
            'current_active': 0
        }
        self.logger = logging.getLogger(__name__)
    
    @asynccontextmanager
    async def get_database_connection(self, db_name: str) -> AsyncGenerator:
        """Get database connection with automatic cleanup"""
        async with self.semaphore:
            connection_id = f"{db_name}_{asyncio.current_task().get_name()}"
            
            try:
                # Create connection
                connection = await create_database_connection(db_name)
                self.active_connections[connection_id] = connection
                self.connection_stats['total_created'] += 1
                self.connection_stats['current_active'] += 1
                
                self.logger.debug(f"Created connection: {connection_id}")
                yield connection
                
            except Exception as e:
                self.logger.error(f"Database connection failed: {e}")
                raise ResourceError(
                    f"Failed to create database connection: {e}",
                    resource_type="database",
                    resource_id=connection_id
                )
            finally:
                # Cleanup connection
                if connection_id in self.active_connections:
                    connection = self.active_connections.pop(connection_id)
                    try:
                        await connection.close()
                        self.connection_stats['total_closed'] += 1
                        self.connection_stats['current_active'] -= 1
                        self.logger.debug(f"Closed connection: {connection_id}")
                    except Exception as e:
                        self.logger.error(f"Error closing connection {connection_id}: {e}")
    
    @asynccontextmanager
    async def get_session(self, session_name: str) -> AsyncGenerator:
        """Get session with conflict prevention"""
        session_file = Path(f"data/sessions/{session_name}.session")
        lock_file = Path(f"data/locks/{session_name}.lock")
        
        # Acquire file lock
        try:
            # Check if session is already locked
            if lock_file.exists():
                lock_age = time.time() - lock_file.stat().st_mtime
                if lock_age < 300:  # 5 minutes
                    raise ResourceError(
                        f"Session {session_name} is locked by another process",
                        resource_type="session",
                        resource_id=session_name
                    )
                else:
                    # Remove stale lock
                    lock_file.unlink()
            
            # Create lock file
            lock_file.touch()
            
            try:
                # Create session
                session = await create_telegram_session(session_file)
                yield session
            finally:
                # Close session
                if session:
                    await session.disconnect()
                    
        finally:
            # Remove lock file
            if lock_file.exists():
                lock_file.unlink()
    
    async def cleanup_all(self):
        """Clean up all active connections"""
        cleanup_tasks = []
        for connection_id, connection in self.active_connections.items():
            cleanup_tasks.append(self._cleanup_connection(connection_id, connection))
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.active_connections.clear()
    
    async def _cleanup_connection(self, connection_id: str, connection: Any):
        """Clean up individual connection"""
        try:
            await connection.close()
            self.logger.debug(f"Cleaned up connection: {connection_id}")
        except Exception as e:
            self.logger.error(f"Error cleaning up connection {connection_id}: {e}")

# Enhanced async data processing
class AsyncBatchProcessor:
    """Process data in batches with concurrency control and resource management"""
    
    def __init__(self, batch_size: int = 10, max_concurrent: int = 5,
                 resource_manager: AsyncResourceManager = None):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.resource_manager = resource_manager or AsyncResourceManager()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'batches_processed': 0
        }
    
    async def process_items(self, items: List[Any], 
                          processor_func: Callable) -> List[ProcessingResult]:
        """Process items in batches with error handling"""
        results = []
        
        # Split into batches
        batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
        
        # Process batches concurrently
        batch_tasks = [
            self._process_batch(batch, processor_func, batch_idx)
            for batch_idx, batch in enumerate(batches)
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Flatten results
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                # Handle batch-level failures
                results.extend([
                    ProcessingResult(
                        status=ProcessingStatus.FAILED,
                        error_message=f"Batch processing failed: {batch_result}"
                    )
                    for _ in range(self.batch_size)
                ])
            else:
                results.extend(batch_result)
        
        return results
    
    async def _process_batch(self, batch: List[Any], processor_func: Callable,
                           batch_idx: int) -> List[ProcessingResult]:
        """Process a single batch with resource management"""
        async with self.semaphore:
            async with error_context(
                "batch_processing",
                batch_idx=batch_idx,
                batch_size=len(batch)
            ):
                batch_results = []
                
                # Process items in batch
                for item in batch:
                    try:
                        result = await processor_func(item, self.resource_manager)
                        batch_results.append(result)
                        
                        if result.status == ProcessingStatus.COMPLETED:
                            self.processing_stats['successful'] += 1
                        else:
                            self.processing_stats['failed'] += 1
                            
                    except Exception as e:
                        batch_results.append(ProcessingResult(
                            status=ProcessingStatus.FAILED,
                            error_message=str(e)
                        ))
                        self.processing_stats['failed'] += 1
                    
                    self.processing_stats['total_processed'] += 1
                
                self.processing_stats['batches_processed'] += 1
                return batch_results
```

#### **Background Task Management**
```python
class BackgroundTaskManager:
    """Enhanced background task management with resource awareness"""
    
    def __init__(self, resource_manager: AsyncResourceManager):
        self.resource_manager = resource_manager
        self.tasks: Dict[str, asyncio.Task] = {}
        self.task_stats: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        self._shutdown_timeout = 30  # seconds
    
    async def start(self):
        """Start the background task manager"""
        self.running = True
        
        # Start monitoring task
        self.create_task("task_monitor", self._monitor_tasks, interval=30)
        
        self.logger.info("Background task manager started")
    
    async def stop(self):
        """Stop all background tasks gracefully"""
        self.logger.info("Stopping background task manager...")
        self.running = False
        
        # Cancel all tasks
        for name, task in self.tasks.items():
            if not task.done():
                self.logger.info(f"Cancelling task: {name}")
                task.cancel()
        
        # Wait for tasks to complete with timeout
        if self.tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.tasks.values(), return_exceptions=True),
                    timeout=self._shutdown_timeout
                )
            except asyncio.TimeoutError:
                self.logger.warning("Some tasks did not complete within shutdown timeout")
        
        self.logger.info("Background task manager stopped")
    
    def create_task(self, name: str, coro: Callable, *args, 
                   interval: Optional[int] = None, **kwargs) -> asyncio.Task:
        """Create and register a background task"""
        
        if interval:
            # Periodic task
            async def periodic_wrapper():
                while self.running:
                    try:
                        async with error_context(f"periodic_task_{name}"):
                            await coro(*args, **kwargs)
                    except Exception as e:
                        self.logger.error(f"Periodic task {name} error: {e}")
                        self._update_task_stats(name, 'error', str(e))
                    
                    # Wait for next interval or shutdown
                    try:
                        await asyncio.wait_for(
                            asyncio.Event().wait(),  # Wait forever
                            timeout=interval
                        )
                    except asyncio.TimeoutError:
                        continue  # Normal timeout, continue loop
                    except asyncio.CancelledError:
                        break  # Task cancelled
            
            task_coro = periodic_wrapper()
        else:
            # One-time task with error handling
            async def task_wrapper():
                try:
                    async with error_context(f"background_task_{name}"):
                        result = await coro(*args, **kwargs)
                        self._update_task_stats(name, 'completed', result)
                        return result
                except asyncio.CancelledError:
                    self.logger.info(f"Task {name} was cancelled")
                    self._update_task_stats(name, 'cancelled')
                    raise
                except Exception as e:
                    self.logger.error(f"Task {name} failed: {e}")
                    self._update_task_stats(name, 'failed', str(e))
                    raise
                finally:
                    # Remove from active tasks
                    self.tasks.pop(name, None)
            
            task_coro = task_wrapper()
        
        # Create and register task
        task = asyncio.create_task(task_coro)
        task.set_name(name)
        self.tasks[name] = task
        
        # Initialize task stats
        self._update_task_stats(name, 'created')
        
        self.logger.info(f"Created background task: {name}")
        return task
    
    def _update_task_stats(self, name: str, status: str, data: Any = None):
        """Update task statistics"""
        if name not in self.task_stats:
            self.task_stats[name] = {
                'created_at': datetime.now(),
                'status_history': []
            }
        
        self.task_stats[name]['status_history'].append({
            'status': status,
            'timestamp': datetime.now(),
            'data': data
        })
        self.task_stats[name]['current_status'] = status
    
    async def _monitor_tasks(self):
        """Monitor task health and performance"""
        active_count = len([t for t in self.tasks.values() if not t.done()])
        completed_count = len([t for t in self.tasks.values() if t.done() and not t.cancelled()])
        failed_count = len([t for t in self.tasks.values() if t.done() and t.exception()])
        
        self.logger.info(
            f"Task status: {active_count} active, {completed_count} completed, {failed_count} failed"
        )
        
        # Check for failed tasks and optionally restart them
        for name, task in list(self.tasks.items()):
            if task.done() and task.exception():
                exception = task.exception()
                self.logger.error(f"Task {name} failed with exception: {exception}")
                # Could implement automatic restart logic here
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get comprehensive task statistics"""
        return {
            'total_tasks': len(self.task_stats),
            'active_tasks': len([t for t in self.tasks.values() if not t.done()]),
            'task_details': self.task_stats,
            'manager_running': self.running
        }
```

---

## 7. Resource Management

### 🔐 Centralized Resource Management Architecture

#### **Database Connection Pooling with Conflict Prevention**
```python
import sqlite3
import asyncio
import threading
import time
from typing import Dict, Optional, Any, List, ContextManager
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import fcntl
import os

@dataclass
class ConnectionInfo:
    """Information about a database connection"""
    connection: Any
    created_at: datetime
    last_used: datetime
    thread_id: int
    is_busy: bool = False
    usage_count: int = 0

class DatabaseConnectionManager:
    """
    Centralized SQLite connection manager preventing locking conflicts
    
    Key features learned from TG extractor:
    1. Single connection pool for all components
    2. Proper connection cleanup and resource management
    3. Thread-safe connection handling
    4. Connection timeout and retry logic
    5. Automatic cleanup of stale connections
    """
    
    def __init__(self, max_connections: int = 10, connection_timeout: int = 30):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[str, ConnectionInfo] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = 0
        self.max_retries = 3
        self.retry_delay = 1.0
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_connection(self, db_name: str, db_path: str = None) -> ContextManager[sqlite3.Connection]:
        """Get database connection with automatic cleanup"""
        if db_path is None:
            db_path = f"data/{db_name}.db"
        
        connection_key = f"{db_name}_{threading.get_ident()}"
        
        # Periodic cleanup
        self._periodic_cleanup()
        
        try:
            # Try to get existing connection
            with self._lock:
                if connection_key in self.connections:
                    conn_info = self.connections[connection_key]
                    if not conn_info.is_busy:
                        conn_info.is_busy = True
                        conn_info.last_used = datetime.now()
                        conn_info.usage_count += 1
                        yield conn_info.connection
                        return
            
            # Create new connection with retry logic
            connection = self._create_connection_with_retry(db_name, db_path)
            
            # Store connection info
            with self._lock:
                conn_info = ConnectionInfo(
                    connection=connection,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                    thread_id=threading.get_ident(),
                    is_busy=True,
                    usage_count=1
                )
                self.connections[connection_key] = conn_info
            
            try:
                yield connection
            finally:
                # Release connection
                with self._lock:
                    if connection_key in self.connections:
                        self.connections[connection_key].is_busy = False
                        
        except Exception as e:
            self.logger.error(f"Database connection error for {db_name}: {e}")
            raise ResourceError(
                f"Failed to acquire database connection: {e}",
                resource_type="database",
                resource_id=db_name
            )
    
    def _create_connection_with_retry(self, db_name: str, db_path: str) -> sqlite3.Connection:
        """Create database connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                # Create connection with proper settings
                connection = sqlite3.connect(
                    db_path,
                    timeout=self.connection_timeout,
                    isolation_level=None,  # Autocommit mode
                    check_same_thread=False
                )
                
                # Configure for better performance and reliability
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA synchronous=NORMAL")
                connection.execute("PRAGMA temp_store=MEMORY")
                connection.execute("PRAGMA mmap_size=268435456")  # 256MB
                connection.execute(f"PRAGMA busy_timeout={int(self.connection_timeout * 1000)}")
                
                self.logger.debug(f"Created database connection for '{db_name}'")
                return connection
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < self.max_retries - 1:
                    self.logger.warning(f"Database locked, retrying in {self.retry_delay}s (attempt {attempt + 1})")
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    raise
        
        raise sqlite3.OperationalError(f"Could not acquire connection for '{db_name}' after {self.max_retries} attempts")
    
    def _periodic_cleanup(self):
        """Periodically clean up old connections"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = current_time
        
        with self._lock:
            keys_to_remove = []
            for key, conn_info in self.connections.items():
                # Remove connections that are too old or unused
                age = (datetime.now() - conn_info.created_at).total_seconds()
                idle_time = (datetime.now() - conn_info.last_used).total_seconds()
                
                if (age > 3600 or idle_time > 1800) and not conn_info.is_busy:  # 1 hour max age, 30 min idle
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                conn_info = self.connections[key]
                try:
                    conn_info.connection.close()
                    self.logger.debug(f"Cleaned up old connection: {key}")
                except:
                    pass
                del self.connections[key]
    
    def close_all_connections(self):
        """Close all database connections"""
        with self._lock:
            for conn_info in self.connections.values():
                try:
                    conn_info.connection.close()
                except:
                    pass
            self.connections.clear()
        
        self.logger.info("All database connections closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._lock:
            active_connections = len([c for c in self.connections.values() if c.is_busy])
            total_connections = len(self.connections)
            
            return {
                'total_connections': total_connections,
                'active_connections': active_connections,
                'max_connections': self.max_connections,
                'connection_details': {
                    key: {
                        'created_at': info.created_at.isoformat(),
                        'last_used': info.last_used.isoformat(),
                        'usage_count': info.usage_count,
                        'is_busy': info.is_busy
                    }
                    for key, info in self.connections.items()
                }
            }

# Global database manager
db_manager = DatabaseConnectionManager()
```

#### **Session and File Lock Management**
```python
class ConflictPrevention:
    """
    Resource conflict prevention system
    
    Prevents:
    - Database locking conflicts
    - Session file conflicts  
    - File lock conflicts
    - Event loop conflicts
    """
    
    def __init__(self, lock_directory: str = "data/locks"):
        self.lock_directory = Path(lock_directory)
        self.lock_directory.mkdir(parents=True, exist_ok=True)
        
        self._active_locks: Dict[str, Any] = {}
        self._process_id = os.getpid()
        self.logger = logging.getLogger(__name__)
    
    async def setup(self):
        """Setup conflict prevention"""
        self.logger.info("🛡️  Setting up conflict prevention...")
        
        # Clean up any orphaned locks from previous runs
        await self._cleanup_orphaned_locks()
        
        self.logger.info("✅ Conflict prevention ready")
    
    @asynccontextmanager
    async def acquire_file_lock(self, resource_name: str, lock_type: str = "exclusive"):
        """
        Acquire file lock for resource with automatic cleanup
        
        Args:
            resource_name: Name of the resource to lock
            lock_type: Type of lock (exclusive, shared)
            
        Yields:
            True if lock acquired successfully
            
        Raises:
            ResourceError: If lock cannot be acquired
        """
        lock_file = self.lock_directory / f"{resource_name}.lock"
        
        try:
            # Check if already locked by another process
            if lock_file.exists():
                if not await self._is_lock_stale(lock_file):
                    raise ResourceError(
                        f"Resource {resource_name} is locked by another process",
                        resource_type="file_lock",
                        resource_id=resource_name
                    )
                else:
                    # Remove stale lock
                    lock_file.unlink()
            
            # Create lock file with process info
            lock_info = {
                'process_id': self._process_id,
                'timestamp': datetime.now().isoformat(),
                'lock_type': lock_type,
                'resource_name': resource_name
            }
            
            with open(lock_file, 'w') as f:
                json.dump(lock_info, f)
                if hasattr(fcntl, 'flock'):  # Unix systems
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Track lock
            self._active_locks[resource_name] = {
                'lock_file': lock_file,
                'process_id': self._process_id,
                'created_at': datetime.now(),
                'lock_type': lock_type
            }
            
            self.logger.debug(f"🔒 Acquired lock: {resource_name}")
            
            try:
                yield True
            finally:
                # Release lock
                await self._release_lock(resource_name)
                
        except (IOError, OSError) as e:
            raise ResourceError(
                f"Failed to acquire lock for {resource_name}: {e}",
                resource_type="file_lock",
                resource_id=resource_name
            )
    
    async def _release_lock(self, resource_name: str):
        """Release file lock for resource"""
        if resource_name in self._active_locks:
            lock_info = self._active_locks[resource_name]
            try:
                if lock_info['lock_file'].exists():
                    lock_info['lock_file'].unlink()
                del self._active_locks[resource_name]
                self.logger.debug(f"🔓 Released lock: {resource_name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to release lock {resource_name}: {e}")
    
    async def _is_lock_stale(self, lock_file: Path, max_age_minutes: int = 30) -> bool:
        """Check if lock file is stale (from crashed process)"""
        try:
            # Check file age
            stat = lock_file.stat()
            age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            
            if age > timedelta(minutes=max_age_minutes):
                return True
            
            # Check if process is still running
            try:
                with open(lock_file, 'r') as f:
                    lock_info = json.load(f)
                    pid = lock_info.get('process_id')
                    
                    if pid:
                        # Try to check if process exists
                        os.kill(pid, 0)  # Doesn't actually kill, just checks
                        return False  # Process exists, lock is valid
                    
            except (json.JSONDecodeError, KeyError, OSError, ProcessLookupError):
                return True  # Process doesn't exist or invalid lock file
            
            return True
            
        except Exception:
            return True  # If we can't read it, consider it stale
    
    async def _cleanup_orphaned_locks(self):
        """Clean up orphaned lock files"""
        cleaned_count = 0
        for lock_file in self.lock_directory.glob("*.lock"):
            if await self._is_lock_stale(lock_file):
                try:
                    lock_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to clean orphaned lock {lock_file}: {e}")
        
        if cleaned_count > 0:
            self.logger.info(f"🗑️  Cleaned up {cleaned_count} orphaned locks")
    
    async def cleanup(self):
        """Cleanup all locks created by this process"""
        self.logger.info("🧹 Cleaning up conflict prevention...")
        
        for resource_name in list(self._active_locks.keys()):
            await self._release_lock(resource_name)
        
        self.logger.info("✅ Conflict prevention cleanup completed")

# Global conflict prevention instance
conflict_prevention = ConflictPrevention()
```

---

## 8. AI Integration Patterns

### 🤖 Smart AI Provider Management

#### **Multi-Provider AI Router with Fallbacks**
```python
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
import asyncio
import time
import logging

class AIProvider(Enum):
    CLAUDE = "claude"
    OPENAI = "openai" 
    LOCAL = "local"
    OLLAMA = "ollama"

class TaskComplexity(Enum):
    SIMPLE = "simple"      # Basic text processing
    MEDIUM = "medium"      # Analysis and summarization
    COMPLEX = "complex"    # Deep analysis and reasoning
    CREATIVE = "creative"  # Content generation

@dataclass
class AIRequest:
    prompt: str
    task_type: str
    complexity: TaskComplexity = TaskComplexity.MEDIUM
    max_tokens: int = 1000
    temperature: float = 0.2
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AIResponse:
    content: str
    provider: AIProvider
    model: str
    tokens_used: int
    processing_time: float
    cost_estimate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderConfig:
    enabled: bool = True
    priority: int = 1  # 1 = highest priority
    max_tokens_per_minute: int = 10000
    max_requests_per_minute: int = 60
    cost_per_token: float = 0.0
    timeout: int = 30
    retry_attempts: int = 3

class SmartAIRouter:
    """
    Intelligent AI provider routing with fallbacks and performance optimization
    
    Features:
    - Multi-provider support (Claude, OpenAI, Local models)
    - Automatic provider selection based on task complexity
    - Rate limiting and cost optimization
    - Circuit breaker pattern for failed providers
    - Performance monitoring and adaptive routing
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[AIProvider, ProviderConfig] = {}
        self.provider_stats: Dict[AIProvider, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[AIProvider, CircuitBreaker] = {}
        self.rate_limiters: Dict[AIProvider, 'RateLimiter'] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize providers
        self._initialize_providers()
        
        # Performance tracking
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'cost_total': 0.0,
            'provider_distribution': {}
        }
    
    def _initialize_providers(self):
        """Initialize AI providers with configurations"""
        # Claude configuration
        if self.config.get('claude_api_key'):
            self.providers[AIProvider.CLAUDE] = ProviderConfig(
                enabled=True,
                priority=1,
                max_tokens_per_minute=8000,  # Conservative rate limiting
                cost_per_token=0.0000015,    # Approximate cost
                timeout=30
            )
            self.circuit_breakers[AIProvider.CLAUDE] = CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=60
            )
        
        # OpenAI configuration
        if self.config.get('openai_api_key'):
            self.providers[AIProvider.OPENAI] = ProviderConfig(
                enabled=True,
                priority=2,
                max_tokens_per_minute=10000,
                cost_per_token=0.000002,
                timeout=30
            )
            self.circuit_breakers[AIProvider.OPENAI] = CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=60
            )
        
        # Local model configuration
        if self.config.get('local_ai_enabled'):
            self.providers[AIProvider.LOCAL] = ProviderConfig(
                enabled=True,
                priority=3,  # Lower priority for fallback
                max_tokens_per_minute=50000,  # No external rate limits
                cost_per_token=0.0,  # Free
                timeout=60  # Local models might be slower
            )
            self.circuit_breakers[AIProvider.LOCAL] = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30
            )
        
        # Initialize stats and rate limiters
        for provider in self.providers:
            self.provider_stats[provider] = {
                'requests': 0,
                'successful': 0,
                'failed': 0,
                'average_time': 0.0,
                'total_cost': 0.0
            }
            
            config = self.providers[provider]
            self.rate_limiters[provider] = RateLimiter(
                max_requests=config.max_requests_per_minute,
                time_window=60
            )
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """Process AI request with intelligent provider routing"""
        start_time = time.time()
        
        # Select best provider for this request
        selected_provider = await self._select_provider(request)
        
        if not selected_provider:
            raise ExternalServiceError("No available AI providers")
        
        # Check rate limiting
        if not await self.rate_limiters[selected_provider].acquire():
            # Try fallback provider
            fallback_provider = await self._select_fallback_provider(request, selected_provider)
            if fallback_provider:
                selected_provider = fallback_provider
            else:
                raise RateLimitError(selected_provider.value, retry_after=60)
        
        # Process request with selected provider
        try:
            response = await self._process_with_provider(request, selected_provider)
            
            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(selected_provider, True, processing_time, response.tokens_used)
            
            return response
            
        except Exception as e:
            # Update failure metrics
            processing_time = time.time() - start_time
            self._update_metrics(selected_provider, False, processing_time, 0)
            
            # Try fallback
            fallback_provider = await self._select_fallback_provider(request, selected_provider)
            if fallback_provider:
                self.logger.warning(f"Trying fallback provider {fallback_provider.value} after {selected_provider.value} failed")
                return await self.process_request(request)  # Recursive fallback
            
            raise ExternalServiceError(f"AI processing failed: {e}", selected_provider.value)
    
    async def _select_provider(self, request: AIRequest) -> Optional[AIProvider]:
        """Select best provider based on request characteristics"""
        available_providers = []
        
        for provider, config in self.providers.items():
            if not config.enabled:
                continue
            
            # Check circuit breaker
            circuit_breaker = self.circuit_breakers[provider]
            if circuit_breaker.state == CircuitState.OPEN:
                continue
            
            # Check if provider is suitable for task complexity
            if self._is_provider_suitable(provider, request):
                available_providers.append((provider, config.priority))
        
        if not available_providers:
            return None
        
        # Sort by priority and performance
        available_providers.sort(key=lambda x: (
            x[1],  # Priority
            self.provider_stats[x[0]]['average_time']  # Performance
        ))
        
        return available_providers[0][0]
    
    def _is_provider_suitable(self, provider: AIProvider, request: AIRequest) -> bool:
        """Check if provider is suitable for request"""
        provider_config = self.providers[provider]
        
        # Check token limits
        if request.max_tokens > provider_config.max_tokens_per_minute / 10:
            return False
        
        # Task complexity routing
        if request.complexity == TaskComplexity.SIMPLE and provider == AIProvider.LOCAL:
            return True  # Local models good for simple tasks
        
        if request.complexity == TaskComplexity.COMPLEX and provider in [AIProvider.CLAUDE, AIProvider.OPENAI]:
            return True  # Cloud models better for complex tasks
        
        if request.complexity == TaskComplexity.CREATIVE and provider == AIProvider.CLAUDE:
            return True  # Claude preferred for creative tasks
        
        return True  # Default to suitable
    
    async def _process_with_provider(self, request: AIRequest, provider: AIProvider) -> AIResponse:
        """Process request with specific provider"""
        if provider == AIProvider.CLAUDE:
            return await self._process_with_claude(request)
        elif provider == AIProvider.OPENAI:
            return await self._process_with_openai(request)
        elif provider == AIProvider.LOCAL:
            return await self._process_with_local(request)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _process_with_claude(self, request: AIRequest) -> AIResponse:
        """Process request with Claude"""
        import anthropic
        
        client = anthropic.AsyncAnthropic(api_key=self.config['claude_api_key'])
        
        start_time = time.time()
        
        response = await client.messages.create(
            model=self.config.get('claude_model', 'claude-3-sonnet-20240229'),
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}]
        )
        
        processing_time = time.time() - start_time
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
        return AIResponse(
            content=response.content[0].text,
            provider=AIProvider.CLAUDE,
            model=self.config.get('claude_model', 'claude-3-sonnet-20240229'),
            tokens_used=tokens_used,
            processing_time=processing_time,
            cost_estimate=tokens_used * self.providers[AIProvider.CLAUDE].cost_per_token
        )
    
    def _update_metrics(self, provider: AIProvider, success: bool, 
                       processing_time: float, tokens_used: int):
        """Update provider and global metrics"""
        # Update provider stats
        stats = self.provider_stats[provider]
        stats['requests'] += 1
        
        if success:
            stats['successful'] += 1
            # Update average time (exponential moving average)
            if stats['average_time'] == 0:
                stats['average_time'] = processing_time
            else:
                stats['average_time'] = 0.9 * stats['average_time'] + 0.1 * processing_time
            
            # Update cost
            cost = tokens_used * self.providers[provider].cost_per_token
            stats['total_cost'] += cost
            
        else:
            stats['failed'] += 1
            # Update circuit breaker
            self.circuit_breakers[provider]._on_failure()
        
        # Update global metrics
        self.performance_metrics['total_requests'] += 1
        if success:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1
        
        # Update provider distribution
        if provider.value not in self.performance_metrics['provider_distribution']:
            self.performance_metrics['provider_distribution'][provider.value] = 0
        self.performance_metrics['provider_distribution'][provider.value] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        total_requests = self.performance_metrics['total_requests']
        success_rate = (
            self.performance_metrics['successful_requests'] / total_requests * 100
            if total_requests > 0 else 0
        )
        
        return {
            'global_metrics': {
                **self.performance_metrics,
                'success_rate': success_rate
            },
            'provider_stats': self.provider_stats,
            'circuit_breaker_states': {
                provider.value: breaker.state.value
                for provider, breaker in self.circuit_breakers.items()
            },
            'provider_configs': {
                provider.value: {
                    'enabled': config.enabled,
                    'priority': config.priority,
                    'cost_per_token': config.cost_per_token
                }
                for provider, config in self.providers.items()
            }
        }

class RateLimiter:
    """Token bucket rate limiter for AI providers"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire rate limit token"""
        async with self._lock:
            current_time = time.time()
            
            # Remove old requests outside the time window
            self.requests = [req_time for req_time in self.requests 
                           if req_time > current_time - self.time_window]
            
            # Check if we can make a request
            if len(self.requests) >= self.max_requests:
                return False
            
            # Add current request
            self.requests.append(current_time)
            return True
```

---

## 9. Performance Optimization

### ⚡ Advanced Caching and Performance Monitoring

#### **Multi-Level Caching System**
```python
import asyncio
import time
import hashlib
import json
import pickle
from typing import Any, Optional, Callable, TypeVar, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum

T = TypeVar('T')

class CacheLevel(Enum):
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: int = 3600
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.created_at + self.ttl
    
    @property
    def age(self) -> float:
        return time.time() - self.created_at

class AdvancedCacheManager:
    """
    Multi-level caching with intelligent eviction and performance optimization
    
    Features:
    - Memory, disk, and Redis caching layers
    - LRU eviction with TTL support
    - Cache warming and prefetching
    - Performance metrics and optimization
    - Intelligent cache key generation
    """
    
    def __init__(self, memory_limit: int = 1000, disk_cache_dir: str = "data/cache"):
        self.memory_limit = memory_limit
        self.disk_cache_dir = Path(disk_cache_dir)
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        self._cache_lock = asyncio.Lock()
        
        # Performance metrics
        self.stats = {
            'memory_hits': 0,
            'memory_misses': 0,
            'disk_hits': 0,
            'disk_misses': 0,
            'redis_hits': 0,
            'redis_misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate deterministic cache key"""
        key_data = {
            'function': func_name,
            'args': self._serialize_args(args),
            'kwargs': self._serialize_args(kwargs)
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def _serialize_args(self, args: Union[tuple, dict]) -> Union[list, dict]:
        """Serialize arguments for cache key generation"""
        if isinstance(args, dict):
            return {k: self._serialize_single_arg(v) for k, v in args.items()}
        elif isinstance(args, (list, tuple)):
            return [self._serialize_single_arg(arg) for arg in args]
        else:
            return self._serialize_single_arg(args)
    
    def _serialize_single_arg(self, arg: Any) -> Any:
        """Serialize a single argument"""
        if hasattr(arg, '__dict__'):
            # For objects, use their dict representation
            return str(arg.__dict__)
        elif callable(arg):
            # For functions, use their name
            return arg.__name__
        else:
            return arg
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with multi-level lookup"""
        self.stats['total_requests'] += 1
        
        # Try memory cache first
        async with self._cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not entry.is_expired:
                    entry.last_accessed = time.time()
                    entry.access_count += 1
                    self.stats['memory_hits'] += 1
                    return entry.value
                else:
                    # Remove expired entry
                    del self.memory_cache[key]
        
        self.stats['memory_misses'] += 1
        
        # Try disk cache
        disk_value = await self._get_from_disk(key)
        if disk_value is not None:
            self.stats['disk_hits'] += 1
            # Promote to memory cache
            await self.set(key, disk_value, ttl=3600, promote_to_memory=True)
            return disk_value
        
        self.stats['disk_misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600, 
                  promote_to_memory: bool = True) -> None:
        """Set value in cache with intelligent placement"""
        entry = CacheEntry(
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            ttl=ttl
        )
        
        # Store in memory cache if requested and there's space
        if promote_to_memory:
            async with self._cache_lock:
                # Check if we need to evict entries
                if len(self.memory_cache) >= self.memory_limit:
                    await self._evict_lru_entries()
                
                self.memory_cache[key] = entry
        
        # Also store in disk cache for persistence
        await self._set_to_disk(key, value, ttl)
    
    async def _evict_lru_entries(self, evict_count: int = None):
        """Evict least recently used entries from memory"""
        if evict_count is None:
            evict_count = max(1, len(self.memory_cache) // 10)  # Evict 10%
        
        # Sort by last accessed time and access count
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: (x[1].last_accessed, x[1].access_count)
        )
        
        for i in range(min(evict_count, len(sorted_entries))):
            key, entry = sorted_entries[i]
            
            # Move to disk before evicting from memory
            await self._set_to_disk(key, entry.value, entry.ttl)
            del self.memory_cache[key]
            self.stats['evictions'] += 1
    
    async def _get_from_disk(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        cache_file = self.disk_cache_dir / f"{key}.cache"
        metadata_file = self.disk_cache_dir / f"{key}.meta"
        
        try:
            if cache_file.exists() and metadata_file.exists():
                # Check if expired
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                if time.time() > metadata['created_at'] + metadata['ttl']:
                    # Expired, remove files
                    cache_file.unlink()
                    metadata_file.unlink()
                    return None
                
                # Load value
                with open(cache_file, 'rb') as f:
                    value = pickle.load(f)
                
                return value
        
        except Exception as e:
            self.logger.warning(f"Error reading disk cache for {key}: {e}")
            # Clean up corrupted cache files
            for file in [cache_file, metadata_file]:
                if file.exists():
                    try:
                        file.unlink()
                    except:
                        pass
        
        return None
    
    async def _set_to_disk(self, key: str, value: Any, ttl: int):
        """Set value to disk cache"""
        cache_file = self.disk_cache_dir / f"{key}.cache"
        metadata_file = self.disk_cache_dir / f"{key}.meta"
        
        try:
            # Save value
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            
            # Save metadata
            metadata = {
                'created_at': time.time(),
                'ttl': ttl,
                'size': cache_file.stat().st_size
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)
        
        except Exception as e:
            self.logger.error(f"Error writing disk cache for {key}: {e}")
    
    def cached(self, ttl: int = 3600, key_func: Optional[Callable] = None):
        """Caching decorator with advanced features"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # For sync functions, we need to run async operations in a new loop
                # This is a simplified version - in practice, you'd want better handling
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Try to get from cache
                cached_result = loop.run_until_complete(self.get(cache_key))
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                loop.run_until_complete(self.set(cache_key, result, ttl))
                
                return result
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def warm_cache(self, warm_functions: List[Dict[str, Any]]):
        """Warm cache with frequently used data"""
        self.logger.info(f"Warming cache with {len(warm_functions)} functions")
        
        for func_info in warm_functions:
            try:
                func = func_info['function']
                args = func_info.get('args', ())
                kwargs = func_info.get('kwargs', {})
                
                # Execute function to populate cache
                if asyncio.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
                    
            except Exception as e:
                self.logger.warning(f"Cache warming failed for {func_info}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_requests = self.stats['total_requests']
        
        if total_requests > 0:
            memory_hit_rate = self.stats['memory_hits'] / total_requests * 100
            overall_hit_rate = (
                self.stats['memory_hits'] + self.stats['disk_hits']
            ) / total_requests * 100
        else:
            memory_hit_rate = 0
            overall_hit_rate = 0
        
        return {
            'cache_stats': self.stats,
            'memory_hit_rate': memory_hit_rate,
            'overall_hit_rate': overall_hit_rate,
            'memory_cache_size': len(self.memory_cache),
            'memory_usage_mb': sum(
                len(pickle.dumps(entry.value)) for entry in self.memory_cache.values()
            ) / 1024 / 1024,
            'eviction_rate': self.stats['evictions'] / max(1, total_requests) * 100
        }
    
    async def cleanup_expired(self):
        """Clean up expired cache entries"""
        # Clean memory cache
        async with self._cache_lock:
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
        
        # Clean disk cache
        for cache_file in self.disk_cache_dir.glob("*.cache"):
            metadata_file = cache_file.with_suffix('.meta')
            
            try:
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    if time.time() > metadata['created_at'] + metadata['ttl']:
                        cache_file.unlink()
                        metadata_file.unlink()
            except:
                pass

# Global cache manager
cache_manager = AdvancedCacheManager()
```

#### **Performance Monitoring and Optimization**
```python
import psutil
import time
import asyncio
from typing import Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    disk_io_read: int = 0
    disk_io_write: int = 0
    network_sent: int = 0
    network_recv: int = 0
    active_threads: int = 0
    open_files: int = 0
    
    # Application-specific metrics
    database_connections: int = 0
    cache_hit_rate: float = 0.0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    background_tasks: int = 0

class PerformanceMonitor:
    """
    Comprehensive performance monitoring with optimization recommendations
    
    Features:
    - System resource monitoring (CPU, memory, disk, network)
    - Application-specific metrics
    - Performance trend analysis
    - Automatic optimization suggestions
    - Alerting for performance degradation
    """
    
    def __init__(self, monitoring_interval: int = 60):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000  # Keep last 1000 measurements
        self.running = False
        self.monitoring_task = None
        self.logger = logging.getLogger(__name__)
        
        # Performance thresholds for alerting
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_io_high': 50 * 1024 * 1024,  # 50MB/s
            'cache_hit_rate_low': 70.0,
            'average_response_time_high': 5.0,  # 5 seconds
            'error_rate_high': 5.0  # 5%
        }
        
        # Component references for metrics collection
        self.cache_manager = None
        self.db_manager = None
        self.task_manager = None
    
    def register_components(self, cache_manager=None, db_manager=None, task_manager=None):
        """Register components for metrics collection"""
        self.cache_manager = cache_manager
        self.db_manager = db_manager
        self.task_manager = task_manager
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self.running:
            return
        
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                metrics = await self._collect_metrics()
                self._store_metrics(metrics)
                
                # Check for performance issues
                alerts = self._check_thresholds(metrics)
                if alerts:
                    await self._handle_alerts(alerts)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collect comprehensive performance metrics"""
        try:
            # System metrics
            process = psutil.Process()
            
            # CPU and memory
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # I/O metrics
            try:
                io_counters = process.io_counters()
                disk_io_read = io_counters.read_bytes
                disk_io_write = io_counters.write_bytes
            except (AttributeError, OSError):
                disk_io_read = disk_io_write = 0
            
            # Network metrics (system-wide)
            try:
                net_io = psutil.net_io_counters()
                network_sent = net_io.bytes_sent
                network_recv = net_io.bytes_recv
            except (AttributeError, OSError):
                network_sent = network_recv = 0
            
            # Process info
            active_threads = process.num_threads()
            try:
                open_files = process.num_fds()  # Unix only
            except (AttributeError, OSError):
                open_files = 0
            
            # Application-specific metrics
            cache_hit_rate = 0.0
            if self.cache_manager:
                cache_stats = self.cache_manager.get_stats()
                cache_hit_rate = cache_stats.get('overall_hit_rate', 0.0)
            
            database_connections = 0
            if self.db_manager:
                db_stats = self.db_manager.get_stats()
                database_connections = db_stats.get('active_connections', 0)
            
            background_tasks = 0
            average_response_time = 0.0
            error_rate = 0.0
            if self.task_manager:
                task_stats = self.task_manager.get_task_stats()
                background_tasks = task_stats.get('active_tasks', 0)
                # Add response time and error rate if available
            
            return PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_info.rss / 1024 / 1024,
                disk_io_read=disk_io_read,
                disk_io_write=disk_io_write,
                network_sent=network_sent,
                network_recv=network_recv,
                active_threads=active_threads,
                open_files=open_files,
                database_connections=database_connections,
                cache_hit_rate=cache_hit_rate,
                average_response_time=average_response_time,
                error_rate=error_rate,
                background_tasks=background_tasks
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return PerformanceMetrics()  # Return empty metrics on error
    
    def _store_metrics(self, metrics: PerformanceMetrics):
        """Store metrics in history with size limit"""
        self.metrics_history.append(metrics)
        
        # Maintain history size limit
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def _check_thresholds(self, metrics: PerformanceMetrics) -> List[Dict[str, Any]]:
        """Check metrics against thresholds and return alerts"""
        alerts = []
        
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'message': f"High CPU usage: {metrics.cpu_percent:.1f}%",
                'severity': 'warning',
                'value': metrics.cpu_percent,
                'threshold': self.thresholds['cpu_percent']
            })
        
        if metrics.memory_percent > self.thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'message': f"High memory usage: {metrics.memory_percent:.1f}%",
                'severity': 'warning',
                'value': metrics.memory_percent,
                'threshold': self.thresholds['memory_percent']
            })
        
        if metrics.cache_hit_rate < self.thresholds['cache_hit_rate_low']:
            alerts.append({
                'type': 'cache_hit_rate_low',
                'message': f"Low cache hit rate: {metrics.cache_hit_rate:.1f}%",
                'severity': 'info',
                'value': metrics.cache_hit_rate,
                'threshold': self.thresholds['cache_hit_rate_low']
            })
        
        return alerts
    
    async def _handle_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle performance alerts"""
        for alert in alerts:
            if alert['severity'] == 'warning':
                self.logger.warning(f"Performance Alert: {alert['message']}")
            else:
                self.logger.info(f"Performance Info: {alert['message']}")
    
    def get_performance_report(self, hours: int = 1) -> Dict[str, Any]:
        """Generate performance report for specified time period"""
        if not self.metrics_history:
            return {'message': 'No performance data available'}
        
        # Filter metrics by time period
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {'message': f'No data available for last {hours} hours'}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        cache_hit_rates = [m.cache_hit_rate for m in recent_metrics if m.cache_hit_rate > 0]
        
        report = {
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu_usage': {
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_usage': {
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'current_status': {
                'cpu_percent': recent_metrics[-1].cpu_percent,
                'memory_percent': recent_metrics[-1].memory_percent,
                'memory_mb': recent_metrics[-1].memory_mb,
                'database_connections': recent_metrics[-1].database_connections,
                'background_tasks': recent_metrics[-1].background_tasks
            }
        }
        
        if cache_hit_rates:
            report['cache_performance'] = {
                'average_hit_rate': sum(cache_hit_rates) / len(cache_hit_rates),
                'max_hit_rate': max(cache_hit_rates),
                'min_hit_rate': min(cache_hit_rates)
            }
        
        # Add optimization recommendations
        report['recommendations'] = self._generate_optimization_recommendations(recent_metrics)
        
        return report
    
    def _generate_optimization_recommendations(self, metrics: List[PerformanceMetrics]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Analyze trends
        if len(metrics) < 2:
            return recommendations
        
        # CPU recommendations
        avg_cpu = sum(m.cpu_percent for m in metrics) / len(metrics)
        if avg_cpu > 70:
            recommendations.append("Consider increasing batch processing intervals to reduce CPU load")
            recommendations.append("Review async task scheduling for better CPU utilization")
        
        # Memory recommendations
        avg_memory = sum(m.memory_percent for m in metrics) / len(metrics)
        if avg_memory > 80:
            recommendations.append("Consider reducing cache size or implementing more aggressive cache eviction")
            recommendations.append("Review memory usage in data processing pipelines")
        
        # Cache recommendations
        cache_rates = [m.cache_hit_rate for m in metrics if m.cache_hit_rate > 0]
        if cache_rates and sum(cache_rates) / len(cache_rates) < 70:
            recommendations.append("Improve cache hit rate by optimizing cache key generation")
            recommendations.append("Consider increasing cache TTL for frequently accessed data")
        
        # Database connection recommendations
        db_connections = [m.database_connections for m in metrics]
        if db_connections and max(db_connections) > 8:
            recommendations.append("Consider optimizing database queries to reduce connection time")
            recommendations.append("Review connection pooling configuration")
        
        return recommendations

# Global performance monitor
performance_monitor = PerformanceMonitor()
```

---

## 10. Testing Strategy

### 🧪 Comprehensive Testing with Resource Management

#### **Resource-Aware Test Framework**
```python
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import AsyncGenerator, Generator, Dict, Any
from contextlib import asynccontextmanager

# Enhanced test fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def temp_data_dir():
    """Create temporary data directory for tests"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
async def test_config(temp_data_dir):
    """Test configuration with isolated resources"""
    config = AppConfig(
        environment=Environment.TESTING,
        debug=True,
        log_level="DEBUG",
        data_directory=temp_data_dir,
        database=DatabaseConfig(
            host="localhost",
            database="test_db",
            username="test",
            password="test"
        ),
        ai=AIConfig(
            provider="mock",
            api_key="test-key"
        ),
        resources=ResourceConfig(
            max_database_connections=2,  # Limit for tests
            cleanup_interval=10
        ),
        monitoring=MonitoringConfig(
            enabled=False  # Disable in tests
        )
    )
    return config

@pytest.fixture
async def mock_resource_manager(test_config):
    """Mock resource manager for testing"""
    manager = Mock(spec=ResourceManager)
    manager.config = test_config
    
    # Mock database connection
    mock_db = AsyncMock()
    manager.get_database_connection = AsyncMock(return_value=mock_db)
    
    # Mock session management
    mock_session = AsyncMock()
    manager.get_session = AsyncMock(return_value=mock_session)
    
    return manager

@pytest.fixture
async def test_cache_manager(temp_data_dir):
    """Cache manager for testing"""
    cache_dir = temp_data_dir / "cache"
    cache_manager = AdvancedCacheManager(
        memory_limit=10,  # Small limit for tests
        disk_cache_dir=str(cache_dir)
    )
    yield cache_manager
    await cache_manager.cleanup_expired()

class TestResourceManagement:
    """Test resource management functionality"""
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, test_config):
        """Test database connection pooling"""
        db_manager = DatabaseConnectionManager(max_connections=2)
        
        # Test getting connections
        async def get_connection_task():
            with db_manager.get_connection("test_db", ":memory:") as conn:
                # Simulate some work
                await asyncio.sleep(0.1)
                return conn is not None
        
        # Run multiple concurrent connection requests
        tasks = [get_connection_task() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert all(results), "All connection requests should succeed"
        
        # Verify connection limits are respected
        stats = db_manager.get_stats()
        assert stats['total_connections'] <= 2, "Should not exceed max connections"
        
        # Cleanup
        db_manager.close_all_connections()
    
    @pytest.mark.asyncio
    async def test_conflict_prevention(self, temp_data_dir):
        """Test file lock conflict prevention"""
        conflict_prevention = ConflictPrevention(str(temp_data_dir / "locks"))
        await conflict_prevention.setup()
        
        # Test acquiring lock
        async with conflict_prevention.acquire_file_lock("test_resource"):
            # Verify lock is active
            lock_file = temp_data_dir / "locks" / "test_resource.lock"
            assert lock_file.exists(), "Lock file should exist"
            
            # Try to acquire same lock from different context
            try:
                async with conflict_prevention.acquire_file_lock("test_resource"):
                    pytest.fail("Should not be able to acquire same lock twice")
            except ResourceError:
                pass  # Expected behavior
        
        # Verify lock is released
        assert not lock_file.exists(), "Lock file should be cleaned up"
        
        await conflict_prevention.cleanup()
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, test_cache_manager):
        """Test cache performance and functionality"""
        cache = test_cache_manager
        
        # Test basic caching
        await cache.set("test_key", "test_value", ttl=60)
        value = await cache.get("test_key")
        assert value == "test_value", "Should retrieve cached value"
        
        # Test cache miss
        missing_value = await cache.get("nonexistent_key")
        assert missing_value is None, "Should return None for missing key"
        
        # Test TTL expiration
        await cache.set("expire_key", "expire_value", ttl=0.1)
        await asyncio.sleep(0.2)
        expired_value = await cache.get("expire_key")
        assert expired_value is None, "Should return None for expired key"
        
        # Test cache statistics
        stats = cache.get_stats()
        assert 'cache_stats' in stats, "Should provide cache statistics"
        assert stats['memory_hit_rate'] >= 0, "Hit rate should be non-negative"

class TestAIIntegration:
    """Test AI integration patterns"""
    
    @pytest.mark.asyncio
    async def test_ai_router_provider_selection(self):
        """Test AI router provider selection logic"""
        config = {
            'claude_api_key': 'test-claude-key',
            'openai_api_key': 'test-openai-key',
            'local_ai_enabled': True
        }
        
        router = SmartAIRouter(config)
        
        # Test simple task routing
        simple_request = AIRequest(
            prompt="Simple test",
            task_type="summary",
            complexity=TaskComplexity.SIMPLE
        )
        
        provider = await router._select_provider(simple_request)
        assert provider is not None, "Should select a provider"
        
        # Test complex task routing
        complex_request = AIRequest(
            prompt="Complex analysis task",
            task_type="analysis",
            complexity=TaskComplexity.COMPLEX
        )
        
        provider = await router._select_provider(complex_request)
        assert provider in [AIProvider.CLAUDE, AIProvider.OPENAI], "Should prefer cloud providers for complex tasks"
    
    @pytest.mark.asyncio
    @patch('anthropic.AsyncAnthropic')
    async def test_ai_processing_with_fallback(self, mock_anthropic):
        """Test AI processing with fallback mechanisms"""
        # Mock Claude client
        mock_client = AsyncMock()
        mock_anthropic.return_value = mock_client
        
        # Test successful processing
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_client.messages.create.return_value = mock_response
        
        config = {'claude_api_key': 'test-key', 'claude_model': 'claude-3-sonnet-20240229'}
        router = SmartAIRouter(config)
        
        request = AIRequest(prompt="Test prompt", task_type="test")
        response = await router._process_with_claude(request)
        
        assert response.content == "Test response", "Should return AI response"
        assert response.provider == AIProvider.CLAUDE, "Should indicate Claude provider"
        assert response.tokens_used == 15, "Should calculate total tokens"
        
        # Test error handling
        mock_client.messages.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            await router._process_with_claude(request)

class TestErrorHandling:
    """Test comprehensive error handling"""
    
    @pytest.mark.asyncio
    async def test_error_context_manager(self):
        """Test error context manager functionality"""
        test_context = {'test_id': 'test_123', 'operation': 'test_operation'}
        
        # Test successful operation
        async with error_context("test_operation", **test_context):
            result = "success"
        
        # Test error handling
        try:
            async with error_context("failing_operation", **test_context):
                raise ValueError("Test error")
        except ProcessingError as e:
            assert "failing_operation failed" in str(e), "Should wrap error with context"
            assert e.context is not None, "Should include context information"
            assert 'test_id' in e.context, "Should preserve original context"
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test retry mechanism with exponential backoff"""
        call_count = 0
        
        @retry_with_circuit_breaker(max_attempts=3, delay=0.01, backoff=2.0)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ExternalServiceError("Service unavailable", "test_service")
            return "success"
        
        # Should succeed after retries
        result = await failing_function()
        assert result == "success", "Should eventually succeed"
        assert call_count == 3, "Should retry correct number of times"
    
    def test_circuit_breaker_pattern(self):
        """Test circuit breaker functionality"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Test normal operation
        assert breaker.state == CircuitState.CLOSED
        
        # Simulate failures
        for _ in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(Exception("Test error")))
            except:
                pass
        
        # Should open circuit after threshold
        assert breaker.state == CircuitState.OPEN
        
        # Should reject calls when open
        with pytest.raises(ExternalServiceError):
            breaker.call(lambda: "success")

class TestPerformanceMonitoring:
    """Test performance monitoring functionality"""
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self):
        """Test performance metrics collection"""
        monitor = PerformanceMonitor(monitoring_interval=0.1)
        
        # Mock components
        mock_cache = Mock()
        mock_cache.get_stats.return_value = {'overall_hit_rate': 85.0}
        
        mock_db = Mock()
        mock_db.get_stats.return_value = {'active_connections': 3}
        
        monitor.register_components(cache_manager=mock_cache, db_manager=mock_db)
        
        # Collect metrics
        metrics = await monitor._collect_metrics()
        
        assert metrics.cpu_percent >= 0, "CPU percentage should be non-negative"
        assert metrics.memory_percent >= 0, "Memory percentage should be non-negative"
        assert metrics.cache_hit_rate == 85.0, "Should use cache manager stats"
        assert metrics.database_connections == 3, "Should use database manager stats"
    
    @pytest.mark.asyncio
    async def test_performance_alerting(self):
        """Test performance alerting system"""
        monitor = PerformanceMonitor()
        
        # Create metrics that should trigger alerts
        high_cpu_metrics = PerformanceMetrics(cpu_percent=90.0, memory_percent=70.0)
        alerts = monitor._check_thresholds(high_cpu_metrics)
        
        cpu_alerts = [a for a in alerts if a['type'] == 'cpu_high']
        assert len(cpu_alerts) > 0, "Should generate CPU alert"
        assert cpu_alerts[0]['severity'] == 'warning', "Should be warning level"
        
        # Test low cache hit rate alert
        low_cache_metrics = PerformanceMetrics(cache_hit_rate=50.0)
        cache_alerts = monitor._check_thresholds(low_cache_metrics)
        
        cache_alert_types = [a['type'] for a in cache_alerts]
        assert 'cache_hit_rate_low' in cache_alert_types, "Should generate cache alert"

# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_processing_workflow(self, test_config, mock_resource_manager):
        """Test complete data processing workflow"""
        # Mock components
        extractor = Mock(spec=BaseProcessor)
        extractor.initialize = AsyncMock(return_value=True)
        extractor.process_batch = AsyncMock(return_value=[
            ProcessingResult(status=ProcessingStatus.COMPLETED, data="processed_1"),
            ProcessingResult(status=ProcessingStatus.COMPLETED, data="processed_2")
        ])
        
        processor = Mock(spec=BaseProcessor)
        processor.initialize = AsyncMock(return_value=True)
        processor.process = AsyncMock(return_value=ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            data="ai_processed"
        ))
        
        # Test workflow
        await extractor.initialize()
        await processor.initialize()
        
        # Process test data
        test_data = ["item1", "item2"]
        extraction_results = await extractor.process_batch(test_data)
        
        assert len(extraction_results) == 2, "Should process all items"
        assert all(r.status == ProcessingStatus.COMPLETED for r in extraction_results), "All should succeed"
        
        # Process with AI
        for result in extraction_results:
            ai_result = await processor.process(result.data)
            assert ai_result.status == ProcessingStatus.COMPLETED, "AI processing should succeed"
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, test_config):
        """Test error recovery in processing workflow"""
        error_count = 0
        
        async def failing_processor(data):
            nonlocal error_count
            error_count += 1
            if error_count <= 2:
                raise ProcessingError("Temporary failure", retryable=True)
            return ProcessingResult(status=ProcessingStatus.COMPLETED, data="recovered")
        
        # Test with retry mechanism
        @retry_with_circuit_breaker(max_attempts=3, delay=0.01)
        async def process_with_retry(data):
            return await failing_processor(data)
        
        result = await process_with_retry("test_data")
        assert result.status == ProcessingStatus.COMPLETED, "Should recover from failures"
        assert error_count == 3, "Should retry correct number of times"

# Performance tests
@pytest.mark.performance
class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self, test_cache_manager):
        """Test performance under concurrent load"""
        cache = test_cache_manager
        
        async def concurrent_cache_operation(item_id: int):
            key = f"test_key_{item_id}"
            value = f"test_value_{item_id}"
            
            # Set and get value
            await cache.set(key, value)
            retrieved = await cache.get(key)
            
            return retrieved == value
        
        # Run 100 concurrent operations
        tasks = [concurrent_cache_operation(i) for i in range(100)]
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Verify all operations succeeded
        assert all(results), "All cache operations should succeed"
        
        # Check performance
        total_time = end_time - start_time
        operations_per_second = 200 / total_time  # 100 sets + 100 gets
        
        assert operations_per_second > 100, f"Should handle >100 ops/sec, got {operations_per_second:.1f}"
        
        # Check cache statistics
        stats = cache.get_stats()
        assert stats['memory_hit_rate'] > 0, "Should have cache hits"
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage during heavy processing"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create large dataset
        large_dataset = [{"id": i, "data": f"item_{i}" * 100} for i in range(1000)]
        
        # Process dataset
        async def process_item(item):
            # Simulate processing
            await asyncio.sleep(0.001)
            return {"processed": item["id"], "result": len(item["data"])}
        
        # Process in batches to test memory management
        batch_size = 50
        results = []
        
        for i in range(0, len(large_dataset), batch_size):
            batch = large_dataset[i:i + batch_size]
            batch_tasks = [process_item(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            
            # Force garbage collection between batches
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Verify processing completed
        assert len(results) == 1000, "Should process all items"
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024, f"Memory increase too high: {memory_increase / 1024 / 1024:.1f}MB"

# Test configuration
pytest_plugins = ['pytest_asyncio']

# Custom markers
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

# Pytest configuration
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, temp_data_dir):
    """Setup isolated test environment"""
    # Set test environment variables
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATA_DIRECTORY", str(temp_data_dir))
    
    # Disable external services in tests
    monkeypatch.setenv("ENABLE_EXTERNAL_APIS", "false")
    monkeypatch.setenv("MONITORING_ENABLED", "false")
```

---

## 11. Documentation Standards

### 📝 Enhanced Documentation Patterns

#### **Comprehensive Code Documentation**
```python
from typing import List, Optional, Dict, Any, Union, AsyncGenerator
from datetime import datetime
import asyncio

class AdvancedDataProcessor:
    """
    Advanced data processor with AI integration and resource management.
    
    This class provides sophisticated data processing capabilities including:
    - Multi-provider AI processing with intelligent routing
    - Resource-aware batch processing with automatic optimization
    - Comprehensive error handling with autonomous recovery
    - Performance monitoring and optimization recommendations
    
    The processor is designed for high-throughput scenarios where data quality,
    processing reliability, and resource efficiency are critical requirements.
    
    Attributes:
        config (ProcessorConfig): Configuration object containing processing parameters
        resource_manager (ResourceManager): Centralized resource management instance
        ai_router (SmartAIRouter): AI provider routing and fallback management
        performance_monitor (PerformanceMonitor): Real-time performance tracking
        is_initialized (bool): Whether the processor has been properly initialized
        
    Example:
        Basic usage with default configuration:
        
        >>> config = ProcessorConfig(batch_size=50, ai_provider="claude")
        >>> processor = AdvancedDataProcessor(config)
        >>> await processor.initialize()
        >>> 
        >>> # Process a batch of data
        >>> data = [{"text": "Sample text", "id": i} for i in range(100)]
        >>> results = await processor.process_batch(data)
        >>> 
        >>> # Check processing statistics
        >>> stats = processor.get_processing_stats()
        >>> print(f"Success rate: {stats['success_rate']:.1f}%")
        
        Advanced usage with custom resource management:
        
        >>> resource_manager = ResourceManager()
        >>> await resource_manager.initialize()
        >>> 
        >>> processor = AdvancedDataProcessor(
        ...     config=config,
        ...     resource_manager=resource_manager
        ... )
        >>> 
        >>> # Process with custom AI routing
        >>> results = await processor.process_with_ai_routing(
        ...     data,
        ...     complexity=TaskComplexity.COMPLEX,
        ...     fallback_enabled=True
        ... )
        
    Note:
        This processor requires proper resource initialization before use.
        Always call `initialize()` before processing and `cleanup()` when done.
        
    Warning:
        Large datasets (>10,000 items) should be processed using the batch
        processing methods to avoid memory exhaustion and ensure optimal
        resource utilization.
        
    See Also:
        - ResourceManager: For centralized resource management
        - SmartAIRouter: For AI provider selection and fallbacks
        - ProcessorConfig: For configuration options and examples
        - https://docs.example.com/processors for detailed guides
    """
    
    def __init__(self, config: 'ProcessorConfig', 
                 resource_manager: Optional['ResourceManager'] = None):
        """
        Initialize the advanced data processor.
        
        Sets up the processor with the provided configuration and optional
        resource manager. If no resource manager is provided, a default
        instance will be created with standard settings.
        
        Args:
            config (ProcessorConfig): Configuration object containing all
                processing parameters including AI settings, batch sizes,
                retry policies, and performance thresholds. Must be a valid
                ProcessorConfig instance with required fields populated.
                
            resource_manager (ResourceManager, optional): Pre-configured
                resource manager instance for database connections, caching,
                and session management. If None, a new instance will be
                created with default settings. Defaults to None.
                
        Raises:
            ConfigurationError: If the provided config is invalid or missing
                required parameters. This includes missing AI API keys,
                invalid batch sizes, or unsupported AI providers.
                
            ResourceError: If the resource manager initialization fails,
                typically due to database connection issues or file
                permission problems.
                
        Example:
            Initialize with minimal configuration:
            
            >>> config = ProcessorConfig(
            ...     ai_provider="claude",
            ...     api_key="sk-ant-your-key-here",
            ...     batch_size=25
            ... )
            >>> processor = AdvancedDataProcessor(config)
            
            Initialize with shared resource manager:
            
            >>> shared_resources = ResourceManager()
            >>> await shared_resources.initialize()
            >>> 
            >>> processor = AdvancedDataProcessor(
            ...     config=config,
            ...     resource_manager=shared_resources
            ... )
            
        Note:
            The processor is not ready for use until `initialize()` is called.
            This separation allows for better error handling and resource
            setup validation.
        """
        self.config = config
        self.resource_manager = resource_manager or ResourceManager()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize components (will be set up in initialize())
        self.ai_router: Optional['SmartAIRouter'] = None
        self.performance_monitor: Optional['PerformanceMonitor'] = None
        self._is_initialized = False
        self._shutdown_event = asyncio.Event()
        
        # Processing statistics
        self._stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'average_processing_time': 0.0,
            'last_processing_session': None
        }
        
        # Validate configuration
        self._validate_config()
    
    async def process_batch_with_ai_analysis(
        self, 
        data: List[Dict[str, Any]], 
        analysis_type: str = "comprehensive",
        priority: 'ProcessingPriority' = ProcessingPriority.MEDIUM,
        timeout: Optional[int] = None,
        custom_prompts: Optional[Dict[str, str]] = None
    ) -> 'BatchProcessingResult':
        """
        Process a batch of data with advanced AI analysis and resource optimization.
        
        This method performs sophisticated batch processing with the following features:
        - Intelligent batch size optimization based on current system load
        - Multi-provider AI processing with automatic fallback capabilities
        - Real-time performance monitoring and adjustment
        - Comprehensive error handling with retry logic and partial failure recovery
        - Resource-aware processing to prevent system overload
        
        The processing pipeline includes:
        1. Data validation and preprocessing
        2. Intelligent batch size calculation based on system resources
        3. Parallel AI processing with rate limiting
        4. Result aggregation and quality validation
        5. Performance metrics collection and optimization recommendations
        
        Args:
            data (List[Dict[str, Any]]): List of data items to process. Each item
                must be a dictionary containing at least the required fields as
                specified in the processor configuration. Maximum recommended
                batch size is 1000 items for optimal performance.
                
                Expected format:
                [
                    {"id": "item_1", "text": "Content to process", "metadata": {...}},
                    {"id": "item_2", "text": "More content", "metadata": {...}},
                    ...
                ]
                
            analysis_type (str, optional): Type of AI analysis to perform.
                Supported values:
                - "summary": Basic summarization and key point extraction
                - "comprehensive": Full analysis including sentiment, entities, topics
                - "custom": Use custom prompts provided in custom_prompts parameter
                - "categorization": Focus on content categorization and tagging
                
                Defaults to "comprehensive" for maximum insight extraction.
                
            priority (ProcessingPriority, optional): Processing priority level
                affecting resource allocation and AI provider selection.
                - HIGH: Uses premium AI providers, maximum parallelism
                - MEDIUM: Balanced approach with good performance and cost
                - LOW: Cost-optimized processing, may use local AI when available
                
                Defaults to ProcessingPriority.MEDIUM.
                
            timeout (int, optional): Maximum time in seconds to wait for processing
                completion. If None, uses the default timeout from configuration
                (typically 300 seconds). Individual item timeouts are calculated
                as timeout / batch_size with a minimum of 30 seconds.
                
            custom_prompts (Dict[str, str], optional): Custom AI prompts for
                specific analysis tasks. Only used when analysis_type is "custom".
                
                Expected format:
                {
                    "summarization": "Your custom summarization prompt here",
                    "analysis": "Your custom analysis prompt here",
                    "categorization": "Your custom categorization prompt here"
                }
                
        Returns:
            BatchProcessingResult: Comprehensive result object containing:
                - results (List[ProcessingResult]): Individual item results
                - summary_statistics (Dict[str, Any]): Batch-level statistics
                - performance_metrics (Dict[str, float]): Timing and resource usage
                - recommendations (List[str]): Optimization recommendations
                - errors (List[Dict[str, Any]]): Detailed error information
                
                The BatchProcessingResult provides methods for:
                - get_successful_results(): Filter for successful processing
                - get_failed_results(): Get items that failed processing
                - export_to_json(): Export results in JSON format
                - get_quality_score(): Overall processing quality assessment
                
        Raises:
            ValidationError: If input data format is invalid or required fields
                are missing. Includes detailed information about which items
                failed validation and why.
                
            ResourceError: If system resources are insufficient for processing
                or if resource allocation fails. This may indicate high system
                load or configuration issues.
                
            ProcessingError: If the majority of items fail processing, indicating
                a systematic issue with the data or AI provider availability.
                Individual item failures are included in the result object.
                
            TimeoutError: If processing exceeds the specified timeout. Partial
                results may be available in the exception context.
                
        Example:
            Basic batch processing:
            
            >>> data = [
            ...     {"id": "doc1", "text": "Important business document"},
            ...     {"id": "doc2", "text": "Customer feedback message"},
            ...     {"id": "doc3", "text": "Technical specification"}
            ... ]
            >>> 
            >>> result = await processor.process_batch_with_ai_analysis(
            ...     data=data,
            ...     analysis_type="comprehensive",
            ...     priority=ProcessingPriority.HIGH
            ... )
            >>> 
            >>> print(f"Processed {len(result.results)} items")
            >>> print(f"Success rate: {result.get_success_rate():.1f}%")
            >>> print(f"Processing time: {result.performance_metrics['total_time']:.2f}s")
            
            Custom analysis with specific prompts:
            
            >>> custom_prompts = {
            ...     "analysis": "Extract key business insights and action items",
            ...     "categorization": "Categorize as: urgent, normal, or informational"
            ... }
            >>> 
            >>> result = await processor.process_batch_with_ai_analysis(
            ...     data=data,
            ...     analysis_type="custom",
            ...     custom_prompts=custom_prompts,
            ...     timeout=600  # 10 minutes for complex analysis
            ... )
            
            Processing with error handling:
            
            >>> try:
            ...     result = await processor.process_batch_with_ai_analysis(data)
            ...     
            ...     # Handle partial failures
            ...     if result.has_failures():
            ...         failed_items = result.get_failed_results()
            ...         logger.warning(f"{len(failed_items)} items failed processing")
            ...         
            ...         # Retry failed items with lower priority
            ...         retry_data = [item.original_data for item in failed_items]
            ...         retry_result = await processor.process_batch_with_ai_analysis(
            ...             retry_data, priority=ProcessingPriority.LOW
            ...         )
            ...         
            ... except ProcessingError as e:
            ...     logger.error(f"Batch processing failed: {e}")
            ...     # Handle systematic failure
            ...     
        Performance Notes:
            - Optimal batch size is automatically calculated based on system resources
            - Processing time scales roughly linearly with batch size for most data types
            - Memory usage peaks at approximately 50MB per 1000 text items
            - AI provider rate limits are automatically managed with intelligent backoff
            
        See Also:
            - ProcessingResult: Individual item processing result format
            - BatchProcessingResult: Batch result object documentation
            - ProcessingPriority: Priority level effects on resource allocation
            - process_single_item(): For processing individual items
            - get_optimization_recommendations(): For performance tuning advice
        """
        start_time = asyncio.get_event_loop().time()
        
        # Implementation would go here...
        # This is just the docstring example
        
        pass
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive processing statistics and performance metrics.
        
        Returns detailed information about processor performance, resource usage,
        and processing quality metrics collected since initialization or the last
        statistics reset.
        
        Returns:
            Dict[str, Any]: Comprehensive statistics dictionary containing:
                
                Processing Statistics:
                - total_processed (int): Total number of items processed
                - successful (int): Number of successfully processed items
                - failed (int): Number of items that failed processing
                - success_rate (float): Success rate as percentage (0-100)
                - average_processing_time (float): Average time per item in seconds
                
                Performance Metrics:
                - throughput_per_second (float): Items processed per second
                - peak_memory_usage_mb (float): Peak memory usage in megabytes
                - cpu_utilization_avg (float): Average CPU usage percentage
                - ai_provider_distribution (Dict[str, int]): Usage by AI provider
                
                Quality Metrics:
                - average_confidence_score (float): AI confidence (0.0-1.0)
                - retry_rate (float): Percentage of items requiring retry
                - timeout_rate (float): Percentage of items that timed out
                
                Resource Usage:
                - database_connections_peak (int): Peak database connections used
                - cache_hit_rate (float): Cache hit rate percentage
                - network_requests_total (int): Total external API requests
                
                Recent Activity:
                - last_processing_session (datetime): Timestamp of last processing
                - sessions_today (int): Number of processing sessions today
                - uptime_hours (float): Hours since processor initialization
                
        Example:
            >>> stats = processor.get_processing_stats()
            >>> print(f"Success rate: {stats['success_rate']:.1f}%")
            >>> print(f"Throughput: {stats['throughput_per_second']:.1f} items/sec")
            >>> print(f"Memory usage: {stats['peak_memory_usage_mb']:.1f} MB")
            >>> 
            >>> # Check for performance issues
            >>> if stats['success_rate'] < 95.0:
            ...     print("Warning: Low success rate detected")
            >>> 
            >>> if stats['average_processing_time'] > 5.0:
            ...     print("Warning: Processing time above recommended threshold")
        """
        total = self._stats['total_processed']
        success_rate = (self._stats['successful'] / total * 100) if total > 0 else 0
        
        return {
            'total_processed': total,
            'successful': self._stats['successful'],
            'failed': self._stats['failed'],
            'success_rate': success_rate,
            'average_processing_time': self._stats['average_processing_time'],
            'last_processing_session': self._stats['last_processing_session'],
            'processor_uptime': self._get_uptime_hours(),
            'is_healthy': self._check_health_status()
        }
```

#### **API Documentation Templates**
```markdown
# Advanced Data Processor API Reference

## Overview

The Advanced Data Processor provides enterprise-grade data processing capabilities with AI integration, resource management, and comprehensive error handling.

## Quick Start

```python
from advanced_processor import AdvancedDataProcessor, ProcessorConfig

# Initialize processor
config = ProcessorConfig(
    ai_provider="claude",
    api_key="your-api-key",
    batch_size=50
)

processor = AdvancedDataProcessor(config)
await processor.initialize()

# Process data
data = [{"text": "Sample text", "id": 1}]
results = await processor.process_batch(data)
```

## Classes

### AdvancedDataProcessor

The main processor class providing AI-powered data processing capabilities.

#### Constructor

```python
AdvancedDataProcessor(config: ProcessorConfig, resource_manager: Optional[ResourceManager] = None)
```

**Parameters:**
- `config` *(ProcessorConfig)*: Configuration object containing processing parameters
- `resource_manager` *(ResourceManager, optional)*: Pre-configured resource manager

**Raises:**
- `ConfigurationError`: Invalid configuration parameters
- `ResourceError`: Resource initialization failure

#### Methods

##### `async initialize() -> bool`

Initialize the processor and all dependent resources.

**Returns:**
- `bool`: True if initialization successful

**Example:**
```python
success = await processor.initialize()
if not success:
    raise RuntimeError("Processor initialization failed")
```

##### `async process_batch_with_ai_analysis(...) -> BatchProcessingResult`

Process a batch of data with AI analysis.

**Parameters:**
- `data` *(List[Dict[str, Any]])*: Data items to process
- `analysis_type` *(str, optional)*: Type of analysis ("summary", "comprehensive", "custom")
- `priority` *(ProcessingPriority, optional)*: Processing priority level
- `timeout` *(int, optional)*: Maximum processing time in seconds
- `custom_prompts` *(Dict[str, str], optional)*: Custom AI prompts

**Returns:**
- `BatchProcessingResult`: Comprehensive processing results

**Raises:**
- `ValidationError`: Invalid input data format
- `ProcessingError`: Systematic processing failure
- `TimeoutError`: Processing timeout exceeded

**Example:**
```python
results = await processor.process_batch_with_ai_analysis(
    data=data_items,
    analysis_type="comprehensive",
    priority=ProcessingPriority.HIGH,
    timeout=300
)

print(f"Success rate: {results.get_success_rate():.1f}%")
```

## Data Structures

### ProcessorConfig

Configuration object for the Advanced Data Processor.

```python
@dataclass
class ProcessorConfig:
    ai_provider: str                    # AI provider ("claude", "openai", "local")
    api_key: str                       # AI API key
    batch_size: int = 25               # Default batch size
    max_retries: int = 3               # Maximum retry attempts
    timeout: int = 300                 # Default timeout in seconds
    enable_caching: bool = True        # Enable result caching
    performance_monitoring: bool = True # Enable performance monitoring
```

### BatchProcessingResult

Result object containing comprehensive batch processing information.

```python
@dataclass
class BatchProcessingResult:
    results: List[ProcessingResult]           # Individual item results
    summary_statistics: Dict[str, Any]        # Batch-level statistics
    performance_metrics: Dict[str, float]     # Performance information
    recommendations: List[str]               # Optimization recommendations
    errors: List[Dict[str, Any]]             # Error details
```

**Methods:**
- `get_successful_results() -> List[ProcessingResult]`: Get successful results only
- `get_failed_results() -> List[ProcessingResult]`: Get failed results only
- `get_success_rate() -> float`: Calculate success rate percentage
- `export_to_json() -> str`: Export results as JSON string
- `has_failures() -> bool`: Check if any items failed

## Error Handling

### Exception Hierarchy

```
AppError
├── ConfigurationError          # Configuration issues
├── ValidationError            # Data validation failures
├── ProcessingError           # Processing failures
├── ResourceError            # Resource management issues
└── TimeoutError            # Timeout exceeded
```

### Error Context

All exceptions include comprehensive context information:

```python
try:
    result = await processor.process_batch(data)
except ProcessingError as e:
    print(f"Error: {e}")
    print(f"Context: {e.context}")
    print(f"Retryable: {e.retryable}")
```

## Configuration Examples

### Basic Configuration

```python
config = ProcessorConfig(
    ai_provider="claude",
    api_key="sk-ant-your-key-here",
    batch_size=25
)
```

### High-Performance Configuration

```python
config = ProcessorConfig(
    ai_provider="claude",
    api_key="sk-ant-your-key-here",
    batch_size=100,                    # Larger batches
    max_retries=1,                     # Fewer retries for speed
    timeout=600,                       # Longer timeout
    enable_caching=True,               # Cache for performance
    performance_monitoring=True        # Monitor performance
)
```

### Production Configuration

```python
config = ProcessorConfig(
    ai_provider="claude",
    api_key=os.getenv("CLAUDE_API_KEY"),
    batch_size=50,
    max_retries=3,                     # Robust retry handling
    timeout=300,
    enable_caching=True,
    performance_monitoring=True,
    
    # Production-specific settings
    resource_limits=ResourceLimits(
        max_memory_mb=1024,
        max_cpu_percent=80
    ),
    monitoring_config=MonitoringConfig(
        enable_alerts=True,
        alert_webhook="https://alerts.company.com/webhook"
    )
)
```

## Performance Optimization

### Batch Size Recommendations

| Data Type | Recommended Batch Size | Notes |
|-----------|----------------------|-------|
| Short text (< 100 words) | 100-200 | High throughput |
| Medium text (100-1000 words) | 50-100 | Balanced performance |
| Long text (> 1000 words) | 10-25 | Memory intensive |
| Mixed content | 50 | Safe default |

### Monitoring and Metrics

```python
# Get processing statistics
stats = processor.get_processing_stats()

# Check performance thresholds
if stats['average_processing_time'] > 5.0:
    print("Warning: High processing time")

if stats['success_rate'] < 95.0:
    print("Warning: Low success rate")

# Get optimization recommendations
recommendations = await processor.get_optimization_recommendations()
for rec in recommendations:
    print(f"Recommendation: {rec}")
```

## Integration Examples

### With Resource Manager

```python
# Shared resource manager for multiple processors
resource_manager = ResourceManager()
await resource_manager.initialize()

processor1 = AdvancedDataProcessor(config1, resource_manager)
processor2 = AdvancedDataProcessor(config2, resource_manager)

await processor1.initialize()
await processor2.initialize()
```

### With Performance Monitoring

```python
# Enable detailed performance monitoring
monitor = PerformanceMonitor()
await monitor.start_monitoring()

processor = AdvancedDataProcessor(config)
processor.register_performance_monitor(monitor)

# Process data with monitoring
results = await processor.process_batch(data)

# Get performance report
report = monitor.get_performance_report(hours=1)
print(f"Average response time: {report['average_response_time']:.2f}s")
```

## Troubleshooting

### Common Issues

#### High Memory Usage
```python
# Reduce batch size
config.batch_size = 25

# Enable memory monitoring
config.resource_limits.max_memory_mb = 512
```

#### Slow Processing
```python
# Check AI provider performance
stats = processor.get_ai_provider_stats()
if stats['claude']['average_time'] > 3.0:
    # Consider switching provider or reducing complexity
    pass
```

#### Rate Limiting
```python
# Configure rate limiting
config.rate_limit_config = RateLimitConfig(
    requests_per_minute=30,
    burst_allowance=10
)
```

For more examples and advanced usage, see the [Examples Repository](https://github.com/example/processor-examples).
```

---

## 12. Security Practices

### 🔐 Advanced Security Architecture

#### **Comprehensive Security Manager**
```python
import secrets
import hashlib
import hmac
import time
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from typing import Dict, Any, Optional, List, Tuple
import os
from pathlib import Path

class SecurityManager:
    """
    Comprehensive security management for enterprise applications
    
    Features:
    - Multi-layer credential encryption and management
    - JWT token generation and validation
    - API key rotation and validation
    - Rate limiting with IP-based tracking
    - Security audit logging
    - Intrusion detection and prevention
    """
    
    def __init__(self, security_config: Dict[str, Any]):
        self.config = security_config
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
        
        # Rate limiting storage
        self._rate_limits: Dict[str, List[float]] = {}
        self._blocked_ips: Set[str] = set()
        
        # Security audit log
        self._security_events: List[Dict[str, Any]] = []
        
        # Initialize security components
        self._initialize_security_components()
    
    def _initialize_security_components(self):
        """Initialize security components"""
        # Create secure directories
        secure_dirs = ['credentials', 'keys', 'audit_logs']
        for dir_name in secure_dirs:
            dir_path = Path(self.config.get('security_directory', 'security')) / dir_name
            dir_path.mkdir(parents=True, mode=0o700, exist_ok=True)
        
        # Load or generate JWT keys
        self._jwt_private_key, self._jwt_public_key = self._get_or_create_jwt_keys()
        
        # Initialize intrusion detection
        self._intrusion_patterns = self._load_intrusion_patterns()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create main encryption key"""
        key_file = Path(self.config.get('security_directory', 'security')) / 'keys' / 'main.key'
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            key_file.chmod(0o600)
        
        return key
    
    def _get_or_create_jwt_keys(self) -> Tuple[Any, Any]:
        """Get or create JWT RSA key pair"""
        private_key_file = Path(self.config.get('security_directory', 'security')) / 'keys' / 'jwt_private.pem'
        public_key_file = Path(self.config.get('security_directory', 'security')) / 'keys' / 'jwt_public.pem'
        
        if private_key_file.exists() and public_key_file.exists():
            # Load existing keys
            with open(private_key_file, 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)
            
            with open(public_key_file, 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read())
        else:
            # Generate new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Save private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            with open(private_key_file, 'wb') as f:
                f.write(private_pem)
            private_key_file.chmod(0o600)
            
            # Save public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            with open(public_key_file, 'wb') as f:
                f.write(public_pem)
            public_key_file.chmod(0o644)
        
        return private_key, public_key
    
    def encrypt_credential(self, credential: str, credential_name: str) -> str:
        """Encrypt and store credential securely"""
        try:
            # Encrypt the credential
            encrypted_credential = self._cipher.encrypt(credential.encode())
            
            # Store with metadata
            credential_data = {
                'encrypted_value': encrypted_credential.hex(),
                'created_at': time.time(),
                'last_rotated': time.time(),
                'access_count': 0
            }
            
            credential_file = (
                Path(self.config.get('security_directory', 'security')) / 
                'credentials' / f"{credential_name}.json"
            )
            
            with open(credential_file, 'w') as f:
                json.dump(credential_data, f)
            credential_file.chmod(0o600)
            
            # Log security event
            self._log_security_event('credential_stored', {
                'credential_name': credential_name,
                'success': True
            })
            
            return encrypted_credential.hex()
            
        except Exception as e:
            self._log_security_event('credential_storage_failed', {
                'credential_name': credential_name,
                'error': str(e)
            })
            raise SecurityError(f"Failed to encrypt credential: {e}")
    
    def decrypt_credential(self, credential_name: str) -> Optional[str]:
        """Decrypt and retrieve credential"""
        try:
            credential_file = (
                Path(self.config.get('security_directory', 'security')) / 
                'credentials' / f"{credential_name}.json"
            )
            
            if not credential_file.exists():
                self._log_security_event('credential_not_found', {
                    'credential_name': credential_name
                })
                return None
            
            with open(credential_file, 'r') as f:
                credential_data = json.load(f)
            
            # Decrypt the credential
            encrypted_bytes = bytes.fromhex(credential_data['encrypted_value'])
            decrypted_credential = self._cipher.decrypt(encrypted_bytes).decode()
            
            # Update access count
            credential_data['access_count'] += 1
            credential_data['last_accessed'] = time.time()
            
            with open(credential_file, 'w') as f:
                json.dump(credential_data, f)
            
            # Log access (without revealing the credential)
            self._log_security_event('credential_accessed', {
                'credential_name': credential_name,
                'access_count': credential_data['access_count']
            })
            
            return decrypted_credential
            
        except Exception as e:
            self._log_security_event('credential_decryption_failed', {
                'credential_name': credential_name,
                'error': str(e)
            })
            raise SecurityError(f"Failed to decrypt credential: {e}")
    
    def generate_api_key(self, key_name: str, permissions: List[str], 
                        expires_in_days: int = 365) -> str:
        """Generate secure API key with permissions"""
        # Generate secure random key
        key_data = secrets.token_urlsafe(32)
        
        # Create key metadata
        api_key_info = {
            'key_name': key_name,
            'permissions': permissions,
            'created_at': time.time(),
            'expires_at': time.time() + (expires_in_days * 24 * 60 * 60),
            'last_used': None,
            'usage_count': 0,
            'is_active': True
        }
        
        # Store key info (hashed for security)
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()
        key_file = (
            Path(self.config.get('security_directory', 'security')) / 
            'keys' / f"api_key_{key_hash[:16]}.json"
        )
        
        with open(key_file, 'w') as f:
            json.dump(api_key_info, f)
        key_file.chmod(0o600)
        
        self._log_security_event('api_key_generated', {
            'key_name': key_name,
            'permissions': permissions,
            'expires_in_days': expires_in_days
        })
        
        return f"ak_{key_data}"
    
    def validate_api_key(self, api_key: str, required_permission: str = None) -> Dict[str, Any]:
        """Validate API key and check permissions"""
        try:
            if not api_key.startswith('ak_'):
                self._log_security_event('invalid_api_key_format', {
                    'key_prefix': api_key[:10] if len(api_key) > 10 else api_key
                })
                raise SecurityError("Invalid API key format")
            
            key_data = api_key[3:]  # Remove 'ak_' prefix
            key_hash = hashlib.sha256(key_data.encode()).hexdigest()
            
            # Find key file
            key_file = (
                Path(self.config.get('security_directory', 'security')) / 
                'keys' / f"api_key_{key_hash[:16]}.json"
            )
            
            if not key_file.exists():
                self._log_security_event('api_key_not_found', {
                    'key_hash_prefix': key_hash[:16]
                })
                raise SecurityError("Invalid API key")
            
            with open(key_file, 'r') as f:
                key_info = json.load(f)
            
            # Check if key is active
            if not key_info['is_active']:
                self._log_security_event('api_key_inactive', {
                    'key_name': key_info['key_name']
                })
                raise SecurityError("API key is inactive")
            
            # Check expiration
            if time.time() > key_info['expires_at']:
                self._log_security_event('api_key_expired', {
                    'key_name': key_info['key_name']
                })
                raise SecurityError("API key has expired")
            
            # Check permissions
            if required_permission and required_permission not in key_info['permissions']:
                self._log_security_event('api_key_insufficient_permissions', {
                    'key_name': key_info['key_name'],
                    'required_permission': required_permission,
                    'available_permissions': key_info['permissions']
                })
                raise SecurityError("Insufficient permissions")
            
            # Update usage
            key_info['last_used'] = time.time()
            key_info['usage_count'] += 1
            
            with open(key_file, 'w') as f:
                json.dump(key_info, f)
            
            self._log_security_event('api_key_validated', {
                'key_name': key_info['key_name'],
                'permission_checked': required_permission
            })
            
            return {
                'valid': True,
                'key_name': key_info['key_name'],
                'permissions': key_info['permissions'],
                'usage_count': key_info['usage_count']
            }
            
        except SecurityError:
            raise
        except Exception as e:
            self._log_security_event('api_key_validation_error', {
                'error': str(e)
            })
            raise SecurityError(f"API key validation failed: {e}")
    
    def generate_jwt_token(self, user_id: str, permissions: List[str], 
                          expires_in_minutes: int = 60) -> str:
        """Generate JWT token with user claims"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'iat': int(time.time()),
            'exp': int(time.time()) + (expires_in_minutes * 60),
            'iss': self.config.get('jwt_issuer', 'advanced-python-app'),
            'jti': secrets.token_hex(16)  # Unique token ID
        }
        
        token = jwt.encode(payload, self._jwt_private_key, algorithm='RS256')
        
        self._log_security_event('jwt_token_generated', {
            'user_id': user_id,
            'permissions': permissions,
            'expires_in_minutes': expires_in_minutes
        })
        
        return token
    
    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and extract claims"""
        try:
            payload = jwt.decode(
                token, 
                self._jwt_public_key, 
                algorithms=['RS256'],
                issuer=self.config.get('jwt_issuer', 'advanced-python-app')
            )
            
            self._log_security_event('jwt_token_validated', {
                'user_id': payload.get('user_id'),
                'jti': payload.get('jti')
            })
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self._log_security_event('jwt_token_expired', {})
            raise SecurityError("Token has expired")
        except jwt.InvalidTokenError as e:
            self._log_security_event('jwt_token_invalid', {
                'error': str(e)
            })
            raise SecurityError("Invalid token")
    
    def check_rate_limit(self, identifier: str, max_requests: int = 100, 
                        window_minutes: int = 60) -> bool:
        """Check if request is within rate limit"""
        current_time = time.time()
        window_start = current_time - (window_minutes * 60)
        
        # Clean old entries
        if identifier in self._rate_limits:
            self._rate_limits[identifier] = [
                req_time for req_time in self._rate_limits[identifier]
                if req_time > window_start
            ]
        else:
            self._rate_limits[identifier] = []
        
        # Check current request count
        request_count = len(self._rate_limits[identifier])
        
        if request_count >= max_requests:
            self._log_security_event('rate_limit_exceeded', {
                'identifier': identifier,
                'request_count': request_count,
                'max_requests': max_requests,
                'window_minutes': window_minutes
            })
            return False
        
        # Add current request
        self._rate_limits[identifier].append(current_time)
        return True
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event for audit purposes"""
        event = {
            'timestamp': time.time(),
            'event_type': event_type,
            'details': details,
            'ip_address': details.get('ip_address'),  # Would be set by calling code
            'user_agent': details.get('user_agent')   # Would be set by calling code
        }
        
        self._security_events.append(event)
        
        # Also log to standard logger for immediate visibility
        self.logger.info(f"Security Event: {event_type}", extra=event)
        
        # Persist to audit log file
        self._persist_security_event(event)
    
    def _persist_security_event(self, event: Dict[str, Any]):
        """Persist security event to audit log"""
        audit_log_file = (
            Path(self.config.get('security_directory', 'security')) / 
            'audit_logs' / f"security_audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        
        try:
            with open(audit_log_file, 'a') as f:
                json.dump(event, f)
                f.write('\n')
        except Exception as e:
            self.logger.error(f"Failed to persist security event: {e}")
    
    def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate security report for specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        recent_events = [
            event for event in self._security_events
            if event['timestamp'] > cutoff_time
        ]
        
        # Categorize events
        event_counts = {}
        for event in recent_events:
            event_type = event['event_type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Identify potential security issues
        security_alerts = []
        
        if event_counts.get('rate_limit_exceeded', 0) > 10:
            security_alerts.append("High rate limit violations detected")
        
        if event_counts.get('api_key_validation_error', 0) > 5:
            security_alerts.append("Multiple API key validation failures")
        
        if event_counts.get('jwt_token_invalid', 0) > 3:
            security_alerts.append("Invalid JWT token attempts detected")
        
        return {
            'report_period_hours': hours,
            'total_events': len(recent_events),
            'event_breakdown': event_counts,
            'security_alerts': security_alerts,
            'blocked_ips': list(self._blocked_ips),
            'active_rate_limits': len(self._rate_limits),
            'recommendations': self._generate_security_recommendations(event_counts)
        }
    
    def _generate_security_recommendations(self, event_counts: Dict[str, int]) -> List[str]:
        """Generate security recommendations based on events"""
        recommendations = []
        
        if event_counts.get('rate_limit_exceeded', 0) > 20:
            recommendations.append("Consider implementing more aggressive rate limiting")
        
        if event_counts.get('api_key_not_found', 0) > 10:
            recommendations.append("Review API key distribution and rotation policies")
        
        if event_counts.get('credential_decryption_failed', 0) > 0:
            recommendations.append("Investigate potential credential corruption")
        
        return recommendations

# Security decorators
def require_api_key(permission: str = None):
    """Decorator to require valid API key with optional permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract API key from request (implementation depends on framework)
            api_key = kwargs.get('api_key') or getattr(args[0], 'api_key', None)
            
            if not api_key:
                raise SecurityError("API key required")
            
            # Validate with security manager
            security_manager = get_security_manager()
            validation_result = security_manager.validate_api_key(api_key, permission)
            
            # Add validation result to kwargs
            kwargs['api_key_info'] = validation_result
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_jwt_token(required_permissions: List[str] = None):
    """Decorator to require valid JWT token with optional permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract JWT token from request
            token = kwargs.get('jwt_token') or getattr(args[0], 'jwt_token', None)
            
            if not token:
                raise SecurityError("JWT token required")
            
            # Validate with security manager
            security_manager = get_security_manager()
            token_payload = security_manager.validate_jwt_token(token)
            
            # Check required permissions
            if required_permissions:
                user_permissions = token_payload.get('permissions', [])
                missing_permissions = set(required_permissions) - set(user_permissions)
                
                if missing_permissions:
                    raise SecurityError(f"Missing required permissions: {missing_permissions}")
            
            # Add token payload to kwargs
            kwargs['jwt_payload'] = token_payload
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Global security manager instance
_security_manager: Optional[SecurityManager] = None

def get_security_manager() -> SecurityManager:
    """Get the global security manager instance"""
    global _security_manager
    if _security_manager is None:
        config = get_config()
        security_config = {
            'security_directory': config.data_directory / 'security',
            'jwt_issuer': f"{config.name}-app"
        }
        _security_manager = SecurityManager(security_config)
    return _security_manager

class SecurityError(AppError):
    """Security-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, retryable=False, **kwargs)
```

---

## 13. Monitoring & Observability

### 📊 Comprehensive Monitoring Architecture

#### **Application Health Monitoring**

The foundation of production observability is comprehensive health monitoring that tracks system components, external dependencies, and application-specific metrics.

```python
import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Individual health check configuration"""
    name: str
    check_function: Callable
    timeout: int = 30
    critical: bool = True
    interval: int = 60
    description: str = ""

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

class HealthMonitor:
    """
    Comprehensive health monitoring system
    
    Features:
    - Multiple health check types (database, external services, resources)
    - Configurable check intervals and timeouts
    - Health status aggregation and reporting
    - Alert generation for health degradation
    - Historical health tracking
    - Integration with notification systems
    """
    
    def __init__(self, monitoring_config: Dict[str, Any]):
        self.config = monitoring_config
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_results: Dict[str, List[HealthCheckResult]] = {}
        self.running = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self.logger = logging.getLogger(__name__)
        
        # Overall system health
        self.system_status = HealthStatus.UNKNOWN
        self.last_health_update = datetime.now()
        
        # Component references for health checks
        self.resource_manager = None
        self.cache_manager = None
        self.ai_router = None
        
    def register_components(self, resource_manager=None, cache_manager=None, ai_router=None):
        """Register components for health monitoring"""
        self.resource_manager = resource_manager
        self.cache_manager = cache_manager
        self.ai_router = ai_router
        
        # Register default health checks
        self._register_default_health_checks()
    
    def _register_default_health_checks(self):
        """Register default system health checks"""
        # System resource checks
        self.register_health_check(HealthCheck(
            name="system_memory",
            check_function=self._check_system_memory,
            critical=True,
            interval=30,
            description="Monitor system memory usage"
        ))
        
        self.register_health_check(HealthCheck(
            name="system_cpu",
            check_function=self._check_system_cpu,
            critical=False,
            interval=30,
            description="Monitor system CPU usage"
        ))
        
        self.register_health_check(HealthCheck(
            name="disk_space",
            check_function=self._check_disk_space,
            critical=True,
            interval=300,  # Check every 5 minutes
            description="Monitor available disk space"
        ))
        
        # Application component checks
        if self.resource_manager:
            self.register_health_check(HealthCheck(
                name="database_connectivity",
                check_function=self._check_database_connectivity,
                critical=True,
                interval=60,
                description="Check database connection health"
            ))
        
        if self.cache_manager:
            self.register_health_check(HealthCheck(
                name="cache_performance",
                check_function=self._check_cache_performance,
                critical=False,
                interval=120,
                description="Monitor cache hit rates and performance"
            ))
        
        if self.ai_router:
            self.register_health_check(HealthCheck(
                name="ai_provider_health",
                check_function=self._check_ai_provider_health,
                critical=False,
                interval=180,
                description="Check AI provider availability and performance"
            ))
    
    async def start_monitoring(self):
        """Start all health monitoring tasks"""
        if self.running:
            return
        
        self.running = True
        
        # Start individual health check tasks
        for check_name, health_check in self.health_checks.items():
            task = asyncio.create_task(
                self._health_check_loop(check_name, health_check)
            )
            task.set_name(f"health_check_{check_name}")
            self.monitoring_tasks.append(task)
        
        # Start health aggregation task
        aggregation_task = asyncio.create_task(self._health_aggregation_loop())
        aggregation_task.set_name("health_aggregation")
        self.monitoring_tasks.append(aggregation_task)
        
        self.logger.info(f"Health monitoring started with {len(self.health_checks)} checks")
    
    async def stop_monitoring(self):
        """Stop all health monitoring tasks"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        self.monitoring_tasks.clear()
        self.logger.info("Health monitoring stopped")

    # Health check implementations
    async def _check_system_memory(self) -> HealthCheckResult:
        """Check system memory usage"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = f"Critical memory usage: {memory_percent:.1f}%"
        elif memory_percent > 80:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {memory_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {memory_percent:.1f}%"
        
        return HealthCheckResult(
            name="system_memory",
            status=status,
            message=message,
            execution_time=0.0,
            details={'memory_percent': memory_percent, 'memory_mb': memory.used / 1024 / 1024}
        )

    async def _check_database_connectivity(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        try:
            if not self.resource_manager:
                return HealthCheckResult(
                    name="database_connectivity",
                    status=HealthStatus.UNKNOWN,
                    message="Resource manager not available",
                    execution_time=0.0
                )
            
            start_time = time.time()
            # Test connection with a simple query
            async with self.resource_manager.get_database_connection() as conn:
                await conn.execute("SELECT 1")
            
            execution_time = time.time() - start_time
            
            if execution_time > 5.0:
                status = HealthStatus.DEGRADED
                message = f"Slow database response: {execution_time:.2f}s"
            else:
                status = HealthStatus.HEALTHY
                message = f"Database responsive: {execution_time:.2f}s"
            
            return HealthCheckResult(
                name="database_connectivity",
                status=status,
                message=message,
                execution_time=execution_time,
                details={'response_time': execution_time}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="database_connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e}",
                execution_time=0.0
            )
```

### 📢 Production Notification Architecture

[The multi-channel notification patterns we added earlier go here - already integrated]

### 🔍 Performance Metrics & Alerting

#### **Comprehensive Performance Monitoring**

```python
import psutil
import time
import asyncio
from typing import Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    disk_io_read: int = 0
    disk_io_write: int = 0
    network_sent: int = 0
    network_recv: int = 0
    active_threads: int = 0
    open_files: int = 0
    
    # Application-specific metrics
    database_connections: int = 0
    cache_hit_rate: float = 0.0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    background_tasks: int = 0

class PerformanceMonitor:
    """
    Comprehensive performance monitoring with optimization recommendations
    
    Features:
    - System resource monitoring (CPU, memory, disk, network)
    - Application-specific metrics
    - Performance trend analysis
    - Automatic optimization suggestions
    - Alerting for performance degradation
    """
    
    def __init__(self, monitoring_interval: int = 60):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000  # Keep last 1000 measurements
        self.running = False
        self.monitoring_task = None
        self.logger = logging.getLogger(__name__)
        
        # Performance thresholds for alerting
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_io_high': 50 * 1024 * 1024,  # 50MB/s
            'cache_hit_rate_low': 70.0,
            'average_response_time_high': 5.0,  # 5 seconds
            'error_rate_high': 5.0  # 5%
        }
        
        # Component references for metrics collection
        self.cache_manager = None
        self.db_manager = None
        self.task_manager = None

    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Performance monitoring started")

    def get_performance_report(self, hours: int = 1) -> Dict[str, Any]:
        """Generate performance report for specified time period"""
        if not self.metrics_history:
            return {'message': 'No performance data available'}
        
        # Filter metrics by time period
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {'message': f'No data available for last {hours} hours'}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        report = {
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu_usage': {
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_usage': {
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'recommendations': self._generate_optimization_recommendations(recent_metrics)
        }
        
        return report
```

### 🔗 Integrated Monitoring & Alerting System

#### **Comprehensive Production Monitoring Setup**

```python
class ProductionMonitoringOrchestrator:
    """
    Integrated monitoring system combining health checks, performance monitoring,
    and multi-channel notifications for production environments
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize monitoring components
        self.health_monitor = HealthMonitor(config.get('health_monitoring', {}))
        self.performance_monitor = PerformanceMonitor(
            monitoring_interval=config.get('performance_interval', 60)
        )
        self.notifier = MultiChannelNotifier(config.get('notifications', {}))
        
        # Alerting configuration
        self.alert_config = config.get('alerting', {})
        self.alert_cooldown = {}  # Prevent alert spam
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self, **components):
        """Initialize monitoring with application components"""
        # Register components with health monitor
        self.health_monitor.register_components(**components)
        self.performance_monitor.register_components(**components)
        
        # Initialize notification system
        await self.notifier.initialize(**components)
        
        self.logger.info("Production monitoring orchestrator initialized")
    
    async def start_monitoring(self):
        """Start all monitoring systems"""
        # Start health monitoring
        await self.health_monitor.start_monitoring()
        
        # Start performance monitoring
        await self.performance_monitor.start_monitoring()
        
        # Start alert processing
        self.alert_task = asyncio.create_task(self._alert_processing_loop())
        
        self.logger.info("All monitoring systems started")
    
    async def stop_monitoring(self):
        """Stop all monitoring systems"""
        await self.health_monitor.stop_monitoring()
        await self.performance_monitor.stop_monitoring()
        
        if hasattr(self, 'alert_task'):
            self.alert_task.cancel()
            try:
                await self.alert_task
            except asyncio.CancelledError:
                pass
        
        await self.notifier.cleanup()
        self.logger.info("All monitoring systems stopped")
    
    async def _alert_processing_loop(self):
        """Process alerts from health and performance monitors"""
        while True:
            try:
                # Check health status
                await self._process_health_alerts()
                
                # Check performance metrics
                await self._process_performance_alerts()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(30)
    
    async def _process_health_alerts(self):
        """Process health monitoring alerts"""
        health_report = self.health_monitor.get_health_report()
        
        # Check overall system health
        if health_report['system_status'] == 'unhealthy':
            await self._send_alert(
                "Critical system health issue detected",
                {
                    'alert_type': 'system_health',
                    'severity': 'critical',
                    'system_status': health_report['system_status'],
                    'failed_checks': [
                        name for name, status in health_report['checks'].items()
                        if status['status'] == 'unhealthy'
                    ]
                },
                priority="critical"
            )
        elif health_report['system_status'] == 'degraded':
            await self._send_alert(
                "System performance degradation detected",
                {
                    'alert_type': 'system_degradation',
                    'severity': 'high',
                    'system_status': health_report['system_status'],
                    'degraded_checks': [
                        name for name, status in health_report['checks'].items()
                        if status['status'] in ['degraded', 'unhealthy']
                    ]
                },
                priority="high"
            )
    
    async def _process_performance_alerts(self):
        """Process performance monitoring alerts"""
        if not self.performance_monitor.metrics_history:
            return
        
        latest_metrics = self.performance_monitor.metrics_history[-1]
        alerts = []
        
        # Check CPU usage
        if latest_metrics.cpu_percent > self.performance_monitor.thresholds['cpu_percent']:
            alerts.append({
                'type': 'high_cpu',
                'message': f"High CPU usage: {latest_metrics.cpu_percent:.1f}%",
                'value': latest_metrics.cpu_percent,
                'threshold': self.performance_monitor.thresholds['cpu_percent']
            })
        
        # Check memory usage
        if latest_metrics.memory_percent > self.performance_monitor.thresholds['memory_percent']:
            alerts.append({
                'type': 'high_memory',
                'message': f"High memory usage: {latest_metrics.memory_percent:.1f}%",
                'value': latest_metrics.memory_percent,
                'threshold': self.performance_monitor.thresholds['memory_percent']
            })
        
        # Send performance alerts
        for alert in alerts:
            await self._send_alert(
                f"Performance Alert: {alert['message']}",
                {
                    'alert_type': 'performance',
                    'severity': 'high',
                    'metric_type': alert['type'],
                    'current_value': alert['value'],
                    'threshold': alert['threshold']
                },
                priority="high"
            )
    
    async def _send_alert(self, message: str, context: Dict[str, Any], priority: str = "normal"):
        """Send alert with cooldown management"""
        alert_key = f"{context.get('alert_type', 'unknown')}_{context.get('metric_type', '')}"
        
        # Check cooldown
        cooldown_duration = self.alert_config.get('cooldown_minutes', 15) * 60
        if alert_key in self.alert_cooldown:
            time_since_last = time.time() - self.alert_cooldown[alert_key]
            if time_since_last < cooldown_duration:
                return  # Still in cooldown
        
        # Send alert
        success = await self.notifier.send_notification(
            message,
            message_type="alert",
            priority=priority
        )
        
        if success:
            self.alert_cooldown[alert_key] = time.time()
            self.logger.info(f"Alert sent: {message}")
        else:
            self.logger.error(f"Failed to send alert: {message}")
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'health': self.health_monitor.get_health_report(),
            'performance': self.performance_monitor.get_performance_report(hours=1),
            'alert_status': {
                'active_cooldowns': len(self.alert_cooldown),
                'last_alert_times': {
                    key: datetime.fromtimestamp(timestamp).isoformat()
                    for key, timestamp in self.alert_cooldown.items()
                }
            }
        }

# Global monitoring orchestrator
monitoring_orchestrator = ProductionMonitoringOrchestrator({})
```

### 🎯 Usage Examples

#### **Basic Monitoring Setup**
```python
# Initialize monitoring in your main application
async def setup_monitoring(app_components):
    config = {
        'health_monitoring': {
            'enabled': True,
            'check_interval': 60
        },
        'performance_interval': 30,
        'notifications': {
            'telegram': {'enabled': True, 'notification_targets': ['@admin']},
            'sms': {'enabled': True, 'sms_targets': ['+1234567890']}
        },
        'alerting': {
            'cooldown_minutes': 15
        }
    }
    
    orchestrator = ProductionMonitoringOrchestrator(config)
    await orchestrator.initialize(
        resource_manager=app_components['resource_manager'],
        cache_manager=app_components['cache_manager'],
        ai_router=app_components['ai_router']
    )
    
    await orchestrator.start_monitoring()
    return orchestrator
```

#### **Custom Health Checks**
```python
async def custom_api_health_check():
    """Custom health check for external API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.external-service.com/health', timeout=10) as response:
                if response.status == 200:
                    return HealthCheckResult(
                        name="external_api",
                        status=HealthStatus.HEALTHY,
                        message="External API responding",
                        execution_time=0.0
                    )
                else:
                    return HealthCheckResult(
                        name="external_api",
                        status=HealthStatus.DEGRADED,
                        message=f"External API returned {response.status}",
                        execution_time=0.0
                    )
    except Exception as e:
        return HealthCheckResult(
            name="external_api",
            status=HealthStatus.UNHEALTHY,
            message=f"External API check failed: {e}",
            execution_time=0.0
        )

# Register custom health check
health_monitor.register_health_check(HealthCheck(
    name="external_api",
    check_function=custom_api_health_check,
    critical=False,
    interval=120,
    description="Monitor external API availability"
))
```
## 14. Task Scheduler Integration & OS-Specific Deployment
## 📅 **Task Scheduler Integration & OS-Specific Deployment**

### **OS Detection & Configuration**
- **Always include OS detection** in project setup to generate platform-specific scheduler configs
- **Generate complete scheduler configurations** - users should get ready-to-deploy scheduler setups
- **Include both cron AND systemd** for Linux to provide flexibility
- **Create PowerShell automation scripts** for Windows Task Scheduler setup

### **Windows Task Scheduler Configuration**
```python
# Auto-generate Windows Task Scheduler XML template
def generate_windows_task_xml(project_name, python_path, script_path, schedule_cron):
    """Generate Windows Task Scheduler XML configuration"""
    # Convert cron to Windows schedule format
    # Include proper error handling and logging paths
    # Set up proper user context and privileges
```

**Required Components:**
- XML task definition template
- PowerShell setup script (`setup_windows_scheduler.ps1`)
- Batch file wrapper for Python script execution
- Windows Event Log integration for monitoring

### **Linux Scheduler Configuration** 
```python
# Auto-generate both cron and systemd configurations
def generate_linux_cron(project_name, user, python_path, script_path, schedule):
    """Generate crontab entry with proper logging"""
    
def generate_systemd_service(project_name, user, python_path, script_path):
    """Generate systemd service + timer files"""
    # Include proper user, working directory, environment
    # Set up restart policies and failure handling
```

**Required Components:**
- Crontab entry generation with logging redirection
- Systemd service file (`project-name.service`)
- Systemd timer file (`project-name.timer`) 
- Installation script (`setup_linux_scheduler.sh`)

### **Enhanced .env Template Generation**
```bash
# Scheduler Configuration
SCHEDULE_ENABLED=true
SCHEDULE_CRON="0 */6 * * *"  # Every 6 hours
SCHEDULE_TIMEZONE="America/New_York"
LOG_LEVEL=INFO
LOG_FILE_PATH="/var/log/project-name/app.log"  # Linux
# LOG_FILE_PATH="C:\ProgramData\ProjectName\logs\app.log"  # Windows

# Platform Detection (auto-set)
PLATFORM=linux  # or windows
PYTHON_PATH=/usr/bin/python3  # auto-detected
PROJECT_PATH=/opt/project-name  # auto-detected
```

### **Scheduler Setup Scripts Generation**
- **Windows**: `scripts/setup_scheduler.ps1` - Import XML task, set permissions
- **Linux**: `scripts/setup_scheduler.sh` - Install cron/systemd, enable services
- **Cross-platform**: `setup_scheduler.py` - Detect OS and call appropriate setup

### **Logging & Monitoring for Scheduled Tasks**
- **Always configure file logging** for scheduled executions (no console output)
- **Include rotation policies** to prevent log file growth
- **Add health check endpoints** for monitoring scheduled task status
- **Generate monitoring scripts** that can be called by external systems

### **Error Handling for Unattended Execution**
```python
# Enhanced error handling for scheduled execution
def scheduled_main():
    """Main function optimized for scheduled execution"""
    try:
        # Setup file logging
        # Load environment variables with validation
        # Include failure notification system
        # Implement graceful shutdown handling
        # Add database connection retry logic
    except Exception as e:
        # Log to file AND system event log
        # Optional: Send notification (email/Slack/etc.)
        # Ensure clean resource cleanup
        sys.exit(1)  # Proper exit code for scheduler
```

### **Scheduler Integration Anti-Patterns to Avoid**
1. **Missing absolute paths**: Always use full paths in scheduler configs
2. **Environment variable isolation**: Scheduled tasks lose shell environment
3. **No failure notifications**: Silent failures in production
4. **Shared resource conflicts**: Multiple scheduled instances running simultaneously
5. **Insufficient permissions**: Task runs with limited user context
6. **Missing working directory**: Scripts fail due to relative path assumptions

### **Platform-Specific Considerations**

**Windows Specifics:**
- Run with proper user account (not SYSTEM unless necessary)
- Handle Windows path separators and spaces in paths
- Include UAC considerations for elevated tasks
- Use Windows Event Log for centralized logging

**Linux Specifics:**
- Consider user vs system cron differences
- Handle systemd vs SysV init variations
- Set proper file permissions and ownership
- Include logrotate configuration for log management

### **Testing Scheduled Tasks**
- **Provide manual execution scripts** that simulate scheduled environment
- **Include dry-run modes** for testing without side effects
- **Generate test schedulers** that run every minute for validation
- **Create monitoring dashboard** for scheduled task health

### **Scheduler Configuration Template Generation**
```python
def setup_project_scheduler(project_name, schedule_cron="0 6 * * *"):
    """Auto-generate complete scheduler setup for current OS"""
    os_type = platform.system().lower()
    
    if os_type == "windows":
        generate_windows_task_xml()
        generate_powershell_setup_script()
        generate_batch_wrapper()
    elif os_type == "linux":
        generate_cron_config()
        generate_systemd_files()
        generate_bash_setup_script()
    
    generate_cross_platform_env_template()
    generate_monitoring_scripts()
    generate_documentation()
```

---

*These guidelines prevent recursive debugging cycles and ensure architectural changes are implemented correctly on the first attempt.*

## 15. Deployment Considerations

### 🐳 Container Deployment

#### **Production-Ready Dockerfile**

```dockerfile
# Multi-stage build for optimized production images
FROM python:3.11-slim as builder

# Build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p data logs backups && \
    chown -R appuser:appuser data logs backups

# Security: Run as non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=10)" || exit 1

# Expose port
EXPOSE 8000

# Use exec form for proper signal handling
CMD ["python", "main.py"]
```

#### **Docker Compose for Development and Production**

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      target: production
    container_name: telegram_extractor
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
      - MONITORING_ENABLED=true
      - NOTIFICATIONS_ENABLED=true
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
      - ./backups:/app/backups:rw
    ports:
      - "8000:8000"
    networks:
      - app_network
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  redis:
    image: redis:7-alpine
    container_name: telegram_extractor_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  postgres:
    image: postgres:15-alpine
    container_name: telegram_extractor_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: telegram_extractor
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups/postgres:/backups
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d telegram_extractor"]
      interval: 10s
      timeout: 5s
      retries: 3

  monitoring:
    image: prom/prometheus:latest
    container_name: telegram_extractor_monitoring
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - app_network

volumes:
  redis_data:
  postgres_data:
  prometheus_data:

networks:
  app_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### **Environment-Specific Configurations**

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=telegram_extractor
DB_USER=app_user
DB_PASSWORD=your_secure_password_here
DB_POOL_SIZE=10

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# AI Services
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Telegram
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_PATH=/app/data/sessions

# Notifications
NOTIFICATIONS_ENABLED=true
TELEGRAM_NOTIFICATIONS_ENABLED=true
TELEGRAM_TARGETS=@admin_channel
SMS_NOTIFICATIONS_ENABLED=true
SMS_TARGETS=+1234567890
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_FROM_NUMBER=+1234567890

# Monitoring
MONITORING_ENABLED=true
PERFORMANCE_MONITORING=true
HEALTH_CHECK_INTERVAL=30

# Resource Limits
MAX_DB_CONNECTIONS=10
MAX_MEMORY_MB=1024
MAX_CPU_PERCENT=80
CLEANUP_INTERVAL=300
```

### ☸️ Kubernetes Orchestration

#### **Kubernetes Deployment Manifests**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: telegram-extractor
  labels:
    app: telegram-extractor
    environment: production

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: telegram-extractor-config
  namespace: telegram-extractor
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  MONITORING_ENABLED: "true"
  NOTIFICATIONS_ENABLED: "true"
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "telegram_extractor"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: telegram-extractor-secrets
  namespace: telegram-extractor
type: Opaque
stringData:
  DB_PASSWORD: "your_secure_password"
  ANTHROPIC_API_KEY: "your_anthropic_api_key"
  OPENAI_API_KEY: "your_openai_api_key"
  TELEGRAM_API_ID: "your_api_id"
  TELEGRAM_API_HASH: "your_api_hash"
  TWILIO_ACCOUNT_SID: "your_twilio_sid"
  TWILIO_AUTH_TOKEN: "your_twilio_token"

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: telegram-extractor
  namespace: telegram-extractor
  labels:
    app: telegram-extractor
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: telegram-extractor
  template:
    metadata:
      labels:
        app: telegram-extractor
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: telegram-extractor
        image: telegram-extractor:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: telegram-extractor-config
        - secretRef:
            name: telegram-extractor-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: logs-volume
          mountPath: /app/logs
        - name: backups-volume
          mountPath: /app/backups
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: telegram-extractor-data
      - name: logs-volume
        persistentVolumeClaim:
          claimName: telegram-extractor-logs
      - name: backups-volume
        persistentVolumeClaim:
          claimName: telegram-extractor-backups

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: telegram-extractor-service
  namespace: telegram-extractor
  labels:
    app: telegram-extractor
spec:
  selector:
    app: telegram-extractor
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: telegram-extractor-ingress
  namespace: telegram-extractor
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - telegram-extractor.yourdomain.com
    secretName: telegram-extractor-tls
  rules:
  - host: telegram-extractor.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: telegram-extractor-service
            port:
              number: 80

---
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: telegram-extractor-data
  namespace: telegram-extractor
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: telegram-extractor-logs
  namespace: telegram-extractor
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: standard

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: telegram-extractor-backups
  namespace: telegram-extractor
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: backup-storage
```

#### **Horizontal Pod Autoscaler**

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: telegram-extractor-hpa
  namespace: telegram-extractor
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: telegram-extractor
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### 🚀 CI/CD Pipeline Patterns

#### **GitHub Actions Workflow**

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: telegram-extractor

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Type check with mypy
      run: mypy src
    
    - name: Test with pytest
      run: |
        pytest tests/ --cov=src --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  security:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Security check with bandit
      run: |
        pip install bandit
        bandit -r src/
    
    - name: Check for vulnerabilities with safety
      run: |
        pip install safety
        safety check

  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        target: production
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to staging
      run: |
        # Update staging environment
        kubectl set image deployment/telegram-extractor telegram-extractor=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:develop-${{ github.sha }} -n telegram-extractor-staging

  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to production
      run: |
        # Blue-green deployment
        kubectl apply -f k8s/ -n telegram-extractor
        kubectl set image deployment/telegram-extractor telegram-extractor=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest -n telegram-extractor
        kubectl rollout status deployment/telegram-extractor -n telegram-extractor
```

#### **Deployment Scripts**

```bash
#!/bin/bash
# scripts/deploy.sh

set -euo pipefail

ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}
NAMESPACE="telegram-extractor-${ENVIRONMENT}"

echo "🚀 Deploying to ${ENVIRONMENT} environment..."

# Verify environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo "❌ Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

# Check if kubectl is available and configured
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ kubectl not configured or cluster not accessible"
    exit 1
fi

# Create namespace if it doesn't exist
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations
echo "📝 Applying Kubernetes manifests..."
kubectl apply -f k8s/ -n "${NAMESPACE}"

# Update image
echo "🐳 Updating container image to ${IMAGE_TAG}..."
kubectl set image deployment/telegram-extractor \
    telegram-extractor="ghcr.io/telegram-extractor:${IMAGE_TAG}" \
    -n "${NAMESPACE}"

# Wait for rollout
echo "⏳ Waiting for deployment rollout..."
kubectl rollout status deployment/telegram-extractor -n "${NAMESPACE}" --timeout=300s

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -n "${NAMESPACE}" -l app=telegram-extractor

# Run health check
echo "🏥 Running health check..."
if kubectl exec -n "${NAMESPACE}" \
    deployment/telegram-extractor -- \
    python -c "import requests; requests.get('http://localhost:8000/health', timeout=10)"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

echo "🎉 Deployment to ${ENVIRONMENT} completed successfully!"
```

### 📈 Production Scaling Strategies

#### **Auto-Scaling Configuration**

```python
# src/config/scaling.py
from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class ScalingConfig:
    """Production scaling configuration"""
    
    # Horizontal scaling
    min_replicas: int = 2
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80
    
    # Vertical scaling
    base_cpu_request: str = "250m"
    base_memory_request: str = "512Mi"
    max_cpu_limit: str = "1"
    max_memory_limit: str = "2Gi"
    
    # Application-specific scaling
    max_concurrent_requests: int = 100
    request_timeout: int = 300
    worker_count: int = 4
    
    # Database scaling
    db_pool_min: int = 5
    db_pool_max: int = 20
    db_pool_scale_factor: float = 0.7
    
    # Cache scaling
    cache_max_memory: str = "512mb"
    cache_eviction_policy: str = "allkeys-lru"
    
    @classmethod
    def from_environment(cls) -> 'ScalingConfig':
        """Load scaling configuration from environment"""
        return cls(
            min_replicas=int(os.getenv('SCALING_MIN_REPLICAS', 2)),
            max_replicas=int(os.getenv('SCALING_MAX_REPLICAS', 10)),
            target_cpu_utilization=int(os.getenv('SCALING_CPU_TARGET', 70)),
            target_memory_utilization=int(os.getenv('SCALING_MEMORY_TARGET', 80)),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', 100)),
            worker_count=int(os.getenv('WORKER_COUNT', 4)),
            db_pool_max=int(os.getenv('DB_POOL_MAX', 20))
        )

class ProductionScalingManager:
    """Manages application scaling based on load and metrics"""
    
    def __init__(self, config: ScalingConfig):
        self.config = config
        self.current_load_metrics = {}
        self.scaling_history = []
        
    async def monitor_and_scale(self):
        """Monitor system metrics and trigger scaling if needed"""
        metrics = await self._collect_scaling_metrics()
        
        # Determine if scaling is needed
        scaling_decision = self._analyze_scaling_needs(metrics)
        
        if scaling_decision['action'] != 'none':
            await self._execute_scaling(scaling_decision)
    
    async def _collect_scaling_metrics(self) -> Dict[str, Any]:
        """Collect metrics relevant to scaling decisions"""
        return {
            'cpu_utilization': await self._get_cpu_utilization(),
            'memory_utilization': await self._get_memory_utilization(),
            'request_queue_size': await self._get_request_queue_size(),
            'response_time_p95': await self._get_response_time_percentile(95),
            'error_rate': await self._get_error_rate(),
            'active_connections': await self._get_active_connections()
        }
    
    def _analyze_scaling_needs(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metrics to determine scaling needs"""
        scale_up_triggers = [
            metrics['cpu_utilization'] > self.config.target_cpu_utilization,
            metrics['memory_utilization'] > self.config.target_memory_utilization,
            metrics['response_time_p95'] > 5000,  # 5 seconds
            metrics['request_queue_size'] > 50
        ]
        
        scale_down_triggers = [
            metrics['cpu_utilization'] < self.config.target_cpu_utilization * 0.5,
            metrics['memory_utilization'] < self.config.target_memory_utilization * 0.5,
            metrics['response_time_p95'] < 1000,  # 1 second
            metrics['request_queue_size'] < 5
        ]
        
        if any(scale_up_triggers):
            return {'action': 'scale_up', 'reason': 'high_load', 'metrics': metrics}
        elif all(scale_down_triggers):
            return {'action': 'scale_down', 'reason': 'low_load', 'metrics': metrics}
        else:
            return {'action': 'none', 'reason': 'stable', 'metrics': metrics}
```

### 🛡️ Production Security Configuration

#### **Security Hardening Checklist**

```python
# src/security/production_security.py
import os
import secrets
import hashlib
from typing import Dict, Any, List
from pathlib import Path

class ProductionSecurityManager:
    """Manages production security configurations and checks"""
    
    def __init__(self):
        self.security_config = self._load_security_config()
        self.security_checks = []
        
    def _load_security_config(self) -> Dict[str, Any]:
        """Load production security configuration"""
        return {
            'enforce_https': os.getenv('ENFORCE_HTTPS', 'true').lower() == 'true',
            'api_rate_limit': int(os.getenv('API_RATE_LIMIT', 100)),
            'session_timeout': int(os.getenv('SESSION_TIMEOUT', 3600)),
            'max_file_size': int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024)),  # 10MB
            'allowed_origins': os.getenv('ALLOWED_ORIGINS', '').split(','),
            'secret_key_rotation': os.getenv('SECRET_KEY_ROTATION', 'true').lower() == 'true',
            'audit_logging': os.getenv('AUDIT_LOGGING', 'true').lower() == 'true'
        }
    
    def run_security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'issues': [],
            'recommendations': []
        }
        
        # Check file permissions
        audit_results['checks']['file_permissions'] = self._check_file_permissions()
        
        # Check environment variables
        audit_results['checks']['env_vars'] = self._check_environment_security()
        
        # Check network security
        audit_results['checks']['network'] = self._check_network_security()
        
        # Check container security
        audit_results['checks']['container'] = self._check_container_security()
        
        # Aggregate issues and recommendations
        for check_name, check_result in audit_results['checks'].items():
            if not check_result['passed']:
                audit_results['issues'].extend(check_result['issues'])
                audit_results['recommendations'].extend(check_result['recommendations'])
        
        return audit_results
    
    def _check_file_permissions(self) -> Dict[str, Any]:
        """Check file and directory permissions"""
        issues = []
        recommendations = []
        
        # Check sensitive directories
        sensitive_paths = [
            Path('data'),
            Path('logs'),
            Path('backups'),
            Path('.env'),
            Path('src/config')
        ]
        
        for path in sensitive_paths:
            if path.exists():
                stat = path.stat()
                # Check if world-readable/writable
                if stat.st_mode & 0o077:
                    issues.append(f"Insecure permissions on {path}")
                    recommendations.append(f"chmod 700 {path}")
        
        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _check_environment_security(self) -> Dict[str, Any]:
        """Check environment variable security"""
        issues = []
        recommendations = []
        
        # Check for exposed secrets
        sensitive_vars = [
            'API_KEY', 'SECRET_KEY', 'PASSWORD', 'TOKEN', 'PRIVATE_KEY'
        ]
        
        for var_name, var_value in os.environ.items():
            if any(secret in var_name.upper() for secret in sensitive_vars):
                if len(var_value) < 32:
                    issues.append(f"Weak secret in {var_name}")
                    recommendations.append(f"Use stronger secret for {var_name}")
        
        # Check for debug mode in production
        if os.getenv('DEBUG', 'false').lower() == 'true':
            issues.append("Debug mode enabled in production")
            recommendations.append("Set DEBUG=false in production")
        
        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations
        }

# Security middleware
class SecurityMiddleware:
    """Production security middleware"""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        # Add security headers
        if scope['type'] == 'http':
            # Implement security headers
            pass
        
        return await self.app(scope, receive, send)
```

### 📊 Production Monitoring Setup

#### **Prometheus Configuration**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'telegram-extractor'
    static_configs:
      - targets: ['telegram-extractor-service:80']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### **Grafana Dashboard Configuration**

```json
{
  "dashboard": {
    "title": "Telegram Extractor - Production Dashboard",
    "panels": [
      {
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"telegram-extractor\"}",
            "legendFormat": "Service Status"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 🔄 Backup and Disaster Recovery

#### **Automated Backup Strategy**

```bash
#!/bin/bash
# scripts/backup.sh

set -euo pipefail

BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=30

echo "🔄 Starting backup process..."

# Database backup
echo "📊 Backing up database..."
pg_dump "${DATABASE_URL}" | gzip > "${BACKUP_DIR}/database_${TIMESTAMP}.sql.gz"

# Application data backup
echo "📁 Backing up application data..."
tar -czf "${BACKUP_DIR}/data_${TIMESTAMP}.tar.gz" -C /app data/

# Configuration backup
echo "⚙️ Backing up configuration..."
tar -czf "${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz" -C /app src/config/

# Upload to cloud storage (AWS S3 example)
if [[ "${CLOUD_BACKUP_ENABLED:-false}" == "true" ]]; then
    echo "☁️ Uploading to cloud storage..."
    aws s3 cp "${BACKUP_DIR}/" "s3://${BACKUP_BUCKET}/backups/" --recursive
fi

# Clean up old backups
echo "🧹 Cleaning up old backups..."
find "${BACKUP_DIR}" -name "*.gz" -mtime +${RETENTION_DAYS} -delete

echo "✅ Backup completed successfully"
```

#### **Disaster Recovery Procedures**

```bash
#!/bin/bash
# scripts/restore.sh

set -euo pipefail

BACKUP_FILE=${1:-}
RESTORE_TYPE=${2:-full}

if [[ -z "${BACKUP_FILE}" ]]; then
    echo "Usage: $0 <backup_file> [restore_type]"
    echo "Restore types: full, database, data, config"
    exit 1
fi

echo "🔄 Starting restore process..."

case "${RESTORE_TYPE}" in
    "database"|"full")
        echo "📊 Restoring database..."
        zcat "${BACKUP_FILE}" | psql "${DATABASE_URL}"
        ;;
    "data"|"full")
        echo "📁 Restoring application data..."
        tar -xzf "${BACKUP_FILE}" -C /app
        ;;
    "config"|"full")
        echo "⚙️ Restoring configuration..."
        tar -xzf "${BACKUP_FILE}" -C /app
        ;;
esac

echo "✅ Restore completed successfully"
echo "🔄 Please restart the application to apply changes"
```

### 🎯 Production Optimization Checklist

#### **Performance Optimization**
- [ ] Enable connection pooling for databases
- [ ] Implement caching layers (Redis/Memcached)
- [ ] Use async/await for I/O operations
- [ ] Optimize database queries and indexing
- [ ] Enable gzip compression for responses
- [ ] Implement CDN for static assets
- [ ] Use multi-stage Docker builds
- [ ] Configure proper resource limits

#### **Security Hardening**
- [ ] Run containers as non-root user
- [ ] Use secrets management (Kubernetes secrets/Vault)
- [ ] Enable network policies
- [ ] Implement rate limiting
- [ ] Use HTTPS everywhere
- [ ] Regular security audits
- [ ] Dependency vulnerability scanning
- [ ] Log all security events

#### **Monitoring & Observability**
- [ ] Comprehensive health checks
- [ ] Performance metrics collection
- [ ] Error tracking and alerting
- [ ] Distributed tracing
- [ ] Log aggregation and analysis
- [ ] Business metrics monitoring
- [ ] SLA/SLO monitoring
- [ ] Capacity planning metrics

#### **Reliability & Scalability**
- [ ] Horizontal pod autoscaling
- [ ] Circuit breaker patterns
- [ ] Graceful shutdown handling
- [ ] Zero-downtime deployments
- [ ] Database replication
- [ ] Backup and disaster recovery
- [ ] Load testing and capacity planning
- [ ] Multi-region deployment

---

*This deployment guide provides production-ready patterns for deploying and scaling robust Python applications with comprehensive monitoring, security, and operational excellence.*