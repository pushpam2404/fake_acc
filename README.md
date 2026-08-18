# 🛡️ Dual-Platform Fake Account & Bot Detection Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7%2B-orange.svg)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-brightgreen.svg)](https://shap.readthedocs.io/)

Production-ready machine learning framework, FastAPI backend, and React web dashboard for detecting fake, bot, and automated accounts across **Twitter/X** and **Meta (Instagram & Facebook)** platforms with real-time SHAP natural language explanations.

---

## ⚡ Quickstart (Local Development)

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

## 🌐 Production Cloud Deployment Guide

### Part A: Backend Web Service ➔ Render (`render.com`)
1. Create new Web Service on Render connecting this GitHub repository.
2. Set **Root Directory**: `.` (or leave empty)
3. Set **Build Command**: `pip install -r backend/requirements.txt`
4. Set **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Verify health check: `curl https://sih1775-backend.onrender.com/health`

### Part B: Frontend Web App ➔ Vercel (`vercel.com`)
1. Create new Project on Vercel importing this GitHub repository.
2. Set **Root Directory**: `frontend`
3. Set Environment Variable: `VITE_API_BASE` = `https://sih1775-backend.onrender.com`
4. Deploy!

> [!NOTE]
> **Free Tier Warm-Up Tip**: Render free instances spin down after 15 minutes of inactivity. Ping `/health` 2 minutes prior to live stage presentations to warm up the model in memory.

---

## 📌 Technical Architecture

```text
fake-account-detection/
├── backend/
│   ├── main.py             # FastAPI REST service, CSV batch route & CORS middleware
│   ├── requirements.txt    # Pinned production backend dependencies
│   └── schemas.py          # Pydantic request/response data contracts
├── data/
│   ├── raw/                # Raw multi-platform datasets (Cresci, Satish, LIMFADD)
│   └── processed/          # Clean feature matrices (twitter_master.csv, meta_master.csv)
├── feature_extractor/
│   ├── build_twitter.py    # Twitter 13-feature ETL & ratio engineering
│   └── build_meta.py       # Meta 7-feature ETL & ratio engineering
├── frontend/               # React + TypeScript + Vite Editorial Dashboard
│   ├── src/
│   │   ├── App.tsx         # Main Editorial Dashboard React component
│   │   ├── BatchView.tsx   # Central Agency Batch CSV upload table
│   │   ├── api.ts          # Axios HTTP client connecting to FastAPI
│   │   ├── presets.ts      # Sample telemetry profiles for Twitter and Meta
│   │   ├── types.ts        # TypeScript contracts matching backend schemas
│   │   └── index.css       # Light Parchment Editorial design system
│   ├── .env                # Local VITE_API_BASE config
│   ├── .env.example        # Production VITE_API_BASE template
│   ├── vercel.json         # Vercel deployment spec
│   ├── index.html          # HTML entry point (Playfair Display & Inter fonts)
│   ├── package.json        # React frontend dependencies
│   └── vite.config.ts      # Vite dev server configuration
├── models/
│   ├── saved/              # Tuned model binaries (twitter_xgboost_tuned.pkl, meta_xgboost_tuned.pkl)
│   └── predict.py          # Dual-platform predictor & SHAP explainability engine
├── demo_batch.csv          # Sample 10-account mixed dataset for batch testing
├── render.yaml             # Render service deployment specification
├── test_payload.json       # API test payload
├── PROJECT_SUMMARY.md      # Detailed hackathon journey & presentation guide
└── README.md               # Quick technical overview
```

---

## ⚙️ Canonical Feature Schemas

- **Twitter / X (13 Features)**: `followers`, `following`, `post_count`, `verified`, `description_length`, `account_age_days`, `follower_following_ratio`, `reputation_score`, `username_length`, `digits_in_username`, `digit_ratio_username`, `has_url`, `posts_per_day`.
- **Meta / Instagram & Facebook (7 Features)**: `followers`, `following`, `post_count`, `has_profile_pic`, `bio_length`, `follower_following_ratio`, `reputation_score`.

---

## 📊 Benchmark Performance

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
