@echo off
REM Job Search Intelligence - Remove All Scheduled Tasks
REM This script removes all Job Search Intelligence scheduled tasks

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  Job Search Intelligence - Remove Scheduled Tasks
echo ============================================================
echo.

echo 🗑️  Removing all Job Search Intelligence scheduled tasks...
echo.

REM List of all Job Search Intelligence task names
set TASKS=LinkedIn-Daily-Opportunity-Detection LinkedIn-Daily-Market-Analysis LinkedIn-Daily-Network-Insights LinkedIn-Daily-Summary LinkedIn-Weekly-Intelligence LinkedIn-Weekly-Predictive-Analytics LinkedIn-Biweekly-Deep-Analysis

REM Remove each task
for %%T in (%TASKS%) do (
    echo Removing: %%T
    schtasks /delete /tn "%%T" /f >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Removed: %%T
    ) else (
        echo ⚠️  Not found or already removed: %%T
    )
    echo.
)

echo ============================================================
echo  Task Removal Complete
echo ============================================================
echo.

REM Verify removal by listing remaining LinkedIn tasks
echo 📋 Checking for remaining LinkedIn tasks...
schtasks /query /tn "LinkedIn*" /fo table >nul 2>&1
if !errorlevel! equ 0 (
    echo ⚠️  Some LinkedIn tasks may still exist:
    schtasks /query /tn "LinkedIn*" /fo table
) else (
    echo ✅ All Job Search Intelligence tasks have been removed successfully!
)

echo.
echo 🎉 Cleanup completed!
echo.
echo 📊 To recreate tasks:
echo   • Run: scripts\scheduled_tasks\create_windows_tasks.bat
echo.

pause