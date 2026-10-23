# SolidGuard - Accuracy Analysis Report

## Executive Summary

**Current Model Accuracy:**
- **4-label dataset**: 85.93% CV Accuracy (BEST)
- **8-label dataset**: 51.41% CV Accuracy
- **Combined dataset**: 51.57% CV Accuracy

---

## Key Findings

### 1. 4-Label Dataset Performance (RECOMMENDED)

| Metric | Value |
|--------|-------|
| Samples | 2,217 |
| Classes | 4 |
| CV Accuracy | **85.93%** |
| Train Accuracy | 89.58% |

**Per-Class Performance:**
| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Reentrancy | 0.97 | 0.90 | 0.93 | 1,218 |
| Integer Overflow | 0.89 | 0.85 | 0.87 | 590 |
| Bad Randomness | 0.74 | 0.98 | 0.84 | 312 |
| Dangerous Delegatecall | 0.74 | 0.90 | 0.81 | 97 |

**Verdict:** This model is **production-ready** for these 4 vulnerability types.

---

### 2. 8-Label Dataset Problems

| Metric | Value |
|--------|-------|
| Samples | 4,285 |
| Classes | 7 |
| CV Accuracy | 51.41% |
| Train Accuracy | 58.90% |

**Per-Class Performance:**
| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Reentrancy | 0.63 | **0.16** | 0.25 | 1,218 |
| Integer Overflow | 0.80 | 0.81 | 0.81 | 590 |
| Unchecked External Call | 0.51 | 0.76 | 0.61 | 1,199 |
| Bad Randomness | 0.73 | 0.87 | 0.79 | 718 |
| Dangerous Delegatecall | 0.40 | 0.49 | 0.44 | 97 |
| Ether Strict Equality | 0.45 | 0.61 | 0.52 | 366 |
| Ether Frozen | 0.40 | 0.39 | 0.40 | 97 |

**Major Issues Identified:**

1. **Reentrancy Recall Collapse (0.16)**: Model misses 84% of reentrancy vulnerabilities!
2. **New classes have weak features**: "Ether Frozen" and "Ether Strict Equality" don't have unique feature patterns
3. **Feature overlap**: Multiple classes share similar feature signatures

---

### 3. Combined Dataset Analysis

Combining datasets **does NOT help**:
- CV Accuracy drops from 85.93% → 51.57%
- More samples (6,502) but worse performance
- Same 7 classes, but model gets more confused

**Why combining hurts:**
1. **Duplicate samples**: Same contracts in both datasets
2. **Feature insufficiency**: 14 binary features can't distinguish 7 classes
3. **Class imbalance worsens**: Ether Frozen (97) vs Reentrancy (2,436)

---

## Root Cause Analysis

### Why 8-Label Dataset Fails

The 14 features are **not discriminative enough** for 7 classes:

| Feature | Importance (4-label) | Importance (8-label) |
|---------|---------------------|---------------------|
| has_block_dependency | 0.21 | 0.14 |
| has_external_call | 0.18 | 0.18 |
| has_overflow_risk | 0.13 | 0.14 |
| has_delegatecall | 0.11 | 0.10 |

**Problem**: Classes like "Ether Frozen", "Ether Strict Equality", and "Unchecked External Call" share overlapping feature patterns. The model can't tell them apart with only binary features.

### Feature Limitations

Current features are **too simple**:
- Binary (0/1) - loses nuance
- Surface-level pattern matching
- No semantic understanding
- No control flow analysis
- No data flow analysis

---

## Recommendations

### ✅ IMMEDIATE ACTIONS

1. **Use 4-label model for production** (85.93% CV accuracy)
   - Deploy `models/model.pkl`
   - Detects: Reentrancy, Integer Overflow, Bad Randomness, Dangerous Delegatecall

2. **Do NOT combine datasets** - it makes accuracy worse

3. **Improve feature extraction** for new vulnerability types

---

### 🔧 HOW TO IMPROVE ACCURACY (Long-term)

#### 1. Add More Discriminative Features

```python
# New features to add:
- comparison_operator_count  # For "Ether Strict Equality"
- balance_usage_pattern      # For "Ether Frozen"
- loop_depth                 # For DoS detection
- external_call_chain_depth  # For reentrancy severity
- modifier_list              # For access control analysis
- event_emission             # Missing events = smell
- gas_limit_usage            # Gas-related vulnerabilities
```

#### 2. Use AST-Based Analysis (Not Regex)

```python
# Instead of regex patterns, use Solidity AST:
from solc import compile_standard

ast = compile_standard(code)['sources']['<stdin>']['AST']
# Proper parsing catches:
# - Actual data flow
# - State change ordering
# - Call context
```

#### 3. Add Code Embeddings

```python
# Use CodeBERT or similar for semantic understanding
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
embeddings = tokenizer(code, return_tensors="pt")
# 768-dimensional features capture semantics
```

#### 4. Better Model Architecture

```python
# Try these instead of Random Forest:
- XGBoost / LightGBM (gradient boosting)
- Neural Network with embeddings
- Graph Neural Network (for control flow)
```

#### 5. Data Augmentation

```python
# For underrepresented classes:
- Rename variables (same logic, different names)
- Add comments
- Reorder functions
- Equivalent code transformations
```

---

## Dataset Recommendation

### Should you combine datasets?

**NO!** Here's why:

| Aspect | 4-label Only | Combined |
|--------|-------------|----------|
| CV Accuracy | 85.93% | 51.57% |
| Classes | 4 (focused) | 7 (confused) |
| Production Ready | ✅ Yes | ❌ No |

**Better approach:**
1. Use 4-label model now (85.93% accuracy)
2. Improve features for new vulnerability types
3. Add more samples for weak classes (Ether Frozen, Delegatecall)
4. Train new model when features are better

---

## Action Plan

### Week 1: Stabilize
- [ ] Keep using 4-label model
- [ ] Document current limitations

### Week 2-3: Feature Engineering
- [ ] Add 5-10 new discriminative features
- [ ] Implement AST-based parsing
- [ ] Test feature importance

### Week 4: Model Upgrade
- [ ] Try XGBoost
- [ ] Add CodeBERT embeddings
- [ ] Compare with Random Forest baseline

### Month 2: Expand Classes
- [ ] Collect more samples for rare classes
- [ ] Create synthetic samples
- [ ] Retrain with 7 classes

---

## Conclusion

**Current accuracy: 85.93% (4-label model) is GOOD for production.**

**Limitations:**
- Only detects 4 vulnerability types
- Binary features miss semantic patterns
- Can't distinguish similar vulnerability classes

**To improve:**
1. Better features (AST-based, not regex)
2. Code embeddings (CodeBERT)
3. More training data for rare classes
4. Advanced models (XGBoost, GNN)

**Do NOT combine datasets** - quality over quantity!
