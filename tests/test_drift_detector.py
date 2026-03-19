import pytest
import pandas as pd
import numpy as np
from core.drift_detector import DriftDetector

@pytest.fixture
def baseline_data():
    return pd.DataFrame({
        'age': np.random.normal(35, 5, 1000),
        'income': np.random.normal(50000, 10000, 1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000)
    })

@pytest.fixture
def drift_detector(baseline_data):
    return DriftDetector(
        baseline_data=baseline_data,
        numerical_features=['age', 'income'],
        categorical_features=['category']
    )

def test_initialization(drift_detector, baseline_data):
    """Test if DriftDetector initializes properly."""
    assert drift_detector.numerical_features == ['age', 'income']
    assert drift_detector.categorical_features == ['category']

def test_calculate_psi_no_drift(drift_detector):
    """Test PSI with identical distributions. Expect No Drift (PSI < 0.1)."""
    expected = np.random.normal(0, 1, 1000)
    actual = expected.copy()
    
    psi_value = drift_detector._calculate_psi(expected, actual, buckets=10)
    assert psi_value < 0.1, f"PSI should be close to 0, got {psi_value}"

def test_calculate_psi_significant_drift(drift_detector):
    """Test PSI with shifted distributions. Expect Major Drift (PSI > 0.25)."""
    expected = np.random.normal(0, 1, 1000)
    actual = np.random.normal(3, 1, 1000) # Drastically shifted mean
    
    psi_value = drift_detector._calculate_psi(expected, actual, buckets=10)
    assert psi_value > 0.25, f"PSI should be high due to drift, got {psi_value}"

def test_detect_feature_drift(drift_detector, baseline_data):
    """Test overall drift detection on current data."""
    # Create production data where 'age' drifts and 'income' is stable
    production_data = pd.DataFrame({
        'age': np.random.normal(60, 5, 1000), # Drifted feature
        'income': np.random.normal(50000, 10000, 1000), # Non-drifted
        'category': np.random.choice(['A', 'B', 'C'], 1000)
    })
    
    results = drift_detector.detect_feature_drift(production_data)
    
    assert isinstance(results, pd.DataFrame)
    assert 'feature' in results.columns
    assert 'alert' in results.columns
    
    # Assert age drifted
    age_alert = results.loc[results['feature'] == 'age', 'alert'].values[0]
    assert age_alert == True, "Age should trigger a drift alert."
    
    # Assert income did not drift
    income_alert = results.loc[results['feature'] == 'income', 'alert'].values[0]
    assert income_alert == False, "Income should not trigger an alert."

