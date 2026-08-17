import os
import time
import pandas as pd
import joblib
import warnings
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

# Suppress XGBoost deprecation warnings for clean output
warnings.filterwarnings(action='ignore', category=UserWarning)

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "saved")

def tune_xgboost():
    print("="*60)
    print("INITIATING XGBOOST HYPERPARAMETER TUNING")
    print("="*60)

    # 1. Load Data
    data_path = os.path.join(PROCESSED_DIR, "twitter_master.csv")
    df = pd.read_csv(data_path)
    
    X = df.drop(columns=['username', 'is_fake'])
    y = df['is_fake']

    # Calculate scale_pos_weight dynamically to combat class imbalance
    neg_class_count = (y == 0).sum()
    pos_class_count = (y == 1).sum()
    spw = round(neg_class_count / pos_class_count, 2)
    print(f"Dataset Imbalance Detected. Injecting scale_pos_weight: {spw}")

    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 2. Define the Hyperparameter Grid
    param_dist = {
        'max_depth': [5, 7, 10, 15],          # Depth of decision logic
        'learning_rate': [0.01, 0.05, 0.1],   # Step size for error correction
        'n_estimators': [200, 400, 600],      # Total number of trees
        'subsample': [0.7, 0.9, 1.0],         # Row sampling to prevent memorization
        'colsample_bytree': [0.7, 0.9, 1.0],  # Column sampling to force feature exploration
        'gamma': [0, 0.1, 0.5],               # Minimum loss reduction required to split a node
        'scale_pos_weight': [spw, spw * 1.5]  # Imbalance punishment modifier
    }

    # 3. Setup the Search Space
    xgb_base = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42, n_jobs=-1)
    
    # We explicitly optimize for F1 to balance catching bots without banning everyone.
    random_search = RandomizedSearchCV(
        estimator=xgb_base,
        param_distributions=param_dist,
        n_iter=20,          
        scoring='f1',       
        cv=3,               
        verbose=2,          
        n_jobs=-1,          
        random_state=42
    )

    print(f"\nStarting search across {len(X_train)} accounts... This will push your CPU.")
    start_time = time.time()
    
    random_search.fit(X_train, y_train)
    
    print(f"\nSearch Complete in {round((time.time() - start_time)/60, 2)} minutes.")

    # 4. Extract and Evaluate the Victor
    best_xgb = random_search.best_estimator_
    
    print("\n" + "="*60)
    print("WINNING HYPERPARAMETERS:")
    for key, val in random_search.best_params_.items():
        print(f"{key:>20}: {val}")
    print("="*60)

    y_pred = best_xgb.predict(X_test)
    
    print("\nTUNED MODEL PERFORMANCE ON UNSEEN DATA:")
    print(classification_report(y_test, y_pred, target_names=['Real (0)', 'Fake (1)']))
    
    # 5. Save the Tuned Model
    winner_path = os.path.join(SAVED_MODELS_DIR, "twitter_xgboost_tuned.pkl")
    joblib.dump(best_xgb, winner_path)
    print(f"\n[+] Saved tuned model to: {winner_path}")

if __name__ == "__main__":
    tune_xgboost()