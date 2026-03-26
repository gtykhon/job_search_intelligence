"""
JobSpy integration for unified job board scraping

JobSpy provides a clean interface for:
- LinkedIn, Indeed, Glassdoor, Google Jobs
- Standardized output format
- Built-in rate limiting and proxy support
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd

from .scraping_errors import ScrapingError, ExternalServiceError
from .async_helpers import retry_with_circuit_breaker
from .models import JobListing, JobSite, JobType, ExperienceLevel, RemoteType, ScrapingRequest


class JobSpyScraper:
    """
    JobSpy-based scraper for major job boards
    
    Features:
    - Multi-site scraping with single interface
    - Built-in rate limiting and proxy support
    - Standardized data format
    - Robust error handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # JobSpy configuration
        self.max_workers = self.config.get('max_workers', 3)
        self.request_delay = self.config.get('request_delay', 2.0)
        self.timeout = self.config.get('timeout', 30)
        
        # Rate limiting
        self.requests_per_minute = self.config.get('requests_per_minute', 30)
        self._last_request_time = 0
        
    async def initialize(self) -> bool:
        """Initialize the scraper"""
        try:
            # Test import
            import jobspy
            self.logger.info("✅ JobSpy scraper initialized successfully")
            return True
        except ImportError:
            self.logger.error("❌ JobSpy not installed. Install with: pip install python-jobspy")
            return False
    
    @retry_with_circuit_breaker(max_attempts=3, delay=2.0, backoff=2.0)
    async def scrape_jobs(self, request: ScrapingRequest) -> List[JobListing]:
        """
        Scrape jobs using JobSpy
        
        Args:
            request: Scraping request with search parameters
            
        Returns:
            List of JobListing objects
            
        Raises:
            ScrapingError: If scraping fails
        """
        try:
            import jobspy
            
            # Apply rate limiting
            await self._apply_rate_limit()
            
            # Convert our request to JobSpy parameters
            jobspy_params = self._convert_request_to_jobspy(request)
            
            self.logger.info(f"🔍 Starting JobSpy scrape: {request.keywords} in {request.location}")
            
            # Run JobSpy scraping in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            
            def run_jobspy():
                return jobspy.scrape_jobs(**jobspy_params)
            
            # Execute in thread pool to avoid blocking
            df_jobs = await loop.run_in_executor(None, run_jobspy)
            
            if df_jobs is None or df_jobs.empty:
                self.logger.warning("⚠️  No jobs found with JobSpy")
                return []
            
            # Convert DataFrame to our JobListing objects
            jobs = await self._convert_jobspy_results(df_jobs, request)
            
            self.logger.info(f"✅ JobSpy scraped {len(jobs)} jobs successfully")
            return jobs
            
        except ImportError:
            raise ScrapingError("JobSpy not installed", url=f"search:{request.keywords}")
        except Exception as e:
            self.logger.error(f"❌ JobSpy scraping failed: {e}")
            raise ScrapingError(f"JobSpy scraping failed: {e}", url=f"search:{request.keywords}")
    
    def _convert_request_to_jobspy(self, request: ScrapingRequest) -> Dict[str, Any]:
        """Convert our request format to JobSpy parameters"""

        # Attempt to augment search with GREEN keywords from active keyword profile
        try:
            from src.intelligence.keyword_profile import KeywordProfileManager
            _kpm = KeywordProfileManager()
            _profile = _kpm.load("default")
            if _profile.green:
                # Pick up to 3 green keywords that don't overlap existing search terms
                existing = (request.keywords or "").lower()
                boost_kws = [
                    kw for kw in _profile.green[:5]
                    if kw.lower() not in existing
                ][:3]
                if boost_kws:
                    self.logger.debug("Boosting search with GREEN keywords: %s", boost_kws)
                    # Note: we don't add to search_term directly to avoid over-constraining
                    # results; this is stored for reference only
        except Exception:
            pass  # Never let keyword profile loading break the scraper

        # Map our job sites to JobSpy site names
        site_mapping = {
            JobSite.LINKEDIN: "linkedin",
            JobSite.INDEED: "indeed", 
            JobSite.GLASSDOOR: "glassdoor",
            JobSite.GOOGLE_JOBS: "google",
            JobSite.ZIP_RECRUITER: "zip_recruiter"
        }
        
        # Convert sites
        jobspy_sites = []
        for site in request.job_sites:
            if site in site_mapping:
                jobspy_sites.append(site_mapping[site])
        
        if not jobspy_sites:
            jobspy_sites = ["indeed"]  # Default fallback
        
        # Convert job type
        job_type_mapping = {
            JobType.FULL_TIME: "fulltime",
            JobType.PART_TIME: "parttime", 
            JobType.CONTRACT: "contract",
            JobType.TEMPORARY: "temporary",
            JobType.INTERNSHIP: "internship"
        }
        
        jobspy_job_type = None
        if request.job_type:
            jobspy_job_type = job_type_mapping.get(request.job_type)
        
        # Convert experience level
        experience_mapping = {
            ExperienceLevel.ENTRY: "entry_level",
            ExperienceLevel.MID: "mid_level",
            ExperienceLevel.SENIOR: "senior_level",
            ExperienceLevel.EXECUTIVE: "director"
        }
        
        jobspy_experience = None
        if request.experience_level:
            jobspy_experience = experience_mapping.get(request.experience_level)
        
        # Convert remote type  
        remote_mapping = {
            RemoteType.REMOTE: True,
            RemoteType.HYBRID: False,
            RemoteType.ON_SITE: False
        }
        
        is_remote = False  # Default to False instead of None
        if request.remote_type:
            is_remote = remote_mapping.get(request.remote_type, False)
        
        params = {
            "site_name": jobspy_sites,
            "search_term": request.keywords,
            "location": request.location,
            "distance": request.radius_miles,
            "job_type": jobspy_job_type,
            "is_remote": is_remote,
            "results_wanted": min(request.max_results, 100),  # Limit to avoid timeouts
            "country_indeed": "USA"
        }

        # Fetch full descriptions from LinkedIn (slower but complete text)
        if "linkedin" in jobspy_sites:
            params["linkedin_fetch_description"] = True

        return params
    
    async def _convert_jobspy_results(self, df_jobs: pd.DataFrame, request: ScrapingRequest) -> List[JobListing]:
        """Convert JobSpy DataFrame results to our JobListing objects"""
        jobs = []
        
        for _, row in df_jobs.iterrows():
            try:
                # Parse basic information
                title = str(row.get('title', 'Unknown Title'))
                company = str(row.get('company', 'Unknown Company'))
                location = str(row.get('location', request.location))
                description = str(row.get('description', ''))
                job_url = str(row.get('job_url', ''))
                
                # Skip if no URL
                if not job_url or job_url == 'nan':
                    continue
                
                # Parse job site
                site_str = str(row.get('site', 'indeed')).lower()
                source_site = self._parse_job_site(site_str)
                
                # Parse dates
                posted_date = self._parse_date(row.get('date_posted'))
                
                # Parse salary
                salary_min, salary_max = self._parse_salary(row)
                
                # Parse job type
                job_type = self._parse_job_type(row.get('job_type'))
                
                # Parse remote type
                remote_type = self._parse_remote_type(row)
                
                # Extract DC area specific information
                clearance_required = self._extract_clearance_info(description)
                metro_accessible = self._check_metro_accessibility(location, description)
                
                # Create JobListing
                job = JobListing(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    job_url=job_url,
                    job_id=str(row.get('job_id', '')),
                    company_url=str(row.get('company_url', '')) if pd.notna(row.get('company_url')) else None,
                    job_type=job_type,
                    remote_type=remote_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    posted_date=posted_date,
                    source_site=source_site,
                    clearance_required=clearance_required,
                    metro_accessible=metro_accessible,
                    # Company intelligence data
                    company_industry=str(row.get('company_industry', '')) if pd.notna(row.get('company_industry')) else None,
                    company_num_employees=str(row.get('company_num_employees', '')) if pd.notna(row.get('company_num_employees')) else None,
                    company_revenue=str(row.get('company_revenue', '')) if pd.notna(row.get('company_revenue')) else None,
                    company_rating=float(row.get('company_rating')) if pd.notna(row.get('company_rating')) else None,
                    company_reviews_count=int(row.get('company_reviews_count')) if pd.notna(row.get('company_reviews_count')) else None,
                    company_description=str(row.get('company_description', '')) if pd.notna(row.get('company_description')) else None,
                    raw_data=row.to_dict()
                )
                
                jobs.append(job)
                
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to parse job row: {e}")
                continue
        
        return jobs
    
    def _parse_job_site(self, site_str: str) -> JobSite:
        """Parse job site from string"""
        site_mapping = {
            'linkedin': JobSite.LINKEDIN,
            'indeed': JobSite.INDEED,
            'glassdoor': JobSite.GLASSDOOR,
            'google': JobSite.GOOGLE_JOBS,
            'zip_recruiter': JobSite.ZIP_RECRUITER
        }
        return site_mapping.get(site_str, JobSite.CUSTOM)
    
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_value or str(date_value) == 'nan':
            return None
        
        try:
            if isinstance(date_value, datetime):
                return date_value
            elif isinstance(date_value, str):
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y']:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return None
    
    def _parse_salary(self, row: pd.Series) -> tuple[Optional[float], Optional[float]]:
        """Parse salary information"""
        try:
            salary_min = row.get('min_amount')
            salary_max = row.get('max_amount')
            
            # Convert to float if possible
            if salary_min and str(salary_min) != 'nan':
                salary_min = float(salary_min)
            else:
                salary_min = None
                
            if salary_max and str(salary_max) != 'nan':
                salary_max = float(salary_max)
            else:
                salary_max = None
                
            return salary_min, salary_max
            
        except (ValueError, TypeError):
            return None, None
    
    def _parse_job_type(self, job_type_str: Any) -> Optional[JobType]:
        """Parse job type from string"""
        if not job_type_str or str(job_type_str) == 'nan':
            return None
        
        job_type_str = str(job_type_str).lower()
        
        type_mapping = {
            'fulltime': JobType.FULL_TIME,
            'full_time': JobType.FULL_TIME,
            'full-time': JobType.FULL_TIME,
            'parttime': JobType.PART_TIME,
            'part_time': JobType.PART_TIME,
            'part-time': JobType.PART_TIME,
            'contract': JobType.CONTRACT,
            'contractor': JobType.CONTRACT,
            'temporary': JobType.TEMPORARY,
            'temp': JobType.TEMPORARY,
            'internship': JobType.INTERNSHIP,
            'intern': JobType.INTERNSHIP
        }
        
        return type_mapping.get(job_type_str)
    
    def _parse_remote_type(self, row: pd.Series) -> Optional[RemoteType]:
        """Parse remote work type"""
        is_remote = row.get('is_remote')
        
        if is_remote is True:
            return RemoteType.REMOTE
        elif is_remote is False:
            # Check description for hybrid indicators
            description = str(row.get('description', '')).lower()
            if 'hybrid' in description:
                return RemoteType.HYBRID
            else:
                return RemoteType.ON_SITE
        
        return None
    
    def _extract_clearance_info(self, description: str) -> Optional[str]:
        """Extract security clearance requirements from job description"""
        if not description:
            return None
        
        description_lower = description.lower()
        
        # Check for specific clearance levels
        if 'top secret' in description_lower or 'ts/sci' in description_lower:
            return "top_secret"
        elif 'secret clearance' in description_lower or 'secret security' in description_lower:
            return "secret"
        elif 'public trust' in description_lower:
            return "public_trust"
        elif 'clearance' in description_lower:
            return "required"  # Some form of clearance required
        
        return None
    
    def _check_metro_accessibility(self, location: str, description: str) -> Optional[bool]:
        """Check if job location is metro accessible"""
        # DC Metro stations and areas
        metro_keywords = [
            'metro', 'wmata', 'subway', 'rail',
            'dupont', 'foggy bottom', 'downtown dc', 'union station',
            'rosslyn', 'ballston', 'clarendon', 'courthouse',
            'crystal city', 'pentagon', 'national airport',
            'bethesda', 'silver spring', 'rockville'
        ]
        
        combined_text = f"{location} {description}".lower()
        
        # Check if any metro keywords are mentioned
        for keyword in metro_keywords:
            if keyword in combined_text:
                return True
        
        # Check specific DC area locations known to be metro accessible
        metro_areas = [
            'washington dc', 'arlington va', 'alexandria va',
            'bethesda md', 'silver spring md', 'rockville md'
        ]
        
        location_lower = location.lower()
        for area in metro_areas:
            if area in location_lower:
                return True
        
        return None  # Unknown/not specified
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        
        min_interval = 60.0 / self.requests_per_minute  # seconds between requests
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def cleanup(self):
        """Cleanup scraper resources"""
        self.logger.info("✅ JobSpy scraper cleanup completed")


# Quick test function
async def test_jobspy():
    """Test the JobSpy scraper"""
    logging.basicConfig(level=logging.INFO)
    
    scraper = JobSpyScraper()
    
    if not await scraper.initialize():
        print("❌ Failed to initialize JobSpy scraper")
        return
    
    # Create test request
    request = ScrapingRequest(
        keywords="Python Developer",
        location="Washington, DC",
        job_sites=[JobSite.INDEED, JobSite.LINKEDIN],
        max_results=10,
        posted_since_days=7
    )
    
    print(f"\n🔍 Testing JobSpy with: {request.keywords} in {request.location}")
    
    try:
        jobs = await scraper.scrape_jobs(request)
        
        print(f"\n✅ Found {len(jobs)} jobs:\n")
        
        for i, job in enumerate(jobs[:5], 1):
            print(f"{i}. {job.title}")
            print(f"   🏢 {job.company}")
            print(f"   📍 {job.location}")
            print(f"   💰 {job.get_salary_range_string()}")
            print(f"   🔗 {job.job_url}")
            print(f"   📝 {job.get_short_description(150)}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(test_jobspy())
