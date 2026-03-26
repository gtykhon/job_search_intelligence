#!/usr/bin/env python3
"""
List/Filter Connections stored in the database (network_connections table)

Examples:
  # List the latest 50 connections
  python scripts/list_connections.py --limit 50

  # Filter by company and export to CSV (UTF-8 BOM)
  python scripts/list_connections.py --company microsoft --csv output/microsoft_connections.csv

  # Filter by title and location, derive seniority in output
  python scripts/list_connections.py --title engineer --location seattle --show-seniority

  # Filter by derived seniority only (computed from title)
  python scripts/list_connections.py --seniority senior --show-seniority
"""

import argparse
import sqlite3
from pathlib import Path
from typing import List, Dict
import csv
import json
import sys
from src.database.enhanced_database_manager import EnhancedDatabaseManager


def derive_seniority(title: str) -> str:
    t = (title or "").lower()
    if any(k in t for k in ["chief ", " cto", " ceo", " cfo", " coo", "president", "founder", "co-founder"]):
        return "Executive"
    if any(k in t for k in ["vice president", " vp ", "svp", "avp", "director", "principal", "lead "]):
        return "Senior"
    if any(k in t for k in ["manager", "supervisor", "coordinator"]):
        return "Mid"
    if any(k in t for k in ["junior", " jr", "associate", "assistant", "intern"]):
        return "Junior"
    return "Unknown"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="List/Filter connections from network_connections")
    p.add_argument("--db", default="job_search.db", help="Path to SQLite DB")
    p.add_argument("--name", default=None, help="Name contains (case-insensitive)")
    p.add_argument("--title", default=None, help="Title/headline contains")
    p.add_argument("--company", default=None, help="Company contains")
    p.add_argument("--industry", default=None, help="Industry contains")
    p.add_argument("--location", default=None, help="Location contains")
    p.add_argument("--seniority", default=None, choices=["executive","senior","mid","junior","unknown"], help="Derived seniority filter")
    p.add_argument("--limit", type=int, default=100, help="Limit rows (default 100)")
    p.add_argument("--offset", type=int, default=0, help="Offset rows (default 0)")
    p.add_argument("--order", default="updated_at desc", help="SQL ORDER BY clause (default 'updated_at desc')")
    p.add_argument("--csv", default=None, help="Write results to CSV (UTF-8 BOM)")
    p.add_argument("--json", default=None, help="Write results to JSON (UTF-8)")
    p.add_argument("--show-seniority", action="store_true", help="Show derived seniority column in output")
    return p.parse_args()


def build_query(args: argparse.Namespace):
    where = ["1=1"]
    params: List[str] = []
    def like_clause(col: str, val: str):
        nonlocal where, params
        where.append(f"LOWER({col}) LIKE ?")
        params.append(f"%{val.lower()}%")

    if args.name:
        like_clause("connection_name", args.name)
    if args.title:
        like_clause("connection_title", args.title)
    if args.company:
        like_clause("connection_company", args.company)
    if args.industry:
        like_clause("connection_industry", args.industry)
    if args.location:
        like_clause("connection_location", args.location)

    sql = (
        "SELECT connection_id, connection_name, connection_title, "
        "connection_company, connection_industry, connection_location, updated_at "
        "FROM network_connections WHERE " + " AND ".join(where) + f" ORDER BY {args.order} LIMIT ? OFFSET ?"
    )
    params.extend([args.limit, args.offset])
    return sql, params


def print_rows(rows: List[Dict], show_seniority: bool):
    cols = ["name", "title", "company", "industry", "location"]
    if show_seniority:
        cols.append("seniority")
    # Build data
    data: List[List[str]] = []
    for r in rows:
        s = derive_seniority(r["connection_title"]) if show_seniority else None
        row = [
            r.get("connection_name", "") or "",
            r.get("connection_title", "") or "",
            r.get("connection_company", "") or "",
            r.get("connection_industry", "") or "",
            r.get("connection_location", "") or "",
        ]
        if show_seniority:
            row.append(s)
        data.append(row)

    # Column widths
    widths = [
        max([len(cols[0])] + [len(d[0]) for d in data]) if data else len(cols[0]),
        max([len(cols[1])] + [len(d[1]) for d in data]) if data else len(cols[1]),
        max([len(cols[2])] + [len(d[2]) for d in data]) if data else len(cols[2]),
        max([len(cols[3])] + [len(d[3]) for d in data]) if data else len(cols[3]),
        max([len(cols[4])] + [len(d[4]) for d in data]) if data else len(cols[4]),
    ]
    if show_seniority:
        widths.append(max(len("seniority"), max((len(d[5]) for d in data), default=0)))

    # Header
    header = [
        cols[0].title().ljust(widths[0]),
        cols[1].title().ljust(widths[1]),
        cols[2].title().ljust(widths[2]),
        cols[3].title().ljust(widths[3]),
        cols[4].title().ljust(widths[4]),
    ]
    if show_seniority:
        header.append("Seniority".ljust(widths[5]))
    print(" | ".join(header))
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))

    # Rows
    for d in data:
        line = [
            d[0].ljust(widths[0]),
            d[1].ljust(widths[1]),
            d[2].ljust(widths[2]),
            d[3].ljust(widths[3]),
            d[4].ljust(widths[4]),
        ]
        if show_seniority:
            line.append(d[5].ljust(widths[5]))
        print(" | ".join(line))


def main() -> int:
    args = parse_args()

    # Fetch
    try:
        # Ensure schema exists/updated
        EnhancedDatabaseManager(db_path=args.db)
        conn = sqlite3.connect(args.db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Verify table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='network_connections'")
        if not cur.fetchone():
            print("❌ Table 'network_connections' not found. Run a data refresh first.")
            return 1

        sql, params = build_query(args)
        cur.execute(sql, params)
        rows = cur.fetchall()
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return 1
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Optional seniority filter derived from title
    dict_rows = [dict(r) for r in rows]
    if args.seniority:
        want = args.seniority.lower()
        dict_rows = [r for r in dict_rows if derive_seniority(r.get("connection_title", "")).lower() == want]

    # Output files
    if args.csv:
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            headers = ["name","title","company","industry","location","id","updated_at"]
            if args.show_seniority:
                headers.append("seniority")
            writer.writerow(headers)
            for r in dict_rows:
                row = [
                    r.get("connection_name",""),
                    r.get("connection_title",""),
                    r.get("connection_company",""),
                    r.get("connection_industry",""),
                    r.get("connection_location",""),
                    r.get("connection_id",""),
                    r.get("updated_at",""),
                ]
                if args.show_seniority:
                    row.append(derive_seniority(r.get("connection_title","")))
                writer.writerow(row)
        print(f"✅ CSV saved: {out}")

    if args.json:
        outj = Path(args.json)
        outj.parent.mkdir(parents=True, exist_ok=True)
        payload = []
        for r in dict_rows:
            item = {
                "id": r.get("connection_id"),
                "name": r.get("connection_name"),
                "title": r.get("connection_title"),
                "company": r.get("connection_company"),
                "industry": r.get("connection_industry"),
                "location": r.get("connection_location"),
                "updated_at": r.get("updated_at"),
            }
            if args.show_seniority:
                item["seniority"] = derive_seniority(item.get("title",""))
            payload.append(item)
        with open(outj, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON saved: {outj}")

    # Print table to console
    print_rows(dict_rows, args.show_seniority)
    print(f"\nTotal: {len(dict_rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
