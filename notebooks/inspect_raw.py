"""
================================================================================
RAW DATASET EXPLORATION & DIAGNOSTIC INSPECTOR (inspect_raw.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This utility script recursively scans the `data/raw/` directory to inspect every 
downloaded dataset CSV file. It outputs dataset shape, column names, data types, 
and automatically guesses which column represents the ground truth classification target 
(`is_fake` / `bot` label). This diagnostic output prevents developer blind guessing when 
configuring column mapping dictionaries in the feature extraction pipelines.

TECHNICAL SPECIFICATIONS & DOMAIN LOGIC:
1. Recursive Traversal & Tokenizing Safety:
   - Traverses nested subdirectories within `data/raw/` using `glob.glob`.
   - Reads 5,000-row samples per CSV using `pd.read_csv(nrows=5000, on_bad_lines='warn')` 
     to evaluate dataset contents rapidly without memory overflow or parsing crashes.

2. Target Header Deduction & Label Distribution:
   - Uses fuzzy string substring matching (`LABEL_HINTS`) to locate ground truth columns.
   - Evaluates label value distributions (`value_counts()`) to detect class balance.
   - Ignores known corrupt, non-structural, or redundant datasets (`satish/fake_social_media.csv`).
"""

import glob
import os
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

LABEL_HINTS = ["fake", "bot", "label", "is_fake", "class", "target", "type"]


def standardize_labels(file_path: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes dataset targets by extracting labels from filenames 
    and mapping multi-class strings to binary integers.
    """
    # FIX 1: LIMFADD Multi-class to Binary Mapping
    if 'Labels' in df.columns:
        label_map = {'Real': 0, 'Spam': 1, 'Scam': 1, 'Bot': 1}
        df['is_fake'] = df['Labels'].map(label_map)
        df = df.drop(columns=['Labels'])
        return df

    # Check if any column name contains our hint words as a substring
    has_label = any(any(hint in col.lower() for hint in LABEL_HINTS) for col in df.columns)
    
    # FIX 2: Dynamic Filename Label Extraction
    if not has_label:
        # Extract ONLY the filename (e.g., 'genuine_users.csv') so the parent folder doesn't poison the logic
        filename = os.path.basename(file_path).lower()
        
        # Check Fake/Spam first
        if any(kw in filename for kw in ['fake', 'spam', 'fuser', 'bot']):
            df['is_fake'] = 1
        # Check Genuine/Real second
        elif any(kw in filename for kw in ['genuine', 'real', 'user']):
            df['is_fake'] = 0
            
    return df


def guess_label_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if any(hint in col.lower() for hint in LABEL_HINTS):
            return col
    return None


def main():
    csv_paths = sorted(glob.glob(os.path.join(RAW_DIR, "**", "*.csv"), recursive=True))

    if not csv_paths:
        print(f"No CSVs found under {RAW_DIR}. Did the kaggle downloads run?")
        return

    for path in csv_paths:
        # Prevent crashes from macOS treating folders as CSVs
        if not os.path.isfile(path):
            continue 
            
        rel = os.path.relpath(path, RAW_DIR)
        
        # Skip mathematically broken or perfectly redundant datasets
        if "satish/fake_social_media.csv" in rel or "twitter_profiles_original.csv" in rel:
            continue
            
        print("=" * 80)
        print(rel)
        try:
            # Using on_bad_lines='warn' to prevent tokenizing crashes
            df = pd.read_csv(path, nrows=5000, on_bad_lines='warn') 
        except Exception as e:
            print(f"  FAILED TO READ: {e}")
            continue
            
        # Apply our label standardization before inspection
        df = standardize_labels(path, df)

        print(f"  shape (sampled): {df.shape}")
        print(f"  columns: {list(df.columns)}")
        guess = guess_label_column(df)
        print(f"  guessed label column: {guess}")
        if guess:
            print(f"  label value counts:\n{df[guess].value_counts().to_string()}")
        print()


if __name__ == "__main__":
    main()