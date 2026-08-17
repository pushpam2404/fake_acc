"""
================================================================================
META / INSTAGRAM FEATURE EXTRACTION PIPELINE ENGINE (build_meta.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This script processes raw CSV files containing Instagram and Facebook account 
metadata from `data/raw/`. It standardizes inconsistent column headers across 
different Meta platform datasets, extracts structural profile features (like 
profile picture flags, bio lengths, post counts, and follower-following ratios), 
and compiles them into a clean, deduplicated matrix saved at 
`data/processed/meta_master.csv`.

TECHNICAL SPECIFICATIONS & DOMAIN LOGIC:
1. Target Label Standardization:
   - Maps multi-class strings ('real', 'spam', 'scam', 'bot') to binary target 
     `is_fake` (`1`=Fake, `0`=Real).
   - Employs filename keyword matching ('fake', 'spam', 'genuine', 'real') when 
     explicit target headers are missing in raw CSV files.

2. Meta/Instagram Schema Mapping:
   - Remaps platform-specific headers ('#followers', '#follows', '#posts', 
     'description length', 'profile pic') into unified schema fields: 
     `followers`, `following`, `post_count`, `bio_length`, `has_profile_pic`.

3. Feature Engineering & Type Sanitization:
   - Profile Pic Indicator: Maps boolean/string flags ('Y', 'N', 'yes', 'no', 
     '1', '0', 'true', 'false') cleanly to `1` or `0`.
   - Bio Length: Measures string character length of profile bio text.
   - Follower-Following Ratio: Computes `followers / (following + 1)` and caps 
     infinite/NaN values to `0`.
   - Routing Logic: Isolates Meta/IG schemas from Twitter schemas by checking for 
     Meta specific column signatures (`bio_length`, `has_profile_pic`, `friend_count`).
"""

import os
import glob
import pandas as pd
import numpy as np
import warnings

warnings.simplefilter(action='ignore', category=pd.errors.DtypeWarning)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# ---------------------------------------------------------
# 1. CONSTANTS & MAPPINGS
# ---------------------------------------------------------
LABEL_HINTS = ["fake", "bot", "label", "is_fake", "class", "target", "type"]

# Standardize incoming raw Meta/IG columns to our backend schema
META_MAPPING = {
    '#followers': 'followers',
    'followers_count': 'followers',
    '#follows': 'following',
    'following_count': 'following',
    '#posts': 'post_count',
    'posts_count': 'post_count',
    'posts': 'post_count',
    'description length': 'bio_length',
    'profile pic': 'has_profile_pic',
    'profile_pic': 'has_profile_pic',
    'profile picture': 'has_profile_pic'
}

# The mandatory schema for the Meta model
META_CORE_FEATURES = [
    'followers', 'following', 'post_count', 
    'has_profile_pic', 'bio_length', 'is_fake',
    'follower_following_ratio', 'reputation_score'
]
# ---------------------------------------------------------
# 2. STANDARDIZATION LOGIC (Identical to Twitter)
# ---------------------------------------------------------
def standardize_labels(file_path: str, df: pd.DataFrame) -> pd.DataFrame:
    if 'labels' in df.columns:
        df['is_fake'] = df['labels'].astype(str).str.lower().map({'real': 0, 'spam': 1, 'scam': 1, 'bot': 1})
        return df.drop(columns=['labels'])

    has_label = any(any(hint in col for hint in LABEL_HINTS) for col in df.columns)
    
    if not has_label:
        filename = os.path.basename(file_path).lower()
        if any(kw in filename for kw in ['fake', 'spam', 'fuser', 'bot']):
            df['is_fake'] = 1
        elif any(kw in filename for kw in ['genuine', 'real', 'user']):
            df['is_fake'] = 0

    for col in df.columns:
        if col in ['label', 'fake', 'bot label', 'account_type', 'is_fake']:
            if df[col].dtype == 'object' or df[col].dtype == 'string':
                df['is_fake'] = df[col].astype(str).str.lower().map({'bot': 1, 'human': 0, 'fake': 1, 'real': 0, 'spam': 1}).fillna(0).astype(int)
            else:
                df['is_fake'] = df[col].fillna(0).astype(int)
            if col != 'is_fake':
                df = df.drop(columns=[col])
            break
    return df

# ---------------------------------------------------------
# 3. FEATURE ENGINEERING
# ---------------------------------------------------------
def engineer_meta_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Dynamically creates derived features for Instagram/Facebook constraints.
    """
    if 'bio' in df.columns:
        df['bio_length'] = df['bio'].fillna('').astype(str).str.len()
    elif 'bio_length' not in df.columns:
        df['bio_length'] = 0

    if 'has_profile_pic' in df.columns:
        s = df['has_profile_pic'].astype(str).str.lower().str.strip()
        df['has_profile_pic'] = s.map({
            '1': 1, '1.0': 1, 'true': 1, 'y': 1, 'yes': 1,
            '0': 0, '0.0': 0, 'false': 0, 'n': 0, 'no': 0
        }).fillna(0).astype(int)
    else:
        df['has_profile_pic'] = 0

    for col in ['followers', 'following', 'post_count']:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    for col in META_CORE_FEATURES:
        if col in df.columns and col not in ['follower_following_ratio', 'reputation_score']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # ---------------------------------------------------------
    # NEW DERIVED BEHAVIORAL FEATURES
    # ---------------------------------------------------------
    # 1. The Ratio: Safe division
    df['follower_following_ratio'] = df['followers'] / (df['following'] + 1)
    df['follower_following_ratio'] = df['follower_following_ratio'].replace([np.inf, -np.inf], 0).fillna(0)

    # 2. Reputation Score: Bounded strictly in [0, 1]
    df['reputation_score'] = df['followers'] / (df['followers'] + df['following'] + 1)
    df['reputation_score'] = df['reputation_score'].replace([np.inf, -np.inf], 0).fillna(0)

    return df

# ---------------------------------------------------------
# 4. PIPELINE ENGINE
# ---------------------------------------------------------
def main():
    csv_paths = sorted(glob.glob(os.path.join(RAW_DIR, "**", "*.csv"), recursive=True))
    meta_dataframes = []

    print(f"Starting Meta/IG Pipeline Build...\n" + "="*40)
    
    for path in csv_paths:
        if not os.path.isfile(path) or "fake_social_media.csv" in path or "original.csv" in path:
            continue
            
        filename = os.path.basename(path)
        df = pd.read_csv(path, on_bad_lines='warn')
        df.columns = df.columns.str.lower().str.strip()
        
        df = standardize_labels(path, df)
        df = df.rename(columns=META_MAPPING)
        df = df.loc[:, ~df.columns.duplicated(keep='first')]
        
        # Meta Routing Logic: Catch FB/IG sets, avoid Twitter sets
        # If it has a 'friends_count' (FB) or 'bio_length' or 'has_profile_pic' or 'followers_following_ratio'
        is_meta = any(col in df.columns for col in ['bio_length', 'has_profile_pic', 'friend_count', 'followers_following_ratio'])
        is_twitter = 'statuses_count' in df.columns or 'screen_name' in df.columns or 'tweet' in df.columns
        
        if is_meta and not is_twitter:
            df = engineer_meta_features(df)
            
            missing_cols = [c for c in META_CORE_FEATURES if c not in df.columns]
            if not missing_cols:
                final_df = df[META_CORE_FEATURES].copy()
                meta_dataframes.append(final_df)
                print(f"[+] INCLUDED: {filename} (Rows: {len(final_df)})")
            else:
                print(f"[-] SKIPPED:  {filename} (Missing Core Cols: {missing_cols})")

    if meta_dataframes:
        print("\nConcatenating matrices...")
        meta_master = pd.concat(meta_dataframes, ignore_index=True)
        
        # Meta lacks usernames, drop exact duplicate rows instead
        initial_rows = len(meta_master)
        meta_master = meta_master.drop_duplicates()
        dropped_rows = initial_rows - len(meta_master)
        
        out_path = os.path.join(PROCESSED_DIR, "meta_master.csv")
        meta_master.to_csv(out_path, index=False)
        
        print("="*40)
        print(f"PIPELINE COMPLETE")
        print(f"Saved: {out_path}")
        print(f"Total Unique Rows: {len(meta_master)}")
        print(f"Exact Duplicates Removed: {dropped_rows}")
        print("\nClass Distribution:")
        print(meta_master['is_fake'].value_counts())
    else:
        print("CRITICAL ERROR: No datasets passed the Meta validation checks.")

if __name__ == "__main__":
    main()