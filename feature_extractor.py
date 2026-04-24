"""
Feature Extractor for Solidity Smart Contract Vulnerability Detection.

Extracts 33 features from Solidity source code and labels contracts
into vulnerability classes based on the smart-contracts-set folder structure.

Vulnerability Categories (mapped from smart-contracts-set):
    0 = Safe / No known vulnerability
    1 = Reentrancy
    2 = Denial of Service (DoS)
    3 = Integer Overflow / Underflow
    4 = Access Control (Unprotected Function / Wrong Constructor)
    5 = Unchecked External Call
    6 = Bad Randomness
    7 = Race Condition (Front-Running)
    8 = Honeypot
    9 = Forced Ether Reception
   10 = Incorrect Interface
   11 = Variable Shadowing
"""

import os
import re
import argparse
import pandas as pd


# ── Label constants ──────────────────────────────────────────────────────────
LABEL_SAFE = 0
LABEL_REENTRANCY = 1
LABEL_DOS = 2
LABEL_OVERFLOW = 3
LABEL_ACCESS_CONTROL = 4
LABEL_UNCHECKED_CALL = 5
LABEL_BAD_RANDOMNESS = 6
LABEL_RACE_CONDITION = 7
LABEL_HONEYPOT = 8
LABEL_FORCED_ETHER = 9
LABEL_INCORRECT_INTERFACE = 10
LABEL_VARIABLE_SHADOWING = 11
LABEL_DELEGATECALL = 12
LABEL_STRICT_EQUALITY = 13
LABEL_ETHER_FROZEN = 14

LABEL_NAMES = {
    0: "Safe",
    1: "Reentrancy",
    2: "Denial of Service",
    3: "Integer Overflow/Underflow",
    4: "Access Control",
    5: "Unchecked External Call",
    6: "Bad Randomness",
    7: "Race Condition (Front-Running)",
    8: "Honeypot",
    9: "Forced Ether Reception",
    10: "Incorrect Interface",
    11: "Variable Shadowing",
    12: "Dangerous Delegatecall",
    13: "Ether Strict Equality",
    14: "Ether Frozen",
}

# Map folder names from smart-contracts-set → label
FOLDER_TO_LABEL = {
    "safe": LABEL_SAFE,
    "reentrancy": LABEL_REENTRANCY,
    "denial_of_service": LABEL_DOS,
    "integer_overflow": LABEL_OVERFLOW,
    "unprotected_function": LABEL_ACCESS_CONTROL,
    "wrong_constructor_name": LABEL_ACCESS_CONTROL,
    "unchecked_external_call": LABEL_UNCHECKED_CALL,
    "bad_randomness": LABEL_BAD_RANDOMNESS,
    "race_condition": LABEL_RACE_CONDITION,
    "honeypots": LABEL_HONEYPOT,
    "forced_ether_reception": LABEL_FORCED_ETHER,
    "incorrect_interface": LABEL_INCORRECT_INTERFACE,
    "variable_shadowing": LABEL_VARIABLE_SHADOWING,
}


# ── Feature extraction ──────────────────────────────────────────────────────
def extract_features(code: str) -> dict:
    """
    Return a dict of 28 features extracted from Solidity source code.
    Enhanced features for better vulnerability class separation.
    Original 14 binary features + 14 active enhanced features.
    (5 dead features removed after importance analysis.)
    """

    # === ORIGINAL 14 FEATURES ===
    # 1. External calls: .call(, .transfer(, .send(, call.value(
    has_external_call = int(
        bool(re.search(r"\.(call|transfer|send)\s*\(", code, re.I))
        or bool(re.search(r"call\.value\s*\(", code, re.I))
    )

    # 2. State variable update (assignment with =, but not ==)
    updates_state = int(bool(re.search(r"[a-zA-Z_]\w*\s*=[^=][^;]*;", code)))

    # 3. Payable functions
    is_payable = int(bool(re.search(r"\bpayable\b", code)))

    # 4. Reentrancy guard (nonReentrant, ReentrancyGuard, mutex, locked)
    has_reentrancy_guard = int(
        bool(re.search(r"(nonReentrant|ReentrancyGuard|mutex|locked)", code, re.I))
    )

    # 5. Loops (for / while)
    has_loop = int(bool(re.search(r"\b(for|while)\s*\(", code)))

    # 6. Array operations (.push, .pop, .length)
    has_array_ops = int(bool(re.search(r"\.(push|pop|length)\b", code)))

    # 7. selfdestruct / suicide
    has_selfdestruct = int(bool(re.search(r"\b(selfdestruct|suicide)\s*\(", code)))

    # 8. tx.origin (access-control weakness)
    has_tx_origin = int(bool(re.search(r"\btx\.origin\b", code)))

    # 9. Unchecked low-level call
    has_unchecked_call = 0
    call_matches = list(re.finditer(r"\.call\s*[\.\(]", code))
    for m in call_matches:
        prefix = code[max(0, m.start() - 80) : m.start()]
        if not re.search(r"(require|assert|if\s*\(|bool\s+\w+\s*=)", prefix, re.I):
            has_unchecked_call = 1
            break

    # 10. Overflow risk (arithmetic without SafeMath or unchecked)
    has_overflow_risk = 0
    if re.search(r"(\+\=|\-\=|\*\=|\+\s|\-\s|\*\s)", code):
        if not re.search(r"(SafeMath|using\s+\w+\s+for\s+uint|unchecked\s*\{)", code, re.I):
            has_overflow_risk = 1

    # 11. Block dependency (block.timestamp, block.number, now)
    has_block_dependency = int(
        bool(re.search(r"\b(block\.timestamp|block\.number|now)\b", code))
    )

    # 12. delegatecall
    has_delegatecall = int(bool(re.search(r"\.delegatecall\s*\(", code)))

    # 13. msg.value usage (relevant for forced ether, honeypots)
    has_msg_value = int(bool(re.search(r"\bmsg\.value\b", code)))

    # 14. Fallback function (function() or receive())
    has_fallback = int(
        bool(re.search(r"function\s*\(\s*\)\s*(public\s+)?payable", code))
        or bool(re.search(r"(receive|fallback)\s*\(\s*\)\s*external\s*payable", code))
    )

    # === ENHANCED FEATURES (19 new) ===
    # 15. Strict equality operators (===, !==)
    has_strict_equality = int(bool(re.search(r'===|!==', code)))

    # 16. Comparison operator count
    comparison_count = min(len(re.findall(r'[<>=!]=?', code)), 1)

    # 17. Balance check pattern
    has_balance_check = int(bool(re.search(r'\.balance\s*[<>=!]', code)))

    # 18. Address balance pattern
    has_address_balance = int(bool(re.search(r'address\s*\(.+\)\.balance', code)))

    # 19. call.value pattern
    has_call_value = int(bool(re.search(r'\.call\.value', code)))

    # 20. staticcall usage
    has_static_call = int(bool(re.search(r'\bstaticcall\b', code)))

    # 21. Unbounded loop (loop over array length)
    has_unbounded_loop = int(bool(re.search(r'(for|while).*\.length', code)))

    # 22. Loop count (binary: has multiple loops)
    loop_count = len(re.findall(r'\b(for|while)\s*\(', code))
    has_multiple_loops = 1 if loop_count > 1 else 0

    # 23. Arithmetic operation count
    arithmetic_count = len(re.findall(r'(\+\+|--|\+=|-=|\*=|/)', code))
    has_arithmetic = 1 if arithmetic_count > 0 else 0

    # 24. Unchecked block presence
    has_unchecked_block = int(bool(re.search(r'\bunchecked\s*\{', code)))

    # 25. onlyOwner modifier
    has_onlyOwner = int(bool(re.search(r'onlyOwner', code)))

    # 26. Custom modifier definition
    has_modifier = int(bool(re.search(r'\bmodifier\s+\w+', code)))

    # 27. Event emission
    has_event = int(bool(re.search(r'\bemit\s+', code)))

    # 28. Event count (binary)
    event_count = len(re.findall(r'\bemit\s+', code))
    has_multiple_events = 1 if event_count > 1 else 0

    # 29. Gas limit specification
    has_gas_limit = int(bool(re.search(r'\bgas\s*=', code)))

    # 30. Contract inheritance
    has_inheritance = int(bool(re.search(r'\bis\s+[A-Z]\w*', code)))

    # 31. Interface definition
    has_interface = int(bool(re.search(r'\binterface\s+\w+', code)))

    # 32. Selfdestruct call (explicit)
    has_selfdestruct_call = int(bool(re.search(r'selfdestruct\s*\(', code)))

    # 33. Delegatecall with address target
    has_delegatecall_target = int(bool(re.search(r'\.delegatecall\s*\(\s*address', code)))

    return {
        # Original 14 features
        "has_external_call": has_external_call,
        "is_payable": is_payable,
        "has_reentrancy_guard": has_reentrancy_guard,
        "has_loop": has_loop,
        "has_array_ops": has_array_ops,
        "has_selfdestruct": has_selfdestruct,
        "has_tx_origin": has_tx_origin,
        "has_unchecked_call": has_unchecked_call,
        "has_overflow_risk": has_overflow_risk,
        "has_block_dependency": has_block_dependency,
        "has_delegatecall": has_delegatecall,
        "has_msg_value": has_msg_value,
        "has_fallback": has_fallback,
        # Enhanced features (19 new)
        "has_strict_equality": has_strict_equality,
        "has_balance_check": has_balance_check,
        "has_address_balance": has_address_balance,
        "has_call_value": has_call_value,
        "has_unbounded_loop": has_unbounded_loop,
        "has_multiple_loops": has_multiple_loops,
        "has_arithmetic": has_arithmetic,
        "has_onlyOwner": has_onlyOwner,
        "has_modifier": has_modifier,
        "has_event": has_event,
        "has_multiple_events": has_multiple_events,
        "has_gas_limit": has_gas_limit,
        "has_inheritance": has_inheritance,
        "has_interface": has_interface,
        "has_selfdestruct_call": has_selfdestruct_call,
    }


FEATURE_COLUMNS = list(extract_features("").keys())


# ── Heuristic vulnerability detection (for unknown files) ───────────────────
def detect_vulnerability(code: str, filename: str) -> int:
    """
    Classify a Solidity contract using code-pattern heuristics.
    Used for files NOT in the smart-contracts-set (i.e., user uploads).
    """
    name = filename.lower()

    # DoS (check first - loops + transfers are a strong signal)
    if re.search(
        r"(for|while)\s*\([^)]*\)\s*\{[^}]*\.(call|transfer|send)\s*\(",
        code, re.I | re.S,
    ):
        return LABEL_DOS
    if re.search(r"(for|while)\s*\([^)]*\.length", code):
        return LABEL_DOS

    # Dangerous Delegatecall (very specific signal, check early)
    if re.search(r"\.delegatecall\s*\(", code):
        return LABEL_DELEGATECALL

    # Reentrancy
    # Matches both old .call()(value) AND new Solidity 0.6+ .call{value:x}() syntax
    ext_call = re.search(r"\.(call|send|transfer)\s*[.({]", code, re.I)
    if ext_call:
        after = code[ext_call.end() : ext_call.end() + 400]
        if re.search(r"[a-zA-Z_][\w\[\].]*\s*=[^=][^;]*;", after):
            if not re.search(r"(nonReentrant|ReentrancyGuard|mutex|locked)", code, re.I):
                return LABEL_REENTRANCY

    # Unchecked external call (check before overflow to avoid masking)
    # Also matches new .call{value:}() syntax
    call_matches = list(re.finditer(r"\.call\s*[.({[]", code))
    for m in call_matches:
        prefix = code[max(0, m.start() - 80) : m.start()]
        if not re.search(r"(require|assert|if\s*\(|bool\s+\w+[\s,=]|!\s*\(|\(\s*bool)", prefix, re.I):
            return LABEL_UNCHECKED_CALL

    # Integer Overflow (checked AFTER external call checks to prevent false positives)
    if re.search(r"(\+\=|\-\=|\*\=)", code):
        if not re.search(r"(SafeMath|unchecked\s*\{)", code, re.I):
            if re.search(r"\buint\b", code):
                return LABEL_OVERFLOW

    # Bad randomness
    if re.search(r"\b(block\.timestamp|block\.number|blockhash|now)\b", code):
        if re.search(r"(random|winner|lottery|prize|bet)", code, re.I):
            return LABEL_BAD_RANDOMNESS

    # Access Control
    if re.search(r"function\s+\w*[oO]wner\w*\s*\([^)]*\)\s*public\b", code):
        return LABEL_ACCESS_CONTROL

    # Ether Strict Equality (tightened: only flag balance == or != comparisons)
    if re.search(r"\.balance\s*(==|!=)\s*", code):
        return LABEL_STRICT_EQUALITY

    # Ether Frozen (tightened: must actively USE address(this).balance, not just msg.value)
    if re.search(r"\bpayable\b", code):
        has_withdrawal = re.search(
            r"\b(withdraw|transfer|send|transferTo|sendTo|claimFunds|refund)\b",
            code, re.I
        )
        if not has_withdrawal:
            if re.search(r"address\s*\(\s*this\s*\)\.balance|this\.balance", code):
                return LABEL_ETHER_FROZEN

    # Variable shadowing
    if re.search(r"\bshadow", name):
        return LABEL_VARIABLE_SHADOWING

    return LABEL_SAFE


# ── Walk smart-contracts-set to build labeled dataset ───────────────────────
def walk_dataset(dataset_dir: str) -> list:
    """
    Recursively walk the smart-contracts-set directory.
    Labels are determined by the TOP-LEVEL folder name under dataset_dir.
    Returns a list of dicts ready for DataFrame.
    """
    rows = []

    for top_folder in sorted(os.listdir(dataset_dir)):
        top_path = os.path.join(dataset_dir, top_folder)
        if not os.path.isdir(top_path):
            continue

        label = FOLDER_TO_LABEL.get(top_folder, LABEL_SAFE)
        category_name = LABEL_NAMES.get(label, "Unknown")

        # Walk recursively to find all .sol files under this category
        for root, _dirs, files in os.walk(top_path):
            for fname in sorted(files):
                if not fname.endswith(".sol"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        code = fh.read()
                except Exception as e:
                    print(f"  ⚠ Skipping {fpath}: {e}")
                    continue

                features = extract_features(code)
                rows.append({
                    "file": fname,
                    "category": top_folder,
                    **features,
                    "label": label,
                })
                print(f"  {fname:40s} [{top_folder}] -> {category_name}")

    return rows


# ── CLI entry point ─────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract features from Solidity files for vulnerability detection."
    )
    parser.add_argument(
        "--dataset",
        default="smart-contracts-set",
        help="Path to labeled dataset folder (smart-contracts-set)",
    )
    parser.add_argument(
        "--extra-folder",
        default=None,
        help="Optional: additional folder of .sol files (labeled by heuristic)",
    )
    parser.add_argument("--output", default="data/features.csv", help="Output CSV path")
    args = parser.parse_args()

    rows = []

    # 1. Walk the labeled dataset
    if os.path.isdir(args.dataset):
        print(f"[INFO] Reading labeled dataset from: {args.dataset}")
        rows.extend(walk_dataset(args.dataset))
    else:
        print(f"[WARN] Dataset folder not found: {args.dataset}")

    # 2. Optionally add extra unlabeled .sol files (heuristic labeling)
    if args.extra_folder and os.path.isdir(args.extra_folder):
        print(f"\n[INFO] Reading extra .sol files from: {args.extra_folder}")
        for fname in sorted(os.listdir(args.extra_folder)):
            if not fname.endswith(".sol"):
                continue
            fpath = os.path.join(args.extra_folder, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    code = fh.read()
            except Exception:
                continue
            features = extract_features(code)
            label = detect_vulnerability(code, fname)
            rows.append({
                "file": fname,
                "category": "extra",
                **features,
                "label": label,
            })
            print(f"  {fname:40s} [heuristic] -> {LABEL_NAMES[label]}")

    if not rows:
        print("[ERROR] No .sol files found.")
        return

    df = pd.DataFrame(rows)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    try:
        df.to_csv(args.output, index=False)
        print(f"\n[OK] Features for {len(df)} contracts saved to {args.output}")
    except PermissionError:
        print(f"\n[ERROR] Cannot write to {args.output} -- close the file and retry.")
        return

    # Print label distribution
    print("\n-- Label Distribution --")
    for label_val in sorted(df["label"].unique()):
        count = (df["label"] == label_val).sum()
        print(f"  {LABEL_NAMES.get(label_val, '?'):35s} : {count}")


if __name__ == "__main__":
    main()
