"""
session_manager.py
==================
Manages Playwright storageState session files per platform.
Sessions are stored locally as JSON files in a dedicated sessions/ directory.
The user's PASSWORD is never stored — only the browser session cookies
(equivalent to what any browser holds after login).

Supported platforms: "twitter", "instagram", "facebook"
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger("SessionManager")

# Store sessions next to this file, in a dedicated directory
_SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")


def _ensure_sessions_dir() -> None:
    os.makedirs(_SESSIONS_DIR, exist_ok=True)


def _session_path(platform: str) -> str:
    return os.path.join(_SESSIONS_DIR, f"{platform}_session.json")


def _meta_path(platform: str) -> str:
    return os.path.join(_SESSIONS_DIR, f"{platform}_meta.json")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def has_session(platform: str) -> bool:
    """Returns True if a valid storageState file exists for this platform."""
    _ensure_sessions_dir()
    return os.path.exists(_session_path(platform))


def get_session_path(platform: str) -> Optional[str]:
    """
    Returns the absolute path to the storageState JSON file, or None
    if no session exists. Pass this directly to Playwright's
    `browser.new_context(storage_state=...)`.
    """
    _ensure_sessions_dir()
    path = _session_path(platform)
    return path if os.path.exists(path) else None


def save_session(platform: str, storage_state: Dict[str, Any]) -> str:
    """
    Persists a Playwright storageState dict (cookies + localStorage) to disk.
    Also writes a metadata file with the capture timestamp.
    Returns the path where the session was saved.
    """
    _ensure_sessions_dir()
    path = _session_path(platform)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(storage_state, f, indent=2)

    # Write metadata (capture time, platform)
    meta = {
        "platform": platform,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "cookies_count": len(storage_state.get("cookies", [])),
    }
    with open(_meta_path(platform), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Session saved for platform '{platform}' → {path}")
    return path


def revoke_session(platform: str) -> bool:
    """
    Deletes the storageState and metadata files for a platform.
    Returns True if files were found and deleted, False otherwise.
    """
    _ensure_sessions_dir()
    deleted = False
    for p in [_session_path(platform), _meta_path(platform)]:
        if os.path.exists(p):
            os.remove(p)
            deleted = True
    if deleted:
        logger.info(f"Session revoked for platform '{platform}'")
    return deleted


def get_session_meta(platform: str) -> Optional[Dict[str, Any]]:
    """Returns session metadata (capture time, cookie count), or None."""
    _ensure_sessions_dir()
    p = _meta_path(platform)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_session_status() -> Dict[str, Any]:
    """
    Returns a dict summarising the session status for all 3 platforms.
    Used by the /session/status API endpoint.
    """
    result = {}
    for platform in ("twitter", "instagram", "facebook"):
        meta = get_session_meta(platform)
        result[platform] = {
            "connected": has_session(platform),
            "captured_at": meta.get("captured_at") if meta else None,
            "cookies_count": meta.get("cookies_count", 0) if meta else 0,
        }
    return result


def extract_instagram_session_id(platform: str = "instagram") -> Optional[str]:
    """
    Extracts the Instagram `sessionid` cookie value from the saved storageState.
    Used to authenticate Instaloader without sharing the password.
    Returns the sessionid string, or None if not found.
    """
    path = get_session_path(platform)
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        for cookie in state.get("cookies", []):
            if cookie.get("name") == "sessionid" and "instagram" in cookie.get("domain", ""):
                return cookie["value"]
    except Exception as e:
        logger.warning(f"Could not extract Instagram sessionid: {e}")
    return None


def parse_and_import_session(platform: str, data: Any) -> Dict[str, Any]:
    """
    Accepts:
      1. A full Playwright storageState dict: {"cookies": [...], "origins": [...]}
      2. A list of cookies: [{"name": "...", "value": "..."}, ...]
      3. A single string token: e.g. "auth_token_value" or "sessionid_value"
      4. A raw cookie string: "auth_token=xyz; ct0=abc"
    Normalizes it into a valid Playwright storageState format and saves it.
    """
    _ensure_sessions_dir()

    storage_state: Dict[str, Any] = {"cookies": [], "origins": []}

    domain_map = {
        "twitter": ".x.com",
        "instagram": ".instagram.com",
        "facebook": ".facebook.com",
    }
    token_name_map = {
        "twitter": "auth_token",
        "instagram": "sessionid",
        "facebook": "c_user",
    }
    target_domain = domain_map.get(platform, f".{platform}.com")

    if isinstance(data, dict) and "cookies" in data:
        storage_state = data
    elif isinstance(data, list):
        # Normalize list of cookie objects
        cookies = []
        for item in data:
            if isinstance(item, dict) and "name" in item and "value" in item:
                cookies.append({
                    "name": str(item["name"]),
                    "value": str(item["value"]),
                    "domain": item.get("domain", target_domain),
                    "path": item.get("path", "/"),
                    "httpOnly": item.get("httpOnly", True),
                    "secure": item.get("secure", True),
                    "sameSite": item.get("sameSite", "Lax"),
                })
        storage_state = {"cookies": cookies, "origins": []}
    elif isinstance(data, str):
        text = data.strip()
        # Check if text is JSON string
        if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
            try:
                parsed = json.loads(text)
                return parse_and_import_session(platform, parsed)
            except Exception:
                pass

        cookies = []
        if "=" in text:
            # Semicolon-separated cookies: "cookie1=val1; cookie2=val2"
            parts = [p.strip() for p in text.split(";") if p.strip()]
            for part in parts:
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookies.append({
                        "name": k.strip(),
                        "value": v.strip(),
                        "domain": target_domain,
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax",
                    })
        else:
            # Single raw token string
            token_name = token_name_map.get(platform, "session")
            cookies.append({
                "name": token_name,
                "value": text,
                "domain": target_domain,
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax",
            })
        storage_state = {"cookies": cookies, "origins": []}
    else:
        raise ValueError("Unsupported session format. Provide storageState JSON, cookie array, or session token.")

    cookie_count = len(storage_state.get("cookies", []))
    if cookie_count == 0:
        raise ValueError("No valid cookies found in provided data.")

    path = save_session(platform, storage_state)
    return {
        "status": "imported",
        "platform": platform,
        "cookies_saved": cookie_count,
        "session_path": path,
        "message": f"Successfully imported session for {platform} ({cookie_count} cookies saved).",
    }

