#!/usr/bin/env python3
"""
Live gate test: pulls 5 specific jobs from job_tracker.db and runs them
through the full 9-gate screening pipeline, reporting gate-by-gate results.
"""
import sqlite3, asyncio, sys, json
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

DB = Path(__file__).parent.parent / "data" / "job_tracker.db"
JOB_IDS = [2491, 971, 896, 2569, 2893]

def pull_jobs():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    placeholders = ",".join("?" * len(JOB_IDS))
    cur.execute(f"""
        SELECT id, title, company, location, description,
               salary_min, salary_max, job_url, source_site,
               clearance_required, remote_type, alignment_score,
               semantic_alignment_score
        FROM jobs
        WHERE id IN ({placeholders})
    """, JOB_IDS)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def to_ns(r):
    return SimpleNamespace(
        id=r["id"],
        title=r["title"] or "",
        company=r["company"] or "",
        company_name=r["company"] or "",
        description=r["description"] or "",
        location=r["location"] or "",
        salary_min=r["salary_min"],
        salary_max=r["salary_max"],
        job_url=r["job_url"] or "",
        source_site=r["source_site"] or "",
        clearance_required=r["clearance_required"],
        remote_type=r["remote_type"],
        alignment_score=r["alignment_score"],
        semantic_alignment_score=r["semantic_alignment_score"],
    )

def fmt_salary(job):
    lo = f"${int(job.salary_min):,}" if job.salary_min else "?"
    hi = f"${int(job.salary_max):,}" if job.salary_max else "?"
    if job.salary_min or job.salary_max:
        return f"{lo} - {hi}"
    return "not listed"

async def main():
    from src.screening import get_screening_pipeline, reset_screening_pipeline
    reset_screening_pipeline()
    pipeline = get_screening_pipeline()

    gate_names = [g.name for g in pipeline._gates]
    print(f"Active gates ({len(gate_names)}):")
    for gn in gate_names:
        print(f"  - {gn}")
    print()
    print("=" * 70)

    jobs_raw = pull_jobs()
    jobs = [to_ns(r) for r in jobs_raw]

    for job in jobs:
        result = await pipeline.screen_job(job)
        verdict = "PROCEED" if result.passed else "REJECT"

        print(f"[{verdict}]  #{job.id}  {job.title}")
        print(f"         Company  : {job.company}")
        print(f"         Location : {job.location}")
        print(f"         Salary   : {fmt_salary(job)}")
        sem_str = f"{job.semantic_alignment_score:.1f}" if job.semantic_alignment_score is not None else "—"
        print(f"         Align    : kw={job.alignment_score}  sem={sem_str}")
        print(f"         Source   : {job.source_site}")
        desc_preview = job.description[:250].replace("\n", " ").strip()
        print(f"         Preview  : {desc_preview}...")
        print()
        print("         Gate Results:")

        for v in result.verdicts:
            sym = {
                "pass": "  PASS",
                "fail": "  FAIL",
                "override_required": "  OVRD",
            }.get(v.result.value, "  ????")
            reason = (v.reason or "")[:75]
            print(f"         {sym}  {v.gate_name:<38} {reason}")

        # Show first blocking gate if rejected
        if not result.passed:
            blocking = next(
                (v for v in result.verdicts if v.result.value in ("fail", "override_required")),
                None
            )
            if blocking:
                print(f"\n         >> Blocked by: {blocking.gate_name}")
                print(f"         >> Reason    : {blocking.reason}")

        print()
        print("-" * 70)

asyncio.run(main())
