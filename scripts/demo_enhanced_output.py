"""
Demo script to showcase enhanced Job Search Intelligence output management
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.output_manager import OutputManager
from enhanced_analyzer import EnhancedLinkedInAnalyzer
import json
from datetime import datetime

async def demo_enhanced_features():
    """Demonstrate enhanced output management features"""
    
    print("🚀 Job Search Intelligence - Enhanced Output Demo")
    print("=" * 60)
    
    analyzer = EnhancedLinkedInAnalyzer()
    
    # Demo 1: Run AI Analysis with enhanced output
    print("\n1️⃣ Running AI Analysis with Enhanced Output Management...")
    print("-" * 50)
    
    try:
        result = await analyzer.run_enhanced_ai_analysis("demo_user")
        if result["success"]:
            print(f"✅ AI Analysis completed!")
            print(f"📁 Session ID: {result['session_id']}")
            print(f"⏱️  Duration: {result['duration']:.2f}s")
            print(f"📄 File saved to: {result['file_path']}")
        else:
            print(f"❌ AI Analysis failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Demo AI analysis error: {e}")
    
    # Demo 2: Run Network Analysis
    print("\n2️⃣ Running Network Analysis with CSV Export...")
    print("-" * 50)
    
    try:
        network_result = await analyzer.run_network_analysis("demo_user")
        if network_result["success"]:
            print(f"✅ Network Analysis completed!")
            print(f"📁 JSON results: {network_result['file_path']}")
            print(f"📊 CSV export: {network_result['csv_path']}")
            print(f"🔗 Total connections: {network_result['data']['total_connections']}")
        else:
            print(f"❌ Network analysis failed: {network_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Demo network analysis error: {e}")
    
    # Demo 3: Generate Daily Report
    print("\n3️⃣ Generating Daily Report...")
    print("-" * 50)
    
    try:
        report_path = analyzer.output_manager.generate_daily_report()
        print(f"✅ Daily report generated: {report_path}")
        
        # Show report content
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        print(f"📊 Report Summary:")
        print(f"   - Date: {report_data['date']}")
        print(f"   - Total analyses: {report_data['total_analyses']}")
        print(f"   - AI insights: {report_data['summary']['ai_insights']}")
        print(f"   - Network analyses: {report_data['summary']['network_analyses']}")
        
    except Exception as e:
        print(f"❌ Report generation error: {e}")
    
    # Demo 4: Show Analysis History
    print("\n4️⃣ Analysis History (Database Integration)...")
    print("-" * 50)
    
    try:
        history = analyzer.get_analysis_history(days=1)
        print(f"📈 Found {len(history)} recent analyses")
    except Exception as e:
        print(f"❌ History retrieval error: {e}")
    
    # Demo 5: Show organized file structure
    print("\n5️⃣ Enhanced File Organization...")
    print("-" * 50)
    
    output_manager = OutputManager()
    
    print("📁 New organized structure:")
    print("output/")
    print("  ├── analyses/")
    print("  │   ├── insights/    # AI analysis results")
    print("  │   ├── networks/    # Network analysis")
    print("  │   └── profiles/    # Profile analysis")
    print("  ├── exports/")
    print("  │   ├── csv/         # CSV exports")
    print("  │   ├── json/        # JSON exports")
    print("  │   └── excel/       # Excel exports")
    print("  ├── reports/")
    print("  │   ├── daily/       # Daily summaries")
    print("  │   ├── weekly/      # Weekly reports")
    print("  │   └── monthly/     # Monthly reports")
    print("  └── archive/         # Old files")
    
    # Demo 6: Database Benefits
    print("\n6️⃣ Database Integration Benefits...")
    print("-" * 50)
    
    print("💾 SQLite Database Features:")
    print("   ✅ Structured data storage")
    print("   ✅ Relationship tracking")
    print("   ✅ Time series analysis")
    print("   ✅ Complex queries")
    print("   ✅ Data integrity")
    print("   ✅ Performance optimization")
    print("   ✅ Historical analysis")
    
    print("\n🎯 Hybrid Approach Benefits:")
    print("   📄 Files: Human-readable reports, exports, visualizations")
    print("   💾 Database: Structured data, relationships, analytics")
    print("   🔗 Integration: Best of both worlds")
    
    print("\n✨ Summary of Enhancements:")
    print("=" * 60)
    print("✅ Organized timestamp-based file structure")
    print("✅ SQLite database with proper schema")
    print("✅ Automated daily/weekly/monthly reports")
    print("✅ CSV/JSON/Excel export capabilities")
    print("✅ Analysis history tracking")
    print("✅ File archival system")
    print("✅ Performance metrics storage")
    print("✅ Hybrid file + database approach")
    
    return True

if __name__ == "__main__":
    asyncio.run(demo_enhanced_features())
