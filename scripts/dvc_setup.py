"""
dvc_setup.py — One-Command DVC Initialization for Bias Drift Guardian
=====================================================================
WHAT THIS SCRIPT DOES :
  Think of DVC like Git, but for large files (datasets, model weights).
  Git tracks code. DVC tracks DATA. Together, they make your experiments
  100% reproducible — every commit = exact code + exact data + exact model.

INTERVIEW EXPLANATION:
  "I use DVC because `git commit` alone doesn't capture the data state.
  If someone clones my repo 6 months later, they get the same code but
  potentially different data. DVC solves this by creating a .dvc pointer
  file that knows the exact version of data used in each experiment."

HOW TO RUN:
  python scripts/dvc_setup.py

WHAT IT DOES:
  1. Initializes DVC in the project
  2. Adds data/ and mlruns/ to DVC tracking
  3. Creates a local DVC remote (./dvc-remote) — swap to S3 in production
  4. Does the first `dvc push` to commit the initial data snapshot
"""

import subprocess
import sys
import os
from pathlib import Path


def run(cmd: str, check: bool = True) -> str:
    """Run a shell command and return output."""
    print(f"\n>>> {cmd}")
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr and result.returncode != 0:
        print(f"[WARN] {result.stderr.strip()}")
    if check and result.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        sys.exit(1)
    return result.stdout.strip()


def is_dvc_initialized() -> bool:
    """Check if DVC is already set up in this repo."""
    return Path(".dvc").exists()


def main():
    print("=" * 60)
    print("  Bias Drift Guardian — DVC Setup")
    print("  Making your data pipeline reproducible")
    print("=" * 60)

    # --- STEP 1: Install DVC if not available ---
    print("\n[Step 1/5] Checking DVC installation...")
    result = subprocess.run("dvc --version", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("DVC not found. Installing...")
        run("pip install dvc")
    else:
        print(f"DVC already installed: {result.stdout.strip()}")

    # --- STEP 2: Initialize DVC ---
    print("\n[Step 2/5] Initializing DVC repository...")
    if not is_dvc_initialized():
        run("dvc init")
        print("DVC initialized successfully!")
    else:
        print("DVC already initialized. Skipping.")

    # --- STEP 3: Configure a local remote ---
    # In production you'd use: dvc remote add -d s3remote s3://your-bucket/dvc
    print("\n[Step 3/5] Setting up local DVC remote storage...")
    remote_path = Path("./dvc-remote").resolve()
    remote_path.mkdir(exist_ok=True)
    run(f'dvc remote add -d localremote "{remote_path}"', check=False)
    print(f"Local remote configured at: {remote_path}")
    print("[NOTE] Swap to S3 in production: dvc remote add -d s3remote s3://bucket/dvc")

    # --- STEP 4: Track data and model artifacts ---
    print("\n[Step 4/5] Adding data directories to DVC tracking...")

    # Track the data registry (where models and baselines are stored)
    data_dir = Path("data")
    if data_dir.exists() and any(data_dir.iterdir()):
        run("dvc add data/", check=False)
        print("'data/' directory tracked by DVC.")
    else:
        print("[SKIP] 'data/' directory is empty. Run a demo first to populate it.")

    # Track mlflow artifacts separately
    mlruns_dir = Path("mlruns")
    if mlruns_dir.exists() and any(mlruns_dir.iterdir()):
        run("dvc add mlruns/", check=False)
        print("'mlruns/' directory tracked by DVC.")
    else:
        print("[SKIP] 'mlruns/' directory is empty. Run 'python scripts/train_mlflow.py' first.")

    # --- STEP 5: Push to remote ---
    print("\n[Step 5/5] Pushing data snapshot to DVC remote...")
    run("dvc push", check=False)

    print("\n" + "=" * 60)
    print("  DVC Setup Complete!")
    print("=" * 60)
    print("""
NEXT STEPS:
  1. Commit the .dvc files to Git:
       git add .dvc/ data.dvc mlruns.dvc .gitignore
       git commit -m "feat: add DVC data versioning"

  2. After retraining a model, version the new data:
       dvc add data/
       git add data.dvc
       git commit -m "data: update registry after v2.0 training run"
       dvc push

  3. Anyone cloning the repo can reproduce your exact data:
       git clone <repo>
       dvc pull

INTERVIEW TIP:
  "With DVC, every Git tag corresponds to a specific dataset version.
  So when I say 'v1.0 model', it's not just the code — it's the exact
  training data, hyperparameters (MLflow), and evaluation metrics."
""")


if __name__ == "__main__":
    main()
