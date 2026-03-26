#!/usr/bin/env python3
"""
Test Real LinkedIn API Integration
Quick test to verify the LinkedIn API credentials are working
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from src.intelligence.real_linkedin_api_client import RealLinkedInAPIClient

async def test_linkedin_api():
    """Test the real LinkedIn API integration"""
    
    print("🔍 Testing Real LinkedIn API Integration")
    print("=" * 50)
    
    client = RealLinkedInAPIClient()
    
    # Test authentication
    print("\n🔐 Testing authentication...")
    auth_success = await client.authenticate()
    if auth_success:
        print("✅ Authentication successful!")
    else:
        print("❌ Authentication failed")
        return
    
    # Test profile data
    print("\n📊 Testing profile data retrieval...")
    try:
        profile_data = await client.get_real_profile_data()
        if profile_data:
            print("✅ Profile data retrieved successfully!")
            print(f"   • Name: {profile_data.get('first_name', '')} {profile_data.get('last_name', '')}")
            print(f"   • Headline: {profile_data.get('headline', 'N/A')}")
            print(f"   • Location: {profile_data.get('location', 'N/A')}")
            print(f"   • Connections: {profile_data.get('connection_count', 0)}")
        else:
            print("⚠️  No profile data returned")
    except Exception as e:
        print(f"❌ Profile data failed: {e}")
    
    # Test network data
    print("\n🌐 Testing network data retrieval...")
    try:
        network_data = await client.get_real_network_data()
        if network_data:
            print("✅ Network data retrieved successfully!")
            print(f"   • Total Connections: {network_data.get('total_connections', 0)}")
            print(f"   • Leadership Engagement: {network_data.get('leadership_engagement', 'N/A')}")
            print(f"   • Fortune 500 Penetration: {network_data.get('f500_penetration', 'N/A')}")
            print(f"   • Senior Connections: {network_data.get('senior_connections', 0)}")
            print(f"   • Engagement Quality: {network_data.get('engagement_quality', 'N/A')}")
            print(f"   • Data Source: {network_data.get('data_source', 'Unknown')}")
        else:
            print("⚠️  No network data returned")
    except Exception as e:
        print(f"❌ Network data failed: {e}")
    
    # Test job search
    print("\n💼 Testing job search...")
    try:
        search_criteria = {
            'job_titles': ['Senior Python Developer', 'Data Scientist'],
            'locations': ['Remote', 'San Francisco'],
            'required_skills': ['Python', 'JavaScript', 'AI']
        }
        
        jobs = await client.search_real_jobs(search_criteria)
        if jobs:
            print(f"✅ Job search successful! Found {len(jobs)} opportunities")
            for i, job in enumerate(jobs[:3], 1):
                print(f"   {i}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                print(f"      📍 {job.get('location', 'Unknown')} | 💰 {job.get('salary', 'N/A')}")
        else:
            print("⚠️  No jobs found")
    except Exception as e:
        print(f"❌ Job search failed: {e}")
    
    print("\n🎉 LinkedIn API test complete!")

if __name__ == "__main__":
    asyncio.run(test_linkedin_api())