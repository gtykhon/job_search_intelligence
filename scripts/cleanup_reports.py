#!/usr/bin/env python3
"""
Reports Folder Cleanup and Reorganization Script
Consolidates duplicate folders and implements consistent naming
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import re


def cleanup_reports_folder():
    """Clean up and reorganize the reports folder structure"""
    base_path = Path("reports")
    
    print("🧹 Starting Reports Folder Cleanup...")
    print("=" * 50)
    
    # Create the new clean structure
    new_structure = {
        "daily": base_path / "daily",
        "weekly": base_path / "weekly", 
        "monthly": base_path / "monthly",
        "archive": base_path / "archive"  # For old/test files
    }
    
    # Create directories
    for folder_name, folder_path in new_structure.items():
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/verified: {folder_path}")
    
    # Move files from intelligence/daily to main daily folder
    intelligence_daily = base_path / "intelligence" / "daily"
    if intelligence_daily.exists():
        print(f"\n📁 Processing intelligence/daily folder...")
        for date_folder in intelligence_daily.iterdir():
            if date_folder.is_dir():
                target_folder = new_structure["daily"] / date_folder.name
                target_folder.mkdir(parents=True, exist_ok=True)
                
                for report_file in date_folder.iterdir():
                    if report_file.is_file():
                        target_file = target_folder / report_file.name
                        if not target_file.exists():
                            shutil.move(str(report_file), str(target_file))
                            print(f"  ➡️  Moved: {report_file.name} → daily/{date_folder.name}/")
    
    # Process weekly reports
    old_weekly = base_path / "weekly"
    if old_weekly.exists():
        print(f"\n📁 Processing weekly folder...")
        for week_folder in old_weekly.iterdir():
            if week_folder.is_dir():
                for report_file in week_folder.iterdir():
                    if report_file.is_file():
                        # Check if it's a test file
                        if "test_" in report_file.name:
                            # Move test files to archive
                            archive_folder = new_structure["archive"] / "test_files"
                            archive_folder.mkdir(parents=True, exist_ok=True)
                            target_file = archive_folder / report_file.name
                            if not target_file.exists():
                                shutil.move(str(report_file), str(target_file))
                                print(f"  📦 Archived test file: {report_file.name}")
                        else:
                            # Keep real weekly reports
                            target_folder = new_structure["weekly"] / week_folder.name
                            target_folder.mkdir(parents=True, exist_ok=True)
                            target_file = target_folder / report_file.name
                            if not target_file.exists():
                                shutil.move(str(report_file), str(target_file))
                                print(f"  ✅ Kept weekly report: {report_file.name}")
    
    # Remove empty folders
    print(f"\n🗑️  Removing empty folders...")
    remove_empty_folders(base_path)
    
    print(f"\n📊 Final Structure:")
    display_folder_structure(base_path)
    
    print(f"\n🎉 Reports folder cleanup completed!")
    return True


def remove_empty_folders(path):
    """Remove empty folders recursively"""
    for folder in path.iterdir():
        if folder.is_dir():
            remove_empty_folders(folder)
            try:
                if not any(folder.iterdir()):  # If folder is empty
                    folder.rmdir()
                    print(f"  🗑️  Removed empty folder: {folder}")
            except OSError:
                pass  # Folder not empty or can't be removed


def display_folder_structure(path, indent=0):
    """Display folder structure in tree format"""
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    
    for item in items:
        prefix = "  " * indent
        if item.is_dir():
            print(f"{prefix}📁 {item.name}/")
            # Only show first level of subfolders to avoid clutter
            if indent < 2:
                display_folder_structure(item, indent + 1)
        else:
            print(f"{prefix}📄 {item.name}")


def create_reports_readme():
    """Create a README.md file explaining the reports structure"""
    readme_content = """# Reports Folder Structure

This folder contains all generated reports from the Job Search Intelligence.

## 📁 Folder Structure

```
reports/
├── daily/           # Daily reports (opportunity detection, market analysis)
│   └── YYYY-MM-DD/  # Date-based subfolders
├── weekly/          # Weekly intelligence reports  
│   └── YYYY-WXX/    # Week-based subfolders (e.g., 2025-W40)
├── monthly/         # Monthly comprehensive reports
│   └── YYYY-MM/     # Month-based subfolders
└── archive/         # Archived/test files
    └── test_files/  # Test reports and old files
```

## 📝 File Naming Conventions

### Daily Reports
- `opportunity_detection_YYYY-MM-DD_HHMM.md` - Daily job opportunity detection
- `market_analysis_YYYY-MM-DD_HHMM.md` - Daily market trend analysis

### Weekly Reports  
- `intelligence_orchestrator_weekly_YYYY-WXX.md` - Comprehensive weekly analysis
- `performance_summary_weekly_YYYY-WXX.md` - Weekly performance metrics

### Monthly Reports
- `comprehensive_monthly_YYYY-MM.md` - Full monthly intelligence report
- `trends_analysis_monthly_YYYY-MM.md` - Monthly trend analysis

## 🔄 Automated Cleanup

The reports folder is automatically organized by:
- **Windows Task Scheduler** - Runs daily/weekly report generation
- **Intelligence Scheduler** - Organizes reports by date/type
- **Cleanup Script** - Removes old test files and empty folders

## 📊 Report Types

| Type | Frequency | Description |
|------|-----------|-------------|
| Opportunity Detection | Daily 6:00 AM | LinkedIn job opportunity scanning |
| Market Analysis | Daily 10:00 AM | Market trends and insights |
| Intelligence Orchestrator | Weekly Monday 8:00 AM | Comprehensive weekly intelligence |
| Performance Summary | Monthly 1st | Monthly performance metrics |

## 🎯 Accessing Reports

- **Latest Reports**: Check today's date folder in `daily/`
- **Weekly Summaries**: Check current week folder in `weekly/`
- **Historical Data**: Browse by date in respective folders
- **Telegram**: Reports automatically sent via Telegram bot

---
*Generated by Job Search Intelligence*
*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    readme_path = Path("reports") / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📝 Created: {readme_path}")
    return readme_path


if __name__ == "__main__":
    print("🔧 Job Search Intelligence - Reports Cleanup")
    print("=" * 60)
    
    try:
        # Change to the project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Run cleanup
        success = cleanup_reports_folder()
        
        if success:
            # Create documentation
            create_reports_readme()
            print("\n✅ All cleanup tasks completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()