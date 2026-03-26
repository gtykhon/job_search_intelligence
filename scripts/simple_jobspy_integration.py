#!/usr/bin/env python3
"""
Simple JobSpy Integration for Scheduled Tasks
Standalone version that doesn't require external config files
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

# Setup logging
logger = logging.getLogger(__name__)

def get_simple_job_opportunities(max_jobs: int = 25) -> List[Dict[str, Any]]:
    """
    Simple JobSpy integration for scheduled tasks without external dependencies
    
    Args:
        max_jobs: Maximum number of jobs to return
        
    Returns:
        List of real job opportunities
    """
    try:
        # Import jobspy
        try:
            import jobspy
        except ImportError:
            logger.error("❌ JobSpy not installed. Run: pip install python-jobspy")
            return []
        
        logger.info("🔍 Searching for job opportunities with JobSpy...")
        
        # Simple search queries for data/python roles
        search_queries = [
            {"term": "Senior Python Developer", "location": "Remote"},
            {"term": "Data Engineer", "location": "Remote"},
            {"term": "Software Engineer Python", "location": "Remote"},
            {"term": "Backend Developer Python", "location": "Remote"},
            {"term": "ETL Developer", "location": "Remote"}
        ]
        
        all_opportunities = []
        
        for i, query in enumerate(search_queries):
            if len(all_opportunities) >= max_jobs:
                break
                
            try:
                logger.info(f"🔍 Searching for '{query['term']}' in '{query['location']}' (Query {i+1}/{len(search_queries)})")
                
                # Execute JobSpy search
                jobs_df = jobspy.scrape_jobs(
                    search_term=query["term"],
                    location=query["location"],
                    results_wanted=min(10, max_jobs - len(all_opportunities)),
                    hours_old=168,  # 1 week
                    country_indeed="USA",
                    site_name=["linkedin", "indeed"],  # Exclude glassdoor
                    is_remote=True,
                    job_type="fulltime",
                    verbose=0
                )
                
                if jobs_df is not None and not jobs_df.empty:
                    logger.info(f"✅ Found {len(jobs_df)} jobs for '{query['term']}'")
                    
                    # Convert to our format
                    for _, row in jobs_df.iterrows():
                        try:
                            # Handle salary conversion with NaN checking
                            salary_min = None
                            salary_max = None
                            
                            if hasattr(row, 'min_amount') and pd.notna(row.min_amount):
                                try:
                                    salary_min = int(float(row.min_amount))
                                except (ValueError, TypeError):
                                    pass
                                    
                            if hasattr(row, 'max_amount') and pd.notna(row.max_amount):
                                try:
                                    salary_max = int(float(row.max_amount))
                                except (ValueError, TypeError):
                                    pass
                            
                            # Calculate basic match score
                            score = 0.5  # Base score
                            title = str(row.title).lower() if hasattr(row, 'title') else ""
                            description = str(row.description).lower() if hasattr(row, 'description') else ""
                            
                            # Basic scoring
                            python_skills = ["python", "sql", "pandas", "numpy", "etl", "data"]
                            skills_found = sum(1 for skill in python_skills if skill in title or skill in description)
                            score += (skills_found / len(python_skills)) * 0.4
                            
                            # Remote boost
                            location = str(row.location).lower() if hasattr(row, 'location') else ""
                            if "remote" in location:
                                score += 0.1
                            
                            # Senior level boost
                            if any(level in title for level in ["senior", "lead", "principal"]):
                                score += 0.1
                                
                            score = min(score, 1.0)  # Cap at 1.0
                            
                            opportunity = {
                                "title": str(row.title) if hasattr(row, 'title') else "Software Engineer",
                                "company": str(row.company) if hasattr(row, 'company') else "Unknown Company",
                                "location": str(row.location) if hasattr(row, 'location') else "Remote",
                                "job_url": str(row.job_url) if hasattr(row, 'job_url') else "",
                                "description": str(row.description) if hasattr(row, 'description') else "",
                                "posted_date": str(row.date_posted) if hasattr(row, 'date_posted') else str(datetime.now().date()),
                                "salary_min": salary_min,
                                "salary_max": salary_max,
                                "source": str(row.site) if hasattr(row, 'site') else "jobspy",
                                "search_term": query["term"],
                                "timestamp": datetime.now().isoformat(),
                                "match_score": score,
                                "match_percentage": f"{score * 100:.1f}%"
                            }
                            
                            # Skip if no URL
                            if not opportunity["job_url"] or opportunity["job_url"] == "nan":
                                continue
                                
                            all_opportunities.append(opportunity)
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Error processing job row: {e}")
                            continue
                            
                else:
                    logger.warning(f"⚠️ No jobs found for '{query['term']}'")
                    
            except Exception as e:
                logger.error(f"❌ Error searching for '{query['term']}': {e}")
                continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_opportunities = []
        for opp in all_opportunities:
            if opp["job_url"] not in seen_urls:
                seen_urls.add(opp["job_url"])
                unique_opportunities.append(opp)
        
        # Sort by match score
        unique_opportunities.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Limit results
        final_opportunities = unique_opportunities[:max_jobs]
        
        logger.info(f"✅ Collected {len(final_opportunities)} unique job opportunities")
        return final_opportunities
        
    except Exception as e:
        logger.error(f"❌ Error in simple JobSpy integration: {e}")
        return []

if __name__ == "__main__":
    # Test the simple integration
    print("🔍 Testing Simple JobSpy Integration")
    jobs = get_simple_job_opportunities(10)
    
    if jobs:
        print(f"✅ Found {len(jobs)} job opportunities:")
        for i, job in enumerate(jobs[:3], 1):
            print(f"\n{i}. {job['title']} at {job['company']}")
            print(f"   📍 {job['location']}")
            if job['salary_min'] and job['salary_max']:
                print(f"   💰 ${job['salary_min']:,} - ${job['salary_max']:,}")
            print(f"   🎯 Match: {job['match_percentage']}")
            print(f"   🔗 {job['job_url'][:80]}...")
    else:
        print("❌ No jobs found")