#!/usr/bin/env python3
"""
Job Search Intelligence - Production Launcher
Start the complete automation system with organized reports and real Telegram messaging
"""

import os
import sys
import time
from datetime import datetime
from src.config import AppConfig

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_banner():
    """Print startup banner"""
    print("🚀" + "="*70 + "🚀")
    print("   LINKEDIN INTELLIGENCE SYSTEM - PRODUCTION LAUNCH")
    print("="*74)
    print(f"   📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   🎯 Real Telegram Bot Integration: ACTIVE")
    print("   📁 Organized Report Structure: ENABLED") 
    print("   ⏰ Automated Schedule: CONFIGURED")
    print("="*74)
    print()

def show_schedule():
    """Show the automation schedule"""
    print("📅 AUTOMATED SCHEDULE:")
    print("   🌅 Monday    9:00 AM  - Weekly Deep Dive Analysis")
    print("   🔍 Wednesday 12:00 PM - Mid-week Market Scan") 
    print("   🔮 Friday    5:00 PM  - Predictive Weekend Analysis")
    print("   📊 Sunday    10:00 AM - Comprehensive Weekly Report")
    print()

def show_report_structure():
    """Show the report organization structure"""
    print("📁 REPORT ORGANIZATION:")
    print("   📂 reports/")
    print("      ├── 📂 weekly/")
    print("      │   └── 📂 2025-W39/")
    print("      │       ├── monday_deep_dive_YYYYMMDD.md")
    print("      │       └── weekly_comprehensive_YYYY-WXX.md")
    print("      └── 📂 daily/")
    print("          └── 📂 YYYY-MM-DD/")
    print("              ├── wednesday_scan_YYYYMMDD_HHMM.md")
    print("              └── friday_predictive_YYYYMMDD_HHMM.md")
    print()

def show_telegram_info():
    """Show Telegram integration info"""
    cfg = AppConfig()
    notif = cfg.notifications
    enabled = notif.telegram_enabled and bool(notif.telegram_bot_token) and bool(notif.telegram_chat_id)
    masked = (notif.telegram_bot_token[:4] + "..." + notif.telegram_bot_token[-4:]) if notif.telegram_bot_token else "N/A"
    print("📱 TELEGRAM INTEGRATION:")
    print(f"   🤖 Bot Token: {masked} ({'ENABLED' if enabled else 'DISABLED'})")
    print(f"   💬 Chat ID: {notif.telegram_chat_id or 'N/A'}")
    print("   📨 Message Format: HTML with emojis")
    print(f"   📎 Document Delivery: {'Enabled' if enabled else 'Disabled'}")
    print(f"   ✅ Status: {'Operational' if enabled else 'Not Configured'}")
    print()

def main():
    """Main launcher"""
    print_banner()
    show_schedule()
    show_report_structure()
    show_telegram_info()
    
    print("🔄 STARTING AUTOMATION SYSTEM...")
    print("   Press Ctrl+C to stop the system")
    print("="*74)
    print()
    
    try:
        # Import and start the scheduler
        from automation.weekly_automation_scheduler import LinkedInIntelligenceScheduler
        
        scheduler = LinkedInIntelligenceScheduler()
        scheduler.run_scheduler()
        
    except KeyboardInterrupt:
        print("\n" + "="*74)
        print("🛑 SYSTEM STOPPED BY USER")
        print("   All scheduled reports and Telegram notifications have been paused.")
        print("   To restart: python launch_automation_system.py")
        print("="*74)
        
    except Exception as e:
        print(f"\n❌ SYSTEM ERROR: {e}")
        print("   Please check the logs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
