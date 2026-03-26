# Job Search Intelligence - Windows Task Scheduler Setup

## 📋 Overview

This guide will help you set up automated Windows scheduled tasks for the Job Search Intelligence. The system will run comprehensive intelligence gathering and analysis automatically throughout the week.

## 🕒 Schedule Overview

### Daily Tasks
- **6:00 AM** - Opportunity Detection
- **10:00 AM** - Market Analysis  
- **2:00 PM** - Network Insights
- **6:00 PM** - Daily Summary

### Weekly Tasks
- **Monday 8:00 AM** - Intelligence Orchestrator
- **Monday 9:00 AM** - Predictive Analytics

### Bi-weekly Tasks
- **Wednesday 12:00 PM** - Deep Analysis (every other week)

## 🚀 Quick Setup

### Method 1: Automated Setup (Recommended)

1. **Run the setup script:**
   ```batch
   scripts\scheduled_tasks\create_windows_tasks.bat
   ```

2. **Verify tasks were created:**
   ```batch
   scripts\scheduled_tasks\manage_windows_tasks.bat list
   ```

### Method 2: PowerShell Setup (Advanced)

1. **Open PowerShell as Administrator**
2. **Run the PowerShell setup:**
   ```powershell
   scripts\scheduled_tasks\setup_windows_tasks.ps1
   ```

## 📊 Task Management

### List All Tasks
```batch
scripts\scheduled_tasks\manage_windows_tasks.bat list
```

### Check Task Status
```batch
scripts\scheduled_tasks\manage_windows_tasks.bat status
```

### Enable All Tasks
```batch
scripts\scheduled_tasks\manage_windows_tasks.bat enable
```

### Disable All Tasks
```batch
scripts\scheduled_tasks\manage_windows_tasks.bat disable
```

### Run Task Immediately
```batch
scripts\scheduled_tasks\manage_windows_tasks.bat run LinkedIn-Daily-Opportunity-Detection
```

### Remove All Tasks
```batch
scripts\scheduled_tasks\remove_windows_tasks.bat
```

## 📁 Task Files

### Batch Files (Windows Task Executors)
- `run_daily_opportunity_detection.bat`
- `run_daily_market_analysis.bat`
- `run_daily_network_insights.bat`
- `run_daily_summary.bat`
- `run_weekly_intelligence_orchestrator.bat`
- `run_weekly_predictive_analytics.bat`
- `run_biweekly_deep_analysis.bat`

### Python Scripts (Intelligence Engines)
- `daily_opportunity_detection.py`
- `daily_market_analysis.py`
- `daily_network_insights.py`
- `daily_summary.py`
- `weekly_intelligence_orchestrator.py`
- `weekly_predictive_analytics.py`
- `biweekly_deep_analysis.py`

## 🔧 Troubleshooting

### Task Creation Issues

1. **Permission Error:**
   - Run Command Prompt as Administrator
   - Ensure you have task scheduling permissions

2. **Virtual Environment Not Found:**
   - Verify `.venv` exists in project root
   - Run: `python -m venv .venv` if needed
   - Activate: `.venv\Scripts\activate`

3. **Path Issues:**
   - Ensure project is at: `C:\path\to\job_search_intelligence`
   - Update paths in batch files if different location

### Task Execution Issues

1. **Check Task Logs:**
   ```
   logs\daily_opportunity_detection.log
   logs\weekly_intelligence.log
   ```

2. **Test Individual Scripts:**
   ```batch
   .venv\Scripts\python.exe scripts\scheduled_tasks\daily_opportunity_detection.py
   ```

3. **Verify Dependencies:**
   ```batch
   .venv\Scripts\pip install -r requirements.txt
   ```

## 📈 Monitoring

### Task Scheduler GUI
1. Press `Win + R`, type `taskschd.msc`
2. Navigate to Task Scheduler Library
3. Look for tasks starting with "LinkedIn-"

### Command Line Monitoring
```batch
# Check all LinkedIn tasks
schtasks /query /tn "LinkedIn*" /fo table

# Check specific task
schtasks /query /tn "LinkedIn-Daily-Opportunity-Detection" /fo list

# View task history
schtasks /query /tn "LinkedIn-Daily-Opportunity-Detection" /v /fo list
```

## 🎯 Expected Output

### Daily Reports
- Opportunity detection reports in `reports/daily/`
- Market analysis summaries
- Network insights and metrics
- Comprehensive daily summaries

### Weekly Reports
- Intelligence orchestrator reports in `reports/weekly/`
- Predictive analytics forecasts
- Deep analysis insights

### Telegram Notifications
- Real-time task completion notifications
- Error alerts and status updates
- Weekly intelligence summaries

## 🛡️ Security Notes

1. **Task Privileges:** Tasks run with current user privileges
2. **Credential Storage:** No LinkedIn credentials stored in tasks
3. **Logging:** All activities logged for audit trail
4. **Error Handling:** Graceful failure with notification system

## 🔄 Maintenance

### Regular Checks
- Monitor logs weekly for errors
- Review task performance in Task Scheduler
- Update Python dependencies monthly

### Updates
- Re-run setup after code updates
- Check batch file paths after directory changes
- Restart tasks after system reboots

## 📞 Support

If you encounter issues:

1. Check logs in `logs/` directory
2. Run tasks manually to test
3. Verify virtual environment is working
4. Review Windows Event Viewer for system errors

## 🎉 Success Verification

After setup, you should see:

✅ 7 Job Search Intelligence tasks in Task Scheduler
✅ Tasks running at scheduled times
✅ Reports generated in `reports/` directory
✅ Telegram notifications (if configured)
✅ Log files updating with task execution

Your Job Search Intelligence is now fully automated! 🚀