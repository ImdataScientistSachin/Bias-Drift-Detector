# 🚀 Bias Drift Guardian - Quick Reference Guide

**Last Updated:** December 8, 2025

---

## 📁 Project Structure

```
bias-drift-detector/
│
├── 🧠 core/                        # Analytics Engine
│   ├── drift_detector.py           # PSI, KS-test, Chi-square
│   ├── bias_analyzer.py            # Fairness metrics (Fairlearn)
│   ├── intersectional_analyzer.py  # ⭐ Unique intersectional bias detection
│   └── root_cause.py               # SHAP-based analysis
│
├── 🌐 api/                         # FastAPI Backend
│   └── main.py                     # REST API (5 endpoints)
│
├── 📊 dashboard/                   # Streamlit Frontend
│   └── app.py                      # Standalone demo (MAIN FILE)
│
├── 📚 examples/                    # Usage Examples
│   ├── german_credit_demo.py       # German Credit dataset
│   └── adult_demo.py               # Adult Census dataset
│
├── 📖 docs/                        # Documentation
│   ├── COMPREHENSIVE_PROJECT_ANALYSIS.md  # ⭐ Full analysis
│   └── FIXES_AND_IMPROVEMENTS.md          # ⭐ Recent fixes
│
├── requirements.txt                # Dashboard dependencies (30MB)
└── requirements-full.txt           # Full stack dependencies (150MB)
```

---

## ⚡ Quick Start

### Option 1: Dashboard Only (Fastest)
```bash
# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run dashboard/app.py
```
**Access:** http://localhost:8501

### Option 2: Full Stack (API + Dashboard)
```bash
# Install all dependencies
pip install -r requirements-full.txt

# Terminal 1: Start API
uvicorn api.main:app --reload

# Terminal 2: Start Dashboard
streamlit run dashboard/app.py
```
**API:** http://localhost:8000  
**Dashboard:** http://localhost:8501  
**API Docs:** http://localhost:8000/docs

---

## 🎯 Key Features

### 1. Data Drift Detection
**What it does:** Detects when production data differs from training data

**Metrics:**
- **PSI (Population Stability Index)** - Numerical features
  - < 0.1: ✅ No drift
  - 0.1-0.25: ⚠️ Minor drift
  - \> 0.25: ❌ Major drift
  
- **KS Test (Kolmogorov-Smirnov)** - Numerical features
  - p-value < 0.05: ❌ Significant drift
  
- **Chi-square Test** - Categorical features
  - p-value < 0.05: ❌ Significant drift

**Code Example:**
```python
from core.drift_detector import DriftDetector

detector = DriftDetector(
    baseline_data=train_df,
    numerical_features=['age', 'credit_amount'],
    categorical_features=['job', 'housing']
)

results = detector.detect_feature_drift(production_df)
```

---

### 2. Bias & Fairness Analysis
**What it does:** Evaluates model fairness across demographic groups

**Metrics:**
- **Disparate Impact** - Should be ≥ 0.8 (Four-Fifths Rule)
- **Demographic Parity Difference** - Should be ≤ 0.1
- **Equalized Odds Difference** - Should be ≤ 0.1

**Code Example:**
```python
from core.bias_analyzer import BiasAnalyzer

analyzer = BiasAnalyzer(sensitive_attrs=['Sex', 'Age_Group'])

metrics = analyzer.calculate_bias_metrics(
    y_true=true_labels,
    y_pred=predictions,
    sensitive_features=sensitive_df
)

print(f"Fairness Score: {metrics['fairness_score']}/100")
```

---

### 3. Intersectional Bias Detection ⭐
**What it does:** Detects bias in subgroups (e.g., "Female employees aged 50+")

**Why it's unique:**
- Most tools only check single attributes
- This catches compound discrimination
- EEOC compliance requirement

**Code Example:**
```python
from core.intersectional_analyzer import IntersectionalAnalyzer

analyzer = IntersectionalAnalyzer(
    sensitive_attrs=['Sex', 'Age_Group', 'Race']
)

results = analyzer.analyze_intersectional_bias(
    y_pred=predictions,
    sensitive_features=sensitive_df
)

# Get worst-performing groups
leaderboard = analyzer.get_intersectional_leaderboard(
    y_pred=predictions,
    sensitive_features=sensitive_df
)
```

---

### 4. Root Cause Analysis
**What it does:** Explains WHY drift is happening using SHAP values

**Code Example:**
```python
from core.root_cause import RootCauseAnalyzer

analyzer = RootCauseAnalyzer()

drift_analysis = analyzer.analyze_feature_importance_drift(
    model=trained_model,
    baseline_data=train_df,
    current_data=production_df
)

report = analyzer.generate_report(drift_analysis)
print(report)
```

---

## 🌐 API Endpoints

### 1. Register Model
```bash
POST /api/v1/models/register
```
**Payload:**
```json
{
  "model_id": "my_model_v1",
  "numerical_features": ["age", "credit_amount"],
  "categorical_features": ["job", "housing"],
  "sensitive_attributes": ["Sex", "Age_Group"],
  "baseline_data": [
    {"age": 35, "credit_amount": 5000, "job": "skilled", ...},
    ...
  ]
}
```

### 2. Log Prediction
```bash
POST /api/v1/predictions/log
```
**Payload:**
```json
{
  "model_id": "my_model_v1",
  "features": {"age": 40, "credit_amount": 7500, ...},
  "prediction": 1,
  "true_label": 1,
  "sensitive_features": {"Sex": "Female", "Age_Group": "40-50"}
}
```

### 3. Get Metrics
```bash
GET /api/v1/metrics/{model_id}
```
**Response:**
```json
{
  "model_id": "my_model_v1",
  "total_predictions": 150,
  "drift_analysis": [...],
  "bias_analysis": {...},
  "root_cause_report": "..."
}
```

### 4. List Models
```bash
GET /api/v1/models
```

### 5. Health Check
```bash
GET /api/v1/health
```

---

## 📊 Dashboard Sections

### 1. Top Metrics Cards
- Total Predictions
- Fairness Score (0-100)
- Drift Alerts Count
- Average Drift Score

### 2. Drift Analysis
- Interactive table with alerts
- Bar chart visualization
- Educational tooltips

### 3. Interactive Drift Simulation 🌊
- Slider to simulate drift (0-100%)
- Side-by-side distribution comparison
- Real-time KS-test

### 4. Bias Analysis (Tabs)
- Per-attribute analysis
- Selection rate charts
- Accuracy comparison
- Pass/Fail indicators

### 5. Intersectional Analysis ⭐
- Worst-performing groups leaderboard
- Intersectional fairness score
- Visual heatmap

### 6. Model Performance
- Confusion Matrix
- Accuracy, Precision, Recall, F1
- Error breakdown

### 7. Root Cause Analysis
- Feature importance drift
- Top drifting features
- Recommendations

---

## 🎓 Common Use Cases

### Use Case 1: Monitor Production Model
```python
# 1. Register model with baseline data
# 2. Log predictions as they happen
# 3. Check metrics periodically
# 4. Investigate if drift/bias detected
```

### Use Case 2: Pre-deployment Audit
```python
# 1. Load test dataset
# 2. Run bias analysis
# 3. Check intersectional fairness
# 4. Fix issues before deployment
```

### Use Case 3: A/B Testing
```python
# 1. Register Model A and Model B
# 2. Log predictions from both
# 3. Compare fairness scores
# 4. Choose better model
```

---

## 🐛 Troubleshooting

### Issue: Import Errors
```bash
# Solution: Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Streamlit Won't Start
```bash
# Solution: Clear cache
streamlit cache clear
pip install --upgrade streamlit
```

### Issue: API Won't Start
```bash
# Solution: Check dependencies
pip install -r requirements-full.txt

# Check if port is available
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
```

### Issue: SHAP Errors
```bash
# Solution: Ensure model is compatible
# Supported: RandomForest, XGBoost, LightGBM, Linear models
# Unsupported: Custom models without predict() method
```

---

## 📚 Key Concepts

### PSI (Population Stability Index)
**Formula:**
```
PSI = Σ (Actual% - Expected%) × ln(Actual% / Expected%)
```
**Interpretation:**
- Measures distribution shift
- Higher = more drift
- Industry standard in credit scoring

### Four-Fifths Rule
**Formula:**
```
Disparate Impact = min(selection_rate) / max(selection_rate)
```
**Interpretation:**
- EEOC standard for discrimination
- Must be ≥ 0.8 (80%)
- Example: If males approved at 80%, females must be ≥ 64%

### SHAP Values
**Concept:**
- Game theory approach
- Shows feature contribution to predictions
- Model-agnostic

**Example:**
```
Prediction: 0.85 (approve loan)
Base value: 0.50
SHAP contributions:
  - age: +0.15
  - credit_amount: +0.10
  - job: +0.05
  - housing: +0.05
```

---

## 🎯 Best Practices

### 1. Baseline Data Selection
- ✅ Use representative training data
- ✅ Minimum 500 samples
- ✅ Include all feature distributions
- ❌ Don't use test data as baseline

### 2. Monitoring Frequency
- High-risk models: Every 100 predictions
- Medium-risk: Every 1,000 predictions
- Low-risk: Daily/weekly batch analysis

### 3. Alert Thresholds
- PSI > 0.25: Immediate investigation
- Disparate Impact < 0.8: Legal review
- Fairness Score < 60: Retrain model

### 4. Intersectional Analysis
- ✅ Always check 2-way combinations
- ✅ Check 3-way if high-stakes (hiring, lending)
- ✅ Set min_group_size ≥ 10 to avoid noise

---

## 📈 Performance Tips

### 1. SHAP Optimization
```python
# Use smaller sample for faster analysis
analyzer.analyze_feature_importance_drift(
    model=model,
    baseline_data=train_df.sample(100),  # Instead of full dataset
    current_data=prod_df.sample(100)
)
```

### 2. Batch Processing
```python
# Log predictions in batches
predictions_batch = [...]
for pred in predictions_batch:
    client.post("/api/v1/predictions/log", json=pred)
```

### 3. Caching
```python
# Cache drift analysis results
@st.cache_data(ttl=3600)  # 1 hour cache
def get_drift_analysis(model_id):
    return client.get(f"/api/v1/metrics/{model_id}").json()
```

---

## 🔗 Useful Links

- **Fairlearn Docs:** https://fairlearn.org/
- **SHAP Docs:** https://shap.readthedocs.io/
- **Streamlit Docs:** https://docs.streamlit.io/
- **FastAPI Docs:** https://fastapi.tiangolo.com/

---

## 📞 Support

**Issues?** Check:
1. `docs/COMPREHENSIVE_PROJECT_ANALYSIS.md` - Full analysis
2. `docs/FIXES_AND_IMPROVEMENTS.md` - Recent fixes
3. GitHub Issues (if public repo)

**Contact:**
- Email: ImdataScientistSachin@gmail.com
- LinkedIn: [Sachin Paunikar](https://www.linkedin.com/in/sachin-paunikar-datascientists)

---

**Version:** 1.0  
**Last Updated:** December 8, 2025  
**Status:** ✅ Production Ready
