"""
Weekly Automation Schedule Configuration

This script configures and starts the weekly LinkedIn intelligence automation system.
It provides multiple scheduling options and proper error handling.
"""

import sys
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from automation.weekly_automation_scheduler import LinkedInIntelligenceScheduler
from src.utils.unicode_logging import get_unicode_logger

# Initialize logger
logger = get_unicode_logger("weekly_schedule_config")

def safe_print(message, status=None):
    """Print with status indicator"""
    if status is True:
        print(f"[OK] {message}")
    elif status is False:
        print(f"[ERROR] {message}")
    else:
        print(f"[INFO] {message}")

class WeeklyAutomationManager:
    """Manager for LinkedIn intelligence weekly automation"""
    
    def __init__(self):
        self.scheduler_instance = None
        self.is_running = False
        self.schedule_config = {
            'monday_deep_dive': {'time': '09:00', 'enabled': True},
            'wednesday_market_scan': {'time': '12:00', 'enabled': True},
            'friday_predictive': {'time': '17:00', 'enabled': True},
            'sunday_comprehensive': {'time': '10:00', 'enabled': True}
        }
    
    async def initialize_system(self):
        """Initialize the LinkedIn intelligence system"""
        try:
            safe_print("Initializing Enhanced Job Search Intelligence...")
            self.scheduler_instance = LinkedInIntelligenceScheduler()
            
            if not self.scheduler_instance.intelligence:
                safe_print("Job Search Intelligence system not available", False)
                return False
            
            safe_print("Job Search Intelligence system initialized successfully", True)
            return True
            
        except Exception as e:
            safe_print(f"Failed to initialize system: {str(e)}", False)
            logger.error(f"System initialization error: {e}")
            return False
    
    def configure_schedules(self):
        """Configure all weekly schedules"""
        safe_print("Configuring Weekly Automation Schedules...")
        
        try:
            # Clear existing schedules
            schedule.clear()
            
            # Monday Deep Dive - 9:00 AM
            if self.schedule_config['monday_deep_dive']['enabled']:
                schedule.every().monday.at(self.schedule_config['monday_deep_dive']['time']).do(
                    self._run_async_job, 'monday_deep_dive'
                )
                safe_print(f"Monday Deep Dive scheduled for {self.schedule_config['monday_deep_dive']['time']}")
            
            # Wednesday Market Scan - 12:00 PM
            if self.schedule_config['wednesday_market_scan']['enabled']:
                schedule.every().wednesday.at(self.schedule_config['wednesday_market_scan']['time']).do(
                    self._run_async_job, 'wednesday_market_scan'
                )
                safe_print(f"Wednesday Market Scan scheduled for {self.schedule_config['wednesday_market_scan']['time']}")
            
            # Friday Predictive Analysis - 5:00 PM
            if self.schedule_config['friday_predictive']['enabled']:
                schedule.every().friday.at(self.schedule_config['friday_predictive']['time']).do(
                    self._run_async_job, 'friday_predictive'
                )
                safe_print(f"Friday Predictive Analysis scheduled for {self.schedule_config['friday_predictive']['time']}")
            
            # Sunday Comprehensive Report - 10:00 AM
            if self.schedule_config['sunday_comprehensive']['enabled']:
                schedule.every().sunday.at(self.schedule_config['sunday_comprehensive']['time']).do(
                    self._run_async_job, 'sunday_comprehensive'
                )
                safe_print(f"Sunday Comprehensive Report scheduled for {self.schedule_config['sunday_comprehensive']['time']}")
            
            safe_print("All schedules configured successfully", True)
            return True
            
        except Exception as e:
            safe_print(f"Failed to configure schedules: {str(e)}", False)
            logger.error(f"Schedule configuration error: {e}")
            return False
    
    def _run_async_job(self, job_type):
        """Run an async job in the scheduler"""
        try:
            logger.info(f"Starting scheduled job: {job_type}")
            
            # Create new event loop for the job
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the job
                result = loop.run_until_complete(
                    self.scheduler_instance.run_manual_analysis(job_type)
                )
                
                if result and result.get('status') == 'success':
                    logger.info(f"Scheduled job {job_type} completed successfully")
                else:
                    logger.error(f"Scheduled job {job_type} failed")
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error running scheduled job {job_type}: {e}")
    
    def start_automation(self):
        """Start the weekly automation system"""
        safe_print("Starting Weekly Automation System...")
        
        self.is_running = True
        safe_print("Automation system is now running", True)
        safe_print("Press Ctrl+C to stop the automation")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            safe_print("Automation stopped by user", True)
            self.is_running = False
        except Exception as e:
            safe_print(f"Automation error: {str(e)}", False)
            logger.error(f"Automation runtime error: {e}")
            self.is_running = False
    
    def stop_automation(self):
        """Stop the automation system"""
        self.is_running = False
        schedule.clear()
        safe_print("Automation system stopped", True)
    
    def get_next_runs(self):
        """Get information about next scheduled runs"""
        next_runs = []
        
        for job in schedule.jobs:
            next_run = job.next_run
            if next_run:
                next_runs.append({
                    'job': str(job.job_func),
                    'next_run': next_run.strftime('%Y-%m-%d %H:%M:%S'),
                    'time_until': str(next_run - datetime.now())
                })
        
        return sorted(next_runs, key=lambda x: x['next_run'])
    
    def show_schedule_status(self):
        """Display current schedule status"""
        safe_print("Weekly Automation Schedule Status")
        safe_print("=" * 50)
        
        if not schedule.jobs:
            safe_print("No schedules configured")
            return
        
        next_runs = self.get_next_runs()
        
        safe_print(f"Total scheduled jobs: {len(schedule.jobs)}")
        safe_print(f"System running: {'Yes' if self.is_running else 'No'}")
        safe_print("")
        safe_print("Next scheduled runs:")
        
        for run_info in next_runs[:5]:  # Show next 5 runs
            safe_print(f"  {run_info['next_run']} - {run_info['job']}")

async def test_single_run(automation_manager, job_type="test_manual"):
    """Test a single manual run"""
    safe_print(f"Testing manual run: {job_type}")
    
    try:
        if not automation_manager.scheduler_instance:
            safe_print("System not initialized", False)
            return False
        
        results = await automation_manager.scheduler_instance.run_manual_analysis(job_type)
        
        if results and results.get('status') == 'success':
            safe_print("Manual test run completed successfully", True)
            safe_print(f"Session ID: {results['session_id']}")
            safe_print(f"Database saved: {results['database_saved']}")
            safe_print(f"Telegram sent: {results['telegram_sent']}")
            return True
        else:
            safe_print("Manual test run failed", False)
            return False
            
    except Exception as e:
        safe_print(f"Test run failed: {str(e)}", False)
        logger.error(f"Test run error: {e}")
        return False

def show_configuration_menu():
    """Show configuration options"""
    safe_print("Job Search Intelligence Weekly Automation Setup")
    safe_print("=" * 55)
    safe_print("")
    safe_print("Available Options:")
    safe_print("1. Test System (Manual Run)")
    safe_print("2. Configure and Start Automation")
    safe_print("3. Show Schedule Status")
    safe_print("4. Start Automation (if already configured)")
    safe_print("5. Stop Automation")
    safe_print("6. Exit")
    safe_print("")

async def main():
    """Main automation setup function"""
    automation_manager = WeeklyAutomationManager()
    
    while True:
        show_configuration_menu()
        
        try:
            choice = input("Select an option (1-6): ").strip()
            
            if choice == '1':
                # Test System
                safe_print("\nTesting Job Search Intelligence...")
                
                if await automation_manager.initialize_system():
                    await test_single_run(automation_manager)
                else:
                    safe_print("Cannot test - system initialization failed", False)
            
            elif choice == '2':
                # Configure and Start Automation
                safe_print("\nConfiguring Weekly Automation...")
                
                if await automation_manager.initialize_system():
                    if automation_manager.configure_schedules():
                        safe_print("\nConfiguration complete. Starting automation...")
                        automation_manager.show_schedule_status()
                        safe_print("\nStarting automation in 5 seconds...")
                        safe_print("Press Ctrl+C to stop")
                        
                        try:
                            time.sleep(5)
                            automation_manager.start_automation()
                        except KeyboardInterrupt:
                            safe_print("Automation startup cancelled", True)
                    else:
                        safe_print("Configuration failed", False)
                else:
                    safe_print("Cannot start - system initialization failed", False)
            
            elif choice == '3':
                # Show Schedule Status
                automation_manager.show_schedule_status()
            
            elif choice == '4':
                # Start Automation (if configured)
                if schedule.jobs:
                    safe_print("Starting automation with existing configuration...")
                    automation_manager.show_schedule_status()
                    automation_manager.start_automation()
                else:
                    safe_print("No schedules configured. Use option 2 to configure first.", False)
            
            elif choice == '5':
                # Stop Automation
                automation_manager.stop_automation()
            
            elif choice == '6':
                # Exit
                safe_print("Exiting automation setup")
                automation_manager.stop_automation()
                break
            
            else:
                safe_print("Invalid option. Please select 1-6.", False)
        
        except KeyboardInterrupt:
            safe_print("\nExiting...", True)
            automation_manager.stop_automation()
            break
        except Exception as e:
            safe_print(f"Error: {str(e)}", False)
        
        if choice != '6':
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        safe_print("Setup interrupted by user", True)
    except Exception as e:
        safe_print(f"Setup failed: {str(e)}", False)
        sys.exit(1)