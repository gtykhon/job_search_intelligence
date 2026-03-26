"""
Database Schema Setup for Job Search Intelligence
Creates tables and organizes existing data
"""
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

def setup_database_schema(db_path: str = "data/job_search.db"):
    """Create complete database schema"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Analysis Sessions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            session_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            profile_id TEXT NOT NULL,
            status TEXT DEFAULT 'completed',
            duration_seconds REAL,
            file_path TEXT,
            ai_provider TEXT,
            ai_model TEXT,
            confidence_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Analysis Results Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            profile_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            results_json TEXT,
            file_path TEXT,
            summary TEXT,
            key_insights TEXT,
            recommendations TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    """)
    
    # Network Connections Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            connection_name TEXT,
            connection_title TEXT,
            connection_company TEXT,
            connection_url TEXT,
            connection_location TEXT,
            relationship_type TEXT,
            connection_strength REAL,
            mutual_connections INTEGER,
            timestamp TEXT NOT NULL,
            session_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    """)
    
    # Profile Metrics Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            metric_type TEXT,
            metric_category TEXT,
            timestamp TEXT NOT NULL,
            session_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    """)
    
    # AI Insights Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            insight_category TEXT,
            insight_title TEXT,
            insight_description TEXT,
            insight_score REAL,
            actionable_recommendation TEXT,
            priority_level TEXT,
            timestamp TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    """)
    
    # Network Analysis Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            total_connections INTEGER,
            industry_diversity_score REAL,
            geographic_spread_score REAL,
            seniority_distribution TEXT,
            top_companies TEXT,
            top_industries TEXT,
            growth_potential_score REAL,
            timestamp TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        )
    """)
    
    # Weekly Performance Tracking Tables - New Addition for Job Search Intelligence
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start_date TEXT NOT NULL,
            week_end_date TEXT NOT NULL,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            leadership_engagement_count INTEGER DEFAULT 0,
            total_engagement_count INTEGER DEFAULT 0,
            leadership_engagement_percentage REAL DEFAULT 0.0,
            f500_profile_views INTEGER DEFAULT 0,
            total_profile_views INTEGER DEFAULT 0,
            f500_penetration_percentage REAL DEFAULT 0.0,
            senior_connections_count INTEGER DEFAULT 0,
            total_connections_count INTEGER DEFAULT 0,
            recruiter_messages_count INTEGER DEFAULT 0,
            comment_quality_score REAL DEFAULT 0.0,
            alert_status TEXT DEFAULT 'green',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(week_start_date, week_end_date)
        )
    """)
    
    # Post Performance Tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE NOT NULL,
            post_date TEXT NOT NULL,
            post_topic TEXT,
            post_content_preview TEXT,
            impressions INTEGER DEFAULT 0,
            total_engagement INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            shares_count INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            leadership_engagement_count INTEGER DEFAULT 0,
            leadership_engagement_percentage REAL DEFAULT 0.0,
            f500_engagement_count INTEGER DEFAULT 0,
            f500_engagement_percentage REAL DEFAULT 0.0,
            comment_quality_score REAL DEFAULT 0.0,
            week_start_date TEXT NOT NULL,
            alert_status TEXT DEFAULT 'green',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (week_start_date) REFERENCES weekly_metrics(week_start_date)
        )
    """)
    
    # Engagement Details (who engaged)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS engagement_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL,
            engager_name TEXT,
            engager_title TEXT,
            engager_company TEXT,
            engagement_type TEXT NOT NULL,
            is_leadership BOOLEAN DEFAULT FALSE,
            is_f500 BOOLEAN DEFAULT FALSE,
            is_senior_role BOOLEAN DEFAULT FALSE,
            comment_text TEXT,
            comment_quality_score REAL DEFAULT 0.0,
            engagement_timestamp TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES post_performance(post_id)
        )
    """)
    
    # Profile Viewers Tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_viewers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            viewer_name TEXT,
            viewer_title TEXT,
            viewer_company TEXT,
            viewer_location TEXT,
            is_leadership BOOLEAN DEFAULT FALSE,
            is_f500 BOOLEAN DEFAULT FALSE,
            is_recruiter BOOLEAN DEFAULT FALSE,
            view_reason TEXT,
            view_date TEXT NOT NULL,
            week_start_date TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (week_start_date) REFERENCES weekly_metrics(week_start_date)
        )
    """)
    
    # Connection Requests Tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connection_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_name TEXT,
            requester_title TEXT,
            requester_company TEXT,
            requester_location TEXT,
            request_message TEXT,
            is_senior_role BOOLEAN DEFAULT FALSE,
            is_leadership BOOLEAN DEFAULT FALSE,
            is_f500 BOOLEAN DEFAULT FALSE,
            request_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            week_start_date TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (week_start_date) REFERENCES weekly_metrics(week_start_date)
        )
    """)
    
    # Fortune 500 Companies Reference
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fortune_500_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT UNIQUE NOT NULL,
            rank_2024 INTEGER,
            industry TEXT,
            revenue_billions REAL,
            employees_count INTEGER,
            website TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Leadership Titles Reference
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leadership_titles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_pattern TEXT UNIQUE NOT NULL,
            title_level TEXT NOT NULL,
            is_c_level BOOLEAN DEFAULT FALSE,
            is_vp_level BOOLEAN DEFAULT FALSE,
            is_director_level BOOLEAN DEFAULT FALSE,
            seniority_score INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Weekly Dashboard Cache (for fast 30-second dashboard)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            cache_data TEXT NOT NULL,
            cache_type TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for better performance (including new weekly tracking indexes)
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON analysis_sessions(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_type ON analysis_sessions(analysis_type)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_profile ON analysis_sessions(profile_id)",
        "CREATE INDEX IF NOT EXISTS idx_results_session ON analysis_results(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_connections_profile ON network_connections(profile_id)",
        "CREATE INDEX IF NOT EXISTS idx_connections_session ON network_connections(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_metrics_profile ON profile_metrics(profile_id)",
        "CREATE INDEX IF NOT EXISTS idx_insights_session ON ai_insights(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_network_session ON network_analysis(session_id)",
        # New indexes for weekly tracking
        "CREATE INDEX IF NOT EXISTS idx_weekly_metrics_date ON weekly_metrics(week_start_date)",
        "CREATE INDEX IF NOT EXISTS idx_weekly_metrics_year_week ON weekly_metrics(year, week_number)",
        "CREATE INDEX IF NOT EXISTS idx_post_performance_date ON post_performance(post_date)",
        "CREATE INDEX IF NOT EXISTS idx_post_performance_week ON post_performance(week_start_date)",
        "CREATE INDEX IF NOT EXISTS idx_engagement_details_post ON engagement_details(post_id)",
        "CREATE INDEX IF NOT EXISTS idx_engagement_details_leadership ON engagement_details(is_leadership)",
        "CREATE INDEX IF NOT EXISTS idx_profile_viewers_week ON profile_viewers(week_start_date)",
        "CREATE INDEX IF NOT EXISTS idx_profile_viewers_f500 ON profile_viewers(is_f500)",
        "CREATE INDEX IF NOT EXISTS idx_connection_requests_week ON connection_requests(week_start_date)",
        "CREATE INDEX IF NOT EXISTS idx_connection_requests_senior ON connection_requests(is_senior_role)",
        "CREATE INDEX IF NOT EXISTS idx_dashboard_cache_key ON dashboard_cache(cache_key)",
        "CREATE INDEX IF NOT EXISTS idx_dashboard_cache_expires ON dashboard_cache(expires_at)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    conn.close()
    
    print("✅ Database schema created successfully!")
    
    # Initialize reference data
    _initialize_reference_data(db_path)
    
    return True


def _initialize_reference_data(db_path: str):
    """Initialize Fortune 500 companies and leadership titles reference data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Sample Fortune 500 companies (top 50 for demo)
    fortune_500_companies = [
        ("Apple", 1, "Technology", 365.8, 154000),
        ("Microsoft", 2, "Technology", 198.3, 221000),
        ("Alphabet", 3, "Technology", 282.8, 156500),
        ("Amazon", 4, "E-commerce/Cloud", 469.8, 1540000),
        ("Tesla", 5, "Automotive/Energy", 96.8, 127855),
        ("Meta", 6, "Technology", 117.9, 86482),
        ("Berkshire Hathaway", 7, "Conglomerate", 302.1, 396500),
        ("JPMorgan Chase", 8, "Financial Services", 162.4, 293723),
        ("Johnson & Johnson", 9, "Healthcare", 93.8, 152700),
        ("Procter & Gamble", 10, "Consumer Goods", 80.2, 101000),
        ("Visa", 11, "Financial Services", 29.3, 26500),
        ("Home Depot", 12, "Retail", 157.4, 475000),
        ("Mastercard", 13, "Financial Services", 22.2, 33400),
        ("Bank of America", 14, "Financial Services", 119.0, 216823),
        ("Pfizer", 15, "Healthcare", 100.3, 83000),
        ("Walmart", 16, "Retail", 611.3, 2100000),
        ("UnitedHealth Group", 17, "Healthcare", 324.2, 400000),
        ("Chevron", 18, "Energy", 200.5, 47600),
        ("Coca-Cola", 19, "Beverages", 43.0, 82500),
        ("Adobe", 20, "Software", 19.4, 29239)
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO fortune_500_companies 
        (company_name, rank_2024, industry, revenue_billions, employees_count)
        VALUES (?, ?, ?, ?, ?)
    """, fortune_500_companies)
    
    # Leadership title patterns
    leadership_titles = [
        ("CEO", "C-Level", True, False, False, 10),
        ("Chief Executive Officer", "C-Level", True, False, False, 10),
        ("CTO", "C-Level", True, False, False, 10),
        ("Chief Technology Officer", "C-Level", True, False, False, 10),
        ("CIO", "C-Level", True, False, False, 10),
        ("Chief Information Officer", "C-Level", True, False, False, 10),
        ("CFO", "C-Level", True, False, False, 10),
        ("Chief Financial Officer", "C-Level", True, False, False, 10),
        ("COO", "C-Level", True, False, False, 10),
        ("Chief Operating Officer", "C-Level", True, False, False, 10),
        ("VP", "VP-Level", False, True, False, 8),
        ("Vice President", "VP-Level", False, True, False, 8),
        ("SVP", "VP-Level", False, True, False, 9),
        ("Senior Vice President", "VP-Level", False, True, False, 9),
        ("EVP", "VP-Level", False, True, False, 9),
        ("Executive Vice President", "VP-Level", False, True, False, 9),
        ("Director", "Director-Level", False, False, True, 7),
        ("Senior Director", "Director-Level", False, False, True, 8),
        ("Engineering Manager", "Manager-Level", False, False, False, 6),
        ("Staff Engineer", "Senior-IC", False, False, False, 7),
        ("Principal Engineer", "Senior-IC", False, False, False, 8),
        ("Senior Staff Engineer", "Senior-IC", False, False, False, 8),
        ("Distinguished Engineer", "Senior-IC", False, False, False, 9),
        ("Fellow", "Senior-IC", False, False, False, 10)
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO leadership_titles 
        (title_pattern, title_level, is_c_level, is_vp_level, is_director_level, seniority_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, leadership_titles)
    
    conn.commit()
    conn.close()
    
    print("✅ Reference data initialized!")


def migrate_existing_output_files():
    """Organize existing output files with timestamps"""
    
    output_dir = Path("output")
    if not output_dir.exists():
        print("No output directory found")
        return
        
    # Create new organized structure
    organized_dirs = {
        "analyses/insights": [],
        "analyses/networks": [],
        "analyses/profiles": [],
        "exports/csv": [],
        "exports/json": [],
        "archive/legacy": []
    }
    
    for dir_path in organized_dirs.keys():
        (output_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Get current timestamp for migration
    migration_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Process existing files
    moved_files = []
    
    for file_path in output_dir.glob("*.*"):
        if file_path.is_file():
            filename = file_path.name
            
            # Determine new location based on filename
            if "ai_insights" in filename or "insights" in filename:
                new_dir = output_dir / "analyses" / "insights"
                new_name = f"insights_migrated_{migration_timestamp}_{filename}"
            elif "network" in filename:
                new_dir = output_dir / "analyses" / "networks"
                new_name = f"network_migrated_{migration_timestamp}_{filename}"
            elif "connections" in filename or "relationships" in filename:
                if filename.endswith('.csv'):
                    new_dir = output_dir / "exports" / "csv"
                else:
                    new_dir = output_dir / "exports" / "json"
                new_name = f"connections_migrated_{migration_timestamp}_{filename}"
            else:
                new_dir = output_dir / "archive" / "legacy"
                new_name = f"legacy_migrated_{migration_timestamp}_{filename}"
            
            # Move file
            new_path = new_dir / new_name
            try:
                file_path.rename(new_path)
                moved_files.append({
                    "original": str(file_path),
                    "new": str(new_path)
                })
            except Exception as e:
                print(f"Error moving {filename}: {e}")
    
    # Create migration report
    migration_report = {
        "migration_timestamp": migration_timestamp,
        "files_moved": len(moved_files),
        "moved_files": moved_files,
        "new_structure_created": list(organized_dirs.keys())
    }
    
    report_path = output_dir / f"migration_report_{migration_timestamp}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(migration_report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Migrated {len(moved_files)} files to organized structure")
    print(f"📄 Migration report saved to: {report_path}")
    
    return migration_report

def populate_database_from_files():
    """Populate database with data from organized files"""
    
    setup_database_schema()
    
    conn = sqlite3.connect("data/job_search.db")
    cursor = conn.cursor()
    
    output_dir = Path("output")
    populated_sessions = 0
    
    # Process insights files
    insights_dir = output_dir / "analyses" / "insights"
    if insights_dir.exists():
        for file_path in insights_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract metadata if available
                if "metadata" in data:
                    metadata = data["metadata"]
                    session_id = metadata.get("session_id", f"legacy_{file_path.stem}")
                    analysis_type = metadata.get("analysis_type", "ai_insights")
                    profile_id = metadata.get("profile_id", "default")
                    timestamp = metadata.get("timestamp", datetime.now().isoformat())
                else:
                    # Legacy file format
                    session_id = f"legacy_{file_path.stem}"
                    analysis_type = "ai_insights"
                    profile_id = "default"
                    timestamp = datetime.now().isoformat()
                
                # Insert session
                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_sessions 
                    (session_id, timestamp, analysis_type, profile_id, status, file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, timestamp, analysis_type, profile_id, "completed", str(file_path)))
                
                # Insert results
                results_json = json.dumps(data)
                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_results 
                    (session_id, analysis_type, profile_id, timestamp, results_json, file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, analysis_type, profile_id, timestamp, results_json, str(file_path)))
                
                populated_sessions += 1
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Populated database with {populated_sessions} sessions")
    return populated_sessions

if __name__ == "__main__":
    print("🚀 Setting up Job Search Intelligence Database...")
    
    # Step 1: Create database schema
    setup_database_schema()
    
    # Step 2: Organize existing files
    migration_report = migrate_existing_output_files()
    
    # Step 3: Populate database
    populated_count = populate_database_from_files()
    
    print("\n✅ Setup completed successfully!")
    print(f"📁 Files organized: {migration_report['files_moved']}")
    print(f"💾 Database sessions: {populated_count}")
    print("\n📊 New organized structure:")
    print("output/")
    print("  ├── analyses/")
    print("  │   ├── insights/    # AI analysis results")
    print("  │   ├── networks/    # Network analysis")
    print("  │   └── profiles/    # Profile analysis")
    print("  ├── exports/")
    print("  │   ├── csv/         # CSV exports")
    print("  │   ├── json/        # JSON exports")
    print("  │   └── excel/       # Excel exports")
    print("  ├── reports/")
    print("  │   ├── daily/       # Daily summaries")
    print("  │   ├── weekly/      # Weekly reports")
    print("  │   └── monthly/     # Monthly reports")
    print("  ├── visualizations/")
    print("  │   ├── graphs/      # Network graphs")
    print("  │   └── charts/      # Analytics charts")
    print("  └── archive/")
    print("      └── legacy/      # Old files")
