"""
Configuration for Company Verification System

Copy this file to config.py and fill in your API keys
"""

# API Keys (replace with your actual keys)
WEB_SEARCH_API_KEY = None  # For web research (optional)
GLASSDOOR_API_KEY = None   # For Glassdoor scraping (optional)

# File paths
COMPANY_DATABASE_PATH = "/mnt/project/company_research_database.md"
DEFENSE_EXCLUSION_PATH = "/mnt/project/defense_exclusion_criteria_framework.md"

# Scoring thresholds
GLASSDOOR_MIN_RATING = 3.5  # Auto-decline if below this
CULTURE_PROCEED_THRESHOLD = 50  # Proceed if culture score >= this
WLB_PROCEED_THRESHOLD = 50      # Proceed if WLB score >= this

# Review count thresholds
MIN_REVIEWS_FOR_CONFIDENCE = 20
HIGH_CONFIDENCE_REVIEWS = 50

# Defense screening
AUTO_DECLINE_DEFENSE_CONTRACTORS = True
AUTO_DECLINE_GOVERNMENT_CONTRACTORS = True  # User preference: no government work

# Time saving estimates (minutes)
TIME_SAVED_DATABASE_HIT = 15
TIME_SAVED_AUTO_DECLINE = 25
TIME_SAVED_FULL_RESEARCH = 40

# Known contractors (can be extended)
ADDITIONAL_DEFENSE_CONTRACTORS = [
    # Add any additional known defense contractors here
]

ADDITIONAL_GOVERNMENT_CONTRACTORS = [
    # Add any additional known government contractors here
]

# Edge case companies (require user decision)
EDGE_CASE_COMPANIES = {
    'amazon': 'AWS GovCloud (~5% revenue)',
    'microsoft': 'Azure Government Cloud',
    'google': 'Google Cloud for Government',
    'oracle': 'Oracle Cloud for Government'
}

# Output settings
GENERATE_DETAILED_REPORTS = True
SAVE_REPORTS_TO_FILE = True
REPORTS_DIRECTORY = "./company_reports/"

# Web scraping settings (if implementing)
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (compatible; CompanyResearchBot/1.0)"

# Glassdoor scraping settings
GLASSDOOR_BASE_URL = "https://www.glassdoor.com"
CACHE_GLASSDOOR_RESULTS = True
CACHE_EXPIRY_DAYS = 7

# Logging
ENABLE_LOGGING = True
LOG_FILE = "./company_verification.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
