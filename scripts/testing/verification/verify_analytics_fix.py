#!/usr/bin/env python3
"""
Verification Script - Final Analytics Engine Test
Confirms that the database schema fix is working correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Force fresh import
if 'src.analytics.advanced_analytics_engine' in sys.modules:
    del sys.modules['src.analytics.advanced_analytics_engine']

from src.analytics.advanced_analytics_engine import AdvancedAnalyticsEngine

def final_verification():
    """Final verification that all analytics are working"""
    
    print("🎯 FINAL VERIFICATION - LinkedIn Analytics Engine")
    print("=" * 60)
    
    # Initialize engine
    engine = AdvancedAnalyticsEngine('job_search.db')
    
    # Test exact scenario from dashboard
    print("📊 Testing EXACT dashboard scenario:")
    print("   Metrics: leadership_engagement_percentage, comment_quality_score, f500_penetration_percentage") 
    print("   Time Range: 7 days")
    print("   Analysis Type: Trend Analysis")
    print()
    
    metrics = ['leadership_engagement_percentage', 'comment_quality_score', 'f500_penetration_percentage']
    all_success = True
    
    for i, metric in enumerate(metrics, 1):
        print(f"🔍 Test {i}/3: {metric}")
        
        try:
            # This is the exact call that was failing in the dashboard
            trend = engine.analyze_trends(metric, 7)
            
            print(f"   ✅ SUCCESS!")
            print(f"   📈 Trend: {trend.trend_direction}")
            print(f"   💡 Current Value: {trend.current_value}")
            print(f"   📅 7-day Change: {trend.percentage_change_7d:+.1f}%")
            
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            all_success = False
        
        print()
    
    # Additional tests
    print("🧪 Additional Verification Tests:")
    
    # Test database connection
    try:
        data = engine.load_historical_data(7)
        print(f"   ✅ Database connection: {len(data)} records loaded")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        all_success = False
    
    # Test benchmarking
    try:
        benchmark = engine.benchmark_performance('leadership_engagement_percentage')
        print(f"   ✅ Benchmarking: Grade {benchmark.performance_grade}")
    except Exception as e:
        print(f"   ❌ Benchmarking failed: {e}")
        all_success = False
    
    print()
    print("=" * 60)
    
    if all_success:
        print("🎉 VERIFICATION COMPLETE - ALL SYSTEMS OPERATIONAL!")
        print()
        print("✅ Analytics Engine: WORKING")
        print("✅ Database Schema: COMPATIBLE") 
        print("✅ Trend Analysis: FUNCTIONAL")
        print("✅ Dashboard Ready: YES")
        print()
        print("🚀 Your dashboard at http://localhost:8000 should now work perfectly!")
        print("   Select your metrics and run Trend Analysis - no more errors!")
        
    else:
        print("⚠️  VERIFICATION FAILED - Some issues detected")
        print("   Please review the errors above")
    
    return all_success

if __name__ == "__main__":
    final_verification()