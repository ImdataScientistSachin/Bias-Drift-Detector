from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np

# Load & Prep (from our plan)
data = fetch_openml('adult', version=2, as_frame=True, parser='auto')['frame']
X = data.select_dtypes(include=['number']).drop('fnlwgt', axis=1)  # Clean
y = (data['income'] == '>50K').astype(int)
sensitive = pd.get_dummies(data['sex'])['Male'].astype(int)  # Gender proxy

X_base, X_curr, y_base, y_curr, sens_base, sens_curr = train_test_split(X, y, sensitive, test_size=0.5)

model = RandomForestClassifier().fit(X_base, y_base)
preds_curr = model.predict(X_curr)

# Init & Run
from core.drift_detector import DriftDetector
from core.bias_analyzer import BiasAnalyzer
from core.root_cause import RootCauseAnalyzer

dd = DriftDetector(X_base)
ba = BiasAnalyzer(['sex'])
rca = RootCauseAnalyzer(model, X_base)

# Simulate drift
X_curr_dr = X_curr.copy()
X_curr_dr['age'] += np.random.normal(0, 5, len(X_curr))

drift_res = dd.detect_feature_drift(X_curr_dr)
group_bd, bias_met = ba.calculate_bias_metrics(y_curr, preds_curr, sens_curr)
rc_res = rca.analyze_feature_importance_drift(X_curr_dr, ['sex'])  # Stub call

report = rca.generate_natural_language_report({'drift_ranking': [{'feature': 'age', 'drift_pct': 15}], 'proxy_discrimination_risks': [{'feature': 'occupation', 'sensitive_attr': 'sex', 'correlation': 0.45}]}, use_llm=True)

print("=== ALERTS ===")
print(drift_res[drift_res['alert'] == True])
print(f"Disparate Impact: {bias_met['disparate_impact']:.3f}")
print("\n=== ROOT CAUSE REPORT ===")
print(report)