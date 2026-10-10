# Feasibility Assessment: HVAC Fault Detection & GenAI Diagnostics

**Audit Date:** 2026-10-10  
**Phase:** Phase 0 Feasibility Audit (No Training, No LLM Implementation)  
**Author:** Automated Data-Audit Engine  

---

## 1. Observed Facts

### 1.1 Equipment Coverage and Label Reality
1. **Diverse Systems:** The benchmark encompasses four distinct HVAC system configurations:
   - Rooftop Unit with 10 VAV terminal zones (`RTU.csv`)
   - Single-Zone Constant Air Volume AHU (`SZCAV.csv`)
   - Single-Zone Variable Air Volume AHU (`SZVAV.csv`)
   - Multi-Zone Variable Air Volume AHU (`MZVAV-1.csv`, `MZVAV-2-1.csv`, `MZVAV-2-2.csv`)
2. **Binary Ground Truth Only:** Tabular files provide solely a binary `Fault Detection Ground Truth` indicator (0 = normal, 1 = faulted). There is **no multiclass fault type or fault severity label column** anywhere in the CSV files.
3. **Severe Imbalance in Experimental Sets:**
   - `RTU.csv`: 30,240 rows (100% faulted in CSV, 0% normal).
   - `SZCAV.csv`: 20,160 rows faulted (93.3%) vs 1,440 rows normal (6.7%, single calendar day).
   - `MZVAV-2-1.csv`: 18,720 rows normal (86.7%) vs 2,880 rows faulted (13.3%, only 2 calendar days).
4. **Balanced or Substantial Sets:**
   - `MZVAV-2-2.csv` (Simulated): Exactly 18,720 normal rows (50%) and 18,720 faulted rows (50%) across 26 experimental days.
   - `SZVAV.csv` (Experimental): 5,759 normal rows (36.4%) and 10,080 faulted rows (63.6%) across 11 experimental days.
   - `MZVAV-1.csv` (Simulated): 38,880 normal rows (14.3%) and 233,280 faulted rows (85.7%) across 189 experimental days.
5. **Technical Documentation Presence:**
   - The archive includes `LBNLDataSynthesisInventory.pdf` (25 pages), which specifies equipment schematics, control sequences, points lists, and explicit date-to-fault schedules (Tables 1-2, 2-2, 3-3, 3-4, and 4-3).

---

## 2. Model Feasibility Assessment

### 2.1 Supervised Fault-Detection Task Viability
- **Binary Fault Detection:**
  - **Viable with Preprocessing:** The data supports a defensible binary fault-detection task (normal vs. faulted), provided datasets are treated separately by equipment type.
  - **Hard Dependency on Relabeling `RTU.csv`:** Binary classification on `RTU.csv` is completely impossible without re-assigning the 7 documented unfaulted days to label `0`.
- **Multiclass Fault Diagnosis Task:**
  - **Conditional Viability:** The benchmark does *not* natively provide multiclass labels. To perform fault diagnosis (e.g., distinguishing Damper Stuck vs. Valve Leaking vs. Sensor Bias), an automated ingestion pipeline must extract the date ranges from the PDF and join them with the timestamp column of each CSV.
  - **Limited Physical Replicates:** In `SZCAV.csv` and `SZVAV.csv`, each specific fault type occurs on only 1 or 2 calendar days. A multiclass model would train on 1 day of a fault and test on zero unseen days of that fault, risking memorization of specific weather conditions rather than learning true fault dynamics.

### 2.2 Data Leakage and Validation Split Strategy
- **Failure Mode of Random Shuffling:**
  - Standard random row splitting (`train_test_split`) on 1-minute time series data guarantees severe data leakage. Contiguous minutes share thermal mass, outdoor air temperature, and fan speeds.
  - A randomly sampled test row will almost always be flanked by training rows from the same hour, causing naive classifiers to achieve near-100% accuracy while failing completely in production.
- **Recommended Split Strategy:**
  - **Grouped by Calendar Day / Experiment Scenario:** Use `GroupKFold` or block time-series splits grouped on `date`.
  - **Condition Invariance:** Ensure both training and test sets contain diverse outdoor air temperatures and both occupied/unoccupied modes so the model does not treat "nighttime setback" as a "fault".

### 2.3 Required Baselines for Any Deep-Learning Project
Prior to introducing complex deep-learning architectures (e.g., 1D-CNN, LSTM, Transformer/PatchTST), a rigorous engineering evaluation must establish:
1. **Rule-Based HVAC Baselines:**
   - APAR (Air Handling Unit Performance Assessment Rules, Schein et al., NIST) based on temperature and control signal balance (e.g., cooling coil valve open while supply air temperature exceeds setpoint).
2. **Tabular Machine Learning Baselines:**
   - Logistic Regression with L2 regularization on physical differential features (e.g., $\Delta T = T_{\text{supply}} - T_{\text{setpoint}}$).
   - XGBoost / LightGBM / Random Forest with daily grouped cross-validation.
3. **Evaluation Metrics:**
   - Accuracy is misleading due to class imbalance. Baselines must report Macro-F1, Precision-Recall AUC (PR-AUC), and per-class recall.

---

## 3. GenAI Feasibility Assessment

### 3.1 Grounding Requirements for Evidence-Backed Troubleshooting
- GenAI cannot generate defensible, hallucination-free troubleshooting reports solely from raw sensor numbers.
- To produce evidence-backed reports that withstand technical review, the project requires an external engineering corpus:
  1. **ASHRAE Guideline 36-2018:** *High-Performance Sequences of Operation for HVAC Systems*.
  2. **ASHRAE 1312-RP:** *Tools for Evaluating Fault Detection and Diagnostic Methods for Air Handling Units*.
  3. **PNNL Building Re-Tuning Guides:** Official diagnostics workflows for AHUs and RTUs.
  4. **Manufacturer O&M Manuals:** Specifically Trane RTU Series (YCD150) manuals.

### 3.2 Label-to-Reference Grounding Mechanism
- **PDF Metadata Mapping:** `LBNLDataSynthesisInventory.pdf` establishes ground-truth causal links (e.g., "OA Damper Stuck at 50% on 3/19/17 via automated override").
- **Evidence Extraction Flow:**
  - Detection model flags an anomalous time block.
  - Telemetry statistics (e.g., "Mixed Air Temperature equals Outdoor Air Temperature despite 0% damper command") provide the quantitative symptom evidence.
  - GenAI pipeline references the specific section of ASHRAE Guideline 36 or the LBNL inventory to explain *why* the symptom indicates an economizer damper failure.

---

## 4. Unknowns and Project Risks
1. **Label Discrepancies:** Unclear why `RTU.csv` unfaulted days were tagged as `1` and `MZVAV-2-1.csv` day `2007-08-30` was tagged as `0`.
2. **Missing Sensor Channels:** In `RTU.csv`, 10 terminal air temperature channels are 33.3% missing.
3. **Generalization across Facilities:** Models trained on synthetic data (`MZVAV-1`) may experience significant domain shift when applied to physical testbeds (`MZVAV-2-1` or `SZCAV`).

---

## 5. Feasibility Verdict & Next Steps

> **Decision:** **Conditionally Feasible for Research / Benchmarking, NOT Approved for Production Deployment.**

### Mandatory Prerequisites Before Phase 1 (Modeling):
1. Programmatically parse `LBNLDataSynthesisInventory.pdf` to construct an authoritative scenario lookup table.
2. Correct the ground truth label column in `RTU.csv` using Table 4-3 unfaulted dates.
3. Establish a date-grouped cross-validation protocol (`GroupKFold` on calendar day).
4. Implement physical rule-based (APAR) and tabular ML (Random Forest/XGBoost) baselines before any deep learning experimentation.
