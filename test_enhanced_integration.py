#!/usr/bin/env python3
"""Test the enhanced JobSpy integration"""

import asyncio
import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.enhanced_jobspy_integration import EnhancedJobSpyIntegration

async def main():
    """Test the enhanced JobSpy integration"""
    print("🚀 Testing Enhanced JobSpy Integration...")
    
    try:
        integration = EnhancedJobSpyIntegration()
        
        # Test with limited jobs
        print("📋 Searching for job opportunities...")
        opportunities = await integration.get_real_job_opportunities(max_jobs=15)
        
        print(f"✅ Found {len(opportunities)} job opportunities")
        
        if opportunities:
            df = pd.DataFrame(opportunities)
            print(f"📊 Columns: {list(df.columns)}")
            
            # Show top 3 opportunities
            top_jobs = df.head(3)
            for i, job in top_jobs.iterrows():
                print(f"\n🎯 Job #{i+1}:")
                print(f"   Title: {job.title}")
                print(f"   Company: {job.company}")
                print(f"   Location: {job.location}")
                print(f"   Salary: ${job.salary_min:,.0f} - ${job.salary_max:,.0f}" if pd.notna(job.salary_min) and pd.notna(job.salary_max) else "Salary: Not specified")
                print(f"   Score: {job.match_score*100:.1f}/100")
                print(f"   URL: {job.job_url[:80]}...")
            
            # Show statistics
            valid_salaries = df[df.salary_min.notna() & df.salary_max.notna()]
            print(f"\n📈 Statistics:")
            print(f"   Jobs with salary info: {len(valid_salaries)}/{len(df)} ({len(valid_salaries)/len(df)*100:.1f}%)")
            
            if len(valid_salaries) > 0:
                print(f"   Salary range: ${valid_salaries.salary_min.min():,.0f} - ${valid_salaries.salary_max.max():,.0f}")
                print(f"   Average min salary: ${valid_salaries.salary_min.mean():,.0f}")
                print(f"   Average max salary: ${valid_salaries.salary_max.mean():,.0f}")
            
            # Show scoring distribution
            print(f"   Average score: {df.match_score.mean()*100:.1f}/100")
            print(f"   Top score: {df.match_score.max()*100:.1f}/100")
            
        else:
            print("❌ No opportunities found")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())