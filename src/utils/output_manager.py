"""
Enhanced Output Management System for Job Search Intelligence
Provides organized file structure and database integration
"""
import os
import json
import sqlite3
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import asyncio
import aiosqlite

@dataclass
class AnalysisSession:
    """Represents an analysis session"""
    session_id: str
    timestamp: str
    analysis_type: str
    profile_id: str
    status: str
    duration_seconds: float
    results_path: str

class OutputManager:
    """
    Enhanced output management with organized structure and database integration
    """
    
    def __init__(self, base_path: str = "output", db_path: str = "data/job_search.db"):
        self.base_path = Path(base_path)
        self.db_path = Path(db_path)
        self.session_id = None
        self._setup_directories()
        
    def _setup_directories(self):
        """Create organized directory structure"""
        directories = [
            self.base_path / "reports" / "daily",
            self.base_path / "reports" / "weekly", 
            self.base_path / "reports" / "monthly",
            self.base_path / "analyses" / "profiles",
            self.base_path / "analyses" / "networks",
            self.base_path / "analyses" / "insights",
            self.base_path / "exports" / "csv",
            self.base_path / "exports" / "json",
            self.base_path / "exports" / "excel",
            self.base_path / "visualizations" / "graphs",
            self.base_path / "visualizations" / "charts",
            self.base_path / "archive" / str(datetime.now().year),
            self.base_path / "raw_data",
            self.base_path / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def start_session(self, analysis_type: str, profile_id: str = "default") -> str:
        """Start a new analysis session"""
        timestamp = datetime.now(timezone.utc)
        self.session_id = f"{analysis_type}_{profile_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Create session directory
        session_dir = self.base_path / "analyses" / analysis_type / self.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        return self.session_id
        
    def get_timestamped_filename(self, base_name: str, extension: str = "json") -> str:
        """Generate timestamped filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{extension}"
        
    def save_analysis_results(self, 
                            analysis_type: str,
                            data: Dict[str, Any], 
                            profile_id: str = "default",
                            save_to_db: bool = True) -> str:
        """Save analysis results with proper organization"""
        
        # Generate paths
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")
        
        # Organize by analysis type
        if analysis_type == "ai_insights":
            base_dir = self.base_path / "analyses" / "insights"
            filename = f"insights_{profile_id}_{date_str}_{time_str}.json"
        elif analysis_type == "network_analysis":
            base_dir = self.base_path / "analyses" / "networks"
            filename = f"network_{profile_id}_{date_str}_{time_str}.json"
        elif analysis_type == "profile_analysis":
            base_dir = self.base_path / "analyses" / "profiles"
            filename = f"profile_{profile_id}_{date_str}_{time_str}.json"
        else:
            base_dir = self.base_path / "analyses" / "general"
            filename = f"{analysis_type}_{profile_id}_{date_str}_{time_str}.json"
            
        base_dir.mkdir(parents=True, exist_ok=True)
        file_path = base_dir / filename
        
        # Add metadata
        enhanced_data = {
            "metadata": {
                "analysis_type": analysis_type,
                "profile_id": profile_id,
                "timestamp": timestamp.isoformat(),
                "session_id": self.session_id,
                "file_path": str(file_path)
            },
            "data": data
        }
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
        # Save to database if requested
        if save_to_db:
            asyncio.create_task(self._save_to_database(enhanced_data))
            
        return str(file_path)
        
    def save_export(self, data: Any, filename: str, format_type: str = "json") -> str:
        """Save export files with organization"""
        export_dir = self.base_path / "exports" / format_type
        export_dir.mkdir(parents=True, exist_ok=True)
        
        timestamped_filename = self.get_timestamped_filename(filename, format_type)
        file_path = export_dir / timestamped_filename
        
        if format_type == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format_type == "csv":
            if isinstance(data, pd.DataFrame):
                data.to_csv(file_path, index=False)
            else:
                pd.DataFrame(data).to_csv(file_path, index=False)
        elif format_type == "excel":
            if isinstance(data, pd.DataFrame):
                data.to_excel(file_path, index=False)
            else:
                pd.DataFrame(data).to_excel(file_path, index=False)
                
        return str(file_path)
        
    def generate_daily_report(self, date: Optional[datetime] = None, formats: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate daily summary report in multiple formats"""
        if date is None:
            date = datetime.now()
        if formats is None:
            formats = ["json", "csv"]
            
        date_str = date.strftime("%Y%m%d")
        report_dir = self.base_path / "reports" / "daily"
        report_paths = {}
        
        # Collect all analyses from the day
        analyses_today = []
        for analysis_dir in (self.base_path / "analyses").iterdir():
            if analysis_dir.is_dir():
                for file_path in analysis_dir.rglob(f"*{date_str}*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            analysis = json.load(f)
                            analyses_today.append({
                                "file": str(file_path.relative_to(self.base_path)),
                                "type": analysis.get("metadata", {}).get("analysis_type", "unknown"),
                                "timestamp": analysis.get("metadata", {}).get("timestamp", ""),
                                "profile_id": analysis.get("metadata", {}).get("profile_id", "")
                            })
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue
                        
        report_data = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "total_analyses": len(analyses_today),
            "analyses": analyses_today,
            "summary": {
                "ai_insights": len([a for a in analyses_today if a["type"] == "ai_insights"]),
                "network_analyses": len([a for a in analyses_today if a["type"] == "network_analysis"]),
                "profile_analyses": len([a for a in analyses_today if a["type"] == "profile_analysis"])
            }
        }
        
        # Generate reports in requested formats
        for format_type in formats:
            if format_type == "json":
                json_path = report_dir / f"daily_report_{date_str}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                report_paths["json"] = str(json_path)
                
            elif format_type == "csv":
                csv_path = report_dir / f"daily_report_{date_str}.csv"
                
                # Create CSV-friendly summary data
                summary_rows = [
                    {"Metric": "Total Analyses", "Value": report_data["total_analyses"]},
                    {"Metric": "AI Insights", "Value": report_data["summary"]["ai_insights"]},
                    {"Metric": "Network Analyses", "Value": report_data["summary"]["network_analyses"]},
                    {"Metric": "Profile Analyses", "Value": report_data["summary"]["profile_analyses"]},
                    {"Metric": "Generated At", "Value": report_data["generated_at"]}
                ]
                
                # Save summary as CSV
                summary_df = pd.DataFrame(summary_rows)
                summary_df.to_csv(csv_path, index=False)
                report_paths["csv"] = str(csv_path)
                
                # Also save detailed analyses as CSV
                if analyses_today:
                    detailed_csv_path = report_dir / f"daily_analyses_detailed_{date_str}.csv"
                    analyses_df = pd.DataFrame(analyses_today)
                    analyses_df.to_csv(detailed_csv_path, index=False)
                    report_paths["csv_detailed"] = str(detailed_csv_path)
            
        return report_paths
        
    def generate_weekly_report(self, date: Optional[datetime] = None, formats: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate weekly summary report"""
        if date is None:
            date = datetime.now()
        if formats is None:
            formats = ["json", "csv"]
            
        # Get start of week (Monday)
        start_of_week = date - pd.Timedelta(days=date.weekday())
        week_str = start_of_week.strftime("%Y_W%U")  # Year_WeekNumber
        
        report_dir = self.base_path / "reports" / "weekly"
        report_paths = {}
        
        # Collect all analyses from the week
        analyses_this_week = []
        for day_offset in range(7):
            day_date = start_of_week + pd.Timedelta(days=day_offset)
            day_str = day_date.strftime("%Y%m%d")
            
            for analysis_dir in (self.base_path / "analyses").iterdir():
                if analysis_dir.is_dir():
                    for file_path in analysis_dir.rglob(f"*{day_str}*.json"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                analysis = json.load(f)
                                analyses_this_week.append({
                                    "file": str(file_path.relative_to(self.base_path)),
                                    "type": analysis.get("metadata", {}).get("analysis_type", "unknown"),
                                    "timestamp": analysis.get("metadata", {}).get("timestamp", ""),
                                    "profile_id": analysis.get("metadata", {}).get("profile_id", ""),
                                    "day": day_date.strftime("%Y-%m-%d")
                                })
                        except (json.JSONDecodeError, FileNotFoundError):
                            continue
        
        # Generate weekly summary
        weekly_data = {
            "week": week_str,
            "week_start": start_of_week.strftime("%Y-%m-%d"),
            "week_end": (start_of_week + pd.Timedelta(days=6)).strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "total_analyses": len(analyses_this_week),
            "analyses": analyses_this_week,
            "daily_breakdown": {},
            "summary": {
                "ai_insights": len([a for a in analyses_this_week if a["type"] == "ai_insights"]),
                "network_analyses": len([a for a in analyses_this_week if a["type"] == "network_analysis"]),
                "profile_analyses": len([a for a in analyses_this_week if a["type"] == "profile_analysis"])
            }
        }
        
        # Calculate daily breakdown
        for day_offset in range(7):
            day_date = start_of_week + pd.Timedelta(days=day_offset)
            day_key = day_date.strftime("%Y-%m-%d")
            day_analyses = [a for a in analyses_this_week if a["day"] == day_key]
            weekly_data["daily_breakdown"][day_key] = len(day_analyses)
        
        # Save in requested formats
        for format_type in formats:
            if format_type == "json":
                json_path = report_dir / f"weekly_report_{week_str}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(weekly_data, f, indent=2, ensure_ascii=False)
                report_paths["json"] = str(json_path)
                
            elif format_type == "csv":
                csv_path = report_dir / f"weekly_report_{week_str}.csv"
                summary_rows = [
                    {"Metric": "Week", "Value": week_str},
                    {"Metric": "Week Start", "Value": weekly_data["week_start"]},
                    {"Metric": "Week End", "Value": weekly_data["week_end"]},
                    {"Metric": "Total Analyses", "Value": weekly_data["total_analyses"]},
                    {"Metric": "AI Insights", "Value": weekly_data["summary"]["ai_insights"]},
                    {"Metric": "Network Analyses", "Value": weekly_data["summary"]["network_analyses"]},
                    {"Metric": "Profile Analyses", "Value": weekly_data["summary"]["profile_analyses"]}
                ]
                
                summary_df = pd.DataFrame(summary_rows)
                summary_df.to_csv(csv_path, index=False)
                report_paths["csv"] = str(csv_path)
                
                # Daily breakdown CSV
                if weekly_data["daily_breakdown"]:
                    daily_csv_path = report_dir / f"weekly_daily_breakdown_{week_str}.csv"
                    daily_data = [{"Date": k, "Analyses": v} for k, v in weekly_data["daily_breakdown"].items()]
                    daily_df = pd.DataFrame(daily_data)
                    daily_df.to_csv(daily_csv_path, index=False)
                    report_paths["csv_daily"] = str(daily_csv_path)
        
        return report_paths
        
    def generate_monthly_report(self, date: Optional[datetime] = None, formats: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate monthly summary report"""
        if date is None:
            date = datetime.now()
        if formats is None:
            formats = ["json", "csv"]
            
        month_str = date.strftime("%Y_%m")
        report_dir = self.base_path / "reports" / "monthly"
        report_paths = {}
        
        # Get first and last day of month
        first_day = date.replace(day=1)
        if date.month == 12:
            last_day = date.replace(year=date.year + 1, month=1, day=1) - pd.Timedelta(days=1)
        else:
            last_day = date.replace(month=date.month + 1, day=1) - pd.Timedelta(days=1)
        
        # Collect all analyses from the month
        analyses_this_month = []
        current_date = first_day
        while current_date <= last_day:
            day_str = current_date.strftime("%Y%m%d")
            
            for analysis_dir in (self.base_path / "analyses").iterdir():
                if analysis_dir.is_dir():
                    for file_path in analysis_dir.rglob(f"*{day_str}*.json"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                analysis = json.load(f)
                                analyses_this_month.append({
                                    "file": str(file_path.relative_to(self.base_path)),
                                    "type": analysis.get("metadata", {}).get("analysis_type", "unknown"),
                                    "timestamp": analysis.get("metadata", {}).get("timestamp", ""),
                                    "profile_id": analysis.get("metadata", {}).get("profile_id", ""),
                                    "day": current_date.strftime("%Y-%m-%d")
                                })
                        except (json.JSONDecodeError, FileNotFoundError):
                            continue
            
            current_date += pd.Timedelta(days=1)
        
        # Generate monthly summary
        monthly_data = {
            "month": month_str,
            "month_name": date.strftime("%B %Y"),
            "month_start": first_day.strftime("%Y-%m-%d"),
            "month_end": last_day.strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "total_analyses": len(analyses_this_month),
            "analyses": analyses_this_month,
            "weekly_breakdown": {},
            "summary": {
                "ai_insights": len([a for a in analyses_this_month if a["type"] == "ai_insights"]),
                "network_analyses": len([a for a in analyses_this_month if a["type"] == "network_analysis"]),
                "profile_analyses": len([a for a in analyses_this_month if a["type"] == "profile_analysis"])
            }
        }
        
        # Calculate weekly breakdown
        current_date = first_day
        while current_date <= last_day:
            week_start = current_date - pd.Timedelta(days=current_date.weekday())
            week_key = week_start.strftime("Week_%Y_%U")
            week_analyses = [a for a in analyses_this_month 
                           if week_start <= pd.to_datetime(a["day"]) < week_start + pd.Timedelta(days=7)]
            monthly_data["weekly_breakdown"][week_key] = len(week_analyses)
            current_date += pd.Timedelta(days=7)
        
        # Save in requested formats
        for format_type in formats:
            if format_type == "json":
                json_path = report_dir / f"monthly_report_{month_str}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(monthly_data, f, indent=2, ensure_ascii=False)
                report_paths["json"] = str(json_path)
                
            elif format_type == "csv":
                csv_path = report_dir / f"monthly_report_{month_str}.csv"
                summary_rows = [
                    {"Metric": "Month", "Value": monthly_data["month_name"]},
                    {"Metric": "Month Start", "Value": monthly_data["month_start"]},
                    {"Metric": "Month End", "Value": monthly_data["month_end"]},
                    {"Metric": "Total Analyses", "Value": monthly_data["total_analyses"]},
                    {"Metric": "AI Insights", "Value": monthly_data["summary"]["ai_insights"]},
                    {"Metric": "Network Analyses", "Value": monthly_data["summary"]["network_analyses"]},
                    {"Metric": "Profile Analyses", "Value": monthly_data["summary"]["profile_analyses"]}
                ]
                
                summary_df = pd.DataFrame(summary_rows)
                summary_df.to_csv(csv_path, index=False)
                report_paths["csv"] = str(csv_path)
        
        return report_paths
        
    async def _save_to_database(self, data: Dict[str, Any]):
        """Save analysis results to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Ensure tables exist
                await self._create_tables(db)
                
                metadata = data.get("metadata", {})
                
                # Insert analysis session
                await db.execute("""
                    INSERT OR REPLACE INTO analysis_sessions 
                    (session_id, timestamp, analysis_type, profile_id, status, file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metadata.get("session_id"),
                    metadata.get("timestamp"),
                    metadata.get("analysis_type"),
                    metadata.get("profile_id"),
                    "completed",
                    metadata.get("file_path")
                ))
                
                # Insert analysis results
                results_json = json.dumps(data.get("data", {}))
                await db.execute("""
                    INSERT INTO analysis_results 
                    (session_id, analysis_type, profile_id, timestamp, results_json, file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metadata.get("session_id"),
                    metadata.get("analysis_type"),
                    metadata.get("profile_id"),
                    metadata.get("timestamp"),
                    results_json,
                    metadata.get("file_path")
                ))
                
                await db.commit()
                
        except Exception as e:
            print(f"Database save error: {e}")
            
    async def _create_tables(self, db):
        """Create database tables if they don't exist"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                session_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                status TEXT DEFAULT 'in_progress',
                duration_seconds REAL,
                file_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                results_json TEXT,
                file_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS network_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                connection_name TEXT,
                connection_title TEXT,
                connection_company TEXT,
                connection_url TEXT,
                relationship_type TEXT,
                timestamp TEXT NOT NULL,
                session_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS profile_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_type TEXT,
                timestamp TEXT NOT NULL,
                session_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
            )
        """)
        
    def cleanup_old_files(self, days_to_keep: int = 30):
        """Clean up old files (move to archive)"""
        cutoff_date = datetime.now() - pd.Timedelta(days=days_to_keep)
        archive_dir = self.base_path / "archive" / str(cutoff_date.year)
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        moved_count = 0
        for file_path in self.base_path.rglob("*.json"):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                if "archive" not in str(file_path):
                    new_path = archive_dir / file_path.name
                    file_path.rename(new_path)
                    moved_count += 1
                    
        return moved_count
        
    def get_analysis_history(self, analysis_type: Optional[str] = None, 
                           profile_id: Optional[str] = None,
                           days: int = 30) -> List[Dict]:
        """Get analysis history from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
                SELECT * FROM analysis_sessions 
                WHERE datetime(timestamp) >= datetime('now', '-{} days')
            """.format(days)
            
            conditions = []
            params = []
            
            if analysis_type:
                conditions.append("analysis_type = ?")
                params.append(analysis_type)
                
            if profile_id:
                conditions.append("profile_id = ?")
                params.append(profile_id)
                
            if conditions:
                query += " AND " + " AND ".join(conditions)
                
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"Error retrieving history: {e}")
            return []

# Usage example
def create_output_manager() -> OutputManager:
    """Factory function to create configured output manager"""
    return OutputManager()
