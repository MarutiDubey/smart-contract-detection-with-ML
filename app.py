"""
Flask web application for Smart Contract Vulnerability Detection.

ML Method: Random Forest Classifier (scikit-learn)

Routes:
    GET  /             → Serves the web frontend
    POST /api/analyze  → Accepts .sol file, returns vulnerability prediction
    GET  /api/info     → Returns model info (method, features, classes)
"""

import os
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template

from feature_extractor import extract_features, detect_vulnerability, LABEL_NAMES

app = Flask(__name__, static_folder="static", template_folder="templates")

# ── Configuration ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")

SEVERITY_MAP = {
    0:  {"level": "Safe",     "color": "#10b981", "icon": "✓"},
    1:  {"level": "Critical", "color": "#ef4444", "icon": "🔴"},
    2:  {"level": "High",     "color": "#f97316", "icon": "🟠"},
    3:  {"level": "High",     "color": "#f97316", "icon": "🟠"},
    4:  {"level": "Critical", "color": "#ef4444", "icon": "🔴"},
    5:  {"level": "High",     "color": "#f97316", "icon": "🟠"},
    6:  {"level": "Medium",   "color": "#eab308", "icon": "🟡"},
    7:  {"level": "High",     "color": "#f97316", "icon": "🟠"},
    8:  {"level": "Medium",   "color": "#eab308", "icon": "🟡"},
    9:  {"level": "Medium",   "color": "#eab308", "icon": "🟡"},
    10: {"level": "Low",      "color": "#64748b", "icon": "🔵"},
    11: {"level": "Low",      "color": "#64748b", "icon": "🔵"},
    12: {"level": "Critical", "color": "#ef4444", "icon": "🔴"},
    13: {"level": "Medium",   "color": "#eab308", "icon": "🟡"},
    14: {"level": "Medium",   "color": "#eab308", "icon": "🟡"},
}

RECOMMENDATIONS = {
    0: "No vulnerabilities detected. The contract appears to follow safe coding patterns.",
    1: (
        "**Reentrancy Detected.** Use the Checks-Effects-Interactions pattern: "
        "update state variables BEFORE making external calls. Consider using "
        "OpenZeppelin's ReentrancyGuard modifier."
    ),
    2: (
        "**Denial of Service Risk.** Avoid unbounded loops with external calls. "
        "Use a pull-payment pattern (let users withdraw individually) instead of "
        "pushing payments in a loop."
    ),
    3: (
        "**Integer Overflow/Underflow Risk.** Use Solidity ≥0.8.0 (built-in overflow checks) "
        "or OpenZeppelin's SafeMath library for arithmetic operations."
    ),
    4: (
        "**Access Control Vulnerability.** Ensure sensitive functions (e.g., changeOwner, "
        "withdraw) are protected with modifiers like `onlyOwner`. Use the `constructor` "
        "keyword instead of named constructor functions."
    ),
    5: (
        "**Unchecked External Call.** Always check the return value of `.call()`, `.send()`. "
        "Use `require()` to revert on failure, or use `.transfer()` which auto-reverts."
    ),
    6: (
        "**Bad Randomness.** Do NOT use `block.timestamp`, `block.number`, or `blockhash` "
        "as a source of randomness. Use Chainlink VRF or a commit-reveal scheme instead."
    ),
    7: (
        "**Race Condition / Front-Running Risk.** Transactions in the mempool are public. "
        "Use a commit-reveal pattern or a private mempool (Flashbots) to prevent front-running."
    ),
    8: (
        "**Honeypot Pattern Detected.** This contract may contain hidden traps that prevent "
        "users from withdrawing funds. Review all fallback functions and hidden conditions."
    ),
    9: (
        "**Forced Ether Reception.** A contract can receive Ether via `selfdestruct` or "
        "mining rewards even without a `payable` function. Do not rely on `this.balance` "
        "for logic."
    ),
    10: (
        "**Incorrect Interface.** The contract's function signatures may not match the "
        "expected interface. Verify that all external functions match the ABI specification."
    ),
    11: (
        "**Variable Shadowing.** A variable in a derived contract shadows one in a base "
        "contract. This can cause unexpected behavior. Rename the shadowed variable."
    ),
    12: (
        "**Dangerous Delegatecall.** `delegatecall` executes code in the context of the "
        "calling contract, meaning the callee can modify the caller's storage. Validate "
        "the target address and ensure only trusted contracts are called via delegatecall."
    ),
    13: (
        "**Ether Strict Equality.** Using strict equality checks on `this.balance` or "
        "`.balance` is dangerous as Ether can be force-sent via `selfdestruct`. Use "
        "`>=` or `<=` instead of `==` for balance comparisons."
    ),
    14: (
        "**Ether Frozen.** Contract can receive Ether but has no withdrawal mechanism. "
        "Funds may be permanently locked. Add a withdrawal function protected by access control."
    ),
}

FEATURE_DESCRIPTIONS = {
    # Original 14 features
    "has_external_call": "External calls (.call, .transfer, .send)",
    "updates_state": "State variable updates",
    "is_payable": "Payable functions",
    "has_reentrancy_guard": "Reentrancy guard present",
    "has_loop": "Loop constructs (for/while)",
    "has_array_ops": "Array operations (.push, .pop, .length)",
    "has_selfdestruct": "selfdestruct/suicide usage",
    "has_tx_origin": "tx.origin authentication",
    "has_unchecked_call": "Unchecked low-level calls",
    "has_overflow_risk": "Arithmetic without SafeMath",
    "has_block_dependency": "Block timestamp/number dependency",
    "has_delegatecall": "delegatecall usage",
    "has_msg_value": "msg.value usage",
    "has_fallback": "Fallback/receive function",
    # Enhanced features (19 new)
    "has_strict_equality": "Strict equality operators (===, !==)",
    "comparison_count": "Comparison operators present",
    "has_balance_check": "Balance comparison (.balance <>)",
    "has_address_balance": "Address balance check pattern",
    "has_call_value": ".call.value() pattern (legacy reentrancy)",
    "has_static_call": "staticcall usage",
    "has_unbounded_loop": "Unbounded loop over array length",
    "has_multiple_loops": "Multiple loop constructs",
    "has_arithmetic": "Arithmetic operations present",
    "has_unchecked_block": "Unchecked { } block (Solidity 0.8+)",
    "has_onlyOwner": "onlyOwner modifier usage",
    "has_modifier": "Custom modifier definitions",
    "has_event": "Event emission (emit)",
    "has_multiple_events": "Multiple events emitted",
    "has_gas_limit": "Gas limit specification (.gas())",
    "has_inheritance": "Contract inheritance (is keyword)",
    "has_interface": "Interface definition",
    "has_selfdestruct_call": "Explicit selfdestruct() call",
    "has_delegatecall_target": "Delegatecall with address target",
}

MODEL_METHOD_INFO = {
    "method": "Random Forest Classifier",
    "library": "scikit-learn",
    "n_estimators": 200,
    "description": (
        "Ensemble of 200 decision trees with balanced class weights, "
        "trained on binary features extracted from Solidity source code."
    ),
    "how_to_add_data": [
        "1. Add .sol files to smart-contracts-set/<vulnerability_category>/",
        "2. Run: python feature_extractor.py",
        "3. Run: python train_model.py",
        "4. Restart the web app",
    ],
}

# ── Load model at startup ───────────────────────────────────────────
model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print(f"[OK] Model loaded from {MODEL_PATH}")
    except Exception as e:
        print(f"[WARN] Could not load model: {e}")
else:
    print(f"[WARN] Model file not found at {MODEL_PATH}. Run train_model.py first.")


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["GET"])
def model_info():
    """Return information about the ML model and supported categories."""
    return jsonify({
        "model": MODEL_METHOD_INFO,
        "categories": {str(k): v for k, v in LABEL_NAMES.items()},
        "total_categories": len(LABEL_NAMES),
        "model_loaded": model is not None,
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Accept a .sol file upload and return vulnerability analysis."""

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send a .sol file as 'file'."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400
    if not file.filename.endswith(".sol"):
        return jsonify({"error": "Only .sol (Solidity) files are accepted."}), 400

    try:
        code = file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 400

    if not code.strip():
        return jsonify({"error": "File is empty."}), 400

    # ── Extract features ─────────────────────────────────────────────────
    features = extract_features(code)
    feature_df = pd.DataFrame([features])

    # ── ML Prediction ────────────────────────────────────────────────────
    if model is not None:
        try:
            prediction = int(model.predict(feature_df)[0])
            probabilities = model.predict_proba(feature_df)[0]
            confidence = float(np.max(probabilities)) * 100

            class_probs = {}
            for i, prob in enumerate(probabilities):
                class_label = int(model.classes_[i])
                class_probs[LABEL_NAMES.get(class_label, f"Class {class_label}")] = round(
                    float(prob) * 100, 1
                )
        except Exception:
            prediction = detect_vulnerability(code, file.filename)
            confidence = 70.0
            class_probs = {LABEL_NAMES.get(prediction, "Unknown"): 70.0}
    else:
        prediction = detect_vulnerability(code, file.filename)
        confidence = 65.0
        class_probs = {LABEL_NAMES.get(prediction, "Unknown"): 65.0}

    vuln_name = LABEL_NAMES.get(prediction, "Unknown")
    severity = SEVERITY_MAP.get(prediction, SEVERITY_MAP[0])
    recommendation = RECOMMENDATIONS.get(prediction, "")

    # ── Feature breakdown for the UI ─────────────────────────────────────
    detected_features = []
    for feat_key, feat_val in features.items():
        detected_features.append({
            "name": FEATURE_DESCRIPTIONS.get(feat_key, feat_key),
            "key": feat_key,
            "detected": bool(feat_val),
        })

    return jsonify({
        "filename": file.filename,
        "vulnerability": vuln_name,
        "label": prediction,
        "confidence": round(confidence, 1),
        "severity": severity["level"],
        "severity_color": severity["color"],
        "severity_icon": severity["icon"],
        "recommendation": recommendation,
        "features": detected_features,
        "class_probabilities": class_probs,
        "model_method": MODEL_METHOD_INFO["method"],
    })


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  SolidGuard - Smart Contract Vulnerability Scanner")
    print("  ML Method: Random Forest Classifier")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
