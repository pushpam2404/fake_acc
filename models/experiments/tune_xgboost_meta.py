"""
================================================================================
META / INSTAGRAM XGBOOST HYPERPARAMETER TUNING ENGINE (tune_xgboost_meta.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This script performs hyperparameter optimization over XGBoost for the Meta platform 
dataset (`data/processed/meta_master.csv`). It uses 3-fold cross-validation (`RandomizedSearchCV`) 
to discover the optimal decision tree depth, learning rate, and feature colsampling settings, 
saving the tuned estimator checkpoint to `models/saved/meta_xgboost_tuned.pkl`.

TECHNICAL SPECIFICATIONS & DOMAIN LOGIC:
1. Dynamic Imbalance Modifier (`scale_pos_weight`):
   - Computes `spw = neg_class_count / pos_class_count` dynamically based on Meta label distribution.
2. RandomizedSearchCV Configuration:
   - Search Space: `max_depth` [5, 7, 10, 15], `learning_rate` [0.01, 0.05, 0.1], `n_estimators` [200, 400, 600].
   - Optimization Scoring: `f1`.
3. Model Serialization:
   - Exports trained tuned pipeline estimator to `models/saved/meta_xgboost_tuned.pkl`.
"""

import os
import time
import pandas as pd
import numpy as np
import joblib
import warnings
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

warnings.filterwarnings(action='ignore', category=UserWarning)

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "saved")
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

def tune_meta_xgboost():
    print("="*60)
    print("INITIATING META / INSTAGRAM XGBOOST HYPERPARAMETER TUNING")
    print("="*60)

    data_path = os.path.join(PROCESSED_DIR, "meta_master.csv")
    if not os.path.exists(data_path):
        print(f"CRITICAL ERROR: Data not found at {data_path}")
        return

    df = pd.read_csv(data_path)
    
    X = df.drop(columns=['is_fake'])
    y = df['is_fake']

    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    neg_class_count = (y == 0).sum()
    pos_class_count = (y == 1).sum()
    spw = round(neg_class_count / pos_class_count, 2)
    print(f"Dataset Imbalance Detected. Injecting scale_pos_weight: {spw}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    param_dist = {
        'max_depth': [5, 7, 10, 15],
        'learning_rate': [0.01, 0.05, 0.1],
        'n_estimators': [200, 400, 600],
        'subsample': [0.7, 0.9, 1.0],
        'colsample_bytree': [0.7, 0.9, 1.0],
        'gamma': [0, 0.1, 0.5],
        'scale_pos_weight': [spw, spw * 1.5]
    }

    xgb_base = XGBClassifier(eval_metric='logloss', random_state=42, n_jobs=-1)
    
    random_search = RandomizedSearchCV(
        estimator=xgb_base,
        param_distributions=param_dist,
        n_iter=15,
        scoring='f1',
        cv=3,
        verbose=1,
        n_jobs=-1,
        random_state=42
    )

    print(f"\nStarting search across {len(X_train)} Meta accounts...")
    start_time = time.time()
    random_search.fit(X_train, y_train)
    print(f"\nSearch Complete in {round((time.time() - start_time)/60, 2)} minutes.")

    best_xgb = random_search.best_estimator_
    
    print("\n" + "="*60)
    print("WINNING HYPERPARAMETERS (META):")
    for key, val in random_search.best_params_.items():
        print(f"{key:>20}: {val}")
    print("="*60)

    y_pred = best_xgb.predict(X_test)
    print("\nTUNED META MODEL PERFORMANCE ON UNSEEN DATA:")
    print(classification_report(y_test, y_pred, target_names=['Real (0)', 'Fake (1)']))
    
    winner_path = os.path.join(SAVED_MODELS_DIR, "meta_xgboost_tuned.pkl")
    joblib.dump(best_xgb, winner_path)
    print(f"\n[+] Saved tuned Meta model to: {winner_path}")

if __name__ == "__main__":
    tune_meta_xgboost()
