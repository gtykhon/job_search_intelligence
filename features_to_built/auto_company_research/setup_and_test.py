#!/usr/bin/env python3
"""
Setup and Test Script for Company Verification System

This script helps you:
1. Check dependencies
2. Install Playwright if needed
3. Test the scraper
4. Verify integration
"""

import sys
import subprocess
import os
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def check_dependency(module_name, import_name=None):
    """Check if a Python module is installed"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        print(f"✓ {module_name} is installed")
        return True
    except ImportError:
        print(f"✗ {module_name} is NOT installed")
        return False


def install_playwright():
    """Install Playwright and browser"""
    print_header("Installing Playwright")
    
    print("Installing Python package...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "playwright", "--break-system-packages"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Playwright package installed")
    else:
        print(f"✗ Installation failed: {result.stderr}")
        return False
    
    print("\nInstalling Chromium browser...")
    result = subprocess.run(
        ["playwright", "install", "chromium"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Chromium browser installed")
        return True
    else:
        print(f"✗ Browser installation failed: {result.stderr}")
        return False


def test_scraper():
    """Test the Playwright scraper"""
    print_header("Testing Playwright Scraper")
    
    try:
        from playwright_glassdoor_scraper import PlaywrightGlassdoorScraper
        
        print("Creating scraper instance...")
        scraper = PlaywrightGlassdoorScraper(headless=True)
        
        print("Testing company search...")
        url = scraper.search_company("Netflix")
        
        if url:
            print(f"✓ Successfully found Netflix")
            print(f"  URL: {url}")
            
            print("\nFetching metrics (this may take a few seconds)...")
            metrics = scraper.fetch_metrics_from_url(url, "Netflix")
            
            if metrics:
                print("✓ Successfully scraped metrics!")
                print(f"\n  Overall Rating: {metrics.overall_rating}/5")
                print(f"  Total Reviews: {metrics.total_reviews}")
                return True
            else:
                print("✗ Failed to scrape metrics")
                return False
        else:
            print("✗ Could not find Netflix on Glassdoor")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_integration():
    """Test integration with company verification system"""
    print_header("Testing Integration with Company Verification System")
    
    try:
        from company_verification_system import CompanyVerificationSystem
        
        print("Creating verification system with scraper enabled...")
        system = CompanyVerificationSystem(
            database_path="/mnt/project/company_research_database.md",
            use_glassdoor_scraper=True
        )
        
        print("✓ System initialized")
        
        print("\nTesting company verification...")
        result = system.verify_company("Netflix", "Test Position")
        
        print(f"✓ Verification complete")
        print(f"  Decision: {result.decision_status.value}")
        
        if result.glassdoor_metrics:
            print(f"  Glassdoor Rating: {result.glassdoor_metrics.overall_rating}/5")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def main():
    """Main setup script"""
    
    print_header("Company Verification System - Setup & Test")
    
    print("""
This script will:
1. Check for required dependencies
2. Optionally install Playwright
3. Test the Glassdoor scraper
4. Verify integration with company verification system
""")
    
    # Step 1: Check dependencies
    print_header("Step 1: Checking Dependencies")
    
    deps_ok = True
    deps_ok &= check_dependency("requests")
    deps_ok &= check_dependency("beautifulsoup4", "bs4")
    
    playwright_installed = check_dependency("playwright")
    
    if not deps_ok:
        print("\n⚠️  Some basic dependencies are missing.")
        print("Installing...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "requests", "beautifulsoup4", "lxml",
            "--break-system-packages"
        ])
    
    # Step 2: Install Playwright if needed
    if not playwright_installed:
        print_header("Step 2: Playwright Installation")
        
        response = input("Playwright is not installed. Install it now? (y/n): ")
        
        if response.lower() == 'y':
            if install_playwright():
                playwright_installed = True
            else:
                print("\n⚠️  Playwright installation failed.")
                print("You can install manually with:")
                print("  pip install playwright --break-system-packages")
                print("  playwright install chromium")
        else:
            print("\nSkipping Playwright installation.")
            print("The system will use placeholder Glassdoor data.")
    else:
        print("\n✓ Playwright is already installed")
    
    # Step 3: Test scraper (if Playwright is installed)
    if playwright_installed:
        print_header("Step 3: Testing Scraper")
        
        response = input("Test the Glassdoor scraper? (y/n): ")
        
        if response.lower() == 'y':
            test_scraper()
        else:
            print("Skipping scraper test")
    
    # Step 4: Test integration
    print_header("Step 4: Testing Integration")
    
    response = input("Test the company verification system? (y/n): ")
    
    if response.lower() == 'y':
        if test_integration():
            print("\n✓ All tests passed!")
        else:
            print("\n⚠️  Integration test failed")
    else:
        print("Skipping integration test")
    
    # Final summary
    print_header("Setup Complete")
    
    if playwright_installed:
        print("""
✓ Setup complete! You can now use the company verification system with
  real Glassdoor scraping.

Next steps:

1. Try the example:
   python integration_example.py

2. Or use the CLI:
   python verify_company_cli.py "Netflix" "Analytics Engineer"

3. Or use in your code:
   from company_verification_system import CompanyVerificationSystem
   
   system = CompanyVerificationSystem(use_glassdoor_scraper=True)
   result = system.verify_company("Netflix")
""")
    else:
        print("""
Setup complete (without Playwright scraping).

The system will use placeholder Glassdoor data for now.

To enable real scraping later:
1. pip install playwright --break-system-packages
2. playwright install chromium
3. Run this script again to test

You can still use the system with placeholder data:
   python verify_company_cli.py "Netflix" "Analytics Engineer"
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
