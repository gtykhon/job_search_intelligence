"""
Proxy Manager — Rotating proxy support for anti-bot bypass.

Supports multiple proxy backends:
  1. Direct residential proxy (BrightData, Oxylabs, etc.)
  2. ScrapFly API (anti-bot as a service)
  3. Free proxy list (unreliable, fallback only)
  4. No proxy (direct connection)

Configuration via .env:
  PROXY_TYPE=residential|scrapfly|free|none
  PROXY_URL=http://user:pass@proxy.example.com:port
  SCRAPFLY_API_KEY=your_key_here

For Wellfound (DataDome), residential proxies are recommended.
ScrapFly with asp=True is the most reliable but costs ~$0.005/request.
"""

import os
import re
import json
import random
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Load .env
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

# ── Configuration ────────────────────────────────────────────────────────────

PROXY_TYPE = os.getenv("PROXY_TYPE", "none").lower()  # residential, scrapfly, free, none
PROXY_URL = os.getenv("PROXY_URL", "")  # http://user:pass@host:port
SCRAPFLY_API_KEY = os.getenv("SCRAPFLY_API_KEY", "")

# Free proxy list — rotated, unreliable
_FREE_PROXIES: List[str] = []
_FREE_PROXY_IDX = 0


# ── Proxy Fetch Functions ────────────────────────────────────────────────────

def _get_http_client():
    """Get the best available HTTP client."""
    try:
        from curl_cffi import requests as client
        return client, True
    except ImportError:
        import requests as client  # type: ignore[no-redef]
        return client, False


def fetch_with_proxy(
    url: str,
    timeout: int = 20,
    impersonate: str = "chrome124",
    headers: Optional[Dict[str, str]] = None,
    method: str = "GET",
) -> Optional[str]:
    """
    Fetch a URL using the configured proxy backend.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.
        impersonate: TLS fingerprint to impersonate (curl_cffi only).
        headers: Optional extra headers.
        method: HTTP method.

    Returns:
        Response text or None on failure.
    """
    if PROXY_TYPE == "scrapfly" and SCRAPFLY_API_KEY:
        return _fetch_scrapfly(url, timeout, headers)
    elif PROXY_TYPE == "residential" and PROXY_URL:
        return _fetch_residential(url, timeout, impersonate, headers)
    elif PROXY_TYPE == "free":
        return _fetch_free_proxy(url, timeout, impersonate, headers)
    else:
        return _fetch_direct(url, timeout, impersonate, headers)


def _fetch_scrapfly(
    url: str,
    timeout: int = 20,
    headers: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Fetch via ScrapFly anti-bot API."""
    client, _ = _get_http_client()

    api_url = "https://api.scrapfly.io/scrape"
    params = {
        "key": SCRAPFLY_API_KEY,
        "url": url,
        "asp": "true",  # Anti-Scraping Protection bypass
        "render_js": "false",  # Don't need JS rendering for __NEXT_DATA__
        "country": "us",
    }
    if headers:
        params["headers"] = json.dumps(headers)

    try:
        resp = client.get(api_url, params=params, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("result", {})
            content = result.get("content", "")
            status = result.get("status_code", 0)
            if status == 200 and content:
                logger.info(f"ScrapFly: fetched {url} ({len(content)} chars)")
                return content
            else:
                logger.warning(f"ScrapFly: upstream returned {status} for {url}")
                return None
        else:
            logger.warning(f"ScrapFly API returned {resp.status_code}")
            return None
    except Exception as e:
        logger.warning(f"ScrapFly fetch failed: {e}")
        return None


def _fetch_residential(
    url: str,
    timeout: int = 20,
    impersonate: str = "chrome124",
    headers: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Fetch via residential proxy with TLS impersonation."""
    client, has_cffi = _get_http_client()

    proxies = {"http": PROXY_URL, "https": PROXY_URL}

    default_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    if headers:
        default_headers.update(headers)

    try:
        kwargs: Dict[str, Any] = {
            "timeout": timeout,
            "headers": default_headers,
            "proxies": proxies,
        }
        if has_cffi:
            kwargs["impersonate"] = impersonate
            # curl_cffi uses 'proxy' not 'proxies'
            kwargs.pop("proxies")
            kwargs["proxy"] = PROXY_URL

        resp = client.get(url, **kwargs)

        if resp.status_code == 200:
            logger.info(f"Residential proxy: fetched {url} ({len(resp.text)} chars)")
            return resp.text
        else:
            logger.warning(f"Residential proxy: {resp.status_code} for {url}")
            return None
    except Exception as e:
        logger.warning(f"Residential proxy fetch failed: {e}")
        return None


def _fetch_free_proxy(
    url: str,
    timeout: int = 15,
    impersonate: str = "chrome124",
    headers: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
) -> Optional[str]:
    """Fetch via rotating free proxy list (unreliable)."""
    global _FREE_PROXIES, _FREE_PROXY_IDX

    # Lazy-load free proxy list
    if not _FREE_PROXIES:
        _FREE_PROXIES = _fetch_free_proxy_list()
        if not _FREE_PROXIES:
            logger.warning("No free proxies available, falling back to direct")
            return _fetch_direct(url, timeout, impersonate, headers)

    client, has_cffi = _get_http_client()

    default_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    if headers:
        default_headers.update(headers)

    for attempt in range(max_retries):
        proxy = _FREE_PROXIES[_FREE_PROXY_IDX % len(_FREE_PROXIES)]
        _FREE_PROXY_IDX += 1

        try:
            kwargs: Dict[str, Any] = {
                "timeout": timeout,
                "headers": default_headers,
            }
            if has_cffi:
                kwargs["impersonate"] = impersonate
                kwargs["proxy"] = proxy
            else:
                kwargs["proxies"] = {"http": proxy, "https": proxy}

            resp = client.get(url, **kwargs)
            if resp.status_code == 200:
                logger.info(f"Free proxy: fetched {url} via {proxy[:30]}...")
                return resp.text
        except Exception:
            continue

    logger.warning(f"All free proxy attempts failed for {url}")
    return None


def _fetch_direct(
    url: str,
    timeout: int = 20,
    impersonate: str = "chrome124",
    headers: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Direct fetch with TLS impersonation (no proxy)."""
    client, has_cffi = _get_http_client()

    default_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    if headers:
        default_headers.update(headers)

    try:
        kwargs: Dict[str, Any] = {"timeout": timeout, "headers": default_headers}
        if has_cffi:
            kwargs["impersonate"] = impersonate

        resp = client.get(url, **kwargs)
        if resp.status_code == 200:
            return resp.text
        else:
            logger.debug(f"Direct fetch: {resp.status_code} for {url}")
            return None
    except Exception as e:
        logger.warning(f"Direct fetch failed: {e}")
        return None


# ── Free Proxy Discovery ────────────────────────────────────────────────────

def _fetch_free_proxy_list() -> List[str]:
    """Fetch a list of free HTTPS proxies from public APIs."""
    proxies = []
    client, _ = _get_http_client()

    # Try free proxy API
    try:
        resp = client.get(
            "https://api.proxyscrape.com/v4/free-proxy-list/get"
            "?request=display_proxies&proxy_format=protocolipport"
            "&protocol=http&timeout=5000&country=us&anonymity=elite",
            timeout=10,
        )
        if resp.status_code == 200:
            for line in resp.text.strip().split("\n"):
                line = line.strip()
                if line and re.match(r'https?://\d+\.\d+\.\d+\.\d+:\d+', line):
                    proxies.append(line)
    except Exception:
        pass

    # Shuffle for rotation
    random.shuffle(proxies)
    logger.info(f"Loaded {len(proxies)} free proxies")
    return proxies[:50]  # Cap at 50


# ── Public Helpers ───────────────────────────────────────────────────────────

def get_proxy_status() -> Dict[str, Any]:
    """Return current proxy configuration status."""
    return {
        "proxy_type": PROXY_TYPE,
        "proxy_configured": bool(PROXY_URL) if PROXY_TYPE == "residential" else bool(SCRAPFLY_API_KEY) if PROXY_TYPE == "scrapfly" else PROXY_TYPE == "free",
        "proxy_url_masked": PROXY_URL[:20] + "..." if PROXY_URL else None,
        "scrapfly_configured": bool(SCRAPFLY_API_KEY),
        "free_proxies_loaded": len(_FREE_PROXIES),
    }


def is_proxy_available() -> bool:
    """Check if any proxy backend is configured."""
    if PROXY_TYPE == "residential" and PROXY_URL:
        return True
    if PROXY_TYPE == "scrapfly" and SCRAPFLY_API_KEY:
        return True
    if PROXY_TYPE == "free":
        return True
    return False
