"""
================================================================================
DRIFT DETECTOR MODULE
================================================================================

This module is your "early warning system" for data changes. It detects when
the data your model sees in production is different from the data it was
trained on.

🎯 WHY THIS MATTERS:
Imagine you trained a model on data from 2020, but now it's 2025 and people's
behaviors have changed. Your model's accuracy will drop! This detector catches
those changes BEFORE your model starts failing.

📊 WHAT IT DETECTS:
- Numerical Drift: Age distribution shifted from avg 35 to avg 45
- Categorical Drift: More people using mobile vs desktop than before

🔬 HOW IT WORKS:
Uses statistical tests to compare "baseline" (training) data vs "current"
(production) data.

================================================================================
"""

import pandas as pd
import numpy as np
from scipy.stats import ks_2samp, chisquare
from typing import List, Dict, Union, Optional


class DriftDetector:
    """
    🎯 PURPOSE:
    Monitors whether your production data is drifting away from training data.
    
    📊 WHAT IT DOES:
    - Compares current data distributions to baseline (training) data
    - Uses statistical tests (KS test, PSI, Chi-square) to detect changes
    - Flags features that have significantly drifted
    
    🔍 EXAMPLE USE CASE:
    You trained a loan approval model in 2020. In 2025, you notice accuracy
    dropping. This detector would show you that "income" distribution has
    shifted significantly (maybe due to inflation).
    
    ⚠️ IMPORTANT:
    Drift doesn't always mean bad! But it DOES mean you should investigate
    and possibly retrain your model.
    """
    
    def __init__(
        self, 
        baseline_data: Optional[pd.DataFrame] = None,
        numerical_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None
    ):
        """
        Initialize the drift detector with your training data.
        
        Args:
            baseline_data: The data your model was trained on (reference point)
                          This is what we'll compare production data against
            
            numerical_features: List of numeric column names to monitor
                              Examples: ['age', 'income', 'credit_score']
            
            categorical_features: List of categorical column names to monitor
                                 Examples: ['gender', 'country', 'product_type']
        
        Example:
            detector = DriftDetector(
                baseline_data=training_df,
                numerical_features=['age', 'income'],
                categorical_features=['gender', 'country']
            )
        """
        # Store the baseline data for comparison
        # In production, you might store summary statistics instead of raw data
        # to save memory
        self.baseline_data = baseline_data
        
        # Store which features to monitor
        self.numerical_features = numerical_features if numerical_features else []
        self.categorical_features = categorical_features if categorical_features else []
    
    
    def detect_feature_drift(self, current_data: pd.DataFrame) -> pd.DataFrame:
        """
        🎯 MAIN FUNCTION: Detects drift in all configured features
        
        This is like running a "health check" on your data. It compares each
        feature in your current production data against the baseline and flags
        any significant changes.
        
        Args:
            current_data: Recent production data to check for drift
                         Should have same columns as baseline_data
        
        Returns:
            DataFrame with drift analysis results:
            | feature | type        | metric      | score | p_value | psi   | alert |
            |---------|-------------|-------------|-------|---------|-------|-------|
            | age     | numerical   | KS+PSI      | 0.15  | 0.001   | 0.28  | True  |
            | gender  | categorical | Chi-square  | 12.5  | 0.002   | 0.0   | True  |
        
        Interpretation:
            - alert=True: Significant drift detected! ⚠️
            - alert=False: No significant drift ✅
        """
        results = []
        
        # ========================================================================
        # VALIDATION: Check if we have baseline data
        # ========================================================================
        if self.baseline_data is None or self.baseline_data.empty:
            # Can't detect drift without a reference point!
            return pd.DataFrame()
        
        # ========================================================================
        # PART 1: NUMERICAL DRIFT DETECTION
        # ========================================================================
        # For numerical features (age, income, etc.), we use two tests:
        # 1. KS Test: Detects changes in distribution shape
        # 2. PSI: Quantifies magnitude of drift
        
        for feature in self.numerical_features:
            # Skip if feature not in both datasets
            if feature not in current_data.columns or feature not in self.baseline_data.columns:
                continue
            
            # ================================================================
            # TEST 1: Kolmogorov-Smirnov (KS) Test
            # ================================================================
            # 📊 WHAT IT DOES:
            # Compares two distributions to see if they're significantly different
            #
            # 🎯 HOW TO INTERPRET:
            # - p_value < 0.05: Distributions are different (drift detected!)
            # - p_value >= 0.05: Distributions are similar (no drift)
            #
            # EXAMPLE:
            # Baseline age: mostly 30-40 year olds
            # Current age: mostly 50-60 year olds
            # → KS test will flag this as drift
            
            try:
                # Remove missing values before testing
                baseline_values = self.baseline_data[feature].dropna()
                current_values = current_data[feature].dropna()
                
                # Run the 2-sample KS test
                stat, p_value = ks_2samp(baseline_values, current_values)
                
            except Exception as e:
                # If test fails (e.g., all values are NaN), use safe defaults
                stat, p_value = 0.0, 1.0
            
            # ================================================================
            # TEST 2: Population Stability Index (PSI)
            # ================================================================
            # 📊 WHAT IT DOES:
            # Industry-standard metric for quantifying drift magnitude
            #
            # 🎯 HOW TO INTERPRET:
            # PSI < 0.1:    No significant change ✅
            # PSI 0.1-0.25: Minor drift (monitor) ⚠️
            # PSI > 0.25:   Major drift (action needed!) ❌
            #
            # EXAMPLE:
            # If income distribution shifts from $50k avg to $60k avg,
            # PSI might be 0.15 (minor drift)
            
            psi = self._calculate_psi(baseline_values, current_values)
            
            # ================================================================
            # Store Results
            # ================================================================
            results.append({
                'feature': feature,
                'type': 'numerical',
                'metric': 'KS+PSI',
                'score': float(stat),  # KS statistic
                'p_value': float(p_value),
                'psi': float(psi),
                # Alert if EITHER test indicates drift
                'alert': p_value < 0.05 or psi > 0.25
            })
        
        # ========================================================================
        # PART 2: CATEGORICAL DRIFT DETECTION
        # ========================================================================
        # For categorical features (gender, country, etc.), we use Chi-square test
        # to detect changes in category frequencies
        
        for feature in self.categorical_features:
            # Skip if feature not in both datasets
            if feature not in current_data.columns or feature not in self.baseline_data.columns:
                continue
            
            # ================================================================
            # Chi-Square Test for Categorical Data
            # ================================================================
            # 📊 WHAT IT DOES:
            # Compares category frequencies between baseline and current data
            #
            # 🎯 HOW TO INTERPRET:
            # - p_value < 0.05: Category distribution has changed (drift!)
            # - p_value >= 0.05: Category distribution is similar (no drift)
            #
            # EXAMPLE:
            # Baseline: 60% Male, 40% Female
            # Current:  40% Male, 60% Female
            # → Chi-square test will flag this as drift
            
            try:
                # Get frequency distributions (as proportions)
                # Example: {'Male': 0.6, 'Female': 0.4}
                base_counts = self.baseline_data[feature].value_counts(normalize=True)
                curr_counts = current_data[feature].value_counts(normalize=True)
                
                # ============================================================
                # ALIGNMENT: Handle categories that appear in one dataset but not the other
                # ============================================================
                # Example: Baseline has ['USA', 'UK'], Current has ['USA', 'UK', 'Canada']
                # We need to align them so we're comparing apples to apples
                
                all_cats = set(base_counts.index) | set(curr_counts.index)
                base_aligned = base_counts.reindex(all_cats, fill_value=0)
                curr_aligned = curr_counts.reindex(all_cats, fill_value=0)
                
                # ============================================================
                # CONVERT: Proportions → Counts
                # ============================================================
                # Chi-square test expects counts, not proportions
                # We scale by current sample size
                
                current_size = len(current_data)
                expected = base_aligned * current_size  # What we'd expect based on baseline
                observed = curr_aligned * current_size  # What we actually see
                
                # ============================================================
                # FILTERING: Remove categories with very low counts
                # ============================================================
                # Chi-square test is unreliable when expected counts are < 5
                # This is a standard statistical practice
                
                valid_mask = expected > 5
                
                if valid_mask.sum() > 1:  # Need at least 2 categories for test
                    obs_valid = observed[valid_mask]
                    exp_valid = expected[valid_mask]
                    
                    # CRITICAL FIX: Normalize expected to match observed sum
                    # This prevents scipy errors due to rounding/filtering
                    if exp_valid.sum() > 0:
                        exp_valid = exp_valid * (obs_valid.sum() / exp_valid.sum())
                    
                    # Run the Chi-square test
                    stat, p_value = chisquare(obs_valid, exp_valid)
                else:
                    # Not enough valid categories for a meaningful test
                    stat, p_value = 0.0, 1.0
                
                # ============================================================
                # Store Results
                # ============================================================
                results.append({
                    'feature': feature,
                    'type': 'categorical',
                    'metric': 'Chi-square',
                    'score': float(stat),
                    'p_value': float(p_value),
                    'psi': 0.0,  # PSI not calculated for categorical
                    'alert': p_value < 0.05
                })
                
            except Exception as e:
                # If anything goes wrong, log it but don't crash
                print(f"⚠️ Error in categorical drift for {feature}: {e}")
        
        # Return results as a DataFrame for easy viewing
        return pd.DataFrame(results)
    
    
    def _calculate_psi(self, expected, actual, buckets=10):
        """
        🎯 PURPOSE:
        Calculates Population Stability Index (PSI) for numerical features.
        
        📊 HOW IT WORKS:
        1. Divide baseline data into buckets (like a histogram)
        2. See how current data falls into those same buckets
        3. Calculate how much the distribution has shifted
        
        🔍 ANALOGY:
        Imagine you have 10 bins for age ranges (0-10, 10-20, etc.).
        In baseline, 20% of people were in the 30-40 bin.
        In current data, only 10% are in that bin.
        PSI quantifies this shift across all bins.
        
        Args:
            expected: Baseline data values (what we expect to see)
            actual: Current data values (what we actually see)
            buckets: Number of bins to divide the data into (default: 10)
        
        Returns:
            PSI value (float):
            - < 0.1: No significant change
            - 0.1-0.25: Minor drift
            - > 0.25: Major drift
        """
        try:
            # ================================================================
            # VALIDATION: Check if we have enough data
            # ================================================================
            if len(expected) == 0 or len(actual) == 0:
                return 0.0
            
            # ================================================================
            # TYPE CHECK: Ensure data is numeric
            # ================================================================
            # PSI only makes sense for numbers, not strings!
            # This prevents errors like "unsupported operand type(s) for -: 'str' and 'str'"
            
            if not np.issubdtype(expected.dtype, np.number) or not np.issubdtype(actual.dtype, np.number):
                return 0.0
            
            # ================================================================
            # STEP 1: Define Buckets Using Baseline Data
            # ================================================================
            # We use percentiles to create equal-sized buckets in the baseline
            # Example: For 10 buckets, we use 0th, 10th, 20th, ..., 100th percentiles
            
            breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
            
            # ================================================================
            # EDGE CASE: Handle Duplicate Breakpoints
            # ================================================================
            # If data has few unique values, percentiles might be identical
            # Example: Data is all [1, 1, 1, 2, 2] → many percentiles will be 1
            
            breakpoints = np.unique(breakpoints)
            if len(breakpoints) < 2:
                # Can't create bins with only 1 unique value
                return 0.0
            
            # ================================================================
            # STEP 2: Calculate Frequencies in Each Bucket
            # ================================================================
            # Count what % of data falls in each bin
            
            expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
            actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)
            
            # ================================================================
            # STEP 3: Smoothing to Avoid Math Errors
            # ================================================================
            # If a bucket has 0% in either dataset, we'd get log(0) = infinity!
            # We add a tiny value (epsilon) to prevent this
            
            epsilon = 1e-4
            expected_percents = np.where(expected_percents == 0, epsilon, expected_percents)
            actual_percents = np.where(actual_percents == 0, epsilon, actual_percents)
            
            # ================================================================
            # STEP 4: Calculate PSI
            # ================================================================
            # PSI Formula: Σ (Actual% - Expected%) × ln(Actual% / Expected%)
            #
            # INTUITION:
            # - If distributions are identical, PSI = 0
            # - Larger differences → larger PSI
            
            psi_value = np.sum(
                (expected_percents - actual_percents) * 
                np.log(expected_percents / actual_percents)
            )
            
            return psi_value
            
        except Exception as e:
            # If anything goes wrong, return 0 (no drift detected)
            # In production, you'd want to log this error
            return 0.0


# ================================================================================
# USAGE EXAMPLE
# ================================================================================
"""
# Example: Monitoring a credit scoring model

import pandas as pd

# Training data (baseline)
baseline = pd.DataFrame({
    'age': [25, 30, 35, 40, 45, 50],
    'income': [30000, 40000, 50000, 60000, 70000, 80000],
    'country': ['USA', 'USA', 'UK', 'UK', 'Canada', 'Canada']
})

# Production data (current)
current = pd.DataFrame({
    'age': [45, 50, 55, 60, 65, 70],  # Ages have shifted up!
    'income': [35000, 45000, 55000, 65000, 75000, 85000],
    'country': ['USA', 'UK', 'UK', 'Canada', 'Canada', 'Mexico']  # New country!
})

# Create detector
detector = DriftDetector(
    baseline_data=baseline,
    numerical_features=['age', 'income'],
    categorical_features=['country']
)

# Detect drift
results = detector.detect_feature_drift(current)

# Check results
print(results)

# Example output:
#   feature  type        metric      score  p_value    psi  alert
#   age      numerical   KS+PSI      0.83   0.001     0.35  True   ← DRIFT!
#   income   numerical   KS+PSI      0.17   0.450     0.08  False  ← OK
#   country  categorical Chi-square  8.50   0.014     0.00  True   ← DRIFT!

# Interpretation:
# - Age has drifted significantly (PSI=0.35 > 0.25)
# - Income is stable (PSI=0.08 < 0.1)
# - Country distribution has changed (new category 'Mexico')
# → You should retrain your model!
"""