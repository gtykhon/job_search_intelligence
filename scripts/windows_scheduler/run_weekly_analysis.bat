@echo off
REM Enhanced Job Search Intelligence - Weekly Analysis
REM Windows Task Scheduler Integration
REM Author: Job Search Intelligence
REM Last Updated: December 12, 2024

echo Starting Enhanced Job Search Intelligence Analysis...
echo Timestamp: %date% %time%
echo.

REM Navigate to project directory
cd /d "C:\path\to\job_search_intelligence"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, using system Python...
)

REM Set environment variables for Unicode support
set PYTHONIOENCODING=utf-8
set LANG=en_US.UTF-8

REM Run the enhanced LinkedIn intelligence analysis
echo Running enhanced LinkedIn intelligence analysis...
python -c "
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.getcwd())

from src.intelligence.integrated_job_search_intelligence import IntegratedLinkedInIntelligence

async def main():
    try:
        print('🚀 Starting Enhanced Job Search Intelligence Analysis...')
        intelligence = IntegratedLinkedInIntelligence()
        
        # Get current day for analysis type
        current_day = datetime.now().strftime('%%A').lower()
        analysis_type = f'weekly_{current_day}_automated'
        
        print(f'📊 Running {current_day} analysis...')
        results = await intelligence.run_weekly_analysis(analysis_type)
        
        if results:
            print('✅ Analysis completed successfully!')
            print(f'📁 Reports saved to: {results.get(\"output_path\", \"reports/\")}')
            
            # Telegram notification is handled by the integrated system via AppConfig
            print('ℹ️ Telegram notification handled by integrated system')
        else:
            print('❌ Analysis failed or returned no results')
            
    except Exception as e:
        print(f'❌ Error during analysis: {e}')
        import traceback
        traceback.print_exc()
        
        # Send error notification via integrated Telegram notifier
        try:
            from scripts.intelligence_scheduler import TelegramNotifier, IntelligenceConfig
            notifier = TelegramNotifier(IntelligenceConfig())
            await notifier.send_message(f'Analysis Error: {e}')
        except Exception:
            pass

if __name__ == '__main__':
    asyncio.run(main())
"

echo.
echo Analysis complete. Check logs for details.
echo Timestamp: %date% %time%

REM Optional: Keep window open for debugging (comment out for production)
REM pause
