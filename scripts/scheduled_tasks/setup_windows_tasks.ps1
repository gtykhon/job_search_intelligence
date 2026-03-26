# Job Search Intelligence - Windows Task Scheduler Setup
# Run this PowerShell script as Administrator to create all scheduled tasks

param(
    [switch]$Remove,
    [switch]$List
)

# Configuration
$ProjectPath = "C:\path\to\job_search_intelligence"
$TasksPath = "$ProjectPath\scripts\scheduled_tasks"

# Task definitions
$Tasks = @(
    @{
        Name = "LinkedIn-Daily-Opportunity-Detection"
        Description = "Daily LinkedIn opportunity detection and reporting"
        BatchFile = "$TasksPath\run_daily_opportunity_detection.bat"
        Schedule = "Daily"
        Time = "06:00"
        Days = $null
    },
    @{
        Name = "LinkedIn-Daily-Market-Analysis"
        Description = "Daily market analysis and trend reporting"
        BatchFile = "$TasksPath\run_daily_market_analysis.bat"
        Schedule = "Daily"
        Time = "10:00"
        Days = $null
    },
    @{
        Name = "LinkedIn-Weekly-Intelligence"
        Description = "Weekly intelligence orchestrator and comprehensive reporting"
        BatchFile = "$TasksPath\run_weekly_intelligence_orchestrator.bat"
        Schedule = "Weekly"
        Time = "08:00"
        Days = "Monday"
    }
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Remove-LinkedInTasks {
    Write-ColorOutput "🗑️  Removing Job Search Intelligence scheduled tasks..." "Yellow"
    
    foreach ($task in $Tasks) {
        try {
            $existingTask = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
            if ($existingTask) {
                Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
                Write-ColorOutput "   ✅ Removed: $($task.Name)" "Green"
            } else {
                Write-ColorOutput "   ⚠️  Not found: $($task.Name)" "Gray"
            }
        }
        catch {
            Write-ColorOutput "   ❌ Failed to remove: $($task.Name) - $($_.Exception.Message)" "Red"
        }
    }
}

function List-LinkedInTasks {
    Write-ColorOutput "📋 Job Search Intelligence scheduled tasks:" "Cyan"
    
    foreach ($task in $Tasks) {
        try {
            $existingTask = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
            if ($existingTask) {
                $state = $existingTask.State
                $nextRun = (Get-ScheduledTask -TaskName $task.Name | Get-ScheduledTaskInfo).NextRunTime
                Write-ColorOutput "   ✅ $($task.Name)" "Green"
                Write-ColorOutput "      State: $state" "Gray"
                Write-ColorOutput "      Next Run: $nextRun" "Gray"
                Write-ColorOutput "      Description: $($task.Description)" "Gray"
            } else {
                Write-ColorOutput "   ❌ $($task.Name) - Not scheduled" "Red"
            }
        }
        catch {
            Write-ColorOutput "   ❌ Error checking: $($task.Name)" "Red"
        }
    }
}

function Create-LinkedInTasks {
    Write-ColorOutput "🤖 Job Search Intelligence - Task Scheduler Setup" "Cyan"
    Write-ColorOutput "=" * 60 "Gray"
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-ColorOutput "❌ This script must be run as Administrator to create scheduled tasks." "Red"
        Write-ColorOutput "   Right-click PowerShell and select 'Run as Administrator'" "Yellow"
        exit 1
    }
    
    # Verify project path exists
    if (-not (Test-Path $ProjectPath)) {
        Write-ColorOutput "❌ Project path not found: $ProjectPath" "Red"
        Write-ColorOutput "   Please update the `$ProjectPath variable in this script." "Yellow"
        exit 1
    }
    
    Write-ColorOutput "📂 Project Path: $ProjectPath" "Green"
    Write-ColorOutput "📅 Creating scheduled tasks..." "Yellow"
    Write-ColorOutput ""
    
    foreach ($task in $Tasks) {
        try {
            Write-ColorOutput "Creating task: $($task.Name)..." "White"
            
            # Check if batch file exists
            if (-not (Test-Path $task.BatchFile)) {
                Write-ColorOutput "   ❌ Batch file not found: $($task.BatchFile)" "Red"
                continue
            }
            
            # Remove existing task if it exists
            $existingTask = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
            if ($existingTask) {
                Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
                Write-ColorOutput "   🗑️  Removed existing task" "Yellow"
            }
            
            # Create action
            $action = New-ScheduledTaskAction -Execute $task.BatchFile
            
            # Create trigger based on schedule type
            if ($task.Schedule -eq "Daily") {
                $trigger = New-ScheduledTaskTrigger -Daily -At $task.Time
            }
            elseif ($task.Schedule -eq "Weekly") {
                $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $task.Days -At $task.Time
            }
            
            # Create principal (run as current user)
            $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
            
            # Create settings
            $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
            
            # Register the task
            Register-ScheduledTask -TaskName $task.Name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $task.Description
            
            Write-ColorOutput "   ✅ Created successfully" "Green"
            Write-ColorOutput "   📅 Schedule: $($task.Schedule) at $($task.Time)" "Gray"
            if ($task.Days) {
                Write-ColorOutput "   📆 Days: $($task.Days)" "Gray"
            }
            
        }
        catch {
            Write-ColorOutput "   ❌ Failed to create task: $($_.Exception.Message)" "Red"
        }
        
        Write-ColorOutput ""
    }
    
    Write-ColorOutput "🎉 Task creation completed!" "Green"
    Write-ColorOutput ""
    Write-ColorOutput "📋 To view your tasks:" "Cyan"
    Write-ColorOutput "   • Open Task Scheduler (taskschd.msc)" "Gray"
    Write-ColorOutput "   • Or run: .\setup_windows_tasks.ps1 -List" "Gray"
    Write-ColorOutput ""
    Write-ColorOutput "🗑️  To remove all tasks:" "Cyan"
    Write-ColorOutput "   • Run: .\setup_windows_tasks.ps1 -Remove" "Gray"
    Write-ColorOutput ""
    Write-ColorOutput "📊 Task Schedule Summary:" "Yellow"
    Write-ColorOutput "   • 6:00 AM Daily - Opportunity Detection" "Gray"
    Write-ColorOutput "   • 10:00 AM Daily - Market Analysis" "Gray"
    Write-ColorOutput "   • 8:00 AM Monday - Weekly Intelligence" "Gray"
}

# Main execution
try {
    if ($Remove) {
        Remove-LinkedInTasks
    }
    elseif ($List) {
        List-LinkedInTasks
    }
    else {
        Create-LinkedInTasks
    }
}
catch {
    Write-ColorOutput "❌ Script execution failed: $($_.Exception.Message)" "Red"
    exit 1
}