# 🛡️ Dual-Platform Fake Account & Bot Detection Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7%2B-orange.svg)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-brightgreen.svg)](https://shap.readthedocs.io/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph_Analysis-blueviolet.svg)](https://networkx.org/)
[![Instaloader](https://img.shields.io/badge/Instaloader-OSINT-yellow.svg)](https://instaloader.github.io/)

Intelligence-grade fake account & bot detection engine built for **ITBP / Ministry of Home Affairs (SIH-1775)**. Features real-time XGBoost classification with SHAP explainability, OSINT profile scraping via URL paste, coordinated botnet network graph analysis, and 1-click forensic PDF case file export across **Twitter/X** and **Meta (Instagram & Facebook)** platforms.

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
│   ├── main.py                # FastAPI REST service, URL scanner, CSV batch, PDF export & CORS
│   ├── schemas.py             # Pydantic request/response data contracts
│   ├── osint_scraper.py       # OSINT profile extraction (Instaloader + URL parser + offline cache)
│   ├── network_analyser.py    # NetworkX graph analysis (Degree Centrality, CIB cluster detection)
│   ├── report_generator.py    # Forensic PDF case file generator (fpdf2, ITBP/MHA legal format)
│   └── requirements.txt       # Pinned production backend dependencies
├── data/
│   ├── raw/                   # Raw multi-platform datasets (Cresci, Satish, LIMFADD)
│   └── processed/             # Clean feature matrices (twitter_master.csv, meta_master.csv)
├── feature_extractor/
│   ├── build_twitter.py       # Twitter 13-feature ETL & ratio engineering
│   └── build_meta.py          # Meta 7-feature ETL & ratio engineering
├── frontend/                  # React + TypeScript + Vite Editorial Dashboard
│   ├── src/
│   │   ├── App.tsx            # Main Dashboard (URL scanner, form, results, PDF export)
│   │   ├── BatchView.tsx      # Central Agency Batch CSV upload table
│   │   ├── NetworkGraph.tsx   # Interactive SVG force-directed threat network graph
│   │   ├── api.ts             # Axios HTTP client (analyze, analyzeUrl, downloadReport)
│   │   ├── presets.ts         # Sample telemetry profiles for Twitter and Meta
│   │   ├── types.ts           # TypeScript contracts matching backend schemas
│   │   └── index.css          # Light Parchment Editorial design system + pulse animation
│   ├── vercel.json            # Vercel deployment spec
│   ├── index.html             # HTML entry point (Playfair Display & Inter fonts)
│   ├── package.json           # React frontend dependencies
│   └── vite.config.ts         # Vite dev server configuration
├── models/
│   ├── saved/                 # Tuned model binaries (twitter_xgboost_tuned.pkl, meta_xgboost_tuned.pkl)
│   └── predict.py             # Dual-platform predictor & SHAP explainability engine
├── demo_batch.csv             # Sample 10-account mixed dataset for batch testing
├── render.yaml                # Render service deployment specification
├── test_payload.json          # API test payload
├── PROJECT_SUMMARY.md         # Detailed hackathon journey & presentation guide
└── README.md                  # Quick technical overview
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
  ],
  "network_graph": { "nodes": [...], "edges": [...], "density": 0.714, "clique_count": 3 }
}
```

### URL-Based Profile Scan
```bash
curl -X POST http://localhost:8000/analyze/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://x.com/cybersec_alert_bot"}'
```

### Export Forensic PDF Report
```bash
curl -X POST http://localhost:8000/analyze/report \
  -H "Content-Type: application/json" \
  -d '{"username": "cybersec_alert_bot", "features": {...}, "prediction": {...}}' \
  --output report.pdf
```

---

## 🧩 Key Features

| Feature | Description |
| :--- | :--- |
| **URL Profile Scanner** | Paste any Twitter/X or Instagram/Facebook profile link — the OSINT scraper auto-extracts metadata and runs ML classification. |
| **Dual-Platform XGBoost** | Separate tuned models for Twitter (13 features, 90% accuracy) and Meta (7 features, 97% accuracy) with SHAP explainability. |
| **Network Graph Analysis** | NetworkX-powered Degree Centrality and CIB cluster detection visualized as an interactive SVG force-directed graph. |
| **Forensic PDF Export** | 1-click download of a law-enforcement-grade case file with ITBP/MHA header, SHA256 hash, and Sec. 65B Indian Evidence Act compliance. |
| **Batch CSV Analysis** | Central agency dashboard for bulk-scanning accounts via CSV upload with color-coded threat results. |
| **Offline Intel Cache** | Pre-seeded demo profiles ensure the live presentation never fails due to rate limiting. |

