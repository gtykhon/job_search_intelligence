"""
Enhanced Job Search Intelligence Test Script

This script tests the complete integrated LinkedIn intelligence system including:
- Enhanced LinkedIn analyzer
- Database storage
- Telegram notifications
- Weekly reporting
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.intelligence.integrated_job_search_intelligence import IntegratedLinkedInIntelligence
from automation.weekly_automation_scheduler import LinkedInIntelligenceScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_integrated_intelligence():
    """Test the integrated LinkedIn intelligence system"""
    
    print("🚀 Testing Enhanced Job Search Intelligence Integration")
    print("=" * 60)
    
    try:
        # Initialize integrated system
        print("\n1. Initializing Integrated Job Search Intelligence...")
        intelligence = IntegratedLinkedInIntelligence()
        
        # Check system status
        print("\n2. Checking Integration Status...")
        status = intelligence.get_integration_status()
        print(f"   ✅ Analyzer: {'✓' if status['analyzer'] else '✗'}")
        print(f"   ✅ Database: {'✓' if status['database'] else '✗'}")
        print(f"   ✅ Telegram: {'✓' if status['telegram'] else '✗'}")
        print(f"   ✅ Reports Dir: {'✓' if status['reports_directory'] else '✗'}")
        if status['last_analysis']:
            print(f"   📅 Last Analysis: {status['last_analysis']}")
        
        # Test manual analysis
        print("\n3. Running Manual Enhanced LinkedIn Analysis...")
        results = intelligence.run_weekly_analysis("test_manual")
        
        if results['status'] == 'success':
            print("   ✅ Analysis completed successfully!")
            print(f"   📁 Session ID: {results['session_id']}")
            print(f"   💾 Database Saved: {results['database_saved']}")
            print(f"   📱 Telegram Sent: {results['telegram_sent']}")
            
            # Display key metrics
            real_data = results['analysis_results'].get('real_data', {})
            print(f"   🤝 Total Connections: {real_data.get('total_connections', 0):,}")
            print(f"   👔 Leadership: {real_data.get('leadership_engagement', '0%')}")
            print(f"   🏢 Fortune 500: {real_data.get('f500_penetration', '0%')}")
            
            # Show top companies
            analytics = results['analysis_results'].get('enhanced_analytics', {})
            if analytics.get('top_companies'):
                print("   🏢 Top Companies:")
                for i, (company, count) in enumerate(analytics['top_companies'][:5], 1):
                    print(f"      {i}. {company} ({count})")
            
            # Show generated files
            report_files = results.get('report_files', {})
            if report_files:
                print("   📄 Generated Files:")
                for file_type, file_path in report_files.items():
                    print(f"      {file_type}: {Path(file_path).name}")
        else:
            print(f"   ❌ Analysis failed: {results.get('error', 'Unknown error')}")
            return False
        
        print("\n4. Testing Database Retrieval...")
        latest_analysis = intelligence.database.get_latest_enhanced_analysis()
        if latest_analysis:
            session_data = latest_analysis['session_data']
            print("   ✅ Latest analysis retrieved from database:")
            print(f"      Session: {session_data['session_id']}")
            print(f"      Connections: {session_data['total_connections']:,}")
            print(f"      Companies: {session_data['unique_companies']}")
            print(f"      Locations: {session_data['unique_locations']}")
        else:
            print("   ⚠️ No analysis data found in database")
        
        print("\n5. Testing Weekly Intelligence Summary...")
        summary = intelligence.database.get_weekly_intelligence_summary()
        if summary:
            print(f"   📊 Total Reports: {summary['total_reports']}")
            print(f"   📅 Recent Weeks: {len(summary['recent_weeks'])}")
        
        print("\n✅ Integrated Job Search Intelligence Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Integration test failed: {e}")
        return False

async def test_scheduler_manual():
    """Test the enhanced scheduler with manual execution"""
    
    print("\n🗓️ Testing Enhanced Weekly Scheduler")
    print("=" * 50)
    
    try:
        # Initialize scheduler
        print("\n1. Initializing Enhanced Job Search Intelligence Scheduler...")
        scheduler = LinkedInIntelligenceScheduler()
        
        if not scheduler.intelligence:
            print("   ❌ Job Search Intelligence system not available")
            return False
        
        print("   ✅ Scheduler initialized with enhanced intelligence")
        
        # Test manual analysis
        print("\n2. Running Manual Test Analysis...")
        results = await scheduler.run_manual_analysis("test_scheduler")
        
        if results and results['status'] == 'success':
            print("   ✅ Manual analysis completed successfully!")
            print(f"   📁 Session: {results['session_id']}")
            print(f"   💾 Database: {results['database_saved']}")
            print(f"   📱 Telegram: {results['telegram_sent']}")
            
            # Show metrics
            analysis_results = results['analysis_results']
            real_data = analysis_results.get('real_data', {})
            combined_metrics = analysis_results.get('combined_metrics', {})
            
            print("\n   📊 Analysis Results:")
            print(f"      🤝 Connections: {real_data.get('total_connections', 0):,}")
            print(f"      👔 Leadership: {real_data.get('leadership_engagement', '0%')}")
            print(f"      🏢 Fortune 500: {real_data.get('f500_penetration', '0%')}")
            print(f"      🏭 Companies: {combined_metrics.get('unique_companies', 0)}")
            print(f"      🌍 Locations: {combined_metrics.get('unique_locations', 0)}")
            print(f"      💪 Avg Strength: {combined_metrics.get('average_connection_strength', 0):.2f}/3.0")
            
        else:
            print("   ❌ Manual analysis failed")
            return False
        
        print("\n✅ Enhanced Scheduler Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Scheduler test failed: {e}")
        logger.error(f"Scheduler test failed: {e}")
        return False

def test_database_schema():
    """Test the enhanced database schema"""
    
    print("\n💾 Testing Enhanced Database Schema")
    print("=" * 40)
    
    try:
        from src.database.enhanced_linkedin_database import EnhancedLinkedInDatabase
        
        print("\n1. Initializing Enhanced Database...")
        db = EnhancedLinkedInDatabase()
        print("   ✅ Database schema created successfully")
        
        print("\n2. Testing Database Operations...")
        
        # Test data retrieval
        latest_analysis = db.get_latest_enhanced_analysis()
        if latest_analysis:
            print("   ✅ Latest analysis retrieved")
            session_data = latest_analysis['session_data']
            print(f"      Session: {session_data['session_id']}")
            print(f"      Timestamp: {session_data['timestamp']}")
            print(f"      Connections: {session_data['total_connections']:,}")
        else:
            print("   ℹ️ No previous analysis data found (expected for first run)")
        
        # Test weekly summary
        summary = db.get_weekly_intelligence_summary()
        print(f"   📊 Weekly reports found: {summary.get('total_reports', 0)}")
        
        print("\n✅ Database Schema Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        logger.error(f"Database test failed: {e}")
        return False

async def run_full_integration_test():
    """Run complete integration test suite"""
    
    print("🚀 ENHANCED LINKEDIN INTELLIGENCE - FULL INTEGRATION TEST")
    print("=" * 70)
    
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
    print("\n" + "=" * 70)
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("\n🚀 Enhanced Job Search Intelligence is ready for:")
        print("   • Automated weekly reporting")
        print("   • Database storage and analytics")
        print("   • Telegram notifications")
        print("   • CSV/JSON export capabilities")
        print("   • Real LinkedIn data integration")
        
        print("\n📅 Scheduled Reports:")
        print("   • Monday 9:00 AM - Deep Dive with Enhanced Analytics")
        print("   • Wednesday 12:00 PM - Market Scan with Network Analysis")
        print("   • Friday 5:00 PM - Predictive Analysis with Intelligence")
        print("   • Sunday 10:00 AM - Comprehensive Report with Full Analytics")
        
        print("\n🎯 To start automated scheduling:")
        print("   python automation/weekly_automation_scheduler.py")
        
        return True
    else:
        print(f"❌ {total_tests - tests_passed} TESTS FAILED - Please review errors above")
        return False

if __name__ == "__main__":
    # Run the full integration test
    success = asyncio.run(run_full_integration_test())
    
    if success:
        print("\n🎉 Enhanced Job Search Intelligence Integration Complete!")
    else:
        print("\n🔧 Please fix integration issues before proceeding")
        sys.exit(1)