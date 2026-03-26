#!/usr/bin/env python3
"""
50-job random pipeline validation.

Pulls 50 random jobs from the DB (stratified by source_site for variety),
runs them through the full gate pipeline, and prints:
  - Per-job gate-by-gate results
  - Aggregate stats: PROCEED/REJECT counts, gate rejection breakdown
  - Semantic scoring status (confirms sentence-transformers is live)
"""
import sqlite3, asyncio, sys, random
from pathlib import Path
from types import SimpleNamespace
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

DB = Path(__file__).parent.parent / "data" / "job_tracker.db"
N_JOBS = 50
SEED   = 99   # reproducible run; change to None for true random


# ── DB helpers ────────────────────────────────────────────────────────────────

def pull_random_jobs(n: int, seed) -> list[dict]:
    """Pull n random jobs that have a title and description."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, company, location, description,
               salary_min, salary_max, job_url, source_site,
               clearance_required, remote_type, alignment_score,
               semantic_alignment_score
        FROM jobs
        WHERE title IS NOT NULL
          AND description IS NOT NULL
          AND length(description) > 100
        ORDER BY RANDOM()
        LIMIT ?
    """, (n * 3,))   # pull 3× then sample to get variety
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows[:n]


def to_ns(r: dict) -> SimpleNamespace:
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


def fmt_salary(job: SimpleNamespace) -> str:
    lo = f"${int(job.salary_min):,}" if job.salary_min else "?"
    hi = f"${int(job.salary_max):,}" if job.salary_max else "?"
    return f"{lo}-{hi}" if (job.salary_min or job.salary_max) else "unlisted"


# ── Semantic scorer bootstrap ─────────────────────────────────────────────────

def init_semantic_scorer():
    """Load the resume and warm up the semantic scorer if available."""
    try:
        from src.intelligence.semantic_scorer import get_semantic_scorer
        # Minimal resume stub — enough to compute cosine similarity
        resume = (
            "Senior software engineer and data engineering lead with 8+ years "
            "building distributed systems, data pipelines, ML infrastructure, "
            "and cloud-native backends. Expert in Python, SQL, Spark, Kafka, "
            "AWS, GCP, Kubernetes, and Airflow. Strong ML/AI integration experience."
        )
        scorer = get_semantic_scorer(resume)
        if scorer.is_available():
            print("[OK] sentence-transformers ACTIVE -- semantic scoring ON")
            return scorer
        else:
            print("[WARN] sentence-transformers not available -- semantic scoring OFF")
            return None
    except Exception as e:
        print(f"[WARN] Semantic scorer init failed: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

async def run():
    from src.screening import get_screening_pipeline, reset_screening_pipeline

    # ── Semantic scorer
    semantic_scorer = init_semantic_scorer()

    # ── Pipeline
    reset_screening_pipeline()
    pipeline = get_screening_pipeline()
    gate_names = [g.name for g in pipeline._gates]
    print(f"Active gates ({len(gate_names)}): {', '.join(gate_names)}")
    print()

    # ── Pull jobs
    jobs_raw = pull_random_jobs(N_JOBS, SEED)
    print(f"Pulled {len(jobs_raw)} jobs for testing  (seed={SEED})\n")
    print("=" * 78)

    # ── Tracking
    summary   = []   # (idx, id, title, company, verdict, gate, reason, sem_score)
    proceed   = 0
    reject    = 0
    gate_hits = Counter()
    sem_computed = 0

    for idx, raw in enumerate(jobs_raw, 1):
        job = to_ns(raw)

        # Compute live semantic score if scorer is available and DB value missing
        live_sem = None
        if semantic_scorer and job.description:
            try:
                result_sem = semantic_scorer.score(job.description, job.title)
                if result_sem:
                    live_sem = result_sem.score_0_100
                    sem_computed += 1
                    # Inject into job namespace so Gate 0I can use it
                    job.semantic_alignment_score = live_sem
            except Exception:
                pass

        result = await pipeline.screen_job(job)
        verdict = "PROCEED" if result.passed else "REJECT "

        blocking = next(
            (v for v in result.verdicts if v.result.value in ("fail", "override_required")),
            None,
        )
        block_gate   = blocking.gate_name if blocking else "-"
        block_reason = (blocking.reason or "")[:60] if blocking else "all gates passed"

        # ── Score display
        kw  = f"{job.alignment_score:.1f}" if job.alignment_score is not None else "-"
        sem_val = live_sem if live_sem is not None else job.semantic_alignment_score
        sem = f"{sem_val:.1f}" if sem_val is not None else "-"
        if live_sem is not None and job.alignment_score is not None:
            blended = 0.60 * job.alignment_score + 0.40 * live_sem
            blend_str = f"{blended:.1f}"
        else:
            blend_str = "-"

        # ── Print
        print(f"\n[{verdict}] #{job.id:>5}  {job.title[:52]}")
        print(f"           {job.company[:30]}  |  {job.location[:28]}  |  {job.source_site}")
        print(f"           kw={kw}  sem={sem}  blend={blend_str}  salary={fmt_salary(job)}")

        for v in result.verdicts:
            sym = {"pass": "PASS", "fail": "FAIL", "override_required": "OVRD"}.get(
                v.result.value, "????"
            )
            print(f"             {sym}  {v.gate_name:<38}  {(v.reason or '')[:60]}")

        if result.passed:
            proceed += 1
        else:
            reject += 1
            gate_hits[block_gate] += 1

        summary.append((idx, job.id, job.title[:40], job.company[:22],
                        verdict.strip(), block_gate, block_reason, sem))

    # ── Summary table ──────────────────────────────────────────────────────────
    print(f"\n\n{'=' * 78}")
    print("  SUMMARY — 50 RANDOM JOBS")
    print(f"{'=' * 78}")
    print(f"  {'#':<3}  {'ID':<5}  {'Verdict':<7}  {'Title':<40}  {'Blocked at':<28}  Sem")
    print(f"  {'-'*3}  {'-'*5}  {'-'*7}  {'-'*40}  {'-'*28}  {'-'*5}")

    for idx, jid, title, company, verdict, gate, reason, sem in summary:
        v_sym = "PROCEED" if verdict == "PROCEED" else "REJECT "
        print(f"  {idx:<3}  {jid:<5}  {v_sym}  {title:<40}  {gate:<28}  {sem}")

    print(f"\n  PROCEED : {proceed}")
    print(f"  REJECT  : {reject}")
    print(f"  Total   : {proceed + reject}")
    print(f"\n  Semantic scores computed live: {sem_computed}/{N_JOBS}")
    print(f"\n  Rejections by gate:")
    for gate, count in sorted(gate_hits.items(), key=lambda x: -x[1]):
        pct = count / reject * 100 if reject else 0
        print(f"    {gate:<40}  {count:>3} job(s)  ({pct:.0f}% of rejects)")

    # ── Sanity checks ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 78}")
    print("  SANITY CHECKS")
    print(f"{'=' * 78}")

    sales_in_proceed = [
        s for s in summary
        if s[4] == "PROCEED" and any(
            kw in s[2].lower()
            for kw in ["account executive", "sales", "sdr", "bdr", "revenue"]
        )
    ]
    if sales_in_proceed:
        print(f"  [WARN] {len(sales_in_proceed)} sales-ish title(s) slipped through:")
        for s in sales_in_proceed:
            print(f"       #{s[1]}  {s[2]}")
    else:
        print(f"  [OK]  No sales titles in PROCEED set")

    low_align_in_proceed = [
        s for s in summary
        if s[4] == "PROCEED" and s[7] != "-" and float(s[7]) < 40
    ]
    if low_align_in_proceed:
        print(f"  [WARN] {len(low_align_in_proceed)} low-sem-score job(s) in PROCEED:")
        for s in low_align_in_proceed:
            print(f"       #{s[1]}  sem={s[7]}  {s[2]}")
    else:
        print(f"  [OK]  No low-alignment jobs in PROCEED set")

    print()


asyncio.run(run())
