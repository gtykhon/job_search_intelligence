#!/usr/bin/env python3
"""
Enhanced JobSpy Integration for Daily Opportunity Detection
Uses centralized configuration and provides real job opportunities
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.company_research_db import (
    get_company_record,
    upsert_company_from_research,
    mark_avoided_company,
)

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Ensure auto_company_research helpers are importable (for Glassdoor Playwright scraper)
auto_company_dir = os.path.join(parent_dir, "features_to_built", "auto_company_research")
if auto_company_dir not in sys.path:
    sys.path.insert(0, auto_company_dir)

# Import centralized configuration
try:
    from config.job_search_config import (
        JOBSPY_SEARCH_QUERIES,
        JOBSPY_CONFIG,
        PREFERRED_SKILLS,
        PREFERRED_COMPANIES,
        IGNORED_COMPANIES,
        MIN_SALARY,
        SCORING_WEIGHTS,
        MIN_OPPORTUNITY_SCORE,
        PREFERRED_INDUSTRIES,
        AVOIDED_INDUSTRIES,
        COMPANY_RESEARCH_CONFIG,
        check_company_tier,
        calculate_skills_authenticity_score,
        is_preferred_company,
        calculate_salary_score,
    )
    CONFIG_IMPORTED = True
    print("✅ Centralized config imported successfully")
except ImportError as e:
    print(f"❌ Could not import centralized config: {e}")
    CONFIG_IMPORTED = False
    
    # Comprehensive fallback configuration based on your LinkedIn profile
    # Grygorii T: Senior Software Engineer, 7 years experience
    JOBSPY_SEARCH_QUERIES = [
        {"search_term": "Senior Software Engineer", "location": "Remote"},
        {"search_term": "Senior Python Developer", "location": "Remote"},
        {"search_term": "Data Engineer", "location": "Remote"},
        {"search_term": "Backend Developer Python", "location": "Remote"},
        {"search_term": "Full Stack Engineer", "location": "Remote"}
    ]
    
    JOBSPY_CONFIG = {
        "results_wanted": 25,
        "hours_old": 168,
        "country_indeed": "USA",
        "site_name": ["linkedin", "indeed"],
        "is_remote": True,
        "job_type": "fulltime"
    }
    
    # Skills from your LinkedIn profile
    PREFERRED_SKILLS = [
        "Python", "JavaScript", "AWS", "Django", "Docker", "PostgreSQL", 
        "React", "Git", "Linux", "Agile", "Kubernetes", "Node.js", "MongoDB", 
        "Redis", "CI/CD", "Java", "Go", "SQL", "ETL", "Data Engineering",
        "Apache Spark", "Airflow", "Pandas", "NumPy", "Machine Learning"
    ]
    
    PREFERRED_COMPANIES = [
        "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla",
        "Spotify", "Uber", "Airbnb", "Salesforce", "Adobe", "IBM", "Oracle",
        "Stripe", "Slack", "Zoom", "Datadog", "Snowflake", "Palantir"
    ]
    
    IGNORED_COMPANIES = ["Unknown Company", "Confidential", "Undisclosed"]
    
    # Based on your profile: 7 years experience, Senior SWE, salary expectations $140k-$150k
    MIN_SALARY = {"senior": 140000, "staff": 160000, "principal": 180000, "default": 120000}
    
    SCORING_WEIGHTS = {
        "company_preference": 0.30,
        "salary_match": 0.25,
        "title_relevance": 0.20,
        "skills_match": 0.15,
        "location_preference": 0.10
    }
    
    def is_preferred_company(company_name: str) -> bool:
        """Fallback function to check if company is preferred"""
        if not company_name or company_name in IGNORED_COMPANIES:
            return False
        return any(preferred.lower() in company_name.lower() for preferred in PREFERRED_COMPANIES)
    
    def calculate_salary_score(salary_min: int, salary_max: int, role_level: str = "default") -> float:
        """Fallback function to calculate salary score"""
        if not salary_min and not salary_max:
            return 0.0
        
        target_min = MIN_SALARY.get(role_level, MIN_SALARY["default"])
        actual_min = salary_min or salary_max or 0
        
        if actual_min >= target_min:
            return 1.0
        elif actual_min >= target_min * 0.8:
            return 0.7
        elif actual_min >= target_min * 0.6:
            return 0.4
        else:
            return 0.1

logger = logging.getLogger(__name__)

# Optional company research system (culture/WLB/toxicity screening)
try:
    from features_to_built.auto_company_research.company_verification_system import (
        CompanyVerificationSystem,
        DecisionStatus,
    )
    COMPANY_RESEARCH_AVAILABLE = True
except Exception:
    CompanyVerificationSystem = None  # type: ignore
    DecisionStatus = None  # type: ignore
    COMPANY_RESEARCH_AVAILABLE = False

class EnhancedJobSpyIntegration:
    """Enhanced JobSpy integration using centralized configuration"""
    
    def __init__(self):
        self.config = JOBSPY_CONFIG
        self.search_queries = JOBSPY_SEARCH_QUERIES

        # Optional company research (culture/WLB/toxicity) integration
        self.company_research_enabled = (
            COMPANY_RESEARCH_AVAILABLE
            and COMPANY_RESEARCH_CONFIG.get("enabled", False)
        )
        self.company_verifier: Optional[CompanyVerificationSystem] = None  # type: ignore
        self.company_research_cache: Dict[str, Dict[str, Any]] = {}

        if self.company_research_enabled and CompanyVerificationSystem is not None:
            try:
                self.company_verifier = CompanyVerificationSystem(
                    database_path=COMPANY_RESEARCH_CONFIG.get(
                        "database_path", "company_research_database.md"
                    ),
                    web_search_api_key=None,
                    use_glassdoor_scraper=COMPANY_RESEARCH_CONFIG.get(
                        "use_glassdoor_scraper", False
                    ),
                    glassdoor_cache_dir=COMPANY_RESEARCH_CONFIG.get(
                        "glassdoor_cache_dir", "./glassdoor_cache/"
                    ),
                )
            except Exception as e:
                logger.warning(
                    f"Company research system disabled due to init error: {e}"
                )
                self.company_research_enabled = False
        
    async def get_real_job_opportunities(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """
        Get real job opportunities using JobSpy with centralized configuration
        
        Args:
            max_jobs: Maximum number of jobs to return
            
        Returns:
            List of job opportunities with real URLs and data
        """
        try:
            import jobspy
            logger.info(f"🔍 Starting enhanced JobSpy search for {len(self.search_queries)} job types")
            
            all_jobs = []
            
            for query in self.search_queries[:5]:  # Limit to first 5 queries for speed
                try:
                    search_term = query["search_term"]
                    location = query["location"]
                    
                    logger.info(f"🔍 Searching for '{search_term}' in '{location}'...")
                    
                    # Execute JobSpy search - exclude problematic sources
                    jobs_df = jobspy.scrape_jobs(
                        search_term=search_term,
                        location=location,
                        results_wanted=self.config.get("results_wanted", 25),
                        hours_old=self.config.get("hours_old", 168),
                        country_indeed=self.config.get("country_indeed", "USA"),
                        site_name=["linkedin", "indeed"],  # Exclude glassdoor due to 403 errors
                        is_remote=self.config.get("is_remote", True),
                        job_type=self.config.get("job_type", "fulltime"),
                        verbose=0  # Reduce output noise
                    )
                    
                    if jobs_df is not None and not jobs_df.empty:
                        # Convert DataFrame to our format
                        for _, job in jobs_df.iterrows():
                            job_dict = self._convert_jobspy_job(job, search_term)
                            if job_dict:
                                all_jobs.append(job_dict)
                        
                        logger.info(f"✅ Found {len(jobs_df)} jobs for '{search_term}'")
                    else:
                        logger.warning(f"⚠️ No jobs found for '{search_term}' in '{location}'")
                        
                except Exception as e:
                    logger.error(f"❌ Error searching for '{search_term}': {e}")
                    continue
            
            # Remove duplicates and sort by score
            unique_jobs = self._remove_duplicates(all_jobs)
            scored_jobs = self._score_and_rank_jobs(unique_jobs)
            
            # Return top jobs up to max_jobs limit
            top_jobs = scored_jobs[:max_jobs]
            
            logger.info(f"✅ Enhanced JobSpy search complete: {len(top_jobs)} unique opportunities found")
            return top_jobs
            
        except ImportError:
            logger.error("❌ JobSpy not installed. Run: pip install python-jobspy")
            return []
        except Exception as e:
            logger.error(f"❌ Enhanced JobSpy search failed: {e}")
            return []
    
    def _convert_jobspy_job(self, job_row, search_term: str) -> Optional[Dict[str, Any]]:
        """Convert JobSpy DataFrame row to our job format"""
        try:
            # Extract salary information with NaN handling
            salary_min = None
            salary_max = None
            
            if hasattr(job_row, 'min_amount') and job_row.min_amount is not None:
                try:
                    # Handle NaN values
                    if str(job_row.min_amount).lower() != 'nan' and job_row.min_amount != '':
                        salary_min = int(float(job_row.min_amount))
                except (ValueError, TypeError):
                    salary_min = None
                    
            if hasattr(job_row, 'max_amount') and job_row.max_amount is not None:
                try:
                    # Handle NaN values  
                    if str(job_row.max_amount).lower() != 'nan' and job_row.max_amount != '':
                        salary_max = int(float(job_row.max_amount))
                except (ValueError, TypeError):
                    salary_max = None
            
            # Create job dictionary with safe string conversion
            job_dict = {
                "title": str(job_row.title) if hasattr(job_row, 'title') and job_row.title is not None else search_term,
                "company": str(job_row.company) if hasattr(job_row, 'company') and job_row.company is not None else "Unknown Company",
                "location": str(job_row.location) if hasattr(job_row, 'location') and job_row.location is not None else "Remote",
                "job_url": str(job_row.job_url) if hasattr(job_row, 'job_url') and job_row.job_url is not None else "",
                "description": str(job_row.description) if hasattr(job_row, 'description') and job_row.description is not None else "",
                "posted_date": str(job_row.date_posted) if hasattr(job_row, 'date_posted') and job_row.date_posted is not None else str(datetime.now().date()),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "source": str(job_row.site) if hasattr(job_row, 'site') and job_row.site is not None else "jobspy",
                "search_term": search_term,
                "timestamp": datetime.now().isoformat()
            }
            
            # Validate essential fields and handle NaN in URLs
            job_url = job_dict["job_url"]
            if not job_url or job_url == "nan" or str(job_url).lower() == 'nan':
                logger.warning(f"⚠️ Skipping job without valid URL: {job_dict['title']}")
                return None
                
            return job_dict
            
        except Exception as e:
            logger.error(f"❌ Error converting job row: {e}")
            return None
    
    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on URL and title+company"""
        seen_urls = set()
        seen_combinations = set()
        unique_jobs = []
        
        for job in jobs:
            # Check URL uniqueness
            url = job.get("job_url", "")
            if url and url in seen_urls:
                continue
            
            # Check title+company uniqueness
            combination = f"{job.get('title', '').lower()}|{job.get('company', '').lower()}"
            if combination in seen_combinations:
                continue
            
            # Add to unique jobs
            if url:
                seen_urls.add(url)
            seen_combinations.add(combination)
            unique_jobs.append(job)
        
        return unique_jobs
    
    def _score_and_rank_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score and rank jobs based on centralized criteria"""
        scored_jobs = []
        
        for job in jobs:
            # Optional company culture/toxicity research and filtering
            research_info = self._run_company_research(job)
            if research_info is not None:
                job.update(research_info)

                # Apply research-based filters (weed out toxic/defense-heavy companies)
                if research_info.get("filtered_out"):
                    continue

            score = self._calculate_job_score_v2(job)

            # Apply minimum opportunity score threshold when using centralized config
            try:
                if CONFIG_IMPORTED and score < MIN_OPPORTUNITY_SCORE:
                    continue
            except Exception:
                # If threshold unavailable, fall back to including all jobs
                pass

            job["match_score"] = score
            job["match_percentage"] = f"{score * 100:.1f}%"
            scored_jobs.append(job)
        
        # Sort by score (highest first)
        scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_jobs

    def _run_company_research(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Run company verification (culture/WLB/toxicity) for a job.

        Returns a small dict of annotations or None if research is disabled/unavailable.
        """
        if not self.company_research_enabled or not self.company_verifier:
            return None

        company = (job.get("company") or "").strip()
        title = (job.get("title") or "").strip()

        if not company:
            return None

        cache_key = company.lower()

        # Check in-memory cache first
        if cache_key in self.company_research_cache:
            return self.company_research_cache[cache_key]

        # Check persistent DB to avoid re-running research
        db_record = get_company_record(company)
        if db_record:
            # If explicitly avoided in DB, respect that immediately
            annotations = {
                "company_decision_status": db_record.get("decision_status"),
                "company_culture_score": db_record.get("culture_score"),
                "company_wlb_score": db_record.get("wlb_score"),
                "company_risk_level": db_record.get("risk_level"),
                "glassdoor_overall_rating": db_record.get("glassdoor_overall"),
                "glassdoor_total_reviews": db_record.get("glassdoor_reviews"),
                "filtered_out": bool(db_record.get("avoided_flag", False)),
            }
            self.company_research_cache[cache_key] = annotations
            return annotations

        # Run full verification workflow as a fallback
        try:
            result = self.company_verifier.verify_company(company, title)
        except Exception as e:
            logger.warning(f"Company research error for '{company}': {e}")
            self.company_research_cache[cache_key] = None  # type: ignore
            return None

        annotations: Dict[str, Any] = {
            "company_decision_status": result.decision_status.value,
            "company_culture_score": (
                result.scoring_result.culture_score
                if result.scoring_result
                else None
            ),
            "company_wlb_score": (
                result.scoring_result.wlb_score
                if result.scoring_result
                else None
            ),
            "company_risk_level": (
                result.scoring_result.risk_level
                if result.scoring_result
                else None
            ),
            "glassdoor_overall_rating": (
                result.glassdoor_metrics.overall_rating
                if result.glassdoor_metrics
                else None
            ),
            "glassdoor_total_reviews": (
                result.glassdoor_metrics.total_reviews
                if result.glassdoor_metrics
                else None
            ),
        }

        # Determine if this company should be filtered out
        filtered_out = False

        try:
            # Auto-decline from verification system (defense/government/very low ratings)
            if (
                COMPANY_RESEARCH_CONFIG.get("respect_auto_decline", True)
                and DecisionStatus is not None
                and result.decision_status == DecisionStatus.AUTO_DECLINE
            ):
                filtered_out = True

            # Culture/WLB thresholds
            min_culture = COMPANY_RESEARCH_CONFIG.get("min_culture_score", 65)
            min_wlb = COMPANY_RESEARCH_CONFIG.get("min_wlb_score", 65)

            culture_score = annotations["company_culture_score"]
            wlb_score = annotations["company_wlb_score"]

            if culture_score is not None and culture_score < min_culture:
                filtered_out = True

            if wlb_score is not None and wlb_score < min_wlb:
                filtered_out = True
        except Exception as e:
            logger.warning(f"Company research filtering error for '{company}': {e}")

        annotations["filtered_out"] = filtered_out

        # Persist to DB for future searches
        try:
            # Use preferred-company tiers if possible
            from config.job_search_config import check_company_tier  # type: ignore
        except Exception:
            tier = None
        else:
            try:
                tier = check_company_tier(company)
            except Exception:
                tier = None

        try:
            upsert_company_from_research(result, tier=tier)
        except Exception as e:
            logger.warning(f"Failed to persist company research for '{company}': {e}")

        self.company_research_cache[cache_key] = annotations
        return annotations
    
    def _calculate_job_score_v2(self, job: Dict[str, Any]) -> float:
        """
        New scoring logic aligned with strategic config.
        
        Uses config.job_search_config weights:
          - company_tier
          - salary_match
          - skills_authenticity
          - title_level
          - industry_alignment
        
        Falls back to the legacy _calculate_job_score when the centralized
        config is not available.
        """
        if not CONFIG_IMPORTED:
            # Fall back to the original scoring if config import failed
            return self._calculate_job_score(job)

        score = 0.0

        try:
            company = (job.get("company") or "").strip()
            title = (job.get("title") or "").strip()
            description = (job.get("description") or "").strip()
            location = (job.get("location") or "").strip()
            salary_min = job.get("salary_min")
            salary_max = job.get("salary_max")

            # 1) Company tier / exclusion (35%)
            try:
                # Hard exclusion for explicitly ignored companies
                if company and any(
                    ignored.lower() in company.lower() for ignored in IGNORED_COMPANIES
                ):
                    return 0.0

                tier = check_company_tier(company) if company else 0
                if tier > 0:
                    company_score = tier / 3.0  # 1/3, 2/3, 1.0 for tiers 1-3
                elif company:
                    # Non-ignored, non-preferred company still gets some credit
                    company_score = 0.4
                else:
                    company_score = 0.0

                score += SCORING_WEIGHTS["company_tier"] * company_score
            except Exception as e:
                logger.warning(f"Company scoring error: {e}")
                if company:
                    score += SCORING_WEIGHTS["company_tier"] * 0.4

            # 2) Salary match (25%)
            try:
                if salary_min is not None or salary_max is not None:
                    role_level = self._determine_role_level(title)
                    salary_score = calculate_salary_score(
                        salary_min, salary_max, role_level
                    )
                    score += SCORING_WEIGHTS["salary_match"] * salary_score
            except Exception as e:
                logger.warning(f"Salary scoring error: {e}")
                if salary_min and salary_min >= MIN_SALARY.get("default", 0):
                    score += SCORING_WEIGHTS["salary_match"] * 0.5

            # 3) Skills authenticity (20%)
            try:
                authenticity_score = calculate_skills_authenticity_score(description)
                score += SCORING_WEIGHTS["skills_authenticity"] * authenticity_score
            except Exception as e:
                logger.warning(f"Skills authenticity scoring error: {e}")
                desc_lower = description.lower()
                skills_found = sum(
                    1 for skill in PREFERRED_SKILLS if skill.lower() in desc_lower
                )
                simple_score = min(
                    skills_found / max(len(PREFERRED_SKILLS), 1), 1.0
                )
                score += SCORING_WEIGHTS["skills_authenticity"] * simple_score

            # 4) Title level (10%)
            try:
                role_level = self._determine_role_level(title)
                level_map = {
                    "principal": 1.0,
                    "senior": 0.9,
                    "manager": 0.7,
                    "default": 0.5,
                }
                title_score = level_map.get(role_level, 0.5)
                score += SCORING_WEIGHTS["title_level"] * title_score
            except Exception as e:
                logger.warning(f"Title level scoring error: {e}")

            # 5) Industry / mission alignment (10%)
            try:
                text = f"{title} {description} {location}".lower()
                preferred_hits = 0
                for industry in PREFERRED_INDUSTRIES:
                    if industry.lower() in text:
                        preferred_hits += 1

                if preferred_hits:
                    industry_score = min(
                        preferred_hits / max(len(PREFERRED_INDUSTRIES), 1), 1.0
                    )
                else:
                    industry_score = 0.0

                # Penalize avoided industries if detected in text
                for avoided in AVOIDED_INDUSTRIES:
                    if avoided.lower() in text:
                        industry_score *= 0.5
                        break

                score += SCORING_WEIGHTS["industry_alignment"] * industry_score
            except Exception as e:
                logger.warning(f"Industry alignment scoring error: {e}")

            # Small bonus for explicitly remote roles if not already captured
            try:
                if "remote" in location.lower() and score < 1.0:
                    score += 0.02
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error calculating score for job: {e}")
            score = 0.5  # Neutral fallback

        return min(score, 1.0)
    
    def _calculate_job_score(self, job: Dict[str, Any]) -> float:
        """Calculate job score based on centralized scoring criteria with robust error handling"""
        score = 0.0
        
        try:
            # Company preference score (30%)
            company = job.get("company", "")
            try:
                if is_preferred_company(company):
                    score += SCORING_WEIGHTS["company_preference"]
            except Exception as e:
                logger.warning(f"⚠️ Company scoring error: {e}")
                # Fallback scoring for company
                if company and company not in IGNORED_COMPANIES:
                    score += 0.15  # Give some points for having a company name
            
            # Salary score (25%)
            salary_min = job.get("salary_min")
            salary_max = job.get("salary_max")
            try:
                if salary_min or salary_max:
                    role_level = self._determine_role_level(job.get("title", ""))
                    salary_score = calculate_salary_score(salary_min, salary_max, role_level)
                    score += SCORING_WEIGHTS["salary_match"] * salary_score
            except Exception as e:
                logger.warning(f"⚠️ Salary scoring error: {e}")
                # Fallback salary scoring
                if salary_min and salary_min >= 100000:
                    score += 0.15  # Some points for decent salary
            
            # Title relevance (20%)
            title = job.get("title", "").lower()
            try:
                if any(skill.lower() in title for skill in PREFERRED_SKILLS[:10]):  # Check top skills
                    score += SCORING_WEIGHTS["title_relevance"]
            except Exception as e:
                logger.warning(f"⚠️ Title scoring error: {e}")
                # Fallback title scoring
                if any(keyword in title for keyword in ["senior", "python", "engineer", "developer"]):
                    score += 0.1
            
            # Skills match (15%)
            description = job.get("description", "").lower()
            try:
                skills_found = sum(1 for skill in PREFERRED_SKILLS if skill.lower() in description)
                skills_score = min(skills_found / len(PREFERRED_SKILLS), 1.0)
                score += SCORING_WEIGHTS["skills_match"] * skills_score
            except Exception as e:
                logger.warning(f"⚠️ Skills scoring error: {e}")
                # Fallback skills scoring
                if any(skill in description for skill in ["python", "javascript", "aws", "docker"]):
                    score += 0.08
            
            # Location preference (10%) - boost for remote
            location = job.get("location", "").lower()
            try:
                if "remote" in location or "work from home" in location:
                    score += SCORING_WEIGHTS["location_preference"]
            except Exception as e:
                logger.warning(f"⚠️ Location scoring error: {e}")
                # Fallback location scoring
                if "remote" in location:
                    score += 0.05
            
        except Exception as e:
            logger.error(f"❌ Error calculating score for job: {e}")
            score = 0.5  # Default neutral score
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _determine_role_level(self, title: str) -> str:
        """Determine role level from job title"""
        title_lower = title.lower()
        
        if "principal" in title_lower or "architect" in title_lower:
            return "principal"
        elif "staff" in title_lower or "sr." in title_lower or "senior" in title_lower:
            return "senior"
        elif "manager" in title_lower or "lead" in title_lower:
            return "manager"
        else:
            return "default"

# Async wrapper function for easy integration
async def get_enhanced_job_opportunities(max_jobs: int = 50) -> List[Dict[str, Any]]:
    """
    Easy async function to get job opportunities using enhanced JobSpy integration
    
    Args:
        max_jobs: Maximum number of jobs to return
        
    Returns:
        List of real job opportunities with scoring and ranking
    """
    integrator = EnhancedJobSpyIntegration()
    return await integrator.get_real_job_opportunities(max_jobs)

# Synchronous wrapper for immediate use
def get_enhanced_job_opportunities_sync(max_jobs: int = 50) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for getting job opportunities
    
    Args:
        max_jobs: Maximum number of jobs to return
        
    Returns:
        List of real job opportunities
    """
    try:
        # Create a new integration instance and call the method directly
        integration = EnhancedJobSpyIntegration()
        
        # Call the async method in a new event loop
        import asyncio
        try:
            # Try to get existing loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, we need to create a new thread
            import concurrent.futures
            import threading
            
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(integration.get_real_job_opportunities(max_jobs))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result(timeout=300)  # 5 minute timeout
                
        except RuntimeError:
            # No running loop, can use asyncio.run directly
            return asyncio.run(integration.get_real_job_opportunities(max_jobs))
            
    except Exception as e:
        logger.error(f"❌ Error in sync wrapper: {e}")
        # Return empty list as fallback
        return []

if __name__ == "__main__":
    # Test the enhanced integration
    print("🔍 Testing Enhanced JobSpy Integration")
    jobs = get_enhanced_job_opportunities_sync(10)
    
    if jobs:
        print(f"✅ Found {len(jobs)} job opportunities:")
        for i, job in enumerate(jobs[:3], 1):
            print(f"\n{i}. {job['title']} at {job['company']}")
            print(f"   📍 {job['location']} | 💰 ${job.get('salary_min', 0):,} - ${job.get('salary_max', 0):,}")
            print(f"   🎯 Match: {job['match_percentage']} | 🔗 {job['job_url'][:80]}...")
    else:
        print("❌ No jobs found")
