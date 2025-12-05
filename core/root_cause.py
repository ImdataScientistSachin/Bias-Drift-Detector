import shap
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

class RootCauseAnalyzer:
    """
    The RootCauseAnalyzer uses SHAP (SHapley Additive exPlanations) to understand 
    why model behavior might be changing. It specifically looks for 'feature importance drift',
    which happens when the features driving the model's predictions change over time.
    """
    def __init__(self):
        pass
    
    def analyze_feature_importance_drift(self, model: Any, baseline_data: pd.DataFrame, current_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyzes how feature importance has changed between baseline and current data.
        Returns a dictionary with drift scores per feature and a list of top drifting features.
        """
        results = {}
        
        # Performance Optimization:
        # SHAP calculation can be very expensive. We sample the data to keep the 
        # API response time reasonable for this MVP.
        # In production, this should be done asynchronously on a larger sample.
        sample_size = min(100, len(baseline_data), len(current_data))
        if sample_size < 10:
             return {"error": "Not enough data for SHAP analysis"}

        baseline_sample = baseline_data.sample(sample_size)
        current_sample = current_data.sample(sample_size)
            
        try:
            # 1. Initialize Explainer
            # We try to use the most efficient explainer available.
            # TreeExplainer is fast for XGBoost/LightGBM/RF. KernelExplainer is generic but slow.
            try:
                explainer = shap.Explainer(model, baseline_sample)
            except Exception:
                # Fallback for models where generic Explainer fails or needs predict function explicitly
                if hasattr(model, 'predict'):
                    explainer = shap.KernelExplainer(model.predict, baseline_sample)
                else:
                    return {"error": "Could not initialize SHAP explainer. Model might not be compatible."}
            
            # 2. Calculate SHAP values
            # This tells us the contribution of each feature for every sample.
            shap_values_base = explainer(baseline_sample)
            shap_values_curr = explainer(current_sample)
            
            # 3. Aggregate SHAP values to get Global Feature Importance
            # We take the mean absolute value of SHAP values across the sample.
            def get_mean_abs_shap(shap_obj):
                if hasattr(shap_obj, 'values'):
                    vals = shap_obj.values
                else:
                    vals = shap_obj
                
                # Handle 3D array for classification (N_samples, N_features, N_classes)
                # For binary classification, we usually focus on the positive class (index 1).
                if len(vals.shape) == 3:
                    if vals.shape[2] > 1:
                        vals = vals[:, :, 1]
                    else:
                        vals = vals[:, :, 0]
                
                # Mean absolute value across samples
                return np.abs(vals).mean(axis=0)

            base_vals = get_mean_abs_shap(shap_values_base)
            curr_vals = get_mean_abs_shap(shap_values_curr)

            feature_names = baseline_data.columns
            
            # 4. Calculate Drift in Importance
            importance_drift = {}
            for i, feature in enumerate(feature_names):
                if i < len(base_vals) and i < len(curr_vals):
                    drift = curr_vals[i] - base_vals[i]
                    importance_drift[feature] = {
                        'baseline_importance': float(base_vals[i]),
                        'current_importance': float(curr_vals[i]),
                        'drift': float(drift)
                    }
            
            # Sort by absolute magnitude of drift to highlight the biggest changes
            sorted_drift = sorted(importance_drift.items(), key=lambda x: abs(x[1]['drift']), reverse=True)
            
            results = {
                'feature_importance_drift': dict(sorted_drift),
                'top_drifted_features': [x[0] for x in sorted_drift[:3]]
            }
            
        except Exception as e:
            print(f"SHAP analysis failed: {e}")
            results = {"error": str(e)}
            
        return results

    def generate_report(self, drift_analysis: Dict) -> str:
        """
        Generates a human-readable summary of the root cause analysis.
        """
        if 'error' in drift_analysis:
            return f"Root Cause Analysis Failed: {drift_analysis['error']}"
            
        top_features = drift_analysis.get('top_drifted_features', [])
        if not top_features:
            return "No significant feature importance drift detected."

        report = f"Root Cause Analysis:\n"
        report += f"The model's reliance on features has shifted. The following features showed the most significant change:\n"
        for feature in top_features:
            data = drift_analysis['feature_importance_drift'][feature]
            direction = "increased" if data['drift'] > 0 else "decreased"
            report += f"- **{feature}**: Importance {direction} by {abs(data['drift']):.4f} (Base: {data['baseline_importance']:.4f} -> Curr: {data['current_importance']:.4f})\n"
            
        report += "\nRecommendation: Investigate if the data distribution for these features has changed or if there is a new relationship in the data."
        return report