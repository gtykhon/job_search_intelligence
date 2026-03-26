"""
Centralized Job Search Configuration — EXAMPLE TEMPLATE
Copy to job_search_config.py and fill in your own values.
job_search_config.py is gitignored (contains personal salary/skill data).
"""

# ==================== CORE SEARCH CRITERIA ====================

SEARCH_TERMS = [
    "Senior Data Engineer",
    "Staff Data Engineer",
    "Senior Backend Engineer Python",
    # Add your target roles here
]

LOCATIONS = [
    "Remote",
    "Remote, USA",
    # Add your preferred locations
]

EXPERIENCE_LEVELS = [
    "senior_level",
    "executive_level",
]

JOB_SITES = ["linkedin", "indeed", "glassdoor", "google"]

# ==================== COMPANY PREFERENCES ====================

PREFERRED_COMPANIES_TIER1 = [
    # Climate Tech, Developer Tools, Healthcare Tech, Fintech, Data Infrastructure
    # e.g. "Stripe", "Databricks", "Anthropic"
]

PREFERRED_COMPANIES_TIER2 = [
    # Established product companies
]

PREFERRED_COMPANIES_TIER3 = [
    # High-growth startups (Series B+)
]

IGNORED_COMPANIES = [
    # Government contractors, consulting firms, staffing agencies
    # e.g. "Booz Allen Hamilton", "Deloitte", "Robert Half"
]

# ==================== SALARY REQUIREMENTS ====================
# Set your own targets — do not commit real values

MIN_SALARY = {
    "default": 0,
    "senior": 0,
    "staff": 0,
    "principal": 0,
    "manager": 0,
    "lead": 0,
}

PREFERRED_SALARY_RANGES = {
    "minimum_acceptable": 0,
    "target_range_min": 0,
    "target_range_max": 0,
    "stretch_target": 0,
    "dream_salary": 0,
}

# ==================== SKILLS ====================

CORE_SKILLS = [
    # Your primary skills with production experience
    "Python", "SQL", "Git",
]

SECONDARY_SKILLS = [
    # Skills with some exposure but not primary
]

EXCLUDED_SKILLS = [
    # Technologies you're deliberately avoiding
]

TOOL_GAPS_TO_ACKNOWLEDGE = [
    # Modern stack tools you don't have hands-on production experience with
]

AVOIDED_SKILLS = []

# ==================== WORK PREFERENCES ====================

WORK_ARRANGEMENTS = ["remote", "hybrid"]
EMPLOYMENT_TYPES = ["full_time"]

# ==================== COMPANY SCREENING ====================

COMPANY_QUALITY_GATES = {
    "glassdoor_minimum": 3.5,
    "layoffs_exclusion_months": 18,
    "minimum_employees": 50,
    "maximum_employees": 10000,
    "required_benefits": ["Health", "401k", "Remote Work"],
}

PREFERRED_INDUSTRIES = [
    "Climate Tech", "Healthcare Technology", "Fintech",
    "Developer Tools", "Data Infrastructure", "SaaS",
]

AVOIDED_INDUSTRIES = [
    "Government", "Defense", "Consulting Services", "Staffing Services",
]

# ==================== SEARCH BEHAVIOR ====================

JOBS_PER_SEARCH = 25
MAX_JOB_AGE_DAYS = 7

JOBSPY_CONFIG = {
    "results_wanted": 20,
    "hours_old": 168,
    "distance": None,
    "country_indeed": "USA",
    "site_name": ["indeed", "linkedin", "glassdoor", "google"],
    "output_name": "daily_jobs",
    "verbose": 2,
    "is_remote": True,
    "job_type": "fulltime",
    "linkedin_fetch_description": True,
    "linkedin_company_link": True,
}

JOBSPY_SEARCH_QUERIES = [
    {"search_term": "Senior Data Engineer", "location": "Remote"},
    # Add your search queries here
]

SEARCH_FREQUENCY = {
    "opportunity_detection": "daily",
    "company_page_crawl": "weekly",
    "quick_scan": "never",
}

# ==================== SCORING ====================

SCORING_WEIGHTS = {
    "company_tier": 0.35,
    "salary_match": 0.25,
    "skills_authenticity": 0.20,
    "title_level": 0.10,
    "industry_alignment": 0.10,
}

MIN_OPPORTUNITY_SCORE = 0.70

ALERT_THRESHOLDS = {
    "high_priority_job": 0.85,
    "tier1_company": True,
    "salary_in_target": True,
}

# ==================== BACKWARDS-COMPATIBILITY HELPERS ====================

PREFERRED_COMPANIES = (
    PREFERRED_COMPANIES_TIER1 + PREFERRED_COMPANIES_TIER2 + PREFERRED_COMPANIES_TIER3
)
PREFERRED_SKILLS = CORE_SKILLS + SECONDARY_SKILLS

SCORING_WEIGHTS_LEGACY = {
    "company_preference": SCORING_WEIGHTS["company_tier"],
    "salary_match": SCORING_WEIGHTS["salary_match"],
    "skills_match": SCORING_WEIGHTS["skills_authenticity"],
    "title_relevance": SCORING_WEIGHTS["title_level"],
    "location_preference": SCORING_WEIGHTS["industry_alignment"],
}


def is_product_company(company_name, company_description=""):
    product_indicators = ["builds", "develops own", "product company", "saas", "platform"]
    contractor_indicators = ["consulting", "staffing", "solutions provider", "services", "contractor"]
    description_lower = company_description.lower()
    product_score = sum(1 for i in product_indicators if i in description_lower)
    contractor_score = sum(1 for i in contractor_indicators if i in description_lower)
    return product_score > contractor_score


def check_company_tier(company_name):
    if not company_name:
        return 0
    company_lower = company_name.lower()
    if any(t1.lower() in company_lower for t1 in PREFERRED_COMPANIES_TIER1):
        return 1
    if any(t2.lower() in company_lower for t2 in PREFERRED_COMPANIES_TIER2):
        return 2
    if any(t3.lower() in company_lower for t3 in PREFERRED_COMPANIES_TIER3):
        return 3
    return 0


def is_excluded_company(company_name):
    if not company_name:
        return False
    company_lower = company_name.lower()
    return any(e.lower() in company_lower for e in IGNORED_COMPANIES)


def is_preferred_company(company_name):
    return check_company_tier(company_name) > 0


def is_ignored_company(company_name):
    return is_excluded_company(company_name)


def calculate_salary_score(salary_min, salary_max, role_level="default"):
    if salary_min is None and salary_max is None:
        return 0.5
    min_required = MIN_SALARY.get(role_level, MIN_SALARY["default"])
    salary_to_check = salary_max if salary_max is not None else salary_min
    if salary_to_check is None:
        return 0.5
    if salary_to_check >= PREFERRED_SALARY_RANGES["dream_salary"] > 0:
        return 1.0
    if salary_to_check >= PREFERRED_SALARY_RANGES["stretch_target"] > 0:
        return 0.9
    if salary_to_check >= PREFERRED_SALARY_RANGES["target_range_max"] > 0:
        return 0.8
    if salary_to_check >= PREFERRED_SALARY_RANGES["target_range_min"] > 0:
        return 0.7
    if min_required > 0 and salary_to_check >= min_required:
        return 0.6
    return 0.5


def calculate_skills_authenticity_score(job_requirements):
    requirements_lower = job_requirements.lower()
    core_matches = sum(1 for s in CORE_SKILLS if s.lower() in requirements_lower)
    secondary_matches = sum(0.5 for s in SECONDARY_SKILLS if s.lower() in requirements_lower)
    gap_penalties = sum(
        -0.3 for g in TOOL_GAPS_TO_ACKNOWLEDGE
        if g.lower() in requirements_lower and "required" in requirements_lower
    )
    exclusion_penalties = sum(
        -0.5 for e in EXCLUDED_SKILLS
        if e.lower() in requirements_lower and "required" in requirements_lower
    )
    total = (core_matches + secondary_matches + gap_penalties + exclusion_penalties) / 10
    return max(0.0, min(1.0, total))


def meets_quality_gates(company_data):
    if company_data.get("glassdoor_rating", 0) < COMPANY_QUALITY_GATES["glassdoor_minimum"]:
        return False, "Glassdoor rating below minimum"
    if company_data.get("recent_layoffs", False):
        return False, "Layoffs within exclusion window"
    if is_excluded_company(company_data.get("name", "")):
        return False, "Excluded company"
    industry = company_data.get("industry")
    if industry in AVOIDED_INDUSTRIES:
        return False, f"Avoided industry: {industry}"
    if not is_product_company(company_data.get("name", ""), company_data.get("description", "")):
        return False, "Consulting/staffing firm detected"
    return True, "Passed all quality gates"


def get_search_terms_for_level(level="senior"):
    base_terms = SEARCH_TERMS.copy()
    level_lower = (level or "").lower()
    if level_lower == "senior":
        return [t for t in base_terms if "Senior" in t or "Staff" in t]
    if level_lower == "principal":
        return [t for t in base_terms if "Principal" in t]
    if level_lower == "manager":
        return [t for t in base_terms if "Manager" in t or "Lead" in t]
    return base_terms
