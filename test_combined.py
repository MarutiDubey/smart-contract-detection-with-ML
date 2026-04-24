"""
Test script to compare accuracy across different dataset configurations.
"""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
import joblib

from feature_extractor import LABEL_NAMES

# Label mapping
LABEL_MAP = {
    # 8-label paths
    './Dataset/reentrancy (RE)/': 1,
    './Dataset/integer overflow (OF)/': 3,
    './Dataset/unchecked external call (UC)': 5,
    './Dataset/timestamp dependency (TP)/': 6,
    './Dataset/block number dependency (BN)': 6,
    './Dataset/dangerous delegatecall (DE)/': 12,
    './Dataset/ether strict equality (SE)': 13,
    './Dataset/ether frozen (EF)': 14,
    # 4-label paths
    '/content/drive/My Drive/SC_Dataset/reentrancy (RE)/': 1,
    '/content/drive/My Drive/SC_Dataset/integer overflow (OF)/': 3,
    '/content/drive/My Drive/SC_Dataset/timestamp dependency (TP)/': 6,
    '/content/drive/My Drive/SC_Dataset/dangerous delegatecall (DE)/': 12,
}

def load_and_process(csv_path):
    """Load CSV and convert to features."""
    df = pd.read_csv(csv_path)

    rows = []
    for idx, row in df.iterrows():
        code = str(row.get('code', ''))
        label_str = str(row.get('label', ''))

        # Extract features (same logic as train_from_csv.py)
        from feature_extractor import extract_features
        features = extract_features(code)
        numeric_label = LABEL_MAP.get(label_str, 0)

        rows.append({**features, "label": numeric_label})

    return pd.DataFrame(rows)

def evaluate_dataset(name, df):
    """Evaluate a dataset and print results."""
    X = df.drop(columns=["label"])
    y = df["label"]

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Samples  : {len(df)}")
    print(f"  Features : {len(X.columns)}")
    print(f"  Classes  : {y.nunique()}")

    # Class distribution
    print(f"\n  Class Distribution:")
    for lbl in sorted(y.unique()):
        count = (y == lbl).sum()
        bar = "#" * min(count, 60)
        print(f"  [{lbl:2d}] {LABEL_NAMES.get(lbl, str(lbl)):<35} {count:5d}  {bar}")

    # Cross-validation
    min_class_count = y.value_counts().min()
    n_folds = min(5, max(2, min_class_count))
    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    model = RandomForestClassifier(n_estimators=200, max_depth=10,
                                   class_weight="balanced", random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")

    # Train final model
    model.fit(X, y)
    y_pred = model.predict(X)
    train_acc = sum(y == y_pred) / len(y)

    print(f"\n  Cross-Validation Accuracy: {scores.mean():.2%} (+/- {scores.std():.2%})")
    print(f"  Train Accuracy:            {train_acc:.2%}")

    # Classification report
    labels_present = sorted(set(y) | set(y_pred))
    target_names = [LABEL_NAMES.get(l, f"Class {l}") for l in labels_present]
    print("\n  Classification Report:")
    print(classification_report(y, y_pred, labels=labels_present,
                                target_names=target_names, zero_division=0))

    return {
        "name": name,
        "samples": len(df),
        "classes": y.nunique(),
        "cv_acc": scores.mean(),
        "train_acc": train_acc,
    }

def main():
    print("\n" + "="*60)
    print("  SOLIDGUARD - DATASET COMPARISON ANALYSIS")
    print("="*60)

    results = []

    # Test 1: 4-label only
    df4 = load_and_process("data/4label.csv")
    results.append(evaluate_dataset("4-LABEL DATASET (Original)", df4))

    # Test 2: 8-label only
    df8 = load_and_process("data/8label.csv")
    results.append(evaluate_dataset("8-LABEL DATASET", df8))

    # Test 3: COMBINED
    df_combined = pd.concat([df4, df8], ignore_index=True)
    results.append(evaluate_dataset("COMBINED (4-label + 8-label)", df_combined))

    # Summary table
    print("\n" + "="*60)
    print("  SUMMARY COMPARISON")
    print("="*60)
    print(f"  {'Dataset':<35} {'Samples':>10} {'Classes':>8} {'CV Acc':>10} {'Train Acc':>10}")
    print("  " + "-"*75)
    for r in results:
        print(f"  {r['name']:<35} {r['samples']:>10} {r['classes']:>8} {r['cv_acc']:>9.2%} {r['train_acc']:>10.2%}")

    # Recommendation
    print("\n" + "="*60)
    print("  RECOMMENDATION")
    print("="*60)

    best = max(results, key=lambda x: x['cv_acc'])
    print(f"\n  Best CV Accuracy: {best['name']} ({best['cv_acc']:.2%})")

    if best['name'] == "COMBINED (4-label + 8-label)":
        print("\n  YES! You SHOULD combine both datasets.")
        print("  - More samples = better generalization")
        print("  - Reduces overfitting on small classes")
    else:
        print(f"\n  Using only {best['name']} gives better results.")
        print("  Combining may introduce noise or duplicate samples.")

if __name__ == "__main__":
    main()
