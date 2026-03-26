# Enhanced Job Search Intelligence - Windows Task Scheduler Integration
# PowerShell Script for Advanced Windows Automation
# Author: Job Search Intelligence
# Last Updated: December 12, 2024

param(
    [string]$AnalysisType = "automated",
    [string]$LogLevel = "INFO",
    [switch]$SendNotification = $true
)

# Script configuration
$ProjectPath = "C:\path\to\job_search_intelligence"
$LogPath = "$ProjectPath\logs"
$VenvPath = "$ProjectPath\.venv"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = "$LogPath\windows_scheduler_$Timestamp.log"

# Ensure log directory exists
if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force
}

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$TimeStamp] [$Level] $Message"
    Write-Output $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry -Encoding UTF8
}

try {
    Write-Log "Starting Enhanced Job Search Intelligence Analysis via Windows Task Scheduler"
    # Sanitize AnalysisType in case quotes were passed through from Task Scheduler
    $AnalysisType = ($AnalysisType.Trim("'" )).Trim([char]34)
    Write-Log "Analysis Type: $AnalysisType"
    Write-Log "Project Path: $ProjectPath"
    
    # Change to project directory
    Set-Location $ProjectPath
    Write-Log "Changed directory to: $(Get-Location)"
    
# Set environment variables for Unicode support and run context
$env:PYTHONIOENCODING = "utf-8"
$env:LANG = "en_US.UTF-8"
$env:PYTHONPATH = $ProjectPath
$env:RUN_CONTEXT = "SCHEDULED"

# Allow real-data authentication only for Sunday comprehensive job
try {
    $etype = $AnalysisType.ToLower()
} catch { $etype = "" }
if ($etype -eq 'sunday_comprehensive') {
    $env:ALLOW_LI_AUTH_IN_SCHEDULED = "true"
    if (-not $env:LI_AUTH_TIMEOUT_SECONDS) { $env:LI_AUTH_TIMEOUT_SECONDS = "120" }
} else {
    $env:ALLOW_LI_AUTH_IN_SCHEDULED = "false"
}
    
    # Check for virtual environment
    $PythonCommand = "python"
    if (Test-Path "$VenvPath\Scripts\python.exe") {
        $PythonCommand = "$VenvPath\Scripts\python.exe"
        Write-Log "Using virtual environment Python: $PythonCommand"
    } else {
        Write-Log "Virtual environment not found, using system Python"
    }
    
    # Prepare Python analysis script (uses canonical report types)
    $PythonScript = @"
import asyncio
import sys
import os
from datetime import datetime
import traceback

# Add project root to path
sys.path.insert(0, r'$ProjectPath')

async def main():
    try:
        print('🚀 Enhanced Job Search Intelligence Analysis Starting...')
        
        from src.intelligence.integrated_job_search_intelligence import IntegratedLinkedInIntelligence
        
        # Initialize intelligence system
        intelligence = IntegratedLinkedInIntelligence()
        
        # Determine canonical report type (prefer provided AnalysisType)
        # Robustly strip any stray quotes and whitespace from injected value
        report_type = (r'$AnalysisType').strip().strip('\"\'').lower()
        valid = {'monday_deep_dive','wednesday_scan','friday_analysis','sunday_comprehensive','weekly_intelligence'}
        if report_type not in valid:
            day = datetime.now().strftime('%A').lower()
            if day == 'monday':
                report_type = 'monday_deep_dive'
            elif day == 'wednesday':
                report_type = 'wednesday_scan'
            elif day == 'friday':
                report_type = 'friday_analysis'
            elif day == 'sunday':
                report_type = 'sunday_comprehensive'
            else:
                report_type = 'weekly_intelligence'
        
        print(f"📊 Running automated analysis: {report_type}")
        results = await intelligence.run_weekly_analysis(report_type)
        
        if results:
            print('✅ Analysis completed successfully!')
            print(f"📁 Report files: {list((results.get('report_files') or {}).keys())}")
            # Telegram notification is handled inside the integrated system via AppConfig
        
        else:
            print('❌ Analysis failed or returned no results')
            raise Exception('Analysis returned no results')
            
    except Exception as e:
        print(f'❌ Critical error during analysis: {e}')
        traceback.print_exc()
        raise e

if __name__ == '__main__':
    asyncio.run(main())
"@
    
    # Save Python script to temporary file
    $TempScript = "$ProjectPath\temp_analysis_script.py"
    $PythonScript | Out-File -FilePath $TempScript -Encoding UTF8
    
    Write-Log "Executing Job Search Intelligence Analysis..."
    
    # Run the analysis
    $Process = Start-Process -FilePath $PythonCommand -ArgumentList $TempScript -Wait -PassThru -RedirectStandardOutput "$LogPath\python_output_$Timestamp.log" -RedirectStandardError "$LogPath\python_error_$Timestamp.log"
    
    if ($Process.ExitCode -eq 0) {
        Write-Log "Analysis completed successfully!" "SUCCESS"
        
    # Read Python output for logging with proper UTF-8 decoding
    $PythonOutput = Get-Content "$LogPath\python_output_$Timestamp.log" -Raw -Encoding UTF8
    Write-Log "Python Output: $PythonOutput"
        
    } else {
        Write-Log "Analysis failed with exit code: $($Process.ExitCode)" "ERROR"
        
        # Read error output
        $ErrorOutput = Get-Content "$LogPath\python_error_$Timestamp.log" -Raw
        Write-Log "Python Error: $ErrorOutput" "ERROR"
        
        throw "Analysis execution failed"
    }
    
} catch {
    Write-Log "Critical error in PowerShell script: $($_.Exception.Message)" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    
    # Send PowerShell error notification
    if ($SendNotification) {
        try {
            # Use Python to send error notification
            $ErrorScript = @"
import asyncio
import sys
sys.path.insert(0, r'$ProjectPath')

async def send_error():
    try:
        from scripts.intelligence_scheduler import TelegramNotifier, IntelligenceConfig
        notifier = TelegramNotifier(IntelligenceConfig())
        await notifier.send_message(
            '🚨 PowerShell Scheduler Error: $($_.Exception.Message)'
        )
    except Exception as e:
        print(f'Failed to send error notification: {e}')

asyncio.run(send_error())
"@
            $ErrorScript | Out-File -FilePath "$ProjectPath\temp_error_script.py" -Encoding UTF8
            & $PythonCommand "$ProjectPath\temp_error_script.py"
        } catch {
            Write-Log "Failed to send error notification: $($_.Exception.Message)" "ERROR"
        }
    }
    
    exit 1
    
} finally {
    # Cleanup temporary files
    if (Test-Path "$ProjectPath\temp_analysis_script.py") {
        Remove-Item "$ProjectPath\temp_analysis_script.py" -Force
    }
    if (Test-Path "$ProjectPath\temp_error_script.py") {
        Remove-Item "$ProjectPath\temp_error_script.py" -Force
    }
    
    Write-Log "Windows Task Scheduler execution completed"
    Write-Log "Log file: $LogFile"
}

# Return to original location
Pop-Location
