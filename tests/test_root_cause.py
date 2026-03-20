import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from core.root_cause import RootCauseAnalyzer

@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 200
    X = pd.DataFrame({
        'feature1': np.random.randn(n),
        'feature2': np.random.randn(n),
        'feature3': np.random.randn(n)
    })
    # Target depends strongly on feature1
    y = (X['feature1'] + 0.1 * np.random.randn(n) > 0).astype(int)
    return X, y

@pytest.fixture
def trained_model(sample_data):
    X, y = sample_data
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model

@pytest.fixture
def analyzer():
    return RootCauseAnalyzer()

def test_analyze_feature_importance_drift_no_drift(analyzer, trained_model, sample_data):
    X, _ = sample_data
    # Use the same data for baseline and current (should have near-zero drift)
    results = analyzer.analyze_feature_importance_drift(trained_model, X, X)
    
    assert 'feature_importance_drift' in results
    assert 'top_drifted_features' in results
    # Drift should be small
    for feature, data in results['feature_importance_drift'].items():
        assert abs(data['drift']) < 0.1

def test_analyze_feature_importance_drift_significant_drift(analyzer, trained_model, sample_data):
    X, _ = sample_data
    # Create current data where feature2 is very different
    current_X = X.copy()
    current_X['feature2'] = current_X['feature2'] * 10 + 5
    
    results = analyzer.analyze_feature_importance_drift(trained_model, X, current_X)
    
    assert 'feature_importance_drift' in results
    assert 'feature2' in results['feature_importance_drift']

def test_generate_report(analyzer):
    drift_analysis = {
        'feature_importance_drift': {
            'age': {'baseline_importance': 0.1, 'current_importance': 0.2, 'drift': 0.1},
            'income': {'baseline_importance': 0.3, 'current_importance': 0.1, 'drift': -0.2}
        },
        'top_drifted_features': ['income', 'age']
    }
    report = analyzer.generate_report(drift_analysis)
    assert "Root Cause Analysis" in report
    assert "income" in report
    assert "age" in report
    assert "decreased" in report
    assert "increased" in report

def test_error_handling_not_enough_data(analyzer, trained_model):
    X = pd.DataFrame({'a': [1, 2]})
    results = analyzer.analyze_feature_importance_drift(trained_model, X, X)
    assert 'error' in results
    assert "Not enough data" in results['error']

def test_generate_report_error(analyzer):
    drift_analysis = {'error': 'Something went wrong'}
    report = analyzer.generate_report(drift_analysis)
    assert "Root Cause Analysis Failed" in report
    assert "Something went wrong" in report

def test_generate_report_no_drift(analyzer):
    drift_analysis = {'top_drifted_features': []}
    report = analyzer.generate_report(drift_analysis)
    assert "No significant feature importance drift detected" in report
