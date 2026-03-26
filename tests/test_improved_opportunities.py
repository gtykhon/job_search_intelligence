#!/usr/bin/env python3
"""
Test the improved opportunity formatting
"""

import sys
import os
from datetime import datetime

# Mock opportunity data that simulates what the system generates
opportunities = [
    {
        "title": "Senior Python Developer",
        "company": "Multiple Companies", 
        "location": "Remote",
        "salary": "$100,000 - $130,000",
        "match": "0%",
        "priority": "medium",
        "posted": "2025-10-11 06:00:47.320893",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Senior%20Python%20Developer&location=Remote",
        "source": "job_search_guidance"
    },
    {
        "title": "Data Engineer", 
        "company": "Multiple Companies",
        "location": "New York, NY",
        "salary": "$85,000 - $115,000", 
        "match": "0%",
        "priority": "medium",
        "posted": "2025-10-11 06:00:47.321029",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Data%20Engineer&location=New%20York%2C%20NY",
        "source": "job_search_guidance"
    }
]

def format_opportunity_md(opp):
    """Improved formatting function"""
    # Add context for search-based opportunities
    if opp.get('source') == 'job_search_guidance':
        link_text = f"🔍 Search: {opp['title']}"
        description = f"  - 📍 {opp['location']} | 💰 {opp['salary']} | 📅 {opp['posted']}\n  - 🔗 *Click to search LinkedIn for similar positions*"
    else:
        link_text = opp['title']
        description = f"  - 📍 {opp['location']} | 💰 {opp['salary']} | 📅 {opp['posted']}"
    
    return f"- **[{link_text}]({opp['url']})** (Match: {opp['match']})\n{description}"

print("🔍 Improved Opportunity Report Format")
print("=" * 50)

print("\n## 📊 Detected Opportunities")
print("\n*Note: Opportunities marked with 🔍 are intelligent job search suggestions. Click the links to search LinkedIn for similar positions matching your profile.*")

print("\n### Medium Priority Opportunities")
for opp in opportunities:
    if opp['priority'] == 'medium':
        print(format_opportunity_md(opp))
        print()

print("=" * 50)
print("✅ This format clearly indicates these are search suggestions, not specific job postings!")