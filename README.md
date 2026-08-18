# 🛡️ Dual-Platform Fake Account & Bot Detection Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7%2B-orange.svg)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-brightgreen.svg)](https://shap.readthedocs.io/)

A production-ready machine learning system and FastAPI backend for detecting fake, bot, and automated accounts across **Twitter/X** and **Meta (Instagram & Facebook)** platforms, complete with real-time SHAP natural language explanations.

---

## 📌 Features & Architecture

- **Bifurcated ETL Pipelines**: Custom extraction pipelines for Twitter (13 metadata features) and Meta (7 visual/bio features) to prevent missing-data sparse matrices.
- **Tuned XGBoost Estimators**: High-precision gradient boosted decision trees tuned with dynamic class imbalance weighting (`scale_pos_weight`).
- **SHAP Explainability Engine**: Translates complex decision tree feature contributions into human-readable English reasons (e.g. *"Suspicious follower-to-following ratio"*, *"Account lacks profile picture"*).
- **FastAPI REST Service**: Production backend featuring Pydantic contract validation, CORS middleware, single-account `/analyze`, batch processing `/analyze/batch`, and `/health` monitoring.

---

## 📁 Repository Structure

```text
fake-account-detection/
├── backend/
│   ├── main.py             # FastAPI REST application & routes
│   └── schemas.py          # Pydantic request/response data contracts
├── data/
│   ├── raw/                # Multi-source raw datasets (Cresci, Satish, LIMFADD, etc.)
│   └── processed/          # Processed dataset matrices (twitter_master.csv, meta_master.csv)
├── feature_extractor/
│   ├── build_twitter.py    # Twitter ETL & feature engineering pipeline (13 features)
│   └── build_meta.py       # Meta/IG ETL & feature engineering pipeline (7 features)
├── models/
│   ├── experiments/
│   │   ├── compare_twitter_models.py # Twitter Gladiator Arena benchmark script
│   │   ├── compare_meta_models.py    # Meta Gladiator Arena benchmark script
│   │   ├── tune_xgboost_twitter.py   # Twitter XGBoost hyperparameter search
│   │   └── tune_xgboost_meta.py      # Meta XGBoost hyperparameter search
│   ├── saved/              # Tuned model artifacts (*.pkl) & scalers (*_scaler.pkl)
│   └── predict.py          # Unified dual-platform prediction & SHAP explainability engine
├── notebooks/
│   ├── inspect_raw.py      # Raw dataset diagnostic scanner
│   └── test_predict.py     # Independent dual-platform inference stress test
├── test_payload.json       # Sample JSON payload for API testing
├── PROJECT_SUMMARY.md      # Hackathon pitch & battle-tested problem-solving notes
└── README.md               # Repository documentation
```

---

## ⚙️ Feature Engineering Schemas

### 🐦 Twitter / X Schema (13 Features)
`followers`, `following`, `post_count`, `verified`, `description_length`, `account_age_days`, `follower_following_ratio`, `reputation_score`, `username_length`, `digits_in_username`, `digit_ratio_username`, `has_url`, `posts_per_day`.

### 📸 Meta / Instagram Schema (7 Features)
`followers`, `following`, `post_count`, `has_profile_pic`, `bio_length`, `follower_following_ratio`, `reputation_score`.

---

## 📊 Benchmark Performance

### 🐦 Twitter Platform (64,919 Accounts)
| Rank | Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Inference Latency |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **Soft-Voting Ensemble** | **90.47%** | **88.50%** | **83.96%** | **86.17%** | 2.81s |
| 🥈 | **Random Forest** | 90.16% | 88.15% | 83.41% | 85.72% | 1.12s |
| 🥉 | **Tuned XGBoost (Production Champion)** | **90.04%** | **87.47%** | **83.87%** | **85.63%** | **0.21s** |
| 4 | Logistic Regression | 81.64% | 76.78% | 68.96% | 72.66% | 0.02s |

### 📸 Meta / Instagram Platform (36,383 Accounts)
| Rank | Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Inference Latency |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **Soft-Voting Ensemble** | **97.05%** | **97.57%** | **97.06%** | **97.31%** | 1.63s |
| 🥈 | **Random Forest** | 97.02% | 97.59% | 96.98% | 97.28% | 0.37s |
| 🥉 | **Tuned XGBoost (Production Champion)** | **96.87%** | **97.23%** | **97.08%** | **97.15%** | **0.15s** |
| 4 | Logistic Regression | 89.05% | 90.21% | 89.87% | 90.04% | 0.02s |

---

## 🚀 Getting Started

### 1. Installation & Environment
```bash
# Clone the repository
git clone https://github.com/pushpam2404/fake_acc.git
cd fake_acc

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install pandas numpy scikit-learn xgboost joblib shap fastapi uvicorn pydantic
```

### 2. Build Datasets & Train Models
```bash
# Rebuild feature matrices
python feature_extractor/build_twitter.py
python feature_extractor/build_meta.py

# Retrain tuned models
python models/experiments/tune_xgboost_twitter.py
python models/experiments/tune_xgboost_meta.py
```

### 3. Launch FastAPI Backend Service
```bash
uvicorn backend.main:app --reload --port 8000
```
Interactive Swagger API documentation will be available at: `http://localhost:8000/docs`

---

## 🔌 API Endpoint Documentation

### Analyze Single Account (`POST /analyze`)
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

**Sample Response**:
```json
{
  "platform": "meta",
  "risk_score": 99.64,
  "classification": "FAKE",
  "confidence": 1.0,
  "reasons": [
    "Suspicious follower-to-following ratio (0.0).",
    "Unusual total post count (0).",
    "Anomalous follower count (0)."
  ]
}
```

### Healthcheck (`GET /health`)
```bash
curl http://localhost:8000/health
```
```json
{"status": "ok", "message": "Backend and ML Models are online."}
```
