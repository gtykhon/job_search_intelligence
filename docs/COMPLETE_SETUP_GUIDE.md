# Job Search Intelligence - Complete Setup Guide

This guide will walk you through setting up the Job Search Intelligence with Profile Intelligence features.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Profile Intelligence Setup](#profile-intelligence-setup)
5. [LinkedIn API Setup](#linkedin-api-setup)
6. [Telegram Integration](#telegram-integration)
7. [Testing and Verification](#testing-and-verification)
8. [Usage Examples](#usage-examples)
9. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### System Requirements
- **Python 3.8+** (Recommended: Python 3.9 or 3.10)
- **Windows/Linux/macOS** (Tested on Windows 11)
- **4GB+ RAM** (8GB recommended for large-scale analysis)
- **2GB+ Disk Space** for logs, reports, and cache

### Required Accounts
- **LinkedIn Account** - For profile analysis and job search
- **Telegram Account** - For notifications (optional but recommended)
- **GitHub Account** - For version control (if contributing)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/gtykhon/job_search_intelligence.git
cd job_search_intelligence
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "import linkedin_api; print('LinkedIn API installed successfully')"
```

## ⚙️ Configuration

### 1. Environment Configuration
Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
```properties
# LinkedIn Configuration
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Telegram Configuration (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### 2. Database Setup
```bash
python config/setup_database.py
```

### 3. Telegram Bot Setup (Optional)
```bash
python config/setup_telegram_bot.py
```

## 🧠 Profile Intelligence Setup

The Profile Intelligence System is the core feature that analyzes your LinkedIn profile for intelligent job matching.

### Step 1: Create Your Profile Intelligence
```bash
python tools/create_grygorii_profile.py
```

This will:
- ✅ Extract intelligence from your LinkedIn profile data
- ✅ Analyze your skills, experience, and background
- ✅ Create structured profile intelligence
- ✅ Save to `config/profile_intelligence.json`

### Step 2: Generate Intelligent Job Search Configuration
```bash
python tools/generate_grygorii_job_search_config.py
```

This will:
- ✅ Create optimized job search parameters
- ✅ Generate LinkedIn search strings
- ✅ Identify target companies
- ✅ Set appropriate salary ranges
- ✅ Save to `config/intelligent_job_search_config.json`

### Step 3: Verify Profile Integration
```bash
python tools/verify_grygorii_profile_integration.py
```

This will:
- ✅ Verify profile data quality
- ✅ Check configuration files
- ✅ Display profile summary
- ✅ Show LinkedIn search strings
- ✅ List target companies

### Step 4: Interactive Profile Management
```bash
python profile_intelligence_cli.py
```

This provides:
- 📊 Interactive profile dashboard
- ⚙️ Configuration management
- 🔍 Search string testing
- 📈 Career insights

## 🔗 LinkedIn API Setup

### Option 1: Use LinkedIn Credentials (Recommended)
Your LinkedIn username and password in `.env` file will be used for authentication.

### Option 2: LinkedIn API Integration (Advanced)
```bash
python tools/real_linkedin_api_integration.py
```

This will:
- 🔐 Authenticate with LinkedIn using your credentials
- 📥 Fetch real profile data via API
- 🧠 Create intelligence from API data
- 📊 Compare with manual profile data

## 📱 Telegram Integration

### 1. Create Telegram Bot
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the bot token to your `.env` file

### 2. Get Your Chat ID
1. Message your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your chat ID in the response
4. Add it to your `.env` file

### 3. Test Telegram Integration
```bash
python config/setup_telegram_bot.py
```

## 🧪 Testing and Verification

### 1. Quick System Check
```bash
python tests/test_intelligent_config.py
```

### 2. Profile Intelligence Test
```bash
python tests/test_real_integration.py
```

### 3. External Pipeline Test
```bash
python tests/test_external_pipeline_integration.py
```

### 4. Complete System Test
```bash
python tests/test_complete_automation.py
```

### 5. Demo Profile Intelligence
```bash
python examples/demo_profile_intelligence.py
```

## 📖 Usage Examples

### Basic Profile Intelligence
```python
from src.intelligence.profile_based_intelligence import ProfileBasedIntelligence

# Initialize the system
intelligence = ProfileBasedIntelligence()

# Load your profile
intelligence.load_profile_from_file("config/profile_intelligence.json")

# Generate search criteria
criteria = intelligence.generate_intelligent_search_criteria()

print(f"Recommended job titles: {criteria.recommended_job_titles}")
print(f"Target companies: {criteria.target_companies}")
```

### Manual LinkedIn Search
Use the generated search strings from verification:

```bash
# Get your optimized search strings
python tools/verify_grygorii_profile_integration.py
```

Copy the LinkedIn search strings and paste into LinkedIn's job search.

### Automated Job Search Pipeline
```bash
python run_complete_pipeline.py
```

### Production Automation
```bash
python launchers/launch_automation_system.py
```

## 🔧 Troubleshooting

### Common Issues

#### 1. LinkedIn Authentication Failed
```bash
# Check your credentials
python tools/real_linkedin_api_integration.py
```

**Solutions:**
- Verify `LINKEDIN_USERNAME` and `LINKEDIN_PASSWORD` in `.env`
- Check if LinkedIn account requires 2FA
- Try clearing cache: `rm -rf cache/`

#### 2. Profile Intelligence Not Working
```bash
# Recreate profile intelligence
python tools/create_grygorii_profile.py
```

**Solutions:**
- Ensure you provided complete LinkedIn profile text
- Check `config/profile_intelligence.json` exists
- Verify profile data quality score > 80%

#### 3. Import Errors
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

**Solutions:**
- Ensure you're in the project root directory
- Activate virtual environment: `.venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

#### 4. Configuration File Errors
```bash
# Reset configuration
rm config/profile_intelligence.json
rm config/intelligent_job_search_config.json
python tools/create_grygorii_profile.py
python tools/generate_grygorii_job_search_config.py
```

#### 5. Telegram Bot Not Working
```bash
# Test Telegram setup
python config/setup_telegram_bot.py
```

**Solutions:**
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Ensure bot is started (send `/start` to your bot)
- Check network connectivity

### Debug Mode
Enable debug logging in `.env`:
```properties
DEBUG=true
LOG_LEVEL=DEBUG
```

Then check logs in `logs/` directory.

### Support
If you need help:

1. **Check logs**: Look in `logs/` directory for error details
2. **Run diagnostics**: Use verification scripts to identify issues
3. **Reset configuration**: Delete config files and recreate
4. **Contact support**: Create an issue on GitHub with error logs

## 📊 System Architecture

```
Profile Intelligence Flow:
LinkedIn Profile → Profile Extractor → Intelligence Analysis → Job Search Config → Search Strings
                     ↓                      ↓                       ↓                    ↓
                Profile Data    →    Intelligence Data    →    Search Parameters  →  Optimized Results
```

## 🎯 Next Steps

After successful setup:

1. **Run Profile Intelligence**: Create and verify your profile intelligence
2. **Test Job Search**: Use generated search strings on LinkedIn
3. **Setup Automation**: Configure automated weekly reports
4. **Monitor Results**: Check reports and notifications
5. **Optimize Configuration**: Adjust parameters based on results

---

**Job Search Intelligence Setup Guide** - Complete installation and configuration instructions.

*Last updated: October 6, 2025*