#!/usr/bin/env python3
"""
Job Search Intelligence Dashboard Launcher
Quick launcher for the real-time dashboard

Run this script to launch the interactive Streamlit dashboard
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 LinkedIn Profile Intelligence - Dashboard Launcher")
    print("=" * 60)
    
    # Get the project directory
    project_dir = Path(__file__).parent
    dashboard_path = project_dir / "src" / "dashboard" / "real_time_dashboard.py"
    
    if not dashboard_path.exists():
        print("❌ Dashboard not found!")
        print(f"   Expected: {dashboard_path}")
        return
        
    print(f"📊 Starting real-time dashboard...")
    print(f"🌐 Dashboard will open in your browser automatically")
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("-" * 60)
    
    try:
        # Change to project directory
        os.chdir(project_dir)
        
        # Launch Streamlit dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--browser.serverAddress", "localhost",
            "--browser.gatherUsageStats", "false",
            "--logger.level", "error"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")

if __name__ == "__main__":
    main()