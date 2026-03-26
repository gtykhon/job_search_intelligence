"""
Integration Example: Using Playwright Scraper with Company Verification System

This demonstrates how to enable real Glassdoor web scraping in your workflow.
"""

from company_verification_system import CompanyVerificationSystem

# Example 1: Enable Playwright scraping
print("="*70)
print("Example 1: Company Verification with Real Glassdoor Scraping")
print("="*70 + "\n")

# Initialize system with Playwright scraping enabled
system = CompanyVerificationSystem(
    database_path="/mnt/project/company_research_database.md",
    use_glassdoor_scraper=True,  # Enable Playwright web scraping
    glassdoor_cache_dir="./glassdoor_cache/"  # Cache for 7 days
)

# Verify a company (will scrape real Glassdoor data)
result = system.verify_company("Netflix", "Analytics Engineer 5")

# Print report
print(system.generate_report(result))

print("\n" + "="*70)
print("Example 2: Batch Processing with Scraping")
print("="*70 + "\n")

# Process multiple companies
companies = [
    ("Netflix", "Analytics Engineer"),
    ("Watershed", "Senior Data Engineer"),
    ("Docker", "Staff Platform Engineer")
]

for company, position in companies:
    print(f"\n{'─'*70}")
    print(f"Processing: {company}")
    print('─'*70)
    
    result = system.verify_company(company, position)
    
    if result.decision_status.value == "PROCEED":
        print(f"✓ {company}: PROCEED")
        if result.scoring_result:
            print(f"  Culture: {result.scoring_result.culture_score}/100")
            print(f"  WLB: {result.scoring_result.wlb_score}/100")
    elif result.decision_status.value == "AUTO_DECLINE":
        print(f"✗ {company}: AUTO-DECLINE")
        print(f"  Reason: {result.decline_reason}")
        print(f"  Time saved: {result.time_saved_minutes} minutes")
    else:
        print(f"⚠ {company}: USER DECISION REQUIRED")

# Show cache statistics (if scraper was used)
if hasattr(system.glassdoor_scraper, 'scraper') and system.glassdoor_scraper.scraper:
    print("\n" + "="*70)
    print("Glassdoor Scraping Statistics")
    print("="*70)
    stats = system.glassdoor_scraper.scraper.get_cache_stats()
    print(f"Cache Hits: {stats['cache_hits']}")
    print(f"Cache Misses: {stats['cache_misses']}")
    print(f"Hit Rate: {stats['hit_rate_percent']}%")
    print(f"\nCache hits save ~30 seconds per company!")

print("\n" + "="*70)
print("Example 3: Using Without Scraping (Placeholder Data)")
print("="*70 + "\n")

# Initialize without scraping (uses placeholder data)
system_no_scraping = CompanyVerificationSystem(
    database_path="/mnt/project/company_research_database.md",
    use_glassdoor_scraper=False  # Placeholder data only
)

result = system_no_scraping.verify_company("Test Company", "Engineer")
print(f"Decision: {result.decision_status.value}")
print("(Used placeholder Glassdoor data)")

print("\n" + "="*70)
print("Setup Instructions")
print("="*70)
print("""
To enable real Glassdoor scraping:

1. Install Playwright:
   pip install playwright --break-system-packages
   playwright install chromium

2. Use in your code:
   system = CompanyVerificationSystem(
       database_path="/mnt/project/company_research_database.md",
       use_glassdoor_scraper=True
   )

3. First run will scrape (slow), subsequent runs use cache (fast)

4. Cache expires after 7 days - configurable in code

Benefits:
- 90%+ reduction in scraping after first run (caching)
- Real Glassdoor data instead of estimates
- Automatic rate limiting and stealth mode
- Error handling and fallbacks

Considerations:
- Respect Glassdoor's Terms of Service
- Use rate limiting (3-7 seconds between requests)
- Cache aggressively to minimize requests
- Consider using placeholder data for testing
""")
