# 🚀 Deployment Guide - Bias Drift Guardian

## Overview

Your project has **two components** that need to be deployed:
1. **FastAPI Backend** (API server)
2. **Streamlit Dashboard** (Frontend)

## 🎯 Deployment Options

### Option 1: Full Stack Deployment (Recommended for Production)

Deploy both components to cloud platforms that support them.

#### Backend (FastAPI) → Render.com or Railway.app

**Why**: Free tier, supports Python backends, always-on

**Steps for Render.com**:

1. Create `render.yaml` in project root:
```yaml
services:
  - type: web
    name: bias-drift-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
```

2. Push to GitHub
3. Go to [render.com](https://render.com)
4. Click "New +" → "Blueprint"
5. Connect your GitHub repo
6. Deploy!

**Result**: You'll get a URL like `https://bias-drift-api.onrender.com`

#### Frontend (Streamlit) → Streamlit Community Cloud

1. Update `dashboard/app.py` to use deployed API:
```python
# Change this line:
API_URL = "http://localhost:8000/api/v1"

# To this (use your Render URL):
API_URL = os.getenv("API_URL", "https://bias-drift-api.onrender.com/api/v1")
```

2. Deploy to Streamlit Cloud (see below)

---

### Option 2: Demo-Only Deployment (Quick & Easy)

Deploy a **standalone version** of the dashboard with **pre-loaded demo data** (no live API needed).

**Pros**: 
- ✅ Deploy in 5 minutes
- ✅ Perfect for portfolio/interviews
- ✅ No backend hosting costs

**Cons**:
- ❌ Shows static demo data only
- ❌ Can't register new models

**I can create this version for you!**

---

## 📦 Streamlit Community Cloud Deployment (Step-by-Step)

### Prerequisites
- GitHub account
- Your code pushed to GitHub

### Step 1: Prepare Your Repository

1. **Ensure these files exist**:
   - `requirements.txt` ✅ (you have this)
   - `dashboard/app.py` ✅ (you have this)
   - `.gitignore` ✅ (you have this)

2. **Add a `.streamlit/config.toml`** (optional, for custom theme):
```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Step 2: Push to GitHub

```bash
cd "g:/Project Directory/bias-drift-detector"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for Streamlit deployment"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/bias-drift-detector.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Fill in:
   - **Repository**: `YOUR_USERNAME/bias-drift-detector`
   - **Branch**: `main`
   - **Main file path**: `dashboard/app.py`
5. Click "Deploy!"

**Deployment time**: ~2-3 minutes

---

## 🎨 Creating a Standalone Demo Version

Since your current dashboard requires the API, I recommend creating a **demo version** that works standalone.

### What I'll Create:

1. **`dashboard/demo_app.py`** - Standalone version with:
   - Pre-loaded German Credit demo data
   - Pre-calculated metrics
   - All visualizations working
   - No API dependency

2. **Benefits**:
   - ✅ Deploys instantly to Streamlit Cloud
   - ✅ Shows your full feature set
   - ✅ Perfect for portfolio/LinkedIn
   - ✅ Visitors can interact immediately

**Would you like me to create this standalone demo version?**

---

## 🔧 Environment Variables (For Full Deployment)

If deploying both API + Dashboard:

### On Render.com (API):
No special env vars needed for basic deployment.

### On Streamlit Cloud (Dashboard):
1. Go to App Settings → Secrets
2. Add:
```toml
API_URL = "https://your-api-url.onrender.com/api/v1"
```

3. Update `dashboard/app.py`:
```python
import os
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
```

---

## 📊 Cost Breakdown

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Streamlit Cloud** | ✅ Unlimited public apps | $20/mo for private |
| **Render.com** | ✅ 750 hours/month | $7/mo for always-on |
| **Railway.app** | ✅ $5 free credit/month | Pay-as-you-go |

**Recommendation**: Use free tiers for portfolio/demo. Both are sufficient.

---

## 🚀 Quick Start: Deploy Demo Version Now

If you want to deploy **immediately** for your portfolio:

1. I'll create `dashboard/demo_app.py` (standalone, no API needed)
2. You push to GitHub
3. Deploy to Streamlit Cloud pointing to `dashboard/demo_app.py`
4. **Live in 10 minutes!**

**Ready to proceed?** Let me know which option you prefer:
- **Option A**: Create standalone demo version (fast, portfolio-ready)
- **Option B**: Full stack deployment (API + Dashboard, production-ready)
- **Option C**: Both! (Demo for portfolio + Full stack for real use)
