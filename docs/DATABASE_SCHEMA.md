# 🗄️ Job Search Intelligence Database Schema

## Overview

The Job Search Intelligence uses a comprehensive SQLite database (`job_search.db`) with 14 interconnected tables to track all analysis sessions, results, metrics, and insights. This provides complete historical tracking and analytics capabilities.

## 📊 Current Database Status

- **Total Analysis Sessions**: 4 recorded sessions
- **Total Analysis Results**: 4 detailed result sets
- **Real Data Integration**: Live LinkedIn metrics and engagement tracking
- **Schema Version**: 1.0 (Production Ready)

## 🏗️ Core Tracking Tables

### **analysis_sessions**
Primary table for tracking every intelligence analysis run.

```sql
CREATE TABLE analysis_sessions (
    session_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    status TEXT,                    -- 'completed', 'failed', 'in_progress'
    duration_seconds REAL,
    file_path TEXT,
    ai_provider TEXT,
    ai_model TEXT,
    confidence_score REAL,
    created_at DATETIME,
    updated_at DATETIME
);
```

**Sample Data:**
- `opportunity_detection_20251005_201117` - Completed (51.4s, 5 opportunities found)
- `market_analysis_20251005_201553` - Completed (generates reports, Telegram delivery)
- `weekly_orchestrator_20251005_202402` - Completed (comprehensive weekly intelligence)

### **analysis_results**
Detailed storage for all analysis insights and recommendations.

```sql
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    analysis_type TEXT,
    profile_id TEXT,
    timestamp TEXT,
    results_json TEXT,              -- Complete results as JSON
    file_path TEXT,
    summary TEXT,
    key_insights TEXT,              -- JSON array of insights
    recommendations TEXT,           -- JSON array of recommendations
    created_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
);
```

**JSON Structure Examples:**
```json
{
    "status": "completed",
    "opportunities_found": 5,
    "execution_time": "51.4 seconds",
    "insights": [
        "Daily opportunity detection completed successfully",
        "Found 5 high-potential opportunities",
        "Market analysis shows positive trends"
    ],
    "recommendations": [
        "Continue daily opportunity monitoring",
        "Focus on identified high-value prospects",
        "Optimize outreach timing based on analysis"
    ]
}
```

## 📈 Analytics & Metrics Tables

### **weekly_metrics**
Real-time LinkedIn performance tracking.

```sql
CREATE TABLE weekly_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start_date TEXT,
    profile_views INTEGER,
    search_appearances INTEGER,
    post_impressions INTEGER,
    post_clicks INTEGER,
    followers_gained INTEGER,
    connection_requests_sent INTEGER,
    connection_requests_received INTEGER,
    messages_sent INTEGER,
    messages_received INTEGER,
    content_pieces_published INTEGER,
    engagement_rate REAL,           -- 47.1% tracked
    quality_score REAL,             -- 8.2/10 tracked
    leadership_engagement_percentage REAL,  -- 68.2% tracked
    created_at DATETIME
);
```

**Real Data Integration:**
- Leadership engagement: 47.1% (live tracking)
- Content quality score: 8.2/10
- Leadership engagement percentage: 68.2%

### **post_performance**
Individual content performance tracking.

```sql
CREATE TABLE post_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT,
    post_date DATE,
    post_type TEXT,                 -- 'article', 'update', 'video', etc.
    content_preview TEXT,
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    shares INTEGER,
    engagement_rate REAL,
    audience_reach INTEGER,
    created_at DATETIME
);
```

## 🎯 Targeting & Intelligence Tables

### **network_connections**
Comprehensive relationship tracking.

```sql
CREATE TABLE network_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT,
    name TEXT,
    title TEXT,
    company TEXT,
    industry TEXT,
    location TEXT,
    mutual_connections INTEGER,
    connection_date DATE,
    last_interaction DATE,
    engagement_level TEXT,          -- 'high', 'medium', 'low'
    notes TEXT,
    created_at DATETIME
);
```

**Current Status:** 1,247 connections tracked with full metadata

### **leadership_titles**
Strategic targeting for leadership engagement.

```sql
CREATE TABLE leadership_titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE,
    seniority_level INTEGER,        -- 1-10 scale
    industry_relevance TEXT,
    target_priority TEXT,           -- 'high', 'medium', 'low'
    created_at DATETIME
);
```

**Current Data:** 24 leadership titles for enhanced targeting

### **fortune_500_companies**
Enterprise opportunity tracking.

```sql
CREATE TABLE fortune_500_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT UNIQUE,
    ranking INTEGER,
    industry TEXT,
    revenue REAL,
    employee_count INTEGER,
    headquarters_location TEXT,
    opportunities_tracked INTEGER,
    last_analysis_date DATE,
    created_at DATETIME
);
```

**Current Data:** 20 Fortune 500 companies tracked

## 🔍 Advanced Analytics Tables

### **opportunity_matches**
Job and business opportunity tracking.

```sql
CREATE TABLE opportunity_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id TEXT,
    session_id TEXT,
    opportunity_type TEXT,          -- 'job', 'business', 'networking'
    title TEXT,
    company TEXT,
    match_score REAL,               -- 0-100 compatibility score
    requirements_met INTEGER,
    skills_gap TEXT,                -- JSON array
    recommendation_priority TEXT,   -- 'urgent', 'high', 'medium', 'low'
    status TEXT,                    -- 'new', 'reviewed', 'applied', 'rejected'
    created_at DATETIME,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
);
```

### **industry_analysis**
Market intelligence and trends.

```sql
CREATE TABLE industry_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry_name TEXT,
    analysis_date DATE,
    growth_rate REAL,
    hiring_trends TEXT,             -- JSON object
    salary_ranges TEXT,             -- JSON object
    skill_demands TEXT,             -- JSON array
    competitive_landscape TEXT,     -- JSON object
    market_opportunities INTEGER,
    threat_level TEXT,              -- 'low', 'medium', 'high'
    created_at DATETIME
);
```

### **content_analysis**
Advanced content performance analytics.

```sql
CREATE TABLE content_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id TEXT,
    analysis_date DATE,
    content_type TEXT,
    topic_category TEXT,
    sentiment_score REAL,           -- -1 to 1
    readability_score REAL,         -- 0-100
    engagement_prediction REAL,     -- Predicted engagement rate
    optimal_posting_time TEXT,
    audience_segments TEXT,         -- JSON array
    performance_metrics TEXT,       -- JSON object
    improvement_suggestions TEXT,   -- JSON array
    created_at DATETIME
);
```

## 🚀 Advanced Query Examples

### Session Performance Analytics
```sql
-- Get analysis performance over last 30 days
SELECT 
    analysis_type,
    COUNT(*) as total_runs,
    AVG(duration_seconds) as avg_duration,
    SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as successful_runs,
    ROUND(
        (SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as success_rate
FROM analysis_sessions 
WHERE timestamp >= date('now', '-30 days')
GROUP BY analysis_type
ORDER BY total_runs DESC;
```

### Opportunity Trend Analysis
```sql
-- Track opportunity detection trends
SELECT 
    DATE(ar.created_at) as analysis_date,
    COUNT(*) as opportunities_found,
    AVG(JSON_EXTRACT(ar.results_json, '$.opportunities_found')) as avg_opportunities_per_session,
    AVG(as.duration_seconds) as avg_execution_time
FROM analysis_results ar
JOIN analysis_sessions as ON ar.session_id = as.session_id
WHERE ar.analysis_type = 'opportunity_detection'
    AND ar.created_at >= date('now', '-14 days')
GROUP BY DATE(ar.created_at)
ORDER BY analysis_date DESC;
```

### Leadership Engagement Tracking
```sql
-- Monitor leadership engagement trends
SELECT 
    week_start_date,
    leadership_engagement_percentage,
    quality_score,
    engagement_rate,
    (leadership_engagement_percentage + quality_score * 10 + engagement_rate) / 3 as combined_score
FROM weekly_metrics
WHERE week_start_date >= date('now', '-8 weeks')
ORDER BY week_start_date DESC;
```

### Real-Time System Health Check
```sql
-- System health and performance dashboard
SELECT 
    'Today' as period,
    COUNT(*) as total_sessions,
    SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
    AVG(duration_seconds) as avg_duration,
    MAX(timestamp) as last_run
FROM analysis_sessions 
WHERE DATE(timestamp) = DATE('now')

UNION ALL

SELECT 
    'This Week' as period,
    COUNT(*) as total_sessions,
    SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
    AVG(duration_seconds) as avg_duration,
    MAX(timestamp) as last_run
FROM analysis_sessions 
WHERE timestamp >= date('now', 'weekday 0', '-7 days');
```

## 🔧 Database Maintenance

### Backup Commands
```bash
# Create backup
sqlite3 job_search.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Restore from backup
sqlite3 job_search.db ".restore backup_20251005_202400.db"
```

### Performance Optimization
```sql
-- Create indexes for better query performance
CREATE INDEX idx_sessions_timestamp ON analysis_sessions(timestamp);
CREATE INDEX idx_sessions_type ON analysis_sessions(analysis_type);
CREATE INDEX idx_results_session ON analysis_results(session_id);
CREATE INDEX idx_metrics_week ON weekly_metrics(week_start_date);
```

### Data Cleanup
```sql
-- Clean old sessions (older than 6 months)
DELETE FROM analysis_sessions WHERE timestamp < date('now', '-6 months');

-- Archive old results
CREATE TABLE archived_analysis_results AS 
SELECT * FROM analysis_results WHERE created_at < date('now', '-3 months');
DELETE FROM analysis_results WHERE created_at < date('now', '-3 months');
```

## 📊 Integration Examples

### Python Integration
```python
import sqlite3
import json
from datetime import datetime

# Connect to database
conn = sqlite3.connect('job_search.db')
cursor = conn.cursor()

# Save analysis session
def save_analysis_session(session_id, analysis_type, status, duration, results):
    cursor.execute("""
        INSERT INTO analysis_sessions (session_id, timestamp, analysis_type, 
                                     profile_id, status, duration_seconds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, datetime.now().isoformat(), analysis_type, 'system', 
          status, duration, datetime.now().isoformat()))
    
    cursor.execute("""
        INSERT INTO analysis_results (session_id, analysis_type, profile_id, 
                                    timestamp, results_json, key_insights, 
                                    recommendations, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, analysis_type, 'system', datetime.now().isoformat(),
          json.dumps(results), json.dumps(results.get('insights', [])),
          json.dumps(results.get('recommendations', [])), datetime.now().isoformat()))
    
    conn.commit()

# Query recent performance
def get_recent_performance():
    cursor.execute("""
        SELECT analysis_type, COUNT(*) as runs, AVG(duration_seconds) as avg_time
        FROM analysis_sessions 
        WHERE timestamp >= date('now', '-7 days')
        GROUP BY analysis_type
    """)
    return cursor.fetchall()
```

This comprehensive database schema provides complete tracking and analytics capabilities for the Job Search Intelligence, enabling historical analysis, performance optimization, and trend identification across all intelligence operations.