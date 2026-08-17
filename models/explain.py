"""
================================================================================
EXPLAINABILITY & PREDICTION INFERENCE ENGINE (explain.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This script acts as the prediction and explainability engine for the fake account 
detection system. It loads the trained XGBoost model and initializes a SHAP (SHapley 
Additive exPlanations) TreeExplainer. When given an account's feature metrics, it calculates 
a continuous risk score (0-100%), assigns a 3-tier classification label (`REAL`, `SUSPICIOUS`, 
or `FAKE`), and translates tree decision impacts into plain-English reasons explaining 
why the account was flagged.

TECHNICAL SPECIFICATIONS & DOMAIN LOGIC:
1. Feature Alignment & Input Preprocessing:
   - Enforces strict canonical column ordering (`EXPECTED_FEATURE_ORDER`) matching the 
     exact schema memory of the trained XGBoost estimator.
   - Converts dictionary payloads into 2D NumPy float arrays to prevent feature name 
     mismatch warnings during evaluation.

2. Risk Scoring & 3-Class Categorization Thresholds:
   - Extracts raw target probability via `predict_proba(X)[0][1]`.
   - Risk Score Calculation: `risk_score = round(raw_probability * 100, 2)`.
   - 3-Class Thresholding Logic:
     - `raw_probability < 0.30`: Categorized as `REAL`.
     - `0.30 <= raw_probability <= 0.70`: Categorized as `SUSPICIOUS`.
     - `raw_probability > 0.70`: Categorized as `FAKE`.

3. SHAP Tree Attribution & Translation:
   - Uses `shap.TreeExplainer` to compute marginal feature impact values (`shap_values`).
   - Filters features with positive SHAP contributions (pushing classification towards `FAKE`).
   - Maps raw feature keys to human-readable explanation strings (e.g., `follower_following_ratio` 
     -> "Suspicious follower-to-following ratio", `digits_in_username` -> "High entropy in username").
"""

import os
import joblib
import pandas as pd
import numpy as np
import shap

# Configuration Paths
SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved")
MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "twitter_xgboost_tuned.pkl")

# The exact column order the model memorized during training
EXPECTED_FEATURE_ORDER = [
    'followers', 'following', 'post_count', 'verified', 
    'description_length', 'account_age_days', 'follower_following_ratio', 
    'reputation_score', 'username_length', 'digits_in_username', 
    'digit_ratio_username', 'has_url', 'posts_per_day'
]

# Load artifact
try:
    model = joblib.load(MODEL_PATH)
    explainer = shap.TreeExplainer(model)
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load model artifacts. {e}")
    model, explainer = None, None

def translate_shap_to_english(feature_name: str, feature_value, shap_value) -> str:
    """
    Translates raw feature names and values into readable reasons for the frontend.
    Only processes features pushing the score TOWARDS a 'Fake' classification (shap_value > 0).
    """
    val = round(feature_value, 2)
    
    translations = {
        'follower_following_ratio': f"Suspicious follower-to-following ratio ({val}).",
        'posts_per_day': f"Abnormal activity density ({val} posts per day).",
        'account_age_days': f"Account age metric is anomalous ({val} days old).",
        'reputation_score': f"Low reputation score within the network ({val}).",
        'digits_in_username': f"High entropy in username ({val} digits detected).",
        'verified': "Account lacks verification credentials.",
        'has_url': "Presence of an external URL paired with other suspicious traits.",
        'post_count': f"Unusual total post count ({val}).",
        'following': f"Mass-following behavior detected ({val} accounts followed)."
    }
    
    return translations.get(feature_name, f"Anomalous metric detected in {feature_name} ({val}).")

def predict(features_dict: dict) -> dict:
    """
    Standalone prediction function. 
    Accepts a dictionary of features, returns risk score, 3-class label, and SHAP reasons.
    """
    if model is None:
        return {"error": "Model artifact not loaded."}

    # 1. Prepare Data
    df_input = pd.DataFrame([features_dict])
    
    # Force the DataFrame into the exact column order expected by XGBoost
    df_input = df_input[EXPECTED_FEATURE_ORDER]
    
    # Convert to numpy array to prevent XGBoost feature name mismatch warnings
    X_ready = df_input.to_numpy()

    # 2. Extract Prediction & Probabilities directly from raw data
    proba = model.predict_proba(X_ready)[0]
    risk_score_raw = proba[1]
    risk_score = round(risk_score_raw * 100, 2)

    # 3. Apply 3-Class Threshold Logic
    if risk_score_raw < 0.30:
        classification = "REAL"
    elif risk_score_raw <= 0.70:
        classification = "SUSPICIOUS"
    else:
        classification = "FAKE"

    # 4. Generate Explainability (SHAP)
    shap_values = explainer.shap_values(X_ready)
    
    if isinstance(shap_values, list):
        instance_shap = shap_values[1][0]
    elif len(shap_values.shape) == 3:
        instance_shap = shap_values[0, :, 1]
    else:
        instance_shap = shap_values[0]

    feature_impacts = []
    features_list = df_input.columns.tolist()
    for i, feature_name in enumerate(features_list):
        feature_impacts.append({
            'feature': feature_name,
            'original_value': df_input.iloc[0, i],
            'shap_value': instance_shap[i]
        })

    feature_impacts.sort(key=lambda x: x['shap_value'], reverse=True)

    reasons = []
    for impact in feature_impacts:
        if impact['shap_value'] > 0 and len(reasons) < 3:
            english_reason = translate_shap_to_english(
                impact['feature'], 
                impact['original_value'], 
                impact['shap_value']
            )
            reasons.append(english_reason)

    if classification == "REAL":
        reasons = ["Account metrics align with standard human baseline behavior."]

    return {
        "risk_score": risk_score,
        "classification": classification,
        "confidence": round(risk_score_raw if classification == "FAKE" else (1 - risk_score_raw), 2),
        "reasons": reasons
    }