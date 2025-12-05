# 🎯 How to Use the Bias Drift Guardian Dashboard

## 🚀 Quick Start

Your dashboard is **already running** at: **http://localhost:8501**

![Dashboard Demo](file:///C:/Users/demog/.gemini/antigravity/brain/8f118e26-224d-4490-a39c-2931bdda0349/dashboard_demo_1764408981345.webp)

---

## 📊 Dashboard Overview

### Left Sidebar: Configuration

1. **Select Model** - Dropdown showing all registered models:
   - `adult_v1` - Income prediction model
   - `german_credit_v1` - Credit risk model

2. **Refresh Metrics** - Click to reload latest analysis

### Main Panel: Metrics Display

#### Top Metrics (3 Cards)
- **Total Predictions** - Number of predictions logged
- **Fairness Score** - Overall fairness (0-100, higher is better)
- **Active Drift Alerts** - Number of features with significant drift

#### Drift Analysis Section
- **Table** - Shows all features with drift scores
  - Red rows = Drift detected (alert = true)
  - Blue rows = No drift (alert = false)
- **Bar Chart** - Visual comparison of drift scores
  - Red bars = Features with drift alerts
  - Blue bars = Normal features

#### Bias & Fairness Analysis Section
- **Tabs** - One tab per sensitive attribute (e.g., Sex, Race)
- **Metrics Cards**:
  - **Disparate Impact** - Ratio of selection rates (target: ~1.0)
  - **Demographic Parity Difference** - Difference in selection rates (target: ~0)
  - **Equalized Odds Difference** - Difference in error rates (target: ~0)
- **Selection Rate Chart** - Bar chart showing positive prediction rate by group

#### Root Cause Analysis Section
- Shows SHAP-based analysis (when model artifact is available)
- Currently shows: "Model artifact not available for SHAP analysis"

---

## 🎮 How to Use

### Step 1: Select a Model
1. Look at the **left sidebar**
2. Click the **"Select Model"** dropdown
3. Choose either:
   - `adult_v1` - To see income prediction bias analysis
   - `german_credit_v1` - To see credit risk drift analysis

### Step 2: View Metrics
The dashboard will automatically load and display:
- Total predictions logged
- Fairness score
- Drift alerts
- Bias metrics

### Step 3: Analyze Drift
1. Scroll to **"📉 Data Drift Analysis"**
2. Look at the table:
   - **Red rows** = Features with significant drift
   - Check the **score** column (higher = more drift)
   - Check the **p_value** column (lower = more significant)

**Example from German Credit**:
```
Feature: age
Type: numerical
Metric: KS+PSI
Score: 0.2733
P-value: 0.0001
Alert: TRUE ⚠️
```

### Step 4: Check Fairness
1. Scroll to **"⚖️ Bias & Fairness Analysis"**
2. Click on a sensitive attribute tab (e.g., "Sex" or "foreign_worker")
3. Review the metrics:
   - **Disparate Impact < 0.8** = Potential discrimination
   - **Demographic Parity Diff > 0.1** = Unfair selection rates
   - **Equalized Odds Diff > 0.1** = Unfair error rates

### Step 5: Compare Groups
Look at the **Selection Rate** bar chart:
- Compare the height of bars across groups
- Large differences indicate potential bias

**Example**:
```
Male: 0.75 (75% positive predictions)
Female: 0.45 (45% positive predictions)
→ Potential gender bias!
```

### Step 6: Refresh Data
- Click **"Refresh Metrics"** button to reload latest analysis
- Useful after running new predictions

---

## 🔍 Understanding the Metrics

### Fairness Score (0-100)
- **80-100**: Excellent fairness
- **60-79**: Good fairness
- **40-59**: Moderate bias concerns
- **0-39**: Significant bias detected

### Drift Scores
- **PSI (Population Stability Index)**:
  - < 0.1: No change
  - 0.1-0.25: Minor drift
  - \> 0.25: Major drift ⚠️

- **KS Statistic**:
  - < 0.1: Similar distributions
  - 0.1-0.3: Moderate drift
  - \> 0.3: Significant drift ⚠️

- **Chi-square**:
  - p-value < 0.05: Significant drift ⚠️

### Bias Metrics
- **Disparate Impact**:
  - 1.0 = Perfect fairness
  - < 0.8 = Potential discrimination (Four-Fifths Rule)

- **Demographic Parity Difference**:
  - 0.0 = Perfect parity
  - \> 0.1 = Significant disparity

---

## 🎬 Demo Workflow

### Scenario: Monitoring German Credit Model

1. **Select Model**: Choose `german_credit_v1` from dropdown

2. **Check Overall Health**:
   ```
   Total Predictions: 100
   Fairness Score: 60/100
   Active Drift Alerts: 2
   ```

3. **Investigate Drift**:
   - See that `age` has drift (Score: 0.27)
   - This makes sense - we simulated drift by adding noise!

4. **Check Fairness**:
   - Click "foreign_worker" tab
   - See selection rates by group
   - Fairness score of 60 indicates moderate bias

5. **Take Action**:
   - If drift detected: Retrain model with recent data
   - If bias detected: Adjust decision threshold or use fairness constraints

---

## 🛠️ Troubleshooting

### "Could not fetch models from API"
**Problem**: Dashboard can't connect to API  
**Solution**: 
```bash
# Check if API is running
curl http://localhost:8000/api/v1/health

# If not, start it
python -m api.main
```

### "No drift analysis data available yet"
**Problem**: No predictions logged  
**Solution**: Run a demo script
```bash
python examples/german_credit_demo.py
```

### Empty Dropdown
**Problem**: No models registered  
**Solution**: Run a demo to register a model
```bash
python examples/adult_demo.py
```

### Dashboard Not Loading
**Problem**: Streamlit not running  
**Solution**:
```bash
streamlit run dashboard/app.py
```

---

## 🎯 Best Practices

1. **Regular Monitoring**: Check dashboard daily in production
2. **Set Alerts**: Monitor fairness score < 60
3. **Investigate Drift**: Any drift alert warrants investigation
4. **Compare Trends**: Track metrics over time
5. **Document Actions**: Keep log of bias mitigation steps

---

## 🔗 Quick Links

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **List Models**: http://localhost:8000/api/v1/models

---

## 📸 Screenshots

The dashboard includes:
- ✅ Real-time metrics
- ✅ Interactive charts
- ✅ Model comparison
- ✅ Drill-down analysis
- ✅ Auto-refresh capability

**Your dashboard is ready to use!** 🎉
