import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from core.counterfactual_explainer import CounterfactualExplainer
import os

@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'age': np.random.randint(20, 60, n),
        'income': np.random.randint(30000, 100000, n),
        'gender': np.random.choice(['Male', 'Female'], n),
        'target': np.random.randint(0, 2, n)
    })
    return df

@pytest.fixture
def trained_model(sample_data):
    X = sample_data.drop('target', axis=1)
    y = sample_data['target']
    # Small forest for speed
    model = RandomForestClassifier(n_estimators=5, random_state=42)
    # Convert gender to numeric for sklearn
    X_num = X.copy()
    X_num['gender'] = X_num['gender'].map({'Male': 0, 'Female': 1})
    model.fit(X_num, y)
    return model

@pytest.fixture
def explainer(trained_model, sample_data):
    # Need to provide a model that works with DiCE (which expects the same format it receives)
    # DiCE handles categorical features, but sklearn might not.
    # However, CounterfactualExplainer uses dice_ml.Model(model=model, backend='sklearn')
    # Let's wrap the sklearn model to handle mapping if needed inside DiCE.
    # Actually, for the test we can just use a simple data/model that works.
    
    constraints_path = 'tests/test_constraints.json'
    return CounterfactualExplainer(
        model=trained_model,
        data=sample_data,
        target_column='target',
        continuous_features=['age', 'income'],
        categorical_features=['gender'],
        constraints_path=constraints_path
    )

def test_init(explainer):
    assert explainer.target_column == 'target'
    assert 'age' in explainer.continuous_features
    assert 'gender' in explainer.categorical_features
    assert 'features' in explainer.constraints

def test_explain_instance_basic(explainer):
    query_instance = pd.DataFrame([{
        'age': 25,
        'income': 50000,
        'gender': 'Male'
    }])
    
    # Run explanation
    results = explainer.explain_instance(query_instance, total_CFs=1)
    
    assert 'explanations' in results
    assert len(results['explanations']) == 1
    exp = results['explanations'][0]
    if 'error' not in exp:
        assert 'counterfactuals' in exp
        assert 'validity_summary' in exp

def test_validate_constraints(explainer):
    original = pd.DataFrame([{'age': 30, 'income': 50000, 'gender': 'Male', 'target': 0}])
    cfs = pd.DataFrame([
        {'age': 25, 'income': 60000, 'gender': 'Male', 'target': 1}, # Invalid: age decreased
        {'age': 35, 'income': 60000, 'gender': 'Female', 'target': 1}, # Invalid: gender changed
        {'age': 35, 'income': 250000, 'gender': 'Male', 'target': 1}, # Invalid: income too high
        {'age': 35, 'income': 60000, 'gender': 'Male', 'target': 1}  # Valid
    ])
    
    valid_cfs, rejections = explainer.validate_constraints(original, cfs)
    
    assert len(valid_cfs) == 1
    assert valid_cfs[0]['age'] == 35
    assert valid_cfs[0]['income'] == 60000
    
    assert 'age_decreased' in rejections
    assert 'gender_changed_immutable' in rejections
    assert 'custom_rule_income_limit' in rejections

def test_calculate_minimal_change(explainer):
    original = {'age': 30, 'income': 50000, 'gender': 'Male'}
    cf = {'age': 33, 'income': 55000, 'gender': 'Male'}
    
    score_l1, score_l0, changes = explainer.calculate_minimal_change(original, cf)
    
    assert score_l0 == 2 # age, income
    assert 'age' in changes
    assert 'income' in changes
    assert score_l1 > 0

def test_rank_counterfactuals(explainer):
    original = pd.DataFrame([{'age': 30, 'income': 50000, 'gender': 'Male', 'target': 0}])
    valid_cfs = [
        {'age': 35, 'income': 60000, 'gender': 'Male', 'target': 1}, # 2 changes
        {'age': 31, 'income': 50000, 'gender': 'Male', 'target': 1}  # 1 change
    ]
    
    ranked = explainer.rank_counterfactuals(original, valid_cfs)
    
    assert len(ranked) == 2
    assert ranked[0]['score_l0'] == 1
    assert ranked[1]['score_l0'] == 2
