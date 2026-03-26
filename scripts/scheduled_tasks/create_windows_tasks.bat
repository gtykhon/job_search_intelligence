@echo off
REM Job Search Intelligence - Windows Task Scheduler Setup
REM Creates scheduled tasks for automated intelligence gathering
REM Run this script to set up all automation tasks

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  Job Search Intelligence - Task Scheduler Setup
echo ============================================================
echo.

REM Get current directory
set "PROJECT_DIR=%~dp0..\.."
set "TASKS_DIR=%PROJECT_DIR%\scripts\scheduled_tasks"

echo 📂 Project Directory: %PROJECT_DIR%
echo 📂 Tasks Directory: %TASKS_DIR%
echo.

REM Check if project directory exists
if not exist "%PROJECT_DIR%" (
    echo ❌ Project directory not found: %PROJECT_DIR%
    echo Please run this script from the correct location.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo ❌ Virtual environment not found: %PROJECT_DIR%\.venv
    echo Please ensure the Python virtual environment is set up.
    pause
    exit /b 1
)

echo 🤖 Creating Job Search Intelligence scheduled tasks...
echo.

REM Task 1: Daily Opportunity Detection (6:00 AM)
echo Creating: LinkedIn-Daily-Opportunity-Detection
schtasks /create /tn "LinkedIn-Daily-Opportunity-Detection" /tr "\"%TASKS_DIR%\run_daily_opportunity_detection.bat\"" /sc daily /st 06:00 /f /rl highest
if !errorlevel! equ 0 (
    echo ✅ Created: Daily Opportunity Detection at 6:00 AM
) else (
    echo ❌ Failed to create: Daily Opportunity Detection
)
echo.

REM Task 2: Daily Market Analysis (10:00 AM)
echo Creating: LinkedIn-Daily-Market-Analysis
schtasks /create /tn "LinkedIn-Daily-Market-Analysis" /tr "\"%TASKS_DIR%\run_daily_market_analysis.bat\"" /sc daily /st 10:00 /f /rl highest
if !errorlevel! equ 0 (
    echo ✅ Created: Daily Market Analysis at 10:00 AM
) else (
    echo ❌ Failed to create: Daily Market Analysis
)
echo.

REM Task 3: Daily Network Insights (2:00 PM)
echo Creating: LinkedIn-Daily-Network-Insights
schtasks /create /tn "LinkedIn-Daily-Network-Insights" /tr "\"%TASKS_DIR%\run_daily_network_insights.bat\"" /sc daily /st 14:00 /f /rl highest
if !errorlevel! equ 0 (
    echo ✅ Created: Daily Network Insights at 2:00 PM
) else (
    echo ❌ Failed to create: Daily Network Insights
)
echo.

REM Task 4: Daily Summary Report (6:00 PM)
echo Creating: LinkedIn-Daily-Summary
schtasks /create /tn "LinkedIn-Daily-Summary" /tr "\"%TASKS_DIR%\run_daily_summary.bat\"" /sc daily /st 18:00 /f /rl highest
if !errorlevel! equ 0 (
    echo ✅ Created: Daily Summary at 6:00 PM
) else (
    echo ❌ Failed to create: Daily Summary
)
echo.

REM Task 5: Weekly Intelligence Orchestrator (Monday 8:00 AM)
echo Creating: LinkedIn-Weekly-Intelligence
schtasks /create /tn "LinkedIn-Weekly-Intelligence" /tr "\"%TASKS_DIR%\run_weekly_intelligence_orchestrator.bat\"" /sc weekly /d MON /st 08:00 /f /rl highest
if !errorlevel! equ 0 (
    echo ✅ Created: Weekly Intelligence on Monday at 8:00 AM
) else (
    echo ❌ Failed to create: Weekly Intelligence
)
echo.

REM Task 6: Weekly Predictive Analytics (Monday 9:00 AM)
echo Creating: LinkedIn-Weekly-Predictive-Analytics
schtasks /create /tn "LinkedIn-Weekly-Predictive-Analytics" /tr "\"%TASKS_DIR%\run_weekly_predictive_analytics.bat\"" /sc weekly /d MON /st 09:00 /f /rl highest
if !errorlevel! equ 0 (
    echo ✅ Created: Weekly Predictive Analytics on Monday at 9:00 AM
) else (
    echo ❌ Failed to create: Weekly Predictive Analytics
)
echo.

REM Task 7: Bi-weekly Deep Analysis (Every other Wednesday 12:00 PM)
echo Creating: LinkedIn-Biweekly-Deep-Analysis
schtasks /create /tn "LinkedIn-Biweekly-Deep-Analysis" /tr "\"%TASKS_DIR%\run_biweekly_deep_analysis.bat\"" /sc weekly /d WED /st 12:00 /f /rl highest
if !errorlevel! equ 0 (
    echo ✅ Created: Bi-weekly Deep Analysis on Wednesday at 12:00 PM
) else (
    echo ❌ Failed to create: Bi-weekly Deep Analysis
)
echo.

echo ============================================================
echo  Task Creation Summary
echo ============================================================
echo.
echo 📅 DAILY SCHEDULES:
echo   • 6:00 AM  - Opportunity Detection
echo   • 10:00 AM - Market Analysis
echo   • 2:00 PM  - Network Insights
echo   • 6:00 PM  - Daily Summary
echo.
echo 📅 WEEKLY SCHEDULES:
echo   • Monday 8:00 AM  - Intelligence Orchestrator
echo   • Monday 9:00 AM  - Predictive Analytics
echo   • Wednesday 12:00 PM - Deep Analysis (Bi-weekly)
echo.

REM List all created tasks
echo 📋 Verifying created tasks...
echo.
schtasks /query /tn "LinkedIn*" /fo table

echo.
echo 🎉 Job Search Intelligence Task Setup Complete!
echo.
echo 📊 To manage your tasks:
echo   • View tasks: schtasks /query /tn "LinkedIn*"
echo   • Run task now: schtasks /run /tn "LinkedIn-Daily-Opportunity-Detection"
echo   • Delete task: schtasks /delete /tn "LinkedIn-Daily-Opportunity-Detection"
echo   • Open Task Scheduler: taskschd.msc
echo.
echo 🗑️  To remove all LinkedIn tasks:
echo   • Run: scripts\scheduled_tasks\remove_windows_tasks.bat
echo.

pause