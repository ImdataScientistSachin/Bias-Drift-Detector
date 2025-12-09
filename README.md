<div align="center">

# 🛡️ Bias Drift Guardian

### Real-time AI Fairness & Data Drift Monitoring System

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28%2B-FF4B4B.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**[Live Demo](https://bias-drift-detector.streamlit.app)** • **[Documentation](docs/INDEX.md)** • **[API Docs](http://localhost:8000/docs)** • **[Report Bug](https://github.com/ImdataScientistSachin/Bias-Drift-Detector/issues)**

<img src="https://img.shields.io/badge/Status-Production%20Ready-success" alt="Status">
<img src="https://img.shields.io/badge/Maintained-Yes-green" alt="Maintained">

---

### 🎯 **Detect bias before it becomes a lawsuit. Monitor drift before it breaks your model.**

</div>

---

## 📖 Table of Contents

- [🌟 Why Bias Drift Guardian?](#-why-bias-drift-guardian)
- [✨ Key Features](#-key-features)
- [🚀 Quick Start](#-quick-start)
- [📊 Demo & Screenshots](#-demo--screenshots)
- [🏗️ Architecture](#️-architecture)
- [💼 Use Cases](#-use-cases)
- [📚 Documentation](#-documentation)
- [🛠️ Installation](#️-installation)
- [🎓 Usage Examples](#-usage-examples)
- [🌐 API Reference](#-api-reference)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [📞 Contact](#-contact)

---

## 🌟 Why Bias Drift Guardian?

**The Problem:**
- 🚨 **80% of AI models** experience performance degradation in production due to data drift
- ⚖️ **$1M+ lawsuits** from algorithmic discrimination are becoming common
- 🔍 **Hidden bias** in intersectional groups (e.g., "Female employees 50+") goes undetected by standard tools

**The Solution:**
Bias Drift Guardian is a **production-ready monitoring system** that combines:
- ✅ **Data Drift Detection** - Catch distribution shifts before they break your model
- ✅ **Fairness Analysis** - Ensure compliance with EEOC and EU AI Act
- ✅ **Intersectional Bias Detection** - Unique feature that catches compound discrimination
- ✅ **Root Cause Analysis** - SHAP-based explanations for why drift is happening

---

## ✨ Key Features

### 🎯 **Intersectional Fairness Analysis** ⭐ UNIQUE
**What makes us different:** Most fairness tools only check one attribute at a time (gender OR age). We detect **compound bias** affecting specific subgroups.

**Example:**
```
Standard Analysis: "No gender bias" ✅ (Male: 70%, Female: 68%)
Our Analysis: "Female employees aged 50+ have only 38% approval rate!" ❌
```

**Why it matters:**
- 📋 EEOC compliance requirement
- 💼 Prevents discrimination lawsuits
- 🎓 Not available in standard Fairlearn

### 📊 **Comprehensive Drift Detection**
- **PSI (Population Stability Index)** - Industry standard for numerical features
- **KS Test** - Statistical distribution comparison
- **Chi-square Test** - Categorical feature drift

**Thresholds:**
- PSI < 0.1: ✅ No drift
- PSI 0.1-0.25: ⚠️ Monitor closely
- PSI > 0.25: ❌ Action required

### 🔍 **Root Cause Analysis**
SHAP-based feature importance drift detection:
```
Root Cause Analysis:
- age: Importance increased by 0.0847 (0.1234 → 0.2081)
- credit_amount: Decreased by 0.0423
Recommendation: Investigate data distribution changes
```

### 🌊 **Interactive Drift Simulation**
Educational tool to visualize how distribution shifts affect model performance in real-time.

### 📈 **Model Performance Monitoring**
- Confusion Matrix visualization
- Accuracy, Precision, Recall, F1-Score
- Error breakdown and actionable insights

---

## 🚀 Quick Start

### Option 1: Standalone Dashboard (30 seconds)
Perfect for demos and portfolio showcases.

```bash
# Clone repository
git clone https://github.com/ImdataScientistSachin/Bias-Drift-Detector.git
cd Bias-Drift-Detector

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run dashboard/app.py
```

**Access:** http://localhost:8501

### Option 2: Full Stack (5 minutes)
For production deployment with API backend.

```bash
# Install all dependencies
pip install -r requirements-full.txt

# Terminal 1: Start API
uvicorn api.main:app --reload

# Terminal 2: Start Dashboard
streamlit run dashboard/app.py
```

**Access:**
- 📊 Dashboard: http://localhost:8501
- 🌐 API: http://localhost:8000
- 📖 API Docs: http://localhost:8000/docs

### Option 3: Docker (Production)

```bash
docker-compose up -d
```

---

## 📊 Demo & Screenshots

### 🎬 Live Demo
**Try it now:** https://bias-drift-guardian.streamlit.app/

### 📸 Screenshots

<details>
<summary><b>📊 Dashboard Overview</b></summary>

**Top Metrics Cards**
- Total Predictions: 150
- Fairness Score: 60/100
- Drift Alerts: 4
- Average Drift Score: 0.18

</details>

<details>
<summary><b>🌊 Interactive Drift Simulation</b></summary>

Visualize how data distribution changes affect your model with real-time KS-test calculations.

</details>

<details>
<summary><b>🎯 Intersectional Bias Analysis</b></summary>

**Worst-Performing Groups:**
1. Female_50+ → 38% approval (Disparity: 0.48 ❌)
2. Female_40-50 → 52% approval (Disparity: 0.65 ⚠️)
3. Male_50+ → 58% approval (Disparity: 0.73 ⚠️)

</details>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BIAS DRIFT GUARDIAN                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   STREAMLIT      │     │   FASTAPI        │     │   CORE ENGINE    │
│   DASHBOARD      │────▶│   API            │────▶│   (Analytics)    │
│                  │     │                  │     │                  │
│ • Visualizations │     │ • REST Endpoints │     │ • Drift Detector │
│ • Metrics Cards  │     │ • Persistence    │     │ • Bias Analyzer  │
│ • Simulations    │     │ • Background     │     │ • Intersectional │
│                  │     │   Tasks          │     │ • Root Cause     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit | Interactive dashboard |
| **Backend** | FastAPI | REST API with async support |
| **Analytics** | Fairlearn, SHAP | Fairness metrics & explainability |
| **Data** | Pandas, NumPy | Data processing |
| **Visualization** | Plotly, Seaborn | Interactive charts |
| **Statistics** | SciPy, Scikit-learn | Statistical tests |

---

## 💼 Use Cases

### 🏦 Financial Services
**Scenario:** Credit scoring model monitoring
- Monitor for age/gender bias in loan approvals
- Detect drift in applicant demographics
- EEOC compliance reporting
- Prevent discrimination lawsuits

### 👔 HR & Recruiting
**Scenario:** Hiring algorithm fairness
- Intersectional bias detection (race × gender × age)
- Resume screening fairness analysis
- Legal risk mitigation
- Diversity & inclusion metrics

### 🏥 Healthcare
**Scenario:** Treatment recommendation systems
- Ensure equal treatment across demographics
- Monitor for patient population changes
- Regulatory compliance (HIPAA, GDPR)
- Ethical AI deployment

### 🛒 E-commerce
**Scenario:** Recommendation systems
- Prevent filter bubbles
- Ensure fair product exposure
- Monitor for seasonal drift
- A/B testing fairness

---

## 📚 Documentation

### 📖 Core Documentation
- **[Documentation Index](docs/INDEX.md)** - Start here for navigation
- **[Comprehensive Analysis](docs/COMPREHENSIVE_PROJECT_ANALYSIS.md)** - Technical deep dive (30 min read)
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Code examples & API docs (10 min read)
- **[Analysis Summary](docs/ANALYSIS_SUMMARY.md)** - Executive overview (5 min read)

### 🎓 Guides
- **[Dashboard Guide](docs/dashboard_guide.md)** - UI/UX documentation
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Fixes & Improvements](docs/FIXES_AND_IMPROVEMENTS.md)** - Change log

### 📊 Project Info
- **[Cleanup Plan](docs/CLEANUP_PLAN.md)** - Project structure
- **Grade:** ⭐⭐⭐⭐½ (4.5/5) - See [Analysis Summary](docs/ANALYSIS_SUMMARY.md)

---

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Git

### Dependencies

**Dashboard Only** (~30MB):
```bash
pip install -r requirements.txt
```

**Full Stack** (~150MB):
```bash
pip install -r requirements-full.txt
```

**Key Packages:**
- `streamlit` - Dashboard framework
- `fastapi` - API framework (full stack only)
- `fairlearn` - Fairness metrics (full stack only)
- `shap` - Explainability (full stack only)
- `pandas`, `numpy` - Data processing
- `plotly`, `seaborn` - Visualizations
- `scipy`, `scikit-learn` - Statistical tests

---

## 🎓 Usage Examples

### Example 1: Drift Detection

```python
from core.drift_detector import DriftDetector
import pandas as pd

# Initialize detector with baseline data
detector = DriftDetector(
    baseline_data=train_df,
    numerical_features=['age', 'credit_amount', 'duration'],
    categorical_features=['job', 'housing', 'purpose']
)

# Detect drift in production data
drift_results = detector.detect_feature_drift(production_df)

# Check for alerts
alerts = drift_results[drift_results['alert'] == True]
print(f"Drift detected in {len(alerts)} features:")
for _, row in alerts.iterrows():
    print(f"  - {row['feature']}: PSI={row['psi']:.3f}")
```

### Example 2: Bias Analysis

```python
from core.bias_analyzer import BiasAnalyzer

# Initialize analyzer
analyzer = BiasAnalyzer(sensitive_attrs=['Sex', 'Age_Group'])

# Calculate fairness metrics
metrics = analyzer.calculate_bias_metrics(
    y_true=true_labels,
    y_pred=predictions,
    sensitive_features=sensitive_df
)

# Check fairness score
print(f"Fairness Score: {metrics['fairness_score']}/100")

# Check disparate impact
for attr in ['Sex', 'Age_Group']:
    di = metrics[attr]['disparate_impact']
    status = "✅ PASS" if di >= 0.8 else "❌ FAIL"
    print(f"{attr} Disparate Impact: {di:.3f} {status}")
```

### Example 3: Intersectional Analysis

```python
from core.intersectional_analyzer import IntersectionalAnalyzer

# Initialize analyzer
analyzer = IntersectionalAnalyzer(
    sensitive_attrs=['Sex', 'Age_Group', 'Race']
)

# Analyze intersectional bias
results = analyzer.analyze_intersectional_bias(
    y_pred=predictions,
    sensitive_features=sensitive_df,
    min_group_size=10
)

# Get worst-performing groups
leaderboard = analyzer.get_intersectional_leaderboard(
    y_pred=predictions,
    sensitive_features=sensitive_df
)

print("Worst-Performing Groups:")
for group in leaderboard[:5]:
    print(f"  {group['group']}: {group['selection_rate']:.1%} "
          f"(Disparity: {group['disparity_ratio']:.2f})")
```

### Example 4: API Integration

```python
import requests

# Register model
response = requests.post("http://localhost:8000/api/v1/models/register", json={
    "model_id": "credit_model_v1",
    "numerical_features": ["age", "credit_amount"],
    "categorical_features": ["job", "housing"],
    "sensitive_attributes": ["Sex", "Age_Group"],
    "baseline_data": baseline_records
})

# Log prediction
requests.post("http://localhost:8000/api/v1/predictions/log", json={
    "model_id": "credit_model_v1",
    "features": {"age": 35, "credit_amount": 5000, "job": "skilled"},
    "prediction": 1,
    "sensitive_features": {"Sex": "Female", "Age_Group": "30-40"}
})

# Get metrics
metrics = requests.get("http://localhost:8000/api/v1/metrics/credit_model_v1").json()
print(f"Drift Alerts: {len([d for d in metrics['drift_analysis'] if d['alert']])}")
print(f"Fairness Score: {metrics['bias_analysis']['fairness_score']}")
```

### Example 5: Complete Demo

See working examples:
- **[German Credit Demo](examples/german_credit_demo.py)** - Credit risk analysis
- **[Adult Census Demo](examples/adult_demo.py)** - Income prediction
- **[Live API Client](examples/live_demo_client.py)** - API integration

---

## 🌐 API Reference

### Endpoints

#### 1. Register Model
```http
POST /api/v1/models/register
```

**Request Body:**
```json
{
  "model_id": "my_model_v1",
  "numerical_features": ["age", "income"],
  "categorical_features": ["job", "education"],
  "sensitive_attributes": ["Sex", "Race"],
  "baseline_data": [...]
}
```

#### 2. Log Prediction
```http
POST /api/v1/predictions/log
```

**Request Body:**
```json
{
  "model_id": "my_model_v1",
  "features": {"age": 35, "income": 50000},
  "prediction": 1,
  "true_label": 1,
  "sensitive_features": {"Sex": "Female", "Race": "Asian"}
}
```

#### 3. Get Metrics
```http
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

#### 4. List Models
```http
GET /api/v1/models
```

#### 5. Health Check
```http
GET /api/v1/health
```

**Full API Documentation:** http://localhost:8000/docs (when API is running)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Bias-Drift-Detector.git
cd Bias-Drift-Detector

# Install dev dependencies
pip install -r requirements-full.txt
pip install pytest pytest-asyncio black flake8

# Run tests (when available)
pytest tests/

# Format code
black .

# Lint code
flake8 .
```

### Code Style
- Follow PEP 8
- Use Black for formatting
- Add docstrings to all functions
- Include type hints where possible

---

## 🗺️ Roadmap

### ✅ Completed
- [x] Core drift detection (PSI, KS, Chi-square)
- [x] Fairness analysis (Disparate Impact, Demographic Parity, Equalized Odds)
- [x] Intersectional bias detection
- [x] Root cause analysis (SHAP)
- [x] Standalone Streamlit demo
- [x] FastAPI backend with persistence
- [x] Comprehensive documentation (2,800+ lines)
- [x] Docker support
- [x] Streamlit Cloud deployment

### 🚧 In Progress
- [ ] Unit tests (target: 80% coverage)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Performance optimizations

### 📋 Planned
- [ ] Time-series drift tracking
- [ ] Automated alerting (email/Slack)
- [ ] Model comparison features
- [ ] PostgreSQL integration
- [ ] Redis caching
- [ ] Kubernetes deployment guide
- [ ] Multi-language support
- [ ] Custom metric plugins

---

## ❓ FAQ

<details>
<summary><b>Can I use this with my own dataset?</b></summary>

Yes! The system is model-agnostic. Just register your model with baseline data and start logging predictions.
</details>

<details>
<summary><b>What models are supported?</b></summary>

Any scikit-learn compatible model. For SHAP analysis: RandomForest, XGBoost, LightGBM, and Linear models work best.
</details>

<details>
<summary><b>How much data do I need?</b></summary>

Minimum 500 samples for baseline. For production monitoring, analyze every 100-1000 predictions depending on risk level.
</details>

<details>
<summary><b>Is this GDPR compliant?</b></summary>

The system doesn't store sensitive data by default. For GDPR compliance, implement data anonymization and retention policies in your deployment.
</details>

<details>
<summary><b>How does intersectional analysis differ from standard bias analysis?</b></summary>

Standard analysis checks one attribute at a time (e.g., gender OR age). Intersectional analysis checks combinations (e.g., "Female employees aged 50+"), catching compound discrimination that single-attribute analysis misses.
</details>

<details>
<summary><b>Can I deploy this commercially?</b></summary>

Yes! This project is MIT licensed. You can use it commercially with attribution.
</details>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Citation

If you use this project in your research or work, please cite:

```bibtex
@software{bias_drift_guardian,
  author = {Sachin Paunikar},
  title = {Bias Drift Guardian: Real-time AI Fairness and Data Drift Monitoring},
  year = {2025},
  url = {https://github.com/ImdataScientistSachin/Bias-Drift-Detector}
}
```

---

## 🙏 Acknowledgments

- **[Fairlearn](https://fairlearn.org/)** - Microsoft's fairness toolkit
- **[SHAP](https://shap.readthedocs.io/)** - Lundberg & Lee's explainability framework
- **[Streamlit](https://streamlit.io/)** - Amazing dashboard framework
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[UCI ML Repository](https://archive.ics.uci.edu/ml/)** - German Credit & Adult Census datasets

### Inspiration
This project was inspired by the need for accessible, production-ready fairness monitoring tools in the ML community and the growing importance of ethical AI deployment.

---

## 📞 Contact

**Sachin Paunikar**

- 📧 Email: [ImdataScientistSachin@gmail.com](mailto:ImdataScientistSachin@gmail.com)
- 💼 LinkedIn: [linkedin.com/in/sachin-paunikar-datascientists](https://www.linkedin.com/in/sachin-paunikar-datascientists)
- 🐙 GitHub: [@ImdataScientistSachin](https://github.com/ImdataScientistSachin)

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! It helps others discover the project.

[![Star History Chart](https://api.star-history.com/svg?repos=ImdataScientistSachin/Bias-Drift-Detector&type=Date)](https://star-history.com/#ImdataScientistSachin/Bias-Drift-Detector&Date)

---

<div align="center">

**Made with ❤️ for Ethical AI**

[⬆ Back to Top](#-bias-drift-guardian)

</div>
