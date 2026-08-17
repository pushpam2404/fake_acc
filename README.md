# 🛡️ Fake Account & Bot Detection Engine

A machine learning system for detecting fake, bot, and automated accounts across social media platforms (**Twitter/X** and **Meta/Instagram/Facebook**).

---

## 📌 Project Overview

This repository provides an end-to-end pipeline to standardize raw multi-source social media datasets, engineer behavioral and structural features, train high-performance ML models (Random Forest, XGBoost, MLP Neural Networks), and generate human-readable decision explanations using SHAP feature attribution.

### Key Milestones Achieved
- **Multi-Source Dataset Standardization**: Ingested and unified raw datasets (Cresci 2017, Genuine/Fake users, Nidhekshaa, Satish, IMFAD) into cleaned master matrices.
- **Toxic Dataset Identification & Purge**: Filtered out corrupted/incomplete datasets (`bot_detection_data.csv`) that lacked structural metadata (e.g., missing `following` count).
- **High-Signal Feature Engineering**: Engineered bounded reputation scores, username entropy ratios, activity density, account age, and behavioral ratios.
- **Model Benchmark Jump**: Boosted Twitter detection **F1-Score from ~63% to 85.72%** and overall accuracy to **90.19%**.
- **Explainable AI Integration**: Built standalone inference and SHAP explainability engine ([`models/explain.py`](file:///Users/pushpam/Desktop/fake-account-detection/models/explain.py)) returning risk scores (0-100%), 3-class categories (`REAL`, `SUSPICIOUS`, `FAKE`), and English reason translations.

---

## 📁 Repository Structure

```text
fake-account-detection/
├── data/
│   ├── raw/                # Original raw CSVs (Cresci, Nidhekshaa, Satish, etc.)
│   └── processed/          # Cleaned master matrices (twitter_master.csv, meta_master.csv)
├── feature_extractor/
│   ├── build_twitter.py    # Twitter pipeline: label mapping, feature engineering, sanitization
│   └── build_meta.py       # Meta/IG pipeline: profile pic, bio length, follower ratios
├── models/
│   ├── experiments/
│   │   ├── compare_twitter_models.py  # Gladiator Arena benchmark script
│   │   └── tune_xgboost.py            # Hyperparameter search using RandomizedSearchCV
│   ├── saved/              # Trained models (*.pkl) & scalers (*_scaler.pkl)
│   ├── explain.py          # Standalone inference & SHAP explainability translation engine
│   └── results.md          # Technical evaluation log & performance post-mortem
├── notebooks/
│   ├── inspect_raw.py      # Exploratory raw dataset diagnostic inspector
│   └── test_predict.py     # Inference & explainability stress test suite
├── .gitignore              # Repository git exclusion rules
└── README.md               # Project documentation
```

---

## ⚙️ Feature Engineering Highlights

The feature extraction engines ([`feature_extractor/build_twitter.py`](file:///Users/pushpam/Desktop/fake-account-detection/feature_extractor/build_twitter.py) and [`feature_extractor/build_meta.py`](file:///Users/pushpam/Desktop/fake-account-detection/feature_extractor/build_meta.py)) process raw account data into the following schema:

| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `followers` | Numeric | Count of account followers |
| `following` | Numeric | Count of accounts followed |
| `post_count` | Numeric | Total tweets/posts published |
| `verified` | Binary | Account verification status (`1`=Verified, `0`=Unverified) |
| `description_length` | Numeric | Character length of profile bio/description |
| `account_age_days` | Numeric | Account age calculated from creation timestamp |
| `follower_following_ratio` | Ratio | `followers / (following + 1)` (Zero-division safe) |
| `reputation_score` | Ratio | `followers / (followers + following + 1)` bounded in `[0, 1]` |
| `username_length` | Numeric | Character length of screen name / username |
| `digits_in_username` | Numeric | Count of numerical digits in username |
| `digit_ratio_username` | Ratio | `digits_in_username / (username_length + 1e-5)` (Detects hash-like bot handles) |
| `has_url` | Binary | Profile contains external link (`1`=Yes, `0`=No) |
| `posts_per_day` | Ratio | Activity density: `post_count / (account_age_days + 1)` |
| `is_fake` | Target | Ground truth label (`0`=Real, `1`=Fake/Bot) |

---

## 📊 Model Gladiator Arena Benchmarks

Evaluated on unseen test split (**12,984 Twitter accounts** from a clean master dataset of **64,919 unique accounts**):

| Rank | Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Train Time (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **Random Forest (Winner)** | **90.19%** | **88.35%** | **83.24%** | **85.72%** | 0.87s |
| 🥈 | **XGBoost Classifier** | **90.03%** | **87.65%** | **83.59%** | **85.57%** | 0.17s |
| 🥉 | **Neural Network (MLP)** | 87.37% | 80.96% | 84.07% | 82.49% | 21.97s |
| 4 | Logistic Regression | 65.04% | 51.24% | 24.77% | 33.40% | 0.02s |

---

## 🚀 How to Run

### 1. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy scikit-learn xgboost joblib shap
```

### 2. Build Processed Master Datasets
Run the feature extraction pipelines to convert raw datasets in `data/raw/` into processed master matrices:
```bash
python feature_extractor/build_twitter.py
python feature_extractor/build_meta.py
```

### 3. Train & Compare Models
Run the Model Gladiator Arena to evaluate baseline algorithms and export the winning model:
```bash
python models/experiments/compare_twitter_models.py
```
Output models and scalers are saved to `models/saved/twitter_best_model.pkl` and `models/saved/twitter_scaler.pkl`.

### 4. Hyperparameter Tuning (XGBoost)
Run randomized search cross-validation to tune decision tree depths, learning rates, and imbalance weights (`scale_pos_weight`):
```bash
python models/experiments/tune_xgboost.py
```

### 5. Run Inference & Explainability Validation
Run the standalone prediction engine stress test to verify SHAP explanation translation and 3-class classifications:
```bash
python notebooks/test_predict.py
```
