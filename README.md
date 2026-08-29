# 🛡️ Dual-Platform Fake Account, Impersonation & Threat Detection Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7%2B-orange.svg)](https://xgboost.readthedocs.io/)
[![SentenceTransformers](https://img.shields.io/badge/SentenceTransformers-all--MiniLM--L6--v2-red.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![Playwright](https://img.shields.io/badge/Playwright-Headless_Chromium-green.svg)](https://playwright.dev/)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-brightgreen.svg)](https://shap.readthedocs.io/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph_Analysis-blueviolet.svg)](https://networkx.org/)

Intelligence-grade fake account, botnet, impersonator, and social threat detection engine built for **ITBP / Ministry of Home Affairs (SIH-1775)**. Features dual-platform XGBoost classification (101,000+ accounts), real-time SHAP plain-English explainability, live Playwright Headless Chromium DOM & media extraction, local PyTorch neural NLP (`all-MiniLM-L6-v2`) semantic threat detection, coordinated threat network topology, and 1-click forensic PDF case file export across **Twitter/X**, **Instagram**, and **Facebook**.

---

## ⚡ Quickstart (Local Development)

### 1. Backend Web Service (`http://localhost:8000`)
```bash
# Activate virtual environment
source .venv/bin/activate

# Launch FastAPI with auto-reload
uvicorn backend.main:app --reload --port 8000
```
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 2. Frontend React Dashboard (`http://localhost:5173`)
```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Production Cloud Deployment Guide

### Part A: Backend Web Service ➔ Render (`render.com`)
1. Create a new **Web Service** on Render connecting your GitHub repository.
2. Set **Root Directory**: `.`
3. Set **Build Command**:
   ```bash
   pip install -r backend/requirements.txt && playwright install chromium --with-deps
   ```
4. Set **Start Command**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
5. Set Environment Variables:
   - `TOKENIZERS_PARALLELISM`: `false`
   - `PYTHONUNBUFFERED`: `1`

### Part B: Frontend Web App ➔ Vercel (`vercel.com`)
1. Create a new Project on Vercel importing this GitHub repository.
2. Set **Root Directory**: `frontend`
3. Set Environment Variable: `VITE_API_BASE` = `https://your-backend.onrender.com`
4. Deploy!

---

## 📌 Technical Architecture

```text
fake-account-detection/
├── backend/
│   ├── main.py                # FastAPI REST server, URL scanner, Multimodal Fusion & CORS
│   ├── schemas.py             # Pydantic data contracts (PostMediaItem, ContentAnalysis, AnalyzeResponse)
│   ├── playwright_scraper.py  # Playwright headless Chromium DOM, avatar, bio & post scraper
│   ├── content_analyser.py    # Local SentenceTransformer neural NLP, cosine matrix, threat taxonomy
│   ├── osint_scraper.py       # OSINT profile extraction, Instaloader & offline cache
│   ├── network_analyser.py    # NetworkX graph analysis (Degree Centrality, CIB cluster detection)
│   ├── report_generator.py    # Forensic PDF case file generator (fpdf2, Sec. 65B legal format)
│   └── requirements.txt       # Pinned production backend dependencies
├── data/
│   ├── raw/                   # Multi-platform research datasets (Cresci, Satish, LIMFADD)
│   └── processed/             # Clean feature matrices (twitter_master.csv, meta_master.csv)
├── feature_extractor/
│   ├── build_twitter.py       # Twitter 13-feature ETL & ratio engineering
│   └── build_meta.py          # Meta 7-feature ETL & ratio engineering
├── frontend/                  # React 18 + TypeScript + Vite Dashboard
│   ├── src/
│   │   ├── App.tsx            # Main Dashboard (URL scanner, form, results, PDF export)
│   │   ├── MediaAuditView.tsx # Live Scraped Post Gallery, Caption Uniformity & Threat Badges
│   │   ├── NetworkGraph.tsx   # Interactive SVG force-directed threat network graph
│   │   ├── BatchView.tsx      # Central Agency Batch CSV upload table
│   │   ├── api.ts             # Axios client with 30s timeout for live scraping
│   │   ├── presets.ts         # Verified telemetry profiles for Twitter and Meta
│   │   └── types.ts           # TypeScript interfaces matching backend schemas
│   ├── package.json           # React frontend dependencies
│   └── vite.config.ts         # Vite dev server configuration
├── models/
│   ├── saved/                 # Tuned model binaries (twitter_xgboost_tuned.pkl, meta_xgboost_tuned.pkl)
│   └── predict.py             # Dual-platform predictor & SHAP explainability engine
├── PROJECT_SUMMARY.md         # Comprehensive engineering journey & hackathon defense guide
└── README.md                  # Technical overview and deployment specifications
```

---

## ⚙️ Core Technical Capabilities

### 1. Dual-Platform XGBoost Machine Learning (101,000+ Accounts)
- **Twitter / X Model (13 Features, 90.04% Accuracy)**: `followers`, `following`, `post_count`, `verified`, `description_length`, `account_age_days`, `follower_following_ratio`, `reputation_score`, `username_length`, `digits_in_username`, `digit_ratio_username`, `has_url`, `posts_per_day`.
- **Meta Model (7 Features, 96.87% Accuracy)**: `followers`, `following`, `post_count`, `has_profile_pic`, `bio_length`, `follower_following_ratio`, `reputation_score`.

### 2. Zero-Shot Neural NLP & Phishing Engine (SentenceTransformer)
- Runs local **`SentenceTransformer('all-MiniLM-L6-v2')`** with PyTorch Apple Silicon MPS / CPU acceleration (100% local, 0 token costs).
- Computes **$N \times N$ Pairwise Cosine Similarity Matrices** across post captions and promotional flyers to mathematically detect automated bot syndication ($>80\%$ uniformity).
- Evaluates 384-dimensional semantic embeddings against threat anchors for **Information Warfare, State Subversion, Hate Sloganeering, and Financial Scams**.

### 3. Universal Identity Discrepancy & Impersonation Engine
- **Token Overlap Math**: Tokenizes display name vs username handle. If display name claims an identity (e.g. `virat•kohli`) but the handle has $0\%$ token overlap (e.g. `@up9o_official_rohit_singh`), flags severe synthetic impersonation.
- **Spoofing Moniker Detection**: Catches deceptive `official_`, `real_`, `support_` tokens on unverified handles.
- **AI Persona Disclosures**: Flags profiles claiming `AI creator / Clone / Parody` while borrowing external celebrity identities.

### 4. Coordinated Inauthentic Behavior (CIB) Network Graph
- **NetworkX** graph theory calculations: Degree Centrality, Graph Density, and Clique Count.
- Renders an interactive SVG constellation graph with glowing threat halos, node dragging, zoom controls, and coordination edge tooltips (*"Shared IP Subnet"*, *"Posting Synchronization <3s"*).

### 5. Official ITBP / MHA Forensic PDF Export
- Generates downloadable law-enforcement-grade case reports containing Target Summary Cards, SHAP Decision Attribution, Telemetry Tables with human baseline benchmarks, Multimodal & Phishing Forensics, and SHA256 integrity hashes for legal admissibility under **Section 65B of the Indian Evidence Act**.

---

## 🔬 Benchmark Performance

| Platform | Production Model | Training Dataset | Accuracy | F1-Score | Inference Latency |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Twitter / X** | Tuned XGBoost | 64,919 Accounts | **90.04%** | **85.63%** | 0.18s |
| **Meta (IG & FB)** | Tuned XGBoost | 36,383 Accounts | **96.87%** | **97.15%** | 0.12s |

---

## 🔌 API Endpoints

### 1. Single Account Telemetry Inference
```bash
POST http://localhost:8000/analyze
Content-Type: application/json

{
  "platform": "twitter",
  "followers": 12,
  "following": 4500,
  "post_count": 5000,
  "verified": 0,
  "description_length": 0,
  "account_age_days": 2,
  "has_url": 1
}
```

### 2. Live Profile URL Deep Scan
```bash
POST http://localhost:8000/analyze/url
Content-Type: application/json

{
  "url": "https://www.instagram.com/stockstrading0/"
}
```

### 3. Forensic PDF Case File Download
```bash
POST http://localhost:8000/analyze/report
Content-Type: application/json

{
  "username": "stockstrading0",
  "features": {...},
  "prediction": {...}
}
```

### 4. Bulk CSV Batch Upload
```bash
POST http://localhost:8000/analyze/batch/csv
Content-Type: multipart/form-data
File: demo_batch.csv
```
