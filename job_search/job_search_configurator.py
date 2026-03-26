#!/usr/bin/env python3
"""
Job Search Configuration and Customization System
Personalize your job search criteria, target companies, and preferences
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class JobSearchConfigurator:
    """
    Interactive configuration system for personalizing job search criteria
    """
    
    def __init__(self):
        self.config_file = Path("job_search_config.json")
        self.default_config = self._get_default_config()
        self.current_config = self._load_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default job search configuration"""
        return {
            "personal_profile": {
                "current_title": "Software Engineer",
                "years_experience": 5,
                "years_leadership": 2,
                "specializations": ["Backend Development", "Full Stack", "System Design"],
                "industries": ["Technology", "SaaS", "Fintech", "Healthcare Tech"],
                "company_sizes": ["Startup (10-50)", "Scale-up (50-200)", "Mid-size (200-1000)"]
            },
            "skills": {
                "technical": [
                    "Python", "JavaScript", "React", "Node.js", "SQL", "Git",
                    "AWS", "Docker", "Machine Learning", "System Design", "API Development"
                ],
                "soft": [
                    "Leadership", "Communication", "Problem Solving",
                    "Team Collaboration", "Project Management", "Mentoring"
                ],
                "learning": [
                    "AI/ML", "Cloud Architecture", "DevOps", "Cybersecurity",
                    "Kubernetes", "Microservices", "Data Engineering"
                ]
            },
            "job_preferences": {
                "target_roles": [
                    "Senior Software Engineer",
                    "Tech Lead",
                    "Staff Engineer",
                    "Principal Engineer",
                    "Engineering Manager"
                ],
                "salary_range": {
                    "min": 120000,
                    "max": 200000,
                    "currency": "USD"
                },
                "location_preferences": {
                    "remote_only": False,
                    "hybrid_acceptable": True,
                    "on_site_acceptable": False,
                    "preferred_locations": ["Remote", "San Francisco", "New York", "Seattle", "Austin"],
                    "willing_to_relocate": False
                },
                "company_preferences": {
                    "stages": ["Series A", "Series B", "Series C", "Public", "Profitable Startup"],
                    "sizes": ["50-200", "200-1000", "1000+"],
                    "culture_values": ["Innovation", "Work-Life Balance", "Growth", "Impact"]
                }
            },
            "target_companies": {
                "high_priority": [
                    "Google", "Microsoft", "Amazon", "Meta", "Apple",
                    "Netflix", "Uber", "Airbnb", "Stripe", "OpenAI"
                ],
                "medium_priority": [
                    "Salesforce", "Adobe", "Spotify", "Slack", "Zoom",
                    "Databricks", "Snowflake", "Palantir", "Square", "Coinbase"
                ],
                "startup_focus": [
                    "AI/ML Startups", "Fintech Startups", "Healthcare Tech",
                    "Climate Tech", "EdTech", "Gaming", "DevTools"
                ]
            },
            "search_criteria": {
                "qualification_threshold": 0.65,
                "max_jobs_per_scan": 20,
                "prioritize_recent_postings": True,
                "include_contract_roles": False,
                "include_internships": False,
                "keywords_to_include": ["remote", "python", "javascript", "senior"],
                "keywords_to_exclude": ["junior", "entry-level", "internship", "contract"]
            },
            "career_goals": {
                "timeline": "6-12 months",
                "primary_motivation": "Career Growth",
                "growth_areas": ["Technical Leadership", "System Architecture", "Team Management"],
                "priorities": ["Learning", "Impact", "Compensation", "Work-Life Balance"],
                "long_term_goal": "CTO/VP Engineering"
            },
            "notification_preferences": {
                "immediate_alerts_threshold": 0.85,
                "daily_summary": True,
                "weekly_market_report": True,
                "send_low_match_jobs": False,
                "alert_for_target_companies": True
            }
        }
        
    def _load_config(self) -> Dict[str, Any]:
        """Load existing configuration or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(self.default_config, config)
            except Exception as e:
                print(f"⚠️ Error loading config: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
            
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults"""
        merged = default.copy()
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
        
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.current_config, f, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            
    def interactive_setup(self):
        """Interactive setup wizard"""
        print("🎯 Job Search Configuration Wizard")
        print("=" * 50)
        print("Let's customize your job search preferences!\n")
        
        # Personal Profile
        self._configure_personal_profile()
        
        # Skills
        self._configure_skills()
        
        # Job Preferences  
        self._configure_job_preferences()
        
        # Target Companies
        self._configure_target_companies()
        
        # Search Criteria
        self._configure_search_criteria()
        
        # Notification Preferences
        self._configure_notifications()
        
        # Save configuration
        self.save_config()
        
        print("\n🎉 Configuration complete!")
        print("Your personalized job search is now ready!")
        
    def _configure_personal_profile(self):
        """Configure personal profile information"""
        print("👤 Personal Profile")
        print("-" * 20)
        
        profile = self.current_config["personal_profile"]
        
        # Current title
        current_title = input(f"Current title [{profile['current_title']}]: ").strip()
        if current_title:
            profile["current_title"] = current_title
            
        # Years of experience
        try:
            years_exp = input(f"Years of experience [{profile['years_experience']}]: ").strip()
            if years_exp:
                profile["years_experience"] = int(years_exp)
        except ValueError:
            print("⚠️ Invalid input, keeping current value")
            
        # Years of leadership
        try:
            years_lead = input(f"Years of leadership experience [{profile['years_leadership']}]: ").strip()
            if years_lead:
                profile["years_leadership"] = int(years_lead)
        except ValueError:
            print("⚠️ Invalid input, keeping current value")
            
        # Specializations
        print(f"\nCurrent specializations: {', '.join(profile['specializations'])}")
        specializations = input("Add specializations (comma-separated, or press Enter to keep current): ").strip()
        if specializations:
            new_specs = [s.strip() for s in specializations.split(',')]
            profile["specializations"].extend(new_specs)
            profile["specializations"] = list(set(profile["specializations"]))  # Remove duplicates
            
        print("✅ Personal profile updated\n")
        
    def _configure_skills(self):
        """Configure skills information"""
        print("🛠️ Skills Configuration")
        print("-" * 20)
        
        skills = self.current_config["skills"]
        
        # Technical skills
        print(f"Current technical skills: {', '.join(skills['technical'][:5])}...")
        tech_skills = input("Add technical skills (comma-separated, or press Enter to skip): ").strip()
        if tech_skills:
            new_tech = [s.strip() for s in tech_skills.split(',')]
            skills["technical"].extend(new_tech)
            skills["technical"] = list(set(skills["technical"]))
            
        # Learning goals
        print(f"Current learning goals: {', '.join(skills['learning'][:3])}...")
        learning = input("Add learning goals (comma-separated, or press Enter to skip): ").strip()
        if learning:
            new_learning = [s.strip() for s in learning.split(',')]
            skills["learning"].extend(new_learning)
            skills["learning"] = list(set(skills["learning"]))
            
        print("✅ Skills updated\n")
        
    def _configure_job_preferences(self):
        """Configure job preferences"""
        print("💼 Job Preferences")
        print("-" * 20)
        
        prefs = self.current_config["job_preferences"]
        
        # Target roles
        print(f"Current target roles: {', '.join(prefs['target_roles'])}")
        roles = input("Add target roles (comma-separated, or press Enter to skip): ").strip()
        if roles:
            new_roles = [r.strip() for r in roles.split(',')]
            prefs["target_roles"].extend(new_roles)
            prefs["target_roles"] = list(set(prefs["target_roles"]))
            
        # Salary range
        salary_range = prefs["salary_range"]
        try:
            min_salary = input(f"Minimum salary [{salary_range['min']}]: ").strip()
            if min_salary:
                salary_range["min"] = int(min_salary)
                
            max_salary = input(f"Maximum salary [{salary_range['max']}]: ").strip()
            if max_salary:
                salary_range["max"] = int(max_salary)
        except ValueError:
            print("⚠️ Invalid salary input, keeping current values")
            
        # Remote work preferences
        location_prefs = prefs["location_preferences"]
        remote_only = input(f"Remote only? [{'Yes' if location_prefs['remote_only'] else 'No'}] (y/n): ").strip().lower()
        if remote_only in ['y', 'yes']:
            location_prefs["remote_only"] = True
        elif remote_only in ['n', 'no']:
            location_prefs["remote_only"] = False
            
        print("✅ Job preferences updated\n")
        
    def _configure_target_companies(self):
        """Configure target companies"""
        print("🏢 Target Companies")
        print("-" * 20)
        
        companies = self.current_config["target_companies"]
        
        # High priority companies
        print(f"Current high-priority companies: {', '.join(companies['high_priority'][:5])}...")
        high_priority = input("Add high-priority companies (comma-separated, or press Enter to skip): ").strip()
        if high_priority:
            new_high = [c.strip() for c in high_priority.split(',')]
            companies["high_priority"].extend(new_high)
            companies["high_priority"] = list(set(companies["high_priority"]))
            
        # Startup focus areas
        print(f"Current startup focus: {', '.join(companies['startup_focus'])}")
        startup_focus = input("Add startup focus areas (comma-separated, or press Enter to skip): ").strip()
        if startup_focus:
            new_focus = [f.strip() for f in startup_focus.split(',')]
            companies["startup_focus"].extend(new_focus)
            companies["startup_focus"] = list(set(companies["startup_focus"]))
            
        print("✅ Target companies updated\n")
        
    def _configure_search_criteria(self):
        """Configure search criteria"""
        print("🔍 Search Criteria")
        print("-" * 20)
        
        criteria = self.current_config["search_criteria"]
        
        # Qualification threshold
        try:
            threshold = input(f"Minimum qualification threshold (0.0-1.0) [{criteria['qualification_threshold']}]: ").strip()
            if threshold:
                threshold_val = float(threshold)
                if 0.0 <= threshold_val <= 1.0:
                    criteria["qualification_threshold"] = threshold_val
                else:
                    print("⚠️ Threshold must be between 0.0 and 1.0")
        except ValueError:
            print("⚠️ Invalid threshold input")
            
        # Keywords to include
        print(f"Current include keywords: {', '.join(criteria['keywords_to_include'])}")
        include_keywords = input("Add keywords to include (comma-separated, or press Enter to skip): ").strip()
        if include_keywords:
            new_include = [k.strip().lower() for k in include_keywords.split(',')]
            criteria["keywords_to_include"].extend(new_include)
            criteria["keywords_to_include"] = list(set(criteria["keywords_to_include"]))
            
        # Keywords to exclude
        print(f"Current exclude keywords: {', '.join(criteria['keywords_to_exclude'])}")
        exclude_keywords = input("Add keywords to exclude (comma-separated, or press Enter to skip): ").strip()
        if exclude_keywords:
            new_exclude = [k.strip().lower() for k in exclude_keywords.split(',')]
            criteria["keywords_to_exclude"].extend(new_exclude)
            criteria["keywords_to_exclude"] = list(set(criteria["keywords_to_exclude"]))
            
        print("✅ Search criteria updated\n")
        
    def _configure_notifications(self):
        """Configure notification preferences"""
        print("📱 Notification Preferences")
        print("-" * 20)
        
        notifs = self.current_config["notification_preferences"]
        
        # Immediate alerts threshold
        try:
            alert_threshold = input(f"Immediate alert threshold (0.0-1.0) [{notifs['immediate_alerts_threshold']}]: ").strip()
            if alert_threshold:
                threshold_val = float(alert_threshold)
                if 0.0 <= threshold_val <= 1.0:
                    notifs["immediate_alerts_threshold"] = threshold_val
        except ValueError:
            print("⚠️ Invalid threshold input")
            
        # Daily summary
        daily = input(f"Daily summary? [{'Yes' if notifs['daily_summary'] else 'No'}] (y/n): ").strip().lower()
        if daily in ['y', 'yes']:
            notifs["daily_summary"] = True
        elif daily in ['n', 'no']:
            notifs["daily_summary"] = False
            
        # Target company alerts
        target_alerts = input(f"Alert for target companies? [{'Yes' if notifs['alert_for_target_companies'] else 'No'}] (y/n): ").strip().lower()
        if target_alerts in ['y', 'yes']:
            notifs["alert_for_target_companies"] = True
        elif target_alerts in ['n', 'no']:
            notifs["alert_for_target_companies"] = False
            
        print("✅ Notification preferences updated\n")
        
    def display_current_config(self):
        """Display current configuration"""
        print("📋 Current Job Search Configuration")
        print("=" * 50)
        
        config = self.current_config
        
        # Personal Profile
        print("\n👤 Personal Profile:")
        profile = config["personal_profile"]
        print(f"   Title: {profile['current_title']}")
        print(f"   Experience: {profile['years_experience']} years total, {profile['years_leadership']} leadership")
        print(f"   Specializations: {', '.join(profile['specializations'][:3])}...")
        
        # Job Preferences
        print("\n💼 Job Preferences:")
        prefs = config["job_preferences"]
        print(f"   Target Roles: {', '.join(prefs['target_roles'][:3])}...")
        salary = prefs["salary_range"]
        print(f"   Salary Range: ${salary['min']:,} - ${salary['max']:,}")
        location = prefs["location_preferences"]
        print(f"   Remote: {'Only' if location['remote_only'] else 'Acceptable' if location['hybrid_acceptable'] else 'No'}")
        
        # Target Companies
        print("\n🏢 Target Companies:")
        companies = config["target_companies"]
        print(f"   High Priority: {', '.join(companies['high_priority'][:5])}...")
        print(f"   Startup Focus: {', '.join(companies['startup_focus'][:3])}...")
        
        # Search Criteria
        print("\n🔍 Search Criteria:")
        criteria = config["search_criteria"]
        print(f"   Qualification Threshold: {criteria['qualification_threshold']:.0%}")
        print(f"   Include Keywords: {', '.join(criteria['keywords_to_include'][:5])}...")
        print(f"   Exclude Keywords: {', '.join(criteria['keywords_to_exclude'][:3])}...")
        
        # Notifications
        print("\n📱 Notifications:")
        notifs = config["notification_preferences"]
        print(f"   Immediate Alerts: {notifs['immediate_alerts_threshold']:.0%}+ matches")
        print(f"   Daily Summary: {'Yes' if notifs['daily_summary'] else 'No'}")
        print(f"   Target Company Alerts: {'Yes' if notifs['alert_for_target_companies'] else 'No'}")
        
    def quick_company_add(self):
        """Quick way to add target companies"""
        print("🏢 Quick Company Addition")
        print("-" * 25)
        
        companies = input("Enter companies (comma-separated): ").strip()
        if not companies:
            print("No companies entered.")
            return
            
        company_list = [c.strip() for c in companies.split(',')]
        
        print("\nPriority level:")
        print("1. High Priority (immediate alerts)")
        print("2. Medium Priority (regular tracking)")
        print("3. Startup Focus (industry category)")
        
        choice = input("Select priority (1-3): ").strip()
        
        target_companies = self.current_config["target_companies"]
        
        if choice == "1":
            target_companies["high_priority"].extend(company_list)
            target_companies["high_priority"] = list(set(target_companies["high_priority"]))
            print(f"✅ Added {len(company_list)} companies to high priority list")
        elif choice == "2":
            target_companies["medium_priority"].extend(company_list)
            target_companies["medium_priority"] = list(set(target_companies["medium_priority"]))
            print(f"✅ Added {len(company_list)} companies to medium priority list")
        elif choice == "3":
            target_companies["startup_focus"].extend(company_list)
            target_companies["startup_focus"] = list(set(target_companies["startup_focus"]))
            print(f"✅ Added {len(company_list)} to startup focus areas")
        else:
            print("❌ Invalid choice")
            return
            
        self.save_config()

def main():
    """Main configuration interface"""
    configurator = JobSearchConfigurator()
    
    while True:
        print("\n🎯 Job Search Configuration")
        print("=" * 30)
        print("1. 🆕 Run Full Setup Wizard")
        print("2. 📋 View Current Configuration")
        print("3. 🏢 Quick Add Target Companies")
        print("4. 💾 Reset to Defaults")
        print("5. 📁 Export Configuration")
        print("6. ❌ Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            configurator.interactive_setup()
            
        elif choice == "2":
            configurator.display_current_config()
            
        elif choice == "3":
            configurator.quick_company_add()
            
        elif choice == "4":
            confirm = input("⚠️ Reset to defaults? This will lose all customizations (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                configurator.current_config = configurator.default_config.copy()
                configurator.save_config()
                print("✅ Configuration reset to defaults")
            
        elif choice == "5":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"job_search_config_backup_{timestamp}.json"
            try:
                with open(export_file, 'w') as f:
                    json.dump(configurator.current_config, f, indent=2)
                print(f"✅ Configuration exported to {export_file}")
            except Exception as e:
                print(f"❌ Export failed: {e}")
                
        elif choice == "6":
            print("👋 Configuration saved! Your job search is personalized.")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    main()
