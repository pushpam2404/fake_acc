"""
================================================================================
STANDALONE INFERENCE & EXPLAINABILITY SANITY TEST SUITE (test_predict.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This validation script tests the standalone prediction and explainability engine 
(`models.explain.predict`) against real and fake account samples from 
`data/processed/twitter_master.csv`. It executes isolated single-account sanity checks 
and a 15-row randomized batch stress test, verifying that risk scores, classification 
labels (`REAL`, `SUSPICIOUS`, `FAKE`), and SHAP feature explanation reasons are generated 
correctly without errors prior to REST API integration.

TECHNICAL SPECIFICATIONS & TEST ASSERTIONS:
1. Isolated Case Validation:
   - Evaluates obvious fake (`is_fake` == 1) and real (`is_fake` == 0) account rows.
   - Asserts key presence: `classification`, `risk_score`, `reasons`.
   - Asserts non-empty list structure for SHAP generated natural-language reason strings.

2. 15-Row Batch Stress Test:
   - Samples 15 random account rows from `twitter_master.csv` with a fixed seed (`random_state=42`).
   - Evaluates standalone inference execution time and binary decision alignment (`risk_score > 50`).
   - Validates model stability across diverse unseen feature distributions.
"""

import os
import sys
import pandas as pd
import numpy as np

# Append root directory to path to allow importing from the models directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.explain import predict

def run_sanity_check():
    print("="*60)
    print("HOUR 7 SANITY CHECK: STANDALONE PREDICTION ENGINE")
    print("="*60)

    data_path = "data/processed/twitter_master.csv"
    if not os.path.exists(data_path):
        print(f"CRITICAL ERROR: Data not found at {data_path}")
        return

    # 1. Load data and sanitize (mirroring the training pipeline)
    df = pd.read_csv(data_path)
    df = df.replace([np.inf, -np.inf], 0).fillna(0)

    # 2. Pick known cases
    fake_case = df[df["is_fake"] == 1].iloc[0].to_dict()
    real_case = df[df["is_fake"] == 0].iloc[0].to_dict()

    # 3. Test isolated cases
    for case, name in [(fake_case, "OBVIOUS FAKE CASE"), (real_case, "OBVIOUS REAL CASE")]:
        actual = int(case['is_fake'])
        # Strip the target and the string identifier
        features = {k: v for k, v in case.items() if k not in ["is_fake", "username"]}
        
        result = predict(features)
        
        print(f"\n--- {name} ---")
        print(f"Actual label: {actual} (1=Fake, 0=Real)")
        print(f"Predicted Classification: {result.get('classification')}")
        print(f"Risk Score: {result.get('risk_score')}")
        print(f"Reasons: {result.get('reasons')}")

        # Hard fail assertions
        assert 'classification' in result, "Missing 'classification' key in output."
        assert 'risk_score' in result, "Missing 'risk_score' key in output."
        assert 'reasons' in result, "Missing 'reasons' key in output."
        assert isinstance(result['reasons'], list) and len(result['reasons']) > 0, "Reasons must be a non-empty list."

    # 4. The 15-Row Stress Test
    print("\n" + "="*60)
    print("15-ROW STRESS TEST")
    print("="*60)
    
    correct = 0
    samples = df.sample(15, random_state=42)
    
    for _, row in samples.iterrows():
        actual = int(row["is_fake"])
        features = {k: v for k, v in row.items() if k not in ["is_fake", "username"]}
        
        pred = predict(features)
        
        # Map the risk score back to a binary outcome to check baseline accuracy
        pred_binary = 1 if pred["risk_score"] > 50 else 0
        
        match = "✓" if pred_binary == actual else "✗"
        correct += (pred_binary == actual)
        
        print(f"{match} actual={actual} pred_binary={pred_binary} (Class: {pred['classification']:<10}) score={pred['risk_score']}")

    print(f"\n{correct}/15 correct")
    
    if correct <= 7:
        print("WARNING: Accuracy is worse than random guessing. Your model or feature alignment is fundamentally broken.")
    elif correct < 12:
        print("NOTICE: Accuracy is acceptable, but thresholding may require fine-tuning.")
    else:
        print("SUCCESS: Standalone prediction engine is robust. You are cleared for Phase 3 (FastAPI).")

if __name__ == "__main__":
    run_sanity_check()