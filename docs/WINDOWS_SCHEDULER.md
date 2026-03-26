# Windows Task Scheduler Integration Guide

## 📋 **Overview**

The Enhanced Job Search Intelligence includes native Windows Task Scheduler integration for automated weekly analysis reports. This integration provides robust, system-level automation that runs independently of user sessions and includes comprehensive error handling and monitoring.

---

## 🎯 **Features**

### **✅ Automated Weekly Schedule**
- **Monday 9:00 AM**: Deep Dive Analysis
- **Wednesday 12:00 PM**: Mid-week Market Scan  
- **Friday 5:00 PM**: Predictive Weekend Analysis
- **Sunday 10:00 AM**: Comprehensive Weekly Report

### **✅ Advanced Capabilities**
- **Unicode-Safe Processing**: Full Unicode support for international names
- **Error Recovery**: Automatic retry mechanisms and fallback procedures
- **Telegram Integration**: Real-time notifications and report delivery
- **Comprehensive Logging**: Detailed execution logs with timestamps
- **System Monitoring**: Automatic error detection and alerting

---

## 🚀 **Quick Setup**

### **1. Run Setup Script**
```powershell
# Open PowerShell as Administrator
cd "C:\path\to\job_search_intelligence"
.\scripts\windows_scheduler\setup_windows_tasks.ps1
```

### **2. Verify Installation**
```powershell
# Check created tasks
Get-ScheduledTask -TaskName "LinkedIn_Intelligence*"

# Test a task manually
Start-ScheduledTask -TaskName "LinkedIn_Intelligence_Monday_DeepDive"
```

### **3. Monitor Execution**
```powershell
# View task history
Get-ScheduledTaskInfo -TaskName "LinkedIn_Intelligence_Monday_DeepDive"

# Check logs
Get-Content "logs\task_scheduler\setup_$(Get-Date -Format 'yyyyMMdd').log"
```

---

## 📁 **File Structure**

```
scripts/windows_scheduler/
├── 📄 setup_windows_tasks.ps1          # Main setup script
├── 📄 run_analysis.ps1                 # PowerShell analysis runner
├── 📄 run_weekly_analysis.bat          # Batch file alternative
├── 📄 monitoring.ps1                   # System monitoring script
└── 📄 README.md                        # This documentation
```

---

## ⚙️ **Configuration Options**

### **Environment Variables**
```powershell
# Set in PowerShell profile or system environment
$env:LINKEDIN_INTELLIGENCE_LOG_LEVEL = "INFO"    # DEBUG, INFO, WARNING, ERROR
$env:LINKEDIN_INTELLIGENCE_RETRY_COUNT = "3"     # Number of retry attempts
$env:LINKEDIN_INTELLIGENCE_TIMEOUT = "1800"      # Timeout in seconds (30 min)
```

### **Task Customization**
Edit `setup_windows_tasks.ps1` to modify:
- **Schedule Times**: Change the `Time` property in task definitions
- **Days**: Modify the `Day` property (Monday, Tuesday, etc.)
- **Arguments**: Add custom parameters to `Arguments` property

### **Example Customization**
```powershell
@{
    Name = "LinkedIn_Intelligence_Custom_Analysis"
    Description = "Custom LinkedIn Analysis"
    Day = "Tuesday"
    Time = "14:30"
    Script = "$ScriptPath\run_analysis.ps1"
    Arguments = "-AnalysisType 'custom_analysis' -LogLevel 'DEBUG' -SendNotification"
}
```

---

## 🔧 **Manual Management**

### **Create Tasks Manually**
```powershell
# Create a single task manually
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"c:\path\to\run_analysis.ps1`" -AnalysisType 'manual'"
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:00"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "LinkedIn_Custom" -Action $Action -Trigger $Trigger -Settings $Settings
```

### **Update Existing Tasks**
```powershell
# Update all tasks
.\scripts\windows_scheduler\setup_windows_tasks.ps1 -Update

# Remove all tasks
.\scripts\windows_scheduler\setup_windows_tasks.ps1 -Remove
```

### **Task Management Commands**
```powershell
# List all LinkedIn tasks
Get-ScheduledTask -TaskName "LinkedIn_Intelligence*"

# Start task immediately
Start-ScheduledTask -TaskName "LinkedIn_Intelligence_Monday_DeepDive"

# Stop running task
Stop-ScheduledTask -TaskName "LinkedIn_Intelligence_Monday_DeepDive"

# Get task execution history
Get-ScheduledTaskInfo -TaskName "LinkedIn_Intelligence_Monday_DeepDive"

# Export task for backup
Export-ScheduledTask -TaskName "LinkedIn_Intelligence_Monday_DeepDive" -TaskPath "\" | Out-File "linkedin_task_backup.xml"
```

---

## 📊 **Monitoring & Logging**

### **Log Locations**
```
logs/
├── task_scheduler/                      # Task scheduler logs
│   ├── setup_YYYYMMDD.log             # Setup execution logs
│   └── windows_scheduler_YYYYMMDD_HHMMSS.log  # Task execution logs
├── python_output_YYYYMMDD_HHMMSS.log  # Python script output
├── python_error_YYYYMMDD_HHMMSS.log   # Python script errors
└── linkedin_analysis_YYYYMMDD_HHMMSS.log  # Analysis logs
```

### **Monitoring Dashboard**
```powershell
# View recent task executions
Get-ScheduledTask -TaskName "LinkedIn_Intelligence*" | ForEach-Object {
    $Info = Get-ScheduledTaskInfo -TaskName $_.TaskName
    [PSCustomObject]@{
        TaskName = $_.TaskName
        State = $_.State
        LastRunTime = $Info.LastRunTime
        LastTaskResult = $Info.LastTaskResult
        NextRunTime = $Info.NextRunTime
    }
} | Format-Table -AutoSize
```

### **Error Monitoring**
The system includes automatic monitoring that:
- Checks for errors every 6 hours
- Sends Telegram alerts for high error rates
- Logs all execution details
- Provides detailed error reporting

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Task Not Running**
```powershell
# Check task state
Get-ScheduledTask -TaskName "LinkedIn_Intelligence_Monday_DeepDive"

# Check last run result (0 = success)
(Get-ScheduledTaskInfo -TaskName "LinkedIn_Intelligence_Monday_DeepDive").LastTaskResult

# Enable task history
wevtutil sl Microsoft-Windows-TaskScheduler/Operational /e:true
```

#### **Python Script Errors**
```powershell
# Check Python output logs
Get-Content "logs\python_error_*.log" | Select-Object -Last 50

# Test Python script manually
cd "C:\path\to\job_search_intelligence"
python -c "import sys; sys.path.insert(0, '.'); from src.intelligence.integrated_job_search_intelligence import IntegratedLinkedInIntelligence; print('Import successful')"
```

#### **Permission Issues**
```powershell
# Run setup as Administrator
Start-Process PowerShell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File .\scripts\windows_scheduler\setup_windows_tasks.ps1"

# Check execution policy
Get-ExecutionPolicy
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **Unicode Issues**
```powershell
# Verify Unicode environment variables
$env:PYTHONIOENCODING
$env:LANG

# Set if missing
$env:PYTHONIOENCODING = "utf-8"
$env:LANG = "en_US.UTF-8"
```

### **Diagnostic Commands**
```powershell
# Full system diagnostic
.\scripts\windows_scheduler\run_analysis.ps1 -AnalysisType "diagnostic" -LogLevel "DEBUG"

# Test Telegram integration
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from scripts.intelligence_scheduler import TelegramNotifier, IntelligenceConfig

async def test():
    notifier = TelegramNotifier(IntelligenceConfig())
    await notifier.send_message('✅ Windows Task Scheduler Integration Test')

asyncio.run(test())
"
```

---

## 📈 **Performance Optimization**

### **System Requirements**
- **RAM**: Minimum 4GB, Recommended 8GB+
- **CPU**: Any modern processor (analysis typically uses 1-2 cores)
- **Storage**: 1GB free space for logs and reports
- **Network**: Stable internet connection for LinkedIn and Telegram APIs

### **Optimization Tips**
1. **Schedule During Off-Hours**: Avoid peak system usage times
2. **Monitor Resource Usage**: Use Task Manager during execution
3. **Regular Cleanup**: Archive old logs and reports monthly
4. **Virtual Environment**: Use isolated Python environment
5. **SSD Storage**: Store project on SSD for faster execution

### **Resource Monitoring**
```powershell
# Monitor task performance
Get-Process python | Select-Object ProcessName, CPU, WorkingSet, VirtualMemorySize

# Check disk usage
Get-ChildItem "C:\path\to\job_search_intelligence" -Recurse | Measure-Object -Property Length -Sum
```

---

## 🔒 **Security Considerations**

### **Best Practices**
1. **Credential Storage**: Use secure `.env` file with appropriate permissions
2. **Script Permissions**: Limit script execution to specific users
3. **Log Security**: Protect log files containing sensitive information
4. **Network Security**: Ensure HTTPS connections for all APIs
5. **Regular Updates**: Keep Python packages and dependencies updated

### **Security Commands**
```powershell
# Set secure file permissions on .env
icacls ".env" /grant:r "$env:USERNAME:(R)" /inheritance:r

# Check script permissions
Get-Acl "scripts\windows_scheduler\*.ps1"

# Secure log directory
icacls "logs" /grant:r "$env:USERNAME:(F)" /inheritance:r
```

---

## 📚 **Advanced Usage**

### **Custom Analysis Types**
Create custom analysis by modifying the PowerShell script:

```powershell
# Add to run_analysis.ps1
param(
    [string]$AnalysisType = "automated",
    [string]$CustomFilter = "",
    [int]$DaysBack = 7,
    [switch]$IncludeArchived = $false
)

# Pass parameters to Python script
$PythonScript = @"
# Use custom parameters in analysis
analysis_config = {
    'type': '$AnalysisType',
    'filter': '$CustomFilter',
    'days_back': $DaysBack,
    'include_archived': $IncludeArchived
}
"@
```

### **Integration with Other Systems**
```powershell
# Export results to CSV for external tools
$ExportScript = @"
# After analysis completion
import pandas as pd
results_df = pd.DataFrame(results)
results_df.to_csv(f'exports/analysis_{datetime.now().strftime("%Y%m%d")}.csv')
"@
```

### **Backup and Recovery**
```powershell
# Backup all tasks
Get-ScheduledTask -TaskName "LinkedIn_Intelligence*" | ForEach-Object {
    Export-ScheduledTask -TaskName $_.TaskName | Out-File "backups\$($_.TaskName)_backup.xml"
}

# Restore from backup
Register-ScheduledTask -Xml (Get-Content "backups\LinkedIn_Intelligence_Monday_DeepDive_backup.xml" | Out-String) -TaskName "LinkedIn_Intelligence_Monday_DeepDive"
```

---

## 📞 **Support**

### **Getting Help**
- **Documentation**: Check `docs/` folder for additional guides
- **Logs**: Always check logs first for error details
- **Telegram**: Error notifications include troubleshooting hints
- **Task Scheduler**: Use `eventvwr.msc` to view detailed task execution logs

### **Common Solutions**
- **Task Fails to Start**: Check user permissions and execution policy
- **Python Import Errors**: Verify virtual environment and dependencies
- **Unicode Errors**: Ensure proper environment variable configuration
- **Network Issues**: Check LinkedIn and Telegram API connectivity

---

**🎯 Enhanced Job Search Intelligence**  
*Native Windows Task Scheduler Integration*

**Last Updated**: December 12, 2024  
**Version**: 2.0 (Enhanced Production Release)  
**Status**: 🟢 **Fully Operational** with robust error handling and monitoring
