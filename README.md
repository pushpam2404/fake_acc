# 🛡️ Cross-Platform Fake Account & Bot Detection Engine

A machine learning system for detecting fake, bot, and automated accounts across social media platforms (**Twitter/X** and **Meta/Instagram/Facebook**).

---

## 📌 Project Overview

This repository provides an end-to-end pipeline to standardize raw multi-source social media datasets, engineer behavioral and structural features, train high-performance ML models (Random Forest, XGBoost, MLP Neural Networks) for both **Twitter** and **Meta/Instagram**, and generate human-readable decision explanations using SHAP feature attribution.

### Key Milestones Achieved
- **Dual-Platform Pipeline Architecture**: Standardized raw datasets across Twitter (Cresci, Satish, Genuine/Fake) and Meta platforms (LIMFADD, Instagram, Facebook profiles).
- **Toxic Dataset Identification & Purge**: Filtered out incomplete/corrupted datasets (`bot_detection_data.csv`) lacking structural metadata.
- **High-Signal Feature Engineering**: Engineered bounded reputation scores, username entropy ratios, activity density, account age, and behavioral ratios.
- **Benchmark Performance**: Achieved **90.19% Accuracy (85.72% F1-Score)** on Twitter and **97.02% Accuracy (97.29% F1-Score)** on Meta/Instagram.
- **Unified SHAP Explainability Engine**: Built dual-platform inference engine ([`models/explain.py`](file:///Users/pushpam/Desktop/fake-account-detection/models/explain.py)) returning risk scores (0-100%), 3-class categories (`REAL`, `SUSPICIOUS`, `FAKE`), and English reason translations.

---

## 📁 Repository Structure

```text
fake-account-detection/
├── data/
│   ├── raw/                # Original raw CSVs (Cresci, Nidhekshaa, Satish, IMFAD, etc.)
│   └── processed/          # Cleaned master matrices (twitter_master.csv, meta_master.csv)
├── feature_extractor/
│   ├── build_twitter.py    # Twitter pipeline: label mapping, feature engineering, sanitization
│   └── build_meta.py       # Meta/IG pipeline: profile pic, bio length, follower ratios
├── models/
│   ├── experiments/
│   │   ├── compare_twitter_models.py  # Gladiator Arena benchmark script (Twitter)
│   │   ├── compare_meta_models.py     # Gladiator Arena benchmark script (Meta/IG)
│   │   ├── tune_xgboost.py            # Hyperparameter search for Twitter XGBoost
│   │   └── tune_xgboost_meta.py       # Hyperparameter search for Meta XGBoost
│   ├── saved/              # Trained Twitter & Meta models (*.pkl) & scalers (*_scaler.pkl)
│   ├── explain.py          # Unified dual-platform inference & SHAP explainability engine
│   └── results.md          # Combined Twitter & Meta benchmark leaderboards
├── notebooks/
│   ├── inspect_raw.py      # Exploratory raw dataset diagnostic inspector
│   └── test_predict.py     # Inference & explainability stress test suite (Twitter & Meta)
├── .gitignore              # Repository git exclusion rules
└── README.md               # Project documentation
```

---

## ⚙️ Feature Engineering Schemas

The feature extraction engines process raw account data into platform-specific schemas:

### Twitter Schema ([`feature_extractor/build_twitter.py`](file:///Users/pushpam/Desktop/fake-account-detection/feature_extractor/build_twitter.py))
`followers`, `following`, `post_count`, `verified`, `description_length`, `account_age_days`, `follower_following_ratio`, `reputation_score`, `username_length`, `digits_in_username`, `digit_ratio_username`, `has_url`, `posts_per_day`.

### Meta/Instagram Schema ([`feature_extractor/build_meta.py`](file:///Users/pushpam/Desktop/fake-account-detection/feature_extractor/build_meta.py))
`followers`, `following`, `post_count`, `has_profile_pic`, `bio_length`, `follower_following_ratio`, `reputation_score`.

---

## 📊 Benchmark Leaderboards

### 🐦 Twitter Platform (64,919 Accounts)
| Rank | Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Train Time (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **Random Forest (Winner)** | **90.19%** | **88.35%** | **83.24%** | **85.72%** | 0.87s |
| 🥈 | **XGBoost Classifier** | **90.03%** | **87.65%** | **83.59%** | **85.57%** | 0.17s |
| 🥉 | **Neural Network (MLP)** | 87.37% | 80.96% | 84.07% | 82.49% | 21.97s |
| 4 | Logistic Regression | 65.04% | 51.24% | 24.77% | 33.40% | 0.02s |

### 📸 Meta / Instagram Platform (36,383 Accounts)
| Rank | Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Train Time (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **Random Forest (Winner)** | **97.02%** | **97.52%** | **97.06%** | **97.29%** | 0.30s |
| 🥈 | **XGBoost Classifier** | **96.83%** | **97.18%** | **97.06%** | **97.12%** | 0.14s |
| 🥉 | **Neural Network (MLP)** | 96.21% | 97.48% | 95.58% | 96.52% | 4.12s |
| 4 | Logistic Regression | 84.20% | 86.25% | 84.83% | 85.53% | 0.01s |

---

## 🚀 How to Run

### 1. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy scikit-learn xgboost joblib shap
```

### 2. Build Processed Master Datasets
```bash
python feature_extractor/build_twitter.py
python feature_extractor/build_meta.py
```

### 3. Train & Benchmark Models
```bash
# Twitter Model Gladiator Arena
python models/experiments/compare_twitter_models.py

# Meta/Instagram Model Gladiator Arena
python models/experiments/compare_meta_models.py
```

### 4. Hyperparameter Tuning
```bash
# Tune Twitter XGBoost
python models/experiments/tune_xgboost.py

# Tune Meta XGBoost
python models/experiments/tune_xgboost_meta.py
```

### 5. Run Dual-Platform Inference & Explainability Test Suite
```bash
python notebooks/test_predict.py
```
