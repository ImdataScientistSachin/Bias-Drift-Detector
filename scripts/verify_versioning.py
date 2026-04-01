from fastapi.testclient import TestClient
import sys
import os
import pandas as pd

# Add parent dir to path to import main from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.main import app

def verify_versioning():
    client = TestClient(app)
    
    # Baseline for registration
    baseline_data = [{"age": 25, "income": 50000}, {"age": 45, "income": 80000}]
    
    # 1. Register v1.0.0
    print("Registering model v1.0.0...")
    reg_v1 = {
        "model_id": "verify_test_model",
        "version": "1.0.0",
        "numerical_features": ["age", "income"],
        "categorical_features": [],
        "sensitive_attributes": ["age"],
        "baseline_data": baseline_data
    }
    resp1 = client.post("/api/v1/models/register", json=reg_v1)
    print(f"v1 Response: {resp1.json()}")
    
    # 2. Register v2.0.0
    print("\nRegistering model v2.0.0...")
    reg_v2 = reg_v1.copy()
    reg_v2["version"] = "2.0.0"
    resp2 = client.post("/api/v1/models/register", json=reg_v2)
    print(f"v2 Response: {resp2.json()}")
    
    # 3. List Versions
    print("\nListing Versions for 'verify_test_model'...")
    resp3 = client.get("/api/v1/models/verify_test_model/versions")
    print(f"Versions: {resp3.json()}")

if __name__ == "__main__":
    verify_versioning()
