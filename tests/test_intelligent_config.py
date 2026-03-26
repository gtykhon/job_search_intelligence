"""
Test the Intelligent Configuration Manager

This script tests the complete profile-based intelligence system
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.intelligence.intelligent_config_manager import IntelligentConfigurationManager, create_intelligent_job_search_config

def test_intelligent_config_manager():
    """Test the intelligent configuration manager"""
    print("=== Testing Intelligent Configuration Manager ===\n")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        print("1. Creating Intelligent Configuration Manager...")
        manager = IntelligentConfigurationManager()
        
        print("2. Loading/Creating User Preferences Template...")
        user_prefs = manager.get_user_preferences_template()
        print(f"   - Found {len(user_prefs)} preference categories")
        print(f"   - Job search preferences: {list(user_prefs.get('job_search_preferences', {}).keys())}")
        
        print("\n3. Creating Intelligent Search Configuration...")
        config = manager.create_intelligent_search_configuration(force_refresh_profile=True)
        
        print(f"   - Configuration created with {len(config)} top-level sections")
        print(f"   - Metadata: {config.get('metadata', {})}")
        
        if 'search_configuration' in config:
            search_config = config['search_configuration']
            job_params = search_config.get('job_search_parameters', {})
            
            print(f"\n4. Job Search Parameters:")
            print(f"   - Job titles: {job_params.get('job_titles', [])}")
            print(f"   - Required skills: {job_params.get('required_skills', [])}")
            print(f"   - Locations: {job_params.get('locations', [])}")
            print(f"   - Salary range: {job_params.get('salary_range', {})}")
            print(f"   - Career level: {job_params.get('seniority_level', 'N/A')}")
        
        print("\n5. Testing Configuration Update...")
        manager.update_user_preference('job_search_preferences.salary_expectations.minimum', 140000)
        print("   - Updated minimum salary to $140,000")
        
        print("\n6. Testing Convenience Function...")
        quick_config = create_intelligent_job_search_config()
        print(f"   - Quick config created with {len(quick_config)} sections")
        
        print("\n✅ All tests passed! Intelligent configuration system is working.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_intelligent_config_manager()
    sys.exit(0 if success else 1)