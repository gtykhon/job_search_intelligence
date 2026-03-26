# Job Search Intelligence - Scheduled Tasks Monitoring Guide

## 📋 Overview
This guide covers monitoring, managing, and troubleshooting the Windows scheduled tasks for Job Search Intelligence automation.

## 🕒 Task Schedule Summary

### Daily Tasks
| Task Name | Time | Purpose | Output Location |
|-----------|------|---------|-----------------|
| LinkedIn-Daily-Opportunity-Detection | 6:00 AM | Detect new job opportunities | `reports/daily/YYYY-MM-DD/opportunity_detection_*.md` |
| LinkedIn-Daily-Market-Analysis | 10:00 AM | Analyze job market trends | `reports/daily/YYYY-MM-DD/market_analysis_*.md` |
| LinkedIn-Daily-Network-Insights | 2:00 PM | Analyze network growth | `reports/daily/YYYY-MM-DD/network_insights_*.md` |
| LinkedIn-Daily-Summary | 6:00 PM | Generate daily summary | `reports/daily/YYYY-MM-DD/daily_summary_*.md` |

### Weekly Tasks
| Task Name | Time | Purpose | Output Location |
|-----------|------|---------|-----------------|
| LinkedIn-Weekly-Intelligence | Monday 8:00 AM | Comprehensive weekly analysis | `reports/weekly/YYYY-WW/intelligence_*.md` |
| LinkedIn-Weekly-Predictive-Analytics | Monday 9:00 AM | Predictive job market analysis | `reports/weekly/YYYY-WW/predictive_*.md` |

### Bi-weekly Tasks
| Task Name | Time | Purpose | Output Location |
|-----------|------|---------|-----------------|
| LinkedIn-Biweekly-Deep-Analysis | Wednesday 12:00 PM (every 2 weeks) | Deep intelligence analysis | `reports/biweekly/YYYY-WW/deep_analysis_*.md` |

## 🔍 Monitoring Commands

### View All LinkedIn Tasks
```cmd
schtasks /query | findstr "LinkedIn"
```

### View Specific Task Details
```cmd
schtasks /query /tn "LinkedIn-Daily-Opportunity-Detection" /fo list /v
```

### Check Task History
```cmd
schtasks /query /tn "LinkedIn-Daily-Opportunity-Detection" /fo list /v | findstr "Last Result"
```

### Run Task Manually
```cmd
schtasks /run /tn "LinkedIn-Daily-Opportunity-Detection"
```

## 📊 Task Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 0x0 | Success | Task completed successfully |
| 0x1 | Incorrect function | General error |
| 0x2 | File not found | Script or batch file missing |
| 0x267008 | Task is currently running | Task already in progress |
| 0x8004131F | Task not scheduled | Task disabled or not properly configured |

## 📁 Log File Locations

### Task Execution Logs
- **Location:** `logs/scheduled_tasks/`
- **Pattern:** `task_name_YYYYMMDD_HHMMSS.log`
- **Example:** `daily_opportunity_detection_20251006_060000.log`

### Application Logs
- **Location:** `logs/`
- **Pattern:** `linkedin_analysis_YYYYMMDD_HHMMSS.log`
- **Contains:** Detailed application execution logs

### Report Files
- **Daily:** `reports/daily/YYYY-MM-DD/`
- **Weekly:** `reports/weekly/YYYY-WW/`
- **Bi-weekly:** `reports/biweekly/YYYY-WW/`

## 🛠️ Management Scripts

### Enable All Tasks
```cmd
scripts\scheduled_tasks\manage_windows_tasks.bat enable
```

### Disable All Tasks
```cmd
scripts\scheduled_tasks\manage_windows_tasks.bat disable
```

### Remove All Tasks
```cmd
scripts\scheduled_tasks\remove_windows_tasks.bat
```

### Recreate All Tasks
```cmd
scripts\scheduled_tasks\create_windows_tasks.bat
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Task Shows "Ready" but Never Runs
**Cause:** Task Scheduler service not running
**Solution:**
```cmd
net start "Task Scheduler"
```

#### 2. Task Fails with Error 0x2
**Cause:** Script file path incorrect
**Solution:** Verify batch file exists and path is correct

#### 3. Task Runs but No Output
**Cause:** Python environment or dependencies missing
**Solution:** 
1. Check Python environment: `python --version`
2. Install requirements: `pip install -r requirements.txt`
3. Test script manually

#### 4. Authentication Errors
**Cause:** LinkedIn cookies expired
**Solution:**
1. Delete `cache/linkedin_cookies.json`
2. Run authentication manually: `python src/core/linkedin_authenticator.py`

### Diagnostic Commands

#### Check Python Environment
```cmd
python --version
pip list | findstr "selenium\|requests\|beautifulsoup4"
```

#### Test LinkedIn Connection
```cmd
python -c "from src.core.linkedin_wrapper import LinkedInWrapper; print('✓ LinkedIn module OK')"
```

#### Verify File Permissions
```cmd
icacls scripts\scheduled_tasks\*.bat
```

## 📈 Performance Monitoring

### Expected Execution Times
- **Daily Opportunity Detection:** 30-60 seconds
- **Daily Market Analysis:** 45-90 seconds
- **Daily Network Insights:** 20-45 seconds
- **Daily Summary:** 15-30 seconds
- **Weekly Intelligence:** 2-5 minutes
- **Weekly Predictive Analytics:** 3-7 minutes
- **Bi-weekly Deep Analysis:** 5-15 minutes

### Resource Usage
- **Memory:** 100-300 MB per task
- **CPU:** Moderate during execution
- **Network:** LinkedIn API calls (rate-limited)
- **Disk:** Report files (~1-5 MB each)

## 🔔 Notification Settings

### Telegram Integration
- **Status:** Enabled by default
- **Channel:** Configured in environment variables
- **Content:** Task completion notifications + reports

### Email Notifications (Optional)
- **Setup:** Configure SMTP settings in `src/config/`
- **Recipients:** Define in environment variables

## 📅 Maintenance Schedule

### Daily
- ✅ Check task execution status
- ✅ Verify report generation
- ✅ Monitor disk space

### Weekly
- ✅ Review log files
- ✅ Clean old reports (optional)
- ✅ Update dependencies if needed

### Monthly
- ✅ Review task performance
- ✅ Update authentication tokens
- ✅ Archive old logs

## 🆘 Emergency Procedures

### Stop All Running Tasks
```cmd
taskkill /f /im python.exe /fi "WINDOWTITLE eq LinkedIn*"
```

### Disable All Tasks Immediately
```cmd
schtasks /change /tn "LinkedIn-Daily-Opportunity-Detection" /disable
schtasks /change /tn "LinkedIn-Daily-Market-Analysis" /disable
schtasks /change /tn "LinkedIn-Daily-Network-Insights" /disable
schtasks /change /tn "LinkedIn-Daily-Summary" /disable
schtasks /change /tn "LinkedIn-Weekly-Intelligence" /disable
schtasks /change /tn "LinkedIn-Weekly-Predictive-Analytics" /disable
schtasks /change /tn "LinkedIn-Biweekly-Deep-Analysis" /disable
```

### Emergency Contact Information
- **System Administrator:** [Your contact info]
- **Technical Support:** [Support contact]
- **Documentation:** This file and `README.md`

## 📚 Additional Resources

- **Main Documentation:** `README.md`
- **Setup Guide:** `docs/user-guides/SETUP_GUIDE.md`
- **Telegram Integration:** `docs/technical/TELEGRAM_INTEGRATION.md`
- **Rate Limiting:** `docs/technical/RATE_LIMITING.md`
- **Task Scripts:** `scripts/scheduled_tasks/`

---

*Last Updated: October 6, 2025*
*Version: 1.0*