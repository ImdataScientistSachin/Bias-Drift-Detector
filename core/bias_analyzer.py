"""
================================================================================
BIAS ANALYZER MODULE
================================================================================

This module is the heart of fairness monitoring. It calculates various metrics
to detect if your AI model is treating different groups unfairly.

Think of it like a "fairness referee" that watches your model's decisions and
flags when certain groups are being treated differently.

Key Concepts:
- Sensitive Attributes: Characteristics we want to ensure fairness across
  (e.g., gender, race, age)
- Selection Rate: How often the model predicts "yes" for a group
- Disparate Impact: Ratio comparing selection rates between groups
- Demographic Parity: Whether all groups get positive predictions at same rate

================================================================================
"""

from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference, selection_rate
from sklearn.metrics import accuracy_score
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any


class BiasAnalyzer:
    """
    🎯 PURPOSE:
    Evaluates whether your AI model is fair across different demographic groups.
    
    📊 WHAT IT DOES:
    - Calculates fairness metrics (Disparate Impact, Demographic Parity, etc.)
    - Compares how the model treats different groups (e.g., Male vs Female)
    - Generates an overall fairness score (0-100)
    
    🔍 EXAMPLE USE CASE:
    You have a hiring model. This analyzer checks if it's equally likely to
    recommend Male and Female candidates with similar qualifications.
    
    ⚠️ IMPORTANT:
    Lower fairness scores mean your model might be discriminating!
    """
    
    def __init__(self, sensitive_attrs: List[str]):
        """
        Initialize the analyzer with the attributes you want to monitor.
        
        Args:
            sensitive_attrs: List of column names representing sensitive groups
                           Examples: ['Sex', 'Race', 'Age_Group']
        
        Example:
            analyzer = BiasAnalyzer(sensitive_attrs=['Sex', 'Race'])
        """
        self.sens_attrs = sensitive_attrs
    
    
    def calculate_bias_metrics(
        self, 
        y_true: Optional[np.ndarray], 
        y_pred: np.ndarray, 
        sensitive_features: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        🎯 MAIN FUNCTION: Calculates all fairness metrics
        
        This is like running a comprehensive "fairness audit" on your model's
        predictions. It checks multiple aspects of fairness and returns a
        detailed report.
        
        Args:
            y_true: Actual labels (can be None if you don't have ground truth yet)
                   Example: [0, 1, 1, 0] where 1 = hired, 0 = not hired
            
            y_pred: Model's predictions (required)
                   Example: [1, 1, 0, 1] - what the model predicted
            
            sensitive_features: DataFrame with demographic info
                               Example:
                               | Sex    | Race  |
                               |--------|-------|
                               | Male   | White |
                               | Female | Black |
        
        Returns:
            Dictionary with:
            - Metrics for each sensitive attribute
            - Overall fairness score (0-100)
            - Group-by-group breakdown
        
        Example Output:
            {
                'Sex': {
                    'disparate_impact': 0.75,  # Male/Female selection ratio
                    'demographic_parity_difference': 0.15,  # Difference in rates
                    'by_group': {
                        'selection_rate': {'Male': 0.8, 'Female': 0.6}
                    }
                },
                'fairness_score': 60  # Overall score out of 100
            }
        """
        results = {}
        
        # ========================================================================
        # STEP 1: Input Validation and Preparation
        # ========================================================================
        
        # Handle case where sensitive_features is passed as a dict instead of DataFrame
        if isinstance(sensitive_features, dict):
            sensitive_features = pd.DataFrame(sensitive_features)
        
        # Convert to numpy arrays for consistent processing
        # (Some libraries expect numpy arrays, not lists or pandas Series)
        y_pred = np.array(y_pred)
        if y_true is not None:
            y_true = np.array(y_true)
        
        # ========================================================================
        # STEP 2: Calculate Metrics for Each Sensitive Attribute
        # ========================================================================
        
        for attr in self.sens_attrs:
            # Skip if this attribute isn't in the current data
            # (Maybe you're monitoring 'Race' but this batch doesn't have it)
            if attr not in sensitive_features.columns:
                continue
            
            # Get the column for this sensitive attribute
            # Example: sf_col = ['Male', 'Female', 'Male', 'Female']
            sf_col = sensitive_features[attr]
            
            # ====================================================================
            # METRIC 1: Demographic Parity Difference
            # ====================================================================
            # 📊 WHAT IT MEASURES:
            # The difference in selection rates between groups.
            # 
            # 🎯 IDEAL VALUE: 0 (all groups have same selection rate)
            # ⚠️ CONCERNING: > 0.1 (10% difference)
            #
            # EXAMPLE:
            # If 80% of Males get positive predictions but only 60% of Females,
            # the difference is 0.20 (20% disparity)
            
            # Fairlearn needs y_true for its API, but demographic parity
            # technically only needs predictions. We use a dummy if needed.
            y_dummy = y_true if y_true is not None else y_pred
            
            try:
                dp_diff = demographic_parity_difference(
                    y_dummy, y_pred, sensitive_features=sf_col
                )
            except Exception:
                # If calculation fails (e.g., only one group), default to 0
                dp_diff = 0.0
            
            # ====================================================================
            # METRIC 2: Disparate Impact (Four-Fifths Rule)
            # ====================================================================
            # 📊 WHAT IT MEASURES:
            # Ratio of selection rates between the least and most favored groups.
            #
            # 🎯 IDEAL VALUE: 1.0 (perfect equality)
            # ⚠️ CONCERNING: < 0.8 (violates the "Four-Fifths Rule")
            #
            # EXAMPLE:
            # Males: 80% selection rate
            # Females: 60% selection rate
            # Disparate Impact = 60/80 = 0.75 (below 0.8 threshold!)
            
            # Create a temporary DataFrame to calculate selection rates by group
            df_temp = pd.DataFrame({
                'pred': y_pred,
                'group': sf_col.values
            })
            
            # Calculate average prediction (selection rate) for each group
            # Example: {'Male': 0.8, 'Female': 0.6}
            sr_by_group = df_temp.groupby('group')['pred'].mean()
            
            # Handle edge case: if no positive predictions at all
            if len(sr_by_group) > 0 and sr_by_group.max() > 0:
                # Ratio of min to max selection rate
                disparate_impact = sr_by_group.min() / sr_by_group.max()
            else:
                # If no predictions or all zero, technically no disparity
                disparate_impact = 1.0
            
            # Store group-level metrics
            group_metrics = {
                'selection_rate': sr_by_group.to_dict()
            }
            
            # ====================================================================
            # METRIC 3: Equalized Odds Difference (Requires Ground Truth)
            # ====================================================================
            # 📊 WHAT IT MEASURES:
            # Difference in True Positive Rate (TPR) and False Positive Rate (FPR)
            # between groups.
            #
            # 🎯 IDEAL VALUE: 0 (model is equally accurate for all groups)
            # ⚠️ CONCERNING: > 0.1 (10% difference in error rates)
            #
            # EXAMPLE:
            # For qualified candidates:
            # - Model correctly identifies 90% of qualified Males
            # - Model correctly identifies 70% of qualified Females
            # → Equalized Odds Difference = 0.20 (unfair!)
            
            eo_diff = None
            
            # Only calculate if we have ground truth labels
            if y_true is not None:
                try:
                    # Calculate equalized odds difference
                    eo_diff = equalized_odds_difference(
                        y_true, y_pred, sensitive_features=sf_col
                    )
                    
                    # BONUS METRIC: Accuracy by group
                    # Helps identify if model performs worse for certain groups
                    df_temp['true'] = y_true
                    
                    # Calculate accuracy for each group
                    # We explicitly select columns to avoid pandas warnings
                    accuracy_by_group = df_temp.groupby('group')[['true', 'pred']].apply(
                        lambda x: accuracy_score(x['true'], x['pred'])
                    ).to_dict()
                    
                    group_metrics['accuracy'] = accuracy_by_group
                    
                except Exception as e:
                    # If calculation fails, log it but continue
                    print(f"⚠️ Error calculating Equalized Odds for {attr}: {e}")
            
            # ====================================================================
            # Store Results for This Attribute
            # ====================================================================
            results[attr] = {
                'by_group': group_metrics,
                'demographic_parity_difference': float(dp_diff),
                'equalized_odds_difference': float(eo_diff) if eo_diff is not None else None,
                'disparate_impact': float(disparate_impact)
            }
        
        # ========================================================================
        # STEP 3: Calculate Overall Fairness Score
        # ========================================================================
        # 🎯 PURPOSE:
        # Give a single number (0-100) that summarizes overall fairness.
        # Think of it like a "credit score" for your model's fairness.
        #
        # 📊 SCORING:
        # - Start at 100 (perfect fairness)
        # - Subtract points for each fairness violation
        # - Minimum score is 0
        #
        # 🚦 INTERPRETATION:
        # 80-100: Excellent fairness ✅
        # 60-79:  Good fairness 👍
        # 40-59:  Moderate concerns ⚠️
        # 0-39:   Significant bias issues ❌
        
        score = 100
        
        for attr, metrics in results.items():
            # Penalty 1: Demographic Parity violation (-20 points)
            # If selection rates differ by more than 10%
            if metrics['demographic_parity_difference'] > 0.1:
                score -= 20
            
            # Penalty 2: Disparate Impact violation (-20 points)
            # If ratio is below the 0.8 threshold (Four-Fifths Rule)
            if metrics['disparate_impact'] < 0.8:
                score -= 20
            
            # Penalty 3: Equalized Odds violation (-10 points)
            # If error rates differ by more than 10%
            if (metrics['equalized_odds_difference'] is not None and 
                metrics['equalized_odds_difference'] > 0.1):
                score -= 10
        
        # Ensure score doesn't go below 0
        results['fairness_score'] = max(0, score)
        
        return results


# ================================================================================
# USAGE EXAMPLE
# ================================================================================
"""
# Example: Analyzing a hiring model

import pandas as pd
import numpy as np

# Your model's predictions
predictions = np.array([1, 0, 1, 1, 0, 1])  # 1 = hire, 0 = don't hire

# Actual outcomes (if available)
actual = np.array([1, 0, 1, 0, 0, 1])

# Demographic information
demographics = pd.DataFrame({
    'Sex': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female'],
    'Race': ['White', 'Black', 'Asian', 'White', 'Black', 'Asian']
})

# Create analyzer
analyzer = BiasAnalyzer(sensitive_attrs=['Sex', 'Race'])

# Calculate metrics
results = analyzer.calculate_bias_metrics(
    y_true=actual,
    y_pred=predictions,
    sensitive_features=demographics
)

# Check results
print(f"Fairness Score: {results['fairness_score']}/100")
print(f"Sex Disparate Impact: {results['Sex']['disparate_impact']}")

# If disparate impact < 0.8, you have a problem!
if results['Sex']['disparate_impact'] < 0.8:
    print("⚠️ WARNING: Potential gender discrimination detected!")
"""