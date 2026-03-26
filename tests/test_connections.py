#!/usr/bin/env python3
"""
Test LinkedIn Connection Data Extraction
Extract actual connection data from LinkedIn
"""

import asyncio
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_connection_extraction():
    """Test LinkedIn connection data extraction"""
    try:
        # Import our components
        from src.config import get_config
        from src.core.job_search_intelligence import LinkedInIntelligenceEngine
        from src.resources import ResourceManager
        
        print("🔗 Testing LinkedIn Connection Data Extraction")
        print("=" * 60)
        
        # Load configuration
        config = get_config()
        print(f"✅ Configuration loaded")
        print(f"   LinkedIn Username: {config.linkedin.username}")
        print(f"   Session Timeout: {config.linkedin.session_timeout}s")
        
        # Initialize resource manager
        resource_manager = ResourceManager(config)
        await resource_manager.initialize()
        print("✅ Resource manager initialized")
        
        # Initialize LinkedIn intelligence engine
        intelligence_engine = LinkedInIntelligenceEngine(config, resource_manager)
        await intelligence_engine.initialize()
        print("✅ LinkedIn intelligence engine initialized")
        
        # Test profile access first
        print("\n🔍 Testing profile access...")
        try:
            profile_data = await intelligence_engine.get_user_profile()
            if profile_data:
                print(f"✅ Profile accessed successfully")
                print(f"   Name: {profile_data.get('firstName', 'N/A')} {profile_data.get('lastName', 'N/A')}")
                print(f"   Identifier: {profile_data.get('publicIdentifier', 'N/A')}")
                print(f"   Headline: {profile_data.get('headline', 'N/A')[:50]}...")
            else:
                print("❌ No profile data retrieved")
                return
        except Exception as e:
            print(f"❌ Profile access failed: {e}")
            return
        
        # Test connection analysis (which includes connection extraction)
        print("\n🔗 Testing network analysis...")
        try:
            network_analysis = await intelligence_engine.analyze_network(max_connections=10)  # Start with just 10
            
            if network_analysis and 'connections' in network_analysis:
                connections = network_analysis['connections']
                print(f"✅ Network analysis completed successfully")
                print(f"   Total connections analyzed: {len(connections)}")
                print(f"   Connection count: {network_analysis.get('connection_count', 0)}")
                
                # Display first few connections
                if connections and len(connections) > 0:
                    print("\n📊 Sample connections:")
                    for i, conn in enumerate(connections[:3]):
                        print(f"   {i+1}. {conn.get('firstName', 'N/A')} {conn.get('lastName', 'N/A')}")
                        print(f"      Company: {conn.get('companyName', 'N/A')}")
                        print(f"      Title: {conn.get('title', 'N/A')}")
                        print(f"      Location: {conn.get('location', 'N/A')}")
                        print()
                
                # Save network analysis data
                output_file = Path("output") / "network_analysis_test.json"
                output_file.parent.mkdir(exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "profile": profile_data,
                        "network_analysis": network_analysis,
                        "extracted_at": "2025-08-20T15:30:00"
                    }, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Network analysis saved to: {output_file}")
                
                # Test with AI analysis if we have connections
                if connections and len(connections) > 0:
                    print("\n🧠 Generating AI insights for network...")
                    from src.core.analysis_engine import AnalysisEngine
                    
                    analysis_engine = AnalysisEngine(config, resource_manager)
                    await analysis_engine.initialize()
                    
                    # Prepare network analysis data
                    network_data = {
                        "profile": profile_data,
                        "connections": connections,
                        "network_analysis": {
                            "total_connections": len(connections),
                            "industries": list(set([c.get('industry', 'Unknown') for c in connections if c.get('industry')])),
                            "locations": list(set([c.get('location', 'Unknown') for c in connections if c.get('location')])),
                            "companies": list(set([c.get('companyName', 'Unknown') for c in connections if c.get('companyName')]))
                        }
                    }
                    
                    # Generate AI insights
                    insights = await analysis_engine.generate_ai_insights(network_data, insight_type="network_analysis")
                    
                    print("🤖 AI Network Insights:")
                    print("=" * 40)
                    if isinstance(insights.get('insights'), str):
                        print(insights['insights'][:500] + "..." if len(insights['insights']) > 500 else insights['insights'])
                    
                    await analysis_engine.cleanup()
                
            else:
                print("❌ No network analysis data or connections found")
                print("   This might be due to:")
                print("   • LinkedIn privacy settings")
                print("   • Rate limiting")
                print("   • Authentication issues")
                print("   • Network connectivity")
        
        except Exception as e:
            print(f"❌ Network analysis failed: {e}")
            logger.exception("Network analysis error")
        
        # Cleanup
        await intelligence_engine.cleanup()
        await resource_manager.cleanup()
        
        print("\n✅ Network analysis test completed!")
        
    except Exception as e:
        logger.error(f"❌ Connection extraction test failed: {e}")
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_connection_extraction())
