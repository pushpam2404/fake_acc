"""
================================================================================
DUAL-PLATFORM EXPLAINABILITY & PREDICTION INFERENCE ENGINE (explain.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This script acts as the unified prediction and explainability engine for both 
Twitter/X and Meta/Instagram social media platforms. It dynamically loads the 
corresponding platform model binaries (Twitter Soft-Voting Ensemble / Tuned XGBoost 
and Meta Soft-Voting Ensemble / Tuned XGBoost) and initializes SHAP (SHapley Additive 
exPlanations) TreeExplainers. When given an account's feature dictionary, it determines 
the platform, computes derived logarithmic scale & ratio features, enforces schema 
alignment, calculates a continuous risk score (0-100%), assigns a 3-tier classification 
label (`REAL`, `SUSPICIOUS`, or `FAKE`), and translates tree decision impacts into 
human-readable English reasons explaining flagged traits.

TECHNICAL SPECIFICATIONS & DOMAIN LOGIC:
1. Multi-Platform Artifact Loading:
   - Twitter Artifact: Prefers `twitter_xgboost_tuned.pkl`, falls back to `twitter_best_model.pkl`.
   - Meta Artifact: Prefers `meta_xgboost_tuned.pkl`, falls back to `meta_best_model.pkl`.
   - Initializes SHAP `TreeExplainer` instances for model feature attribution.

2. Dynamic Feature Engineering & Schema Preprocessing:
   - Derives `log_followers`, `log_following`, `log_post_count` via `np.log1p`.
   - Computes dual-way ratios (`follower_following_ratio`, `following_followers_ratio`, `reputation_score`).
   - Extracts entropy ratios (`digit_ratio_username`, `consonant_ratio_username`) and completeness metrics.
   - Enforces canonical feature ordering per platform (`TWITTER_EXPECTED_FEATURES` vs `META_EXPECTED_FEATURES`).

3. Risk Scoring & 3-Class Categorization Thresholds:
   - Risk Score: `risk_score = round(raw_probability * 100, 2)`.
   - Categorization: `REAL` (<30%), `SUSPICIOUS` (30-70%), `FAKE` (>70%).
"""

import os
import joblib
import pandas as pd
import numpy as np
import shap

SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved")

# Canonical feature ordering per platform
TWITTER_EXPECTED_FEATURES = [
    'followers', 'following', 'post_count', 
    'log_followers', 'log_following', 'log_post_count',
    'verified', 'description_length', 'account_age_days', 
    'follower_following_ratio', 'following_followers_ratio', 'reputation_score', 
    'username_length', 'digits_in_username', 'digit_ratio_username', 'consonant_ratio_username',
    'has_url', 'posts_per_day'
]

META_EXPECTED_FEATURES = [
    'followers', 'following', 'post_count', 
    'log_followers', 'log_following', 'log_post_count',
    'has_profile_pic', 'bio_length', 'profile_pic_bio_score', 
    'follower_following_ratio', 'following_followers_ratio', 'reputation_score'
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
        if hasattr(models['twitter'], 'predict_proba'):
            try:
                explainers['twitter'] = shap.TreeExplainer(models['twitter'])
            except Exception:
                explainers['twitter'] = None
except Exception as e:
    print(f"WARNING: Failed to load Twitter model artifact. {e}")

try:
    if os.path.exists(META_MODEL_PATH):
        models['meta'] = joblib.load(META_MODEL_PATH)
        if hasattr(models['meta'], 'predict_proba'):
            try:
                explainers['meta'] = shap.TreeExplainer(models['meta'])
            except Exception:
                explainers['meta'] = None
except Exception as e:
    print(f"WARNING: Failed to load Meta model artifact. {e}")


def preprocess_features(df_input: pd.DataFrame, platform: str) -> pd.DataFrame:
    for col in ['followers', 'following', 'post_count']:
        if col not in df_input.columns:
            df_input[col] = 0
        else:
            df_input[col] = pd.to_numeric(df_input[col], errors='coerce').fillna(0)

    df_input['log_followers'] = np.log1p(np.maximum(0, df_input['followers']))
    df_input['log_following'] = np.log1p(np.maximum(0, df_input['following']))
    df_input['log_post_count'] = np.log1p(np.maximum(0, df_input['post_count']))

    df_input['follower_following_ratio'] = (df_input['followers'] / (df_input['following'] + 1)).replace([np.inf, -np.inf], 0).fillna(0)
    df_input['following_followers_ratio'] = (df_input['following'] / (df_input['followers'] + 1)).replace([np.inf, -np.inf], 0).fillna(0)
    df_input['reputation_score'] = (df_input['followers'] / (df_input['followers'] + df_input['following'] + 1)).replace([np.inf, -np.inf], 0).fillna(0)

    if platform == "twitter":
        if 'verified' not in df_input.columns:
            df_input['verified'] = 0
        if 'description_length' not in df_input.columns:
            df_input['description_length'] = 0
        if 'account_age_days' not in df_input.columns:
            df_input['account_age_days'] = -1
        if 'has_url' not in df_input.columns:
            df_input['has_url'] = 0

        df_input['posts_per_day'] = (df_input['post_count'] / (df_input['account_age_days'].replace(-1, 0) + 1)).replace([np.inf, -np.inf], 0).fillna(0)

        if 'username' in df_input.columns:
            uname_str = df_input['username'].fillna('').astype(str)
            df_input['username_length'] = uname_str.str.len()
            df_input['digits_in_username'] = uname_str.str.count(r'\d').fillna(0).astype(int)
            df_input['digit_ratio_username'] = (df_input['digits_in_username'] / (df_input['username_length'] + 1e-5)).fillna(0)
            consonants = uname_str.str.count(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]').fillna(0)
            df_input['consonant_ratio_username'] = (consonants / (df_input['username_length'] + 1e-5)).fillna(0)
        else:
            for c in ['username_length', 'digits_in_username', 'digit_ratio_username', 'consonant_ratio_username']:
                if c not in df_input.columns:
                    df_input[c] = 0.0

    elif platform == "meta":
        if 'has_profile_pic' not in df_input.columns:
            df_input['has_profile_pic'] = 0
        if 'bio_length' not in df_input.columns:
            df_input['bio_length'] = 0
        df_input['profile_pic_bio_score'] = df_input['has_profile_pic'] + (df_input['bio_length'] > 0).astype(int)

    return df_input


def translate_shap_to_english(feature_name: str, feature_value, shap_value) -> str:
    val = round(feature_value, 2)
    
    translations = {
        'follower_following_ratio': f"Suspicious follower-to-following ratio ({val}).",
        'following_followers_ratio': f"Aggressive mass-following ratio relative to followers ({val}).",
        'posts_per_day': f"Abnormal activity density ({val} posts per day).",
        'account_age_days': f"Account age metric is anomalous ({val} days old).",
        'reputation_score': f"Low reputation score within the network ({val}).",
        'digits_in_username': f"High entropy in username ({val} digits detected).",
        'digit_ratio_username': f"High numeric concentration in username ({val}).",
        'consonant_ratio_username': f"Unpronounceable consonant pattern in username ({val}).",
        'username_length': f"Unusual username length ({val} characters).",
        'verified': "Account lacks verification credentials.",
        'has_url': "Presence of an external URL paired with suspicious traits.",
        'has_profile_pic': "Account lacks a valid profile picture (default avatar).",
        'bio_length': f"Short or absent bio description ({val} characters).",
        'profile_pic_bio_score': "Incomplete profile credentials (no avatar or bio).",
        'post_count': f"Unusual total post count ({val}).",
        'following': f"Mass-following behavior detected ({val} accounts followed).",
        'followers': f"Anomalous follower count ({val})."
    }
    
    return translations.get(feature_name, f"Anomalous metric detected in {feature_name} ({val}).")


def predict(features_dict: dict, platform: str = "auto") -> dict:
    if platform == "auto":
        if 'has_profile_pic' in features_dict or 'bio_length' in features_dict or 'profile_pic_bio_score' in features_dict:
            platform = "meta"
        else:
            platform = "twitter"

    platform = platform.lower()
    if platform not in models or models[platform] is None:
        return {"error": f"Model artifact for platform '{platform}' is not loaded."}

    model = models[platform]
    explainer = explainers.get(platform)

    expected_features = META_EXPECTED_FEATURES if platform == "meta" else TWITTER_EXPECTED_FEATURES

    # 1. Prepare & Preprocess Data
    df_input = pd.DataFrame([features_dict])
    df_input = preprocess_features(df_input, platform)

    for col in expected_features:
        if col not in df_input.columns:
            df_input[col] = 0

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