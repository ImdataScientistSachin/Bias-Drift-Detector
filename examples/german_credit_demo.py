import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.datasets import fetch_openml
from fastapi.testclient import TestClient
import sys
import os

# Add parent dir to path to import main from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app

def run_german_credit_demo():
    print("--- Starting German Credit Bias Drift Demo ---")
    
    print("1. Loading German Credit dataset (OpenML ID: 31)...")
    # Fetch German Credit data
    # Target: 'class' (good/bad)
    credit_data = fetch_openml(data_id=31, as_frame=True, parser='auto')
    X = credit_data.data
    y = credit_data.target
    
    # Preprocessing
    # Identify categorical and numerical columns
    # In this dataset, many are categorical strings
    categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
    numerical_features = X.select_dtypes(include=['number']).columns.tolist()
    
    print(f"   Numerical: {len(numerical_features)}, Categorical: {len(categorical_features)}")
    
    # Handle categorical encoding for the model (simple LabelEncoding for RF)
    X_encoded = X.copy()
    label_encoders = {}
    for col in categorical_features:
        le = LabelEncoder()
        # Convert to string to handle potential mixed types or categories
        X_encoded[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le
        
    # Encode target (good=1, bad=0)
    y_encoded = (y == 'good').astype(int)
    
    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(X_encoded, y_encoded, test_size=0.2, random_state=42)
    
    print("2. Training model (Random Forest)...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    # Initialize API Client
    client = TestClient(app)
    
    print("3. Registering model with API...")
    # We need to pass the ORIGINAL (unencoded) data for the baseline so the drift detector 
    # sees the actual categories, not just integers.
    # However, for the demo simplicity, let's pass the encoded data as "numerical" 
    # or we need to handle the decoding. 
    # BETTER APPROACH: Pass the raw X_train sample as baseline.
    
    baseline_sample_indices = X_train.sample(300).index
    baseline_sample_raw = X.loc[baseline_sample_indices].copy()
    
    # Helper for serialization
    def to_serializable(val):
        if isinstance(val, (np.integer, np.int64)): return int(val)
        if isinstance(val, (np.floating, np.float64)): return float(val)
        if pd.isna(val): return None
        return str(val) # Default to string for categories

    baseline_records = []
    for record in baseline_sample_raw.to_dict(orient='records'):
        baseline_records.append({k: to_serializable(v) for k, v in record.items()})
        
    # Sensitive attributes in German Credit: 'personal_status' (often proxies for sex/marital), 'age'
    # 'age' is numerical, so we might need to bin it for bias analysis if we want groups.
    # For this demo, let's use 'foreign_worker' as a proxy for bias check or 'personal_status'.
    
    register_payload = {
        "model_id": "german_credit_v1",
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "sensitive_attributes": ["foreign_worker", "personal_status"], 
        "baseline_data": baseline_records
    }
    
    resp = client.post("/api/v1/models/register", json=register_payload)
    print(f"   Register Status: {resp.status_code}")
    if resp.status_code != 200:
        print(resp.text)
        return

    print("4. Simulating Drift (Adding noise to 'credit_amount' and 'age')...")
    # Perturb data: Add 10% noise to numerical features
    X_test_drifted = X.loc[X_test.index].copy()
    
    # Drift 1: Shift Age (older population)
    X_test_drifted['age'] = X_test_drifted['age'] * 1.2 
    
    # Drift 2: Noise in Credit Amount
    noise = np.random.normal(0, 1000, size=len(X_test_drifted))
    X_test_drifted['credit_amount'] = X_test_drifted['credit_amount'] + noise
    
    print("5. Logging predictions...")
    # Create a DataFrame for prediction to avoid feature name warnings
    # We need to match the columns of X_train
    columns = X_encoded.columns
    
    for i in range(min(150, len(X_test_drifted))):
        row_raw = X_test_drifted.iloc[i]
        
        # Prepare features for API (Raw values)
        features_api = {k: to_serializable(v) for k, v in row_raw.to_dict().items()}
        
        # Prepare features for Model (Encoded values)
        row_encoded_dict = {}
        for col in columns:
            val = row_raw[col]
            if col in categorical_features:
                try:
                    val_enc = label_encoders[col].transform([str(val)])[0]
                except:
                    val_enc = 0 
                row_encoded_dict[col] = val_enc
            else:
                row_encoded_dict[col] = val
        
        # Create single-row DataFrame
        df_predict = pd.DataFrame([row_encoded_dict], columns=columns)
        
        pred = int(clf.predict(df_predict)[0])
        
        log_entry = {
            "model_id": "german_credit_v1",
            "features": features_api,
            "prediction": pred,
            "sensitive_features": {
                "foreign_worker": features_api.get("foreign_worker"),
                "personal_status": features_api.get("personal_status")
            }
        }
        
        client.post("/api/v1/predictions/log", json=log_entry)
        
        if i % 50 == 0:
            print(f"   Logged {i} predictions...")

    print("6. Fetching Metrics...")
    resp = client.get("/api/v1/metrics/german_credit_v1")
    if resp.status_code != 200:
        print(f"Error fetching metrics: {resp.text}")
        return
        
    metrics = resp.json()
    
    print("\n--- Analysis Results ---")
    drift_alerts = [d for d in metrics['drift_analysis'] if d['alert']]
    print(f"Drift Alerts: {len(drift_alerts)}")
    for d in drift_alerts:
        print(f"   - {d['feature']} ({d['metric']}): Score={d['score']:.4f}")
        
    print(f"Fairness Score: {metrics['bias_analysis'].get('fairness_score')}")

if __name__ == "__main__":
    run_german_credit_demo()
