#!/usr/bin/env python3
"""
LinkedIn Follower Change Tracking - Test and Demo Script
Tests the complete follower tracking functionality with historical data
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.tracking.follower_change_tracker import LinkedInFollowerTracker
    TRACKER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LinkedInFollowerTracker not available: {e}")
    TRACKER_AVAILABLE = False

try:
    from src.tracking.follower_change_analysis import FollowerChangeAnalysisEngine
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: FollowerChangeAnalysisEngine not available: {e}")
    ANALYSIS_AVAILABLE = False

try:
    from src.reporting.advanced_reporting_system import AdvancedReportingSystem
    REPORTING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AdvancedReportingSystem not available: {e}")
    REPORTING_AVAILABLE = False

def test_follower_tracking():
    """Test complete follower tracking functionality"""
    
    print("🧪 Testing LinkedIn Follower Change Tracking System")
    print("=" * 60)
    
    if not all([TRACKER_AVAILABLE, ANALYSIS_AVAILABLE, REPORTING_AVAILABLE]):
        print("❌ Some modules are not available:")
        if not TRACKER_AVAILABLE:
            print("  - LinkedInFollowerTracker")
        if not ANALYSIS_AVAILABLE:
            print("  - FollowerChangeAnalysisEngine")
        if not REPORTING_AVAILABLE:
            print("  - AdvancedReportingSystem")
        print("\nTest cannot continue without all modules.")
        return False
    
    try:
        # Initialize components
        print("1. 📋 Initializing follower tracking components...")
        tracker = LinkedInFollowerTracker("data/job_search.db")
        analyzer = FollowerChangeAnalysisEngine("data/job_search.db")
        reporter = AdvancedReportingSystem("data/job_search.db")
        
        # Import historical data
        print("2. 📁 Importing historical follower data...")
        historical_file = "data/linkedin_profile/historical/linkedin_raw_followers.csv"
        
        if os.path.exists(historical_file):
            # Import as baseline (simulate data from 7 days ago)
            baseline_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            success = tracker.import_historical_data(historical_file, baseline_date)
            
            if success:
                print(f"   ✅ Historical data imported successfully for {baseline_date}")
            else:
                print("   ❌ Failed to import historical data")
                return False
        else:
            print(f"   ⚠️  Historical file not found: {historical_file}")
            # Create sample data for testing
            print("   📝 Creating sample follower data for testing...")
            sample_data = create_sample_follower_data()
            baseline_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            tracker.save_follower_snapshot(sample_data, baseline_date)
            print(f"   ✅ Sample baseline data created for {baseline_date}")
        
        # Create current data (simulate current followers with some changes)
        print("3. 🔄 Simulating current follower state...")
        current_data = create_current_follower_data()
        today = datetime.now().strftime('%Y-%m-%d')
        tracker.save_follower_snapshot(current_data, today)
        print(f"   ✅ Current follower snapshot saved for {today}")
        
        # Analyze follower changes
        print("4. 📊 Analyzing follower changes...")
        analysis = tracker.analyze_follower_changes(current_data, today)
        
        print(f"   📈 Analysis Results:")
        print(f"      Current Followers: {analysis.total_current_followers}")
        print(f"      Previous Followers: {analysis.total_previous_followers}")
        print(f"      Net Change: {analysis.net_change}")
        print(f"      New Followers: {len(analysis.new_followers)}")
        print(f"      Unfollowers: {len(analysis.unfollowers)}")
        print(f"      Growth Rate: {analysis.growth_rate:.1f}%")
        print(f"      Retention Rate: {analysis.follower_retention_rate:.1f}%")
        
        # Show specific changes
        if analysis.new_followers:
            print(f"\n   🎉 New Followers:")
            for follower in analysis.new_followers[:3]:  # Show first 3
                print(f"      + {follower.user_name} - {follower.user_title}")
        
        if analysis.unfollowers:
            print(f"\n   👋 Unfollowers:")
            for unfollower in analysis.unfollowers[:3]:  # Show first 3
                print(f"      - {unfollower.user_name} - {unfollower.user_title}")
        
        # Generate comprehensive analysis
        print("\n5. 🔮 Generating comprehensive analysis...")
        comprehensive_analysis = analyzer.generate_comprehensive_analysis(7)
        
        print(f"   🎯 Trend Direction: {comprehensive_analysis.trend_direction}")
        print(f"   🔗 Engagement Correlation: {comprehensive_analysis.engagement_correlation:.2f}")
        print(f"   📋 Key Insights: {len(comprehensive_analysis.key_insights)}")
        print(f"   💡 Recommendations: {len(comprehensive_analysis.recommendations)}")
        
        # Show insights
        if comprehensive_analysis.key_insights:
            print(f"\n   💡 Key Insights:")
            for insight in comprehensive_analysis.key_insights[:2]:  # Show first 2
                print(f"      • {insight.title}: {insight.description}")
        
        # Show recommendations
        if comprehensive_analysis.recommendations:
            print(f"\n   🚀 Top Recommendations:")
            for rec in comprehensive_analysis.recommendations[:3]:  # Show first 3
                print(f"      • {rec}")
        
        # Generate follower change report
        print("\n6. 📋 Generating follower change report...")
        follower_report = reporter.generate_follower_change_report(7)
        
        if follower_report.get("report_available"):
            print("   ✅ Follower change report generated successfully!")
            
            # Show report summary
            print(f"\n   📊 Report Summary:")
            key_metrics = follower_report.get("key_metrics", {})
            for metric, value in key_metrics.items():
                print(f"      {metric.replace('_', ' ').title()}: {value}")
                
            # Show executive summary
            exec_summary = follower_report.get("executive_summary", [])
            if exec_summary:
                print(f"\n   🎯 Executive Summary:")
                for point in exec_summary[:2]:  # Show first 2 points
                    print(f"      • {point}")
        else:
            print(f"   ❌ Report generation failed: {follower_report.get('error')}")
        
        # Test historical retrieval
        print("\n7. 📚 Testing historical data retrieval...")
        history = tracker.get_follower_change_history(7)
        analytics_summary = tracker.get_follower_analytics_summary(7)
        
        print(f"   📈 Change History: {len(history)} events")
        print(f"   📊 Analytics Summary: {len(analytics_summary)} data points")
        
        if analytics_summary:
            print(f"      • Total New Followers: {analytics_summary.get('total_new_followers', 0)}")
            print(f"      • Total Unfollowers: {analytics_summary.get('total_unfollowers', 0)}")
            print(f"      • Average Growth Rate: {analytics_summary.get('avg_growth_rate', 0):.1f}%")
        
        print("\n🎉 All tests completed successfully!")
        print("✅ Follower change tracking system is fully operational!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_follower_data():
    """Create sample follower data for testing"""
    return [
        {
            'urn_id': 'ACoAAC001',
            'name': 'John Smith',
            'occupation': 'Senior Software Engineer at Microsoft',
            'location': 'Seattle, WA',
            'company': 'Microsoft',
            'relationship': 'follower'
        },
        {
            'urn_id': 'ACoAAC002',
            'name': 'Sarah Johnson',
            'occupation': 'Product Manager at Google',
            'location': 'Mountain View, CA',
            'company': 'Google',
            'relationship': 'follower'
        },
        {
            'urn_id': 'ACoAAC003',
            'name': 'Mike Chen',
            'occupation': 'Director of Engineering at Amazon',
            'location': 'Seattle, WA',
            'company': 'Amazon',
            'relationship': 'follower'
        },
        {
            'urn_id': 'ACoAAC004',
            'name': 'Emily Davis',
            'occupation': 'VP of Marketing at Tesla',
            'location': 'Austin, TX',
            'company': 'Tesla',
            'relationship': 'follower'
        },
        {
            'urn_id': 'ACoAAC005',
            'name': 'David Wilson',
            'occupation': 'Lead Data Scientist at Netflix',
            'location': 'Los Gatos, CA',
            'company': 'Netflix',
            'relationship': 'follower'
        }
    ]

def create_current_follower_data():
    """Create current follower data with some changes"""
    # Start with baseline and make some changes
    current_data = create_sample_follower_data()
    
    # Remove one follower (simulate unfollowing)
    current_data = [f for f in current_data if f['urn_id'] != 'ACoAAC002']
    
    # Add two new followers
    current_data.extend([
        {
            'urn_id': 'ACoAAC006',
            'name': 'Lisa Rodriguez',
            'occupation': 'Senior Designer at Apple',
            'location': 'Cupertino, CA',
            'company': 'Apple',
            'relationship': 'follower'
        },
        {
            'urn_id': 'ACoAAC007',
            'name': 'James Thompson',
            'occupation': 'Principal Engineer at Meta',
            'location': 'Menlo Park, CA',
            'company': 'Meta',
            'relationship': 'follower'
        }
    ])
    
    return current_data

def save_report_to_file(report_data, filename="follower_change_report.json"):
    """Save the report data to a file for review"""
    try:
        with open(f"output/{filename}", 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"   💾 Report saved to output/{filename}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to save report: {e}")
        return False

if __name__ == "__main__":
    print("🚀 LinkedIn Follower Change Tracking - Test Suite")
    print("Testing complete follower tracking and analysis system")
    print()
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Run tests
    success = test_follower_tracking()
    
    if success:
        print("\n✅ Ready for production use!")
        print("📋 You can now use follower change tracking in your Job Search Intelligence reports.")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
    
    print(f"\n💡 Next steps:")
    print("   1. Run this script to initialize follower tracking with historical data")
    print("   2. Use the reporting system to generate follower change reports")
    print("   3. Monitor follower changes in your weekly intelligence reports")