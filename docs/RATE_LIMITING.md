# Rate Limiting Configuration - Job Search Intelligence

## Overview

The Job Search Intelligence now features a comprehensive, configurable rate limiting system that helps prevent your account from being blocked while maintaining optimal performance for your use case.

## Current Configuration

Your system is currently using these rate limiting settings (loaded from `.env`):

- **Min Delay**: 2.0s (minimum time between requests)
- **Max Delay**: 5.0s (maximum time between requests) 
- **Penalty Delay**: 60s (wait time when rate limited)
- **Max Requests per Minute**: 10
- **Max Requests per Hour**: 300
- **Max Requests per Day**: 5000
- **Conservative Mode**: False (normal operation)

## Rate Limiting Protection Features

### 1. **Configurable Delays**
- Minimum and maximum delays between requests
- Randomized timing to avoid detection patterns
- Exponential backoff on errors

### 2. **Request Tracking**
- Tracks requests per minute, hour, and day
- Automatically throttles when limits are approached
- Session-based request counting

### 3. **Conservative Mode**
- Multiplies all delays by configurable factor (default: 2.0x)
- Reduces request limits for extra safety
- Ideal for new accounts or research use

### 4. **Error Handling**
- Detects HTTP 429 (Too Many Requests) responses
- Automatic backoff with increasing delays
- Cooldown periods after consecutive errors

### 5. **Smart Session Management**
- Session timeout handling
- Automatic reconnection with delays
- Cookie management and refresh

## Configuration Examples

### Conservative (Recommended for New Users)
```env
RATE_LIMIT_MIN_DELAY=5.0
RATE_LIMIT_MAX_DELAY=10.0
RATE_LIMIT_PENALTY_DELAY=300
RATE_LIMIT_MAX_PER_MINUTE=5
RATE_LIMIT_MAX_PER_HOUR=100
RATE_LIMIT_MAX_PER_DAY=1000
RATE_LIMIT_CONSERVATIVE_MODE=true
```

### Standard (Current Default)
```env
RATE_LIMIT_MIN_DELAY=2.0
RATE_LIMIT_MAX_DELAY=5.0
RATE_LIMIT_PENALTY_DELAY=60
RATE_LIMIT_MAX_PER_MINUTE=10
RATE_LIMIT_MAX_PER_HOUR=300
RATE_LIMIT_MAX_PER_DAY=5000
RATE_LIMIT_CONSERVATIVE_MODE=false
```

### Aggressive (Advanced Users Only)
```env
RATE_LIMIT_MIN_DELAY=1.0
RATE_LIMIT_MAX_DELAY=3.0
RATE_LIMIT_PENALTY_DELAY=30
RATE_LIMIT_MAX_PER_MINUTE=20
RATE_LIMIT_MAX_PER_HOUR=500
RATE_LIMIT_MAX_PER_DAY=10000
RATE_LIMIT_CONSERVATIVE_MODE=false
```

### Ultra Safe (Research/Academic)
```env
RATE_LIMIT_MIN_DELAY=10.0
RATE_LIMIT_MAX_DELAY=20.0
RATE_LIMIT_PENALTY_DELAY=600
RATE_LIMIT_MAX_PER_MINUTE=3
RATE_LIMIT_MAX_PER_HOUR=50
RATE_LIMIT_MAX_PER_DAY=500
RATE_LIMIT_CONSERVATIVE_MODE=true
```

## All Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `RATE_LIMIT_MIN_DELAY` | 2.0 | Minimum seconds between requests |
| `RATE_LIMIT_MAX_DELAY` | 5.0 | Maximum seconds between requests |
| `RATE_LIMIT_PENALTY_DELAY` | 60 | Seconds to wait when rate limited |
| `RATE_LIMIT_MAX_PER_MINUTE` | 10 | Maximum requests per minute |
| `RATE_LIMIT_MAX_PER_HOUR` | 300 | Maximum requests per hour |
| `RATE_LIMIT_MAX_PER_DAY` | 5000 | Maximum requests per day |
| `RATE_LIMIT_CONSERVATIVE_MODE` | false | Enable conservative multipliers |
| `RATE_LIMIT_CONSERVATIVE_MULTIPLIER` | 2.0 | Multiplier for conservative mode |
| `RATE_LIMIT_SESSION_TIMEOUT` | 3600 | Session timeout in seconds |
| `RATE_LIMIT_MAX_CONSECUTIVE_ERRORS` | 5 | Max errors before cooldown |
| `RATE_LIMIT_COOLDOWN_AFTER_ERRORS` | 300 | Cooldown time after errors |
| `RATE_LIMIT_EXPONENTIAL_BACKOFF` | true | Enable exponential backoff |
| `RATE_LIMIT_RANDOMIZE_DELAYS` | true | Randomize request timing |
| `RATE_LIMIT_RESPECT_ROBOTS_TXT` | true | Respect robots.txt guidelines |

## Usage Recommendations

### 🆕 First Time Users
- Start with **Conservative** or **Ultra Safe** settings
- Monitor logs carefully for any warnings
- Gradually increase limits if no issues occur
- Never skip the rate limiting protections

### 👤 Regular Users  
- Use **Standard** settings for balanced performance
- Enable Conservative Mode if you encounter any blocking
- Adjust based on your account age and typical activity
- Monitor request patterns in logs

### 🚀 Heavy Users
- **Aggressive** settings only for established accounts
- Monitor closely for signs of rate limiting
- Be prepared to scale back immediately if issues arise
- Consider using multiple accounts with rotation

### 🎓 Research/Academic
- Always use **Ultra Safe** or **Conservative** settings
- Spread data collection over longer periods
- Document your rate limiting approach
- Consider ethical implications of data collection

## How to Modify Settings

1. **Edit the `.env` file** in your project root directory
2. **Add or modify** the rate limiting variables you want to change
3. **Restart the application** to load new settings
4. **Check the logs** to confirm new settings are active
5. **Monitor performance** and adjust as needed

## Monitoring and Troubleshooting

### Log Messages to Watch For
- `Rate limit detected, waiting...` - Normal rate limiting response
- `Too many consecutive errors` - May need to increase delays
- `Session timeout, reconnecting` - Normal session management
- `Conservative mode enabled` - Extra protection active

### Warning Signs
- Frequent rate limit messages
- Login challenges or CAPTCHAs
- Sudden drops in data collection
- HTTP 429 responses

### If You Get Blocked
1. **Stop the application immediately**
2. **Switch to Ultra Safe settings**
3. **Wait 24-48 hours before resuming**
4. **Consider using different IP/account**
5. **Review and reduce your request patterns**

## Best Practices

### ✅ Do
- Start conservative and increase gradually
- Monitor logs regularly
- Respect LinkedIn's terms of service
- Use randomized delays
- Enable exponential backoff
- Test settings with small datasets first

### ❌ Don't
- Disable all rate limiting
- Use the same timing patterns repeatedly
- Ignore rate limit warnings
- Run multiple instances simultaneously
- Skip the cooldown periods
- Use aggressive settings on new accounts

## Technical Implementation

The rate limiting system is implemented at multiple levels:

1. **Request Level**: Individual request delays and timing
2. **Session Level**: Session management and timeouts  
3. **Application Level**: Global request tracking and limits
4. **Configuration Level**: Environment-based customization

The system automatically adjusts behavior based on:
- Response codes (especially HTTP 429)
- Error patterns and frequency
- Request success/failure rates
- Session state and health

## Support and Further Help

If you encounter issues with rate limiting:

1. Check the logs for specific error messages
2. Try more conservative settings
3. Review your network and account status
4. Consider your overall usage patterns
5. Ensure you're following LinkedIn's terms of service

Remember: The goal is sustainable, long-term data access while respecting platform policies and avoiding account restrictions.
