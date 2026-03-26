#!/usr/bin/env python3
"""
Export LinkedIn Connections (names, headlines, location, industry)

Fetches your connections via the LinkedIn wrapper and exports to CSV/JSON.
Requires authentication (same as other real-data features). Supports manual
visible login for 2FA.

Examples:
  python scripts/export_connections.py --csv output/connections.csv --allow-auth --manual --timeout 180
  python scripts/export_connections.py --json output/connections.json --limit 1000 --allow-auth
"""

import os
import sys
import csv
import json
import time
import argparse
from pathlib import Path

# Project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.linkedin_authenticator import LinkedInAuthenticator
from core.linkedin_wrapper import LinkedInWrapper


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export LinkedIn connections")
    p.add_argument("--csv", type=str, default=None, help="Output CSV path (UTF-8 BOM)")
    p.add_argument("--json", type=str, default=None, help="Output JSON path (UTF-8)")
    p.add_argument("--limit", type=int, default=5000, help="Max connections to fetch (default: 5000)")
    p.add_argument("--page-size", type=int, default=100, help="Page size (<=100)")
    p.add_argument("--allow-auth", action="store_true", help="Allow Selenium authentication if needed")
    p.add_argument("--manual", action="store_true", help="Open visible browser for manual/2FA login")
    p.add_argument("--timeout", type=int, default=180, help="Auth timeout seconds (default: 180)")
    return p.parse_args()


def ensure_outputs(args: argparse.Namespace) -> None:
    if not args.csv and not args.json:
        # Default CSV path
        ts = time.strftime("%Y%m%d_%H%M%S")
        Path("output").mkdir(parents=True, exist_ok=True)
        args.csv = f"output/connections_{ts}.csv"


def main() -> int:
    args = parse_args()
    ensure_outputs(args)

    # Auth environment hints
    os.environ.setdefault("RUN_CONTEXT", "MANUAL")
    if args.allow_auth:
        os.environ["ALLOW_LI_AUTH_IN_SCHEDULED"] = "true"
        os.environ["LI_AUTH_TIMEOUT_SECONDS"] = str(args.timeout)
    if args.manual:
        os.environ["LI_FORCE_MANUAL_AUTH"] = "true"

    # Initialize authenticator (reads .env for credentials)
    authenticator = LinkedInAuthenticator(debug=False, force_manual_auth=args.manual)
    cookies = authenticator.get_cookies()
    if not cookies:
        print("❌ Could not obtain LinkedIn cookies. Ensure credentials/2FA and try --manual.")
        return 1

    # Build wrapper
    username = os.getenv('LINKEDIN_USERNAME', '')
    password = os.getenv('LINKEDIN_PASSWORD', '')
    wrapper = LinkedInWrapper(username=username, password=password, cookies=cookies, authenticator=authenticator)

    # Get profile id
    profile = wrapper.get_user_profile()
    if not profile:
        print("❌ Failed to load LinkedIn profile")
        return 1
    profile_id = profile.get('profile_id') or profile.get('entityUrn', '').split(':')[-1]
    if not profile_id:
        print("❌ Could not determine profile id")
        return 1

    # Fetch connections with pagination
    total = 0
    start = 0
    page_size = min(max(1, args.page_size), 100)
    all_conns = []

    while total < args.limit:
        batch = wrapper.get_profile_connections(profile_id, start=start, count=page_size)
        if not batch:
            break
        all_conns.extend(batch)
        total += len(batch)
        start += len(batch)
        if len(batch) < page_size:
            break

    # Trim to limit
    if len(all_conns) > args.limit:
        all_conns = all_conns[:args.limit]

    # Write outputs
    if args.csv:
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "headline", "public_id", "location", "industry", "urn_id", "picture_url"])
            for c in all_conns:
                writer.writerow([
                    c.get('name', ''),
                    c.get('headline', ''),
                    c.get('public_id', ''),
                    c.get('location', ''),
                    c.get('industry', ''),
                    c.get('urn_id', ''),
                    c.get('picture_url', ''),
                ])
        print(f"✅ CSV saved: {out}")

    if args.json:
        outj = Path(args.json)
        outj.parent.mkdir(parents=True, exist_ok=True)
        with open(outj, 'w', encoding='utf-8') as f:
            json.dump(all_conns, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON saved: {outj}")

    print(f"📦 Exported {len(all_conns)} connections")
    return 0


if __name__ == "__main__":
    sys.exit(main())

