"""
================================================================================
DUAL-PLATFORM PREDICTION & EXPLAINABILITY ENGINE (predict.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This module serves as the primary inference engine for detecting fake accounts 
across Twitter/X and Meta/Instagram platforms. It loads trained XGBoost models, 
enforces strict schema alignment (13 features for Twitter, 7 for Meta), calculates 
a continuous risk score (0-100%), assigns a 3-tier classification label (`REAL`, 
`SUSPICIOUS`, or `FAKE`), and uses SHAP to translate decision tree feature impacts 
into human-readable English reasons explaining why an account was flagged.

TECHNICAL SPECIFICATIONS:
1. Canonical Schema Alignment:
   - Twitter Features (13): followers, following, post_count, verified, description_length,
     account_age_days, follower_following_ratio, reputation_score, username_length,
     digits_in_username, digit_ratio_username, has_url, posts_per_day.
   - Meta Features (7): followers, following, post_count, has_profile_pic, bio_length,
     follower_following_ratio, reputation_score.

2. Auto-Derived Ratios:
   - Automatically computes missing derived metrics (`follower_following_ratio`, 
     `reputation_score`, `posts_per_day`, `digit_ratio_username`) if raw inputs are passed.
"""

import os
import joblib
import pandas as pd
import numpy as np
import shap

SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved")

# Clean Canonical Schemas
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

TWITTER_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "twitter_xgboost_tuned.pkl")
META_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "meta_xgboost_tuned.pkl")

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


def preprocess_features(df_input: pd.DataFrame, platform: str) -> pd.DataFrame:
    # Ensure numeric types
    for col in ['followers', 'following', 'post_count']:
        if col not in df_input.columns:
            df_input[col] = 0
        else:
            df_input[col] = pd.to_numeric(df_input[col], errors='coerce').fillna(0)

    # Compute behavioral ratios if missing
    if 'follower_following_ratio' not in df_input.columns:
        df_input['follower_following_ratio'] = df_input['followers'] / (df_input['following'] + 1)
    df_input['follower_following_ratio'] = df_input['follower_following_ratio'].replace([np.inf, -np.inf], 0).fillna(0)

    if 'reputation_score' not in df_input.columns:
        df_input['reputation_score'] = df_input['followers'] / (df_input['followers'] + df_input['following'] + 1)
    df_input['reputation_score'] = df_input['reputation_score'].replace([np.inf, -np.inf], 0).fillna(0)

    if platform == "twitter":
        if 'verified' not in df_input.columns:
            df_input['verified'] = 0
        if 'description_length' not in df_input.columns:
            df_input['description_length'] = 0
        if 'account_age_days' not in df_input.columns:
            df_input['account_age_days'] = -1
        if 'has_url' not in df_input.columns:
            df_input['has_url'] = 0

        if 'posts_per_day' not in df_input.columns:
            df_input['posts_per_day'] = df_input['post_count'] / (df_input['account_age_days'].replace(-1, 0) + 1)
        df_input['posts_per_day'] = df_input['posts_per_day'].replace([np.inf, -np.inf], 0).fillna(0)

        if 'username' in df_input.columns:
            uname_str = df_input['username'].fillna('').astype(str)
            df_input['username_length'] = uname_str.str.len()
            df_input['digits_in_username'] = uname_str.str.count(r'\d').fillna(0).astype(int)
            df_input['digit_ratio_username'] = (df_input['digits_in_username'] / (df_input['username_length'] + 1e-5)).fillna(0)
        else:
            for c in ['username_length', 'digits_in_username', 'digit_ratio_username']:
                if c not in df_input.columns:
                    df_input[c] = 0.0

    elif platform == "meta":
        if 'has_profile_pic' not in df_input.columns:
            df_input['has_profile_pic'] = 0
        if 'bio_length' not in df_input.columns:
            df_input['bio_length'] = 0

    return df_input


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
        'has_url': "Presence of an external URL paired with suspicious traits.",
        'has_profile_pic': "Account lacks a valid profile picture (default avatar).",
        'bio_length': f"Short or absent bio description ({val} characters).",
        'post_count': f"Unusual total post count ({val}).",
        'following': f"Mass-following behavior detected ({val} accounts followed).",
        'followers': f"Anomalous follower count ({val})."
    }
    
    return translations.get(feature_name, f"Anomalous metric detected in {feature_name} ({val}).")


def predict(features_dict: dict, platform: str = "auto") -> dict:
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

    # 1. Prepare & Preprocess Input Data
    df_input = pd.DataFrame([features_dict])
    df_input = preprocess_features(df_input, platform)

    for col in expected_features:
        if col not in df_input.columns:
            df_input[col] = 0

    df_input = df_input[expected_features]
    df_input = df_input.replace([np.inf, -np.inf], np.nan).fillna(0)
    X_ready = df_input.to_numpy()

    # 2. Extract Predictions & Probabilities
    proba = model.predict_proba(X_ready)[0]
    risk_score_raw = proba[1]
    risk_score = round(risk_score_raw * 100, 2)

    # 3. Apply 3-Class Categorization Thresholds
    if risk_score_raw < 0.30:
        classification = "REAL"
    elif risk_score_raw <= 0.70:
        classification = "SUSPICIOUS"
    else:
        classification = "FAKE"

    # 4. Generate SHAP Explainability Reasons
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
        except Exception:
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
