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
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from scipy.stats import ks_2samp
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score
import seaborn as sns
import matplotlib.pyplot as plt

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
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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
""")

model_id = st.sidebar.selectbox(
    "📊 Demo Model",
    ["german_credit_v1"],
    help="Pre-loaded demo model"
)

st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

data = DEMO_METRICS

# Top-level metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_preds = data.get("total_predictions", 0)
    st.metric(
        label="📊 Total Predictions",
        value=f"{total_preds:,}",
        help="Total number of predictions logged for this model"
    )

with col2:
    fairness_score = data.get("bias_analysis", {}).get("fairness_score", 0)
    st.metric(
        label="⚖️ Fairness Score",
        value=f"{fairness_score}/100",
        delta=f"{fairness_score - 70}" if fairness_score < 70 else None,
        delta_color="inverse" if fairness_score < 70 else "normal",
        help="Overall fairness score (0-100). Higher is better."
    )

with col3:
    drift_alerts = len([d for d in data.get("drift_analysis", []) if d.get('alert')])
    st.metric(
        label="🚨 Drift Alerts",
        value=drift_alerts,
        delta=f"+{drift_alerts}" if drift_alerts > 0 else "0",
        delta_color="inverse" if drift_alerts > 0 else "normal",
        help="Number of features showing significant drift"
    )

with col4:
    drift_data = data.get("drift_analysis", [])
    if drift_data:
        avg_drift = sum(d.get('score', 0) for d in drift_data) / len(drift_data)
        st.metric(
            label="📈 Avg Drift Score",
            value=f"{avg_drift:.3f}",
            help="Average drift score across all features"
        )
    else:
        st.metric(label="📈 Avg Drift Score", value="N/A")

# Fairness interpretation
if fairness_score >= 80:
    st.markdown('<div class="success-box">✅ <strong>Excellent Fairness</strong> - Model shows minimal bias</div>', unsafe_allow_html=True)
elif fairness_score >= 60:
    st.markdown('<div class="alert-box">⚠️ <strong>Good Fairness</strong> - Minor bias concerns, monitor closely</div>', unsafe_allow_html=True)
elif fairness_score >= 40:
    st.markdown('<div class="alert-box">⚠️ <strong>Moderate Bias</strong> - Investigation recommended</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="danger-box">❌ <strong>Significant Bias Detected</strong> - Immediate action required!</div>', unsafe_allow_html=True)

# ============================================================================
# DRIFT ANALYSIS
# ============================================================================

st.markdown("---")
st.markdown("## 📉 Data Drift Analysis")

drift_data = data.get("drift_analysis", [])

if drift_data:
    df_drift = pd.DataFrame(drift_data)
    
    col_table, col_chart = st.columns([1, 1])
    
    with col_table:
        st.subheader("Drift Details")
        
        def highlight_alerts(row):
            if row['alert']:
                return ['background-color: #ffcdd2'] * len(row)
            else:
                return [''] * len(row)
        
        st.dataframe(
            df_drift.style.apply(highlight_alerts, axis=1),
            use_container_width=True,
            height=300
        )
        
        st.caption("🔴 Red rows indicate drift alerts")
    
    with col_chart:
        st.subheader("Drift Score Visualization")
        
        fig_drift = px.bar(
            df_drift,
            x='feature',
            y='score',
            color='alert',
            title="Feature Drift Scores",
            color_discrete_map={True: '#dc3545', False: '#28a745'},
            labels={'score': 'Drift Score', 'feature': 'Feature'},
            hover_data=['type', 'metric', 'p_value']
        )
        
        fig_drift.update_layout(
            showlegend=True,
            legend_title_text='Alert Status',
            height=350
        )
        
        st.plotly_chart(fig_drift, use_container_width=True)
    
    with st.expander("📖 How to Interpret Drift Scores"):
        st.markdown("""
        **For Numerical Features (KS+PSI)**:
        - PSI < 0.1: ✅ No significant change
        - PSI 0.1-0.25: ⚠️ Minor drift (monitor)
        - PSI > 0.25: ❌ Major drift (action needed)
        
        **For Categorical Features (Chi-square)**:
        - p-value < 0.05: ❌ Significant drift detected
        - p-value >= 0.05: ✅ No significant drift
        
        **What to do if drift is detected**:
        1. Investigate the root cause (data collection changes, user behavior shifts)
        2. Consider retraining your model with recent data
        3. Monitor performance metrics closely
        """)
else:
    st.info("ℹ️ No drift analysis data available yet.")

# ============================================================================
# DRIFT SIMULATION (NEW!)
# ============================================================================

st.markdown("---")
st.markdown("## 🌊 Interactive Drift Simulation")
st.markdown("**What If Production Data Shifts?** See how distribution changes affect your model.")

drift_intensity = st.slider(
    "Simulate drift by shifting numerical features ± X%",
    min_value=0, max_value=100, value=20, step=10,
    help="Simulates concept drift by adding noise to numerical features"
)

if drift_intensity > 0:
    # Create drifted version of data
    df_drift = DEMO_DF.copy()
    numeric_cols = ['age', 'credit_amount', 'duration', 'installment_rate']
    
    for col in numeric_cols:
        shift = np.random.normal(0, drift_intensity/100, len(df_drift)) * DEMO_DF[col].std()
        df_drift[col] = DEMO_DF[col] + shift
    
    # Visualize drift
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Distribution")
        fig_orig = px.histogram(
            DEMO_DF, 
            x="credit_amount", 
            color="Risk",
            title="Credit Amount (Original Data)",
            nbins=30,
            color_discrete_map={'good': '#28a745', 'bad': '#dc3545'}
        )
        fig_orig.update_layout(height=350)
        st.plotly_chart(fig_orig, use_container_width=True)
    
    with col2:
        st.subheader(f"Drifted Distribution (+{drift_intensity}%)")
        fig_drift_sim = px.histogram(
            df_drift, 
            x="credit_amount", 
            color="Risk",
            title=f"Credit Amount (Drifted +{drift_intensity}%)",
            nbins=30,
            color_discrete_map={'good': '#28a745', 'bad': '#dc3545'}
        )
        fig_drift_sim.update_layout(height=350)
        st.plotly_chart(fig_drift_sim, use_container_width=True)
    
    # KS-test for drift detection
    ks_stat, p_value = ks_2samp(DEMO_DF["credit_amount"], df_drift["credit_amount"])
    
    if p_value < 0.05:
        st.error(f"🚨 **Drift Detected!** KS Test p-value: {p_value:.4f} (< 0.05) → Significant distribution shift detected")
    else:
        st.success(f"✅ **No Significant Drift** KS Test p-value: {p_value:.4f} (>= 0.05) → Distribution remains stable")
    
    st.info(f"📊 **KS Statistic**: {ks_stat:.4f} | **Interpretation**: Higher values indicate greater distribution differences")
else:
    st.info("👆 Move the slider above to simulate drift and see its impact on data distribution")

# ============================================================================
# BIAS ANALYSIS
# ============================================================================

st.markdown("---")
st.markdown("## ⚖️ Bias & Fairness Analysis")

bias_data = data.get("bias_analysis", {})

if bias_data and len(bias_data) > 1:
    sensitive_attrs = [k for k in bias_data.keys() if k != 'fairness_score']
    
    tabs = st.tabs([f"📊 {attr}" for attr in sensitive_attrs])
    
    for i, attr in enumerate(sensitive_attrs):
        with tabs[i]:
            metrics = bias_data[attr]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                di = metrics['disparate_impact']
                di_status = "✅" if di >= 0.8 else "❌"
                st.metric(
                    label=f"{di_status} Disparate Impact",
                    value=f"{di:.4f}",
                    delta="Pass" if di >= 0.8 else "Fail",
                    delta_color="normal" if di >= 0.8 else "inverse",
                    help="Ratio of selection rates. Should be >= 0.8 (Four-Fifths Rule)"
                )
            
            with col2:
                dpd = metrics['demographic_parity_difference']
                dpd_status = "✅" if abs(dpd) <= 0.1 else "❌"
                st.metric(
                    label=f"{dpd_status} Demographic Parity Diff",
                    value=f"{dpd:.4f}",
                    delta="Pass" if abs(dpd) <= 0.1 else "Fail",
                    delta_color="normal" if abs(dpd) <= 0.1 else "inverse",
                    help="Difference in selection rates. Should be close to 0"
                )
            
            with col3:
                eod = metrics.get('equalized_odds_difference')
                if eod is not None:
                    eod_status = "✅" if abs(eod) <= 0.1 else "❌"
                    st.metric(
                        label=f"{eod_status} Equalized Odds Diff",
                        value=f"{eod:.4f}",
                        delta="Pass" if abs(eod) <= 0.1 else "Fail",
                        delta_color="normal" if abs(eod) <= 0.1 else "inverse",
                        help="Difference in error rates. Should be close to 0"
                    )
                else:
                    st.metric(
                        label="Equalized Odds Diff",
                        value="N/A",
                        help="Requires ground truth labels"
                    )
            
            st.subheader(f"Selection Rates by {attr}")
            
            sel_rates = metrics['by_group']['selection_rate']
            df_sel = pd.DataFrame(list(sel_rates.items()), columns=['Group', 'Selection Rate'])
            
            fig_sel = px.bar(
                df_sel,
                x='Group',
                y='Selection Rate',
                title=f"Positive Prediction Rate by {attr}",
                color='Selection Rate',
                color_continuous_scale='RdYlGn',
                range_y=[0, 1]
            )
            
            if len(df_sel) > 0:
                max_rate = df_sel['Selection Rate'].max()
                threshold = max_rate * 0.8
                fig_sel.add_hline(
                    y=threshold,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="80% Threshold",
                    annotation_position="right"
                )
            
            fig_sel.update_layout(height=400)
            st.plotly_chart(fig_sel, use_container_width=True)
            
            if 'accuracy' in metrics['by_group']:
                st.subheader(f"Model Accuracy by {attr}")
                acc_data = metrics['by_group']['accuracy']
                df_acc = pd.DataFrame(list(acc_data.items()), columns=['Group', 'Accuracy'])
                
                fig_acc = px.bar(
                    df_acc,
                    x='Group',
                    y='Accuracy',
                    title=f"Prediction Accuracy by {attr}",
                    color='Accuracy',
                    color_continuous_scale='Blues',
                    range_y=[0, 1]
                )
                
                fig_acc.update_layout(height=350)
                st.plotly_chart(fig_acc, use_container_width=True)

# ============================================================================
# INTERSECTIONAL ANALYSIS (NEW!)
# ============================================================================

st.markdown("---")
st.markdown("## 🎯 Intersectional Bias Analysis")
st.markdown("**The Game-Changer**: Detects bias in subgroups that single-attribute analysis misses")

intersectional_score = INTERSECTIONAL_DATA['intersectional_fairness_score']

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Worst-Performing Groups")
    
    df_intersectional = pd.DataFrame(INTERSECTIONAL_DATA['worst_groups'])
    
    # Add status column
    def get_status(ratio):
        if ratio < 0.8:
            return "❌ FAIL"
        elif ratio < 0.9:
            return "⚠️ WARN"
        else:
            return "✅ PASS"
    
    df_intersectional['status'] = df_intersectional['disparity_ratio'].apply(get_status)
    df_intersectional['selection_rate_pct'] = df_intersectional['selection_rate'].apply(lambda x: f"{x:.1%}")
    
    st.dataframe(
        df_intersectional[['group', 'selection_rate_pct', 'count', 'disparity_ratio', 'status']],
        use_container_width=True,
        height=250
    )

with col2:
    st.metric(
        label="Intersectional Fairness Score",
        value=f"{intersectional_score}/100",
        delta="Critical" if intersectional_score < 50 else "Warning",
        delta_color="inverse",
        help="Score based on Four-Fifths Rule across all intersectional groups"
    )
    
    st.markdown("""
    **Key Finding:**
    
    Female employees aged 50+ have a **0.38 selection rate** compared to **0.79** for the best-performing group.
    
    **Disparity Ratio: 0.48** ❌
    
    This is an **EEOC red flag** that single-attribute analysis would miss!
    """)

# Visualization
fig_intersectional = px.bar(
    df_intersectional,
    x='group',
    y='selection_rate',
    color='disparity_ratio',
    title="Selection Rates by Intersectional Groups",
    color_continuous_scale='RdYlGn',
    labels={'selection_rate': 'Selection Rate', 'group': 'Intersectional Group'}
)

fig_intersectional.add_hline(
    y=0.8,
    line_dash="dash",
    line_color="red",
    annotation_text="Fairness Threshold",
    annotation_position="right"
)

st.plotly_chart(fig_intersectional, use_container_width=True)

# ============================================================================
# ROOT CAUSE ANALYSIS
# ============================================================================

st.markdown("---")
st.markdown("## 🔍 Root Cause Analysis")

report = data.get("root_cause_report")
if report:
    st.markdown(report)
else:
    st.info("ℹ️ No root cause report available.")

# ============================================================================
# MODEL PERFORMANCE & CONFUSION MATRIX (NEW!)
# ============================================================================

st.markdown("---")
st.markdown("## 📊 Model Performance Summary")
st.markdown("**Evaluate model accuracy and error patterns**")

# Calculate metrics from demo data
y_true = DEMO_DF['y_true'].values
y_pred = DEMO_DF['y_pred'].values

# Calculate performance metrics
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred, zero_division=0)
recall = recall_score(y_true, y_pred, zero_division=0)
f1 = f1_score(y_true, y_pred, zero_division=0)

# Display metrics in cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_color = "normal" if accuracy >= 0.7 else "inverse"
    st.metric(
        "Accuracy", 
        f"{accuracy:.1%}",
        delta=f"{(accuracy - 0.7):.1%}" if accuracy >= 0.7 else f"{(accuracy - 0.7):.1%}",
        delta_color=delta_color,
        help="Overall correctness of predictions"
    )

with col2:
    st.metric(
        "Precision", 
        f"{precision:.1%}",
        help="Of predicted positives, how many are actually positive?"
    )

with col3:
    st.metric(
        "Recall", 
        f"{recall:.1%}",
        help="Of actual positives, how many did we catch?"
    )

with col4:
    st.metric(
        "F1-Score", 
        f"{f1:.1%}",
        delta="Key Metric",
        help="Harmonic mean of precision and recall"
    )

# Confusion Matrix Visualization
st.subheader("Confusion Matrix")

col1, col2 = st.columns([2, 1])

with col1:
    # Calculate confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Create heatmap
    fig_cm, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm, 
        annot=True, 
        fmt='d', 
        cmap='Blues', 
        ax=ax,
        xticklabels=['Predicted Good (0)', 'Predicted Bad (1)'],
        yticklabels=['Actual Good (0)', 'Actual Bad (1)'],
        cbar_kws={'label': 'Count'}
    )
    ax.set_title("Confusion Matrix - Credit Risk Predictions", fontsize=14, fontweight='bold')
    ax.set_xlabel("Predicted Label", fontsize=12)
    ax.set_ylabel("True Label", fontsize=12)
    
    st.pyplot(fig_cm)
    plt.close()

with col2:
    st.markdown("### Interpretation")
    
    tn, fp, fn, tp = cm.ravel()
    
    st.markdown(f"""
    **Matrix Breakdown**:
    - ✅ **True Negatives**: {tn} (Correctly predicted good)
    - ❌ **False Positives**: {fp} (Predicted bad, actually good)
    - ❌ **False Negatives**: {fn} (Predicted good, actually bad)
    - ✅ **True Positives**: {tp} (Correctly predicted bad)
    
    **Key Insights**:
    - Total predictions: {len(y_true)}
    - Correct predictions: {tn + tp}
    - Errors: {fp + fn}
    """)
    
    if fp > fn:
        st.warning("⚠️ More **false positives** - Model is conservative (rejects good applicants)")
    elif fn > fp:
        st.warning("⚠️ More **false negatives** - Model is risky (approves bad applicants)")
    else:
        st.success("✅ Balanced error distribution")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    🛡️ Bias Drift Guardian | Built with Streamlit | Powered by Fairlearn & SHAP<br>
    <strong>This is a demo version</strong> - For production deployment, see the full stack version<br>
    📧 Contact: ImdataScientistSachin@gmail.com | 
    <a href='https://www.linkedin.com/in/sachin-paunikar-datascientists' target='_blank'>LinkedIn</a> |
    <a href='https://github.com/YOUR_USERNAME/bias-drift-detector' target='_blank'>GitHub</a>
</div>
""", unsafe_allow_html=True)
