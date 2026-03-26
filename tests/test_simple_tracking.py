#!/usr/bin/env python3
"""
Simple test for follower tracking module
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_import():
    """Test basic module imports"""
    print("Testing module imports...")
    
    try:
        from src.tracking.follower_change_tracker import LinkedInFollowerTracker
        print("✅ LinkedInFollowerTracker imported successfully")
        
        # Test basic initialization
        tracker = LinkedInFollowerTracker("test.db")
        print("✅ LinkedInFollowerTracker initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Follower Tracking Test")
    print("=" * 40)
    
    success = test_basic_import()
    
    if success:
        print("\n✅ Basic test passed!")
    else:
        print("\n❌ Test failed")