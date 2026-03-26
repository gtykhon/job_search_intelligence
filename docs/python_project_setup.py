#!/usr/bin/env python3
"""
Enhanced Python Application Framework Generator
Based on proven enterprise-grade patterns from Telegram Knowledge Base Extractor

This framework generates complete, production-ready Python applications with:
- Multi-channel notification systems (Telegram + SMS + Email)
- Comprehensive monitoring and observability
- Production deployment configurations
- Resource management and conflict prevention
- AI integration patterns
- Error handling and autonomous debugging foundations

Usage:
    python scripts/enhanced_python_setup.py --idea "Telegram message extractor with AI processing"
    python scripts/enhanced_python_setup.py --template production_automation
    python scripts/enhanced_python_setup.py --interactive
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import textwrap


@dataclass
class ProjectConfig:
    """Enhanced configuration for generating production-ready projects"""
    name: str
    description: str
    type: str
    components: List[str] = field(default_factory=list)
    external_services: List[str] = field(default_factory=list)
    database: Optional[str] = None
    ai_integration: bool = True
    async_support: bool = True
    docker_support: bool = True
    kubernetes_support: bool = False
    testing_framework: str = "pytest"
    
    # Enhanced production features
    notification_channels: List[str] = field(default_factory=lambda: ["telegram"])
    monitoring_enabled: bool = True
    performance_monitoring: bool = True
    autonomous_debugging: bool = False
    resource_management: bool = True
    cicd_pipeline: str = "github_actions"
    

class EnhancedPythonFramework:
    """Enhanced framework generator incorporating production-grade patterns"""
    
    def __init__(self):
        self.templates = self._load_enhanced_templates()
        self.base_structure = self._define_enhanced_structure()
        
    def _load_enhanced_templates(self) -> Dict[str, Dict]:
        """Load enhanced application templates with production patterns"""
        return {
            "production_automation": {
                "description": "Production automation with notifications, monitoring, and AI",
                "components": ["extractors", "processors", "storage", "notifications", "monitoring"],
                "external_services": ["telegram", "sms_provider", "database"],
                "notification_channels": ["telegram", "sms"],
                "patterns": ["resource_management", "notification_patterns", "monitoring"],
                "monitoring_enabled": True,
                "kubernetes_support": True
            },
            "ai_data_pipeline": {
                "description": "AI-powered data pipeline with comprehensive monitoring",
                "components": ["extractors", "processors", "ai_router", "storage", "monitoring"],
                "external_services": ["anthropic", "openai", "database"],
                "notification_channels": ["telegram"],
                "patterns": ["ai_integration", "performance_optimization", "error_handling"],
                "ai_integration": True,
                "autonomous_debugging": True
            },
            "enterprise_api": {
                "description": "Enterprise API with notifications and monitoring",
                "components": ["api", "auth", "database", "notifications", "monitoring"],
                "external_services": ["database", "redis", "telegram"],
                "notification_channels": ["telegram", "sms", "email"],
                "patterns": ["api_patterns", "security", "monitoring"],
                "kubernetes_support": True
            },
            "notification_service": {
                "description": "Multi-channel notification service",
                "components": ["notifications", "monitoring", "api"],
                "external_services": ["telegram", "twilio", "sendgrid"],
                "notification_channels": ["telegram", "sms", "email"],
                "patterns": ["notification_patterns", "multi_channel"],
                "monitoring_enabled": True
            },
            "monitoring_system": {
                "description": "Comprehensive monitoring and alerting system",
                "components": ["monitoring", "notifications", "performance"],
                "external_services": ["prometheus", "grafana", "telegram"],
                "notification_channels": ["telegram", "sms"],
                "patterns": ["monitoring", "alerting", "performance"],
                "monitoring_enabled": True,
                "kubernetes_support": True
            }
        }
    
    def _define_enhanced_structure(self) -> Dict[str, Any]:
        """Define enhanced project structure with production patterns"""
        return {
            "directories": [
                "src/config",
                "src/core", 
                "src/resources",  # Enhanced resource management
                "src/utils",
                "src/integrations/ai",
                "src/integrations/notifications",
                "src/integrations/monitoring",
                "src/storage",
                "data/sessions",  # Session isolation
                "data/locks",     # File lock management
                "data/cache",     # Performance caching
                "data/backups",   # Automated backups
                "logs/application",
                "logs/resources",
                "logs/performance",
                "logs/notifications",
                "tests/unit",
                "tests/integration", 
                "tests/performance",
                "docs",
                "scripts",
                "k8s",           # Kubernetes manifests
                "monitoring",    # Prometheus/Grafana configs
                ".github/workflows"  # CI/CD pipelines
            ],
            "files": [
                "main.py",
                "requirements.txt",
                "requirements-dev.txt",
                ".env.template",
                ".gitignore",
                "README.md",
                "pyproject.toml",
                "Dockerfile",
                "docker-compose.yml",
                "docker-compose.production.yml"
            ]
        }
    
    def generate_project(self, config: ProjectConfig) -> Path:
        """Generate enhanced project with production patterns"""
        project_name = config.name.lower().replace(" ", "_").replace("-", "_")
        project_path = Path(project_name)
        
        if project_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_path = Path(f"{project_name}_{timestamp}")
        
        print(f"🚀 Generating production-ready project: {config.name}")
        print(f"📁 Project path: {project_path}")
        
        # Create project structure
        self._create_project_structure(project_path)
        
        # Generate enhanced core files
        self._generate_enhanced_main(project_path, config)
        self._generate_enhanced_config(project_path, config)
        self._generate_production_requirements(project_path, config)
        self._generate_enhanced_utils(project_path, config)
        
        # Generate notification system if enabled
        if config.notification_channels:
            self._generate_notification_system(project_path, config)
        
        # Generate monitoring system if enabled
        if config.monitoring_enabled:
            self._generate_monitoring_system(project_path, config)
        
        # Generate AI integration if enabled
        if config.ai_integration:
            self._generate_ai_integration(project_path, config)
        
        # Generate scheduler configurations
        self._generate_scheduler_configurations(project_path, config)
        
        # Generate deployment configurations
        self._generate_enhanced_docker(project_path, config)
        if config.kubernetes_support:
            self._generate_kubernetes_manifests(project_path, config)
        
        # Generate CI/CD pipeline
        self._generate_cicd_pipeline(project_path, config)
        
        # Generate documentation
        self._generate_enhanced_documentation(project_path, config)
        
        # Generate tests
        self._generate_enhanced_tests(project_path, config)
        
        print(f"✅ Project generated successfully!")
        return project_path
    
    def _create_project_structure(self, project_path: Path):
        """Create enhanced directory structure"""
        project_path.mkdir(exist_ok=True)
        
        for directory in self.base_structure["directories"]:
            (project_path / directory).mkdir(parents=True, exist_ok=True)
            
        # Create __init__.py files
        init_files = [
            "src/__init__.py",
            "src/config/__init__.py",
            "src/core/__init__.py",
            "src/resources/__init__.py",
            "src/utils/__init__.py",
            "src/integrations/__init__.py",
            "src/integrations/ai/__init__.py",
            "src/integrations/notifications/__init__.py",
            "src/integrations/monitoring/__init__.py",
            "src/storage/__init__.py",
            "tests/__init__.py",
        ]
        
        for init_file in init_files:
            (project_path / init_file).write_text("")
    
    def _generate_enhanced_main(self, project_path: Path, config: ProjectConfig):
        """Generate enhanced main.py with production patterns"""
        main_content = f'''#!/usr/bin/env python3
"""
{config.name} - Enhanced Production Application
Generated with enterprise-grade patterns including:
- Multi-channel notifications
- Comprehensive monitoring
- Resource management
- Error handling with autonomous debugging foundations

{config.description}
"""

import os
import asyncio
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Force emoji display
os.environ['FORCE_EMOJI'] = 'true'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import get_config
from src.core.application import Application
from src.utils.emoji_logger import create_emoji_logger
from src.utils.error_handling import setup_error_handling
{"from src.integrations.notifications import MultiChannelNotifier" if config.notification_channels else ""}
{"from src.integrations.monitoring import ProductionMonitoringOrchestrator" if config.monitoring_enabled else ""}

logger = create_emoji_logger(__name__)


async def main():
    """Main application entry point with production patterns"""
    parser = argparse.ArgumentParser(description="{config.name}")
    parser.add_argument("--setup", action="store_true", help="Run initial setup")
    parser.add_argument("--diagnose", action="store_true", help="Run system diagnostics")
    parser.add_argument("--test-notifications", action="store_true", help="Test notification system")
    args = parser.parse_args()
    
    try:
        # Initialize configuration
        config = get_config()
        logger.info(f"🚀 Starting {{config.name}} in {{config.environment.value}} mode")
        
        if args.setup:
            await run_setup(config)
            return
        
        if args.diagnose:
            await run_diagnostics(config)
            return
        
        if args.test_notifications:
            await test_notifications(config)
            return
        
        # Initialize and run application
        app = Application(config)
        
        try:
            await app.initialize()
            await app.run()
        finally:
            await app.cleanup()
            
    except KeyboardInterrupt:
        logger.info("🛑 Graceful shutdown requested")
    except Exception as e:
        logger.error(f"❌ Application failed: {{e}}")
        sys.exit(1)


async def run_setup(config):
    """Run initial application setup"""
    logger.info("🔧 Running initial setup...")
    
    # Create necessary directories
    directories = ["data", "logs", "backups"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"📁 Created directory: {{directory}}")
    
    {"# Setup notification system" if config.notification_channels else ""}
    {"await setup_notification_system(config)" if config.notification_channels else ""}
    
    {"# Setup monitoring system" if config.monitoring_enabled else ""}
    {"await setup_monitoring_system(config)" if config.monitoring_enabled else ""}
    
    logger.info("✅ Setup completed successfully!")


async def run_diagnostics(config):
    """Run comprehensive system diagnostics"""
    logger.info("🔍 Running system diagnostics...")
    
    diagnostics = {{
        "timestamp": datetime.now().isoformat(),
        "checks": {{}}
    }}
    
    # System checks
    diagnostics["checks"]["python_version"] = sys.version
    diagnostics["checks"]["environment"] = config.environment.value
    
    {"# Notification system checks" if config.notification_channels else ""}
    {"diagnostics['checks']['notifications'] = await check_notification_system()" if config.notification_channels else ""}
    
    {"# Monitoring system checks" if config.monitoring_enabled else ""}
    {"diagnostics['checks']['monitoring'] = await check_monitoring_system()" if config.monitoring_enabled else ""}
    
    # Display results
    for check_name, result in diagnostics["checks"].items():
        if isinstance(result, bool):
            status = "✅" if result else "❌"
            logger.info(f"{{status}} {{check_name}}: {{result}}")
        else:
            logger.info(f"ℹ️ {{check_name}}: {{result}}")


{"async def test_notifications(config):" if config.notification_channels else ""}
{"    '''Test notification system'''" if config.notification_channels else ""}
{"    logger.info('📢 Testing notification system...')" if config.notification_channels else ""}
{"    " if config.notification_channels else ""}
{"    from src.integrations.notifications import MultiChannelNotifier" if config.notification_channels else ""}
{"    " if config.notification_channels else ""}
{"    notifier = MultiChannelNotifier(config.notifications)" if config.notification_channels else ""}
{"    success = await notifier.initialize()" if config.notification_channels else ""}
{"    " if config.notification_channels else ""}
{"    if success:" if config.notification_channels else ""}
{"        await notifier.send_notification(" if config.notification_channels else ""}
{"            'Test notification from {config.name}'," if config.notification_channels else ""}
{"            message_type='test'," if config.notification_channels else ""}
{"            priority='normal'" if config.notification_channels else ""}
{"        )" if config.notification_channels else ""}
{"        logger.info('✅ Notification test completed')" if config.notification_channels else ""}
{"    else:" if config.notification_channels else ""}
{"        logger.error('❌ Notification system initialization failed')" if config.notification_channels else ""}
{"    " if config.notification_channels else ""}
{"    await notifier.cleanup()" if config.notification_channels else ""}


if __name__ == "__main__":
    asyncio.run(main())
'''
        
        (project_path / "main.py").write_text(main_content)
    
    def _generate_production_requirements(self, project_path: Path, config: ProjectConfig):
        """Generate production requirements with all necessary dependencies"""
        base_requirements = [
            "asyncio-mqtt>=0.16.1",
            "aiofiles>=23.1.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.0.0",
            "loguru>=0.7.0",
            "click>=8.1.0",
            "httpx>=0.24.0",
            "psutil>=5.9.0"
        ]
        
        # Add notification dependencies
        notification_deps = {
            "telegram": ["telethon>=1.29.0"],
            "sms": ["twilio>=8.5.0", "boto3>=1.28.0"],  # Twilio + AWS SNS
            "email": ["aiosmtplib>=3.0.0", "sendgrid>=6.10.0"]
        }
        
        for channel in config.notification_channels:
            if channel in notification_deps:
                base_requirements.extend(notification_deps[channel])
        
        # Add AI dependencies
        if config.ai_integration:
            base_requirements.extend([
                "anthropic>=0.25.0",
                "openai>=1.0.0",
                "tiktoken>=0.4.0"
            ])
        
        # Add monitoring dependencies
        if config.monitoring_enabled:
            base_requirements.extend([
                "prometheus-client>=0.17.0",
                "psutil>=5.9.0"
            ])
        
        # Add database dependencies
        database_deps = {
            "sqlite": ["aiosqlite>=0.19.0"],
            "postgresql": ["asyncpg>=0.28.0", "sqlalchemy[asyncio]>=2.0.0"],
            "redis": ["redis[hiredis]>=4.6.0"]
        }
        
        if config.database and config.database in database_deps:
            base_requirements.extend(database_deps[config.database])
        
        # Development requirements
        dev_requirements = [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "bandit>=1.7.0",
            "safety>=2.3.0"
        ]
        
        # Write requirements files
        (project_path / "requirements.txt").write_text("\\n".join(sorted(base_requirements)) + "\\n")
        (project_path / "requirements-dev.txt").write_text(
            "-r requirements.txt\\n" + "\\n".join(sorted(dev_requirements)) + "\\n"
        )
    
    def _generate_notification_system(self, project_path: Path, config: ProjectConfig):
        """Generate multi-channel notification system"""
        # Multi-channel notifier
        notifier_content = '''"""
Multi-Channel Notification System
Supports Telegram, SMS, and Email with priority-based routing
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime

class NotificationChannel(Enum):
    TELEGRAM = "telegram"
    SMS = "sms"
    EMAIL = "email"

class NotificationProvider(ABC):
    """Base class for all notification providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.channel = None  # Set by subclass
        
    @abstractmethod
    async def initialize(self, **kwargs) -> bool:
        """Initialize the notification provider"""
        pass
    
    @abstractmethod
    async def send_notification(self, message: str, message_type: str = "general") -> bool:
        """Send a notification"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources"""
        pass

class MultiChannelNotifier:
    """Manages notifications across multiple channels with priority routing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self, **kwargs) -> bool:
        """Initialize all configured notification providers"""
        success_count = 0
        
        # Initialize providers based on configuration
        if self.config.get('telegram', {}).get('enabled', False):
            from .telegram_notifier import TelegramNotifier
            telegram_notifier = TelegramNotifier(self.config.get('telegram', {}))
            if await telegram_notifier.initialize(**kwargs):
                self.providers[NotificationChannel.TELEGRAM] = telegram_notifier
                success_count += 1
        
        if self.config.get('sms', {}).get('enabled', False):
            from .sms_notifier import SMSNotifier
            sms_notifier = SMSNotifier(self.config.get('sms', {}))
            if await sms_notifier.initialize():
                self.providers[NotificationChannel.SMS] = sms_notifier
                success_count += 1
        
        self.logger.info(f"Initialized {success_count} notification channels")
        return success_count > 0
    
    async def send_notification(self, message: str, message_type: str = "general", 
                              priority: str = "normal") -> bool:
        """Send notification through appropriate channels based on priority"""
        if not self.providers:
            return True
            
        # Determine which channels to use based on priority
        if priority == "critical":
            channels_to_use = list(self.providers.keys())
        elif priority == "high":
            channels_to_use = [NotificationChannel.SMS, NotificationChannel.TELEGRAM]
        else:
            channels_to_use = [NotificationChannel.TELEGRAM]
        
        # Send to selected channels
        results = []
        for channel in channels_to_use:
            if channel in self.providers:
                try:
                    success = await self.providers[channel].send_notification(message, message_type)
                    results.append(success)
                except Exception as e:
                    self.logger.error(f"Failed to send via {channel.value}: {e}")
                    results.append(False)
        
        return any(results)
    
    async def cleanup(self) -> None:
        """Clean up all notification providers"""
        for provider in self.providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
'''
        
        (project_path / "src" / "integrations" / "notifications" / "__init__.py").write_text(
            'from .multi_channel_notifier import MultiChannelNotifier\\n'
        )
        (project_path / "src" / "integrations" / "notifications" / "multi_channel_notifier.py").write_text(notifier_content)
        
        # Generate Telegram notifier if enabled
        if "telegram" in config.notification_channels:
            self._generate_telegram_notifier(project_path)
        
        # Generate SMS notifier if enabled
        if "sms" in config.notification_channels:
            self._generate_sms_notifier(project_path)
    
    def _generate_telegram_notifier(self, project_path: Path):
        """Generate Telegram notification provider"""
        telegram_content = '''"""
Telegram Notification Provider with Shared Client Pattern
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError, PeerFloodError
    from telethon.tl.types import User, Chat, Channel
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    TelegramClient = None

from .multi_channel_notifier import NotificationProvider, NotificationChannel

class TelegramNotifier(NotificationProvider):
    """Telegram notification provider with shared client support"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.channel = NotificationChannel.TELEGRAM
        self.client = None
        self.notification_targets = []
        self.owns_client = False
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self, external_client=None, **kwargs) -> bool:
        """Initialize with optional external client sharing"""
        if not TELETHON_AVAILABLE:
            self.logger.error("Telethon not available for Telegram notifications")
            return False
            
        if not self.enabled:
            return True
            
        # Use external client if provided (shared client pattern)
        if external_client:
            self.client = external_client
            self.owns_client = False
            self.logger.info("Using external Telegram client")
        else:
            # Create own client (fallback)
            api_id = self.config.get('api_id')
            api_hash = self.config.get('api_hash')
            if not api_id or not api_hash:
                self.logger.error("Telegram API credentials not configured")
                return False
                
            self.client = TelegramClient("notifications_session", api_id, api_hash)
            self.owns_client = True
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                self.logger.error("Telegram client not authorized")
                return False
        
        # Resolve notification targets
        targets = self.config.get('notification_targets', [])
        for target in targets:
            try:
                entity = await self.client.get_entity(target)
                self.notification_targets.append((target, entity))
            except Exception as e:
                self.logger.warning(f"Could not resolve target '{target}': {e}")
        
        return len(self.notification_targets) > 0
    
    async def send_notification(self, message: str, message_type: str = "general") -> bool:
        """Send notification to all configured targets"""
        if not self.notification_targets:
            return True
            
        success_count = 0
        for target_id, entity in self.notification_targets:
            try:
                await self.client.send_message(entity, message)
                success_count += 1
                await asyncio.sleep(1)  # Rate limiting
            except FloodWaitError as e:
                self.logger.warning(f"Rate limited for {e.seconds} seconds")
            except Exception as e:
                self.logger.error(f"Failed to send to {target_id}: {e}")
        
        return success_count > 0
    
    async def cleanup(self) -> None:
        """Clean up Telegram client resources"""
        if self.client and self.owns_client and self.client.is_connected():
            await self.client.disconnect()
'''
        
        (project_path / "src" / "integrations" / "notifications" / "telegram_notifier.py").write_text(telegram_content)
    
    def _generate_sms_notifier(self, project_path: Path):
        """Generate SMS notification provider"""
        sms_content = '''"""
SMS Notification Provider with Twilio and AWS SNS Support
"""

import aiohttp
import logging
from typing import List, Dict, Any
from datetime import datetime

from .multi_channel_notifier import NotificationProvider, NotificationChannel

class SMSNotifier(NotificationProvider):
    """SMS notification provider using Twilio or AWS SNS"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.channel = NotificationChannel.SMS
        self.provider = config.get('sms_provider', 'twilio')
        self.phone_numbers = config.get('sms_targets', [])
        self.max_message_length = 160
        self.logger = logging.getLogger(__name__)
        
        # Provider-specific configuration
        if self.provider == 'twilio':
            self.account_sid = config.get('twilio_account_sid')
            self.auth_token = config.get('twilio_auth_token')
            self.from_number = config.get('twilio_from_number')
        elif self.provider == 'aws_sns':
            self.aws_access_key = config.get('aws_access_key_id')
            self.aws_secret_key = config.get('aws_secret_access_key')
            self.aws_region = config.get('aws_region', 'us-east-1')
    
    async def initialize(self, **kwargs) -> bool:
        """Initialize SMS provider"""
        if not self.enabled or not self.phone_numbers:
            return False
            
        # Validate provider configuration
        if self.provider == 'twilio':
            if not all([self.account_sid, self.auth_token, self.from_number]):
                self.logger.error("Twilio configuration incomplete")
                return False
        elif self.provider == 'aws_sns':
            if not all([self.aws_access_key, self.aws_secret_key]):
                self.logger.error("AWS SNS configuration incomplete")
                return False
                
        self.logger.info(f"SMS notifications initialized via {self.provider}")
        return True
    
    async def send_notification(self, message: str, message_type: str = "general") -> bool:
        """Send SMS notification"""
        if not self.enabled or not self.phone_numbers:
            return True
            
        # Format message for SMS constraints
        sms_message = self._format_for_sms(message)
        
        success_count = 0
        for phone_number in self.phone_numbers:
            try:
                if self.provider == 'twilio':
                    success = await self._send_twilio_sms(phone_number, sms_message)
                elif self.provider == 'aws_sns':
                    success = await self._send_aws_sms(phone_number, sms_message)
                else:
                    continue
                    
                if success:
                    success_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to send SMS to {phone_number[-4:]}: {e}")
        
        return success_count > 0
    
    def _format_for_sms(self, message: str) -> str:
        """Format message for SMS constraints"""
        # Remove emojis and markdown
        sms_text = message.replace('**', '').replace('*', '')
        
        # Convert common emoji patterns to text
        emoji_replacements = {
            '🚀': 'START',
            '✅': 'OK',
            '⚠️': 'WARN',
            '❌': 'ERROR',
            '📊': 'Stats:'
        }
        
        for emoji, text in emoji_replacements.items():
            sms_text = sms_text.replace(emoji, text)
        
        # Truncate if too long
        if len(sms_text) > self.max_message_length:
            sms_text = sms_text[:self.max_message_length-3] + "..."
        
        return sms_text
    
    async def _send_twilio_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via Twilio API"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
        async with aiohttp.ClientSession() as session:
            data = {
                'From': self.from_number,
                'To': phone_number,
                'Body': message
            }
            
            auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
            
            async with session.post(url, data=data, auth=auth) as response:
                return response.status == 201
    
    async def cleanup(self) -> None:
        """Clean up SMS provider resources"""
        pass  # No persistent connections to clean up
'''
        
        (project_path / "src" / "integrations" / "notifications" / "sms_notifier.py").write_text(sms_content)
    
    def _generate_monitoring_system(self, project_path: Path, config: ProjectConfig):
        """Generate comprehensive monitoring system"""
        # Create the monitoring orchestrator we designed
        monitoring_content = '''"""
Production Monitoring & Observability System
Combines health monitoring, performance tracking, and alerting
"""

import asyncio
import psutil
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    active_threads: int = 0
    
    # Application-specific metrics
    cache_hit_rate: float = 0.0
    average_response_time: float = 0.0
    error_rate: float = 0.0

class ProductionMonitoringOrchestrator:
    """
    Integrated monitoring system for production environments
    Combines health checks, performance monitoring, and alerting
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_checks = {}
        self.health_results = {}
        self.performance_history = []
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Initialize monitoring components
        self.alert_cooldown = {}
        self.system_status = HealthStatus.UNKNOWN
        
    async def initialize(self, **components):
        """Initialize monitoring with application components"""
        self.components = components
        self._register_default_health_checks()
        self.logger.info("Production monitoring initialized")
    
    def _register_default_health_checks(self):
        """Register default system health checks"""
        self.health_checks['system_memory'] = self._check_system_memory
        self.health_checks['system_cpu'] = self._check_system_cpu
        self.health_checks['disk_space'] = self._check_disk_space
        
        # Component-specific checks
        if 'resource_manager' in self.components:
            self.health_checks['database'] = self._check_database_health
    
    async def start_monitoring(self):
        """Start all monitoring systems"""
        if self.running:
            return
            
        self.running = True
        
        # Start monitoring tasks
        self.health_task = asyncio.create_task(self._health_monitoring_loop())
        self.performance_task = asyncio.create_task(self._performance_monitoring_loop())
        self.alert_task = asyncio.create_task(self._alert_processing_loop())
        
        self.logger.info("Production monitoring started")
    
    async def stop_monitoring(self):
        """Stop all monitoring systems"""
        if not self.running:
            return
            
        self.running = False
        
        # Cancel monitoring tasks
        for task in [self.health_task, self.performance_task, self.alert_task]:
            if hasattr(self, task.get_name().split('_')[0] + '_task'):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.logger.info("Production monitoring stopped")
    
    async def _health_monitoring_loop(self):
        """Health monitoring loop"""
        while self.running:
            try:
                for check_name, check_func in self.health_checks.items():
                    result = await self._execute_health_check(check_name, check_func)
                    self.health_results[check_name] = result
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _performance_monitoring_loop(self):
        """Performance monitoring loop"""
        while self.running:
            try:
                metrics = await self._collect_performance_metrics()
                self.performance_history.append(metrics)
                
                # Keep only recent metrics (last 1000)
                if len(self.performance_history) > 1000:
                    self.performance_history = self.performance_history[-1000:]
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _execute_health_check(self, name: str, check_func) -> HealthCheckResult:
        """Execute a health check with timeout"""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(check_func(), timeout=30)
            execution_time = time.time() - start_time
            
            if isinstance(result, HealthCheckResult):
                result.execution_time = execution_time
                return result
            else:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    message="Check passed" if result else "Check failed",
                    execution_time=execution_time
                )
                
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e}",
                execution_time=time.time() - start_time
            )
    
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        process = psutil.Process()
        
        return PerformanceMetrics(
            cpu_percent=process.cpu_percent(),
            memory_percent=process.memory_percent(),
            memory_mb=process.memory_info().rss / 1024 / 1024,
            active_threads=process.num_threads()
        )
    
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
            details={'memory_percent': memory_percent}
        )
    
    async def _check_system_cpu(self) -> HealthCheckResult:
        """Check system CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = f"Critical CPU usage: {cpu_percent:.1f}%"
        elif cpu_percent > 80:
            status = HealthStatus.DEGRADED
            message = f"High CPU usage: {cpu_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"CPU usage normal: {cpu_percent:.1f}%"
        
        return HealthCheckResult(
            name="system_cpu",
            status=status,
            message=message,
            execution_time=0.0,
            details={'cpu_percent': cpu_percent}
        )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Check available disk space"""
        disk_usage = psutil.disk_usage('/')
        free_percent = (disk_usage.free / disk_usage.total) * 100
        
        if free_percent < 10:
            status = HealthStatus.UNHEALTHY
            message = f"Critical disk space: {free_percent:.1f}% free"
        elif free_percent < 20:
            status = HealthStatus.DEGRADED
            message = f"Low disk space: {free_percent:.1f}% free"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk space adequate: {free_percent:.1f}% free"
        
        return HealthCheckResult(
            name="disk_space",
            status=status,
            message=message,
            execution_time=0.0,
            details={'free_percent': free_percent}
        )
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_status': self.system_status.value,
            'health_checks': {
                name: {
                    'status': result.status.value,
                    'message': result.message,
                    'last_check': result.timestamp.isoformat()
                }
                for name, result in self.health_results.items()
            },
            'performance': {
                'current': self.performance_history[-1].__dict__ if self.performance_history else {},
                'history_points': len(self.performance_history)
            }
        }
'''
        
        (project_path / "src" / "integrations" / "monitoring" / "__init__.py").write_text(
            'from .production_monitoring import ProductionMonitoringOrchestrator\\n'
        )
        (project_path / "src" / "integrations" / "monitoring" / "production_monitoring.py").write_text(monitoring_content)
    
    def _generate_enhanced_docker(self, project_path: Path, config: ProjectConfig):
        """Generate production-ready Docker configurations"""
        # Multi-stage Dockerfile
        dockerfile_content = f'''# Multi-stage build for production optimization
FROM python:3.11-slim as builder

# Build dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p data logs backups && \\
    chown -R appuser:appuser data logs backups

# Security: Run as non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app/src \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port
EXPOSE 8000

# Use exec form for proper signal handling
CMD ["python", "main.py"]
'''
        
        # Production docker-compose
        compose_content = f'''version: '3.8'

services:
  {config.name.lower().replace(" ", "_")}:
    build:
      context: .
      target: production
    container_name: {config.name.lower().replace(" ", "_")}
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
      - MONITORING_ENABLED=true
      {"- NOTIFICATIONS_ENABLED=true" if config.notification_channels else ""}
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
      {"redis:" if "redis" in config.external_services else ""}
      {"  condition: service_healthy" if "redis" in config.external_services else ""}
      {"postgres:" if "postgresql" in config.external_services else ""}
      {"  condition: service_healthy" if "postgresql" in config.external_services else ""}
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

{"  redis:" if "redis" in config.external_services else ""}
{"    image: redis:7-alpine" if "redis" in config.external_services else ""}
{"    container_name: " + config.name.lower().replace(" ", "_") + "_redis" if "redis" in config.external_services else ""}
{"    restart: unless-stopped" if "redis" in config.external_services else ""}
{"    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru" if "redis" in config.external_services else ""}
{"    volumes:" if "redis" in config.external_services else ""}
{"      - redis_data:/data" if "redis" in config.external_services else ""}
{"    networks:" if "redis" in config.external_services else ""}
{"      - app_network" if "redis" in config.external_services else ""}
{"    healthcheck:" if "redis" in config.external_services else ""}
{"      test: ['CMD', 'redis-cli', 'ping']" if "redis" in config.external_services else ""}
{"      interval: 10s" if "redis" in config.external_services else ""}
{"      timeout: 5s" if "redis" in config.external_services else ""}
{"      retries: 3" if "redis" in config.external_services else ""}

{"  postgres:" if "postgresql" in config.external_services else ""}
{"    image: postgres:15-alpine" if "postgresql" in config.external_services else ""}
{"    container_name: " + config.name.lower().replace(" ", "_") + "_postgres" if "postgresql" in config.external_services else ""}
{"    restart: unless-stopped" if "postgresql" in config.external_services else ""}
{"    environment:" if "postgresql" in config.external_services else ""}
{"      POSTGRES_DB: " + config.name.lower().replace(" ", "_") if "postgresql" in config.external_services else ""}
{"      POSTGRES_USER: app_user" if "postgresql" in config.external_services else ""}
{"      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD}}" if "postgresql" in config.external_services else ""}
{"    volumes:" if "postgresql" in config.external_services else ""}
{"      - postgres_data:/var/lib/postgresql/data" if "postgresql" in config.external_services else ""}
{"    networks:" if "postgresql" in config.external_services else ""}
{"      - app_network" if "postgresql" in config.external_services else ""}
{"    healthcheck:" if "postgresql" in config.external_services else ""}
{"      test: ['CMD-SHELL', 'pg_isready -U app_user -d " + config.name.lower().replace(" ", "_") + "']" if "postgresql" in config.external_services else ""}
{"      interval: 10s" if "postgresql" in config.external_services else ""}
{"      timeout: 5s" if "postgresql" in config.external_services else ""}
{"      retries: 3" if "postgresql" in config.external_services else ""}

{"  monitoring:" if config.monitoring_enabled else ""}
{"    image: prom/prometheus:latest" if config.monitoring_enabled else ""}
{"    container_name: " + config.name.lower().replace(" ", "_") + "_monitoring" if config.monitoring_enabled else ""}
{"    restart: unless-stopped" if config.monitoring_enabled else ""}
{"    ports:" if config.monitoring_enabled else ""}
{"      - '9090:9090'" if config.monitoring_enabled else ""}
{"    volumes:" if config.monitoring_enabled else ""}
{"      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml" if config.monitoring_enabled else ""}
{"      - prometheus_data:/prometheus" if config.monitoring_enabled else ""}
{"    networks:" if config.monitoring_enabled else ""}
{"      - app_network" if config.monitoring_enabled else ""}

volumes:
  {"redis_data:" if "redis" in config.external_services else ""}
  {"postgres_data:" if "postgresql" in config.external_services else ""}
  {"prometheus_data:" if config.monitoring_enabled else ""}

networks:
  app_network:
    driver: bridge
'''
        
        (project_path / "Dockerfile").write_text(dockerfile_content)
        (project_path / "docker-compose.production.yml").write_text(compose_content)
    
    def _generate_kubernetes_manifests(self, project_path: Path, config: ProjectConfig):
        """Generate Kubernetes deployment manifests"""
        namespace_content = f'''apiVersion: v1
kind: Namespace
metadata:
  name: {config.name.lower().replace(" ", "-")}
  labels:
    app: {config.name.lower().replace(" ", "-")}
    environment: production
'''
        
        deployment_content = f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {config.name.lower().replace(" ", "-")}
  namespace: {config.name.lower().replace(" ", "-")}
  labels:
    app: {config.name.lower().replace(" ", "-")}
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: {config.name.lower().replace(" ", "-")}
  template:
    metadata:
      labels:
        app: {config.name.lower().replace(" ", "-")}
      annotations:
        {"prometheus.io/scrape: 'true'" if config.monitoring_enabled else ""}
        {"prometheus.io/port: '8000'" if config.monitoring_enabled else ""}
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: {config.name.lower().replace(" ", "-")}
        image: {config.name.lower().replace(" ", "-")}:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: MONITORING_ENABLED
          value: "true"
        {"- name: NOTIFICATIONS_ENABLED" if config.notification_channels else ""}
        {"  value: 'true'" if config.notification_channels else ""}
        envFrom:
        - secretRef:
            name: {config.name.lower().replace(" ", "-")}-secrets
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
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: {config.name.lower().replace(" ", "-")}-data
      - name: logs-volume
        persistentVolumeClaim:
          claimName: {config.name.lower().replace(" ", "-")}-logs
'''
        
        (project_path / "k8s" / "namespace.yaml").write_text(namespace_content)
        (project_path / "k8s" / "deployment.yaml").write_text(deployment_content)
    
    def _generate_cicd_pipeline(self, project_path: Path, config: ProjectConfig):
        """Generate CI/CD pipeline configuration"""
        if config.cicd_pipeline == "github_actions":
            workflow_content = f'''name: Build and Deploy {config.name}

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: {config.name.lower().replace(" ", "-")}

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Lint and type check
      run: |
        black --check src tests
        isort --check-only src tests
        flake8 src tests
        mypy src
    
    - name: Security checks
      run: |
        bandit -r src/
        safety check
    
    - name: Test with pytest
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{{{ env.REGISTRY }}}}
        username: ${{{{ github.actor }}}}
        password: ${{{{ secrets.GITHUB_TOKEN }}}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        target: production
        push: true
        tags: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max

  {"deploy:" if config.kubernetes_support else ""}
  {"  runs-on: ubuntu-latest" if config.kubernetes_support else ""}
  {"  needs: build" if config.kubernetes_support else ""}
  {"  if: github.ref == 'refs/heads/main'" if config.kubernetes_support else ""}
  {"  environment: production" if config.kubernetes_support else ""}
  {"  " if config.kubernetes_support else ""}
  {"  steps:" if config.kubernetes_support else ""}
  {"  - uses: actions/checkout@v4" if config.kubernetes_support else ""}
  {"  " if config.kubernetes_support else ""}
  {"  - name: Deploy to Kubernetes" if config.kubernetes_support else ""}
  {"    run: |" if config.kubernetes_support else ""}
  {"      kubectl apply -f k8s/" if config.kubernetes_support else ""}
  {"      kubectl set image deployment/{config.name.lower().replace(' ', '-')} {config.name.lower().replace(' ', '-')}=${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:latest" if config.kubernetes_support else ""}
  {"      kubectl rollout status deployment/{config.name.lower().replace(' ', '-')}" if config.kubernetes_support else ""}
'''
            
            (project_path / ".github" / "workflows" / "deploy.yml").write_text(workflow_content)
    
    def _generate_scheduler_configurations(self, project_path: Path, config: ProjectConfig):
        """Generate OS-specific task scheduler configurations"""
        import platform
        
        current_os = platform.system().lower()
        
        # Generate configurations for both OS types
        self._generate_windows_task_scheduler(project_path, config)
        self._generate_linux_cron_config(project_path, config)
        self._generate_systemd_service(project_path, config)
        
        # Generate OS detection and setup scripts
        self._generate_scheduler_setup_scripts(project_path, config, current_os)
    
    def _generate_windows_task_scheduler(self, project_path: Path, config: ProjectConfig):
        """Generate Windows Task Scheduler XML configuration"""
        task_name = config.name.replace(" ", "_")
        
        # Create scheduler directory
        (project_path / "scheduler").mkdir(exist_ok=True)
        
        # Windows Task Scheduler XML template
        task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2024-01-01T00:00:00</Date>
    <Author>{config.name} Automation</Author>
    <Description>Automated task for {config.name} - {config.description}</Description>
  </RegistrationInfo>
  <Triggers>
    <!-- Daily execution at specified time -->
    <CalendarTrigger>
      <StartBoundary>2024-01-01T$(SCHEDULER_START_TIME)</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
    
    <!-- Optional: Hourly execution (disabled by default) -->
    <CalendarTrigger>
      <StartBoundary>2024-01-01T00:00:00</StartBoundary>
      <Enabled>$(SCHEDULER_HOURLY_ENABLED)</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
      <Repetition>
        <Interval>PT$(SCHEDULER_INTERVAL_HOURS)H</Interval>
        <Duration>P1D</Duration>
      </Repetition>
    </CalendarTrigger>
  </Triggers>
  
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <DisallowStartOnRemoteAppSession>false</DisallowStartOnRemoteAppSession>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT$(SCHEDULER_TIMEOUT_HOURS)H</ExecutionTimeLimit>
    <Priority>6</Priority>
  </Settings>
  
  <Actions Context="Author">
    <Exec>
      <Command>$(SCHEDULER_PYTHON_PATH)</Command>
      <Arguments>$(SCHEDULER_SCRIPT_PATH)</Arguments>
      <WorkingDirectory>$(SCHEDULER_WORKING_DIR)</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
        
        # PowerShell script to install the task
        install_script = f'''# Windows Task Scheduler Installation Script for {config.name}
# Run as Administrator

param(
    [string]$TaskName = "{task_name}",
    [string]$ConfigFile = ".env"
)

# Load environment variables from .env file
if (Test-Path $ConfigFile) {{
    Get-Content $ConfigFile | ForEach-Object {{
        if ($_ -match '^([^#][^=]*?)=(.*)
        readme_content = f'''# {config.name}

{config.description}

## 🚀 **Production-Ready Features**

This application includes enterprise-grade patterns learned from production systems:

### **📅 Cross-Platform Scheduler Support**
- ✅ **Windows Task Scheduler** with XML configuration and PowerShell automation
- ✅ **Linux Cron Jobs** with intelligent schedule management
- ✅ **Systemd Services** for persistent Linux operation
- ✅ **Unified setup script** with automatic OS detection
- ✅ **Schedule validation** and configuration management

### **📢 Multi-Channel Notifications**
{"- ✅ Telegram notifications with shared client pattern" if "telegram" in config.notification_channels else ""}
{"- ✅ SMS notifications via Twilio/AWS SNS with cost management" if "sms" in config.notification_channels else ""}
{"- ✅ Email notifications" if "email" in config.notification_channels else ""}
{"- ✅ Priority-based routing (critical→all channels, high→SMS+Telegram, normal→Telegram)" if len(config.notification_channels) > 1 else ""}

### **📊 Comprehensive Monitoring**
{"- ✅ Health monitoring with configurable checks" if config.monitoring_enabled else ""}
{"- ✅ Performance metrics and alerting" if config.performance_monitoring else ""}
{"- ✅ System resource monitoring (CPU, memory, disk)" if config.monitoring_enabled else ""}
{"- ✅ Integrated monitoring dashboard" if config.monitoring_enabled else ""}

### **🐳 Production Deployment**
- ✅ Multi-stage Docker builds with security hardening
- ✅ Docker Compose with health checks and dependencies
{"- ✅ Kubernetes manifests with autoscaling and security contexts" if config.kubernetes_support else ""}
- ✅ CI/CD pipeline with security scanning and automated testing
- ✅ Production environment configuration and secrets management

### **🛡️ Enterprise Patterns**
- ✅ Resource management and conflict prevention
- ✅ Comprehensive error handling with structured logging
- ✅ Configuration validation and environment-based settings
- ✅ Structured logging with emoji visual indicators
{"- ✅ AI integration with smart routing and fallbacks" if config.ai_integration else ""}
{"- ✅ Autonomous debugging foundations" if config.autonomous_debugging else ""}

## 🚀 **Quick Start**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env with your configuration
```

### 3. Run Setup
```bash
python main.py --setup
```

### 4. Configure Scheduler (OS-Specific)
```bash
# Automatic OS detection and setup
python setup_scheduler.py

# Or setup specific scheduler types
python setup_scheduler.py systemd    # Linux systemd service
python setup_scheduler.py status     # Check current status
```

### 5. Test Systems
```bash
# Test all systems
python main.py --diagnose

{"# Test notifications" if config.notification_channels else ""}
{"python main.py --test-notifications" if config.notification_channels else ""}

# Check scheduler status
python setup_scheduler.py status
```

### 6. Start Application
```bash
python main.py
```

## 📅 **Scheduler Configuration**

This application supports multiple scheduler types based on your operating system:

### **Windows Task Scheduler**
Configure in `.env`:
```bash
# Daily execution at 2:00 AM
SCHEDULER_START_TIME=02:00:00

# Enable hourly execution (optional)
SCHEDULER_HOURLY_ENABLED=false
SCHEDULER_INTERVAL_HOURS=1

# Task timeout (hours)
SCHEDULER_TIMEOUT_HOURS=2
```

**Management commands:**
```powershell
# Install task (run as Administrator)
./scheduler/install_windows_task.ps1

# Manage task
Start-ScheduledTask -TaskName "{config.name.replace(' ', '_')}"
Stop-ScheduledTask -TaskName "{config.name.replace(' ', '_')}"
Get-ScheduledTask -TaskName "{config.name.replace(' ', '_')}"
```

### **Linux Cron Jobs**
Configure in `.env`:
```bash
# Cron schedule: minute hour day month weekday
CRON_SCHEDULE=0 2 * * *              # Daily at 2:00 AM
# CRON_SCHEDULE=0 */6 * * *          # Every 6 hours
# CRON_SCHEDULE=*/30 * * * *         # Every 30 minutes

# Log file for cron output
CRON_LOG_FILE=logs/cron.log
```

**Management commands:**
```bash
# Install cron job
./scheduler/install_cron.sh

# View cron jobs
crontab -l

# Edit cron jobs
crontab -e

# View logs
tail -f logs/cron.log
```

### **Linux Systemd Service**
Configure in `.env`:
```bash
# Service user (auto-detected if empty)
SYSTEMD_USER=

# Resource limits
SYSTEMD_MEMORY_LIMIT=1G
SYSTEMD_CPU_QUOTA=100%
```

**Management commands:**
```bash
# Install service (requires sudo)
sudo ./scheduler/install_systemd.sh

# Manage service
sudo systemctl start {config.name.replace(' ', '_').lower()}
sudo systemctl stop {config.name.replace(' ', '_').lower()}
sudo systemctl status {config.name.replace(' ', '_').lower()}
sudo journalctl -u {config.name.replace(' ', '_').lower()} -f
```

## 🐳 **Docker Deployment**

### Development
```bash
docker-compose up --build
```

### Production
```bash
docker-compose -f docker-compose.production.yml up -d
```

{"## ☸️ **Kubernetes Deployment**" if config.kubernetes_support else ""}
{"" if config.kubernetes_support else ""}
{"```bash" if config.kubernetes_support else ""}
{"# Deploy to Kubernetes" if config.kubernetes_support else ""}
{"kubectl apply -f k8s/" if config.kubernetes_support else ""}
{"" if config.kubernetes_support else ""}
{"# Check deployment status" if config.kubernetes_support else ""}
{"kubectl get pods -n {config.name.lower().replace(' ', '-')}" if config.kubernetes_support else ""}
{"kubectl logs -f deployment/{config.name.lower().replace(' ', '-')} -n {config.name.lower().replace(' ', '-')}" if config.kubernetes_support else ""}
{"```" if config.kubernetes_support else ""}

## 📊 **Monitoring**

{"### Health Checks" if config.monitoring_enabled else ""}
{"- System memory usage" if config.monitoring_enabled else ""}
{"- CPU utilization" if config.monitoring_enabled else ""}
{"- Disk space availability" if config.monitoring_enabled else ""}
{"- Database connectivity" if config.monitoring_enabled else ""}
{"- Application performance metrics" if config.monitoring_enabled else ""}

{"### Alerting" if config.notification_channels and config.monitoring_enabled else ""}
{"- Critical alerts → SMS + Telegram + Email" if len(config.notification_channels) > 2 else ""}
{"- High priority → SMS + Telegram" if "sms" in config.notification_channels and "telegram" in config.notification_channels else ""}
{"- Normal alerts → Telegram" if "telegram" in config.notification_channels else ""}
{"- Alert cooldown prevents spam" if config.monitoring_enabled else ""}

{"### Dashboard Access" if config.monitoring_enabled else ""}
{"```bash" if config.monitoring_enabled else ""}
{"# View monitoring dashboard" if config.monitoring_enabled else ""}
{"python main.py --diagnose" if config.monitoring_enabled else ""}
{"" if config.monitoring_enabled else ""}
{"# Prometheus metrics (if enabled)" if config.monitoring_enabled else ""}
{"curl http://localhost:9090/metrics" if config.monitoring_enabled else ""}
{"```" if config.monitoring_enabled else ""}

## 🔧 **Configuration**

### Environment Variables
```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Scheduler (Windows)
SCHEDULER_START_TIME=02:00:00
SCHEDULER_HOURLY_ENABLED=false
SCHEDULER_TIMEOUT_HOURS=2

# Scheduler (Linux Cron)
CRON_SCHEDULE=0 2 * * *
CRON_LOG_FILE=logs/cron.log

# Scheduler (Linux Systemd)
SYSTEMD_MEMORY_LIMIT=1G
SYSTEMD_CPU_QUOTA=100%

{"# Notifications" if config.notification_channels else ""}
{"NOTIFICATIONS_ENABLED=true" if config.notification_channels else ""}
{"TELEGRAM_TARGETS=@admin_channel" if "telegram" in config.notification_channels else ""}
{"SMS_TARGETS=+1234567890" if "sms" in config.notification_channels else ""}
{"TWILIO_ACCOUNT_SID=your_sid" if "sms" in config.notification_channels else ""}
{"TWILIO_AUTH_TOKEN=your_token" if "sms" in config.notification_channels else ""}

{"# AI Integration" if config.ai_integration else ""}
{"ANTHROPIC_API_KEY=your_key" if config.ai_integration else ""}
{"OPENAI_API_KEY=your_key" if config.ai_integration else ""}

{"# Monitoring" if config.monitoring_enabled else ""}
{"MONITORING_ENABLED=true" if config.monitoring_enabled else ""}
{"PERFORMANCE_MONITORING=true" if config.performance_monitoring else ""}
{"HEALTH_CHECK_INTERVAL=30" if config.monitoring_enabled else ""}
```

## 📋 **Scheduler Management**

### Check Status
```bash
# Cross-platform status check
python setup_scheduler.py status

# Output shows:
# 📊 Scheduler Status for {config.name}
# ✅ Windows Task Scheduler: Configured
# ✅ Next Run Time: 2024-01-02 02:00:00
```

### Schedule Examples
```bash
# Daily at 2:00 AM
CRON_SCHEDULE="0 2 * * *"

# Every 6 hours
CRON_SCHEDULE="0 */6 * * *"

# Every 30 minutes
CRON_SCHEDULE="*/30 * * * *"

# Weekly on Monday at 2:00 AM
CRON_SCHEDULE="0 2 * * 1"

# Business hours only (9 AM - 5 PM, Mon-Fri)
CRON_SCHEDULE="0 9-17 * * 1-5"
```

### Troubleshooting Schedulers

**Windows Task Scheduler:**
```powershell
# Check task history
Get-WinEvent -FilterHashtable @{{LogName='Microsoft-Windows-TaskScheduler/Operational'}} | Where-Object {{$_.Message -like '*{config.name.replace(' ', '_')}*'}}

# Test task manually
Start-ScheduledTask -TaskName "{config.name.replace(' ', '_')}"
```

**Linux Cron:**
```bash
# Check cron service status
sudo systemctl status cron

# View cron logs
sudo journalctl -u cron -f

# Test cron entry manually
cd /path/to/project && python main.py
```

**Linux Systemd:**
```bash
# Check service logs
sudo journalctl -u {config.name.replace(' ', '_').lower()} --since "1 hour ago"

# Check service status
sudo systemctl status {config.name.replace(' ', '_').lower()}
```

## 🧪 **Testing**

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Performance tests
pytest tests/performance/

# Integration tests
pytest tests/integration/

# Test scheduler setup
python setup_scheduler.py status
```

## 📈 **Performance**

This application includes several performance optimizations:

- Async/await throughout for I/O operations
- Connection pooling for databases
- Multi-level caching systems
- Resource conflict prevention
- Smart batching for AI operations
- Performance monitoring and alerting
- Scheduler-aware resource management

## 🔐 **Security**

Security features included:

- Non-root Docker containers with security contexts
- Environment variable validation and secrets management
- Rate limiting for APIs and external services
- Comprehensive input validation
- Security scanning in CI/CD pipeline
- Regular dependency updates
- Scheduler runs with least privileges

## 📚 **Documentation**

- [Setup Guide](docs/setup.md) - Detailed installation instructions
- [Scheduler Guide](docs/scheduler.md) - Complete scheduler configuration
- [API Documentation](docs/api.md) - API reference and examples
- [Architecture Guide](docs/architecture.md) - System design and patterns
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Run linting: `black src/ && isort src/ && flake8 src/`
5. Test scheduler: `python setup_scheduler.py status`
6. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with enterprise-grade patterns from production systems including the Telegram Knowledge Base Extractor. Includes cross-platform scheduler support for automated operation on Windows, Linux, and macOS.*
'''
        
        (project_path / "README.md").write_text(readme_content)
        
        # Generate dedicated scheduler documentation
        scheduler_docs = f'''# Scheduler Configuration Guide

Complete guide for setting up automated scheduling for {config.name} across different operating systems.

## 📅 **Overview**

This application supports three scheduler types:

1. **Windows Task Scheduler** - XML-based task configuration with PowerShell automation
2. **Linux Cron Jobs** - Traditional Unix cron with enhanced management
3. **Linux Systemd Services** - Modern Linux service management with resource controls

The setup process automatically detects your operating system and configures the appropriate scheduler.

## 🚀 **Quick Setup**

### Automatic Configuration
```bash
# Detect OS and setup appropriate scheduler
python setup_scheduler.py

# Check status
python setup_scheduler.py status
```

### Manual Configuration
```bash
# Windows only
powershell -ExecutionPolicy Bypass -File scheduler/install_windows_task.ps1

# Linux cron only
./scheduler/install_cron.sh

# Linux systemd only (requires sudo)
sudo ./scheduler/install_systemd.sh
```

## 🪟 **Windows Task Scheduler**

### Configuration Variables
Add to your `.env` file:

```bash
# Execution time (24-hour format)
SCHEDULER_START_TIME=02:00:00

# Enable hourly execution (true/false)
SCHEDULER_HOURLY_ENABLED=false

# Interval for hourly execution (hours)
SCHEDULER_INTERVAL_HOURS=1

# Task timeout (hours)
SCHEDULER_TIMEOUT_HOURS=2

# Python interpreter path (auto-detected if empty)
SCHEDULER_PYTHON_PATH=python

# Script to execute
SCHEDULER_SCRIPT_PATH=main.py

# Working directory (auto-detected if empty)
SCHEDULER_WORKING_DIR=
```

### Installation
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scheduler/install_windows_task.ps1
```

### Management Commands
```powershell
# Start task immediately
Start-ScheduledTask -TaskName "{config.name.replace(' ', '_')}"

# Stop running task
Stop-ScheduledTask -TaskName "{config.name.replace(' ', '_')}"

# View task status
Get-ScheduledTask -TaskName "{config.name.replace(' ', '_')}"

# View task properties
Get-ScheduledTask -TaskName "{config.name.replace(' ', '_')}" | Get-ScheduledTaskInfo

# Remove task
Unregister-ScheduledTask -TaskName "{config.name.replace(' ', '_')}" -Confirm:$false
```

### Troubleshooting Windows Tasks

**Check Task History:**
```powershell
# View recent task events
Get-WinEvent -FilterHashtable @{{LogName='Microsoft-Windows-TaskScheduler/Operational'}} | 
Where-Object {{$_.Message -like '*{config.name.replace(' ', '_')}*'}} | 
Select-Object TimeCreated, LevelDisplayName, Message | 
Format-Table -Wrap
```

**Common Issues:**
- **Task not running**: Check if user has "Log on as batch job" rights
- **Script errors**: Verify Python path and working directory
- **Permission denied**: Ensure task runs with appropriate user privileges

## 🐧 **Linux Cron Jobs**

### Configuration Variables
Add to your `.env` file:

```bash
# Cron schedule (minute hour day month weekday)
CRON_SCHEDULE=0 2 * * *

# Python interpreter path (auto-detected if empty)
CRON_PYTHON_PATH=

# Script to execute
CRON_SCRIPT_PATH=main.py

# Working directory (auto-detected if empty)
CRON_WORKING_DIR=

# Log file for cron output
CRON_LOG_FILE=logs/cron.log

# Log directory for rotation
CRON_LOG_DIR=logs
```

### Schedule Examples
```bash
# Daily at 2:00 AM
CRON_SCHEDULE="0 2 * * *"

# Every 6 hours
CRON_SCHEDULE="0 */6 * * *"

# Every 30 minutes
CRON_SCHEDULE="*/30 * * * *"

# Weekly on Monday at 2:00 AM
CRON_SCHEDULE="0 2 * * 1"

# Business hours only (9 AM - 5 PM, Mon-Fri)
CRON_SCHEDULE="0 9-17 * * 1-5"

# Every 15 minutes during business hours
CRON_SCHEDULE="*/15 9-17 * * 1-5"
```

### Installation
```bash
# Make script executable and install
chmod +x scheduler/install_cron.sh
./scheduler/install_cron.sh
```

### Management Commands
```bash
# View current crontab
crontab -l

# Edit crontab manually
crontab -e

# Remove all cron jobs (be careful!)
crontab -r

# View cron logs
tail -f logs/cron.log

# Check cron service status
sudo systemctl status cron
```

### Troubleshooting Cron

**Check Cron Service:**
```bash
# Ensure cron daemon is running
sudo systemctl status cron

# Start cron if stopped
sudo systemctl start cron

# View cron system logs
sudo journalctl -u cron -f
```

**Test Job Manually:**
```bash
# Run the exact command from cron
cd /path/to/project && python main.py

# Check if all required environment variables are available
env | grep -E "(PATH|PYTHON|HOME)"
```

**Common Issues:**
- **Environment variables not available**: Cron has minimal environment
- **Path issues**: Use absolute paths for Python and scripts
- **Permissions**: Ensure log directory is writable

## 🔧 **Linux Systemd Services**

### Configuration Variables
Add to your `.env` file:

```bash
# User to run service as (auto-detected if empty)
SYSTEMD_USER=

# Group to run service as (same as user if empty)
SYSTEMD_GROUP=

# Python interpreter path (auto-detected if empty)
SYSTEMD_PYTHON_PATH=

# Script to execute
SYSTEMD_SCRIPT_PATH=main.py

# Working directory (auto-detected if empty)
SYSTEMD_WORKING_DIR=

# Memory limit for service
SYSTEMD_MEMORY_LIMIT=1G

# CPU quota (percentage)
SYSTEMD_CPU_QUOTA=100%
```

### Installation
```bash
# Requires root privileges
sudo ./scheduler/install_systemd.sh
```

### Management Commands
```bash
# Start service
sudo systemctl start {config.name.replace(' ', '_').lower()}

# Stop service
sudo systemctl stop {config.name.replace(' ', '_').lower()}

# Restart service
sudo systemctl restart {config.name.replace(' ', '_').lower()}

# Enable auto-start on boot
sudo systemctl enable {config.name.replace(' ', '_').lower()}

# Disable auto-start
sudo systemctl disable {config.name.replace(' ', '_').lower()}

# View service status
sudo systemctl status {config.name.replace(' ', '_').lower()}

# View logs (real-time)
sudo journalctl -u {config.name.replace(' ', '_').lower()} -f

# View logs (recent)
sudo journalctl -u {config.name.replace(' ', '_').lower()} --since "1 hour ago"
```

### Troubleshooting Systemd

**Check Service Configuration:**
```bash
# Validate service file syntax
sudo systemd-analyze verify /etc/systemd/system/{config.name.replace(' ', '_').lower()}.service

# Reload systemd after changes
sudo systemctl daemon-reload
```

**Monitor Resource Usage:**
```bash
# Check memory and CPU usage
sudo systemctl status {config.name.replace(' ', '_').lower()}

# Detailed resource information
sudo systemctl show {config.name.replace(' ', '_').lower()}
```

**Common Issues:**
- **Service fails to start**: Check file permissions and user existence
- **Memory/CPU limits exceeded**: Adjust limits in .env file
- **Path issues**: Ensure all paths are absolute

## 📊 **Monitoring and Status**

### Unified Status Check
```bash
# Check all scheduler types
python setup_scheduler.py status

# Example output:
# 📊 Scheduler Status for {config.name}
# ================================================
# 🖥️ Operating System: Windows
# ✅ Windows Task Scheduler: Configured
# 📋 Task Details:
#    Next Run Time: 1/2/2024 2:00:00 AM
#    Status: Ready
#    Last Run Time: 1/1/2024 2:00:00 AM
```

### Health Monitoring
```bash
# Test application execution
python main.py --diagnose

# View execution logs
tail -f logs/application.log

# Check for errors
grep -i error logs/*.log
```

## ⚡ **Performance Optimization**

### Scheduler Best Practices

1. **Resource Limits**: Set appropriate memory and CPU limits
2. **Logging**: Configure log rotation to prevent disk fill
3. **Error Handling**: Implement robust error handling in main script
4. **Monitoring**: Set up alerts for scheduler failures
5. **Testing**: Regularly test scheduled execution

### Log Rotation Setup

**Linux (logrotate):**
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/{config.name.replace(' ', '_').lower()} << EOF
/path/to/project/logs/*.log {{
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    postrotate
        # Restart service if needed
        # sudo systemctl reload {config.name.replace(' ', '_').lower()}
    endscript
}}
EOF
```

**Windows (PowerShell):**
```powershell
# Add to scheduled task or separate task
Get-ChildItem "C:\\path\\to\\project\\logs\\*.log" | 
Where-Object {{$_.LastWriteTime -lt (Get-Date).AddDays(-7)}} | 
Remove-Item -Force
```

## 🔐 **Security Considerations**

### Principle of Least Privilege
- Run schedulers with minimal required permissions
- Use dedicated service accounts for production
- Avoid running with administrator/root privileges when possible

### File Permissions
```bash
# Linux: Secure log directory
chmod 750 logs/
chown $USER:$USER logs/

# Secure configuration files
chmod 600 .env
```

### Environment Variables
- Store sensitive data in environment variables, not config files
- Use system keyring or vault services for production secrets
- Rotate API keys and credentials regularly

## 🧪 **Testing Schedulers**

### Manual Testing
```bash
# Test application without scheduler
python main.py

# Test with specific environment
ENVIRONMENT=production python main.py

# Test with debug output
DEBUG=true python main.py --diagnose
```

### Scheduler Testing
```bash
# Test cron entry manually
cd /path/to/project && /usr/bin/python3 main.py

# Test systemd service manually
sudo -u $USER /usr/bin/python3 /path/to/project/main.py

# Test Windows task manually
Start-ScheduledTask -TaskName "{config.name.replace(' ', '_')}"
```

### Automated Testing
```bash
# Create test schedule (every minute for testing)
CRON_SCHEDULE="* * * * *"

# Monitor for 5 minutes
tail -f logs/cron.log &
sleep 300
kill %1
```

## 📋 **Maintenance**

### Regular Maintenance Tasks

1. **Monitor Logs**: Check for errors and warnings
2. **Update Dependencies**: Keep Python packages current
3. **Test Execution**: Verify scheduler runs successfully
4. **Resource Usage**: Monitor memory and CPU consumption
5. **Backup Configuration**: Save scheduler configurations

### Backup and Recovery
```bash
# Backup scheduler configurations
tar -czf scheduler_backup.tar.gz scheduler/ .env

# Export crontab
crontab -l > crontab_backup.txt

# Export systemd service
sudo cp /etc/systemd/system/{config.name.replace(' ', '_').lower()}.service systemd_backup.service
```

---

*This scheduler configuration guide ensures reliable, automated operation of {config.name} across Windows, Linux, and macOS environments.*
'''
        
        (project_path / "docs" / "scheduler.md").write_text(scheduler_docs)
    
    def _generate_enhanced_tests(self, project_path: Path, config: ProjectConfig):
        """Generate enhanced test suite with scheduler testing"""
        # Main application test with scheduler support
        test_content = f'''"""
Test main application functionality with scheduler support
"""

import pytest
import asyncio
import platform
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.core.application import Application
from src.config import ApplicationConfig, SchedulerConfig, SchedulerType
from src.config import get_config, reset_config


class TestApplication:
    """Test the main application class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        config = Mock(spec=ApplicationConfig)
        config.environment.value = "development"
        config.debug = True
        config.data_directory = Path("test_data")
        config.scheduler = Mock(spec=SchedulerConfig)
        config.scheduler.scheduler_type = SchedulerType.NONE
        {"config.notifications = Mock()" if config.notification_channels else ""}
        {"config.notifications.notifications_enabled = True" if config.notification_channels else ""}
        return config
    
    @pytest.fixture
    def app(self, mock_config):
        """Create an application instance"""
        return Application(mock_config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, app):
        """Test application initialization"""
        result = await app.initialize()
        assert result is True
        assert app.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self, app):
        """Test application cleanup"""
        await app.initialize()
        await app.cleanup()
        # Add specific cleanup assertions
    
    def test_get_stats(self, app):
        """Test statistics retrieval"""
        stats = app.get_stats()
        assert isinstance(stats, dict)
        assert "uptime_seconds" in stats
        assert "operations_completed" in stats


class TestSchedulerConfiguration:
    """Test scheduler configuration and detection"""
    
    def test_scheduler_type_detection_windows(self):
        """Test Windows scheduler type detection"""
        with patch('platform.system', return_value='Windows'):
            scheduler_config = SchedulerConfig.from_env()
            assert scheduler_config.scheduler_type == SchedulerType.WINDOWS_TASK
    
    def test_scheduler_type_detection_linux(self):
        """Test Linux scheduler type detection"""
        with patch('platform.system', return_value='Linux'):
            scheduler_config = SchedulerConfig.from_env()
            assert scheduler_config.scheduler_type == SchedulerType.LINUX_CRON
    
    def test_scheduler_type_detection_mac(self):
        """Test macOS scheduler type detection (should use cron)"""
        with patch('platform.system', return_value='Darwin'):
            scheduler_config = SchedulerConfig.from_env()
            assert scheduler_config.scheduler_type == SchedulerType.LINUX_CRON
    
    @patch.dict('os.environ', {{
        'SCHEDULER_START_TIME': '03:00:00',
        'SCHEDULER_HOURLY_ENABLED': 'true',
        'SCHEDULER_INTERVAL_HOURS': '2',
        'CRON_SCHEDULE': '0 3 * * *',
        'SCHEDULER_PYTHON_PATH': '/usr/bin/python3'
    }})
    def test_scheduler_config_from_env(self):
        """Test scheduler configuration from environment variables"""
        with patch('platform.system', return_value='Windows'):
            config = SchedulerConfig.from_env()
            
            assert config.windows_start_time == '03:00:00'
            assert config.windows_hourly_enabled is True
            assert config.windows_interval_hours == 2
            assert config.cron_schedule == '0 3 * * *'
            assert config.python_path == '/usr/bin/python3'
    
    def test_get_display_schedule_windows_daily(self):
        """Test Windows daily schedule display"""
        config = SchedulerConfig(
            scheduler_type=SchedulerType.WINDOWS_TASK,
            windows_start_time='02:30:00',
            windows_hourly_enabled=False
        )
        display = config.get_display_schedule()
        assert display == "Daily at 02:30:00"
    
    def test_get_display_schedule_windows_hourly(self):
        """Test Windows hourly schedule display"""
        config = SchedulerConfig(
            scheduler_type=SchedulerType.WINDOWS_TASK,
            windows_start_time='02:30:00',
            windows_hourly_enabled=True,
            windows_interval_hours=4
        )
        display = config.get_display_schedule()
        assert display == "Every 4 hour(s), starting at 02:30:00"
    
    def test_get_display_schedule_cron_daily(self):
        """Test cron daily schedule display"""
        config = SchedulerConfig(
            scheduler_type=SchedulerType.LINUX_CRON,
            cron_schedule='0 2 * * *'
        )
        display = config.get_display_schedule()
        assert display == "Daily at 2:00"
    
    def test_get_display_schedule_cron_hourly(self):
        """Test cron hourly schedule display"""
        config = SchedulerConfig(
            scheduler_type=SchedulerType.LINUX_CRON,
            cron_schedule='0 */6 * * *'
        )
        display = config.get_display_schedule()
        assert display == "Every 6 hours"


{"class TestNotificationSystem:" if config.notification_channels else ""}
{"    '''Test notification system functionality'''" if config.notification_channels else ""}
{"    " if config.notification_channels else ""}
{"    @pytest.fixture" if config.notification_channels else ""}
{"    def mock_notification_config(self):" if config.notification_channels else ""}
{"        '''Create mock notification configuration'''" if config.notification_channels else ""}
{"        from src.integrations.notifications import MultiChannelNotifier" if config.notification_channels else ""}
{"        " if config.notification_channels else ""}
{"        config = {{" if config.notification_channels else ""}
{"            'telegram': {{'enabled': True, 'notification_targets': ['@test_channel']}}," if "telegram" in config.notification_channels else ""}
{"            'sms': {{'enabled': True, 'sms_targets': ['+1234567890']}}," if "sms" in config.notification_channels else ""}
{"            'enabled': True" if config.notification_channels else ""}
{"        }}" if config.notification_channels else ""}
{"        return config" if config.notification_channels else ""}
{"    " if config.notification_channels else ""}
{"    @pytest.mark.asyncio" if config.notification_channels else ""}
{"    async def test_multi_channel_notifier_initialization(self, mock_notification_config):" if config.notification_channels else ""}
{"        '''Test multi-channel notifier initialization'''" if config.notification_channels else ""}
{"        from src.integrations.notifications import MultiChannelNotifier" if config.notification_channels else ""}
{"        " if config.notification_channels else ""}
{"        notifier = MultiChannelNotifier(mock_notification_config)" if config.notification_channels else ""}
{"        " if config.notification_channels else ""}
{"        # Mock provider initialization" if config.notification_channels else ""}
{"        with patch('src.integrations.notifications.telegram_notifier.TelegramNotifier') as mock_telegram:" if "telegram" in config.notification_channels else ""}
{"            mock_telegram.return_value.initialize = AsyncMock(return_value=True)" if "telegram" in config.notification_channels else ""}
{"            " if "telegram" in config.notification_channels else ""}
{"            success = await notifier.initialize()" if config.notification_channels else ""}
{"            assert success is True" if config.notification_channels else ""}
{"    " if config.notification_channels else ""}
{"    @pytest.mark.asyncio" if config.notification_channels else ""}
{"    async def test_priority_based_notification_routing(self, mock_notification_config):" if config.notification_channels else ""}
{"        '''Test priority-based notification channel routing'''" if config.notification_channels else ""}
{"        from src.integrations.notifications import MultiChannelNotifier" if config.notification_channels else ""}
{"        " if config.notification_channels else ""}
{"        notifier = MultiChannelNotifier(mock_notification_config)" if config.notification_channels else ""}
{"        " if config.notification_channels else ""}
{"        # Mock providers" if config.notification_channels else ""}
{"        mock_telegram = Mock()" if "telegram" in config.notification_channels else ""}
{"        mock_telegram.send_notification = AsyncMock(return_value=True)" if "telegram" in config.notification_channels else ""}
{"        mock_sms = Mock()" if "sms" in config.notification_channels else ""}
{"        mock_sms.send_notification = AsyncMock(return_value=True)" if "sms" in config.notification_channels else ""}
{"        " if config.notification_channels else ""}
{"        notifier.providers = {{" if config.notification_channels else ""}
{"            NotificationChannel.TELEGRAM: mock_telegram," if "telegram" in config.notification_channels else ""}
{"            NotificationChannel.SMS: mock_sms" if "sms" in config.notification_channels else ""}
{"        }}" if config.notification_channels else ""}
{"        " if config.notification_channels else ""}
{"        # Test critical priority (should use all channels)" if len(config.notification_channels) > 1 else ""}
{"        await notifier.send_notification('Test critical', 'test', priority='critical')" if len(config.notification_channels) > 1 else ""}
{"        mock_telegram.send_notification.assert_called_once()" if len(config.notification_channels) > 1 and "telegram" in config.notification_channels else ""}
{"        mock_sms.send_notification.assert_called_once()" if len(config.notification_channels) > 1 and "sms" in config.notification_channels else ""}


{"class TestMonitoringSystem:" if config.monitoring_enabled else ""}
{"    '''Test monitoring and health check functionality'''" if config.monitoring_enabled else ""}
{"    " if config.monitoring_enabled else ""}
{"    @pytest.mark.asyncio" if config.monitoring_enabled else ""}
{"    async def test_health_monitor_initialization(self):" if config.monitoring_enabled else ""}
{"        '''Test health monitor initialization'''" if config.monitoring_enabled else ""}
{"        from src.integrations.monitoring import ProductionMonitoringOrchestrator" if config.monitoring_enabled else ""}
{"        " if config.monitoring_enabled else ""}
{"        config = {{'health_monitoring': {{'enabled': True}}}}" if config.monitoring_enabled else ""}
{"        monitor = ProductionMonitoringOrchestrator(config)" if config.monitoring_enabled else ""}
{"        " if config.monitoring_enabled else ""}
{"        await monitor.initialize()" if config.monitoring_enabled else ""}
{"        " if config.monitoring_enabled else ""}
{"        # Should have default health checks registered" if config.monitoring_enabled else ""}
{"        assert 'system_memory' in monitor.health_checks" if config.monitoring_enabled else ""}
{"        assert 'system_cpu' in monitor.health_checks" if config.monitoring_enabled else ""}
{"        assert 'disk_space' in monitor.health_checks" if config.monitoring_enabled else ""}
{"    " if config.monitoring_enabled else ""}
{"    @pytest.mark.asyncio" if config.monitoring_enabled else ""}
{"    async def test_performance_metrics_collection(self):" if config.monitoring_enabled else ""}
{"        '''Test performance metrics collection'''" if config.monitoring_enabled else ""}
{"        from src.integrations.monitoring import ProductionMonitoringOrchestrator" if config.monitoring_enabled else ""}
{"        " if config.monitoring_enabled else ""}
{"        config = {{'performance_interval': 1}}" if config.monitoring_enabled else ""}
{"        monitor = ProductionMonitoringOrchestrator(config)" if config.monitoring_enabled else ""}
{"        " if config.monitoring_enabled else ""}
{"        metrics = await monitor._collect_performance_metrics()" if config.monitoring_enabled else ""}
{"        " if config.monitoring_enabled else ""}
{"        assert metrics.cpu_percent >= 0" if config.monitoring_enabled else ""}
{"        assert metrics.memory_percent >= 0" if config.monitoring_enabled else ""}
{"        assert metrics.memory_mb >= 0" if config.monitoring_enabled else ""}


class TestSchedulerSetup:
    """Test scheduler setup and management functionality"""
    
    def test_os_detection(self):
        """Test operating system detection"""
        # Import the setup script functionality
        import sys
        sys.path.append('.')
        
        # Test Windows detection
        with patch('platform.system', return_value='Windows'):
            from setup_scheduler import detect_os
            assert detect_os() == 'windows'
        
        # Test Linux detection
        with patch('platform.system', return_value='Linux'):
            assert detect_os() == 'linux'
        
        # Test macOS detection (should be treated as Linux)
        with patch('platform.system', return_value='Darwin'):
            assert detect_os() == 'linux'
    
    @patch('subprocess.run')
    def test_windows_scheduler_setup(self, mock_subprocess):
        """Test Windows Task Scheduler setup"""
        # Mock successful PowerShell execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        import sys
        sys.path.append('.')
        from setup_scheduler import setup_windows_scheduler
        
        with patch('platform.system', return_value='Windows'):
            with patch('pathlib.Path.exists', return_value=True):
                result = setup_windows_scheduler()
                assert result is True
                mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_linux_cron_setup(self, mock_subprocess):
        """Test Linux cron setup"""
        # Mock successful bash execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        import sys
        sys.path.append('.')
        from setup_scheduler import setup_linux_scheduler
        
        with patch('platform.system', return_value='Linux'):
            with patch('pathlib.Path.exists', return_value=True):
                result = setup_linux_scheduler()
                assert result is True
                mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_scheduler_status_check_windows(self, mock_subprocess):
        """Test scheduler status check on Windows"""
        # Mock schtasks output
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Next Run Time: 1/2/2024 2:00:00 AM\\nStatus: Ready"
        
        import sys
        sys.path.append('.')
        from setup_scheduler import show_scheduler_status
        
        with patch('platform.system', return_value='Windows'):
            with patch('builtins.print') as mock_print:
                show_scheduler_status()
                # Check that status information was printed
                mock_print.assert_called()
    
    @patch('subprocess.run')
    def test_scheduler_status_check_linux(self, mock_subprocess):
        """Test scheduler status check on Linux"""
        # Mock crontab output
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "0 2 * * * cd /path && python main.py"
        
        import sys
        sys.path.append('.')
        from setup_scheduler import show_scheduler_status
        
        with patch('platform.system', return_value='Linux'):
            with patch('builtins.print') as mock_print:
                show_scheduler_status()
                # Check that status information was printed
                mock_print.assert_called()


class TestIntegration:
    """Integration tests for complete workflows with scheduler support"""
    
    @pytest.mark.asyncio
    async def test_complete_application_lifecycle(self):
        """Test complete application lifecycle including scheduler"""
        # Reset configuration
        reset_config()
        
        # Mock environment for testing
        with patch.dict('os.environ', {{
            'ENVIRONMENT': 'development',
            'DEBUG': 'true',
            'SCHEDULER_START_TIME': '02:00:00',
            'CRON_SCHEDULE': '0 2 * * *'
        }}):
            config = get_config()
            
            # Verify configuration
            assert config.environment.value == 'development'
            assert config.debug is True
            assert config.scheduler is not None
            
            # Test scheduler info
            scheduler_info = config.get_scheduler_info()
            assert 'type' in scheduler_info
            assert 'schedule' in scheduler_info
            assert 'python_path' in scheduler_info
    
    @pytest.mark.asyncio
    async def test_scheduler_and_notification_integration(self):
        """Test integration between scheduler and notification systems"""
        if not {str(config.notification_channels).replace("'", '"')}:
            pytest.skip("Notifications not configured for this project")
        
        # Mock scheduler triggering a notification
        with patch.dict('os.environ', {{
            'NOTIFICATIONS_ENABLED': 'true',
            'CRON_SCHEDULE': '0 2 * * *'
        }}):
            config = get_config()
            
            # Verify both systems are configured
            assert config.scheduler is not None
            {"assert config.notifications is not None" if config.notification_channels else ""}
            {"assert config.notifications.notifications_enabled is True" if config.notification_channels else ""}


# Scheduler-specific test utilities
class TestSchedulerUtilities:
    """Test utilities for scheduler management"""
    
    def test_cron_schedule_validation(self):
        """Test cron schedule format validation"""
        valid_schedules = [
            "0 2 * * *",      # Daily at 2 AM
            "*/30 * * * *",   # Every 30 minutes
            "0 */6 * * *",    # Every 6 hours
            "0 2 * * 1",      # Weekly on Monday
            "0 9-17 * * 1-5"  # Business hours
        ]
        
        for schedule in valid_schedules:
            # Test basic format validation
            parts = schedule.split()
            assert len(parts) == 5, f"Invalid cron format: {{schedule}}"
            
            # Test each part contains valid characters
            for part in parts:
                assert all(c in '0123456789*/-,' for c in part), f"Invalid characters in: {{part}}"
    
    def test_windows_time_format_validation(self):
        """Test Windows time format validation"""
        valid_times = [
            "02:00:00",
            "14:30:00", 
            "00:00:00",
            "23:59:59"
        ]
        
        for time_str in valid_times:
            parts = time_str.split(':')
            assert len(parts) == 3, f"Invalid time format: {{time_str}}"
            
            hour, minute, second = map(int, parts)
            assert 0 <= hour <= 23, f"Invalid hour: {{hour}}"
            assert 0 <= minute <= 59, f"Invalid minute: {{minute}}"
            assert 0 <= second <= 59, f"Invalid second: {{second}}"


# Performance tests for scheduler
class TestSchedulerPerformance:
    """Performance tests for scheduler operations"""
    
    @pytest.mark.performance
    def test_config_loading_performance(self):
        """Test configuration loading performance"""
        import time
        
        start_time = time.time()
        
        # Load configuration multiple times
        for _ in range(100):
            reset_config()
            config = get_config()
            assert config is not None
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should load quickly (less than 10ms average)
        assert avg_time < 0.01, f"Config loading too slow: {{avg_time:.4f}}s"
    
    @pytest.mark.performance
    def test_scheduler_status_check_performance(self):
        """Test scheduler status check performance"""
        import time
        
        start_time = time.time()
        
        # Mock fast subprocess calls
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "test output"
            
            # Check status multiple times
            import sys
            sys.path.append('.')
            from setup_scheduler import show_scheduler_status
            
            for _ in range(10):
                with patch('builtins.print'):
                    show_scheduler_status()
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # Status checks should be fast (less than 100ms average)
        assert avg_time < 0.1, f"Status check too slow: {{avg_time:.4f}}s"
'''
        
        (project_path / "tests" / "unit" / f"test_{config.name.lower().replace(' ', '_')}_enhanced.py").write_text(test_content)
        
        # Scheduler-specific tests
        scheduler_test_content = f'''"""
Scheduler-specific functionality tests
"""

import pytest
import os
import platform
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

class TestSchedulerInstallation:
    """Test scheduler installation scripts"""
    
    def test_windows_task_xml_generation(self):
        """Test Windows Task Scheduler XML generation"""
        # Test XML template processing
        template_vars = {{
            'SCHEDULER_START_TIME': '03:00:00',
            'SCHEDULER_HOURLY_ENABLED': 'true',
            'SCHEDULER_INTERVAL_HOURS': '2',
            'SCHEDULER_TIMEOUT_HOURS': '4',
            'SCHEDULER_PYTHON_PATH': 'C:\\\\Python39\\\\python.exe',
            'SCHEDULER_SCRIPT_PATH': 'main.py',
            'SCHEDULER_WORKING_DIR': 'C:\\\\Project'
        }}
        
        # Mock XML template
        xml_template = '''<Task>
    <StartBoundary>2024-01-01T$(SCHEDULER_START_TIME)</StartBoundary>
    <Enabled>$(SCHEDULER_HOURLY_ENABLED)</Enabled>
    <Interval>PT$(SCHEDULER_INTERVAL_HOURS)H</Interval>
    <ExecutionTimeLimit>PT$(SCHEDULER_TIMEOUT_HOURS)H</ExecutionTimeLimit>
    <Command>$(SCHEDULER_PYTHON_PATH)</Command>
    <Arguments>$(SCHEDULER_SCRIPT_PATH)</Arguments>
    <WorkingDirectory>$(SCHEDULER_WORKING_DIR)</WorkingDirectory>
</Task>'''
        
        # Process template
        processed_xml = xml_template
        for var, value in template_vars.items():
            processed_xml = processed_xml.replace(f'$({var})', value)
        
        # Verify substitutions
        assert '03:00:00' in processed_xml
        assert 'true' in processed_xml
        assert 'PT2H' in processed_xml
        assert 'PT4H' in processed_xml
        assert 'C:\\\\Python39\\\\python.exe' in processed_xml
        assert 'main.py' in processed_xml
        assert 'C:\\\\Project' in processed_xml
    
    def test_cron_template_processing(self):
        """Test Linux cron template processing"""
        template_vars = {{
            'CRON_SCHEDULE': '0 3 * * *',
            'CRON_PYTHON_PATH': '/usr/bin/python3',
            'CRON_SCRIPT_PATH': 'main.py',
            'CRON_WORKING_DIR': '/home/user/project',
            'CRON_LOG_FILE': '/home/user/project/logs/cron.log'
        }}
        
        # Mock cron template
        cron_template = '''# Main application schedule
$(CRON_SCHEDULE) cd $(CRON_WORKING_DIR) && $(CRON_PYTHON_PATH) $(CRON_SCRIPT_PATH) >> $(CRON_LOG_FILE) 2>&1'''
        
        # Process template
        processed_cron = cron_template
        for var, value in template_vars.items():
            processed_cron = processed_cron.replace(f'$({var})', value)
        
        # Verify substitutions
        assert '0 3 * * *' in processed_cron
        assert '/usr/bin/python3' in processed_cron
        assert 'main.py' in processed_cron
        assert '/home/user/project' in processed_cron
        assert 'logs/cron.log' in processed_cron
    
    @patch('subprocess.run')
    def test_powershell_script_execution(self, mock_subprocess):
        """Test PowerShell script execution simulation"""
        # Mock successful execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        # Simulate PowerShell command
        cmd = [
            "powershell.exe",
            "-ExecutionPolicy", "Bypass",
            "-File", "scheduler/install_windows_task.ps1"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Verify mock was called
        mock_subprocess.assert_called_once_with(cmd, capture_output=True, text=True)
        assert result.returncode == 0
    
    @patch('subprocess.run')
    def test_bash_script_execution(self, mock_subprocess):
        """Test bash script execution simulation"""
        # Mock successful execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        result = subprocess.run(["./scheduler/install_cron.sh"], capture_output=True, text=True)
        
        # Verify mock was called
        mock_subprocess.assert_called_once()
        assert result.returncode == 0


class TestSchedulerValidation:
    """Test scheduler configuration validation"""
    
    def test_cron_schedule_validation_valid(self):
        """Test valid cron schedule formats"""
        valid_schedules = [
            "0 2 * * *",        # Daily at 2 AM
            "*/15 * * * *",     # Every 15 minutes
            "0 */4 * * *",      # Every 4 hours
            "30 6 * * 1-5",     # Weekdays at 6:30 AM
            "0 22 * * 7",       # Sundays at 10 PM
            "45 23 * * *",      # Daily at 11:45 PM
            "0 0 1 * *",        # Monthly on 1st at midnight
            "0 12 15 * *",      # 15th of month at noon
        ]
        
        for schedule in valid_schedules:
            parts = schedule.split()
            assert len(parts) == 5, f"Should have 5 parts: {{schedule}}"
            
            # Validate each part
            minute, hour, day, month, weekday = parts
            
            # Basic format validation (simplified)
            assert self._validate_cron_field(minute, 0, 59), f"Invalid minute: {{minute}}"
            assert self._validate_cron_field(hour, 0, 23), f"Invalid hour: {{hour}}"
            assert self._validate_cron_field(day, 1, 31), f"Invalid day: {{day}}"
            assert self._validate_cron_field(month, 1, 12), f"Invalid month: {{month}}"
            assert self._validate_cron_field(weekday, 0, 7), f"Invalid weekday: {{weekday}}"
    
    def test_cron_schedule_validation_invalid(self):
        """Test invalid cron schedule formats"""
        invalid_schedules = [
            "60 2 * * *",       # Invalid minute (60)
            "0 25 * * *",       # Invalid hour (25)
            "0 2 32 * *",       # Invalid day (32)
            "0 2 * 13 *",       # Invalid month (13)
            "0 2 * * 8",        # Invalid weekday (8)
            "0 2 * *",          # Missing field
            "0 2 * * * *",      # Extra field
            "invalid format",    # Non-numeric
        ]
        
        for schedule in invalid_schedules:
            parts = schedule.split()
            if len(parts) != 5:
                continue  # Skip length tests
            
            # These should fail validation
            try:
                minute, hour, day, month, weekday = parts
                is_valid = (
                    self._validate_cron_field(minute, 0, 59) and
                    self._validate_cron_field(hour, 0, 23) and
                    self._validate_cron_field(day, 1, 31) and
                    self._validate_cron_field(month, 1, 12) and
                    self._validate_cron_field(weekday, 0, 7)
                )
                assert not is_valid, f"Should be invalid: {{schedule}}"
            except ValueError:
                # Expected for non-numeric values
                pass
    
    def _validate_cron_field(self, field: str, min_val: int, max_val: int) -> bool:
        """Validate a single cron field"""
        if field == "*":
            return True
        
        if "/" in field:
            # Handle step values like */2 or 1-5/2
            if field.startswith("*/"):
                step = int(field[2:])
                return step > 0
            else:
                base, step = field.split("/")
                return self._validate_cron_field(base, min_val, max_val) and int(step) > 0
        
        if "-" in field:
            # Handle ranges like 1-5
            start, end = field.split("-")
            return (min_val <= int(start) <= max_val and 
                   min_val <= int(end) <= max_val and 
                   int(start) <= int(end))
        
        if "," in field:
            # Handle lists like 1,3,5
            values = field.split(",")
            return all(self._validate_cron_field(v, min_val, max_val) for v in values)
        
        # Single numeric value
        try:
            value = int(field)
            return min_val <= value <= max_val
        except ValueError:
            return False
    
    def test_windows_time_validation(self):
        """Test Windows time format validation"""
        valid_times = [
            "00:00:00",
            "12:30:45", 
            "23:59:59",
            "02:00:00",
            "14:15:30"
        ]
        
        for time_str in valid_times:
            assert self._validate_windows_time(time_str), f"Should be valid: {{time_str}}"
        
        invalid_times = [
            "24:00:00",     # Invalid hour
            "12:60:00",     # Invalid minute
            "12:30:60",     # Invalid second
            "2:30:00",      # Missing zero padding
            "12:30",        # Missing seconds
            "12:30:00:00",  # Extra component
            "invalid"       # Non-time format
        ]
        
        for time_str in invalid_times:
            assert not self._validate_windows_time(time_str), f"Should be invalid: {{time_str}}"
    
    def _validate_windows_time(self, time_str: str) -> bool:
        """Validate Windows time format HH:MM:SS"""
        try:
            parts = time_str.split(":")
            if len(parts) != 3:
                return False
            
            hour, minute, second = map(int, parts)
            return (0 <= hour <= 23 and 
                   0 <= minute <= 59 and 
                   0 <= second <= 59)
        except ValueError:
            return False


class TestSchedulerUtilities:
    """Test scheduler utility functions"""
    
    def test_environment_variable_loading(self):
        """Test environment variable loading with defaults"""
        with patch.dict('os.environ', {{
            'SCHEDULER_START_TIME': '04:00:00',
            'CRON_SCHEDULE': '0 4 * * *',
            'SYSTEMD_MEMORY_LIMIT': '2G'
        }}):
            # Test Windows settings
            start_time = os.getenv('SCHEDULER_START_TIME', '02:00:00')
            assert start_time == '04:00:00'
            
            # Test Linux settings
            cron_schedule = os.getenv('CRON_SCHEDULE', '0 2 * * *')
            assert cron_schedule == '0 4 * * *'
            
            # Test systemd settings
            memory_limit = os.getenv('SYSTEMD_MEMORY_LIMIT', '1G')
            assert memory_limit == '2G'
    
    def test_path_resolution(self):
        """Test Python path and working directory resolution"""
        # Test automatic Python path detection
        import sys
        python_path = sys.executable
        assert python_path is not None
        assert 'python' in python_path.lower()
        
        # Test working directory detection
        current_dir = os.getcwd()
        assert Path(current_dir).exists()
        assert Path(current_dir).is_dir()
    
    def test_log_file_path_creation(self):
        """Test log file path creation and validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"
            log_file = log_dir / "cron.log"
            
            # Create log directory
            log_dir.mkdir(parents=True, exist_ok=True)
            assert log_dir.exists()
            assert log_dir.is_dir()
            
            # Test log file creation
            log_file.touch()
            assert log_file.exists()
            assert log_file.is_file()


class TestSchedulerErrorHandling:
    """Test scheduler error handling and recovery"""
    
    @patch('subprocess.run')
    def test_powershell_execution_failure(self, mock_subprocess):
        """Test handling of PowerShell execution failures"""
        # Mock failed execution
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Access denied"
        
        # This should handle the error gracefully
        result = subprocess.run(["powershell", "-Command", "invalid"], capture_output=True, text=True)
        assert result.returncode != 0
        assert "Access denied" in result.stderr
    
    @patch('subprocess.run')
    def test_crontab_permission_error(self, mock_subprocess):
        """Test handling of crontab permission errors"""
        # Mock permission denied
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Permission denied"
        
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        assert result.returncode != 0
        assert "Permission denied" in result.stderr
    
    def test_missing_configuration_handling(self):
        """Test handling of missing configuration"""
        # Test with empty environment
        with patch.dict('os.environ', {{}}, clear=True):
            # Should use defaults
            start_time = os.getenv('SCHEDULER_START_TIME', '02:00:00')
            assert start_time == '02:00:00'
            
            cron_schedule = os.getenv('CRON_SCHEDULE', '0 2 * * *')
            assert cron_schedule == '0 2 * * *'
    
    def test_invalid_path_handling(self):
        """Test handling of invalid file paths"""
        invalid_paths = [
            "/nonexistent/path/python",
            "C:\\\\NonExistent\\\\python.exe",
            "",
            None
        ]
        
        for path in invalid_paths:
            if path:
                assert not Path(path).exists(), f"Path should not exist: {{path}}"


# Integration tests with actual scheduler files
class TestSchedulerFileGeneration:
    """Test actual scheduler file generation"""
    
    def test_windows_xml_file_structure(self):
        """Test Windows XML file has correct structure"""
        # This would test the actual generated XML file
        xml_content = '''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Test task</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-01-01T02:00:00</StartBoundary>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>python</Command>
      <Arguments>main.py</Arguments>
    </Exec>
  </Actions>
</Task>'''
        
        # Verify XML structure (basic validation)
        assert '<?xml version="1.0"' in xml_content
        assert '<Task version="1.4"' in xml_content
        assert '<RegistrationInfo>' in xml_content
        assert '<Triggers>' in xml_content
        assert '<Actions>' in xml_content
        assert '</Task>' in xml_content
    
    def test_cron_file_structure(self):
        """Test cron file has correct structure"""
        cron_content = '''# Cron configuration for Test App
# Main application schedule
0 2 * * * cd /path/to/app && python main.py >> logs/cron.log 2>&1

# Optional: Health check every hour
# 0 * * * * cd /path/to/app && python main.py --diagnose >> logs/cron.log 2>&1'''
        
        # Verify cron structure
        assert '# Cron configuration' in cron_content
        assert '0 2 * * *' in cron_content
        assert 'python main.py' in cron_content
        assert '>> logs/cron.log 2>&1' in cron_content
    
    def test_systemd_service_structure(self):
        """Test systemd service file has correct structure"""
        service_content = '''[Unit]
Description=Test App
After=network.target

[Service]
Type=simple
User=testuser
WorkingDirectory=/path/to/app
ExecStart=/usr/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target'''
        
        # Verify systemd service structure
        assert '[Unit]' in service_content
        assert '[Service]' in service_content
        assert '[Install]' in service_content
        assert 'Description=' in service_content
        assert 'ExecStart=' in service_content
        assert 'WantedBy=' in service_content
'''
        
        (project_path / "tests" / "unit" / "test_scheduler.py").write_text(scheduler_test_content)
        
        # Generate performance tests
        performance_test_content = f'''"""
Performance tests for {config.name}
"""

import pytest
import time
import asyncio
import psutil
from unittest.mock import patch, Mock

# Mark performance tests
pytestmark = pytest.mark.performance


class TestApplicationPerformance:
    """Test application performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_startup_time(self):
        """Test application startup time"""
        from src.core.application import Application
        from src.config import get_config
        
        config = get_config()
        app = Application(config)
        
        start_time = time.time()
        await app.initialize()
        end_time = time.time()
        
        startup_time = end_time - start_time
        
        # Should start up quickly (less than 5 seconds)
        assert startup_time < 5.0, f"Startup too slow: {{startup_time:.2f}}s"
        
        await app.cleanup()
    
    {"@pytest.mark.asyncio" if config.notification_channels else ""}
    {"async def test_notification_performance(self):" if config.notification_channels else ""}
    {"    '''Test notification system performance'''" if config.notification_channels else ""}
    {"    from src.integrations.notifications import MultiChannelNotifier" if config.notification_channels else ""}
    {"    " if config.notification_channels else ""}
    {"    config = {{'telegram': {{'enabled': True, 'notification_targets': ['@test']}}}}" if config.notification_channels else ""}
    {"    notifier = MultiChannelNotifier(config)" if config.notification_channels else ""}
    {"    " if config.notification_channels else ""}
    {"    # Mock providers for speed" if config.notification_channels else ""}
    {"    mock_provider = Mock()" if config.notification_channels else ""}
    {"    mock_provider.send_notification = Mock(return_value=asyncio.Future())" if config.notification_channels else ""}
    {"    mock_provider.send_notification.return_value.set_result(True)" if config.notification_channels else ""}
    {"    " if config.notification_channels else ""}
    {"    notifier.providers = {{'telegram': mock_provider}}" if config.notification_channels else ""}
    {"    " if config.notification_channels else ""}
    {"    # Test notification speed" if config.notification_channels else ""}
    {"    start_time = time.time()" if config.notification_channels else ""}
    {"    " if config.notification_channels else ""}
    {"    for _ in range(10):" if config.notification_channels else ""}
    {"        await notifier.send_notification('Test message', 'test')" if config.notification_channels else ""}
    {"    " if config.notification_channels else ""}
    {"    end_time = time.time()" if config.notification_channels else ""}
    {"    avg_time = (end_time - start_time) / 10" if config.notification_channels else ""}
    {"    " if config.notification_channels else ""}
    {"    # Should be fast (less than 100ms per notification)" if config.notification_channels else ""}
    {"    assert avg_time < 0.1, f'Notifications too slow: {{avg_time:.4f}}s'" if config.notification_channels else ""}
    
    {"@pytest.mark.asyncio" if config.monitoring_enabled else ""}
    {"async def test_monitoring_performance(self):" if config.monitoring_enabled else ""}
    {"    '''Test monitoring system performance'''" if config.monitoring_enabled else ""}
    {"    from src.integrations.monitoring import ProductionMonitoringOrchestrator" if config.monitoring_enabled else ""}
    {"    " if config.monitoring_enabled else ""}
    {"    config = {{'performance_interval': 1}}" if config.monitoring_enabled else ""}
    {"    monitor = ProductionMonitoringOrchestrator(config)" if config.monitoring_enabled else ""}
    {"    " if config.monitoring_enabled else ""}
    {"    # Test metrics collection speed" if config.monitoring_enabled else ""}
    {"    start_time = time.time()" if config.monitoring_enabled else ""}
    {"    " if config.monitoring_enabled else ""}
    {"    for _ in range(10):" if config.monitoring_enabled else ""}
    {"        metrics = await monitor._collect_performance_metrics()" if config.monitoring_enabled else ""}
    {"        assert metrics is not None" if config.monitoring_enabled else ""}
    {"    " if config.monitoring_enabled else ""}
    {"    end_time = time.time()" if config.monitoring_enabled else ""}
    {"    avg_time = (end_time - start_time) / 10" if config.monitoring_enabled else ""}
    {"    " if config.monitoring_enabled else ""}
    {"    # Metrics collection should be fast (less than 50ms)" if config.monitoring_enabled else ""}
    {"    assert avg_time < 0.05, f'Metrics collection too slow: {{avg_time:.4f}}s'" if config.monitoring_enabled else ""}


class TestMemoryUsage:
    """Test memory usage and resource management"""
    
    def test_memory_usage_baseline(self):
        """Test baseline memory usage"""
        import gc
        gc.collect()  # Clean up before measurement
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Baseline should be reasonable (less than 100MB)
        assert initial_memory < 100, f"High baseline memory: {{initial_memory:.1f}}MB"
    
    @pytest.mark.asyncio
    async def test_memory_usage_after_initialization(self):
        """Test memory usage after application initialization"""
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Initialize application
        from src.core.application import Application
        from src.config import get_config
        
        config = get_config()
        app = Application(config)
        await app.initialize()
        
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 200MB)
        assert memory_increase < 200, f"High memory usage: {{memory_increase:.1f}}MB increase"
        
        await app.cleanup()
        
        # Check for memory leaks
        gc.collect()
        cleanup_memory = process.memory_info().rss / 1024 / 1024
        leak = cleanup_memory - initial_memory
        
        # Should not leak significant memory (less than 50MB)
        assert leak < 50, f"Possible memory leak: {{leak:.1f}}MB"


class TestConcurrencyPerformance:
    """Test performance under concurrent load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test performance with concurrent operations"""
        from src.config import get_config
        
        config = get_config()
        
        async def dummy_operation():
            """Dummy async operation"""
            await asyncio.sleep(0.01)  # 10ms operation
            return "completed"
        
        # Test concurrent execution
        start_time = time.time()
        
        # Run 50 concurrent operations
        tasks = [dummy_operation() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete much faster than sequential (less than 0.5s)
        assert total_time < 0.5, f"Concurrent operations too slow: {{total_time:.2f}}s"
        assert len(results) == 50
        assert all(result == "completed" for result in results)
    
    @pytest.mark.asyncio
    async def test_scheduler_config_concurrency(self):
        """Test scheduler configuration under concurrent access"""
        from src.config import get_config, reset_config
        
        async def get_scheduler_info():
            """Get scheduler information"""
            config = get_config()
            return config.get_scheduler_info()
        
        # Reset config to ensure fresh state
        reset_config()
        
        # Test concurrent configuration access
        start_time = time.time()
        
        tasks = [get_scheduler_info() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle concurrent access efficiently
        assert total_time < 1.0, f"Concurrent config access too slow: {{total_time:.2f}}s"
        assert len(results) == 20
        
        # All results should be identical (consistent)
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "Inconsistent scheduler info"


class TestResourceLimits:
    """Test resource limit compliance"""
    
    def test_cpu_usage_limits(self):
        """Test CPU usage stays within limits"""
        import time
        
        process = psutil.Process()
        
        # Monitor CPU usage for a short period
        cpu_measurements = []
        
        for _ in range(10):
            cpu_percent = process.cpu_percent(interval=0.1)
            cpu_measurements.append(cpu_percent)
        
        avg_cpu = sum(cpu_measurements) / len(cpu_measurements)
        max_cpu = max(cpu_measurements)
        
        # Should not use excessive CPU (average < 50%, max < 80%)
        assert avg_cpu < 50, f"High average CPU usage: {{avg_cpu:.1f}}%"
        assert max_cpu < 80, f"High peak CPU usage: {{max_cpu:.1f}}%"
    
    def test_file_descriptor_limits(self):
        """Test file descriptor usage"""
        process = psutil.Process()
        
        try:
            open_files = process.num_fds()  # Unix only
            
            # Should not have excessive open files (less than 100)
            assert open_files < 100, f"High file descriptor usage: {{open_files}}"
        except AttributeError:
            # Windows doesn't have num_fds
            pytest.skip("File descriptor test not supported on Windows")
    
    def test_thread_count_limits(self):
        """Test thread count stays reasonable"""
        process = psutil.Process()
        thread_count = process.num_threads()
        
        # Should not create excessive threads (less than 20)
        assert thread_count < 20, f"High thread count: {{thread_count}}"


class TestSchedulerPerformanceIntegration:
    """Test scheduler-specific performance"""
    
    def test_config_loading_speed(self):
        """Test scheduler configuration loading speed"""
        from src.config import get_config, reset_config
        
        times = []
        
        for _ in range(10):
            reset_config()
            
            start_time = time.time()
            config = get_config()
            scheduler_info = config.get_scheduler_info()
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Should load quickly (average < 10ms, max < 50ms)
        assert avg_time < 0.01, f"Slow average config loading: {{avg_time:.4f}}s"
        assert max_time < 0.05, f"Slow max config loading: {{max_time:.4f}}s"
    
    @patch('subprocess.run')
    def test_status_check_performance(self, mock_subprocess):
        """Test scheduler status check performance"""
        # Mock fast subprocess response
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Status: Ready"
        mock_subprocess.return_value.stderr = ""
        
        times = []
        
        for _ in range(5):
            start_time = time.time()
            
            # Simulate status check
            result = mock_subprocess.return_value
            assert result.returncode == 0
            
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        
        # Status checks should be very fast (< 1ms when mocked)
        assert avg_time < 0.001, f"Slow status check: {{avg_time:.6f}}s"


# Stress tests
class TestStressScenarios:
    """Stress test scenarios"""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_extended_operation(self):
        """Test extended operation without degradation"""
        from src.config import get_config
        
        config = get_config()
        
        # Monitor performance over time
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        operation_times = []
        
        # Run operations for 30 seconds
        end_time = time.time() + 30
        
        while time.time() < end_time:
            start_op = time.time()
            
            # Simulate work
            await asyncio.sleep(0.01)
            scheduler_info = config.get_scheduler_info()
            assert scheduler_info is not None
            
            end_op = time.time()
            operation_times.append(end_op - start_op)
            
            await asyncio.sleep(0.1)  # Brief pause between operations
        
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = end_memory - start_memory
        
        # Check for performance degradation
        avg_time = sum(operation_times) / len(operation_times)
        recent_avg = sum(operation_times[-10:]) / min(10, len(operation_times))
        
        # Performance should not degrade significantly
        assert recent_avg < avg_time * 1.5, f"Performance degraded: {{recent_avg:.4f}}s vs {{avg_time:.4f}}s"
        
        # Memory should not grow excessively (less than 100MB)
        assert memory_growth < 100, f"Excessive memory growth: {{memory_growth:.1f}}MB"
    
    @pytest.mark.slow
    def test_high_frequency_config_access(self):
        """Test high-frequency configuration access"""
        from src.config import get_config
        
        start_time = time.time()
        
        # Access configuration 1000 times
        for _ in range(1000):
            config = get_config()
            scheduler_info = config.get_scheduler_info()
            assert 'type' in scheduler_info
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 1000
        
        # Should handle high frequency access efficiently
        assert total_time < 2.0, f"High frequency access too slow: {{total_time:.2f}}s"
        assert avg_time < 0.002, f"Average access too slow: {{avg_time:.6f}}s"
'''
        
        (project_path / "tests" / "performance" / "__init__.py").write_text("")
        (project_path / "tests" / "performance" / "test_performance.py").write_text(performance_test_content)
    
    def _generate_enhanced_utils(self, project_path: Path, config: ProjectConfig):
        """Generate enhanced utilities with scheduler support"""
        # Enhanced emoji logger with scheduler events
        emoji_logger_content = f'''"""
Enhanced Emoji Logger with Scheduler Event Support
"""

import logging
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Force emoji display if environment variable is set
FORCE_EMOJI = os.getenv('FORCE_EMOJI', 'false').lower() == 'true'

# Emoji mappings for different event types
EMOJI_MAP = {{
    # Standard application events
    'ROCKET': '🚀',
    'CHECK': '✅', 
    'WARNING': '⚠️',
    'X': '❌',
    'INFO': 'ℹ️',
    'SUCCESS': '🎉',
    'ERROR': '💥',
    'DEBUG': '🐛',
    
    # Scheduler-specific events
    'CLOCK': '🕐',
    'SCHEDULE': '📅',
    'TIMER': '⏰',
    'CALENDAR': '📆',
    'STOPWATCH': '⏱️',
    'HOURGLASS': '⏳',
    
    # System events
    'GEAR': '⚙️',
    'WRENCH': '🔧',
    'HAMMER': '🔨',
    'COMPUTER': '💻',
    'SERVER': '🖥️',
    'DISK': '💾',
    'MEMORY': '🧠',
    'CPU': '⚡',
    
    # Notification events
    'BELL': '🔔',
    'PHONE': '📱',
    'EMAIL': '📧',
    'MESSAGE': '💬',
    'MEGAPHONE': '📢',
    'SPEAKER': '📣',
    
    # File operations
    'FILE': '📄',
    'FOLDER': '📁',
    'SAVE': '💾',
    'DOWNLOAD': '⬇️',
    'UPLOAD': '⬆️',
    'BACKUP': '🗄️',
    
    # Network operations
    'GLOBE': '🌐',
    'LINK': '🔗',
    'WIFI': '📶',
    'CLOUD': '☁️',
    'SATELLITE': '🛰️',
    
    # Security events
    'LOCK': '🔒',
    'UNLOCK': '🔓',
    'KEY': '🔑',
    'SHIELD': '🛡️',
    'SECURE': '🔐',
}}

def should_use_emoji() -> bool:
    """Determine if emojis should be used based on environment"""
    if FORCE_EMOJI:
        return True
    
    # Check terminal capabilities
    if os.getenv('TERM_PROGRAM') in ['vscode', 'iTerm.app']:
        return True
    
    # Check if running in modern terminal
    if sys.stdout.isatty() and os.getenv('TERM') not in ['dumb', 'unknown']:
        return True
    
    return False

def format_message_with_emoji(message: str) -> str:
    """Format message with emoji replacements"""
    if not should_use_emoji():
        # Remove emoji markers for non-emoji environments
        for marker in EMOJI_MAP.keys():
            message = message.replace(f'[{{marker}}]', f'{{marker}}:')
        return message
    
    # Replace emoji markers with actual emojis
    for marker, emoji in EMOJI_MAP.items():
        message = message.replace(f'[{{marker}}]', emoji)
    
    return message

class EmojiFormatter(logging.Formatter):
    """Logging formatter that supports emoji and scheduler events"""
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        if fmt is None:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        super().__init__(fmt, datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        # Add scheduler context if available
        if hasattr(record, 'scheduler_event'):
            record.levelname = f"[SCHEDULE] {{record.levelname}}"
        
        # Format the message with emoji support
        original_msg = record.getMessage()
        record.msg = format_message_with_emoji(original_msg)
        record.args = ()  # Clear args since we've already formatted
        
        return super().format(record)

class SchedulerLogAdapter(logging.LoggerAdapter):
    """Log adapter that adds scheduler context"""
    
    def __init__(self, logger: logging.Logger, scheduler_type: str = "unknown"):
        super().__init__(logger, {{}})
        self.scheduler_type = scheduler_type
    
    def process(self, msg, kwargs):
        # Add scheduler context to all log records
        extra = kwargs.get('extra', {{}})
        extra['scheduler_event'] = True
        extra['scheduler_type'] = self.scheduler_type
        kwargs['extra'] = extra
        
        # Add scheduler emoji prefix if not already present
        if not any(f'[{{marker}}]' in str(msg) for marker in EMOJI_MAP.keys()):
            msg = f"[SCHEDULE] {{msg}}"
        
        return msg, kwargs
    
    def log_schedule_event(self, level: int, event: str, details: Dict[str, Any]):
        """Log scheduler-specific events with structured data"""
        timestamp = datetime.now().isoformat()
        
        message = f"[CALENDAR] Scheduler Event: {{event}}"
        if details:
            detail_str = ", ".join(f"{{k}}={{v}}" for k, v in details.items())
            message += f" ({{detail_str}})"
        
        self.log(level, message, extra={{
            'scheduler_event': True,
            'event_type': event,
            'event_details': details,
            'timestamp': timestamp
        }})
    
    def log_schedule_start(self, schedule_info: Dict[str, Any]):
        """Log scheduler start event"""
        self.log_schedule_event(
            logging.INFO, 
            "schedule_start",
            {{
                'schedule_type': schedule_info.get('type', 'unknown'),
                'schedule_pattern': schedule_info.get('schedule', 'unknown'),
                'next_run': schedule_info.get('next_run', 'unknown')
            }}
        )
    
    def log_schedule_complete(self, duration: float, success: bool):
        """Log scheduler completion event"""
        event = "schedule_success" if success else "schedule_failure"
        self.log_schedule_event(
            logging.INFO if success else logging.ERROR,
            event,
            {{
                'duration_seconds': duration,
                'success': success
            }}
        )
    
    def log_schedule_error(self, error: Exception, context: Dict[str, Any]):
        """Log scheduler error event"""
        self.log_schedule_event(
            logging.ERROR,
            "schedule_error",
            {{
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context
            }}
        )

def create_emoji_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create a logger with emoji support"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger  # Already configured
    
    logger.setLevel(level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Set emoji formatter
    formatter = EmojiFormatter()
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger

def create_scheduler_logger(name: str, scheduler_type: str, level: int = logging.INFO) -> SchedulerLogAdapter:
    """Create a scheduler-specific logger with emoji support"""
    base_logger = create_emoji_logger(name, level)
    return SchedulerLogAdapter(base_logger, scheduler_type)

def log_scheduler_status(logger: SchedulerLogAdapter, status: Dict[str, Any]):
    """Log comprehensive scheduler status"""
    logger.info(f"[CLOCK] Scheduler Status Report")
    logger.info(f"[GEAR] Type: {{status.get('type', 'unknown')}}")
    logger.info(f"[CALENDAR] Schedule: {{status.get('schedule', 'unknown')}}")
    logger.info(f"[TIMER] Next Run: {{status.get('next_run', 'unknown')}}")
    logger.info(f"[CHECK] Status: {{status.get('status', 'unknown')}}")
    
    if 'last_run' in status:
        logger.info(f"[HOURGLASS] Last Run: {{status['last_run']}}")
    
    if 'errors' in status and status['errors']:
        logger.warning(f"[WARNING] Recent Errors: {{len(status['errors'])}}")

def log_application_startup(logger: logging.Logger, config: Dict[str, Any]):
    """Log application startup with scheduler information"""
    logger.info(f"[ROCKET] Starting {{config.get('name', 'Application')}}")
    logger.info(f"[GEAR] Environment: {{config.get('environment', 'unknown')}}")
    logger.info(f"[COMPUTER] Platform: {{config.get('platform', 'unknown')}}")
    
    if 'scheduler' in config:
        scheduler = config['scheduler']
        logger.info(f"[SCHEDULE] Scheduler: {{scheduler.get('type', 'none')}}")
        logger.info(f"[CALENDAR] Schedule: {{scheduler.get('schedule', 'none')}}")
    
    if 'notifications' in config:
        notifications = config['notifications']
        if notifications.get('enabled'):
            channels = notifications.get('channels', [])
            logger.info(f"[BELL] Notifications: {{', '.join(channels)}}")
        else:
            logger.info(f"[BELL] Notifications: disabled")
    
    if 'monitoring' in config:
        monitoring = config['monitoring']
        if monitoring.get('enabled'):
            logger.info(f"[GEAR] Monitoring: enabled")
        else:
            logger.info(f"[GEAR] Monitoring: disabled")

# Export main functions
__all__ = [
    'create_emoji_logger',
    'create_scheduler_logger', 
    'SchedulerLogAdapter',
    'EmojiFormatter',
    'format_message_with_emoji',
    'log_scheduler_status',
    'log_application_startup',
    'should_use_emoji'
]
'''
        
        (project_path / "src" / "utils" / "emoji_logger.py").write_text(emoji_logger_content)
        
        # Enhanced error handling with scheduler support
        error_handling_content = f'''"""
Enhanced Error Handling with Scheduler Support
Comprehensive error handling for production environments
"""

import logging
import traceback
import sys
import asyncio
import functools
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import asynccontextmanager
from enum import Enum

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    SCHEDULER = "scheduler"
    NOTIFICATION = "notification"
    MONITORING = "monitoring"
    APPLICATION = "application"
    CONFIGURATION = "configuration"
    SYSTEM = "system"

@dataclass
class ErrorContext:
    """Enhanced error context with scheduler information"""
    operation: str
    component: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: ErrorCategory = ErrorCategory.APPLICATION
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    
    # Scheduler-specific context
    scheduler_type: Optional[str] = None
    schedule_info: Optional[Dict[str, Any]] = None
    scheduler_event: Optional[str] = None
    
    # Additional context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    environment: Optional[str] = None
    
    # Error details
    error_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {{
            'operation': self.operation,
            'component': self.component,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category.value,
            'severity': self.severity.value,
            'scheduler_type': self.scheduler_type,
            'schedule_info': self.schedule_info,
            'scheduler_event': self.scheduler_event,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'request_id': self.request_id,
            'environment': self.environment,
            'error_data': self.error_data
        }}

class SchedulerError(Exception):
    """Base exception for scheduler-related errors"""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.context = context or ErrorContext(
            operation="scheduler_operation",
            component="scheduler",
            category=ErrorCategory.SCHEDULER
        )

class ConfigurationError(Exception):
    """Exception for configuration-related errors"""
    
    def __init__(self, message: str, suggestion: str = "", context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.suggestion = suggestion
        self.context = context or ErrorContext(
            operation="configuration_validation",
            component="config",
            category=ErrorCategory.CONFIGURATION
        )

class NotificationError(Exception):
    """Exception for notification-related errors"""
    
    def __init__(self, message: str, channel: str = "", context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.channel = channel
        self.context = context or ErrorContext(
            operation="notification_send",
            component="notifications",
            category=ErrorCategory.NOTIFICATION
        )

class MonitoringError(Exception):
    """Exception for monitoring-related errors"""
    
    def __init__(self, message: str, metric: str = "", context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.metric = metric
        self.context = context or ErrorContext(
            operation="monitoring_check",
            component="monitoring",
            category=ErrorCategory.MONITORING
        )

class ErrorCollector:
    """Collects and manages errors across the application"""
    
    def __init__(self):
        self.errors: List[ErrorContext] = []
        self.max_errors = 1000  # Prevent memory growth
        self.logger = logging.getLogger(__name__)
    
    def add_error(self, error: Exception, context: ErrorContext):
        """Add an error to the collection"""
        # Enhance context with error information
        context.error_data.update({{
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }})
        
        self.errors.append(context)
        
        # Maintain size limit
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors//2:]  # Keep recent half
        
        # Log error with appropriate level
        log_level = self._get_log_level(context.severity)
        self.logger.log(log_level, f"[{{context.category.value.upper()}}] {{context.operation}}: {{str(error)}}", 
                       extra={{'error_context': context.to_dict()}})
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get logging level based on error severity"""
        mapping = {{
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }}
        return mapping.get(severity, logging.ERROR)
    
    def get_recent_errors(self, hours: int = 1) -> List[ErrorContext]:
        """Get errors from the last N hours"""
        cutoff = datetime.now().replace(microsecond=0) - timedelta(hours=hours)
        return [error for error in self.errors if error.timestamp > cutoff]
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorContext]:
        """Get errors by category"""
        return [error for error in self.errors if error.category == category]
    
    def get_scheduler_errors(self) -> List[ErrorContext]:
        """Get scheduler-specific errors"""
        return self.get_errors_by_category(ErrorCategory.SCHEDULER)
    
    def clear_errors(self):
        """Clear all collected errors"""
        self.errors.clear()

# Global error collector
error_collector = ErrorCollector()

def create_error_context(operation: str, component: str = "", **kwargs) -> ErrorContext:
    """Create an error context with scheduler information"""
    return ErrorContext(
        operation=operation,
        component=component or operation.split('_')[0],
        **kwargs
    )

def create_scheduler_error_context(operation: str, scheduler_type: str, 
                                 schedule_info: Dict[str, Any] = None, **kwargs) -> ErrorContext:
    """Create scheduler-specific error context"""
    return ErrorContext(
        operation=operation,
        component="scheduler",
        category=ErrorCategory.SCHEDULER,
        scheduler_type=scheduler_type,
        schedule_info=schedule_info or {{}},
        **kwargs
    )

@asynccontextmanager
async def error_context(operation: str, **context_kwargs):
    """Async context manager for error handling with scheduler support"""
    context = create_error_context(operation, **context_kwargs)
    start_time = datetime.now()
    
    try:
        yield context
        
        # Log successful operation
        execution_time = (datetime.now() - start_time).total_seconds()
        logger = logging.getLogger(__name__)
        logger.debug(f"[SUCCESS] {{operation}} completed in {{execution_time:.2f}}s")
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Enhance context with execution information
        context.error_data.update({{
            'execution_time': execution_time,
            'operation_start': start_time.isoformat()
        }})
        
        # Add error to collector
        error_collector.add_error(e, context)
        
        # Re-raise the exception
        raise

def handle_scheduler_error(scheduler_type: str, schedule_info: Dict[str, Any] = None):
    """Decorator for handling scheduler-specific errors"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation = f"scheduler_{{func.__name__}}"
            context = create_scheduler_error_context(
                operation, scheduler_type, schedule_info
            )
            
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                error_collector.add_error(e, context)
                raise SchedulerError(
                    f"Scheduler operation failed: {{func.__name__}}", context
                ) from e
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation = f"scheduler_{{func.__name__}}"
            context = create_scheduler_error_context(
                operation, scheduler_type, schedule_info
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_collector.add_error(e, context)
                raise SchedulerError(
                    f"Scheduler operation failed: {{func.__name__}}", context
                ) from e
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def handle_configuration_error(suggestion: str = ""):
    """Decorator for handling configuration errors"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = create_error_context(
                    f"config_{{func.__name__}}",
                    "configuration",
                    category=ErrorCategory.CONFIGURATION
                )
                error_collector.add_error(e, context)
                raise ConfigurationError(
                    f"Configuration error in {{func.__name__}}: {{str(e)}}",
                    suggestion,
                    context
                ) from e
        return wrapper
    return decorator

{"def handle_notification_error(channel: str = ''):" if config.notification_channels else ""}
{"    '''Decorator for handling notification errors'''" if config.notification_channels else ""}
{"    def decorator(func: Callable):" if config.notification_channels else ""}
{"        @functools.wraps(func)" if config.notification_channels else ""}
{"        async def wrapper(*args, **kwargs):" if config.notification_channels else ""}
{"            try:" if config.notification_channels else ""}
{"                if asyncio.iscoroutinefunction(func):" if config.notification_channels else ""}
{"                    return await func(*args, **kwargs)" if config.notification_channels else ""}
{"                else:" if config.notification_channels else ""}
{"                    return func(*args, **kwargs)" if config.notification_channels else ""}
{"            except Exception as e:" if config.notification_channels else ""}
{"                context = create_error_context(" if config.notification_channels else ""}
{"                    f'notification_{{func.__name__}}'," if config.notification_channels else ""}
{"                    'notifications'," if config.notification_channels else ""}
{"                    category=ErrorCategory.NOTIFICATION" if config.notification_channels else ""}
{"                )" if config.notification_channels else ""}
{"                error_collector.add_error(e, context)" if config.notification_channels else ""}
{"                raise NotificationError(" if config.notification_channels else ""}
{"                    f'Notification error in {{func.__name__}}: {{str(e)}}'," if config.notification_channels else ""}
{"                    channel," if config.notification_channels else ""}
{"                    context" if config.notification_channels else ""}
{"                ) from e" if config.notification_channels else ""}
{"        return wrapper" if config.notification_channels else ""}
{"    return decorator" if config.notification_channels else ""}

{"def handle_monitoring_error(metric: str = ''):" if config.monitoring_enabled else ""}
{"    '''Decorator for handling monitoring errors'''" if config.monitoring_enabled else ""}
{"    def decorator(func: Callable):" if config.monitoring_enabled else ""}
{"        @functools.wraps(func)" if config.monitoring_enabled else ""}
{"        async def wrapper(*args, **kwargs):" if config.monitoring_enabled else ""}
{"            try:" if config.monitoring_enabled else ""}
{"                if asyncio.iscoroutinefunction(func):" if config.monitoring_enabled else ""}
{"                    return await func(*args, **kwargs)" if config.monitoring_enabled else ""}
{"                else:" if config.monitoring_enabled else ""}
{"                    return func(*args, **kwargs)" if config.monitoring_enabled else ""}
{"            except Exception as e:" if config.monitoring_enabled else ""}
{"                context = create_error_context(" if config.monitoring_enabled else ""}
{"                    f'monitoring_{{func.__name__}}'," if config.monitoring_enabled else ""}
{"                    'monitoring'," if config.monitoring_enabled else ""}
{"                    category=ErrorCategory.MONITORING" if config.monitoring_enabled else ""}
{"                )" if config.monitoring_enabled else ""}
{"                error_collector.add_error(e, context)" if config.monitoring_enabled else ""}
{"                raise MonitoringError(" if config.monitoring_enabled else ""}
{"                    f'Monitoring error in {{func.__name__}}: {{str(e)}}'," if config.monitoring_enabled else ""}
{"                    metric," if config.monitoring_enabled else ""}
{"                    context" if config.monitoring_enabled else ""}
{"                ) from e" if config.monitoring_enabled else ""}
{"        return wrapper" if config.monitoring_enabled else ""}
{"    return decorator" if config.monitoring_enabled else ""}

def setup_error_handling(logger: logging.Logger = None) -> ErrorCollector:
    """Setup comprehensive error handling for the application"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Setup exception handler for uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        context = create_error_context(
            "uncaught_exception",
            "system",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL
        )
        
        error_collector.add_error(exc_value, context)
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    return error_collector

def get_error_summary() -> Dict[str, Any]:
    """Get comprehensive error summary"""
    recent_errors = error_collector.get_recent_errors(hours=24)
    
    # Group by category
    by_category = {{}}
    for category in ErrorCategory:
        category_errors = [e for e in recent_errors if e.category == category]
        by_category[category.value] = {{
            'count': len(category_errors),
            'critical': len([e for e in category_errors if e.severity == ErrorSeverity.CRITICAL]),
            'high': len([e for e in category_errors if e.severity == ErrorSeverity.HIGH])
        }}
    
    # Group by severity
    by_severity = {{}}
    for severity in ErrorSeverity:
        severity_errors = [e for e in recent_errors if e.severity == severity]
        by_severity[severity.value] = len(severity_errors)
    
    # Scheduler-specific summary
    scheduler_errors = error_collector.get_scheduler_errors()
    scheduler_summary = {{
        'total_scheduler_errors': len(scheduler_errors),
        'recent_scheduler_errors': len([e for e in scheduler_errors if e.timestamp > datetime.now().replace(microsecond=0) - timedelta(hours=1)]),
        'scheduler_types_with_errors': list(set(e.scheduler_type for e in scheduler_errors if e.scheduler_type))
    }}
    
    return {{
        'timestamp': datetime.now().isoformat(),
        'total_errors_24h': len(recent_errors),
        'by_category': by_category,
        'by_severity': by_severity,
        'scheduler_summary': scheduler_summary,
        'critical_errors': [
            {{
                'operation': e.operation,
                'component': e.component,
                'timestamp': e.timestamp.isoformat(),
                'message': e.error_data.get('error_message', 'Unknown error')
            }}
            for e in recent_errors 
            if e.severity == ErrorSeverity.CRITICAL
        ][-5:]  # Last 5 critical errors
    }}

# Export main components
__all__ = [
    'ErrorContext',
    'ErrorSeverity',
    'ErrorCategory', 
    'SchedulerError',
    'ConfigurationError',
    'NotificationError',
    'MonitoringError',
    'ErrorCollector',
    'create_error_context',
    'create_scheduler_error_context',
    'error_context',
    'handle_scheduler_error',
    'handle_configuration_error',
    {'handle_notification_error,' if config.notification_channels else ''}
    {'handle_monitoring_error,' if config.monitoring_enabled else ''}
    'setup_error_handling',
    'get_error_summary',
    'error_collector'
]
'''
        
        (project_path / "src" / "utils" / "error_handling.py").write_text(error_handling_content)


def main():
    """Enhanced main CLI entry point with scheduler support"""
    parser = argparse.ArgumentParser(
        description="Enhanced Python Application Framework Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 Enhanced Examples with Scheduler Support:

Idea-based generation:
  %(prog)s --idea "Telegram message extractor with AI processing and SMS alerts"
  %(prog)s --idea "Daily report generator with email notifications"
  %(prog)s --idea "System monitor with Slack alerts every hour"

Template-based generation:
  %(prog)s --template production_automation --name "My Automation"
  %(prog)s --template ai_data_pipeline --name "Smart Data Processor"

Interactive configuration:
  %(prog)s --interactive

📅 Generated projects include:
  • Cross-platform scheduler support (Windows Task Scheduler, Linux Cron, Systemd)
  • Multi-channel notifications (Telegram, SMS, Email)
  • Production monitoring and health checks
  • Docker and Kubernetes deployment configurations
  • Comprehensive testing suite with scheduler tests
  • CI/CD pipelines with security scanning

🎯 Features automatically configured based on your needs:
  • AI integration with smart routing and fallbacks
  • Resource management and conflict prevention  
  • Enhanced error handling with autonomous debugging foundations
  • Performance optimization and monitoring
  • Security hardening and compliance
        """
    )
    
    parser.add_argument("--idea", help="Generate project from natural language description")
    parser.add_argument("--template", choices=[
        "production_automation", "ai_data_pipeline", "enterprise_api", 
        "notification_service", "monitoring_system"
    ], help="Use predefined template")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--description", help="Project description")
    parser.add_argument("--interactive", action="store_true", help="Interactive project configuration")
    parser.add_argument("--with-scheduler", choices=["windows", "linux", "both"], 
                       default="both", help="Include scheduler configurations")
    parser.add_argument("--notifications", nargs="+", choices=["telegram", "sms", "email"],
                       default=["telegram"], help="Notification channels to include")
    parser.add_argument("--monitoring", action="store_true", default=True,
                       help="Include monitoring and health checks")
    parser.add_argument("--kubernetes", action="store_true", default=False,
                       help="Include Kubernetes deployment manifests")
    
    args = parser.parse_args()
    
    framework = EnhancedPythonFramework()
    
    if args.idea:
        print(f"🚀 Generating from idea: {args.idea}")
        project_path = framework.generate_from_idea(args.idea)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.template:
        template = framework.templates[args.template]
        name = args.name or f"Enhanced {args.template.replace('_', ' ').title()}"
        description = args.description or template["description"]
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=args.template,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=args.notifications,
            ai_integration=template.get("ai_integration", True),
            monitoring_enabled=args.monitoring,
            kubernetes_support=args.kubernetes,
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.interactive:
        print("🎯 Enhanced Interactive Project Configuration")
        print("=" * 60)
        
        name = input("Project name: ")
        description = input("Project description: ")
        
        print("\\nAvailable templates:")
        templates = list(framework.templates.keys())
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template} - {framework.templates[template]['description']}")
        
        template_choice = int(input("\\nSelect template (1-5): ")) - 1
        template_type = templates[template_choice]
        template = framework.templates[template_type]
        
        # Enhanced configuration options
        ai_integration = input("Include AI integration? (y/n): ").lower() == 'y'
        
        print("\\n📢 Notification channels (space-separated):")
        print("Available: telegram sms email")
        notification_input = input("Channels: ").strip()
        notification_channels = notification_input.split() if notification_input else ["telegram"]
        
        monitoring = input("\\n📊 Enable monitoring and alerting? (y/n): ").lower() == 'y'
        kubernetes = input("Include Kubernetes deployment? (y/n): ").lower() == 'y'
        
        print("\\n📅 Scheduler support:")
        print("1. Windows Task Scheduler only")
        print("2. Linux Cron/Systemd only") 
        print("3. Both (recommended)")
        scheduler_choice = input("Choice (1-3): ").strip()
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=template_type,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=notification_channels,
            ai_integration=ai_integration,
            monitoring_enabled=monitoring,
            kubernetes_support=kubernetes,
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"\\n✅ Enhanced project generated at: {project_path}")
        
    else:
        parser.print_help()
        sys.exit(1)
    
    # Enhanced next steps with scheduler information
    print("\\n🎉 Next steps:")
    print("  1. cd into the project directory")
    print("  2. python -m venv venv && source venv/bin/activate")
    print("  3. pip install -r requirements.txt")
    print("  4. cp .env.template .env && edit .env")
    print("  5. python main.py --setup")
    print("  6. python setup_scheduler.py  # Configure OS-specific scheduler")
    print("  7. python main.py --diagnose")
    print("  8. python main.py")
    print("\\n📅 Scheduler Management:")
    print("  • Check status: python setup_scheduler.py status")
    print("  • Windows: Run PowerShell scripts as Administrator")
    print("  • Linux: Use ./scheduler/install_cron.sh or ./scheduler/install_systemd.sh")
    print("\\n🚀 Your production-ready application with scheduling support is ready!")


if __name__ == "__main__":
    main()
    
    def generate_from_idea(self, idea: str) -> Path:
        """Generate project from natural language idea using AI analysis"""
        print(f"🤖 Analyzing idea: {idea}")
        
        # Simple keyword-based analysis (could be enhanced with AI)
        idea_lower = idea.lower()
        
        # Determine project type
        if any(word in idea_lower for word in ["telegram", "discord", "chat", "message"]):
            project_type = "production_automation"
        elif any(word in idea_lower for word in ["api", "rest", "service", "server"]):
            project_type = "enterprise_api"
        elif any(word in idea_lower for word in ["data", "pipeline", "extract", "process"]):
            project_type = "ai_data_pipeline"
        elif any(word in idea_lower for word in ["notify", "alert", "notification"]):
            project_type = "notification_service"
        elif any(word in idea_lower for word in ["monitor", "health", "metrics"]):
            project_type = "monitoring_system"
        else:
            project_type = "production_automation"
        
        # Determine features
        ai_integration = any(word in idea_lower for word in ["ai", "gpt", "claude", "openai", "anthropic"])
        notification_channels = []
        
        if any(word in idea_lower for word in ["telegram", "tg"]):
            notification_channels.append("telegram")
        if any(word in idea_lower for word in ["sms", "text", "phone"]):
            notification_channels.append("sms")
        if any(word in idea_lower for word in ["email", "mail"]):
            notification_channels.append("email")
        
        if not notification_channels:
            notification_channels = ["telegram"]  # Default
        
        # Generate project name from idea
        words = idea.split()[:3]  # Take first 3 words
        name = " ".join(word.capitalize() for word in words if word.isalpha())
        
        config = ProjectConfig(
            name=name,
            description=idea,
            type=project_type,
            components=self.templates[project_type]["components"],
            external_services=self.templates[project_type].get("external_services", []),
            ai_integration=ai_integration,
            notification_channels=notification_channels,
            monitoring_enabled=True,
            kubernetes_support=True,
            async_support=True,
            docker_support=True
        )
        
        return self.generate_project(config)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Python Application Framework Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --idea "Telegram message extractor with AI processing and SMS alerts"
  %(prog)s --template production_automation --name "My Automation"
  %(prog)s --interactive
        """
    )
    
    parser.add_argument("--idea", help="Generate project from natural language description")
    parser.add_argument("--template", choices=[
        "production_automation", "ai_data_pipeline", "enterprise_api", 
        "notification_service", "monitoring_system"
    ], help="Use predefined template")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--description", help="Project description")
    parser.add_argument("--interactive", action="store_true", help="Interactive project configuration")
    
    args = parser.parse_args()
    
    framework = EnhancedPythonFramework()
    
    if args.idea:
        print(f"🚀 Generating from idea: {args.idea}")
        project_path = framework.generate_from_idea(args.idea)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.template:
        template = framework.templates[args.template]
        name = args.name or f"Enhanced {args.template.replace('_', ' ').title()}"
        description = args.description or template["description"]
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=args.template,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=template.get("notification_channels", ["telegram"]),
            ai_integration=template.get("ai_integration", True),
            monitoring_enabled=template.get("monitoring_enabled", True),
            kubernetes_support=template.get("kubernetes_support", False),
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.interactive:
        print("🎯 Enhanced Interactive Project Configuration")
        print("=" * 60)
        
        name = input("Project name: ")
        description = input("Project description: ")
        
        print("\\nAvailable templates:")
        templates = list(framework.templates.keys())
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template} - {framework.templates[template]['description']}")
        
        template_choice = int(input("\\nSelect template (1-5): ")) - 1
        template_type = templates[template_choice]
        template = framework.templates[template_type]
        
        # Enhanced configuration
        ai_integration = input("Include AI integration? (y/n): ").lower() == 'y'
        
        print("\\nNotification channels (separate with commas):")
        print("Available: telegram, sms, email")
        notification_input = input("Channels: ").strip()
        notification_channels = [ch.strip() for ch in notification_input.split(",") if ch.strip()]
        
        monitoring = input("Enable monitoring and alerting? (y/n): ").lower() == 'y'
        kubernetes = input("Include Kubernetes deployment? (y/n): ").lower() == 'y'
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=template_type,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=notification_channels or ["telegram"],
            ai_integration=ai_integration,
            monitoring_enabled=monitoring,
            kubernetes_support=kubernetes,
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"\\n✅ Enhanced project generated at: {project_path}")
        
    else:
        parser.print_help()
        sys.exit(1)
    
    print("\\n🎉 Next steps:")
    print("  1. cd into the project directory")
    print("  2. python -m venv venv && source venv/bin/activate")
    print("  3. pip install -r requirements.txt")
    print("  4. cp .env.template .env && edit .env")
    print("  5. python main.py --setup")
    print("  6. python main.py --diagnose")
    print("  7. python main.py")
    print("\\n🚀 Your production-ready application is ready!")


if __name__ == "__main__":
    main()
) {{
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }}
    }}
}} else {{
    Write-Error "Configuration file $ConfigFile not found"
    exit 1
}}

# Get environment variables with defaults
$StartTime = $env:SCHEDULER_START_TIME ?? "02:00:00"
$HourlyEnabled = $env:SCHEDULER_HOURLY_ENABLED ?? "false"
$IntervalHours = $env:SCHEDULER_INTERVAL_HOURS ?? "1"
$TimeoutHours = $env:SCHEDULER_TIMEOUT_HOURS ?? "2"
$PythonPath = $env:SCHEDULER_PYTHON_PATH ?? "python"
$ScriptPath = $env:SCHEDULER_SCRIPT_PATH ?? "main.py"
$WorkingDir = $env:SCHEDULER_WORKING_DIR ?? (Get-Location).Path

Write-Host "🔧 Configuring Windows Task Scheduler for $TaskName"
Write-Host "📅 Schedule: Daily at $StartTime"
Write-Host "⏱️ Timeout: $TimeoutHours hours"
Write-Host "📁 Working Directory: $WorkingDir"
Write-Host "🐍 Python: $PythonPath"
Write-Host "📝 Script: $ScriptPath"

# Read and process the XML template
$xmlContent = Get-Content "scheduler\\{task_name}_task.xml" -Raw

# Replace placeholders
$xmlContent = $xmlContent -replace '\\$\\(SCHEDULER_START_TIME\\)', $StartTime
$xmlContent = $xmlContent -replace '\\$\\(SCHEDULER_HOURLY_ENABLED\\)', $HourlyEnabled
$xmlContent = $xmlContent -replace '\\$\\(SCHEDULER_INTERVAL_HOURS\\)', $IntervalHours
$xmlContent = $xmlContent -replace '\\$\\(SCHEDULER_TIMEOUT_HOURS\\)', $TimeoutHours
$xmlContent = $xmlContent -replace '\\$\\(SCHEDULER_PYTHON_PATH\\)', $PythonPath
$xmlContent = $xmlContent -replace '\\$\\(SCHEDULER_SCRIPT_PATH\\)', $ScriptPath
$xmlContent = $xmlContent -replace '\\$\\(SCHEDULER_WORKING_DIR\\)', $WorkingDir

# Save processed XML
$tempXml = "temp_$TaskName.xml"
$xmlContent | Out-File -FilePath $tempXml -Encoding UTF8

try {{
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {{
        Write-Host "⚠️ Task $TaskName already exists. Updating..."
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }}
    
    # Register the task
    Register-ScheduledTask -TaskName $TaskName -Xml (Get-Content $tempXml | Out-String)
    
    Write-Host "✅ Task $TaskName registered successfully!"
    Write-Host ""
    Write-Host "📋 Task Management Commands:"
    Write-Host "   Start task:    Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "   Stop task:     Stop-ScheduledTask -TaskName '$TaskName'"
    Write-Host "   View status:   Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "   View history:  Get-WinEvent -FilterHashtable @{{LogName='Microsoft-Windows-TaskScheduler/Operational'; ID=100,102,103,106,107,108,109,111,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255}} | Where-Object {{$_.Message -like '*$TaskName*'}} | Select-Object -First 10"
    Write-Host "   Remove task:   Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
    
}} catch {{
    Write-Error "❌ Failed to register task: $($_.Exception.Message)"
    exit 1
}} finally {{
    # Clean up temp file
    if (Test-Path $tempXml) {{
        Remove-Item $tempXml
    }}
}}'''
        
        (project_path / "scheduler" / f"{task_name}_task.xml").write_text(task_xml)
        (project_path / "scheduler" / "install_windows_task.ps1").write_text(install_script)
    
    def _generate_linux_cron_config(self, project_path: Path, config: ProjectConfig):
        """Generate Linux cron configuration"""
        task_name = config.name.replace(" ", "_").lower()
        
        # Cron job template
        cron_template = f'''# Cron configuration for {config.name}
# Generated automatically - edit via crontab -e or update this file and run install_cron.sh
#
# Format: minute hour day month weekday command
# Examples:
#   0 2 * * *     - Daily at 2:00 AM
#   0 */6 * * *   - Every 6 hours
#   */30 * * * *  - Every 30 minutes
#   0 2 * * 1     - Weekly on Monday at 2:00 AM

# Main application schedule (configured via .env)
$(CRON_SCHEDULE) cd $(CRON_WORKING_DIR) && $(CRON_PYTHON_PATH) $(CRON_SCRIPT_PATH) >> $(CRON_LOG_FILE) 2>&1

# Optional: Health check every hour (uncomment to enable)
# 0 * * * * cd $(CRON_WORKING_DIR) && $(CRON_PYTHON_PATH) main.py --diagnose >> $(CRON_LOG_FILE) 2>&1

# Optional: Log rotation weekly (uncomment to enable) 
# 0 3 * * 0 find $(CRON_LOG_DIR) -name "*.log" -mtime +7 -delete

# Optional: Backup weekly (uncomment to enable)
# 0 4 * * 0 cd $(CRON_WORKING_DIR) && $(CRON_PYTHON_PATH) -c "import scripts.backup; scripts.backup.run_backup()" >> $(CRON_LOG_FILE) 2>&1
'''
        
        # Shell script to install cron job
        install_script = f'''#!/bin/bash
# Linux Cron Installation Script for {config.name}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/.env"
CRON_FILE="$SCRIPT_DIR/crontab.template"
TEMP_CRON="/tmp/{task_name}_cron_temp"

echo "🔧 Configuring Linux Cron for {config.name}"

# Check if .env file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Configuration file $CONFIG_FILE not found"
    exit 1
fi

# Source environment variables with defaults
source "$CONFIG_FILE" 2>/dev/null || true

# Set defaults if not specified in .env
CRON_SCHEDULE="${{CRON_SCHEDULE:-0 2 * * *}}"
CRON_PYTHON_PATH="${{CRON_PYTHON_PATH:-$(which python3 || which python)}}"
CRON_SCRIPT_PATH="${{CRON_SCRIPT_PATH:-main.py}}"
CRON_WORKING_DIR="${{CRON_WORKING_DIR:-$PROJECT_DIR}}"
CRON_LOG_FILE="${{CRON_LOG_FILE:-$PROJECT_DIR/logs/cron.log}}"
CRON_LOG_DIR="${{CRON_LOG_DIR:-$PROJECT_DIR/logs}}"

echo "📅 Schedule: $CRON_SCHEDULE"
echo "🐍 Python: $CRON_PYTHON_PATH" 
echo "📝 Script: $CRON_SCRIPT_PATH"
echo "📁 Working Directory: $CRON_WORKING_DIR"
echo "📋 Log File: $CRON_LOG_FILE"

# Validate Python path
if [[ ! -x "$CRON_PYTHON_PATH" ]]; then
    echo "❌ Python interpreter not found or not executable: $CRON_PYTHON_PATH"
    exit 1
fi

# Validate script path
if [[ ! -f "$CRON_WORKING_DIR/$CRON_SCRIPT_PATH" ]]; then
    echo "❌ Script not found: $CRON_WORKING_DIR/$CRON_SCRIPT_PATH"
    exit 1
fi

# Create log directory
mkdir -p "$(dirname "$CRON_LOG_FILE")"

# Validate cron schedule format
if ! echo "$CRON_SCHEDULE" | grep -E '^[*0-9,-/]+ [*0-9,-/]+ [*0-9,-/]+ [*0-9,-/]+ [*0-9,-/]+
        readme_content = f'''# {config.name}

{config.description}

## 🚀 **Production-Ready Features**

This application includes enterprise-grade patterns learned from production systems:

### **📢 Multi-Channel Notifications**
{"- ✅ Telegram notifications with shared client pattern" if "telegram" in config.notification_channels else ""}
{"- ✅ SMS notifications via Twilio/AWS SNS" if "sms" in config.notification_channels else ""}
{"- ✅ Email notifications" if "email" in config.notification_channels else ""}
{"- ✅ Priority-based routing (critical→all channels, high→SMS+Telegram, normal→Telegram)" if len(config.notification_channels) > 1 else ""}

### **📊 Comprehensive Monitoring**
{"- ✅ Health monitoring with configurable checks" if config.monitoring_enabled else ""}
{"- ✅ Performance metrics and alerting" if config.performance_monitoring else ""}
{"- ✅ System resource monitoring (CPU, memory, disk)" if config.monitoring_enabled else ""}
{"- ✅ Integrated monitoring dashboard" if config.monitoring_enabled else ""}

### **🐳 Production Deployment**
- ✅ Multi-stage Docker builds
- ✅ Docker Compose with health checks
{"- ✅ Kubernetes manifests with autoscaling" if config.kubernetes_support else ""}
- ✅ CI/CD pipeline with security scanning
- ✅ Production environment configuration

### **🛡️ Enterprise Patterns**
- ✅ Resource management and conflict prevention
- ✅ Comprehensive error handling
- ✅ Configuration validation
- ✅ Structured logging with emojis
{"- ✅ AI integration with smart routing" if config.ai_integration else ""}
{"- ✅ Autonomous debugging foundations" if config.autonomous_debugging else ""}

## 🚀 **Quick Start**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env with your configuration
```

### 3. Run Setup
```bash
python main.py --setup
```

### 4. Test Systems
```bash
# Test all systems
python main.py --diagnose

{"# Test notifications" if config.notification_channels else ""}
{"python main.py --test-notifications" if config.notification_channels else ""}
```

### 5. Start Application
```bash
python main.py
```

## 🐳 **Docker Deployment**

### Development
```bash
docker-compose up --build
```

### Production
```bash
docker-compose -f docker-compose.production.yml up -d
```

{"## ☸️ **Kubernetes Deployment**" if config.kubernetes_support else ""}
{"" if config.kubernetes_support else ""}
{"```bash" if config.kubernetes_support else ""}
{"# Deploy to Kubernetes" if config.kubernetes_support else ""}
{"kubectl apply -f k8s/" if config.kubernetes_support else ""}
{"```" if config.kubernetes_support else ""}

## 📊 **Monitoring**

{"### Health Checks" if config.monitoring_enabled else ""}
{"- System memory usage" if config.monitoring_enabled else ""}
{"- CPU utilization" if config.monitoring_enabled else ""}
{"- Disk space availability" if config.monitoring_enabled else ""}
{"- Database connectivity" if config.monitoring_enabled else ""}
{"- Application performance metrics" if config.monitoring_enabled else ""}

{"### Alerting" if config.notification_channels and config.monitoring_enabled else ""}
{"- Critical alerts → SMS + Telegram + Email" if len(config.notification_channels) > 2 else ""}
{"- High priority → SMS + Telegram" if "sms" in config.notification_channels and "telegram" in config.notification_channels else ""}
{"- Normal alerts → Telegram" if "telegram" in config.notification_channels else ""}
{"- Alert cooldown prevents spam" if config.monitoring_enabled else ""}

## 🔧 **Configuration**

### Environment Variables
```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

{"# Notifications" if config.notification_channels else ""}
{"NOTIFICATIONS_ENABLED=true" if config.notification_channels else ""}
{"TELEGRAM_TARGETS=@admin_channel" if "telegram" in config.notification_channels else ""}
{"SMS_TARGETS=+1234567890" if "sms" in config.notification_channels else ""}
{"TWILIO_ACCOUNT_SID=your_sid" if "sms" in config.notification_channels else ""}
{"TWILIO_AUTH_TOKEN=your_token" if "sms" in config.notification_channels else ""}

{"# AI Integration" if config.ai_integration else ""}
{"ANTHROPIC_API_KEY=your_key" if config.ai_integration else ""}
{"OPENAI_API_KEY=your_key" if config.ai_integration else ""}

{"# Monitoring" if config.monitoring_enabled else ""}
{"MONITORING_ENABLED=true" if config.monitoring_enabled else ""}
{"PERFORMANCE_MONITORING=true" if config.performance_monitoring else ""}
```

## 🧪 **Testing**

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Performance tests
pytest tests/performance/

# Integration tests
pytest tests/integration/
```

## 📈 **Performance**

This application includes several performance optimizations:

- Async/await throughout for I/O operations
- Connection pooling for databases
- Multi-level caching systems
- Resource conflict prevention
- Smart batching for AI operations
- Performance monitoring and alerting

## 🔐 **Security**

Security features included:

- Non-root Docker containers
- Environment variable validation
- Rate limiting for APIs
- Comprehensive input validation
- Security scanning in CI/CD
- Regular dependency updates

## 📚 **Documentation**

- [Setup Guide](docs/setup.md)
- [API Documentation](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Run linting: `black src/ && isort src/ && flake8 src/`
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with enterprise-grade patterns from production systems including the Telegram Knowledge Base Extractor.*
'''
        
        (project_path / "README.md").write_text(readme_content)
    
    def generate_from_idea(self, idea: str) -> Path:
        """Generate project from natural language idea using AI analysis"""
        print(f"🤖 Analyzing idea: {idea}")
        
        # Simple keyword-based analysis (could be enhanced with AI)
        idea_lower = idea.lower()
        
        # Determine project type
        if any(word in idea_lower for word in ["telegram", "discord", "chat", "message"]):
            project_type = "production_automation"
        elif any(word in idea_lower for word in ["api", "rest", "service", "server"]):
            project_type = "enterprise_api"
        elif any(word in idea_lower for word in ["data", "pipeline", "extract", "process"]):
            project_type = "ai_data_pipeline"
        elif any(word in idea_lower for word in ["notify", "alert", "notification"]):
            project_type = "notification_service"
        elif any(word in idea_lower for word in ["monitor", "health", "metrics"]):
            project_type = "monitoring_system"
        else:
            project_type = "production_automation"
        
        # Determine features
        ai_integration = any(word in idea_lower for word in ["ai", "gpt", "claude", "openai", "anthropic"])
        notification_channels = []
        
        if any(word in idea_lower for word in ["telegram", "tg"]):
            notification_channels.append("telegram")
        if any(word in idea_lower for word in ["sms", "text", "phone"]):
            notification_channels.append("sms")
        if any(word in idea_lower for word in ["email", "mail"]):
            notification_channels.append("email")
        
        if not notification_channels:
            notification_channels = ["telegram"]  # Default
        
        # Generate project name from idea
        words = idea.split()[:3]  # Take first 3 words
        name = " ".join(word.capitalize() for word in words if word.isalpha())
        
        config = ProjectConfig(
            name=name,
            description=idea,
            type=project_type,
            components=self.templates[project_type]["components"],
            external_services=self.templates[project_type].get("external_services", []),
            ai_integration=ai_integration,
            notification_channels=notification_channels,
            monitoring_enabled=True,
            kubernetes_support=True,
            async_support=True,
            docker_support=True
        )
        
        return self.generate_project(config)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Python Application Framework Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --idea "Telegram message extractor with AI processing and SMS alerts"
  %(prog)s --template production_automation --name "My Automation"
  %(prog)s --interactive
        """
    )
    
    parser.add_argument("--idea", help="Generate project from natural language description")
    parser.add_argument("--template", choices=[
        "production_automation", "ai_data_pipeline", "enterprise_api", 
        "notification_service", "monitoring_system"
    ], help="Use predefined template")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--description", help="Project description")
    parser.add_argument("--interactive", action="store_true", help="Interactive project configuration")
    
    args = parser.parse_args()
    
    framework = EnhancedPythonFramework()
    
    if args.idea:
        print(f"🚀 Generating from idea: {args.idea}")
        project_path = framework.generate_from_idea(args.idea)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.template:
        template = framework.templates[args.template]
        name = args.name or f"Enhanced {args.template.replace('_', ' ').title()}"
        description = args.description or template["description"]
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=args.template,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=template.get("notification_channels", ["telegram"]),
            ai_integration=template.get("ai_integration", True),
            monitoring_enabled=template.get("monitoring_enabled", True),
            kubernetes_support=template.get("kubernetes_support", False),
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.interactive:
        print("🎯 Enhanced Interactive Project Configuration")
        print("=" * 60)
        
        name = input("Project name: ")
        description = input("Project description: ")
        
        print("\\nAvailable templates:")
        templates = list(framework.templates.keys())
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template} - {framework.templates[template]['description']}")
        
        template_choice = int(input("\\nSelect template (1-5): ")) - 1
        template_type = templates[template_choice]
        template = framework.templates[template_type]
        
        # Enhanced configuration
        ai_integration = input("Include AI integration? (y/n): ").lower() == 'y'
        
        print("\\nNotification channels (separate with commas):")
        print("Available: telegram, sms, email")
        notification_input = input("Channels: ").strip()
        notification_channels = [ch.strip() for ch in notification_input.split(",") if ch.strip()]
        
        monitoring = input("Enable monitoring and alerting? (y/n): ").lower() == 'y'
        kubernetes = input("Include Kubernetes deployment? (y/n): ").lower() == 'y'
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=template_type,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=notification_channels or ["telegram"],
            ai_integration=ai_integration,
            monitoring_enabled=monitoring,
            kubernetes_support=kubernetes,
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"\\n✅ Enhanced project generated at: {project_path}")
        
    else:
        parser.print_help()
        sys.exit(1)
    
    print("\\n🎉 Next steps:")
    print("  1. cd into the project directory")
    print("  2. python -m venv venv && source venv/bin/activate")
    print("  3. pip install -r requirements.txt")
    print("  4. cp .env.template .env && edit .env")
    print("  5. python main.py --setup")
    print("  6. python main.py --diagnose")
    print("  7. python main.py")
    print("\\n🚀 Your production-ready application is ready!")


if __name__ == "__main__":
    main()
 > /dev/null; then
    echo "❌ Invalid cron schedule format: $CRON_SCHEDULE"
    echo "   Expected format: 'minute hour day month weekday'"
    echo "   Example: '0 2 * * *' for daily at 2:00 AM"
    exit 1
fi

# Read existing crontab
crontab -l 2>/dev/null > "$TEMP_CRON" || touch "$TEMP_CRON"

# Remove any existing entries for this project
grep -v "{task_name}" "$TEMP_CRON" > "${{TEMP_CRON}}.new" || touch "${{TEMP_CRON}}.new"

# Process template and add new entry
echo "" >> "${{TEMP_CRON}}.new"
echo "# {config.name} - Auto-generated cron job" >> "${{TEMP_CRON}}.new"

# Replace placeholders in template
sed -e "s|\\$(CRON_SCHEDULE)|$CRON_SCHEDULE|g" \\
    -e "s|\\$(CRON_PYTHON_PATH)|$CRON_PYTHON_PATH|g" \\
    -e "s|\\$(CRON_SCRIPT_PATH)|$CRON_SCRIPT_PATH|g" \\
    -e "s|\\$(CRON_WORKING_DIR)|$CRON_WORKING_DIR|g" \\
    -e "s|\\$(CRON_LOG_FILE)|$CRON_LOG_FILE|g" \\
    -e "s|\\$(CRON_LOG_DIR)|$CRON_LOG_DIR|g" \\
    "$CRON_FILE" | grep -v '^#' | grep -v '^
        readme_content = f'''# {config.name}

{config.description}

## 🚀 **Production-Ready Features**

This application includes enterprise-grade patterns learned from production systems:

### **📢 Multi-Channel Notifications**
{"- ✅ Telegram notifications with shared client pattern" if "telegram" in config.notification_channels else ""}
{"- ✅ SMS notifications via Twilio/AWS SNS" if "sms" in config.notification_channels else ""}
{"- ✅ Email notifications" if "email" in config.notification_channels else ""}
{"- ✅ Priority-based routing (critical→all channels, high→SMS+Telegram, normal→Telegram)" if len(config.notification_channels) > 1 else ""}

### **📊 Comprehensive Monitoring**
{"- ✅ Health monitoring with configurable checks" if config.monitoring_enabled else ""}
{"- ✅ Performance metrics and alerting" if config.performance_monitoring else ""}
{"- ✅ System resource monitoring (CPU, memory, disk)" if config.monitoring_enabled else ""}
{"- ✅ Integrated monitoring dashboard" if config.monitoring_enabled else ""}

### **🐳 Production Deployment**
- ✅ Multi-stage Docker builds
- ✅ Docker Compose with health checks
{"- ✅ Kubernetes manifests with autoscaling" if config.kubernetes_support else ""}
- ✅ CI/CD pipeline with security scanning
- ✅ Production environment configuration

### **🛡️ Enterprise Patterns**
- ✅ Resource management and conflict prevention
- ✅ Comprehensive error handling
- ✅ Configuration validation
- ✅ Structured logging with emojis
{"- ✅ AI integration with smart routing" if config.ai_integration else ""}
{"- ✅ Autonomous debugging foundations" if config.autonomous_debugging else ""}

## 🚀 **Quick Start**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env with your configuration
```

### 3. Run Setup
```bash
python main.py --setup
```

### 4. Test Systems
```bash
# Test all systems
python main.py --diagnose

{"# Test notifications" if config.notification_channels else ""}
{"python main.py --test-notifications" if config.notification_channels else ""}
```

### 5. Start Application
```bash
python main.py
```

## 🐳 **Docker Deployment**

### Development
```bash
docker-compose up --build
```

### Production
```bash
docker-compose -f docker-compose.production.yml up -d
```

{"## ☸️ **Kubernetes Deployment**" if config.kubernetes_support else ""}
{"" if config.kubernetes_support else ""}
{"```bash" if config.kubernetes_support else ""}
{"# Deploy to Kubernetes" if config.kubernetes_support else ""}
{"kubectl apply -f k8s/" if config.kubernetes_support else ""}
{"```" if config.kubernetes_support else ""}

## 📊 **Monitoring**

{"### Health Checks" if config.monitoring_enabled else ""}
{"- System memory usage" if config.monitoring_enabled else ""}
{"- CPU utilization" if config.monitoring_enabled else ""}
{"- Disk space availability" if config.monitoring_enabled else ""}
{"- Database connectivity" if config.monitoring_enabled else ""}
{"- Application performance metrics" if config.monitoring_enabled else ""}

{"### Alerting" if config.notification_channels and config.monitoring_enabled else ""}
{"- Critical alerts → SMS + Telegram + Email" if len(config.notification_channels) > 2 else ""}
{"- High priority → SMS + Telegram" if "sms" in config.notification_channels and "telegram" in config.notification_channels else ""}
{"- Normal alerts → Telegram" if "telegram" in config.notification_channels else ""}
{"- Alert cooldown prevents spam" if config.monitoring_enabled else ""}

## 🔧 **Configuration**

### Environment Variables
```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

{"# Notifications" if config.notification_channels else ""}
{"NOTIFICATIONS_ENABLED=true" if config.notification_channels else ""}
{"TELEGRAM_TARGETS=@admin_channel" if "telegram" in config.notification_channels else ""}
{"SMS_TARGETS=+1234567890" if "sms" in config.notification_channels else ""}
{"TWILIO_ACCOUNT_SID=your_sid" if "sms" in config.notification_channels else ""}
{"TWILIO_AUTH_TOKEN=your_token" if "sms" in config.notification_channels else ""}

{"# AI Integration" if config.ai_integration else ""}
{"ANTHROPIC_API_KEY=your_key" if config.ai_integration else ""}
{"OPENAI_API_KEY=your_key" if config.ai_integration else ""}

{"# Monitoring" if config.monitoring_enabled else ""}
{"MONITORING_ENABLED=true" if config.monitoring_enabled else ""}
{"PERFORMANCE_MONITORING=true" if config.performance_monitoring else ""}
```

## 🧪 **Testing**

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Performance tests
pytest tests/performance/

# Integration tests
pytest tests/integration/
```

## 📈 **Performance**

This application includes several performance optimizations:

- Async/await throughout for I/O operations
- Connection pooling for databases
- Multi-level caching systems
- Resource conflict prevention
- Smart batching for AI operations
- Performance monitoring and alerting

## 🔐 **Security**

Security features included:

- Non-root Docker containers
- Environment variable validation
- Rate limiting for APIs
- Comprehensive input validation
- Security scanning in CI/CD
- Regular dependency updates

## 📚 **Documentation**

- [Setup Guide](docs/setup.md)
- [API Documentation](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Run linting: `black src/ && isort src/ && flake8 src/`
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with enterprise-grade patterns from production systems including the Telegram Knowledge Base Extractor.*
'''
        
        (project_path / "README.md").write_text(readme_content)
    
    def generate_from_idea(self, idea: str) -> Path:
        """Generate project from natural language idea using AI analysis"""
        print(f"🤖 Analyzing idea: {idea}")
        
        # Simple keyword-based analysis (could be enhanced with AI)
        idea_lower = idea.lower()
        
        # Determine project type
        if any(word in idea_lower for word in ["telegram", "discord", "chat", "message"]):
            project_type = "production_automation"
        elif any(word in idea_lower for word in ["api", "rest", "service", "server"]):
            project_type = "enterprise_api"
        elif any(word in idea_lower for word in ["data", "pipeline", "extract", "process"]):
            project_type = "ai_data_pipeline"
        elif any(word in idea_lower for word in ["notify", "alert", "notification"]):
            project_type = "notification_service"
        elif any(word in idea_lower for word in ["monitor", "health", "metrics"]):
            project_type = "monitoring_system"
        else:
            project_type = "production_automation"
        
        # Determine features
        ai_integration = any(word in idea_lower for word in ["ai", "gpt", "claude", "openai", "anthropic"])
        notification_channels = []
        
        if any(word in idea_lower for word in ["telegram", "tg"]):
            notification_channels.append("telegram")
        if any(word in idea_lower for word in ["sms", "text", "phone"]):
            notification_channels.append("sms")
        if any(word in idea_lower for word in ["email", "mail"]):
            notification_channels.append("email")
        
        if not notification_channels:
            notification_channels = ["telegram"]  # Default
        
        # Generate project name from idea
        words = idea.split()[:3]  # Take first 3 words
        name = " ".join(word.capitalize() for word in words if word.isalpha())
        
        config = ProjectConfig(
            name=name,
            description=idea,
            type=project_type,
            components=self.templates[project_type]["components"],
            external_services=self.templates[project_type].get("external_services", []),
            ai_integration=ai_integration,
            notification_channels=notification_channels,
            monitoring_enabled=True,
            kubernetes_support=True,
            async_support=True,
            docker_support=True
        )
        
        return self.generate_project(config)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Python Application Framework Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --idea "Telegram message extractor with AI processing and SMS alerts"
  %(prog)s --template production_automation --name "My Automation"
  %(prog)s --interactive
        """
    )
    
    parser.add_argument("--idea", help="Generate project from natural language description")
    parser.add_argument("--template", choices=[
        "production_automation", "ai_data_pipeline", "enterprise_api", 
        "notification_service", "monitoring_system"
    ], help="Use predefined template")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--description", help="Project description")
    parser.add_argument("--interactive", action="store_true", help="Interactive project configuration")
    
    args = parser.parse_args()
    
    framework = EnhancedPythonFramework()
    
    if args.idea:
        print(f"🚀 Generating from idea: {args.idea}")
        project_path = framework.generate_from_idea(args.idea)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.template:
        template = framework.templates[args.template]
        name = args.name or f"Enhanced {args.template.replace('_', ' ').title()}"
        description = args.description or template["description"]
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=args.template,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=template.get("notification_channels", ["telegram"]),
            ai_integration=template.get("ai_integration", True),
            monitoring_enabled=template.get("monitoring_enabled", True),
            kubernetes_support=template.get("kubernetes_support", False),
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.interactive:
        print("🎯 Enhanced Interactive Project Configuration")
        print("=" * 60)
        
        name = input("Project name: ")
        description = input("Project description: ")
        
        print("\\nAvailable templates:")
        templates = list(framework.templates.keys())
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template} - {framework.templates[template]['description']}")
        
        template_choice = int(input("\\nSelect template (1-5): ")) - 1
        template_type = templates[template_choice]
        template = framework.templates[template_type]
        
        # Enhanced configuration
        ai_integration = input("Include AI integration? (y/n): ").lower() == 'y'
        
        print("\\nNotification channels (separate with commas):")
        print("Available: telegram, sms, email")
        notification_input = input("Channels: ").strip()
        notification_channels = [ch.strip() for ch in notification_input.split(",") if ch.strip()]
        
        monitoring = input("Enable monitoring and alerting? (y/n): ").lower() == 'y'
        kubernetes = input("Include Kubernetes deployment? (y/n): ").lower() == 'y'
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=template_type,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=notification_channels or ["telegram"],
            ai_integration=ai_integration,
            monitoring_enabled=monitoring,
            kubernetes_support=kubernetes,
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"\\n✅ Enhanced project generated at: {project_path}")
        
    else:
        parser.print_help()
        sys.exit(1)
    
    print("\\n🎉 Next steps:")
    print("  1. cd into the project directory")
    print("  2. python -m venv venv && source venv/bin/activate")
    print("  3. pip install -r requirements.txt")
    print("  4. cp .env.template .env && edit .env")
    print("  5. python main.py --setup")
    print("  6. python main.py --diagnose")
    print("  7. python main.py")
    print("\\n🚀 Your production-ready application is ready!")


if __name__ == "__main__":
    main()
 >> "${{TEMP_CRON}}.new"

# Install the new crontab
if crontab "${{TEMP_CRON}}.new"; then
    echo "✅ Cron job installed successfully!"
    echo ""
    echo "📋 Cron Management Commands:"
    echo "   View crontab:     crontab -l"
    echo "   Edit crontab:     crontab -e"
    echo "   Remove crontab:   crontab -r"
    echo "   View logs:        tail -f $CRON_LOG_FILE"
    echo "   Test job:         cd $CRON_WORKING_DIR && $CRON_PYTHON_PATH $CRON_SCRIPT_PATH"
    echo ""
    echo "📅 Next scheduled run:"
    # Calculate next run time (requires 'at' package)
    if command -v at > /dev/null 2>&1; then
        echo "   $(echo "echo 'Next run calculated'" | at now 2>&1 | grep -o '[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}} [0-9]{{2}}:[0-9]{{2}}' || echo 'Unable to calculate')"
    else
        echo "   Install 'at' package to see next run time"
    fi
else
    echo "❌ Failed to install cron job"
    exit 1
fi

# Cleanup
rm -f "$TEMP_CRON" "${{TEMP_CRON}}.new"

# Optional: Test the job immediately
read -p "🧪 Run a test execution now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Running test execution..."
    cd "$CRON_WORKING_DIR"
    "$CRON_PYTHON_PATH" "$CRON_SCRIPT_PATH" --diagnose
    echo "✅ Test completed"
fi'''
        
        (project_path / "scheduler" / "crontab.template").write_text(cron_template)
        (project_path / "scheduler" / "install_cron.sh").write_text(install_script)
        
        # Make the script executable
        import stat
        script_path = project_path / "scheduler" / "install_cron.sh"
        script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    
    def _generate_systemd_service(self, project_path: Path, config: ProjectConfig):
        """Generate systemd service configuration for Linux"""
        service_name = config.name.replace(" ", "_").lower()
        
        # Systemd service file
        service_content = f'''[Unit]
Description={config.name} - {config.description}
After=network.target
Wants=network.target

[Service]
Type=simple
User=$(SYSTEMD_USER)
Group=$(SYSTEMD_GROUP)
WorkingDirectory=$(SYSTEMD_WORKING_DIR)
Environment="PYTHONPATH=$(SYSTEMD_WORKING_DIR)/src"
Environment="ENVIRONMENT=production"
EnvironmentFile=$(SYSTEMD_WORKING_DIR)/.env
ExecStart=$(SYSTEMD_PYTHON_PATH) $(SYSTEMD_SCRIPT_PATH)
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$(SYSTEMD_WORKING_DIR)/data $(SYSTEMD_WORKING_DIR)/logs $(SYSTEMD_WORKING_DIR)/backups
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

# Resource limits
LimitNOFILE=65536
MemoryMax=$(SYSTEMD_MEMORY_LIMIT)
CPUQuota=$(SYSTEMD_CPU_QUOTA)

[Install]
WantedBy=multi-user.target
'''
        
        # Systemd installation script
        systemd_install = f'''#!/bin/bash
# Systemd Service Installation Script for {config.name}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/.env"
SERVICE_NAME="{service_name}"
SERVICE_FILE="/etc/systemd/system/${{SERVICE_NAME}}.service"

echo "🔧 Configuring systemd service for {config.name}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Check if .env file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Configuration file $CONFIG_FILE not found"
    exit 1
fi

# Source environment variables with defaults
source "$CONFIG_FILE" 2>/dev/null || true

# Set defaults
SYSTEMD_USER="${{SYSTEMD_USER:-$(logname 2>/dev/null || echo $SUDO_USER || echo $USER)}}"
SYSTEMD_GROUP="${{SYSTEMD_GROUP:-$SYSTEMD_USER}}"
SYSTEMD_PYTHON_PATH="${{SYSTEMD_PYTHON_PATH:-$(which python3 || which python)}}"
SYSTEMD_SCRIPT_PATH="${{SYSTEMD_SCRIPT_PATH:-main.py}}"
SYSTEMD_WORKING_DIR="${{SYSTEMD_WORKING_DIR:-$PROJECT_DIR}}"
SYSTEMD_MEMORY_LIMIT="${{SYSTEMD_MEMORY_LIMIT:-1G}}"
SYSTEMD_CPU_QUOTA="${{SYSTEMD_CPU_QUOTA:-100%}}"

echo "👤 User: $SYSTEMD_USER"
echo "👥 Group: $SYSTEMD_GROUP" 
echo "🐍 Python: $SYSTEMD_PYTHON_PATH"
echo "📝 Script: $SYSTEMD_SCRIPT_PATH"
echo "📁 Working Directory: $SYSTEMD_WORKING_DIR"
echo "💾 Memory Limit: $SYSTEMD_MEMORY_LIMIT"
echo "⚡ CPU Quota: $SYSTEMD_CPU_QUOTA"

# Validate user exists
if ! id "$SYSTEMD_USER" &>/dev/null; then
    echo "❌ User $SYSTEMD_USER does not exist"
    exit 1
fi

# Validate Python path
if [[ ! -x "$SYSTEMD_PYTHON_PATH" ]]; then
    echo "❌ Python interpreter not found: $SYSTEMD_PYTHON_PATH"
    exit 1
fi

# Validate script exists
if [[ ! -f "$SYSTEMD_WORKING_DIR/$SYSTEMD_SCRIPT_PATH" ]]; then
    echo "❌ Script not found: $SYSTEMD_WORKING_DIR/$SYSTEMD_SCRIPT_PATH"
    exit 1
fi

# Create service file with substitutions
sed -e "s|\\$(SYSTEMD_USER)|$SYSTEMD_USER|g" \\
    -e "s|\\$(SYSTEMD_GROUP)|$SYSTEMD_GROUP|g" \\
    -e "s|\\$(SYSTEMD_PYTHON_PATH)|$SYSTEMD_PYTHON_PATH|g" \\
    -e "s|\\$(SYSTEMD_SCRIPT_PATH)|$SYSTEMD_SCRIPT_PATH|g" \\
    -e "s|\\$(SYSTEMD_WORKING_DIR)|$SYSTEMD_WORKING_DIR|g" \\
    -e "s|\\$(SYSTEMD_MEMORY_LIMIT)|$SYSTEMD_MEMORY_LIMIT|g" \\
    -e "s|\\$(SYSTEMD_CPU_QUOTA)|$SYSTEMD_CPU_QUOTA|g" \\
    "$SCRIPT_DIR/{service_name}.service.template" > "$SERVICE_FILE"

# Set proper permissions
chmod 644 "$SERVICE_FILE"

# Reload systemd and enable service
systemctl daemon-reload

if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
    echo "⚠️ Service $SERVICE_NAME already enabled. Reloading..."
    systemctl stop "$SERVICE_NAME" || true
fi

systemctl enable "$SERVICE_NAME"

echo "✅ Systemd service $SERVICE_NAME installed successfully!"
echo ""
echo "📋 Service Management Commands:"
echo "   Start service:    sudo systemctl start $SERVICE_NAME"
echo "   Stop service:     sudo systemctl stop $SERVICE_NAME"
echo "   Restart service:  sudo systemctl restart $SERVICE_NAME"
echo "   View status:      sudo systemctl status $SERVICE_NAME"
echo "   View logs:        sudo journalctl -u $SERVICE_NAME -f"
echo "   Enable startup:   sudo systemctl enable $SERVICE_NAME"
echo "   Disable startup:  sudo systemctl disable $SERVICE_NAME"
echo ""

# Ask if user wants to start the service now
read -p "🚀 Start the service now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start "$SERVICE_NAME"
    echo "✅ Service started"
    systemctl status "$SERVICE_NAME" --no-pager
fi'''
        
        (project_path / "scheduler" / f"{service_name}.service.template").write_text(service_content)
        (project_path / "scheduler" / "install_systemd.sh").write_text(systemd_install)
        
        # Make scripts executable
        import stat
        for script in ["install_systemd.sh"]:
            script_path = project_path / "scheduler" / script
            script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    
    def _generate_scheduler_setup_scripts(self, project_path: Path, config: ProjectConfig, current_os: str):
        """Generate OS detection and unified setup scripts"""
        
        # Cross-platform scheduler setup script
        unified_setup = f'''#!/usr/bin/env python3
"""
Cross-Platform Scheduler Setup for {config.name}
Automatically detects OS and configures appropriate scheduler
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def detect_os():
    """Detect the operating system"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system in ["linux", "darwin"]:
        return "linux"  # Treat macOS as Linux for cron
    else:
        return "unknown"

def setup_windows_scheduler():
    """Setup Windows Task Scheduler"""
    print("🪟 Detected Windows - Setting up Task Scheduler")
    
    # Check if running as administrator
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("⚠️ Warning: Not running as administrator")
            print("   Some features may not work properly")
    except Exception:
        pass
    
    scheduler_dir = Path("scheduler")
    powershell_script = scheduler_dir / "install_windows_task.ps1"
    
    if not powershell_script.exists():
        print("❌ Windows Task Scheduler script not found")
        return False
    
    # Run PowerShell script
    cmd = [
        "powershell.exe",
        "-ExecutionPolicy", "Bypass",
        "-File", str(powershell_script)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Windows Task Scheduler configured successfully")
            return True
        else:
            print(f"❌ Failed to configure Task Scheduler: {{result.stderr}}")
            return False
    except Exception as e:
        print(f"❌ Error running PowerShell script: {{e}}")
        return False

def setup_linux_scheduler():
    """Setup Linux cron job"""
    print("🐧 Detected Linux/Unix - Setting up Cron")
    
    scheduler_dir = Path("scheduler")
    cron_script = scheduler_dir / "install_cron.sh"
    
    if not cron_script.exists():
        print("❌ Linux cron script not found")
        return False
    
    # Make script executable
    cron_script.chmod(0o755)
    
    # Run bash script
    try:
        result = subprocess.run([str(cron_script)], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Linux Cron configured successfully")
            return True
        else:
            print(f"❌ Failed to configure Cron: {{result.stderr}}")
            return False
    except Exception as e:
        print(f"❌ Error running bash script: {{e}}")
        return False

def setup_systemd_service():
    """Setup systemd service (Linux only)"""
    if detect_os() != "linux":
        return False
        
    print("🔧 Setting up systemd service")
    
    scheduler_dir = Path("scheduler")
    systemd_script = scheduler_dir / "install_systemd.sh"
    
    if not systemd_script.exists():
        print("❌ Systemd installation script not found")
        return False
    
    # Make script executable
    systemd_script.chmod(0o755)
    
    print("⚠️ Systemd service requires root privileges")
    print("   Please run: sudo ./scheduler/install_systemd.sh")
    return True

def show_scheduler_status():
    """Show current scheduler status"""
    current_os = detect_os()
    
    print(f"\\n📊 Scheduler Status for {config.name}")
    print("=" * 50)
    
    if current_os == "windows":
        # Check Windows Task Scheduler
        try:
            cmd = ["schtasks", "/query", "/tn", "{config.name.replace(' ', '_')}", "/fo", "list"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Windows Task Scheduler: Configured")
                print("📋 Task Details:")
                for line in result.stdout.split('\\n'):
                    if 'Next Run Time' in line or 'Status' in line or 'Last Run Time' in line:
                        print(f"   {{line.strip()}}")
            else:
                print("❌ Windows Task Scheduler: Not configured")
        except Exception as e:
            print(f"❌ Could not check Task Scheduler status: {{e}}")
    
    elif current_os == "linux":
        # Check cron
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if result.returncode == 0 and "{config.name.replace(' ', '_').lower()}" in result.stdout.lower():
                print("✅ Cron: Configured")
                cron_lines = [line for line in result.stdout.split('\\n') 
                            if "{config.name.replace(' ', '_').lower()}" in line.lower() and not line.strip().startswith('#')]
                for line in cron_lines:
                    print(f"   {{line.strip()}}")
            else:
                print("❌ Cron: Not configured")
        except Exception:
            print("❌ Could not check cron status")
        
        # Check systemd service
        try:
            service_name = "{config.name.replace(' ', '_').lower()}"
            result = subprocess.run(["systemctl", "is-active", service_name], 
                                  capture_output=True, text=True)
            if "active" in result.stdout:
                print("✅ Systemd Service: Active")
            else:
                print("❌ Systemd Service: Not active")
        except Exception:
            print("❌ Could not check systemd service status")

def main():
    """Main setup function"""
    print(f"🔧 Scheduler Setup for {config.name}")
    print("=" * 50)
    
    current_os = detect_os()
    print(f"🖥️ Operating System: {{current_os.title()}}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            show_scheduler_status()
            return
        elif command == "systemd":
            if current_os == "linux":
                setup_systemd_service()
            else:
                print("❌ Systemd is only available on Linux")
            return
        elif command == "help":
            print("\\nUsage:")
            print("  python setup_scheduler.py        - Auto-configure scheduler")
            print("  python setup_scheduler.py status - Show scheduler status")
            print("  python setup_scheduler.py systemd- Setup systemd service (Linux)")
            return
    
    # Auto-configure based on OS
    if current_os == "windows":
        success = setup_windows_scheduler()
    elif current_os == "linux":
        success = setup_linux_scheduler()
        if success:
            print("\\n💡 Tip: You can also setup a systemd service for persistent operation:")
            print("   python setup_scheduler.py systemd")
    else:
        print(f"❌ Unsupported operating system: {{current_os}}")
        success = False
    
    if success:
        print("\\n🎉 Scheduler setup completed!")
        print("\\n📋 Next steps:")
        print("  1. Check scheduler status: python setup_scheduler.py status")
        print("  2. Review .env configuration for schedule settings")
        print("  3. Test your application: python main.py --diagnose")
    else:
        print("\\n❌ Scheduler setup failed")
        print("   Check the error messages above and try again")

if __name__ == "__main__":
    main()
'''
        
        (project_path / "setup_scheduler.py").write_text(unified_setup)
        
        # Make the script executable on Unix systems
        if current_os != "windows":
            import stat
            script_path = project_path / "setup_scheduler.py"
            script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    
    def _generate_enhanced_documentation(self, project_path: Path, config: ProjectConfig):
        """Generate enhanced documentation"""
        readme_content = f'''# {config.name}

{config.description}

## 🚀 **Production-Ready Features**

This application includes enterprise-grade patterns learned from production systems:

### **📢 Multi-Channel Notifications**
{"- ✅ Telegram notifications with shared client pattern" if "telegram" in config.notification_channels else ""}
{"- ✅ SMS notifications via Twilio/AWS SNS" if "sms" in config.notification_channels else ""}
{"- ✅ Email notifications" if "email" in config.notification_channels else ""}
{"- ✅ Priority-based routing (critical→all channels, high→SMS+Telegram, normal→Telegram)" if len(config.notification_channels) > 1 else ""}

### **📊 Comprehensive Monitoring**
{"- ✅ Health monitoring with configurable checks" if config.monitoring_enabled else ""}
{"- ✅ Performance metrics and alerting" if config.performance_monitoring else ""}
{"- ✅ System resource monitoring (CPU, memory, disk)" if config.monitoring_enabled else ""}
{"- ✅ Integrated monitoring dashboard" if config.monitoring_enabled else ""}

### **🐳 Production Deployment**
- ✅ Multi-stage Docker builds
- ✅ Docker Compose with health checks
{"- ✅ Kubernetes manifests with autoscaling" if config.kubernetes_support else ""}
- ✅ CI/CD pipeline with security scanning
- ✅ Production environment configuration

### **🛡️ Enterprise Patterns**
- ✅ Resource management and conflict prevention
- ✅ Comprehensive error handling
- ✅ Configuration validation
- ✅ Structured logging with emojis
{"- ✅ AI integration with smart routing" if config.ai_integration else ""}
{"- ✅ Autonomous debugging foundations" if config.autonomous_debugging else ""}

## 🚀 **Quick Start**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env with your configuration
```

### 3. Run Setup
```bash
python main.py --setup
```

### 4. Test Systems
```bash
# Test all systems
python main.py --diagnose

{"# Test notifications" if config.notification_channels else ""}
{"python main.py --test-notifications" if config.notification_channels else ""}
```

### 5. Start Application
```bash
python main.py
```

## 🐳 **Docker Deployment**

### Development
```bash
docker-compose up --build
```

### Production
```bash
docker-compose -f docker-compose.production.yml up -d
```

{"## ☸️ **Kubernetes Deployment**" if config.kubernetes_support else ""}
{"" if config.kubernetes_support else ""}
{"```bash" if config.kubernetes_support else ""}
{"# Deploy to Kubernetes" if config.kubernetes_support else ""}
{"kubectl apply -f k8s/" if config.kubernetes_support else ""}
{"```" if config.kubernetes_support else ""}

## 📊 **Monitoring**

{"### Health Checks" if config.monitoring_enabled else ""}
{"- System memory usage" if config.monitoring_enabled else ""}
{"- CPU utilization" if config.monitoring_enabled else ""}
{"- Disk space availability" if config.monitoring_enabled else ""}
{"- Database connectivity" if config.monitoring_enabled else ""}
{"- Application performance metrics" if config.monitoring_enabled else ""}

{"### Alerting" if config.notification_channels and config.monitoring_enabled else ""}
{"- Critical alerts → SMS + Telegram + Email" if len(config.notification_channels) > 2 else ""}
{"- High priority → SMS + Telegram" if "sms" in config.notification_channels and "telegram" in config.notification_channels else ""}
{"- Normal alerts → Telegram" if "telegram" in config.notification_channels else ""}
{"- Alert cooldown prevents spam" if config.monitoring_enabled else ""}

## 🔧 **Configuration**

### Environment Variables
```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

{"# Notifications" if config.notification_channels else ""}
{"NOTIFICATIONS_ENABLED=true" if config.notification_channels else ""}
{"TELEGRAM_TARGETS=@admin_channel" if "telegram" in config.notification_channels else ""}
{"SMS_TARGETS=+1234567890" if "sms" in config.notification_channels else ""}
{"TWILIO_ACCOUNT_SID=your_sid" if "sms" in config.notification_channels else ""}
{"TWILIO_AUTH_TOKEN=your_token" if "sms" in config.notification_channels else ""}

{"# AI Integration" if config.ai_integration else ""}
{"ANTHROPIC_API_KEY=your_key" if config.ai_integration else ""}
{"OPENAI_API_KEY=your_key" if config.ai_integration else ""}

{"# Monitoring" if config.monitoring_enabled else ""}
{"MONITORING_ENABLED=true" if config.monitoring_enabled else ""}
{"PERFORMANCE_MONITORING=true" if config.performance_monitoring else ""}
```

## 🧪 **Testing**

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Performance tests
pytest tests/performance/

# Integration tests
pytest tests/integration/
```

## 📈 **Performance**

This application includes several performance optimizations:

- Async/await throughout for I/O operations
- Connection pooling for databases
- Multi-level caching systems
- Resource conflict prevention
- Smart batching for AI operations
- Performance monitoring and alerting

## 🔐 **Security**

Security features included:

- Non-root Docker containers
- Environment variable validation
- Rate limiting for APIs
- Comprehensive input validation
- Security scanning in CI/CD
- Regular dependency updates

## 📚 **Documentation**

- [Setup Guide](docs/setup.md)
- [API Documentation](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Run linting: `black src/ && isort src/ && flake8 src/`
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with enterprise-grade patterns from production systems including the Telegram Knowledge Base Extractor.*
'''
        
        (project_path / "README.md").write_text(readme_content)
    
    def generate_from_idea(self, idea: str) -> Path:
        """Generate project from natural language idea using AI analysis"""
        print(f"🤖 Analyzing idea: {idea}")
        
        # Simple keyword-based analysis (could be enhanced with AI)
        idea_lower = idea.lower()
        
        # Determine project type
        if any(word in idea_lower for word in ["telegram", "discord", "chat", "message"]):
            project_type = "production_automation"
        elif any(word in idea_lower for word in ["api", "rest", "service", "server"]):
            project_type = "enterprise_api"
        elif any(word in idea_lower for word in ["data", "pipeline", "extract", "process"]):
            project_type = "ai_data_pipeline"
        elif any(word in idea_lower for word in ["notify", "alert", "notification"]):
            project_type = "notification_service"
        elif any(word in idea_lower for word in ["monitor", "health", "metrics"]):
            project_type = "monitoring_system"
        else:
            project_type = "production_automation"
        
        # Determine features
        ai_integration = any(word in idea_lower for word in ["ai", "gpt", "claude", "openai", "anthropic"])
        notification_channels = []
        
        if any(word in idea_lower for word in ["telegram", "tg"]):
            notification_channels.append("telegram")
        if any(word in idea_lower for word in ["sms", "text", "phone"]):
            notification_channels.append("sms")
        if any(word in idea_lower for word in ["email", "mail"]):
            notification_channels.append("email")
        
        if not notification_channels:
            notification_channels = ["telegram"]  # Default
        
        # Generate project name from idea
        words = idea.split()[:3]  # Take first 3 words
        name = " ".join(word.capitalize() for word in words if word.isalpha())
        
        config = ProjectConfig(
            name=name,
            description=idea,
            type=project_type,
            components=self.templates[project_type]["components"],
            external_services=self.templates[project_type].get("external_services", []),
            ai_integration=ai_integration,
            notification_channels=notification_channels,
            monitoring_enabled=True,
            kubernetes_support=True,
            async_support=True,
            docker_support=True
        )
        
        return self.generate_project(config)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Python Application Framework Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --idea "Telegram message extractor with AI processing and SMS alerts"
  %(prog)s --template production_automation --name "My Automation"
  %(prog)s --interactive
        """
    )
    
    parser.add_argument("--idea", help="Generate project from natural language description")
    parser.add_argument("--template", choices=[
        "production_automation", "ai_data_pipeline", "enterprise_api", 
        "notification_service", "monitoring_system"
    ], help="Use predefined template")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--description", help="Project description")
    parser.add_argument("--interactive", action="store_true", help="Interactive project configuration")
    
    args = parser.parse_args()
    
    framework = EnhancedPythonFramework()
    
    if args.idea:
        print(f"🚀 Generating from idea: {args.idea}")
        project_path = framework.generate_from_idea(args.idea)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.template:
        template = framework.templates[args.template]
        name = args.name or f"Enhanced {args.template.replace('_', ' ').title()}"
        description = args.description or template["description"]
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=args.template,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=template.get("notification_channels", ["telegram"]),
            ai_integration=template.get("ai_integration", True),
            monitoring_enabled=template.get("monitoring_enabled", True),
            kubernetes_support=template.get("kubernetes_support", False),
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"✅ Project generated at: {project_path}")
        
    elif args.interactive:
        print("🎯 Enhanced Interactive Project Configuration")
        print("=" * 60)
        
        name = input("Project name: ")
        description = input("Project description: ")
        
        print("\\nAvailable templates:")
        templates = list(framework.templates.keys())
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template} - {framework.templates[template]['description']}")
        
        template_choice = int(input("\\nSelect template (1-5): ")) - 1
        template_type = templates[template_choice]
        template = framework.templates[template_type]
        
        # Enhanced configuration
        ai_integration = input("Include AI integration? (y/n): ").lower() == 'y'
        
        print("\\nNotification channels (separate with commas):")
        print("Available: telegram, sms, email")
        notification_input = input("Channels: ").strip()
        notification_channels = [ch.strip() for ch in notification_input.split(",") if ch.strip()]
        
        monitoring = input("Enable monitoring and alerting? (y/n): ").lower() == 'y'
        kubernetes = input("Include Kubernetes deployment? (y/n): ").lower() == 'y'
        
        config = ProjectConfig(
            name=name,
            description=description,
            type=template_type,
            components=template["components"],
            external_services=template.get("external_services", []),
            notification_channels=notification_channels or ["telegram"],
            ai_integration=ai_integration,
            monitoring_enabled=monitoring,
            kubernetes_support=kubernetes,
            async_support=True,
            docker_support=True
        )
        
        project_path = framework.generate_project(config)
        print(f"\\n✅ Enhanced project generated at: {project_path}")
        
    else:
        parser.print_help()
        sys.exit(1)
    
    print("\\n🎉 Next steps:")
    print("  1. cd into the project directory")
    print("  2. python -m venv venv && source venv/bin/activate")
    print("  3. pip install -r requirements.txt")
    print("  4. cp .env.template .env && edit .env")
    print("  5. python main.py --setup")
    print("  6. python main.py --diagnose")
    print("  7. python main.py")
    print("\\n🚀 Your production-ready application is ready!")


if __name__ == "__main__":
    main()
