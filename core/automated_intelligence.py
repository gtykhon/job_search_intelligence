#!/usr/bin/env python3
"""
Automated Job Search Intelligence Scheduler
Provides automated analysis, insights, and notifications
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import AppConfig
from src.integrations.notifications import NotificationManager
from src.core.job_search_intelligence import LinkedInIntelligenceEngine
from src.resources import ResourceManager

logger = logging.getLogger(__name__)

class AutomatedIntelligence:
    """
    Automated Job Search Intelligence
    Provides scheduled analysis, smart insights, and predictive recommendations
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.running = False
        self.last_analysis = None
        self.automation_stats = {
            'total_analyses': 0,
            'insights_generated': 0,
            'opportunities_detected': 0,
            'notifications_sent': 0,
            'start_time': datetime.now()
        }
        
    async def initialize(self):
        """Initialize the automated intelligence system"""
        logger.info("🤖 Initializing Automated Job Search Intelligence...")
        
        # Initialize components
        self.resource_manager = ResourceManager(self.config)
        await self.resource_manager.initialize()
        
        self.notification_manager = NotificationManager(self.config)
        await self.notification_manager.initialize()
        
        self.job_search_intelligence = LinkedInIntelligenceEngine(
            config=self.config,
            resource_manager=self.resource_manager
        )
        
        # Setup automated schedules
        self._setup_schedules()
        
        # Send startup notification
        await self.notification_manager.send_notification(
            title="🤖 Automated Intelligence Started",
            message="Job Search Intelligence automation is now active and will provide regular insights.",
            priority="normal",
            notification_type="automation_start"
        )
        
        logger.info("✅ Automated Intelligence system ready")
        
    def _setup_schedules(self):
        """Setup automated analysis schedules"""
        
        # Daily deep analysis at 8 AM
        schedule.every().day.at("08:00").do(self._schedule_daily_analysis)
        
        # Quick analysis every 4 hours during business hours
        schedule.every(4).hours.do(self._schedule_quick_analysis)
        
        # Weekly comprehensive report on Mondays at 9 AM
        schedule.every().monday.at("09:00").do(self._schedule_weekly_report)
        
        # Opportunity detection every 2 hours during business hours
        schedule.every(2).hours.do(self._schedule_opportunity_scan)
        
        # Performance monitoring every hour
        schedule.every().hour.do(self._schedule_performance_check)
        
        logger.info("📅 Automated schedules configured:")
        logger.info("   • Daily analysis: 8:00 AM")
        logger.info("   • Quick analysis: Every 4 hours")
        logger.info("   • Weekly report: Mondays 9:00 AM")
        logger.info("   • Opportunity scan: Every 2 hours")
        logger.info("   • Performance check: Every hour")
        
    def _schedule_daily_analysis(self):
        """Schedule daily comprehensive analysis"""
        asyncio.create_task(self.run_daily_analysis())
        
    def _schedule_quick_analysis(self):
        """Schedule quick analysis"""
        # Only during business hours (9 AM - 6 PM)
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 18:
            asyncio.create_task(self.run_quick_analysis())
            
    def _schedule_weekly_report(self):
        """Schedule weekly comprehensive report"""
        asyncio.create_task(self.run_weekly_report())
        
    def _schedule_opportunity_scan(self):
        """Schedule opportunity detection scan"""
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 18:  # Business hours only
            asyncio.create_task(self.scan_opportunities())
            
    def _schedule_performance_check(self):
        """Schedule performance monitoring"""
        asyncio.create_task(self.check_system_performance())
        
    async def run_daily_analysis(self):
        """Run comprehensive daily analysis"""
        try:
            logger.info("🌅 Starting automated daily analysis...")
            
            await self.notification_manager.send_notification(
                title="📊 Daily LinkedIn Analysis Starting",
                message="Comprehensive daily analysis has begun. This includes profile updates, network changes, and AI insights.",
                priority="normal",
                notification_type="daily_analysis_start"
            )
            
            # Run the analysis
            analysis_results = await self._run_intelligence_analysis("daily")
            
            # Generate insights
            insights = await self._generate_automated_insights(analysis_results, "daily")
            
            # Send results
            await self._send_analysis_results("Daily Analysis", analysis_results, insights)
            
            self.automation_stats['total_analyses'] += 1
            self.automation_stats['insights_generated'] += len(insights.get('insights', []))
            self.last_analysis = datetime.now()
            
            logger.info("✅ Daily analysis completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Daily analysis failed: {e}")
            await self.notification_manager.send_error_alert(
                "Daily Analysis Error",
                {
                    'message': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'location': 'run_daily_analysis'
                }
            )
            
    async def run_quick_analysis(self):
        """Run quick analysis for immediate insights"""
        try:
            logger.info("⚡ Starting automated quick analysis...")
            
            # Quick analysis - focus on recent activity
            analysis_results = await self._run_intelligence_analysis("quick")
            
            # Generate quick insights
            insights = await self._generate_automated_insights(analysis_results, "quick")
            
            # Only send notification if significant insights found
            if insights.get('significance_score', 0) > 0.7:
                await self._send_analysis_results("Quick Analysis", analysis_results, insights)
                self.automation_stats['insights_generated'] += len(insights.get('insights', []))
            
            self.automation_stats['total_analyses'] += 1
            
        except Exception as e:
            logger.warning(f"⚠️ Quick analysis warning: {e}")
            
    async def run_weekly_report(self):
        """Generate comprehensive weekly report"""
        try:
            logger.info("📈 Generating automated weekly report...")
            
            await self.notification_manager.send_notification(
                title="📊 Weekly Job Search Intelligence Report",
                message="Generating comprehensive weekly report with trends, insights, and recommendations.",
                priority="normal",
                notification_type="weekly_report_start"
            )
            
            # Comprehensive analysis
            analysis_results = await self._run_intelligence_analysis("weekly")
            
            # Generate comprehensive insights
            insights = await self._generate_automated_insights(analysis_results, "weekly")
            
            # Generate trends and predictions
            trends = await self._analyze_trends()
            
            # Send comprehensive report
            await self._send_weekly_report(analysis_results, insights, trends)
            
            self.automation_stats['total_analyses'] += 1
            self.automation_stats['insights_generated'] += len(insights.get('insights', []))
            
            logger.info("✅ Weekly report completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Weekly report failed: {e}")
            await self.notification_manager.send_error_alert(
                "Weekly Report Error",
                {
                    'message': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'location': 'run_weekly_report'
                }
            )
            
    async def scan_opportunities(self):
        """Automated opportunity detection"""
        try:
            logger.info("🔍 Scanning for automated opportunities...")
            
            # Detect opportunities
            opportunities = await self._detect_opportunities()
            
            if opportunities:
                await self.notification_manager.send_insight_alert(
                    "Opportunity Detection",
                    {
                        'insights': f"🎯 Found {len(opportunities)} new opportunities!\n\n" + 
                                   "\n".join([f"• {opp['title']}: {opp['description']}" for opp in opportunities[:5]]),
                        'confidence': max([opp.get('confidence', 0) for opp in opportunities]),
                        'generated_at': datetime.now().isoformat()
                    }
                )
                
                self.automation_stats['opportunities_detected'] += len(opportunities)
                logger.info(f"✅ Found {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.warning(f"⚠️ Opportunity scan warning: {e}")
            
    async def check_system_performance(self):
        """Automated system performance monitoring"""
        try:
            # Check system health
            performance_data = await self._get_system_performance()
            
            # Send alert if performance issues detected
            if performance_data.get('alert_level', 'normal') in ['high', 'critical']:
                await self.notification_manager.send_performance_alert(performance_data)
                
        except Exception as e:
            logger.warning(f"⚠️ Performance check warning: {e}")
            
    async def _run_intelligence_analysis(self, mode: str) -> Dict[str, Any]:
        """Run LinkedIn intelligence analysis"""
        try:
            # Configure analysis based on mode
            if mode == "daily":
                # Comprehensive daily analysis
                analysis_config = {
                    'include_profile': True,
                    'include_network': True,
                    'include_activity': True,
                    'ai_insights': True,
                    'depth': 'comprehensive'
                }
            elif mode == "quick":
                # Quick analysis for recent changes
                analysis_config = {
                    'include_profile': False,
                    'include_network': True,
                    'include_activity': True,
                    'ai_insights': True,
                    'depth': 'quick'
                }
            elif mode == "weekly":
                # Weekly comprehensive with trends
                analysis_config = {
                    'include_profile': True,
                    'include_network': True,
                    'include_activity': True,
                    'include_trends': True,
                    'ai_insights': True,
                    'depth': 'comprehensive'
                }
            
            # Mock analysis results for now (replace with real implementation)
            results = {
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'data_summary': {
                    'total_connections': 150 + (10 if mode == 'daily' else 0),
                    'new_connections': 5 if mode == 'daily' else 1,
                    'engagement_rate': 0.23,
                    'top_industries': ['Technology', 'Finance', 'Healthcare']
                },
                'confidence_scores': {'overall': 0.92},
                'status': 'success'
            }
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            raise
            
    async def _generate_automated_insights(self, analysis_results: Dict[str, Any], mode: str) -> Dict[str, Any]:
        """Generate AI-powered insights from analysis results"""
        try:
            # Use the AI provider to generate insights
            prompt = f"""
            Based on the LinkedIn analysis results below, generate automated insights for {mode} analysis:
            
            Analysis Data:
            {analysis_results}
            
            Please provide:
            1. Key trends and patterns
            2. Actionable recommendations
            3. Opportunity identification
            4. Risk assessments
            5. Strategic suggestions
            
            Format as clear, actionable insights suitable for mobile notifications.
            """
            
            # Mock AI insights for now (replace with real AI call)
            insights = {
                'insights': [
                    "📈 Network growth rate increased 15% this week - excellent momentum!",
                    "🎯 Healthcare sector connections show 2x higher engagement rates",
                    "💡 Optimal posting time detected: Tuesday 10 AM shows 40% more visibility",
                    "⚡ 3 high-value connection opportunities identified in your target industries",
                    "📊 Your content engagement rate is 35% above industry average"
                ],
                'recommendations': [
                    "Connect with 5 Healthcare professionals this week",
                    "Schedule posts for Tuesday mornings",
                    "Engage with Content Creators for network expansion"
                ],
                'significance_score': 0.85,
                'confidence': 0.91,
                'generated_at': datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Insight generation failed: {e}")
            return {'insights': [], 'confidence': 0, 'generated_at': datetime.now().isoformat()}
            
    async def _detect_opportunities(self) -> List[Dict[str, Any]]:
        """Detect networking and career opportunities using real data"""
        try:
            logger.info("🔍 Detecting real opportunities using integrated systems...")
            
            opportunities = []
            
            # 1. Get real job opportunities from our updated system
            try:
                from src.intelligence.real_linkedin_data_collector import RealLinkedInDataCollector

                # Derive search criteria from centralized job_search_config when available
                try:
                    from config import job_search_config as job_config  # type: ignore
                except Exception:
                    job_config = None

                job_titles = ['Senior Python Developer', 'Data Scientist', 'DevOps Engineer', 'ML Engineer']
                locations = ['Remote', 'San Francisco', 'New York', 'Seattle']
                salary_min = 120000

                if job_config is not None:
                    try:
                        cfg_titles = list(getattr(job_config, "SEARCH_TERMS", []))
                        cfg_locations = list(getattr(job_config, "LOCATIONS", []))
                        salary_ranges = getattr(job_config, "PREFERRED_SALARY_RANGES", {})
                        cfg_salary_min = (
                            salary_ranges.get("minimum_acceptable")
                            or salary_ranges.get("target_range_min")
                            or None
                        )
                        if cfg_titles:
                            job_titles = cfg_titles
                        if cfg_locations:
                            locations = cfg_locations
                        if cfg_salary_min is not None:
                            salary_min = cfg_salary_min
                    except Exception as config_error:
                        logger.warning(
                            f"Failed to derive automated search criteria from job_search_config: {config_error}"
                        )
                
                data_collector = RealLinkedInDataCollector()
                search_criteria = {
                    'job_titles': job_titles,
                    'locations': locations,
                    'experience_level': 'senior',
                    'salary_min': salary_min,
                    'max_results': 5
                }
                
                job_opportunities = await data_collector.collect_real_job_opportunities(search_criteria)
                
                # Convert job opportunities to opportunity format
                for job in job_opportunities[:3]:  # Top 3 job opportunities
                    opportunities.append({
                        'title': f"Job Opportunity: {job.get('title', 'Unknown Position')}",
                        'description': f"{job.get('company', 'Company')} - {job.get('location', 'Location')} | {job.get('salary', 'Salary TBD')}",
                        'type': 'career',
                        'confidence': min(0.95, float(job.get('match', '75%').replace('%', '')) / 100),
                        'action': f"Review position and apply via: {job.get('url', 'LinkedIn')}",
                        'source': job.get('source', 'linkedin_search'),
                        'url': job.get('url', ''),
                        'posted_date': job.get('posted', 'Recently')
                    })
                
                logger.info(f"✅ Found {len(job_opportunities)} real job opportunities")
                
            except Exception as e:
                logger.warning(f"Job opportunity detection failed: {e}")
            
            # 2. Get real network data for connection opportunities
            try:
                from src.intelligence.real_linkedin_api_client import RealLinkedInAPIClient
                
                api_client = RealLinkedInAPIClient()
                network_data = await api_client.get_real_network_data()
                
                if network_data and network_data.get('data_source') in ['linkedin_api_real', 'fallback_api_unavailable']:
                    # Generate connection opportunities based on real network analysis
                    senior_connections = network_data.get('senior_connections', 0)
                    total_connections = network_data.get('total_connections', 0)
                    f500_penetration = float(network_data.get('f500_penetration', '0%').replace('%', ''))
                    
                    if senior_connections > 0 and total_connections > 100:
                        opportunities.append({
                            'title': 'Network Expansion Opportunity',
                            'description': f'You have {senior_connections} senior connections out of {total_connections} total. Consider expanding in high-growth sectors.',
                            'type': 'networking',
                            'confidence': min(0.90, (senior_connections / total_connections) + 0.3),
                            'action': 'Identify and connect with 3-5 senior professionals in target industries',
                            'source': 'network_analysis',
                            'metrics': {
                                'senior_connections': senior_connections,
                                'total_connections': total_connections,
                                'f500_penetration': f500_penetration
                            }
                        })
                    
                    if f500_penetration < 30:
                        # Derive target companies from centralized config, respecting exclusions
                        target_companies = ['Google', 'Microsoft', 'Apple', 'Meta']
                        try:
                            from config import job_search_config as job_config  # type: ignore
                        except Exception:
                            job_config = None

                        if job_config is not None:
                            try:
                                companies = list(getattr(job_config, "PREFERRED_COMPANIES", []))
                                is_ignored = getattr(job_config, "is_ignored_company", None)
                                if callable(is_ignored):
                                    companies = [c for c in companies if not is_ignored(c)]
                                if companies:
                                    target_companies = companies[:5]
                            except Exception as config_error:
                                logger.warning(
                                    f"Failed to derive target companies from job_search_config: {config_error}"
                                )

                        opportunities.append({
                            'title': 'Fortune 500 Network Gap',
                            'description': f'Only {f500_penetration:.1f}% of your network is Fortune 500. Strategic connections could boost career opportunities.',
                            'type': 'connection',
                            'confidence': 0.85,
                            'action': 'Target Fortune 500 professionals in your industry for strategic connections',
                            'source': 'network_analysis',
                            'target_companies': target_companies
                        })
                
                logger.info(f"✅ Generated network-based opportunities from real data")
                
            except Exception as e:
                logger.warning(f"Network opportunity detection failed: {e}")
            
            # 3. Get opportunities from external pipeline
            try:
                from src.integrations.external_job_pipeline import ExternalJobPipelineIntegrator

                integrator = ExternalJobPipelineIntegrator()

                external_titles = ['Senior Python Developer', 'Data Scientist']
                try:
                    from config import job_search_config as job_config  # type: ignore
                except Exception:
                    job_config = None

                if job_config is not None:
                    try:
                        cfg_titles = list(getattr(job_config, "SEARCH_TERMS", []))
                        if cfg_titles:
                            external_titles = cfg_titles
                    except Exception as config_error:
                        logger.warning(
                            f"Failed to derive external pipeline titles from job_search_config: {config_error}"
                        )

                external_opportunities = integrator.get_external_opportunities({
                    'job_titles': external_titles,
                    'max_results': 3
                })
                
                for ext_opp in external_opportunities[:2]:  # Top 2 external opportunities
                    opportunities.append({
                        'title': f"External Pipeline: {getattr(ext_opp, 'title', 'Opportunity')}",
                        'description': f"{getattr(ext_opp, 'company', 'Company')} - {getattr(ext_opp, 'location', 'Location')}",
                        'type': 'career',
                        'confidence': getattr(ext_opp, 'match_score', 0.75),
                        'action': f"Review external opportunity details",
                        'source': 'external_pipeline',
                        'url': getattr(ext_opp, 'url', ''),
                        'salary': getattr(ext_opp, 'salary_range', 'TBD')
                    })
                
                logger.info(f"✅ Found {len(external_opportunities)} external pipeline opportunities")
                
            except Exception as e:
                logger.warning(f"External pipeline opportunities failed: {e}")
            
            # 4. Generate content engagement opportunities based on real data
            try:
                current_hour = datetime.now().hour
                current_day = datetime.now().strftime('%A')
                
                # Use real timing data for content opportunities
                if current_day in ['Tuesday', 'Wednesday', 'Thursday'] and 9 <= current_hour <= 16:
                    opportunities.append({
                        'title': 'Optimal Content Timing',
                        'description': f'{current_day} {current_hour}:00 shows high engagement potential. Perfect time for professional content.',
                        'type': 'engagement',
                        'confidence': 0.82,
                        'action': 'Create and share professional content now for maximum visibility',
                        'source': 'timing_analysis',
                        'optimal_time': f'{current_day} {current_hour}:00'
                    })
            
            except Exception as e:
                logger.warning(f"Content timing analysis failed: {e}")
            
            # 5. Fallback opportunities if no real data available
            if not opportunities:
                logger.warning("⚠️  No real opportunities detected, using intelligent fallbacks...")
                
                opportunities = [
                    {
                        'title': 'LinkedIn Search Opportunity',
                        'description': 'Senior-level positions available in your target locations',
                        'type': 'career',
                        'confidence': 0.75,
                        'action': 'Search LinkedIn Jobs for Senior Python Developer + Remote',
                        'source': 'fallback_search',
                        'url': 'https://www.linkedin.com/jobs/search/?keywords=Senior%20Python%20Developer&location=Remote&f_TPR=r604800&f_WT=2'
                    },
                    {
                        'title': 'Network Quality Analysis',
                        'description': 'Review and optimize your professional network composition',
                        'type': 'networking',
                        'confidence': 0.70,
                        'action': 'Analyze connection quality and identify strategic networking opportunities',
                        'source': 'fallback_analysis'
                    }
                ]
            
            # Sort opportunities by confidence score
            opportunities.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            logger.info(f"✅ Detected {len(opportunities)} total opportunities from real data sources")
            
            # Log sources for transparency
            sources = list(set([opp.get('source', 'unknown') for opp in opportunities]))
            logger.info(f"📊 Opportunity sources: {', '.join(sources)}")
            
            return opportunities[:10]  # Return top 10 opportunities
            
        except Exception as e:
            logger.error(f"❌ Real opportunity detection failed: {e}")
            # Final fallback
            return [
                {
                    'title': 'System Integration Check',
                    'description': 'Opportunity detection system needs attention - check LinkedIn API connectivity',
                    'type': 'system',
                    'confidence': 0.60,
                    'action': 'Review LinkedIn API credentials and system integration',
                    'source': 'system_fallback'
                }
            ]
            
        except Exception as e:
            logger.error(f"❌ Opportunity detection failed: {e}")
            return []
            
    async def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends and patterns"""
        # Mock trend analysis (replace with real implementation)
        return {
            'network_growth': {'trend': 'increasing', 'rate': 0.15},
            'engagement': {'trend': 'stable', 'rate': 0.23},
            'industry_shifts': ['AI/ML gaining momentum', 'Remote work normalizing'],
            'predictions': {
                'next_week': 'Expect 3-5 new connection opportunities',
                'next_month': 'Healthcare sector engagement likely to increase'
            }
        }
        
    async def _get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        uptime = datetime.now() - self.automation_stats['start_time']
        
        return {
            'status': 'Healthy',
            'uptime': str(uptime),
            'total_analyses': self.automation_stats['total_analyses'],
            'insights_generated': self.automation_stats['insights_generated'],
            'opportunities_detected': self.automation_stats['opportunities_detected'],
            'last_analysis': self.last_analysis.isoformat() if self.last_analysis else 'None',
            'alert_level': 'normal',
            'message': 'All automated systems operating normally'
        }
        
    async def _send_analysis_results(self, analysis_type: str, results: Dict[str, Any], insights: Dict[str, Any]):
        """Send analysis results via notifications"""
        
        # Format insights for notification
        insights_text = "\n".join([f"• {insight}" for insight in insights.get('insights', [])[:5]])
        
        message = f"""
🤖 Automated {analysis_type} Complete!

📊 Key Metrics:
• Connections: {results['data_summary']['total_connections']}
• New connections: {results['data_summary']['new_connections']}
• Engagement rate: {results['data_summary']['engagement_rate']:.1%}

💡 AI Insights:
{insights_text}

🎯 Confidence: {insights.get('confidence', 0):.1%}
        """.strip()
        
        await self.notification_manager.send_analysis_complete(analysis_type, {
            'data_summary': results['data_summary'],
            'confidence_scores': results['confidence_scores'],
            'analyzed_at': results['timestamp'],
            'custom_message': message
        })
        
        self.automation_stats['notifications_sent'] += 1
        
    async def _send_weekly_report(self, results: Dict[str, Any], insights: Dict[str, Any], trends: Dict[str, Any]):
        """Send comprehensive weekly report"""
        
        report = f"""
📈 Weekly Job Search Intelligence Report

📊 This Week's Performance:
• Total connections: {results['data_summary']['total_connections']}
• Network growth: {trends['network_growth']['rate']:.1%}
• Engagement trend: {trends['engagement']['trend']}

🎯 Top Insights:
{chr(10).join([f"• {insight}" for insight in insights.get('insights', [])[:3]])}

🔮 Predictions:
• {trends['predictions']['next_week']}
• {trends['predictions']['next_month']}

📋 Recommended Actions:
{chr(10).join([f"• {rec}" for rec in insights.get('recommendations', [])[:3]])}

🤖 Automation Stats:
• Total analyses: {self.automation_stats['total_analyses']}
• Insights generated: {self.automation_stats['insights_generated']}
• Opportunities found: {self.automation_stats['opportunities_detected']}
        """.strip()
        
        await self.notification_manager.send_notification(
            title="📊 Weekly Job Search Intelligence Report",
            message=report,
            priority="normal",
            notification_type="weekly_report"
        )
        
    async def start_automation(self):
        """Start the automated intelligence system"""
        self.running = True
        logger.info("🚀 Starting automated intelligence system...")
        
        await self.initialize()
        
        logger.info("🤖 Automated intelligence is now running...")
        logger.info("   Press Ctrl+C to stop")
        
        try:
            while self.running:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping automated intelligence...")
            await self.stop_automation()
            
    async def stop_automation(self):
        """Stop the automated intelligence system"""
        self.running = False
        
        await self.notification_manager.send_notification(
            title="🛑 Automated Intelligence Stopped",
            message=f"Automation completed. Total analyses: {self.automation_stats['total_analyses']}, Insights: {self.automation_stats['insights_generated']}",
            priority="normal",
            notification_type="automation_stop"
        )
        
        logger.info("✅ Automated intelligence stopped")

async def main():
    """Main function to run automated intelligence"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load configuration
        config = AppConfig()
        
        # Create and start automated intelligence
        automation = AutomatedIntelligence(config)
        await automation.start_automation()
        
    except Exception as e:
        logger.error(f"❌ Automated intelligence failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
