from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
from core.drift_detector import DriftDetector
from core.bias_analyzer import BiasAnalyzer
from core.root_cause import RootCauseAnalyzer
from core.counterfactual_explainer import CounterfactualExplainer
from core.alerting import BiasAlertEngine, AlertConfig  # NEW: automated alerting
import json
import os
import uuid
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

# Global in-memory registry (backed by versioned file storage)
# Production upgrade path: replace with PostgreSQL + Redis
model_registry = {}

# Alerting Engine (initialized once at startup with env-driven config)
# Defaults to MOCK mode — no external accounts needed for local dev/demo
alert_engine = BiasAlertEngine(AlertConfig())

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
    version: str = "1.0.0"  # New: Support for multiple versions
    numerical_features: List[str]
    categorical_features: List[str]
    sensitive_attributes: List[str]
    target_column: Optional[str] = 'target'
    baseline_data: List[Dict[str, Any]]  # List of records (dicts)


class CounterfactualRequest(BaseModel):
    """Schema for requesting counterfactual explanations."""
    model_id: str
    instances: List[Dict[str, Any]]  # List of feature dictionaries
    total_CFs: Optional[int] = 3
    target_class: Optional[int] = 1

# ============================================================================
# PERSISTENCE FUNCTIONS
# ============================================================================

def save_model_config(model_id: str):
    """
    Saves a model's configuration and analysis to its versioned directory.
    Format: data/registry/{model_id}/{version}/
    """
    try:
        entry = model_registry.get(model_id)
        if not entry:
            return
        
        version = entry['config'].version
        model_dir = PERSISTENCE_DIR / model_id / version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        config_data = {
            "model_id": entry['config'].model_id,
            "version": version,
            "numerical_features": entry['config'].numerical_features,
            "categorical_features": entry['config'].categorical_features,
            "sensitive_attributes": entry['config'].sensitive_attributes,
        }
        with open(model_dir / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)
        
        # Save baseline data
        baseline_df = entry['detector'].baseline_data
        if baseline_df is not None and not baseline_df.empty:
            baseline_df.to_csv(model_dir / "baseline.csv", index=False)
        
        # Save logs
        with open(model_dir / "logs.json", "w") as f:
            json.dump(entry['logs'], f, indent=2)
        
        # Save analysis results
        if 'drift_analysis' in entry:
            with open(model_dir / "drift_analysis.json", "w") as f:
                json.dump(entry['drift_analysis'], f, indent=2)
        
        if 'bias_analysis' in entry:
            with open(model_dir / "bias_analysis.json", "w") as f:
                json.dump(entry['bias_analysis'], f, indent=2, default=str)
        
        print(f"✅ Saved model '{model_id}' [v{version}] to {model_dir}")
        
    except Exception as e:
        print(f"❌ Error saving model '{model_id}': {e}")


def load_all_models():
    """
    Loads all models from versioned directories on startup.
    Supports backward compatibility for legacy non-versioned models.
    """
    global model_registry
    
    if not PERSISTENCE_DIR.exists():
        print("📁 No persistence directory found. Starting fresh.")
        return
    
    loaded_count = 0
    # Iterate through model IDs
    for model_id_dir in PERSISTENCE_DIR.iterdir():
        if not model_id_dir.is_dir():
            continue
        
        # Look for versions inside the model ID directory
        versions = [v for v in model_id_dir.iterdir() if v.is_dir()]
        
        # If no version subfolders, check if the folder itself is a legacy model
        if not versions and (model_id_dir / "config.json").exists():
            load_model_from_path(model_id_dir)
            loaded_count += 1
            continue

        for v_dir in versions:
            if (v_dir / "config.json").exists():
                load_model_from_path(v_dir)
                loaded_count += 1
    
    print(f"📊 Loaded {loaded_count} model(s) from disk")


def load_model_from_path(model_dir: Path):
    """Utility to load a single model version from a specific directory."""
    try:
        # Load config
        with open(model_dir / "config.json", "r") as f:
            config_data = json.load(f)
        
        model_id = config_data['model_id']
        version = config_data.get('version', 'legacy')
        
        # Composite ID for internal registry (if multiple versions exist, 
        # we might need to handle which one's 'active'. For now, we load them.)
        registry_key = f"{model_id}:{version}" if version != 'legacy' else model_id
        
        # Load baseline data
        baseline_df = pd.read_csv(model_dir / "baseline.csv")
        
        # Initialize Core Components
        detector = DriftDetector(
            baseline_data=baseline_df,
            numerical_features=config_data['numerical_features'],
            categorical_features=config_data['categorical_features']
        )
        
        analyzer = BiasAnalyzer(sensitive_attrs=config_data['sensitive_attributes'])
        root_analyzer = RootCauseAnalyzer()
        
        # Reconstruct config object
        config = ModelConfig(
            model_id=model_id,
            version=version,
            numerical_features=config_data['numerical_features'],
            categorical_features=config_data['categorical_features'],
            sensitive_attributes=config_data['sensitive_attributes'],
            baseline_data=baseline_df.to_dict(orient='records')
        )
        
        # Store in registry
        model_registry[registry_key] = {
            'config': config,
            'detector': detector,
            'analyzer': analyzer,
            'root_cause': root_analyzer,
            'logs': [],
            'model_artifact': None
        }
        
        # Load logs and analysis if present
        if (model_dir / "logs.json").exists():
            with open(model_dir / "logs.json", "r") as f:
                model_registry[registry_key]['logs'] = json.load(f)
        
        if (model_dir / "drift_analysis.json").exists():
            with open(model_dir / "drift_analysis.json", "r") as f:
                model_registry[registry_key]['drift_analysis'] = json.load(f)
        
        if (model_dir / "bias_analysis.json").exists():
            with open(model_dir / "bias_analysis.json", "r") as f:
                model_registry[registry_key]['bias_analysis'] = json.load(f)
        
        print(f"✅ Loaded model '{model_id}' [v{version}]")
        
    except Exception as e:
        print(f"❌ Error loading model version from {model_dir}: {e}")

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


@app.post("/api/v1/explain/counterfactual")
async def generate_counterfactuals(request: CounterfactualRequest):
    """
    Generates counterfactual explanations (Batch Support).
    Returns minimal changes needed to flip prediction.
    """
    if request.model_id not in model_registry:
        raise HTTPException(status_code=404, detail="Model not found")
    
    entry = model_registry[request.model_id]
    
    # Initialize Explainer (Lazy Load)
    if 'cf_explainer' not in entry:
        if not entry.get('model_artifact'):
             # If no artifact, try to use a dummy model or raise error.
             # For this production-like code, we need a model.
             raise HTTPException(status_code=400, detail="Model artifact (sklearn/pipeline) not found in registry. Cannot initialize DiCE.")
        
        try:
            entry['cf_explainer'] = CounterfactualExplainer(
                model=entry['model_artifact'],
                data=entry['detector'].baseline_data,
                target_column=entry['config'].target_column,
                continuous_features=entry['config'].numerical_features,
                categorical_features=entry['config'].categorical_features
            )
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Failed to initialize DiCE: {str(e)}")

    explainer = entry['cf_explainer']
    
    # Prepare Data
    try:
        query_df = pd.DataFrame(request.instances)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid instance data: {str(e)}")
        
    # Check Batch Limit
    if len(query_df) > 20:
         raise HTTPException(status_code=400, detail="Batch size limit exceeded (Max 20 instances).")

    # Run Explanation
    try:
        result = explainer.explain_instance(
            query_instances=query_df, 
            total_CFs=request.total_CFs, 
            target_class=request.target_class
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")
    
    # Add API Metadata (Audit Ready)
    response = {
        "meta": {
            "request_id": str(uuid.uuid4()),
            "model_id": request.model_id,
            "timestamp": datetime.now().isoformat(),
            "model_version": "v1.0" 
        },
        "validity_summary": result.get("validity_summary"),
        "global_constraints_report": result.get("global_constraints_report"),
        "explanations": result.get("explanations")
    }
    
    return response


@app.get("/api/v1/models")
async def list_models():
    """Returns a list of all registered model IDs and their versions."""
    return {"models": list(model_registry.keys())}


@app.get("/api/v1/models/{model_id}/versions")
async def list_model_versions(model_id: str):
    """Returns all available versions for a specific model ID on disk."""
    model_path = PERSISTENCE_DIR / model_id
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model ID not found")
    
    versions = [d.name for d in model_path.iterdir() if d.is_dir()]
    return {"model_id": model_id, "versions": versions}


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_count": len(model_registry),
        "timestamp": datetime.now()
    }


@app.get("/api/v1/metrics/{model_id}")
async def get_metrics(model_id: str, background_tasks: BackgroundTasks):
    """
    Retrieves the latest drift and bias metrics for a specific model.
    Triggers an on-demand analysis, then fires automated alerts if thresholds
    are breached (PSI > 0.25 or Fairness Score < 80).

    ALERTING FLOW:
      Analysis runs → results checked → alert_engine.check_and_alert() called
      → dispatches to mock console, Slack, or email based on ALERT_MODE env var.
    """
    if model_id not in model_registry:
        raise HTTPException(status_code=404, detail="Model not found")

    results = await run_analysis(model_id)

    # Fire alerts asynchronously so the API response is not delayed
    # BackgroundTasks run AFTER the response is sent to the client
    background_tasks.add_task(alert_engine.check_and_alert, model_id, results)

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