import sys
import os
import io
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# Append root directory to path to allow importing from the models directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.schemas import AccountFeatures, AnalyzeResponse, BatchRequest, ReportRequest, UrlRequest
from models.predict import predict
from backend.report_generator import build_pdf_report
from fastapi.responses import StreamingResponse



app = FastAPI(
    title="SIH1775 Fake Account Detector API",
    description="Live dual-platform inference API powered by tuned XGBoost and SHAP explainability.",
    version="1.0.0"
)

# CORS Middleware (Mandatory for React Frontend Integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        # Compute network graph
        from backend.network_analyser import analyze_profile_network
        result["network_graph"] = analyze_profile_network(
            username, 
            result["platform"], 
            result["risk_score"]
        )
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

        # 2. Extract Tabular Metrics (only fetch secondary OSINT if Playwright didn't get valid numbers)
        has_full_counts = bool(playwright_data.get("followers", 0) > 0 and playwright_data.get("followers") != 100)
        
        if not has_full_counts:
            try:
                osint_features = scrape_profile_data(payload.url)
            except Exception:
                osint_features = {}
        else:
            osint_features = {}

        username = playwright_data.get("username") or osint_features.get("username", "unknown_user")
        platform = playwright_data.get("platform") or osint_features.get("platform", "auto")
        
        features = {**osint_features, **{k: v for k, v in playwright_data.items() if k in ['followers', 'following', 'post_count', 'has_profile_pic', 'bio_length'] and v is not None}}
        features["username"] = username
        features["platform"] = platform

        # 3. Run XGBoost Machine Learning Tabular Prediction
        predict_input = {k: v for k, v in features.items() if k not in ["username", "platform", "bio", "posts", "avatar_url", "external_url", "scraper_engine"]}
        result = predict(predict_input, platform=platform)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        result = sanitize_result(result)
        result["username"] = username
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

@app.get("/health")
def health():
    return {"status": "ok", "message": "Backend, ML Models, and Playwright Multimodal Engine are online."}