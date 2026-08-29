"""
playwright_scraper.py
======================
Platform router — delegates scraping to the correct platform-specific module.

Routing:
  twitter / x.com  →  twitter_scraper.scrape_twitter()
  instagram        →  instagram_scraper.scrape_instagram()
  facebook / fb    →  facebook_scraper.scrape_facebook()
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger("PlaywrightScraper")


def parse_platform_and_handle(url: str):
    """
    Extracts platform identifier and username handle from a social profile URL.
    Returns (platform, handle) tuple.
    Platforms: "twitter", "meta", "meta_fb"
    """
    url = url.strip()

    tw = re.search(r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,25})", url)
    if tw:
        return "twitter", tw.group(1)

    ig = re.search(r"instagram\.com/([a-zA-Z0-9_\.]{1,30})", url)
    if ig:
        return "meta", ig.group(1)

    fb = re.search(r"(?:facebook\.com|fb\.com)/([a-zA-Z0-9_\.]{1,50})", url)
    if fb:
        return "meta_fb", fb.group(1)

    # Generic fallback
    clean = url.replace("https://", "").replace("http://", "").split("/")[0].replace("@", "")
    return "auto", clean


async def scrape_with_playwright(url: str) -> Dict[str, Any]:
    """
    Main entry point — routes to the correct platform scraper.
    All platform scrapers return a standardised dict with the same keys.
    """
    platform, handle = parse_platform_and_handle(url)
    logger.info(f"Routing scrape request: platform={platform}, handle=@{handle}")

    if platform == "twitter":
        from backend.twitter_scraper import scrape_twitter
        return await scrape_twitter(url, handle)

    elif platform == "meta_fb":
        from backend.facebook_scraper import scrape_facebook
        result = await scrape_facebook(url, handle)
        return result

    elif platform == "meta":
        from backend.instagram_scraper import scrape_instagram
        return await scrape_instagram(url, handle)

    else:
        # Unknown platform — return minimal safe default
        logger.warning(f"Unknown platform for URL: {url}")
        return {
            "username": handle,
            "platform": "auto",
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
            "scraper_engine": "Unknown platform",
        }
