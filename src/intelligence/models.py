"""
Data models for job scraping with JobSpy integration
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class JobSite(Enum):
    """Supported job sites"""
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    GOOGLE_JOBS = "google_jobs"
    ZIP_RECRUITER = "zip_recruiter"
    HACKER_NEWS = "hackernews"
    WELLFOUND = "wellfound"
    CLIMATEBASE = "climatebase"
    GREENHOUSE = "greenhouse"
    ASHBY = "ashby"
    CLIMATETECHLIST = "climatetechlist"
    LEVELS_FYI = "levels_fyi"
    OTTA = "otta"
    CUSTOM = "custom"


class JobType(Enum):
    """Job employment types"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"


class ExperienceLevel(Enum):
    """Experience level requirements"""
    ENTRY = "entry_level"
    MID = "mid_level"
    SENIOR = "senior_level"
    EXECUTIVE = "executive"
    DIRECTOR = "director"


class RemoteType(Enum):
    """Remote work types"""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"


@dataclass
class ScrapingRequest:
    """Request parameters for job scraping"""
    keywords: str
    location: str = "United States"
    job_sites: List[JobSite] = field(default_factory=lambda: [JobSite.INDEED, JobSite.LINKEDIN])
    radius_miles: int = 50
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    remote_type: Optional[RemoteType] = None
    posted_since_days: Optional[int] = 7
    max_results: int = 50
    
    # DC area specific filters
    clearance_required: Optional[str] = None  # "secret", "top_secret", "public_trust"
    metro_accessible: Optional[bool] = None


@dataclass
class JobListing:
    """A single job listing from any job site"""
    # Basic information
    title: str
    company: str
    location: str
    description: str
    job_url: str
    
    # Additional details
    job_id: Optional[str] = None
    company_url: Optional[str] = None
    job_type: Optional[JobType] = None
    remote_type: Optional[RemoteType] = None
    experience_level: Optional[ExperienceLevel] = None
    
    # Salary information
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    salary_period: str = "yearly"
    
    # Dates
    posted_date: Optional[datetime] = None
    scraped_date: datetime = field(default_factory=datetime.now)
    
    # Source
    source_site: JobSite = JobSite.CUSTOM
    
    # DC area specific
    clearance_required: Optional[str] = None
    metro_accessible: Optional[bool] = None
    
    # Company intelligence
    company_industry: Optional[str] = None
    company_num_employees: Optional[str] = None
    company_staff_count: Optional[int] = None  # Exact headcount from Voyager API
    company_revenue: Optional[str] = None
    company_rating: Optional[float] = None
    company_reviews_count: Optional[int] = None
    company_description: Optional[str] = None

    # Applicant & poster data (Voyager API enrichment)
    applicant_count: Optional[int] = None
    hiring_manager_name: Optional[str] = None
    hiring_manager_title: Optional[str] = None
    hiring_manager_url: Optional[str] = None

    # Exact timestamps from Voyager API (ms epoch)
    listed_at_ms: Optional[int] = None
    original_listed_at_ms: Optional[int] = None

    # Skills and requirements
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)

    # Keyword classification result (populated by gate_0g/gate_0h during screening)
    keyword_classification: Optional[str] = None   # "GREEN" | "YELLOW" | "RED"
    yellow_keyword_matches: List[str] = field(default_factory=list)

    # Metadata
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'job_url': self.job_url,
            'job_id': self.job_id,
            'company_url': self.company_url,
            'job_type': self.job_type.value if self.job_type else None,
            'remote_type': self.remote_type.value if self.remote_type else None,
            'experience_level': self.experience_level.value if self.experience_level else None,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_currency': self.salary_currency,
            'salary_period': self.salary_period,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'scraped_date': self.scraped_date.isoformat(),
            'source_site': self.source_site.value,
            'clearance_required': self.clearance_required,
            'metro_accessible': self.metro_accessible,
            'company_industry': self.company_industry,
            'company_num_employees': self.company_num_employees,
            'company_revenue': self.company_revenue,
            'company_rating': self.company_rating,
            'company_reviews_count': self.company_reviews_count,
            'company_staff_count': self.company_staff_count,
            'applicant_count': self.applicant_count,
            'hiring_manager_name': self.hiring_manager_name,
            'hiring_manager_title': self.hiring_manager_title,
            'hiring_manager_url': self.hiring_manager_url,
            'listed_at_ms': self.listed_at_ms,
            'original_listed_at_ms': self.original_listed_at_ms,
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills
        }
    
    def get_salary_range_string(self) -> str:
        """Get formatted salary range string"""
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,.0f} - ${self.salary_max:,.0f}"
        elif self.salary_min:
            return f"${self.salary_min:,.0f}+"
        elif self.salary_max:
            return f"Up to ${self.salary_max:,.0f}"
        else:
            return "Not specified"
    
    def is_recent(self, days: int = 7) -> bool:
        """Check if job was posted within last N days"""
        if not self.posted_date:
            return False
        
        age = datetime.now() - self.posted_date
        return age.days <= days
    
    def get_short_description(self, max_chars: int = 200) -> str:
        """Get truncated description"""
        if len(self.description) <= max_chars:
            return self.description
        
        truncated = self.description[:max_chars].rsplit(' ', 1)[0]
        return f"{truncated}..."
