# Enhanced Job Search Intelligence - Windows Task Scheduler Setup
# Automated Task Creation and Configuration Script
# Author: Job Search Intelligence
# Last Updated: December 12, 2024

param(
    [switch]$Remove = $false,
    [switch]$Update = $false,
    [string]$UserName = $env:USERNAME
)

# Configuration
$TaskNamePrefix = "LinkedIn_Intelligence"
$ProjectPath = "C:\path\to\job_search_intelligence"
$ScriptPath = "$ProjectPath\scripts\windows_scheduler"
$LogPath = "$ProjectPath\logs\task_scheduler"

# Ensure directories exist
if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force
}
 
# Task definitions with enhanced scheduling
$Tasks = @(
    @{
        Name = "LinkedIn_Intelligence_Monday_DeepDive"
        Description = "Job Search Intelligence - Monday Deep Dive Analysis"
        Day = "Monday"
        Time = "09:00"
        Script = "$ScriptPath\run_analysis.ps1"
        Arguments = "-AnalysisType monday_deep_dive -SendNotification"
    },
    @{
        Name = "LinkedIn_Intelligence_Wednesday_MarketScan"
        Description = "Job Search Intelligence - Wednesday Market Scan"
        Day = "Wednesday" 
        Time = "12:00"
        Script = "$ScriptPath\run_analysis.ps1"
        Arguments = "-AnalysisType wednesday_scan -SendNotification"
    },
    @{
        Name = "LinkedIn_Intelligence_Friday_Predictive"
        Description = "Job Search Intelligence - Friday Predictive Analysis"
        Day = "Friday"
        Time = "17:00"
        Script = "$ScriptPath\run_analysis.ps1"
        Arguments = "-AnalysisType friday_analysis -SendNotification"
    },
    @{
        Name = "LinkedIn_Intelligence_Sunday_Comprehensive"
        Description = "Job Search Intelligence - Sunday Comprehensive Report"
        Day = "Sunday"
        Time = "10:00"
        Script = "$ScriptPath\run_analysis.ps1"
        Arguments = "-AnalysisType sunday_comprehensive -SendNotification"
    }
    ,
    @{
        Name = "LinkedIn_Intelligence_Weekly_Refresh"
        Description = "Job Search Intelligence - Weekly Real Data Refresh"
        Day = "Sunday"
        Time = "09:30"
        Script = "$ScriptPath\run_refresh.ps1"
        Arguments = "-TimeoutSeconds 180 -AllowAuth"
    },
    @{
        Name = "LinkedIn_Intelligence_Weekly_Content_Tracking"
        Description = "Job Search Intelligence - Weekly Content Tracking from LinkedIn Analytics Export"
        Day = "Sunday"
        Time = "11:30"
        Script = "$ProjectPath\scripts\scheduled_tasks\weekly_content_tracking.py"
        Arguments = ""
    }
)

# Logging function
function Write-SetupLog {
    param([string]$Message, [string]$Level = "INFO")
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$TimeStamp] [$Level] $Message"
    Write-Output $LogEntry
    Add-Content -Path "$LogPath\setup_$(Get-Date -Format 'yyyyMMdd').log" -Value $LogEntry
}

# Function to remove existing tasks
function Remove-LinkedInTasks {
    Write-SetupLog "Removing existing Job Search Intelligence tasks..."
    
    foreach ($Task in $Tasks) {
        try {
            if (Get-ScheduledTask -TaskName $Task.Name -ErrorAction SilentlyContinue) {
                Unregister-ScheduledTask -TaskName $Task.Name -Confirm:$false
                Write-SetupLog "Removed task: $($Task.Name)" "SUCCESS"
            } else {
                Write-SetupLog "Task not found: $($Task.Name)" "INFO"
            }
        } catch {
            Write-SetupLog "Error removing task $($Task.Name): $($_.Exception.Message)" "ERROR"
        }
    }
}

# Function to create scheduled tasks
function Create-LinkedInTasks {
    Write-SetupLog "Creating Job Search Intelligence scheduled tasks..."
    
    foreach ($Task in $Tasks) {
        try {
            Write-SetupLog "Creating task: $($Task.Name)"
            
            # Create task action
            if ($Task.Script.ToLower().EndsWith(".ps1")) {
                $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$($Task.Script)`" $($Task.Arguments)"
            } else {
                # Assume Python script for .py paths
                $PythonExe = "python"
                if (Test-Path "$ProjectPath\.venv\Scripts\python.exe") {
                    $PythonExe = "$ProjectPath\.venv\Scripts\python.exe"
                }
                $Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$($Task.Script)`" $($Task.Arguments)"
            }
            
            # Create task trigger (weekly on specific day)
            $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Task.Day -At $Task.Time
            
            # Create task settings
            $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
            
            # Create task principal (run with highest privileges)
            $Principal = New-ScheduledTaskPrincipal -UserId $UserName -LogonType Interactive -RunLevel Highest
            
            # Register the task
            Register-ScheduledTask -TaskName $Task.Name -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $Task.Description
            
            Write-SetupLog "Successfully created task: $($Task.Name)" "SUCCESS"
            Write-SetupLog "  Schedule: $($Task.Day) at $($Task.Time)"
            Write-SetupLog "  Script: $($Task.Script)"
            Write-SetupLog "  Arguments: $($Task.Arguments)"
            
        } catch {
            Write-SetupLog "Error creating task $($Task.Name): $($_.Exception.Message)" "ERROR"
        }
    }
}

# Function to test tasks
function Test-LinkedInTasks {
    Write-SetupLog "Testing Job Search Intelligence tasks..."
    
    foreach ($Task in $Tasks) {
        try {
            $ScheduledTask = Get-ScheduledTask -TaskName $Task.Name -ErrorAction SilentlyContinue
            
            if ($ScheduledTask) {
                Write-SetupLog "✅ Task found: $($Task.Name)" "SUCCESS"
                Write-SetupLog "  State: $($ScheduledTask.State)"
                Write-SetupLog "  Next Run: $($ScheduledTask.NextRunTime)"
                
                # Optional: Run task immediately for testing
                # Start-ScheduledTask -TaskName $Task.Name
                # Write-SetupLog "  Test execution triggered"
                
            } else {
                Write-SetupLog "❌ Task not found: $($Task.Name)" "ERROR"
            }
        } catch {
            Write-SetupLog "Error testing task $($Task.Name): $($_.Exception.Message)" "ERROR"
        }
    }
}

# Function to create monitoring task
function Create-MonitoringTask {
    Write-SetupLog "Creating system monitoring task..."
    
    try {
        $MonitoringScript = @"
# Job Search Intelligence Monitoring
`$LogPath = "$ProjectPath\logs"
`$ErrorThreshold = 5
`$RecentErrors = Get-ChildItem `$LogPath -Filter "*error*.log" | Where-Object { `$_.LastWriteTime -gt (Get-Date).AddHours(-24) }

if (`$RecentErrors.Count -gt `$ErrorThreshold) {
    # Send alert notification
    `$AlertScript = @'
import asyncio
import sys
sys.path.insert(0, r'$ProjectPath')

async def send_alert():
    try:
        from src.messaging.telegram_notifier import TelegramNotifier
        notifier = TelegramNotifier()
        await notifier.send_error_notification(
            '🚨 **System Alert**: High error rate detected in Job Search Intelligence. Please check logs.'
        )
    except Exception as e:
        print(f'Failed to send alert: {e}')

asyncio.run(send_alert())
'@
    
    `$AlertScript | Out-File -FilePath "`$LogPath\temp_alert.py" -Encoding UTF8
    python "`$LogPath\temp_alert.py"
    Remove-Item "`$LogPath\temp_alert.py" -Force
}
"@
        
        $MonitoringScript | Out-File -FilePath "$ScriptPath\monitoring.ps1" -Encoding UTF8
        
        # Create monitoring task (runs every 6 hours)
        $MonitorAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath\monitoring.ps1`""
        $MonitorTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6)
        $MonitorSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        $MonitorPrincipal = New-ScheduledTaskPrincipal -UserId $UserName -LogonType Interactive
        
        Register-ScheduledTask -TaskName "LinkedIn_Intelligence_Monitoring" -Action $MonitorAction -Trigger $MonitorTrigger -Settings $MonitorSettings -Principal $MonitorPrincipal -Description "Job Search Intelligence Monitoring"
        
        Write-SetupLog "✅ Monitoring task created successfully" "SUCCESS"
        
    } catch {
        Write-SetupLog "Error creating monitoring task: $($_.Exception.Message)" "ERROR"
    }
}

# Main execution
try {
    Write-SetupLog "Enhanced Job Search Intelligence - Windows Task Scheduler Setup"
    Write-SetupLog "Project Path: $ProjectPath"
    Write-SetupLog "Script Path: $ScriptPath"
    Write-SetupLog "User: $UserName"
    
    # Check if running as administrator
    if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        Write-SetupLog "WARNING: This script should be run as Administrator for best results" "WARNING"
    }
    
    # Validate script files exist
    if (!(Test-Path "$ScriptPath\run_analysis.ps1")) {
        Write-SetupLog "ERROR: Analysis script not found at $ScriptPath\run_analysis.ps1" "ERROR"
        exit 1
    }
    
    if ($Remove) {
        Write-SetupLog "REMOVE MODE: Removing all Job Search Intelligence tasks"
        Remove-LinkedInTasks
        
        # Remove monitoring task
        try {
            if (Get-ScheduledTask -TaskName "LinkedIn_Intelligence_Monitoring" -ErrorAction SilentlyContinue) {
                Unregister-ScheduledTask -TaskName "LinkedIn_Intelligence_Monitoring" -Confirm:$false
                Write-SetupLog "Removed monitoring task" "SUCCESS"
            }
        } catch {
            Write-SetupLog "Error removing monitoring task: $($_.Exception.Message)" "ERROR"
        }
        
    } elseif ($Update) {
        Write-SetupLog "UPDATE MODE: Updating existing tasks"
        Remove-LinkedInTasks
        Start-Sleep -Seconds 2
        Create-LinkedInTasks
        Create-MonitoringTask
        Test-LinkedInTasks
        
    } else {
        Write-SetupLog "CREATE MODE: Creating new tasks"
        Create-LinkedInTasks
        Create-MonitoringTask
        Test-LinkedInTasks
    }
    
    Write-SetupLog "Setup completed successfully!" "SUCCESS"
    Write-SetupLog "Next steps:"
    Write-SetupLog "1. Verify tasks in Task Scheduler (taskschd.msc)"
    Write-SetupLog "2. Test a task manually: Start-ScheduledTask -TaskName 'LinkedIn_Intelligence_Monday_DeepDive'"
    Write-SetupLog "3. Monitor logs in: $LogPath"
    
} catch {
    Write-SetupLog "Critical error during setup: $($_.Exception.Message)" "ERROR"
    Write-SetupLog "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
}

# Display summary
Write-Output ""
Write-Output "🎯 Enhanced Job Search Intelligence - Task Scheduler Setup Complete!"
Write-Output ""
Write-Output "📋 Created Tasks:"
foreach ($Task in $Tasks) {
    Write-Output "  • $($Task.Name) - $($Task.Day) at $($Task.Time)"
}
Write-Output "  • LinkedIn_Intelligence_Monitoring - Every 6 hours"
Write-Output ""
Write-Output "📁 Log Location: $LogPath"
Write-Output "⚙️ Task Manager: Run 'taskschd.msc' to view/manage tasks"
Write-Output "🧪 Test Command: Start-ScheduledTask -TaskName 'LinkedIn_Intelligence_Monday_DeepDive'"
