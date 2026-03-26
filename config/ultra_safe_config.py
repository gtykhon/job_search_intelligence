"""
Enhanced Rate Limiting Configuration for Job Search Intelligence
Ultra-conservative settings to minimize blocking risk
"""

# Place this in your .env file or config
RATE_LIMITING_CONFIG = {
    # Ultra-conservative delays
    "MIN_DELAY": 5,                    # 5-10 second delays (vs current 2-5)
    "MAX_DELAY": 10,
    "RATE_LIMIT_DELAY": 300,           # 5 minutes on rate limit (vs 1 minute)
    
    # Request limits per time period
    "MAX_REQUESTS_PER_MINUTE": 6,      # Maximum 6 requests per minute
    "MAX_REQUESTS_PER_HOUR": 200,      # Maximum 200 requests per hour
    "MAX_REQUESTS_PER_DAY": 2000,      # Maximum 2000 requests per day
    
    # Session management
    "SESSION_TIMEOUT": 1800,           # 30 minutes (vs 1 hour)
    "MAX_CONSECUTIVE_ERRORS": 3,       # Stop after 3 errors (vs 5)
    "COOLDOWN_AFTER_ERRORS": 600,     # 10 minutes cooldown
    
    # Safety features
    "CONSERVATIVE_MODE": True,         # Enable extra safety
    "RANDOMIZE_DELAYS": True,          # Add randomness to requests
    "PROGRESSIVE_BACKOFF": True,       # Increase delays on errors
}

# Recommended usage patterns
SAFE_USAGE_PATTERNS = {
    "daily_analysis": {
        "max_connections_analyzed": 100,    # Limit to 100 connections per day
        "analysis_frequency": "once_daily", # Run once per day max
        "batch_size": 20,                   # Smaller batches
    },
    "network_analysis": {
        "max_connections_analyzed": 50,     # Even smaller for network analysis
        "delay_between_batches": 300,       # 5 minutes between batches
        "max_depth": 2,                     # Limit connection depth
    },
    "ai_analysis": {
        "frequency": "weekly",              # AI analysis weekly only
        "data_source": "cached",            # Use cached data when possible
    }
}

# Signs that you might be getting flagged
WARNING_SIGNS = [
    "Increased captcha requests",
    "Login challenges",
    "Slower response times",
    "Empty results when data should exist",
    "Profile access restrictions",
    "Connection request failures",
    "Repeated HTTP 429 errors",
    "Session timeouts",
]

# Emergency procedures if you think you're flagged
EMERGENCY_PROCEDURES = [
    "1. Stop all automated requests immediately",
    "2. Wait 24-48 hours before manual LinkedIn use",
    "3. Use LinkedIn manually/normally for a few days", 
    "4. Reduce automation frequency when resuming",
    "5. Implement longer delays (10-30 seconds)",
    "6. Consider changing IP address",
    "7. Use different user-agent strings",
]
