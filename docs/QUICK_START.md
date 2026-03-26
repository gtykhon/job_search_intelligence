# ⚡ Quick Start Guide

> **Get up and running in 5 minutes**

The fastest way to start scraping jobs and using the dashboard.

---

## 🎯 Prerequisites

- **Python 3.13+** installed
- **Git** installed
- **Internet connection** for scraping

---

## 🚀 Installation (2 minutes)

### 1. Clone Repository

```bash
git clone https://github.com/gtykhon/job_search_intelligence.git
cd job_search_intelligence
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

**Wait for installation to complete (~1-2 minutes)**

---

## 🔍 Scrape Jobs (1 minute)

### Run the Scraper

```bash
python scripts/scheduled_tasks/daily_jobspy_detection.py
```

**What happens:**
- ✅ Scrapes Indeed, LinkedIn, Glassdoor, Google Jobs
- ✅ Filters for $100K+ salaries
- ✅ Saves to database (`data/job_tracker.db`)
- ✅ Creates JSON report

**Expected output:**
```
Starting JobSpy job detection...
Scraping Python Developer in Washington, DC...
Found 32 jobs from this search
Scraping Machine Learning Engineer in Washington, DC...
Found 28 jobs from this search
...
Total unique jobs: 104
Jobs with salary >= $100,000: 57
Average salary: $135,667 - $233,286
```

**Duration:** ~30-60 seconds depending on network speed

---

## 📊 Launch Dashboard (30 seconds)

### Start Dashboard

```bash
streamlit run job_dashboard.py
```


**Dashboard features:**
- 🏠 **Overview** - Stats and recent jobs
- 💼 **Job Listings** - Browse with filters
- 📈 **Analytics** - Charts and insights
- ✅ **Applications** - Track applications
- 🔍 **Search History** - Past searches

---

## 🎨 Using the Dashboard

### Browse Jobs

1. Click **"💼 Job Listings"** in sidebar
2. Use filters:
   - **Source:** Indeed, LinkedIn, etc.
   - **Min Salary:** $100K default
   - **Remote Type:** Remote, Hybrid, On-site
   - **Search:** Type keywords

3. Click job cards to expand details
4. Click "🔗 Apply" to open job URL

### View Analytics

1. Click **"📈 Analytics"** in sidebar
2. See charts:
   - Salary distribution
   - Top companies
   - Top locations
   - Remote work trends

### Check Overview

1. Click **"🏠 Overview"** in sidebar
2. View:
   - Total jobs count
   - Average salary
   - Recent additions
   - Job source breakdown

---

## ⚙️ Customize (Optional)

### Change Salary Threshold

Edit `scripts/scheduled_tasks/daily_jobspy_detection.py`:

```python
# Line ~70
MIN_SALARY = 150000  # Change from 100000 to 150000
```

### Add More Searches

Edit `scripts/scheduled_tasks/daily_jobspy_detection.py`:

```python
# Line ~40
search_requests = [
    ScrapingRequest(
        keywords="Your Job Title",
        location="Your City, State",
        job_sites=[JobSite.INDEED, JobSite.LINKEDIN],
        max_results=25,
        posted_since_days=7
    ),
    # Add more searches here
]
```

### Change Search Location

```python
ScrapingRequest(
    keywords="Python Developer",
    location="New York, NY",  # Change location
    # ... rest of config
)
```

---

## 🔄 Daily Workflow

### Morning Routine

```bash
# 1. Activate environment
.venv\Scripts\activate

# 2. Run scraper
python scripts/scheduled_tasks/daily_jobspy_detection.py

# 3. Launch dashboard
streamlit run job_dashboard.py

# 4. Browse new jobs
```

**Time:** ~2 minutes

---

## 📝 Next Steps

### Learn More

- **[README.md](../README.md)** - Full project overview
- **[JOBSPY_INTEGRATION.md](JOBSPY_INTEGRATION.md)** - Advanced scraping
- **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** - Database schema & SQL
- **[DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)** - Dashboard features

### Advanced Usage

**Schedule Daily Scraping (Windows Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9 AM
4. Action: Start a program
5. Program: `C:\Path\To\.venv\Scripts\python.exe`
6. Arguments: `scripts/scheduled_tasks/daily_jobspy_detection.py`
7. Start in: `C:\Path\To\job_search_intelligence`

**Schedule Daily Scraping (Mac/Linux cron):**
```bash
# Edit crontab
crontab -e

# Add line (runs daily at 9 AM)
0 9 * * * cd /path/to/job_search_intelligence && /path/to/.venv/bin/python scripts/scheduled_tasks/daily_jobspy_detection.py
```

### Backup Database

```bash
# Manual backup
cp data/job_tracker.db data/backups/job_tracker_$(date +%Y%m%d).db

# Or on Windows
copy data\job_tracker.db data\backups\job_tracker_%date:~10,4%%date:~4,2%%date:~7,2%.db
```

---

## 🐛 Troubleshooting

### "python: command not found"

**Solution:** Install Python 3.13+ from [python.org](https://www.python.org/downloads/)

### "No module named 'jobspy'"

**Solution:** 
```bash
# Make sure virtual environment is activated
.venv\Scripts\activate

# Reinstall requirements
pip install -r requirements.txt
```

### "No jobs found"

**Causes:**
- Network connection issue
- Sites may be temporarily unavailable
- Search too specific

**Solution:**
- Check internet connection
- Try again in a few minutes
- Broaden search keywords

### "Dashboard won't start"

**Solution:**
```bash
# Check Streamlit installed
pip show streamlit

# Reinstall if needed
pip install streamlit==1.40.1
```

### "Database is empty"

**Solution:** Run scraper first before launching dashboard
```bash
python scripts/scheduled_tasks/daily_jobspy_detection.py
```

---

## 📊 What You Should See

### After Scraping

**Console output:**
```
✅ Total jobs scraped: 104
✅ Jobs after deduplication: 104
✅ Jobs with salary >= $100,000: 57
✅ Average salary: $135,667 - $233,286

📊 Results by source:
  - Indeed: 59 jobs
  - LinkedIn: 45 jobs
  - Glassdoor: 0 jobs
  - Google Jobs: 0 jobs

📁 Results saved to:
  - Database: data/job_tracker.db
  - JSON: data/opportunities/jobs_20241211_143023.json
```

### Dashboard Overview

**Metrics:**
- Total Jobs: 104
- Average Salary: $135,667 - $233,286
- Applications: 0
- Last Updated: 2024-12-11

**Charts:**
- Pie chart showing 57% Indeed, 43% LinkedIn
- Bar chart for applications (if any)
- Recent jobs list with titles and companies

---

## 💡 Pro Tips

### 1. Filter Effectively

Use multiple filters together:
- Source: Indeed (most reliable)
- Min Salary: $120K
- Remote Type: Remote
- Search: "Senior Python"

### 2. Check Daily

Run scraper daily to catch new postings:
- Jobs posted in last 7 days
- Many disappear quickly
- Early application improves chances

### 3. Expand Sources

Start with Indeed + LinkedIn, add others later:
```python
job_sites=[JobSite.INDEED, JobSite.LINKEDIN, JobSite.GLASSDOOR]
```

### 4. Track Applications

**Coming soon** - For now, use spreadsheet:
- Copy job URL from dashboard
- Track application status
- Set follow-up reminders

### 5. Export Data

Use SQL for custom reports:
```python
from src.intelligence.job_database import JobDatabase

db = JobDatabase()
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT title, company, salary_min, job_url FROM jobs WHERE salary_min >= 150000")
    high_paying = cursor.fetchall()
```

---

## ⏱️ Time Estimates

| Task | Duration |
|------|----------|
| Initial setup | 2-3 minutes |
| First scrape | 30-60 seconds |
| Dashboard launch | 10-20 seconds |
| Browse jobs | 5-10 minutes |
| Daily routine | ~2 minutes |

**Total first-time setup:** ~5-10 minutes

---

## 🎉 Success!

You now have:
- ✅ Working job scraper
- ✅ 100+ real job postings
- ✅ Interactive web dashboard
- ✅ Salary filtering ($100K+)
- ✅ SQLite database

**Next:**
- Browse jobs in dashboard
- Apply to opportunities
- Customize searches
- Schedule daily runs

---

## 📞 Need Help?

- **Full documentation:** [README.md](../README.md)
- **Issues:** GitHub Issues
- **Questions:** Open a discussion

---

**⭐ Star the repo if you find it useful!**

**🚀 Happy job hunting!**
