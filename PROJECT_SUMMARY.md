# 🛡️ Dual-Platform Fake Account & Bot Detection Engine

A comprehensive, production-ready machine learning framework for detecting fake, bot, and automated social media accounts across both **Twitter/X** and **Meta (Instagram & Facebook)** platforms.

---

### The Foundation: What I Have Built (Progress)

I have successfully transitioned from wrestling with fragmented, corrupted raw data to possessing a mathematically sound, production-ready machine learning inference engine. I didn't take the sloppy route of blindly throwing data at an algorithm; I built a professional-grade ETL (Extract, Transform, Load) pipeline prioritizing backend efficiency over messy mathematical imputation.

* **Reconnaissance & Labeling (`inspect_raw.py`):** I built a scanner that dynamically intercepts missing target variables by parsing file names (extracting `1` for "fake" and `0` for "genuine"). This single script saved over 12,000 rows of high-quality data from the void.
* **Bifurcated ETL Pipelines (`build_twitter.py`, `build_meta.py`):** I abandoned the "Universal Schema" trap. By splitting the architecture into domain-isolated pipelines that respect the structural differences between Twitter (metadata-heavy) and Meta (visual/bio-heavy), I guaranteed dense, high-signal matrices without a sea of Null values.
* **Derived Feature Engineering:** Instead of relying on raw, noisy metrics, I engineered behavioral derivations—like `follower_following_ratio`, `posts_per_day`, `digit_ratio_username`, `consonant_ratio_username`, and `profile_pic_bio_score`. Just like calculating a car's power-to-weight ratio tells you more than just its weight, these ratios act as the actual mathematical tripwires for catching bots.
* **Model Gladiator Arena (`compare_twitter_models.py`, `compare_meta_models.py`):** I set up a rigorous testing ground to prove the math. I demonstrated that tree-based ensembles (Random Forest/XGBoost/Extra Trees) completely annihilate standard linear models and neural networks on this specific tabular data.
* **Hyperparameter Optimization (`tune_xgboost_twitter.py`, `tune_xgboost_meta.py`):** I maxed out my M4 Mac's multi-core processing to run randomized cross-validation searches. This pushed the XGBoost model to **90.04% accuracy / 85.63% F1-Score on Twitter** and **96.87% accuracy / 97.15% F1-Score on Meta**, mapping highly complex decision boundaries.
* **The Explainability Engine (`explain.py` & `test_predict.py`):** I integrated SHAP (SHapley Additive exPlanations—a game-theory approach to explain machine learning predictions) to reverse-engineer the model's brain. It now outputs human-readable English reasons for *why* an account is fake, backed by an isolated 30-row stress test proving robust performance outside the training environment.

---

### The Battlefield: Obstacles Encountered & Destroyed

The path was littered with data engineering landmines that would have derailed a standard script. Here is exactly how I identified and neutralized them. 💣

* **Obstacle 1: The OS File Trap (`[Errno 21]`)**
  * *The Threat:* macOS unzipping artifacts created rogue folders literally named `.csv`. My ingestion loop was crashing blindly trying to read directories as flat files.
  * *The Fix:* I implemented strict `os.path.isfile()` checks and `on_bad_lines='warn'` to shield the ingestion engine from OS-level garbage and corrupted tokenization.

* **Obstacle 2: The Multi-Class Collision (`LIMFADD.csv`)**
  * *The Threat:* One dataset introduced four distinct text labels (Spam, Scam, Real, Bot). Left unchecked, this would have blown up the binary classification loss functions downstream.
  * *The Fix:* I wrote a highly efficient `map()` dictionary protocol to intercept and squash the multi-class strings into strict binary integers (`1` or `0`).

* **Obstacle 3: The Apple Silicon OpenMP Crash**
  * *The Threat:* XGBoost failed to initialize because my hardware architecture lacked the C++ multi-threading libraries required for hyper-fast tree building.
  * *The Fix:* I dropped into the terminal and installed `libomp` via Homebrew, bridging the OS-level dependency gap seamlessly.

* **Obstacle 4: The 50,000-Row Poison Pill (`goyaladi` dataset)**
  * *The Threat:* My hyperparameter search hit a hard ceiling (67% F1-Score). The pipeline had ingested 50,000 rows of a tweet-level dataset that lacked `following` and `description` data, forcing the pipeline to inject fake `0`s. The model was learning contradictory, poisoned logic.
  * *The Fix:* I ruthlessly purged the incompatible dataset, sacrificing raw volume for high-fidelity signal. This surgical strike instantly rocketed the model's performance to 90%.

* **Obstacle 5: The Inference Scaler Mismatch (The 3/15 Failure)**
  * *The Threat:* During the Hour 7 Sanity Check, the standalone predictor failed spectacularly (3/15 correct), screaming "FAKE" at real accounts. The inference script was passing the data through a `StandardScaler`, shrinking human follower counts to tiny decimals, which tricked the unscaled XGBoost trees into seeing massive bot anomalies.
  * *The Fix:* I executed a rapid root-cause analysis, stripped the `StandardScaler` entirely out of the tree-based inference pipeline, and forced a strict column-ordering array to ensure the data geometry matched the training phase perfectly.

* **Obstacle 6: The 100 MB GitHub File Limit & Ensemble Storage Trap**
  * *The Threat:* Combining multiple heavy tree models into a `VotingClassifier` ensemble inflated the binary serialized pickle file (`twitter_best_model.pkl`) to 497.28 MB and `meta_best_model.pkl` to 124.86 MB. GitHub rejected the `git push` command due to its hard 100 MB per-file limit.
  * *The Fix:* Decoupled the repository binary storage to rely on compact, single-model **Tuned XGBoost artifacts (`twitter_xgboost_tuned.pkl` and `meta_xgboost_tuned.pkl`)**, which are only ~5-15 MB in size, lightning fast (0.14s inference latency), and fully compatible with native SHAP `TreeExplainer` feature attribution.

---

### The Dual-Platform Paradigm Shift

Social media platforms operate on radically different structural mechanics. Enforcing a single unified feature matrix leads to sparse, low-quality matrices. I engineered two dedicated pipelines:

#### 🐦 Twitter / X Pipeline Architecture (`build_twitter.py`)
- **Dataset**: 64,919 Unique Accounts (41,948 Genuine / 22,971 Fake).
- **Core Features (18 Features)**: `followers`, `following`, `post_count`, `log_followers`, `log_following`, `log_post_count`, `verified`, `description_length`, `account_age_days`, `follower_following_ratio`, `following_followers_ratio`, `reputation_score`, `username_length`, `digits_in_username`, `digit_ratio_username`, `consonant_ratio_username`, `has_url`, `posts_per_day`.

#### 📸 Meta / Instagram Pipeline Architecture (`build_meta.py`)
- **Dataset**: 36,383 Unique Accounts (16,343 Genuine / 20,040 Fake).
- **Core Features (12 Features)**: `followers`, `following`, `post_count`, `log_followers`, `log_following`, `log_post_count`, `has_profile_pic`, `bio_length`, `profile_pic_bio_score`, `follower_following_ratio`, `following_followers_ratio`, `reputation_score`.

---

### Final Benchmark Leaderboards

#### 🐦 Twitter Dataset Leaderboard (64,919 Accounts)
| Rank | Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Inference Time |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **Soft-Voting Ensemble (RF+XGB+ET)** | **90.47%** | **88.50%** | **83.96%** | **86.17%** | 2.81s |
| 🥈 | **Random Forest** | 90.16% | 88.15% | 83.41% | 85.72% | 1.12s |
| 🥉 | **Tuned XGBoost (Production Champion)** | **90.04%** | **87.47%** | **83.87%** | **85.63%** | **0.21s** |
| 4 | Extra Trees Classifier | 89.99% | 88.48% | 82.43% | 85.35% | 0.42s |
| 5 | Neural Network (MLP) | 87.82% | 85.16% | 79.43% | 82.19% | 26.89s |
| 6 | Logistic Regression (Baseline) | 81.64% | 76.78% | 68.96% | 72.66% | 0.02s |

#### 📸 Meta / Instagram Dataset Leaderboard (36,383 Accounts)
| Rank | Model | Accuracy | Precision (Fake) | Recall (Fake) | F1-Score | Inference Time |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **Soft-Voting Ensemble (RF+XGB+ET)** | **97.05%** | **97.57%** | **97.06%** | **97.31%** | 1.63s |
| 🥈 | **Random Forest** | 97.02% | 97.59% | 96.98% | 97.28% | 0.37s |
| 🥉 | **Extra Trees Classifier** | 96.91% | 97.68% | 96.68% | 97.18% | 0.15s |
| 4 | **Tuned XGBoost (Production Champion)** | **96.87%** | **97.23%** | **97.08%** | **97.15%** | **0.15s** |
| 5 | Neural Network (MLP) | 96.26% | 95.92% | 97.36% | 96.63% | 4.35s |
| 6 | Logistic Regression (Baseline) | 89.05% | 90.21% | 89.87% | 90.04% | 0.02s |

---

### Production Explainability & Real-Time Risk Engine (`explain.py`)

The inference engine receives raw account feature dictionaries and executes the following pipeline:
1. **Dynamic Platform Routing**: Autodetects platform context (`twitter` vs `meta`).
2. **Feature Imputation & Log Preprocessing**: Computes `log_followers`, `log_following`, `following_followers_ratio`, `consonant_ratio_username`, and `profile_pic_bio_score` dynamically on raw payload inputs.
3. **Probability Scoring & 3-Class Categorization**:
   - `Risk Score < 30%` ➔ **`REAL`**
   - `30% <= Risk Score <= 70%` ➔ **`SUSPICIOUS`**
   - `Risk Score > 70%` ➔ **`FAKE`**
4. **SHAP Natural Language Reasons**: Translates positive SHAP decision tree contributions into human-readable English:
   - ❌ *"Unpronounceable consonant pattern in username (0.86)."*
   - ❌ *"Aggressive mass-following ratio relative to followers (42.5)."*
   - ❌ *"Incomplete profile credentials (no avatar or bio)."*
