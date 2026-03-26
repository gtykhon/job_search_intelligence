#!/usr/bin/env python3
"""
Daily Job Summary Report
Queries real job data from job_tracker.db and delivers via Email + Telegram.
Run via Windows Task Scheduler daily at 6:00 PM.
"""

import os
import sys
import asyncio
import logging
import smtplib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

# Add parent directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv(Path(parent_dir) / '.env')

# Setup logging
log_dir = Path(parent_dir) / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'daily_summary.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

DB_PATH = Path(parent_dir) / "data" / "job_tracker.db"

EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_RECIPIENTS = [
    r.strip() for r in os.getenv('EMAIL_RECIPIENTS', '').split(',') if r.strip()
]

TELEGRAM_ENABLED = os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


# ── Database queries ─────────────────────────────────────────────────────────

def _has_column(conn, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def get_todays_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch jobs scraped in the last 24 hours, remote-first + alignment score sorted."""
    if not DB_PATH.exists():
        logger.warning(f"Database not found at {DB_PATH}")
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    cursor = conn.cursor()

    # Check if alignment_score column exists
    has_score = _has_column(conn, 'jobs', 'alignment_score')
    score_col = ", alignment_score" if has_score else ""
    score_order = "COALESCE(alignment_score, 0) DESC," if has_score else ""

    max_age = (datetime.now() - timedelta(days=7)).isoformat()

    cursor.execute(f'''
        SELECT title, company, location, salary_min, salary_max,
               source_site, remote_type, clearance_required, job_url,
               posted_date, scraped_date{score_col}
        FROM jobs
        WHERE scraped_date >= ? AND is_active = 1
          AND (posted_date IS NULL OR posted_date >= ?)
        ORDER BY
            CASE WHEN remote_type = 'remote' THEN 0
                 WHEN remote_type = 'hybrid' THEN 1
                 ELSE 2 END ASC,
            {score_order}
            salary_max DESC NULLS LAST, salary_min DESC NULLS LAST
        LIMIT ?
    ''', (cutoff, max_age, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_daily_stats() -> Dict[str, Any]:
    """Get summary statistics for today's scrape vs overall database."""
    if not DB_PATH.exists():
        return {}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()

    # Today's counts
    c.execute('SELECT COUNT(*) as cnt FROM jobs WHERE scraped_date >= ? AND is_active = 1', (cutoff,))
    today_total = c.fetchone()['cnt']

    c.execute('''
        SELECT source_site, COUNT(*) as cnt FROM jobs
        WHERE scraped_date >= ? AND is_active = 1
        GROUP BY source_site ORDER BY cnt DESC
    ''', (cutoff,))
    today_by_source = {r['source_site']: r['cnt'] for r in c.fetchall()}

    c.execute('''
        SELECT COUNT(*) as cnt FROM jobs
        WHERE scraped_date >= ? AND is_active = 1
          AND (salary_min IS NOT NULL OR salary_max IS NOT NULL)
    ''', (cutoff,))
    today_with_salary = c.fetchone()['cnt']

    c.execute('''
        SELECT COUNT(*) as cnt FROM jobs
        WHERE scraped_date >= ? AND is_active = 1
          AND remote_type = 'remote'
    ''', (cutoff,))
    today_remote = c.fetchone()['cnt']

    c.execute('''
        SELECT AVG(salary_min) as avg_min, AVG(salary_max) as avg_max,
               MAX(salary_max) as top_salary
        FROM jobs
        WHERE scraped_date >= ? AND is_active = 1 AND salary_min IS NOT NULL
    ''', (cutoff,))
    salary_row = c.fetchone()

    # Overall DB counts
    c.execute('SELECT COUNT(*) as cnt FROM jobs WHERE is_active = 1')
    db_total = c.fetchone()['cnt']

    conn.close()

    return {
        'today_total': today_total,
        'today_by_source': today_by_source,
        'today_with_salary': today_with_salary,
        'today_remote': today_remote,
        'avg_salary_min': salary_row['avg_min'] if salary_row else None,
        'avg_salary_max': salary_row['avg_max'] if salary_row else None,
        'top_salary': salary_row['top_salary'] if salary_row else None,
        'db_total': db_total,
    }


# ── Formatting ───────────────────────────────────────────────────────────────

def _salary_str(job: Dict) -> str:
    s_min, s_max = job.get('salary_min'), job.get('salary_max')
    if s_min and s_max:
        return f"${s_min:,.0f} – ${s_max:,.0f}"
    if s_min:
        return f"${s_min:,.0f}+"
    if s_max:
        return f"Up to ${s_max:,.0f}"
    return "Not listed"


def _location_str(job: Dict) -> str:
    loc = job.get('location') or ''
    remote = job.get('remote_type') or ''
    if remote == 'remote':
        return f"🏠 Remote" + (f" ({loc})" if loc else "")
    return loc or "Unknown"


def _job_age(job: Dict) -> str:
    """Return human-readable age string like '2d', '1w', '3mo'."""
    date_str = job.get("posted_date") or job.get("scraped_date")
    if not date_str:
        return "?"
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).replace(tzinfo=None)
        days = (datetime.now() - dt).days
        if days == 0:
            return "Today"
        if days == 1:
            return "1d"
        if days < 7:
            return f"{days}d"
        if days < 30:
            return f"{days // 7}w"
        return f"{days // 30}mo"
    except (ValueError, TypeError):
        return "?"


def _job_age_days(job: Dict) -> int:
    """Return age in days (999 if unknown)."""
    date_str = job.get("posted_date") or job.get("scraped_date")
    if not date_str:
        return 999
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).replace(tzinfo=None)
        return max(0, (datetime.now() - dt).days)
    except (ValueError, TypeError):
        return 999


def _section_jobs(jobs: List[Dict]) -> Dict[str, List[Dict]]:
    """Split jobs into report sections: Remote, Newest, Highest Score."""
    remote = [j for j in jobs if j.get('remote_type') == 'remote']
    # Newest: sort all by posted_date/scraped_date, take top 10
    newest = sorted(jobs, key=lambda j: _job_age_days(j))[:10]
    # Highest score: sort by alignment_score desc, take top 10
    scored = [j for j in jobs if j.get('alignment_score')]
    top_scored = sorted(scored, key=lambda j: j.get('alignment_score', 0), reverse=True)[:10]
    return {
        'remote': remote,
        'newest': newest,
        'top_scored': top_scored,
    }


def _format_tg_job(i: int, job: Dict) -> List[str]:
    """Format a single job for Telegram."""
    salary = _salary_str(job)
    loc = _location_str(job)
    clearance = " 🔒" if job.get('clearance_required') else ""
    score = job.get('alignment_score')
    score_str = f" 🎯{score:.0f}%" if score else ""
    age = _job_age(job)
    age_str = f" ⏳{age}" if age != "?" else ""
    lines = [
        f"<b>{i}. {job['title']}</b>{clearance}{score_str}{age_str}",
        f"   🏢 {job['company']} | {loc}",
        f"   💰 {salary}",
    ]
    if job.get('job_url'):
        lines.append(f"   🔗 <a href=\"{job['job_url']}\">Apply</a>")
    lines.append("")
    return lines


def format_telegram_message(jobs: List[Dict], stats: Dict) -> str:
    """Build an HTML-formatted Telegram message with sections: Remote, Newest, Top Score."""
    now = datetime.now()
    today_total = stats.get('today_total', 0)
    by_source = stats.get('today_by_source', {})
    source_str = ", ".join(f"{s}: {c}" for s, c in by_source.items()) or "none"

    lines = [
        f"<b>📋 Daily Job Report — {now.strftime('%A, %B %d')}</b>",
        "",
        f"<b>📊 Today's Scrape:</b>",
        f"• {today_total} jobs found ({source_str})",
        f"• {stats.get('today_with_salary', 0)} with salary info",
        f"• {stats.get('today_remote', 0)} remote positions",
    ]

    if stats.get('avg_salary_min'):
        lines.append(
            f"• Avg salary: ${stats['avg_salary_min']:,.0f} – ${stats['avg_salary_max']:,.0f}"
        )
    if stats.get('top_salary'):
        lines.append(f"• Top salary today: ${stats['top_salary']:,.0f}")

    lines.append(f"• DB total: {stats.get('db_total', '?')} active jobs")
    lines.append("")

    sections = _section_jobs(jobs)

    # Section 1: Top Remote
    if sections['remote']:
        lines.append(f"<b>🏠 Remote Jobs ({len(sections['remote'])})</b>")
        lines.append("")
        for i, job in enumerate(sections['remote'][:5], 1):
            lines.extend(_format_tg_job(i, job))

    # Section 2: Newest Posted
    if sections['newest']:
        lines.append(f"<b>🆕 Newest Posted</b>")
        lines.append("")
        for i, job in enumerate(sections['newest'][:5], 1):
            lines.extend(_format_tg_job(i, job))

    # Section 3: Highest Alignment Score
    if sections['top_scored']:
        lines.append(f"<b>🎯 Highest Alignment Score</b>")
        lines.append("")
        for i, job in enumerate(sections['top_scored'][:5], 1):
            lines.extend(_format_tg_job(i, job))

    lines.append(f"<i>⏰ {now.strftime('%I:%M %p')} | Job Intelligence System</i>")

    msg = "\n".join(lines)
    # Telegram max 4096 chars
    if len(msg) > 4000:
        msg = msg[:3990] + "\n..."
    return msg


def _email_job_row(job: Dict) -> str:
    """Build a single HTML table row for email report."""
    salary = _salary_str(job)
    loc = _location_str(job).replace("🏠 ", "")
    clearance = "🔒 " if job.get('clearance_required') else ""
    link = job.get('job_url', '#')
    age = _job_age(job)
    score = job.get('alignment_score')
    if score is not None:
        if score >= 70:
            score_html = f'<span style="color:#16a34a;font-weight:700;">{score:.0f}%</span>'
        elif score >= 50:
            score_html = f'<span style="color:#ca8a04;font-weight:700;">{score:.0f}%</span>'
        else:
            score_html = f'<span style="color:#dc2626;font-weight:700;">{score:.0f}%</span>'
    else:
        score_html = '<span style="color:#9ca3af;">—</span>'
    remote_badge = ""
    if job.get('remote_type') == 'remote':
        remote_badge = ' <span style="background:#dbeafe;color:#1d4ed8;padding:1px 6px;border-radius:8px;font-size:11px;">Remote</span>'
    return f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee;">
            <a href="{link}" style="color:#1a73e8;text-decoration:none;font-weight:600;">
              {clearance}{job['title']}
            </a>{remote_badge}
          </td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{job['company']}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{loc}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{salary}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">{score_html}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">{age}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{job.get('source_site', '')}</td>
        </tr>"""


def _email_section(title: str, emoji: str, jobs_list: List[Dict], color: str) -> str:
    """Build an HTML section with table for email report."""
    if not jobs_list:
        return ""
    rows = "".join(_email_job_row(j) for j in jobs_list)
    return f"""
      <div style="padding:16px;">
        <h2 style="font-size:18px;color:{color};margin-bottom:8px;">{emoji} {title} ({len(jobs_list)})</h2>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr style="background:{color};color:white;">
            <th style="padding:10px;text-align:left;">Title</th>
            <th style="padding:10px;text-align:left;">Company</th>
            <th style="padding:10px;text-align:left;">Location</th>
            <th style="padding:10px;text-align:left;">Salary</th>
            <th style="padding:10px;text-align:center;">Score</th>
            <th style="padding:10px;text-align:center;">Age</th>
            <th style="padding:10px;text-align:left;">Source</th>
          </tr>
          {rows}
        </table>
      </div>"""


def format_email_html(jobs: List[Dict], stats: Dict) -> str:
    """Build a styled HTML email with sections: Remote, Newest, Top Score."""
    now = datetime.now()
    today_total = stats.get('today_total', 0)
    by_source = stats.get('today_by_source', {})

    sections = _section_jobs(jobs)

    source_badges = " ".join(
        f'<span style="background:#e8f0fe;color:#1a73e8;padding:2px 8px;border-radius:12px;'
        f'font-size:12px;margin-right:4px;">{s}: {c}</span>'
        for s, c in by_source.items()
    )

    remote_section = _email_section("Remote Jobs", "🏠", sections['remote'], "#1d4ed8")
    newest_section = _email_section("Newest Posted", "🆕", sections['newest'], "#16a34a")
    scored_section = _email_section("Highest Alignment Score", "🎯", sections['top_scored'], "#d97706")

    html = f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif;max-width:960px;margin:auto;color:#333;">
      <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);color:white;padding:24px;border-radius:8px 8px 0 0;">
        <h1 style="margin:0;font-size:22px;">📋 Daily Job Report</h1>
        <p style="margin:4px 0 0;opacity:0.9;">{now.strftime('%A, %B %d, %Y')}</p>
      </div>

      <div style="background:#f8f9fa;padding:16px;border:1px solid #e0e0e0;">
        <table style="width:100%;border-collapse:collapse;">
          <tr>
            <td style="text-align:center;padding:12px;">
              <div style="font-size:28px;font-weight:700;color:#1a73e8;">{today_total}</div>
              <div style="font-size:12px;color:#666;">Jobs Found</div>
            </td>
            <td style="text-align:center;padding:12px;">
              <div style="font-size:28px;font-weight:700;color:#34a853;">{stats.get('today_with_salary', 0)}</div>
              <div style="font-size:12px;color:#666;">With Salary</div>
            </td>
            <td style="text-align:center;padding:12px;">
              <div style="font-size:28px;font-weight:700;color:#ea4335;">{stats.get('today_remote', 0)}</div>
              <div style="font-size:12px;color:#666;">Remote</div>
            </td>
            <td style="text-align:center;padding:12px;">
              <div style="font-size:28px;font-weight:700;color:#fbbc04;">{stats.get('db_total', 0)}</div>
              <div style="font-size:12px;color:#666;">DB Total</div>
            </td>
          </tr>
        </table>
        <div style="text-align:center;margin-top:8px;">{source_badges}</div>
      </div>

      {remote_section}
      {newest_section}
      {scored_section}

      <div style="background:#f8f9fa;padding:12px;text-align:center;font-size:12px;color:#999;border-radius:0 0 8px 8px;border:1px solid #e0e0e0;">
        Generated at {now.strftime('%I:%M %p')} by Job Intelligence System
      </div>
    </body>
    </html>
    """
    return html


# ── Delivery ─────────────────────────────────────────────────────────────────

async def send_telegram(message: str) -> bool:
    """Send message via Telegram Bot API."""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info("Telegram not configured; skipping")
        return False

    import aiohttp
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    logger.info("✅ Telegram message sent")
                    return True
                else:
                    body = await resp.text()
                    logger.error(f"Telegram API error {resp.status}: {body}")
                    return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_email(subject: str, html_body: str) -> bool:
    """Send HTML email via SMTP."""
    if not EMAIL_ENABLED or not EMAIL_USERNAME or not EMAIL_PASSWORD or not EMAIL_RECIPIENTS:
        logger.info("Email not configured; skipping")
        return False

    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_USERNAME
    msg['To'] = ', '.join(EMAIL_RECIPIENTS)
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"✅ Email sent to {', '.join(EMAIL_RECIPIENTS)}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


# ── Main ─────────────────────────────────────────────────────────────────────

async def run_daily_summary():
    """Query real jobs from DB and deliver report via email + Telegram."""
    start_time = datetime.now()
    logger.info("📋 Starting daily summary report generation...")

    # Pull real data
    jobs = get_todays_jobs(limit=50)
    stats = get_daily_stats()

    if not jobs:
        logger.warning("No jobs found in the last 24 hours — skipping report")
        # Still send a short Telegram note so you know the pipeline ran
        await send_telegram(
            "<b>📋 Daily Job Report</b>\n\n"
            "⚠️ No new jobs scraped in the last 24 hours.\n"
            "Check that the Daily JobSpy Scraper task ran at 5:30 AM."
        )
        return True

    logger.info(f"Found {len(jobs)} jobs from last 24 hours")

    # Format and deliver
    now = datetime.now()
    subject = f"📋 Daily Job Report — {now.strftime('%B %d, %Y')} ({len(jobs)} jobs)"

    # Telegram (top 10, concise)
    tg_msg = format_telegram_message(jobs, stats)
    await send_telegram(tg_msg)

    # Email (full list, styled)
    email_html = format_email_html(jobs, stats)
    send_email(subject, email_html)

    # Save markdown report to disk
    try:
        report_dir = Path(parent_dir) / "reports" / "daily" / now.strftime('%Y-%m-%d')
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"daily_summary_{now.strftime('%H%M')}.md"

        sections = _section_jobs(jobs)
        md_lines = [
            f"# Daily Job Report — {now.strftime('%A, %B %d, %Y')}",
            "",
            f"**Jobs found:** {stats.get('today_total', 0)}",
            f"**With salary:** {stats.get('today_with_salary', 0)}",
            f"**Remote:** {stats.get('today_remote', 0)}",
            f"**DB total:** {stats.get('db_total', 0)}",
            "",
        ]

        for section_title, section_key in [
            ("Remote Jobs", "remote"),
            ("Newest Posted", "newest"),
            ("Highest Alignment Score", "top_scored"),
        ]:
            section_jobs = sections[section_key]
            if section_jobs:
                md_lines.append(f"## {section_title} ({len(section_jobs)})")
                md_lines.append("")
                for i, job in enumerate(section_jobs[:15], 1):
                    sal = _salary_str(job)
                    loc = job.get('location', '') or 'Unknown'
                    age = _job_age(job)
                    score = job.get('alignment_score')
                    score_str = f" | Score: {score:.0f}%" if score else ""
                    md_lines.append(f"{i}. **{job['title']}** — {job['company']} ({loc}) — {sal} — {age}{score_str}")
                md_lines.append("")

        report_path.write_text("\n".join(md_lines), encoding='utf-8')
        logger.info(f"📄 Report saved to {report_path}")
    except Exception as e:
        logger.warning(f"Failed to save report file: {e}")

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"✅ Daily summary completed in {duration:.1f}s")
    return True


def main():
    """Main function for Windows Task Scheduler."""
    # Force UTF-8 output on Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    print("📋 Daily Job Summary Report")
    print("=" * 40)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        success = asyncio.run(run_daily_summary())
        exit_code = 0 if success else 1
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        logger.error(f"Critical error in daily summary: {e}", exc_info=True)
        exit_code = 1

    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
