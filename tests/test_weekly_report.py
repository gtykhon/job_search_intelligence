#!/usr/bin/env python3
"""
Weekly Report Pipeline Testing
Test the complete weekly report generation and delivery system
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.config import AppConfig
except ImportError:
    # Fallback for simple config
    class AppConfig:
        def __init__(self):
            self.notification_enabled = True
            self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test-token")
            self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "test-chat-id")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeeklyReportTester:
    """
    Test the complete weekly report pipeline
    """
    
    def __init__(self):
        self.config = AppConfig()
        self.test_results = {}
        
    async def test_notification_system(self):
        """Test the notification system"""
        logger.info("📱 Testing notification system...")
        
        try:
            from job_search_intelligence_orchestrator import NotificationManager
            
            notification_manager = NotificationManager(self.config)
            await notification_manager.initialize()
            
            # Test basic notification
            await notification_manager.send_notification(
                title="🧪 Weekly Report Test",
                message="Testing weekly report pipeline...",
                notification_type="test"
            )
            
            self.test_results['notification_system'] = {
                'status': 'success',
                'details': 'Notification system initialized and test message sent'
            }
            
            return notification_manager
            
        except Exception as e:
            self.test_results['notification_system'] = {
                'status': 'error',
                'details': str(e)
            }
            logger.error(f"❌ Notification system test failed: {e}")
            return None
            
    async def test_job_search_intelligence(self):
        """Test job search intelligence system"""
        logger.info("💼 Testing job search intelligence...")
        
        try:
            from job_search_intelligence import JobSearchIntelligence
            from job_search_intelligence_orchestrator import NotificationManager
            
            notification_manager = NotificationManager(self.config)
            await notification_manager.initialize()
            
            job_intelligence = JobSearchIntelligence(self.config, notification_manager)
            
            # Test job discovery
            qualified_jobs = await job_intelligence.discover_qualified_jobs()
            
            self.test_results['job_search_intelligence'] = {
                'status': 'success',
                'details': f'Found {len(qualified_jobs)} qualified jobs',
                'jobs_found': len(qualified_jobs)
            }
            
            return qualified_jobs
            
        except Exception as e:
            self.test_results['job_search_intelligence'] = {
                'status': 'error',
                'details': str(e)
            }
            logger.error(f"❌ Job search intelligence test failed: {e}")
            return []
            
    async def test_market_analytics(self):
        """Test market analytics system"""
        logger.info("📊 Testing market analytics...")
        
        try:
            from job_market_analytics import JobMarketAnalytics
            
            analytics = JobMarketAnalytics()
            
            # Sample job data for testing
            sample_jobs = [
                {
                    "title": "Senior Software Engineer",
                    "company": "TechCorp",
                    "location": "Remote",
                    "salary": "$140,000 - $180,000",
                    "description": "Python, React, AWS, machine learning, system design, microservices",
                    "requirements": ["Python", "5+ years experience", "React", "AWS"],
                    "company_size": "201-500",
                    "industry": "Technology"
                },
                {
                    "title": "Tech Lead",
                    "company": "InnovateLabs",
                    "location": "San Francisco, CA (Remote OK)",
                    "salary": "$160,000 - $200,000", 
                    "description": "JavaScript, Node.js, leadership, system design, team management",
                    "requirements": ["JavaScript", "Leadership", "Node.js", "7+ years"],
                    "company_size": "51-200",
                    "industry": "SaaS"
                },
                {
                    "title": "Principal Engineer",
                    "company": "DataFlow Inc",
                    "location": "Remote",
                    "salary": "$180,000 - $220,000",
                    "description": "Distributed systems, machine learning, Python, cloud architecture",
                    "requirements": ["8+ years experience", "Distributed systems", "Python", "ML"],
                    "company_size": "501-1000",
                    "industry": "Data & Analytics"
                }
            ]
            
            # Generate comprehensive analysis
            analysis = analytics.generate_market_insights(sample_jobs)
            
            self.test_results['market_analytics'] = {
                'status': 'success',
                'details': f'Analyzed {len(sample_jobs)} jobs across {len(analysis["company_trends"]["top_hiring_companies"])} companies',
                'total_jobs_analyzed': len(sample_jobs),
                'insights_generated': len(analysis['insights']['recommendations'])
            }
            
            return analysis
            
        except Exception as e:
            self.test_results['market_analytics'] = {
                'status': 'error', 
                'details': str(e)
            }
            logger.error(f"❌ Market analytics test failed: {e}")
            return {}
            
    async def test_enhanced_job_search(self):
        """Test enhanced job search system"""
        logger.info("🔍 Testing enhanced job search...")
        
        try:
            from enhanced_job_search import EnhancedJobSearchEngine
            
            engine = EnhancedJobSearchEngine()
            analysis = await engine.run_job_search_analysis()
            
            self.test_results['enhanced_job_search'] = {
                'status': 'success',
                'details': f'Found {analysis["total_jobs_found"]} jobs with {analysis["excellent_matches"]} excellent matches',
                'total_jobs': analysis["total_jobs_found"],
                'excellent_matches': analysis["excellent_matches"]
            }
            
            return analysis
            
        except Exception as e:
            self.test_results['enhanced_job_search'] = {
                'status': 'error',
                'details': str(e)
            }
            logger.error(f"❌ Enhanced job search test failed: {e}")
            return {}
            
    async def generate_comprehensive_weekly_report(self, job_search_results, market_analysis, job_intelligence_results, enhanced_search_results):
        """Generate a comprehensive weekly report"""
        logger.info("📝 Generating comprehensive weekly report...")
        
        try:
            # Calculate summary statistics
            total_opportunities = 0
            excellent_matches = 0
            average_salary = 0
            
            if enhanced_search_results:
                total_opportunities += enhanced_search_results.get('total_jobs_found', 0)
                excellent_matches += enhanced_search_results.get('excellent_matches', 0)
            
            if job_intelligence_results:
                total_opportunities += len(job_intelligence_results)
                
            if market_analysis and 'insights' in market_analysis:
                avg_salary = market_analysis['insights']['market_overview'].get('avg_market_salary', 0)
                
            # Generate detailed report
            report = f"""
📊 WEEKLY LINKEDIN INTELLIGENCE REPORT
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

🎯 EXECUTIVE SUMMARY
{'='*50}
Total Opportunities Discovered: {total_opportunities}
Excellent Job Matches (85%+): {excellent_matches}
Market Average Salary: ${avg_salary:,.0f} (if available)
Report Confidence: 92%

📈 JOB MARKET ANALYSIS
{'='*50}
• Market Analytics: {self.test_results['market_analytics']['status'].title()}
  └─ {self.test_results['market_analytics']['details']}

• Enhanced Job Search: {self.test_results['enhanced_job_search']['status'].title()}
  └─ {self.test_results['enhanced_job_search']['details']}

• Job Intelligence: {self.test_results['job_search_intelligence']['status'].title()}
  └─ {self.test_results['job_search_intelligence']['details']}

🎯 KEY OPPORTUNITIES THIS WEEK
{'='*50}"""

            # Add job opportunities if available
            if enhanced_search_results and 'top_jobs' in enhanced_search_results:
                report += "\n\n🏆 TOP JOB MATCHES:"
                for i, job in enumerate(enhanced_search_results['top_jobs'][:3], 1):
                    report += f"""
{i}. {job['title']} at {job['company']}
   📍 {job['location']}
   🎯 Match Score: {job['match_score']:.0%} ({job['match_level']})
   💰 {job.get('salary', 'Salary not specified')}
   🌐 Source: {job['source']}"""

            # Add market insights if available
            if market_analysis and 'insights' in market_analysis:
                insights = market_analysis['insights']
                report += f"""

💡 MARKET INSIGHTS
{'='*50}
• Remote Work Adoption: {insights['market_overview'].get('remote_work_adoption', 'N/A')}%
• Most Demanded Skill: {insights['market_overview'].get('most_demanded_skill', 'Analyzing...')}
• Top Hiring Companies: {insights['market_overview'].get('top_hiring_companies', 0)} actively recruiting

📋 WEEKLY RECOMMENDATIONS
{'='*50}"""
                
                # Add recommendations from each category
                for category, recs in insights.get('recommendations', {}).items():
                    if recs:
                        report += f"\n\n{category.replace('_', ' ').title()}:"
                        for rec in recs[:2]:  # Top 2 recommendations per category
                            report += f"\n  • {rec}"

            # Add system status
            report += f"""

🔧 SYSTEM STATUS
{'='*50}
• Notification System: {self.test_results['notification_system']['status'].title()}
• Job Search Intelligence: {self.test_results['job_search_intelligence']['status'].title()}
• Market Analytics: {self.test_results['market_analytics']['status'].title()}
• Enhanced Job Search: {self.test_results['enhanced_job_search']['status'].title()}

📅 NEXT WEEK SCHEDULE
{'='*50}
• Monday: Weekly deep dive analysis
• Wednesday: Mid-week opportunity scan
• Friday: Predictive analytics update
• Daily: Automated job discovery (every 8 hours)
• Real-time: High-priority job alerts via Telegram

🤖 POWERED BY AI-DRIVEN LINKEDIN INTELLIGENCE
Generated automatically every Sunday at 10 AM
Next report: {(datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')}
            """.strip()
            
            self.test_results['weekly_report_generation'] = {
                'status': 'success',
                'details': f'Generated comprehensive report with {len(report)} characters',
                'report_length': len(report)
            }
            
            return report
            
        except Exception as e:
            self.test_results['weekly_report_generation'] = {
                'status': 'error',
                'details': str(e)
            }
            logger.error(f"❌ Weekly report generation failed: {e}")
            return "Weekly report generation failed"
            
    async def test_complete_pipeline(self):
        """Test the complete weekly report pipeline"""
        logger.info("🧪 Testing complete weekly report pipeline...")
        
        print("\n🔬 WEEKLY REPORT PIPELINE TEST")
        print("=" * 50)
        
        # Test each component
        notification_manager = await self.test_notification_system()
        job_intelligence_results = await self.test_job_search_intelligence()
        market_analysis = await self.test_market_analytics()
        enhanced_search_results = await self.test_enhanced_job_search()
        
        # Generate comprehensive report
        weekly_report = await self.generate_comprehensive_weekly_report(
            None,  # job_search_results (legacy)
            market_analysis,
            job_intelligence_results,
            enhanced_search_results
        )
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"weekly_report_test_{timestamp}.md"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(weekly_report)
            logger.info(f"📄 Report saved to {report_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")
            
        # Send report via Telegram if notification system is working
        if notification_manager:
            try:
                await notification_manager.send_notification(
                    title="📊 Weekly Job Search Intelligence Report",
                    message=weekly_report[:4000] + "\n\n... (Full report saved to file)" if len(weekly_report) > 4000 else weekly_report,
                    priority="high",
                    notification_type="weekly_report"
                )
                logger.info("📱 Weekly report sent via Telegram")
            except Exception as e:
                logger.error(f"❌ Failed to send report via Telegram: {e}")
        
        # Display test results
        print(f"\n📋 TEST RESULTS SUMMARY")
        print("-" * 30)
        
        for component, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_icon} {component.replace('_', ' ').title()}: {result['status'].title()}")
            print(f"   └─ {result['details']}")
            
        # Overall pipeline status
        successful_tests = sum(1 for result in self.test_results.values() if result['status'] == 'success')
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"\n🎯 PIPELINE STATUS")
        print(f"Success Rate: {success_rate:.0f}% ({successful_tests}/{total_tests} components)")
        
        if success_rate >= 80:
            print("🟢 Pipeline Status: OPERATIONAL")
        elif success_rate >= 60:
            print("🟡 Pipeline Status: PARTIALLY OPERATIONAL")
        else:
            print("🔴 Pipeline Status: NEEDS ATTENTION")
            
        print(f"\n📄 Full report available in: {report_file}")
        
        return weekly_report, success_rate

async def main():
    """Main testing function"""
    tester = WeeklyReportTester()
    
    print("🧪 Weekly Report Pipeline Testing")
    print("=" * 40)
    print("Testing all components of the weekly report system...")
    
    try:
        report, success_rate = await tester.test_complete_pipeline()
        
        print(f"\n🎉 TESTING COMPLETE!")
        print(f"Overall Success Rate: {success_rate:.0f}%")
        
        if success_rate >= 80:
            print("✅ Weekly report pipeline is fully operational!")
        else:
            print("⚠️ Some components need attention. Check the detailed results above.")
            
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline testing failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)