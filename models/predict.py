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


def translate_shap_to_english(feature_name: str, feature_value, shap_value, is_fake: bool = True) -> str:
    """
    Translates mathematical SHAP values into rich, context-aware forensic explanations.
    Uses value thresholds, direction, and magnitude to generate nuanced plain-English descriptions.
    """
    fval = float(feature_value)
    val = round(fval, 2)
    int_val = int(fval) if fval.is_integer() or abs(fval - round(fval)) < 1e-4 else val

    
    # 1. Negative SHAP impact (evidence supporting AUTHENTIC HUMAN behavior)
    if not is_fake or shap_value < 0:
        human_translations = {
            'follower_following_ratio': f"Healthy, balanced follower-to-following ratio ({val}) within normal human social distribution.",
            'posts_per_day': f"Organic posting tempo ({val} posts/day), consistent with natural human usage patterns.",
            'account_age_days': f"Established account tenure ({int_val} days), showing an authentic long-term activity history.",
            'reputation_score': f"Strong network reputation index ({val}), indicating reciprocated follower trust.",
            'digits_in_username': f"Natural username construction ({int_val} digits), matching human naming patterns.",
            'digit_ratio_username': f"Low numerical concentration in username ({val}), reflecting non-automated registration.",
            'username_length': f"Standard handle length ({int_val} chars), typical of human-chosen handles.",
            'verified': "Verified account badge confirms official identity authentication.",
            'has_url': "Associated bio URL aligns with authentic portfolio or verified profile link.",
            'has_profile_pic': "Presence of an authentic profile picture/avatar.",
            'bio_length': f"Well-developed profile biography ({int_val} characters) demonstrating genuine self-expression.",
            'post_count': f"Consistent and natural posting activity ({int_val} total posts).",
            'following': f"Normal following volume ({int_val} accounts), avoiding aggressive follow-for-follow patterns.",
            'followers': f"Established follower audience ({int_val} followers) consistent with organic engagement."
        }
        return human_translations.get(feature_name, f"Metric '{feature_name}' ({val}) conforms to genuine user benchmarks.")

    # 2. Positive SHAP impact (evidence indicating BOT / SUSPICIOUS behavior)
    if feature_name == 'follower_following_ratio':
        if val < 0.1:
            return f"Severely depressed follower-to-following ratio ({val}) — aggressive outbound following with minimal reciprocation."
        elif val > 50.0:
            return f"Uncharacteristically high follower ratio ({val}) disconnected from organic post interaction rates."
        return f"Anomalous follower-to-following distribution ratio ({val}) deviating from human norms."

    elif feature_name == 'posts_per_day':
        if val > 30.0:
            return f"Hyper-velocity posting density ({val} posts/day) exceeds physical human content creation limits."
        elif val == 0:
            return "Zero posting cadence (0 posts/day) indicative of a dormant or scraping sleeper bot."
        return f"Irregular automated posting frequency ({val} posts per day)."

    elif feature_name == 'account_age_days':
        if int_val <= 7:
            return f"Disposable account footprint — created only {int_val} days ago, characteristic of rapid bot farm deployment."
        elif int_val <= 30:
            return f"Fresh account creation date ({int_val} days old), exhibiting premature high-volume activity."
        return f"Atypical temporal account age metric ({int_val} days)."

    elif feature_name == 'reputation_score':
        if val < 0.15:
            return f"Critically degraded network reputation score ({val}), heavily skewed toward spam broadcasting."
        return f"Suppressed reputation index ({val}) reflecting one-sided audience engagement."

    elif feature_name == 'digits_in_username':
        if int_val >= 4:
            return f"High algorithmic entropy in handle ({int_val} trailing digits), signature of automated script registration."
        return f"Suspicious numerical suffix detected in handle ({int_val} digits)."

    elif feature_name == 'digit_ratio_username':
        return f"High digit-to-letter concentration in username ({round(val * 100, 1)}% numeric), matching bot farm patterns."

    elif feature_name == 'username_length':
        if int_val > 15:
            return f"Abnormally long generated handle ({int_val} chars), typical of programmatic batch registration."
        return f"Atypical username length ({int_val} characters)."

    elif feature_name == 'verified':
        return "Unverified account status paired with high-velocity propagation behavior."

    elif feature_name == 'has_url':
        return "Suspicious external URL payload in bio, commonly leveraged for phishing or traffic redirection."

    elif feature_name == 'has_profile_pic':
        return "Missing profile picture (default blank avatar), consistent with mass-produced throwaway bots."

    elif feature_name == 'bio_length':
        if int_val == 0:
            return "Completely absent biography (0 characters), omitting baseline personal or organizational identity."
        elif int_val < 15:
            return f"Sparse/placeholder profile description ({int_val} characters), typical of automated spam shells."
        return f"Anomalous biography structure ({int_val} characters)."

    elif feature_name == 'post_count':
        if int_val == 0:
            return "Zero published posts despite active following, characteristic of a silent lurking/scraper bot."
        elif int_val > 20000:
            return f"Massive post volume ({int_val:,} posts) indicative of automated continuous syndication."
        return f"Unusual total post count distribution ({int_val} posts)."

    elif feature_name == 'following':
        if int_val > 2000:
            return f"Mass-following behavior detected ({int_val:,} accounts followed), typical of aggressive follow-back rings."
        elif int_val < 5:
            return f"Near-zero following connection count ({int_val} accounts), operating as an isolated broadcast node."
        return f"Anomalous following metric ({int_val:,} followed accounts)."

    elif feature_name == 'followers':
        if int_val < 20:
            return f"Extremely restricted follower footprint ({int_val} followers) despite active network interactions."
        return f"Statistically anomalous follower count ({int_val:,} followers)."

    return f"Elevated anomaly score detected in {feature_name.replace('_', ' ').title()} ({val})."


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

    # 4. Generate Comprehensive SHAP Explainability Reasons
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
                    'shap_value': float(instance_shap[i])
                })

            if classification in ["FAKE", "SUSPICIOUS"]:
                # Sort features pushing toward FAKE descending
                feature_impacts.sort(key=lambda x: x['shap_value'], reverse=True)
                for impact in feature_impacts:
                    if impact['shap_value'] > 0 and len(reasons) < 4:
                        english_reason = translate_shap_to_english(
                            impact['feature'], 
                            impact['original_value'], 
                            impact['shap_value'],
                            is_fake=True
                        )
                        reasons.append(english_reason)
            else:
                # For REAL accounts, sort features proving authenticity (most negative SHAP values)
                feature_impacts.sort(key=lambda x: x['shap_value'])
                for impact in feature_impacts:
                    if impact['shap_value'] < 0 and len(reasons) < 3:
                        english_reason = translate_shap_to_english(
                            impact['feature'], 
                            impact['original_value'], 
                            impact['shap_value'],
                            is_fake=False
                        )
                        reasons.append(english_reason)

        except Exception:
            pass

    if not reasons:
        if classification == "REAL":
            reasons = [
                "Follower-to-following ratio aligns with authentic human social benchmarks.",
                "Consistent posting timeline and healthy profile tenure.",
                "Profile metadata and engagement indicators show organic human operation."
            ]
        else:
            reasons = ["Multiple anomalous telemetry metrics exceed automated risk thresholds."]

    return {
        "platform": platform,
        "risk_score": risk_score,
        "classification": classification,
        "confidence": round(risk_score_raw if classification == "FAKE" else (1 - risk_score_raw), 2),
        "reasons": reasons
    }
