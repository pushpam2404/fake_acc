"""
================================================================================
DUAL-PLATFORM EXPLAINABILITY & PREDICTION INFERENCE ENGINE (explain.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This script acts as the unified prediction and explainability engine for both 
Twitter/X and Meta/Instagram social media platforms. It dynamically loads the 
corresponding platform model binaries (Twitter XGBoost/RandomForest and Meta 
XGBoost/RandomForest) and initializes SHAP (SHapley Additive exPlanations) 
TreeExplainers. When given an account's feature dictionary, it determines the platform, 
enforces schema alignment, calculates a continuous risk score (0-100%), assigns a 3-tier 
classification label (`REAL`, `SUSPICIOUS`, or `FAKE`), and translates tree decision 
impacts into human-readable English reasons explaining flagged traits.

TECHNICAL SPECIFICATIONS & DOMAIN LOGIC:
1. Multi-Platform Artifact Loading:
   - Twitter Artifact: Loads `twitter_xgboost_tuned.pkl` (or `twitter_best_model.pkl`).
   - Meta Artifact: Loads `meta_xgboost_tuned.pkl` (or `meta_best_model.pkl`).
   - Initializes dedicated SHAP `TreeExplainer` instances for both platform models.

2. Dynamic Platform Routing & Schema Alignment:
   - Supports explicit `platform="twitter" | "meta" | "auto"`.
   - In "auto" mode, detects Meta payloads via distinct Meta feature presence (`has_profile_pic`, `bio_length`).
   - Enforces canonical feature ordering per platform (`TWITTER_EXPECTED_FEATURES` vs `META_EXPECTED_FEATURES`).

3. Risk Scoring & 3-Class Categorization Thresholds:
   - Extracts raw prediction probability: `risk_score = round(raw_probability * 100, 2)`.
   - Classification Thresholds:
     - `risk_score < 30.0`: `REAL`
     - `30.0 <= risk_score <= 70.0`: `SUSPICIOUS`
     - `risk_score > 70.0`: `FAKE`

4. SHAP Feature Attribution Translation:
   - Filters positive SHAP contribution impacts pushing classification towards `FAKE`.
   - Translates platform-specific metrics (`follower_following_ratio`, `has_profile_pic`, `bio_length`, 
     `reputation_score`, `digit_ratio_username`, `posts_per_day`) into human-readable statements.
"""

import os
import joblib
import pandas as pd
import numpy as np
import shap

SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved")

# Canonical feature ordering per platform
TWITTER_EXPECTED_FEATURES = [
    'followers', 'following', 'post_count', 'verified', 
    'description_length', 'account_age_days', 'follower_following_ratio', 
    'reputation_score', 'username_length', 'digits_in_username', 
    'digit_ratio_username', 'has_url', 'posts_per_day'
]

META_EXPECTED_FEATURES = [
    'followers', 'following', 'post_count', 
    'has_profile_pic', 'bio_length', 
    'follower_following_ratio', 'reputation_score'
]

# Load artifacts for Twitter
TWITTER_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "twitter_xgboost_tuned.pkl")
if not os.path.exists(TWITTER_MODEL_PATH):
    TWITTER_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "twitter_best_model.pkl")

# Load artifacts for Meta
META_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "meta_xgboost_tuned.pkl")
if not os.path.exists(META_MODEL_PATH):
    META_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "meta_best_model.pkl")

models = {}
explainers = {}

try:
    if os.path.exists(TWITTER_MODEL_PATH):
        models['twitter'] = joblib.load(TWITTER_MODEL_PATH)
        explainers['twitter'] = shap.TreeExplainer(models['twitter'])
except Exception as e:
    print(f"WARNING: Failed to load Twitter model artifact. {e}")

try:
    if os.path.exists(META_MODEL_PATH):
        models['meta'] = joblib.load(META_MODEL_PATH)
        explainers['meta'] = shap.TreeExplainer(models['meta'])
except Exception as e:
    print(f"WARNING: Failed to load Meta model artifact. {e}")


def translate_shap_to_english(feature_name: str, feature_value, shap_value) -> str:
    val = round(feature_value, 2)
    
    translations = {
        'follower_following_ratio': f"Suspicious follower-to-following ratio ({val}).",
        'posts_per_day': f"Abnormal activity density ({val} posts per day).",
        'account_age_days': f"Account age metric is anomalous ({val} days old).",
        'reputation_score': f"Low reputation score within the network ({val}).",
        'digits_in_username': f"High entropy in username ({val} digits detected).",
        'digit_ratio_username': f"High numeric concentration in username ({val}).",
        'username_length': f"Unusual username length ({val} characters).",
        'verified': "Account lacks verification credentials.",
        'has_url': "Presence of an external URL paired with other suspicious traits.",
        'has_profile_pic': "Account lacks a valid profile picture (default avatar).",
        'bio_length': f"Short or absent bio description ({val} characters).",
        'post_count': f"Unusual total post count ({val}).",
        'following': f"Mass-following behavior detected ({val} accounts followed).",
        'followers': f"Anomalous follower count ({val})."
    }
    
    return translations.get(feature_name, f"Anomalous metric detected in {feature_name} ({val}).")


def predict(features_dict: dict, platform: str = "auto") -> dict:
    """
    Standalone multi-platform prediction function.
    Accepts a feature dictionary and platform string ("twitter", "meta", or "auto").
    Returns risk_score, classification label, confidence, and SHAP explainability reasons.
    """
    # Auto-detect platform if requested
    if platform == "auto":
        if 'has_profile_pic' in features_dict or 'bio_length' in features_dict:
            platform = "meta"
        else:
            platform = "twitter"

    platform = platform.lower()
    if platform not in models or models[platform] is None:
        return {"error": f"Model artifact for platform '{platform}' is not loaded."}

    model = models[platform]
    explainer = explainers.get(platform)

    expected_features = META_EXPECTED_FEATURES if platform == "meta" else TWITTER_EXPECTED_FEATURES

    # 1. Prepare Data & Clean Missing/Inf Values
    df_input = pd.DataFrame([features_dict])
    for col in expected_features:
        if col not in df_input.columns:
            df_input[col] = 0
        else:
            df_input[col] = pd.to_numeric(df_input[col], errors='coerce').fillna(0)

    df_input = df_input[expected_features]
    df_input = df_input.replace([np.inf, -np.inf], np.nan).fillna(0)
    X_ready = df_input.to_numpy()

    # 2. Prediction Probabilities
    proba = model.predict_proba(X_ready)[0]
    risk_score_raw = proba[1]
    risk_score = round(risk_score_raw * 100, 2)

    # 3. Categorization Thresholds
    if risk_score_raw < 0.30:
        classification = "REAL"
    elif risk_score_raw <= 0.70:
        classification = "SUSPICIOUS"
    else:
        classification = "FAKE"

    # 4. Generate SHAP Reasons
    reasons = []
    if explainer is not None:
        try:
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

            for impact in feature_impacts:
                if impact['shap_value'] > 0 and len(reasons) < 3:
                    english_reason = translate_shap_to_english(
                        impact['feature'], 
                        impact['original_value'], 
                        impact['shap_value']
                    )
                    reasons.append(english_reason)
        except Exception as e:
            pass

    if classification == "REAL":
        reasons = ["Account metrics align with standard human baseline behavior."]

    return {
        "platform": platform,
        "risk_score": risk_score,
        "classification": classification,
        "confidence": round(risk_score_raw if classification == "FAKE" else (1 - risk_score_raw), 2),
        "reasons": reasons
    }