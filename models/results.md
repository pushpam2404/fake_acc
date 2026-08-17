# Model Evaluation Results

This document tracks the performance evolution of our classification models. The primary metric for success is **F1-Score** on the "Fake" (1) class, as we must balance the system's ability to catch bots (Recall) without falsely banning genuine human users (Precision).

## The Data Poisoning Hurdle
Initial models (V1) were trained on a raw, concatenated dataset of 105,000 rows. Performance hit a hard mathematical ceiling (Max F1: ~0.67) because tweet-level datasets lacking account metadata forced massive `0` imputations. 

We purged the incompatible datasets and engineered high-signal behavioral features (e.g., `follower_following_ratio`, `posts_per_day`, `digit_ratio_username`), yielding a clean dataset of ~51,000 accounts.

## Performance Leaderboard

| Model Iteration | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression (V1 Baseline)** | 59.72% | 51.64% | 29.17% | 37.28% | Heavy data scaling required; linear logic failed to map complex bot behaviors. |
| **Random Forest (V1 Untuned)** | 74.23% | 75.98% | 54.41% | 63.41% | Severe class imbalance caused the model to ignore 45% of actual bots to maintain overall accuracy. |
| **Neural Network (MLP) (V1)** | 72.12% | 64.63% | 70.82% | 67.59% | Best V1 model, but computationally expensive and lacked explainability (black box). |
| **XGBoost (V2 Cleaned & Tuned)** | **90.00%** | **84.00%** | **88.00%** | **86.00%** | **VICTOR.** Imbalance corrected via `scale_pos_weight`. Cleaned behavioral features unlocked deep decision boundaries. |

### Key Takeaways
1. **Accuracy is a Trap:** V1 Random Forest had 74% accuracy but a miserable 54% Recall. It was flipping a coin on bots. 
2. **Data Quality > Model Complexity:** Purging the `bot_detection_data.csv` poison and engineering `posts_per_day` caused a 23% spike in our F1-score without changing the underlying algorithm.
3. **Chosen Architecture:** **Tuned XGBoost**. It delivers maximum predictive power while retaining tree-based explainability (via SHAP) to justify bans to end-users.