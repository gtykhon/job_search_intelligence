"""
Final Real Profile Integration Script

This script ensures your real LinkedIn profile intelligence is properly
integrated and demonstrates the complete system with your actual data.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

def verify_and_display_real_profile():
    """Verify the real profile intelligence is loaded and display the results"""
    
    print("=" * 80)
    print("🔍 Real LinkedIn Profile Intelligence Verification")
    print("=" * 80)
    
    # Check if the real profile intelligence exists
    profile_intelligence_file = Path('config/profile_intelligence.json')
    
    if not profile_intelligence_file.exists():
        print("❌ Profile intelligence file not found!")
        return False
    
    # Load the profile intelligence
    with open(profile_intelligence_file, 'r', encoding='utf-8') as f:
        profile_data = json.load(f)
    
    profile_intel = profile_data.get('profile_intelligence', {})
    
    print("📊 Your Real Profile Intelligence:")
    print(f"   • Current Title: {profile_intel.get('current_title', 'N/A')}")
    print(f"   • Years Experience: {profile_intel.get('years_experience', 'N/A')}")
    print(f"   • Career Level: {profile_intel.get('career_level', 'N/A')}")
    print(f"   • Primary Skills: {', '.join(profile_intel.get('primary_skills', []))}")
    print(f"   • Secondary Skills: {', '.join(profile_intel.get('secondary_skills', []))}")
    print(f"   • Industry Preferences: {', '.join(profile_intel.get('industry_preferences', []))}")
    
    salary_range = profile_intel.get('salary_range', {})
    if salary_range:
        print(f"   • Salary Range: ${salary_range.get('min', 0):,} - ${salary_range.get('max', 0):,}")
    
    print(f"   • Confidence Score: {profile_intel.get('confidence_score', 0):.1%}")
    print(f"   • Last Updated: {profile_intel.get('last_updated', 'N/A')}")
    
    # Check extraction method
    extraction_method = profile_data.get('extraction_method', 'unknown')
    print(f"   • Data Source: {extraction_method}")
    
    if extraction_method == 'real_network_analysis':
        print("✅ Using real LinkedIn network analysis data")
    else:
        print("⚠️  Using sample/mock data - consider updating with real data")
    
    return True

def generate_intelligent_config_with_real_data():
    """Generate intelligent configuration ensuring real data is used"""
    
    print("\n🧠 Generating Intelligent Configuration with Real Data...")
    
    # Import without forcing refresh to preserve real data
    from src.intelligence.intelligent_config_manager import IntelligentConfigurationManager
    
    manager = IntelligentConfigurationManager()
    
    # Generate configuration without forcing profile refresh
    config = manager.create_intelligent_search_configuration(force_refresh_profile=False)
    
    print("✅ Intelligent configuration generated!")
    
    # Display the results
    if 'search_configuration' in config:
        search_config = config['search_configuration']
        job_params = search_config.get('job_search_parameters', {})
        
        print("\n🎯 Your Intelligent Job Search Parameters:")
        
        job_titles = job_params.get('job_titles', [])
        print(f"   • Job Titles ({len(job_titles)}): {', '.join(job_titles)}")
        
        required_skills = job_params.get('required_skills', [])
        print(f"   • Required Skills: {', '.join(required_skills)}")
        
        locations = job_params.get('locations', [])
        print(f"   • Target Locations: {', '.join(locations)}")
        
        salary_range = job_params.get('salary_range', {})
        if salary_range:
            print(f"   • Intelligent Salary Range: ${salary_range.get('minimum', 0):,} - ${salary_range.get('target', 0):,}")
            if salary_range.get('experience_multiplier'):
                print(f"     (Experience multiplier: {salary_range.get('experience_multiplier', 1.0):.1f}x)")
        
        print(f"   • Career Level: {job_params.get('seniority_level', 'N/A')}")
        
        industry_focus = job_params.get('industry_focus', [])
        if industry_focus:
            print(f"   • Industry Focus: {', '.join(industry_focus)}")
    
    return config

def show_integration_examples():
    """Show how to integrate with existing systems"""
    
    print("\n🔗 Integration with Your Existing Systems:")
    print("="*80)
    
    print("1. 🚀 Run Complete Pipeline with Real Profile Intelligence:")
    print("   python run_complete_pipeline.py")
    print("   # Automatically uses your real profile configuration")
    
    print("\n2. 📱 Interactive Configuration Management:")
    print("   python profile_intelligence_cli.py")
    print("   # Full CLI for managing your profile intelligence")
    
    print("\n3. 🤖 Programmatic Usage:")
    print("""   from src.intelligence.intelligent_config_manager import get_current_intelligent_config
   config = get_current_intelligent_config()
   # Use config in your existing job search pipeline""")
    
    print("\n4. 📊 Update Preferences:")
    print("""   from src.intelligence.intelligent_config_manager import IntelligentConfigurationManager
   manager = IntelligentConfigurationManager()
   manager.update_user_preference('job_search_preferences.salary_expectations.minimum', 95000)""")

def main():
    """Main function to verify and demonstrate real profile intelligence"""
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Step 1: Verify real profile data
    if not verify_and_display_real_profile():
        print("❌ Cannot proceed without valid profile intelligence")
        return
    
    # Step 2: Generate intelligent configuration with real data
    config = generate_intelligent_config_with_real_data()
    
    # Step 3: Show integration examples
    show_integration_examples()
    
    print("\n" + "="*80)
    print("✅ Real Profile Intelligence System Ready!")
    print("="*80)
    
    print("\n🎯 Summary of Your Real Data:")
    profile_file = Path('config/profile_intelligence.json')
    if profile_file.exists():
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        if profile_data.get('extraction_method') == 'real_network_analysis':
            print("✅ Using real LinkedIn network analysis")
            print(f"✅ Based on {profile_data.get('raw_data', {}).get('network_analysis', {}).get('total_connections', 0)} LinkedIn connections")
            print(f"✅ Primary industry: {profile_data.get('raw_data', {}).get('basic_info', {}).get('industry', 'N/A')}")
            print(f"✅ Confidence score: {profile_data.get('profile_intelligence', {}).get('confidence_score', 0):.1%}")
        else:
            print("⚠️  Still using sample data - run update_profile_with_real_data.py to fix")
    
    print(f"\n🚀 Your intelligent job search system is now powered by real LinkedIn data!")
    print("Ready to find better job matches with AI-powered personalization!")

if __name__ == "__main__":
    main()