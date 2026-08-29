"""
facebook_scraper.py
====================
Facebook profile scraper using two complementary strategies:

Strategy 1 (Primary — no login needed):
  Parse structured JSON data embedded by Facebook in <script> tags.
  Facebook injects rich profile data into window.__initialData__, __bbox,
  application/json script tags, and application/ld+json on public pages.
  This is more durable than CSS selectors since it doesn't depend on
  Facebook's frequently-changing layout classes.

Strategy 2 (Fallback — session injection):
  If the page redirects to login (profile is private or restricted), use
  the saved Playwright storageState to authenticate and retry.
"""

import re
import json
import logging
from typing import Dict, Any, Optional

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

from backend.session_manager import get_session_path

logger = logging.getLogger("FacebookScraper")

_BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def _parse_count(text: str) -> int:
    """Parse '1.2K', '3M', '450,000' → int."""
    if not text:
        return 0
    text = text.replace(",", "").strip().upper()
    try:
        if "K" in text:
            return int(float(text.replace("K", "")) * 1_000)
        if "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        if "B" in text:
            return int(float(text.replace("B", "")) * 1_000_000_000)
        return int(float(text))
    except (ValueError, TypeError):
        return 0


def _deep_search(obj: Any, target_keys: list[str]) -> Dict[str, Any]:
    """
    Recursively searches a nested dict/list for any of the target keys.
    Returns a flat dict of found key→value pairs.
    """
    found: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in target_keys and v is not None:
                found[k] = v
            found.update(_deep_search(v, target_keys))
    elif isinstance(obj, list):
        for item in obj:
            found.update(_deep_search(item, target_keys))
    return found


def _extract_from_script_tags(html: str) -> Dict[str, Any]:
    """
    Extracts profile data by parsing Facebook's embedded JSON script tags.
    Facebook injects structured data in multiple <script> blocks.
    """
    extracted: Dict[str, Any] = {}

    # --- Strategy A: application/ld+json (structured SEO data) ---
    ld_json_blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    )
    for block in ld_json_blocks:
        try:
            data = json.loads(block.strip())
            if isinstance(data, list):
                data = data[0] if data else {}
            # Common ld+json fields
            if data.get("name"):
                extracted["display_name"] = data["name"]
            if data.get("description"):
                extracted["bio"] = data["description"]
            if data.get("url"):
                extracted["external_url"] = data["url"]
            img = data.get("image")
            if isinstance(img, dict) and img.get("url"):
                extracted["avatar_url"] = img["url"]
            elif isinstance(img, str):
                extracted["avatar_url"] = img
            # interactionStatistic can hold follower count
            for stat in data.get("interactionStatistic", []):
                itype = stat.get("interactionType", "")
                if "Follow" in itype or "Like" in itype:
                    val = stat.get("userInteractionCount", 0)
                    try:
                        extracted["followers"] = int(val)
                    except (ValueError, TypeError):
                        pass
        except (json.JSONDecodeError, KeyError):
            continue

    # --- Strategy B: application/json inline React data ---
    json_script_blocks = re.findall(
        r'<script[^>]+type=["\']application/json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    )
    for block in json_script_blocks:
        try:
            data = json.loads(block.strip())
            target_keys = [
                "name", "biography", "follower_count", "fan_count",
                "friend_count", "profile_pic_url", "profile_picture",
                "website", "about", "description", "username",
                "category_name", "page_likes",
            ]
            found = _deep_search(data, target_keys)
            if found.get("name") and not extracted.get("display_name"):
                extracted["display_name"] = found["name"]
            if found.get("biography") and not extracted.get("bio"):
                extracted["bio"] = found["biography"]
            if found.get("about") and not extracted.get("bio"):
                extracted["bio"] = found["about"]
            if found.get("description") and not extracted.get("bio"):
                extracted["bio"] = found["description"]
            for fc_key in ("follower_count", "fan_count", "page_likes"):
                if found.get(fc_key) and not extracted.get("followers"):
                    try:
                        extracted["followers"] = int(found[fc_key])
                    except (ValueError, TypeError):
                        pass
            if found.get("friend_count") and not extracted.get("following"):
                try:
                    extracted["following"] = int(found["friend_count"])
                except (ValueError, TypeError):
                    pass
            for pic_key in ("profile_pic_url", "profile_picture"):
                if found.get(pic_key) and not extracted.get("avatar_url"):
                    extracted["avatar_url"] = found[pic_key]
            if found.get("website") and not extracted.get("external_url"):
                extracted["external_url"] = found["website"]
        except (json.JSONDecodeError, KeyError):
            continue

    # --- Strategy C: og: meta tags (always present, minimal data) ---
    og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html)
    og_desc = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)', html)
    og_image = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)

    if og_title and not extracted.get("display_name"):
        extracted["display_name"] = og_title.group(1).strip()
    if og_desc and not extracted.get("bio"):
        raw_desc = og_desc.group(1).strip()
        extracted["bio"] = raw_desc
        # Try to parse follower count from og:description text
        # e.g. "12,345 likes · 8,901 followers"
        fc_match = re.search(r"([\d,\.]+)\s*(?:followers|likes|fans)", raw_desc, re.IGNORECASE)
        if fc_match and not extracted.get("followers"):
            extracted["followers"] = _parse_count(fc_match.group(1))
    if og_image and not extracted.get("avatar_url"):
        extracted["avatar_url"] = og_image.group(1).strip()

    return extracted


def _is_login_wall(html: str) -> bool:
    """Detects if Facebook served a login page instead of the profile."""
    signals = [
        "id=\"loginbutton\"",
        "name=\"login\"",
        "Log in to Facebook",
        "/login/",
        "LoginController",
    ]
    return any(s.lower() in html.lower() for s in signals)


async def _fetch_page_html(url: str, storage_state_path: Optional[str]) -> Optional[str]:
    """Launches Playwright and returns full page HTML."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=_BROWSER_ARGS)
            ctx_kwargs: Dict[str, Any] = {
                "user_agent": _USER_AGENT,
                "viewport": {"width": 1280, "height": 900},
                "locale": "en-US",
            }
            if storage_state_path:
                ctx_kwargs["storage_state"] = storage_state_path
            context = await browser.new_context(**ctx_kwargs)
            page = await context.new_page()
            page.set_default_timeout(12000)
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2500)
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        logger.warning(f"Playwright fetch failed for {url}: {e}")
        return None


async def scrape_facebook(url: str, handle: str) -> Dict[str, Any]:
    """
    Main Facebook scraper entry point.
    Returns a standardised profile dict.
    """
    base: Dict[str, Any] = {
        "username": handle,
        "platform": "meta",
        "display_name": None,
        "bio": "",
        "external_url": None,
        "avatar_url": None,
        "followers": 0,
        "following": 0,
        "post_count": 0,
        "has_profile_pic": 0,
        "bio_length": 0,
        "posts": [],
        "scrape_success": False,
        "scraper_engine": "Facebook Script-JSON Extractor",
    }

    session_path = get_session_path("facebook")

    # --- Attempt 1: No session (works for most public pages) ---
    html = await _fetch_page_html(url, None)

    if html and _is_login_wall(html) and session_path:
        logger.info("Facebook login wall detected — retrying with saved session...")
        html = await _fetch_page_html(url, session_path)

    if not html:
        logger.warning(f"Could not fetch Facebook page for @{handle}")
        return base

    if _is_login_wall(html):
        logger.warning(f"Facebook login wall persists for @{handle} — no session available or session expired")
        base["scraper_engine"] = "Facebook (Login Wall — connect session in Settings)"
        return base

    # --- Extract from script tags ---
    extracted = _extract_from_script_tags(html)

    if extracted.get("display_name"):
        base["display_name"] = extracted["display_name"]
        base["scrape_success"] = True
    if extracted.get("bio"):
        base["bio"] = extracted["bio"]
        base["bio_length"] = len(extracted["bio"])
        base["scrape_success"] = True
    if extracted.get("followers"):
        base["followers"] = extracted["followers"]
        base["scrape_success"] = True
    if extracted.get("following"):
        base["following"] = extracted["following"]
    if extracted.get("avatar_url"):
        base["avatar_url"] = extracted["avatar_url"]
        base["has_profile_pic"] = 1
    if extracted.get("external_url"):
        base["external_url"] = extracted["external_url"]

    logger.info(
        f"Facebook scrape complete for @{handle}: "
        f"success={base['scrape_success']}, followers={base['followers']}, "
        f"display_name={base['display_name']}"
    )
    return base
