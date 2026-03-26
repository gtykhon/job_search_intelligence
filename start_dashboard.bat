@echo off
cd /d "C:\path\to\job_search_intelligence"
python -m uvicorn src.dashboard.app:app --host 0.0.0.0 --port 8888
