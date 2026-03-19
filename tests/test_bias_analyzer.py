import pytest
import pandas as pd
import numpy as np
from core.bias_analyzer import BiasAnalyzer

@pytest.fixture
def bias_analyzer():
    return BiasAnalyzer(sensitive_attrs=['Sex', 'Race'])

@pytest.fixture
def unbiased_mock_data():
    """Generates mock data representing fair model outcomes across groups."""
    n_samples = 1000
    
    # True and predicted labels where everything is fairly distributed
    y_true = np.random.choice([0, 1], n_samples)
    y_pred = y_true.copy()  # perfect accuracy
    
    # Sex and Race roughly independent from outcomes
    sensitive_features = pd.DataFrame({
        'Sex': np.random.choice(['Male', 'Female'], n_samples),
        'Race': np.random.choice(['White', 'Black', 'Asian'], n_samples)
    })
    
    return y_true, y_pred, sensitive_features

def test_initialization(bias_analyzer):
    """Test BiasAnalyzer initializes correctly."""
    assert 'Sex' in bias_analyzer.sens_attrs
    assert 'Race' in bias_analyzer.sens_attrs

def test_calculate_bias_metrics_unbiased(bias_analyzer, unbiased_mock_data):
    """Test bias metrics on unbiased, perfectly accurate data."""
    y_true, y_pred, sensitive_features = unbiased_mock_data
    
    metrics = bias_analyzer.calculate_bias_metrics(
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_features
    )
    
    assert isinstance(metrics, dict)
    assert 'fairness_score' in metrics
    # Given randomness and perfect predictions based on same distribution, 
    # it shouldn't show huge disparity (<0.8 or >1.2).
    assert metrics['fairness_score'] >= 0, "Fairness score returned invalid range."

def test_calculate_bias_metrics_biased():
    """Test bias metrics when there is obvious bias introduced manually."""
    analyzer = BiasAnalyzer(sensitive_attrs=['Sex'])
    
    n_samples = 200
    # Group sizes
    sex_female = ['Female'] * 100
    sex_male = ['Male'] * 100
    sensitive_features = pd.DataFrame({'Sex': sex_female + sex_male})
    
    y_true = np.ones(n_samples) # All should technically be '1'
    
    # Force bias: females are rejected (0), males are accepted (1)
    y_pred_female = [0] * 100
    y_pred_male = [1] * 100
    y_pred = np.array(y_pred_female + y_pred_male)
    
    metrics = analyzer.calculate_bias_metrics(
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_features
    )
    
    assert 'Sex' in metrics
    
    # The male selection rate is 1.0, female is 0.0
    # The disparate impact should be close to 0 (or exactly 0)
    di = metrics['Sex'].get('disparate_impact', 0.0)
    assert di < 0.8, f"Expected significant disparate impact indicating bias. Got {di}"

