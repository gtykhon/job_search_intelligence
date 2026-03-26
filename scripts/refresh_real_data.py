#!/usr/bin/env python3
"""
Manual Real LinkedIn Data Refresh CLI

Runs the real data collector to refresh cached LinkedIn network metrics.
Useful when scheduled runs are non-interactive and skip authentication.

Usage examples:
  python scripts/refresh_real_data.py --force --allow-auth --timeout 120
  python scripts/refresh_real_data.py --no-telegram
"""

import os
import sys
import asyncio
import argparse
import time
from pathlib import Path
from datetime import datetime

# Ensure project import path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.intelligence.real_linkedin_data_collector import RealLinkedInDataCollector
from src.config import AppConfig
from src.integrations.notifications import NotificationManager
from core.linkedin_authenticator import LinkedInAuthenticator
from core.linkedin_wrapper import LinkedInWrapper
from src.database.enhanced_database_manager import EnhancedDatabaseManager
from typing import List, Dict
from src.tracking.follower_change_tracker import LinkedInFollowerTracker


async def refresh_real_data(force: bool, allow_auth: bool, timeout: int, send_telegram: bool, manual: bool, page_delay_opt: float | None) -> int:
    # Mark manual run context
    os.environ.setdefault("RUN_CONTEXT", "MANUAL")
    if allow_auth:
        os.environ["ALLOW_LI_AUTH_IN_SCHEDULED"] = "true"
    if timeout:
        os.environ["LI_AUTH_TIMEOUT_SECONDS"] = str(timeout)
    if manual:
        os.environ["LI_FORCE_MANUAL_AUTH"] = "true"

    # Load config
    config = AppConfig()

    # Initialize collector
    collector = RealLinkedInDataCollector()
    if force:
        collector.set_force_refresh(True)

    # Try to authenticate (best-effort)
    authed = await collector.authenticate()

    # Collect
    data = await collector.collect_real_network_intelligence()

    # Prepare summary
    total = data.get('total_connections') or data.get('data', {}).get('total_connections') or 0
    source = data.get('data_source', 'unknown')
    when = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Compute effective authentication result based on data source
    ds = (data.get('data_source') or data.get('data', {}).get('data_source') or '').lower()
    authed_effective = bool(authed or ds in ("linkedin_wrapper_connections", "linkedin_api_real"))

    print("\n✅ Real data refresh completed")
    print(f"   Time: {when}")
    print(f"   Authenticated: {authed_effective}")
    print(f"   Data source: {source}")
    print(f"   Total connections: {total}")

    # Also update the network_connections table for convenience
    try:
        # Use existing cookies or login again (cookies should be cached already)
        authenticator = LinkedInAuthenticator(debug=False, force_manual_auth=manual)
        cookies = authenticator.get_cookies()
        if cookies:
            username = os.getenv('LINKEDIN_USERNAME', '')
            password = os.getenv('LINKEDIN_PASSWORD', '')
            wrapper = LinkedInWrapper(username=username, password=password, cookies=cookies, authenticator=authenticator)
            profile = wrapper.get_user_profile()
            pid = profile.get('profile_id') or profile.get('entityUrn', '').split(':')[-1]
            cap = int(os.getenv('CONNECTIONS_EXPORT_LIMIT', '2000'))

            # Resolve page delay (in seconds)
            pd = page_delay_opt if page_delay_opt is not None else float(os.getenv('CONNECTIONS_PAGE_DELAY_SECONDS', '0.8'))

            def fetch_via_graphql() -> List[Dict]:
                page_size = 100
                fetched: List[Dict] = []
                start = 0
                while start < cap:
                    batch = wrapper.get_profile_connections(pid, start=start, count=page_size)
                    if not batch:
                        break
                    fetched.extend(batch)
                    start += len(batch)
                    if len(batch) < page_size:
                        break
                    # Gentle delay between pages to reduce throttling risk
                    time.sleep(pd)
                return fetched

            def fetch_via_voyager() -> List[Dict]:
                sess = wrapper.api.client.session
                # Build voyager headers
                js = sess.cookies.get('JSESSIONID', '')
                csrf = js.strip('"') if isinstance(js, str) else ''
                headers = {
                    'accept': 'application/vnd.linkedin.normalized+json+2.1',
                    'csrf-token': csrf,
                    'x-restli-protocol-version': '2.0.0',
                    'user-agent': 'Mozilla/5.0',
                    'accept-language': 'en-US,en;q=0.9',
                    'referer': 'https://www.linkedin.com/',
                    'origin': 'https://www.linkedin.com'
                }
                fetched: List[Dict] = []
                start = 0
                page_size = 40
                while start < cap:
                    resp = sess.get(
                        'https://www.linkedin.com/voyager/api/relationships/connections',
                        params={'start': start, 'count': page_size},
                        headers=headers,
                        timeout=30
                    )
                    if resp.status_code != 200:
                        break
                    payload = resp.json()
                    mini_profiles = [
                        item for item in payload.get('included', [])
                        if item.get('$type') == 'com.linkedin.voyager.identity.shared.MiniProfile'
                    ]
                    new_items = 0
                    for item in mini_profiles:
                        fetched.append({
                            'urn_id': item.get('entityUrn'),
                            'name': f"{item.get('firstName', '')} {item.get('lastName', '')}".strip(),
                            'headline': item.get('occupation', '') or '',
                            'public_id': item.get('publicIdentifier', ''),
                            'location': '',
                            'industry': '',
                        })
                        new_items += 1
                    # Advance by requested page size; continue until no new items returned
                    start += page_size
                    if new_items == 0:
                        break
                    # Gentle delay between pages
                    time.sleep(pd)
                return fetched

            # Try GraphQL first; if forbidden, fall back to voyager endpoint
            fetched: List[Dict]
            try:
                fetched = fetch_via_graphql()
                if not fetched:
                    raise RuntimeError('Empty response from GraphQL')
            except Exception:
                fetched = fetch_via_voyager()
            # Upsert into DB
            db = EnhancedDatabaseManager()
            upserted = db.upsert_network_connections(fetched)
            print(f"   DB update: fetched {len(fetched)}; upserted ~{upserted} connections into network_connections")

            # Followers snapshot and change analysis (best effort)
            try:
                def fetch_followers_voyager() -> List[Dict]:
                    sess = wrapper.api.client.session
                    js = sess.cookies.get('JSESSIONID', '')
                    csrf = js.strip('"') if isinstance(js, str) else ''
                    headers = {
                        'accept': 'application/vnd.linkedin.normalized+json+2.1',
                        'csrf-token': csrf,
                        'x-restli-protocol-version': '2.0.0',
                        'user-agent': 'Mozilla/5.0',
                        'accept-language': 'en-US,en;q=0.9',
                        'referer': 'https://www.linkedin.com/',
                        'origin': 'https://www.linkedin.com'
                    }
                    results: List[Dict] = []
                    start = 0
                    page_size = 50
                    # Try two likely endpoints
                    endpoints = [
                        'https://www.linkedin.com/voyager/api/relationships/followers',
                        'https://www.linkedin.com/voyager/api/following/followers'
                    ]
                    for ep in endpoints:
                        start = 0
                        while start < cap:
                            resp = sess.get(ep, params={'start': start, 'count': page_size}, headers=headers, timeout=30)
                            if resp.status_code != 200:
                                break
                            payload = resp.json()
                            items = []
                            if 'included' in payload:
                                items = [it for it in payload['included'] if isinstance(it, dict) and 'publicIdentifier' in it]
                            elif 'elements' in payload:
                                items = payload['elements']
                            new_items = 0
                            for it in items:
                                pid = it.get('publicIdentifier', '') or it.get('publicId', '')
                                first = it.get('firstName', '')
                                last = it.get('lastName', '')
                                headline = it.get('headline', '') or it.get('occupation', '')
                                urn = it.get('entityUrn') or it.get('urn') or ''
                                if not first and not last and 'miniProfile' in it:
                                    mp = it.get('miniProfile') or {}
                                    first = mp.get('firstName','')
                                    last = mp.get('lastName','')
                                    urn = urn or mp.get('entityUrn','')
                                    pid = pid or mp.get('publicIdentifier','')
                                    headline = headline or mp.get('occupation','')
                                name = f"{first} {last}".strip()
                                results.append({
                                    'urn_id': urn,
                                    'name': name,
                                    'occupation': headline,
                                    'company': '',
                                    'location': '',
                                    'relationship': 'follower',
                                    'profile_url': f"https://www.linkedin.com/in/{pid}" if pid else ''
                                })
                                new_items += 1
                            start += page_size
                            if new_items == 0:
                                break
                            time.sleep(pd)
                        if results:
                            break
                    return results

                followers = fetch_followers_voyager()
                if followers:
                    from datetime import datetime as _dt
                    today = _dt.now().strftime('%Y-%m-%d')
                    tracker = LinkedInFollowerTracker(db_path=db.db_path)
                    tracker.save_follower_snapshot(followers, snapshot_date=today, session_id=f"refresh_{today}")
                    analysis = tracker.analyze_follower_changes(followers, analysis_date=today)
                    print(f"   Followers snapshot: {len(followers)} | New: {len(analysis.new_followers)} | Lost: {len(analysis.unfollowers)}")
                else:
                    print("   Followers snapshot skipped (endpoint blocked or no data)")
            except Exception as e:
                print(f"   Followers snapshot warning: {e}")
        else:
            print("   DB update skipped (no cookies available)")
    except Exception as e:
        print(f"   DB update warning: {e}")

    # Optional Telegram notification
    if send_telegram and config.notifications.telegram_enabled:
        try:
            nm = NotificationManager(config)
            await nm.initialize()
            await nm.send_notification(
                title="🔄 LinkedIn Data Refresh",
                message=(
                    f"Real data refresh completed at {when}.\n"
                    f"Source: {source} | Connections: {total} | Auth: {authed_effective}"
                ),
                priority="normal",
                notification_type="data_refresh"
            )
        except Exception:
            # Non-fatal if Telegram fails
            pass

    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Manual LinkedIn real data refresh")
    p.add_argument("--force", action="store_true", help="Force bypass of cache and fetch fresh data")
    p.add_argument("--allow-auth", action="store_true", help="Allow Selenium authentication during this run")
    p.add_argument("--timeout", type=int, default=120, help="Auth timeout seconds (default: 120)")
    p.add_argument("--no-telegram", action="store_true", help="Do not send Telegram notification")
    p.add_argument("--manual", action="store_true", help="Open a visible browser for manual login/2FA")
    p.add_argument("--page-delay", type=float, default=None, help="Delay between pages (seconds), default 0.8")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(
        refresh_real_data(
            force=args.force,
            allow_auth=args.allow_auth,
            timeout=args.timeout,
            send_telegram=not args.no_telegram,
            manual=args.manual,
            page_delay_opt=args.page_delay,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
