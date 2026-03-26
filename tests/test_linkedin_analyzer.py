#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'intelligence'))

from linkedin_job_market_analyzer import LinkedInJobMarketAnalyzer

def test_linkedin_analyzer():
    analyzer = LinkedInJobMarketAnalyzer()
    jobs = analyzer.search_real_linkedin_jobs(5)
    
    print(f"Found {len(jobs)} LinkedIn jobs:")
    for job in jobs:
        print(f"📋 {job.title} at {job.company}")
        print(f"   🔗 {job.url}")
        print(f"   📊 Match: {job.match_score}%")
        print()

if __name__ == "__main__":
    test_linkedin_analyzer()