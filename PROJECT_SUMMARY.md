# 📖 PROJECT_SUMMARY.md: The Complete Engineering Journey & Hackathon Defense Guide

> **Note for Team Members & Presenters**: This document is our comprehensive, narrative-style record of the entire project build. It details every technical breakthrough, data obstacle, architectural pivot, false positive resolution, and model calibration we executed. Use this document to prepare your presentation pitch, rehearse hackathon judge Q&A, and tell a compelling story of engineering rigor on stage.

---

## 📑 Executive Summary

We built an intelligence-grade **Dual-Platform Fake Account, Botnet, Impersonator & Social Threat Detection Engine** designed for **ITBP / Ministry of Home Affairs (SIH-1775)**. The engine evaluates social media profiles across **Twitter/X**, **Instagram**, and **Facebook** using a multi-layered defense architecture:
1. **Dual-Platform Tabular XGBoost Classifiers**: Trained on 101,000+ real-world accounts (**90.04% Accuracy on Twitter**, **96.87% Accuracy on Meta**).
2. **Local Neural NLP Threat Analyser**: Uses PyTorch `SentenceTransformer('all-MiniLM-L6-v2')` to evaluate 384-dimensional dense semantic vectors (0 API costs, 100% self-hosted).
3. **Universal Identity Discrepancy & Impersonation Engine**: Algorithmic lexical token overlap mathematics catching celebrity clones, fake official monikers (`official_`), and synthetic persona disclosures.
4. **Playwright Headless Chromium Scraper**: Live browser DOM and media extraction recovering high-resolution avatars, verified DOM bios, outbound Telegram/phishing links, and recent post flyers.
5. **NetworkX Coordinated Inauthentic Behavior (CIB) Topology**: Graph theory centrality and clique clustering for botnet identification.
6. **Forensic PDF Case File Generator**: 1-click legal report export compliant with **Section 65B of the Indian Evidence Act**.

---

## 🎯 Section 1: Core Problem & Engineering Philosophy

### 1. The Core SIH-1775 Mandate
Law enforcement agencies and social platforms face sophisticated threat vectors that simple rule-checks fail to catch:
- **Automated Botnets & Sybil Clusters**: Coordinated farms inflating metrics and astroturfing narratives.
- **Celebrity & Institutional Impersonation**: Accounts borrowing the avatar and name of public figures or government bodies while hiding behind unverified handles.
- **Financial Investment & Telegram Funnels**: Unregistered stock tipsters, F&O intraday calls, and crypto doubling schemes funneling users into unmonitored Telegram/WhatsApp groups.
- **Hostile Information Warfare & State Subversion**: Accounts using derogatory entity prefixes, attack hashtags (`#fuck...`), and inflammatory propaganda.

### 2. The Multi-Layered Defense Architecture

```
                                  ┌────────────────────────────────────────┐
                                  │      INPUT: Profile URL / Telemetry    │
                                  └──────────────────┬─────────────────────┘
                                                     │
                             ┌───────────────────────┴───────────────────────┐
                             │                                               │
                             ▼                                               ▼
              ┌──────────────────────────────┐                ┌──────────────────────────────┐
              │  Tabular Metadata Pipeline   │                │   Multimodal NLP & Visual    │
              │     (Dual-Platform XGBoost)  │                │    (SentenceTransformer)     │
              ├──────────────────────────────┤                ├──────────────────────────────┤
              │ • Follower/Following Ratios  │                │ • Zero-Shot Threat Vectors   │
              │ • Reputation & Velocity Score│                │ • Caption Uniformity Matrix  │
              │ • Username Syntax & Digits   │                │ • Identity Token Discrepancy │
              │ • Account Age & Activity Rate│                │ • Outbound Redirect Audit    │
              └──────────────┬───────────────┘                └──────────────┬───────────────┘
                             │                                               │
                             └───────────────────────┬───────────────────────┘
                                                     │
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │  Continuous Multimodal Fusion│
                                      │  Risk = (XGB × w1) + (NLP × w2)
                                      └──────────────┬───────────────┘
                                                     │
                                     ┌───────────────┴───────────────┐
                                     ▼                               ▼
                      ┌──────────────────────────────┐┌──────────────────────────────┐
                      │    SHAP Decision Forensics   ││ Interactive CIB Graph & PDF  │
                      └──────────────────────────────┘└──────────────────────────────┘
```

---

## ⌛ Section 2: Chronological Build Odyssey & Major Obstacles Overcome

### Phase 1: Data Reconnaissance & Bifurcated Schema Design

* **Challenge #1: The Universal Schema Trap**
  * *Problem:* Forcing Twitter and Instagram into one shared schema created excessive null values (Twitter lacks `has_profile_pic`, Instagram lacks `verified` badges or tweet velocity).
  * *Solution:* Built **Bifurcated Domain-Isolated Pipelines**: 13 canonical features for Twitter (`build_twitter.py`) and 7 for Meta (`build_meta.py`).
* **Challenge #2: The Missing Target Variable Void**
  * *Solution:* Built an automated reconnaissance scanner (`inspect_raw.py`) extracting ground-truth labels from research directory names.
* **Challenge #3: The 50,000-Row Poison Pill Dataset (`goyaladi`)**
  * *Problem:* A noisy tweet-level dataset without follower metrics capped Twitter accuracy at 67%. Purging it rocketed model accuracy to **90.04%**!

---

### Phase 2: Model Benchmarking & Tuning

* **Gladiator Arena Benchmark Results**:
  1. *Logistic Regression*: 81.6% (Twitter) / 89.0% (Meta) — too simplistic for non-linear step thresholds.
  2. *Multi-Layer Perceptron (MLP)*: 87.8% (Twitter) / 96.2% (Meta) — slow inference (26.8s).
  3. **Tuned XGBoost (CHAMPION 🏆)**: **90.04% on Twitter**, **96.87% on Meta**, 0.15s latency, and native SHAP integration.

---

### Phase 3: Solving Complex Real-World Detection Failures (No Hardcoding)

Throughout live validation on active Instagram, Twitter, and Facebook accounts, we confronted and algorithmically solved 5 major real-world blind spots:

#### 1. The Intent Blindness of Tabular Models (e.g. Political Troll `@fuck_bjp._`)
* **The Failure:** Tabular XGBoost saw 74 followers and 113 following (ratio 0.65) and rated the account as **REAL (2.98% Risk)** because its numeric ratios looked like a normal peer user.
* **The Solution:** Added **Continuous Multimodal Fusion** in `backend/main.py`. When local SentenceTransformer semantic vectors and handle morphology detect hate campaign signatures or targeted entity defamation, the Content Threat dynamically scales its fusion weight ($w_2 = 0.60$), elevating the classification to **CRITICAL / FAKE**.

#### 2. The Celebrity Impersonation Blind Spot (e.g. `@up9o_official_rohit_singh` claiming `virat•kohli`)
* **The Failure:** The account used Virat Kohli's avatar and display name `virat•kohli`, but had a completely unrelated handle `@up9o_official_rohit_singh` with only 2 posts and 1,988 followers. Tabular models saw normal ratios and missed the impersonation.
* **The Solution:** Engineered the **Universal Identity Discrepancy Algorithm** in `backend/content_analyser.py`:
  - Tokenizes the display name (e.g. `['virat', 'kohli']`) and the handle (e.g. `['up9o', 'rohit', 'singh']`).
  - Measures lexical token overlap. When overlap is **0%** and the unverified handle uses spoofing prefixes (`official_`, `real_`) or claims `AI creator / clone`, threat points (+55 to +90) trigger an immediate **IMPERSONATION ALERT**.

#### 3. Telegram Stock Trading & Duplicate Promotional Flyer Repetition (e.g. `@stockstrading0`)
* **The Failure:** Instagram trading scams post duplicate marketing flyers promising *"120 DAYS FREE NIFTY CALLS"* to funnel users to Telegram (`t.me/...`). Initial scraping missed the grid due to lazy-loading overlays.
* **The Solution:**
  - Upgraded `backend/playwright_scraper.py` with multi-element grid selectors (`a[href*="/reel/"] img`, `div._aagv img`) and automatic overlay dismissal.
  - Implemented the **Pairwise Caption & Flyer Uniformity Matrix**, detecting that all 4 posts share the same promotional template (**81.3% Uniformity — Critical Template Syndication**).
  - Added Unregistered Stock Tip & F&O Telegram funnel patterns to the Threat Taxonomy.

#### 4. Eliminating False Positives on Real Personal Profiles (e.g. Rural Cricket User `@hamim______kkr____56`)
* **The Failure:** A genuine village cricket enthusiast posting personal videos without captions was falsely flagged as **`CRITICAL THREAT (75/100)`** with **`87.2% Caption Uniformity`**.
* **Root Cause Auditing:**
  1. *Accessibility Metadata Treated as Captions:* Instagram generated automated alt text (*"Video by USER on July 06. May be an image of 1 person..."*). The neural model compared Instagram's own boilerplate strings across posts and found artificial 87% similarity!
  2. *Unicode Decorative Script:* The user wrote their name in decorative Unicode script (`ᴵᴬᴹ 𝓡𝓸𝓱𝓲𝓽`), which stripped to empty symbols, tripping the impersonation check.
  3. *Meta Threads Link:* The user's legitimate `threads.net` profile badge was flagged as an external redirect.
* **The Algorithmic Fixes:**
  - **Boilerplate Stripping (`clean_user_caption`)**: Automatically removes platform accessibility phrases. If the user posted raw visual media without text, uniformity reports **0.0% (Organic Media Uploads)**.
  - **Unicode Normalization (NFKD)**: Normalizes stylized fonts (𝓡𝓸𝓱𝓲𝓽 → `rohit`) to standard ASCII.
  - **First-Party Whitelist**: Whitelists official Threads, Instagram, YouTube, and X profile links as 100% SAFE.
  - *Result:* Risk score dropped from 75/100 to **0.38% (REAL / AUTHENTIC HUMAN)**!

#### 5. Selective Personal Circles vs Influencers (e.g. `@subham__8112`)
* **The Failure:** An account with 104 followers and 4 following ($20.8\times$ ratio) was described by SHAP as *"Strong creator/influencer ratio"*.
* **The Solution:** Made SHAP explanations volume-aware:
  - Followers $< 5,000$ and ratio $\ge 3.0 \rightarrow$ **`Selective personal social circle (104 followers vs 4 following)`**.
  - Followers $\ge 5,000$ and ratio $\ge 5.0 \rightarrow$ **`Creator/public audience distribution`**.
  - Followers $\ge 500,000$ and ratio $\ge 50.0 \rightarrow$ **`High-authority public figure footprint`**.

---

## 🛡️ Section 3: The "No-Hardcoding" Principle

Judges often ask: *"Did you just hardcode these specific accounts?"*

**Our Mathematical Defense**:
Every classification in this system is computed dynamically using generalized algorithms:
1. **Dense Vector Embeddings**: SentenceTransformer maps raw text into a 384-dimensional continuous Hilbert space. Similarities are computed via normalized dot products ($\cos \theta = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$).
2. **Lexical Token Geometry**: Identity discrepancy compares sets of N-gram word stems, independent of specific names.
3. **Entropy & Syntax Heuristics**: Handles are evaluated on delimiter repetition, vowel-to-consonant balance, and numerical digit concentration.
4. **SHAP Game Theory**: Explanations are derived from coalitional game theory calculating marginal feature contributions to tree paths.

---

## 🎤 Section 4: Hackathon Presentation Pitch Script

> **Opening Hook (30 Seconds)**:
> *"Judges, modern malicious actors no longer just build simple bot accounts. They create identity clones of public figures, flood feeds with syndicated Telegram stock pump funnels, and astroturf coordinated disinformation campaigns. Standard tools fail because they only check follower ratios. Today, we present the SIH-1775 Dual-Platform Threat & Impersonation Detection Engine — fusing XGBoost tabular ML with local zero-shot Neural NLP to expose malicious accounts in under 0.2 seconds."*

> **Technical Innovations (60 Seconds)**:
> 1. *"We bifurcated our ML pipelines: 13 features for Twitter and 7 for Meta, trained on 101,000 accounts with 90% and 97% accuracy."*
> 2. *"We deployed local SentenceTransformer embeddings on Apple Silicon/Linux to compute pairwise caption similarity matrices and zero-shot threat vectors without third-party API costs."*
> 3. *"We solved celebrity impersonation through universal identity token discrepancy mathematics."*
> 4. *"We eliminated accessibility boilerplate false positives, ensuring everyday personal users are never misclassified."*

> **Live Demo Steps (90 Seconds)**:
> 1. Scan `https://www.instagram.com/up9o_official_rohit_singh/` ➔ Show instant **CRITICAL IMPERSONATION ALERT** (Claims `virat•kohli` with 0% token match).
> 2. Scan `https://www.instagram.com/stockstrading0/` ➔ Show **81.3% Caption Uniformity**, Telegram trading funnel alert, and extracted promotional flyer cards.
> 3. Scan `https://www.instagram.com/hamim______kkr____56/` ➔ Show **0.38% Risk (REAL)**, demonstrating zero false positives on everyday cricket fans.
> 4. Click **Export Forensic Case File (PDF)** ➔ Present the official ITBP legal case document with SHA256 integrity hash.
> 5. Upload **`demo_batch.csv`** in Central Agency View ➔ Demonstrate parallel multi-account batch screening.

---

## 🛡️ Section 5: Hackathon Judges Q&A Defense Cheat Sheet

| Likely Judge Question | Our Battle-Tested Answer |
| :--- | :--- |
| **"Why not just use an LLM API like GPT-4?"** | High latency (2–5s vs 0.15s), expensive token costs at scale, privacy compliance risks, and API rate limits. Our local `all-MiniLM-L6-v2` runs on-premise inside our container with **zero external dependencies and zero recurring cost**. |
| **"How do you catch a fake account with normal follower ratios?"** | That was our exact breakthrough with Continuous Multimodal Fusion. If an account has balanced numbers but its display name contradicts its handle, its captions are 85% duplicated, or its bio contains high-risk Telegram funnels, the Content Threat engine dynamically overrides the tabular score. |
| **"How do you prevent false positives on everyday people who don't write captions?"** | We engineered accessibility boilerplate stripping (`clean_user_caption`). If a user posts personal videos without text, our system recognizes it as organic visual media and reports 0% uniformity rather than mistaking Instagram's alt text for bot spam. |
| **"Is this admissible in court?"** | Yes. Our PDF report generates an ITBP/MHA header, SHA256 cryptographic file integrity hash, exact SHAP evidence attribution, and an officer sign-off block structured for compliance with **Section 65B of the Indian Evidence Act**. |
| **"How does the Network Graph detect botnets?"** | Using NetworkX graph algorithms, we calculate Degree Centrality and Graph Density. Bot farms exhibit dense inter-connected cliques (density $>0.6$), whereas organic human networks form sparse trees (density $<0.2$). |

---

## 📋 Phase 6: Central Agency Escalation & Reporting Module (IT Rules 2021 Compliance Pipeline)

### The Problem This Phase Solves

Detection without enforcement is intelligence without consequence. Phases 1–5 could identify a FAKE or SUSPICIOUS account with 90%+ accuracy in 0.15 seconds — but the output was a JSON blob on a screen. There was no answer to the most important operational question: *"A flagged account has been detected. Now what?"*

India's IT Rules 2021, Rule 3(1)(d), mandates that Significant Social Media Intermediaries (SSMIs) must acknowledge government/agency takedown requests within 24 hours and act upon them within 72 hours, or face loss of safe harbour immunity under Section 79 of the IT Act 2000. This module closes the loop: it turns a detection result into a trackable legal escalation case.

### What Was Built

#### Backend: `backend/cases.py` — SQLite Persistence + REST API

* **Zero-setup persistence**: Uses SQLAlchemy with a local SQLite file (`backend/cases.db`, auto-created on first startup). No Postgres, no Docker, no environment variables — a fresh clone with `pip install -r requirements.txt` is enough.
* **Case Model**: Stores `id` (UUID), `platform`, `handle`, `risk_score`, `classification`, `reasons` (JSON array from SHAP), `status` (workflow enum), `created_at`, `updated_at`, `reviewed_by`, and `report_generated`.
* **Forward-only status workflow**: `FLAGGED → UNDER_REVIEW → REPORT_SENT → TAKEDOWN_CONFIRMED`. Any attempt to skip a step or move backward returns a `400 Bad Request` with the legal next state named explicitly. No state machine library — pure dict-based transition table.
* **6 REST endpoints** mounted at `/cases`:
  - `POST /cases` — create case (guards: `REAL` accounts rejected, `numpy` float sanitized via the existing `sanitize_result` pattern)
  - `GET /cases` — list all, newest first
  - `GET /cases/summary` — dashboard stats (total, pending, reports_sent, takedowns_confirmed, avg_time_to_takedown_hours)
  - `GET /cases/{id}` — single case detail
  - `PATCH /cases/{id}/status` — advance status (validates legal transition)
  - `GET /cases/{id}/report` — structured JSON report with `legal_basis` citing IT Rules 2021, sets `report_generated=True`
* **Critical routing fix**: `GET /cases/summary` is declared *before* `GET /cases/{id}` in the router to prevent FastAPI from treating the literal string `"summary"` as a UUID path parameter.
* **Startup seeding**: `backend/seed_cases.py` inserts 10 realistic mock cases (across all 4 statuses, both platforms, with SHAP-style reasons) on first startup if the table is empty. The dashboard is never blank on a fresh demo.

#### Backend: `backend/seed_cases.py` — Demo-Ready Data

10 seed cases modeled on real detection scenarios (bot farms, celebrity impersonators, Telegram stock funnels, government handle spoofing, information warfare cells). Reasons text matches the style of `frontend/src/presets.ts` for narrative consistency.

#### Frontend: `EscalationView.tsx` — Central Agency Dashboard

* **Summary strip**: 4 stat cards (Total Escalated, Pending Review, Reports Sent, Avg. Time-to-Takedown) with live data from `GET /cases/summary`.
* **Cases table**: Filterable by status, shows Handle, Platform, Risk Score (color-coded by threshold), Classification badge, Flagged Date, and inline "quick advance" status button.
* **Detail drawer**: Slides in from the right with the full SHAP reasons list (reusing `reason-item`/`reason-bullet` CSS classes from the existing design system), officer name input, and "Advance Status" button with next-legal-state logic enforced on both client and server.
* **Formal Report modal**: Calls `GET /cases/{id}/report`, renders the JSON as a readable printable view (serif headers, monospace `legal_basis` citation). Includes "Copy as JSON" and "Print (Cmd+P)" buttons. No PDF library — browser print handles demo output.
* **Toast system**: Lightweight, no external dependency.

#### Frontend: `BatchView.tsx` — CSV Batch Analysis with Escalation

* Drag-and-drop CSV upload to `/analyze/batch/csv`.
* Per-row SHAP reasons accordion (click to expand).
* Per-row "Escalate" button (only shown for FAKE/SUSPICIOUS) calling `POST /cases`.
* Summary strip showing batch totals and an "Escalation Centre →" CTA banner when threats are detected.
* "Escalated ✓" state persists within the session after escalation.

#### Frontend: `App.tsx` — Navigation & Escalate Button

* Added two new nav tabs: **Batch CSV Analysis** and **Central Agency Cases**.
* "Escalate to Central Agency" button appears on the Scan tab's result panel only when classification is `FAKE` or `SUSPICIOUS`. On click, `POST /cases` is called and a toast confirms. The button uses the classification's risk color (red for FAKE, amber for SUSPICIOUS) so it's visually obvious without adding clutter for REAL results.

### Known Limitation: Render Ephemeral Filesystem

`cases.db` is stored as a file at `backend/cases.db`. On Render's free-tier web service, the filesystem resets on each deploy, meaning case data does not persist across redeployments. This is acceptable for a demo session (data survives for the session duration) and is standard behaviour for SQLite on any PaaS with ephemeral disks.

**For a production deployment**, the fix would be one of:
1. Mount a Render Persistent Disk (available on paid plans) at a fixed path and point `DB_PATH` to it.
2. Migrate to PostgreSQL with SQLAlchemy's `postgresql://` connection string (zero code changes beyond the URL).

This limitation is explicitly flagged here and does not silently fail — the backend starts cleanly and seeds fresh data on each deploy, keeping the demo functional.
