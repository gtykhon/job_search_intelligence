#!/usr/bin/env python3
"""
Batch gate tester — runs 5 batches of 5 jobs through the full screening pipeline.
Reports gate-by-gate results and a summary table.
"""
import sqlite3, asyncio, sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

DB = Path(__file__).parent.parent / "data" / "job_tracker.db"

ALL_IDS = [
    # ── Targeted regression / new-gate verification batches ──────────────
    [612,  616,  2957, 517,  1711],   # Batch 6  (sales titles, geography, align, clearance fix)
    [1828, 475,  2959, 213,  2964],   # Batch 7  (clearance fix, remote presales, align, geo x2)
]

def pull_jobs(ids):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    placeholders = ",".join("?" * len(ids))
    cur.execute(f"""
        SELECT id, title, company, location, description,
               salary_min, salary_max, job_url, source_site,
               clearance_required, remote_type, alignment_score,
               semantic_alignment_score
        FROM jobs WHERE id IN ({placeholders})
    """, ids)
    rows = {r["id"]: dict(r) for r in cur.fetchall()}
    conn.close()
    return [rows[i] for i in ids if i in rows]

def to_ns(r):
    return SimpleNamespace(
        id=r["id"], title=r["title"] or "",
        company=r["company"] or "", company_name=r["company"] or "",
        description=r["description"] or "", location=r["location"] or "",
        salary_min=r["salary_min"], salary_max=r["salary_max"],
        job_url=r["job_url"] or "", source_site=r["source_site"] or "",
        clearance_required=r["clearance_required"],
        remote_type=r["remote_type"], alignment_score=r["alignment_score"],
        semantic_alignment_score=r["semantic_alignment_score"],
    )

def fmt_salary(job):
    lo = f"${int(job.salary_min):,}" if job.salary_min else "?"
    hi = f"${int(job.salary_max):,}" if job.salary_max else "?"
    return f"{lo}-{hi}" if (job.salary_min or job.salary_max) else "unlisted"

async def run_batches():
    from src.screening import get_screening_pipeline, reset_screening_pipeline
    reset_screening_pipeline()
    pipeline = get_screening_pipeline()

    summary = []   # (batch, id, title, company, verdict, blocking_gate, reason)

    for batch_num, ids in enumerate(ALL_IDS, 1):
        print(f"\n{'='*70}")
        print(f"  BATCH {batch_num}")
        print(f"{'='*70}")
        jobs = [to_ns(r) for r in pull_jobs(ids)]

        for job in jobs:
            result = await pipeline.screen_job(job)
            verdict = "PROCEED" if result.passed else "REJECT"

            blocking = next(
                (v for v in result.verdicts if v.result.value in ("fail", "override_required")),
                None
            )
            block_gate   = blocking.gate_name if blocking else "—"
            block_reason = (blocking.reason or "")[:65] if blocking else "all gates passed"
            block_type   = blocking.result.value.upper() if blocking else ""

            sem = f"sem={job.semantic_alignment_score:.0f}" if job.semantic_alignment_score is not None else "sem=—"
            print(f"\n  [{verdict}]  #{job.id}  {job.title}")
            print(f"           {job.company}  |  {job.location}  |  {job.source_site}  |  align={job.alignment_score}  |  {sem}  |  salary={fmt_salary(job)}")

            for v in result.verdicts:
                sym = {"pass": "PASS", "fail": "FAIL", "override_required": "OVRD"}.get(v.result.value, "????")
                reason_short = (v.reason or "")[:68]
                print(f"           {sym}  {v.gate_name:<38} {reason_short}")

            if not result.passed:
                print(f"\n           >> {block_type}  {block_gate}")
                print(f"           >> {block_reason}")

            summary.append((batch_num, job.id, job.title[:38], job.company[:22],
                            verdict, block_gate, block_reason))

    # ── Summary table ──────────────────────────────────────────────────
    print(f"\n\n{'='*70}")
    print("  SUMMARY — ALL 25 JOBS")
    print(f"{'='*70}")
    print(f"  {'B':<2}  {'ID':<5}  {'Verdict':<7}  {'Title':<38}  {'Blocked by':<30}  Reason")
    print(f"  {'-'*2}  {'-'*5}  {'-'*7}  {'-'*38}  {'-'*30}  {'-'*30}")
    proceed_count = 0
    reject_count  = 0
    gate_counts   = {}
    for b, jid, title, company, verdict, gate, reason in summary:
        v_sym = "PROCEED" if verdict == "PROCEED" else "REJECT "
        print(f"  {b:<2}  {jid:<5}  {v_sym}  {title:<38}  {gate:<30}  {reason[:40]}")
        if verdict == "PROCEED":
            proceed_count += 1
        else:
            reject_count += 1
            gate_counts[gate] = gate_counts.get(gate, 0) + 1

    print(f"\n  PROCEED: {proceed_count}  |  REJECT: {reject_count}  |  Total: {proceed_count+reject_count}")
    print(f"\n  Rejections by gate:")
    for gate, count in sorted(gate_counts.items(), key=lambda x: -x[1]):
        print(f"    {gate:<40} {count} job(s)")

asyncio.run(run_batches())
