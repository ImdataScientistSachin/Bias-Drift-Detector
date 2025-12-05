from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
from core.drift_detector import DriftDetector
from core.bias_analyzer import BiasAnalyzer
from core.root_cause import RootCauseAnalyzer
import json
import os
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Initialize the FastAPI application
app = FastAPI(
    title="Bias Drift Guardian API v1",
    description="API for monitoring AI model drift and bias in real-time."
)

# Persistence paths
PERSISTENCE_DIR = Path("data/registry")
PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)

# Global registry (In-memory with file backup)
# In production, use PostgreSQL + Redis
model_registry = {}

# ============================================================================
# DATA MODELS (Pydantic Schemas)
# ============================================================================

class PredictionLog(BaseModel):
    """Schema for logging a single prediction."""
    model_id: str
    features: Dict[str, Any]
    prediction: int
    true_label: Optional[int] = None
    sensitive_features: Optional[Dict[str, Any]] = None


class ModelConfig(BaseModel):
    """Schema for registering a new model for monitoring."""
    model_id: str
    numerical_features: List[str]
    categorical_features: List[str]
    sensitive_attributes: List[str]
    baseline_data: List[Dict[str, Any]]  # List of records (dicts)

# ============================================================================
# PERSISTENCE FUNCTIONS
# ============================================================================

def save_model_config(model_id: str):
    """
    Saves a single model's configuration and logs to disk.
    Uses JSON for configs and logs (human-readable and debuggable).
    """
    try:
        entry = model_registry.get(model_id)
        if not entry:
            return
        
        model_dir = PERSISTENCE_DIR / model_id
        model_dir.mkdir(exist_ok=True)
        
        # Save configuration
        config_data = {
            "model_id": entry['config'].model_id,
            "numerical_features": entry['config'].numerical_features,
            "categorical_features": entry['config'].categorical_features,
            "sensitive_attributes": entry['config'].sensitive_attributes,
        }
        with open(model_dir / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)
        
        # Save baseline data as CSV (more efficient for DataFrames)
        baseline_df = entry['detector'].baseline_data
        if baseline_df is not None and not baseline_df.empty:
            baseline_df.to_csv(model_dir / "baseline.csv", index=False)
        
        # Save logs as JSON
        with open(model_dir / "logs.json", "w") as f:
            json.dump(entry['logs'], f, indent=2)
        
        # Save analysis results if they exist
        if 'drift_analysis' in entry:
            with open(model_dir / "drift_analysis.json", "w") as f:
                json.dump(entry['drift_analysis'], f, indent=2)
        
        if 'bias_analysis' in entry:
            with open(model_dir / "bias_analysis.json", "w") as f:
                json.dump(entry['bias_analysis'], f, indent=2, default=str)
        
        print(f"✅ Saved model '{model_id}' to {model_dir}")
        
    except Exception as e:
        print(f"❌ Error saving model '{model_id}': {e}")


def load_all_models():
    """
    Loads all models from disk on startup.
    Reconstructs detector and analyzer objects from saved configs.
    """
    global model_registry
    
    if not PERSISTENCE_DIR.exists():
        print("📁 No persistence directory found. Starting fresh.")
        return
    
    loaded_count = 0
    for model_dir in PERSISTENCE_DIR.iterdir():
        if not model_dir.is_dir():
            continue
        
        try:
            model_id = model_dir.name
            
            # Load config
            with open(model_dir / "config.json", "r") as f:
                config_data = json.load(f)
            
            # Load baseline data
            baseline_df = pd.read_csv(model_dir / "baseline.csv")
            
            # Load logs
            logs = []
            if (model_dir / "logs.json").exists():
                with open(model_dir / "logs.json", "r") as f:
                    logs = json.load(f)
            
            # Reconstruct objects
            detector = DriftDetector(
                baseline_data=baseline_df,
                numerical_features=config_data['numerical_features'],
                categorical_features=config_data['categorical_features']
            )
            
            analyzer = BiasAnalyzer(
                sensitive_attrs=config_data['sensitive_attributes']
            )
            
            root_analyzer = RootCauseAnalyzer()
            
            # Reconstruct config object
            config = ModelConfig(
                model_id=config_data['model_id'],
                numerical_features=config_data['numerical_features'],
                categorical_features=config_data['categorical_features'],
                sensitive_attributes=config_data['sensitive_attributes'],
                baseline_data=baseline_df.to_dict(orient='records')
            )
            
            # Store in registry
            model_registry[model_id] = {
                'config': config,
                'detector': detector,
                'analyzer': analyzer,
                'root_cause': root_analyzer,
                'logs': logs,
                'model_artifact': None
            }
            
            # Load analysis results if they exist
            if (model_dir / "drift_analysis.json").exists():
                with open(model_dir / "drift_analysis.json", "r") as f:
                    model_registry[model_id]['drift_analysis'] = json.load(f)
            
            if (model_dir / "bias_analysis.json").exists():
                with open(model_dir / "bias_analysis.json", "r") as f:
                    model_registry[model_id]['bias_analysis'] = json.load(f)
            
            loaded_count += 1
            print(f"✅ Loaded model '{model_id}' ({len(logs)} logs)")
            
        except Exception as e:
            print(f"❌ Error loading model from {model_dir}: {e}")
    
    print(f"📊 Loaded {loaded_count} model(s) from disk")

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load persisted models on startup."""
    print("🚀 Starting Bias Drift Guardian API...")
    load_all_models()
    print(f"📋 Active models: {list(model_registry.keys())}")


@app.on_event("shutdown")
async def shutdown_event():
    """Save all models on shutdown."""
    print("💾 Saving all models before shutdown...")
    for model_id in model_registry.keys():
        save_model_config(model_id)
    print("👋 Shutdown complete")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/api/v1/models/register")
async def register_model(config: ModelConfig):
    """
    Registers a new model with its baseline data and configuration.
    Initializes the DriftDetector and BiasAnalyzer for this model.
    """
    try:
        # Convert list of dicts back to DataFrame for internal use
        baseline_df = pd.DataFrame(config.baseline_data)
        
        # Initialize Core Components
        detector = DriftDetector(
            baseline_data=baseline_df,
            numerical_features=config.numerical_features,
            categorical_features=config.categorical_features
        )
        
        analyzer = BiasAnalyzer(sensitive_attrs=config.sensitive_attributes)
        root_analyzer = RootCauseAnalyzer()
        
        # Store in registry
        model_registry[config.model_id] = {
            'config': config,
            'detector': detector,
            'analyzer': analyzer,
            'root_cause': root_analyzer,
            'logs': [],
            'model_artifact': None
        }
        
        # Save immediately after registration
        save_model_config(config.model_id)
        
        return {"status": "registered", "model_id": config.model_id}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


@app.post("/api/v1/predictions/log")
async def log_prediction(log: PredictionLog, background_tasks: BackgroundTasks):
    """
    Logs a prediction event.
    Triggers analysis every N predictions to check for drift/bias.
    """
    if log.model_id not in model_registry:
        raise HTTPException(status_code=404, detail="Model not registered")
    
    # Store log in memory
    model_registry[log.model_id]['logs'].append(log.dict())
    
    # Trigger analysis periodically (every 100 predictions)
    if len(model_registry[log.model_id]['logs']) % 100 == 0:
        background_tasks.add_task(run_analysis, log.model_id)
        # Save to disk periodically
        background_tasks.add_task(save_model_config, log.model_id)
    
    return {"status": "logged", "timestamp": datetime.now()}


@app.get("/api/v1/models")
async def list_models():
    """Returns a list of all registered model IDs."""
    return {"models": list(model_registry.keys())}


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_count": len(model_registry),
        "timestamp": datetime.now()
    }


@app.get("/api/v1/metrics/{model_id}")
async def get_metrics(model_id: str):
    """
    Retrieves the latest drift and bias metrics for a specific model.
    Triggers an on-demand analysis.
    """
    if model_id not in model_registry:
        raise HTTPException(status_code=404, detail="Model not found")
    
    results = await run_analysis(model_id)
    return results

# ============================================================================
# ANALYSIS PIPELINE
# ============================================================================

async def run_analysis(model_id: str):
    """
    Internal function to run the full analysis pipeline:
    1. Drift Detection
    2. Bias Analysis
    3. Root Cause Analysis (if drift detected)
    """
    registry_entry = model_registry[model_id]
    logs = registry_entry['logs']
    
    if not logs:
        return {"status": "no_logs", "message": "No logs available for analysis."}
    
    logs_df = pd.DataFrame(logs)
    
    # Extract features from the nested dictionary
    features_df = pd.json_normalize(logs_df['features'].tolist())
    
    # 1. Detect Drift
    drift_results = registry_entry['detector'].detect_feature_drift(features_df)
    
    # 2. Calculate Bias
    preds = logs_df['prediction'].values
    true_labels = None
    if 'true_label' in logs_df.columns and logs_df['true_label'].notna().any():
        true_labels = logs_df['true_label'].fillna(-1).astype(int).values
    
    # Extract sensitive features
    if 'sensitive_features' in logs_df.columns:
        sens_list = logs_df['sensitive_features'].tolist()
        sens_list = [x if x is not None else {} for x in sens_list]
        sens_df = pd.json_normalize(sens_list)
    else:
        sens_df = pd.DataFrame()
    
    bias_metrics = registry_entry['analyzer'].calculate_bias_metrics(
        y_true=true_labels,
        y_pred=preds,
        sensitive_features=sens_df
    )
    
    # 3. Root Cause Analysis (Conditional)
    root_cause_report = None
    if not drift_results.empty and drift_results['alert'].any():
        if registry_entry['model_artifact']:
            rc_analysis = registry_entry['root_cause'].analyze_feature_importance_drift(
                model=registry_entry['model_artifact'],
                baseline_data=registry_entry['detector'].baseline_data,
                current_data=features_df
            )
            root_cause_report = registry_entry['root_cause'].generate_report(rc_analysis)
        else:
            root_cause_report = "Model artifact not available for SHAP analysis."
    
    # Store results back in registry so they persist
    registry_entry['drift_analysis'] = drift_results.to_dict(orient='records') if not drift_results.empty else []
    registry_entry['bias_analysis'] = bias_metrics
    registry_entry['root_cause_report'] = root_cause_report
    
    return {
        "model_id": model_id,
        "total_predictions": len(logs),
        "drift_analysis": registry_entry['drift_analysis'],
        "bias_analysis": registry_entry['bias_analysis'],
        "root_cause_report": registry_entry['root_cause_report'],
        "timestamp": datetime.now()
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)