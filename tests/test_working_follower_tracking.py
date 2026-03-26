#!/usr/bin/env python3
"""
Comprehensive Follower Tracking Test
Tests the complete follower tracking functionality with sample data
"""
import sys
import os
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.tracking.follower_change_tracker import LinkedInFollowerTracker
from src.tracking.follower_change_analysis import FollowerChangeAnalysisEngine

def create_sample_data():
    """Create sample follower data for testing"""
    base_date = datetime.now() - timedelta(days=30)
    
    # Sample followers data over time
    followers_data = []
    
    # Initial follower set (30 days ago)
    initial_followers = [
        {"user_id": f"user_{i}", "user_name": f"User {i}", "user_title": f"Title {i}", "user_company": f"Company {i // 5}"}
        for i in range(1, 101)  # 100 initial followers
    ]
    
    # Generate daily snapshots with changes
    current_followers = initial_followers.copy()
    
    for day in range(30):
        current_date = base_date + timedelta(days=day)
        
        # Simulate some followers leaving (1-3 per day)
        if day > 5 and len(current_followers) > 2:
            for _ in range(min(3, len(current_followers) - 50)):
                if current_followers:
                    current_followers.pop()
        
        # Simulate new followers joining (2-5 per day)
        new_follower_count = min(5, 3 + (day % 3))
        for i in range(new_follower_count):
            new_id = 100 + day * 10 + i
            current_followers.append({
                "user_id": f"user_{new_id}",
                "user_name": f"New User {new_id}",
                "user_title": f"Professional {new_id}",
                "user_company": f"NewCorp {new_id // 10}"
            })
        
        followers_data.append({
            "date": current_date,
            "followers": current_followers.copy(),
            "total_count": len(current_followers)
        })
    
    return followers_data

def test_comprehensive_tracking():
    """Test comprehensive follower tracking with sample data"""
    
    print("🧪 Comprehensive Follower Tracking Test")
    print("=" * 50)
    
    try:
        # Initialize components
        print("1. 📋 Initializing components...")
        tracker = LinkedInFollowerTracker("data/test_follower_tracking.db")
        analyzer = FollowerChangeAnalysisEngine("data/test_follower_tracking.db")
        
        print("✅ Components initialized successfully")
        
        # Create sample data
        print("\n2. 📊 Creating sample follower data...")
        sample_data = create_sample_data()
        print(f"✅ Created {len(sample_data)} days of sample data")
        
        # Process data through tracker
        print("\n3. 🔄 Processing follower data...")
        processed_days = 0
        
        for day_data in sample_data:
            try:
                # Save snapshot
                tracker.save_follower_snapshot(day_data["followers"], day_data["date"])
                processed_days += 1
                
                if processed_days % 10 == 0:
                    print(f"   Processed {processed_days} days...")
                    
            except Exception as e:
                print(f"   Error processing day {day_data['date']}: {e}")
        
        print(f"✅ Processed {processed_days} days of data")
        
        # Analyze follower changes
        print("\n4. 📈 Analyzing follower changes...")
        
        # Get recent analysis
        analysis = analyzer.generate_comprehensive_analysis(days=30)
        print(f"✅ Generated analysis for last 30 days")
        
        # Get change history
        change_history = tracker.get_follower_change_history(days=30)
        print(f"✅ Retrieved {len(change_history)} change events")
        
        # Get analytics summary
        analytics = tracker.get_follower_analytics_summary(days=30)
        print(f"✅ Generated analytics summary")
        
        # Display results
        print("\n5. 📊 Results Summary:")
        print("-" * 30)
        
        print(f"📈 Growth Rate: {analysis.growth_rate:.2f}%")
        print(f"📊 Trend Direction: {analysis.trend_direction}")
        print(f"🎯 Retention Rate: {analysis.retention_rate:.2f}%")
        print(f"⚡ Engagement Correlation: {analysis.engagement_correlation:.2f}")
        
        print(f"\n📊 Analytics Summary:")
        print(f"   Total Followers Change: {analytics.get('net_follower_change', 0)}")
        print(f"   New Followers: {analytics.get('total_new_followers', 0)}")
        print(f"   Lost Followers: {analytics.get('total_unfollowers', 0)}")
        print(f"   Current Followers: {analytics.get('current_followers', 0)}")
        
        print(f"\n🔍 Key Insights:")
        for i, insight in enumerate(analysis.key_insights[:3], 1):
            print(f"   {i}. {insight.description}")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(analysis.recommendations[:3], 1):
            print(f"   {i}. {rec}")
        
        # Test report generation
        print("\n6. 📋 Testing Report Generation...")
        report = analyzer.generate_follower_report(days=30)
        print(f"✅ Generated comprehensive follower report")
        
        print(f"\n📋 Report Summary:")
        print(f"   Report Period: {report['report_metadata']['analysis_period']}")
        print(f"   Data Points: {report['report_metadata']['data_points']}")
        print(f"   Recent Followers: {len(report['recent_followers'])}")
        print(f"   Recent Unfollowers: {len(report['recent_unfollowers'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Follower Tracking Test")
    print("=" * 60)
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    success = test_comprehensive_tracking()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Follower tracking system is working correctly.")
        print("📁 Test database saved as: data/test_follower_tracking.db")
    else:
        print("❌ Test failed. Check the error messages above.")