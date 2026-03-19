
import sys
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import sys

# Add project root to path
sys.path.append(os.getcwd())

from core.counterfactual_explainer import CounterfactualExplainer

def verification_suite():
    print("Starting DiCE Implementation Verification...")
    
    # 1. Setup Dummy Data & Model
    print("\n[1/5] Setting up environment...")
    df = pd.DataFrame({
        'age': np.random.randint(18, 70, 100),
        'income': np.random.randint(20000, 150000, 100),
        'score': np.random.randint(300, 850, 100),
        'housing': np.random.choice(['own', 'rent'], 100),
        'target': np.random.choice([0, 1], 100) # 0=Reject, 1=Approve
    })
    
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Create Pipeline
    numerical_features = ['age', 'income', 'score']
    categorical_features = ['housing']
    
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(random_state=42))
    ])
    
    model.fit(X, y)
    print("Dummy Model Pipeline Trained.")

    # 2. Initialize Explainer
    print("\n[2/5] Initializing CounterfactualExplainer...")
    try:
        explainer = CounterfactualExplainer(
            model=model,
            data=df,
            target_column='target',
            continuous_features=['age', 'income', 'score'],
            categorical_features=['housing']
        )
        print("Explainer Initialized.")
    except Exception as e:
        print(f"Failed to initialize explainer: {e}")
        return

    # 3. Test Single Instance with Custom Rules (numexpr)
    print("\n[3/5] Testing Single Instance + Custom Rules...")
    # Add a custom rule on the fly for testing
    explainer.constraints['custom_rules'] = [
        {"name": "income_no_decrease", "expr": "cf_income >= original_income"}
    ]
    
    query = df.iloc[0:1].drop('target', axis=1)
    print(f"Query: {query.to_dict(orient='records')}")
    
    result = explainer.explain_instance(query, total_CFs=2)
    
    if result['explanations']:
        print("Explanation generated.")
        cfs = result['explanations'][0]['counterfactuals']
        print(f"   Generated {len(cfs)} valid CFs.")
        if cfs:
            print(f"   Top CF Score (L1): {cfs[0]['minimal_change_score']}")
            print(f"   Top CF L0: {cfs[0]['score_l0']}")
    else:
        print("No explanation generated.")

    # 4. Test Batch Processing & Global Reporting
    print("\n[4/5] Testing Batch Processing & Global Reporting...")
    query_batch = df.iloc[0:5].drop('target', axis=1)
    
    batch_result = explainer.explain_instance(query_batch, total_CFs=1)
    
    print(f"   Validity Summary: {batch_result['validity_summary']}")
    print(f"   Global Constraints Report: {batch_result['global_constraints_report']}")
    
    if 'global_constraints_report' in batch_result:
        print("Global Summary Verified.")
    else:
        print("Global Summary Missing.")

    # 5. Verify Polish Items (Toggle Logic / Metadata)
    print("\n[5/5] Verifying Polish Elements...")
    
    # Check if rejected reasons are captured (Toggle Logic)
    rejections_found = False
    for exp in batch_result['explanations']:
        if 'constraints_report' in exp and exp['constraints_report']:
            rejections_found = True
            print(f"   Found rejections for ID {exp['original_id']}: {exp['constraints_report']}")
            break
            
    if rejections_found:
        print("Rejected CFs are tracked (Toggle Logic Verified).")
    else:
        print("No rejections occurred in this batch (might be expected given data).")

    print("\nVerification Suite Complete!")

if __name__ == "__main__":
    verification_suite()
