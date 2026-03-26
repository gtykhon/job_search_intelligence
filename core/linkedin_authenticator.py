"""
LinkedIn Authenticator Module

This module provides robust LinkedIn authentication handling with improved:
- Cookie management and validation
- Session persistence
- Error handling
- Retry logic
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime, timedelta
import json
import time
import logging
import os

class AuthenticationError(Exception):
    """Custom exception for authentication failures"""
    pass

class LinkedInAuthenticator:
    """
    Enhanced LinkedIn authentication handler with improved cookie management,
    session persistence and validation.
    """
    
    # Constants
    COOKIE_EXPIRY = timedelta(hours=24)
    LOGIN_TIMEOUT = 300  # 5 minutes
    AUTH_CHECK_TIMEOUT = 10
    DEFAULT_RETRY_DELAY = 2
    MAX_RETRIES = 3
    
    def __init__(
        self, 
        force_manual_auth: bool = False,
        cache_dir: Path = Path('cache'),
        cookie_file: str = 'linkedin_cookies.json',
        debug: bool = False
    ):
        """
        Initialize the authenticator.
        
        Args:
            force_manual_auth: Require manual authentication
            cache_dir: Directory for storing cached data
            cookie_file: Filename for cookie storage
            debug: Enable debug logging
        """
        self.force_manual_auth = force_manual_auth
        self.cache_dir = cache_dir
        self.cookies_file = cache_dir / cookie_file
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)

        # Initialize state
        self._cached_cookies = None
        self._driver = None
        
        # Load credentials
        self._load_credentials()
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_credentials(self) -> None:
        """Load LinkedIn credentials from environment with validation."""
        from dotenv import load_dotenv
        load_dotenv()
        
        self.username = os.getenv('LINKEDIN_USERNAME')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        
        if not all([self.username, self.password]):
            raise AuthenticationError(
                "LinkedIn credentials not found. Ensure LINKEDIN_USERNAME and "
                "LINKEDIN_PASSWORD are set in environment variables or .env file."
            )

    def _setup_driver(self) -> webdriver.Chrome:
        """Configure and initialize Chrome WebDriver with optimal settings."""
        options = Options()
        
        if not self.force_manual_auth:
            options.add_argument('--headless=new')
            
        # Standard security options    
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Performance options
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        
        # Additional security
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            })
            return driver
        except WebDriverException as e:
            raise AuthenticationError(f"Failed to initialize Chrome WebDriver: {str(e)}")

    def _validate_cookies(self, cookies: List[Dict[str, Any]], driver: Optional[webdriver.Chrome] = None) -> bool:
        """
        Validate authentication cookies by attempting access.
        
        Args:
            cookies: List of cookie dictionaries
            driver: Optional existing WebDriver instance
        
        Returns:
            bool: True if cookies are valid
        """
        should_quit = False
        try:
            if not driver:
                driver = self._setup_driver()
                should_quit = True
                
            driver.get('https://www.linkedin.com/feed/')
            
            for cookie in cookies:
                try:
                    # Clean up cookie data
                    cookie_data = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.linkedin.com'),
                        'path': cookie.get('path', '/')
                    }
                    if 'expiry' in cookie:
                        cookie_data['expiry'] = int(cookie['expiry'])
                    driver.add_cookie(cookie_data)
                except Exception as e:
                    self.logger.debug(f"Error setting cookie {cookie['name']}: {str(e)}")
                    continue
                    
            driver.refresh()
            
            # Check for successful login
            try:
                WebDriverWait(driver, self.AUTH_CHECK_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, "global-nav"))
                )
                return True
            except TimeoutException:
                return False
                
        except Exception as e:
            self.logger.warning(f"Cookie validation failed: {str(e)}")
            return False
        finally:
            if should_quit and driver:
                driver.quit()

    def get_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get valid authentication cookies with caching and retry logic.
        
        Returns:
            Optional[List[Dict[str, Any]]]: Valid cookies or None if authentication fails
        """
        # Check instance cache first
        if self._cached_cookies:
            if self._validate_cookies(self._cached_cookies):
                self.logger.info("Using valid cached cookies")
                return self._cached_cookies
                
        # Try loading from file
        cached_cookies = self._load_cached_cookies()
        if cached_cookies:
            self._cached_cookies = cached_cookies
            return cached_cookies
            
        # Perform fresh authentication
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.info(
                    f"Attempting authentication (attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                
                driver = self._setup_driver()
                try:
                    cookies = self._authenticate(driver)
                    
                    if cookies:
                        # Validate the new cookies
                        if self._validate_cookies(cookies, driver):
                            # Save valid cookies
                            self._cached_cookies = cookies
                            self._save_cookies(cookies)
                            return cookies
                            
                except Exception as e:
                    self.logger.warning(
                        f"Authentication attempt {attempt + 1} failed: {str(e)}"
                    )
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.DEFAULT_RETRY_DELAY * (2 ** attempt))
                finally:
                    driver.quit()
                    
            except Exception as e:
                self.logger.error(f"Authentication failed: {str(e)}")
                return None

    def _authenticate(self, driver: webdriver.Chrome) -> Optional[List[Dict[str, Any]]]:
        """
        Perform LinkedIn authentication using provided WebDriver.
        
        Args:
            driver: Configured Chrome WebDriver instance
            
        Returns:
            Optional[List[Dict[str, Any]]]: Authentication cookies if successful
        """
        try:
            driver.get('https://www.linkedin.com/login')
            
            if self.force_manual_auth:
                self._handle_manual_auth(driver)
            else:
                self._handle_automated_auth(driver)
                
            # Wait for successful login
            WebDriverWait(driver, self.LOGIN_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            
            # Get cookies after successful login
            cookies = driver.get_cookies()
            
            if not cookies:
                raise AuthenticationError("No cookies obtained after successful login")
                
            return cookies
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def _handle_manual_auth(self, driver: webdriver.Chrome) -> None:
        """Handle manual authentication process."""
        print("\n=== Manual Authentication Required ===")
        print("1. Please log in to LinkedIn in the browser window")
        print("2. Complete any security challenges if required")
        print("3. The script will continue automatically after successful login")
        
        # Wait for manual login
        try:
            WebDriverWait(driver, self.LOGIN_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
        except TimeoutException:
            raise AuthenticationError("Manual authentication timed out")

    def _handle_automated_auth(self, driver: webdriver.Chrome) -> None:
        """Handle automated authentication process."""
        try:
            # Find and fill username field
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Find and fill password field
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit login form
            submit_button = driver.find_element(By.CSS_SELECTOR, "[type=submit]")
            submit_button.click()
            
            # Check for error messages
            try:
                error = driver.find_element(By.ID, "error-for-username")
                if error.is_displayed():
                    raise AuthenticationError(f"Login failed: {error.text}")
            except NoSuchElementException:
                pass
                
        except Exception as e:
            raise AuthenticationError(f"Automated login failed: {str(e)}")

    def _save_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """
        Save authentication cookies with metadata.
        
        Args:
            cookies: List of cookie dictionaries to save
        """
        try:
            cookies_data = {
                'cookies': cookies,
                'timestamp': datetime.now().isoformat(),
                'expiry': time.time() + self.COOKIE_EXPIRY.total_seconds()
            }
            
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies_data, f, indent=2)
                
            self.logger.info(f"Saved authentication cookies to {self.cookies_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save cookies: {str(e)}")

    def _load_cached_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """
        Load and validate cached cookies if available.
        
        Returns:
            Optional[List[Dict[str, Any]]]: Valid cached cookies or None
        """
        try:
            if not self.cookies_file.exists():
                return None
                
            with open(self.cookies_file) as f:
                data = json.load(f)
                
            # Validate cookie data
            if not isinstance(data, dict):
                self.logger.warning("Invalid cookie file format")
                return None
                
            # Check expiry
            if data.get('expiry', 0) <= time.time():
                self.logger.info("Cached cookies have expired")
                return None
                
            cookies = data.get('cookies')
            if not cookies or not isinstance(cookies, list):
                return None
                
            # Validate the cookies
            if self._validate_cookies(cookies):
                self.logger.info("Using valid cached cookies")
                return cookies
                
            return None
            
        except Exception as e:
            self.logger.warning(f"Error loading cached cookies: {str(e)}")
            return None

    def clear_cache(self) -> None:
        """Clear all cached authentication data."""
        try:
            if self.cookies_file.exists():
                self.cookies_file.unlink()
            self._cached_cookies = None
            self.logger.info("Cleared authentication cache")
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {str(e)}")

    def __enter__(self) -> 'LinkedInAuthenticator':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self.clear_cache()