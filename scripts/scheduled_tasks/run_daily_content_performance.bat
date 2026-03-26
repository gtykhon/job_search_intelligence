@echo off
REM Daily LinkedIn Content Performance Report - Windows Task Scheduler
REM Schedule: Daily at 9:00 AM

echo Starting Daily Content Performance Report...
echo Time: %date% %time%

cd /d "C:\path\to\job_search_intelligence"

.venv\Scripts\python.exe "scripts\scheduled_tasks\daily_content_performance.py"

set TASK_EXIT_CODE=%ERRORLEVEL%

echo.
echo Task completed with exit code: %TASK_EXIT_CODE%
echo Time: %date% %time%

exit /b %TASK_EXIT_CODE%
