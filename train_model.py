"""
Train a Random Forest classifier for multi-class smart contract vulnerability detection.

ML Method: Random Forest Classifier (scikit-learn)
────────────────────────────────────────────────────
Random Forest is an ensemble learning method that builds multiple decision trees
and merges them together to get a more accurate and stable prediction.

Why Random Forest?
  - Works well with small datasets (our case: ~25 contracts)
  - Handles binary features (0/1) efficiently
  - Provides feature importance rankings
  - Resistant to overfitting with balanced class weights
  - No need for feature scaling/normalization

Alternative methods you can try:
  - KNN (K-Nearest Neighbors) — good for small datasets, simple
  - SVM (Support Vector Machine) — good for binary classification
  - XGBoost / LightGBM — better for larger datasets

Categories (from smart-contracts-set):
    0 = Safe
    1 = Reentrancy
    2 = Denial of Service (DoS)
    3 = Integer Overflow / Underflow
    4 = Access Control
    5 = Unchecked External Call
    6 = Bad Randomness
    7 = Race Condition (Front-Running)
    8 = Honeypot
    9 = Forced Ether Reception
   10 = Incorrect Interface
   11 = Variable Shadowing

Usage:
    python train_model.py                              # default settings
    python train_model.py --features data/features.csv # custom features file
    python train_model.py --model models/model.pkl     # custom model output

To add more training data:
    1. Add .sol files to the relevant folder inside smart-contracts-set/
    2. Re-run feature_extractor.py to regenerate data/features.csv
    3. Re-run this script to retrain the model
"""

import argparse
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    cross_val_score,
    StratifiedKFold,
    LeaveOneOut,
)
from sklearn.metrics import classification_report
import joblib

from feature_extractor import LABEL_NAMES


MODEL_INFO = {
    "method": "Random Forest Classifier",
    "library": "scikit-learn",
    "n_estimators": 200,
    "max_depth": 10,
    "class_weight": "balanced",
    "description": (
        "Ensemble of 200 decision trees with balanced class weights. "
        "Trained on binary features extracted from Solidity source code patterns."
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train multi-class vulnerability detection model."
    )
    parser.add_argument(
        "--features", default="data/features.csv", help="Path to features CSV"
    )
    parser.add_argument(
        "--model", default="models/model.pkl", help="Output model file path"
    )
    parser.add_argument(
        "--algo", default="rf", choices=["rf", "xgb", "svm", "knn"], 
        help="Algorithm: rf=Random Forest, xgb=XGBoost/GradientBoosting, svm=SVM, knn=KNN"
    )
    args = parser.parse_args()

    # -- Load data --------------------------------------------------------
    if not os.path.exists(args.features):
        print(f"[ERROR] Features file not found: {args.features}")
        print("  Run 'python feature_extractor.py' first to generate it.")
        return

    df = pd.read_csv(args.features)
    if "label" not in df.columns:
        print("[ERROR] No 'label' column found in features file.")
        return

    drop_cols = [c for c in ["file", "category"] if c in df.columns]
    X = df.drop(columns=drop_cols + ["label"])
    y = df["label"]

    print("=" * 60)
    print("  Smart Contract Vulnerability Detection - Model Training")
    print("=" * 60)
    print(f"\n  ML Method  : {MODEL_INFO['method']}")
    print(f"  Library    : {MODEL_INFO['library']}")
    print(f"  Estimators : {MODEL_INFO['n_estimators']}")
    print(f"  Features   : {len(X.columns)}")
    print(f"  Samples    : {len(df)}")
    print(f"  Classes    : {y.nunique()}")

    print("\n-- Class Distribution --")
    for lbl in sorted(y.unique()):
        count = (y == lbl).sum()
        bar = "#" * count
        print(f"  {LABEL_NAMES.get(lbl, f'Class {lbl}'):35s} : {count:3d}  {bar}")

    # -- Model ------------------------------------------------------------
    if args.algo == "rf":
        print("\n[INFO] Initializing Random Forest...")
        model = RandomForestClassifier(
            n_estimators=MODEL_INFO["n_estimators"],
            max_depth=MODEL_INFO["max_depth"],
            random_state=42,
            class_weight=MODEL_INFO["class_weight"],
            n_jobs=-1,
        )
    elif args.algo == "xgb":
        print("\n[INFO] Initializing Gradient Boosting (XGBoost alternative)...")
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
    elif args.algo == "svm":
        print("\n[INFO] Initializing Support Vector Machine (SVM)...")
        from sklearn.svm import SVC
        model = SVC(kernel="rbf", class_weight="balanced", probability=True, random_state=42)
    elif args.algo == "knn":
        print("\n[INFO] Initializing K-Nearest Neighbors (KNN)...")
        from sklearn.neighbors import KNeighborsClassifier
        model = KNeighborsClassifier(n_neighbors=3, n_jobs=-1)

    # -- Apply SMOTE to handle class imbalance ----------------------------
    if len(y) > 100:
        print("\n[INFO] Applying SMOTE to balance classes...")
        from imblearn.over_sampling import SMOTE
        sm = SMOTE(random_state=42, k_neighbors=min(5, y.value_counts().min()-1))
        X, y = sm.fit_resample(X, y)
        print(f"  [OK] After SMOTE: {len(y)} samples")

    # -- Training strategy based on dataset size --------------------------
    n_samples = len(X)
    n_classes = y.nunique()

    if n_samples < 5 or n_classes < 2:
        print("\n[WARN] Too few samples/classes. Training on all data (no eval split).")
        model.fit(X, y)
    else:
        # Use Leave-One-Out or Stratified K-Fold depending on size
        if n_samples < 30:
            print("\n-> Using Leave-One-Out Cross-Validation (small dataset)...")
            loo = LeaveOneOut()
            scores = cross_val_score(model, X, y, cv=loo, scoring="accuracy")
        else:
            n_folds = min(5, min(y.value_counts()))
            n_folds = max(2, n_folds)
            print(f"\n-> Using {n_folds}-Fold Stratified Cross-Validation...")
            skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
            scores = cross_val_score(model, X, y, cv=skf, scoring="accuracy")

        print(f"  Cross-Val Accuracy: {scores.mean():.2%} (+/-{scores.std():.2%})")

        # Train final model on ALL data
        model.fit(X, y)

        # Show full classification report (on training data for small sets)
        y_pred = model.predict(X)
        labels_present = sorted(set(y) | set(y_pred))
        target_names = [LABEL_NAMES.get(l, f"Class {l}") for l in labels_present]
        print("\n-- Classification Report (on training data) --")
        print(
            classification_report(
                y, y_pred,
                labels=labels_present,
                target_names=target_names,
                zero_division=0,
            )
        )

    # -- Feature importances ----------------------------------------------
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        feat_names = list(X.columns)
        sorted_idx = np.argsort(importances)[::-1]
        print("-- Feature Importances --")
        for i in sorted_idx:
            bar = "#" * int(importances[i] * 40)
            print(f"  {feat_names[i]:25s} {importances[i]:.4f}  {bar}")
    else:
        print(f"\n-- {args.algo.upper()} does not provide native feature importances --")

    # -- Save -------------------------------------------------------------
    os.makedirs(os.path.dirname(args.model) or ".", exist_ok=True)
    joblib.dump(model, args.model)
    print(f"\n[OK] Model saved to {args.model}")
    print(f"\n  To retrain with more data:")
    print(f"  1. Add .sol files to smart-contracts-set/<category>/")
    print(f"  2. python feature_extractor.py")
    print(f"  3. python train_model.py")


if __name__ == "__main__":
    main()
