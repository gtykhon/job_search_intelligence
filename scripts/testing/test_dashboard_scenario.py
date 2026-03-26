#!/usr/bin/env python3
"""
Direct test of the analytics engine with the exact metrics from the dashboard error
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Clear any cached modules
if 'src.analytics.advanced_analytics_engine' in sys.modules:
    del sys.modules['src.analytics.advanced_analytics_engine']

# Fresh import
from src.analytics.advanced_analytics_engine import AdvancedAnalyticsEngine

def test_exact_dashboard_scenario():
    """Test the exact scenario that was failing in the dashboard"""
    
    print("🧪 Testing exact dashboard scenario...")
    print("=" * 50)
    
    # Initialize analytics engine (same as dashboard)
    engine = AdvancedAnalyticsEngine('job_search.db')
    
    # Test the exact metrics that were failing
    metrics = ['leadership_engagement_percentage', 'comment_quality_score', 'f500_penetration_percentage']
    time_range = 7  # 7 days as requested
    
    print(f"📊 Testing {len(metrics)} metrics with {time_range}-day time range...")
    print()
    
    results = {}
    
    for metric in metrics:
        print(f"🔍 Analyzing {metric}...")
        try:
            # This is the exact call that was failing
            trend = engine.analyze_trends(metric, time_range)
            
            print(f"  ✅ SUCCESS!")
            print(f"  📈 Trend Direction: {trend.trend_direction}")
            print(f"  📊 Current Value: {trend.current_value}")
            print(f"  📅 7-day Change: {trend.percentage_change_7d}%")
            print(f"  🔮 7-day Forecast: {trend.forecast_7d}")
            print(f"  🎯 Confidence: {trend.confidence_interval}")
            
            results[metric] = {
                'status': 'success',
                'trend': trend
            }
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results[metric] = {
                'status': 'error',
                'error': str(e)
            }
        
        print()
    
    # Summary
    print("=" * 50)
    print("📋 SUMMARY:")
    
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_count = len(results)
    
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Analytics engine is working correctly.")
        print("🚀 Dashboard should now work without errors.")
    else:
        print(f"\n⚠️  Some tests failed. Investigating...")
        for metric, result in results.items():
            if result['status'] == 'error':
                print(f"   {metric}: {result['error']}")
    
    return results

if __name__ == "__main__":
    test_exact_dashboard_scenario()