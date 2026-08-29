"""
twitter_scraper.py
==================
Twitter / X profile scraper using Playwright with storageState session injection.

With a valid session:
  - Extracts real follower/following counts, display name, bio, verified badge,
    tweets, and avatar directly from the authenticated DOM.

Without a session (or expired session):
  - Falls back to parsing what's visible in meta description tags (limited),
    then marks scrape_success=False so main.py uses OSINT heuristics.
"""

import re
import logging
from typing import Dict, Any, Optional

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

from backend.session_manager import get_session_path

logger = logging.getLogger("TwitterScraper")

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


def _is_login_wall(url: str) -> bool:
    """Detects if X redirected to a login page."""
    return "login" in url.lower() or "x.com/i/flow" in url.lower()


async def scrape_twitter(url: str, handle: str) -> Dict[str, Any]:
    """
    Scrapes a Twitter/X profile using Playwright with session injection.
    Returns a standardised profile dict.
    """
    base: Dict[str, Any] = {
        "username": handle,
        "platform": "twitter",
        "display_name": None,
        "bio": "",
        "external_url": None,
        "avatar_url": None,
        "followers": 0,
        "following": 0,
        "post_count": 0,
        "verified": 0,
        "has_profile_pic": 0,
        "bio_length": 0,
        "description_length": 0,
        "has_url": 0,
        "account_age_days": -1,
        "posts": [],
        "scrape_success": False,
        "scraper_engine": "Twitter Playwright (session-injected)",
    }

    session_path = get_session_path("twitter")
    target_url = f"https://x.com/{handle}"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=_BROWSER_ARGS)

            ctx_kwargs: Dict[str, Any] = {
                "user_agent": _USER_AGENT,
                "viewport": {"width": 1280, "height": 900},
                "locale": "en-US",
            }
            if session_path:
                ctx_kwargs["storage_state"] = session_path
                logger.info(f"Twitter: using saved session for @{handle}")
            else:
                logger.info(f"Twitter: no session — limited scrape for @{handle}")

            context = await browser.new_context(**ctx_kwargs)
            page = await context.new_page()
            page.set_default_timeout(12000)

            await page.goto(target_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2200)

            # Check for login redirect
            current_url = page.url
            if _is_login_wall(current_url):
                logger.warning(f"Twitter session expired or missing for @{handle} — login wall detected")
                base["scraper_engine"] = "Twitter (Session Expired — reconnect in Settings)"
                await browser.close()
                return base

            # ----------------------------------------------------------------
            # 1. Display Name
            # ----------------------------------------------------------------
            try:
                dn_el = page.locator('[data-testid="UserName"]').first
                if await dn_el.count() > 0:
                    raw = await dn_el.inner_text()
                    lines = [l.strip() for l in raw.split("\n") if l.strip()]
                    if lines:
                        base["display_name"] = lines[0]
            except Exception:
                pass

            # ----------------------------------------------------------------
            # 2. Bio / Description
            # ----------------------------------------------------------------
            try:
                bio_el = page.locator('[data-testid="UserDescription"]').first
                if await bio_el.count() > 0:
                    bio = await bio_el.inner_text()
                    base["bio"] = bio
                    base["bio_length"] = len(bio)
                    base["description_length"] = len(bio)
                    base["scrape_success"] = True
            except Exception:
                pass

            # ----------------------------------------------------------------
            # 3. Follower / Following counts
            #    Primary: parse stat anchor links in the profile header
            #    Fallback: meta description regex
            # ----------------------------------------------------------------
            try:
                # Following
                fing_el = page.locator(f'a[href="/{handle}/following"] span span').first
                if await fing_el.count() > 0:
                    base["following"] = _parse_count(await fing_el.inner_text())
                    base["scrape_success"] = True
            except Exception:
                pass

            try:
                # Followers (verified_followers first, then /followers)
                fol_sel = (
                    f'a[href="/{handle}/verified_followers"] span span, '
                    f'a[href="/{handle}/followers"] span span'
                )
                fol_el = page.locator(fol_sel).first
                if await fol_el.count() > 0:
                    base["followers"] = _parse_count(await fol_el.inner_text())
                    base["scrape_success"] = True
            except Exception:
                pass

            # Meta description fallback if DOM counts didn't work
            if base["followers"] == 0:
                try:
                    meta = await page.locator('meta[name="description"]').first.get_attribute("content")
                    if meta:
                        m = re.search(
                            r"([\d,\.KkMm]+)\s*Followers?,\s*([\d,\.KkMm]+)\s*Following",
                            meta
                        )
                        if m:
                            base["followers"] = _parse_count(m.group(1))
                            base["following"] = _parse_count(m.group(2))
                            base["scrape_success"] = True
                except Exception:
                    pass

            # ----------------------------------------------------------------
            # 4. Verified badge
            # ----------------------------------------------------------------
            try:
                vbadge = page.locator('[data-testid="icon-verified"]').first
                if await vbadge.count() > 0:
                    base["verified"] = 1
            except Exception:
                pass

            # ----------------------------------------------------------------
            # 5. Avatar
            # ----------------------------------------------------------------
            try:
                av_el = page.locator(
                    'img[alt*="profile image"], [data-testid="Tweet-User-Avatar"] img'
                ).first
                if await av_el.count() > 0:
                    src = await av_el.get_attribute("src")
                    if src:
                        base["avatar_url"] = src
                        base["has_profile_pic"] = 1
            except Exception:
                pass

            # ----------------------------------------------------------------
            # 6. External URL in bio
            # ----------------------------------------------------------------
            try:
                url_el = page.locator('[data-testid="UserUrl"] a').first
                if await url_el.count() > 0:
                    base["external_url"] = await url_el.get_attribute("href")
                    base["has_url"] = 1
            except Exception:
                pass

            # ----------------------------------------------------------------
            # 7. Tweets (up to 6)
            # ----------------------------------------------------------------
            try:
                tweet_els = page.locator('article[data-testid="tweet"]')
                t_count = await tweet_els.count()
                posts = []
                for i in range(min(t_count, 6)):
                    el = tweet_els.nth(i)
                    text = ""
                    img_src = ""
                    if await el.locator('[data-testid="tweetText"]').count() > 0:
                        text = await el.locator('[data-testid="tweetText"]').first.inner_text()
                    if await el.locator('[data-testid="tweetPhoto"] img').count() > 0:
                        img_src = await el.locator('[data-testid="tweetPhoto"] img').first.get_attribute("src") or ""
                    if text:
                        posts.append({
                            "id": f"tw_{i+1}",
                            "thumbnail_url": img_src or "https://abs.twimg.com/icons/apple-touch-icon-192x192.png",
                            "caption": text,
                            "likes": 0,
                            "comments": 0,
                            "timestamp": "Recent",
                        })
                if posts:
                    base["posts"] = posts
                    base["post_count"] = max(base["post_count"], len(posts))
            except Exception:
                pass

            await browser.close()

    except Exception as e:
        logger.warning(f"Twitter Playwright scrape failed for @{handle}: {e}")

    logger.info(
        f"Twitter scrape done for @{handle}: "
        f"success={base['scrape_success']}, followers={base['followers']}, "
        f"display_name={base['display_name']}"
    )
    return base
