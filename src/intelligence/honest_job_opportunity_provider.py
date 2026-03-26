"""
Honest Job Opportunity Provider
Provides transparent job search recommendations without fake URLs
"""

import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class JobOpportunityRecommendation:
    """Honest job opportunity recommendation"""
    rec_id: str
    recommendation_type: str  # 'linkedin_company_search', 'indeed_search', 'direct_company'
    title: str
    target_company: str
    location: str
    search_url: str
    company_career_url: Optional[str]
    salary_estimate: str
    why_recommended: str
    match_score: int
    required_skills: List[str]
    next_steps: str

class HonestJobOpportunityProvider:
    """Provides honest, actionable job search recommendations"""
    
    def __init__(self):
        # Real company career page URLs
        self.company_career_pages = {
            'Microsoft': 'https://careers.microsoft.com/us/en/search-results?keywords=python',
            'Google': 'https://www.google.com/about/careers/applications/jobs/results/?q=python',
            'Amazon': 'https://www.amazon.jobs/en/search?base_query=python&loc_query=',
            'Meta': 'https://www.metacareers.com/jobs?q=python',
            'Apple': 'https://jobs.apple.com/en-us/search?search=python',
            'Netflix': 'https://jobs.netflix.com/search?q=python',
            'Stripe': 'https://stripe.com/jobs/search?query=python',
            'Databricks': 'https://www.databricks.com/company/careers/open-positions?department=Engineering&location=all',
            'OpenAI': 'https://openai.com/careers/search?query=engineer',
            'Anthropic': 'https://www.anthropic.com/careers#open-roles'
        }

    def get_honest_job_recommendations(self, limit: int = 8) -> List[JobOpportunityRecommendation]:
        """Get honest, transparent job recommendations with multiple search strategies"""
        try:
            logger.info("🎯 Creating honest job recommendations...")
            
            recommendations = []
            
            # Strategy 1: Direct company career pages (most reliable)
            company_recs = self._get_company_career_recommendations(limit // 3)
            recommendations.extend(company_recs)
            
            # Strategy 2: LinkedIn company-specific searches
            linkedin_recs = self._get_linkedin_company_searches(limit // 3)
            recommendations.extend(linkedin_recs)
            
            # Strategy 3: Indeed + Glassdoor targeted searches
            job_board_recs = self._get_job_board_recommendations(limit // 3)
            recommendations.extend(job_board_recs)
            
            # Sort by match score
            recommendations.sort(key=lambda x: x.match_score, reverse=True)
            
            logger.info(f"✅ Created {len(recommendations)} honest job recommendations")
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error creating recommendations: {e}")
            return []

    def _get_company_career_recommendations(self, limit: int) -> List[JobOpportunityRecommendation]:
        """Recommend applying directly on company career pages"""
        recommendations = []
        
        top_companies = [
            ('Microsoft', 'Redmond, WA', '$150,000 - $220,000', 95),
            ('Google', 'Mountain View, CA', '$160,000 - $240,000', 94),
            ('Amazon', 'Seattle, WA', '$140,000 - $200,000', 92),
            ('Meta', 'Menlo Park, CA', '$160,000 - $250,000', 91),
            ('Netflix', 'Los Gatos, CA', '$180,000 - $300,000', 90),
            ('Stripe', 'San Francisco, CA', '$150,000 - $230,000', 89)
        ]
        
        for company, location, salary, score in top_companies[:limit]:
            career_url = self.company_career_pages.get(company, f'https://www.google.com/search?q={company}+careers+python')
            
            rec = JobOpportunityRecommendation(
                rec_id=f"company_direct_{company.lower()}",
                recommendation_type='direct_company',
                title=f'Senior Python/ML Engineer at {company}',
                target_company=company,
                location=location,
                search_url=career_url,
                company_career_url=career_url,
                salary_estimate=salary,
                why_recommended=f"{company} is actively hiring engineers. Apply directly on their career page for best results.",
                match_score=score,
                required_skills=['Python', 'System Design', 'Cloud (AWS/Azure/GCP)', 'ML/AI'],
                next_steps=f"1. Visit {company} career page\n2. Search for 'Python' or 'ML Engineer'\n3. Apply directly\n4. Mention your LinkedIn profile"
            )
            recommendations.append(rec)
        
        return recommendations

    def _get_linkedin_company_searches(self, limit: int) -> List[JobOpportunityRecommendation]:
        """Create LinkedIn company-specific job searches"""
        recommendations = []
        
        company_searches = [
            ('Microsoft', 'Seattle, WA', '$150,000 - $220,000', 88, 'python OR "machine learning" OR "software engineer"'),
            ('Google', 'Mountain View, CA', '$160,000 - $240,000', 87, 'python OR ML OR "backend engineer"'),
            ('Amazon', 'Seattle, WA', '$140,000 - $200,000', 86, 'python OR AWS OR "senior engineer"'),
        ]
        
        for company, location, salary, score, search_terms in company_searches[:limit]:
            # Create LinkedIn company search URL
            linkedin_url = f'https://www.linkedin.com/jobs/search?keywords={search_terms.replace(" ", "+")}&f_C={self._get_company_id(company)}&location={location.replace(" ", "+")}&f_TPR=r604800&f_JT=F'
            
            rec = JobOpportunityRecommendation(
                rec_id=f"linkedin_company_{company.lower()}",
                recommendation_type='linkedin_company_search',
                title=f'Search {company} openings on LinkedIn',
                target_company=company,
                location=location,
                search_url=linkedin_url,
                company_career_url=self.company_career_pages.get(company),
                salary_estimate=salary,
                why_recommended=f"LinkedIn shows recent {company} postings. Set up job alerts for new openings.",
                match_score=score,
                required_skills=['Python', 'ML', 'System Design'],
                next_steps=f"1. Click search link\n2. Set up job alert\n3. Filter by experience level\n4. Apply within 24 hours of posting"
            )
            recommendations.append(rec)
        
        return recommendations

    def _get_job_board_recommendations(self, limit: int) -> List[JobOpportunityRecommendation]:
        """Create targeted job board searches"""
        recommendations = []
        
        job_boards = [
            {
                'title': 'Senior Python Engineers - Top Tech',
                'url': 'https://www.indeed.com/jobs?q=senior+python+engineer+%28Microsoft+OR+Google+OR+Amazon+OR+Meta%29&l=United+States&sort=date&fromage=7',
                'company': 'FAANG+ Companies',
                'location': 'Multiple Locations',
                'salary': '$150,000 - $250,000',
                'score': 85,
                'why': 'Indeed aggregates jobs from top tech companies. Check daily for new postings.',
                'next_steps': '1. Set up Indeed job alert\n2. Upload resume\n3. Enable "Easy Apply"\n4. Apply within 2 days'
            },
            {
                'title': 'Machine Learning Engineers',
                'url': 'https://www.linkedin.com/jobs/search?keywords=machine+learning+engineer&location=United+States&f_TPR=r86400&f_JT=F&sortBy=DD',
                'company': 'AI/ML Companies',
                'location': 'Remote/Bay Area',
                'salary': '$160,000 - $280,000',
                'score': 84,
                'why': 'LinkedIn ML roles updated daily. Many remote opportunities.',
                'next_steps': '1. Set up LinkedIn job alert\n2. Update profile with ML projects\n3. Network with recruiters\n4. Apply and follow up'
            }
        ]
        
        for i, board in enumerate(job_boards[:limit]):
            rec = JobOpportunityRecommendation(
                rec_id=f"job_board_{i}",
                recommendation_type='job_board_search',
                title=board['title'],
                target_company=board['company'],
                location=board['location'],
                search_url=board['url'],
                company_career_url=None,
                salary_estimate=board['salary'],
                why_recommended=board['why'],
                match_score=board['score'],
                required_skills=['Python', 'ML/AI', 'Cloud Platform'],
                next_steps=board['next_steps']
            )
            recommendations.append(rec)
        
        return recommendations

    def _get_company_id(self, company: str) -> str:
        """Get LinkedIn company ID (these are examples, real IDs vary)"""
        company_ids = {
            'Microsoft': '1035',
            'Google': '1441',
            'Amazon': '1586',
            'Meta': '10667',
            'Apple': '162479',
            'Netflix': '165158'
        }
        return company_ids.get(company, '1035')

def main():
    """Test the honest job opportunity provider"""
    provider = HonestJobOpportunityProvider()
    
    print("🎯 Testing Honest Job Opportunity Provider...")
    recommendations = provider.get_honest_job_recommendations(6)
    
    print(f"\n✅ Generated {len(recommendations)} honest job recommendations:\n")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.title}")
        print(f"   🏢 Company: {rec.target_company}")
        print(f"   📍 Location: {rec.location}")
        print(f"   💰 Salary: {rec.salary_estimate}")
        print(f"   📊 Match: {rec.match_score}%")
        print(f"   🔗 URL: {rec.search_url[:80]}...")
        print(f"   💡 Why: {rec.why_recommended}")
        print(f"   📋 Next Steps:\n      {rec.next_steps.replace(chr(10), chr(10) + '      ')}")
        print()

if __name__ == "__main__":
    main()