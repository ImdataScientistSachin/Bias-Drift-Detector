import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from fastapi.testclient import TestClient
import sys
import os
import json

# Add parent dir to path to import main from api
# This allows us to run the script from the project root or the examples directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app
import shap

def run_demo():
    """
    Runs an end-to-end demo of the Bias Drift Detector system.
    1. Loads Adult Income dataset.
    2. Trains a Logistic Regression model.
    3. Registers the model with the API.
    4. Simulates data drift (Age shift).
    5. Logs predictions to the API.
    6. Fetches and displays drift/bias metrics.
    """
    print("--- Starting Bias Drift Detector Demo ---")
    
    print("1. Loading Adult dataset...")
    # shap.datasets.adult returns (X, y)
    # display=True returns raw data which is better for simulating drift on original features
    X_display, y_display = shap.datasets.adult(display=True)
    
    # Define feature groups
    numerical_features = ['Age', 'Education-Num', 'Capital Gain', 'Capital Loss', 'Hours per week']
    categorical_features = ['Workclass', 'Marital Status', 'Occupation', 'Relationship', 'Race', 'Sex', 'Country']
    
    # Verify columns exist to avoid runtime errors
    missing_cols = [c for c in numerical_features + categorical_features if c not in X_display.columns]
    if missing_cols:
        print(f"Warning: Missing columns in dataset: {missing_cols}")
        # Adjust features to what's available
        numerical_features = [c for c in numerical_features if c in X_display.columns]
        categorical_features = [c for c in categorical_features if c in X_display.columns]
    
    data = X_display.copy()
    data['Income'] = y_display # 0 or 1 (False/True)
    
    # Split Data
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
    
    print("2. Training model (Logistic Regression)...")
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    
    clf = Pipeline(steps=[('preprocessor', preprocessor),
                          ('classifier', LogisticRegression(max_iter=1000))])
    
    clf.fit(train_data.drop('Income', axis=1), train_data['Income'])
    
    # Initialize API Client
    client = TestClient(app)
    
    print("3. Registering model with API...")
    baseline_sample = train_data.sample(500)
    
    # Robust Serialization Helper
    def to_serializable(val):
        if isinstance(val, (np.integer, np.int64)):
            return int(val)
        if isinstance(val, (np.floating, np.float64)):
            return float(val)
        if isinstance(val, np.ndarray):
            return val.tolist()
        if pd.isna(val):
            return None
        return val

    # Prepare baseline data for JSON payload
    # We convert to dict records, then sanitize every value
    baseline_records_raw = baseline_sample.drop('Income', axis=1).to_dict(orient='records')
    baseline_records = []
    for record in baseline_records_raw:
        clean_record = {k: to_serializable(v) for k, v in record.items()}
        baseline_records.append(clean_record)
    
    register_payload = {
        "model_id": "adult_v1",
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "sensitive_attributes": ["Sex", "Race"],
        "baseline_data": baseline_records
    }
    
    resp = client.post("/api/v1/models/register", json=register_payload)
    if resp.status_code != 200:
        print(f"Error registering model: {resp.text}")
        return
    print(f"   Success: {resp.json()}")
    
    print("4. Simulating drift (increasing Age in test data by 20 years)...")
    drifted_data = test_data.copy()
    if 'Age' in drifted_data.columns:
        drifted_data['Age'] = drifted_data['Age'] + 20 
    
    print("5. Logging predictions to API...")
    # Log enough to trigger analysis (threshold is 100)
    for i in range(150): 
        row = drifted_data.iloc[i]
        features_raw = row.drop('Income').to_dict()
        
        # Sanitize features
        features = {k: to_serializable(v) for k, v in features_raw.items()}
        
        # Predict
        df_row = pd.DataFrame([features])
        # Ensure types match training expectations (some might have been cast to None/float during sanitization if NaNs existed)
        # For this demo, we assume data is clean enough or model handles it.
        
        try:
            pred = int(clf.predict(df_row)[0])
        except Exception:
            # Fallback if prediction fails on modified data
            pred = 0
        
        # True label
        true_label = row['Income']
        if isinstance(true_label, bool):
            true_label = 1 if true_label else 0
        
        log_entry = {
            "model_id": "adult_v1",
            "features": features,
            "prediction": pred,
            "true_label": int(true_label),
            "sensitive_features": {"Sex": features.get('Sex'), "Race": features.get('Race')}
        }
        
        client.post("/api/v1/predictions/log", json=log_entry)
        
        if i % 50 == 0:
            print(f"   Logged {i} predictions...")
        
    print("6. Fetching analysis metrics...")
    resp = client.get("/api/v1/metrics/adult_v1")
    metrics = resp.json()
    
    print("\n--- Analysis Results ---")
    print(f"Total Predictions Analyzed: {metrics['total_predictions']}")
    
    drift_alerts = [d for d in metrics['drift_analysis'] if d['alert']]
    print(f"\n[Drift Alerts] Found {len(drift_alerts)} significant drifts:")
    for d in drift_alerts:
        print(f"   - {d['feature']} ({d['metric']}): Score={d['score']:.4f}, P-value={d['p_value']:.4f}")
        
    bias_score = metrics['bias_analysis'].get('fairness_score')
    print(f"\n[Fairness Score] {bias_score}/100")
    
    if 'Sex' in metrics['bias_analysis']:
        di_sex = metrics['bias_analysis']['Sex']['disparate_impact']
        print(f"   - Disparate Impact (Sex): {di_sex:.4f} (Target > 0.8)")
    
    if metrics.get('root_cause_report'):
        print(f"\n[Root Cause Report]\n{metrics['root_cause_report']}")

if __name__ == "__main__":
    run_demo()
