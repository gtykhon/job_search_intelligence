"""
Enhanced Job Search Intelligence Test Script - Windows Unicode Compatible

This script tests the complete integrated LinkedIn intelligence system including:
- Enhanced LinkedIn analyzer
- Database storage
- Telegram notifications
- Weekly reporting

Windows Unicode Fix: Properly handles emoji display on Windows console
"""

import sys
import asyncio
import logging
import os
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform.startswith('win'):
    import codecs
    import locale
    
    # Set console to UTF-8
    os.system('chcp 65001 > nul')
    
    # Configure stdout/stderr encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    else:
        # Fallback for older Python versions
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Add project path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.intelligence.integrated_job_search_intelligence import IntegratedLinkedInIntelligence
from automation.weekly_automation_scheduler import LinkedInIntelligenceScheduler

# Configure logging with UTF-8 encoding
class UTF8FileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        super().__init__(filename, mode, encoding, delay)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        UTF8FileHandler('logs/test_integration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Emoji mappings for fallback
EMOJI_MAP = {
    '🚀': '[ROCKET]',
    '✅': '[OK]',
    '❌': '[ERROR]',
    '📊': '[CHART]',
    '🎯': '[TARGET]',
    '📁': '[FOLDER]',
    '💾': '[SAVE]',
    '📱': '[PHONE]',
    '🤝': '[HANDSHAKE]',
    '👔': '[SHIRT]',
    '🏢': '[BUILDING]',
    '📄': '[FILE]',
    '⚠️': '[WARNING]',
    '📅': '[CALENDAR]',
    '🗓️': '[CALENDAR]',
    '🌍': '[GLOBE]',
    '💪': '[MUSCLE]',
    '💾': '[DISK]',
    'ℹ️': '[INFO]',
    '🎉': '[PARTY]',
    '🔧': '[WRENCH]'
}

def safe_print(text):
    """Print text with emoji fallback for Unicode issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace emojis with text equivalents
        safe_text = text
        for emoji, replacement in EMOJI_MAP.items():
            safe_text = safe_text.replace(emoji, replacement)
        print(safe_text)

async def test_integrated_intelligence():
    """Test the integrated LinkedIn intelligence system"""
    
    safe_print("🚀 Testing Enhanced Job Search Intelligence Integration")
    safe_print("=" * 60)
    
    try:
        # Initialize integrated system
        safe_print("\n1. Initializing Integrated Job Search Intelligence...")
        intelligence = IntegratedLinkedInIntelligence()
        
        # Check system status
        safe_print("\n2. Checking Integration Status...")
        status = intelligence.get_integration_status()
        safe_print(f"   ✅ Analyzer: {'✓' if status['analyzer'] else '✗'}")
        safe_print(f"   ✅ Database: {'✓' if status['database'] else '✗'}")
        safe_print(f"   ✅ Telegram: {'✓' if status['telegram'] else '✗'}")
        safe_print(f"   ✅ Reports Dir: {'✓' if status['reports_directory'] else '✗'}")
        if status['last_analysis']:
            safe_print(f"   📅 Last Analysis: {status['last_analysis']}")
        
        # Test manual analysis
        safe_print("\n3. Running Manual Enhanced LinkedIn Analysis...")
        results = intelligence.run_weekly_analysis("test_manual")
        
        if results['status'] == 'success':
            safe_print("   ✅ Analysis completed successfully!")
            safe_print(f"   📁 Session ID: {results['session_id']}")
            safe_print(f"   💾 Database Saved: {results['database_saved']}")
            safe_print(f"   📱 Telegram Sent: {results['telegram_sent']}")
            
            # Display key metrics
            real_data = results['analysis_results'].get('real_data', {})
            safe_print(f"   🤝 Total Connections: {real_data.get('total_connections', 0):,}")
            safe_print(f"   👔 Leadership: {real_data.get('leadership_engagement', '0%')}")
            safe_print(f"   🏢 Fortune 500: {real_data.get('f500_penetration', '0%')}")
            
            # Show top companies
            analytics = results['analysis_results'].get('enhanced_analytics', {})
            if analytics.get('top_companies'):
                safe_print("   🏢 Top Companies:")
                for i, (company, count) in enumerate(analytics['top_companies'][:5], 1):
                    safe_print(f"      {i}. {company} ({count})")
            
            # Show generated files
            report_files = results.get('report_files', {})
            if report_files:
                safe_print("   📄 Generated Files:")
                for file_type, file_path in report_files.items():
                    safe_print(f"      {file_type}: {Path(file_path).name}")
        else:
            safe_print(f"   ❌ Analysis failed: {results.get('error', 'Unknown error')}")
            return False
        
        safe_print("\n4. Testing Database Retrieval...")
        latest_analysis = intelligence.database.get_latest_enhanced_analysis()
        if latest_analysis:
            session_data = latest_analysis['session_data']
            safe_print("   ✅ Latest analysis retrieved from database:")
            safe_print(f"      Session: {session_data['session_id']}")
            safe_print(f"      Connections: {session_data['total_connections']:,}")
            safe_print(f"      Companies: {session_data['unique_companies']}")
            safe_print(f"      Locations: {session_data['unique_locations']}")
        else:
            safe_print("   ⚠️ No analysis data found in database")
        
        safe_print("\n5. Testing Weekly Intelligence Summary...")
        summary = intelligence.database.get_weekly_intelligence_summary()
        if summary:
            safe_print(f"   📊 Total Reports: {summary['total_reports']}")
            safe_print(f"   📅 Recent Weeks: {len(summary['recent_weeks'])}")
        
        safe_print("\n✅ Integrated Job Search Intelligence Test Completed Successfully!")
        return True
        
    except Exception as e:
        safe_print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Integration test failed: {e}")
        return False

async def test_scheduler_manual():
    """Test the enhanced scheduler with manual execution"""
    
    safe_print("\n🗓️ Testing Enhanced Weekly Scheduler")
    safe_print("=" * 50)
    
    try:
        # Initialize scheduler
        safe_print("\n1. Initializing Enhanced Job Search Intelligence Scheduler...")
        scheduler = LinkedInIntelligenceScheduler()
        
        if not scheduler.intelligence:
            safe_print("   ❌ Job Search Intelligence system not available")
            return False
        
        safe_print("   ✅ Scheduler initialized with enhanced intelligence")
        
        # Test manual analysis
        safe_print("\n2. Running Manual Test Analysis...")
        results = await scheduler.run_manual_analysis("test_scheduler")
        
        if results and results['status'] == 'success':
            safe_print("   ✅ Manual analysis completed successfully!")
            safe_print(f"   📁 Session: {results['session_id']}")
            safe_print(f"   💾 Database: {results['database_saved']}")
            safe_print(f"   📱 Telegram: {results['telegram_sent']}")
            
            # Show metrics
            analysis_results = results['analysis_results']
            real_data = analysis_results.get('real_data', {})
            combined_metrics = analysis_results.get('combined_metrics', {})
            
            safe_print("\n   📊 Analysis Results:")
            safe_print(f"      🤝 Connections: {real_data.get('total_connections', 0):,}")
            safe_print(f"      👔 Leadership: {real_data.get('leadership_engagement', '0%')}")
            safe_print(f"      🏢 Fortune 500: {real_data.get('f500_penetration', '0%')}")
            safe_print(f"      🏭 Companies: {combined_metrics.get('unique_companies', 0)}")
            safe_print(f"      🌍 Locations: {combined_metrics.get('unique_locations', 0)}")
            safe_print(f"      💪 Avg Strength: {combined_metrics.get('average_connection_strength', 0):.2f}/3.0")
            
        else:
            safe_print("   ❌ Manual analysis failed")
            return False
        
        safe_print("\n✅ Enhanced Scheduler Test Completed Successfully!")
        return True
        
    except Exception as e:
        safe_print(f"\n❌ Scheduler test failed: {e}")
        logger.error(f"Scheduler test failed: {e}")
        return False

def test_database_schema():
    """Test the enhanced database schema"""
    
    safe_print("\n💾 Testing Enhanced Database Schema")
    safe_print("=" * 40)
    
    try:
        from src.database.enhanced_linkedin_database import EnhancedLinkedInDatabase
        
        safe_print("\n1. Initializing Enhanced Database...")
        db = EnhancedLinkedInDatabase()
        safe_print("   ✅ Database schema created successfully")
        
        safe_print("\n2. Testing Database Operations...")
        
        # Test data retrieval
        latest_analysis = db.get_latest_enhanced_analysis()
        if latest_analysis:
            safe_print("   ✅ Latest analysis retrieved")
            session_data = latest_analysis['session_data']
            safe_print(f"      Session: {session_data['session_id']}")
            safe_print(f"      Timestamp: {session_data['timestamp']}")
            safe_print(f"      Connections: {session_data['total_connections']:,}")
        else:
            safe_print("   ℹ️ No previous analysis data found (expected for first run)")
        
        # Test weekly summary
        summary = db.get_weekly_intelligence_summary()
        safe_print(f"   📊 Weekly reports found: {summary.get('total_reports', 0)}")
        
        safe_print("\n✅ Database Schema Test Completed Successfully!")
        return True
        
    except Exception as e:
        safe_print(f"\n❌ Database test failed: {e}")
        logger.error(f"Database test failed: {e}")
        return False

async def run_full_integration_test():
    """Run complete integration test suite"""
    
    safe_print("🚀 ENHANCED LINKEDIN INTELLIGENCE - FULL INTEGRATION TEST")
    safe_print("=" * 70)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Database Schema
    if test_database_schema():
        tests_passed += 1
    
    # Test 2: Integrated Intelligence
    if await test_integrated_intelligence():
        tests_passed += 1
    
    # Test 3: Enhanced Scheduler
    if await test_scheduler_manual():
        tests_passed += 1
    
    # Summary
    safe_print("\n" + "=" * 70)
    safe_print("🎯 INTEGRATION TEST SUMMARY")
    safe_print("=" * 70)
    safe_print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        safe_print("✅ ALL INTEGRATION TESTS PASSED!")
        safe_print("\n🚀 Enhanced Job Search Intelligence is ready for:")
        safe_print("   • Automated weekly reporting")
        safe_print("   • Database storage and analytics")
        safe_print("   • Telegram notifications")
        safe_print("   • CSV/JSON export capabilities")
        safe_print("   • Real LinkedIn data integration")
        
        safe_print("\n📅 Scheduled Reports:")
        safe_print("   • Monday 9:00 AM - Deep Dive with Enhanced Analytics")
        safe_print("   • Wednesday 12:00 PM - Market Scan with Network Analysis")
        safe_print("   • Friday 5:00 PM - Predictive Analysis with Intelligence")
        safe_print("   • Sunday 10:00 AM - Comprehensive Report with Full Analytics")
        
        safe_print("\n🎯 To start automated scheduling:")
        safe_print("   python automation/weekly_automation_scheduler.py")
        
        return True
    else:
        safe_print(f"❌ {total_tests - tests_passed} TESTS FAILED - Please review errors above")
        return False

if __name__ == "__main__":
    # Run the full integration test
    success = asyncio.run(run_full_integration_test())
    
    if success:
        safe_print("\n🎉 Enhanced Job Search Intelligence Integration Complete!")
    else:
        safe_print("\n🔧 Please fix integration issues before proceeding")
        sys.exit(1)