"""
Test Enhanced LinkedIn Analyzer
"""

import sys
import asyncio

sys.path.append('src')
from intelligence.enhanced_linkedin_analyzer import EnhancedLinkedInAnalyzer

async def test_enhanced_analyzer():
    """Test the enhanced LinkedIn analyzer functionality"""
    print("🚀 Testing Enhanced LinkedIn Analyzer")
    
    try:
        # Initialize analyzer
        analyzer = EnhancedLinkedInAnalyzer(debug=True)
        print("✅ Analyzer initialized successfully")
        
        # Test cache info
        cache_info = analyzer.get_cache_info()
        print(f"📊 Cache Status: {cache_info.get('status', 'unknown')}")
        
        if cache_info.get('age_hours') is not None:
            print(f"🕒 Cache Age: {cache_info['age_hours']:.1f} hours")
        
        # Test data freshness
        is_fresh = analyzer.is_data_fresh()
        print(f"💾 Data Fresh: {is_fresh}")
        
        # Test enhanced analysis (quick test)
        print("\\n🔍 Running enhanced network analysis...")
        results = await analyzer.analyze_enhanced_network()
        
        # Display results
        print("\\n📈 Enhanced Analysis Results:")
        print("==============================")
        
        real_data = results.get('real_data', {})
        combined = results.get('combined_metrics', {})
        
        print(f"Total Connections: {real_data.get('total_connections', 'N/A')}")
        print(f"Leadership Engagement: {real_data.get('leadership_engagement', 'N/A')}")
        print(f"F500 Penetration: {real_data.get('f500_penetration', 'N/A')}")
        print(f"Profile: {real_data.get('profile_name', 'N/A')}")
        print(f"Unique Companies: {combined.get('unique_companies', 'N/A')}")
        print(f"Unique Locations: {combined.get('unique_locations', 'N/A')}")
        print(f"Avg Connection Strength: {combined.get('average_connection_strength', 0):.2f}")
        
        print("\\n✅ Enhanced analyzer test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_analyzer())
    exit(0 if success else 1)