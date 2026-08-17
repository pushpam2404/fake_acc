# Model Evaluation & Benchmark Leaderboards

This document tracks the performance evolution of our classification models across platforms (**Twitter/X** and **Meta/Instagram**). The primary evaluation metric is **F1-Score** on the "Fake" (`1`) class to balance catching automated/spam accounts (Recall) without falsely flagging genuine human users (Precision).

---

## 1. Twitter Platform Leaderboard

Evaluated on unseen test split (**12,984 Twitter accounts** from a clean master dataset of **64,919 unique accounts**):

| Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Train Time (s) | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Random Forest (Winner)** | **90.19%** | **88.35%** | **83.24%** | **85.72%** | **0.87s** | **VICTOR.** Dominates speed and accuracy on tabular features. |
| **XGBoost (Tuned)** | **90.03%** | **87.65%** | **83.59%** | **85.57%** | **0.17s** | Excellent tree explainability via SHAP. |
| **Neural Network (MLP)** | 87.37% | 80.96% | 84.07% | 82.49% | 21.97s | Computationally heavier, black-box logic. |
| Logistic Regression (Baseline) | 65.04% | 51.24% | 24.77% | 33.40% | 0.02s | Linear boundaries fail on complex behavioral ratios. |

---

## 2. Meta / Instagram Platform Leaderboard

Evaluated on unseen test split (**7,277 Meta accounts** from a clean master dataset of **36,383 unique accounts**):

| Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Train Time (s) | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Random Forest (Winner)** | **97.02%** | **97.52%** | **97.06%** | **97.29%** | **0.30s** | **VICTOR.** Exceptional separation on IG bio & profile pic features. |
| **XGBoost (Tuned)** | **96.83%** | **97.18%** | **97.06%** | **97.12%** | **0.14s** | High precision and near-instant inference speed. |
| **Neural Network (MLP)** | 96.21% | 97.48% | 95.58% | 96.52% | 4.12s | Strong performance, but higher memory footprint. |
| Logistic Regression (Baseline) | 84.20% | 86.25% | 84.83% | 85.53% | 0.01s | Solid baseline performance on structural IG signals. |

---

## 3. Key Takeaways & Architecture Selection

1. **Dual-Platform Artifact Storage**:
   - **Twitter Artifacts**: `models/saved/twitter_best_model.pkl`, `models/saved/twitter_scaler.pkl`, `models/saved/twitter_xgboost_tuned.pkl`.
   - **Meta Artifacts**: `models/saved/meta_best_model.pkl`, `models/saved/meta_scaler.pkl`, `models/saved/meta_xgboost_tuned.pkl`.

2. **Data Quality over Model Complexity**:
   - Purging missing-metadata tweet datasets (`bot_detection_data.csv`) and engineering bounded ratios (`reputation_score`, `follower_following_ratio`) unlocked 90%+ performance across platforms.

3. **Inference & Explainability Engine (`models/explain.py`)**:
   - Automatically routes payloads between Twitter and Meta estimators, providing continuous risk scores (0-100%), 3-class classifications (`REAL`, `SUSPICIOUS`, `FAKE`), and SHAP feature translations.