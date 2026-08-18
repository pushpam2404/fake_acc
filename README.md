# 🛡️ Dual-Platform Fake Account & Bot Detection Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7%2B-orange.svg)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-brightgreen.svg)](https://shap.readthedocs.io/)

Production-ready machine learning framework, FastAPI backend, and React web dashboard for detecting fake, bot, and automated accounts across **Twitter/X** and **Meta (Instagram & Facebook)** platforms with real-time SHAP natural language explanations.

---

## ⚡ Quickstart

### 1. Backend Server (`http://localhost:8000`)
```bash
./.venv/bin/uvicorn backend.main:app --reload --port 8000
```
- Interactive Swagger API Docs: `http://localhost:8000/docs`

### 2. Frontend React Dashboard (`http://localhost:5173`)
```bash
cd frontend
npm install
npm run dev
```

---

## 📌 Technical Architecture

```text
fake-account-detection/
├── backend/
│   ├── main.py             # FastAPI REST service & CORS middleware
│   └── schemas.py          # Pydantic request/response data contracts
├── data/
│   ├── raw/                # Raw multi-platform datasets (Cresci, Satish, LIMFADD)
│   └── processed/          # Clean feature matrices (twitter_master.csv, meta_master.csv)
├── feature_extractor/
│   ├── build_twitter.py    # Twitter 13-feature ETL & ratio engineering
│   └── build_meta.py       # Meta 7-feature ETL & ratio engineering
├── frontend/               # React + TypeScript + Vite Editorial Dashboard
├── models/
│   ├── saved/              # Tuned model binaries (twitter_xgboost_tuned.pkl, meta_xgboost_tuned.pkl)
│   └── predict.py          # Dual-platform predictor & SHAP explainability engine
├── test_payload.json       # API test payload
├── PROJECT_SUMMARY.md      # Detailed hackathon journey & presentation guide
└── README.md               # Quick technical overview
```

---

## ⚙️ Canonical Feature Schemas

- **Twitter / X (13 Features)**: `followers`, `following`, `post_count`, `verified`, `description_length`, `account_age_days`, `follower_following_ratio`, `reputation_score`, `username_length`, `digits_in_username`, `digit_ratio_username`, `has_url`, `posts_per_day`.
- **Meta / Instagram & Facebook (7 Features)**: `followers`, `following`, `post_count`, `has_profile_pic`, `bio_length`, `follower_following_ratio`, `reputation_score`.

---

## 📊 Performance Benchmarks

| Platform | Production Model | Dataset Size | Accuracy | F1-Score | Inference Latency |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Twitter / X** | Tuned XGBoost | 64,919 Accounts | **90.04%** | **85.63%** | 0.21s |
| **Meta (IG & FB)** | Tuned XGBoost | 36,383 Accounts | **96.87%** | **97.15%** | 0.15s |

---

## 🔌 REST API Usage

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

**Response:**
```json
{
  "platform": "twitter",
  "risk_score": 98.45,
  "classification": "FAKE",
  "confidence": 0.98,
  "reasons": [
    "Suspicious follower-to-following ratio (0.002).",
    "High posting frequency (2500.0 posts per day).",
    "Anomalous metric detected in description_length (0)."
  ]
}
```
