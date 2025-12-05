import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import requests
import time
import shap

# Configuration
API_URL = "http://localhost:8000/api/v1"

def run_live_demo():
    print(f"--- Connecting to API at {API_URL} ---")
    
    # Check if API is running
    try:
        requests.get(f"{API_URL.replace('/api/v1', '')}/docs")
        print("API is online.")
    except requests.exceptions.ConnectionError:
        print("Error: API is not running. Please run 'python api/main.py' in a separate terminal.")
        return

    print("1. Loading Adult dataset...")
    X_display, y_display = shap.datasets.adult(display=True)
    
    numerical_features = ['Age', 'Education-Num', 'Capital Gain', 'Capital Loss', 'Hours per week']
    categorical_features = ['Workclass', 'Marital Status', 'Occupation', 'Relationship', 'Race', 'Sex', 'Country']
    
    # Filter columns
    numerical_features = [c for c in numerical_features if c in X_display.columns]
    categorical_features = [c for c in categorical_features if c in X_display.columns]
    
    data = X_display.copy()
    data['Income'] = y_display
    
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
    
    print("2. Training model...")
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
    
    print("3. Registering model...")
    baseline_sample = train_data.sample(500)
    
    def to_serializable(val):
        if isinstance(val, (np.integer, np.int64)): return int(val)
        if isinstance(val, (np.floating, np.float64)): return float(val)
        if isinstance(val, np.ndarray): return val.tolist()
        if pd.isna(val): return None
        return val

    baseline_records = []
    for record in baseline_sample.drop('Income', axis=1).to_dict(orient='records'):
        baseline_records.append({k: to_serializable(v) for k, v in record.items()})
    
    register_payload = {
        "model_id": "adult_v1",
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "sensitive_attributes": ["Sex", "Race"],
        "baseline_data": baseline_records
    }
    
    resp = requests.post(f"{API_URL}/models/register", json=register_payload)
    print(f"   Response: {resp.json()}")
    
    print("4. Simulating drift & Logging predictions...")
    drifted_data = test_data.copy()
    if 'Age' in drifted_data.columns:
        drifted_data['Age'] = drifted_data['Age'] + 20 
    
    # Log 200 predictions to ensure we trigger analysis twice
    for i in range(200): 
        row = drifted_data.iloc[i]
        features = {k: to_serializable(v) for k, v in row.drop('Income').to_dict().items()}
        
        df_row = pd.DataFrame([features])
        try:
            pred = int(clf.predict(df_row)[0])
        except:
            pred = 0
            
        true_label = 1 if row['Income'] else 0
        
        log_entry = {
            "model_id": "adult_v1",
            "features": features,
            "prediction": pred,
            "true_label": true_label,
            "sensitive_features": {"Sex": features.get('Sex'), "Race": features.get('Race')}
        }
        
        requests.post(f"{API_URL}/predictions/log", json=log_entry)
        
        if i % 50 == 0:
            print(f"   Logged {i} predictions...")
            time.sleep(0.1) # Small delay to be nice
            
    print("Done! Data populated. Check the dashboard.")

if __name__ == "__main__":
    run_live_demo()
