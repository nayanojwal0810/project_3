# Phase 1B — CSIRO HVAC Model-Signal Validation Report

**Experiment Date:** October 2026  
**Auditor / Engineer:** Antigravity Agentic Pair Programmer  
**Dataset:** CSIRO AHU Fault-Detection Dataset (`AHU9.parquet`, `AHU10.parquet`, `fault-experiments.parquet`)  
**Script:** [`scripts/run_signal_check.py`](file:///d:/project-3/scripts/run_signal_check.py)  
**Execution Environment:** Local CPU (Windows, Intel/AMD multi-core), Python 3.13.3, PyTorch 2.13.0+cpu, scikit-learn 1.9.0, Pandas 3.0.3  
**Random Seed:** `42` (Fixed across NumPy, PyTorch CPU, Python `random`, and scikit-learn)

---

## Executive Summary & Strict Pass/Fail Gate

This controlled experiment evaluated whether sensor telemetry from the CSIRO HVAC fault-detection benchmark provides sufficient temporal and cross-unit predictive signal to justify a deep-learning project. We executed an exact, non-leaking temporal split comparing a lightweight scikit-learn baseline (Logistic Regression with summary statistics) against a small 1D Convolutional Neural Network (PyTorch 1D CNN) on non-overlapping 10-minute sensor windows.

### Three-Part Evaluation Decision

| Gate Dimension | Decision | Evidence & Justification |
|---|---|---|
| **1. Data / Evaluation Validity** | **PASS** | Strict calendar partitioning strictly preserved time blocks and fault event boundaries. 1-day temporal buffers separated Train/Val and Val/Test. Feature scaling was fitted solely on training telemetry. Zero window or row leakage. Primary test partition contained 139 independent fault events across both AHUs (exceeding the $\ge 20$ event requirement). |
| **2. Predictive Signal** | **FAIL (Marginal / Non-generalizing)** | On held-out Primary Test (Oct–Nov 2013), the simple baseline achieved a PR-AUC of **0.1365** against a positive-class prevalence of **0.1321** (barely +0.0044 above random chance). Balanced accuracy was **0.5015** (essentially a coin flip). Event-level recall was **20.14%** overall, collapsing to **4.17%** on AHU 10 where no prior fault data existed in training. |
| **3. Deep-Learning Justification** | **FAIL** | The 1D CNN failed to outperform the lightweight baseline on the Primary Test. CNN PR-AUC was **0.1215** (worse than baseline 0.1365 and below random prevalence 0.1321). Test F1 was **0.1315** vs baseline **0.1394**. CNN balanced accuracy was **0.4867** (worse than random guessing). Event-level recall was **18.71%** vs baseline **20.14%**. |

> **Required Statement:**  
> **"Predictive signal may exist, but the deep-learning advantage is not demonstrated."**

---

## 1. Preflight Verification & Data Audit Reconciliation

Before preprocessing or training, all required environment components and dataset files were verified:

- `data/raw/csiro/AHU9.parquet`: **9,786,479 bytes** (verified present).
- `data/raw/csiro/AHU10.parquet`: **7,884,660 bytes** (verified present).
- `data/raw/csiro/fault-experiments.parquet`: **28,276 bytes** (verified present).
- Dependencies: Python `3.13.3`, Pandas `3.0.3`, PyArrow `24.0.0`, scikit-learn `1.9.0`, PyTorch `2.13.0+cpu`.
- Git status: `data/raw/` is properly ignored in `.gitignore`. No raw data files are staged or tracked.

### Preprocessing & Feature Engineering Decisions

1. **Prefix Normalization:** Stripped equipment-specific column prefixes (`AHU9` and `AHU10`), producing consistent unified feature names across both air handling units.
2. **Duplicate Channel Removal (`ahuMaTemp`):**  
   - *Decision:* Removed `ahuMaTemp` and retained `ahuSaTemp`.
   - *Justification & Limitation:* As proven during Phase 1A.1 audit reconciliation, `ahuMaTemp` and `ahuSaTemp` are bit-for-bit identical ($100\%$ identical rows across both AHU 9 and AHU 10). Dropping the redundant duplicate removes rank-deficient collinearity. The limitation is that mixed air temperature telemetry was either miswired to supply air temperature or mapped to the identical register in the building management system.
3. **Excluded Metadata:** All timestamps, experiment IDs, fault descriptions, fault severity labels, and AHU IDs were excluded from input feature tensors.
4. **Window Construction:**
   - 10-minute non-overlapping windows (`dt.floor('10min')`).
   - Retained only windows containing **exactly 20 observations at 30-second intervals** (a continuous span of 570 seconds without data gaps).
   - Enforced **pure label consistency**: a window is retained if and only if all 20 observations share the exact same binary label ($y=1$ for timestamps inside any documented half-open fault injection $[start, end)$; $y=0$ for timestamps outside all documented injections).
   - Excluded all windows crossing fault injection boundaries and any window with missing or irregular sampling. No interpolation was performed across gaps.

### Row & Window Accounting

| Metric | AHU 9 | AHU 10 | Total |
|---|---|---|---|
| **Raw Telemetry Rows** | 457,653 | 422,169 | 879,822 |
| **Incomplete / Gapped 10-min Bins Excluded** | 3,502 | 3,485 | 6,987 |
| **Boundary-Crossing Mixed Windows Excluded** | 215 | 106 | 321 |
| **Usable Pure 10-min Windows Retained** | **22,309** | **20,645** | **42,954** |
| Retained Window Observations ($20 \times 30\text{s}$) | 446,180 (97.5%) | 412,900 (97.8%) | 859,080 (97.6%) |

---

## 2. Temporal Partitioning & Leakage Prevention

Data was partitioned along fixed calendar boundaries with 1-day exclusion buffers to prevent temporal leakage between adjacent periods:

| Partition | Calendar Period | Buffer Applied | Usable Windows | Positive Windows | Prevalence | Unique Fault Experiments |
|---|---|---|---|---|---|---|
| **Training** | May 1, 2013 – Aug 30, 2013 | N/A | 10,098 | 942 | 9.33% | 52 |
| *Buffer 1* | Aug 31, 2013 | Excluded | 96 | 0 | 0.00% | 0 |
| **Validation** | Sep 1, 2013 – Sep 29, 2013 | N/A | 2,729 | 311 | 11.40% | 35 |
| *Buffer 2* | Sep 30, 2013 | Excluded | 96 | 0 | 0.00% | 0 |
| **Primary Test** | Oct 1, 2013 – Nov 30, 2013 | N/A | 4,922 | 650 | 13.21% | 139 |
| **Background Stress Test** | Dec 1, 2013 – May 27, 2015 | Post-experiment period | 25,013 | 0 | 0.00% | 0 |

### Evaluation Preflight Check
- **Primary Test Requirement:** Must contain both classes and $\ge 20$ independent fault events.
- **Actual Primary Test:** Contains 650 positive windows, 4,272 negative windows, and **139 unique independent fault experiments**. (Requirement satisfied).
- **Leakage Prevention:**
  - `StandardScaler` was fitted strictly on the $201,960$ observation rows of the `train` partition ($10,098 \times 20$). Validation, test, and background windows were transformed using the frozen training parameters.
  - No random splitting or cross-window shuffling was performed.

---

## 3. Model Architectures & Training Protocol

Both models were evaluated on the exact same scaled window representations:

### 1. Simple Baseline (Scikit-Learn Logistic Regression)
- **Features:** 32 summary statistics per 10-minute window (mean and standard deviation across the 20 timesteps for each of the 16 normalized sensor channels).
- **Configuration:** `LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)`.
- **Classification Threshold:** Tuned on Validation set by maximizing F1 score $\rightarrow$ Optimal threshold = **0.84**.
- **CPU Training Runtime:** **0.11 seconds**.

### 2. Deep-Learning Model (PyTorch 1D CNN)
- **Architecture:**
  - Input: $(B, 16, 20)$ (16 sensor channels, 20 timesteps).
  - Block 1: `Conv1d(16, 32, kernel_size=3, padding=1)` $\rightarrow$ `BatchNorm1d(32)` $\rightarrow$ `ReLU` $\rightarrow$ `MaxPool1d(2)` (timesteps: $20 \rightarrow 10$).
  - Block 2: `Conv1d(32, 64, kernel_size=3, padding=1)` $\rightarrow$ `BatchNorm1d(64)` $\rightarrow$ `ReLU` $\rightarrow$ `AdaptiveAvgPool1d(1)` (timesteps: $10 \rightarrow 1$).
  - Head: `Linear(64, 32)` $\rightarrow$ `ReLU` $\rightarrow$ `Dropout(0.2)` $\rightarrow$ `Linear(32, 1)`.
- **Optimization:** Adam ($\text{lr}=10^{-3}$, weight decay $=10^{-4}$), `BCEWithLogitsLoss` with positive class weighting ($pos\_weight \approx 9.72$).
- **Epochs:** 12 epochs on CPU. Validation PR-AUC tracked each epoch for early model checkpointing.
- **Classification Threshold:** Tuned on Validation set by maximizing F1 score $\rightarrow$ Optimal threshold = **0.59**.
- **CPU Training Runtime:** **12.74 seconds**.

---

## 4. Empirical Evaluation Results

### Validation Partition (September 2013)
*Prevalence: 11.40% (311 pos / 2,418 neg; 35 fault events)*

| Metric | Dummy Classifier | Simple Baseline (LogReg) | Small 1D CNN |
|---|---|---|---|
| **Threshold** | Most Frequent ($y=0$) | 0.84 | 0.59 |
| **PR-AUC (Average Precision)** | 0.1140 | 0.2237 | **0.2445** |
| **Precision** | 0.0000 | 0.2211 | **0.2677** |
| **Recall** | 0.0000 | 0.3376 | **0.4244** |
| **F1 Score** | 0.0000 | 0.2672 | **0.3284** |
| **Balanced Accuracy** | 0.5000 | 0.5923 | **0.6376** |
| **Event-Level Recall** | 0.0% (0/35) | 45.71% (16/35) | **57.14% (20/35)** |
| **Confusion Matrix [TN, FP; FN, TP]** | [2418, 0; 311, 0] | [2048, 370; 206, 105] | [2057, 361; 179, 132] |

*Observation on Validation:* In September 2013 (immediately following the training window), the 1D CNN showed higher metrics across F1 (+0.061) and event recall (+11.4%). However, temporal generalization to subsequent months tells a completely different story.

---

### Primary Test Partition (October–November 2013)
*Prevalence: 13.21% (650 pos / 4,272 neg; 139 fault events)*

| Metric | Dummy Classifier | Simple Baseline (LogReg) | Small 1D CNN | CNN vs Baseline |
|---|---|---|---|---|
| **Classification Threshold** | Most Frequent ($y=0$) | 0.84 (frozen from val) | 0.59 (frozen from val) | — |
| **PR-AUC (Average Precision)** | 0.1321 | **0.1365** | 0.1215 | **-0.0150 (Worse)** |
| **Precision** | 0.0000 | **0.1345** | 0.1148 | -0.0197 (Worse) |
| **Recall** | 0.0000 | 0.1446 | **0.1538** | +0.0092 |
| **F1 Score** | 0.0000 | **0.1394** | 0.1315 | **-0.0079 (Worse)** |
| **Balanced Accuracy** | 0.5000 | **0.5015** | 0.4867 | **-0.0148 (Worse)** |
| **Event-Level Recall** | 0.0% (0/139) | **20.14% (28/139)** | 18.71% (26/139) | **-1.43% (Worse)** |
| **Confusion Matrix [TN, FP; FN, TP]** | [4272, 0; 650, 0] | [3667, 605; 556, 94] | [3501, 771; 550, 100] | +166 False Positives |

---

### Primary Test Breakdown by Equipment Unit (AHU 9 vs AHU 10)

| Metric | AHU 9 (In Train: 52 Faults) | AHU 10 (In Train: 0 Faults) |
|---|---|---|
| **Positive Prevalence** | 11.13% (314 pos / 2,507 neg) | 15.99% (336 pos / 1,765 neg) |
| **Unique Fault Events** | 67 events | 72 events |
| **Baseline PR-AUC** | **0.1289** (chance = 0.1113) | **0.1567** (chance = 0.1599) |
| **1D CNN PR-AUC** | 0.1101 (worse than chance) | 0.1633 |
| **Baseline F1** | **0.1946** | 0.0308 |
| **1D CNN F1** | 0.1576 | **0.0624** |
| **Baseline Balanced Accuracy** | **0.5402** | 0.4787 |
| **1D CNN Balanced Accuracy** | 0.4983 | **0.5001** |
| **Baseline Event Recall** | **37.31% (25 / 67 events)** | 4.17% (3 / 72 events) |
| **1D CNN Event Recall** | 29.85% (20 / 67 events) | **8.33% (6 / 72 events)** |
| **Baseline Confusion Matrix** | [2014, 493; 227, 87] | [1653, 112; 329, 7] |
| **1D CNN Confusion Matrix** | [1804, 703; 227, 87] | [1697, 68; 323, 13] |

#### Key Insights from Unit Breakdown:
1. **AHU 9 (Same unit as training):**
   - The simple baseline distinctly outperformed the 1D CNN (Baseline F1 = 0.1946 vs CNN F1 = 0.1576; Baseline Event Recall = 37.31% vs CNN = 29.85%).
   - The CNN suffered from severe false alarm inflation (+210 additional false positive windows compared to baseline).
2. **AHU 10 (Zero training fault instances):**
   - In May–August 2013, zero fault experiments were run on AHU 10.
   - When evaluating on October–November 2013, both models suffered severe transfer failure: baseline detected only 3 of 72 events (4.17%), while the CNN detected only 6 of 72 events (8.33%).
   - Neither model generalized across units without unit-specific training data.

---

### Background Stress Test Period (December 2013 – May 2015)
*25,013 windows across 18 months; 0 recorded injected faults.*

The background stress test evaluates false alarm stability across changing seasons without any ground-truth fault injection:

| Metric | Simple Baseline (LogReg) | Small 1D CNN |
|---|---|---|
| **Total Background Windows** | 25,013 | 25,013 |
| **False Positive Windows** | 7,735 | **2,084** |
| **False Positive Rate (FPR)** | **30.92%** | **8.33%** |
| **True Negatives** | 17,278 | 22,929 |

*Interpretation:* The CNN achieved a substantially lower false positive rate during the background period (8.33% vs 30.92% for baseline). However, given that the CNN's test-set balanced accuracy was below random chance (0.4867), this reduced FPR is largely a symptom of conservative bias, not superior discriminative power.

---

## 5. Runtime & Efficiency Comparison

| Dimension | Simple Baseline | Small 1D CNN | Ratio |
|---|---|---|---|
| **Training Time (CPU)** | **0.11 s** | 12.74 s | $115\times$ slower |
| **Inference Time (Full Test + Background)** | ~0.08 s | ~25.2 s | $315\times$ slower |
| **Parameter Count** | 33 weights | 22,753 weights | $689\times$ larger |
| **Total Pipeline Time** | — | — | 113.67 s |

---

## 6. Detailed Analysis & Engineering Diagnosis

### Why Did the 1D CNN Fail to Provide an Advantage?

1. **Seasonal Drift and Changing Weather Regimes:**  
   The training set spans Australian late autumn and winter (May–August 2013), while the primary test set spans spring/early summer (October–November 2013). HVAC thermal operating regimes shift dramatically between winter heating mode and summer cooling mode. Fixed temporal models without explicit weather conditioning or outdoor air reset models cannot disentangle normal seasonal variation from injected faults.
2. **Short Window Temporal Dynamics Lack Waveform Signals:**  
   In 10-minute windows (20 samples at 30-second intervals), slow thermal processes (room temperature, chilled water loops) barely exhibit intra-window curvature or high-frequency spectral dynamics. Summary statistics (mean and standard deviation) capture virtually all the usable variance available at a 10-minute scale. The convolutional filters learned spurious high-frequency noise that failed to generalize.
3. **Severe Cross-Unit Transfer Barrier:**  
   HVAC air handling units exhibit distinct duct static pressures, damper characteristics, and physical zone loads. Because AHU 10 had zero fault injections during May–August 2013, evaluating on AHU 10 in October–November tested zero-shot cross-unit transfer. Both models failed completely (detecting $<8.5\%$ of events).
4. **Weak Overall Signal-to-Noise Ratio:**  
   Even on AHU 9 where training data existed, the test PR-AUC was merely 0.1289 vs random prevalence of 0.1113. This indicates that the raw sensor channels alone under a binary label do not provide a strong, separable fault signature without explicit thermodynamic domain engineering (e.g., energy balance residuals, temperature split differentials, control loop tracking error).

---

## 7. Final Recommendation & Next Steps

1. **Do Not Proceed Directly to Deep-Learning Model Application:**  
   The empirical evidence decisively rejects the hypothesis that a deep learning model provides an out-of-the-box advantage over simple linear/statistical methods on this dataset. 
2. **Project Feasibility Verdict:**  
   A project centered on "raw sensor telemetry $\rightarrow$ black-box 1D CNN / Deep Learning FDD" on the CSIRO dataset is **not viable** in its current framing.
3. **Alternative Pivot Options (For Future Consideration):**  
   If the team desires to continue working with the CSIRO dataset, the problem formulation must change:
   - **Thermodynamic Residual Feature Engineering:** Instead of feeding raw temperatures and valve commands to a CNN, compute physical residual features (e.g., predicted cooling coil discharge temperature minus actual supply air temperature, fan curve tracking errors).
   - **Equipment-Normalized or Supervised Multi-Unit Framing:** Models must be trained with data from both units across multiple seasons, rather than expecting single-unit winter-to-summer zero-shot generalization.
   - **Multiclass Fault Signature Matching:** Focusing on specific high-signal fault types (e.g., stuck dampers or simultaneous heating/cooling) rather than an undifferentiated binary injection flag.
