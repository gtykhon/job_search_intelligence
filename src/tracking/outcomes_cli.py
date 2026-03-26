"""
CLI commands for the Outcomes Tracker.

Usage:
    python -m src.tracking.outcomes_cli log --platform linkedin --outcome interview
    python -m src.tracking.outcomes_cli stats --days 30
    python -m src.tracking.outcomes_cli diagnose
    python -m src.tracking.outcomes_cli correlate
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tracking.outcomes_tracker import ApplicationOutcome, OutcomeType, OutcomesTracker


def _get_tracker() -> OutcomesTracker:
    db_candidates = [
        Path("data/job_search.db"),
        Path("job_search.db"),
    ]
    for p in db_candidates:
        if p.exists():
            return OutcomesTracker(str(p))
    # Create in default location
    return OutcomesTracker()


def cmd_log(platform: str, outcome: str, job_id=None, notes=None,
            auth_score=None, hm_research=False) -> None:
    """Log a new application outcome."""
    try:
        ot = OutcomeType(outcome.lower())
    except ValueError:
        valid = [o.value for o in OutcomeType]
        print(f"Invalid outcome '{outcome}'. Valid: {', '.join(valid)}")
        return

    tracker = _get_tracker()
    record_id = tracker.log_outcome(ApplicationOutcome(
        platform=platform,
        outcome=ot,
        job_id=int(job_id) if job_id else None,
        authenticity_score=float(auth_score) if auth_score else None,
        hm_research_done=hm_research,
        notes=notes,
    ))
    print(f"Logged outcome id={record_id}: {platform} / {outcome}")


def cmd_stats(days: int = 30) -> None:
    """Print outcome stats for the last N days."""
    tracker = _get_tracker()
    stats = tracker.get_stats(days=days)
    print(f"\n=== Outcome Stats (last {days} days) ===")
    print(f"Total applications : {stats.total_applications}")
    print(f"Interview rate     : {stats.interview_rate:.1%}")
    print(f"Offer rate         : {stats.offer_rate:.1%}")
    print(f"Avg auth score     : {stats.avg_authenticity_score or 'N/A'}")
    print(f"HM research rate   : {stats.hm_research_rate:.1%}")
    print(f"\nBy outcome: {json.dumps(stats.by_outcome, indent=2)}")
    print(f"By platform: {json.dumps(stats.by_platform, indent=2)}")
    if stats.diagnostic_triggered:
        print(f"\n[DIAGNOSTIC] {stats.diagnostic_message}")


def cmd_diagnose() -> None:
    """Run the weekly diagnostic analysis."""
    tracker = _get_tracker()
    stats = tracker.run_weekly_analysis()
    if stats.diagnostic_triggered:
        print(f"[ALERT] {stats.diagnostic_message}")
    else:
        print(f"No diagnostic triggered. {stats.total_applications} applications, "
              f"{stats.interview_rate:.1%} interview rate.")


def cmd_correlate() -> None:
    """Print authenticity score and HM research correlations."""
    tracker = _get_tracker()
    print("\n=== Authenticity Score vs Outcomes ===")
    print(json.dumps(tracker.correlate_authenticity(), indent=2))
    print("\n=== HM Research vs Outcomes ===")
    print(json.dumps(tracker.correlate_hm_research(), indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Outcomes Tracker CLI")
    sub = parser.add_subparsers(dest="cmd")

    p_log = sub.add_parser("log", help="Log an outcome")
    p_log.add_argument("--platform", required=True)
    p_log.add_argument("--outcome", required=True)
    p_log.add_argument("--job-id", default=None)
    p_log.add_argument("--notes", default=None)
    p_log.add_argument("--auth-score", default=None, type=float)
    p_log.add_argument("--hm-research", action="store_true")

    p_stats = sub.add_parser("stats", help="View stats")
    p_stats.add_argument("--days", type=int, default=30)

    sub.add_parser("diagnose", help="Run weekly diagnostic")
    sub.add_parser("correlate", help="Show correlations")

    args = parser.parse_args()
    if args.cmd == "log":
        cmd_log(args.platform, args.outcome, args.job_id, args.notes,
                args.auth_score, args.hm_research)
    elif args.cmd == "stats":
        cmd_stats(args.days)
    elif args.cmd == "diagnose":
        cmd_diagnose()
    elif args.cmd == "correlate":
        cmd_correlate()
    else:
        parser.print_help()
