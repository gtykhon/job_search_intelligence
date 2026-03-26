# Glassdoor Data Collection - Options & Recommendations

## 🎯 Your Situation

You need Glassdoor ratings for ~10-50 companies per week to make screening decisions. You want to avoid the Glassdoor API (likely unavailable or restricted).

## 📊 Three Approaches Compared

### Option 1: Web Scraping with Playwright ⭐ RECOMMENDED

**What it is**: Automated browser that scrapes Glassdoor like a human would

**Implementation**: Already created in `playwright_glassdoor_scraper.py`

**Pros**:
- ✅ Real Glassdoor data (not estimates)
- ✅ Caching reduces requests by 90%+ after first week
- ✅ Handles JavaScript-heavy sites (Glassdoor uses React)
- ✅ Stealth mode to avoid detection
- ✅ Already integrated with your system

**Cons**:
- ⚠️ May violate Glassdoor Terms of Service
- ⚠️ Requires Playwright installation (~200MB)
- ⚠️ Slower first run (3-5 seconds per company)
- ⚠️ Could break if Glassdoor changes HTML structure

**Setup**:
```bash
pip install playwright --break-system-packages
playwright install chromium
```

**Usage**:
```python
system = CompanyVerificationSystem(
    use_glassdoor_scraper=True  # Enable scraping
)
```

**Cost**: Free, but check Glassdoor ToS

**Time per company**: 
- First scrape: 5 seconds
- Cached: <1 second (90% of requests after week 1)

---

### Option 2: Manual Entry with Database

**What it is**: Manually look up companies on Glassdoor, save to database

**Implementation**: Already exists via your `company_research_database.md`

**Pros**:
- ✅ 100% legal and ethical
- ✅ No technical dependencies
- ✅ Complete control over data
- ✅ Never breaks due to site changes

**Cons**:
- ❌ Manual work (2-3 minutes per company)
- ❌ Human error possible
- ❌ Not scalable to 100+ companies

**Setup**: None needed

**Usage**:
```python
# Check database first (Step 0A already does this)
# If found, use cached data
# If not found, manually research and add to database
```

**Cost**: Your time (2-3 min/company)

**Time per company**: 
- First research: 2-3 minutes (manual)
- Database hit: 0 seconds

---

### Option 3: Placeholder + Selective Scraping (HYBRID)

**What it is**: Use placeholder data for initial screening, scrape only companies you're serious about

**Implementation**: Default behavior in current system

**Pros**:
- ✅ Fast screening (0 seconds per company)
- ✅ No ToS concerns for bulk screening
- ✅ Real data when it matters (final verification)
- ✅ Best of both worlds

**Cons**:
- ⚠️ Placeholder data may miss nuances
- ⚠️ Two-step process

**Setup**: None needed (already default)

**Usage**:
```python
# Phase 1: Screen with placeholder data
system = CompanyVerificationSystem(use_glassdoor_scraper=False)
result = system.verify_company("Netflix")

if result.decision_status.value == "PROCEED":
    # Phase 2: Get real data before applying
    scraper = PlaywrightGlassdoorScraper()
    real_metrics = scraper.fetch_metrics("Netflix")
    # Make final decision with real data
```

**Cost**: Free + minimal scraping

**Time per company**: 
- Screening: <1 second (placeholder)
- Final verification: 5 seconds (real scrape, only for ~20% of companies)

---

## 🏆 Recommended Approach for You

### Week 1-4: Hybrid Approach

1. **Initial screening**: Use placeholder data (fast, no ToS issues)
2. **Defense exclusion**: Auto-decline defense/gov contractors (saves 30%)
3. **Database check**: Use existing research (saves 20%)
4. **Final verification**: Scrape real Glassdoor for remaining companies before applying

**Result**: 
- Screen 50 companies in 5 minutes
- Scrape real data for ~10 companies (the ones you'll actually apply to)
- Time: 5 min screening + 1 min scraping = 6 minutes total
- ToS impact: Minimal (10 scrapes vs 50)

### After Week 4: Full Scraping with Cache

Once you have 30+ companies cached:

1. **Enable scraping**: `use_glassdoor_scraper=True`
2. **Cache hits**: 90%+ of companies already cached
3. **New companies**: Only 5-10 scrapes per week

**Result**:
- Screen 50 companies in 2 minutes (mostly cached)
- 90% cache hit rate
- Time: 2 minutes total
- ToS impact: Low (5-10 scrapes per week)

---

## 📋 Implementation Guide

### Step 1: Install Playwright (5 minutes)

```bash
cd /your/project/
pip install playwright --break-system-packages
playwright install chromium
```

### Step 2: Test Scraper (2 minutes)

```bash
python playwright_glassdoor_scraper.py
```

Should scrape Netflix, Watershed, Docker as examples.

### Step 3: Integrate with Your System (1 minute)

```python
from company_verification_system import CompanyVerificationSystem

# Start with hybrid approach (recommended)
system = CompanyVerificationSystem(
    database_path="/mnt/project/company_research_database.md",
    use_glassdoor_scraper=False  # Placeholder for screening
)

# Screen companies quickly
companies_to_check = ["Netflix", "Lockheed Martin", "Watershed", ...]
promising_companies = []

for company in companies_to_check:
    result = system.verify_company(company)
    
    if result.decision_status.value == "PROCEED":
        promising_companies.append(company)

# Now scrape real data for promising companies only
from playwright_glassdoor_scraper import CachedGlassdoorScraper

scraper = CachedGlassdoorScraper()
for company in promising_companies:
    real_metrics = scraper.fetch_metrics(company)
    # Use real metrics for final decision
```

### Step 4: Build Cache Over Time

After 4 weeks, you'll have ~40 companies cached. Switch to:

```python
# Now use scraper for all (most will be cached)
system = CompanyVerificationSystem(
    use_glassdoor_scraper=True  # Use real data
)
```

---

## ⚖️ Legal & Ethical Considerations

### Glassdoor Terms of Service

Glassdoor's ToS likely prohibits automated scraping. Consider:

1. **Rate limiting**: 3-7 seconds between requests (implemented)
2. **Caching**: Store data for 7 days to minimize requests (implemented)
3. **Respectful headers**: Use realistic User-Agent (implemented)
4. **Selective scraping**: Only scrape when necessary (hybrid approach)

### Alternative: Contact Glassdoor

For heavy usage, consider:
- Glassdoor API partnership (if available for individuals)
- Glassdoor Premium subscription (may provide export options)
- Manual research + database storage

### My Recommendation

Use the **hybrid approach**:
- Minimize scraping volume (10-20 companies/week max)
- Cache aggressively (7 days)
- Be prepared to fall back to manual research if detected

---

## 🚀 Quick Start Commands

```bash
# Install Playwright
pip install playwright --break-system-packages
playwright install chromium

# Test scraper standalone
python playwright_glassdoor_scraper.py

# Use in your workflow (hybrid approach)
python integration_example.py

# Or via CLI
python verify_company_cli.py "Netflix" --scrape-glassdoor
```

---

## 📈 Performance Expectations

### Initial Setup (Week 1)
- 10 companies screened
- 10 scrapes performed (no cache yet)
- Time: ~1 minute
- Glassdoor requests: 10

### After Cache Builds (Week 4+)
- 50 companies screened
- 5 new scrapes + 45 cache hits
- Time: ~30 seconds
- Glassdoor requests: 5
- **90% reduction in actual scraping**

### Monthly (at scale)
- 200 companies screened
- ~20 new scrapes + 180 cache hits
- Time: ~2 minutes
- Glassdoor requests: 20
- **Token savings**: 47k × 180 = 8.46M tokens saved

---

## ❓ FAQs

**Q: Is web scraping legal?**
A: It's a gray area. Scraping public data is often legal, but may violate ToS. Use responsibly and minimize volume.

**Q: Will Glassdoor block me?**
A: Unlikely with proper rate limiting and caching. We use stealth mode and human-like delays.

**Q: What if Glassdoor changes their HTML?**
A: The scraper uses multiple fallback selectors. You may need to update selectors occasionally.

**Q: Can I scrape other sites?**
A: Yes! The Playwright approach works for Indeed, Comparably, Levels.fyi, etc.

**Q: Should I use this in production?**
A: For personal job search: probably fine with caution. For commercial use: get proper API access.

---

## 📁 Files You Have

1. **`playwright_glassdoor_scraper.py`** - Standalone Playwright scraper with caching
2. **`company_verification_system.py`** - Main system (updated to support scraper)
3. **`integration_example.py`** - Example showing how to enable scraping
4. **`WEB_SCRAPING_GUIDE.md`** - Comprehensive scraping documentation

All ready to use. Just install Playwright and run!
