#!/usr/bin/env pwsh
# Windows Task Scheduler wrapper for manual real data refresh

param(
    [int]$TimeoutSeconds = 180,
    [switch]$AllowAuth = $true,
    [switch]$Manual = $false
)

$ProjectPath = "C:\path\to\job_search_intelligence"
$LogPath = "$ProjectPath\logs"
$VenvPath = "$ProjectPath\.venv"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = "$LogPath\windows_refresh_$Timestamp.log"

if (!(Test-Path $LogPath)) { New-Item -ItemType Directory -Path $LogPath -Force }

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Line = "[$TimeStamp] [$Level] $Message"
    Write-Output $Line
    Add-Content -Path $LogFile -Value $Line -Encoding UTF8
}

try {
    Write-Log "Starting LinkedIn real data refresh"
    Set-Location $ProjectPath
    $env:PYTHONIOENCODING = "utf-8"
    $env:LANG = "en_US.UTF-8"
    $env:PYTHONPATH = $ProjectPath
    $env:RUN_CONTEXT = "SCHEDULED"

    $Python = "python"
    if (Test-Path "$VenvPath\Scripts\python.exe") { $Python = "$VenvPath\Scripts\python.exe" }

    $argsList = @("scripts/refresh_real_data.py", "--force", "--timeout", $TimeoutSeconds)
    if ($AllowAuth) { $argsList += "--allow-auth" }
    if ($Manual) { $argsList += "--manual" }

    Write-Log "Executing: $Python $($argsList -join ' ')"
    $proc = Start-Process -FilePath $Python -ArgumentList $argsList -Wait -PassThru -RedirectStandardOutput "$LogPath\refresh_out_$Timestamp.log" -RedirectStandardError "$LogPath\refresh_err_$Timestamp.log"
    if ($proc.ExitCode -eq 0) {
        Write-Log "Refresh completed successfully" "SUCCESS"
        $out = Get-Content "$LogPath\refresh_out_$Timestamp.log" -Raw -Encoding UTF8
        Write-Log "Output: $out"
    } else {
        Write-Log "Refresh failed with exit code $($proc.ExitCode)" "ERROR"
        $err = Get-Content "$LogPath\refresh_err_$Timestamp.log" -Raw
        Write-Log "Error: $err" "ERROR"
        throw "Refresh failed"
    }
}
catch {
    Write-Log "Critical error: $($_.Exception.Message)" "ERROR"
    exit 1
}
finally {
    Write-Log "Windows refresh task completed"
}

