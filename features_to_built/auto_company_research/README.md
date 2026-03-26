# Company Verification System

Automates the company research and screening workflow from Claude Projects, saving 15-40 minutes per company by systematically checking databases, screening for defense/government ties, verifying Glassdoor ratings, and calculating culture/WLB scores.

## Features

- **Step 0A: Database Check** - Searches existing company research database to avoid duplicate work
- **Step 0B: Defense Exclusion** - Screens for defense contractors and government work
- **Step 1: Web Research** - Gathers company intelligence from multiple sources
- **Step 2: Glassdoor Verification** - Fetches ratings, reviews, and metrics
- **Step 3: Scoring System** - Calculates culture and work-life balance scores (0-100)
- **Step 4: Decision Framework** - Applies systematic decision criteria

## Workflow

```
Input: Company Name + Position
    ↓
Step 0A: Database Check
    ├─ Found + DECLINED → Stop (15 min saved)
    ├─ Found + APPROVED → Use existing data
    └─ Not found → Continue
    ↓
Step 0B: Defense Screening
    ├─ Known Defense Contractor → AUTO-DECLINE (25 min saved)
    ├─ Edge Case → USER DECISION (present evidence)
    └─ Clear → PROCEED
    ↓
Step 2: Glassdoor Verification
    ├─ Fetch ratings (Overall, Culture, WLB, Leadership)
    └─ Extract review count and CEO approval
    ↓
Step 3: Scoring
    ├─ Culture Score (0-100)
    ├─ WLB Score (0-100)
    └─ Risk Assessment
    ↓
Step 4: Decision
    ├─ Score ≥70 → PROCEED (high confidence)
    ├─ Score 50-69 → PROCEED (moderate confidence)
    ├─ Score 35-49 → USER DECISION (proceed with caution)
    └─ Score <35 → USER DECISION (consider avoiding)
    ↓
Output: CompanyResearchResult with full report
```

## Installation

```bash
# Clone or copy the files
cp company_verification_system.py /your/project/path/
cp config_template.py config.py

# Install dependencies (if using web scraping)
pip install requests beautifulsoup4 lxml --break-system-packages

# Configure API keys in config.py (optional)
nano config.py
```

## Basic Usage

```python
from company_verification_system import CompanyVerificationSystem

# Initialize system
system = CompanyVerificationSystem(
    database_path="/mnt/project/company_research_database.md"
)

# Verify a company
result = system.verify_company(
    company_name="Netflix",
    position="Analytics Engineer 5"
)

# Generate report
report = system.generate_report(result)
print(report)

# Check decision
if result.decision_status.value == "AUTO_DECLINE":
    print(f"Company declined: {result.decline_reason}")
    print(f"Time saved: {result.time_saved_minutes} minutes")
elif result.decision_status.value == "PROCEED":
    print("Proceed with application!")
    print(f"Culture Score: {result.scoring_result.culture_score}/100")
    print(f"WLB Score: {result.scoring_result.wlb_score}/100")
```

## Advanced Usage

### Custom Scoring Thresholds

```python
from company_verification_system import CompanyScorer

scorer = CompanyScorer()

# Customize decision thresholds
def custom_decision(culture_score, wlb_score):
    avg = (culture_score + wlb_score) / 2
    
    if avg >= 75:  # Higher bar
        return "PROCEED"
    elif avg >= 60:
        return "USER_DECISION"
    else:
        return "AUTO_DECLINE"
```

### Batch Processing

```python
companies = [
    ("Netflix", "Analytics Engineer"),
    ("Watershed", "Senior Data Engineer"),
    ("Docker", "Staff Platform Engineer")
]

results = []
for company, position in companies:
    result = system.verify_company(company, position)
    results.append(result)
    
    # Save report
    report = system.generate_report(result)
    with open(f"reports/{company.replace(' ', '_')}.txt", 'w') as f:
        f.write(report)

# Summary statistics
auto_declined = sum(1 for r in results if r.decision_status.value == "AUTO_DECLINE")
proceed = sum(1 for r in results if r.decision_status.value == "PROCEED")
total_time_saved = sum(r.time_saved_minutes for r in results)

print(f"\nBatch Summary:")
print(f"  Companies screened: {len(results)}")
print(f"  Auto-declined: {auto_declined}")
print(f"  Proceed: {proceed}")
print(f"  Total time saved: {total_time_saved} minutes")
```

### Integration with Web APIs

To enable full web research capabilities, implement these integrations:

#### 1. Glassdoor API Integration

```python
class GlassdoorScraper:
    def fetch_metrics(self, company_name: str) -> Optional[GlassdoorMetrics]:
        # Option 1: Official Glassdoor API (if available)
        response = requests.get(
            f"https://api.glassdoor.com/companies/{company_name}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # Option 2: Web scraping (use responsibly)
        url = f"https://www.glassdoor.com/Overview/Working-at-{company_name}.htm"
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse ratings from HTML
        overall_rating = float(soup.select_one('.rating').text)
        # ... parse other metrics
        
        return GlassdoorMetrics(
            overall_rating=overall_rating,
            # ... other fields
        )
```

#### 2. Defense Contract Research (USASpending.gov)

```python
def _web_research_defense(self, company_name: str) -> List[str]:
    evidence = []
    
    # Query USASpending.gov API
    api_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    payload = {
        "filters": {
            "keywords": [company_name],
            "award_type_codes": ["A", "B", "C", "D"]  # Contracts
        }
    }
    
    response = requests.post(api_url, json=payload)
    data = response.json()
    
    if data.get('results'):
        total_contracts = len(data['results'])
        defense_contracts = [r for r in data['results'] 
                           if 'defense' in r.get('awarding_agency', '').lower()]
        
        if defense_contracts:
            evidence.append(f"Found {len(defense_contracts)} defense contracts")
            evidence.append(f"Total government contracts: {total_contracts}")
    
    return evidence
```

#### 3. Company News Search

```python
def search_company_news(self, company_name: str, keywords: List[str]) -> List[str]:
    """Search for company news with specific keywords"""
    news = []
    
    # Use news API (e.g., NewsAPI, Bing News)
    query = f"{company_name} {' OR '.join(keywords)}"
    response = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "apiKey": self.news_api_key,
            "sortBy": "relevancy",
            "pageSize": 5
        }
    )
    
    articles = response.json().get('articles', [])
    for article in articles:
        news.append(f"{article['title']} - {article['source']['name']}")
    
    return news
```

## Scoring Methodology

### Culture Score (0-100)

Based on Glassdoor overall rating:

- **80-100 (Excellent)**: 4.5+ stars, 50+ reviews, strong leadership
- **65-79 (Good)**: 3.8-4.4 stars, 20+ reviews, positive feedback
- **50-64 (Average)**: 3.0-3.7 stars, mixed reviews
- **35-49 (Below Average)**: 2.5-2.9 stars, negative trends
- **0-34 (Poor)**: <2.5 stars, toxic indicators

Adjustments:
- Review count bonus: +5 for 50+ reviews, -5 for <20 reviews
- Leadership bonus: +5 for 80%+ CEO approval, -5 for <65%

### Work-Life Balance Score (0-100)

Based on Glassdoor WLB rating:

- **80-100 (Excellent)**: 4.5+ WLB stars
- **65-79 (Good)**: 3.8-4.4 WLB stars
- **50-64 (Average)**: 3.0-3.7 WLB stars
- **35-49 (Below Average)**: 2.5-2.9 WLB stars
- **0-34 (Poor)**: <2.5 WLB stars

### Risk Assessment

Combined culture + WLB score:

- **Low Risk**: Average score ≥70, no layoffs
- **Moderate Risk**: Average score 50-69, stable company
- **Moderate-High Risk**: Average score 35-49 OR recent layoffs
- **High Risk**: Average score <35 OR layoffs + poor culture

## Decision Framework

```
IF Glassdoor < 3.5 → AUTO_DECLINE
ELSE IF Known defense contractor → AUTO_DECLINE
ELSE IF Known government contractor → AUTO_DECLINE
ELSE IF Edge case defense → USER_DECISION
ELSE IF Average score ≥ 50 → PROCEED
ELSE → USER_DECISION
```

## Defense Screening Rules

### Auto-Decline Categories

1. **Direct Defense Contractors**
   - Lockheed Martin, Northrop Grumman, Raytheon, Boeing Defense
   - L3Harris, BAE Systems, General Dynamics
   - Leidos, SAIC, CACI, Booz Allen Hamilton

2. **Government Contractors**
   - Deloitte Federal, Accenture Federal, PwC Federal
   - Maximus, GDIT, CGI Federal
   - Any company with "Federal Services" division

3. **Special Cases**
   - Palantir Technologies (ethical concerns)

### Edge Cases (User Decision Required)

- **Cloud Platforms**: AWS, Azure, Google Cloud (if <20% government revenue)
- **Dual-Use Technology**: AI/ML, cybersecurity (depends on role specificity)
- **Platform Providers**: Software used incidentally by government

## Extending the System

### Adding Custom Exclusion Rules

```python
class CustomDefenseScreener(DefenseScreener):
    def screen_company(self, company_name: str) -> Tuple[DefenseStatus, DecisionStatus, List[str]]:
        # Add custom logic
        company_lower = company_name.lower()
        
        # Example: Exclude companies with "consulting" in name
        if 'consulting' in company_lower:
            return (
                DefenseStatus.GOVERNMENT_CONTRACTOR,
                DecisionStatus.AUTO_DECLINE,
                ["Consulting firm - automatic exclusion"]
            )
        
        # Fall back to default screening
        return super().screen_company(company_name)
```

### Custom Scoring Criteria

```python
class CustomScorer(CompanyScorer):
    def calculate_culture_score(self, metrics: GlassdoorMetrics) -> Tuple[int, str]:
        base_score, category = super().calculate_culture_score(metrics)
        
        # Add custom adjustments
        if metrics.total_reviews < 10:
            base_score -= 15  # Penalize low review count more
        
        if metrics.recommend_friend < 50:
            base_score -= 10  # Penalize low recommendation rate
        
        return max(0, base_score), category
```

### Database Integration

```python
import sqlite3

class DatabaseBackedChecker(DatabaseChecker):
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                name TEXT PRIMARY KEY,
                status TEXT,
                culture_score INTEGER,
                wlb_score INTEGER,
                research_date TEXT,
                decline_reason TEXT
            )
        ''')
    
    def check_company(self, company_name: str) -> Tuple[bool, Optional[Dict]]:
        cursor = self.conn.execute(
            'SELECT * FROM companies WHERE name = ?',
            (company_name,)
        )
        row = cursor.fetchone()
        
        if row:
            return True, {
                'found': True,
                'status': row[1],
                'culture_score': row[2],
                'wlb_score': row[3],
                'research_date': row[4],
                'decline_reason': row[5]
            }
        return False, None
```

## Output Examples

### Example 1: Auto-Decline (Defense Contractor)

```
==============================================================
COMPANY VERIFICATION REPORT
==============================================================

Company: Lockheed Martin
Position: Software Engineer
Research Date: 2025-11-14
Final Decision: AUTO_DECLINE

==============================================================
DEFENSE SCREENING
==============================================================

Defense Status: Direct Defense Contractor

Evidence:
  1. Known defense contractor: Lockheed Martin

==============================================================
DECLINE REASON
==============================================================

Defense/Government contractor: Direct Defense Contractor

==============================================================
EFFICIENCY METRICS
==============================================================

Time Saved: ~25 minutes
```

### Example 2: Proceed (Good Culture)

```
==============================================================
COMPANY VERIFICATION REPORT
==============================================================

Company: Netflix
Position: Analytics Engineer 5
Research Date: 2025-11-14
Final Decision: PROCEED

==============================================================
GLASSDOOR METRICS
==============================================================

Overall Rating: 3.8/5
Culture & Values: 3.9/5
Work-Life Balance: 3.7/5
Career Opportunities: 3.5/5
Senior Leadership: 3.6/5
Recommend to Friend: 68.0%
CEO Approval: 75.0%
Total Reviews: 150

==============================================================
SCORING ANALYSIS
==============================================================

Culture Score: 72/100 (Good)
Work-Life Balance Score: 72/100 (Good)
Risk Level: LOW
```

## Performance Metrics

Time savings per company:

- **Database hit (DECLINED)**: 15 minutes saved
- **Auto-decline (defense)**: 25 minutes saved
- **Auto-decline (Glassdoor < 3.5)**: 30 minutes saved
- **Full research avoided**: 40 minutes saved

For 10 companies screened:
- Typical: 3 database hits + 2 auto-declines + 5 full verifications
- Time saved: (3×15) + (2×25) = 95 minutes
- Time invested: 5×3 = 15 minutes (verification only)
- Net savings: 80 minutes

## Integration with Claude Projects

This system translates the Claude Projects workflow into Python code. To maintain consistency:

1. **Update `company_research_database.md`** with new research
2. **Sync defense contractor lists** with `defense_exclusion_criteria_framework.md`
3. **Use same scoring criteria** as documented in project frameworks
4. **Generate reports** in same format as Claude outputs

## API Rate Limits & Caching

To avoid hitting API rate limits:

```python
import time
from functools import lru_cache

class CachedGlassdoorScraper(GlassdoorScraper):
    @lru_cache(maxsize=100)
    def fetch_metrics(self, company_name: str) -> Optional[GlassdoorMetrics]:
        # Add rate limiting
        time.sleep(1)  # 1 second between requests
        
        return super().fetch_metrics(company_name)
```

## Logging

Enable detailed logging for debugging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('company_verification.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Verifying company: {company_name}")
```

## Error Handling

The system includes robust error handling:

- **Missing database file**: Falls through to web research
- **API failures**: Returns partial results with warnings
- **Invalid company names**: Returns USER_DECISION for manual review
- **Network timeouts**: Retries with exponential backoff

## Contributing

To extend this system:

1. Add new screening rules in `DefenseScreener`
2. Enhance scoring in `CompanyScorer`
3. Integrate additional data sources (LinkedIn, Crunchbase, etc.)
4. Add ML-based classification for edge cases
5. Create web interface for non-technical users

## License

This is based on the Claude Projects automation framework documented in project knowledge. Adapt and extend as needed for your job search workflow.

## Support

For questions or issues:
- Review project documentation in `/mnt/project/`
- Check `QUALITY_GATES_UNIVERSAL.md` for validation protocols
- Reference `company_research_database.md` for examples
