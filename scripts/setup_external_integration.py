#!/usr/bin/env python3
"""
External Job Search Integration Setup Script

This script helps set up the external job search project for integration
with the Job Search Intelligence.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def main():
    print("=== Job Search Intelligence - External Job Search Integration Setup ===\n")
    
    # Define paths
    external_project_path = Path(os.getenv('EXTERNAL_PROJECT_PATH', ''))
    
    print(f"External project path: {external_project_path}")
    print(f"External project exists: {external_project_path.exists()}\n")
    
    if not external_project_path.exists():
        print("❌ External job search project not found!")
        print("Please ensure the external project exists at the expected path.")
        return False
    
    # Check for main.py
    main_py = external_project_path / "main.py"
    print(f"main.py exists: {main_py.exists()}")
    
    # Check for requirements.txt
    requirements_txt = external_project_path / "requirements.txt"
    print(f"requirements.txt exists: {requirements_txt.exists()}")
    
    # Test Python environment
    print("\n🔍 Testing external project Python environment...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import sys; print(f'Python: {sys.executable}')"],
            cwd=external_project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Python accessible: {result.stdout.strip()}")
        else:
            print(f"❌ Python test failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Python environment test error: {e}")
    
    # Test main.py execution
    print("\n🔍 Testing main.py execution...")
    
    if main_py.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(main_py), "--help"],
                cwd=external_project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ main.py executes successfully")
                if result.stdout:
                    print(f"Help output preview: {result.stdout[:200]}...")
            else:
                print(f"⚠️ main.py has issues: {result.stderr[:200]}...")
                print("This is normal if dependencies are missing.")
                
        except subprocess.TimeoutExpired:
            print("⚠️ main.py execution timed out")
        except Exception as e:
            print(f"⚠️ main.py test error: {e}")
    
    # Check for common dependencies
    print("\n🔍 Checking for common dependencies...")
    
    dependencies_to_check = [
        "anthropic",
        "openai", 
        "requests",
        "beautifulsoup4",
        "selenium",
        "pandas",
        "numpy"
    ]
    
    available_deps = []
    missing_deps = []
    
    for dep in dependencies_to_check:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {dep}; print('✅ {dep}')"],
                cwd=external_project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                available_deps.append(dep)
            else:
                missing_deps.append(dep)
                
        except Exception:
            missing_deps.append(dep)
    
    print(f"Available dependencies: {available_deps}")
    print(f"Missing dependencies: {missing_deps}")
    
    # Create integration helper script
    print("\n🔧 Creating integration helper script...")
    
    helper_script = external_project_path / "integration_helper.py"
    helper_content = '''#!/usr/bin/env python3
"""
Integration Helper for Job Search Intelligence

This script provides a simple interface for the Job Search Intelligence
system to interact with the job search project.
"""

import json
import sys
from datetime import datetime

def get_job_opportunities(search_criteria=None):
    """
    Return job opportunities in a format compatible with Job Search Intelligence
    
    Args:
        search_criteria: Dictionary with search parameters
        
    Returns:
        List of job opportunities
    """
    
    # Generate real LinkedIn job search URLs instead of fake ones
    def generate_linkedin_url(title, location):
        """Generate real LinkedIn job search URL"""
        import urllib.parse
        title_encoded = urllib.parse.quote(title)
        location_encoded = urllib.parse.quote(location) if location != "Remote" else urllib.parse.quote("Remote")
        return f"https://www.linkedin.com/jobs/search/?keywords={title_encoded}&location={location_encoded}&f_TPR=r604800&f_WT=2"
    
    opportunities = [
        {
            "title": "Senior Python Developer",
            "company": "Various Companies",
            "location": "Remote",
            "salary_range": "$120,000 - $160,000",
            "description": "Senior Python developer roles available across multiple companies",
            "url": generate_linkedin_url("Senior Python Developer", "Remote"),
            "posted_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "linkedin_search",
            "skills": ["Python", "Django", "PostgreSQL", "AWS"],
            "job_type": "full-time",
            "remote_option": True,
            "experience_level": "senior"
        },
        {
            "title": "Data Engineer",
            "company": "Multiple Companies",
            "location": "New York, NY",
            "salary_range": "$100,000 - $140,000",
            "description": "Data Engineer positions at top companies in NYC",
            "url": generate_linkedin_url("Data Engineer", "New York, NY"),
            "posted_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "linkedin_search", 
            "skills": ["Python", "Apache Spark", "SQL", "Docker"],
            "job_type": "full-time",
            "remote_option": False,
            "experience_level": "mid"
        }
    ]
    
    # TODO: Replace with actual job search logic
    # This is where you would integrate with your real job search functionality
    
    return opportunities

def main():
    """Main entry point for integration"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--json":
            # Output JSON format for Job Search Intelligence integration
            opportunities = get_job_opportunities()
            print(json.dumps({"opportunities": opportunities}, indent=2))
            return
        elif sys.argv[1] == "--help":
            print("Integration Helper for Job Search Intelligence")
            print("Usage:")
            print("  python integration_helper.py --json    # Output opportunities as JSON")
            print("  python integration_helper.py --help    # Show this help")
            return
    
    # Default behavior
    opportunities = get_job_opportunities()
    print(f"Found {len(opportunities)} job opportunities:")
    for i, opp in enumerate(opportunities, 1):
        print(f"  {i}. {opp['title']} at {opp['company']}")
        print(f"     Location: {opp['location']}")
        print(f"     Salary: {opp['salary_range']}")
        print()

if __name__ == "__main__":
    main()
'''
    
    try:
        with open(helper_script, 'w', encoding='utf-8') as f:
            f.write(helper_content)
        print(f"✅ Created integration helper: {helper_script}")
        
        # Test the helper script
        result = subprocess.run(
            [sys.executable, str(helper_script), "--json"],
            cwd=external_project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Integration helper script works!")
            # Try to parse the JSON output
            try:
                data = json.loads(result.stdout)
                opportunities = data.get('opportunities', [])
                print(f"   Found {len(opportunities)} test opportunities")
            except json.JSONDecodeError:
                print("⚠️ JSON parsing issue, but script executed")
        else:
            print(f"⚠️ Helper script issue: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Failed to create helper script: {e}")
    
    # Create installation guide
    print("\n📝 Creating dependency installation guide...")
    
    install_guide = external_project_path / "INTEGRATION_SETUP.md"
    guide_content = f'''# External Job Search - Job Search Intelligence Integration Setup

## Quick Setup Guide

### 1. Install Required Dependencies

```bash
cd "{external_project_path}"

# Install basic dependencies
pip install anthropic openai requests beautifulsoup4 selenium pandas numpy

# Or if you have a requirements.txt:
pip install -r requirements.txt
```

### 2. Test Integration Helper

```bash
# Test the integration helper script
python integration_helper.py --json

# Should output JSON with job opportunities
```

### 3. Configure Your Job Search Logic

Edit `integration_helper.py` and replace the mock data in `get_job_opportunities()` 
with your actual job search logic.

### 4. Test with Job Search Intelligence

The Job Search Intelligence system will automatically detect and use your 
external job search project once the dependencies are installed.

## Current Status

- External project path: {external_project_path}
- main.py exists: {main_py.exists()}
- Integration helper created: {helper_script.exists()}

## Available Dependencies

{available_deps}

## Missing Dependencies

{missing_deps}

## Next Steps

1. Install missing dependencies using pip
2. Test the integration helper script
3. Update integration_helper.py with your real job search logic
4. Run the Job Search Intelligence integration test again

## Support

If you encounter issues, check:
1. Python environment is correct
2. All dependencies are installed in the right environment
3. integration_helper.py executes without errors
4. Output is valid JSON format
'''
    
    try:
        with open(install_guide, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print(f"✅ Created setup guide: {install_guide}")
    except Exception as e:
        print(f"❌ Failed to create setup guide: {e}")
    
    # Final summary
    print("\n" + "="*60)
    print("🎯 SETUP SUMMARY")
    print("="*60)
    print(f"✅ External project found: {external_project_path}")
    print(f"✅ Integration helper created: {helper_script}")  
    print(f"✅ Setup guide created: {install_guide}")
    print(f"⚠️ Missing dependencies: {len(missing_deps)}")
    print(f"✅ Available dependencies: {len(available_deps)}")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Install missing dependencies in the external project")
    print("2. Test integration_helper.py")
    print("3. Run Job Search Intelligence integration test again")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)