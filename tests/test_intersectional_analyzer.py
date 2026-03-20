import pytest
import pandas as pd
import numpy as np
from core.intersectional_analyzer import IntersectionalAnalyzer

@pytest.fixture
def sample_demographics():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'Sex': np.random.choice(['Male', 'Female'], n),
        'Race': np.random.choice(['White', 'Black', 'Asian'], n),
        'Age_Group': np.random.choice(['18-30', '30-50', '50+'], n)
    })
    return df

@pytest.fixture
def analyzer():
    return IntersectionalAnalyzer(sensitive_attrs=['Sex', 'Race', 'Age_Group'])

def test_init(analyzer):
    assert analyzer.sensitive_attrs == ['Sex', 'Race', 'Age_Group']

def test_analyze_intersectional_bias_basic(analyzer, sample_demographics):
    y_pred = np.random.randint(0, 2, len(sample_demographics))
    results = analyzer.analyze_intersectional_bias(y_pred, sample_demographics, min_group_size=2)
    
    assert 'Sex_Race' in results
    assert 'Sex_Age_Group' in results
    assert 'Race_Age_Group' in results
    assert 'Sex_Race_Age_Group' in results
    assert 'worst_groups' in results
    assert 'intersectional_fairness_score' in results
    assert 'summary' in results

def test_analyze_intersectional_bias_with_true_labels(analyzer, sample_demographics):
    y_pred = np.random.randint(0, 2, len(sample_demographics))
    y_true = np.random.randint(0, 2, len(sample_demographics))
    results = analyzer.analyze_intersectional_bias(y_pred, sample_demographics, y_true=y_true, min_group_size=2)
    
    # Check if accuracy is present in one of the group results
    any_group = list(results['Sex_Race'].values())[0]
    assert 'accuracy' in any_group

def test_min_group_size_filtering(analyzer, sample_demographics):
    y_pred = np.random.randint(0, 2, len(sample_demographics))
    # Use a large min_group_size that should result in few or no groups
    results = analyzer.analyze_intersectional_bias(y_pred, sample_demographics, min_group_size=50)
    
    # Check if number of groups is small
    for combo in ['Sex_Race', 'Sex_Age_Group', 'Race_Age_Group']:
        if combo in results:
            assert len(results[combo]) <= 2

def test_disparity_ratio_calculation(analyzer):
    df = pd.DataFrame({
        'Sex': ['Male'] * 20 + ['Female'] * 20,
        'Race': ['White'] * 20 + ['Black'] * 20
    })
    # High selection rate for White Male, low for Black Female
    y_pred = np.array([1] * 18 + [0] * 2 + [0] * 15 + [1] * 5)
    
    results = analyzer.analyze_intersectional_bias(y_pred, df, min_group_size=5)
    
    # White_Male should have high selection rate (~0.9)
    # Black_Female should have low selection rate (~0.25)
    white_male = results['Sex_Race']['Male_White']
    black_female = results['Sex_Race']['Female_Black']
    
    assert white_male['selection_rate'] > black_female['selection_rate']
    assert black_female['disparity_ratio'] < 1.0
    assert white_male['disparity_ratio'] == 1.0

def test_generate_summary_no_bias(analyzer):
    results = {
        'worst_groups': [],
        'intersectional_fairness_score': 100
    }
    summary = analyzer._generate_summary(results)
    assert "No significant intersectional bias detected" in summary

def test_generate_summary_with_bias(analyzer):
    results = {
        'worst_groups': [
            {'group': 'Group A', 'selection_rate': 0.1, 'disparity_ratio': 0.2, 'count': 50}
        ],
        'intersectional_fairness_score': 30
    }
    summary = analyzer._generate_summary(results)
    assert "INTERSECTIONAL BIAS DETECTED" in summary
    assert "Group A" in summary
    assert "Immediate investigation required" in summary

def test_get_intersectional_leaderboard(analyzer, sample_demographics):
    y_pred = np.random.randint(0, 2, len(sample_demographics))
    leaderboard = analyzer.get_intersectional_leaderboard(y_pred, sample_demographics)
    
    assert isinstance(leaderboard, pd.DataFrame)
    if not leaderboard.empty:
        assert 'rank' in leaderboard.columns
        assert 'group' in leaderboard.columns
        assert 'status' in leaderboard.columns
