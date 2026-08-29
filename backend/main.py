import sys
import os
import io
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# Append root directory to path to allow importing from the models directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.schemas import (
    AccountFeatures, AnalyzeResponse, BatchRequest, ReportRequest, UrlRequest,
    SessionCaptureRequest, SessionImportRequest, SessionStatusResponse, PlatformSessionInfo,
)
from models.predict import predict
from backend.report_generator import build_pdf_report
from backend.session_manager import get_all_session_status, save_session, revoke_session, parse_and_import_session
from fastapi.responses import StreamingResponse
from backend.cases import router as cases_router, create_tables
from backend.seed_cases import seed_cases


@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup: ensure DB tables exist and seed mock cases if empty."""
    create_tables()
    seed_cases()
    yield



app = FastAPI(
    title="SIH1775 Fake Account Detector API",
    description="Live dual-platform inference API powered by tuned XGBoost and SHAP explainability.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware (Mandatory for React Frontend Integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the escalation cases router
app.include_router(cases_router)

def sanitize_result(res: dict) -> dict:
    """Safely converts numpy data types to standard Python primitives for JSON encoding."""
    if "risk_score" in res:
        res["risk_score"] = float(res["risk_score"])
    if "confidence" in res:
        res["confidence"] = float(res["confidence"])
    return res

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(features: AccountFeatures):
    try:
        # Filter out None values so predict auto-calculates missing ratios if needed
        input_dict = {k: v for k, v in features.dict().items() if v is not None}
        platform = input_dict.pop("platform", "auto")
        username = input_dict.get("username", "suspect_profile")
        
        result = predict(input_dict, platform=platform)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        result = sanitize_result(result)
        result["network_graph"] = None
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/analyze/batch")
def analyze_batch(payload: BatchRequest):
    results = []
    for acc in payload.accounts:
        try:
            input_dict = {k: v for k, v in acc.dict().items() if v is not None}
            platform = input_dict.pop("platform", "auto")
            res = predict(input_dict, platform=platform)
            if "error" in res:
                results.append({"error": res["error"]})
            else:
                results.append(sanitize_result(res))
        except Exception as e:
            results.append({"error": str(e)})
    return {"results": results}

@app.post("/analyze/batch/csv")
async def analyze_batch_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. CSV file required.")
        
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
        df = df.replace([np.inf, -np.inf], 0).fillna(0)
        
        results = []
        for _, row in df.iterrows():
            features = row.to_dict()
            account_id = features.pop("username", features.pop("account_id", "Unknown Account"))
            features.pop("is_fake", None)
            
            try:
                res = predict(features)
                if "error" in res:
                    results.append({"account_id": str(account_id), "error": res["error"]})
                else:
                    res = sanitize_result(res)
                    res["account_id"] = str(account_id)
                    results.append(res)
            except Exception as e:
                results.append({"account_id": str(account_id), "error": str(e)})
                
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

@app.post("/analyze/report")
def export_report(payload: ReportRequest):
    try:
        pdf_bytes = build_pdf_report(payload.username, payload.features, payload.prediction)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ITBP_Forensic_Report_{payload.username}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.post("/analyze/url")
async def analyze_url(payload: UrlRequest):
    try:
        from backend.playwright_scraper import scrape_with_playwright
        from backend.content_analyser import analyze_multimodal_content
        from backend.osint_scraper import scrape_profile_data
        from backend.network_analyser import analyze_profile_network
        
        # 1. Execute Playwright Headless Scraping for rich media, captions, and bio
        playwright_data = {}
        try:
            playwright_data = await scrape_with_playwright(payload.url)
        except Exception as pe:
            print(f"Playwright scrape notice: {pe}")
            playwright_data = {}

        # 2. Extract Tabular Metrics — only hit OSINT if Playwright didn't successfully scrape
        # scrape_success=True means the scraper got real DOM data; False = fallback/blocked
        playwright_scrape_success = bool(playwright_data.get("scrape_success", False))

        if not playwright_scrape_success:
            try:
                osint_features = scrape_profile_data(payload.url)
            except Exception:
                osint_features = {}
        else:
            osint_features = {}

        username = playwright_data.get("username") or osint_features.get("username", "unknown_user")
        platform = playwright_data.get("platform") or osint_features.get("platform", "auto")
        display_name = playwright_data.get("display_name")

        features = {**osint_features, **{k: v for k, v in playwright_data.items() if k in ['followers', 'following', 'post_count', 'has_profile_pic', 'bio_length'] and v is not None}}
        features["username"] = username
        features["platform"] = platform

        # 3. Run XGBoost Machine Learning Tabular Prediction
        predict_input = {k: v for k, v in features.items() if k not in [
            "username", "platform", "bio", "posts", "avatar_url",
            "external_url", "scraper_engine", "scrape_success", "display_name"
        ]}
        result = predict(predict_input, platform=platform)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        result = sanitize_result(result)
        result["username"] = username
        result["display_name"] = display_name
        result["raw_features"] = features
        
        # 4. Run Multimodal NLP, Phishing & Caption Similarity Analysis
        bio_text = playwright_data.get("bio") or ""
        external_url = playwright_data.get("external_url")
        posts = playwright_data.get("posts", [])
        avatar_url = playwright_data.get("avatar_url")

        content_analysis = analyze_multimodal_content(
            bio=bio_text,
            external_url=external_url,
            posts=posts,
            avatar_url=avatar_url,
            username=username,
            display_name=playwright_data.get("display_name"),
            followers=features.get("followers", 0),
            post_count=features.get("post_count", 0)
        )

        # 5. Compute Unified Multimodal Intelligence Risk Score (60% Tabular ML + 40% Multimodal NLP/Threat)
        tabular_score = result["risk_score"]
        content_score = content_analysis["content_risk_score"]
        
        # If content threat is critical/elevated, weight content threat strongly
        if content_score >= 60:
            unified_risk = round(max(tabular_score, (tabular_score * 0.40) + (content_score * 0.60)), 2)
        elif content_score >= 35:
            unified_risk = round((tabular_score * 0.50) + (content_score * 0.50), 2)
        else:
            unified_risk = round((tabular_score * 0.70) + (content_score * 0.30), 2)

        result["content_analysis"] = content_analysis
        result["posts"] = posts
        result["avatar_url"] = avatar_url
        result["bio"] = bio_text
        result["external_url"] = external_url
        result["multimodal_risk_score"] = unified_risk
        result["risk_score"] = unified_risk

        # Adjust classification according to fused multimodal risk
        if unified_risk >= 65.0:
            result["classification"] = "FAKE"
        elif unified_risk >= 35.0:
            result["classification"] = "SUSPICIOUS"
        else:
            result["classification"] = "REAL"

        # Dynamically calculate confidence from the unified risk score
        unified_prob = float(unified_risk) / 100.0
        if result["classification"] == "FAKE":
            dyn_conf = unified_prob
        elif result["classification"] == "REAL":
            dyn_conf = 1.0 - unified_prob
        else:
            dyn_conf = 0.50 + abs(unified_prob - 0.50)

        result["confidence"] = float(round(float(np.clip(dyn_conf, 0.51, 0.9999)), 4))

        # Prepend content/threat forensic reasons if any threats detected
        for forensic in reversed(content_analysis.get("forensic_reasons", [])):
            if "authentic" not in forensic.lower() and forensic not in result["reasons"]:
                result["reasons"].insert(0, f"Threat Forensics: {forensic}")

        # 6. Add Coordinated Network Graph
        result["network_graph"] = analyze_profile_network(
            username, 
            result["platform"], 
            result["risk_score"]
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze/deep")
async def analyze_deep(payload: UrlRequest):
    """Alias for deep Playwright multimodal audit."""
    return await analyze_url(payload)


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/session/status", response_model=SessionStatusResponse)
def session_status():
    """
    Returns which platforms have active saved sessions.
    Used by the frontend Settings panel to show connection status.
    """
    raw = get_all_session_status()
    return SessionStatusResponse(
        twitter=PlatformSessionInfo(**raw["twitter"]),
        instagram=PlatformSessionInfo(**raw["instagram"]),
        facebook=PlatformSessionInfo(**raw["facebook"]),
    )


@app.post("/session/capture")
async def session_capture(payload: SessionCaptureRequest):
    """
    Launches a VISIBLE (non-headless) Playwright Chromium browser window.
    The user logs in to the platform manually (handles 2FA/CAPTCHA themselves).
    Once login is detected, the session is saved and the browser closes.

    The user's PASSWORD is never stored — only the browser session cookies.
    """
    from playwright.async_api import async_playwright
    import asyncio

    platform = payload.platform
    login_urls = {
        "twitter": "https://x.com/i/flow/login",
        "instagram": "https://www.instagram.com/accounts/login/",
        "facebook": "https://www.facebook.com/login/",
    }
    success_domains = {
        "twitter": "x.com",
        "instagram": "instagram.com",
        "facebook": "facebook.com",
    }
    # Patterns that indicate a successful login (not on a login/flow page)
    login_complete_patterns = {
        "twitter": lambda url: "x.com" in url and "/login" not in url and "/flow" not in url,
        "instagram": lambda url: "instagram.com" in url and "/login" not in url and "/accounts" not in url,
        "facebook": lambda url: "facebook.com" in url and "/login" not in url and "/checkpoint" not in url,
    }

    # Check if running in a headless cloud environment without a display
    is_headless_cloud = bool(os.environ.get("RENDER")) or (sys.platform.startswith("linux") and not os.environ.get("DISPLAY"))
    if is_headless_cloud:
        raise HTTPException(
            status_code=400,
            detail=(
                "Interactive browser login is only available when running the backend locally on your computer (localhost:8000). "
                "Cloud deployments (like Render) run headlessly without a desktop display to open a pop-up browser window."
            ),
        )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,   # VISIBLE window — user logs in themselves
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = await browser.new_context(
                viewport={"width": 1100, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            await page.goto(login_urls[platform])

            # Wait up to 3 minutes for the user to log in
            is_logged_in = login_complete_patterns[platform]
            timeout = 180  # seconds
            interval = 2
            elapsed = 0
            while elapsed < timeout:
                await asyncio.sleep(interval)
                elapsed += interval
                current_url = page.url
                if is_logged_in(current_url):
                    # Give the page a moment to fully load cookies
                    await asyncio.sleep(2)
                    break
            else:
                await browser.close()
                raise HTTPException(
                    status_code=408,
                    detail=f"Login timeout: user did not complete {platform} login within 3 minutes."
                )

            # Save the full browser session state (cookies + localStorage)
            storage_state = await context.storage_state()
            await browser.close()

        path = save_session(platform, storage_state)
        cookie_count = len(storage_state.get("cookies", []))
        return {
            "status": "captured",
            "platform": platform,
            "cookies_saved": cookie_count,
            "session_path": path,
            "message": f"Session captured for {platform}. {cookie_count} cookies saved. Future scans will use this session."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session capture failed: {str(e)}")


@app.post("/session/revoke")
def session_revoke(payload: SessionCaptureRequest):
    """
    Deletes the saved session for a platform.
    The user will need to reconnect before scraping that platform again.
    """
    deleted = revoke_session(payload.platform)
    return {
        "status": "revoked" if deleted else "not_found",
        "platform": payload.platform,
        "message": f"Session for {payload.platform} {'deleted' if deleted else 'was not found'}."
    }


@app.post("/session/import")
def session_import(payload: SessionImportRequest):
    """
    Directly imports session cookies, storageState JSON, or a raw session token.
    Allows authenticating cloud-hosted backend instances (e.g. Render) where
    interactive GUI pop-up windows cannot be opened.
    """
    try:
        res = parse_and_import_session(payload.platform, payload.data)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import session: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok", "message": "Backend, ML Models, and Playwright Multimodal Engine are online."}