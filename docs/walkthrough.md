# Bias Drift Detector - User Guide

This guide provides step-by-step instructions on how to set up, run, and use the Ethical AI Bias Drift Detector System.

## 1. Prerequisites

Ensure you have **Anaconda** or **Miniconda** installed on your system.
This project uses a Conda environment to manage dependencies and avoid conflicts.

## 2. Installation

1.  **Open your terminal** (Command Prompt or PowerShell on Windows).
2.  **Navigate to the project directory**:
    ```bash
    cd "g:/Project Directory/bias-drift-detector"
    ```
3.  **Create the Conda environment**:
    ```bash
    conda create -n Bias_Drift_Detector python=3.10
    ```
4.  **Activate the environment**:
    ```bash
    conda activate Bias_Drift_Detector
    ```
5.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 3. Running the Demo

The quickest way to see the system in action is to run the end-to-end demo script. This script:
- Loads the Adult Income dataset.
- Trains a Logistic Regression model.
- Registers the model with the API.
- Simulates data drift (by shifting Age).
- Logs predictions.
- Fetches and displays drift and bias metrics.

**Command:**
```bash
python examples/adult_demo.py
```

**Expected Output:**
You should see logs indicating model training, registration, prediction logging, and finally a summary of alerts:
- **Drift Alerts**: Features that have significantly changed (e.g., Age).
- **Fairness Score**: An overall score (0-100) indicating model fairness.
- **Disparate Impact**: Metrics showing bias against sensitive groups (e.g., Sex, Race).

## 4. Running the API Server

To use the system for your own models, you need to run the FastAPI server.

**Command:**
```bash
python api/main.py
```
*The server will start at `http://0.0.0.0:8000`.*

**Accessing Documentation:**
Open your browser and go to:
[http://localhost:8000/docs](http://localhost:8000/docs)

This interactive Swagger UI allows you to test endpoints directly.

## 5. Using the System for Your Models

### Step 1: Register your Model
Send a `POST` request to `/api/v1/models/register` with your model configuration and baseline data.
- **baseline_data**: A sample of your training data (list of dictionaries).
- **numerical_features**: List of numerical column names.
- **categorical_features**: List of categorical column names.
- **sensitive_attributes**: List of attributes to monitor for bias (e.g., "Gender", "ZipCode").

### Step 2: Log Predictions
Send `POST` requests to `/api/v1/predictions/log` whenever your model makes a prediction.
- **features**: The input features for the prediction.
- **prediction**: The model's output.
- **sensitive_features**: Values for the sensitive attributes (if not included in features).
- **true_label** (Optional): The ground truth, if available later (for accuracy/recall bias metrics).

### Step 3: Monitor Metrics
Send a `GET` request to `/api/v1/metrics/{model_id}` to retrieve the latest analysis.
- The system runs analysis in the background every 100 predictions.
- You will receive drift alerts, bias metrics, and root cause reports.

## 6. Project Structure

- **`core/`**: Contains the logic for drift detection, bias analysis, and root cause analysis.
- **`api/`**: Contains the FastAPI application (`main.py`).
- **`examples/`**: Contains demo scripts (`adult_demo.py`).
- **`requirements.txt`**: List of python dependencies.

## Troubleshooting

- **"Module not found"**: Ensure you have activated the conda environment (`conda activate Bias_Drift_Detector`) and installed requirements.
- **"Chi-square error"**: This might happen if a categorical feature has too few samples. The system handles this by skipping the test, but check your data quality.
