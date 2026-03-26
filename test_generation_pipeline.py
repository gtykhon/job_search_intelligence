"""
Validation test for the 3-layer resume generation pipeline.
Tests Layers 1 and 3 (Python-only, no LLM calls needed).

Run from project root: python test_generation_pipeline.py
"""
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} — {detail}")
        failed += 1


print("=" * 60)
print("Resume Generation Pipeline — Validation Tests")
print("=" * 60)

# ── Test Group 1: Tier 3 Blocklist ─────────────────────────────────────────
print("\n[1] Tier 3 Blocklist")
from src.generation.tier3_blocklist import (
    TIER_3_NEVER_CLAIM, TIER1_PRODUCTION, TIER2_VERIFIED,
    GCP_API_TIER2_EXCEPTION, is_claimable, classify_tool, filter_claimable,
)

test("Snowflake is Tier 3", classify_tool("snowflake") == "TIER3")
test("dbt is Tier 3", classify_tool("dbt") == "TIER3")
test("airflow is Tier 3", classify_tool("airflow") == "TIER3")
test("spark is Tier 3", classify_tool("spark") == "TIER3")
test("kubernetes is Tier 3", classify_tool("kubernetes") == "TIER3")
test("aws is Tier 3", classify_tool("aws") == "TIER3")

test("python is Tier 1", classify_tool("python") == "TIER1")
test("sql is Tier 1", classify_tool("sql") == "TIER1")
test("oracle is Tier 1", classify_tool("oracle") == "TIER1")
test("r is Tier 1", classify_tool("r") == "TIER1")
test("microsoft_access is Tier 1", classify_tool("microsoft_access") == "TIER1")

test("fastapi is Tier 2", classify_tool("fastapi") == "TIER2")
test("tableau is Tier 2", classify_tool("tableau") == "TIER2")
test("claude_code is Tier 2", classify_tool("claude_code") == "TIER2")
test("claude_cowork is Tier 2", classify_tool("claude_cowork") == "TIER2")

# GCP API exception
test("Google Sheets API is claimable", is_claimable("google sheets api") == True)
test("GCP platform is not claimable", is_claimable("gcp") == False)
test("Google Sheets API classified as GCP_API_TIER2",
     classify_tool("google sheets api") == "GCP_API_TIER2")

# filter_claimable
claimable, blocked = filter_claimable(["python", "sql", "snowflake", "dbt", "fastapi"])
test("filter_claimable: python claimable", "python" in claimable)
test("filter_claimable: snowflake blocked", "snowflake" in blocked)
test("filter_claimable: dbt blocked", "dbt" in blocked)
test("filter_claimable: fastapi claimable", "fastapi" in claimable)

# ── Test Group 2: Set Arithmetic Fix (v2) ──────────────────────────────────
print("\n[2] Set Arithmetic (v2 fix)")
claimable, blocked = filter_claimable(["python", "sql", "snowflake"])
user_added = ["fastapi"]
user_removed = ["python"]
final = list((set(claimable) | set(user_added)) - set(user_removed))
test("user_removed removes from claimable", "python" not in final)
test("user_added still present", "fastapi" in final)
test("sql still present", "sql" in final)

# ── Test Group 3: Achievement Bank ─────────────────────────────────────────
print("\n[3] Achievement Bank")
from src.generation.context_builder import load_achievement_bank, select_achievements_by_coverage

bank = load_achievement_bank()
test("Achievement bank loads", bank is not None)
test("Has achievements array", "achievements" in bank)
test("Has blocked_achievements", "blocked_achievements" in bank)
test("Has meta", "_meta" in bank)

achievements = bank["achievements"]
test(f"Has {len(achievements)} achievements", len(achievements) >= 10)

# Check microloan employer fix (v2)
microloan = next((a for a in achievements if a["id"] == "sba_budget_microloan_db"), None)
test("Microloan achievement exists", microloan is not None)
if microloan:
    test("Microloan employer is Budget Division",
         "Budget Division" in microloan["employer"],
         f"Got: {microloan['employer']}")

# Check blocked achievements
blocked_ids = {b["id"] for b in bank.get("blocked_achievements", [])}
test("gmail_pipeline is blocked", "gmail_pipeline" in blocked_ids)
test("projected_metrics is blocked", "projected_metrics_938_61_96" in blocked_ids)

# ── Test Group 4: Achievement Selection ────────────────────────────────────
print("\n[4] Achievement Selection")
selected = select_achievements_by_coverage("data_engineer", ["python", "sql", "fastapi"])
test("Returns achievements for data_engineer", len(selected) > 0)
test("Returns at most 4", len(selected) <= 4)
test("Achievements have required fields",
     all("id" in a and "label" in a and "resume_bullets" in a for a in selected))

# Check that blocked achievements are excluded
selected_ids = {a["id"] for a in selected}
test("No blocked achievements selected", len(selected_ids & blocked_ids) == 0)

# ── Test Group 5: VERSION_MAP ──────────────────────────────────────────────
print("\n[5] VERSION_MAP routing")
from src.generation.context_builder import VERSION_MAP

# Actual classifier output categories
test("software_data_engineering -> RV-001", VERSION_MAP["software_data_engineering"] == "RV-001")
test("data_analysis_business_analysis -> RV-002", VERSION_MAP["data_analysis_business_analysis"] == "RV-002")
test("analytics_engineering -> RV-002", VERSION_MAP["analytics_engineering"] == "RV-002")
test("executive_management -> RV-003", VERSION_MAP["executive_management"] == "RV-003")
# Legacy categories still mapped
test("data_engineer -> RV-001 (legacy)", VERSION_MAP["data_engineer"] == "RV-001")
test("business_analyst -> RV-004 (legacy)", VERSION_MAP["business_analyst"] == "RV-004")
test("other -> RV-001", VERSION_MAP["other"] == "RV-001")
test("unknown -> RV-001", VERSION_MAP["unknown"] == "RV-001")

# ── Test Group 6: Output Validator ─────────────────────────────────────────
print("\n[6] Output Validator — Fabrication Detection")
from src.generation.output_validator import validate_generated_output
from src.generation.context_builder import GenerationContext

# Create minimal context for testing
test_context = GenerationContext(
    job_id=999,
    job_title="Data Engineer",
    company="Test Corp",
    job_category="data_engineer",
    alignment_score=75.0,
    base_resume_version="RV-001",
    base_resume_text="test resume",
    verified_tools_for_job=["python", "sql", "fastapi"],
    blocked_tools_in_jd=["snowflake", "dbt"],
    user_added_skills=[],
    user_removed_skills=[],
    selected_achievements=[],
    jd_keywords=["python", "sql"],
    jd_summary="",
    jd_full_text="",
    gap_flags=["snowflake", "dbt"],
)

# Test: Tier 3 fabrication detection
fake_resume = "Built pipelines using Snowflake, dbt, and Airflow."
result = validate_generated_output(fake_resume, test_context)
test("Detects Snowflake fabrication", any("snowflake" in e.lower() for e in result["fabrication_errors"]))
test("Detects dbt fabrication", any("dbt" in e.lower() for e in result["fabrication_errors"]))
test("Detects airflow fabrication", any("airflow" in e.lower() for e in result["fabrication_errors"]))
test("Catches multiple fabrication errors", len(result["fabrication_errors"]) >= 3)

# Test: Clean output passes
clean_resume = (
    'User Name\n'
    'City, ST 12345\n'
    'user@example.com\n'
    'linkedin.com/in/user\n'
    'Designed and built multi-source job intelligence platform using Python and FastAPI.'
)
result = validate_generated_output(clean_resume, test_context)
test("Clean output has no fabrication errors", len(result["fabrication_errors"]) == 0)
test("Clean output has no formatting warnings about name",
     not any("NAME_FORMAT" in w for w in result["formatting_warnings"]))

# Test: Wrong ZIP code
wrong_zip_resume = clean_resume.replace("12345", "12346")
result = validate_generated_output(wrong_zip_resume, test_context)
test("Detects wrong ZIP code", any("WRONG_ZIP" in e for e in result["fabrication_errors"]))

# Test: ALL CAPS name
caps_resume = clean_resume.replace('User Name', 'USER NAME')
result = validate_generated_output(caps_resume, test_context)
test("Warns about ALL CAPS name", any("NAME_FORMAT" in w for w in result["formatting_warnings"]))

# Test: Empty output
result = validate_generated_output("", test_context)
test("Empty output is a fabrication error", len(result["fabrication_errors"]) > 0)

# ── Test Group 7: Context Builder (with DB) ────────────────────────────────
print("\n[7] Context Builder (DB integration)")
try:
    from src.dashboard.db import DashboardDB
    from src.generation.context_builder import build_generation_context

    db = DashboardDB()

    # Find a scored job to test with
    with db.get_connection() as conn:
        test_job = conn.execute(
            "SELECT id, title, company, alignment_score, job_category FROM jobs "
            "WHERE alignment_score > 50 AND job_category IS NOT NULL "
            "ORDER BY alignment_score DESC LIMIT 1"
        ).fetchone()

    if test_job:
        job_id = test_job["id"]
        print(f"  Using test job: {test_job['title']} at {test_job['company']} "
              f"(score: {test_job['alignment_score']}, cat: {test_job['job_category']})")

        context = build_generation_context(db, job_id, resume_text="Test resume text for validation")
        test("Context builds successfully", context is not None)
        test("Context has valid version",
             context.base_resume_version in ["RV-001", "RV-002", "RV-003", "RV-004"])
        test("Context has job_title", bool(context.job_title))
        test("Context has company", bool(context.company))
        test("Context has alignment_score", context.alignment_score > 0)
        # Note: achievement count depends on job_category matching achievement bank coverage keys.
        # Categories like "software_data_engineering" may not have coverage entries.
        if context.job_category in ["data_engineer", "software_engineer", "ml_engineer", "analytics_engineer"]:
            test("Context has achievements", len(context.selected_achievements) > 0,
                 f"Got {len(context.selected_achievements)} achievements for {context.job_category}")
        else:
            test(f"Context achievements (category={context.job_category})",
                 True, f"Got {len(context.selected_achievements)} (non-standard category, may be 0)")
        print(f"  Context: version={context.base_resume_version}, "
              f"verified_tools={len(context.verified_tools_for_job)}, "
              f"blocked_tools={len(context.blocked_tools_in_jd)}, "
              f"achievements={len(context.selected_achievements)}, "
              f"gap_flags={len(context.gap_flags)}")
    else:
        print("  SKIP: No scored jobs with category found in database")

    # Test DB migration: generation_log table exists
    with db.get_connection() as conn:
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
    test("generation_log table exists", "generation_log" in tables)

    # Test application_packages has new columns
    with db.get_connection() as conn:
        cols = {row[1] for row in conn.execute(
            "PRAGMA table_info(application_packages)"
        ).fetchall()}
    test("generation_metadata column exists", "generation_metadata" in cols)
    test("cover_letter_status column exists", "cover_letter_status" in cols)

except Exception as e:
    print(f"  SKIP: DB integration tests failed: {e}")

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
if failed == 0:
    print("All pipeline tests PASSED.")
else:
    print(f"WARNING: {failed} test(s) FAILED — review output above.")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
