#!/usr/bin/env python3
"""
Test AI Insights Generation
Generate actual Claude-powered insights about LinkedIn profile
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

async def test_ai_insights():
    """Test Claude AI insights generation"""
    try:
        # Import our components
        from src.config import get_config
        from src.core.analysis_engine import AnalysisEngine
        from src.resources import ResourceManager
        
        print("🧠 Testing AI Insights Generation with Claude")
        print("=" * 60)
        
        # Load configuration
        config = get_config()
        print(f"✅ Configuration loaded")
        print(f"   AI Provider: {config.ai.provider}")
        print(f"   AI Model: {config.ai.model}")
        print(f"   AI Enabled: {config.ai.enabled}")
        
        # Initialize resource manager
        resource_manager = ResourceManager(config)
        await resource_manager.initialize()
        print("✅ Resource manager initialized")
        
        # Initialize analysis engine
        analysis_engine = AnalysisEngine(config, resource_manager)
        await analysis_engine.initialize()
        print("✅ Analysis engine initialized")
        print(f"   Claude client: {'✅ Active' if hasattr(analysis_engine, 'claude_client') else '❌ Not found'}")
        
        # Test profile data (using your actual profile info from previous runs)
        test_profile_data = {
            "firstName": "Grygorii",
            "lastName": "T",
            "publicIdentifier": "example-user",
            "headline": "Tech Professional",
            "location": "Location",
            "industry": "Technology",
            "summary": "Experienced professional in technology sector",
            "experience": [],
            "education": [],
            "skills": [],
            "connections": []
        }
        
        print("\n🔍 Generating AI insights for profile...")
        print(f"   Profile: {test_profile_data['firstName']} {test_profile_data['lastName']}")
        print(f"   Identifier: {test_profile_data['publicIdentifier']}")
        
        # Prepare analysis data format
        analysis_data = {
            "profile": test_profile_data,
            "connections": [],
            "network_analysis": {
                "total_connections": 0,
                "industries": [],
                "locations": [],
                "companies": []
            },
            "insights": {
                "profile_completeness": 0.7,
                "network_diversity": 0.0,
                "professional_interests": []
            }
        }
        
        # Generate insights using Claude
        insights = await analysis_engine.generate_ai_insights(analysis_data, insight_type="profile_analysis")
        
        print("\n🤖 Claude AI Insights Generated:")
        print("=" * 40)
        
        if insights:
            # Display insights in a formatted way
            if isinstance(insights, dict):
                for category, content in insights.items():
                    print(f"\n📊 {category.replace('_', ' ').title()}:")
                    if isinstance(content, list):
                        for item in content:
                            print(f"   • {item}")
                    else:
                        print(f"   {content}")
            else:
                print(f"   {insights}")
                
            # Save insights to file
            output_file = Path("output") / "ai_insights_test.json"
            output_file.parent.mkdir(exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "profile": test_profile_data,
                    "insights": insights,
                    "generated_at": "2025-08-20T15:30:00",
                    "ai_provider": config.ai.provider,
                    "ai_model": config.ai.model
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Insights saved to: {output_file}")
        else:
            print("❌ No insights generated")
        
        # Cleanup
        await analysis_engine.cleanup()
        await resource_manager.cleanup()
        
        print("\n✅ AI insights test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ AI insights test failed: {e}")
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_ai_insights())
