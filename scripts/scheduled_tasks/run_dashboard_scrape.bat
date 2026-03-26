@echo off
REM Dashboard Scrape Task — Windows Task Scheduler
REM Schedule: Daily at 6:00 AM (replaces run_daily_opportunity_detection.bat)
REM Uses the dashboard ScrapeRunner (JobSpy) + saves to job_tracker.db + Telegram

echo Starting Dashboard Scrape Task...
echo Time: %date% %time%

cd /d "C:\path\to\job_search_intelligence"

REM Run the task using the project's venv Python
.venv\Scripts\python.exe "scripts\scheduled_tasks\dashboard_scrape_task.py"

set TASK_EXIT_CODE=%ERRORLEVEL%

echo.
echo Task completed with exit code: %TASK_EXIT_CODE%
echo Time: %date% %time%

exit /b %TASK_EXIT_CODE%
