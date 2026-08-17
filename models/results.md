# Model Evaluation & Benchmark Leaderboards

This document tracks the performance evolution of our classification models across platforms (**Twitter/X** and **Meta/Instagram**). The primary evaluation metric is **F1-Score** on the "Fake" (`1`) class to balance catching automated/spam accounts (Recall) without falsely flagging genuine human users (Precision).

---

## 1. Twitter Platform Leaderboard (Enhanced Schemas & Ensembling)

Evaluated on unseen test split (**12,984 Twitter accounts** from a clean master dataset of **64,919 unique accounts**):

| Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Train Time (s) | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 🥇 **Soft-Voting Ensemble (RF+XGB+ET)** | **90.47%** | **88.50%** | **83.96%** | **86.17%** | **2.81s** | **VICTOR.** Soft probability voting reduces individual model variance. |
| 🥈 **Random Forest** | 90.16% | 88.15% | 83.41% | 85.72% | 1.12s | High accuracy on tabular metadata features. |
| 🥉 **XGBoost (Tuned)** | 90.04% | 87.47% | 83.87% | 85.63% | 0.21s | Excellent tree explainability via SHAP. |
| 4 **Extra Trees Classifier** | 89.99% | 88.48% | 82.43% | 85.35% | 0.42s | Extremely randomized decision boundaries. |
| 5 **Neural Network (MLP)** | 87.82% | 85.16% | 79.43% | 82.19% | 26.89s | Heavier computation with non-linear hidden layers. |
| 6 **Logistic Regression (Baseline)** | **81.64%** | **76.78%** | **68.96%** | **72.66%** | **0.02s** | **Huge jump from 65% -> 81.6%** thanks to `np.log1p` features! |

---

## 2. Meta / Instagram Platform Leaderboard (Enhanced Schemas & Ensembling)

Evaluated on unseen test split (**7,277 Meta accounts** from a clean master dataset of **36,383 unique accounts**):

| Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Train Time (s) | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 🥇 **Soft-Voting Ensemble (RF+XGB+ET)** | **97.05%** | **97.57%** | **97.06%** | **97.31%** | **1.63s** | **VICTOR.** Combines tree predictions for maximum precision. |
| 🥈 **Random Forest** | 97.02% | 97.59% | 96.98% | 97.28% | 0.37s | Dominates on bio completeness & default avatar signals. |
| 🥉 **Extra Trees Classifier** | 96.91% | 97.68% | 96.68% | 97.18% | 0.15s | High precision on structural profile metadata. |
| 4 **XGBoost (Tuned)** | 96.87% | 97.23% | 97.08% | 97.15% | 0.15s | Primary production choice for instant SHAP explainability. |
| 5 **Neural Network (MLP)** | 96.26% | 95.92% | 97.36% | 96.63% | 4.35s | High recall, slightly higher computational overhead. |
| 6 **Logistic Regression (Baseline)** | **89.05%** | **90.21%** | **89.87%** | **90.04%** | **0.02s** | **Jump from 84% -> 89%** using log feature scaling. |

---

## 3. Key Takeaways & Performance Gains

1. **Ensemble Modeling (Soft Voting)**:
   - Combining probabilities from Random Forest, XGBoost, and Extra Trees reduced classification noise, pushing Twitter F1-Score to **86.17%** and Meta F1-Score to **97.31%**.

2. **Logarithmic Feature Scaling (`np.log1p`)**:
   - Applying log scale transformations to heavy-tailed counts (`followers`, `following`, `post_count`) enabled linear models like Logistic Regression to jump **16.6% on Twitter** (from 65% to 81.6%) and **4.8% on Meta** (from 84% to 89%).

3. **Production Deployment Choice**:
   - **`twitter_best_model.pkl` & `meta_best_model.pkl`**: Soft-Voting Ensemble champion artifacts for maximum predictive accuracy.
   - **`twitter_xgboost_tuned.pkl` & `meta_xgboost_tuned.pkl`**: Tuned XGBoost artifacts used for live REST inference when real-time **SHAP natural-language explanations** are required.