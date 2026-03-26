# Web Scraping for Company Research - Implementation Guide

## Recommended Libraries (Ranked by Use Case)

### 1. BeautifulSoup + Requests (Simple Static Pages)
**Best for**: Basic HTML parsing, static content
**Pros**: Lightweight, easy to learn, minimal dependencies
**Cons**: No JavaScript rendering, basic anti-bot evasion

```bash
pip install beautifulsoup4 requests lxml --break-system-packages
```

### 2. Playwright (Modern, JavaScript-Heavy Sites) ⭐ RECOMMENDED
**Best for**: Glassdoor, Indeed, LinkedIn (JavaScript-rendered content)
**Pros**: Full browser automation, excellent anti-detection, handles dynamic content
**Cons**: Heavier resource usage

```bash
pip install playwright --break-system-packages
playwright install chromium
```

### 3. Scrapy (Large-Scale Scraping)
**Best for**: Scraping 100+ companies, building scraping pipelines
**Pros**: Built-in rate limiting, concurrent requests, data pipelines
**Cons**: Steeper learning curve, overkill for small projects

```bash
pip install scrapy --break-system-packages
```

### 4. Selenium (Older but Reliable)
**Best for**: Sites requiring complex interactions
**Pros**: Mature ecosystem, lots of tutorials
**Cons**: Slower than Playwright, more detectable

```bash
pip install selenium --break-system-packages
```

---

## RECOMMENDED: Playwright Implementation

Playwright is the best choice for Glassdoor because:
- Handles JavaScript rendering (Glassdoor loads ratings dynamically)
- Built-in stealth mode (harder to detect)
- Can handle authentication if needed
- Faster than Selenium
- Better anti-detection than requests/BeautifulSoup

### Installation

```bash
pip install playwright --break-system-packages
playwright install chromium  # or firefox, webkit
```

### Basic Glassdoor Scraper (Playwright)

```python
from playwright.sync_api import sync_playwright
import time
import random
from typing import Optional
from dataclasses import dataclass


@dataclass
class GlassdoorMetrics:
    overall_rating: float = 0.0
    culture_values: float = 0.0
    work_life_balance: float = 0.0
    career_opportunities: float = 0.0
    senior_leadership: float = 0.0
    recommend_friend: float = 0.0
    ceo_approval: float = 0.0
    total_reviews: int = 0
    company_url: str = ""


class PlaywrightGlassdoorScraper:
    """
    Glassdoor scraper using Playwright for JavaScript rendering
    """
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        """
        Args:
            headless: Run browser in headless mode (no GUI)
            slow_mo: Slow down operations by X milliseconds (for debugging)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        
    def search_company(self, company_name: str) -> Optional[str]:
        """
        Search for company and return Glassdoor URL
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
            
            # Use stealth settings to avoid detection
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = context.new_page()
            
            try:
                # Search for company on Glassdoor
                search_url = f"https://www.glassdoor.com/Search/results.htm?keyword={company_name}"
                page.goto(search_url, wait_until='networkidle')
                
                # Wait for search results
                time.sleep(random.uniform(2, 4))  # Random delay to appear human
                
                # Find first company result
                first_result = page.query_selector('a[data-test="employer-name"]')
                if first_result:
                    company_url = first_result.get_attribute('href')
                    if not company_url.startswith('http'):
                        company_url = f"https://www.glassdoor.com{company_url}"
                    
                    return company_url
                    
                return None
                
            finally:
                context.close()
                browser.close()
    
    def fetch_metrics(self, company_name: str) -> Optional[GlassdoorMetrics]:
        """
        Fetch Glassdoor metrics for a company
        """
        # First, find the company URL
        company_url = self.search_company(company_name)
        if not company_url:
            print(f"Could not find {company_name} on Glassdoor")
            return None
            
        return self.fetch_metrics_from_url(company_url)
        
    def fetch_metrics_from_url(self, company_url: str) -> Optional[GlassdoorMetrics]:
        """
        Scrape Glassdoor metrics from a specific company URL
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = context.new_page()
            
            try:
                # Navigate to company page
                page.goto(company_url, wait_until='networkidle')
                
                # Random delay to appear human
                time.sleep(random.uniform(2, 4))
                
                metrics = GlassdoorMetrics(company_url=company_url)
                
                # Extract overall rating
                overall_rating_elem = page.query_selector('[data-test="rating"]')
                if overall_rating_elem:
                    metrics.overall_rating = float(overall_rating_elem.inner_text())
                
                # Extract specific ratings
                # Note: Glassdoor's HTML structure changes frequently
                # You may need to update these selectors
                
                # Method 1: Try data attributes
                rating_categories = {
                    'culture_values': 'Culture & Values',
                    'work_life_balance': 'Work/Life Balance',
                    'career_opportunities': 'Career Opportunities',
                    'senior_leadership': 'Senior Management'
                }
                
                for attr, label in rating_categories.items():
                    elem = page.query_selector(f'text="{label}"')
                    if elem:
                        # Find rating value near this label
                        parent = elem.evaluate('el => el.parentElement')
                        rating_text = page.evaluate('el => el.textContent', parent)
                        # Extract number (e.g., "3.8" from "Work/Life Balance 3.8")
                        import re
                        match = re.search(r'(\d+\.\d+)', rating_text)
                        if match:
                            setattr(metrics, attr, float(match.group(1)))
                
                # Extract CEO approval
                ceo_elem = page.query_selector('text=/CEO Approval.*?\\d+%/')
                if ceo_elem:
                    text = ceo_elem.inner_text()
                    import re
                    match = re.search(r'(\d+)%', text)
                    if match:
                        metrics.ceo_approval = float(match.group(1))
                
                # Extract "Recommend to Friend"
                recommend_elem = page.query_selector('text=/Recommend.*?\\d+%/')
                if recommend_elem:
                    text = recommend_elem.inner_text()
                    import re
                    match = re.search(r'(\d+)%', text)
                    if match:
                        metrics.recommend_friend = float(match.group(1))
                
                # Extract review count
                review_count_elem = page.query_selector('[data-test="review-count"]')
                if review_count_elem:
                    text = review_count_elem.inner_text()
                    # Extract number from "1,234 reviews"
                    import re
                    match = re.search(r'([\d,]+)', text)
                    if match:
                        metrics.total_reviews = int(match.group(1).replace(',', ''))
                
                return metrics
                
            except Exception as e:
                print(f"Error scraping {company_url}: {e}")
                return None
                
            finally:
                context.close()
                browser.close()


# Example usage
if __name__ == "__main__":
    scraper = PlaywrightGlassdoorScraper(headless=False)  # headless=False to see browser
    
    metrics = scraper.fetch_metrics("Netflix")
    
    if metrics:
        print(f"\nGlassdoor Metrics for Netflix:")
        print(f"Overall Rating: {metrics.overall_rating}/5")
        print(f"Culture & Values: {metrics.culture_values}/5")
        print(f"Work-Life Balance: {metrics.work_life_balance}/5")
        print(f"CEO Approval: {metrics.ceo_approval}%")
        print(f"Total Reviews: {metrics.total_reviews}")
```

---

## Alternative: BeautifulSoup + Requests (Simpler, Less Reliable)

For simpler sites or if Playwright is too heavy:

```python
import requests
from bs4 import BeautifulSoup
import time
import random


class BeautifulSoupGlassdoorScraper:
    """
    Simple scraper using requests + BeautifulSoup
    WARNING: May not work on Glassdoor due to JavaScript rendering
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def fetch_metrics(self, company_name: str) -> Optional[GlassdoorMetrics]:
        """
        Attempt to scrape Glassdoor with basic requests
        Note: Likely to fail due to JavaScript requirements
        """
        # Search for company
        search_url = f"https://www.glassdoor.com/Search/results.htm?keyword={company_name}"
        
        try:
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Random delay
            time.sleep(random.uniform(2, 5))
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract data (selectors will vary)
            # This is simplified - Glassdoor uses JavaScript to load content
            # So this approach may not work well
            
            metrics = GlassdoorMetrics()
            
            # Try to find rating
            rating_elem = soup.select_one('.rating')
            if rating_elem:
                metrics.overall_rating = float(rating_elem.text.strip())
            
            return metrics
            
        except Exception as e:
            print(f"Error: {e}")
            return None
```

---

## Alternative Sources (Easier to Scrape)

Instead of Glassdoor, consider these alternatives:

### 1. Indeed Company Reviews

```python
class IndeedReviewScraper:
    """Indeed reviews are sometimes easier to scrape"""
    
    def fetch_metrics(self, company_name: str):
        url = f"https://www.indeed.com/cmp/{company_name}/reviews"
        # Similar Playwright approach
```

### 2. Comparably

```python
class ComparablyScaper:
    """Comparably has similar metrics to Glassdoor"""
    
    def fetch_metrics(self, company_name: str):
        url = f"https://www.comparably.com/companies/{company_name}"
        # Similar Playwright approach
```

### 3. Levels.fyi (For Tech Companies)

```python
class LevelsFyiScraper:
    """Good for compensation and culture data on tech companies"""
    
    def fetch_company_data(self, company_name: str):
        url = f"https://www.levels.fyi/companies/{company_name}/salaries"
        # Playwright approach
```

---

## Important: Ethical & Legal Considerations

### ⚠️ Terms of Service

1. **Read Glassdoor's Terms**: Scraping may violate ToS
2. **Robots.txt**: Check `https://www.glassdoor.com/robots.txt`
3. **Rate Limiting**: Don't overwhelm their servers

### ✅ Best Practices

```python
class EthicalScraper:
    """
    Implements ethical scraping practices
    """
    
    def __init__(self):
        self.min_delay = 3  # seconds between requests
        self.max_delay = 7
        self.last_request = 0
        
    def rate_limit(self):
        """Enforce rate limiting"""
        now = time.time()
        elapsed = now - self.last_request
        
        if elapsed < self.min_delay:
            sleep_time = random.uniform(self.min_delay, self.max_delay)
            time.sleep(sleep_time)
        
        self.last_request = time.time()
    
    def fetch_with_respect(self, url: str):
        """Fetch with rate limiting and error handling"""
        self.rate_limit()
        
        try:
            # Your scraping code here
            pass
        except Exception as e:
            # Log error, don't retry aggressively
            print(f"Error (respecting site): {e}")
            return None
```

### 🛡️ Anti-Detection Techniques

```python
def setup_stealth_browser(playwright):
    """Configure browser to avoid detection"""
    
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox'
        ]
    )
    
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='America/New_York',
        
        # Additional stealth options
        permissions=['geolocation'],
        geolocation={'latitude': 38.9072, 'longitude': -77.0369},  # DC
    )
    
    # Remove webdriver flag
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return browser, context
```

---

## Caching Strategy (Reduce Scraping Load)

```python
import json
from datetime import datetime, timedelta
from pathlib import Path


class CachedGlassdoorScraper:
    """
    Cache Glassdoor results to avoid repeated scraping
    """
    
    def __init__(self, cache_dir: str = "./glassdoor_cache/", 
                 cache_days: int = 7):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_days = cache_days
        self.scraper = PlaywrightGlassdoorScraper()
    
    def _get_cache_path(self, company_name: str) -> Path:
        """Get cache file path for company"""
        safe_name = company_name.replace(' ', '_').replace('/', '_')
        return self.cache_dir / f"{safe_name}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache is still valid"""
        if not cache_path.exists():
            return False
        
        # Check age
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age < timedelta(days=self.cache_days)
    
    def fetch_metrics(self, company_name: str, 
                     force_refresh: bool = False) -> Optional[GlassdoorMetrics]:
        """
        Fetch metrics with caching
        """
        cache_path = self._get_cache_path(company_name)
        
        # Try cache first
        if not force_refresh and self._is_cache_valid(cache_path):
            print(f"Using cached data for {company_name}")
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return GlassdoorMetrics(**data)
        
        # Scrape fresh data
        print(f"Scraping fresh data for {company_name}")
        metrics = self.scraper.fetch_metrics(company_name)
        
        if metrics:
            # Save to cache
            with open(cache_path, 'w') as f:
                json.dump(asdict(metrics), f, indent=2)
        
        return metrics


# Usage
cached_scraper = CachedGlassdoorScraper(cache_days=7)

# First call: scrapes
metrics = cached_scraper.fetch_metrics("Netflix")

# Second call within 7 days: uses cache (0 requests)
metrics = cached_scraper.fetch_metrics("Netflix")

# Force refresh
metrics = cached_scraper.fetch_metrics("Netflix", force_refresh=True)
```

---

## Complete Integration with Your System

```python
# Update company_verification_system.py

from playwright_glassdoor_scraper import CachedGlassdoorScraper


class GlassdoorScraper:
    """Updated Glassdoor scraper using Playwright"""
    
    def __init__(self):
        self.scraper = CachedGlassdoorScraper(
            cache_dir="./glassdoor_cache/",
            cache_days=7  # Cache for 1 week
        )
        
    def fetch_metrics(self, company_name: str) -> Optional[GlassdoorMetrics]:
        """
        Fetch Glassdoor metrics with caching
        """
        try:
            return self.scraper.fetch_metrics(company_name)
        except Exception as e:
            print(f"Error fetching Glassdoor data for {company_name}: {e}")
            return None
```

---

## Handling Common Issues

### Issue 1: Glassdoor Requires Login

```python
class AuthenticatedGlassdoorScraper:
    """Scraper with authentication support"""
    
    def login(self, page, email: str, password: str):
        """Login to Glassdoor"""
        page.goto("https://www.glassdoor.com/profile/login_input.htm")
        
        # Fill login form
        page.fill('input[name="username"]', email)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        
        # Wait for login to complete
        page.wait_for_url("**/member/**", timeout=10000)
```

**Note**: Automated login may violate ToS. Use manual cookies instead:

```python
def load_cookies(context, cookie_file: str):
    """Load saved cookies"""
    with open(cookie_file, 'r') as f:
        cookies = json.load(f)
    context.add_cookies(cookies)
```

### Issue 2: CAPTCHA Challenges

```python
def handle_captcha(page):
    """Detect and handle CAPTCHA"""
    
    # Check for CAPTCHA
    if page.query_selector('iframe[title*="reCAPTCHA"]'):
        print("CAPTCHA detected - manual intervention required")
        print("Please solve CAPTCHA in the browser window")
        
        # Wait for user to solve
        input("Press Enter after solving CAPTCHA...")
```

### Issue 3: Changing HTML Structure

```python
class RobustExtractor:
    """Extract data with fallback selectors"""
    
    def extract_rating(self, page) -> Optional[float]:
        """Try multiple selectors"""
        selectors = [
            '[data-test="rating"]',
            '.rating',
            'div.ratingNum',
            'span.rating-value'
        ]
        
        for selector in selectors:
            elem = page.query_selector(selector)
            if elem:
                try:
                    return float(elem.inner_text())
                except:
                    continue
        
        return None
```

---

## Recommended Approach for Your Use Case

Given your needs (screening 10-50 companies/week):

### Option 1: Playwright + Caching (RECOMMENDED)

```python
# Best balance of reliability and ethics
scraper = CachedGlassdoorScraper(cache_days=7)

# Only scrapes once per week per company
metrics = scraper.fetch_metrics("Netflix")
```

**Pros**:
- Works with JavaScript-heavy sites
- Caching reduces requests by 90%+
- More reliable than BeautifulSoup

**Cons**:
- Heavier resource usage
- Still potentially against ToS

### Option 2: Manual Data Entry with Assisted Scraping

```python
def assisted_scraping_mode():
    """
    Open browser for user to manually verify
    while script extracts data
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible browser
        page = browser.new_page()
        
        page.goto("https://www.glassdoor.com/Reviews/netflix-reviews-SRCH_KE0,7.htm")
        
        # User manually navigates, script extracts visible data
        input("Navigate to company page, then press Enter...")
        
        # Extract from current page
        metrics = extract_from_current_page(page)
        
        return metrics
```

### Option 3: Hybrid - Scrape Public Data Only

```python
# Only scrape data that doesn't require login
# Respect robots.txt completely
# Add significant delays (10+ seconds)
```

---

## Installation Commands

```bash
# Recommended setup
pip install playwright beautifulsoup4 lxml requests --break-system-packages
playwright install chromium

# Alternative: Just BeautifulSoup (simpler but less reliable)
pip install beautifulsoup4 requests lxml --break-system-packages
```

---

## Summary

**For Glassdoor specifically**, I recommend:

1. **Playwright with caching** - Most reliable for JavaScript-heavy sites
2. **7-day cache** - Reduces scraping by 90%+
3. **Rate limiting** - 3-7 seconds between requests
4. **Stealth mode** - Avoid detection
5. **Error handling** - Graceful fallbacks

**Alternative**: Consider using multiple sources (Indeed, Comparably, Levels.fyi) to reduce dependence on any single site.

Would you like me to create the complete Playwright implementation file that integrates with your existing system?
