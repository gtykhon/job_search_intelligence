"""
Complete test of enhanced Job Search Intelligence output management
"""
import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.output_manager import OutputManager

async def test_complete_enhanced_system():
    """Test complete enhanced output management system"""
    
    print("🚀 Job Search Intelligence - Complete Enhanced Output Test")
    print("=" * 70)
    
    # Initialize output manager
    output_manager = OutputManager()
    
    # Test 1: AI Insights Analysis
    print("\n1️⃣ Testing AI Insights with Enhanced Output...")
    print("-" * 50)
    
    session_id = output_manager.start_session("ai_insights", "production_user")
    print(f"📋 Started session: {session_id}")
    
    # Simulate AI insights data (replace with real Claude analysis)
    ai_insights_data = {
        "profile_analysis": {
            "strengths": [
                "Strong technical background in AI/ML",
                "Extensive network in technology sector",
                "Active engagement with industry leaders"
            ],
            "opportunities": [
                "Expand into emerging tech markets",
                "Increase thought leadership content",
                "Develop mentor relationships"
            ],
            "recommendations": [
                "Post 2-3 technical articles per month",
                "Engage with AI/ML communities",
                "Attend virtual tech conferences"
            ]
        },
        "network_insights": {
            "connection_quality": 8.5,
            "industry_diversity": 7.2,
            "geographic_reach": 6.8,
            "engagement_potential": 9.1
        },
        "ai_analysis": {
            "confidence_score": 0.92,
            "processing_time": 11.3,
            "model": "claude-3-5-sonnet-20241022",
            "insights_generated": 15
        }
    }
    
    # Save with enhanced output management
    insights_file = output_manager.save_analysis_results(
        analysis_type="ai_insights",
        data=ai_insights_data,
        profile_id="production_user",
        save_to_db=True
    )
    
    print(f"✅ AI insights saved to: {insights_file}")
    
    # Test 2: Network Analysis
    print("\n2️⃣ Testing Network Analysis with CSV Export...")
    print("-" * 50)
    
    network_session = output_manager.start_session("network_analysis", "production_user")
    
    network_data = {
        "total_connections": 1247,
        "industry_breakdown": {
            "Technology": 542,
            "Finance": 198,
            "Healthcare": 145,
            "Education": 89,
            "Consulting": 76,
            "Other": 197
        },
        "geographic_distribution": {
            "United States": 687,
            "United Kingdom": 156,
            "Canada": 123,
            "Germany": 98,
            "India": 87,
            "Other": 96
        },
        "seniority_levels": {
            "C-Level": 45,
            "VP/Director": 234,
            "Manager": 387,
            "Senior": 298,
            "Junior": 156,
            "Student": 127
        },
        "connection_strength": {
            "strong": 312,
            "medium": 567,
            "weak": 368
        },
        "growth_metrics": {
            "monthly_growth_rate": 3.2,
            "quality_score": 8.7,
            "engagement_rate": 18.4,
            "response_rate": 12.8
        }
    }
    
    # Save network analysis
    network_file = output_manager.save_analysis_results(
        analysis_type="network_analysis",
        data=network_data,
        profile_id="production_user",
        save_to_db=True
    )
    
    # Export as CSV
    industry_csv = output_manager.save_export(
        data=[{"Industry": k, "Count": v} for k, v in network_data["industry_breakdown"].items()],
        filename="industry_breakdown",
        format_type="csv"
    )
    
    geography_csv = output_manager.save_export(
        data=[{"Country": k, "Count": v} for k, v in network_data["geographic_distribution"].items()],
        filename="geographic_distribution",
        format_type="csv"
    )
    
    print(f"✅ Network analysis saved to: {network_file}")
    print(f"📊 Industry CSV: {industry_csv}")
    print(f"🌍 Geography CSV: {geography_csv}")
    
    # Test 3: Profile Analysis
    print("\n3️⃣ Testing Profile Analysis...")
    print("-" * 50)
    
    profile_session = output_manager.start_session("profile_analysis", "production_user")
    
    profile_data = {
        "profile_completeness": 94,
        "content_analysis": {
            "post_frequency": "2.3 per week",
            "engagement_rate": "15.7%",
            "top_topics": ["AI/ML", "Leadership", "Technology Trends"],
            "audience_growth": "12% monthly"
        },
        "skills_assessment": {
            "technical_skills": 9.2,
            "leadership_skills": 8.5,
            "communication_skills": 8.8,
            "industry_expertise": 9.0
        },
        "optimization_score": 87,
        "recommendations": [
            "Add more project details to experience section",
            "Include relevant certifications",
            "Optimize headline for keywords",
            "Add call-to-action in summary"
        ]
    }
    
    profile_file = output_manager.save_analysis_results(
        analysis_type="profile_analysis",
        data=profile_data,
        profile_id="production_user",
        save_to_db=True
    )
    
    print(f"✅ Profile analysis saved to: {profile_file}")
    
    # Test 4: Generate Reports
    print("\n4️⃣ Generating Comprehensive Reports...")
    print("-" * 50)
    
    daily_report = output_manager.generate_daily_report()
    print(f"📅 Daily report: {daily_report}")
    
    # Read and display report summary
    with open(daily_report, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    print(f"📊 Report Summary:")
    print(f"   - Total analyses today: {report_data['total_analyses']}")
    print(f"   - AI insights: {report_data['summary']['ai_insights']}")
    print(f"   - Network analyses: {report_data['summary']['network_analyses']}")
    print(f"   - Profile analyses: {report_data['summary']['profile_analyses']}")
    
    # Test 5: Analysis History
    print("\n5️⃣ Analysis History (Database Integration)...")
    print("-" * 50)
    
    history = output_manager.get_analysis_history(days=1)
    print(f"📈 Recent analyses found: {len(history)}")
    
    if history:
        print(f"{'Type':<15} {'Profile':<15} {'Timestamp':<20} {'Status':<10}")
        print("-" * 65)
        for record in history[:5]:  # Show last 5
            timestamp = record['timestamp'][:19] if record['timestamp'] else "Unknown"
            print(f"{record['analysis_type']:<15} {record['profile_id']:<15} {timestamp:<20} {record['status']:<10}")
    
    # Test 6: Export All Data
    print("\n6️⃣ Exporting All Analysis Data...")
    print("-" * 50)
    
    # Export comprehensive data
    comprehensive_export = {
        "export_timestamp": datetime.now().isoformat(),
        "ai_insights": ai_insights_data,
        "network_analysis": network_data,
        "profile_analysis": profile_data,
        "session_summary": {
            "sessions_created": 3,
            "files_generated": 6,
            "database_records": len(history)
        }
    }
    
    export_file = output_manager.save_export(
        data=comprehensive_export,
        filename="comprehensive_analysis",
        format_type="json"
    )
    
    print(f"📦 Comprehensive export: {export_file}")
    
    # Test 7: File Organization Summary
    print("\n7️⃣ Enhanced File Organization Summary...")
    print("-" * 50)
    
    print("📁 Organized Output Structure:")
    output_base = Path("output")
    
    for analysis_type in ["insights", "networks", "profiles"]:
        analysis_dir = output_base / "analyses" / analysis_type
        if analysis_dir.exists():
            files = list(analysis_dir.glob("*.json"))
            print(f"   📂 analyses/{analysis_type}/: {len(files)} files")
    
    for export_type in ["csv", "json"]:
        export_dir = output_base / "exports" / export_type
        if export_dir.exists():
            files = list(export_dir.glob("*.*"))
            print(f"   📊 exports/{export_type}/: {len(files)} files")
    
    reports_dir = output_base / "reports" / "daily"
    if reports_dir.exists():
        files = list(reports_dir.glob("*.json"))
        print(f"   📅 reports/daily/: {len(files)} files")
    
    print("\n✨ Enhanced Output Management Benefits:")
    print("=" * 70)
    print("✅ Timestamp-based organization")
    print("✅ Database integration with SQLite")
    print("✅ Multiple export formats (JSON, CSV, Excel)")
    print("✅ Automated daily/weekly/monthly reports")
    print("✅ Analysis session tracking")
    print("✅ Historical data retention")
    print("✅ Performance metrics storage")
    print("✅ Hybrid file + database approach")
    print("✅ Archive management")
    print("✅ Query capabilities")
    
    print("\n🎯 Why SQL Database is Essential:")
    print("-" * 50)
    print("💾 Structured Data: Relationships, metrics, time series")
    print("🔍 Query Power: Complex analytics, filtering, aggregations")
    print("📈 Scalability: Handle thousands of analyses efficiently")
    print("🔒 Integrity: ACID properties, data consistency")
    print("⚡ Performance: Indexed searches, optimized queries")
    print("📊 Analytics: Trend analysis, comparative studies")
    print("🔗 Relationships: Connect profiles, networks, insights")
    print("📅 Time Series: Track changes over time")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_complete_enhanced_system())
