#!/usr/bin/env python3
"""
Test LinkedIn Wrapper with Real Data Collection
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_wrapper_and_data_collection():
    try:
        print("🔍 Testing LinkedIn Wrapper and Data Collection...")
        
        # Test authenticator
        from src.core.linkedin_authenticator import LinkedInAuthenticator
        auth = LinkedInAuthenticator(debug=False)
        cookies = auth.get_cookies()
        
        if not cookies:
            print("❌ Authentication failed")
            return False
            
        print(f"✅ Authentication successful ({len(cookies)} cookies)")
        
        # Test wrapper
        from src.core.linkedin_wrapper import LinkedInWrapper
        wrapper = LinkedInWrapper(
            username=auth.username,
            password=auth.password,
            debug=False,
            cookies=cookies,
            authenticator=auth
        )
        print("✅ LinkedIn wrapper initialized")
        
        # Test profile retrieval
        print("🔍 Testing profile retrieval...")
        profile = wrapper.get_user_profile()
        if profile:
            print(f"✅ Profile retrieved: {profile.get('firstName', 'Unknown')} {profile.get('lastName', '')}")
        else:
            print("❌ Failed to retrieve profile")
            return False
            
        # Test connection fetching
        print("🔍 Testing connection retrieval...")
        profile_id = profile.get('publicIdentifier') or profile.get('urn_id', '')
        if profile_id:
            connections = wrapper.get_profile_connections(profile_id, count=5)  # Test with small batch
            if connections:
                print(f"✅ Retrieved {len(connections)} connections (test batch)")
                for i, conn in enumerate(connections[:3], 1):
                    print(f"   {i}. {conn.get('name', 'Unknown')} - {conn.get('headline', 'No headline')[:50]}...")
            else:
                print("⚠️  No connections retrieved (may be rate limited or permissions issue)")
        else:
            print("❌ Could not extract profile ID for connection testing")
        
        # Test real data collector
        print("🔍 Testing real data collector...")
        from src.intelligence.real_linkedin_data_collector import RealLinkedInDataCollector
        collector = RealLinkedInDataCollector(wrapper)
        
        # Test authentication
        auth_success = collector.authenticate()
        if auth_success:
            print("✅ Data collector authenticated")
        else:
            print("⚠️  Data collector using fallback mode")
            
        # Test data collection
        network_data = collector.collect_real_network_intelligence()
        print(f"✅ Network data collected:")
        print(f"   • Total Connections: {network_data.get('total_connections', 'N/A')}")
        print(f"   • Leadership Engagement: {network_data.get('leadership_engagement', 'N/A')}")
        print(f"   • F500 Penetration: {network_data.get('f500_penetration', 'N/A')}")
        print(f"   • Data Source: {network_data.get('data_source', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wrapper_and_data_collection()
    sys.exit(0 if success else 1)