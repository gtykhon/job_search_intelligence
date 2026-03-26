# Quick Start Guide

## 30-Second Start

```bash
# Single company verification
python verify_company_cli.py "Netflix" "Analytics Engineer"

# Batch processing
python verify_company_cli.py --batch example_companies.txt

# Interactive mode
python verify_company_cli.py --interactive
```

## Import as Module

```python
from company_verification_system import CompanyVerificationSystem

# Initialize
system = CompanyVerificationSystem(
    database_path="/mnt/project/company_research_database.md"
)

# Verify company
result = system.verify_company("Netflix", "Analytics Engineer 5")

# Print report
print(system.generate_report(result))

# Check decision
print(f"Decision: {result.decision_status.value}")
print(f"Time saved: {result.time_saved_minutes} minutes")
```

## Decision Codes

The system returns these decision codes:

- **AUTO_DECLINE**: Company automatically excluded (saves 25+ minutes)
  - Defense contractors
  - Government contractors
  - Glassdoor rating < 3.5
  
- **PROCEED**: Safe to apply (research complete)
  - Culture/WLB scores ≥ 50
  - No defense ties
  - Good Glassdoor ratings

- **USER_DECISION**: Requires manual review
  - Edge cases (cloud platforms with gov divisions)
  - Marginal scores (35-49)
  - Insufficient data

- **DATABASE_HIT**: Found in database (saves 15 minutes)
  - Previous research available
  - Previous decision reused

## CLI Exit Codes

```bash
python verify_company_cli.py "Netflix" "Analytics Engineer"
echo $?  # Check exit code
```

Exit codes:
- `0` = PROCEED (safe to apply)
- `1` = USER_DECISION (review required)
- `2` = AUTO_DECLINE (excluded)

Use in scripts:

```bash
#!/bin/bash
for company in "Netflix" "Lockheed Martin" "Watershed"; do
    if python verify_company_cli.py "$company" "Data Engineer" --format json > /dev/null; then
        echo "✓ $company: PROCEED"
    else
        echo "✗ $company: DECLINED"
    fi
done
```

## Batch File Format

Create `my_companies.txt`:

```
# Companies to research
Netflix, Analytics Engineer 5
Watershed, Senior Data Engineer
Docker, Staff Platform Engineer
Stripe, Staff Engineer

# Lines starting with # are ignored
```

Run batch:

```bash
python verify_company_cli.py --batch my_companies.txt --output ./my_reports/
```

## Output Formats

### Text Report (default)

```bash
python verify_company_cli.py "Netflix" "Analytics Engineer"
```

### JSON Output

```bash
python verify_company_cli.py "Netflix" "Analytics Engineer" --format json
```

```json
{
  "company": "Netflix",
  "position": "Analytics Engineer",
  "decision": "PROCEED",
  "defense_status": "No Defense Ties",
  "glassdoor": {
    "overall_rating": 3.8,
    "culture_values": 3.9,
    "work_life_balance": 3.7
  },
  "scores": {
    "culture_score": 72,
    "culture_rating": "Good",
    "wlb_score": 72,
    "wlb_rating": "Good"
  }
}
```

## Integration Examples

### With jq for JSON processing

```bash
# Extract just the decision
python verify_company_cli.py "Netflix" "Analytics Engineer" --format json | jq -r '.decision'

# Get culture score
python verify_company_cli.py "Netflix" "Analytics Engineer" --format json | jq -r '.scores.culture_score'

# Filter only companies to proceed
for company in Netflix Watershed Docker; do
    decision=$(python verify_company_cli.py "$company" --format json | jq -r '.decision')
    if [ "$decision" == "PROCEED" ]; then
        echo "$company"
    fi
done
```

### As Python Function

```python
def should_apply(company: str, position: str = "") -> bool:
    """Return True if should apply to this company"""
    system = CompanyVerificationSystem()
    result = system.verify_company(company, position)
    return result.decision_status.value == "PROCEED"

# Usage
if should_apply("Netflix", "Analytics Engineer"):
    print("Generate resume and apply!")
else:
    print("Skip this company")
```

### Automated Job Search

```python
from company_verification_system import CompanyVerificationSystem

system = CompanyVerificationSystem()

# List of companies from Indeed/LinkedIn
job_postings = [
    ("Netflix", "Analytics Engineer 5"),
    ("Lockheed Martin", "Data Scientist"),  # Will auto-decline
    ("Watershed", "Senior Data Engineer"),
    ("Amazon", "SDE - EC2"),  # Edge case
]

for company, position in job_postings:
    result = system.verify_company(company, position)
    
    if result.decision_status.value == "AUTO_DECLINE":
        print(f"⏭️  Skipping {company}: {result.decline_reason}")
        print(f"   Time saved: {result.time_saved_minutes} min")
    
    elif result.decision_status.value == "PROCEED":
        print(f"✓ {company}: Proceed with application!")
        if result.scoring_result:
            print(f"   Culture: {result.scoring_result.culture_score}/100")
            print(f"   WLB: {result.scoring_result.wlb_score}/100")
        # TODO: Generate resume for this company
    
    elif result.decision_status.value == "USER_DECISION":
        print(f"⚠️  {company}: Manual review required")
        print(f"   Reason: {result.decline_reason}")
        # TODO: Flag for manual review
```

## Time Savings Calculator

```python
def calculate_savings(num_companies: int, 
                     decline_rate: float = 0.3,
                     database_hit_rate: float = 0.2) -> dict:
    """
    Calculate estimated time savings
    
    Args:
        num_companies: Number of companies to screen
        decline_rate: Expected auto-decline rate (default 30%)
        database_hit_rate: Expected database hit rate (default 20%)
    """
    db_hits = int(num_companies * database_hit_rate)
    auto_declines = int((num_companies - db_hits) * decline_rate)
    full_verifications = num_companies - db_hits - auto_declines
    
    time_saved = (db_hits * 15) + (auto_declines * 25)
    time_invested = full_verifications * 3  # 3 min per verification
    
    return {
        "companies_screened": num_companies,
        "database_hits": db_hits,
        "auto_declined": auto_declines,
        "full_verifications": full_verifications,
        "time_saved_minutes": time_saved,
        "time_invested_minutes": time_invested,
        "net_savings_minutes": time_saved - time_invested,
        "net_savings_hours": (time_saved - time_invested) / 60
    }

# Example: Screening 50 companies
savings = calculate_savings(50)
print(f"Net time saved: {savings['net_savings_hours']:.1f} hours")
```

## Common Use Cases

### Daily Job Search Workflow

```bash
# Morning: Screen new job postings
python verify_company_cli.py "Company Name" "Position" --format json > result.json

# Check if should proceed
decision=$(jq -r '.decision' result.json)

if [ "$decision" == "PROCEED" ]; then
    # Generate resume and cover letter
    echo "Applying to $(jq -r '.company' result.json)"
    # TODO: Call resume generation system
fi
```

### Weekly Batch Review

```bash
# Create weekly.txt with all companies from job boards
# Run batch screening
python verify_company_cli.py --batch weekly.txt --output ./week_of_2025_11_14/

# Review summary
cat ./week_of_2025_11_14/batch_summary.json

# Focus on PROCEED and USER_DECISION companies only
```

### Database Maintenance

```python
# Update database with new research
result = system.verify_company("NewCompany", "Position")

# Save to database (would need to implement)
with open("company_research_database.md", "a") as f:
    f.write(f"\n### **{result.company_name}**\n")
    f.write(system.generate_report(result))
```

## Troubleshooting

### Issue: Database file not found

```bash
# Specify database path
python verify_company_cli.py "Netflix" --database /path/to/company_research_database.md
```

### Issue: No Glassdoor data

The example code returns placeholder Glassdoor data. To get real data:

1. Implement Glassdoor API integration (see README)
2. Or use web scraping (use responsibly, respect robots.txt)
3. Or manually input ratings when prompted

### Issue: Permission denied

```bash
# Make CLI executable
chmod +x verify_company_cli.py

# Or run with python
python verify_company_cli.py "Netflix"
```

## Next Steps

1. **Test with example data**: `python verify_company_cli.py --batch example_companies.txt`
2. **Review output reports**: Check `./reports/` directory
3. **Integrate with job search**: Automate screening of Indeed/LinkedIn results
4. **Customize scoring**: Adjust thresholds in `config.py`
5. **Add API keys**: Enable real-time Glassdoor/web research

## Performance Tips

- Use batch mode for multiple companies (saves startup time)
- Enable database caching to avoid re-research
- Run during off-hours to avoid API rate limits
- Cache Glassdoor results for 7 days to reduce API calls

## Help

```bash
# Show CLI help
python verify_company_cli.py --help

# Interactive mode for experimentation
python verify_company_cli.py --interactive
```
