"""
================================================================================
BIAS DRIFT GUARDIAN - STREAMLIT DASHBOARD
================================================================================

This is the visual interface for monitoring AI model fairness and data drift.
Think of it as your "mission control" for responsible AI.

🎯 PURPOSE:
Provide an intuitive, beautiful dashboard where anyone (even non-technical
stakeholders) can quickly understand if their AI models are:
1. Treating people fairly
2. Working with data similar to what they were trained on

📊 FEATURES:
- Real-time metrics display
- Interactive charts and visualizations
- Model comparison
- Drill-down analysis
- Alert highlighting

================================================================================
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Try to get API URL from environment variable (for deployment)
# Falls back to localhost for local development
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# ============================================================================
# DEMO DATA FALLBACK (Used when API is unavailable)
# ============================================================================

DEMO_METRICS = {
    "total_predictions": 150,
    "drift_analysis": [
        {"feature": "age", "type": "numerical", "metric": "KS+PSI", "score": 0.27, "p_value": 0.001, "psi": 0.28, "alert": True},
        {"feature": "credit_amount", "type": "numerical", "metric": "KS+PSI", "score": 0.12, "p_value": 0.234, "psi": 0.08, "alert": False},
        {"feature": "duration", "type": "numerical", "metric": "KS+PSI", "score": 0.15, "p_value": 0.089, "psi": 0.11, "alert": False},
        {"feature": "savings_status", "type": "categorical", "metric": "Chi-square", "score": 10.77, "p_value": 0.013, "psi": 0.0, "alert": True},
        {"feature": "job", "type": "categorical", "metric": "Chi-square", "score": 10.18, "p_value": 0.017, "psi": 0.0, "alert": True},
        {"feature": "own_telephone", "type": "categorical", "metric": "Chi-square", "score": 6.53, "p_value": 0.011, "psi": 0.0, "alert": True}
    ],
    "bias_analysis": {
        "Sex": {
            "by_group": {"selection_rate": {"Male": 0.72, "Female": 0.54}, "accuracy": {"Male": 0.68, "Female": 0.71}},
            "demographic_parity_difference": 0.18,
            "equalized_odds_difference": 0.12,
            "disparate_impact": 0.75
        },
        "Age_Group": {
            "by_group": {"selection_rate": {"20-30": 0.65, "30-40": 0.71, "40-50": 0.58, "50+": 0.42}},
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

# ============================================================================
# API CONNECTION HELPER
# ============================================================================

def check_api_connection():
    """Check if API is available."""
    try:
        response = requests.get(f"{API_URL.replace('/api/v1', '')}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_data_with_fallback(endpoint, demo_data):
    """Try to fetch from API, fall back to demo data if unavailable."""
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json(), True  # Return data and API status
        else:
            return demo_data, False
    except:
        return demo_data, False

# Set page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Bias Drift Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS FOR PROFESSIONAL STYLING
# ============================================================================

st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* Subtitle styling */
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Alert box styling */
    .alert-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Success box styling */
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Danger box styling */
    .danger-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Section header */
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #333;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER SECTION
# ============================================================================

# Main title with gradient effect
st.markdown('<h1 class="main-title">🛡️ Bias Drift Guardian</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time AI Fairness & Data Drift Monitoring</p>', unsafe_allow_html=True)

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

st.sidebar.header("⚙️ Configuration")

# Add API status indicator
try:
    health_resp = requests.get(f"{API_URL}/health", timeout=2)
    if health_resp.status_code == 200:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Error")
except:
    st.sidebar.error("❌ API Offline")
    st.error("⚠️ Cannot connect to API. Please ensure the API server is running:\n```bash\npython -m api.main\n```")
    st.stop()

# Fetch available models
try:
    resp = requests.get(f"{API_URL}/models", timeout=2)
    if resp.status_code == 200:
        models = resp.json().get("models", [])
    else:
        models = []
except:
    models = []

# Model selection
if models:
    model_id = st.sidebar.selectbox(
        "📊 Select Model",
        models,
        index=0,
        help="Choose which model to monitor"
    )
    st.sidebar.info(f"Monitoring: **{model_id}**")
else:
    st.sidebar.warning("⚠️ No models registered")
    st.warning("No models found. Please run a demo script to register a model:\n```bash\npython examples/german_credit_demo.py\n```")
    st.stop()

# Refresh button with custom styling
refresh_btn = st.sidebar.button("🔄 Refresh Metrics", use_container_width=True)

# Add last updated timestamp
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = datetime.now()

if refresh_btn:
    st.session_state.last_updated = datetime.now()

st.sidebar.caption(f"Last updated: {st.session_state.last_updated.strftime('%H:%M:%S')}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def fetch_metrics(model_id):
    """
    Fetches metrics from the API for a given model.
    
    Returns:
        dict: Metrics data or None if error
    """
    try:
        response = requests.get(f"{API_URL}/metrics/{model_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Error fetching metrics: {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ Connection error: {e}")
        return None


def get_fairness_color(score):
    """
    Returns color based on fairness score.
    
    Args:
        score: Fairness score (0-100)
    
    Returns:
        str: Color code
    """
    if score >= 80:
        return "#28a745"  # Green
    elif score >= 60:
        return "#ffc107"  # Yellow
    elif score >= 40:
        return "#fd7e14"  # Orange
    else:
        return "#dc3545"  # Red


def get_fairness_message(score):
    """
    Returns interpretation message for fairness score.
    
    Args:
        score: Fairness score (0-100)
    
    Returns:
        str: HTML formatted message
    """
    if score >= 80:
        return '<div class="success-box">✅ <strong>Excellent Fairness</strong> - Model shows minimal bias</div>'
    elif score >= 60:
        return '<div class="alert-box">⚠️ <strong>Good Fairness</strong> - Minor bias concerns, monitor closely</div>'
    elif score >= 40:
        return '<div class="alert-box">⚠️ <strong>Moderate Bias</strong> - Investigation recommended</div>'
    else:
        return '<div class="danger-box">❌ <strong>Significant Bias Detected</strong> - Immediate action required!</div>'

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Fetch data
data = fetch_metrics(model_id)

if data:
    # ========================================================================
    # TOP-LEVEL METRICS (KPI Cards)
    # ========================================================================
    
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
        # Calculate average drift score
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
    
    # ========================================================================
    # FAIRNESS INTERPRETATION
    # ========================================================================
    
    st.markdown(get_fairness_message(fairness_score), unsafe_allow_html=True)
    
    # ========================================================================
    # DRIFT ANALYSIS SECTION
    # ========================================================================
    
    st.markdown("---")
    st.markdown('<h2 class="section-header">📉 Data Drift Analysis</h2>', unsafe_allow_html=True)
    
    drift_data = data.get("drift_analysis", [])
    
    if drift_data:
        df_drift = pd.DataFrame(drift_data)
        
        # Create two columns for table and chart
        col_table, col_chart = st.columns([1, 1])
        
        with col_table:
            st.subheader("Drift Details")
            
            # Style the dataframe
            def highlight_alerts(row):
                if row['alert']:
                    return ['background-color: #ffcdd2'] * len(row)
                else:
                    return [''] * len(row)
            
            # Display styled table
            st.dataframe(
                df_drift.style.apply(highlight_alerts, axis=1),
                use_container_width=True,
                height=300
            )
            
            # Add legend
            st.caption("🔴 Red rows indicate drift alerts")
        
        with col_chart:
            st.subheader("Drift Score Visualization")
            
            # Create interactive bar chart
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
        
        # Add interpretation guide
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
        st.info("ℹ️ No drift analysis data available yet. Log more predictions to enable drift detection.")
    
    # ========================================================================
    # BIAS & FAIRNESS ANALYSIS SECTION
    # ========================================================================
    
    st.markdown("---")
    st.markdown('<h2 class="section-header">⚖️ Bias & Fairness Analysis</h2>', unsafe_allow_html=True)
    
    bias_data = data.get("bias_analysis", {})
    
    if bias_data and len(bias_data) > 1:  # More than just fairness_score
        # Extract sensitive attributes
        sensitive_attrs = [k for k in bias_data.keys() if k != 'fairness_score']
        
        # Create tabs for each sensitive attribute
        tabs = st.tabs([f"📊 {attr}" for attr in sensitive_attrs])
        
        for i, attr in enumerate(sensitive_attrs):
            with tabs[i]:
                metrics = bias_data[attr]
                
                # Display key metrics
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
                
                # Selection Rate Visualization
                st.subheader(f"Selection Rates by {attr}")
                
                sel_rates = metrics['by_group']['selection_rate']
                df_sel = pd.DataFrame(list(sel_rates.items()), columns=['Group', 'Selection Rate'])
                
                # Create enhanced bar chart
                fig_sel = px.bar(
                    df_sel,
                    x='Group',
                    y='Selection Rate',
                    title=f"Positive Prediction Rate by {attr}",
                    color='Selection Rate',
                    color_continuous_scale='RdYlGn',
                    range_y=[0, 1]
                )
                
                # Add reference line at 0.8 ratio
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
                
                # Accuracy by group (if available)
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
    else:
        st.info("ℹ️ No bias analysis data available yet.")
    
    # ========================================================================
    # ROOT CAUSE ANALYSIS SECTION
    # ========================================================================
    
    st.markdown("---")
    st.markdown('<h2 class="section-header">🔍 Root Cause Analysis</h2>', unsafe_allow_html=True)
    
    report = data.get("root_cause_report")
    if report and report != "Model artifact not available for SHAP analysis.":
        st.markdown(report)
    else:
        st.info("ℹ️ Root cause analysis requires model artifact. Currently using statistical drift detection only.")
        st.caption("To enable SHAP-based root cause analysis, pass the trained model object during registration.")

else:
    st.error("❌ Failed to fetch metrics. Please check if the API is running and the model is registered.")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("🛡️ Bias Drift Guardian | Built with Streamlit | Powered by Fairlearn & SHAP")
