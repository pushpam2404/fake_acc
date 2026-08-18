import sys
import os
from fastapi import FastAPI, HTTPException
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

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(features: AccountFeatures):
    try:
        # Filter out None values so predict auto-calculates missing ratios if needed
        input_dict = {k: v for k, v in features.dict().items() if v is not None}
        platform = input_dict.pop("platform", "auto")
        
        result = predict(input_dict, platform=platform)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
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
                results.append(res)
        except Exception as e:
            results.append({"error": str(e)})
    return {"results": results}

@app.get("/health")
def health():
    return {"status": "ok", "message": "Backend and ML Models are online."}