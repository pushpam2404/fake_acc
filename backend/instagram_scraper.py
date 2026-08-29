"""
instagram_scraper.py
=====================
Instagram profile scraper with two complementary strategies:

Strategy 1 — Playwright with storageState session (Primary):
  Loads a saved logged-in browser session, navigates to the profile,
  and extracts: display name, bio, followers, following, post count,
  avatar, external URL, and the post grid (images + captions).
  This works on any public profile when a valid session is available.

Strategy 2 — Instaloader with sessionid cookie (Fallback):
  If Playwright hits a CAPTCHA or timeout, uses Instaloader authenticated
  with the sessionid cookie extracted from the same storageState JSON.
  Returns structured profile metadata (bio, follower counts, post count).
  No DOM scraping needed — Instaloader uses Instagram's private API.

No session available:
  Returns scrape_success=False so main.py falls back to OSINT heuristics.
"""

import re
import logging
from typing import Dict, Any, Optional, List

try:
    import instaloader
except ImportError:
    instaloader = None

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

from backend.session_manager import get_session_path, extract_instagram_session_id

logger = logging.getLogger("InstagramScraper")

_BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)


def _parse_count(text: str) -> int:
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


def _is_login_wall(html: str) -> bool:
    signals = [
        '"loginPage"', "Log in to Instagram",
        "You need to log in", "loginForm",
    ]
    return any(s.lower() in html.lower() for s in signals)


def _decode_instagram_redirect(url: str) -> str:
    """
    Instagram wraps external URLs in l.instagram.com redirects.
    Decodes the real destination URL from the 'u' query parameter.
    """
    match = re.search(r"[?&]u=([^&]+)", url)
    if match:
        from urllib.parse import unquote
        return unquote(match.group(1))
    return url


async def _playwright_scrape(handle: str, session_path: Optional[str]) -> Dict[str, Any]:
    """Playwright-based scrape of an Instagram profile."""
    result: Dict[str, Any] = {
        "scrape_success": False,
        "followers": 0,
        "following": 0,
        "post_count": 0,
        "bio": "",
        "bio_length": 0,
        "display_name": None,
        "avatar_url": None,
        "external_url": None,
        "has_profile_pic": 0,
        "posts": [],
    }

    target_url = f"https://www.instagram.com/{handle}/"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=_BROWSER_ARGS)
            ctx_kwargs: Dict[str, Any] = {
                "user_agent": _USER_AGENT,
                "viewport": {"width": 390, "height": 844},   # Mobile viewport — more stable
                "locale": "en-US",
                "is_mobile": True,
            }
            if session_path:
                ctx_kwargs["storage_state"] = session_path
                logger.info(f"Instagram Playwright: using saved session for @{handle}")
            else:
                logger.info(f"Instagram Playwright: no session for @{handle}")

            context = await browser.new_context(**ctx_kwargs)
            page = await context.new_page()
            page.set_default_timeout(12000)

            await page.goto(target_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2500)

            # Dismiss cookie/login popups
            try:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(300)
            except Exception:
                pass

            html = await page.content()
            if _is_login_wall(html) and not session_path:
                logger.warning(f"Instagram login wall for @{handle} — no session available")
                await browser.close()
                return result

            # ----------------------------------------------------------------
            # Parse og: meta and meta description (most reliable across layouts)
            # ----------------------------------------------------------------
            try:
                og_title = await page.locator('meta[property="og:title"]').first.get_attribute("content")
                if og_title:
                    # og:title format: "Username (@handle) • Instagram"
                    name_match = re.match(r"^(.+?)\s*\(@", og_title)
                    if name_match:
                        result["display_name"] = name_match.group(1).strip()
                    else:
                        result["display_name"] = og_title.replace("• Instagram", "").strip()
            except Exception:
                pass

            try:
                meta_desc = await page.locator(
                    'meta[name="description"], meta[property="og:description"]'
                ).first.get_attribute("content")
                if meta_desc:
                    # "N Followers, N Following, N Posts — See Instagram photos..."
                    m = re.search(
                        r"([\d,\.KkMm]+)\s*Followers?,\s*([\d,\.KkMm]+)\s*Following,\s*([\d,\.KkMm]+)\s*Posts?",
                        meta_desc,
                    )
                    if m:
                        result["followers"] = _parse_count(m.group(1))
                        result["following"] = _parse_count(m.group(2))
                        result["post_count"] = _parse_count(m.group(3))
                        result["scrape_success"] = True
                    # Also extract bio text (everything after " — ")
                    if " — " in meta_desc:
                        bio_part = meta_desc.split(" — ", 1)[1]
                        if len(bio_part) > 5:
                            result["bio"] = bio_part
                            result["bio_length"] = len(bio_part)
                            result["scrape_success"] = True
            except Exception:
                pass

            # ----------------------------------------------------------------
            # DOM bio (more complete than meta description)
            # ----------------------------------------------------------------
            for bio_sel in [
                'header section div._aa_c',
                'header div[dir="auto"]',
                'section > div > span[dir="auto"]',
                'header section span._ap3a',
            ]:
                try:
                    el = page.locator(bio_sel).first
                    if await el.count() > 0:
                        text = await el.inner_text()
                        if len(text.strip()) > 5:
                            result["bio"] = text.strip()
                            result["bio_length"] = len(text.strip())
                            result["scrape_success"] = True
                            break
                except Exception:
                    continue

            # ----------------------------------------------------------------
            # External URL
            # ----------------------------------------------------------------
            for link_sel in [
                'header a[href*="l.instagram.com"]',
                'header a[target="_blank"]',
                'header a[href*="t.me"]',
            ]:
                try:
                    el = page.locator(link_sel).first
                    if await el.count() > 0:
                        href = await el.get_attribute("href") or ""
                        result["external_url"] = _decode_instagram_redirect(href)
                        break
                except Exception:
                    continue

            # ----------------------------------------------------------------
            # Avatar
            # ----------------------------------------------------------------
            for av_sel in [
                'img[alt*="profile picture"]',
                'img[alt*="avatar"]',
                'header img',
            ]:
                try:
                    el = page.locator(av_sel).first
                    if await el.count() > 0:
                        src = await el.get_attribute("src")
                        if src:
                            result["avatar_url"] = src
                            result["has_profile_pic"] = 1
                            break
                except Exception:
                    continue

            # ----------------------------------------------------------------
            # Post grid
            # ----------------------------------------------------------------
            try:
                img_locators = page.locator(
                    'a[href^="/p/"] img, a[href^="/reel/"] img, div._aagv img, article img'
                )
                count = await img_locators.count()
                posts: List[Dict[str, Any]] = []
                for i in range(min(count, 6)):
                    img = img_locators.nth(i)
                    src = await img.get_attribute("src")
                    alt = await img.get_attribute("alt") or ""
                    if src and "profile" not in alt.lower():
                        posts.append({
                            "id": f"post_{i+1}",
                            "thumbnail_url": src,
                            "caption": alt if len(alt) > 5 else f"Post from @{handle}",
                            "likes": 0,
                            "comments": 0,
                            "timestamp": "Recent",
                        })
                if posts:
                    result["posts"] = posts
            except Exception:
                pass

            await browser.close()

    except Exception as e:
        logger.warning(f"Instagram Playwright scrape failed for @{handle}: {e}")

    return result


def _instaloader_scrape(handle: str, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Fallback: use Instaloader authenticated with the saved sessionid cookie.
    Returns structured metadata or None on failure.
    """
    logger.info(f"Instagram Instaloader fallback for @{handle}")
    L = instaloader.Instaloader(
        compress_json=False,
        download_geotags=False,
        download_comments=False,
        save_metadata_json=False,
        quiet=True,
    )
    try:
        # Load session from the cookie value (no password needed)
        L.context._session.cookies.update({"sessionid": session_id})
        L.context._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram"
            )
        })
        profile = instaloader.Profile.from_username(L.context, handle)
        has_pic = 1
        if not profile.profile_pic_url or "default" in profile.profile_pic_url:
            has_pic = 0
        return {
            "followers": profile.followers,
            "following": profile.followees,
            "post_count": profile.mediacount,
            "bio": profile.biography or "",
            "bio_length": len(profile.biography) if profile.biography else 0,
            "has_profile_pic": has_pic,
            "avatar_url": profile.profile_pic_url,
            "display_name": profile.full_name,
            "scrape_success": True,
        }
    except Exception as e:
        logger.warning(f"Instaloader fallback failed for @{handle}: {e}")
        return None


async def scrape_instagram(url: str, handle: str) -> Dict[str, Any]:
    """
    Main Instagram scraper entry point.
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
        "scraper_engine": "Instagram Playwright (session-injected)",
    }

    session_path = get_session_path("instagram")
    session_id = extract_instagram_session_id("instagram")

    # --- Strategy 1: Playwright ---
    pw_result = await _playwright_scrape(handle, session_path)
    base.update({k: v for k, v in pw_result.items() if v not in (None, "", 0, [], False)})
    if pw_result.get("scrape_success"):
        base["scrape_success"] = True

    # --- Strategy 2: Instaloader fallback if Playwright didn't get counts ---
    if not base["scrape_success"] and session_id:
        il_result = _instaloader_scrape(handle, session_id)
        if il_result:
            base.update({k: v for k, v in il_result.items() if v not in (None, "", 0, [], False)})
            base["scrape_success"] = il_result.get("scrape_success", False)
            base["scraper_engine"] = "Instagram Instaloader (session-cookie fallback)"

    if not base["scrape_success"]:
        if not session_path:
            base["scraper_engine"] = "Instagram (No session — connect in Settings)"
        else:
            base["scraper_engine"] = "Instagram (Session may be expired — reconnect in Settings)"

    logger.info(
        f"Instagram scrape done for @{handle}: "
        f"success={base['scrape_success']}, followers={base['followers']}, "
        f"display_name={base['display_name']}"
    )
    return base
