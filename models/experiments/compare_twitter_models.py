"""
================================================================================
MODEL GLADIATOR ARENA & EVALUATION BENCHMARK (compare_twitter_models.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This script acts as a competitive benchmark suite ("Gladiator Arena") that loads 
the processed Twitter dataset, trains four distinct machine learning model architectures 
(Logistic Regression, Random Forest, XGBoost, and MLP Neural Network) on an 80/20 
train-test split, evaluates their performance across standard metrics (Accuracy, 
Precision, Recall, F1-Score), and automatically serializes the winning model and 
feature scaler to `models/saved/`.

TECHNICAL SPECIFICATIONS & DOMAIN LOGIC:
1. Feature Isolation & Data Sanitization:
   - Drops string identifiers (`username`) and isolates target ground truth (`is_fake`).
   - Implements a sanitization block replacing infinite values (`inf`, `-inf`) with `NaN` 
     and imputing missing values with `0`.

2. Data Splitting & Feature Scaling:
   - Applies stratified 80/20 train-test splitting (`train_test_split(stratify=y)`) to 
     preserve positive class distribution between training and test subsets.
   - Fits a `StandardScaler` on training features only to prevent data leakage from test data.
   - Serializes the fitted scaler to `models/saved/twitter_scaler.pkl`.

3. Model Ecosystem & Evaluation Metrics:
   - Baseline Linear: `LogisticRegression(max_iter=1000)`
   - Ensemble Trees: `RandomForestClassifier(n_estimators=100, n_jobs=-1)`
   - Gradient Boosting: `XGBClassifier(eval_metric='logloss', n_jobs=-1)`
   - Deep Learning: `MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500)`
   - Metrics Evaluated: Accuracy, Precision (Fake class), Recall (Fake class), F1-Score.
   - Selection Criterion: Automatically selects the top model based on F1-Score (to balance 
     catching fake accounts without false bans) and saves it to `models/saved/twitter_best_model.pkl`.
"""

import os
import time
import pandas as pd
import numpy as np
import joblib

# Scikit-Learn & XGBoost Ecosystem
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier

# Path Configuration
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "saved")
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

def run_model_arena():
    print("="*60)
    print("INITIALIZING MODEL GLADIATOR ARENA (TWITTER DATASET)")
    print("="*60)

    data_path = os.path.join(PROCESSED_DIR, "twitter_master.csv")
    if not os.path.exists(data_path):
        print(f"CRITICAL ERROR: Data not found at {data_path}")
        return

    df = pd.read_csv(data_path)
    
    # 1. Feature Isolation
    X = df.drop(columns=['username', 'is_fake'])
    y = df['is_fake']

    # --- SANITIZATION BLOCK: Catch NaNs and Infinities ---
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(0)
    # -----------------------------------------------------

    # 2. Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Feature Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    scaler_path = os.path.join(SAVED_MODELS_DIR, "twitter_scaler.pkl")
    joblib.dump(scaler, scaler_path)

    # 4. Define the Combatants
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    xgb = XGBClassifier(eval_metric='logloss', random_state=42, n_jobs=-1)
    et = ExtraTreesClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    ensemble = VotingClassifier(
        estimators=[('rf', rf), ('xgb', xgb), ('et', et)],
        voting='soft',
        n_jobs=-1
    )

    models = {
        "Logistic Regression (Baseline)": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": rf,
        "XGBoost": xgb,
        "Extra Trees": et,
        "Soft-Voting Ensemble (RF+XGB+ET)": ensemble,
        "Neural Network (MLP)": MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)
    }

    results = []
    best_model_name = None
    best_model_obj = None
    best_f1 = 0

    print(f"Training on {len(X_train)} rows. Testing on {len(X_test)} rows.\n")
    
    for name, model in models.items():
        print(f"Training {name}...")
        start_time = time.time()
        
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        train_time = time.time() - start_time
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        results.append({
            "Model": name,
            "Accuracy": acc,
            "Precision (Fake)": prec,
            "Recall (Fake)": rec,
            "F1-Score": f1,
            "Train Time (s)": round(train_time, 2)
        })

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model_obj = model

    # 5. Generate Leaderboard
    print("\n" + "="*60)
    print("MODEL LEADERBOARD")
    print("="*60)
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by="F1-Score", ascending=False).reset_index(drop=True)
    
    for col in ["Accuracy", "Precision (Fake)", "Recall (Fake)", "F1-Score"]:
        results_df[col] = (results_df[col] * 100).round(2).astype(str) + "%"
        
    print(results_df.to_string(index=False))

    # 6. Save the Victor
    print("\n" + "="*60)
    winner_path = os.path.join(SAVED_MODELS_DIR, "twitter_best_model.pkl")
    joblib.dump(best_model_obj, winner_path)
    print(f"WINNER SAVED: {best_model_name}")
    print(f"Location: {winner_path}")
    print("="*60)

if __name__ == "__main__":
    run_model_arena()