#!/usr/bin/env python3
"""
Test follower analysis module
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_analysis_module():
    """Test follower analysis module"""
    print("Testing follower analysis module...")
    
    try:
        from src.tracking.follower_change_analysis import FollowerChangeAnalysisEngine
        print("✅ FollowerChangeAnalysisEngine imported successfully")
        
        # Test basic initialization
        analyzer = FollowerChangeAnalysisEngine("test.db")
        print("✅ FollowerChangeAnalysisEngine initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Follower Analysis Module Test")
    print("=" * 40)
    
    success = test_analysis_module()
    
    if success:
        print("\n✅ Analysis module test passed!")
    else:
        print("\n❌ Test failed")