#!/usr/bin/env python3
"""
Job Search Intelligence Launcher
Easy-to-use launcher for the complete AI-powered LinkedIn intelligence system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def main():
    """Main launcher interface"""
    print("🤖 Job Search Intelligence")
    print("=" * 50)
    print()
    print("Welcome to your AI-powered LinkedIn intelligence platform!")
    print()
    print("Available Systems:")
    print("1. 🚀 Complete Intelligence Orchestrator (Recommended)")
    print("2. 🔍 Smart Opportunity Detector")
    print("3. 🔮 Predictive Analytics")
    print("4. ⚡ Automated Intelligence")
    print("5. 💼 Job Search Intelligence")
    print("6. 🧠 Intelligence Scheduler (NEW)")
    print("7. 📱 Test Telegram Notifications")
    print("8. ⚙️  Setup & Configuration")
    print("9. 📊 View System Status")
    print("10. 🛠️ Troubleshooting")
    print("11. ❌ Exit")
    print()
    
    try:
        choice = input("Select an option (1-11): ").strip()
        
        if choice == "1":
            print("\n🚀 Launching Complete Intelligence Orchestrator...")
            run_orchestrator()
            
        elif choice == "2":
            print("\n🔍 Launching Smart Opportunity Detector...")
            run_opportunity_detector()
            
        elif choice == "3":
            print("\n🔮 Launching Predictive Analytics...")
            run_predictive_analytics()
            
        elif choice == "4":
            print("\n⚡ Launching Automated Intelligence...")
            run_automated_intelligence()
            
        elif choice == "5":
            print("\n💼 Launching Job Search Intelligence...")
            run_job_search_intelligence()
            
        elif choice == "6":
            print("\n🧠 Launching Intelligence Scheduler...")
            run_intelligence_scheduler()
            
        elif choice == "7":
            print("\n📱 Testing Telegram Notifications...")
            test_telegram()
            
        elif choice == "8":
            print("\n⚙️ Setup & Configuration...")
            run_setup()
            
        elif choice == "9":
            print("\n📊 System Status...")
            show_system_status()
            print("✅ Status check completed!")
            
        elif choice == "10":
            print("\n🛠️ Troubleshooting...")
            show_troubleshooting()
            print("📋 Troubleshooting guide displayed!")
            
        elif choice == "11":
            print("\n👋 Goodbye!")
            sys.exit(0)
            
        else:
            print("❌ Invalid choice. Please select 1-11.")
            
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

def run_orchestrator():
    """Run the complete intelligence orchestrator"""
    try:
        from core.job_search_intelligence_orchestrator import main as orchestrator_main
        asyncio.run(orchestrator_main())
    except ImportError as e:
        print(f"❌ Failed to import orchestrator: {e}")
        print("💡 Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")

def run_opportunity_detector():
    """Run the smart opportunity detector"""
    try:
        from core.smart_opportunity_detector import SmartOpportunityDetector
        detector = SmartOpportunityDetector()
        print("🔍 Starting Smart Opportunity Detector...")
        print("Note: This requires configuration to run properly.")
    except ImportError as e:
        print(f"❌ Failed to import opportunity detector: {e}")
        print("💡 Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Opportunity detector failed: {e}")

def run_predictive_analytics():
    """Run predictive analytics"""
    try:
        from core.predictive_analytics import PredictiveAnalytics
        analytics = PredictiveAnalytics()
        print("🔮 Starting Predictive Analytics...")
        print("Note: This requires configuration to run properly.")
    except ImportError as e:
        print(f"❌ Failed to import predictive analytics: {e}")
        print("💡 Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Predictive analytics failed: {e}")

def run_automated_intelligence():
    """Run automated intelligence"""
    try:
        from core.automated_intelligence import AutomatedIntelligence
        print("⚡ Starting Automated Intelligence...")
        print("Note: This requires configuration to run properly.")
    except ImportError as e:
        print(f"❌ Failed to import automated intelligence: {e}")
        print("💡 Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Automated intelligence failed: {e}")

def run_job_search_intelligence():
    """Run job search intelligence"""
    try:
        from job_search.job_search_intelligence import JobSearchIntelligence
        print("💼 Starting Job Search Intelligence...")
        print("Note: This requires configuration to run properly.")
    except ImportError as e:
        print(f"❌ Failed to import job search intelligence: {e}")
        print("💡 Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Job search intelligence failed: {e}")

def run_intelligence_scheduler():
    """Run the comprehensive intelligence scheduler"""
    try:
        print("🧠 Starting Intelligence Scheduler...")
        print("This will run continuous automated intelligence tasks.")
        print("⚠️  This is a long-running process. Press Ctrl+C to stop.")
        print()
        
        from scripts.intelligence_scheduler import LinkedInIntelligenceScheduler
        
        scheduler = LinkedInIntelligenceScheduler()
        scheduler.run_scheduler()
        
    except ImportError as e:
        print(f"❌ Failed to import intelligence scheduler: {e}")
        print("💡 Try running: pip install -r requirements.txt")
    except KeyboardInterrupt:
        print("\n🛑 Intelligence scheduler stopped by user")
    except Exception as e:
        print(f"❌ Intelligence scheduler failed: {e}")

def test_telegram():
    """Test Telegram notifications"""
    try:
        import tests.test_telegram_integration
        print("📱 Running Telegram integration test...")
        print("Note: This requires proper Telegram bot configuration.")
    except ImportError as e:
        print(f"❌ Failed to import Telegram test: {e}")
        print("💡 Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")

def run_setup():
    """Run setup and configuration"""
    try:
        import config.setup_telegram_bot
        print("⚙️ Running Telegram bot setup...")
        print("Note: Follow the interactive prompts to configure your bot.")
    except ImportError as e:
        print(f"❌ Failed to import setup: {e}")
        print("💡 Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Setup failed: {e}")

def show_system_status():
    """Show system status information"""
    print("\n📊 System Status Check")
    print("-" * 30)
    
    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env configuration file exists")
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            if "TELEGRAM_BOT_TOKEN" in content:
                print("✅ Telegram bot token configured")
            else:
                print("⚠️  Telegram bot token not found")
                
            if "TELEGRAM_CHAT_ID" in content:
                print("✅ Telegram chat ID configured")
            else:
                print("⚠️  Telegram chat ID not found")
                
            if "TELEGRAM_ENABLED=true" in content:
                print("✅ Telegram notifications enabled")
            else:
                print("⚠️  Telegram notifications not enabled")
                
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print("❌ .env configuration file not found")
        print("💡 Run option 6 (Setup & Configuration) to create it")
    
    # Check requirements
    try:
        import pandas
        print("✅ Data analysis packages available")
    except ImportError:
        print("⚠️  Data analysis packages not installed")
        print("💡 Run: pip install -r requirements.txt")
    
    # Check database
    db_file = Path("data/job_search.db")
    if db_file.exists():
        print("✅ Database file exists")
    else:
        print("⚠️  Database file not found")
        print("💡 Database will be created automatically on first run")
    
    print("\n📈 Recent Activity:")
    
    # Check logs
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            print(f"✅ Latest log: {latest_log.name}")
        else:
            print("⚠️  No log files found")
    else:
        print("⚠️  Logs directory not found")
    
    try:
        input("\nPress Enter to continue...")
    except (EOFError, KeyboardInterrupt):
        pass

def show_troubleshooting():
    """Show troubleshooting information"""
    print("\n🛠️ Troubleshooting Guide")
    print("-" * 30)
    print()
    print("Common Issues & Solutions:")
    print()
    print("1. 🔌 Import Errors:")
    print("   Solution: pip install -r requirements.txt")
    print()
    print("2. 📱 Telegram Not Working:")
    print("   - Check .env file has TELEGRAM_BOT_TOKEN")
    print("   - Check .env file has TELEGRAM_CHAT_ID")
    print("   - Check TELEGRAM_ENABLED=true")
    print("   - Run option 6 to reconfigure")
    print()
    print("3. 🗄️ Database Issues:")
    print("   - Database is created automatically")
    print("   - Check data/ directory permissions")
    print("   - Restart the application")
    print()
    print("4. 🌐 Network Issues:")
    print("   - Check internet connection")
    print("   - Check firewall settings")
    print("   - Try running individual components")
    print()
    print("5. 🔄 Performance Issues:")
    print("   - Adjust rate limiting in .env")
    print("   - Check system resources")
    print("   - Run during off-peak hours")
    print()
    print("6. 📊 No Data/Results:")
    print("   - Ensure LinkedIn credentials are valid")
    print("   - Check rate limiting settings")
    print("   - Verify network connectivity")
    print()
    print("📞 For additional help:")
    print("   - Check logs in logs/ directory")
    print("   - Review .env configuration")
    print("   - Test individual components")
    print()
    
    try:
        input("Press Enter to continue...")
    except (EOFError, KeyboardInterrupt):
        pass

if __name__ == "__main__":
    main()
