"""
Tier 3 blocklist — tools extracted from JDs that must never appear in generated output.
These are technologies with no hands-on Grisha experience (Tier 3 / Not Found).
Source of truth: tech_stack_comprehensive.md
Last updated: 2026-03-20 (v2 — audit corrections applied)

v2 changes:
  - Added oracle, r, tableau, microsoft_access to TIER1/TIER2 (were UNKNOWN)
  - Added claude_code, claude_cowork, roo_code, klein to TIER2
  - Removed duplicate fastapi from TIER2
  - GCP_API_TIER2_EXCEPTION now referenced in is_claimable() (was dead code)
"""

# Tools that appear frequently in data engineering JDs but have no authenticated hands-on basis.
# If ANY of these appear in a generated resume, it is a fabrication event.
TIER_3_NEVER_CLAIM: set[str] = {
    # Cloud data platforms
    "snowflake",
    "databricks",
    "bigquery",
    "redshift",
    "synapse",

    # Transformation / orchestration
    "dbt",
    "airflow",
    "dagster",
    "prefect",
    "luigi",
    "metaflow",

    # Big data
    "spark",
    "pyspark",
    "kafka",
    "flink",
    "hadoop",
    "hive",
    "presto",
    "trino",

    # Infrastructure / containers (beyond Docker Desktop basics)
    "kubernetes",
    "k8s",
    "terraform",
    "helm",
    "ansible",
    "pulumi",

    # Cloud platforms with no hands-on basis
    "aws",
    "amazon web services",
    "gcp",          # Platform-level only — GCP APIs are Tier 2, see GCP_API_TIER2_EXCEPTION
    "google cloud",

    # ML/data tooling
    "mlflow",
    "kubeflow",
    "feast",
    "great expectations",
    "dvc",
    "weights and biases",
    "wandb",

    # Databases with no hands-on
    "cassandra",
    "mongodb",
    "elasticsearch",
    "neo4j",
    "dynamodb",
    "cosmos db",
}

# GCP APIs exception: These are Tier 2 (personal projects, API-level only).
# Claim only in this limited scope — NOT platform engineering.
# v2 FIX: This set is now checked in is_claimable() — was dead code in v1.
GCP_API_TIER2_EXCEPTION: set[str] = {
    "google sheets api",
    "google drive api",
    "gmail api",   # NOTE: gmail_pipeline project is BLOCKED. Route to n8n instead.
    "google docs api",
    "google services api",
}

# Tools that are Tier 2 (personal projects, full architecture ownership).
# Safe to claim for job_search_intelligence-adjacent roles.
# v2 FIX: removed duplicate fastapi; added claude_code, claude_cowork, roo_code, klein, tableau
TIER2_VERIFIED: set[str] = {
    "fastapi",
    "streamlit",
    "sqlite",
    "sqlalchemy",
    "plotly",
    "htmx",
    "jinja2",
    "ollama",
    "sentence-transformers",
    "all-minilm-l6-v2",
    "python-jobspy",
    "beautifulsoup4",
    "aiohttp",
    "telethon",
    "scikit-learn",    # scope: TF-IDF, cosine similarity, ML role classifier (7-category)
    "langflow",
    "n8n",
    "uipath",
    "react",
    "nodejs",
    "javascript",
    "claude_code",     # v2: AI-augmented development tool (Gabi feedback 2026-03-18)
    "claude_cowork",   # v2: AI-augmented development tool (Gabi feedback 2026-03-18)
    "roo_code",        # v2: AI coding assistant (tech_stack_comprehensive.md — Tier 2, in use)
    "klein",           # v2: AI coding assistant (tech_stack_comprehensive.md — Tier 2, in use)
    "tableau",         # v2: Tier 2 — USDA Innovation Center, ~4 months (tech_stack_comprehensive.md)
}

# Tools that are Tier 1 (production, 10+ years).
# v2 FIX: added oracle, r, microsoft_access (were UNKNOWN, confirmed in tech_stack/resume)
TIER1_PRODUCTION: set[str] = {
    "python",
    "sql",
    "vba",
    "pandas",
    "azure",
    "azure_form_recognizer",
    "azure_blob_storage",
    "azure_web_apps",
    "azure_devops",
    "power_bi",
    "git",
    "github",
    "anthropic",
    "claude_api",
    "oracle",          # v2: Oracle Database Systems (tech_stack_comprehensive.md line 45)
    "r",               # v2: R programming — used at OCRM for statistical analysis
    "microsoft_access", # v2: VBA-SQL pipelines, 10+ years (tech_stack_comprehensive.md line 45)
}


def is_claimable(tool: str) -> bool:
    """
    Return True if the tool can be claimed in a resume. False if Tier 3.

    v2 FIX: Now checks GCP_API_TIER2_EXCEPTION before blocking GCP-related terms.
    Without this, "Google Sheets API" would hit "gcp" in TIER_3_NEVER_CLAIM and get
    incorrectly blocked despite being Tier 2 (API-level personal project usage).
    """
    normalized = tool.lower().strip()

    # Check GCP API exception FIRST — these are Tier 2 despite "gcp" being Tier 3
    if normalized in GCP_API_TIER2_EXCEPTION:
        return True

    return normalized not in TIER_3_NEVER_CLAIM


def classify_tool(tool: str) -> str:
    """
    Classify a tool into its tier.
    Returns: 'TIER1' | 'TIER2' | 'GCP_API_TIER2' | 'TIER3' | 'UNKNOWN'
    """
    normalized = tool.lower().strip()

    # Check GCP API exception first
    if normalized in GCP_API_TIER2_EXCEPTION:
        return "GCP_API_TIER2"

    if normalized in TIER_3_NEVER_CLAIM:
        return "TIER3"
    if normalized in TIER1_PRODUCTION:
        return "TIER1"
    if normalized in TIER2_VERIFIED:
        return "TIER2"
    return "UNKNOWN"


def filter_claimable(tools: list[str]) -> tuple[list[str], list[str]]:
    """
    Split a list of tools into (claimable, blocked).
    claimable = Tier 1 + Tier 2 + GCP API exceptions
    blocked = Tier 3 (fabrication risk)
    """
    claimable = [t for t in tools if is_claimable(t)]
    blocked = [t for t in tools if not is_claimable(t)]
    return claimable, blocked
