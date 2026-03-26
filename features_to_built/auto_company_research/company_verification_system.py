"""
Company Verification System
Automates the company research and screening workflow from Claude Projects

Workflow:
    Step 0A: Database Check (company_research_database.md)
    Step 0B: Defense Exclusion Screening
    Step 1: Web Research & Company Intelligence
    Step 2: Glassdoor Verification & Scoring
    Step 3: Culture/WLB Scoring
    Step 4: Risk Assessment
    Step 5: Decision Framework

Author: Based on Claude Projects automation framework
Last Updated: 2025-11-14
"""

import requests
import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime


class DecisionStatus(Enum):
    """Company screening decision status"""
    AUTO_DECLINE = "AUTO_DECLINE"
    USER_DECISION = "USER_DECISION"
    PROCEED = "PROCEED"
    DATABASE_HIT = "DATABASE_HIT"


class DefenseStatus(Enum):
    """Defense contractor classification"""
    DIRECT_CONTRACTOR = "Direct Defense Contractor"
    DEFENSE_ADJACENT = "Defense-Adjacent"
    PLATFORM_PROVIDER = "Platform Provider"
    NO_TIES = "No Defense Ties"
    GOVERNMENT_CONTRACTOR = "Government Contractor"


@dataclass
class GlassdoorMetrics:
    """Glassdoor ratings and metrics"""
    overall_rating: float = 0.0
    culture_values: float = 0.0
    work_life_balance: float = 0.0
    career_opportunities: float = 0.0
    senior_leadership: float = 0.0
    recommend_friend: float = 0.0
    ceo_approval: float = 0.0
    total_reviews: int = 0


@dataclass
class CompanyScoringResult:
    """Culture and WLB scoring results"""
    culture_score: int = 0
    culture_rating: str = ""
    wlb_score: int = 0
    wlb_rating: str = ""
    risk_level: str = ""
    
    
@dataclass
class CompanyResearchResult:
    """Complete company research results"""
    company_name: str
    position: str
    decision_status: DecisionStatus
    defense_status: Optional[DefenseStatus] = None
    glassdoor_metrics: Optional[GlassdoorMetrics] = None
    scoring_result: Optional[CompanyScoringResult] = None
    decline_reason: Optional[str] = None
    evidence: List[str] = None
    time_saved_minutes: int = 0
    research_date: str = ""
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []
        if not self.research_date:
            self.research_date = datetime.now().strftime("%Y-%m-%d")


class DatabaseChecker:
    """Step 0A: Check company_research_database.md for existing research"""
    
    def __init__(self, database_path: str = "company_research_database.md"):
        self.database_path = database_path
        
    def check_company(self, company_name: str) -> Tuple[bool, Optional[Dict]]:
        """
        Search database for company
        
        Returns:
            (found, existing_research_dict)
        """
        try:
            with open(self.database_path, 'r') as f:
                content = f.read()
                
            # Simple search for company name (case-insensitive)
            pattern = rf"###\s+\*\*{re.escape(company_name)}\s*\("
            match = re.search(pattern, content, re.IGNORECASE)
            
            if match:
                # Extract section for this company
                section_start = match.start()
                # Find next company section or end
                next_match = re.search(r'###\s+\*\*[A-Z]', content[section_start + 10:])
                if next_match:
                    section_end = section_start + 10 + next_match.start()
                else:
                    section_end = len(content)
                    
                company_section = content[section_start:section_end]
                
                # Parse key information
                research_data = {
                    'found': True,
                    'section': company_section,
                    'status': self._extract_status(company_section),
                    'decline_reason': self._extract_decline_reason(company_section),
                    'culture_score': self._extract_score(company_section, 'CULTURE_SCORE'),
                    'wlb_score': self._extract_score(company_section, 'WORK_LIFE_BALANCE_SCORE'),
                    'glassdoor_rating': self._extract_glassdoor_rating(company_section)
                }
                
                return True, research_data
            else:
                return False, None
                
        except FileNotFoundError:
            print(f"Warning: Database file {self.database_path} not found")
            return False, None
            
    def _extract_status(self, section: str) -> str:
        """Extract company status (APPROVED/DECLINED)"""
        if re.search(r'\*\*STATUS:\*\*\s*(APPROVED|DECLINED)', section, re.IGNORECASE):
            match = re.search(r'\*\*STATUS:\*\*\s*(APPROVED|DECLINED)', section, re.IGNORECASE)
            return match.group(1).upper()
        if 'DECISION:** DECLINED' in section:
            return 'DECLINED'
        if 'DECISION:** APPROVED' in section:
            return 'APPROVED'
        return 'UNKNOWN'
        
    def _extract_decline_reason(self, section: str) -> Optional[str]:
        """Extract decline reason if present"""
        patterns = [
            r'\*\*Rationale:\*\*\s*([^\n]+)',
            r'DECLINE.*?REASON.*?:\s*([^\n]+)',
            r'Exclusion Reason:\s*([^\n]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, section, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
        
    def _extract_score(self, section: str, score_type: str) -> Optional[int]:
        """Extract culture or WLB score"""
        pattern = rf'\*\*{score_type}:\*\*\s*(\d+)/100'
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
        
    def _extract_glassdoor_rating(self, section: str) -> Optional[float]:
        """Extract overall Glassdoor rating"""
        pattern = r'Overall[:\s]+(\d+\.?\d*)/5'
        match = re.search(pattern, section, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None


class DefenseScreener:
    """Step 0B: Screen for defense/government contractor ties"""
    
    # Known defense contractors (auto-decline)
    KNOWN_DEFENSE_CONTRACTORS = {
        'lockheed martin', 'northrop grumman', 'raytheon', 'boeing defense',
        'general dynamics', 'leidos', 'booz allen hamilton', 'caci',
        'saic', 'l3harris', 'bae systems', 'palantir technologies',
        'parsons corporation', 'kbr', 'aecom', 'jacobs engineering',
        'tetra tech', 'peraton', 'amentum', 'vectrus'
    }
    
    # Known government contractors (auto-decline per user preference)
    KNOWN_GOVERNMENT_CONTRACTORS = {
        'deloitte federal', 'accenture federal', 'pwc federal',
        'ernst & young government', 'kpmg government', 'cgifederal',
        'maximus', 'serco', 'gdit', 'credence management solutions'
    }
    
    # Edge case companies requiring user decision
    EDGE_CASE_COMPANIES = {
        'amazon': 'AWS GovCloud (~5% revenue)',
        'microsoft': 'Azure Government Cloud',
        'google': 'Google Cloud for Government',
        'oracle': 'Oracle Cloud for Government'
    }
    
    def __init__(self, web_search_api_key: Optional[str] = None):
        self.api_key = web_search_api_key
        
    def screen_company(self, company_name: str) -> Tuple[DefenseStatus, DecisionStatus, List[str]]:
        """
        Screen company for defense/government ties
        
        Returns:
            (defense_status, decision_status, evidence_list)
        """
        company_lower = company_name.lower()
        evidence = []
        
        # Check known defense contractors
        if any(contractor in company_lower for contractor in self.KNOWN_DEFENSE_CONTRACTORS):
            evidence.append(f"Known defense contractor: {company_name}")
            return DefenseStatus.DIRECT_CONTRACTOR, DecisionStatus.AUTO_DECLINE, evidence
            
        # Check known government contractors
        if any(contractor in company_lower for contractor in self.KNOWN_GOVERNMENT_CONTRACTORS):
            evidence.append(f"Known government contractor: {company_name}")
            return DefenseStatus.GOVERNMENT_CONTRACTOR, DecisionStatus.AUTO_DECLINE, evidence
            
        # Check edge cases (cloud platforms with government divisions)
        for edge_company, context in self.EDGE_CASE_COMPANIES.items():
            if edge_company in company_lower:
                evidence.append(f"Edge case: {context}")
                return DefenseStatus.PLATFORM_PROVIDER, DecisionStatus.USER_DECISION, evidence
                
        # If we have API access, do web research
        if self.api_key:
            web_evidence = self._web_research_defense(company_name)
            evidence.extend(web_evidence)
            
            if self._has_significant_defense_ties(web_evidence):
                return DefenseStatus.DEFENSE_ADJACENT, DecisionStatus.USER_DECISION, evidence
        
        # Default: no defense ties found
        evidence.append("No defense contractor ties found in initial screening")
        return DefenseStatus.NO_TIES, DecisionStatus.PROCEED, evidence
        
    def _web_research_defense(self, company_name: str) -> List[str]:
        """Research defense ties via web search (placeholder)"""
        # In production, this would call:
        # - USASpending.gov API
        # - Company website scraping
        # - News search for defense contracts
        evidence = []
        
        # Placeholder - would integrate with actual web search
        search_queries = [
            f"{company_name} defense contracts",
            f"{company_name} military customers",
            f"{company_name} DOD contracts",
            f"{company_name} USASpending.gov"
        ]
        
        # TODO: Implement actual web search
        # For now, return placeholder
        evidence.append("Web research: No significant defense contracts found")
        
        return evidence
        
    def _has_significant_defense_ties(self, evidence: List[str]) -> bool:
        """Determine if evidence indicates significant defense work"""
        # Look for keywords indicating defense work
        defense_keywords = ['military', 'defense contract', 'DOD', 'pentagon', 
                          'clearance required', 'classified', 'weapons system']
        
        evidence_text = ' '.join(evidence).lower()
        return any(keyword in evidence_text for keyword in defense_keywords)


class GlassdoorScraper:
    """Step 2: Fetch Glassdoor ratings and metrics"""
    
    def __init__(self, use_scraper: bool = False, cache_dir: str = "./glassdoor_cache/"):
        """
        Args:
            use_scraper: If True, use Playwright web scraper. If False, return placeholder data.
            cache_dir: Directory for caching scraped data
        """
        self.use_scraper = use_scraper
        self.scraper = None
        
        if use_scraper:
            try:
                # Import Playwright scraper (requires playwright to be installed)
                from playwright_glassdoor_scraper import CachedGlassdoorScraper
                self.scraper = CachedGlassdoorScraper(
                    cache_dir=cache_dir,
                    cache_days=7,
                    headless=True
                )
                print("✓ Playwright scraper initialized")
            except ImportError:
                print("⚠️  Playwright not installed. Run: pip install playwright && playwright install chromium")
                print("   Using placeholder data instead.")
                self.use_scraper = False
        
    def fetch_metrics(self, company_name: str) -> Optional[GlassdoorMetrics]:
        """
        Fetch Glassdoor metrics for company
        
        If use_scraper=True and Playwright is installed, scrapes real data.
        Otherwise returns placeholder data for demonstration.
        """
        if self.use_scraper and self.scraper:
            # Use real web scraping
            try:
                return self.scraper.fetch_metrics(company_name)
            except Exception as e:
                print(f"Scraping failed: {e}")
                print("Falling back to placeholder data")
        
        # Placeholder data when metrics have not been fetched yet.
        # All zeros make it clear that Glassdoor data is not available.
        print(f"Using placeholder Glassdoor data for {company_name}")
        return GlassdoorMetrics(
            overall_rating=0.0,
            culture_values=0.0,
            work_life_balance=0.0,
            career_opportunities=0.0,
            senior_leadership=0.0,
            recommend_friend=0.0,
            ceo_approval=0.0,
            total_reviews=0
        )


class CompanyScorer:
    """Step 3: Calculate culture and WLB scores from Glassdoor metrics"""
    
    def calculate_culture_score(self, metrics: GlassdoorMetrics) -> Tuple[int, str]:
        """
        Calculate culture score (0-100) from Glassdoor metrics
        
        Scoring criteria from project framework:
        - Excellent (80-100): 4.5+ stars, 50+ reviews
        - Good (65-79): 3.8-4.4 stars, 20+ reviews
        - Average (50-64): 3.0-3.7 stars
        - Below Average (35-49): 2.5-2.9 stars
        - Poor (0-34): <2.5 stars
        """
        # If we have no real data yet, return 0 / Unknown so it is
        # clearly distinguishable from real scores.
        if metrics.overall_rating == 0.0 and metrics.total_reviews == 0:
            return 0, "Unknown"

        rating = metrics.overall_rating
        reviews = metrics.total_reviews
        
        # Base score from rating
        if rating >= 4.5:
            base_score = 85
            rating_category = "Excellent"
        elif rating >= 3.8:
            base_score = 72
            rating_category = "Good"
        elif rating >= 3.0:
            base_score = 57
            rating_category = "Average"
        elif rating >= 2.5:
            base_score = 42
            rating_category = "Below Average"
        else:
            base_score = 25
            rating_category = "Poor"
            
        # Adjust for review count (confidence)
        if reviews >= 50:
            confidence_bonus = 5
        elif reviews >= 20:
            confidence_bonus = 0
        else:
            confidence_bonus = -5
            
        # Adjust for leadership approval
        if metrics.ceo_approval >= 80:
            leadership_bonus = 5
        elif metrics.ceo_approval >= 65:
            leadership_bonus = 0
        else:
            leadership_bonus = -5
            
        final_score = min(100, max(0, base_score + confidence_bonus + leadership_bonus))
        
        return final_score, rating_category
        
    def calculate_wlb_score(self, metrics: GlassdoorMetrics) -> Tuple[int, str]:
        """
        Calculate work-life balance score (0-100) from Glassdoor WLB rating
        
        Scoring criteria:
        - Excellent (80-100): 4.5+ WLB stars
        - Good (65-79): 3.8-4.4 WLB stars
        - Average (50-64): 3.0-3.7 WLB stars
        - Below Average (35-49): 2.5-2.9 WLB stars
        - Poor (0-34): <2.5 WLB stars
        """
        # If we have no real data yet, return 0 / Unknown.
        if metrics.work_life_balance == 0.0:
            return 0, "Unknown"

        wlb_rating = metrics.work_life_balance
        
        if wlb_rating >= 4.5:
            score = 85
            category = "Excellent"
        elif wlb_rating >= 3.8:
            score = 72
            category = "Good"
        elif wlb_rating >= 3.0:
            score = 57
            category = "Average"
        elif wlb_rating >= 2.5:
            score = 42
            category = "Below Average"
        else:
            score = 25
            category = "Poor"
            
        return score, category
        
    def assess_risk_level(self, culture_score: int, wlb_score: int, 
                         has_layoffs: bool = False) -> str:
        """
        Assess overall risk level
        
        Risk levels:
        - Low Risk: Well-established, strong culture (70+ scores)
        - Moderate Risk: Stable, average culture (50-69 scores)
        - Moderate-High Risk: Below-average culture (35-49 scores)
        - High Risk: Poor culture (<35 scores)
        """
        # If both scores are 0, treat as unknown risk (no data yet).
        if culture_score == 0 and wlb_score == 0:
            return "UNKNOWN"

        avg_score = (culture_score + wlb_score) / 2
        
        if has_layoffs:
            # Layoffs increase risk
            if avg_score >= 70:
                return "MODERATE (layoff concerns)"
            elif avg_score >= 50:
                return "MODERATE-HIGH (layoff + culture concerns)"
            else:
                return "HIGH (layoff + poor culture)"
        else:
            if avg_score >= 70:
                return "LOW"
            elif avg_score >= 50:
                return "MODERATE"
            elif avg_score >= 35:
                return "MODERATE-HIGH"
            else:
                return "HIGH"


class CompanyVerificationSystem:
    """
    Main orchestration system for company verification workflow
    """
    
    def __init__(self, 
                 database_path: str = "company_research_database.md",
                 web_search_api_key: Optional[str] = None,
                 use_glassdoor_scraper: bool = False,
                 glassdoor_cache_dir: str = "./glassdoor_cache/"):
        """
        Args:
            database_path: Path to company research database
            web_search_api_key: API key for web search (optional)
            use_glassdoor_scraper: Enable Playwright web scraping for Glassdoor
            glassdoor_cache_dir: Directory for caching Glassdoor data
        """
        self.db_checker = DatabaseChecker(database_path)
        self.defense_screener = DefenseScreener(web_search_api_key)
        self.glassdoor_scraper = GlassdoorScraper(
            use_scraper=use_glassdoor_scraper,
            cache_dir=glassdoor_cache_dir
        )
        self.scorer = CompanyScorer()
        
    def verify_company(self, company_name: str, position: str = "") -> CompanyResearchResult:
        """
        Execute complete company verification workflow
        
        Workflow:
            Step 0A: Database Check
            Step 0B: Defense Screening
            Step 1: Web Research (if needed)
            Step 2: Glassdoor Verification
            Step 3: Scoring
            Step 4: Decision
        """
        print(f"\n{'='*60}")
        print(f"COMPANY VERIFICATION: {company_name}")
        print(f"Position: {position}")
        print(f"{'='*60}\n")
        
        # Step 0A: Database Check
        print("Step 0A: Checking company database...")
        found, existing_data = self.db_checker.check_company(company_name)
        
        if found:
            print(f"✓ Company found in database!")
            print(f"  Status: {existing_data['status']}")
            
            if existing_data['status'] == 'DECLINED':
                print(f"  Previous decline reason: {existing_data['decline_reason']}")
                print(f"\n⏱️  TIME SAVED: ~15 minutes (skipped full research)")
                
                return CompanyResearchResult(
                    company_name=company_name,
                    position=position,
                    decision_status=DecisionStatus.DATABASE_HIT,
                    decline_reason=existing_data['decline_reason'],
                    time_saved_minutes=15
                )
            else:
                print("  Using existing research data")
                print("  Note: Would ask user if they want updated research")
                
        # Step 0B: Defense Screening
        print("\nStep 0B: Defense/Government contractor screening...")
        defense_status, decision, defense_evidence = self.defense_screener.screen_company(company_name)
        
        print(f"  Defense Status: {defense_status.value}")
        print(f"  Decision: {decision.value}")
        
        for i, evidence in enumerate(defense_evidence, 1):
            print(f"    {i}. {evidence}")
            
        if decision == DecisionStatus.AUTO_DECLINE:
            print(f"\n❌ AUTO-DECLINE: {defense_status.value}")
            print(f"⏱️  TIME SAVED: ~25 minutes (skipped culture research + application)")
            
            return CompanyResearchResult(
                company_name=company_name,
                position=position,
                decision_status=DecisionStatus.AUTO_DECLINE,
                defense_status=defense_status,
                decline_reason=f"Defense/Government contractor: {defense_status.value}",
                evidence=defense_evidence,
                time_saved_minutes=25
            )
            
        if decision == DecisionStatus.USER_DECISION:
            print(f"\n⚠️  USER DECISION REQUIRED")
            print("   Edge case detected - requires user confirmation to proceed")
            
            return CompanyResearchResult(
                company_name=company_name,
                position=position,
                decision_status=DecisionStatus.USER_DECISION,
                defense_status=defense_status,
                evidence=defense_evidence,
                decline_reason="Awaiting user decision on defense ties"
            )
            
        # Step 2: Glassdoor Verification
        print("\nStep 2: Fetching Glassdoor metrics...")
        glassdoor_metrics = self.glassdoor_scraper.fetch_metrics(company_name)
        
        if glassdoor_metrics:
            print(f"  Overall Rating: {glassdoor_metrics.overall_rating}/5")
            print(f"  Culture & Values: {glassdoor_metrics.culture_values}/5")
            print(f"  Work-Life Balance: {glassdoor_metrics.work_life_balance}/5")
            print(f"  Career Opportunities: {glassdoor_metrics.career_opportunities}/5")
            print(f"  CEO Approval: {glassdoor_metrics.ceo_approval}%")
            print(f"  Total Reviews: {glassdoor_metrics.total_reviews}")
        else:
            print("  ⚠️  Could not fetch Glassdoor metrics")
            
        # Step 3: Scoring
        print("\nStep 3: Calculating culture and WLB scores...")
        
        if glassdoor_metrics:
            culture_score, culture_rating = self.scorer.calculate_culture_score(glassdoor_metrics)
            wlb_score, wlb_rating = self.scorer.calculate_wlb_score(glassdoor_metrics)
            risk_level = self.scorer.assess_risk_level(culture_score, wlb_score)
            
            print(f"  Culture Score: {culture_score}/100 ({culture_rating})")
            print(f"  WLB Score: {wlb_score}/100 ({wlb_rating})")
            print(f"  Risk Level: {risk_level}")
            
            scoring_result = CompanyScoringResult(
                culture_score=culture_score,
                culture_rating=culture_rating,
                wlb_score=wlb_score,
                wlb_rating=wlb_rating,
                risk_level=risk_level
            )
        else:
            scoring_result = None
            
        # Step 4: Final Decision
        print("\nStep 4: Final decision framework...")
        
        final_decision = self._apply_decision_framework(
            glassdoor_metrics, 
            scoring_result,
            defense_status
        )
        
        print(f"  Final Decision: {final_decision.value}")
        
        result = CompanyResearchResult(
            company_name=company_name,
            position=position,
            decision_status=final_decision,
            defense_status=defense_status,
            glassdoor_metrics=glassdoor_metrics,
            scoring_result=scoring_result,
            evidence=defense_evidence
        )
        
        print(f"\n{'='*60}")
        print(f"VERIFICATION COMPLETE")
        print(f"{'='*60}\n")
        
        return result
        
    def _apply_decision_framework(self,
                                  metrics: Optional[GlassdoorMetrics],
                                  scoring: Optional[CompanyScoringResult],
                                  defense_status: DefenseStatus) -> DecisionStatus:
        """
        Apply decision framework based on all gathered data
        
        Decision criteria:
        - Culture/WLB 70+: PROCEED with confidence
        - Culture/WLB 50-69: PROCEED with preparation
        - Culture/WLB 35-49: USER_DECISION (proceed with caution)
        - Culture/WLB <35: USER_DECISION (consider avoiding)
        - Glassdoor <3.5: AUTO_DECLINE
        """
        if not metrics or not scoring:
            return DecisionStatus.USER_DECISION
            
        # Auto-decline if Glassdoor rating too low
        if metrics.overall_rating < 3.5:
            return DecisionStatus.AUTO_DECLINE
            
        # Calculate average score
        avg_score = (scoring.culture_score + scoring.wlb_score) / 2
        
        if avg_score >= 50:
            return DecisionStatus.PROCEED
        else:
            return DecisionStatus.USER_DECISION
            
    def generate_report(self, result: CompanyResearchResult) -> str:
        """Generate formatted text report of research results"""
        
        report = f"""
{'='*70}
COMPANY VERIFICATION REPORT
{'='*70}

Company: {result.company_name}
Position: {result.position}
Research Date: {result.research_date}
Final Decision: {result.decision_status.value}

{'='*70}
DEFENSE SCREENING
{'='*70}

Defense Status: {result.defense_status.value if result.defense_status else 'N/A'}

Evidence:
"""
        
        if result.evidence:
            for i, evidence in enumerate(result.evidence, 1):
                report += f"  {i}. {evidence}\n"
        else:
            report += "  No evidence recorded\n"
            
        if result.glassdoor_metrics:
            report += f"""
{'='*70}
GLASSDOOR METRICS
{'='*70}

Overall Rating: {result.glassdoor_metrics.overall_rating}/5
Culture & Values: {result.glassdoor_metrics.culture_values}/5
Work-Life Balance: {result.glassdoor_metrics.work_life_balance}/5
Career Opportunities: {result.glassdoor_metrics.career_opportunities}/5
Senior Leadership: {result.glassdoor_metrics.senior_leadership}/5
Recommend to Friend: {result.glassdoor_metrics.recommend_friend}%
CEO Approval: {result.glassdoor_metrics.ceo_approval}%
Total Reviews: {result.glassdoor_metrics.total_reviews}
"""
        
        if result.scoring_result:
            report += f"""
{'='*70}
SCORING ANALYSIS
{'='*70}

Culture Score: {result.scoring_result.culture_score}/100 ({result.scoring_result.culture_rating})
Work-Life Balance Score: {result.scoring_result.wlb_score}/100 ({result.scoring_result.wlb_rating})
Risk Level: {result.scoring_result.risk_level}
"""
        
        if result.decline_reason:
            report += f"""
{'='*70}
DECLINE REASON
{'='*70}

{result.decline_reason}
"""
        
        if result.time_saved_minutes > 0:
            report += f"""
{'='*70}
EFFICIENCY METRICS
{'='*70}

Time Saved: ~{result.time_saved_minutes} minutes
"""
        
        report += f"\n{'='*70}\n"
        
        return report


# Example usage
def main():
    """Example usage of the company verification system"""
    
    print("Company Verification System - Example Usage\n")
    
    # Initialize system
    system = CompanyVerificationSystem(
        database_path="/mnt/project/company_research_database.md",
        # In production, would provide actual API keys:
        # web_search_api_key="your_key_here",
        # glassdoor_api_key="your_key_here"
    )
    
    # Example 1: Known defense contractor (auto-decline)
    print("\n" + "="*70)
    print("EXAMPLE 1: Known Defense Contractor")
    print("="*70)
    result1 = system.verify_company("Lockheed Martin", "Software Engineer")
    print(system.generate_report(result1))
    
    # Example 2: Edge case (user decision)
    print("\n" + "="*70)
    print("EXAMPLE 2: Edge Case - Cloud Platform")
    print("="*70)
    result2 = system.verify_company("Amazon", "Software Development Engineer - EC2")
    print(system.generate_report(result2))
    
    # Example 3: Clean commercial company (proceed)
    print("\n" + "="*70)
    print("EXAMPLE 3: Commercial Company")
    print("="*70)
    result3 = system.verify_company("Netflix", "Analytics Engineer 5")
    print(system.generate_report(result3))
    
    # Example 4: Company in database
    print("\n" + "="*70)
    print("EXAMPLE 4: Database Hit")
    print("="*70)
    result4 = system.verify_company("Watershed", "Senior Analytics Engineer")
    print(system.generate_report(result4))


if __name__ == "__main__":
    main()
