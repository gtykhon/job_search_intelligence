#!/usr/bin/env python3
"""
Test LinkedIn Data Cache Management
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_cache_management():
    try:
        print("🔍 Testing LinkedIn Data Cache Management...")
        
        from src.intelligence.real_linkedin_data_collector import RealLinkedInDataCollector
        collector = RealLinkedInDataCollector()
        
        # Test cache info
        print("📋 Current cache status:")
        cache_info = collector.get_cache_info()
        for key, value in cache_info.items():
            print(f"   • {key}: {value}")
        
        # Test normal collection (should use cache if available)
        print("\n🔍 Normal data collection (cache enabled):")
        data1 = await collector.collect_real_network_intelligence()
        print(f"   • Data source: {data1.get('data_source', 'N/A')}")
        print(f"   • Connections: {data1.get('total_connections', 'N/A')}")
        
        # Test cache freshness check
        print(f"\n⏰ Is data fresh? {collector.is_data_fresh()}")
        
        # Test force refresh
        print("\n🔄 Testing force refresh:")
        collector.set_force_refresh(True)
        data2 = await collector.collect_real_network_intelligence()
        print(f"   • Data source: {data2.get('data_source', 'N/A')}")
        print(f"   • Connections: {data2.get('total_connections', 'N/A')}")
        
        # Reset force refresh
        collector.set_force_refresh(False)
        
        # Test cache info again
        print("\n📋 Updated cache status:")
        cache_info = collector.get_cache_info()
        for key, value in cache_info.items():
            print(f"   • {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cache_management())
    sys.exit(0 if success else 1)