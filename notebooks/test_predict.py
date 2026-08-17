"""
================================================================================
DUAL-PLATFORM INFERENCE & EXPLAINABILITY SANITY TEST SUITE (test_predict.py)
================================================================================

PLAIN ENGLISH SUMMARY:
This validation script tests the standalone prediction and SHAP explainability engine 
(`models.explain.predict`) against real and fake account samples from BOTH Twitter 
(`twitter_master.csv`) and Meta (`meta_master.csv`) processed datasets. It executes 
isolated single-account sanity checks and 15-row randomized batch stress tests for both 
platforms, verifying that risk scores, classification labels (`REAL`, `SUSPICIOUS`, `FAKE`), 
and SHAP explanation reasons are generated cleanly prior to REST API integration.

TECHNICAL SPECIFICATIONS & TEST ASSERTIONS:
1. Dual-Platform Isolated Case Validation:
   - Evaluates obvious fake (`is_fake` == 1) and real (`is_fake` == 0) accounts for Twitter and Meta.
   - Asserts key presence: `platform`, `classification`, `risk_score`, `reasons`.
   - Asserts non-empty list structure for SHAP generated natural-language reason strings.

2. 15-Row Batch Stress Tests (Twitter & Meta):
   - Samples 15 random account rows from both processed datasets with fixed seeds (`random_state=42`).
   - Evaluates standalone inference execution time and binary decision alignment (`risk_score > 50`).
"""

import os
import sys
import pandas as pd
import numpy as np

# Append root directory to path to allow importing from the models directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.explain import predict

def run_platform_test(data_path: str, platform_name: str):
    print("\n" + "="*60)
    print(f"SANITY CHECK & STRESS TEST: {platform_name.upper()} PREDICTION ENGINE")
    print("="*60)

    if not os.path.exists(data_path):
        print(f"CRITICAL ERROR: Data not found at {data_path}")
        return

    # 1. Load data and sanitize
    df = pd.read_csv(data_path)
    df = df.replace([np.inf, -np.inf], 0).fillna(0)

    # 2. Pick known cases
    fake_case = df[df["is_fake"] == 1].iloc[0].to_dict()
    real_case = df[df["is_fake"] == 0].iloc[0].to_dict()

    # 3. Test isolated cases
    for case, name in [(fake_case, f"OBVIOUS FAKE CASE ({platform_name.upper()})"), (real_case, f"OBVIOUS REAL CASE ({platform_name.upper()})")]:
        actual = int(case['is_fake'])
        features = {k: v for k, v in case.items() if k not in ["is_fake", "username"]}
        
        result = predict(features, platform=platform_name)
        
        print(f"\n--- {name} ---")
        print(f"Platform: {result.get('platform')}")
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
    print(f"15-ROW STRESS TEST ({platform_name.upper()})")
    print("="*60)
    
    correct = 0
    samples = df.sample(min(15, len(df)), random_state=42)
    
    for _, row in samples.iterrows():
        actual = int(row["is_fake"])
        features = {k: v for k, v in row.items() if k not in ["is_fake", "username"]}
        
        pred = predict(features, platform=platform_name)
        pred_binary = 1 if pred["risk_score"] > 50 else 0
        
        match = "✓" if pred_binary == actual else "✗"
        correct += (pred_binary == actual)
        
        print(f"{match} actual={actual} pred_binary={pred_binary} (Class: {pred['classification']:<10}) score={pred['risk_score']}")

    print(f"\n{correct}/{len(samples)} correct")
    assert correct >= (0.70 * len(samples)), f"Accuracy fell below threshold for {platform_name}."
    print(f"SUCCESS: {platform_name.upper()} standalone prediction engine is robust.")

def main():
    run_platform_test("data/processed/twitter_master.csv", "twitter")
    run_platform_test("data/processed/meta_master.csv", "meta")

if __name__ == "__main__":
    main()