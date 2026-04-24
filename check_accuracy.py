"""
SolidGuard - Model Accuracy Checker
Run this anytime to see how well the model performs.

Usage:
    python check_accuracy.py
"""

import warnings
warnings.filterwarnings("ignore")

import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import cross_val_score, LeaveOneOut, StratifiedKFold

from feature_extractor import LABEL_NAMES

MODEL_PATH   = "models/model.pkl"
FEATURES_CSV = "data/features.csv"

# ── Load ──────────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("   SolidGuard - Model Accuracy Report")
print("=" * 55)

model = joblib.load(MODEL_PATH)
df    = pd.read_csv(FEATURES_CSV)

drop_cols = [c for c in ["file", "category"] if c in df.columns]
X = df.drop(columns=drop_cols + ["label"])
y = df["label"]

print(f"\n  Samples  : {len(df)}")
print(f"  Features : {len(X.columns)}")
print(f"  Classes  : {y.nunique()}")

# ── Class distribution ────────────────────────────────────────────────────────
print("\n  Class Distribution:")
print(f"  {'Label':<5} {'Category':<35} Count")
print("  " + "-" * 50)
for lbl in sorted(y.unique()):
    count = (y == lbl).sum()
    bar   = "#" * count
    print(f"  [{lbl:2d}]  {LABEL_NAMES.get(lbl, str(lbl)):<35} {count}  {bar}")

# ── Cross-validation ──────────────────────────────────────────────────────────
n = len(df)
if n < 30:
    cv      = LeaveOneOut()
    cv_name = "Leave-One-Out CV (small dataset)"
else:
    folds   = max(2, min(5, int(y.value_counts().min())))
    cv      = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    cv_name = f"{folds}-Fold Stratified CV"

scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")

print(f"\n  Cross-Validation  : {cv_name}")
print(f"  CV Accuracy       : {scores.mean():.2%}  (+/- {scores.std():.2%})")
print(f"  Min / Max         : {scores.min():.2%} / {scores.max():.2%}")

# ── Training accuracy ─────────────────────────────────────────────────────────
y_pred     = model.predict(X)
train_acc  = accuracy_score(y, y_pred)
print(f"  Train Accuracy    : {train_acc:.2%}  (on full training set)")

# ── Classification report ─────────────────────────────────────────────────────
labels = sorted(set(y) | set(y_pred))
names  = [LABEL_NAMES.get(l, str(l)) for l in labels]
print("\n  Classification Report (training data):")
print(classification_report(y, y_pred, labels=labels, target_names=names, zero_division=0))

# ── Feature importances ───────────────────────────────────────────────────────
imp  = model.feature_importances_
feat = list(X.columns)
idx  = np.argsort(imp)[::-1]
print("  Feature Importances (most -> least):")
print(f"  {'Feature':<28} {'Importance':>10}  Bar")
print("  " + "-" * 55)
for i in idx:
    bar = "#" * int(imp[i] * 40)
    print(f"  {feat[i]:<28} {imp[i]:>10.4f}  {bar}")
