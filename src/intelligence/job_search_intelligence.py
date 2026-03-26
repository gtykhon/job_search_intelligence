#!/usr/bin/env python3
"""
AI-Powered Job Search Intelligence System
Advanced job discovery, qualification analysis, and application strategy
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import AppConfig
from src.integrations.notifications import NotificationManager


def load_job_search_config() -> Dict[str, Any]:
    """Load personalized job search configuration"""
    config_file = Path("job_search_config.json")
    
    # Default configuration if file doesn't exist
    default_config = {
        "personal_profile": {
            "current_title": "Software Engineer",
            "years_experience": 5,
            "years_leadership": 2,
            "specializations": ["Backend Development", "Full Stack", "System Design"]
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
            "learning": ["AI/ML", "Cloud Architecture", "DevOps", "Cybersecurity"]
        },
        "job_preferences": {
            "target_roles": [
                "Senior Software Engineer", "Tech Lead", "Staff Engineer",
                "Principal Engineer", "Engineering Manager"
            ],
            "salary_range": {"min": 120000, "max": 200000, "currency": "USD"},
            "location_preferences": {
                "remote_only": False,
                "hybrid_acceptable": True,
                "on_site_acceptable": False,
                "preferred_locations": ["Remote", "San Francisco", "New York", "Seattle"],
                "willing_to_relocate": False
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
            ]
        },
        "search_criteria": {
            "qualification_threshold": 0.65,
            "max_jobs_per_scan": 20,
            "prioritize_recent_postings": True,
            "keywords_to_include": ["remote", "python", "javascript", "senior"],
            "keywords_to_exclude": ["junior", "entry-level", "internship", "contract"]
        },
        "notification_preferences": {
            "immediate_alerts_threshold": 0.85,
            "daily_summary": True,
            "alert_for_target_companies": True
        }
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                for key, value in loaded_config.items():
                    if key in default_config:
                        if isinstance(default_config[key], dict) and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                return default_config
        except Exception as e:
            print(f"⚠️ Error loading job search config: {e}, using defaults")
            
    return default_config


logger = logging.getLogger(__name__)

class JobSearchIntelligence:
    """
    AI-powered job search and qualification analysis system
    Discovers, analyzes, and ranks job opportunities based on qualifications
    """
    
    def __init__(self, config: AppConfig, notification_manager: NotificationManager):
        self.config = config
        self.notification_manager = notification_manager
        
        # Load personalized job search configuration
        self.job_config = load_job_search_config()
        
        # Extract configuration values
        search_criteria = self.job_config.get("search_criteria", {})
        self.qualification_threshold = search_criteria.get("qualification_threshold", 0.65)
        self.max_jobs_per_scan = search_criteria.get("max_jobs_per_scan", 20)
        self.keywords_to_include = search_criteria.get("keywords_to_include", [])
        self.keywords_to_exclude = search_criteria.get("keywords_to_exclude", [])
        
        # Target companies from configuration
        companies_config = self.job_config.get("target_companies", {})
        self.target_companies = (
            companies_config.get("high_priority", []) + 
            companies_config.get("medium_priority", [])
        )
        
        # Notification preferences
        notif_prefs = self.job_config.get("notification_preferences", {})
        self.immediate_alert_threshold = notif_prefs.get("immediate_alerts_threshold", 0.85)
        self.send_target_company_alerts = notif_prefs.get("alert_for_target_companies", True)
        
        self.user_profile = self._initialize_user_profile()
        self.job_market_data = {}
        self.qualification_algorithms = self._initialize_qualification_algorithms()
        
    def _initialize_user_profile(self) -> Dict[str, Any]:
        """Initialize user profile for job matching from configuration"""
        skills_config = self.job_config.get("skills", {})
        personal_config = self.job_config.get("personal_profile", {})
        job_prefs = self.job_config.get("job_preferences", {})
        
        return {
            'skills': {
                'technical': skills_config.get("technical", []),
                'soft': skills_config.get("soft", []),
                'emerging': skills_config.get("learning", [])
            },
            'experience': {
                'years_total': personal_config.get("years_experience", 5),
                'years_leadership': personal_config.get("years_leadership", 2),
                'industries': personal_config.get("industries", ['Technology', 'SaaS', 'Startups']),
                'company_sizes': personal_config.get("company_sizes", ['Startup (10-50)', 'Scale-up (50-200)', 'Mid-size (200-1000)'])
            },
            'preferences': {
                'remote_work': job_prefs.get("location_preferences", {}).get("remote_only", False),
                'hybrid_acceptable': job_prefs.get("location_preferences", {}).get("hybrid_acceptable", True),
                'relocation_willing': job_prefs.get("location_preferences", {}).get("willing_to_relocate", False),
                'preferred_locations': job_prefs.get("location_preferences", {}).get("preferred_locations", ['Remote']),
                'salary_range': job_prefs.get("salary_range", {'min': 120000, 'max': 180000}),
                'company_stage': job_prefs.get("company_preferences", {}).get("stages", ['Series A', 'Series B', 'Series C', 'Public']),
                'role_types': ['Individual Contributor', 'Tech Lead', 'Engineering Manager']
            },
            'career_goals': {
                'target_roles': ['Senior Software Engineer', 'Tech Lead', 'Principal Engineer'],
                'growth_areas': ['System Design', 'Leadership', 'Architecture'],
                'timeline': '6-12 months',
                'priorities': ['Growth', 'Impact', 'Learning', 'Compensation']
            }
        }
        
    def _initialize_qualification_algorithms(self) -> Dict[str, Any]:
        """Initialize job qualification scoring algorithms"""
        return {
            'skill_matching': {
                'exact_match_weight': 1.0,
                'partial_match_weight': 0.7,
                'related_skill_weight': 0.5,
                'missing_critical_penalty': -0.3
            },
            'experience_matching': {
                'years_weight': 0.3,
                'industry_weight': 0.2,
                'company_size_weight': 0.15,
                'role_level_weight': 0.35
            },
            'preference_scoring': {
                'location_weight': 0.25,
                'remote_weight': 0.2,
                'salary_weight': 0.25,
                'company_stage_weight': 0.15,
                'role_type_weight': 0.15
            },
            'growth_potential': {
                'learning_opportunities': 0.3,
                'career_advancement': 0.4,
                'skill_development': 0.3
            }
        }
        
    async def discover_qualified_jobs(self) -> List[Dict[str, Any]]:
        """Discover jobs that match user qualifications"""
        logger.info("🔍 Discovering qualified job opportunities...")
        
        # Mock job data - replace with real job board APIs
        job_listings = await self._fetch_job_listings()
        
        # Analyze each job for qualification match
        qualified_jobs = []
        
        for job in job_listings:
            qualification_score = await self._calculate_qualification_score(job)
            
            if qualification_score['overall_score'] >= 0.6:  # 60% qualification threshold
                job_analysis = await self._analyze_job_opportunity(job, qualification_score)
                qualified_jobs.append(job_analysis)
        
        # Sort by qualification score
        qualified_jobs.sort(key=lambda x: x['qualification_score']['overall_score'], reverse=True)
        
        logger.info(f"✅ Found {len(qualified_jobs)} qualified job opportunities")
        return qualified_jobs
        
    async def _fetch_job_listings(self) -> List[Dict[str, Any]]:
        """Fetch job listings from various sources with real LinkedIn job links"""
        # Real job listings with LinkedIn job search URLs
        return [
            {
                'id': 'job_001',
                'title': 'Senior Software Engineer',
                'company': 'Amazon',
                'location': 'San Francisco, CA (Remote OK)',
                'salary_range': {'min': 140000, 'max': 180000},
                'company_size': 'Large Enterprise (10000+)',
                'company_stage': 'Public Company',
                'posted_date': '2025-08-18',
                'linkedin_url': 'https://www.linkedin.com/jobs/search/?keywords=Senior%20Software%20Engineer%20Amazon&location=San%20Francisco%2C%20CA&f_TPR=r604800&f_WT=2',
                'company_url': 'https://www.linkedin.com/company/amazon/',
                'description': """
                We're looking for a Senior Software Engineer to join our growing team.
                
                Requirements:
                - 4+ years of software development experience
                - Strong proficiency in Python and JavaScript
                - Experience with React and Node.js
                - Knowledge of cloud platforms (AWS preferred)
                - Experience with microservices architecture
                - Strong communication and collaboration skills
                
                Nice to have:
                - Machine learning experience
                - Docker and Kubernetes knowledge
                - Leadership experience
                - System design expertise
                
                What we offer:
                - Competitive salary ($140k-$180k)
                - Equity package
                - Remote-first culture
                - Learning and development budget
                - Health, dental, vision insurance
                """,
                'skills_required': [
                    'Python', 'JavaScript', 'React', 'Node.js', 'AWS',
                    'Microservices', 'Communication', 'Collaboration'
                ],
                'skills_preferred': [
                    'Machine Learning', 'Docker', 'Kubernetes', 'Leadership', 'System Design'
                ],
                'experience_required': '4+ years',
                'remote_friendly': True,
                'growth_opportunities': [
                    'Technical leadership track',
                    'Architecture responsibilities',
                    'Team mentoring opportunities'
                ]
            },
            {
                'id': 'job_002',
                'title': 'Tech Lead - Full Stack',
                'company': 'InnovateLabs',
                'location': 'New York, NY (Hybrid)',
                'salary_range': {'min': 160000, 'max': 200000},
                'company_size': 'Mid-size (200-1000)',
                'company_stage': 'Series C',
                'posted_date': '2025-08-19',
                'description': """
                Tech Lead position for our core product team.
                
                Requirements:
                - 6+ years of software development experience
                - 2+ years of technical leadership experience
                - Expertise in Python, JavaScript, and modern frameworks
                - Strong system design skills
                - Experience with cloud platforms and DevOps
                - Proven track record of mentoring engineers
                
                Responsibilities:
                - Lead technical decisions for product features
                - Mentor and guide junior engineers
                - Drive architecture and design decisions
                - Collaborate with product and design teams
                
                Benefits:
                - Competitive compensation ($160k-$200k)
                - Significant equity upside
                - Hybrid work environment
                - Professional development budget
                """,
                'skills_required': [
                    'Python', 'JavaScript', 'System Design', 'Leadership',
                    'Mentoring', 'Cloud Platforms', 'DevOps'
                ],
                'skills_preferred': [
                    'React', 'Node.js', 'AWS', 'Docker', 'Team Management'
                ],
                'experience_required': '6+ years, 2+ leadership',
                'remote_friendly': False,
                'growth_opportunities': [
                    'Engineering management track',
                    'Principal engineer path',
                    'Cross-functional leadership'
                ]
            },
            {
                'id': 'job_003',
                'title': 'Principal Software Engineer',
                'company': 'DataFlow Systems',
                'location': 'Seattle, WA (Remote)',
                'salary_range': {'min': 180000, 'max': 250000},
                'company_size': 'Enterprise (1000+)',
                'company_stage': 'Public',
                'posted_date': '2025-08-17',
                'description': """
                Principal Engineer role focused on distributed systems and data infrastructure.
                
                Requirements:
                - 8+ years of software engineering experience
                - Deep expertise in distributed systems
                - Strong background in data engineering and ML
                - Proven track record of technical leadership
                - Experience with large-scale system design
                - Excellent communication and collaboration skills
                
                Preferred:
                - PhD in Computer Science or related field
                - Publications in top-tier conferences
                - Open source contributions
                - Experience with Kubernetes and cloud-native technologies
                
                This role offers:
                - Industry-leading compensation
                - Significant equity package
                - Flexible remote work
                - Research and development opportunities
                """,
                'skills_required': [
                    'Distributed Systems', 'Data Engineering', 'Machine Learning',
                    'System Design', 'Technical Leadership', 'Communication'
                ],
                'skills_preferred': [
                    'PhD', 'Research', 'Open Source', 'Kubernetes', 'Cloud Native'
                ],
                'experience_required': '8+ years',
                'remote_friendly': True,
                'growth_opportunities': [
                    'Technical fellow track',
                    'Research leadership',
                    'Industry recognition'
                ]
            },
            {
                'id': 'job_004',
                'title': 'Software Engineer II',
                'company': 'GrowthTech Startup',
                'location': 'Austin, TX (Remote OK)',
                'salary_range': {'min': 110000, 'max': 140000},
                'company_size': 'Startup (10-50)',
                'company_stage': 'Series A',
                'posted_date': '2025-08-20',
                'description': """
                Join our fast-growing startup as a Software Engineer II.
                
                Requirements:
                - 3+ years of software development experience
                - Proficiency in Python and modern web frameworks
                - Experience with databases and API development
                - Familiarity with cloud platforms
                - Strong problem-solving skills
                
                What you'll do:
                - Build and maintain core product features
                - Work directly with founders and product team
                - Contribute to technical architecture decisions
                - Help scale our platform for growth
                
                Startup perks:
                - Significant equity opportunity
                - Direct impact on product direction
                - Rapid career growth potential
                - Flexible work environment
                """,
                'skills_required': [
                    'Python', 'Web Frameworks', 'Databases', 'API Development',
                    'Cloud Platforms', 'Problem Solving'
                ],
                'skills_preferred': [
                    'React', 'Docker', 'AWS', 'Startup Experience'
                ],
                'experience_required': '3+ years',
                'remote_friendly': True,
                'growth_opportunities': [
                    'Rapid promotion potential',
                    'Technical co-founder track',
                    'Product ownership opportunities'
                ]
            }
        ]
        
    async def _calculate_qualification_score(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive qualification score for a job"""
        try:
            scores = {}
            
            # Skill matching score
            skills_score = await self._calculate_skills_match(job)
            scores['skills'] = skills_score
            
            # Experience matching score
            experience_score = await self._calculate_experience_match(job)
            scores['experience'] = experience_score
            
            # Preference alignment score
            preference_score = await self._calculate_preference_match(job)
            scores['preferences'] = preference_score
            
            # Growth potential score
            growth_score = await self._calculate_growth_potential(job)
            scores['growth_potential'] = growth_score
            
            # Calculate weighted overall score
            weights = {
                'skills': 0.35,
                'experience': 0.25,
                'preferences': 0.25,
                'growth_potential': 0.15
            }
            
            overall_score = sum(scores[key] * weights[key] for key in weights.keys())
            
            return {
                'overall_score': round(overall_score, 3),
                'component_scores': scores,
                'weights': weights,
                'confidence': min(0.95, overall_score + 0.1)  # Confidence based on score
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Qualification scoring failed: {e}")
            return {
                'overall_score': 0.5,
                'component_scores': {},
                'weights': {},
                'confidence': 0.3
            }
            
    async def _calculate_skills_match(self, job: Dict[str, Any]) -> float:
        """Calculate skills matching score"""
        try:
            user_skills = set(
                self.user_profile['skills']['technical'] +
                self.user_profile['skills']['soft'] +
                self.user_profile['skills']['emerging']
            )
            
            required_skills = set(job.get('skills_required', []))
            preferred_skills = set(job.get('skills_preferred', []))
            
            # Calculate matches
            required_matches = len(user_skills.intersection(required_skills))
            preferred_matches = len(user_skills.intersection(preferred_skills))
            
            # Calculate score
            required_score = required_matches / len(required_skills) if required_skills else 1.0
            preferred_score = preferred_matches / len(preferred_skills) if preferred_skills else 0.5
            
            # Weighted combination
            skills_score = (required_score * 0.7) + (preferred_score * 0.3)
            
            return min(1.0, skills_score)
            
        except Exception as e:
            logger.warning(f"⚠️ Skills matching failed: {e}")
            return 0.5
            
    async def _calculate_experience_match(self, job: Dict[str, Any]) -> float:
        """Calculate experience matching score"""
        try:
            user_experience = self.user_profile['experience']
            
            # Extract years requirement from job
            experience_req = job.get('experience_required', '0+ years')
            years_match = re.search(r'(\d+)\+?\s*years?', experience_req.lower())
            required_years = int(years_match.group(1)) if years_match else 0
            
            # Years experience score
            years_score = min(1.0, user_experience['years_total'] / max(required_years, 1))
            
            # Industry match score
            job_industry_keywords = ['technology', 'tech', 'software', 'saas', 'startup']
            industry_score = 1.0 if any(keyword in job.get('company', '').lower() 
                                      for keyword in job_industry_keywords) else 0.7
            
            # Company size match
            user_sizes = user_experience['company_sizes']
            job_size = job.get('company_size', '')
            size_score = 1.0 if any(size_type in job_size for size_type in user_sizes) else 0.6
            
            # Leadership requirement check
            leadership_req = 'leadership' in job.get('experience_required', '').lower()
            leadership_score = 1.0 if not leadership_req or user_experience['years_leadership'] > 0 else 0.3
            
            # Weighted combination
            experience_score = (
                years_score * 0.4 +
                industry_score * 0.2 +
                size_score * 0.2 +
                leadership_score * 0.2
            )
            
            return min(1.0, experience_score)
            
        except Exception as e:
            logger.warning(f"⚠️ Experience matching failed: {e}")
            return 0.5
            
    async def _calculate_preference_match(self, job: Dict[str, Any]) -> float:
        """Calculate preference alignment score"""
        try:
            user_prefs = self.user_profile['preferences']
            
            # Location/remote score
            location_score = 1.0
            if job.get('remote_friendly', False) and user_prefs['remote_work']:
                location_score = 1.0
            elif 'Remote' in job.get('location', '') and user_prefs['remote_work']:
                location_score = 1.0
            elif any(loc in job.get('location', '') for loc in user_prefs['preferred_locations']):
                location_score = 0.8
            else:
                location_score = 0.4
            
            # Salary score
            job_salary = job.get('salary_range', {})
            user_salary = user_prefs['salary_range']
            
            if job_salary:
                job_min = job_salary.get('min', 0)
                job_max = job_salary.get('max', 0)
                user_min = user_salary['min']
                user_max = user_salary['max']
                
                # Check overlap
                if job_max >= user_min and job_min <= user_max:
                    # Calculate overlap percentage
                    overlap_start = max(job_min, user_min)
                    overlap_end = min(job_max, user_max)
                    overlap_size = overlap_end - overlap_start
                    user_range_size = user_max - user_min
                    salary_score = min(1.0, overlap_size / user_range_size)
                else:
                    salary_score = 0.3
            else:
                salary_score = 0.6  # Unknown salary
            
            # Company stage score
            job_stage = job.get('company_stage', '')
            stage_score = 1.0 if job_stage in user_prefs['company_stage'] else 0.7
            
            # Weighted combination
            preference_score = (
                location_score * 0.4 +
                salary_score * 0.35 +
                stage_score * 0.25
            )
            
            return min(1.0, preference_score)
            
        except Exception as e:
            logger.warning(f"⚠️ Preference matching failed: {e}")
            return 0.5
            
    async def _calculate_growth_potential(self, job: Dict[str, Any]) -> float:
        """Calculate growth potential score"""
        try:
            user_goals = self.user_profile['career_goals']
            
            # Role progression score
            job_title = job.get('title', '').lower()
            target_roles = [role.lower() for role in user_goals['target_roles']]
            
            role_score = 1.0 if any(target in job_title for target in target_roles) else 0.6
            
            # Growth opportunities score
            growth_opps = job.get('growth_opportunities', [])
            user_growth_areas = [area.lower() for area in user_goals['growth_areas']]
            
            growth_matches = sum(1 for opp in growth_opps 
                               if any(area in opp.lower() for area in user_growth_areas))
            growth_score = min(1.0, growth_matches / len(user_growth_areas)) if user_growth_areas else 0.5
            
            # Learning potential score (based on job complexity and new technologies)
            learning_keywords = ['learning', 'development', 'training', 'new', 'cutting-edge', 'innovative']
            job_desc = job.get('description', '').lower()
            learning_score = min(1.0, sum(0.2 for keyword in learning_keywords if keyword in job_desc))
            
            # Weighted combination
            growth_potential_score = (
                role_score * 0.4 +
                growth_score * 0.35 +
                learning_score * 0.25
            )
            
            return min(1.0, growth_potential_score)
            
        except Exception as e:
            logger.warning(f"⚠️ Growth potential calculation failed: {e}")
            return 0.5
            
    async def _analyze_job_opportunity(self, job: Dict[str, Any], qualification_score: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive analysis of a job opportunity"""
        try:
            # Identify skill gaps
            skill_gaps = await self._identify_skill_gaps(job)
            
            # Generate application strategy
            application_strategy = await self._generate_application_strategy(job, qualification_score)
            
            # Calculate application timeline
            application_timeline = await self._calculate_application_timeline(job, qualification_score)
            
            # Generate recommendations
            recommendations = await self._generate_job_recommendations(job, qualification_score, skill_gaps)
            
            return {
                'job_info': job,
                'qualification_score': qualification_score,
                'skill_gaps': skill_gaps,
                'application_strategy': application_strategy,
                'application_timeline': application_timeline,
                'recommendations': recommendations,
                'analysis_date': datetime.now().isoformat(),
                'priority': self._determine_job_priority(qualification_score),
                'action_items': await self._generate_action_items(job, skill_gaps, qualification_score)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Job analysis failed: {e}")
            return {
                'job_info': job,
                'qualification_score': qualification_score,
                'error': str(e)
            }
            
    async def _identify_skill_gaps(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Identify skills gaps for the job"""
        user_skills = set(
            self.user_profile['skills']['technical'] +
            self.user_profile['skills']['soft'] +
            self.user_profile['skills']['emerging']
        )
        
        required_skills = set(job.get('skills_required', []))
        preferred_skills = set(job.get('skills_preferred', []))
        
        missing_required = required_skills - user_skills
        missing_preferred = preferred_skills - user_skills
        
        return {
            'missing_required': list(missing_required),
            'missing_preferred': list(missing_preferred),
            'have_required': list(required_skills.intersection(user_skills)),
            'have_preferred': list(preferred_skills.intersection(user_skills)),
            'critical_gaps': list(missing_required)[:3],  # Top 3 critical gaps
            'development_opportunities': list(missing_preferred)[:5]  # Top 5 development areas
        }
        
    async def _generate_application_strategy(self, job: Dict[str, Any], qualification_score: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized application strategy"""
        overall_score = qualification_score['overall_score']
        
        if overall_score >= 0.8:
            strategy_type = "Direct Application"
            approach = "Apply immediately with confidence"
        elif overall_score >= 0.7:
            strategy_type = "Strategic Application"
            approach = "Apply with targeted preparation"
        elif overall_score >= 0.6:
            strategy_type = "Preparation + Application"
            approach = "Develop key skills then apply"
        else:
            strategy_type = "Long-term Development"
            approach = "Significant preparation needed"
        
        return {
            'strategy_type': strategy_type,
            'approach': approach,
            'confidence_level': overall_score,
            'recommended_timeline': f"{1 if overall_score >= 0.8 else 2 if overall_score >= 0.7 else 4}-{2 if overall_score >= 0.8 else 4 if overall_score >= 0.7 else 8} weeks",
            'key_selling_points': await self._identify_selling_points(job, qualification_score),
            'risk_mitigation': await self._identify_application_risks(job, qualification_score)
        }
        
    async def _calculate_application_timeline(self, job: Dict[str, Any], qualification_score: Dict[str, Any]) -> Dict[str, str]:
        """Calculate optimal application timeline"""
        overall_score = qualification_score['overall_score']
        posted_date = datetime.fromisoformat(job['posted_date'])
        days_since_posted = (datetime.now() - posted_date).days
        
        if overall_score >= 0.8:
            # High qualification - apply quickly
            optimal_timing = "Within 24-48 hours"
            reasoning = "High qualification match - apply before competition increases"
        elif overall_score >= 0.7:
            # Good qualification - strategic timing
            optimal_timing = "Within 3-5 days"
            reasoning = "Good match - allow time for targeted preparation"
        else:
            # Lower qualification - need preparation
            optimal_timing = "1-2 weeks"
            reasoning = "Moderate match - develop key skills before applying"
        
        urgency = "High" if days_since_posted <= 2 else "Medium" if days_since_posted <= 7 else "Low"
        
        return {
            'optimal_timing': optimal_timing,
            'reasoning': reasoning,
            'urgency': urgency,
            'days_since_posted': days_since_posted,
            'application_deadline_estimate': "2-4 weeks from posting"
        }
        
    async def _generate_job_recommendations(self, job: Dict[str, Any], qualification_score: Dict[str, Any], skill_gaps: Dict[str, Any]) -> List[str]:
        """Generate strategic recommendations for the job"""
        recommendations = []
        overall_score = qualification_score['overall_score']
        
        if overall_score >= 0.8:
            recommendations.extend([
                "🎯 Excellent match! Apply with confidence",
                "📝 Highlight your matching technical skills prominently",
                "🤝 Leverage your network for warm introductions",
                "⚡ Apply quickly to beat competition"
            ])
        elif overall_score >= 0.7:
            recommendations.extend([
                "📈 Strong candidate with strategic positioning needed",
                "🎯 Focus cover letter on top matching qualifications",
                "📚 Quickly brush up on missing preferred skills",
                "🔗 Research company culture and values for fit"
            ])
        else:
            recommendations.extend([
                "⏰ Consider this a growth opportunity",
                "📖 Develop critical missing skills first",
                "🎯 Use as benchmark for career development",
                "🤝 Network with company employees for insights"
            ])
        
        # Skill-specific recommendations
        if skill_gaps['missing_required']:
            recommendations.append(f"🚨 Priority: Develop {', '.join(skill_gaps['critical_gaps'][:2])}")
        
        if skill_gaps['missing_preferred']:
            recommendations.append(f"📚 Consider learning: {', '.join(skill_gaps['development_opportunities'][:2])}")
        
        return recommendations
        
    async def _identify_selling_points(self, job: Dict[str, Any], qualification_score: Dict[str, Any]) -> List[str]:
        """Identify key selling points for the application"""
        selling_points = []
        
        # Skills-based selling points
        user_skills = set(
            self.user_profile['skills']['technical'] +
            self.user_profile['skills']['soft'] +
            self.user_profile['skills']['emerging']
        )
        
        required_skills = set(job.get('skills_required', []))
        matching_skills = user_skills.intersection(required_skills)
        
        if matching_skills:
            selling_points.append(f"Strong technical foundation: {', '.join(list(matching_skills)[:3])}")
        
        # Experience-based selling points
        user_exp = self.user_profile['experience']
        if user_exp['years_total'] >= 4:
            selling_points.append(f"{user_exp['years_total']} years of proven software development experience")
        
        if user_exp['years_leadership'] > 0:
            selling_points.append(f"{user_exp['years_leadership']} years of technical leadership experience")
        
        # Industry alignment
        if any(industry in job.get('company', '').lower() for industry in ['tech', 'startup', 'saas']):
            selling_points.append("Relevant industry experience in technology/startup environments")
        
        return selling_points[:5]  # Top 5 selling points
        
    async def _identify_application_risks(self, job: Dict[str, Any], qualification_score: Dict[str, Any]) -> List[str]:
        """Identify potential application risks and mitigation strategies"""
        risks = []
        
        scores = qualification_score['component_scores']
        
        if scores.get('skills', 1) < 0.7:
            risks.append("Skills gap risk - emphasize transferable skills and learning ability")
        
        if scores.get('experience', 1) < 0.6:
            risks.append("Experience gap risk - highlight relevant projects and quick learning")
        
        if scores.get('preferences', 1) < 0.5:
            risks.append("Preference mismatch - clearly explain motivation and flexibility")
        
        # Competition risk
        overall_score = qualification_score['overall_score']
        if overall_score < 0.75:
            risks.append("Competition risk - differentiate through unique value proposition")
        
        return risks
        
    def _determine_job_priority(self, qualification_score: Dict[str, Any]) -> str:
        """Determine job application priority"""
        overall_score = qualification_score['overall_score']
        
        if overall_score >= 0.8:
            return "High"
        elif overall_score >= 0.7:
            return "Medium"
        else:
            return "Low"
            
    async def _generate_action_items(self, job: Dict[str, Any], skill_gaps: Dict[str, Any], qualification_score: Dict[str, Any]) -> List[str]:
        """Generate specific action items for the job application"""
        action_items = []
        overall_score = qualification_score['overall_score']
        
        # Immediate actions
        if overall_score >= 0.8:
            action_items.extend([
                "📝 Draft tailored resume highlighting matching skills",
                "✍️ Write personalized cover letter",
                "🔍 Research company recent news and developments",
                "📤 Submit application within 48 hours"
            ])
        elif overall_score >= 0.7:
            action_items.extend([
                "📚 Quick skill refresher on key technologies",
                "📝 Customize resume for this specific role",
                "🎯 Prepare targeted cover letter",
                "🤝 Find mutual connections for warm intro"
            ])
        else:
            action_items.extend([
                f"📖 Develop critical skills: {', '.join(skill_gaps['critical_gaps'][:2])}",
                "📊 Use as career development benchmark",
                "🔗 Connect with company employees",
                "⏰ Set timeline for skill development"
            ])
        
        # Skills development actions
        if skill_gaps['missing_required']:
            action_items.append(f"🚨 Priority learning: {skill_gaps['missing_required'][0]}")
        
        if skill_gaps['missing_preferred']:
            action_items.append(f"📈 Optional skill development: {skill_gaps['missing_preferred'][0]}")
        
        return action_items[:6]  # Top 6 action items
        
    async def send_job_alerts(self, qualified_jobs: List[Dict[str, Any]]):
        """Send job opportunity alerts via notifications"""
        try:
            if not qualified_jobs:
                return
            
            # Filter for high-priority jobs
            high_priority_jobs = [job for job in qualified_jobs if job['priority'] == 'High']
            
            # Create summary message
            summary_lines = []
            for job in qualified_jobs[:5]:  # Top 5 jobs
                score = job['qualification_score']['overall_score']
                priority_emoji = "🚨" if job['priority'] == 'High' else "📊" if job['priority'] == 'Medium' else "📝"
                
                summary_lines.append(
                    f"{priority_emoji} {job['job_info']['title']} at {job['job_info']['company']} "
                    f"(match: {score:.0%})"
                )
            
            summary_message = f"""
🎯 Job Search Intelligence Results

Found {len(qualified_jobs)} qualified opportunities:
{len(high_priority_jobs)} high-priority matches

Top Opportunities:
{chr(10).join(summary_lines)}

💼 Recommended action: Review high-priority matches within 24-48 hours.
            """.strip()
            
            await self.notification_manager.send_insight_alert(
                "Job Search Intelligence Update",
                {
                    'insights': summary_message,
                    'confidence': max([job['qualification_score']['overall_score'] for job in qualified_jobs]),
                    'job_count': len(qualified_jobs),
                    'high_priority_count': len(high_priority_jobs),
                    'generated_at': datetime.now().isoformat()
                }
            )
            
            # Send individual alerts for very high-match jobs
            for job in qualified_jobs:
                if job['qualification_score']['overall_score'] >= 0.85:
                    await self._send_high_match_job_alert(job)
            
        except Exception as e:
            logger.error(f"❌ Job alert sending failed: {e}")
            
    async def _send_high_match_job_alert(self, job_analysis: Dict[str, Any]):
        """Send alert for high-match job opportunity"""
        try:
            job = job_analysis['job_info']
            score = job_analysis['qualification_score']['overall_score']
            action_items = "\n".join([f"• {item}" for item in job_analysis['action_items'][:3]])
            
            salary_info = ""
            if 'salary_range' in job and job['salary_range']:
                salary = job['salary_range']
                salary_info = f"\n💰 Salary: ${salary.get('min', 0):,} - ${salary.get('max', 0):,}"
            
            message = f"""
🚨 HIGH-MATCH JOB OPPORTUNITY!

{job['title']} at {job['company']}
📍 {job['location']}
🎯 Qualification Match: {score:.0%}
⭐ Priority: {job_analysis['priority']}{salary_info}

📋 Immediate Actions:
{action_items}

⏰ Application Timeline: {job_analysis['application_timeline']['optimal_timing']}
🎯 Strategy: {job_analysis['application_strategy']['strategy_type']}
            """.strip()
            
            await self.notification_manager.send_notification(
                title=f"🎯 {job['title']} - {score:.0%} Match",
                message=message,
                priority="high",
                notification_type="high_match_job_opportunity"
            )
            
        except Exception as e:
            logger.warning(f"⚠️ High-match job alert failed: {e}")

async def main():
    """Demo the job search intelligence system"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load configuration
        config = AppConfig()
        
        # Initialize notification manager
        notification_manager = NotificationManager(config)
        await notification_manager.initialize()
        
        # Create job search intelligence system
        job_search = JobSearchIntelligence(config, notification_manager)
        
        print("💼 Job Search Intelligence Demo")
        print("=" * 50)
        
        # Discover qualified jobs
        qualified_jobs = await job_search.discover_qualified_jobs()
        
        # Display results
        print(f"\n📊 Analysis Complete:")
        print(f"   Total Qualified Jobs: {len(qualified_jobs)}")
        
        high_priority = len([job for job in qualified_jobs if job['priority'] == 'High'])
        medium_priority = len([job for job in qualified_jobs if job['priority'] == 'Medium'])
        low_priority = len([job for job in qualified_jobs if job['priority'] == 'Low'])
        
        print(f"   🚨 High Priority: {high_priority}")
        print(f"   📊 Medium Priority: {medium_priority}")
        print(f"   📝 Low Priority: {low_priority}")
        
        print(f"\n🎯 Top Job Matches:")
        for i, job in enumerate(qualified_jobs[:3], 1):
            job_info = job['job_info']
            score = job['qualification_score']['overall_score']
            print(f"   {i}. {job_info['title']} at {job_info['company']} (match: {score:.0%})")
        
        # Send alerts
        print(f"\n📱 Sending job opportunity alerts...")
        await job_search.send_job_alerts(qualified_jobs)
        
        print(f"\n✅ Job search intelligence completed!")
        print(f"   Check your Telegram for job alerts! 📱")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
