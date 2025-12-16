"""
================================================================================
BIAS DRIFT GUARDIAN - STANDALONE DEMO
================================================================================

This is a self-contained demo version that works WITHOUT the API backend.
Perfect for Streamlit Community Cloud deployment and portfolio showcases.

Uses pre-loaded demo data from the German Credit dataset to demonstrate
all features: drift detection, fairness analysis, and intersectional bias.

🎯 DEPLOY THIS FILE to Streamlit Cloud for instant portfolio demo!
================================================================================
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from scipy.stats import ks_2samp
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score
import seaborn as sns
import matplotlib.pyplot as plt
import time
import uuid

# ============================================================================
# DEMO DATA (Pre-calculated from German Credit Dataset)
# ============================================================================

# This data simulates what the API would return
DEMO_METRICS = {
    "total_predictions": 150,
    "drift_analysis": [
        {
            "feature": "age",
            "type": "numerical",
            "metric": "KS+PSI",
            "score": 0.27,
            "p_value": 0.001,
            "psi": 0.28,
            "alert": True
        },
        {
            "feature": "credit_amount",
            "type": "numerical",
            "metric": "KS+PSI",
            "score": 0.12,
            "p_value": 0.234,
            "psi": 0.08,
            "alert": False
        },
        {
            "feature": "duration",
            "type": "numerical",
            "metric": "KS+PSI",
            "score": 0.15,
            "p_value": 0.089,
            "psi": 0.11,
            "alert": False
        },
        {
            "feature": "savings_status",
            "type": "categorical",
            "metric": "Chi-square",
            "score": 10.77,
            "p_value": 0.013,
            "psi": 0.0,
            "alert": True
        },
        {
            "feature": "job",
            "type": "categorical",
            "metric": "Chi-square",
            "score": 10.18,
            "p_value": 0.017,
            "psi": 0.0,
            "alert": True
        },
        {
            "feature": "own_telephone",
            "type": "categorical",
            "metric": "Chi-square",
            "score": 6.53,
            "p_value": 0.011,
            "psi": 0.0,
            "alert": True
        }
    ],
    "bias_analysis": {
        "Sex": {
            "by_group": {
                "selection_rate": {
                    "Male": 0.72,
                    "Female": 0.54
                },
                "accuracy": {
                    "Male": 0.68,
                    "Female": 0.71
                }
            },
            "demographic_parity_difference": 0.18,
            "equalized_odds_difference": 0.12,
            "disparate_impact": 0.75
        },
        "Age_Group": {
            "by_group": {
                "selection_rate": {
                    "20-30": 0.65,
                    "30-40": 0.71,
                    "40-50": 0.58,
                    "50+": 0.42
                }
            },
            "demographic_parity_difference": 0.29,
            "equalized_odds_difference": None,
            "disparate_impact": 0.59
        },
        "fairness_score": 60
    },
    "root_cause_report": """
Root Cause Analysis:

The model's reliance on features has shifted. The following features showed the most significant change:

- **age**: Importance increased by 0.0847 (Base: 0.1234 → Curr: 0.2081)
- **credit_amount**: Importance decreased by -0.0423 (Base: 0.1567 → Curr: 0.1144)
- **duration**: Importance increased by 0.0312 (Base: 0.0891 → Curr: 0.1203)

Recommendation: Investigate if the data distribution for these features has changed or if there is a new relationship in the data.
    """
}

# Intersectional analysis demo data
INTERSECTIONAL_DATA = {
    "worst_groups": [
        {
            "combination": "Sex_Age_Group",
            "group": "Female_50+",
            "selection_rate": 0.38,
            "count": 45,
            "disparity_ratio": 0.48
        },
        {
            "combination": "Sex_Age_Group",
            "group": "Female_40-50",
            "selection_rate": 0.52,
            "count": 67,
            "disparity_ratio": 0.65
        },
        {
            "combination": "Sex_Age_Group",
            "group": "Male_50+",
            "selection_rate": 0.58,
            "count": 82,
            "disparity_ratio": 0.73
        },
        {
            "combination": "Sex_Age_Group",
            "group": "Female_30-40",
            "selection_rate": 0.64,
            "count": 91,
            "disparity_ratio": 0.80
        },
        {
            "combination": "Sex_Age_Group",
            "group": "Male_40-50",
            "selection_rate": 0.69,
            "count": 103,
            "disparity_ratio": 0.86
        }
    ],
    "intersectional_fairness_score": 40
}

# Sample DataFrame for drift simulation and confusion matrix
# This simulates the German Credit dataset structure
np.random.seed(42)
n_samples = 150

DEMO_DF = pd.DataFrame({
    'age': np.random.randint(20, 70, n_samples),
    'credit_amount': np.random.randint(500, 15000, n_samples),
    'duration': np.random.randint(6, 48, n_samples),
    'installment_rate': np.random.randint(1, 5, n_samples),
    'Risk': np.random.choice(['good', 'bad'], n_samples, p=[0.7, 0.3])
})

# Simulated model predictions (for confusion matrix)
# In reality, these would come from your actual model
DEMO_DF['y_true'] = (DEMO_DF['Risk'] == 'bad').astype(int)
# Simple rule-based prediction for demo (replace with actual model)
DEMO_DF['y_pred'] = ((DEMO_DF['credit_amount'] > 7500) | (DEMO_DF['duration'] > 30)).astype(int)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Bias Drift Guardian - Demo",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    .demo-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    .alert-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .danger-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    #MainMenu {visibility: hidden;}
    
    /* Sticky Footer */
    .sticky-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: center;
        padding: 10px;
        font-size: 0.85rem;
        border-top: 1px solid #dee2e6;
        z-index: 999;
    }
    
    /* Sticky Top Button & Welcome container */
    .sticky-btn-container {
        position: fixed;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        width: 420px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# ONBOARDING FLOW (Day 1 Polish)
# ============================================================================
# Purpose: Reduce bounce rate by giving new users an immediate, high-value action.
# 1. Sticky Button: Ensures the "Try Demo" call-to-action is always visible.
# 2. Welcome Message: Contextualizes the demo for recruiters ("EEOC-style").
# Implementation: Checks st.session_state to only show on first load.
# ============================================================================

st.markdown('<div class="sticky-btn-container">', unsafe_allow_html=True)
if st.button("🚀 Try Demo – Bias Gap in 15s", type="primary", use_container_width=True):
    st.session_state.selected_dataset = "german_credit"
    st.rerun()

# Welcome Message (Only on first load / if no dataset selected)
if st.session_state.get('selected_dataset') is None:
    st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True) 
    st.success("👋 New here? Click above to see EEOC-style bias detection!")
    st.caption("💡 **Launch demo instantly — one click to value**. Loads real datasets with known fairness gaps — Designed for **EEOC‑style bias detection**.")
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown('<h1 class="main-title">🛡️ Bias Drift Guardian</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time AI Fairness & Data Drift Monitoring - Interactive Demo</p>', unsafe_allow_html=True)
st.markdown('<div class="demo-badge">📊 LIVE DEMO - German Credit Dataset</div>', unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.header("⚙️ Demo Configuration")
st.sidebar.success("✅ Demo Mode Active")
st.sidebar.info("""
**About This Demo:**

This is a standalone demo using pre-calculated metrics from the German Credit dataset.

**Features Demonstrated:**
- ✅ Drift Detection (PSI, KS, Chi-square)
- ✅ Fairness Analysis
- ✅ Intersectional Bias Detection
- ✅ Root Cause Analysis
- ✅ **What-If Analysis & Counterfactuals**
""")

model_id = st.sidebar.selectbox(
    "📊 Demo Model",
    ["german_credit_v1"],
    help="Pre-loaded demo model"
)

st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ============================================================================
# MAIN DASHBOARD TABS
# ============================================================================

data = DEMO_METRICS

# Create Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", 
    "⚖️ Fairness", 
    "🎯 Intersectional", 
    "🔮 What-If Analysis", 
    "📉 Drift", 
    "📊 Performance"
])

# ============================================================================
# TAB 1: OVERVIEW
# ============================================================================

with tab1:
    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_preds = data.get("total_predictions", 0)
        st.metric(
            label="Total Predictions",
            value=f"{total_preds:,}",
            help="Total number of predictions logged"
        )
    
    with col2:
        fairness_score = data.get("bias_analysis", {}).get("fairness_score", 0)
        st.metric(
            label="Fairness Score",
            value=f"{fairness_score}/100",
            delta=f"{fairness_score - 70}" if fairness_score < 70 else None,
            delta_color="inverse" if fairness_score < 70 else "normal",
            help="Overall fairness score (0-100)"
        )
    
    with col3:
        drift_alerts = len([d for d in data.get("drift_analysis", []) if d.get('alert')])
        st.metric(
            label="Drift Alerts",
            value=drift_alerts,
            delta=f"+{drift_alerts}" if drift_alerts > 0 else "0",
            delta_color="inverse" if drift_alerts > 0 else "normal"
        )
    
    with col4:
        drift_data = data.get("drift_analysis", [])
        if drift_data:
            avg_drift = sum(d.get('score', 0) for d in drift_data) / len(drift_data)
            st.metric(
                label="Avg Drift Score",
                value=f"{avg_drift:.3f}"
            )
        else:
            st.metric(label="Avg Drift Score", value="N/A")
    
    # Fairness interpretation
    if fairness_score >= 80:
        st.markdown('<div class="success-box">✅ <strong>Excellent Fairness</strong> - Model shows minimal bias</div>', unsafe_allow_html=True)
    elif fairness_score >= 60:
        st.markdown('<div class="alert-box">⚠️ <strong>Good Fairness</strong> - Minor bias concerns, monitor closely</div>', unsafe_allow_html=True)
    elif fairness_score >= 40:
        st.markdown('<div class="alert-box">⚠️ <strong>Moderate Bias</strong> - Investigation recommended</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="danger-box">❌ <strong>Significant Bias Detected</strong> - Immediate action required!</div>', unsafe_allow_html=True)

    # Root Cause (Summary)
    st.subheader("🔍 Key Insights")
    report = data.get("root_cause_report")
    if report:
        st.markdown(report)

# ============================================================================
# TAB 2: FAIRNESS ANALYSIS
# ============================================================================

with tab2:
    st.markdown("## ⚖️ Bias & Fairness Analysis")
    
    bias_data = data.get("bias_analysis", {})
    
    if bias_data and len(bias_data) > 1:
        sensitive_attrs = [k for k in bias_data.keys() if k != 'fairness_score']
        
        # Inner Tabs for Attributes
        sub_tabs = st.tabs([f"Attr: {attr}" for attr in sensitive_attrs])
        
        for i, attr in enumerate(sensitive_attrs):
            with sub_tabs[i]:
                metrics = bias_data[attr]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    di = metrics['disparate_impact']
                    st.metric(
                        label="Disparate Impact",
                        value=f"{di:.4f}",
                        delta="Pass" if di >= 0.8 else "Fail",
                        delta_color="normal" if di >= 0.8 else "inverse",
                        help="Should be >= 0.8"
                    )
                
                with col2:
                    dpd = metrics['demographic_parity_difference']
                    st.metric(
                        label="Demographic Parity Diff",
                        value=f"{dpd:.4f}",
                        delta="Pass" if abs(dpd) <= 0.1 else "Fail",
                        delta_color="normal" if abs(dpd) <= 0.1 else "inverse"
                    )
                
                with col3:
                    eod = metrics.get('equalized_odds_difference')
                    if eod is not None:
                        st.metric(
                            label="Equalized Odds Diff",
                            value=f"{eod:.4f}",
                            delta="Pass" if abs(eod) <= 0.1 else "Fail",
                            delta_color="normal" if abs(eod) <= 0.1 else "inverse"
                        )
                    else:
                        st.metric("Equalized Odds Diff", "N/A")
                
                st.subheader(f"Selection Rates by {attr}")
                sel_rates = metrics['by_group']['selection_rate']
                df_sel = pd.DataFrame(list(sel_rates.items()), columns=['Group', 'Selection Rate'])
                
                fig_sel = px.bar(
                    df_sel, x='Group', y='Selection Rate', color='Selection Rate',
                    color_continuous_scale='RdYlGn', range_y=[0, 1]
                )
                fig_sel.add_hline(y=0.8 * df_sel['Selection Rate'].max(), line_dash="dash", line_color="red")
                st.plotly_chart(fig_sel, use_container_width=True)

# ============================================================================
# TAB 3: INTERSECTIONAL
# ============================================================================

with tab3:
    st.markdown("## 🎯 Intersectional Bias Analysis")
    st.caption("Detecting bias in subgroups (e.g., Black Female over 50)")
    
    intersectional_score = INTERSECTIONAL_DATA['intersectional_fairness_score']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Worst-Performing Groups")
        df_intersectional = pd.DataFrame(INTERSECTIONAL_DATA['worst_groups'])
        
        def get_status(ratio):
            if ratio < 0.8: return "❌ FAIL"
            elif ratio < 0.9: return "⚠️ WARN"
            else: return "✅ PASS"
        
        df_intersectional['status'] = df_intersectional['disparity_ratio'].apply(get_status)
        df_intersectional['selection_rate_pct'] = df_intersectional['selection_rate'].apply(lambda x: f"{x:.1%}")
        
        st.dataframe(df_intersectional[['group', 'selection_rate_pct', 'count', 'disparity_ratio', 'status']], use_container_width=True)
    
    with col2:
        st.metric(
            label="Intersectional Score",
            value=f"{intersectional_score}/100",
            delta="Critical" if intersectional_score < 50 else "Warning",
            delta_color="inverse"
        )
        st.info("EEOC Compliance Alert: Groups with Disparity Ratio < 0.80 require justification.")

# ============================================================================
# TAB 4: WHAT-IF ANALYSIS (NEW!)
# ============================================================================

with tab4:
    st.markdown("## 🔮 What-If Analysis & Counterfactuals")
    st.markdown("""
    **Understanding Decisions:** Adjust feature values to see how the model's prediction changes.
    Generates minimal, realistic changes to flip a 'Reject' to 'Approve'.
    """)
    
    col_input, col_results = st.columns([1, 2])
    
    with col_input:
        st.subheader("📝 Applicant Profile")
        with st.form("what_if_form"):
            val_age = st.slider("Age", 18, 90, 35)
            val_credit = st.number_input("Credit Amount", 500, 20000, 5000)
            val_duration = st.slider("Duration (Months)", 6, 72, 24)
            val_job = st.selectbox("Job Skill Level", [0, 1, 2, 3], index=2)
            val_housing = st.selectbox("Housing", ["own", "rent", "free"], index=0)
            
            submitted = st.form_submit_button("Generate Counterfactuals")
            

    with col_results:
        st.subheader("📋 Results")
        
        if submitted:
            with st.spinner("Generating explanations..."):
                # Prepare Payload
                payload = {
                    "model_id": model_id,
                    "instances": [{
                        "age": val_age, 
                        "credit_amount": val_credit, 
                        "duration": val_duration, 
                        "job": val_job, 
                        "housing": val_housing,
                        # Add other defaults if needed by model schema
                        "savings_status": "unknown",
                        "own_telephone": "yes"
                    }],
                    "total_CFs": 3
                }
                
                api_success = False
                response_data = None
                
                # 1. Try Real API
                try:
                    # Assuming API is running locally on port 8000
                    api_url = "http://localhost:8000/api/v1/explain/counterfactual"
                    res = requests.post(api_url, json=payload, timeout=5)
                    
                    if res.status_code == 200:
                        data = res.json()
                        # specific parsing to match UI
                        # The API returns 'explanations': [{'counterfactuals': ...}]
                        if data.get('explanations'):
                            response_data = data['explanations'][0] # Take first (single instance)
                            # Remap API format to UI format if slightly different
                            # API returns 'changes' and 'counterfactual' (full dict)
                            # UI expects 'values' key for full dict
                            for cf in response_data['counterfactuals']:
                                cf['values'] = cf['counterfactual']
                                # Ensure scores are present (API provides minimal_change_score as score_l1 usually)
                                if 'score_l1' not in cf:
                                    cf['score_l1'] = cf.get('minimal_change_score', 0)
                                if 'score_l0' not in cf:
                                    cf['score_l0'] = len(cf['changes'])
                                
                            api_success = True
                            st.toast("✅ Connected to Live API Engine", icon="🔌")
                except Exception as e:
                    # API failed or not running
                    pass

                # 2. Fallback to Mock (if API failed)
                if not api_success:
                    time.sleep(1.0) # Simulate delay
                    st.toast("⚠️ API Unavailable - Using Simulation Mode", icon="🎮")
                    
                    # Mock Response (Same as before)
                    response_data = {
                        "original_prediction": "Reject (High Risk)",
                        "counterfactuals": [
                            {
                                "changes": {"credit_amount": 3500, "duration": 48},
                                "values": {"age": val_age, "credit_amount": 3500, "duration": 48, "job": val_job, "housing": val_housing},
                                "score_l1": 0.15,
                                "score_l0": 2,
                                "validity": "Valid"
                            },
                            {
                                "changes": {"credit_amount": 4000, "housing": "own"},
                                "values": {"age": val_age, "credit_amount": 4000, "duration": val_duration, "job": val_job, "housing": "own"},
                                "score_l1": 0.22,
                                "score_l0": 1,
                                "validity": "Valid"
                            }
                        ],
                        "validity_summary": "2 Valid, 1 Rejected by Constraints",
                        "constraints_report": {"age_below_min": 1} # Adjusted to match API
                    }

                # RENDER RESULTS (Common logic)
                # CURRENT PREDICTION
                pred = response_data.get('original_prediction', 'Unknown')
                # If API returned simple prediction in meta, use it. Otherwise mock.
                st.markdown(f"#### Current Prediction: 🔴 **{pred}**")
                
                # RANKING TABLE
                cfs = response_data.get('counterfactuals', [])
                if not cfs:
                    st.warning("No valid counterfactuals found.")
                else:
                    rows = []
                    for i, cf in enumerate(cfs):
                        # Format Changes
                        changes_txt = ", ".join([f"{k}: {v}" for k,v in cf['changes'].items()])
                        rows.append({
                            "Rank": i+1,
                            "Changes Needed": changes_txt,
                            "L0 (Count)": cf.get('score_l0', 'N/A'),
                            "L1 (Score)": round(cf.get('score_l1', 0), 4),
                            "Validity": "✅ Valid"
                        })
                    
                    df_results = pd.DataFrame(rows)
                    st.table(df_results)
                    
                    # TOOLTIPS & METRICS
                    st.info(f"ℹ️ **Minimal Change Score (L1)**: Lower is better. Represents the magnitude of change required.")
                    
                    # REJECTED TOGGLE
                    report = response_data.get('constraints_report', {})
                    if not report and 'rejected_cfs' in response_data:
                         # Handle mock format variance
                         report = {item['reason']: item['count'] for item in response_data['rejected_cfs']}

                    show_rejected = st.checkbox("Show Rejected Plans (Debug)")
                    if show_rejected:
                        if report:
                            st.warning("⚠️ **Rejected Suggestions** (Violated Constraints)")
                            st.json(report)
                        else:
                            st.info("No plans were rejected by constraints.")

                    # CSV EXPORT
                    csv = df_results.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Report (CSV)",
                        csv,
                        "counterfactual_report.csv",
                        "text/csv",
                        key='download-csv'
                    )

# ============================================================================
# TAB 5: DRIFT ANALYSIS
# ============================================================================

with tab5:
    st.markdown("## 📉 Data Drift Analysis")
    
    drift_data = data.get("drift_analysis", [])
    if drift_data:
        df_drift = pd.DataFrame(drift_data)
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(df_drift, use_container_width=True)
        with col2:
            fig_drift = px.bar(
                df_drift, x='feature', y='score', color='alert',
                color_discrete_map={True: '#dc3545', False: '#28a745'}
            )
            st.plotly_chart(fig_drift, use_container_width=True)
            
    # Interactive Drift Simulation
    st.markdown("### 🌊 Interactive Drift Simulation")
    drift_intensity = st.slider("Simulate Drift (%)", 0, 100, 20)
    
    if drift_intensity > 0:
        df_drifted = DEMO_DF.copy()
        df_drifted['credit_amount'] += np.random.normal(0, drift_intensity*10, len(df_drifted))
        
        ks_stat, p_val = ks_2samp(DEMO_DF['credit_amount'], df_drifted['credit_amount'])
        
        st.metric("KS P-Value", f"{p_val:.4f}", delta="Drift Detected" if p_val < 0.05 else "Stable", delta_color="inverse")

# ============================================================================
# TAB 6: PERFORMANCE
# ============================================================================

with tab6:
    st.markdown("## 📊 Model Performance")
    
    y_true = DEMO_DF['y_true']
    y_pred = DEMO_DF['y_pred']
    
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Accuracy", f"{acc:.2%}")
    c2.metric("Precision", f"{prec:.2%}")
    c3.metric("Recall", f"{rec:.2%}")
    
    st.subheader("Confusion Matrix")
    cm = confusion_matrix(y_true, y_pred)
    fig_cm = px.imshow(cm, text_auto=True, color_continuous_scale='Blues',
                       labels=dict(x="Predicted", y="Actual", color="Count"),
                       x=['Good', 'Bad'], y=['Good', 'Bad'])
    st.plotly_chart(fig_cm, use_container_width=True)

# ============================================================================
# STICKY FOOTER
# ============================================================================

st.markdown("""
<div class="sticky-footer">
    🛡️ <strong>Bias Drift Guardian</strong> | Designed to support EEOC‑style analysis and compliance workflows. | v1.0
</div>
""", unsafe_allow_html=True)
