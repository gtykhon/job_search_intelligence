"""
Configuration Management for Job Search Intelligence
Based on enhanced Python guidelines with comprehensive validation
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class AnalysisMode(Enum):
    QUICK = "quick"          # Basic analysis
    STANDARD = "standard"    # Full analysis
    DEEP = "deep"           # Deep analysis with AI insights
    INTELLIGENCE = "intelligence"  # Full intelligence analysis

@dataclass
class LinkedInConfig:
    """LinkedIn API configuration"""
    username: str = ""
    password: str = ""
    session_timeout: int = 3600
    max_retries: int = 3
    request_delay: float = 2.0
    batch_size: int = 50
    cache_duration: int = 86400  # 24 hours
    
    def __post_init__(self):
        if not self.username:
            self.username = os.getenv('LINKEDIN_USERNAME', '')
        if not self.password:
            self.password = os.getenv('LINKEDIN_PASSWORD', '')
        
        if not all([self.username, self.password]):
            raise ValueError("LinkedIn credentials are required")

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    min_delay: float = 2.0
    max_delay: float = 5.0
    penalty_delay: int = 60
    max_requests_per_minute: int = 10
    max_requests_per_hour: int = 300
    max_requests_per_day: int = 5000
    conservative_mode: bool = False
    conservative_multiplier: float = 2.0
    session_timeout: int = 3600
    max_consecutive_errors: int = 5
    cooldown_after_errors: int = 300
    exponential_backoff: bool = True
    randomize_delays: bool = True
    respect_robots_txt: bool = True
    
    def __post_init__(self):
        # Load from environment
        self.min_delay = float(os.getenv('RATE_LIMIT_MIN_DELAY', self.min_delay))
        self.max_delay = float(os.getenv('RATE_LIMIT_MAX_DELAY', self.max_delay))
        self.penalty_delay = int(os.getenv('RATE_LIMIT_PENALTY_DELAY', self.penalty_delay))
        self.max_requests_per_minute = int(os.getenv('RATE_LIMIT_MAX_PER_MINUTE', self.max_requests_per_minute))
        self.max_requests_per_hour = int(os.getenv('RATE_LIMIT_MAX_PER_HOUR', self.max_requests_per_hour))
        self.max_requests_per_day = int(os.getenv('RATE_LIMIT_MAX_PER_DAY', self.max_requests_per_day))
        self.conservative_mode = os.getenv('RATE_LIMIT_CONSERVATIVE_MODE', 'false').lower() == 'true'
        self.conservative_multiplier = float(os.getenv('RATE_LIMIT_CONSERVATIVE_MULTIPLIER', self.conservative_multiplier))
        self.session_timeout = int(os.getenv('RATE_LIMIT_SESSION_TIMEOUT', self.session_timeout))
        self.max_consecutive_errors = int(os.getenv('RATE_LIMIT_MAX_CONSECUTIVE_ERRORS', self.max_consecutive_errors))
        self.cooldown_after_errors = int(os.getenv('RATE_LIMIT_COOLDOWN_AFTER_ERRORS', self.cooldown_after_errors))
        self.exponential_backoff = os.getenv('RATE_LIMIT_EXPONENTIAL_BACKOFF', 'true').lower() == 'true'
        self.randomize_delays = os.getenv('RATE_LIMIT_RANDOMIZE_DELAYS', 'true').lower() == 'true'
        self.respect_robots_txt = os.getenv('RATE_LIMIT_RESPECT_ROBOTS_TXT', 'true').lower() == 'true'
        
        # Validate configuration
        if self.min_delay < 0:
            raise ValueError("min_delay must be non-negative")
        if self.max_delay < self.min_delay:
            raise ValueError("max_delay must be >= min_delay")
        if self.max_requests_per_minute <= 0:
            raise ValueError("max_requests_per_minute must be positive")
        if self.max_requests_per_hour < self.max_requests_per_minute:
            raise ValueError("max_requests_per_hour must be >= max_requests_per_minute")
        if self.max_requests_per_day < self.max_requests_per_hour:
            raise ValueError("max_requests_per_day must be >= max_requests_per_hour")

@dataclass
class AIConfig:
    """AI integration configuration"""
    enabled: bool = True
    provider: str = "claude"  # claude, openai, ollama, lmstudio, textgen, localai, custom
    api_key: str = ""
    # Default to a current Sonnet model; can be overridden via AI_MODEL env var
    model: str = "claude-3-7-sonnet-latest"
    max_tokens: int = 4000
    temperature: float = 0.2
    timeout: int = 30
    max_retries: int = 3
    
    # Local LLM HTTP endpoints
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    lmstudio_host: str = "http://localhost:1234"
    lmstudio_model: str = "llama-3.1-8b-instruct"
    textgen_host: str = "http://localhost:5000"
    localai_host: str = "http://localhost:8080"
    localai_model: str = "gpt-3.5-turbo"
    custom_host: str = "http://localhost:8000"
    custom_model: str = "custom-model"
    custom_headers: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        # Load configuration from environment
        # Allow overriding the base model via environment
        self.model = os.getenv('AI_MODEL', self.model)

        if not self.api_key:
            if self.provider == "claude":
                self.api_key = os.getenv('ANTHROPIC_API_KEY', '')
            elif self.provider == "openai":
                self.api_key = os.getenv('OPENAI_API_KEY', '')
        
        # Load local LLM settings from environment
        self.ollama_host = os.getenv('OLLAMA_HOST', self.ollama_host)
        self.ollama_model = os.getenv('OLLAMA_MODEL', self.ollama_model)
        self.lmstudio_host = os.getenv('LMSTUDIO_HOST', self.lmstudio_host)
        self.lmstudio_model = os.getenv('LMSTUDIO_MODEL', self.lmstudio_model)
        self.textgen_host = os.getenv('TEXTGEN_HOST', self.textgen_host)
        self.localai_host = os.getenv('LOCALAI_HOST', self.localai_host)
        self.localai_model = os.getenv('LOCALAI_MODEL', self.localai_model)
        self.custom_host = os.getenv('CUSTOM_LLM_HOST', self.custom_host)
        self.custom_model = os.getenv('CUSTOM_LLM_MODEL', self.custom_model)
        
        # Initialize custom headers if not set
        if self.custom_headers is None:
            self.custom_headers = {}
        
        # Validate configuration based on provider
        if self.provider in ["claude", "openai"] and not self.api_key:
            self.enabled = False
            logger = logging.getLogger(__name__)
            logger.warning("AI features disabled: No API key found for provider '%s'", self.provider)
        elif self.provider in ["ollama", "lmstudio", "textgen", "localai", "custom"]:
            # Local providers don't need API keys, just endpoint validation
            self.enabled = True
            logger = logging.getLogger(__name__)
            logger.info("AI configured for local provider '%s'", self.provider)

@dataclass
class NotificationConfig:
    """Notification system configuration"""
    enabled: bool = True
    channels: List[str] = field(default_factory=lambda: ["console"])
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Load from environment
        self.enabled = os.getenv('NOTIFICATIONS_ENABLED', 'true').lower() == 'true'
        
        # Telegram configuration
        self.telegram_enabled = os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
        if not self.telegram_bot_token:
            self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        if not self.telegram_chat_id:
            self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # Email configuration
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        if not self.email_smtp_server:
            self.email_smtp_server = os.getenv('EMAIL_SMTP_SERVER', '')
        if not self.email_username:
            self.email_username = os.getenv('EMAIL_USERNAME', '')
        if not self.email_password:
            self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
        # Validate Telegram configuration if enabled
        if self.telegram_enabled and not all([self.telegram_bot_token, self.telegram_chat_id]):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Telegram enabled but configuration incomplete. Disabling Telegram notifications.")
            self.telegram_enabled = False

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    enabled: bool = True
    health_check_interval: int = 60
    performance_monitoring: bool = True
    metrics_retention_days: int = 30
    log_level: str = "INFO"
    structured_logging: bool = True
    
    def __post_init__(self):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")

@dataclass
class ResourceConfig:
    """Resource management configuration"""
    max_concurrent_requests: int = 5
    connection_pool_size: int = 10
    connection_timeout: int = 30
    cleanup_interval: int = 300
    session_isolation: bool = True
    conflict_prevention: bool = True
    
    def __post_init__(self):
        if self.max_concurrent_requests < 1:
            raise ValueError("Must have at least 1 concurrent request")

@dataclass
class StorageConfig:
    """Data storage configuration"""
    data_directory: Path = Path("data")
    cache_directory: Path = Path("data/cache")
    output_directory: Path = Path("output")
    logs_directory: Path = Path("logs")
    backup_enabled: bool = True
    backup_retention_days: int = 30
    compression_enabled: bool = True
    
    def __post_init__(self):
        # Ensure directories exist
        for directory in [self.data_directory, self.cache_directory, 
                         self.output_directory, self.logs_directory]:
            directory.mkdir(parents=True, exist_ok=True)

@dataclass
class AnalysisConfig:
    """Analysis configuration"""
    mode: AnalysisMode = AnalysisMode.STANDARD
    include_connections: bool = True
    include_followers: bool = True
    include_posts: bool = False
    include_companies: bool = True
    ai_insights: bool = True
    pattern_detection: bool = True
    relationship_mapping: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv"])
    
    def __post_init__(self):
        if self.mode == AnalysisMode.QUICK:
            # Quick mode - minimal analysis
            self.include_posts = False
            self.ai_insights = False
        elif self.mode == AnalysisMode.INTELLIGENCE:
            # Intelligence mode - full analysis
            self.include_posts = True
            self.ai_insights = True
            self.pattern_detection = True
            self.relationship_mapping = True

@dataclass
class AppSettings:
    """Application-specific settings"""
    output_dir: str = "output"
    data_dir: str = "data"
    logs_dir: str = "logs"
    cache_dir: str = "cache"
    
    def __post_init__(self):
        # Ensure directories exist
        from pathlib import Path
        for dir_path in [self.output_dir, self.data_dir, self.logs_dir, self.cache_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

@dataclass
class AppConfig:
    """Main application configuration"""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # Component configurations
    app: AppSettings = field(default_factory=AppSettings)
    linkedin: LinkedInConfig = field(default_factory=LinkedInConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    resources: ResourceConfig = field(default_factory=ResourceConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    
    def __post_init__(self):
        # Environment-specific validations
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("Debug mode not allowed in production")
            if self.monitoring.log_level == "DEBUG":
                raise ValueError("Debug logging not recommended in production")
    
    def validate(self) -> List[str]:
        """Comprehensive configuration validation"""
        errors = []
        
        # Validate component configurations
        try:
            self.linkedin.__post_init__()
        except ValueError as e:
            errors.append(f"LinkedIn config: {e}")
        
        try:
            self.rate_limit.__post_init__()
        except ValueError as e:
            errors.append(f"Rate limit config: {e}")
        
        try:
            self.ai.__post_init__()
        except ValueError as e:
            errors.append(f"AI config: {e}")
        
        try:
            self.notifications.__post_init__()
        except ValueError as e:
            errors.append(f"Notifications config: {e}")
        
        try:
            self.monitoring.__post_init__()
        except ValueError as e:
            errors.append(f"Monitoring config: {e}")
        
        try:
            self.resources.__post_init__()
        except ValueError as e:
            errors.append(f"Resources config: {e}")
        
        # Production-specific validations
        if self.environment == Environment.PRODUCTION:
            if not self.ai.api_key and self.ai.enabled:
                errors.append("AI API key required when AI is enabled in production")
            if not self.monitoring.enabled:
                errors.append("Monitoring should be enabled in production")
        
        return errors
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'AppConfig':
        """Load configuration from environment variables"""
        if env_file:
            load_dotenv(env_file)
        
        # Parse environment
        env = Environment(os.getenv('ENVIRONMENT', 'development'))
        
        # Create component configs
        app_settings = AppSettings(
            output_dir=os.getenv('OUTPUT_DIR', 'output'),
            data_dir=os.getenv('DATA_DIR', 'data'),
            logs_dir=os.getenv('LOGS_DIR', 'logs'),
            cache_dir=os.getenv('CACHE_DIR', 'cache')
        )
        
        linkedin_config = LinkedInConfig()
        
        rate_limit_config = RateLimitConfig()
        
        ai_config = AIConfig(
            enabled=os.getenv('AI_ENABLED', 'true').lower() == 'true',
            provider=os.getenv('AI_PROVIDER', 'claude'),
            model=os.getenv('AI_MODEL', 'claude-3-sonnet-20240229'),
            max_tokens=int(os.getenv('AI_MAX_TOKENS', 4000)),
            temperature=float(os.getenv('AI_TEMPERATURE', 0.2))
        )
        
        notification_config = NotificationConfig(
            enabled=os.getenv('NOTIFICATIONS_ENABLED', 'true').lower() == 'true',
            telegram_enabled=os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
        )
        
        monitoring_config = MonitoringConfig(
            enabled=os.getenv('MONITORING_ENABLED', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            performance_monitoring=os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
        )
        
        resource_config = ResourceConfig(
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', 5)),
            connection_pool_size=int(os.getenv('CONNECTION_POOL_SIZE', 10))
        )
        
        storage_config = StorageConfig(
            data_directory=Path(os.getenv('DATA_DIRECTORY', 'data')),
            backup_enabled=os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
        )
        
        analysis_config = AnalysisConfig(
            mode=AnalysisMode(os.getenv('ANALYSIS_MODE', 'standard')),
            ai_insights=os.getenv('AI_INSIGHTS', 'true').lower() == 'true' and ai_config.enabled
        )
        
        return cls(
            environment=env,
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            app=app_settings,
            linkedin=linkedin_config,
            rate_limit=rate_limit_config,
            ai=ai_config,
            notifications=notification_config,
            monitoring=monitoring_config,
            resources=resource_config,
            storage=storage_config,
            analysis=analysis_config
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

def update_config(**kwargs):
    """Update configuration values"""
    global _config
    if _config is None:
        _config = get_config()
    
    for key, value in kwargs.items():
        if hasattr(_config, key):
            setattr(_config, key, value)
        else:
            raise ValueError(f"Invalid configuration key: {key}")
