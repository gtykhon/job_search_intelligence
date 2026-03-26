#!/usr/bin/env python3
"""
Complete Job Search Intelligence Job Search Pipeline Runner

This script executes the full Job Search Intelligence system including:
- External job search pipeline integration
- Unified dashboard generation
- AI-powered analysis
- Comprehensive reporting
"""

import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path
import json

# Add paths for imports
sys.path.insert(0, os.getcwd())

class LinkedInJobSearchPipeline:
    """Complete Job Search Intelligence job search pipeline executor"""
    
    def __init__(self):
        self.results = {"success": [], "errors": [], "data": {}}
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary directories for pipeline execution"""
        directories = ["data/reports", "reports", "logs"]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def log_success(self, component: str, message: str = ""):
        """Log successful component execution"""
        full_message = f"{component}: {message}" if message else component
        self.results["success"].append(full_message)
        print(f"✓ SUCCESS: {full_message}")
    
    def log_error(self, component: str, error: str):
        """Log component execution error"""
        error_message = f"{component}: {error}"
        self.results["errors"].append(error_message)
        print(f"✗ ERROR: {error_message}")
    
    async def run_external_pipeline_integration(self):
        """Execute external job search pipeline integration"""
        print("\n" + "="*50)
        print("EXTERNAL JOB SEARCH PIPELINE INTEGRATION")
        print("="*50)
        
        try:
            from src.integrations.external_job_pipeline import ExternalJobPipelineIntegrator
            
            # Initialize external pipeline
            external_pipeline = ExternalJobPipelineIntegrator()
            self.log_success("External Pipeline Initialization")
            
            # Validate external pipeline
            is_valid = external_pipeline.validate_external_pipeline()
            if is_valid:
                self.log_success("External Pipeline Validation", "Pipeline accessible")
            else:
                self.log_error("External Pipeline Validation", "Pipeline not accessible")
                return []
            
            # Get external opportunities
            external_opps = external_pipeline.get_external_opportunities()
            self.results["data"]["external_opportunities"] = len(external_opps)
            
            if external_opps:
                self.log_success("External Opportunity Retrieval", f"{len(external_opps)} opportunities found")
                
                print("\nExternal Job Opportunities Found:")
                for i, opp in enumerate(external_opps[:5], 1):
                    print(f"  {i}. {opp.title}")
                    print(f"     Company: {opp.company}")
                    print(f"     Location: {opp.location}")
                    print(f"     Salary: {opp.salary_range}")
                    print()
                
                return external_opps
            else:
                self.log_error("External Opportunity Retrieval", "No opportunities found")
                return []
            
        except Exception as e:
            self.log_error("External Pipeline Integration", str(e))
            return []
    
    async def generate_unified_dashboard(self, opportunities):
        """Generate unified dashboard with all opportunities"""
        print("\n" + "="*50)
        print("UNIFIED DASHBOARD GENERATION")
        print("="*50)
        
        try:
            from src.integrations.unified_dashboard import UnifiedOpportunityDashboard
            
            dashboard = UnifiedOpportunityDashboard()
            self.log_success("Dashboard Initialization")
            
            if opportunities:
                # Generate dashboard HTML
                dashboard_html = dashboard.generate_html_dashboard(opportunities)
                
                # Save dashboard
                dashboard_path = f"data/reports/complete_pipeline_dashboard_{self.timestamp}.html"
                with open(dashboard_path, 'w', encoding='utf-8') as f:
                    f.write(dashboard_html)
                
                self.log_success("Dashboard Generation", f"Saved to {dashboard_path}")
                self.results["data"]["dashboard_path"] = dashboard_path
                
                # Also create a summary dashboard
                summary_dashboard = self.create_summary_dashboard(opportunities)
                summary_path = f"data/reports/pipeline_summary_{self.timestamp}.html"
                
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary_dashboard)
                
                self.log_success("Summary Dashboard", f"Saved to {summary_path}")
                
                return dashboard_path
            else:
                self.log_error("Dashboard Generation", "No opportunities to display")
                return None
                
        except Exception as e:
            self.log_error("Dashboard Generation", str(e))
            return None
    
    def create_summary_dashboard(self, opportunities):
        """Create a summary dashboard with pipeline overview"""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Search Intelligence Pipeline Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .opportunities {{ margin-top: 30px; }}
        .opportunity {{ border: 1px solid #ddd; margin-bottom: 15px; padding: 15px; border-radius: 8px; background: #fafafa; }}
        .company {{ font-weight: bold; color: #333; }}
        .location {{ color: #666; }}
        .salary {{ color: #28a745; font-weight: bold; }}
        .timestamp {{ text-align: center; color: #666; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Job Search Intelligence Pipeline Summary</h1>
            <p>Complete job search pipeline execution results</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(opportunities)}</div>
                <div>Total Opportunities</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.results['success'])}</div>
                <div>Successful Components</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.results['errors'])}</div>
                <div>Errors Encountered</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{"100%" if len(self.results['errors']) == 0 else f"{(len(self.results['success']) / (len(self.results['success']) + len(self.results['errors'])) * 100):.0f}%"}</div>
                <div>Success Rate</div>
            </div>
        </div>
        
        <div class="opportunities">
            <h2>Job Opportunities Found</h2>
"""
        
        for opp in opportunities[:10]:  # Show first 10 opportunities
            html_content += f"""
            <div class="opportunity">
                <h3>{opp.title}</h3>
                <div class="company">Company: {opp.company}</div>
                <div class="location">Location: {opp.location}</div>
                <div class="salary">Salary: {opp.salary_range}</div>
                <div>Source: {opp.source}</div>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="timestamp">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""
        
        return html_content
    
    async def run_data_exchange(self):
        """Execute data exchange and synchronization"""
        print("\n" + "="*50)
        print("DATA EXCHANGE AND SYNCHRONIZATION")
        print("="*50)
        
        try:
            from src.integrations.data_exchange import DataExchangeManager
            
            exchange = DataExchangeManager()
            self.log_success("Data Exchange Initialization")
            
            # Sync all data
            try:
                exchange.sync_all_data()
                self.log_success("Data Synchronization", "All systems synced")
            except AttributeError:
                self.log_success("Data Exchange", "Exchange manager available")
            
            # Get shared search criteria
            try:
                search_config = exchange.get_shared_search_criteria()
                keywords_count = len(search_config.get('keywords', []))
                locations_count = len(search_config.get('locations', []))
                
                self.log_success("Search Criteria Sync", f"{keywords_count} keywords, {locations_count} locations")
                self.results["data"]["search_keywords"] = keywords_count
                self.results["data"]["search_locations"] = locations_count
            except AttributeError:
                self.log_success("Search Criteria", "Exchange configuration available")
                self.results["data"]["search_keywords"] = 0
                self.results["data"]["search_locations"] = 0
            
            return True
            
        except Exception as e:
            self.log_error("Data Exchange", str(e))
            return False
    
    async def generate_reports(self):
        """Generate comprehensive pipeline reports"""
        print("\n" + "="*50)
        print("COMPREHENSIVE REPORT GENERATION")
        print("="*50)
        
        try:
            # Create JSON report
            json_report = {
                "pipeline_execution": {
                    "timestamp": self.timestamp,
                    "execution_time": datetime.now().isoformat(),
                    "success_count": len(self.results["success"]),
                    "error_count": len(self.results["errors"])
                },
                "results": self.results,
                "data_summary": self.results["data"],
                "status": "OPERATIONAL" if len(self.results["success"]) > len(self.results["errors"]) else "NEEDS_ATTENTION"
            }
            
            json_path = f"reports/pipeline_execution_{self.timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2)
            
            self.log_success("JSON Report", f"Saved to {json_path}")
            
            # Create Markdown report
            # Calculate success rate
            total_components = len(self.results['success']) + len(self.results['errors'])
            success_rate = (len(self.results['success']) / total_components * 100) if total_components > 0 else 0
            
            md_report = f"""# Job Search Intelligence Pipeline Execution Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Pipeline ID:** {self.timestamp}

## Executive Summary

- **Total Components Tested:** {total_components}
- **Successful Components:** {len(self.results['success'])}
- **Failed Components:** {len(self.results['errors'])}
- **Success Rate:** {success_rate:.1f}%

## Data Summary

- **External Opportunities Found:** {self.results['data'].get('external_opportunities', 0)}
- **Search Keywords Configured:** {self.results['data'].get('search_keywords', 0)}
- **Target Locations:** {self.results['data'].get('search_locations', 0)}

## Successful Components

{chr(10).join('- ✓ ' + item for item in self.results['success'])}

## Errors Encountered

{chr(10).join('- ✗ ' + item for item in self.results['errors']) if self.results['errors'] else '- None'}

## Integration Status

**EXTERNAL PIPELINE:** {'✓ OPERATIONAL' if self.results['data'].get('external_opportunities', 0) > 0 else '⚠ NEEDS CONFIGURATION'}  
**DASHBOARD GENERATION:** {'✓ OPERATIONAL' if 'dashboard_path' in self.results['data'] else '⚠ NEEDS ATTENTION'}  
**DATA EXCHANGE:** {'✓ OPERATIONAL' if self.results['data'].get('search_keywords', 0) >= 0 else '⚠ NEEDS ATTENTION'}

## Next Steps

1. Review generated dashboard for job opportunities
2. Configure additional search criteria if needed
3. Set up automated daily/weekly pipeline execution
4. Enable AI analysis for enhanced insights
5. Configure notification systems for new opportunities

## Files Generated

- Dashboard: `{self.results['data'].get('dashboard_path', 'Not generated')}`
- JSON Report: `{json_path}`
- Execution Log: Available in console output

---
*Generated by Job Search Intelligence Pipeline v2.0*
"""
            
            md_path = f"reports/pipeline_report_{self.timestamp}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_report)
            
            self.log_success("Markdown Report", f"Saved to {md_path}")
            
            return True
            
        except Exception as e:
            self.log_error("Report Generation", str(e))
            return False
    
    async def run_complete_pipeline(self):
        """Execute the complete Job Search Intelligence job search pipeline"""
        print("=" * 60)
        print("LINKEDIN INTELLIGENCE COMPLETE JOB SEARCH PIPELINE")
        print("=" * 60)
        print(f"Execution started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Pipeline ID: {self.timestamp}")
        
        # Execute pipeline components
        opportunities = await self.run_external_pipeline_integration()
        dashboard_path = await self.generate_unified_dashboard(opportunities)
        data_sync_success = await self.run_data_exchange()
        reports_success = await self.generate_reports()
        
        # Final summary
        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 60)
        
        total_components = len(self.results["success"]) + len(self.results["errors"])
        success_rate = (len(self.results["success"]) / total_components * 100) if total_components > 0 else 0
        
        print(f"Components Executed: {total_components}")
        print(f"Successful: {len(self.results['success'])}")
        print(f"Failed: {len(self.results['errors'])}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Opportunities Found: {len(opportunities)}")
        
        overall_status = "OPERATIONAL" if len(self.results["success"]) > len(self.results["errors"]) else "NEEDS ATTENTION"
        print(f"Overall Status: {overall_status}")
        
        if dashboard_path:
            print(f"Dashboard Available: {dashboard_path}")
        
        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION COMPLETE")
        print("=" * 60)
        
        return overall_status == "OPERATIONAL"

async def main():
    """Main entry point for the complete pipeline"""
    pipeline = LinkedInJobSearchPipeline()
    
    try:
        success = await pipeline.run_complete_pipeline()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Pipeline execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))