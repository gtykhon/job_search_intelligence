#!/usr/bin/env python3
"""
Intelligence Scheduler Launcher - Job Search Intelligence
Start the comprehensive intelligence automation system
"""

import os
import sys
import time
from datetime import datetime
from src.config import AppConfig

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def print_banner():
    """Print startup banner"""
    print("🧠" + "="*70 + "🧠")
    print("   LINKEDIN INTELLIGENCE SCHEDULER - AUTOMATED SYSTEM")
    print("="*74)
    print(f"   📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   🤖 AI-Powered Intelligence: ACTIVE")
    print("   📊 Automated Reporting: ENABLED") 
    print("   ⏰ Smart Scheduling: CONFIGURED")
    print("="*74)
    print()

def show_intelligence_schedule():
    """Show the intelligence automation schedule"""
    print("📅 INTELLIGENCE SCHEDULE:")
    print()
    print("   🌅 Daily 6:00 AM  - Opportunity Detection")
    print("   📈 Daily 10:00 AM - Market Analysis") 
    print("   🌐 Daily 2:00 PM  - Network Insights")
    print("   📋 Daily 6:00 PM  - Daily Summary")
    print()
    print("   🚀 Monday 8:00 AM  - Intelligence Orchestrator")
    print("   🔮 Monday 9:00 AM  - Predictive Analytics")
    print()
    print("   🔬 Bi-weekly Wed 12:00 PM - Deep Analysis")
    print("   📊 Monthly 1st Sun 10:00 AM - Comprehensive Report")
    print()

def show_report_organization():
    """Show the report organization structure"""
    print("📁 INTELLIGENCE REPORT ORGANIZATION:")
    print("   📂 reports/intelligence/")
    print("      ├── 📂 daily/")
    print("      │   └── 📂 YYYY-MM-DD/")
    print("      │       ├── opportunity_detection_YYYY-MM-DD_HHMM.md")
    print("      │       ├── market_analysis_YYYY-MM-DD_HHMM.md")
    print("      │       ├── network_insights_YYYY-MM-DD_HHMM.md")
    print("      │       └── daily_summary_YYYY-MM-DD_HHMM.md")
    print("      ├── 📂 weekly/")
    print("      │   └── 📂 YYYY-WXX/")
    print("      │       ├── weekly_intelligence_YYYY-WXX.md")
    print("      │       ├── predictive_analytics_YYYY-WXX.md")
    print("      │       └── deep_analysis_YYYY-WXX.md")
    print("      └── 📂 monthly/")
    print("          └── 📂 YYYY-MM/")
    print("              └── monthly_comprehensive_YYYY-MM.md")
    print()

def show_telegram_integration():
    """Show Telegram integration details"""
    cfg = AppConfig()
    notif = cfg.notifications
    enabled = notif.telegram_enabled and bool(notif.telegram_bot_token) and bool(notif.telegram_chat_id)
    masked = (notif.telegram_bot_token[:4] + "..." + notif.telegram_bot_token[-4:]) if notif.telegram_bot_token else "N/A"
    print("📱 INTELLIGENCE TELEGRAM INTEGRATION:")
    print(f"   🤖 Bot Token: {masked} ({'ENABLED' if enabled else 'DISABLED'})")
    print(f"   💬 Chat ID: {notif.telegram_chat_id or 'N/A'}")
    print("   📨 Message Format: HTML with emojis")
    print(f"   📎 Document Delivery: {'Enabled' if enabled else 'Disabled'}")
    print(f"   🔔 Real-time Notifications: {'Active' if enabled else 'Inactive'}")
    print(f"   ✅ Status: {'Operational' if enabled else 'Not Configured'}")
    print()

def main():
    """Main launcher function"""
    print_banner()
    show_intelligence_schedule()
    show_report_organization()
    show_telegram_integration()
    
    print("🔄 STARTING INTELLIGENCE AUTOMATION SYSTEM...")
    print("   Press Ctrl+C to stop the system")
    print("="*74)
    print()
    
    try:
        # Import and start the intelligence scheduler
        from scripts.intelligence_scheduler import LinkedInIntelligenceScheduler
        
        scheduler = LinkedInIntelligenceScheduler()
        scheduler.run_scheduler()
        
    except KeyboardInterrupt:
        print("\n" + "="*74)
        print("🛑 INTELLIGENCE SYSTEM STOPPED BY USER")
        print("   All scheduled intelligence tasks have been paused.")
        print("   To restart: python launchers/launch_intelligence_scheduler.py")
        print("="*74)
        
    except Exception as e:
        print(f"\n❌ SYSTEM ERROR: {e}")
        print("   Please check the logs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
