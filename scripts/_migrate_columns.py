"""One-shot migration: add new ML columns to jobs table if missing."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "job_tracker.db"

NEW_COLS = [
    ("semantic_alignment_score", "REAL"),
    ("role_type_label",          "TEXT"),
    ("job_category",             "TEXT"),
    ("category_confidence",      "REAL"),
]

conn = sqlite3.connect(DB)
existing = {r[1] for r in conn.execute("PRAGMA table_info(jobs)")}
added = []
for col, typ in NEW_COLS:
    if col not in existing:
        conn.execute(f"ALTER TABLE jobs ADD COLUMN {col} {typ}")
        added.append(col)
conn.commit()

if added:
    print(f"Added columns: {added}")
else:
    print("All columns already present — nothing to migrate.")

# Verify
present = [r[1] for r in conn.execute("PRAGMA table_info(jobs)")
           if r[1] in {c for c, _ in NEW_COLS}]
print(f"Confirmed present: {present}")
conn.close()
