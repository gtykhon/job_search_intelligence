# 📊 Dashboard Guide

> **Complete guide to the Job Search Dashboard**

Interactive web-based dashboard for viewing, filtering, and managing job opportunities from the database.

---

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Dashboard Pages](#dashboard-pages)
- [Filtering & Search](#filtering--search)
- [Application Tracking](#application-tracking)
- [Tips & Tricks](#tips--tricks)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Launch Dashboard

```bash
# Make sure you're in the project root
cd job_search_intelligence

# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Run dashboard
python -m uvicorn src.dashboard.app:app --host 0.0.0.0 --port 8889
```

**Dashboard will open at:** http://localhost:8889

### First Time Setup

1. **Run the scraper first** to populate database:
   ```bash
   python scripts/scheduled_tasks/daily_jobspy_detection.py
   ```

2. **Launch dashboard:**
   ```bash
   python -m uvicorn src.dashboard.app:app --host 0.0.0.0 --port 8889
   ```

3. **Navigate pages** using the sidebar

---

## Dashboard Pages

### 🏠 Overview Page

**Purpose:** High-level summary and quick insights

**Components:**

#### Metrics Row
- 📊 **Total Jobs** - Number of jobs in database
- 💰 **Average Salary** - Mean salary range
- ✅ **Applications** - Tracked applications
- 🔄 **Last Updated** - Most recent scrape

#### Charts

**Jobs by Source (Pie Chart)**
- Visual breakdown by job site
- Indeed, LinkedIn, Glassdoor, Google Jobs
- Shows which sources provide most results

**Applications by Status (Bar Chart)**
- Tracks application pipeline
- interested → applied → interviewing → offer
- Helps identify bottlenecks

#### Recent Jobs Feed
- Last 10 jobs added to database
- Expandable cards with full details
- Quick apply links

**Use cases:**
- Quick daily check-in
- See what's new at a glance
- Monitor scraping activity

---

### 💼 Job Listings Page

**Purpose:** Browse, filter, and search all jobs

**Features:**

#### Filters (Sidebar)

**Source Filter**
- All sources (default)
- Indeed only
- LinkedIn only
- Glassdoor only
- Google Jobs only

**Minimum Salary**
- Slider from $0 to $200K
- Default: $100K
- Shows jobs above threshold

**Remote Type**
- All (default)
- Remote
- On-site
- Hybrid

**Search**
- Text search box
- Searches: title, company, location
- Case-insensitive
- Real-time filtering

#### Sorting

Sort by:
- 📅 **Date Posted** (newest first) - Default
- 💰 **Salary** (highest first)
- 🏢 **Company** (A-Z)
- 📋 **Job Title** (A-Z)

#### Pagination

- 20 jobs per page
- Page navigation at bottom
- "Previous" / "Next" buttons
- Shows: "Page 1 of 5 (104 total jobs)"

#### Job Cards

Each card shows:
- **Title** (large text)
- **Company** (with emoji)
- **Location** 📍
- **Salary** 💰 (if available)
- **Posted Date** 📅
- **Source** (colored badge)
- **Remote Type** (if specified)
- **Apply Button** 🔗

**Expandable details:**
- Full job description
- Company rating & reviews
- Clearance requirement
- Metro accessibility
- First seen / Last seen dates

**Use cases:**
- Daily job browsing
- Finding specific companies
- Filtering by salary/location
- Quick applying to multiple jobs

---


## Filtering & Search

### Using Filters

**Step-by-step:**

1. **Navigate to Job Listings page**

2. **Open sidebar** (click arrow if collapsed)

3. **Select source:**
   - All sources (no filter)
   - Single source (Indeed, LinkedIn, etc.)

4. **Set minimum salary:**
   - Drag slider to desired amount
   - Default: $100,000
   - Range: $0 - $200,000

5. **Choose remote type:**
   - All (default)
   - Remote only
   - On-site only
   - Hybrid only

6. **Enter search term:**
   - Type in search box
   - Searches: title, company, location
   - Updates results immediately

**Filters are cumulative** - all active filters must match

### Search Tips

**Effective searches:**
- ✅ "Machine Learning" - Finds ML jobs
- ✅ "Acme Corp" - All jobs at Acme
- ✅ "Arlington" - Jobs in Arlington
- ✅ "Senior Python" - Senior Python roles

**Ineffective searches:**
- ❌ Too specific: "Senior Python Developer with 10 years"
- ❌ Too short: "p" (too many matches)
- ❌ Typos: "Pyton" (won't match Python)

**Pro tips:**
- Use key terms only
- Check spelling
- Try variations: "ML" vs "Machine Learning"
- Combine with filters for best results

---

## Application Tracking

### Current Status

**✅ Database Ready**
- Applications table exists
- Schema defined
- Foreign keys configured

**🚧 UI Partially Complete**
- Page placeholder exists
- Basic framework in place

**❌ Not Yet Implemented**
- Add/edit forms
- Status updates
- Reminders

### Manual Application Tracking (Interim)

Use SQL queries directly:

```python
from src.intelligence.job_database import JobDatabase

db = JobDatabase()

# Mark job as applied
with db.get_connection() as conn:
    conn.execute("""
        INSERT INTO applications (job_id, applied_date, status, application_notes)
        VALUES (?, ?, ?, ?)
    """, (job_id, "2024-12-11", "applied", "Submitted via company website"))
    conn.commit()

# View applications
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.title, j.company, a.status, a.applied_date
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        ORDER BY a.applied_date DESC
    """)
    apps = cursor.fetchall()
    for title, company, status, date in apps:
        print(f"{title} at {company}: {status} ({date})")
```

### Coming Soon

**Planned features:**
- 📝 Application form in dashboard
- ✏️ Status update dropdown
- 📅 Interview date picker
- 🔔 Follow-up reminders
- 📊 Application pipeline chart
- 📈 Success rate analytics

---

## Tips & Tricks

### Dashboard Performance

**Speed up large databases:**

1. **Use filters** - Don't load all jobs
2. **Limit date range** - Recent jobs only
3. **Pagination** - Don't scroll endlessly
4. **Close browser tabs** - Reduce memory usage

### Keyboard Shortcuts

- `R` - Rerun app (refresh data)
- `C` - Clear cache
- `Ctrl + K` - Command palette
- `F11` - Fullscreen (browser)

### Browser Tips

**Best experience:**
- Use Chrome or Edge
- Zoom: 100% (Ctrl + 0)
- Fullscreen: F11

### Data Refresh

**Dashboard updates:**
- Data cached for performance
- Click "R" to refresh
- Or use "Rerun" button in top-right

**When to refresh:**
- After running scraper
- After manual database edits
- When numbers look stale

### Export Data

**Copy job listings:**
1. Open job details
2. Copy URL from card
3. Paste into spreadsheet

**Export to CSV (future feature):**
```python
# Current workaround - use SQL
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()
    
    import csv
    with open('jobs_export.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([desc[0] for desc in cursor.description])  # Headers
        writer.writerows(jobs)
```

### Custom Filters (Advanced)

**Combine multiple criteria:**
1. Set salary minimum
2. Choose source
3. Select remote type
4. Add search term

**Example: Remote senior roles at FAANG**
- Source: LinkedIn
- Min salary: $150K
- Remote: Remote only
- Search: "Meta" or "Google" or "Amazon"

---

## Troubleshooting

### Dashboard Won't Start


**Solution:**
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows


# Reinstall if needed
```

### No Data Showing

**Symptoms:** Empty pages, "0 jobs"

**Causes & Solutions:**

1. **Database empty**
   ```bash
   # Run scraper first
   python scripts/scheduled_tasks/daily_jobspy_detection.py
   ```

2. **Wrong database path**
   - Check `job_dashboard.py` line 20
   - Should be: `data/job_tracker.db`

3. **Database file missing**
   - Run scraper to create it
   - Or check `data/` directory exists

### Charts Not Loading

**Error:** Blank chart area

**Solutions:**

1. **Refresh dashboard** - Press `R`

2. **Check browser console** - F12 → Console tab

3. **Update Plotly:**
   ```bash
   pip install --upgrade plotly
   ```

4. **Clear cache:**
   - Click hamburger menu (top-right)
   - "Clear cache"
   - "Rerun"

### Filters Not Working

**Symptoms:** Jobs don't change when filtering

**Solutions:**

1. **Check filter values:**
   - Is salary slider at $0?
   - Is source set to "All"?
   - Is search box empty?

2. **Refresh data:**
   - Press `R`
   - Or restart dashboard

3. **Check data quality:**
   - Do jobs have salary data?
   - Are source fields populated?

### Slow Performance

**Symptoms:** Dashboard sluggish, charts slow to load

**Solutions:**

1. **Reduce data loaded:**
   - Use filters
   - Limit to recent jobs
   - Don't load all at once

2. **Clear browser cache:**
   - Ctrl + Shift + Delete
   - Clear cached images and files

3. **Close other apps:**
   - Free up memory
   - Close unused browser tabs

4. **Restart dashboard:**
   ```bash
   # Ctrl + C to stop
   ```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**

1. **Find process using port 8501:**
   ```bash
   # Windows
   taskkill /PID <PID> /F
   
   # Mac/Linux
   kill -9 <PID>
   ```

2. **Or use different port:**
   ```bash
   ```

---

## Advanced Features

### Caching Strategy


**Database connection cached:**
```python
@st.cache_resource
def get_database():
    return JobDatabase()
```

**Data queries cached:**
```python
@st.cache_data(ttl=300)  # 5 min cache
def load_jobs():
    return db.get_all_jobs()
```

**Benefits:**
- Faster page loads
- Reduced database queries
- Smoother user experience

**Tradeoffs:**
- May show stale data
- Press `R` to refresh

### Customizing Dashboard

**Edit `job_dashboard.py`:**

**Change page names:**
```python
# Line ~50

**Adjust pagination:**
```python
# Line ~200
jobs_per_page = 50  # Default is 20
```

**Modify color scheme:**
```python
# Custom CSS at top of file
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    </style>
""", unsafe_allow_html=True)
```

### Embedding Charts

**Export chart as image:**

Plotly charts can be saved:
```python
import plotly.io as pio

fig = px.pie(...)  # Your chart
pio.write_image(fig, 'chart.png')
```

---

## Future Enhancements

**Roadmap:**
- ✅ Overview dashboard (complete)
- ✅ Job listings with filters (complete)
- 🚧 Application tracking (partial)
- ❌ Email notifications
- ❌ Resume matching
- ❌ Cover letter generator
- ❌ Interview preparation
- ❌ Salary negotiation insights
- ❌ Company research automation

---

## Additional Resources

- **Plotly Docs:** https://plotly.com/python/
- **Our Database Guide:** [DATABASE_GUIDE.md](DATABASE_GUIDE.md)
- **JobSpy Integration:** [JOBSPY_INTEGRATION.md](JOBSPY_INTEGRATION.md)

---

**Need help?** Open an issue or contact the maintainers.

**Found a bug?** Report it on GitHub issues.

**Want a feature?** Submit a feature request!
