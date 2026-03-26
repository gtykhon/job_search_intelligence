"""
Simple Integration Test Runner - Unicode Safe

This script runs the integration tests with proper Unicode handling,
focusing on verifying that all core functionality works correctly
without display issues.
"""

import sys
import asyncio
from pathlib import Path

# Add project path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Configure Unicode-safe logging first
from src.utils.unicode_logging import setup_system_wide_unicode_logging
logger = setup_system_wide_unicode_logging()

from src.intelligence.integrated_job_search_intelligence import IntegratedLinkedInIntelligence
from automation.weekly_automation_scheduler import LinkedInIntelligenceScheduler

def safe_print(message, success=None):
    """Print with status indicator"""
    if success is True:
        print(f"[OK] {message}")
    elif success is False:
        print(f"[ERROR] {message}")
    else:
        print(f"[INFO] {message}")

async def test_core_integration():
    """Test core LinkedIn intelligence integration"""
    
    safe_print("Testing Enhanced Job Search Intelligence Integration")
    safe_print("=" * 60)
    
    try:
        # Test 1: System Initialization
        safe_print("\n1. Initializing Job Search Intelligence...")
        intelligence = IntegratedLinkedInIntelligence()
        safe_print("System initialized successfully", True)
        
        # Test 2: Check Integration Status
        safe_print("\n2. Checking Integration Components...")
        status = intelligence.get_integration_status()
        
        components = {
            'Analyzer': status['analyzer'],
            'Database': status['database'], 
            'Telegram': status['telegram'],
            'Reports Dir': status['reports_directory']
        }
        
        all_good = True
        for component, status_ok in components.items():
            safe_print(f"   {component}: {'Available' if status_ok else 'Not Available'}", status_ok)
            if not status_ok:
                all_good = False
        
        if not all_good:
            safe_print("Some components not available", False)
            return False
            
        # Test 3: Run Analysis
        safe_print("\n3. Running LinkedIn Network Analysis...")
        results = await intelligence.run_weekly_analysis("integration_test")
        
        if results['status'] == 'success':
            safe_print("Analysis completed successfully", True)
            
            # Show key metrics without emojis
            real_data = results['analysis_results'].get('real_data', {})
            safe_print(f"   Total Connections: {real_data.get('total_connections', 0):,}")
            safe_print(f"   Leadership Engagement: {real_data.get('leadership_engagement', '0%')}")
            safe_print(f"   Fortune 500 Penetration: {real_data.get('f500_penetration', '0%')}")
            
            # Check outputs
            safe_print(f"   Database Saved: {results['database_saved']}", results['database_saved'])
            safe_print(f"   Telegram Sent: {results['telegram_sent']}", results['telegram_sent'])
            
            # List generated files
            report_files = results.get('report_files', {})
            if report_files:
                safe_print(f"   Generated {len(report_files)} report files")
                for file_type, file_path in report_files.items():
                    safe_print(f"      {file_type}: {Path(file_path).name}")
            
        else:
            safe_print(f"Analysis failed: {results.get('error', 'Unknown error')}", False)
            return False
        
        # Test 4: Database Verification
        safe_print("\n4. Verifying Database Storage...")
        latest_analysis = intelligence.database.get_latest_enhanced_analysis()
        if latest_analysis:
            session_data = latest_analysis['session_data']
            safe_print("Latest analysis retrieved from database", True)
            safe_print(f"   Session: {session_data['session_id']}")
            safe_print(f"   Connections: {session_data['total_connections']:,}")
            safe_print(f"   Companies: {session_data['unique_companies']}")
            safe_print(f"   Locations: {session_data['unique_locations']}")
        else:
            safe_print("No analysis data found in database", False)
            return False
        
        safe_print("\nIntegration Test PASSED", True)
        return True
        
    except Exception as e:
        safe_print(f"Integration test failed: {str(e)}", False)
        logger.error(f"Integration test error: {e}")
        return False

async def test_scheduler_functionality():
    """Test the enhanced scheduler functionality"""
    
    safe_print("\nTesting Enhanced Weekly Scheduler")
    safe_print("=" * 50)
    
    try:
        # Initialize scheduler
        safe_print("\n1. Initializing Enhanced Scheduler...")
        scheduler = LinkedInIntelligenceScheduler()
        
        if not scheduler.intelligence:
            safe_print("Job Search Intelligence system not available in scheduler", False)
            return False
        
        safe_print("Scheduler initialized with enhanced intelligence", True)
        
        # Test manual analysis
        safe_print("\n2. Running Manual Scheduler Test...")
        results = await scheduler.run_manual_analysis("scheduler_test")
        
        if results and results['status'] == 'success':
            safe_print("Manual scheduler analysis completed successfully", True)
            
            # Show key results
            analysis_results = results['analysis_results']
            real_data = analysis_results.get('real_data', {})
            combined_metrics = analysis_results.get('combined_metrics', {})
            
            safe_print(f"   Session: {results['session_id']}")
            safe_print(f"   Connections: {real_data.get('total_connections', 0):,}")
            safe_print(f"   Leadership: {real_data.get('leadership_engagement', '0%')}")
            safe_print(f"   Fortune 500: {real_data.get('f500_penetration', '0%')}")
            safe_print(f"   Companies: {combined_metrics.get('unique_companies', 0)}")
            safe_print(f"   Locations: {combined_metrics.get('unique_locations', 0)}")
            safe_print(f"   Average Connection Strength: {combined_metrics.get('average_connection_strength', 0):.2f}/3.0")
            
        else:
            safe_print("Manual scheduler analysis failed", False)
            return False
        
        safe_print("\nScheduler Test PASSED", True)
        return True
        
    except Exception as e:
        safe_print(f"Scheduler test failed: {str(e)}", False)
        logger.error(f"Scheduler test error: {e}")
        return False

def test_database_functionality():
    """Test the enhanced database functionality"""
    
    safe_print("\nTesting Enhanced Database Schema")
    safe_print("=" * 40)
    
    try:
        from src.database.enhanced_linkedin_database import EnhancedLinkedInDatabase
        
        safe_print("\n1. Initializing Enhanced Database...")
        db = EnhancedLinkedInDatabase()
        safe_print("Database schema initialized successfully", True)
        
        safe_print("\n2. Testing Database Operations...")
        
        # Test data retrieval
        latest_analysis = db.get_latest_enhanced_analysis()
        if latest_analysis:
            safe_print("Latest analysis retrieved successfully", True)
            session_data = latest_analysis['session_data']
            safe_print(f"   Session: {session_data['session_id']}")
            safe_print(f"   Timestamp: {session_data['timestamp']}")
            safe_print(f"   Connections: {session_data['total_connections']:,}")
        else:
            safe_print("No previous analysis data (expected for first run)")
        
        # Test weekly summary
        summary = db.get_weekly_intelligence_summary()
        safe_print(f"   Weekly reports found: {summary.get('total_reports', 0)}")
        
        safe_print("\nDatabase Test PASSED", True)
        return True
        
    except Exception as e:
        safe_print(f"Database test failed: {str(e)}", False)
        logger.error(f"Database test error: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive integration test suite"""
    
    safe_print("ENHANCED LINKEDIN INTELLIGENCE - COMPREHENSIVE TEST")
    safe_print("=" * 70)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Database Functionality
    safe_print("\n[TEST 1/3] Database Functionality")
    if test_database_functionality():
        tests_passed += 1
        safe_print("Test 1 PASSED", True)
    else:
        safe_print("Test 1 FAILED", False)
    
    # Test 2: Core Integration
    safe_print("\n[TEST 2/3] Core Integration")
    if await test_core_integration():
        tests_passed += 1
        safe_print("Test 2 PASSED", True)
    else:
        safe_print("Test 2 FAILED", False)
    
    # Test 3: Scheduler Functionality
    safe_print("\n[TEST 3/3] Scheduler Functionality")
    if await test_scheduler_functionality():
        tests_passed += 1
        safe_print("Test 3 PASSED", True)
    else:
        safe_print("Test 3 FAILED", False)
    
    # Final Summary
    safe_print("\n" + "=" * 70)
    safe_print("COMPREHENSIVE TEST SUMMARY")
    safe_print("=" * 70)
    safe_print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        safe_print("ALL TESTS PASSED - System Ready for Production!", True)
        
        safe_print("\nEnhanced Job Search Intelligence Features:")
        safe_print("  - Automated weekly reporting")
        safe_print("  - Database storage and analytics") 
        safe_print("  - Telegram notifications")
        safe_print("  - CSV/JSON export capabilities")
        safe_print("  - Real LinkedIn data integration")
        
        safe_print("\nScheduled Reports Available:")
        safe_print("  - Monday 9:00 AM - Deep Dive with Enhanced Analytics")
        safe_print("  - Wednesday 12:00 PM - Market Scan with Network Analysis")
        safe_print("  - Friday 5:00 PM - Predictive Analysis with Intelligence")
        safe_print("  - Sunday 10:00 AM - Comprehensive Report with Full Analytics")
        
        safe_print("\nTo start automated scheduling:")
        safe_print("  python automation/weekly_automation_scheduler.py")
        
        return True
    else:
        safe_print(f"{total_tests - tests_passed} TESTS FAILED", False)
        safe_print("Please review errors above before proceeding")
        return False

if __name__ == "__main__":
    # Run the comprehensive test
    try:
        success = asyncio.run(run_comprehensive_test())
        
        if success:
            safe_print("\nSystem Integration Complete and Verified!", True)
            sys.exit(0)
        else:
            safe_print("\nPlease address test failures before proceeding", False)
            sys.exit(1)
            
    except KeyboardInterrupt:
        safe_print("\nTest interrupted by user", False)
        sys.exit(1)
    except Exception as e:
        safe_print(f"\nTest runner failed: {str(e)}", False)
        sys.exit(1)