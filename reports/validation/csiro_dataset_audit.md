# CSIRO AHU Dataset Feasibility Audit (Phase 1A)

**Audit Date:** 2026-10-10  
**Dataset Source:** [CSIRO AHU Fault Detection Dataset](https://github.com/csiro-energy-systems/ahu-fault-detection-dataset)  
**Location:** `data/raw/csiro/`  
**Auditor:** Automated Data-Audit Engine (Phase 1A)  

---

## 1. File Integrity and Environment Verification

### 1.1 Workspace and Git Status
- **Current Working Directory:** `D:\project-3`
- **Project Root:** `D:\project-3`
- **Git Remote Origin:** `https://github.com/nayanojwal0810/project_3.git`
- **Branch:** `main` tracking `origin/main` at commit `d66f443`
- **Git Working Tree:** Clean.

### 1.2 File Integrity and Parquet Signature Verification
All three expected Parquet files were inspected for byte-level authenticity, sizes, and Git LFS status:

| File Name | Relative Path | Actual Size (Bytes) | Expected Size (Bytes) | Size Match | Magic Bytes Start / End | Git LFS Pointer? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AHU9.parquet` | `data/raw/csiro/AHU9.parquet` | 9,786,479 | 9,786,479 | Yes (Exact) | `PAR1` / `PAR1` | No (Real Parquet) |
| `AHU10.parquet` | `data/raw/csiro/AHU10.parquet` | 7,884,660 | 7,884,660 | Yes (Exact) | `PAR1` / `PAR1` | No (Real Parquet) |
| `fault-experiments.parquet` | `data/raw/csiro/fault-experiments.parquet` | 28,276 | 28,276 | Yes (Exact) | `PAR1` / `PAR1` | No (Real Parquet) |

- **Verdict:** All three files are valid, complete binary Apache Parquet datasets. No files are stub Git LFS pointer files.
- **Dependencies:** Python 3.13.3, Pandas 3.0.3, and PyArrow 24.0.0 are verified and operational.

---

## 2. Sensor Telemetry Inspection (`AHU9.parquet` & `AHU10.parquet`)

100% of the sensor rows were inspected (879,822 total telemetry records across two operational commercial air handling units).

### 2.1 Telemetry Overview & Schema

| Metric | `AHU9.parquet` | `AHU10.parquet` |
| :--- | :--- | :--- |
| **Total Rows** | 457,653 | 422,169 |
| **Total Columns** | 17 | 17 |
| **Index Type** | `DatetimeIndex` (UTC) | `DatetimeIndex` (UTC) |
| **Time Span** | `2013-05-01 09:00:00` to `2015-05-22 17:00:00` | `2013-05-01 09:00:00` to `2015-04-20 17:00:00` |
| **Duration Covered** | ~24.7 months (2+ full years) | ~23.7 months (nearly 2 full years) |
| **Sampling Frequency** | Median = 30 sec, Mode = 30 sec | Median = 30 sec, Mode = 30 sec |
| **Timestamp Ordering** | Strictly monotonic increasing | Strictly monotonic increasing |
| **Duplicate Timestamps** | 0 | 0 |
| **Consecutive Row Repeats** | 16,843 (3.68%) | 95,269 (22.57%) |
| **Large Time Gaps (>2.5 min)** | 6,604 gaps (overnight / BMS dropouts) | 6,586 gaps |
| **Missing Values (Nulls)** | 0 / 17 columns (0.0%) | 0 / 17 columns (0.0%) |

### 2.2 Telemetry Feature Channels (17 per AHU)
Both files contain identical sensor channels reflecting standard VAV-AHU monitoring points:
1. `ahuZoneTemp`, `ahuZoneTemp.1`, `ahuZoneTemp.2`: Individual zone temperatures (°C)
2. `ahuAvgZoneTemp`: Average zone temperature (°C)
3. `ahuCcValve`: Cooling coil valve control position (%)
4. `ahuHcValve`: Heating coil valve control position (%)
5. `ahuMaTemp`: Mixed air temperature (°C)
6. `ahuOaDamper`: Outdoor air damper position (%)
7. `ahuOaTemp`: Outdoor air temperature (°C)
8. `ahuRaDamper`: Return air damper position (%)
9. `ahuRaRH`: Return air relative humidity (%)
10. `ahuRaTemp`: Return air temperature (°C)
11. `ahuSaTemp`: Supply air temperature (°C)
12. `ahuSaTempSP`: Supply air temperature setpoint (°C)
13. `ahuSaRH`: Supply air relative humidity (%)
14. `ahuSaFanSpeed`: Supply fan speed (%)
15. `ahuSaPressure`: Supply air static duct pressure (Pa / in. w.g.)

### 2.3 Sensor Data-Quality Findings & Anomalies
1. **Critical Feature Redundancy (`MaTemp` == `SaTemp`):**
   - In **both** AHU9 and AHU10, `ahuMaTemp` and `ahuSaTemp` are **100% mathematically identical** across every single record (`(df['ahuMaTemp'] == df['ahuSaTemp']).all() == True`).
   - One of these channels must be dropped prior to modeling to avoid exact collinearity.
2. **Sensor Zero Dropouts:**
   - Temperature readings drop to exactly `0.0°C` during brief communications dropouts (e.g., 178 rows in AHU9 zone temperatures, 1,742 rows in outdoor temperature).
3. **Negative Static Pressure:**
   - `ahuSaPressure` registers negative readings down to `-5.6` during fan shut-off periods.
4. **Repeated Telemetry (Steady-State):**
   - 95,269 rows in AHU10 (22.57%) repeat the exact feature vector from the preceding 30-second interval due to slower sensor polling or steady nocturnal equilibrium.

---

## 3. Fault Experiments Audit (`fault-experiments.parquet`)

The experiment metadata table contains 391 ground-truth injected fault runs.

### 3.1 Metadata Fields
- `AHU`: Equipment identifier (`int64`: 9, 10, or 15)
- `Duration (h:mm)`: Human-readable duration (`object`)
- `Magnitude`: Fault intensity/bias parameter (`float64`, e.g. damper % stuck, temperature drift °C)
- `Fault Type`: Standard fault category (`str`)
- `Fault Name`: Detailed experiment identifier (`str`)
- `Fault Description`: Textual explanation of fault mechanism (`str`)
- `Start Datetime`: Experiment start timestamp (`datetime64[us]`)
- `End Datetime`: Experiment end timestamp (`datetime64[us]`)

### 3.2 Experiment Counts and Equipment Distribution
- **Total Experiments:** 391
  - **AHU 9:** 198 experiments
  - **AHU 10:** 103 experiments
  - **AHU 15:** 90 experiments (**Sensor file `AHU15.parquet` is NOT included in the dataset**)
- **Concordance with Sensor Timestamps:**
  - AHU 9: 22 experiments occurred in April 2013 (prior to sensor logging start on May 1, 2013). Thus, **176 experiments** overlap `AHU9.parquet`.
  - AHU 10: All **103 experiments** fall entirely inside the `AHU10.parquet` logging range.
  - **Total Usable Experiments:** 279 experiments across AHU9 and AHU10.
- **Experiment Durations:**
  - Minimum: 20 seconds
  - Maximum: 10 hours
  - Median: 1 hour 8 seconds
  - Missing/Invalid Dates (`End <= Start`): 0

### 3.3 Overlapping & Concurrent Fault Intervals
- A total of **84 overlapping experiment pairs** were discovered across the dataset (30 pairs on AHU 9, 27 pairs on AHU 10, 27 on AHU 15).
- **Physical Reason:** CSIRO researchers injected concurrent compound faults (e.g., `OA Damper Stuck Open` simultaneous with `RA Damper Stuck Open`, or `SA Fan Belt Slip` simultaneous with `Zone Temp Drift`).
- **Impact:** 2,329 sensor rows in AHU9 (0.51%) and 2,238 rows in AHU10 (0.53%) belong to overlapping fault intervals, requiring multi-label framing or explicit disambiguation rules.

---

## 4. Model Label Construction & Class Distribution

Applying interval-join logic between the sensor timestamps and the experiment intervals reveals the following true label distributions:

### 4.1 Binary Fault Detection Labeling (Normal vs. Fault)

| Dataset | Total Sensor Rows | Rows in Fault Intervals | Rows in Normal Baseline | Fault Ratio (%) |
| :--- | :--- | :--- | :--- | :--- |
| `AHU9.parquet` | 457,653 | 32,280 | 425,373 | 7.05% |
| `AHU10.parquet` | 422,169 | 9,338 | 412,831 | 2.21% |
| **Combined** | **879,822** | **41,618** | **838,204** | **4.73%** |

- **Key Takeaway:** Unlike the corrupted LBNL dataset where normal operation was missing or severely truncated, the CSIRO dataset provides **genuine operational normal baselines** comprising 93% to 98% of the data across all four seasons.

### 4.2 Independent Experiments vs. Sensor Rows per Fault Type

A critical data-science pitfall is treating individual 30-second sensor readings as independent samples. The true statistical support is dictated by the number of **independent fault experiments**:

| Fault Type | AHU 9 Exps | AHU 9 Sensor Rows | AHU 10 Exps | AHU 10 Sensor Rows | Total Independent Exps |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OA Damper Stuck Open** | 28 | 2,549 | 28 | 2,641 | **56** |
| **RA Damper Stuck Open** | 31 | 6,710 | 23 | 2,335 | **54** |
| **Zone Average Temp Drift** | 28 | 2,378 | 24 | 1,350 | **52** |
| **SA Fan Belt Slip** | 30 | 8,637 | 10 | 1,479 | **40** |
| **HW Valve Proxy Stuck Open** | 34 | 6,898 | 5 | 423 | **39** |
| **CHW Valve Proxy Stuck Open** | 9 | 585 | 9 | 722 | **18** |
| **Zone Temp Drift** | 8 | 2,228 | 4 | 388 | **12** |
| **HW Valve Stuck Open** | 4 | 600 | 0 | 0 | **4** |
| **SA Duct Leakage** | 1 | 132 | 0 | 0 | **1** |

---

## 5. Evaluation of Leakage & Deep-Learning Feasibility

### 5.1 Data Leakage Risks
1. **Autocorrelation Leakage:** 30-second sensor readings inside a 2-hour fault experiment are nearly identical. Random row shuffling will place adjacent seconds from the same experiment into both train and test, producing near-100% test accuracy via memorization.
2. **Experiment-Level Splitting:** Cross-validation MUST hold out **entire fault experiments and distinct operational weeks**, not individual rows.
3. **Severe Support Deficit for Rare Classes:**
   - `SA Duct Leakage` has exactly **1 experiment**. It is statistically impossible to split this class into independent train and test sets.
   - `HW Valve Stuck Open` has only **4 experiments** (all on AHU 9, zero on AHU 10).
   - Any multiclass classifier must exclude these rare classes or merge them into broader categories (e.g. "Valve Faults").

### 5.2 Deep-Learning Feasibility
- **Feasible Tasks:**
  1. **Binary Fault Detection:** Highly feasible and statistically defensible on both AHU9 and AHU10.
  2. **Top-5 Multiclass Fault Classification:** Feasible for classes with $\ge 30$ independent experiments (`OA Damper`, `RA Damper`, `Fan Belt Slip`, `HW Valve Proxy`, `Zone Avg Temp Drift`).
  3. **Cross-AHU Generalization:** Feasible to train on AHU 9 and test zero-shot transfer on AHU 10 for overlapping fault types.
- **Baseline Requirements:**
  - Deep learning (e.g. 1D-CNN, TCN, LSTM, or PatchTST) must be compared against:
    - Rule-based thresholding (APAR rules).
    - Tabular GBDTs (XGBoost / LightGBM) trained on rolling statistical features (rolling mean, rolling std, temperature differentials).

---

## 6. GenAI Maintenance Copilot Assessment

### 6.1 Capabilities Supported
- `fault-experiments.parquet` supplies descriptive metadata: `Fault Type`, `Fault Name`, `Fault Description`, and `Magnitude`.
- A GenAI assistant can formulate quantitative diagnostic summaries (e.g. "Mixed air temperature rose 4.2°C above setpoint during 50% OA damper override").

### 6.2 Limitations & Unsupported Scope
- The dataset does **not** include maintenance work orders, equipment O&M manuals, manufacturer cut sheets, or resolution procedures.
- The experiment table is an experimental log, not a field maintenance knowledge base.
- **Requirement:** External licensed engineering references (e.g., AIRAH DA19 HVAC Maintenance manual, ASHRAE Guideline 36) must be separately acquired and ingested to provide grounded troubleshooting recommendations without hallucination.

---

## 7. Direct Comparison: CSIRO vs. LBNL

| Dimension | Previously Audited LBNL Dataset | CSIRO Dataset (Audited Here) | Winner |
| :--- | :--- | :--- | :--- |
| **Storage & Format** | Legacy CSVs with formula errors (`#VALUE!`) | Clean, native Apache Parquet (`PAR1`) | **CSIRO** |
| **Data Time Span** | 2 to 3 weeks per dataset | **2+ continuous years** (4 seasons) | **CSIRO** |
| **Ground Truth Structure** | Unstructured PDF tables; binary labels only; 100% constant in `RTU.csv` | **Structured metadata table** (`fault-experiments.parquet`) with exact datetimes, types, descriptions, magnitudes | **CSIRO** |
| **Normal Operation Baseline** | Severe shortage (0% in RTU CSV, 1 day in SZCAV) | **Abundant operational normal baseline** (93% - 98% of data) | **CSIRO** |
| **Sampling Frequency** | 1-minute | 30-second | **CSIRO** |
| **Class Imbalance** | Severe normal-class deficit | Severe fault-class deficit (standard real-world FDD) | **CSIRO** (Realistic) |
| **Multi-Fault Concurrency** | None | 84 compound overlapping fault intervals | **CSIRO** (Realistic) |

---

## 8. Observed Facts, Interpretations, Unresolved Questions, & Recommendation

### 8.1 Observed Facts
1. All three files exist, match expected byte sizes, have valid `PAR1` headers, and are genuine Parquet datasets.
2. Sensor datasets contain 457,653 (AHU9) and 422,169 (AHU10) rows across 17 columns with 0 missing cells.
3. `ahuMaTemp` and `ahuSaTemp` are 100% identical in both AHU9 and AHU10.
4. `fault-experiments.parquet` documents 391 experiments across AHUs 9, 10, and 15. AHU 15 has no corresponding sensor file.
5. 279 experiments fall within the available sensor time windows (176 for AHU9, 103 for AHU10).
6. 84 overlapping fault experiment pairs exist, creating multi-label intervals.

### 8.2 Interpretations
1. The CSIRO dataset is an exponentially higher quality foundation for BuildingOps AI than the LBNL benchmark.
2. The extreme class imbalance (4.7% fault vs 95.3% normal) mirrors real-world commercial HVAC operations and enables meaningful Precision-Recall evaluation.
3. Multiclass classification must be restricted to fault types with $\ge 30$ independent experiments.

### 8.3 Unresolved Questions
1. Is the sensor dataset for `AHU 15` available upstream or intended to remain excluded?
2. Did BMS engineers deliberately wire the supply air temperature sensor to the mixed air temperature point, or is mixed air uninstrumented in these physical units?

### 8.4 Recommendation
> **Verdict:** **CONDITIONALLY PASSES Phase 1A Feasibility Gate.**  
> The CSIRO dataset is recommended as the primary foundation for BuildingOps AI, subject to:
> 1. Dropping `ahuMaTemp` as an exact duplicate of `ahuSaTemp`.
> 2. Excluding `SA Duct Leakage` (1 experiment) and `HW Valve Stuck Open` (4 experiments) from held-out multiclass evaluation.
> 3. Enforcing experiment-level group splitting (`GroupKFold` on experiment ID) to eliminate autocorrelation leakage.
