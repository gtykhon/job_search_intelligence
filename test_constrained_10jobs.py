"""
Test the constrained generation pipeline (Layers 1 + 3) on 10 random jobs.
Validates context building, achievement selection, tool classification,
fabrication detection, and settings integration.

Run from project root: python test_constrained_10jobs.py
"""
import sys
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.dashboard.db import DashboardDB
from src.generation.context_builder import (
    build_generation_context, select_achievements_by_coverage,
    VERSION_MAP, _load_gen_thresholds,
)
from src.generation.output_validator import validate_generated_output, _get_score_delta_floor
from src.generation.tier3_blocklist import TIER_3_NEVER_CLAIM, classify_tool

db = DashboardDB()

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} -- {detail}")
        failed += 1


print("=" * 70)
print("Constrained Pipeline -- 10-Job Integration Test")
print("=" * 70)

# ── 0. Settings Integration ──────────────────────────────────────────────
print("\n[0] Settings Integration")

thresholds = _load_gen_thresholds(db)
test("Thresholds load from DB", isinstance(thresholds, dict))
test("min_score_to_generate is numeric", isinstance(thresholds["min_score_to_generate"], (int, float)))
test("achievement_top_n is int", isinstance(thresholds["achievement_top_n"], int))
test("achievement_coverage_min is int", isinstance(thresholds["achievement_coverage_min"], int))
test("tool_overlap_boost is int", isinstance(thresholds["tool_overlap_boost"], int))
print(f"  Loaded thresholds: {thresholds}")

score_delta = _get_score_delta_floor(db)
test("score_delta_floor is float", isinstance(score_delta, float))
test("score_delta_floor in range", 0.5 <= score_delta <= 1.0, f"Got {score_delta}")
print(f"  Score delta floor: {score_delta}")

timeout = int(db.get_setting("gen_request_timeout", "180"))
max_tokens = int(db.get_setting("gen_max_tokens", "4096"))
test("request_timeout is valid", 30 <= timeout <= 600, f"Got {timeout}")
test("max_tokens is valid", 1024 <= max_tokens <= 8192, f"Got {max_tokens}")
print(f"  Timeout: {timeout}s, Max tokens: {max_tokens}")

# ── 1. Select 10 random scored jobs ──────────────────────────────────────
print("\n[1] Selecting 10 Random Jobs")

with db.get_connection() as conn:
    all_jobs = conn.execute(
        "SELECT id, title, company, alignment_score, job_category "
        "FROM jobs WHERE alignment_score > 0 AND job_category IS NOT NULL "
        "ORDER BY RANDOM() LIMIT 10"
    ).fetchall()

test(f"Found {len(all_jobs)} scored jobs", len(all_jobs) >= 1,
     "Need at least 1 scored job with category")

if len(all_jobs) == 0:
    print("\nNo scored jobs found. Exiting.")
    sys.exit(1)

# Use a dummy resume for context building
dummy_resume = (
    'User Name\n'
    'City, ST 12345\n'
    'user@example.com\n'
    'linkedin.com/in/user\n'
    'Senior Data Engineer with 10+ years experience in Python, SQL, and data systems.\n'
)

# ── 2. Test each job through the pipeline ────────────────────────────────
for i, job_row in enumerate(all_jobs, 1):
    job_id = job_row["id"]
    title = job_row["title"]
    company = job_row["company"]
    score = job_row["alignment_score"]
    category = job_row["job_category"]

    print(f"\n[Job {i}/10] #{job_id}: {title} @ {company}")
    print(f"  Score: {score:.1f}, Category: {category}")

    # ── Layer 1: Build context ────────────────────────────────────────
    try:
        context = build_generation_context(db, job_id, resume_text=dummy_resume)
        test(f"  Context builds", context is not None)
    except Exception as e:
        test(f"  Context builds", False, str(e))
        continue

    # Validate context fields
    test(f"  Has job_title", bool(context.job_title))
    test(f"  Has company", bool(context.company))
    expected_version = VERSION_MAP.get(category, "RV-001")
    test(f"  Version = {context.base_resume_version}",
         context.base_resume_version == expected_version,
         f"Expected {expected_version}")

    # Check tool classification
    for tool in context.verified_tools_for_job:
        tier = classify_tool(tool)
        if tier == "TIER3":
            test(f"  No Tier3 in verified: {tool}", False, "Tier3 tool leaked into verified list")
            break
    else:
        test(f"  No Tier3 in verified tools ({len(context.verified_tools_for_job)} tools)", True)

    test(f"  Blocked tools classified correctly",
         all(classify_tool(t) in ("TIER3", "UNKNOWN") for t in context.blocked_tools_in_jd),
         f"Blocked: {context.blocked_tools_in_jd}")

    # Gap flags should be subset of blocked
    test(f"  Gap flags subset of blocked",
         set(context.gap_flags).issubset(set(context.blocked_tools_in_jd)),
         f"Gap flags: {context.gap_flags}")

    # Achievement selection uses configurable thresholds
    test(f"  Achievements <= {thresholds['achievement_top_n']}",
         len(context.selected_achievements) <= thresholds["achievement_top_n"],
         f"Got {len(context.selected_achievements)}")

    # ── Layer 3: Validate clean resume (should pass) ──────────────────
    # Skip score delta check (AlignmentScorer loads sentence-transformers, too slow for batch test)
    # Score delta is already tested in test_generation_pipeline.py
    context.jd_full_text = ""
    clean_result = validate_generated_output(dummy_resume, context, db=db)
    test(f"  Clean resume: 0 fabrication errors",
         len(clean_result["fabrication_errors"]) == 0,
         f"Errors: {clean_result['fabrication_errors']}")

    # ── Layer 3: Validate fabricated resume (should catch) ────────────
    # Inject some Tier 3 tools to simulate fabrication
    tier3_sample = random.sample(sorted(TIER_3_NEVER_CLAIM), min(3, len(TIER_3_NEVER_CLAIM)))
    fake_resume = dummy_resume + f"\nBuilt pipelines using {', '.join(tier3_sample)}."
    fake_result = validate_generated_output(fake_resume, context, db=db)
    test(f"  Detects fabrication ({', '.join(tier3_sample)})",
         len(fake_result["fabrication_errors"]) >= 1,
         f"Expected errors for {tier3_sample}")

    print(f"  Summary: verified={len(context.verified_tools_for_job)}, "
          f"blocked={len(context.blocked_tools_in_jd)}, "
          f"achievements={len(context.selected_achievements)}, "
          f"gaps={len(context.gap_flags)}, "
          f"review={'YES' if context.requires_human_review else 'no'}")

# ── Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
if failed == 0:
    print("All constrained pipeline tests PASSED.")
else:
    print(f"WARNING: {failed} test(s) FAILED -- review output above.")
print("=" * 70)

sys.exit(0 if failed == 0 else 1)
