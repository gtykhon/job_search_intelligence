#!/usr/bin/env python3
"""
False-Negative Review — manual audit of REJECT decisions.

Loads screen_results_latest.json (written by pipeline_analytics.py) and
prints the 100 most "interesting" rejected jobs for human review.

Interestingness tiers (sorted descending):
  Tier 0 — OVERRIDE_REQUIRED verdicts   (pipeline flagged for human review)
  Tier 1 — kw_score >= 75, blocked in gate 0I or 0F  (alignment-gate kills)
  Tier 2 — kw_score >= 70, blocked in any late gate   (passed most checks)
  Tier 3 — kw_score >= 60, blocked by staffing/agency (could be a real role)

Usage:
    python scripts/review_rejects.py
    python scripts/review_rejects.py --limit 50
    python scripts/review_rejects.py --tier 0        # OVERRIDE_REQUIRED only
    python scripts/review_rejects.py --gate 0E_tech_stack
"""

import argparse
import json
import sys
from pathlib import Path

# Force UTF-8 output so non-ASCII job titles don't crash on Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RESULTS_FILE = Path(__file__).parent.parent / "data" / "screen_results_latest.json"

# Gates considered "early" (cheap to reject)
EARLY_GATES  = {"0A_company_research", "0J_role_type", "0B_defense_exclusion",
                "0C_staffing_agency"}
# Gates considered "late" (expensive — job passed most filters first)
LATE_GATES   = {"0I_alignment_score", "0F_compensation_work_model",
                "culture_glassdoor", "0D_ghost_job"}
# Gates worth extra scrutiny — these catch real edge-cases
SCRUTINY_GATES = {"0C_staffing_agency", "0I_alignment_score",
                  "0F_compensation_work_model"}


def tier(r: dict) -> int:
    """Lower = more interesting."""
    if r["block_type"] == "override_required":
        return 0
    gate = r["block_gate"] or ""
    kw   = r["kw_score"] or 0
    if kw >= 75 and gate in ("0I_alignment_score", "0F_compensation_work_model"):
        return 1
    if kw >= 70 and gate in LATE_GATES:
        return 2
    if kw >= 60 and gate in SCRUTINY_GATES:
        return 3
    return 99   # not interesting


def main():
    parser = argparse.ArgumentParser(description="Review rejected jobs for false negatives")
    parser.add_argument("--limit",  type=int, default=100,
                        help="Max jobs to print (default 100)")
    parser.add_argument("--tier",   type=int, default=None,
                        help="Show only this tier (0-3)")
    parser.add_argument("--gate",   type=str, default=None,
                        help="Filter to specific blocking gate")
    parser.add_argument("--min-kw", type=float, default=0,
                        help="Minimum kw_score to include")
    parser.add_argument("--desc",   action="store_true",
                        help="Print JD snippet for each job")
    args = parser.parse_args()

    if not RESULTS_FILE.exists():
        print(f"[ERROR] Results file not found: {RESULTS_FILE}")
        print("Run pipeline_analytics.py first to generate screen_results_latest.json")
        sys.exit(1)

    with open(RESULTS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    all_results  = data["results"]
    generated    = data.get("generated", "?")
    n_screened   = data.get("jobs_screened", len(all_results))

    rejects = [r for r in all_results if not r["passed"]]
    proceed = [r for r in all_results if r["passed"]]

    print()
    print("=" * 76)
    print("  FALSE-NEGATIVE REVIEW — REJECT AUDIT")
    print(f"  Source: {RESULTS_FILE.name}  (generated {generated[:19]})")
    print(f"  Total screened: {n_screened}   PROCEED: {len(proceed)}   REJECT: {len(rejects)}")
    print("=" * 76)

    # Apply filters
    candidates = rejects
    if args.gate:
        candidates = [r for r in candidates if r["block_gate"] == args.gate]
    if args.min_kw:
        candidates = [r for r in candidates if (r["kw_score"] or 0) >= args.min_kw]

    # Score and sort
    scored = [(tier(r), -(r["kw_score"] or 0), r) for r in candidates]
    scored.sort(key=lambda x: (x[0], x[1]))

    if args.tier is not None:
        scored = [(t, k, r) for t, k, r in scored if t == args.tier]

    to_show = scored[:args.limit]

    if not to_show:
        print("\n  No candidates match filters.")
        return

    # Summary of tiers in current selection
    tier_counts = {}
    for t, _, _ in scored:
        tier_counts[t] = tier_counts.get(t, 0) + 1

    print("\n  TIER SUMMARY (before limit):")
    tier_labels = {
        0: "Tier 0 — OVERRIDE_REQUIRED",
        1: "Tier 1 — kw>=75 killed by alignment/comp gate",
        2: "Tier 2 — kw>=70 killed by late gate",
        3: "Tier 3 — kw>=60 killed by staffing gate",
        99: "Tier 99 — low interest (included if limit allows)",
    }
    for t in sorted(tier_counts):
        label = tier_labels.get(t, f"Tier {t}")
        print(f"    {label}: {tier_counts[t]}")
    print(f"\n  Showing {len(to_show)} of {len(scored)} interesting rejects\n")

    # Print each job
    gate_false_neg_count = {}
    for t, _, r in to_show:
        kw_str  = f"{r['kw_score']:.0f}"  if r["kw_score"]  is not None else "  -"
        sem_str = f"{r['sem_score']:.0f}" if r["sem_score"] is not None else "  -"
        gate    = r["block_gate"] or "(passed all)"
        btype   = r["block_type"] or ""

        tier_tag = f"[T{t}]" if t < 99 else "    "

        flag = ""
        if btype == "override_required":
            flag = " <-- OVERRIDE"
        elif t <= 2:
            flag = " <-- POSSIBLE FN"
        elif t == 3:
            flag = " <-- CHECK AGENCY"

        print(f"  {tier_tag}  #{r['id']:<5}  kw={kw_str:<3}  sem={sem_str:<3}  "
              f"gate={gate:<32}  {flag}")
        print(f"           {r['title'][:55]:<55}  ({r['company'][:22]})")
        if r.get("location"):
            print(f"           loc: {r['location'][:60]}")
        if args.desc and r.get("description"):
            snippet = r["description"][:300].replace("\n", " ")
            print(f"           jd:  {snippet}...")
        print()

        gate_false_neg_count[gate] = gate_false_neg_count.get(gate, 0) + 1

    # Gate breakdown of interesting rejects
    print("-" * 76)
    print(f"  GATE BREAKDOWN for these {len(to_show)} jobs:")
    for g, cnt in sorted(gate_false_neg_count.items(), key=lambda x: -x[1]):
        bar = "#" * cnt
        print(f"    {g:<38}  {cnt:>4}  {bar}")

    print()
    interesting = sum(1 for t, _, _ in to_show if t <= 2)
    print(f"  [SUMMARY] {interesting} jobs in Tier 0-2 are worth close inspection.")
    print(f"            Mark any genuine FN (good job wrongly rejected) in the DB")
    print(f"            and add the rejection reason to the gate allowlist if needed.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
