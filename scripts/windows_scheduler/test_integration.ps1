# Windows Task Scheduler Integration Test
# Quick validation script for Job Search Intelligence automation
# Author: Job Search Intelligence
# Last Updated: December 12, 2024

param(
    [switch]$QuickTest = $false,
    [switch]$FullTest = $false,
    [switch]$SetupOnly = $false
)

$ProjectPath = "C:\path\to\job_search_intelligence"
$ScriptPath = "$ProjectPath\scripts\windows_scheduler"

# Logging function
function Write-TestLog {
    param([string]$Message, [string]$Level = "INFO")
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$TimeStamp] [$Level] $Message"
    Write-Output $LogEntry
}

function Test-Prerequisites {
    Write-TestLog "Testing prerequisites..."
    
    $Passed = $true
    
    # Check project directory
    if (!(Test-Path $ProjectPath)) {
        Write-TestLog "❌ Project directory not found: $ProjectPath" "ERROR"
        $Passed = $false
    } else {
        Write-TestLog "✅ Project directory found" "SUCCESS"
    }
    
    # Check script files
    $RequiredFiles = @(
        "$ScriptPath\setup_windows_tasks.ps1",
        "$ScriptPath\run_analysis.ps1",
        "$ScriptPath\run_weekly_analysis.bat"
    )
    
    foreach ($File in $RequiredFiles) {
        if (!(Test-Path $File)) {
            Write-TestLog "❌ Required file missing: $File" "ERROR"
            $Passed = $false
        } else {
            Write-TestLog "✅ File found: $(Split-Path $File -Leaf)" "SUCCESS"
        }
    }
    
    # Check Python availability
    try {
        $PythonVersion = python --version 2>&1
        Write-TestLog "✅ Python available: $PythonVersion" "SUCCESS"
    } catch {
        Write-TestLog "❌ Python not available or not in PATH" "ERROR"
        $Passed = $false
    }
    
    # Check virtual environment
    if (Test-Path "$ProjectPath\.venv\Scripts\python.exe") {
        Write-TestLog "✅ Virtual environment found" "SUCCESS"
    } else {
        Write-TestLog "⚠️ Virtual environment not found, using system Python" "WARNING"
    }
    
    # Test Python imports
    try {
        Set-Location $ProjectPath
        $ImportTest = python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.intelligence.integrated_job_search_intelligence import IntegratedLinkedInIntelligence
    from scripts.intelligence_scheduler import TelegramNotifier, IntelligenceConfig
    print('SUCCESS: All imports successful')
except ImportError as e:
    print(f'ERROR: Import failed - {e}')
except Exception as e:
    print(f'ERROR: Unexpected error - {e}')
" 2>&1
        
        if ($ImportTest -match "SUCCESS") {
            Write-TestLog "✅ Python imports successful" "SUCCESS"
        } else {
            Write-TestLog "❌ Python import test failed: $ImportTest" "ERROR"
            $Passed = $false
        }
    } catch {
        Write-TestLog "❌ Python import test failed: $($_.Exception.Message)" "ERROR"
        $Passed = $false
    }
    
    return $Passed
}

function Test-TaskCreation {
    Write-TestLog "Testing task creation..."
    
    try {
        # Run setup script in test mode (create but don't schedule)
        $SetupResult = & "$ScriptPath\setup_windows_tasks.ps1" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-TestLog "✅ Task creation script executed successfully" "SUCCESS"
            
            # Verify tasks were created
            $CreatedTasks = Get-ScheduledTask -TaskName "LinkedIn_Intelligence*" -ErrorAction SilentlyContinue
            
            if ($CreatedTasks.Count -gt 0) {
                Write-TestLog "✅ Tasks created successfully: $($CreatedTasks.Count) tasks" "SUCCESS"
                
                foreach ($Task in $CreatedTasks) {
                    Write-TestLog "  • $($Task.TaskName) - State: $($Task.State)"
                }
                
                return $true
            } else {
                Write-TestLog "❌ No tasks were created" "ERROR"
                return $false
            }
        } else {
            Write-TestLog "❌ Task creation failed: $SetupResult" "ERROR"
            return $false
        }
    } catch {
        Write-TestLog "❌ Error during task creation test: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-TaskExecution {
    Write-TestLog "Testing task execution..."
    
    try {
        # Get a test task
        $TestTask = Get-ScheduledTask -TaskName "LinkedIn_Intelligence_Monday_DeepDive" -ErrorAction SilentlyContinue
        
        if ($TestTask) {
            Write-TestLog "Running test execution of: $($TestTask.TaskName)"
            
            # Start the task
            Start-ScheduledTask -TaskName $TestTask.TaskName
            
            # Wait a moment for execution to begin
            Start-Sleep -Seconds 5
            
            # Check task info
            $TaskInfo = Get-ScheduledTaskInfo -TaskName $TestTask.TaskName
            Write-TestLog "Task last run time: $($TaskInfo.LastRunTime)"
            Write-TestLog "Task last result: $($TaskInfo.LastTaskResult)"
            
            # Wait for completion (max 60 seconds)
            $Timeout = 60
            $Elapsed = 0
            
            do {
                Start-Sleep -Seconds 5
                $Elapsed += 5
                $TaskInfo = Get-ScheduledTaskInfo -TaskName $TestTask.TaskName
                Write-TestLog "Waiting for task completion... ($Elapsed/$Timeout seconds)"
            } while ($TaskInfo.LastTaskResult -eq 267009 -and $Elapsed -lt $Timeout)  # 267009 = Task is running
            
            if ($TaskInfo.LastTaskResult -eq 0) {
                Write-TestLog "✅ Task executed successfully!" "SUCCESS"
                return $true
            } else {
                Write-TestLog "❌ Task execution failed with result: $($TaskInfo.LastTaskResult)" "ERROR"
                return $false
            }
        } else {
            Write-TestLog "❌ Test task not found" "ERROR"
            return $false
        }
    } catch {
        Write-TestLog "❌ Error during task execution test: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-LogGeneration {
    Write-TestLog "Testing log generation..."
    
    # Check if logs directory exists
    $LogsPath = "$ProjectPath\logs"
    if (!(Test-Path $LogsPath)) {
        Write-TestLog "❌ Logs directory not found: $LogsPath" "ERROR"
        return $false
    }
    
    # Check for recent log files
    $RecentLogs = Get-ChildItem $LogsPath -Recurse -Filter "*.log" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
    
    if ($RecentLogs.Count -gt 0) {
        Write-TestLog "✅ Found $($RecentLogs.Count) recent log files" "SUCCESS"
        
        foreach ($Log in $RecentLogs | Select-Object -First 3) {
            Write-TestLog "  • $($Log.Name) - Size: $([math]::Round($Log.Length/1KB, 2)) KB"
        }
        
        return $true
    } else {
        Write-TestLog "⚠️ No recent log files found" "WARNING"
        return $false
    }
}

function Cleanup-TestTasks {
    Write-TestLog "Cleaning up test tasks..."
    
    try {
        $TestTasks = Get-ScheduledTask -TaskName "LinkedIn_Intelligence*" -ErrorAction SilentlyContinue
        
        foreach ($Task in $TestTasks) {
            Unregister-ScheduledTask -TaskName $Task.TaskName -Confirm:$false
            Write-TestLog "Removed task: $($Task.TaskName)"
        }
        
        Write-TestLog "✅ Cleanup completed" "SUCCESS"
    } catch {
        Write-TestLog "❌ Error during cleanup: $($_.Exception.Message)" "ERROR"
    }
}

# Main execution
try {
    Write-TestLog "🧪 Windows Task Scheduler Integration Test"
    Write-TestLog "Project: Enhanced Job Search Intelligence"
    Write-TestLog "Test Mode: $(if($QuickTest){'Quick'}elseif($FullTest){'Full'}elseif($SetupOnly){'Setup Only'}else{'Interactive'})"
    Write-TestLog ""
    
    $AllPassed = $true
    
    # Prerequisites test
    Write-TestLog "=== PREREQUISITES TEST ==="
    if (!(Test-Prerequisites)) {
        $AllPassed = $false
        Write-TestLog "❌ Prerequisites test failed" "ERROR"
        
        if (!$FullTest) {
            Write-TestLog "Stopping due to prerequisite failures"
            exit 1
        }
    }
    
    # Setup test
    if (!$QuickTest) {
        Write-TestLog ""
        Write-TestLog "=== SETUP TEST ==="
        if (!(Test-TaskCreation)) {
            $AllPassed = $false
            Write-TestLog "❌ Task creation test failed" "ERROR"
        }
    }
    
    # Execution test (only in full test mode)
    if ($FullTest) {
        Write-TestLog ""
        Write-TestLog "=== EXECUTION TEST ==="
        if (!(Test-TaskExecution)) {
            $AllPassed = $false
            Write-TestLog "❌ Task execution test failed" "ERROR"
        }
        
        Write-TestLog ""
        Write-TestLog "=== LOG GENERATION TEST ==="
        if (!(Test-LogGeneration)) {
            Write-TestLog "⚠️ Log generation test had issues" "WARNING"
        }
    }
    
    # Cleanup (unless setup only)
    if (!$SetupOnly -and !$QuickTest) {
        Write-TestLog ""
        Write-TestLog "=== CLEANUP ==="
        Cleanup-TestTasks
    }
    
    # Final result
    Write-TestLog ""
    Write-TestLog "=== TEST RESULTS ==="
    if ($AllPassed) {
        Write-TestLog "🎉 ALL TESTS PASSED!" "SUCCESS"
        Write-TestLog "Windows Task Scheduler integration is ready for production use."
    } else {
        Write-TestLog "❌ SOME TESTS FAILED" "ERROR"
        Write-TestLog "Please review the errors above and fix issues before production use."
        exit 1
    }
    
} catch {
    Write-TestLog "💥 Critical error during testing: $($_.Exception.Message)" "ERROR"
    Write-TestLog "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
}

Write-TestLog ""
Write-TestLog "Test completed at: $(Get-Date)"
Write-TestLog "To run production setup: .\scripts\windows_scheduler\setup_windows_tasks.ps1"
