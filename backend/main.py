import sys
import os
import io
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# Append root directory to path to allow importing from the models directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.schemas import AccountFeatures, AnalyzeResponse, BatchRequest
from models.predict import predict

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
        
        result = predict(input_dict, platform=platform)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return sanitize_result(result)
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

@app.get("/health")
def health():
    return {"status": "ok", "message": "Backend and ML Models are online."}