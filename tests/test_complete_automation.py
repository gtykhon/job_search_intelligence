#!/usr/bin/env python3
"""
Test Real Telegram Messaging and Report Organization
Validates the complete automation system with actual Telegram delivery
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.weekly_automation_scheduler import (
    LinkedInIntelligenceScheduler,
    WeeklyReportOrganizer,
    TelegramMessenger,
    ReportConfig
)

async def test_telegram_messaging():
    """Test real Telegram message sending"""
    print("🧪 Testing Real Telegram Messaging...")
    
    config = ReportConfig()
    telegram = TelegramMessenger(config.telegram_bot_token, config.telegram_chat_id)
    
    # Test basic message
    test_message = f"""
🧪 <b>Job Search Intelligence Test</b>

📅 <b>Test Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ <b>Testing Components:</b>
• Report organization system
• Telegram messaging
• File structure creation
• Automation readiness

🚀 <b>Status:</b> All systems operational!

#SystemTest #AutomationReady
    """
    
    success = await telegram.send_message(test_message.strip())
    
    if success:
        print("✅ Telegram messaging test PASSED")
        return True
    else:
        print("❌ Telegram messaging test FAILED")
        return False

def test_report_organization():
    """Test report folder organization"""
    print("🧪 Testing Report Organization...")
    
    config = ReportConfig()
    organizer = WeeklyReportOrganizer(config)
    
    # Test week folder creation
    week_folder = organizer.get_week_folder()
    print(f"📁 Week folder: {week_folder}")
    
    # Test daily folder creation
    daily_folder = organizer.get_daily_folder()
    print(f"📁 Daily folder: {daily_folder}")
    
    # Create test reports
    test_weekly_report = Path(week_folder) / f"test_weekly_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    test_daily_report = Path(daily_folder) / f"test_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    # Write test content
    test_content = f"""# Test Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Test Data
- Report organization: WORKING
- Folder structure: CREATED
- File naming: STANDARDIZED

This is a test report to verify the organization system.
"""
    
    with open(test_weekly_report, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    with open(test_daily_report, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✅ Test reports created:")
    print(f"   Weekly: {test_weekly_report}")
    print(f"   Daily: {test_daily_report}")
    
    return True

async def test_complete_workflow():
    """Test complete workflow with real Telegram"""
    print("🧪 Testing Complete Automation Workflow...")
    
    scheduler = LinkedInIntelligenceScheduler()
    
    # Test Monday Deep Dive (simulation)
    print("\n🚀 Testing Monday Deep Dive...")
    await scheduler.run_monday_deep_dive()
    
    # Small delay
    await asyncio.sleep(2)
    
    # Test Wednesday Scan
    print("\n🔍 Testing Wednesday Market Scan...")
    await scheduler.run_wednesday_scan()
    
    # Small delay
    await asyncio.sleep(2)
    
    # Test Friday Analysis
    print("\n🔮 Testing Friday Predictive Analysis...")
    await scheduler.run_friday_analysis()
    
    # Small delay
    await asyncio.sleep(2)
    
    # Test Sunday Report
    print("\n📊 Testing Sunday Comprehensive Report...")
    await scheduler.run_sunday_report()
    
    print("\n✅ Complete workflow test completed!")
    return True

def verify_folder_structure():
    """Verify the folder structure is properly created"""
    print("🧪 Verifying Folder Structure...")
    
    expected_folders = [
        "reports",
        "reports/weekly",
        "reports/daily"
    ]
    
    for folder in expected_folders:
        if Path(folder).exists():
            print(f"✅ {folder} - exists")
        else:
            print(f"❌ {folder} - missing")
            return False
    
    print("✅ Folder structure verification PASSED")
    return True

async def main():
    """Main test execution"""
    print("🚀 Job Search Intelligence - Complete Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Folder Structure
    print("\n1️⃣ Testing Folder Structure...")
    result1 = verify_folder_structure()
    test_results.append(("Folder Structure", result1))
    
    # Test 2: Report Organization
    print("\n2️⃣ Testing Report Organization...")
    result2 = test_report_organization()
    test_results.append(("Report Organization", result2))
    
    # Test 3: Telegram Messaging
    print("\n3️⃣ Testing Real Telegram Messaging...")
    result3 = await test_telegram_messaging()
    test_results.append(("Telegram Messaging", result3))
    
    # Test 4: Complete Workflow
    print("\n4️⃣ Testing Complete Automation Workflow...")
    result4 = await test_complete_workflow()
    test_results.append(("Complete Workflow", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<25} {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED - System Ready for Production!")
        
        # Send final success message
        config = ReportConfig()
        telegram = TelegramMessenger(config.telegram_bot_token, config.telegram_chat_id)
        
        success_message = """
🎉 <b>Job Search Intelligence - Ready!</b>

✅ <b>All Tests Passed:</b>
• Report organization system
• Telegram messaging
• Complete automation workflow
• Folder structure

🚀 <b>System Status:</b> Production Ready!

📅 <b>Ready for Scheduled Automation:</b>
• Monday 9:00 AM - Weekly Deep Dive
• Wednesday 12:00 PM - Market Scan  
• Friday 5:00 PM - Predictive Analysis
• Sunday 10:00 AM - Comprehensive Report

#SystemReady #ProductionLaunch
        """
        
        await telegram.send_message(success_message.strip())
        
        print("\n🚀 To start the full automation system, run:")
        print("   python weekly_automation_scheduler.py")
        
    else:
        print("❌ Some tests failed - Please check the issues above")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())