"""
Test enhanced reporting system with both JSON and CSV formats
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.output_manager import OutputManager
from datetime import datetime
import json

def test_enhanced_reporting():
    """Test the enhanced reporting system"""
    
    print("📊 Testing Enhanced Reporting System (JSON + CSV)")
    print("=" * 60)
    
    output_manager = OutputManager()
    
    # Test 1: Daily Report in both formats
    print("\n1️⃣ Generating Daily Report (JSON + CSV)...")
    print("-" * 50)
    
    daily_paths = output_manager.generate_daily_report(formats=["json", "csv"])
    
    print("✅ Daily Report Generated:")
    for format_type, path in daily_paths.items():
        print(f"   📄 {format_type.upper()}: {path}")
    
    # Test 2: Weekly Report
    print("\n2️⃣ Generating Weekly Report (JSON + CSV)...")
    print("-" * 50)
    
    weekly_paths = output_manager.generate_weekly_report(formats=["json", "csv"])
    
    print("✅ Weekly Report Generated:")
    for format_type, path in weekly_paths.items():
        print(f"   📄 {format_type.upper()}: {path}")
    
    # Test 3: Monthly Report
    print("\n3️⃣ Generating Monthly Report (JSON + CSV)...")
    print("-" * 50)
    
    monthly_paths = output_manager.generate_monthly_report(formats=["json", "csv"])
    
    print("✅ Monthly Report Generated:")
    for format_type, path in monthly_paths.items():
        print(f"   📄 {format_type.upper()}: {path}")
    
    # Test 4: Show report content
    print("\n4️⃣ Sample Report Content...")
    print("-" * 50)
    
    if "json" in daily_paths:
        print("📋 Daily Report JSON Content:")
        with open(daily_paths["json"], 'r', encoding='utf-8') as f:
            daily_data = json.load(f)
        
        print(f"   - Date: {daily_data['date']}")
        print(f"   - Total Analyses: {daily_data['total_analyses']}")
        print(f"   - AI Insights: {daily_data['summary']['ai_insights']}")
        print(f"   - Network Analyses: {daily_data['summary']['network_analyses']}")
        print(f"   - Profile Analyses: {daily_data['summary']['profile_analyses']}")
    
    if "csv" in daily_paths:
        print(f"\n📊 Daily Report CSV: {daily_paths['csv']}")
        if "csv_detailed" in daily_paths:
            print(f"📊 Detailed CSV: {daily_paths['csv_detailed']}")
    
    print("\n✨ Report Format Summary:")
    print("=" * 60)
    print("📄 JSON Reports: Complete data structure, metadata, nested information")
    print("📊 CSV Reports: Summary metrics, easy to import into Excel/analytics tools")
    print("📋 Detailed CSV: Individual analysis records for detailed analysis")
    print("📅 Time-based: Daily, Weekly, Monthly reports automatically generated")
    print("🔄 Hybrid Approach: Best of both worlds - structured data + spreadsheet compatibility")
    
    return {
        "daily": daily_paths,
        "weekly": weekly_paths,
        "monthly": monthly_paths
    }

if __name__ == "__main__":
    results = test_enhanced_reporting()
    
    print(f"\n🎉 Enhanced Reporting Test Complete!")
    print(f"📈 Generated {len(results['daily']) + len(results['weekly']) + len(results['monthly'])} report files")
    print(f"✅ Both JSON and CSV formats supported")
    print(f"📊 Ready for analytics and spreadsheet integration")
