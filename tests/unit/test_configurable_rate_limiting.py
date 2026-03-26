#!/usr/bin/env python3
"""
Test script for configurable rate limiting system
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_rate_limit_config_loading():
    """Test that rate limiting configuration is properly loaded from .env"""
    
    print("Testing Rate Limiting Configuration Loading")
    print("=" * 50)
    
    try:
        from src.config import AppConfig
        
        # Load configuration
        config = AppConfig()
        rate_config = config.rate_limit
        
        print(f"✓ Configuration loaded successfully")
        print(f"  Min Delay: {rate_config.min_delay}s")
        print(f"  Max Delay: {rate_config.max_delay}s")
        print(f"  Penalty Delay: {rate_config.penalty_delay}s")
        print(f"  Max Requests per Minute: {rate_config.max_requests_per_minute}")
        print(f"  Max Requests per Hour: {rate_config.max_requests_per_hour}")
        print(f"  Max Requests per Day: {rate_config.max_requests_per_day}")
        print(f"  Conservative Mode: {rate_config.conservative_mode}")
        print(f"  Conservative Multiplier: {rate_config.conservative_multiplier}")
        print(f"  Session Timeout: {rate_config.session_timeout}s")
        print(f"  Max Consecutive Errors: {rate_config.max_consecutive_errors}")
        print(f"  Cooldown After Errors: {rate_config.cooldown_after_errors}s")
        print(f"  Exponential Backoff: {rate_config.exponential_backoff}")
        print(f"  Randomize Delays: {rate_config.randomize_delays}")
        print(f"  Respect Robots.txt: {rate_config.respect_robots_txt}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

def test_linkedin_wrapper_config():
    """Test that LinkedInWrapper uses the rate limiting configuration"""
    
    print("\nTesting LinkedIn Wrapper Configuration Integration")
    print("=" * 50)
    
    try:
        # Mock credentials for testing (won't actually connect)
        from linkedin_wrapper import LinkedInWrapper
        
        wrapper = LinkedInWrapper(
            username="test@example.com",
            password="test_password"
        )
        
        print(f"✓ LinkedInWrapper initialized successfully")
        print(f"  Min Delay: {wrapper.min_delay}s")
        print(f"  Max Delay: {wrapper.max_delay}s")
        print(f"  Rate Limit Delay: {wrapper.rate_limit_delay}s")
        print(f"  Max Requests per Minute: {wrapper.max_requests_per_minute}")
        print(f"  Max Requests per Hour: {wrapper.max_requests_per_hour}")
        print(f"  Max Requests per Day: {wrapper.max_requests_per_day}")
        print(f"  Conservative Mode: {wrapper.conservative_mode}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to initialize LinkedInWrapper: {e}")
        return False

def test_environment_override():
    """Test that environment variables override default values"""
    
    print("\nTesting Environment Variable Override")
    print("=" * 50)
    
    # Set test environment variables
    test_env = {
        'RATE_LIMIT_MIN_DELAY': '3.5',
        'RATE_LIMIT_MAX_DELAY': '8.0',
        'RATE_LIMIT_PENALTY_DELAY': '120',
        'RATE_LIMIT_CONSERVATIVE_MODE': 'true'
    }
    
    # Save original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        # Import after setting environment variables
        import importlib
        if 'src.config' in sys.modules:
            importlib.reload(sys.modules['src.config'])
        
        from src.config import AppConfig
        
        config = AppConfig()
        rate_config = config.rate_limit
        
        print(f"✓ Environment override test completed")
        print(f"  Min Delay: {rate_config.min_delay}s (expected: 3.5)")
        print(f"  Max Delay: {rate_config.max_delay}s (expected: 8.0)")
        print(f"  Penalty Delay: {rate_config.penalty_delay}s (expected: 120)")
        print(f"  Conservative Mode: {rate_config.conservative_mode} (expected: True)")
        
        # Verify values
        success = (
            rate_config.min_delay == 3.5 and
            rate_config.max_delay == 8.0 and
            rate_config.penalty_delay == 120 and
            rate_config.conservative_mode == True
        )
        
        if success:
            print("✓ All environment overrides working correctly")
        else:
            print("✗ Some environment overrides not working")
            
        return success
        
    except Exception as e:
        print(f"✗ Environment override test failed: {e}")
        return False
        
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

def main():
    """Main test function"""
    print("Configurable Rate Limiting System Test")
    print("=" * 60)
    
    tests = [
        test_rate_limit_config_loading,
        test_linkedin_wrapper_config,
        test_environment_override
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Rate limiting configuration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
