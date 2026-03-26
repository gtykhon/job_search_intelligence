#!/usr/bin/env python3
"""
Weekly Automation Scheduler - Enhanced Job Search Intelligence
Integrates enhanced LinkedIn analytics with weekly reporting and Telegram notifications
"""

import os
import json
import asyncio
import schedule
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dataclasses import dataclass
from typing import Dict, List, Any
import logging

# Add project path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import messaging
from src.messaging.telegram_messenger import TelegramMessenger as BaseTelegramMessenger
from src.config import AppConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automation_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ReportConfig:
    """Configuration for report generation and organization"""
    base_dir: str = "reports"
    weekly_dir: str = "reports/weekly"
    daily_dir: str = "reports/daily"
    # Telegram credentials are sourced from AppConfig
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

class WeeklyReportOrganizer:
    """Organizes reports by week and manages file structure"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories"""
        Path(self.config.base_dir).mkdir(exist_ok=True)
        Path(self.config.weekly_dir).mkdir(exist_ok=True)
        Path(self.config.daily_dir).mkdir(exist_ok=True)
    
    def get_week_folder(self, date: datetime = None) -> str:
        """Get week folder path based on date"""
        if date is None:
            date = datetime.now()
        
        # Get Monday of the week
        monday = date - timedelta(days=date.weekday())
        week_str = monday.strftime("%Y-W%U")
        week_folder = Path(self.config.weekly_dir) / week_str
        week_folder.mkdir(exist_ok=True)
        return str(week_folder)
    
    def get_daily_folder(self, date: datetime = None) -> str:
        """Get daily folder path based on date"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        daily_folder = Path(self.config.daily_dir) / date_str
        daily_folder.mkdir(exist_ok=True)
        return str(daily_folder)

class TelegramMessenger(BaseTelegramMessenger):
    pass

class LinkedInIntelligenceScheduler:
    """Enhanced Job Search Intelligence automation scheduler with integrated analytics"""
    
    def __init__(self):
        self.config = ReportConfig()
        self.organizer = WeeklyReportOrganizer(self.config)
        # Initialize Telegram via AppConfig
        appcfg = AppConfig()
        notif = appcfg.notifications
        if notif.telegram_enabled and notif.telegram_bot_token and notif.telegram_chat_id:
            self.telegram = TelegramMessenger(notif.telegram_bot_token, notif.telegram_chat_id)
        else:
            self.telegram = None
        
        # Initialize integrated LinkedIn intelligence system
        try:
            # Import here to avoid circular dependency
            from src.intelligence.integrated_job_search_intelligence import IntegratedLinkedInIntelligence
            self.intelligence = IntegratedLinkedInIntelligence()
            logger.info("✅ Enhanced Job Search Intelligence system initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LinkedIn intelligence: {e}")
            self.intelligence = None
            
        self.setup_schedules()
    
    def setup_schedules(self):
        """Setup enhanced weekly schedule with LinkedIn intelligence"""
        # Monday - Deep Dive with Enhanced Job Search Intelligence
        schedule.every().monday.at("09:00").do(
            lambda: asyncio.run(self.run_monday_deep_dive())
        )
        
        # Wednesday - Market Scan with Network Analysis
        schedule.every().wednesday.at("12:00").do(
            lambda: asyncio.run(self.run_wednesday_scan())
        )
        
        # Friday - Predictive Analysis with Intelligence Insights
        schedule.every().friday.at("17:00").do(
            lambda: asyncio.run(self.run_friday_analysis())
        )
        
        # Sunday - Comprehensive Report with Full Analytics
        schedule.every().sunday.at("10:00").do(
            lambda: asyncio.run(self.run_sunday_report())
        )
        
        logger.info("🗓️ Enhanced Job Search Intelligence schedules configured:")
        logger.info("   Monday 9:00 AM - Deep Dive with Enhanced Analytics")
        logger.info("   Wednesday 12:00 PM - Market Scan with Network Analysis")
        logger.info("   Friday 5:00 PM - Predictive Analysis with Intelligence")
        logger.info("   Sunday 10:00 AM - Comprehensive Report with Full Analytics")
    
    async def run_monday_deep_dive(self):
        """Monday: Deep Dive Analysis with Enhanced Job Search Intelligence"""
        logger.info("🚀 Starting Monday Deep Dive with Enhanced Job Search Intelligence...")
        
        try:
            if not self.intelligence:
                raise Exception("Job Search Intelligence system not available")
            
            # Run enhanced LinkedIn analysis
            results = await self.intelligence.run_weekly_analysis("monday_deep_dive")
            
            if results['status'] != 'success':
                raise Exception(f"Analysis failed: {results.get('error', 'Unknown error')}")
            
            # Get analysis data
            analysis_results = results['analysis_results']
            report_data = results['report_data']
            real_data = analysis_results.get('real_data', {})
            combined_metrics = analysis_results.get('combined_metrics', {})
            
            # Send enhanced Telegram notification only if integrated did not send
            if not results.get('telegram_sent') and not results.get('telegram_already_sent'):
                message = f"""
🚀 <b>Monday Deep Dive - Enhanced Job Search Intelligence</b>

📊 <b>Network Analysis Summary:</b>
• 🤝 Total Connections: {real_data.get('total_connections', 0):,}
• 👔 Leadership Engagement: {real_data.get('leadership_engagement', '0%')}
• 🏢 Fortune 500 Penetration: {real_data.get('f500_penetration', '0%')}
• 🏭 Unique Companies: {combined_metrics.get('unique_companies', 0):,}
• 💪 Avg Connection Strength: {combined_metrics.get('average_connection_strength', 0):.2f}/3.0

🎯 <b>Top Insights:</b>
{chr(10).join(f"• {insight[:100]}..." if len(insight) > 100 else f"• {insight}" for insight in report_data.get('insights', [])[:3])}

📁 Session: <code>{results['session_id']}</code>

#MondayDeepDive #LinkedInIntelligence #EnhancedAnalytics
            """

                if self.telegram:
                    await self.telegram.send_message(message.strip())

                # Send report files if available
                report_files = results.get('report_files', {})
                if self.telegram and report_files.get('readable_report'):
                    await self.telegram.send_document(
                        report_files['readable_report'],
                        "📊 Monday Deep Dive - Enhanced LinkedIn Report"
                    )
            
            logger.info(f"✅ Monday Deep Dive completed with enhanced intelligence - Session: {results['session_id']}")
            
        except Exception as e:
            logger.error(f"❌ Monday Deep Dive failed: {e}")
            if self.telegram:
                await self.telegram.send_message(f"❌ Monday Deep Dive failed: {str(e)}")
    
    async def run_wednesday_scan(self):
        """Wednesday: Market Scan with Network Analysis"""
        logger.info("🔍 Starting Wednesday Market Scan with Network Analysis...")
        
        try:
            if not self.intelligence:
                raise Exception("Job Search Intelligence system not available")
            
            # Run enhanced LinkedIn analysis
            results = await self.intelligence.run_weekly_analysis("wednesday_scan")
            
            if results['status'] != 'success':
                raise Exception(f"Analysis failed: {results.get('error', 'Unknown error')}")
            
            # Get analysis data
            analysis_results = results['analysis_results']
            report_data = results['report_data']
            
            # Send enhanced Telegram notification only if integrated did not send
            if not results.get('telegram_sent') and not results.get('telegram_already_sent'):
                message = f"""
🔍 <b>Wednesday Market Scan - Network Analysis</b>

📈 <b>Mid-week Network Pulse:</b>
• 🌍 Geographic Reach: {report_data['key_metrics'].get('unique_locations', 0)} locations
• 🎯 Role Diversity: {report_data['key_metrics'].get('unique_roles', 0)} unique roles
• 🏭 Company Diversity: {report_data['key_metrics'].get('unique_companies', 0)} companies
• 💪 Network Quality: {report_data['key_metrics'].get('avg_connection_strength', 0):.2f}/3.0

⚡ <b>Quick Intelligence:</b>
{chr(10).join(f"• {insight[:80]}..." if len(insight) > 80 else f"• {insight}" for insight in report_data.get('insights', [])[:3])}

📁 Session: <code>{results['session_id']}</code>

#WednesdayScan #NetworkAnalysis #MarketIntelligence
            """
                if self.telegram:
                    await self.telegram.send_message(message.strip())
            
            logger.info(f"✅ Wednesday Market Scan completed - Session: {results['session_id']}")
            
        except Exception as e:
            logger.error(f"❌ Wednesday Market Scan failed: {e}")
            if self.telegram:
                await self.telegram.send_message(f"❌ Wednesday Market Scan failed: {str(e)}")
    
    async def run_friday_analysis(self):
        """Friday: Predictive Analysis with Intelligence Insights"""
        logger.info("🔮 Starting Friday Predictive Analysis with Intelligence...")
        
        try:
            if not self.intelligence:
                raise Exception("Job Search Intelligence system not available")
            
            # Run enhanced LinkedIn analysis
            results = await self.intelligence.run_weekly_analysis("friday_analysis")
            
            if results['status'] != 'success':
                raise Exception(f"Analysis failed: {results.get('error', 'Unknown error')}")
            
            # Get analysis data
            analysis_results = results['analysis_results']
            report_data = results['report_data']
            
            # Send enhanced Telegram notification only if integrated did not send
            if not results.get('telegram_sent') and not results.get('telegram_already_sent'):
                message = f"""
🔮 <b>Friday Predictive Analysis - Intelligence Insights</b>

📊 <b>Weekly Intelligence Summary:</b>
• 🚀 Growth Opportunities: Identified in network analysis
• 🤝 Relationship Strength: Quality connections prioritized
• 🎯 Strategic Positioning: Well-positioned for opportunities
• 💡 Network Insights: Advanced analytics complete

🎯 <b>Weekend Preparation:</b>
{chr(10).join(f"• {action[:80]}..." if len(action) > 80 else f"• {action}" for action in report_data.get('action_items', [])[:3])}

📁 Session: <code>{results['session_id']}</code>

#FridayAnalysis #PredictiveIntelligence #WeekendPrep
            """
                if self.telegram:
                    await self.telegram.send_message(message.strip())
            
            logger.info(f"✅ Friday Predictive Analysis completed - Session: {results['session_id']}")
            
        except Exception as e:
            logger.error(f"❌ Friday Predictive Analysis failed: {e}")
            if self.telegram:
                await self.telegram.send_message(f"❌ Friday Predictive Analysis failed: {str(e)}")
    
    async def run_sunday_report(self):
        """Sunday: Comprehensive Weekly Report with Full Analytics"""
        logger.info("📊 Starting Sunday Comprehensive Report with Full Analytics...")
        
        try:
            if not self.intelligence:
                raise Exception("Job Search Intelligence system not available")
            
            # Run comprehensive enhanced LinkedIn analysis
            results = await self.intelligence.run_weekly_analysis("sunday_comprehensive")
            
            if results['status'] != 'success':
                raise Exception(f"Analysis failed: {results.get('error', 'Unknown error')}")
            
            # Get analysis data
            analysis_results = results['analysis_results']
            report_data = results['report_data']
            real_data = analysis_results.get('real_data', {})
            combined_metrics = analysis_results.get('combined_metrics', {})
            
            # Send comprehensive Telegram notification only if integrated did not send
            if not results.get('telegram_sent') and not results.get('telegram_already_sent'):
                message = f"""
📊 <b>Weekly Comprehensive Report - Full LinkedIn Analytics</b>

🎯 <b>Complete Network Analysis:</b>
• 🤝 Total Connections: {real_data.get('total_connections', 0):,}
• 👔 Leadership: {real_data.get('leadership_engagement', '0%')}
• 🏢 Fortune 500: {real_data.get('f500_penetration', '0%')}
• 🏭 Companies: {combined_metrics.get('unique_companies', 0):,}
• 🌍 Locations: {combined_metrics.get('unique_locations', 0):,}
• 🎯 Roles: {combined_metrics.get('unique_roles', 0):,}

💡 <b>Key Weekly Insights:</b>
{chr(10).join(f"• {insight[:80]}..." if len(insight) > 80 else f"• {insight}" for insight in report_data.get('insights', [])[:4])}

🚀 <b>Next Week Strategy:</b>
{chr(10).join(f"• {action[:80]}..." if len(action) > 80 else f"• {action}" for action in report_data.get('action_items', [])[:3])}

📁 Session: <code>{results['session_id']}</code>

#WeeklyReport #LinkedInIntelligence #ComprehensiveAnalytics
            """
                if self.telegram:
                    await self.telegram.send_message(message.strip())

                # Send comprehensive report files
                report_files = results.get('report_files', {})
                if self.telegram and report_files.get('readable_report'):
                    await self.telegram.send_document(
                        report_files['readable_report'],
                        "📊 Weekly Comprehensive Job Search Intelligence Report"
                    )

                if self.telegram and report_files.get('companies_csv'):
                    await self.telegram.send_document(
                        report_files['companies_csv'],
                        "🏢 Top Companies Analysis (CSV)"
                    )
            
            logger.info(f"✅ Sunday Comprehensive Report completed - Session: {results['session_id']}")
            
        except Exception as e:
            logger.error(f"❌ Sunday Comprehensive Report failed: {e}")
            if self.telegram:
                await self.telegram.send_message(f"❌ Sunday Comprehensive Report failed: {str(e)}")
    
    async def run_manual_analysis(self, report_type: str = "manual"):
        """Run manual enhanced LinkedIn analysis"""
        logger.info(f"🔧 Running manual enhanced LinkedIn analysis: {report_type}")
        
        try:
            if not self.intelligence:
                raise Exception("Job Search Intelligence system not available")
            
            results = await self.intelligence.run_weekly_analysis(report_type)
            
            if results['status'] != 'success':
                raise Exception(f"Analysis failed: {results.get('error', 'Unknown error')}")
            
            # Send success notification
            message = f"""
🔧 <b>Manual LinkedIn Analysis Complete</b>

📊 <b>Analysis Results:</b>
• ✅ Enhanced analytics completed
• 💾 Database storage: {results['database_saved']}
• 📱 Telegram notification: {results['telegram_sent']}
• 📁 Session: <code>{results['session_id']}</code>

Analysis type: <code>{report_type}</code>

#ManualAnalysis #LinkedInIntelligence
            """
            
            if self.telegram:
                await self.telegram.send_message(message.strip())
            
            logger.info(f"✅ Manual analysis completed - Session: {results['session_id']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Manual analysis failed: {e}")
            if self.telegram:
                await self.telegram.send_message(f"❌ Manual analysis failed: {str(e)}")
            return None
    
    
    def generate_monday_report(self, data: Dict) -> str:
        """Generate Monday deep dive report content"""
        return f"""# Monday Weekly Deep Dive Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚀 Weekly Analysis Overview

### Opportunities Discovered
- **Total Opportunities:** {data['opportunities_discovered']}
- **New Companies:** {data['new_companies']}
- **Analysis Tasks Completed:** {data['analysis_tasks']}

### 📊 Market Intelligence

#### Trending Skills
{chr(10).join(f"- {skill}" for skill in data['skill_trends'])}

#### Salary Insights
- **Average Increase:** {data['salary_insights']['avg_increase']}
- **Hot Markets:** {', '.join(data['salary_insights']['hot_markets'])}

### 🎯 Priority Actions for This Week

{chr(10).join(f"{i+1}. {action}" for i, action in enumerate(data['priority_actions']))}

---
*Generated by Job Search Intelligence*
"""

    def generate_wednesday_report(self, data: Dict) -> str:
        """Generate Wednesday market scan report content"""
        return f"""# Wednesday Market Scan Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔍 Mid-Week Market Update

### New Opportunities
- **Opportunities Found:** {data['new_opportunities']}
- **Urgent Applications:** {data['urgent_applications']}
- **Networking Actions:** {data['networking_actions']}

### 📈 Market Changes
{chr(10).join(f"- {change}" for change in data['market_changes'])}

### ⚡ Quick Wins for Rest of Week

{chr(10).join(f"{i+1}. {win}" for i, win in enumerate(data['quick_wins']))}

---
*Generated by Job Search Intelligence*
"""

    def generate_friday_report(self, data: Dict) -> str:
        """Generate Friday predictive analysis report content"""
        return f"""# Friday Predictive Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔮 Weekend & Next Week Predictions

### Prediction Summary
- **Predictions Generated:** {data['weekend_predictions']}
- **Confidence Score:** {data['confidence_score']}%
- **Expected Monday Opportunities:** {data['monday_opportunities']}

### 📊 Market Forecast
{data['market_forecast']}

### 🎯 Recommended Weekend Preparation

{chr(10).join(f"{i+1}. {prep}" for i, prep in enumerate(data['recommended_prep']))}

---
*Generated by Job Search Intelligence*
"""

    def generate_sunday_report(self, data: Dict) -> str:
        """Generate Sunday comprehensive report content"""
        return f"""# Weekly Comprehensive Report
Week of: {datetime.now().strftime('%Y-%m-%d')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Weekly Performance Summary

### Key Metrics
- **Total Opportunities Tracked:** {data['total_opportunities']}
- **Applications Sent:** {data['applications_sent']}
- **Interviews Scheduled:** {data['interviews_scheduled']}
- **Network Connections Added:** {data['network_connections']}
- **Skills Improved:** {data['skills_improved']}
- **Market Insights Generated:** {data['market_insights']}

### 🎯 Weekly Performance Score
**{data['weekly_score']}/100** - Excellent Progress!

### 🚀 Next Week Strategic Focus

{chr(10).join(f"{i+1}. {focus}" for i, focus in enumerate(data['next_week_focus']))}

## 📈 Detailed Analytics

### Opportunity Pipeline
- Active applications in review
- Upcoming interview schedules
- Follow-up actions required

### Market Intelligence
- Industry trend analysis
- Salary benchmark updates
- Skills demand patterns

### Networking Growth
- Connection quality assessment
- Engagement metrics
- Referral opportunities

---
*Generated by Job Search Intelligence - Weekly Automation*
"""

    def run_scheduler(self):
        """Run the main scheduler loop"""
        logger.info("🚀 Job Search Intelligence Scheduler Started")
        logger.info("📅 Waiting for scheduled tasks...")
        
        # Send startup notification
        asyncio.run(self.telegram.send_message("""
🚀 <b>Job Search Intelligence Scheduler Started</b>

📅 <b>Active Schedules:</b>
• Monday 9:00 AM - Weekly Deep Dive
• Wednesday 12:00 PM - Market Scan  
• Friday 5:00 PM - Predictive Analysis
• Sunday 10:00 AM - Comprehensive Report

🔄 System is now running and monitoring...

#SystemStartup #AutomationActive
        """.strip()))
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    try:
        scheduler = LinkedInIntelligenceScheduler()
        scheduler.run_scheduler()
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")

if __name__ == "__main__":
    main()
