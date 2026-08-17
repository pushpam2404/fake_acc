"""
================================================================================
TWITTER FEATURE EXTRACTION & DATA PIPELINE ENGINE (build_twitter.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This script scans through all raw dataset CSV files stored in the `data/raw/` 
directory, cleans up inconsistent column headers and missing labels, and 
transforms heterogeneous Twitter datasets into a standardized, tabular matrix 
ready for machine learning models. It filters out incompatible/corrupted 
datasets and extracts high-signal behavioral features (like follower-following 
ratios, username digit entropy, and activity density). The final output is saved 
as a deduplicated dataset at `data/processed/twitter_master.csv`.

TECHNICAL SPECIFICATIONS & DOMAIN LOGIC:
1. Target Label Standardization:
   - Identifies ground truth classification columns across multi-source datasets.
   - Maps multi-class categorical targets ('bot', 'fake', 'spam', 'human', 'real') 
     to binary numerical target labels: `1` for Fake/Bot and `0` for Real.
   - Uses dynamic filename heuristic keyword matching when explicit label columns 
     are absent in dataset files.

2. Schema Alignment & Normalization:
   - Remaps diverse schema column names (e.g., 'screen_name' -> 'username', 
     'statuses_count' -> 'post_count', 'friends_count' -> 'following') to a 
     unified canonical feature schema.
   - Filters out toxic datasets (e.g., `bot_detection_data.csv`) that lack 
     essential structural metadata (such as `following` count).

3. Feature Engineering Math:
   - Follower-Following Ratio: `followers / (following + 1)` (smoothed against division by zero).
   - Bounded Reputation Score: `followers / (followers + following + 1)` bounded in `[0, 1]`.
   - Username Entropy & Character Analysis: Counts string length, digit count, 
     and digit ratio (`digits / (length + 1e-5)`), capturing randomly generated bot hashes.
   - Activity Density: `post_count / (account_age_days + 1)` representing posts per day.
   - Temporal & Boolean Flags: Extracts `description_length`, `account_age_days` 
     from UTC timestamps, `verified` status, and URL presence flags.
"""

import os
import glob
import pandas as pd
import numpy as np
import warnings

warnings.simplefilter(action='ignore', category=pd.errors.DtypeWarning)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

LABEL_HINTS = ["fake", "bot", "label", "is_fake", "class", "target", "type"]

TWITTER_MAPPING = {
    'screen_name': 'username',
    'statuses_count': 'post_count',
    'followers_count': 'followers',
    'friends_count': 'following',
    'favourites_count': 'likes_given',
}

TWITTER_CORE_FEATURES = [
    'username', 'followers', 'following', 'post_count', 
    'verified', 'is_fake', 'description_length', 'account_age_days',
    'follower_following_ratio', 'reputation_score',
    'username_length', 'digits_in_username', 'digit_ratio_username',
    'has_url', 'posts_per_day'
]

def standardize_labels(file_path: str, df: pd.DataFrame) -> pd.DataFrame:
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
                mapping = {'bot': 1, 'human': 0, 'fake': 1, 'real': 0, 'spam': 1}
                df['is_fake'] = df[col].astype(str).str.lower().map(mapping).fillna(0).astype(int)
            else:
                df['is_fake'] = df[col].fillna(0).astype(int)
            if col != 'is_fake':
                df = df.drop(columns=[col])
            break
            
    return df

def engineer_twitter_features(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Base Text Lengths
    if 'description' in df.columns:
        df['description_length'] = df['description'].fillna('').astype(str).str.len()
    else:
        df['description_length'] = 0

    # 2. Account Age
    if 'account_age_days' not in df.columns and 'created_at' in df.columns:
        parsed_dates = pd.to_datetime(df['created_at'], format='mixed', errors='coerce', utc=True)
        max_date = parsed_dates.max()
        df['account_age_days'] = (max_date - parsed_dates).dt.days
        df['account_age_days'] = df['account_age_days'].fillna(df['account_age_days'].median())
    elif 'account_age_days' not in df.columns:
        df['account_age_days'] = -1 

    # 3. Boolean flags
    df['verified'] = df['verified'].astype(bool).astype(int) if 'verified' in df.columns else 0
    df['has_url'] = df['url'].notna().astype(int) if 'url' in df.columns else 0

    # 4. Safe Numeric Handling (Fixes KeyError)
    for col in ['followers', 'following', 'post_count']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0

    # 5. Behavioral Ratios
    df['follower_following_ratio'] = df['followers'] / (df['following'] + 1)
    df['follower_following_ratio'] = df['follower_following_ratio'].replace([np.inf, -np.inf], 0)

    df['reputation_score'] = df['followers'] / (df['followers'] + df['following'] + 1)

    df['posts_per_day'] = df['post_count'] / (df['account_age_days'].replace(-1, 0) + 1)

    # 6. Username Entropy
    if 'username' in df.columns:
        uname_str = df['username'].astype(str)
        df['username_length'] = uname_str.str.len()
        df['digits_in_username'] = uname_str.str.count(r'\d').fillna(0).astype(int)
        df['digit_ratio_username'] = df['digits_in_username'] / (df['username_length'] + 1e-5)
    else:
        df['username_length'] = 0
        df['digits_in_username'] = 0
        df['digit_ratio_username'] = 0.0

    return df

def main():
    csv_paths = sorted(glob.glob(os.path.join(RAW_DIR, "**", "*.csv"), recursive=True))
    twitter_dataframes = []

    print("Starting Clean Twitter Pipeline Build...\n" + "="*40)
    
    for path in csv_paths:
        filename = os.path.basename(path)
        
        if not os.path.isfile(path) or any(x in filename for x in [
            "fake_social_media.csv", 
            "original.csv", 
            "bot_detection_data.csv"
        ]):
            continue
            
        df = pd.read_csv(path, on_bad_lines='warn')
        df.columns = df.columns.str.lower().str.strip()
        
        df = standardize_labels(path, df)
        df = df.rename(columns=TWITTER_MAPPING)
        df = df.loc[:, ~df.columns.duplicated(keep='first')]
        
        # Route Twitter files (must have username or statuses_count)
        if 'username' in df.columns or 'post_count' in df.columns:
            df = engineer_twitter_features(df)
            
            missing_cols = [c for c in TWITTER_CORE_FEATURES if c not in df.columns]
            if not missing_cols:
                final_df = df[TWITTER_CORE_FEATURES].copy()
                twitter_dataframes.append(final_df)
                print(f"[+] INCLUDED: {filename} (Rows: {len(final_df)})")
            else:
                print(f"[-] SKIPPED:  {filename} (Missing: {missing_cols})")

    if twitter_dataframes:
        twitter_master = pd.concat(twitter_dataframes, ignore_index=True)
        twitter_master = twitter_master.drop_duplicates(subset=['username'])
        
        out_path = os.path.join(PROCESSED_DIR, "twitter_master.csv")
        twitter_master.to_csv(out_path, index=False)
        
        print("\n" + "="*40)
        print(f"PIPELINE COMPLETE -> Saved: {out_path}")
        print(f"Clean Unique Accounts: {len(twitter_master)}")
        print("\nClass Distribution:")
        print(twitter_master['is_fake'].value_counts())

if __name__ == "__main__":
    main()