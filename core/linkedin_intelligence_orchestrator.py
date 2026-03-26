#!/usr/bin/env python3
"""
Comprehensive Job Search Intelligence Integration System
Orchestrates all AI-powered modules for complete automation
"""

import asyncio
import json
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import AppConfig
from src.integrations.notifications import NotificationManager

# Import our intelligent systems
from src.intelligence.automated_intelligence import AutomatedIntelligence
from src.intelligence.smart_opportunity_detector import SmartOpportunityDetector
from src.analytics.predictive_analytics import PredictiveAnalytics
from src.intelligence.job_search_intelligence import JobSearchIntelligence
from src.tracking.weekly_metrics_collector import WeeklyMetricsCollector
from src.tracking.weekly_dashboard_generator import WeeklyDashboardGenerator

# Import core LinkedIn modules
from src.core.linkedin_analyzer import LinkedInAnalyzer
from src.core.enhanced_analyzer import EnhancedLinkedInAnalyzer

logger = logging.getLogger(__name__)

class LinkedInIntelligenceOrchestrator:
    """
    Master orchestrator for all LinkedIn intelligence systems
    Coordinates automated analysis, opportunity detection, and predictive insights
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.notification_manager = None
        self.automated_intelligence = None
        self.opportunity_detector = None
        self.predictive_analytics = None
        self.job_search_intelligence = None
        self.linkedin_analyzer = None
        self.enhanced_analyzer = None
        self.weekly_metrics_collector = None
        self.weekly_dashboard_generator = None
        
        # Orchestration state
        self.last_full_analysis = None
        # Scheduling configuration
        self.schedules = {
            'quick_check': '*/30 * * * *',  # Every 30 minutes
            'opportunity_scan': '0 */4 * * *',  # Every 4 hours
            'job_search_scan': '0 */8 * * *',  # Every 8 hours
            'daily_analysis': '0 9 * * *',  # 9 AM daily
            'weekly_deep_dive': '0 10 * * 1',  # 10 AM Mondays
            'weekly_metrics_collection': '0 9 * * 1',  # 9 AM Mondays
            'weekly_dashboard_generation': '0 10 * * 1',  # 10 AM Mondays
            'predictive_update': '0 18 * * 5'  # 6 PM Fridays
        }
        
    async def initialize(self):
        """Initialize all intelligence systems"""
        try:
            logger.info("🚀 Initializing Job Search Intelligence Orchestrator...")
            
            # Initialize notification manager
            self.notification_manager = NotificationManager(self.config)
            await self.notification_manager.initialize()
            
            # Initialize core analyzers
            self.linkedin_analyzer = LinkedInAnalyzer(self.config)
            self.enhanced_analyzer = EnhancedLinkedInAnalyzer()
            
            # Initialize intelligent systems
            # AutomatedIntelligence now manages its own NotificationManager internally
            self.automated_intelligence = AutomatedIntelligence(self.config)
            self.opportunity_detector = SmartOpportunityDetector(self.config, self.notification_manager)
            self.predictive_analytics = PredictiveAnalytics(self.config, self.notification_manager)
            self.job_search_intelligence = JobSearchIntelligence(self.config, self.notification_manager)
            
            # Initialize weekly tracking systems
            db_path = getattr(self.config, 'database_path', 'data/job_search.db')
            self.weekly_metrics_collector = WeeklyMetricsCollector(db_path)
            self.weekly_dashboard_generator = WeeklyDashboardGenerator(db_path)
            
            logger.info("✅ All intelligence systems initialized")
            
            # Send initialization notification
            await self.notification_manager.send_notification(
                title="🚀 Job Search Intelligence Online",
                message="""
🤖 AI-Powered Job Search Intelligence is now active!

Active Modules:
• 🔍 Smart Opportunity Detection
• 📈 Predictive Analytics
• 🎯 Automated Intelligence
•  Job Search Intelligence
• 📱 Real-time Telegram Notifications

🕒 Automated Schedule:
• Quick checks every 30 minutes
• Opportunity scans every 4 hours
• Job search scans every 8 hours
• Daily analysis at 9 AM
• Weekly deep dive on Mondays
• Predictive updates on Fridays

Ready to maximize your LinkedIn potential! 🚀
                """.strip(),
                priority="high",
                notification_type="system_status"
            )
            
        except Exception as e:
            logger.error(f"❌ Automated scheduling failed: {e}")
            
    async def run_weekly_metrics_collection(self):
        """Run weekly metrics collection and analysis"""
        try:
            logger.info("📊 Running weekly metrics collection...")
            
            # Get current week boundaries
            current_date = datetime.now()
            week_start, week_end, week_num = self.weekly_metrics_collector.get_week_boundaries(current_date)
            
            # Collect metrics for the current week
            weekly_metrics = self.weekly_metrics_collector.collect_weekly_metrics(week_start)
            
            if weekly_metrics:
                # Save to database
                success = self.weekly_metrics_collector.save_weekly_metrics(weekly_metrics)
                
                if success:
                    # Send notification with results
                    alert_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(weekly_metrics.alert_status, "⚪")
                    
                    await self.notification_manager.send_notification(
                        title=f"📊 Weekly Metrics Collected {alert_emoji}",
                        message=f"""
📅 Week of {weekly_metrics.week_start_date}

🎯 Leadership Engagement: {weekly_metrics.leadership_engagement_percentage:.1f}%
🏢 Fortune 500 Penetration: {weekly_metrics.f500_penetration_percentage:.1f}%
🤝 Senior Connections: {weekly_metrics.senior_connections_count}
💌 Recruiter Messages: {weekly_metrics.recruiter_messages_count}
💬 Comment Quality: {weekly_metrics.comment_quality_score:.1f}/10

Status: {weekly_metrics.alert_status.upper()} {alert_emoji}

🔗 Dashboard will be generated next...
                        """.strip(),
                        priority="high",
                        notification_type="weekly_metrics"
                    )
                    
                    logger.info(f"✅ Weekly metrics collected successfully for {week_start}")
                else:
                    logger.error("❌ Failed to save weekly metrics")
            else:
                logger.warning("⚠️ No weekly metrics data available")
                
        except Exception as e:
            logger.error(f"❌ Weekly metrics collection failed: {e}")
    
    async def run_weekly_dashboard_generation(self):
        """Generate weekly performance dashboard"""
        try:
            logger.info("📈 Generating weekly performance dashboard...")
            
            # Generate 30-second dashboard
            dashboard_file = self.weekly_dashboard_generator.generate_30_second_dashboard()
            
            # Generate automation spreadsheet
            excel_file = self.weekly_dashboard_generator.generate_automation_spreadsheet()
            
            # Generate visual dashboard
            visual_file = self.weekly_dashboard_generator.generate_visual_dashboard()
            
            # Send notification with dashboard links
            await self.notification_manager.send_notification(
                title="📊 Weekly Dashboard Generated",
                message=f"""
🎯 Your Job Search Intelligence Dashboard is ready!

📊 30-Second Dashboard: {Path(dashboard_file).name}
📈 Visual Analytics: {Path(visual_file).name}
📋 Automation Spreadsheet: {Path(excel_file).name}

All files saved to: output/reports/dashboards/

🚀 Review your performance and identify opportunities!
                """.strip(),
                priority="high",
                notification_type="dashboard_ready"
            )
            
            logger.info("✅ Weekly dashboard generation completed")
            
        except Exception as e:
            logger.error(f"❌ Weekly dashboard generation failed: {e}")
    
    async def process_linkedin_export(self, export_file_path: str):
        """
        Process LinkedIn analytics export file
        Useful for importing data from LinkedIn's native analytics
        """
        try:
            logger.info(f"📂 Processing LinkedIn export: {export_file_path}")
            
            results = self.weekly_metrics_collector.process_linkedin_analytics_export(export_file_path)
            
            posts_processed = results["posts_processed"]
            weeks_updated = results["weeks_updated"]
            errors = results["errors"]
            
            # Send processing summary
            await self.notification_manager.send_notification(
                title="📂 LinkedIn Export Processed",
                message=f"""
✅ LinkedIn analytics export processed successfully!

📊 Posts processed: {posts_processed}
📅 Weeks updated: {len(weeks_updated)}
❌ Errors: {len(errors)}

Updated weeks: {', '.join(weeks_updated) if weeks_updated else 'None'}

🔄 Weekly metrics have been updated. Generate new dashboard?
                """.strip(),
                priority="medium",
                notification_type="export_processed"
            )
            
            logger.info(f"✅ Export processed: {posts_processed} posts, {len(weeks_updated)} weeks updated")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ LinkedIn export processing failed: {e}")
            raise
    
    async def get_weekly_summary(self, weeks_back: int = 4) -> Dict[str, Any]:
        """Get weekly performance summary for dashboard or API"""
        try:
            # Collect dashboard data (reuse dashboard generator logic)
            dashboard_data = self.weekly_dashboard_generator._collect_dashboard_data(weeks_back)
            
            if not dashboard_data.current_week:
                return {"error": "No current week data available"}
            
            current = dashboard_data.current_week
            
            summary = {
                "current_week": {
                    "week_start": current.week_start_date,
                    "leadership_engagement": {
                        "percentage": current.leadership_engagement_percentage,
                        "count": current.leadership_engagement_count,
                        "total": current.total_engagement_count,
                        "status": "excellent" if current.leadership_engagement_percentage >= 70 else 
                                "good" if current.leadership_engagement_percentage >= 65 else "needs_improvement"
                    },
                    "f500_penetration": {
                        "percentage": current.f500_penetration_percentage,
                        "count": current.f500_profile_views,
                        "total": current.total_profile_views,
                        "vs_industry": "3x above" if current.f500_penetration_percentage >= 30 else 
                                     "2x above" if current.f500_penetration_percentage >= 20 else "above average"
                    },
                    "connections": {
                        "senior_count": current.senior_connections_count,
                        "total_count": current.total_connections_count,
                        "recruiter_messages": current.recruiter_messages_count
                    },
                    "content_quality": {
                        "score": current.comment_quality_score,
                        "rating": "excellent" if current.comment_quality_score >= 7 else
                                "good" if current.comment_quality_score >= 5 else "needs_improvement"
                    },
                    "overall_status": current.alert_status
                },
                "trends": dashboard_data.trends,
                "alerts": dashboard_data.alerts,
                "recent_posts_count": len(dashboard_data.recent_posts),
                "generated_at": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating weekly summary: {e}")
            return {"error": str(e)}


async def main():
    """Main execution function"""
    try:
        # Load configuration
        from src.config import AppConfig
        config = AppConfig()
        
        # Create orchestrator
        orchestrator = LinkedInIntelligenceOrchestrator(config)
        await orchestrator.initialize()
        
        print("""
🚀 Job Search Intelligence v2.0 with Weekly Tracking

Select operation:
1. 🔍 Run manual full analysis
2. ⏰ Start automated scheduling  
3. 🧪 Test individual components
4. 📊 Generate weekly dashboard
5. 📈 Collect weekly metrics
6. 📂 Process LinkedIn export
7. 📋 Get weekly summary
8. 🛠️ Setup database schema
""")
        
        choice = input("Enter choice (1-8): ").strip()
        
        if choice == "1":
            print("\n🔍 Running manual full analysis...")
            await orchestrator.run_manual_full_analysis()
            
        elif choice == "2":
            print("\n⏰ Starting automated scheduling...")
            print("Press Ctrl+C to stop automation")
            orchestrator.start_scheduled_automation()
            
        elif choice == "3":
            print("\n🧪 Testing individual components...")
            
            # Test opportunity detection
            print("🔍 Testing opportunity detection...")
            opportunities = await orchestrator.opportunity_detector.detect_all_opportunities()
            print(f"   Found {sum(len(ops) for ops in opportunities.values())} opportunities")
            
            # Test predictive analytics
            print("🔮 Testing predictive analytics...")
            predictions = await orchestrator.predictive_analytics.analyze_trends_and_predict()
            print(f"   Generated insights with {predictions.get('confidence_scores', {}).get('overall', 0.5):.0%} confidence")
            
            print("✅ Component testing completed")
            
        elif choice == "4":
            print("\n📊 Generating weekly dashboard...")
            await orchestrator.run_weekly_dashboard_generation()
            
        elif choice == "5":
            print("\n📈 Collecting weekly metrics...")
            await orchestrator.run_weekly_metrics_collection()
            
        elif choice == "6":
            export_file = input("Enter LinkedIn export file path: ").strip()
            if export_file and Path(export_file).exists():
                print(f"\n📂 Processing {export_file}...")
                await orchestrator.process_linkedin_export(export_file)
            else:
                print("❌ File not found or invalid path")
                
        elif choice == "7":
            print("\n📋 Getting weekly summary...")
            summary = await orchestrator.get_weekly_summary()
            print(json.dumps(summary, indent=2))
            
        elif choice == "8":
            print("\n🛠️ Setting up database schema...")
            from setup_database import setup_database_schema
            setup_database_schema()
            print("✅ Database schema setup completed")
            
        else:
            print("👋 Goodbye!")
            
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")
        return False

    async def run_quick_intelligence_check(self):
        """Run a quick intelligence check (every 30 minutes)"""
        try:
            logger.info("⚡ Running quick intelligence check...")
            
            # Check for immediate opportunities
            opportunities = await self.opportunity_detector.detect_all_opportunities()
            
            # Filter for high-priority items only
            high_priority = {}
            total_high_priority = 0
            
            for category, ops in opportunities.items():
                high_priority[category] = [op for op in ops if op.get('priority') == 'high']
                total_high_priority += len(high_priority[category])
            
            if total_high_priority > 0:
                await self.opportunity_detector.send_opportunity_alerts(high_priority)
                logger.info(f"🎯 Quick check found {total_high_priority} high-priority opportunities")
            else:
                logger.info("✅ Quick check - no urgent opportunities found")
                
        except Exception as e:
            logger.error(f"❌ Quick intelligence check failed: {e}")
            
    async def run_opportunity_scan(self):
        """Run comprehensive opportunity scan (every 4 hours)"""
        try:
            logger.info("🔍 Running comprehensive opportunity scan...")
            
            # Full opportunity detection
            opportunities = await self.opportunity_detector.detect_all_opportunities()
            await self.opportunity_detector.send_opportunity_alerts(opportunities)
            
            total_opportunities = sum(len(ops) for ops in opportunities.values())
            logger.info(f"✅ Opportunity scan completed - {total_opportunities} opportunities found")
            
        except Exception as e:
            logger.error(f"❌ Opportunity scan failed: {e}")
            
    async def run_job_search_scan(self):
        """Run job search intelligence scan (every 8 hours)"""
        try:
            logger.info("💼 Running job search intelligence scan...")
            
            # Discover qualified jobs
            qualified_jobs = await self.job_search_intelligence.discover_qualified_jobs()
            await self.job_search_intelligence.send_job_alerts(qualified_jobs)
            
            logger.info(f"✅ Job search scan completed - {len(qualified_jobs)} qualified jobs found")
            
        except Exception as e:
            logger.error(f"❌ Job search scan failed: {e}")
            
    async def run_daily_analysis(self):
        """Run comprehensive daily analysis (9 AM daily)"""
        try:
            logger.info("📊 Running daily LinkedIn analysis...")
            
            # Run automated intelligence
            intelligence_results = await self.automated_intelligence.run_intelligent_analysis()
            
            # Run opportunity detection
            opportunities = await self.opportunity_detector.detect_all_opportunities()
            
            # Create daily summary
            summary = await self._create_daily_summary(intelligence_results, opportunities)
            
            # Send daily report
            await self.notification_manager.send_insight_alert(
                "Daily Job Search Intelligence Report",
                summary
            )
            
            self.last_full_analysis = datetime.now()
            logger.info("✅ Daily analysis completed")
            
        except Exception as e:
            logger.error(f"❌ Daily analysis failed: {e}")
            
    async def run_weekly_deep_dive(self):
        """Run weekly deep dive analysis (Mondays)"""
        try:
            logger.info("🔬 Running weekly deep dive analysis...")
            
            # Comprehensive analysis of all systems
            tasks = [
                self.automated_intelligence.run_intelligent_analysis(),
                self.opportunity_detector.detect_all_opportunities(),
                self.predictive_analytics.analyze_trends_and_predict()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            intelligence_results, opportunities, predictions = results
            
            # Create comprehensive weekly report
            weekly_report = await self._create_weekly_report(intelligence_results, opportunities, predictions)
            
            # Send weekly deep dive report
            await self.notification_manager.send_notification(
                title="📊 Weekly Job Search Intelligence Deep Dive",
                message=weekly_report,
                priority="high",
                notification_type="weekly_report"
            )
            
            logger.info("✅ Weekly deep dive completed")
            
        except Exception as e:
            logger.error(f"❌ Weekly deep dive failed: {e}")
            
    async def run_predictive_update(self):
        """Run predictive analytics update (Fridays)"""
        try:
            logger.info("🔮 Running predictive analytics update...")
            
            # Generate predictions for next week
            analytics_result = await self.predictive_analytics.analyze_trends_and_predict()
            await self.predictive_analytics.send_predictive_alerts(analytics_result)
            
            logger.info("✅ Predictive update completed")
            
        except Exception as e:
            logger.error(f"❌ Predictive update failed: {e}")
            
    async def _create_daily_summary(self, intelligence_results: Dict[str, Any], opportunities: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Create daily summary report"""
        try:
            total_opportunities = sum(len(ops) for ops in opportunities.values())
            high_priority_ops = sum(len([op for op in ops if op.get('priority') == 'high']) for ops in opportunities.values())
            
            # Extract key insights
            key_insights = []
            if intelligence_results and 'insights' in intelligence_results:
                insights = intelligence_results['insights']
                if 'network_growth' in insights:
                    key_insights.append(f"Network: {insights['network_growth']['insight']}")
                if 'content_performance' in insights:
                    key_insights.append(f"Content: {insights['content_performance']['insight']}")
            
            summary = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'insights': f"""
📊 Daily Job Search Intelligence Summary

🎯 Opportunities Found: {total_opportunities}
🚨 High Priority: {high_priority_ops}

💡 Key Insights:
{chr(10).join([f"• {insight}" for insight in key_insights[:3]]) if key_insights else "• Analysis in progress"}

📈 Next Actions:
• Review high-priority opportunities
• Engage with top content opportunities
• Follow up on networking recommendations

Generated at {datetime.now().strftime('%I:%M %p')}
                """.strip(),
                'confidence': intelligence_results.get('confidence', 0.7) if intelligence_results else 0.7,
                'generated_at': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.warning(f"⚠️ Daily summary creation failed: {e}")
            return {
                'insights': 'Daily summary generation in progress...',
                'confidence': 0.5,
                'generated_at': datetime.now().isoformat()
            }
            
    async def _create_weekly_report(self, intelligence_results: Any, opportunities: Any, predictions: Any) -> str:
        """Create comprehensive weekly report"""
        try:
            # Handle potential exceptions in results
            if isinstance(intelligence_results, Exception):
                intelligence_summary = "Intelligence analysis encountered an error"
            else:
                intelligence_summary = f"Analysis confidence: {intelligence_results.get('confidence', 0.7):.0%}"
            
            if isinstance(opportunities, Exception):
                opp_summary = "Opportunity detection encountered an error"
            else:
                total_ops = sum(len(ops) for ops in opportunities.values()) if opportunities else 0
                opp_summary = f"{total_ops} opportunities identified across all categories"
            
            if isinstance(predictions, Exception):
                pred_summary = "Predictive analysis encountered an error"
            else:
                overall_confidence = predictions.get('confidence_scores', {}).get('overall', 0.7) if predictions else 0.7
                pred_summary = f"Predictive insights generated with {overall_confidence:.0%} confidence"
            
            report = f"""
🔬 Weekly Job Search Intelligence Deep Dive

📊 Intelligence Analysis:
{intelligence_summary}

🎯 Opportunity Detection:
{opp_summary}

🔮 Predictive Analytics:
{pred_summary}

📈 Strategic Recommendations:
• Focus on highest-confidence opportunities
• Optimize content strategy based on predictions
• Strengthen network connections in growth areas
• Prepare for predicted market trends

📅 Next Week Focus:
• Implement top 3 recommended strategies
• Monitor performance metrics
• Adjust approach based on results

Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
🤖 Powered by AI-driven Job Search Intelligence
            """.strip()
            
            return report
            
        except Exception as e:
            logger.warning(f"⚠️ Weekly report creation failed: {e}")
            return f"Weekly report generation in progress... ({datetime.now().strftime('%Y-%m-%d %I:%M %p')})"
            
    def start_scheduled_automation(self):
        """Start the scheduled automation system"""
        try:
            logger.info("⏰ Setting up automated scheduling...")
            
            # Schedule quick checks every 30 minutes
            schedule.every(30).minutes.do(lambda: asyncio.create_task(self.run_quick_intelligence_check()))
            
            # Schedule opportunity scans every 4 hours
            schedule.every(4).hours.do(lambda: asyncio.create_task(self.run_opportunity_scan()))
            
            # Schedule daily analysis at 9 AM
            schedule.every().day.at("09:00").do(lambda: asyncio.create_task(self.run_daily_analysis()))
            
            # Schedule weekly deep dive on Mondays at 10 AM
            schedule.every().monday.at("10:00").do(lambda: asyncio.create_task(self.run_weekly_deep_dive()))
            
            # Schedule predictive updates on Fridays at 6 PM
            schedule.every().friday.at("18:00").do(lambda: asyncio.create_task(self.run_predictive_update()))
            
            logger.info("✅ Automation schedule configured")
            
            # Start the scheduler loop
            logger.info("🔄 Starting automated intelligence loop...")
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("⏹️ Automation stopped by user")
        except Exception as e:
            logger.error(f"❌ Automation loop failed: {e}")
            
    async def run_manual_full_analysis(self):
        """Run a complete manual analysis of all systems"""
        try:
            logger.info("🔍 Running complete manual analysis...")
            
            await self.notification_manager.send_notification(
                title="🔍 Manual Analysis Started",
                message="Running comprehensive LinkedIn intelligence analysis...",
                notification_type="system_status"
            )
            
            # Run all analyses in parallel
            tasks = [
                self.run_daily_analysis(),
                self.run_opportunity_scan(),
                self.run_predictive_update()
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            await self.notification_manager.send_notification(
                title="✅ Manual Analysis Complete",
                message="Comprehensive analysis finished! Check previous messages for detailed insights.",
                priority="high",
                notification_type="analysis_complete"
            )
            
            logger.info("✅ Complete manual analysis finished")
            
        except Exception as e:
            logger.error(f"❌ Manual analysis failed: {e}")
            await self.notification_manager.send_notification(
                title="❌ Analysis Error",
                message=f"Manual analysis encountered an error: {str(e)[:100]}...",
                priority="high",
                notification_type="error"
            )

async def main():
    """Main orchestrator demo and testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load configuration
        config = AppConfig()
        
        # Create orchestrator
        orchestrator = LinkedInIntelligenceOrchestrator(config)
        
        # Initialize all systems
        await orchestrator.initialize()
        
        print("\n🤖 Job Search Intelligence Orchestrator")
        print("=" * 50)
        print("1. Run manual full analysis")
        print("2. Start automated scheduling")
        print("3. Test individual components")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            print("\n🔍 Running manual full analysis...")
            await orchestrator.run_manual_full_analysis()
            
        elif choice == "2":
            print("\n⏰ Starting automated scheduling...")
            print("Press Ctrl+C to stop automation")
            orchestrator.start_scheduled_automation()
            
        elif choice == "3":
            print("\n🧪 Testing individual components...")
            
            # Test opportunity detection
            print("🔍 Testing opportunity detection...")
            opportunities = await orchestrator.opportunity_detector.detect_all_opportunities()
            print(f"   Found {sum(len(ops) for ops in opportunities.values())} opportunities")
            
            # Test predictive analytics
            print("🔮 Testing predictive analytics...")
            predictions = await orchestrator.predictive_analytics.analyze_trends_and_predict()
            print(f"   Generated insights with {predictions.get('confidence_scores', {}).get('overall', 0.5):.0%} confidence")
            
            print("✅ Component testing completed")
            
        else:
            print("👋 Goodbye!")
            
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
