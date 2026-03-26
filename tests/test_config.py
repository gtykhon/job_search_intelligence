#!/usr/bin/env python3
"""
Configuration Test Script
Tests that the .env file is properly connected to the Python configuration
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import AppConfig, get_config

def test_configuration():
    """Test configuration loading from .env file"""
    print("🔧 Job Search Intelligence - Configuration Test")
    print("=" * 60)
    
    try:
        # Load configuration
        config = AppConfig.from_env()
        
        print("✅ Configuration loaded successfully!\n")
        
        # Test LinkedIn configuration
        print("📱 LinkedIn Configuration:")
        print(f"   Username: {'✅ ' + config.linkedin.username if config.linkedin.username else '❌ Not set'}")
        print(f"   Password: {'✅ Configured' if config.linkedin.password else '❌ Not set'}")
        print(f"   Session Timeout: {config.linkedin.session_timeout}s")
        print(f"   Max Retries: {config.linkedin.max_retries}")
        print(f"   Request Delay: {config.linkedin.request_delay}s")
        
        # Test AI configuration
        print("\n🤖 AI Configuration:")
        print(f"   Enabled: {'✅' if config.ai.enabled else '❌'}")
        print(f"   Provider: {config.ai.provider}")
        print(f"   Model: {config.ai.model}")
        print(f"   API Key: {'✅ Configured' if config.ai.api_key else '❌ Not set'}")
        print(f"   Max Tokens: {config.ai.max_tokens}")
        print(f"   Temperature: {config.ai.temperature}")
        
        # Test monitoring configuration
        print("\n📊 Monitoring Configuration:")
        print(f"   Enabled: {'✅' if config.monitoring.enabled else '❌'}")
        print(f"   Log Level: {config.monitoring.log_level}")
        print(f"   Performance Monitoring: {'✅' if config.monitoring.performance_monitoring else '❌'}")
        print(f"   Health Check Interval: {config.monitoring.health_check_interval}s")
        
        # Test notifications configuration
        print("\n📧 Notification Configuration:")
        print(f"   Enabled: {'✅' if config.notifications.enabled else '❌'}")
        print(f"   Channels: {', '.join(config.notifications.channels)}")
        print(f"   Email Enabled: {'✅' if config.notifications.email_enabled else '❌'}")
        print(f"   Telegram Enabled: {'✅' if config.notifications.telegram_enabled else '❌'}")
        
        # Test resource configuration
        print("\n🔧 Resource Configuration:")
        print(f"   Max Concurrent Requests: {config.resources.max_concurrent_requests}")
        print(f"   Connection Pool Size: {config.resources.connection_pool_size}")
        print(f"   Connection Timeout: {config.resources.connection_timeout}s")
        print(f"   Session Isolation: {'✅' if config.resources.session_isolation else '❌'}")
        
        # Test storage configuration
        print("\n💾 Storage Configuration:")
        print(f"   Data Directory: {config.storage.data_directory}")
        print(f"   Output Directory: {config.storage.output_directory}")
        print(f"   Cache Directory: {config.storage.cache_directory}")
        print(f"   Logs Directory: {config.storage.logs_directory}")
        print(f"   Backup Enabled: {'✅' if config.storage.backup_enabled else '❌'}")
        
        # Test analysis configuration
        print("\n🔍 Analysis Configuration:")
        print(f"   Mode: {config.analysis.mode.value}")
        print(f"   AI Insights: {'✅' if config.analysis.ai_insights else '❌'}")
        print(f"   Include Connections: {'✅' if config.analysis.include_connections else '❌'}")
        print(f"   Include Followers: {'✅' if config.analysis.include_followers else '❌'}")
        print(f"   Pattern Detection: {'✅' if config.analysis.pattern_detection else '❌'}")
        print(f"   Export Formats: {', '.join(config.analysis.export_formats)}")
        
        # Test environment
        print(f"\n🌍 Environment: {config.environment.value}")
        print(f"🐛 Debug Mode: {'✅' if config.debug else '❌'}")
        
        # Validate configuration
        print("\n🔍 Configuration Validation:")
        errors = config.validate()
        if errors:
            print("❌ Configuration has errors:")
            for error in errors:
                print(f"   • {error}")
            return False
        else:
            print("✅ Configuration validation passed!")
            
        # Test environment variables direct access
        print("\n🔐 Environment Variables Check:")
        import os
        env_vars = [
            'LINKEDIN_USERNAME',
            'LINKEDIN_PASSWORD', 
            'AI_ENABLED',
            'AI_PROVIDER',
            'ENVIRONMENT',
            'DEBUG',
            'LOG_LEVEL'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                if 'PASSWORD' in var or 'KEY' in var:
                    print(f"   {var}: {'✅ Set' if value else '❌ Not set'}")
                else:
                    print(f"   {var}: ✅ {value}")
            else:
                print(f"   {var}: ❌ Not set")
        
        print("\n🎉 Configuration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_configuration()
    exit(0 if success else 1)
