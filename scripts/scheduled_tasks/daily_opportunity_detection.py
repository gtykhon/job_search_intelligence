#!/usr/bin/env python3
"""
Daily Opportunity Detection Task
Run via Windows Task Scheduler at 6:00 AM daily
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import emoji
import html

# Add parent directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

# Import centralized job search configuration when available
try:
    from config import job_search_config as job_config  # type: ignore
except Exception:
    job_config = None

# Setup logging with UTF-8 encoding and emoji support
log_dir = Path(parent_dir) / "logs"
log_dir.mkdir(exist_ok=True)

# Create custom formatter that handles emojis
class EmojiFormatter(logging.Formatter):
    def format(self, record):
        # Convert emojis to text for Windows console compatibility
        if hasattr(record, 'msg'):
            record.msg = emoji.demojize(str(record.msg))
        return super().format(record)

# Setup logging with UTF-8 file handler
file_handler = logging.FileHandler(log_dir / 'opportunity_detection.log', encoding='utf-8')
file_handler.setFormatter(EmojiFormatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(EmojiFormatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

async def run_opportunity_detection():
    """Run daily opportunity detection with real network intelligence, database tracking, and external pipeline integration"""
    start_time = datetime.now()
    session_id = f"opportunity_detection_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    logger.info("🔍 Starting daily opportunity detection task...")
    
    # Database tracking setup (new tracking DB)
    db_path = 'data/job_search.db'
    analysis_results = {}
    
    # External pipeline integration setup
    try:
        from src.integrations.external_job_pipeline import get_integrator
        from src.integrations.data_exchange import get_data_manager, sync_all_data
        
        integrator = get_integrator()
        data_manager = get_data_manager()
        
        logger.info("🔗 External job pipeline integration initialized")
        
        # Sync data with external pipeline at start
        logger.info("📊 Synchronizing with external job pipeline...")
        sync_result = sync_all_data()
        logger.info(f"✅ Sync completed: {sync_result}")
        
    except Exception as e:
        logger.warning(f"⚠️ External pipeline integration not available: {e}")
        integrator = None
        data_manager = None
    
    def save_analysis_session(session_id: str, status: str, duration_seconds: Optional[float] = None, results: Optional[Dict[str, Any]] = None):
        """Save analysis session to database"""
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insert analysis session
            cursor.execute('''
                INSERT OR REPLACE INTO enhanced_analysis_sessions (
                    session_id, timestamp, analysis_type, total_connections, leadership_engagement,
                    f500_penetration, unique_companies, unique_locations, unique_roles,
                    avg_connection_strength, data_source, profile_name, execution_time, cache_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, start_time.isoformat(), 'opportunity_detection', 0,
                0.0, 0.0, 0, 0, 0,
                0.0, 'job_search', 'user_profile_001', duration_seconds, False
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"💾 Analysis session {session_id} saved to database")
            
        except Exception as e:
            logger.error(f"❌ Failed to save analysis session: {e}")
    
    def generate_linkedin_search_url(keywords, location, work_type="2", time_posted="r604800"):
        """Generate LinkedIn job search URL
        Args:
            keywords: Job title/keywords (will be URL encoded)
            location: Location (will be URL encoded) 
            work_type: "1"=On-site, "2"=Remote, "3"=Hybrid, "1,2"=On-site+Remote, etc.
            time_posted: "r86400"=24h, "r604800"=Week, "r2592000"=Month
        """
        import urllib.parse
        keywords_encoded = urllib.parse.quote(keywords)
        location_encoded = urllib.parse.quote(location)
        return f"https://www.linkedin.com/jobs/search/?keywords={keywords_encoded}&location={location_encoded}&f_TPR={time_posted}&f_WT={work_type}"
    
    # Helper to persist weekly metrics from real network stats into tracking DB
    def _save_weekly_metrics_from_network_stats(network_stats: Dict[str, Any]) -> None:
        try:
            from src.tracking.weekly_metrics_collector import WeeklyMetricsCollector, WeeklyMetrics
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(f"WeeklyMetricsCollector unavailable; cannot save weekly metrics: {e}")
            return

        # Only save if data is from real API/wrapper, not static fallback
        data_source = (network_stats.get("data_source") or "").lower()
        if data_source not in {"linkedin_api_real", "linkedin_wrapper_connections"}:
            logger.info(f"Skipping weekly_metrics save for non-real data_source={data_source!r}")
            return

        # Parse basic fields from network_stats
        def _parse_pct(val: Any) -> float:
            try:
                s = str(val).strip()
                if s.endswith("%"):
                    s = s[:-1]
                return float(s)
            except Exception:
                return 0.0

        def _parse_score(val: Any) -> float:
            try:
                s = str(val)
                # e.g. "6.2/10" -> "6.2"
                if "/" in s:
                    s = s.split("/", 1)[0]
                return float(s)
            except Exception:
                return 0.0

        total_connections = int(network_stats.get("total_connections", 0) or 0)
        senior_connections = int(network_stats.get("senior_connections", 0) or 0)
        leadership_pct = _parse_pct(network_stats.get("leadership_engagement", 0))
        f500_pct = _parse_pct(network_stats.get("f500_penetration", 0))
        comment_quality = _parse_score(network_stats.get("engagement_quality", 0))

        # Determine current week
        current_date = datetime.now()
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=6)

        collector = WeeklyMetricsCollector(db_path=db_path)
        alert_status = collector._calculate_weekly_alert_status(  # type: ignore[attr-defined]
            leadership_pct, f500_pct, comment_quality
        )

        metrics = WeeklyMetrics(
            week_start_date=week_start.strftime("%Y-%m-%d"),
            week_end_date=week_end.strftime("%Y-%m-%d"),
            week_number=week_start.isocalendar()[1],
            year=week_start.year,
            leadership_engagement_count=0,
            total_engagement_count=0,
            leadership_engagement_percentage=leadership_pct,
            f500_profile_views=0,
            total_profile_views=0,
            f500_penetration_percentage=f500_pct,
            senior_connections_count=senior_connections,
            total_connections_count=total_connections,
            recruiter_messages_count=0,
            comment_quality_score=comment_quality,
            alert_status=alert_status,
            notes="metrics derived from real network snapshot",
        )

        try:
            collector.save_weekly_metrics(metrics)
        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"Failed to save weekly metrics from network stats: {e}")

    try:
        # Import intelligence scheduler components
        from scripts.intelligence_scheduler import IntelligenceConfig, IntelligenceReportOrganizer, TelegramNotifier
        
        # Import real network analytics - UPDATED TO USE REAL DATA
        try:
            sys.path.append(str(Path(parent_dir) / "src"))
            from src.intelligence.real_linkedin_data_collector import RealLinkedInDataCollector
            
            logger.info("🔍 Collecting real LinkedIn network intelligence...")
            
            # Use the new real data collector
            collector = RealLinkedInDataCollector()
            collector.set_force_refresh(True)  # ensure fresh data each run
            network_stats = await collector.collect_real_network_intelligence()
            
            logger.info(f"✅ Real network data collected: {network_stats['total_connections']} connections")
            
        except ImportError as import_error:
            logger.warning(f"Could not import real data collector: {import_error}")
            # Fallback to previous system
            try:
                from src.tracking.weekly_metrics_collector import WeeklyMetricsCollector
                from src.core.linkedin_analyzer import LinkedInAnalyzer, NetworkMetrics
                
                metrics_collector = WeeklyMetricsCollector(db_path='data/job_search.db')
                current_date = datetime.now()
                week_start = current_date - timedelta(days=current_date.weekday())
                week_start_str = week_start.strftime("%Y-%m-%d")
                
                current_week_metrics = metrics_collector.collect_weekly_metrics(week_start_str)
                network_stats = {
                    "total_connections": current_week_metrics.total_connections_count if current_week_metrics else 356,  # User's actual count
                    "leadership_engagement": f"{current_week_metrics.leadership_engagement_percentage:.1f}%" if current_week_metrics else "52.3%",
                    "f500_penetration": f"{current_week_metrics.f500_penetration_percentage:.1f}%" if current_week_metrics else "23.8%",
                    "senior_connections": current_week_metrics.senior_connections_count if current_week_metrics else 18,  # Proportional to 356
                    "network_growth": "+0.8 connections/day",
                    "engagement_quality": f"{current_week_metrics.comment_quality_score:.1f}/10" if current_week_metrics else "6.2/10"
                }
            except Exception as fallback_error:
                logger.warning(f"Fallback data collection also failed: {fallback_error}")
                # Final fallback with user's actual connection count
                network_stats = {
                    "total_connections": 356,  # User's actual LinkedIn connection count
                    "leadership_engagement": "52.3%",
                    "f500_penetration": "23.8%",
                    "senior_connections": 18,  # Proportional to 356 connections
                    "network_growth": "+0.8 connections/day",
                    "engagement_quality": "6.2/10"
                }
        except Exception as e:
            logger.error(f"Real data collection failed: {e}")
            # Final fallback with user's actual connection count
            network_stats = {
                "total_connections": 356,  # User's actual LinkedIn connection count
                "leadership_engagement": "52.3%",
                "f500_penetration": "23.8%",
                "senior_connections": 18,  # Proportional to 356 connections
                "network_growth": "+0.8 connections/day",
                "engagement_quality": "6.2/10"
            }
        
        # Initialize components
        config = IntelligenceConfig()
        organizer = IntelligenceReportOrganizer(config)
        telegram = TelegramNotifier(config)
        
        # Persist weekly metrics snapshot to tracking DB using real network stats
        try:
            _save_weekly_metrics_from_network_stats(network_stats)
        except Exception as e:
            logger.warning(f"Weekly metrics save skipped due to error: {e}")

        # Notify if we had to fall back instead of using real data
        try:
            data_source = (network_stats.get("data_source") or "").lower()
            if data_source not in {"linkedin_api_real", "linkedin_wrapper_connections"}:
                logger.warning(
                    "LinkedIn network data fallback in use (data_source=%r); "
                    "metrics not persisted to tracking DB.",
                    data_source,
                )
                if telegram and getattr(telegram, "enabled", False):
                    await telegram.send_message(
                        "⚠️ <b>LinkedIn data not available</b>\n\n"
                        "Today's opportunity detection used fallback network metrics. "
                        "No weekly tracking metrics were written to the database.",
                        parse_mode="HTML",
                    )
        except Exception as e:
            logger.warning(f"Failed to send fallback notification: {e}")

        # COLLECT REAL JOB OPPORTUNITIES - UPDATED TO USE REAL LINKEDIN JOBS
        logger.info("🔍 Collecting real job opportunities...")
        
        # Initialize opportunities list
        opportunities = []
        real_opportunities_found = False

        # Shared search parameters reused across fallback data providers
        base_search_criteria = {
            "job_titles": [
                "Senior Python Developer",
                "Data Scientist",
                "DevOps Engineer",
                "ML Engineer",
                "Product Manager"
            ],
            "locations": [
                "Remote",
                "San Francisco",
                "New York",
                "Seattle",
                "Austin",
                "Boston"
            ],
            "experience_level": "senior",
            "salary_min": 100000,
            "salary_max": 220000,
            "max_results": 10
        }

        # Override base_search_criteria using centralized job config when available
        if job_config is not None:
            try:
                search_titles = list(getattr(job_config, "SEARCH_TERMS", []))
                search_locations = list(getattr(job_config, "LOCATIONS", []))
                salary_ranges = getattr(job_config, "PREFERRED_SALARY_RANGES", {})
                cfg_salary_min = (
                    salary_ranges.get("minimum_acceptable")
                    or salary_ranges.get("target_range_min")
                    or None
                )
                cfg_salary_max = (
                    salary_ranges.get("target_range_max")
                    or salary_ranges.get("stretch_target")
                    or None
                )
                if search_titles:
                    base_search_criteria["job_titles"] = search_titles
                if search_locations:
                    base_search_criteria["locations"] = search_locations
                if cfg_salary_min is not None:
                    base_search_criteria["salary_min"] = cfg_salary_min
                if cfg_salary_max is not None:
                    base_search_criteria["salary_max"] = cfg_salary_max
            except Exception as config_error:
                logger.warning(
                    f"Failed to override search criteria from job_search_config: {config_error}"
                )
        
        # Try to get WORKING job board links that actually load
        try:
            # Import the working job link provider
            sys.path.append(str(Path(parent_dir) / "src" / "intelligence"))
            from working_job_link_provider import WorkingJobLinkProvider
            
            logger.info("🔍 Using WORKING job board links that actually load...")
            provider = WorkingJobLinkProvider()
            working_job_links = provider.get_working_job_links(8)
            
            logger.info(f"🔍 Job link provider returned {len(working_job_links)} working links")
            
            if working_job_links:
                logger.info(f"✅ Found {len(working_job_links)} WORKING job board links!")
                for job in working_job_links:
                    logger.info(f"   🌐 {job.title} at {job.company} ({job.match_score}% match)")
                    logger.info(f"      URL: {job.url[:60]}... | Source: {job.source}")
                    
                    opportunity = {
                        "id": f"working_job_{job.job_id}",
                        "title": job.title,
                        "company": job.company,
                        "url": job.url,
                        "location": job.location,
                        "salary": job.salary_range,
                        "posted_date": job.posted_date,
                        "posted": job.posted_date,  # For compatibility
                        "match_score": job.match_score,
                        "match": f"{job.match_score}%",  # For compatibility with existing code
                        "skills": job.skills,
                        "description": job.description_snippet,
                        "source": f"working_{job.source}",
                        "priority": "high" if job.match_score >= 90 else "medium",
                        "employment_type": job.employment_type,
                        "is_direct_apply": job.is_direct_apply,
                        "job_board": job.source
                    }
                    opportunities.append(opportunity)
                
                real_opportunities_found = True
                logger.info(f"🎯 Successfully processed {len(opportunities)} WORKING job board links")
            else:
                logger.warning("No working job links found from provider")
                
        except Exception as linkedin_scraper_error:
            logger.warning(f"LinkedIn job market analyzer failed: {linkedin_scraper_error}")
            
        # Fallback to market research scraper if no real LinkedIn jobs found
        if not real_opportunities_found:
            try:
                # Import and use the market research job scraper as fallback
                from simple_job_scraper import SimpleLinkedInJobScraper
                
                logger.info("🔄 Falling back to market research job scraper...")
                scraper = SimpleLinkedInJobScraper()
                market_search_criteria = dict(base_search_criteria)
                market_search_criteria["max_results"] = 8
                market_jobs = await scraper.get_real_job_opportunities(market_search_criteria)
                
                new_market_opportunities = []
                for job in market_jobs:
                    job_identifier = job.get("id") or job.get("job_id") or f"job_{len(opportunities) + len(new_market_opportunities)}"
                    raw_match = job.get("match")
                    match_score_value = job.get("match_score")
                    if match_score_value is None and isinstance(raw_match, str) and raw_match.endswith("%"):
                        try:
                            match_score_value = float(raw_match.rstrip("%"))
                        except ValueError:
                            match_score_value = 0.0
                    if isinstance(match_score_value, (int, float)):
                        if match_score_value <= 1:
                            match_score_value *= 100
                    else:
                        match_score_value = 0.0
                    match_display = raw_match or f"{int(match_score_value)}%"
                    priority = job.get("priority")
                    if not priority:
                        priority = "high" if match_score_value >= 85 else "medium" if match_score_value >= 60 else "low"
                    
                    new_market_opportunities.append({
                        "id": f"market_research_{job_identifier}",
                        "title": job.get("title", "Opportunity"),
                        "company": job.get("company", "Multiple Companies"),
                        "url": job.get("url", ""),
                        "location": job.get("location", "Remote"),
                        "salary": job.get("salary") or job.get("salary_range", "Not specified"),
                        "posted_date": job.get("posted_date", job.get("posted", "Recently")),
                        "posted": job.get("posted", job.get("posted_date", "Recently")),
                        "match_score": match_score_value,
                        "skills": job.get("skills") or job.get("skills_required", []),
                        "description": job.get("description") or job.get("description_snippet", ""),
                        "source": job.get("source", "market_research"),
                        "priority": priority,
                        "match": match_display
                    })
                
                opportunities.extend(new_market_opportunities)
                
                if new_market_opportunities:
                    real_opportunities_found = True
                    logger.info(f"✅ Found {len(new_market_opportunities)} market research opportunities as fallback")
                    
            except Exception as market_scraper_error:
                logger.warning(f"Market research scraper also failed: {market_scraper_error}")
            # Continue to fallback methods...
        
        # ENHANCED JOBSPY INTEGRATION - GET REAL JOB OPPORTUNITIES
        if not real_opportunities_found:
            logger.info("🚀 Using Enhanced JobSpy Integration for real job opportunities...")
            try:
                # Import enhanced JobSpy integration
                sys.path.append(str(Path(parent_dir) / "scripts"))
                
                # Ensure config is available
                config_path = Path(parent_dir) / "config"
                if config_path.exists():
                    sys.path.insert(0, str(parent_dir))
                
                from enhanced_jobspy_integration import get_enhanced_job_opportunities_sync
                
                logger.info("🔍 Fetching real job opportunities with enhanced JobSpy...")
                
                # Get real job opportunities using centralized configuration
                jobspy_opportunities = get_enhanced_job_opportunities_sync(max_jobs=25)
                
                # Debug logging
                logger.info(f"📊 Enhanced JobSpy returned {len(jobspy_opportunities) if jobspy_opportunities else 0} opportunities")
                if jobspy_opportunities:
                    logger.info(f"🔍 First opportunity: {jobspy_opportunities[0].get('title', 'Unknown')} at {jobspy_opportunities[0].get('company', 'Unknown')}")
                    
                    # Process the opportunities
                    logger.info(f"✅ Retrieved {len(jobspy_opportunities)} real job opportunities from JobSpy")
                    
                    opportunities = []  # Reset opportunities list
                    
                    # Convert JobSpy opportunities to our format
                    for job in jobspy_opportunities:
                        # Determine priority based on match score
                        match_score = job.get("match_score", 0.0)
                        if match_score >= 0.85:
                            priority = "high"
                        elif match_score >= 0.7:
                            priority = "medium"
                        else:
                            priority = "low"
                        
                        # Format salary display
                        salary_min = job.get("salary_min", 0)
                        salary_max = job.get("salary_max", 0)
                        if salary_min and salary_max:
                            salary_display = f"${salary_min:,} - ${salary_max:,}"
                        elif salary_min:
                            salary_display = f"${salary_min:,}+"
                        elif salary_max:
                            salary_display = f"Up to ${salary_max:,}"
                        else:
                            salary_display = "Salary not specified"
                        
                        opportunities.append({
                            "title": job.get("title", "Software Engineer"),
                            "company": job.get("company", "Unknown Company"),
                            "location": job.get("location", "Remote"),
                            "salary": salary_display,
                            "match": job.get("match_percentage", "0%"),
                            "priority": priority,
                            "posted": job.get("posted_date", datetime.now().strftime("%Y-%m-%d")),
                            "url": job.get("job_url", ""),
                            "source": f"jobspy_{job.get('source', 'unknown')}",
                            "description": job.get("description", "")[:200] + "..." if job.get("description") else "",
                            "search_term": job.get("search_term", ""),
                            "match_score": match_score
                        })
                    
                    real_opportunities_found = True
                    logger.info("✅ Enhanced JobSpy integration successful - using real job data")
                    
                else:
                    logger.warning("⚠️ No opportunities returned from enhanced JobSpy")
                
            except Exception as jobspy_error:
                logger.error(f"❌ Enhanced JobSpy integration failed: {jobspy_error}")
                logger.info("🔄 Trying simple JobSpy integration as backup...")
                
                try:
                    from simple_jobspy_integration import get_simple_job_opportunities
                    jobspy_opportunities = get_simple_job_opportunities(max_jobs=25)
                    
                    if jobspy_opportunities:
                        logger.info(f"✅ Simple JobSpy found {len(jobspy_opportunities)} opportunities")
                        
                        # Process simple JobSpy opportunities
                        opportunities = []  # Reset opportunities list
                        for job in jobspy_opportunities:
                            match_score = job.get("match_score", 0.5)
                            priority = "high" if match_score > 0.8 else "medium" if match_score > 0.6 else "low"
                            
                            # Format salary
                            salary_min = job.get("salary_min")
                            salary_max = job.get("salary_max")
                            
                            if salary_min and salary_max:
                                salary_display = f"${salary_min:,} - ${salary_max:,}"
                            elif salary_min:
                                salary_display = f"${salary_min:,}+"
                            elif salary_max:
                                salary_display = f"Up to ${salary_max:,}"
                            else:
                                salary_display = "Salary not specified"
                            
                            opportunities.append({
                                "title": job.get("title", "Software Engineer"),
                                "company": job.get("company", "Unknown Company"),
                                "location": job.get("location", "Remote"),
                                "salary": salary_display,
                                "match": job.get("match_percentage", "0%"),
                                "priority": priority,
                                "posted": job.get("posted_date", datetime.now().strftime("%Y-%m-%d")),
                                "url": job.get("job_url", ""),
                                "source": f"jobspy_{job.get('source', 'unknown')}",
                                "description": job.get("description", "")[:200] + "..." if job.get("description") else "",
                                "search_term": job.get("search_term", ""),
                                "match_score": match_score
                            })
                        
                        real_opportunities_found = True
                        logger.info("✅ Simple JobSpy integration successful - using real job data")
                    else:
                        logger.warning("⚠️ Simple JobSpy returned no opportunities")
                        
                except Exception as simple_error:
                    logger.error(f"❌ Simple JobSpy integration also failed: {simple_error}")
                    logger.info("🔄 Falling back to external pipeline...")
        
        # Fallback to external pipeline if JobSpy didn't work
        if not real_opportunities_found:
            logger.info("📊 Trying external job pipeline...")
            if not opportunities:  # Only reset if not already set by JobSpy
                opportunities = []
            
            # Get additional opportunities from external pipeline
            if integrator and data_manager:
                try:
                    logger.info("🔍 Fetching opportunities from external job pipeline...")
                    
                    # Define search criteria for external pipeline
                    search_criteria = dict(base_search_criteria)
                    
                    # Share search criteria with external pipeline
                    data_manager.share_search_configuration(search_criteria)
                    
                    # Get opportunities from external pipeline
                    external_opportunities = integrator.get_external_opportunities(search_criteria)
                    
                    if external_opportunities:
                        logger.info(f"✅ Retrieved {len(external_opportunities)} opportunities from external pipeline")
                        
                        # Convert external opportunities to our format and fix fake URLs
                        for ext_opp in external_opportunities[:5]:  # Limit to top 5
                            title = getattr(ext_opp, 'title', 'Unknown Position')
                            location = getattr(ext_opp, 'location', 'Unknown Location')
                            ext_url = getattr(ext_opp, 'url', '')
                            
                            # If URL contains fake domains, replace with informative search guidance
                            if 'example.com' in ext_url or 'external-integration' in ext_url or not ext_url:
                                # Instead of generating misleading search URLs, provide guidance
                                search_guidance = f"Search LinkedIn Jobs for '{title}' in {location}"
                                real_url = f"https://www.linkedin.com/jobs/search/?keywords={title.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
                                logger.info(f" Providing job search guidance: {title}")
                                url_source = "job_search_guidance"
                            else:
                                real_url = ext_url
                                url_source = "external_pipeline"
                            
                            opportunities.append({
                                "title": title,
                                "company": getattr(ext_opp, 'company', 'Multiple Companies'),
                                "location": location,
                                "salary": getattr(ext_opp, 'salary_range', 'Not specified'),
                                "match": f"{int(getattr(ext_opp, 'match_score', 0.75) * 100)}%",
                                "priority": "high" if getattr(ext_opp, 'match_score', 0.75) >= 0.85 else "medium",
                                "posted": getattr(ext_opp, 'posted_date', 'Recently'),
                                "url": real_url,
                                "source": url_source
                            })
                        
                        real_opportunities_found = True
                        
                except Exception as ext_error:
                    logger.warning(f"External pipeline also failed: {ext_error}")
            
            # Final fallback to LinkedIn search suggestions if nothing else works
            if not real_opportunities_found:
                logger.warning("⚠️  No real job data available - providing intelligent search suggestions")
                opportunities = [
                    {
                        "title": "Senior Python Developer", 
                        "priority": "medium", 
                        "match": "0%",  # More honest about match since we don't have real data
                        "company": "Multiple Companies",
                        "location": "Remote",
                        "salary": "$100,000 - $130,000",
                        "url": generate_linkedin_search_url("Senior Python Developer", "Remote", "2"),
                        "posted": datetime.now().isoformat(),
                        "source": "job_search_guidance"
                    },
                    {
                        "title": "Data Engineer", 
                        "priority": "medium", 
                        "match": "0%",  # More honest about match since we don't have real data
                        "company": "Multiple Companies",
                        "location": "New York, NY",
                        "salary": "$85,000 - $115,000",
                        "url": generate_linkedin_search_url("Data Engineer", "New York, NY", "2"),
                        "posted": datetime.now().isoformat(),
                        "source": "job_search_guidance"
                    }
                ]
        
        logger.info(f"📊 Opportunity collection complete: {len(opportunities)} opportunities found")
        logger.info(f"   Source: {'Real data' if real_opportunities_found else 'Fallback searches'}")
        
        # Log opportunity sources for transparency
        for i, opp in enumerate(opportunities[:3], 1):
            logger.info(f"   {i}. {opp['title']} - {opp.get('source', 'unknown')} source")
        
        # Sort opportunities by priority and match score
        priority_order = {"high": 3, "medium": 2, "low": 1}
        opportunities.sort(key=lambda x: (priority_order.get(x['priority'], 0), float(x['match'].replace('%', ''))), reverse=True)
        
        # Generate enhanced report with job links
        now = datetime.now()

        top_companies = network_stats.get('top_companies') or []
        industry_mix = network_stats.get('industry_mix') or []
        skill_highlights = network_stats.get('skill_highlights') or []
        seniority_distribution = network_stats.get('seniority_distribution') or {}
        remote_percentage = network_stats.get('remote_percentage', 'N/A')

        def _format_ranked_entries(entries, max_items=5):
            if not isinstance(entries, list) or not entries:
                return ["- _No data available yet._"]
            lines = []
            for entry in entries[:max_items]:
                name = entry.get('company') or entry.get('industry') or entry.get('skill') or 'Unknown'
                count = entry.get('count')
                percentage = entry.get('percentage')
                if count is not None and percentage:
                    lines.append(f"- **{name}** — {count} ({percentage})")
                elif percentage:
                    lines.append(f"- **{name}** — {percentage}")
                elif count is not None:
                    lines.append(f"- **{name}** — {count}")
                else:
                    lines.append(f"- **{name}**")
            return lines or ["- _No data available yet._"]

        def _format_seniority(dist):
            if not isinstance(dist, dict) or not dist:
                return ["- _No data available yet._"]
            label_map = {
                'c_level': 'C-Level',
                'founder_partner': 'Founder/Partner',
                'vp': 'VP',
                'director': 'Director',
                'manager': 'Manager/Lead',
                'senior_ic': 'Senior IC',
                'other': 'Other'
            }
            lines = []
            for key in ['c_level', 'founder_partner', 'vp', 'director', 'manager', 'senior_ic', 'other']:
                value = dist.get(key)
                if value:
                    lines.append(f"- **{label_map.get(key, key.title())}:** {value}")
            return lines or ["- _No data available yet._"]

        top_companies_section = "\n".join(_format_ranked_entries(top_companies))
        industry_mix_section = "\n".join(_format_ranked_entries(industry_mix))
        skill_highlights_section = "\n".join(_format_ranked_entries(skill_highlights))
        seniority_section = "\n".join(_format_seniority(seniority_distribution))

        def _format_summary(entries, max_items=3):
            if not isinstance(entries, list) or not entries:
                return 'n/a'
            parts = []
            for entry in entries[:max_items]:
                name = entry.get('company') or entry.get('industry') or entry.get('skill') or 'Unknown'
                percentage = entry.get('percentage')
                count = entry.get('count')
                if percentage:
                    parts.append(f"{name} ({percentage})")
                elif count is not None:
                    parts.append(f"{name} ({count})")
                else:
                    parts.append(name)
            return ', '.join(parts)

        top_companies_summary = _format_summary(top_companies)
        industry_summary = _format_summary(industry_mix)
        skill_summary = _format_summary(skill_highlights)

        
        # Helper function to format opportunity with real job links
        def format_opportunity_md(opp):
            """Format an opportunity entry for Markdown output."""
            title = opp.get('title', 'Opportunity')
            url = opp.get('url', '')
            match = opp.get('match', 'N/A')
            company = opp.get('company', 'Unknown')
            location = opp.get('location', 'N/A')
            salary = opp.get('salary', 'N/A')
            posted = opp.get('posted_date') or opp.get('posted', 'Recently')
            source = opp.get('source', 'unknown')
            skills = opp.get('skills') or []

            link = f"[{title}]({url})" if url else title
            lines = [f"- **{link}** (Match: {match})"]

            details = [
                f"Company: {company}",
                f"Location: {location}",
                f"Salary: {salary}",
                f"Posted: {posted}",
            ]

            if source.startswith('working_'):
                details.append(f"Source: Working job board ({source.split('_', 1)[-1].title()})")
            elif source == 'job_search_guidance':
                details.append("Source: LinkedIn search suggestion")
            elif source and source != 'unknown':
                details.append(f"Source: {source.replace('_', ' ').title()}")

            if skills:
                details.append(f"Skills: {', '.join(skills[:4])}")

            lines.append("  - " + " | ".join(details))
            return "\n".join(lines)

        def format_opportunity_text(opp):
            """Format opportunity for console output."""
            title = opp.get('title', 'Opportunity')
            match = opp.get('match', 'N/A')
            url = opp.get('url', '')
            location = opp.get('location', 'N/A')
            salary = opp.get('salary', 'N/A')
            posted = opp.get('posted_date') or opp.get('posted', 'Recently')
            return (
                f"* {title} ({match} match)\n"
                f"  URL: {url}\n"
                f"  Location: {location} | Salary: {salary} | Posted: {posted}"
            )

        report_content = f"""# Daily Opportunity Detection Report
**Date:** {now.strftime('%Y-%m-%d %H:%M')}
**Task:** Windows Scheduled Task

## Opportunity Summary
- **Total Opportunities:** {len(opportunities)}
- **High Priority:** {len([o for o in opportunities if o['priority'] == 'high'])}
- **Medium Priority:** {len([o for o in opportunities if o['priority'] == 'medium'])}
- **Low Priority:** {len([o for o in opportunities if o['priority'] == 'low'])}

## Network Intelligence
- **Total Connections:** {network_stats['total_connections']}
- **Leadership Engagement:** {network_stats['leadership_engagement']}
- **Fortune 500 Penetration:** {network_stats['f500_penetration']}
- **Senior Connections:** {network_stats['senior_connections']}
- **Network Growth:** {network_stats['network_growth']}
- **Engagement Quality:** {network_stats['engagement_quality']}

## Expanded Network Insights
### Top Companies Influencing Your Network
{top_companies_section}

### Focus Industries
{industry_mix_section}

### Skill Highlights
{skill_highlights_section}

### Seniority Distribution
{seniority_section}

- **Remote-friendly signals:** {remote_percentage}

## Opportunity Details

{f"*Working job board links are marked with (Working). Company career pages are marked with (Company). LinkedIn search suggestions are marked with (Search).*" if any(o.get('source', '').startswith('working_') for o in opportunities) else "*Note: Opportunities marked with (Search) are intelligent job search suggestions. Click the links to search LinkedIn for similar positions matching your profile.*"}

### High Priority Opportunities
{chr(10).join([format_opportunity_md(o) for o in opportunities if o['priority'] == 'high'])}

### Medium Priority Opportunities
{chr(10).join([format_opportunity_md(o) for o in opportunities if o['priority'] == 'medium'])}

### Low Priority Opportunities
{chr(10).join([format_opportunity_md(o) for o in opportunities if o['priority'] == 'low'])}

## Strategic Recommendations
- Review search suggestions and browse specific job postings
- Leverage network of {network_stats['total_connections']} connections
- Focus on leadership engagement (current: {network_stats['leadership_engagement']})
- Target Fortune 500 companies (current penetration: {network_stats['f500_penetration']})
- **Use the search links above to find specific job postings that match your skills**

## Next Steps
- **Click the (Search) links to browse current job openings**
- Schedule follow-up applications for specific positions found
- Network with {network_stats['senior_connections']} senior contacts
- Update profile with trending skills
- Monitor market trends and maintain {network_stats['engagement_quality']} quality

---
*Generated by Windows Scheduled Task - Opportunity Detection*
*Next scan: Tomorrow 6:00 AM*
"""
        
        # Save report
        report_path = organizer.save_report(
            report_content,
            "opportunity_detection",
            "daily"
        )
        
        # Send enhanced Telegram notification with job links
        high_priority_jobs = [o for o in opportunities if o['priority'] == 'high']
        featured_jobs = high_priority_jobs[:2] if high_priority_jobs else opportunities[:2]

        def _format_featured_jobs_for_message(jobs):
            if not jobs:
                return "- No opportunities available right now."
            lines = []
            for job in jobs:
                title = html.escape(job.get('title', 'Opportunity'))
                url = job.get('url') or ''
                match = html.escape(job.get('match', 'N/A'))
                location = html.escape(job.get('location', 'N/A'))
                salary = html.escape(job.get('salary', 'N/A'))
                if url:
                    link = f"<a href='{html.escape(url, quote=True)}'>{title}</a>"
                else:
                    link = title
                lines.append(f"- {link} - {match} match<br/>&nbsp;&nbsp;{location} | {salary}")
            return "\n".join(lines)

        featured_jobs_text = _format_featured_jobs_for_message(featured_jobs)

        message_lines = [
            "<b>Daily Opportunity Detection Complete</b>",
            f"&#8226; {len(opportunities)} opportunities found",
            f"&#8226; {len(high_priority_jobs)} high-priority matches",
            f"Report: <code>{html.escape(report_path.name)}</code>",
            "",
            "<b>Network Snapshot</b>",
            f"Connections: {network_stats['total_connections']}",
            f"Leadership engagement: {network_stats['leadership_engagement']}",
            f"Fortune 500 penetration: {network_stats['f500_penetration']}",
            f"Senior contacts: {network_stats['senior_connections']}",
            f"Quality score: {network_stats['engagement_quality']}",
            f"Remote signals: {remote_percentage}",
            "",
            f"Top companies: {html.escape(top_companies_summary)}",
            f"Focus industries: {html.escape(industry_summary)}",
            f"Skill highlights: {html.escape(skill_summary)}",
            "",
            "<b>Featured Roles</b>",
            featured_jobs_text,
            "",
            "<i>Next scan: Tomorrow 6:00 AM</i>",
        ]
        message_text = "\n".join([line for line in message_lines if line])
        await telegram.send_message(message_text.strip())

        if report_path.exists():
            await telegram.send_document(
                str(report_path),
                f"Daily Opportunity Detection Report — {len(opportunities)} opps, {len(high_priority_jobs)} high-priority"
            )

        logger.info(f"✅ Opportunity detection completed successfully. Report: {report_path}")
        
        # Save analysis results to database
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        analysis_results = {
            'session_id': session_id,
            'opportunities_found': len(opportunities),
            'high_priority_count': len([o for o in opportunities if o['priority'] == 'high']),
            'medium_priority_count': len([o for o in opportunities if o['priority'] == 'medium']),
            'low_priority_count': len([o for o in opportunities if o['priority'] == 'low']),
            'opportunities_list': opportunities,
            'network_stats': network_stats,
            'report_path': str(report_path),
            'summary': f"Found {len(opportunities)} opportunities with {len([o for o in opportunities if o['priority'] == 'high'])} high priority matches",
            'insights': [
                f"Leadership engagement at {network_stats['leadership_engagement']}",
                f"Fortune 500 penetration: {network_stats['f500_penetration']}",
                f"Network quality score: {network_stats['engagement_quality']}",
                f"Top match: {opportunities[0]['title']} ({opportunities[0]['match']})" if opportunities else "No opportunities found"
            ],
            'recommendations': [
                "Review high-priority opportunities first",
                f"Leverage network of {network_stats['total_connections']} connections",
                f"Focus on leadership engagement improvement",
                "Apply to top 3 matches today"
            ],
            'execution_time': duration,
            'timestamp': end_time.isoformat()
        }
        
        save_analysis_session(session_id, 'completed', duration, analysis_results)
        
        # Display opportunities with URLs in console
        print(f"Task completed successfully. Report saved to: {report_path}")
        print("\nTop Opportunities Found:")
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"{i}. {opp['title']} ({opp['match']} match)")
            print(f"   🔗 {opp['url']}")
            print(f"   📍 {opp['location']} | 💰 {opp['salary']} | 📅 {opp['posted']}")
            print()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Opportunity detection failed: {e}")
        print(f"❌ Task failed: {e}")
        
        # Save failed analysis session
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        error_results = {
            'session_id': session_id,
            'error': str(e),
            'error_type': type(e).__name__,
            'execution_time': duration,
            'timestamp': end_time.isoformat(),
            'summary': f"Analysis failed: {str(e)}"
        }
        
        save_analysis_session(session_id, 'failed', duration, error_results)
        
        # Try to send error notification
        try:
            from scripts.intelligence_scheduler import TelegramNotifier, IntelligenceConfig
            config = IntelligenceConfig()
            telegram = TelegramNotifier(config)
            error_time = datetime.now()
            await telegram.send_message(f"""
❌ <b>Opportunity Detection Failed</b>

<b>Error:</b> {str(e)}
<b>Time:</b> {error_time.strftime('%Y-%m-%d %H:%M')}

🔧 Check logs for details: opportunity_detection.log
            """)
        except:
            pass
        
        return False

def main():
    """Main function for Windows Task Scheduler"""
    print("Daily Opportunity Detection Task")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        success = asyncio.run(run_opportunity_detection())
        
        if success:
            print("\n🎉 Task completed successfully!")
            exit_code = 0
        else:
            print("\n❌ Task failed!")
            exit_code = 1
            
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        logger.error(f"Critical error in opportunity detection task: {e}")
        exit_code = 1
    
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
