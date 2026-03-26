"""
Intelligent Configuration Manager

This module manages the integration between LinkedIn profile intelligence
and user configuration preferences to create smart job search parameters.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .linkedin_profile_extractor import extract_linkedin_profile_intelligence
from .profile_based_intelligence import ProfileIntelligence, IntelligentSearchCriteria, ProfileBasedIntelligence

logger = logging.getLogger(__name__)

class IntelligentConfigurationManager:
    """Manages intelligent configuration combining profile data with user preferences"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration files
        self.user_config_file = self.config_path / "user_preferences.json"
        self.profile_config_file = self.config_path / "profile_intelligence.json"
        self.merged_config_file = self.config_path / "intelligent_search_config.json"
        
    def get_user_preferences_template(self) -> Dict[str, Any]:
        """Get template for user preferences configuration"""
        return {
            "job_search_preferences": {
                "preferred_locations": [
                    "San Francisco, CA",
                    "Remote",
                    "New York, NY"
                ],
                "salary_expectations": {
                    "minimum": 120000,
                    "target": 150000,
                    "currency": "USD"
                },
                "work_arrangements": [
                    "Remote",
                    "Hybrid", 
                    "On-site"
                ],
                "company_size_preferences": [
                    "Startup (1-50)",
                    "Mid-size (51-500)",
                    "Large (500+)"
                ],
                "industry_preferences": [
                    "Technology",
                    "Financial Services",
                    "Healthcare"
                ]
            },
            "search_parameters": {
                "job_title_keywords": [
                    "Senior Software Engineer",
                    "Lead Developer",
                    "Principal Engineer"
                ],
                "required_skills": [
                    "Python",
                    "AWS",
                    "Django"
                ],
                "nice_to_have_skills": [
                    "Kubernetes",
                    "Machine Learning",
                    "GraphQL"
                ],
                "excluded_keywords": [
                    "Junior",
                    "Intern",
                    "Contract"
                ]
            },
            "notification_preferences": {
                "telegram_enabled": True,
                "email_enabled": False,
                "daily_summary": True,
                "instant_alerts": True,
                "match_threshold": 0.7
            },
            "ai_preferences": {
                "intelligence_level": "high",  # low, medium, high
                "auto_apply_enabled": False,
                "cover_letter_generation": True,
                "resume_customization": True
            }
        }
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences from configuration file"""
        try:
            if self.user_config_file.exists():
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default preferences
                default_prefs = self.get_user_preferences_template()
                self.save_user_preferences(default_prefs)
                return default_prefs
        except Exception as e:
            logger.error(f"Error loading user preferences: {e}")
            return self.get_user_preferences_template()
    
    def save_user_preferences(self, preferences: Dict[str, Any]):
        """Save user preferences to configuration file"""
        try:
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2)
            logger.info(f"Saved user preferences to {self.user_config_file}")
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
    
    def extract_and_save_profile_intelligence(self, 
                                            profile_file: Optional[str] = None,
                                            connections_file: Optional[str] = None) -> ProfileIntelligence:
        """Extract profile intelligence and save to configuration"""
        try:
            # Extract raw LinkedIn profile data
            raw_profile_data = extract_linkedin_profile_intelligence(
                profile_file=profile_file,
                connections_file=connections_file
            )
            
            # Convert to structured intelligence using ProfileBasedIntelligence
            intelligence_system = ProfileBasedIntelligence()
            profile_intelligence = intelligence_system.extract_profile_intelligence(raw_profile_data)
            
            # Save profile intelligence
            profile_data = {
                "profile_intelligence": profile_intelligence.__dict__,
                "raw_data": raw_profile_data,
                "extracted_at": datetime.now().isoformat()
            }
            
            with open(self.profile_config_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, default=str)
            
            logger.info(f"Saved profile intelligence to {self.profile_config_file}")
            
            return profile_intelligence
            
        except Exception as e:
            logger.error(f"Error extracting profile intelligence: {e}")
            # Return a basic profile intelligence with correct structure
            return ProfileIntelligence(
                current_title="Software Engineer",
                career_level="mid",
                primary_skills=["Python", "JavaScript"],
                years_experience=3,
                industry_preferences=["Technology"],
                preferred_locations=["Remote"]
            )
    
    def load_profile_intelligence(self) -> Optional[ProfileIntelligence]:
        """Load profile intelligence from configuration file"""
        try:
            if self.profile_config_file.exists():
                with open(self.profile_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                profile_data = data.get("profile_intelligence", {})
                return ProfileIntelligence(**profile_data)
            else:
                return None
        except Exception as e:
            logger.error(f"Error loading profile intelligence: {e}")
            return None
    
    def create_intelligent_search_configuration(self,
                                              force_refresh_profile: bool = False) -> Dict[str, Any]:
        """Create intelligent search configuration combining profile and user preferences"""
        try:
            # Load user preferences
            user_preferences = self.load_user_preferences()
            
            # Create intelligence system
            intelligence_system = ProfileBasedIntelligence()
            
            # Load or extract profile intelligence
            profile_intelligence = self.load_profile_intelligence()
            
            if profile_intelligence is None or force_refresh_profile:
                logger.info("Extracting fresh profile intelligence...")
                
                # Extract raw LinkedIn profile data
                raw_profile_data = extract_linkedin_profile_intelligence()
                
                # Use intelligence system to extract structured profile
                profile_intelligence = intelligence_system.extract_profile_intelligence(raw_profile_data)
                
                # Save profile intelligence
                profile_data = {
                    "profile_intelligence": profile_intelligence.__dict__,
                    "raw_data": raw_profile_data,
                    "extracted_at": datetime.now().isoformat()
                }
                
                with open(self.profile_config_file, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=2, default=str)
                logger.info(f"Saved profile intelligence to {self.profile_config_file}")
            
            # Set the profile intelligence in the system and load user config
            intelligence_system.profile_intelligence = profile_intelligence
            intelligence_system.user_config = user_preferences
            
            # Generate intelligent search criteria
            search_criteria = intelligence_system.generate_intelligent_search_criteria()
            
            # Create comprehensive configuration
            intelligent_config = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "profile_extracted_at": getattr(profile_intelligence, 'last_updated', None),
                    "intelligence_version": "1.0"
                },
                "profile_intelligence": profile_intelligence.__dict__,
                "user_preferences": user_preferences,
                "intelligent_search_criteria": search_criteria.__dict__,
                "search_configuration": self._build_search_configuration(
                    profile_intelligence, 
                    user_preferences, 
                    search_criteria
                )
            }
            
            # Save intelligent configuration
            with open(self.merged_config_file, 'w', encoding='utf-8') as f:
                json.dump(intelligent_config, f, indent=2, default=str)
            
            logger.info(f"Created intelligent search configuration: {self.merged_config_file}")
            
            return intelligent_config
            
        except Exception as e:
            logger.error(f"Error creating intelligent search configuration: {e}")
            return self._create_fallback_configuration()
    
    def _build_search_configuration(self,
                                  profile: ProfileIntelligence,
                                  preferences: Dict[str, Any],
                                  criteria: IntelligentSearchCriteria) -> Dict[str, Any]:
        """Build comprehensive search configuration from intelligence data"""
        
        # Merge profile skills with user preferences
        required_skills = list(set(
            profile.primary_skills[:5] +  # Top 5 primary skills
            preferences.get("search_parameters", {}).get("required_skills", [])
        ))
        
        # Generate intelligent job titles
        job_titles = self._generate_intelligent_job_titles(profile, preferences)
        
        # Generate location preferences
        locations = self._generate_location_preferences(profile, preferences)
        
        # Generate salary expectations
        salary_range = self._generate_salary_expectations(profile, preferences)
        
        return {
            "job_search_parameters": {
                "job_titles": job_titles,
                "required_skills": required_skills,
                "nice_to_have_skills": profile.secondary_skills[:10],
                "locations": locations,
                "salary_range": salary_range,
                "seniority_level": profile.career_level,
                "industry_focus": profile.industry_preferences + preferences.get("job_search_preferences", {}).get("industry_preferences", [])
            },
            "search_filters": {
                "experience_level": profile.career_level,
                "company_sizes": profile.company_size_preference + preferences.get("job_search_preferences", {}).get("company_size_preferences", []),
                "work_arrangements": [profile.remote_preference] + preferences.get("job_search_preferences", {}).get("work_arrangements", []),
                "excluded_keywords": profile.avoid_keywords + preferences.get("search_parameters", {}).get("excluded_keywords", [])
            },
            "ai_configuration": {
                "match_threshold": profile.confidence_score,
                "intelligence_level": preferences.get("ai_preferences", {}).get("intelligence_level", "medium"),
                "auto_features": {
                    "auto_apply": preferences.get("ai_preferences", {}).get("auto_apply_enabled", False),
                    "cover_letter_gen": preferences.get("ai_preferences", {}).get("cover_letter_generation", True),
                    "resume_customize": preferences.get("ai_preferences", {}).get("resume_customization", True)
                }
            }
        }
    
    def _generate_intelligent_job_titles(self, 
                                       profile: ProfileIntelligence, 
                                       preferences: Dict[str, Any]) -> List[str]:
        """Generate intelligent job title variations"""
        base_titles = preferences.get("search_parameters", {}).get("job_title_keywords", [])
        
        # Add profile-based titles
        profile_titles = []
        
        if profile.current_title:
            profile_titles.append(profile.current_title)
            
            # Generate variations based on career level
            base_title = profile.current_title.replace("Senior ", "").replace("Lead ", "").replace("Principal ", "")
            
            if profile.career_level == "senior":
                profile_titles.extend([
                    f"Senior {base_title}",
                    f"Lead {base_title}",
                    f"Staff {base_title}"
                ])
            elif profile.career_level == "executive":
                profile_titles.extend([
                    f"Lead {base_title}",
                    f"Principal {base_title}",
                    f"Staff {base_title}"
                ])
        
        # Combine and deduplicate
        all_titles = list(set(base_titles + profile_titles))
        return all_titles[:10]  # Limit to top 10
    
    def _generate_location_preferences(self, 
                                     profile: ProfileIntelligence, 
                                     preferences: Dict[str, Any]) -> List[str]:
        """Generate intelligent location preferences"""
        user_locations = preferences.get("job_search_preferences", {}).get("preferred_locations", [])
        
        # Add profile locations if available
        if profile.preferred_locations:
            for location in profile.preferred_locations:
                if location not in user_locations:
                    user_locations.insert(0, location)
        
        # Always include remote as an option
        if "Remote" not in user_locations:
            user_locations.append("Remote")
        
        return user_locations
    
    def _generate_salary_expectations(self, 
                                    profile: ProfileIntelligence, 
                                    preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent salary expectations"""
        base_salary = preferences.get("job_search_preferences", {}).get("salary_expectations", {})
        
        # Adjust based on experience and career level
        experience_multiplier = {
            "entry": 1.0,
            "mid": 1.2,
            "senior": 1.5,
            "executive": 2.0
        }.get(profile.career_level, 1.2)
        
        base_minimum = base_salary.get("minimum", 100000)
        base_target = base_salary.get("target", 130000)
        
        return {
            "minimum": int(base_minimum * experience_multiplier),
            "target": int(base_target * experience_multiplier),
            "currency": base_salary.get("currency", "USD"),
            "adjusted_for_experience": True,
            "experience_multiplier": experience_multiplier
        }
    
    def _create_fallback_configuration(self) -> Dict[str, Any]:
        """Create fallback configuration if intelligence extraction fails"""
        return {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "is_fallback": True
            },
            "user_preferences": self.get_user_preferences_template(),
            "search_configuration": {
                "job_search_parameters": {
                    "job_titles": ["Software Engineer", "Developer"],
                    "required_skills": ["Python", "JavaScript"],
                    "locations": ["Remote"],
                    "salary_range": {"minimum": 100000, "target": 130000, "currency": "USD"}
                }
            }
        }
    
    def get_intelligent_configuration(self) -> Dict[str, Any]:
        """Get the current intelligent configuration"""
        try:
            if self.merged_config_file.exists():
                with open(self.merged_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.create_intelligent_search_configuration()
        except Exception as e:
            logger.error(f"Error getting intelligent configuration: {e}")
            return self._create_fallback_configuration()
    
    def update_user_preference(self, key_path: str, value: Any):
        """Update a specific user preference using dot notation (e.g., 'job_search_preferences.salary_expectations.minimum')"""
        try:
            preferences = self.load_user_preferences()
            
            # Navigate to the nested key
            keys = key_path.split('.')
            current = preferences
            
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            
            # Save updated preferences
            self.save_user_preferences(preferences)
            
            # Regenerate intelligent configuration
            self.create_intelligent_search_configuration()
            
            logger.info(f"Updated preference {key_path} = {value}")
            
        except Exception as e:
            logger.error(f"Error updating user preference: {e}")


def create_intelligent_job_search_config(force_refresh: bool = False) -> Dict[str, Any]:
    """Convenience function to create intelligent job search configuration"""
    manager = IntelligentConfigurationManager()
    return manager.create_intelligent_search_configuration(force_refresh_profile=force_refresh)


def get_current_intelligent_config() -> Dict[str, Any]:
    """Get the current intelligent configuration"""
    manager = IntelligentConfigurationManager()
    return manager.get_intelligent_configuration()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("Creating intelligent job search configuration...")
    config = create_intelligent_job_search_config(force_refresh=True)
    
    print(f"\nConfiguration created with {len(config.get('search_configuration', {}).get('job_search_parameters', {}).get('job_titles', []))} intelligent job titles")
    print(f"Required skills: {config.get('search_configuration', {}).get('job_search_parameters', {}).get('required_skills', [])}")
    print(f"Salary range: {config.get('search_configuration', {}).get('job_search_parameters', {}).get('salary_range', {})}")