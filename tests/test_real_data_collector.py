#!/usr/bin/env python3
"""
Test Real LinkedIn Data Collector
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_real_data_collector():
    try:
        print("🔍 Testing Real LinkedIn Data Collector...")
        
        from src.intelligence.real_linkedin_data_collector import RealLinkedInDataCollector
        collector = RealLinkedInDataCollector()
        
        # Test data collection
        print("🔍 Testing network intelligence collection...")
        network_data = await collector.collect_real_network_intelligence()
        
        print(f"✅ Network data collected successfully!")
        print(f"   • Total Connections: {network_data.get('total_connections', 'N/A')}")
        print(f"   • Leadership Engagement: {network_data.get('leadership_engagement', 'N/A')}")
        print(f"   • F500 Penetration: {network_data.get('f500_penetration', 'N/A')}")
        print(f"   • Senior Connections: {network_data.get('senior_connections', 'N/A')}")
        print(f"   • Data Source: {network_data.get('data_source', 'N/A')}")
        print(f"   • Profile Name: {network_data.get('profile_name', 'N/A')}")
        
        # Test job opportunities collection
        print("🔍 Testing job opportunities collection...")
        search_criteria = {
            "keywords": ["python", "software engineer"],
            "location": "remote",
            "experience_level": "mid"
        }
        
        opportunities = await collector.collect_real_job_opportunities(search_criteria)
        print(f"✅ Job opportunities collected: {len(opportunities)} found")
        
        if opportunities:
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"   {i}. {opp.get('title', 'Unknown')} at {opp.get('company', 'Unknown')} - {opp.get('match', 'N/A')} match")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_data_collector())
    sys.exit(0 if success else 1)