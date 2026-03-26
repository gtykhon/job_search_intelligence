"""
Unified Opportunity Dashboard

A comprehensive dashboard that displays job opportunities from both 
Job Search Intelligence and external job pipeline systems in a unified interface.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import asdict

from src.integrations.external_job_pipeline import get_integrator, JobOpportunity
from src.integrations.data_exchange import get_data_manager

logger = logging.getLogger(__name__)

class UnifiedOpportunityDashboard:
    """Unified dashboard for viewing opportunities from both systems"""
    
    def __init__(self):
        self.integrator = get_integrator()
        self.data_manager = get_data_manager()
        self.data_dir = Path("data")
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def get_all_opportunities(self, days_back: int = 7) -> Dict[str, List[JobOpportunity]]:
        """Get all opportunities from both systems organized by source"""
        try:
            # Get opportunities from Job Search Intelligence
            linkedin_opportunities = self.integrator.get_linkedin_opportunities()
            
            # Get opportunities from external pipeline
            external_opportunities = self.data_manager.import_external_opportunities()
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            linkedin_filtered = [
                opp for opp in linkedin_opportunities 
                if opp.retrieved_at >= cutoff_date
            ]
            
            external_filtered = [
                opp for opp in external_opportunities 
                if opp.retrieved_at >= cutoff_date
            ]
            
            logger.info(f"Retrieved {len(linkedin_filtered)} LinkedIn + {len(external_filtered)} external opportunities")
            
            return {
                "linkedin": linkedin_filtered,
                "external_pipeline": external_filtered,
                "all": linkedin_filtered + external_filtered
            }
            
        except Exception as e:
            logger.error(f"Failed to get all opportunities: {e}")
            return {"linkedin": [], "external_pipeline": [], "all": []}
    
    def generate_html_dashboard(self, opportunities: Dict[str, List[JobOpportunity]]) -> str:
        """Generate HTML dashboard showing all opportunities"""
        try:
            # Sort opportunities by match score
            all_opps = sorted(opportunities["all"], key=lambda x: x.match_score, reverse=True)
            linkedin_opps = opportunities["linkedin"]
            external_opps = opportunities["external_pipeline"]
            
            # Calculate statistics
            stats = self._calculate_statistics(opportunities)
            
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Job Opportunities Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 700; }}
        .header p {{ margin: 10px 0 0; opacity: 0.9; font-size: 1.1em; }}
        
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }}
        .stat-number {{ font-size: 2.5em; font-weight: 700; margin-bottom: 10px; }}
        .stat-label {{ color: #666; font-weight: 500; }}
        .linkedin-stat {{ color: #0a66c2; }}
        .external-stat {{ color: #28a745; }}
        .total-stat {{ color: #6f42c1; }}
        .high-priority-stat {{ color: #dc3545; }}
        
        .dashboard-tabs {{ display: flex; margin-bottom: 20px; background: white; border-radius: 12px; padding: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .tab {{ flex: 1; padding: 12px 20px; text-align: center; cursor: pointer; border-radius: 8px; font-weight: 500; transition: all 0.3s; }}
        .tab:hover {{ background: #f8f9fa; }}
        .tab.active {{ background: #667eea; color: white; }}
        
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        .opportunities-grid {{ display: grid; gap: 20px; }}
        .opportunity-card {{ background: white; border-radius: 12px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s, box-shadow 0.2s; }}
        .opportunity-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.15); }}
        
        .opportunity-header {{ display: flex; justify-content: between; align-items: flex-start; margin-bottom: 15px; }}
        .opportunity-title {{ font-size: 1.4em; font-weight: 600; color: #333; margin: 0 0 8px 0; }}
        .opportunity-company {{ color: #666; font-weight: 500; }}
        
        .opportunity-badges {{ display: flex; gap: 8px; margin-bottom: 15px; flex-wrap: wrap; }}
        .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 500; }}
        .badge-high {{ background: #dc3545; color: white; }}
        .badge-medium {{ background: #ffc107; color: #000; }}
        .badge-low {{ background: #28a745; color: white; }}
        .badge-linkedin {{ background: #0a66c2; color: white; }}
        .badge-external {{ background: #28a745; color: white; }}
        .badge-match {{ background: #6f42c1; color: white; }}
        
        .opportunity-details {{ margin-bottom: 15px; }}
        .detail-row {{ display: flex; margin-bottom: 8px; }}
        .detail-label {{ font-weight: 500; margin-right: 10px; min-width: 80px; color: #666; }}
        .detail-value {{ color: #333; }}
        
        .opportunity-description {{ color: #666; line-height: 1.6; margin-bottom: 15px; max-height: 100px; overflow: hidden; }}
        .opportunity-actions {{ display: flex; gap: 10px; }}
        .btn {{ padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 500; transition: all 0.2s; }}
        .btn-primary {{ background: #667eea; color: white; }}
        .btn-primary:hover {{ background: #5a67d8; }}
        .btn-secondary {{ background: #e2e8f0; color: #4a5568; }}
        .btn-secondary:hover {{ background: #cbd5e0; }}
        
        .filters {{ background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .filter-row {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
        .filter-group {{ display: flex; flex-direction: column; }}
        .filter-label {{ font-weight: 500; margin-bottom: 5px; color: #333; }}
        .filter-input {{ padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; }}
        
        .no-opportunities {{ text-align: center; padding: 60px 20px; color: #666; }}
        .no-opportunities h3 {{ color: #999; margin-bottom: 10px; }}
        
        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .dashboard-tabs {{ flex-direction: column; }}
            .opportunity-header {{ flex-direction: column; }}
            .filter-row {{ flex-direction: column; align-items: stretch; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Unified Job Opportunities Dashboard</h1>
            <p>Job Search Intelligence + External Job Pipeline Integration</p>
            <p>Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number total-stat">{len(all_opps)}</div>
                <div class="stat-label">Total Opportunities</div>
            </div>
            <div class="stat-card">
                <div class="stat-number linkedin-stat">{len(linkedin_opps)}</div>
                <div class="stat-label">Job Search Intelligence</div>
            </div>
            <div class="stat-card">
                <div class="stat-number external-stat">{len(external_opps)}</div>
                <div class="stat-label">External Pipeline</div>
            </div>
            <div class="stat-card">
                <div class="stat-number high-priority-stat">{stats['high_priority_count']}</div>
                <div class="stat-label">High Priority (90%+ Match)</div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-row">
                <div class="filter-group">
                    <label class="filter-label">Search</label>
                    <input type="text" class="filter-input" id="searchInput" placeholder="Search opportunities...">
                </div>
                <div class="filter-group">
                    <label class="filter-label">Source</label>
                    <select class="filter-input" id="sourceFilter">
                        <option value="all">All Sources</option>
                        <option value="linkedin">Job Search Intelligence</option>
                        <option value="external_pipeline">External Pipeline</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label class="filter-label">Match Score</label>
                    <select class="filter-input" id="matchFilter">
                        <option value="all">All Matches</option>
                        <option value="high">High (90%+)</option>
                        <option value="medium">Medium (70-89%)</option>
                        <option value="low">Low (<70%)</option>
                    </select>
                </div>
            </div>
        </div>
        
        <div class="dashboard-tabs">
            <div class="tab active" onclick="showTab('all')">All Opportunities ({len(all_opps)})</div>
            <div class="tab" onclick="showTab('linkedin')">LinkedIn ({len(linkedin_opps)})</div>
            <div class="tab" onclick="showTab('external')">External Pipeline ({len(external_opps)})</div>
            <div class="tab" onclick="showTab('analytics')">Analytics</div>
        </div>
        
        <div id="all-tab" class="tab-content active">
            <div class="opportunities-grid" id="allOpportunities">
                {self._generate_opportunities_html(all_opps)}
            </div>
        </div>
        
        <div id="linkedin-tab" class="tab-content">
            <div class="opportunities-grid">
                {self._generate_opportunities_html(linkedin_opps)}
            </div>
        </div>
        
        <div id="external-tab" class="tab-content">
            <div class="opportunities-grid">
                {self._generate_opportunities_html(external_opps)}
            </div>
        </div>
        
        <div id="analytics-tab" class="tab-content">
            {self._generate_analytics_html(stats, opportunities)}
        </div>
    </div>
    
    <script>
        function showTab(tabName) {{
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }}
        
        // Filter functionality
        function filterOpportunities() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const sourceFilter = document.getElementById('sourceFilter').value;
            const matchFilter = document.getElementById('matchFilter').value;
            
            document.querySelectorAll('.opportunity-card').forEach(card => {{
                const title = card.querySelector('.opportunity-title').textContent.toLowerCase();
                const company = card.querySelector('.opportunity-company').textContent.toLowerCase();
                const source = card.dataset.source;
                const matchScore = parseFloat(card.dataset.match);
                
                let showCard = true;
                
                // Search filter
                if (searchTerm && !title.includes(searchTerm) && !company.includes(searchTerm)) {{
                    showCard = false;
                }}
                
                // Source filter
                if (sourceFilter !== 'all' && source !== sourceFilter) {{
                    showCard = false;
                }}
                
                // Match score filter
                if (matchFilter !== 'all') {{
                    if (matchFilter === 'high' && matchScore < 90) showCard = false;
                    if (matchFilter === 'medium' && (matchScore < 70 || matchScore >= 90)) showCard = false;
                    if (matchFilter === 'low' && matchScore >= 70) showCard = false;
                }}
                
                card.style.display = showCard ? 'block' : 'none';
            }});
        }}
        
        document.getElementById('searchInput').addEventListener('input', filterOpportunities);
        document.getElementById('sourceFilter').addEventListener('change', filterOpportunities);
        document.getElementById('matchFilter').addEventListener('change', filterOpportunities);
    </script>
</body>
</html>
"""
            
            return html_content
            
        except Exception as e:
            logger.error(f"Failed to generate HTML dashboard: {e}")
            return "<html><body><h1>Error generating dashboard</h1></body></html>"
    
    def _generate_opportunities_html(self, opportunities: List[JobOpportunity]) -> str:
        """Generate HTML for opportunities list"""
        if not opportunities:
            return """
            <div class="no-opportunities">
                <h3>No opportunities found</h3>
                <p>Check back later or adjust your filters</p>
            </div>
            """
        
        html_cards = []
        for opp in opportunities:
            # Determine priority badge
            if opp.match_score >= 0.9:
                priority_badge = '<span class="badge badge-high">High Priority</span>'
            elif opp.match_score >= 0.7:
                priority_badge = '<span class="badge badge-medium">Medium Priority</span>'
            else:
                priority_badge = '<span class="badge badge-low">Low Priority</span>'
            
            # Source badge
            source_badge = f'<span class="badge badge-{"linkedin" if opp.source == "linkedin" else "external"}">{opp.source.replace("_", " ").title()}</span>'
            
            # Match score badge
            match_badge = f'<span class="badge badge-match">{int(opp.match_score * 100)}% Match</span>'
            
            # Format description
            description = opp.description[:200] + "..." if len(opp.description) > 200 else opp.description
            
            # Format requirements
            requirements_list = ""
            if opp.requirements:
                requirements_list = "<br>".join([f"• {req}" for req in opp.requirements[:3]])
                if len(opp.requirements) > 3:
                    requirements_list += f"<br>• ... and {len(opp.requirements) - 3} more"
            
            card_html = f"""
            <div class="opportunity-card" data-source="{opp.source}" data-match="{opp.match_score * 100}">
                <div class="opportunity-header">
                    <div>
                        <h3 class="opportunity-title">{opp.title}</h3>
                        <div class="opportunity-company">{opp.company}</div>
                    </div>
                </div>
                
                <div class="opportunity-badges">
                    {priority_badge}
                    {source_badge}
                    {match_badge}
                </div>
                
                <div class="opportunity-details">
                    <div class="detail-row">
                        <span class="detail-label">📍 Location:</span>
                        <span class="detail-value">{opp.location}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">💰 Salary:</span>
                        <span class="detail-value">{opp.salary_range}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">📅 Posted:</span>
                        <span class="detail-value">{opp.posted_date.strftime('%Y-%m-%d')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">📊 Status:</span>
                        <span class="detail-value">{opp.application_status.replace('_', ' ').title()}</span>
                    </div>
                </div>
                
                <div class="opportunity-description">
                    {description}
                    {f'<br><br><strong>Key Requirements:</strong><br>{requirements_list}' if requirements_list else ''}
                </div>
                
                <div class="opportunity-actions">
                    <a href="{opp.url}" target="_blank" class="btn btn-primary">View Job</a>
                    <a href="#" class="btn btn-secondary" onclick="markAsApplied('{opp.id}')">Mark as Applied</a>
                </div>
            </div>
            """
            html_cards.append(card_html)
        
        return "".join(html_cards)
    
    def _generate_analytics_html(self, stats: Dict[str, Any], opportunities: Dict[str, List[JobOpportunity]]) -> str:
        """Generate analytics section HTML"""
        return f"""
        <div style="display: grid; gap: 20px;">
            <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0;">📊 Opportunity Analytics</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px;">
                    <div>
                        <h4>Source Distribution</h4>
                        <ul style="list-style: none; padding: 0;">
                            <li>🔗 Job Search Intelligence: {len(opportunities['linkedin'])} ({len(opportunities['linkedin'])/max(len(opportunities['all']), 1)*100:.1f}%)</li>
                            <li>🌐 External Pipeline: {len(opportunities['external_pipeline'])} ({len(opportunities['external_pipeline'])/max(len(opportunities['all']), 1)*100:.1f}%)</li>
                        </ul>
                    </div>
                    
                    <div>
                        <h4>Match Score Distribution</h4>
                        <ul style="list-style: none; padding: 0;">
                            <li>🔥 High (90%+): {stats['high_priority_count']}</li>
                            <li>📊 Medium (70-89%): {stats['medium_priority_count']}</li>
                            <li>📉 Low (<70%): {stats['low_priority_count']}</li>
                        </ul>
                    </div>
                </div>
                
                <div>
                    <h4>Top Companies</h4>
                    <ul style="list-style: none; padding: 0;">
                        {self._get_top_companies_html(opportunities['all'])}
                    </ul>
                </div>
                
                <div style="margin-top: 20px;">
                    <h4>Application Status</h4>
                    <ul style="list-style: none; padding: 0;">
                        {self._get_application_status_html(opportunities['all'])}
                    </ul>
                </div>
            </div>
            
            <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0;">🎯 Recommendations</h3>
                <ul>
                    <li><strong>High Priority Focus:</strong> You have {stats['high_priority_count']} high-priority opportunities. Start with these first.</li>
                    <li><strong>Source Diversity:</strong> {"Great job leveraging both LinkedIn and external sources!" if len(opportunities['linkedin']) > 0 and len(opportunities['external_pipeline']) > 0 else "Consider enabling both Job Search Intelligence and external pipeline for maximum coverage."}</li>
                    <li><strong>Application Tracking:</strong> Keep your application status updated for better tracking.</li>
                    <li><strong>Regular Review:</strong> Review this dashboard daily to stay on top of new opportunities.</li>
                </ul>
            </div>
        </div>
        """
    
    def _get_top_companies_html(self, opportunities: List[JobOpportunity]) -> str:
        """Get HTML for top companies"""
        from collections import Counter
        company_counts = Counter([opp.company for opp in opportunities])
        top_companies = company_counts.most_common(5)
        
        return "".join([
            f"<li>🏢 {company}: {count} opportunities</li>"
            for company, count in top_companies
        ])
    
    def _get_application_status_html(self, opportunities: List[JobOpportunity]) -> str:
        """Get HTML for application status distribution"""
        from collections import Counter
        status_counts = Counter([opp.application_status for opp in opportunities])
        
        status_icons = {
            "not_applied": "⭕",
            "applied": "✅",
            "interviewed": "💬",
            "rejected": "❌",
            "offered": "🎉"
        }
        
        return "".join([
            f"<li>{status_icons.get(status, '📋')} {status.replace('_', ' ').title()}: {count}</li>"
            for status, count in status_counts.items()
        ])
    
    def _calculate_statistics(self, opportunities: Dict[str, List[JobOpportunity]]) -> Dict[str, Any]:
        """Calculate opportunity statistics"""
        all_opps = opportunities["all"]
        
        high_priority = len([opp for opp in all_opps if opp.match_score >= 0.9])
        medium_priority = len([opp for opp in all_opps if 0.7 <= opp.match_score < 0.9])
        low_priority = len([opp for opp in all_opps if opp.match_score < 0.7])
        
        return {
            "total_opportunities": len(all_opps),
            "linkedin_count": len(opportunities["linkedin"]),
            "external_count": len(opportunities["external_pipeline"]),
            "high_priority_count": high_priority,
            "medium_priority_count": medium_priority,
            "low_priority_count": low_priority,
            "average_match_score": sum([opp.match_score for opp in all_opps]) / max(len(all_opps), 1)
        }
    
    def create_dashboard_report(self, days_back: int = 7) -> str:
        """Create and save unified dashboard report"""
        try:
            # Get all opportunities
            opportunities = self.get_all_opportunities(days_back)
            
            # Generate HTML dashboard
            html_content = self.generate_html_dashboard(opportunities)
            
            # Save dashboard
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dashboard_file = self.reports_dir / f"unified_dashboard_{timestamp}.html"
            
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Also save as latest dashboard
            latest_file = self.reports_dir / "latest_unified_dashboard.html"
            with open(latest_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Create JSON summary for API access
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_opportunities": len(opportunities["all"]),
                "linkedin_opportunities": len(opportunities["linkedin"]),
                "external_opportunities": len(opportunities["external_pipeline"]),
                "statistics": self._calculate_statistics(opportunities),
                "top_opportunities": [
                    {
                        "id": opp.id,
                        "title": opp.title,
                        "company": opp.company,
                        "match_score": opp.match_score,
                        "source": opp.source,
                        "url": opp.url
                    }
                    for opp in sorted(opportunities["all"], key=lambda x: x.match_score, reverse=True)[:10]
                ]
            }
            
            summary_file = self.reports_dir / f"dashboard_summary_{timestamp}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created unified dashboard: {dashboard_file}")
            logger.info(f"Dashboard summary: {len(opportunities['all'])} total opportunities")
            
            return str(dashboard_file)
            
        except Exception as e:
            logger.error(f"Failed to create dashboard report: {e}")
            return ""

# Global dashboard instance
_dashboard = None

def get_dashboard() -> UnifiedOpportunityDashboard:
    """Get or create global dashboard instance"""
    global _dashboard
    if _dashboard is None:
        _dashboard = UnifiedOpportunityDashboard()
    return _dashboard

# Convenience functions
def create_latest_dashboard(days_back: int = 7) -> str:
    """Create the latest unified dashboard"""
    dashboard = get_dashboard()
    return dashboard.create_dashboard_report(days_back)

def get_dashboard_summary() -> Dict[str, Any]:
    """Get dashboard summary data"""
    dashboard = get_dashboard()
    opportunities = dashboard.get_all_opportunities()
    return dashboard._calculate_statistics(opportunities)

if __name__ == "__main__":
    # Test dashboard creation
    dashboard = UnifiedOpportunityDashboard()
    
    print("Creating unified dashboard...")
    dashboard_file = dashboard.create_dashboard_report()
    
    if dashboard_file:
        print(f"✅ Dashboard created: {dashboard_file}")
        
        # Get summary
        summary = get_dashboard_summary()
        print(f"📊 Summary: {summary['total_opportunities']} opportunities ({summary['linkedin_count']} LinkedIn + {summary['external_count']} External)")
    else:
        print("❌ Failed to create dashboard")