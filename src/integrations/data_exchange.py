"""
Cross-System Data Exchange Manager

This module handles data sharing between Job Search Intelligence and external job pipeline
through multiple communication channels: database, JSON files, and direct API calls.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import asdict

from .external_job_pipeline import JobOpportunity, get_integrator

logger = logging.getLogger(__name__)

class DataExchangeManager:
    """Manages data exchange between Job Search Intelligence and external job pipeline"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.exchange_dir = self.data_dir / "exchange"
        self.exchange_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organized data exchange
        (self.exchange_dir / "outgoing").mkdir(exist_ok=True)
        (self.exchange_dir / "incoming").mkdir(exist_ok=True)
        (self.exchange_dir / "processed").mkdir(exist_ok=True)
        (self.exchange_dir / "shared_config").mkdir(exist_ok=True)
        
        self.db_path = self.data_dir / "job_pipeline_integration.db"
        
    def export_linkedin_opportunities(self, opportunities: List[Dict[str, Any]]):
        """Export LinkedIn opportunities for external pipeline consumption"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Convert to external pipeline format
            export_data = {
                "source": "job_search_intelligence",
                "timestamp": datetime.now().isoformat(),
                "count": len(opportunities),
                "opportunities": []
            }
            
            for opp in opportunities:
                # Convert to external pipeline expected format
                external_format = {
                    "job_id": opp.get("id", f"li_{timestamp}_{hash(str(opp))}"),
                    "job_title": opp.get("title", ""),
                    "company_name": opp.get("company", ""),
                    "location": opp.get("location", ""),
                    "salary_range": opp.get("salary_range", ""),
                    "job_url": opp.get("url", ""),
                    "description": opp.get("description", ""),
                    "requirements": opp.get("requirements", []),
                    "posted_date": opp.get("posted_date", datetime.now().isoformat()),
                    "match_score": opp.get("match_score", 0.0),
                    "source_system": "linkedin",
                    "retrieved_at": datetime.now().isoformat()
                }
                export_data["opportunities"].append(external_format)
            
            # Save as JSON for external pipeline
            export_file = self.exchange_dir / "outgoing" / f"linkedin_opportunities_{timestamp}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Also save in format expected by external pipeline
            external_format_file = self.exchange_dir / "shared_config" / "latest_linkedin_opportunities.json"
            with open(external_format_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(opportunities)} LinkedIn opportunities to {export_file}")
            return export_file
            
        except Exception as e:
            logger.error(f"Failed to export LinkedIn opportunities: {e}")
            return None
    
    def import_external_opportunities(self) -> List[JobOpportunity]:
        """Import opportunities from external job pipeline"""
        try:
            opportunities = []
            
            # Check for incoming files from external pipeline
            incoming_files = list(self.exchange_dir.glob("incoming/*.json"))
            
            for file_path in incoming_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convert external format to our unified format
                    if isinstance(data, dict) and "opportunities" in data:
                        for opp_data in data["opportunities"]:
                            opportunity = self._convert_external_to_unified(opp_data)
                            if opportunity:
                                opportunities.append(opportunity)
                    elif isinstance(data, list):
                        for opp_data in data:
                            opportunity = self._convert_external_to_unified(opp_data)
                            if opportunity:
                                opportunities.append(opportunity)
                    
                    # Move processed file
                    processed_path = self.exchange_dir / "processed" / f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
                    file_path.rename(processed_path)
                    
                except Exception as e:
                    logger.error(f"Failed to process incoming file {file_path}: {e}")
                    continue
            
            # Also check shared configuration files
            shared_files = [
                self.exchange_dir / "shared_config" / "latest_external_opportunities.json",
                self.exchange_dir / "shared_config" / "external_pipeline_results.json"
            ]
            
            for shared_file in shared_files:
                if shared_file.exists():
                    try:
                        with open(shared_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if isinstance(data, dict) and "opportunities" in data:
                            for opp_data in data["opportunities"]:
                                opportunity = self._convert_external_to_unified(opp_data)
                                if opportunity:
                                    opportunities.append(opportunity)
                    
                    except Exception as e:
                        logger.error(f"Failed to process shared file {shared_file}: {e}")
            
            logger.info(f"Imported {len(opportunities)} opportunities from external pipeline")
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to import external opportunities: {e}")
            return []
    
    def _convert_external_to_unified(self, opp_data: Dict[str, Any]) -> Optional[JobOpportunity]:
        """Convert external pipeline data to unified JobOpportunity format"""
        try:
            # Handle different field name variations
            field_mappings = {
                'id': ['id', 'job_id', 'opportunity_id', 'identifier', 'unique_id'],
                'title': ['title', 'job_title', 'position', 'role', 'job_name'],
                'company': ['company', 'company_name', 'employer', 'organization'],
                'location': ['location', 'city', 'address', 'workplace', 'job_location'],
                'salary_range': ['salary', 'salary_range', 'compensation', 'pay', 'salary_info'],
                'url': ['url', 'link', 'job_url', 'application_url', 'apply_url'],
                'description': ['description', 'job_description', 'details', 'summary'],
                'requirements': ['requirements', 'qualifications', 'skills', 'criteria', 'skills_required'],
                'posted_date': ['posted_date', 'date_posted', 'created_date', 'publish_date', 'post_date']
            }
            
            # Extract fields using mappings
            extracted_data = {}
            for unified_field, possible_names in field_mappings.items():
                for name in possible_names:
                    if name in opp_data and opp_data[name]:
                        extracted_data[unified_field] = opp_data[name]
                        break
            
            # Set defaults for missing required fields
            opportunity_id = extracted_data.get('id', f"ext_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(opp_data))}")
            title = extracted_data.get('title', 'Unknown Position')
            company = extracted_data.get('company', 'Unknown Company')
            location = extracted_data.get('location', 'Unknown Location')
            salary_range = extracted_data.get('salary_range', 'Not specified')
            url = extracted_data.get('url', '')
            description = extracted_data.get('description', '')
            requirements = extracted_data.get('requirements', [])
            
            # Handle posted_date conversion
            posted_date = datetime.now()
            if 'posted_date' in extracted_data:
                try:
                    if isinstance(extracted_data['posted_date'], str):
                        posted_date = datetime.fromisoformat(extracted_data['posted_date'].replace('Z', '+00:00'))
                    elif isinstance(extracted_data['posted_date'], datetime):
                        posted_date = extracted_data['posted_date']
                except:
                    posted_date = datetime.now()
            
            # Ensure requirements is a list
            if isinstance(requirements, str):
                requirements = [requirements]
            elif not isinstance(requirements, list):
                requirements = []
            
            # Extract match score
            match_score = opp_data.get('match_score', opp_data.get('score', 0.0))
            if isinstance(match_score, str):
                try:
                    match_score = float(match_score)
                except:
                    match_score = 0.0
            
            opportunity = JobOpportunity(
                id=opportunity_id,
                title=title,
                company=company,
                location=location,
                salary_range=salary_range,
                source="external_pipeline",
                url=url,
                description=description,
                requirements=requirements,
                posted_date=posted_date,
                match_score=match_score,
                retrieved_at=datetime.now()
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to convert external opportunity data: {e}")
            return None
    
    def share_search_configuration(self, config: Dict[str, Any]):
        """Share search configuration with external pipeline"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create comprehensive search configuration
            search_config = {
                "source": "job_search_intelligence",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "config": {
                    "job_titles": config.get("job_titles", []),
                    "companies": config.get("companies", []),
                    "locations": config.get("locations", []),
                    "experience_levels": config.get("experience_levels", []),
                    "skills": config.get("skills", []),
                    "salary_range": {
                        "min": config.get("salary_min", 0),
                        "max": config.get("salary_max", 0),
                        "currency": config.get("currency", "USD")
                    },
                    "remote_work": config.get("remote_work", True),
                    "contract_types": config.get("contract_types", ["full-time", "contract"]),
                    "exclusions": {
                        "companies": config.get("excluded_companies", []),
                        "keywords": config.get("excluded_keywords", [])
                    }
                },
                "preferences": {
                    "max_results": config.get("max_results", 50),
                    "date_range_days": config.get("date_range_days", 7),
                    "min_match_score": config.get("min_match_score", 0.6)
                }
            }
            
            # Save to shared configuration
            config_file = self.exchange_dir / "shared_config" / "search_configuration.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(search_config, f, indent=2, ensure_ascii=False)
            
            # Also save timestamped version
            timestamped_file = self.exchange_dir / "outgoing" / f"search_config_{timestamp}.json"
            with open(timestamped_file, 'w', encoding='utf-8') as f:
                json.dump(search_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Shared search configuration with external pipeline: {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to share search configuration: {e}")
    
    def get_external_search_configuration(self) -> Optional[Dict[str, Any]]:
        """Get search configuration from external pipeline"""
        try:
            # Check for configuration from external pipeline
            external_config_files = [
                self.exchange_dir / "incoming" / "external_search_config.json",
                self.exchange_dir / "shared_config" / "external_search_configuration.json"
            ]
            
            for config_file in external_config_files:
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    logger.info(f"Retrieved external search configuration from {config_file}")
                    return config
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get external search configuration: {e}")
            return None
    
    def sync_application_status(self, opportunity_id: str, status: str, notes: str = ""):
        """Sync application status between systems"""
        try:
            # Update in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE shared_opportunities 
                SET application_status = ?, notes = ?
                WHERE id = ?
            ''', (status, notes, opportunity_id))
            
            conn.commit()
            conn.close()
            
            # Create status update message
            status_update = {
                "source": "job_search_intelligence",
                "timestamp": datetime.now().isoformat(),
                "type": "application_status_update",
                "data": {
                    "opportunity_id": opportunity_id,
                    "status": status,
                    "notes": notes,
                    "updated_at": datetime.now().isoformat()
                }
            }
            
            # Save for external pipeline
            status_file = self.exchange_dir / "outgoing" / f"status_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_update, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Synced application status for {opportunity_id}: {status}")
            
        except Exception as e:
            logger.error(f"Failed to sync application status: {e}")
    
    def create_daily_sync_report(self) -> Dict[str, Any]:
        """Create a daily synchronization report"""
        try:
            integrator = get_integrator()
            
            # Get recent opportunities from both systems
            linkedin_opps = integrator.get_linkedin_opportunities()
            external_opps = self.import_external_opportunities()
            
            # Create comprehensive report
            report = {
                "date": datetime.now().isoformat(),
                "sync_summary": {
                    "linkedin_opportunities": len(linkedin_opps),
                    "external_opportunities": len(external_opps),
                    "total_unique": len(set([opp.id for opp in linkedin_opps + external_opps]))
                },
                "data_exchange": {
                    "outgoing_files": len(list(self.exchange_dir.glob("outgoing/*.json"))),
                    "incoming_files": len(list(self.exchange_dir.glob("incoming/*.json"))),
                    "processed_files": len(list(self.exchange_dir.glob("processed/*.json")))
                },
                "application_statuses": {},
                "top_opportunities": [],
                "system_health": {
                    "database_accessible": True,
                    "external_pipeline_reachable": len(getattr(integrator, 'available_modules', [])) > 0,
                    "data_directories_accessible": all([
                        self.exchange_dir.exists(),
                        (self.exchange_dir / "outgoing").exists(),
                        (self.exchange_dir / "incoming").exists()
                    ])
                }
            }
            
            # Add top opportunities (highest match scores)
            all_opportunities = linkedin_opps + external_opps
            top_opportunities = sorted(all_opportunities, key=lambda x: x.match_score, reverse=True)[:10]
            
            for opp in top_opportunities:
                report["top_opportunities"].append({
                    "id": opp.id,
                    "title": opp.title,
                    "company": opp.company,
                    "match_score": opp.match_score,
                    "source": opp.source
                })
            
            # Count application statuses
            for opp in all_opportunities:
                status = opp.application_status
                report["application_statuses"][status] = report["application_statuses"].get(status, 0) + 1
            
            # Save report
            report_file = self.data_dir / f"sync_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created daily sync report: {report_file}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to create daily sync report: {e}")
            return {"error": str(e)}

# Global data exchange manager instance
_data_manager = None

def get_data_manager() -> DataExchangeManager:
    """Get or create global data exchange manager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataExchangeManager()
    return _data_manager

# Convenience functions for easy integration
def sync_all_data():
    """Perform complete data synchronization between systems"""
    manager = get_data_manager()
    integrator = get_integrator()
    
    # Import from external pipeline
    external_opportunities = manager.import_external_opportunities()
    logger.info(f"Imported {len(external_opportunities)} opportunities from external pipeline")
    
    # Export LinkedIn opportunities
    linkedin_opportunities = integrator.get_linkedin_opportunities()
    linkedin_data = [asdict(opp) for opp in linkedin_opportunities]
    manager.export_linkedin_opportunities(linkedin_data)
    
    # Create sync report
    report = manager.create_daily_sync_report()
    
    return {
        "external_imported": len(external_opportunities),
        "linkedin_exported": len(linkedin_opportunities),
        "sync_report": report
    }

if __name__ == "__main__":
    # Test data exchange
    manager = DataExchangeManager()
    
    # Test sync
    result = sync_all_data()
    print(f"Sync completed: {result}")