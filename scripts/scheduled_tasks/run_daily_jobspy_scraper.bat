@echo off
REM Daily JobSpy Scraper - Windows Task Scheduler Batch File
REM Schedule this to run daily at 5:30 AM (before opportunity detection at 6 AM)
REM This is the REAL scraper that fills job_tracker.db with scraped jobs from
REM Indeed, LinkedIn, Glassdoor, and Google Jobs.

echo Starting Daily JobSpy Scraper...
echo Time: %date% %time%

cd /d "C:\path\to\job_search_intelligence"

REM Run the real JobSpy scraper using project venv
.venv\Scripts\python.exe "scripts\scheduled_tasks\daily_jobspy_detection.py"

REM Capture exit code
set TASK_EXIT_CODE=%ERRORLEVEL%

echo.
echo Task completed with exit code: %TASK_EXIT_CODE%
echo Time: %date% %time%

REM Exit with the same code as the Python script
exit /b %TASK_EXIT_CODE%
