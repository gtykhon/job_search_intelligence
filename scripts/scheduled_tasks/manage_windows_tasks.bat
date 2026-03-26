@echo off
REM Job Search Intelligence - Task Management Script
REM Lists and manages Job Search Intelligence scheduled tasks

setlocal enabledelayedexpansion

if "%1"=="" goto :show_usage
if "%1"=="list" goto :list_tasks
if "%1"=="status" goto :show_status
if "%1"=="enable" goto :enable_tasks
if "%1"=="disable" goto :disable_tasks
if "%1"=="run" goto :run_task
goto :show_usage

:show_usage
echo.
echo ============================================================
echo  Job Search Intelligence - Task Management
echo ============================================================
echo.
echo Usage: %0 [command] [task_name]
echo.
echo Commands:
echo   list     - List all Job Search Intelligence tasks
echo   status   - Show detailed status of all tasks
echo   enable   - Enable all Job Search Intelligence tasks
echo   disable  - Disable all Job Search Intelligence tasks
echo   run      - Run a specific task now (requires task name)
echo.
echo Examples:
echo   %0 list
echo   %0 status
echo   %0 enable
echo   %0 disable
echo   %0 run LinkedIn-Daily-Opportunity-Detection
echo.
goto :end

:list_tasks
echo.
echo 📋 Job Search Intelligence Scheduled Tasks:
echo ============================================================
schtasks /query /tn "LinkedIn*" /fo table
echo.
goto :end

:show_status
echo.
echo 📊 Job Search Intelligence Task Status:
echo ============================================================
echo.

REM List of all Job Search Intelligence task names
set TASKS=LinkedIn-Daily-Opportunity-Detection LinkedIn-Daily-Market-Analysis LinkedIn-Daily-Network-Insights LinkedIn-Daily-Summary LinkedIn-Weekly-Intelligence LinkedIn-Weekly-Predictive-Analytics LinkedIn-Biweekly-Deep-Analysis

for %%T in (%TASKS%) do (
    echo Checking: %%T
    schtasks /query /tn "%%T" /fo list | findstr /C:"Task Name" /C:"Status" /C:"Next Run Time" /C:"Last Run Time"
    echo.
)
goto :end

:enable_tasks
echo.
echo ✅ Enabling all Job Search Intelligence tasks...
echo ============================================================

set TASKS=LinkedIn-Daily-Opportunity-Detection LinkedIn-Daily-Market-Analysis LinkedIn-Daily-Network-Insights LinkedIn-Daily-Summary LinkedIn-Weekly-Intelligence LinkedIn-Weekly-Predictive-Analytics LinkedIn-Biweekly-Deep-Analysis

for %%T in (%TASKS%) do (
    echo Enabling: %%T
    schtasks /change /tn "%%T" /enable >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Enabled: %%T
    ) else (
        echo ❌ Failed to enable: %%T
    )
)
echo.
echo 🎉 All tasks enabled!
goto :end

:disable_tasks
echo.
echo ⏸️  Disabling all Job Search Intelligence tasks...
echo ============================================================

set TASKS=LinkedIn-Daily-Opportunity-Detection LinkedIn-Daily-Market-Analysis LinkedIn-Daily-Network-Insights LinkedIn-Daily-Summary LinkedIn-Weekly-Intelligence LinkedIn-Weekly-Predictive-Analytics LinkedIn-Biweekly-Deep-Analysis

for %%T in (%TASKS%) do (
    echo Disabling: %%T
    schtasks /change /tn "%%T" /disable >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Disabled: %%T
    ) else (
        echo ❌ Failed to disable: %%T
    )
)
echo.
echo 🎉 All tasks disabled!
goto :end

:run_task
if "%2"=="" (
    echo ❌ Error: Task name required for run command
    echo Usage: %0 run [task_name]
    echo Example: %0 run LinkedIn-Daily-Opportunity-Detection
    goto :end
)

echo.
echo 🚀 Running task: %2
echo ============================================================
schtasks /run /tn "%2"
if !errorlevel! equ 0 (
    echo ✅ Task started successfully: %2
    echo.
    echo 📊 You can check the task status with:
    echo   %0 status
) else (
    echo ❌ Failed to start task: %2
    echo.
    echo 💡 Available tasks:
    schtasks /query /tn "LinkedIn*" /fo table
)
goto :end

:end
echo.
pause