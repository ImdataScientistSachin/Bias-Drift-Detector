"""
🚀 BIAS DRIFT GUARDIAN - MLOPS TRAINING PIPELINE
-----------------------------------------------
This script represents the "Training" phase of the MLOps lifecycle.
It logs experiments to MLflow, including hyperparameters and fairness metrics.

Author: AI MLOps Implementation Team
Style: Educational & Production-Ready (Humanoid)
"""

import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.datasets import fetch_openml
from sklearn.metrics import accuracy_score, f1_score
import sys
import os

# Add project root to path for core module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bias_analyzer import BiasAnalyzer

def train_and_log_experiment(n_estimators=100, max_depth=None):
    """
    Trains a model on the German Credit dataset and logs results to MLflow.
    We don't just track accuracy; we track FAIRNESS as a primary metric.
    """
    
    # 1. SETUP EXPERIMENT
    mlflow.set_experiment("German_Credit_Fairness_Audit")
    
    with mlflow.start_run():
        print(f"\n[RUN] Starting Run (n_estimators={n_estimators}, max_depth={max_depth})")
        
        # 2. DATA ACQUISITION & PREPROCESSING
        # German Credit is a classic dataset for bias analysis (vulnerable groups: age/sex)
        data = fetch_openml(data_id=31, as_frame=True, parser='auto')
        X = data.data
        y = (data.target == 'good').astype(int)
        
        # Encode categorical features for the Random Forest
        categorical_cols = X.select_dtypes(include=['object', 'category']).columns
        X_encoded = X.copy()
        
        for col in categorical_cols:
            le = LabelEncoder()
            X_encoded[col] = le.fit_transform(X[col].astype(str))
            
        X_train, X_test, y_train, y_test = train_test_split(
            X_encoded, y, test_size=0.2, random_state=42
        )
        
        # 3. MODEL TRAINING
        # We log hyperparameters to MLflow for reproducibility
        mlflow.log_params({
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "random_state": 42,
            "model_type": "RandomForestClassifier"
        })
        
        model = RandomForestClassifier(
            n_estimators=n_estimators, 
            max_depth=max_depth, 
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # 4. PREDICTION & TRADITIONAL METRICS
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        mlflow.log_metrics({
            "accuracy": acc,
            "f1_score": f1
        })
        print(f"DONE: Accuracy: {acc:.4f} | F1: {f1:.4f}")
        
        # 5. FAIRNESS AUDIT (MLOps Critical Step)
        # We use our own BiasAnalyzer to log "Fairness Scores" during training
        analyzer = BiasAnalyzer(sensitive_attrs=['foreign_worker', 'personal_status'])
        
        # Get raw sensitive features for the test set
        sensitive_df = X.loc[X_test.index][['foreign_worker', 'personal_status']]
        
        bias_results = analyzer.calculate_bias_metrics(
            y_true=y_test.values,
            y_pred=y_pred,
            sensitive_features=sensitive_df
        )
        
        fairness_score = bias_results.get('fairness_score', 0)
        mlflow.log_metric("fairness_score", fairness_score)
        print(f"SCORE: Fairness Score: {fairness_score}/100")
        
        # 6. LOG MODEL ARTIFACT
        # This allows us to "serve" this exact model through our API later
        mlflow.sklearn.log_model(model, "model")
        print(f"INFO: Model saved to MLflow artifacts.")

if __name__ == "__main__":
    # In a real MLOps pipeline, you might run a grid search here
    # For this demo, we run two distinct versions to show tracking in the UI
    train_and_log_experiment(n_estimators=50, max_depth=5)
    train_and_log_experiment(n_estimators=150, max_depth=10)
    
    print("\nTRAINING COMPLETE!")
    print("👉 To view the results, run: 'mlflow ui' and visit http://127.0.0.1:5000")
