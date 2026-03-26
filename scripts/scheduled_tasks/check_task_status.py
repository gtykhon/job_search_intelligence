#!/usr/bin/env python3
"""
Job Search Intelligence - Task Status Checker
===========================================

Quick script to check the status of all scheduled tasks and provide
a comprehensive overview of the automation system.
"""

import subprocess
import sys
from datetime import datetime
import os

def run_command(cmd):
    """Run a command and return the output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def check_task_status():
    """Check the status of all LinkedIn scheduled tasks."""
    print("=" * 60)
    print(" Job Search Intelligence - Task Status Report")
    print("=" * 60)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get all LinkedIn tasks
    cmd = 'schtasks /query | findstr "LinkedIn"'
    returncode, output, error = run_command(cmd)
    
    if returncode != 0:
        print("❌ Error querying tasks:")
        print(f"   {error}")
        return
    
    if not output:
        print("⚠️  No LinkedIn tasks found in Task Scheduler")
        return
    
    print("📋 Scheduled Tasks Status:")
    print("-" * 60)
    
    tasks = []
    for line in output.split('\n'):
        if 'LinkedIn' in line:
            parts = line.split()
            if len(parts) >= 4:
                task_name = parts[0]
                next_run = ' '.join(parts[1:3])
                status = parts[3] if len(parts) > 3 else 'Unknown'
                tasks.append((task_name, next_run, status))
    
    # Sort tasks by type (daily, weekly, biweekly)
    daily_tasks = [t for t in tasks if 'Daily' in t[0]]
    weekly_tasks = [t for t in tasks if 'Weekly' in t[0]]
    biweekly_tasks = [t for t in tasks if 'Biweekly' in t[0]]
    
    def print_tasks(task_list, category):
        if task_list:
            print(f"\n🕒 {category} Tasks:")
            for task_name, next_run, status in task_list:
                status_icon = "✅" if status == "Ready" else "❌" if status == "Disabled" else "⚠️"
                clean_name = task_name.replace('LinkedIn-', '').replace('-', ' ')
                print(f"   {status_icon} {clean_name}")
                print(f"      Next Run: {next_run}")
                print(f"      Status: {status}")
                print()
    
    print_tasks(daily_tasks, "Daily")
    print_tasks(weekly_tasks, "Weekly")
    print_tasks(biweekly_tasks, "Bi-weekly")
    
    # Check for recent reports
    print("📄 Recent Reports:")
    print("-" * 60)
    
    reports_dir = "reports"
    if os.path.exists(reports_dir):
        # Check daily reports
        daily_dir = os.path.join(reports_dir, "daily")
        if os.path.exists(daily_dir):
            today = datetime.now().strftime('%Y-%m-%d')
            today_dir = os.path.join(daily_dir, today)
            if os.path.exists(today_dir):
                reports = os.listdir(today_dir)
                if reports:
                    print(f"📅 Today ({today}):")
                    for report in reports:
                        print(f"   📄 {report}")
                else:
                    print(f"📅 Today ({today}): No reports yet")
            else:
                print(f"📅 Today ({today}): No reports directory")
        else:
            print("📅 No daily reports directory found")
    else:
        print("📅 No reports directory found")
    
    print()
    
    # Check system requirements
    print("🔧 System Status:")
    print("-" * 60)
    
    # Check Python
    returncode, output, _ = run_command("python --version")
    if returncode == 0:
        print(f"✅ Python: {output}")
    else:
        print("❌ Python: Not found or not working")
    
    # Check key packages
    packages = ["selenium", "requests", "beautifulsoup4", "pandas", "streamlit"]
    for package in packages:
        returncode, output, _ = run_command(f"pip show {package}")
        if returncode == 0:
            # Extract version
            for line in output.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(': ')[1]
                    print(f"✅ {package}: {version}")
                    break
        else:
            print(f"❌ {package}: Not installed")
    
    # Check authentication
    auth_file = os.path.join("cache", "linkedin_cookies.json")
    if os.path.exists(auth_file):
        mod_time = datetime.fromtimestamp(os.path.getmtime(auth_file))
        days_old = (datetime.now() - mod_time).days
        if days_old < 7:
            print(f"✅ LinkedIn Auth: Valid (cached {days_old} days ago)")
        else:
            print(f"⚠️  LinkedIn Auth: Cached {days_old} days ago (may need refresh)")
    else:
        print("❌ LinkedIn Auth: No cached authentication found")
    
    print()
    print("💡 Management Commands:")
    print("-" * 60)
    print("   View details: schtasks /query /tn \"LinkedIn-Daily-Opportunity-Detection\" /fo list")
    print("   Run task now: schtasks /run /tn \"LinkedIn-Daily-Opportunity-Detection\"")
    print("   Open Task Scheduler: taskschd.msc")
    print("   Disable task: schtasks /change /tn \"TaskName\" /disable")
    print("   Enable task: schtasks /change /tn \"TaskName\" /enable")
    print()
    print("📚 Documentation: docs/technical/SCHEDULED_TASKS_MONITORING.md")
    print("=" * 60)

if __name__ == "__main__":
    try:
        check_task_status()
    except KeyboardInterrupt:
        print("\n\n❌ Status check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error running status check: {e}")
        sys.exit(1)