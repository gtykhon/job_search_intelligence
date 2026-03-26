"""
Playwright Glassdoor Scraper
Production-ready implementation with caching, rate limiting, and stealth mode

Installation:
    pip install playwright --break-system-packages
    playwright install chromium

Usage:
    from playwright_glassdoor_scraper import CachedGlassdoorScraper
    
    scraper = CachedGlassdoorScraper()
    metrics = scraper.fetch_metrics("Netflix")
"""

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import time
import random
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict


@dataclass
class GlassdoorMetrics:
    """Glassdoor company metrics"""
    overall_rating: float = 0.0
    culture_values: float = 0.0
    work_life_balance: float = 0.0
    career_opportunities: float = 0.0
    senior_leadership: float = 0.0
    recommend_friend: float = 0.0
    ceo_approval: float = 0.0
    total_reviews: int = 0
    company_url: str = ""
    scraped_at: str = ""


class PlaywrightGlassdoorScraper:
    """
    Glassdoor scraper using Playwright for JavaScript rendering
    
    Features:
    - Stealth mode to avoid detection
    - Random delays to appear human
    - Multiple selector fallbacks
    - Error handling and logging
    """
    
    def __init__(self, headless: bool = True, slow_mo: int = 0, timeout: int = 60000):
        """
        Args:
            headless: Run browser in headless mode (no GUI)
            slow_mo: Slow down operations by X milliseconds (for debugging)
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        
    def _setup_browser(self, playwright) -> tuple[Browser, BrowserContext]:
        """Configure browser with stealth settings"""
        
        browser = playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        # Create context with stealth settings
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        # Remove webdriver flag
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return browser, context
        
    def _human_delay(self, min_seconds: float = 2, max_seconds: float = 4):
        """Random delay to appear human"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract first number from text"""
        if not text:
            return None
        match = re.search(r'(\d+\.?\d*)', text.replace(',', ''))
        return float(match.group(1)) if match else None
        
    def search_company(self, company_name: str) -> Optional[str]:
        """
        Search for company and return Glassdoor URL
        
        Returns:
            Company overview URL or None if not found
        """
        with sync_playwright() as p:
            browser, context = self._setup_browser(p)
            page = context.new_page()
            page.set_default_timeout(self.timeout)
            
            try:
                # Navigate to Glassdoor search
                search_url = f"https://www.glassdoor.com/Search/results.htm?keyword={company_name.replace(' ', '+')}"
                print(f"Searching for {company_name}...")
                
                # Search results are relatively light; waiting for 'load' is sufficient
                page.goto(search_url, wait_until='load')
                self._human_delay()
                
                # Try multiple selectors for company links
                selectors = [
                    'a[data-test="employer-name"]',
                    'a.eiHdrStyle',
                    'a[href*="/Overview/"]',
                    '.employer-name a'
                ]
                
                company_url = None
                for selector in selectors:
                    elem = page.query_selector(selector)
                    if elem:
                        href = elem.get_attribute('href')
                        if href:
                            company_url = href if href.startswith('http') else f"https://www.glassdoor.com{href}"
                            print(f"Found company URL: {company_url}")
                            break
                
                return company_url
                
            except Exception as e:
                print(f"Error searching for {company_name}: {e}")
                return None
                
            finally:
                context.close()
                browser.close()
    
    def fetch_metrics(self, company_name: str) -> Optional[GlassdoorMetrics]:
        """
        Fetch Glassdoor metrics for a company
        
        Args:
            company_name: Name of company to research
            
        Returns:
            GlassdoorMetrics or None if not found
        """
        # First, find the company URL
        company_url = self.search_company(company_name)
        
        if not company_url:
            print(f"Could not find {company_name} on Glassdoor")
            return None
            
        return self.fetch_metrics_from_url(company_url, company_name)
        
    def fetch_metrics_from_url(self, company_url: str, company_name: str = "") -> Optional[GlassdoorMetrics]:
        """
        Scrape Glassdoor metrics from a specific company URL
        
        Args:
            company_url: Direct URL to company's Glassdoor page
            company_name: Company name (for logging)
            
        Returns:
            GlassdoorMetrics or None on error
        """
        with sync_playwright() as p:
            browser, context = self._setup_browser(p)
            page = context.new_page()
            page.set_default_timeout(self.timeout)
            
            try:
                print(f"Fetching metrics for {company_name or company_url}...")
                
                # Navigate to company overview page.
                # 'networkidle' can be too strict on Glassdoor; use 'load' for better reliability.
                page.goto(company_url, wait_until='load')
                self._human_delay()
                
                metrics = GlassdoorMetrics(
                    company_url=company_url,
                    scraped_at=datetime.now().isoformat()
                )
                
                # Extract overall rating
                metrics.overall_rating = self._extract_overall_rating(page)
                
                # Extract specific category ratings
                self._extract_category_ratings(page, metrics)
                
                # Extract percentages (CEO approval, recommend to friend)
                self._extract_percentages(page, metrics)
                
                # Extract review count
                metrics.total_reviews = self._extract_review_count(page)
                
                print(f"✓ Successfully scraped {company_name or 'company'}")
                print(f"  Overall: {metrics.overall_rating}/5, Reviews: {metrics.total_reviews}")
                
                return metrics
                
            except Exception as e:
                print(f"Error scraping {company_url}: {e}")
                return None
                
            finally:
                context.close()
                browser.close()
    
    def _extract_overall_rating(self, page: Page) -> float:
        """Extract overall company rating"""
        selectors = [
            '[data-test="rating"]',
            'div.rating',
            'span.ratingNum',
            'div[class*="rating"]'
        ]
        
        for selector in selectors:
            elem = page.query_selector(selector)
            if elem:
                text = elem.inner_text().strip()
                rating = self._extract_number(text)
                if rating and 0 <= rating <= 5:
                    return rating
        
        return 0.0
    
    def _extract_category_ratings(self, page: Page, metrics: GlassdoorMetrics):
        """Extract category-specific ratings"""
        
        categories = {
            'culture_values': ['Culture & Values', 'Culture and Values'],
            'work_life_balance': ['Work/Life Balance', 'Work-Life Balance'],
            'career_opportunities': ['Career Opportunities', 'Advancement'],
            'senior_leadership': ['Senior Management', 'Senior Leadership', 'Comp & Benefits']
        }
        
        for attr, labels in categories.items():
            for label in labels:
                # Try to find label and extract nearby rating
                rating = self._find_rating_by_label(page, label)
                if rating:
                    setattr(metrics, attr, rating)
                    break
    
    def _find_rating_by_label(self, page: Page, label: str) -> Optional[float]:
        """Find a rating near a specific label"""
        try:
            # Find element containing the label
            elem = page.query_selector(f'text="{label}"')
            if not elem:
                return None
            
            # Get parent element
            parent = elem.evaluate('el => el.parentElement')
            if not parent:
                return None
            
            # Search parent's text for a rating
            text = page.evaluate('el => el.textContent', parent)
            rating = self._extract_number(text)
            
            if rating and 0 <= rating <= 5:
                return rating
            
            # Try siblings
            siblings = page.evaluate('el => Array.from(el.parentElement.children).map(c => c.textContent)', elem)
            for sibling_text in siblings:
                rating = self._extract_number(sibling_text)
                if rating and 0 <= rating <= 5:
                    return rating
            
        except:
            pass
        
        return None
    
    def _extract_percentages(self, page: Page, metrics: GlassdoorMetrics):
        """Extract CEO approval and recommend to friend percentages"""
        
        # CEO Approval
        ceo_patterns = [
            'CEO Approval',
            'Approve of CEO',
            r'Approve.*?CEO'
        ]
        
        for pattern in ceo_patterns:
            elem = page.query_selector(f'text=/{pattern}/i')
            if elem:
                text = elem.inner_text()
                pct = self._extract_number(text)
                if pct and 0 <= pct <= 100:
                    metrics.ceo_approval = pct
                    break
        
        # Recommend to Friend
        recommend_patterns = [
            'Recommend to a friend',
            'Would recommend',
            r'Recommend.*?friend'
        ]
        
        for pattern in recommend_patterns:
            elem = page.query_selector(f'text=/{pattern}/i')
            if elem:
                text = elem.inner_text()
                pct = self._extract_number(text)
                if pct and 0 <= pct <= 100:
                    metrics.recommend_friend = pct
                    break
    
    def _extract_review_count(self, page: Page) -> int:
        """Extract total number of reviews"""
        selectors = [
            '[data-test="review-count"]',
            'text=/\\d+[,\\d]*\\s+reviews/i',
            'div.reviews'
        ]
        
        for selector in selectors:
            elem = page.query_selector(selector)
            if elem:
                text = elem.inner_text()
                # Extract number from "1,234 reviews" or similar
                match = re.search(r'([\d,]+)', text)
                if match:
                    count_str = match.group(1).replace(',', '')
                    return int(count_str)
        
        return 0


class CachedGlassdoorScraper:
    """
    Glassdoor scraper with caching to reduce requests
    
    Features:
    - 7-day cache by default
    - JSON file storage
    - Force refresh option
    - Cache statistics
    """
    
    def __init__(self, 
                 cache_dir: str = "./glassdoor_cache/",
                 cache_days: int = 7,
                 headless: bool = True,
                 timeout: int = 60000):
        """
        Args:
            cache_dir: Directory to store cache files
            cache_days: Number of days to keep cache valid
            headless: Run browser in headless mode
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_days = cache_days
        
        self.scraper = PlaywrightGlassdoorScraper(headless=headless, timeout=timeout)
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        
    def _get_cache_path(self, company_name: str) -> Path:
        """Get cache file path for company"""
        safe_name = re.sub(r'[^\w\s-]', '', company_name)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        return self.cache_dir / f"{safe_name.lower()}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False
        
        # Check age
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        return age < timedelta(days=self.cache_days)
    
    def _load_from_cache(self, cache_path: Path) -> Optional[GlassdoorMetrics]:
        """Load metrics from cache file"""
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return GlassdoorMetrics(**data)
        except Exception as e:
            print(f"Error loading cache: {e}")
            return None
    
    def _save_to_cache(self, cache_path: Path, metrics: GlassdoorMetrics):
        """Save metrics to cache file"""
        try:
            with open(cache_path, 'w') as f:
                json.dump(asdict(metrics), f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def fetch_metrics(self, 
                     company_name: str,
                     force_refresh: bool = False) -> Optional[GlassdoorMetrics]:
        """
        Fetch Glassdoor metrics with caching
        
        Args:
            company_name: Name of company to research
            force_refresh: Bypass cache and scrape fresh data
            
        Returns:
            GlassdoorMetrics or None if not found
        """
        cache_path = self._get_cache_path(company_name)
        
        # Try cache first (unless force refresh)
        if not force_refresh and self._is_cache_valid(cache_path):
            print(f"📋 Using cached data for {company_name} (age: <{self.cache_days} days)")
            metrics = self._load_from_cache(cache_path)
            if metrics:
                self.cache_hits += 1
                return metrics
        
        # Scrape fresh data
        print(f"🌐 Scraping fresh data for {company_name}...")
        self.cache_misses += 1
        
        metrics = self.scraper.fetch_metrics(company_name)
        
        if metrics:
            # Save to cache
            self._save_to_cache(cache_path, metrics)
            print(f"💾 Cached data for future use")
        
        return metrics
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache hit/miss statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'total_requests': total,
            'hit_rate_percent': round(hit_rate, 1)
        }
    
    def clear_cache(self):
        """Delete all cached files"""
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()
        print(f"Cleared cache directory: {self.cache_dir}")
    
    def list_cached_companies(self) -> List[str]:
        """List all companies in cache"""
        companies = []
        for cache_file in self.cache_dir.glob('*.json'):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    companies.append({
                        'file': cache_file.name,
                        'scraped_at': data.get('scraped_at', 'unknown'),
                        'rating': data.get('overall_rating', 0)
                    })
            except:
                pass
        
        return companies


# Example usage
if __name__ == "__main__":
    print("Playwright Glassdoor Scraper - Example Usage\n")
    
    # Initialize cached scraper
    scraper = CachedGlassdoorScraper(
        cache_dir="./glassdoor_cache/",
        cache_days=7,
        headless=True  # Set to False to see browser
    )
    
    # Test with multiple companies
    companies = ["Netflix", "Watershed", "Docker"]
    
    print("="*70)
    print("Fetching Glassdoor metrics for test companies")
    print("="*70 + "\n")
    
    for company in companies:
        print(f"\n{'='*70}")
        print(f"Company: {company}")
        print('='*70)
        
        metrics = scraper.fetch_metrics(company)
        
        if metrics:
            print(f"\n✓ Successfully scraped {company}")
            print(f"\nGlassdoor Metrics:")
            print(f"  Overall Rating: {metrics.overall_rating}/5")
            print(f"  Culture & Values: {metrics.culture_values}/5")
            print(f"  Work-Life Balance: {metrics.work_life_balance}/5")
            print(f"  Career Opportunities: {metrics.career_opportunities}/5")
            print(f"  Senior Leadership: {metrics.senior_leadership}/5")
            print(f"  CEO Approval: {metrics.ceo_approval}%")
            print(f"  Recommend to Friend: {metrics.recommend_friend}%")
            print(f"  Total Reviews: {metrics.total_reviews}")
            print(f"  URL: {metrics.company_url}")
        else:
            print(f"\n✗ Could not fetch metrics for {company}")
    
    # Show cache statistics
    print(f"\n{'='*70}")
    print("Cache Statistics")
    print('='*70)
    stats = scraper.get_cache_stats()
    print(f"  Cache Hits: {stats['cache_hits']}")
    print(f"  Cache Misses: {stats['cache_misses']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")
    
    # List cached companies
    print(f"\n{'='*70}")
    print("Cached Companies")
    print('='*70)
    cached = scraper.list_cached_companies()
    for item in cached:
        print(f"  {item['file']}: Rating {item['rating']}/5 (cached: {item['scraped_at'][:10]})")
