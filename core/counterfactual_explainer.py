
import pandas as pd
import numpy as np
import dice_ml
import json
import logging
import numexpr as ne
from typing import List, Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

class CounterfactualExplainer:
    """
    Wrapper for DiCE to generate counterfactual explanations with strict constraint validation.
    Includes advanced features: L0/L1 scoring, numexpr custom rules, and global batch reporting.
    """
    
    def __init__(self, model, data: pd.DataFrame, target_column: str = 'target', 
                 continuous_features: List[str] = None, categorical_features: List[str] = None, 
                 backend: str = 'sklearn', constraints_path: str = 'core/constraints.json'):
        """
        Initialize DiCE explainer and load constraints.
        """
        self.model = model
        self.data = data
        self.target_column = target_column
        self.continuous_features = continuous_features or []
        self.categorical_features = categorical_features or []
        self.backend = backend
        
        # Load constraints
        self.constraints = self._load_constraints(constraints_path)
        
        # Initialize DiCE Data
        # Ensure data does not contain the target if it's separate, but DiCE usually handles dataframe with target
        self.d = dice_ml.Data(
            dataframe=data, 
            continuous_features=self.continuous_features, 
            outcome_name=target_column
        )
        
        # Initialize DiCE Model
        self.m = dice_ml.Model(model=model, backend=backend)
        
        # Initialize DiCE Explainer
        # method="random" is faster and deterministic with seed
        self.exp = dice_ml.Dice(self.d, self.m, method="random")
        
    def _load_constraints(self, path: str) -> Dict:
        """Loads validation rules from JSON file."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load constraints from {path}: {e}. Using defaults.")
            return {}

    def explain_instance(self, query_instances: pd.DataFrame, total_CFs: int = 3, target_class: int = 1) -> Dict[str, Any]:
        """
        Generates, validates, and ranks counterfactuals for specific instances (Batch Support).

        Returns dictionary with:
        - explanations: List of per-instance results
        - global_constraints_report: Aggregate rejection reasons
        - validity_summary: Text summary
        """
        explanations = []
        all_rejections = []
        valid_count = 0
        
        # Loop through each instance if batch
        for idx, row in query_instances.iterrows():
            instance_df = pd.DataFrame([row]) 

            try:
                # 1. Generate Raw Counterfactuals
                # Request 2x to have buffer for validation filtering
                raw_cfs_object = self.exp.generate_counterfactuals(
                    query_instances=instance_df, 
                    total_CFs=total_CFs * 2, 
                    desired_class=target_class
                )
                
                # Check for empty results
                if not hasattr(raw_cfs_object, 'cf_examples_list') or not raw_cfs_object.cf_examples_list:
                     explanations.append({
                        "original_id": idx,
                        "error": "No counterfactuals found."
                    })
                     continue
                
                raw_cfs_df = raw_cfs_object.cf_examples_list[0].final_cfs_df
                
                if raw_cfs_df is None or raw_cfs_df.empty:
                     explanations.append({
                        "original_id": idx,
                        "error": "No counterfactuals found capable of flipping the prediction."
                    })
                     continue

                # 2. Validate Constraints (Existing + Custom Rules)
                valid_cfs, rejections = self.validate_constraints(instance_df, raw_cfs_df)
                all_rejections.extend(rejections)
                
                valid_count += len(valid_cfs)

                # 3. Calculate Scores (L1 + L0) & Rank
                ranked_cfs = self.rank_counterfactuals(instance_df, valid_cfs)
                
                # 4. Format Output
                explanation = {
                    "original_id": idx,
                    "original_features": row.to_dict(),
                    "counterfactuals": ranked_cfs[:total_CFs],
                    "validity_summary": f"{len(valid_cfs)} valid, {len(rejections)} rejected",
                    "constraints_report": self.constraints_report(rejections)
                } 
                explanations.append(explanation)
                
            except Exception as e:
                logger.error(f"Error explaining instance {idx}: {e}")
                explanations.append({
                    "original_id": idx,
                    "error": str(e)
                })

        # Global Summary
        global_report = self.constraints_report(all_rejections)
        
        return {
            "explanations": explanations,
            "global_constraints_report": global_report,
            "validity_summary": f"{valid_count} valid CFs generated across batch. {len(all_rejections)} rejected."
        }

    def validate_constraints(self, original_instance: pd.DataFrame, cfs_df: pd.DataFrame):
        """
        Filters out unrealistic counterfactuals based on defined constraints.
        Includes fast custom rule evaluation via numexpr.
        """
        valid_cfs = []
        rejections = []
        
        original_dict = original_instance.iloc[0].to_dict()
        
        feature_constraints = self.constraints.get('features', {})
        cat_constraints = self.constraints.get('categorical_features', {})
        custom_rules = self.constraints.get('custom_rules', [])

        if cfs_df is None:
             return valid_cfs, rejections

        for _, cf_row in cfs_df.iterrows():
            cf_dict = cf_row.to_dict()
            is_valid = True
            reasons = []
            
            # Check Numerical Constraints (Min/Max/Monotonicity)
            for feature, rules in feature_constraints.items():
                if feature in cf_dict:
                    val = cf_dict[feature]
                    
                    if 'min' in rules and val < rules['min']:
                        is_valid = False
                        reasons.append(f"{feature}_below_min")
                    if 'max' in rules and val > rules['max']:
                        is_valid = False
                        reasons.append(f"{feature}_above_max")
                    
                    # Monotonicity checks
                    if not rules.get('can_decrease', True) and val < original_dict[feature]:
                        is_valid = False
                        reasons.append(f"{feature}_decreased")
                    if not rules.get('can_increase', True) and val > original_dict[feature]:
                        is_valid = False
                        reasons.append(f"{feature}_increased")

            # Check Categorical Constraints (Immutable/Allowed)
            for feature, rules in cat_constraints.items():
                if feature in cf_dict:
                    val = cf_dict[feature]
                    
                    if rules.get('immutable', False) and val != original_dict[feature]:
                        is_valid = False
                        reasons.append(f"{feature}_changed_immutable")
                        
                    if 'allowed_values' in rules and val not in rules['allowed_values']:
                        is_valid = False
                        reasons.append(f"{feature}_invalid_value")
            
            # Check Custom Rules (numexpr)
            # Context for expression: 'cf' refers to counterfactual value, 'original' to original value
            for rule in custom_rules:
                try:
                    expr = rule['expr']
                    # We need to construct a local dict for numexpr where keys match the expression variables
                    # Assuming expression like "cf_age >= original_age"
                    # But simpler is "age_cf >= age_orig" or creating specific dicts
                    
                    # Safer approach for generic expressions:
                    # Let user define expression using feature names. 
                    # We prefix them in the local dict: "cf_featurename" and "original_featurename"
                    
                    # Actually, blueprint suggested: "cf.age >= original.age"
                    # numexpr doesn't handle object attributes easily.
                    # Best to map specific variables. 
                    # Let's support simple syntax: "cf_age >= original_age"
                    
                    # We will create a flat dict for evaluation
                    eval_dict = {}
                    for k, v in cf_dict.items():
                        eval_dict[f"cf_{k}"] = v
                    for k, v in original_dict.items():
                        eval_dict[f"original_{k}"] = v
                        
                    # Evaluate
                    if not ne.evaluate(expr, local_dict=eval_dict):
                        is_valid = False
                        reasons.append(f"custom_rule_{rule['name']}")
                        
                except Exception as e:
                    logger.warning(f"Failed to evaluate custom rule {rule.get('name')}: {e}")
                    # Don't reject on eval error, but log it.

            if is_valid:
                valid_cfs.append(cf_dict)
            else:
                rejections.extend(reasons)
                
        return valid_cfs, rejections

    def rank_counterfactuals(self, original_instance: pd.DataFrame, valid_cfs: List[Dict]) -> List[Dict]:
        """
        Ranks valid counterfactuals by a composite score (Primary: L0, Secondary: L1).
        """
        ranked = []
        original_dict = original_instance.iloc[0].to_dict()
        
        for cf in valid_cfs:
            score_l1, score_l0, changes = self.calculate_minimal_change(original_dict, cf)
            ranked.append({
                "counterfactual": cf,
                "changes": changes,
                "minimal_change_score": score_l1, # Keeping the name for compatibility
                "score_l0": score_l0,
                "score_l1": score_l1
            })
            
        # Sort by L0 (fewest changes) then L1 (smallest magnitude)
        ranked.sort(key=lambda x: (x['score_l0'], x['score_l1']))
        return ranked

    def calculate_minimal_change(self, original: Dict, counterfactual: Dict) -> tuple:
        """
        Calculates heuristic scores.
        L0: Number of changed features.
        L1: Magnitude of difference (normalized for numerical).
        """
        score_l1 = 0.0
        score_l0 = 0
        changes = {}
        
        for feat, val in counterfactual.items():
            if feat == self.target_column:
                continue
                
            orig_val = original.get(feat)
            if val != orig_val:
                changes[feat] = val
                score_l0 += 1
                
                # Check numeric vs categorical
                if isinstance(val, (int, float)) and isinstance(orig_val, (int, float)):
                    if orig_val != 0:
                        diff = abs(val - orig_val) / abs(orig_val)
                        score_l1 += diff
                    else:
                        score_l1 += 1.0 # arbitrary penalty for 0 baseline
                else:
                    score_l1 += 0.5 # Penalty for categorical change
                    
        return round(score_l1, 4), score_l0, changes

    def constraints_report(self, rejections: List[str]) -> Dict[str, int]:
        """Summarizes rejection reasons."""
        report = {}
        for r in rejections:
            report[r] = report.get(r, 0) + 1
        return report

    def constraints_report_summary(self, all_explanations: List[Dict]) -> Dict[str, int]:
        """
        Aggregates rejection reasons across multiple instances (Batch Summary).
        """
        summary = {}
        for exp in all_explanations:
            if 'constraints_report' in exp:
                for reason, count in exp['constraints_report'].items():
                    summary[reason] = summary.get(reason, 0) + count
        return summary
