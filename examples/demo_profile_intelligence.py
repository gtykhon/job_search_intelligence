"""
Profile-Based Intelligence System Demo

This script demonstrates the complete profile-based intelligence system
that uses LinkedIn profile data as parameters for intelligent job search.
"""

import sys
import json
import logging
from pathlib import Path

# Add the parent directory to the path to access src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.intelligence.intelligent_config_manager import create_intelligent_job_search_config, get_current_intelligent_config

def demo_profile_based_intelligence():
    """Demonstrate the complete profile-based intelligence system"""
    
    print("="*80)
    print("🧠 LinkedIn Profile-Based Intelligence System Demo")
    print("="*80)
    
    print("\n📖 About this system:")
    print("This demonstration shows how to use your LinkedIn profile data")
    print("as the foundation for intelligent job search parameters.")
    print("\nThe system combines:")
    print("  • LinkedIn profile data (skills, experience, current role)")
    print("  • User preferences (salary, location, company preferences)")  
    print("  • Intelligent analysis (career progression, market insights)")
    print("\nTo create personalized job search criteria that adapt to your profile.")
    
    input("\nPress Enter to start the demonstration...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        print("\n" + "="*80)
        print("🔄 Step 1: Creating Intelligent Job Search Configuration")
        print("="*80)
        
        print("📊 Analyzing LinkedIn profile data...")
        print("⚙️  Combining with user preferences...")
        print("🧠 Generating intelligent search criteria...")
        
        # Create intelligent configuration
        config = create_intelligent_job_search_config(force_refresh=True)
        
        print("✅ Intelligent configuration created successfully!")
        
        print("\n" + "="*80)
        print("📋 Step 2: Profile Intelligence Summary")
        print("="*80)
        
        if 'profile_intelligence' in config:
            profile = config['profile_intelligence']
            
            print(f"👤 Profile Analysis:")
            print(f"   • Current Title: {profile.get('current_title', 'N/A')}")
            print(f"   • Career Level: {profile.get('career_level', 'N/A')}")
            print(f"   • Years Experience: {profile.get('years_experience', 'N/A')}")
            print(f"   • Confidence Score: {profile.get('confidence_score', 0):.2f}")
            
            print(f"\n🛠️  Skills Analysis:")
            primary_skills = profile.get('primary_skills', [])
            secondary_skills = profile.get('secondary_skills', [])
            print(f"   • Primary Skills ({len(primary_skills)}): {', '.join(primary_skills[:5])}")
            print(f"   • Secondary Skills ({len(secondary_skills)}): {', '.join(secondary_skills[:5])}")
            
            print(f"\n📍 Location & Preferences:")
            preferred_locations = profile.get('preferred_locations', [])
            print(f"   • Preferred Locations: {', '.join(preferred_locations) if preferred_locations else 'Not specified'}")
            print(f"   • Remote Preference: {profile.get('remote_preference', 'Not specified')}")
            
            salary_range = profile.get('salary_range', {})
            if salary_range and salary_range.get('min', 0) > 0:
                print(f"   • Salary Range: ${salary_range.get('min', 0):,} - ${salary_range.get('max', 0):,}")
        
        print("\n" + "="*80)
        print("🔍 Step 3: Intelligent Search Configuration")
        print("="*80)
        
        if 'search_configuration' in config:
            search_config = config['search_configuration']
            job_params = search_config.get('job_search_parameters', {})
            
            print("🎯 Generated Job Search Parameters:")
            
            job_titles = job_params.get('job_titles', [])
            print(f"   • Job Titles ({len(job_titles)}): {', '.join(job_titles[:3])}{'...' if len(job_titles) > 3 else ''}")
            
            required_skills = job_params.get('required_skills', [])
            print(f"   • Required Skills: {', '.join(required_skills)}")
            
            nice_to_have = job_params.get('nice_to_have_skills', [])
            if nice_to_have:
                print(f"   • Nice-to-Have Skills: {', '.join(nice_to_have[:5])}")
            
            locations = job_params.get('locations', [])
            print(f"   • Target Locations: {', '.join(locations)}")
            
            salary_range = job_params.get('salary_range', {})
            if salary_range:
                print(f"   • Intelligent Salary Range: ${salary_range.get('minimum', 0):,} - ${salary_range.get('target', 0):,}")
                print(f"     (Experience multiplier: {salary_range.get('experience_multiplier', 1.0):.1f}x)")
            
            print(f"   • Career Level: {job_params.get('seniority_level', 'N/A')}")
            
            industry_focus = job_params.get('industry_focus', [])
            if industry_focus:
                print(f"   • Industry Focus: {', '.join(industry_focus)}")
        
        print("\n" + "="*80)
        print("🤖 Step 4: AI Configuration & Filters")
        print("="*80)
        
        if 'search_configuration' in config:
            search_config = config['search_configuration']
            
            search_filters = search_config.get('search_filters', {})
            if search_filters:
                print("🔍 Search Filters:")
                
                company_sizes = search_filters.get('company_sizes', [])
                if company_sizes:
                    print(f"   • Company Sizes: {', '.join(company_sizes)}")
                
                work_arrangements = search_filters.get('work_arrangements', [])
                if work_arrangements:
                    print(f"   • Work Arrangements: {', '.join(work_arrangements)}")
                
                excluded_keywords = search_filters.get('excluded_keywords', [])
                if excluded_keywords:
                    print(f"   • Excluded Keywords: {', '.join(excluded_keywords)}")
            
            ai_config = search_config.get('ai_configuration', {})
            if ai_config:
                print(f"\n🤖 AI Configuration:")
                print(f"   • Match Threshold: {ai_config.get('match_threshold', 0):.2f}")
                print(f"   • Intelligence Level: {ai_config.get('intelligence_level', 'N/A')}")
                
                auto_features = ai_config.get('auto_features', {})
                if auto_features:
                    print(f"   • Auto Apply: {'Enabled' if auto_features.get('auto_apply') else 'Disabled'}")
                    print(f"   • Cover Letter Generation: {'Enabled' if auto_features.get('cover_letter_gen') else 'Disabled'}")
                    print(f"   • Resume Customization: {'Enabled' if auto_features.get('resume_customize') else 'Disabled'}")
        
        print("\n" + "="*80)
        print("💾 Step 5: Configuration Files Generated")
        print("="*80)
        
        config_files = [
            ("User Preferences", "config/user_preferences.json"),
            ("Profile Intelligence", "config/profile_intelligence.json"),
            ("Intelligent Search Config", "config/intelligent_search_config.json")
        ]
        
        print("📁 Generated Configuration Files:")
        for name, filepath in config_files:
            if Path(filepath).exists():
                file_size = Path(filepath).stat().st_size
                print(f"   ✅ {name}: {filepath} ({file_size:,} bytes)")
            else:
                print(f"   ❌ {name}: {filepath} (not found)")
        
        print("\n" + "="*80)
        print("🚀 Step 6: Integration with Job Search Pipeline")
        print("="*80)
        
        print("🔗 This intelligent configuration can now be used with:")
        print("   • Job Search Intelligence (intelligence_orchestrator.py)")
        print("   • Complete Job Search Pipeline (run_complete_pipeline.py)")
        print("   • External Job Pipeline Integration")
        print("   • Telegram Notifications & Reports")
        
        print("\n💡 Usage Examples:")
        print("   # Run with profile intelligence")
        print("   python run_complete_pipeline.py --use-profile-intelligence")
        print("   ")
        print("   # Launch CLI for interactive configuration")
        print("   python profile_intelligence_cli.py")
        print("   ")
        print("   # Update preferences programmatically")
        print("   from src.intelligence.intelligent_config_manager import IntelligentConfigurationManager")
        print("   manager = IntelligentConfigurationManager()")
        print("   manager.update_user_preference('job_search_preferences.salary_expectations.minimum', 150000)")
        
        print("\n" + "="*80)
        print("✅ Demo Complete - Profile-Based Intelligence System Ready!")
        print("="*80)
        
        print("\n🎯 Summary:")
        print("Your LinkedIn profile has been analyzed and combined with preferences")
        print("to create intelligent, personalized job search parameters that will")
        print("adapt and improve your job search results.")
        
        print(f"\n📊 Configuration Quality Score: {config.get('profile_intelligence', {}).get('confidence_score', 0):.1%}")
        
        export_choice = input("\n📤 Export full configuration to file? [y/n]: ").strip().lower()
        if export_choice in ['y', 'yes']:
            export_file = "profile_intelligence_demo_export.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, default=str)
            print(f"✅ Configuration exported to: {export_file}")
        
        print("\n🚀 Ready to revolutionize your job search with AI-powered intelligence!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_profile_based_intelligence()
    sys.exit(0 if success else 1)