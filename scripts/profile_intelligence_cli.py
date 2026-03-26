"""
LinkedIn Profile-Based Job Search Intelligence CLI

This script provides an interactive command-line interface for setting up
and running the profile-based intelligence job search system.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.intelligence.intelligent_config_manager import IntelligentConfigurationManager, get_current_intelligent_config
from src.intelligence.linkedin_profile_extractor import LinkedInProfileExtractor
from src.intelligence.profile_based_intelligence import ProfileBasedIntelligence

class ProfileIntelligenceCLI:
    """Command-line interface for profile-based intelligence system"""
    
    def __init__(self):
        self.manager = IntelligentConfigurationManager()
        self.extractor = LinkedInProfileExtractor()
        
    def show_welcome(self):
        """Show welcome message and system overview"""
        print("=" * 80)
        print("🔍 LinkedIn Profile-Based Job Search Intelligence System")
        print("=" * 80)
        print("\nThis system creates intelligent job search parameters by combining:")
        print("  • Your LinkedIn profile data (skills, experience, preferences)")  
        print("  • Your personal JSON configuration")
        print("  • Adaptive learning from search patterns")
        print("\nThe system normalizes and enriches job search criteria to provide")
        print("personalized and intelligent job matching.\n")
    
    def show_main_menu(self):
        """Show main menu options"""
        print("📋 Main Menu:")
        print("1. 🔧 Setup Profile Intelligence")
        print("2. ⚙️  Configure Preferences")
        print("3. 🧠 Generate Intelligent Configuration")
        print("4. 📊 View Current Configuration")
        print("5. 🚀 Run Job Search Pipeline")
        print("6.  Quick Pipeline Test")
        print("7. 📁 Manage Profile Data")
        print("8. ❓ Help & Documentation")
        print("9. 🚪 Exit")
        
    def setup_profile_intelligence(self):
        """Setup profile intelligence system"""
        print("\n🔧 Setting up Profile Intelligence...")
        
        try:
            # Check for existing LinkedIn data files
            print("📂 Checking for LinkedIn data files...")
            
            profile_files = []
            connection_files = []
            
            # Look for profile files
            for possible_profile in [
                "linkedin_profile.json",
                "data/linkedin_profile.json",
                "profile_data.json"
            ]:
                if Path(possible_profile).exists():
                    profile_files.append(possible_profile)
            
            # Look for connection files
            for possible_connections in [
                "linkedin_connections.csv",
                "old_code/linkedin_connections.csv",
                "data/linkedin_connections.csv"
            ]:
                if Path(possible_connections).exists():
                    connection_files.append(possible_connections)
            
            print(f"   Found {len(profile_files)} profile files")
            print(f"   Found {len(connection_files)} connection files")
            
            # Extract profile intelligence
            print("\n🧠 Extracting profile intelligence...")
            profile_file = profile_files[0] if profile_files else None
            connection_file = connection_files[0] if connection_files else None
            
            # Force refresh to get latest intelligence
            config = self.manager.create_intelligent_search_configuration(force_refresh_profile=True)
            
            print("✅ Profile intelligence setup complete!")
            
            # Show summary
            if 'profile_intelligence' in config:
                profile = config['profile_intelligence']
                print(f"\n📋 Profile Summary:")
                print(f"   • Current Title: {profile.get('current_title', 'N/A')}")
                print(f"   • Career Level: {profile.get('career_level', 'N/A')}")
                print(f"   • Years Experience: {profile.get('years_experience', 'N/A')}")
                print(f"   • Primary Skills: {', '.join(profile.get('primary_skills', [])[:5])}")
                print(f"   • Preferred Locations: {', '.join(profile.get('preferred_locations', [])[:3])}")
            
        except Exception as e:
            print(f"❌ Error setting up profile intelligence: {e}")
    
    def configure_preferences(self):
        """Configure user preferences interactively"""
        print("\n⚙️  Configuring User Preferences...")
        
        try:
            current_prefs = self.manager.load_user_preferences()
            
            while True:
                print("\n📝 Preference Categories:")
                print("1. 💼 Job Search Preferences (locations, salary, company size)")
                print("2. 🔍 Search Parameters (keywords, skills, exclusions)")
                print("3. 📢 Notification Preferences (Telegram, email, alerts)")
                print("4. 🤖 AI Preferences (intelligence level, automation)")
                print("5. 💾 Save and Exit")
                
                try:
                    choice = int(input("\nSelect category (1-5): "))
                    
                    if choice == 1:
                        self._configure_job_search_preferences(current_prefs)
                    elif choice == 2:
                        self._configure_search_parameters(current_prefs)
                    elif choice == 3:
                        self._configure_notification_preferences(current_prefs)
                    elif choice == 4:
                        self._configure_ai_preferences(current_prefs)
                    elif choice == 5:
                        self.manager.save_user_preferences(current_prefs)
                        print("✅ Preferences saved!")
                        break
                    else:
                        print("❌ Invalid choice. Please select 1-5.")
                        
                except ValueError:
                    print("❌ Please enter a valid number.")
                    
        except Exception as e:
            print(f"❌ Error configuring preferences: {e}")
    
    def _configure_job_search_preferences(self, prefs: Dict[str, Any]):
        """Configure job search preferences"""
        job_prefs = prefs.setdefault('job_search_preferences', {})
        
        print("\n💼 Job Search Preferences:")
        
        # Preferred locations
        current_locations = job_prefs.get('preferred_locations', [])
        print(f"Current locations: {', '.join(current_locations)}")
        new_locations = input("Enter preferred locations (comma-separated) or press Enter to keep current: ").strip()
        if new_locations:
            job_prefs['preferred_locations'] = [loc.strip() for loc in new_locations.split(',')]
        
        # Salary expectations
        salary = job_prefs.setdefault('salary_expectations', {})
        current_min = salary.get('minimum', 0)
        current_target = salary.get('target', 0)
        
        print(f"Current salary range: ${current_min:,} - ${current_target:,}")
        
        min_salary = input(f"Minimum salary (current: ${current_min:,}): ").strip()
        if min_salary.isdigit():
            salary['minimum'] = int(min_salary)
        
        target_salary = input(f"Target salary (current: ${current_target:,}): ").strip()
        if target_salary.isdigit():
            salary['target'] = int(target_salary)
    
    def _configure_search_parameters(self, prefs: Dict[str, Any]):
        """Configure search parameters"""
        search_prefs = prefs.setdefault('search_parameters', {})
        
        print("\n🔍 Search Parameters:")
        
        # Job title keywords
        current_titles = search_prefs.get('job_title_keywords', [])
        print(f"Current job title keywords: {', '.join(current_titles)}")
        new_titles = input("Enter job title keywords (comma-separated) or press Enter to keep current: ").strip()
        if new_titles:
            search_prefs['job_title_keywords'] = [title.strip() for title in new_titles.split(',')]
        
        # Required skills
        current_skills = search_prefs.get('required_skills', [])
        print(f"Current required skills: {', '.join(current_skills)}")
        new_skills = input("Enter required skills (comma-separated) or press Enter to keep current: ").strip()
        if new_skills:
            search_prefs['required_skills'] = [skill.strip() for skill in new_skills.split(',')]
    
    def _configure_notification_preferences(self, prefs: Dict[str, Any]):
        """Configure notification preferences"""
        notif_prefs = prefs.setdefault('notification_preferences', {})
        
        print("\n📢 Notification Preferences:")
        
        # Telegram enabled
        current_telegram = notif_prefs.get('telegram_enabled', True)
        telegram_input = input(f"Enable Telegram notifications? (current: {'Yes' if current_telegram else 'No'}) [y/n]: ").strip().lower()
        if telegram_input in ['y', 'yes']:
            notif_prefs['telegram_enabled'] = True
        elif telegram_input in ['n', 'no']:
            notif_prefs['telegram_enabled'] = False
        
        # Daily summary
        current_daily = notif_prefs.get('daily_summary', True)
        daily_input = input(f"Enable daily summary? (current: {'Yes' if current_daily else 'No'}) [y/n]: ").strip().lower()
        if daily_input in ['y', 'yes']:
            notif_prefs['daily_summary'] = True
        elif daily_input in ['n', 'no']:
            notif_prefs['daily_summary'] = False
    
    def _configure_ai_preferences(self, prefs: Dict[str, Any]):
        """Configure AI preferences"""
        ai_prefs = prefs.setdefault('ai_preferences', {})
        
        print("\n🤖 AI Preferences:")
        
        # Intelligence level
        current_level = ai_prefs.get('intelligence_level', 'medium')
        print(f"Current intelligence level: {current_level}")
        print("Available levels: low, medium, high")
        new_level = input("Enter intelligence level or press Enter to keep current: ").strip().lower()
        if new_level in ['low', 'medium', 'high']:
            ai_prefs['intelligence_level'] = new_level
    
    def generate_intelligent_configuration(self):
        """Generate intelligent configuration"""
        print("\n🧠 Generating Intelligent Configuration...")
        
        try:
            # Ask if user wants to refresh profile data
            refresh = input("Refresh profile intelligence from LinkedIn data? [y/n]: ").strip().lower()
            force_refresh = refresh in ['y', 'yes']
            
            config = self.manager.create_intelligent_search_configuration(force_refresh_profile=force_refresh)
            
            print("✅ Intelligent configuration generated!")
            
            # Show summary
            if 'search_configuration' in config:
                search_config = config['search_configuration']
                job_params = search_config.get('job_search_parameters', {})
                
                print(f"\n📊 Generated Configuration Summary:")
                print(f"   • Job Titles: {len(job_params.get('job_titles', []))} variations")
                print(f"   • Required Skills: {', '.join(job_params.get('required_skills', [])[:5])}")
                print(f"   • Locations: {', '.join(job_params.get('locations', [])[:3])}")
                
                salary_range = job_params.get('salary_range', {})
                if salary_range:
                    print(f"   • Salary Range: ${salary_range.get('minimum', 0):,} - ${salary_range.get('target', 0):,}")
                
                print(f"   • Career Level: {job_params.get('seniority_level', 'N/A')}")
        
        except Exception as e:
            print(f"❌ Error generating configuration: {e}")
    
    def view_current_configuration(self):
        """View current intelligent configuration"""
        print("\n📊 Current Intelligent Configuration...")
        
        try:
            config = get_current_intelligent_config()
            
            if not config:
                print("❌ No configuration found. Please generate one first.")
                return
            
            print("\n📋 Configuration Overview:")
            
            # Metadata
            metadata = config.get('metadata', {})
            print(f"   • Created: {metadata.get('created_at', 'N/A')}")
            print(f"   • Version: {metadata.get('intelligence_version', 'N/A')}")
            
            # Profile intelligence summary
            if 'profile_intelligence' in config:
                profile = config['profile_intelligence']
                print(f"\n👤 Profile Intelligence:")
                print(f"   • Current Title: {profile.get('current_title', 'N/A')}")
                print(f"   • Career Level: {profile.get('career_level', 'N/A')}")
                print(f"   • Years Experience: {profile.get('years_experience', 'N/A')}")
                print(f"   • Primary Skills: {', '.join(profile.get('primary_skills', [])[:5])}")
                print(f"   • Confidence Score: {profile.get('confidence_score', 0):.2f}")
            
            # Search configuration
            if 'search_configuration' in config:
                search_config = config['search_configuration']
                job_params = search_config.get('job_search_parameters', {})
                
                print(f"\n🔍 Search Configuration:")
                print(f"   • Job Titles ({len(job_params.get('job_titles', []))}): {', '.join(job_params.get('job_titles', [])[:3])}...")
                print(f"   • Required Skills: {', '.join(job_params.get('required_skills', [])[:5])}")
                print(f"   • Locations: {', '.join(job_params.get('locations', []))}")
                
                salary_range = job_params.get('salary_range', {})
                if salary_range:
                    print(f"   • Salary Range: ${salary_range.get('minimum', 0):,} - ${salary_range.get('target', 0):,}")
            
            # Ask if user wants to see full configuration
            show_full = input("\nShow full configuration details? [y/n]: ").strip().lower()
            if show_full in ['y', 'yes']:
                print("\n" + "="*80)
                print(json.dumps(config, indent=2))
                print("="*80)
        
        except Exception as e:
            print(f"❌ Error viewing configuration: {e}")
    
    def run_job_search_pipeline(self):
        """Run the complete job search pipeline with intelligent configuration"""
        print("\n🚀 Running Job Search Pipeline with Profile Intelligence...")
        
        try:
            # Check if we have a configuration
            config = get_current_intelligent_config()
            
            if not config:
                print("❌ No intelligent configuration found.")
                generate_now = input("Generate configuration now? [y/n]: ").strip().lower()
                if generate_now in ['y', 'yes']:
                    self.generate_intelligent_configuration()
                    config = get_current_intelligent_config()
                else:
                    return
            
            print("📊 Using current intelligent configuration...")
            
            # Import and run the complete pipeline
            try:
                import asyncio
                from run_complete_pipeline import LinkedInJobSearchPipeline
                
                print("🔄 Initializing LinkedIn Job Search Pipeline...")
                pipeline = LinkedInJobSearchPipeline()
                
                print("▶️  Running complete pipeline...")
                # Run the async pipeline method
                results = asyncio.run(pipeline.run_complete_pipeline())
                
                # Check results from the pipeline
                if len(pipeline.results.get('success', [])) > len(pipeline.results.get('errors', [])):
                    print("✅ Pipeline completed successfully!")
                    print(f"📈 Components successful: {len(pipeline.results.get('success', []))}")
                    print(f"📊 Opportunities found: {len(pipeline.results.get('data', {}).get('opportunities', []))}")
                else:
                    print(f"⚠️ Pipeline completed with some issues:")
                    print(f"✅ Successful: {len(pipeline.results.get('success', []))}")
                    print(f"❌ Failed: {len(pipeline.results.get('errors', []))}")
                
            except ImportError as e:
                print(f"❌ Could not import pipeline: {e}")
                print("📝 Please ensure run_complete_pipeline.py is available")
            except Exception as pipeline_error:
                print(f"❌ Pipeline execution error: {pipeline_error}")
                print("💡 You can also run the pipeline directly with: python run_complete_pipeline.py")
        
        except Exception as e:
            print(f"❌ Error running pipeline: {e}")
    
    def quick_pipeline_test(self):
        """Quick test of the pipeline components"""
        print("\n🔍 Running Quick Pipeline Test...")
        
        try:
            # Test profile intelligence loading
            print("📊 Testing profile intelligence loading...")
            config = get_current_intelligent_config()
            
            if config:
                print("✅ Profile intelligence configuration found")
                metadata = config.get('metadata', {})
                print(f"   • Profile Owner: {metadata.get('profile_owner', 'Unknown')}")
                print(f"   • Intelligence Confidence: {metadata.get('intelligence_confidence', 0):.1%}")
            else:
                print("❌ No profile intelligence configuration found")
                return
            
            # Test pipeline import
            print("🔧 Testing pipeline import...")
            try:
                from run_complete_pipeline import LinkedInJobSearchPipeline
                pipeline = LinkedInJobSearchPipeline()
                print("✅ Pipeline import successful")
                print(f"   • Pipeline initialized with timestamp: {pipeline.timestamp}")
            except Exception as import_error:
                print(f"❌ Pipeline import failed: {import_error}")
                return
            
            # Test configuration files
            print("📁 Testing configuration files...")
            config_files = [
                "config/profile_intelligence.json",
                "config/intelligent_job_search_config.json"
            ]
            
            for config_file in config_files:
                if Path(config_file).exists():
                    print(f"✅ Found: {config_file}")
                else:
                    print(f"❌ Missing: {config_file}")
            
            # Test basic search criteria
            search_config = config.get('search_configuration', {})
            job_params = search_config.get('job_search_parameters', {})
            
            if job_params:
                print("🎯 Testing job search parameters...")
                print(f"✅ Job titles configured: {len(job_params.get('job_titles', []))}")
                print(f"✅ Required skills: {len(job_params.get('required_skills', []))}")
                print(f"✅ Locations configured: {len(job_params.get('locations', []))}")
                
                salary_range = job_params.get('salary_range', {})
                if salary_range:
                    print(f"✅ Salary range: ${salary_range.get('minimum', 0):,} - ${salary_range.get('target', 0):,}")
            
            print("\n🎉 Quick test completed!")
            print("💡 Use option 5 for full pipeline execution")
            
        except Exception as e:
            print(f"❌ Quick test failed: {e}")
    
    def manage_profile_data(self):
        """Manage profile data files"""
        print("\n📁 Managing Profile Data...")
        
        try:
            print("📂 Current profile data files:")
            
            # Check for existing files
            profile_files = []
            data_files = [
                ("LinkedIn Profile", "linkedin_profile.json"),
                ("Connections Data", "linkedin_connections.csv"),
                ("Profile Intelligence", "config/profile_intelligence.json"),
                ("User Preferences", "config/user_preferences.json"),
                ("Intelligent Config", "config/intelligent_search_config.json")
            ]
            
            for name, filepath in data_files:
                if Path(filepath).exists():
                    file_size = Path(filepath).stat().st_size
                    print(f"   ✅ {name}: {filepath} ({file_size:,} bytes)")
                    profile_files.append((name, filepath))
                else:
                    print(f"   ❌ {name}: {filepath} (not found)")
            
            if not profile_files:
                print("\n💡 No profile data files found. Consider:")
                print("   1. Exporting your LinkedIn profile data")
                print("   2. Running the profile intelligence setup")
                return
            
            print("\n📋 Profile Data Management Options:")
            print("1. 📖 View file contents")
            print("2. 🔄 Refresh profile intelligence")
            print("3. 🗑️  Clear cached data")
            print("4. 📤 Export configuration")
            print("5. 🔙 Back to main menu")
            
            try:
                choice = int(input("\nSelect option (1-5): "))
                
                if choice == 1:
                    self._view_file_contents(profile_files)
                elif choice == 2:
                    self.generate_intelligent_configuration()
                elif choice == 3:
                    self._clear_cached_data()
                elif choice == 4:
                    self._export_configuration()
                elif choice == 5:
                    return
                else:
                    print("❌ Invalid choice.")
                    
            except ValueError:
                print("❌ Please enter a valid number.")
        
        except Exception as e:
            print(f"❌ Error managing profile data: {e}")
    
    def _view_file_contents(self, profile_files: List[tuple]):
        """View contents of profile files"""
        print("\n📖 Select file to view:")
        
        for i, (name, filepath) in enumerate(profile_files, 1):
            print(f"{i}. {name} ({filepath})")
        
        try:
            choice = int(input(f"\nSelect file (1-{len(profile_files)}): "))
            
            if 1 <= choice <= len(profile_files):
                name, filepath = profile_files[choice - 1]
                
                print(f"\n📄 {name} Contents:")
                print("="*80)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) > 2000:
                            print(content[:2000] + "\n... (truncated)")
                        else:
                            print(content)
                except Exception as e:
                    print(f"❌ Error reading file: {e}")
                
                print("="*80)
            else:
                print("❌ Invalid choice.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def _clear_cached_data(self):
        """Clear cached profile data"""
        print("\n🗑️  Clearing cached data...")
        
        confirm = input("Are you sure you want to clear all cached data? [y/n]: ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Operation cancelled.")
            return
        
        cache_files = [
            "config/profile_intelligence.json",
            "config/intelligent_search_config.json",
            "data/profile/profile_intelligence.json"
        ]
        
        cleared = 0
        for filepath in cache_files:
            if Path(filepath).exists():
                Path(filepath).unlink()
                print(f"   🗑️  Removed: {filepath}")
                cleared += 1
        
        if cleared > 0:
            print(f"✅ Cleared {cleared} cached files.")
        else:
            print("📝 No cached files found to clear.")
    
    def _export_configuration(self):
        """Export current configuration"""
        print("\n📤 Exporting Configuration...")
        
        try:
            config = get_current_intelligent_config()
            
            if not config:
                print("❌ No configuration to export.")
                return
            
            export_path = f"profile_intelligence_export_{config.get('metadata', {}).get('created_at', 'unknown').replace(':', '-')}.json"
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, default=str)
            
            print(f"✅ Configuration exported to: {export_path}")
        
        except Exception as e:
            print(f"❌ Error exporting configuration: {e}")
    
    def show_help(self):
        """Show help and documentation"""
        print("\n❓ LinkedIn Profile-Based Intelligence Help")
        print("="*80)
        print("\n🎯 Purpose:")
        print("This system combines your LinkedIn profile data with personal preferences")
        print("to create intelligent, personalized job search parameters.")
        print("\n🔧 Setup Process:")
        print("1. Extract intelligence from LinkedIn profile data")
        print("2. Configure your personal preferences")  
        print("3. Generate intelligent search configuration")
        print("4. Run job search pipeline with smart parameters")
        print("\n📁 Data Sources:")
        print("• LinkedIn profile JSON export")
        print("• LinkedIn connections CSV")
        print("• Your personal preferences JSON")
        print("• Cached intelligence data")
        print("\n🧠 Intelligence Features:")
        print("• Automatic skill extraction and categorization")
        print("• Experience-based salary adjustments")
        print("• Career level progression suggestions")
        print("• Location preference optimization")
        print("• Company size matching")
        print("\n🔗 Integration:")
        print("The generated configuration integrates with the existing")
        print("Job Search Intelligence system for complete job search automation.")
        print("\n📝 Configuration Files:")
        print("• config/user_preferences.json - Your personal preferences")
        print("• config/profile_intelligence.json - Extracted profile data")
        print("• config/intelligent_search_config.json - Combined intelligent config")
        print("="*80)
    
    def run(self):
        """Run the CLI application"""
        self.show_welcome()
        
        while True:
            self.show_main_menu()
            
            try:
                choice = int(input("\nSelect option (1-9): "))
                
                if choice == 1:
                    self.setup_profile_intelligence()
                elif choice == 2:
                    self.configure_preferences()
                elif choice == 3:
                    self.generate_intelligent_configuration()
                elif choice == 4:
                    self.view_current_configuration()
                elif choice == 5:
                    self.run_job_search_pipeline()
                elif choice == 6:
                    self.quick_pipeline_test()
                elif choice == 7:
                    self.manage_profile_data()
                elif choice == 8:
                    self.show_help()
                elif choice == 9:
                    print("\n👋 Thank you for using LinkedIn Profile-Based Intelligence!")
                    print("🚀 Your intelligent job search configuration is ready!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-9.")
                    
                input("\nPress Enter to continue...")
                print("\n" + "="*80 + "\n")
                
            except ValueError:
                print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                input("Press Enter to continue...")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run CLI
    cli = ProfileIntelligenceCLI()
    cli.run()