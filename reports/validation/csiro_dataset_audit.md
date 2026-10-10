# Reconciled CSIRO AHU Dataset Feasibility Audit (Phase 1A.1)

**Audit Date:** 2026-10-10  
**Dataset Source:** [CSIRO AHU Fault Detection Dataset](https://github.com/csiro-energy-systems/ahu-fault-detection-dataset)  
**Location:** `data/raw/csiro/`  
**Evaluation Scope:** 100% of local telemetry and experiment records across `AHU9.parquet`, `AHU10.parquet`, and `fault-experiments.parquet`.  
**Auditor:** Automated Data-Audit Engine (Phase 1A.1 Reconciliation)  

---

## 1. File Integrity, Environment & Provenance Checks

### 1.1 Environment & Git Status
- **Current Working Directory:** `D:\project-3`
- **Project Root:** `D:\project-3`
- **Git Remote Origin:** `https://github.com/nayanojwal0810/project_3.git`
- **Branch:** `main` tracking `origin/main`
- **Dependencies:** Python `3.13.3`, Pandas `3.0.3`, PyArrow `24.0.0` operational. Zero package installations needed.

### 1.2 Binary Parquet Authenticity & Git LFS Verification

| File Name | Relative Path | Actual Size (Bytes) | Expected Size (Bytes) | Size Match | Magic Bytes (Start / End) | Git LFS Pointer? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AHU9.parquet` | `data/raw/csiro/AHU9.parquet` | 9,786,479 | 9,786,479 | Yes (Exact) | `PAR1` / `PAR1` | No (Real Parquet) |
| `AHU10.parquet` | `data/raw/csiro/AHU10.parquet` | 7,884,660 | 7,884,660 | Yes (Exact) | `PAR1` / `PAR1` | No (Real Parquet) |
| `fault-experiments.parquet` | `data/raw/csiro/fault-experiments.parquet` | 28,276 | 28,276 | Yes (Exact) | `PAR1` / `PAR1` | No (Real Parquet) |

- **Verification:** All files are valid binary Apache Parquet tables matching the source repository byte sizes. None are Git LFS stubs.
- **Dataset Provenance & Nature:** Data originates from an operational commercial office building in Newcastle, Australia. Faults were artificially injected into the building management system (BMS) between April and November 2013 using software overrides and hardware proxy points. This is an **injected-fault benchmark on operational equipment**, not a passive capture of natural equipment failures.

---

## 2. Sensor Telemetry Schema & Quality Audit

Every record of `AHU9.parquet` (457,653 rows) and `AHU10.parquet` (422,169 rows) was audited.

### 2.1 Sensor Telemetry Metrics

| Metric | `AHU9.parquet` | `AHU10.parquet` | Reconciled Total |
| :--- | :--- | :--- | :--- |
| **Total Rows** | 457,653 | 422,169 | **879,822** |
| **Total Sensor Columns** | 17 | 17 | 17 |
| **Timestamp Timezone Status** | **Timezone unspecified (naive)** | **Timezone unspecified (naive)** | Timezone naive |
| **Timestamp Span** | `2013-05-01 09:00:00` to `2015-05-22 17:00:00` | `2013-05-01 09:00:00` to `2015-04-20 17:00:00` | ~2-year timestamp span |
| **Timestamp Continuity** | Two-year span with sampling gaps | Two-year span with sampling gaps | Discontinuous |
| **Sampling Frequency** | Median = 30 sec, Mode = 30 sec | Median = 30 sec, Mode = 30 sec | 30 sec |
| **Timestamp Monotonicity** | Strictly monotonic increasing | Strictly monotonic increasing | Monotonic |
| **Duplicate Timestamps** | **0** | **0** | **0** |
| **Consecutive Identical Rows** | 16,843 (3.68%) | 95,269 (22.57%) | 112,112 (12.74%) |
| **Sampling Gaps (>2.5 min)** | 6,604 gaps | 6,586 gaps | 13,190 gaps |
| **Missing Values (Nulls)** | 0 / 17 columns (0.0%) | 0 / 17 columns (0.0%) | 0 (0.0%) |

### 2.2 Critical Sensor Findings
1. **Exact Feature Collinearity (`ahuMaTemp` == `ahuSaTemp`):**
   - In **both** AHU9 and AHU10, Mixed Air Temperature (`ahuMaTemp`) and Supply Air Temperature (`ahuSaTemp`) are **100% identical across all rows** (`(df['ahuMaTemp'] == df['ahuSaTemp']).all() == True`).
   - *Implication:* The physical sensors were either bridged in the BMS or mapped to the same point. One must be excluded before modeling to eliminate perfect multicollinearity.
2. **Sensor Communications Dropouts (Zeroes):**
   - Temperature readings drop to exactly `0.0°C` in 178 rows in AHU9 and 103 rows in AHU10, corresponding to momentary communications dropouts.
3. **Negative Static Duct Pressure:**
   - `ahuSaPressure` drops to `-5.6` during fan shut-off periods.
4. **Steady-State Telemetry Duplication:**
   - AHU10 contains 95,269 consecutive rows (22.57%) where telemetry is completely unchanging across 30-second steps due to system equilibrium or slower polling intervals.

---

## 3. Fault-Experiment Metadata Reconciliation

The experiment table `fault-experiments.parquet` contains **391 total experiment rows**.

### 3.1 Field Schema & Timezone Status
- Fields: `AHU` (`int64`), `Duration (h:mm)` (`object`), `Magnitude` (`float64`), `Fault Type` (`str`), `Fault Name` (`str`), `Fault Description` (`str`), `Start Datetime` (`datetime64[us]`), `End Datetime` (`datetime64[us]`).
- **Timezone Status:** Both `Start Datetime` and `End Datetime` are **timezone unspecified (naive)**, aligning with the timezone-naive sensor indexes.
- **Durations:** Minimum = 20 seconds, Maximum = 10 hours, Median = 1 hour 8 seconds.
- **Validity:** 0 invalid durations (`End Datetime <= Start Datetime`). 0 duplicate experiment rows.

### 3.2 Equipment & Window Reconciliation
- **Total Experiments by AHU:**
  - AHU 9: 198 experiments
  - AHU 10: 103 experiments
  - AHU 15: 90 experiments (**Sensor file `AHU15.parquet` is missing from the dataset**)
  - *Sum:* $198 + 103 + 90 = 391$.
- **Usable Experiments in Sensor Time Windows:**
  - AHU 9: 22 experiments occurred between `2013-04-02` and `2013-04-30`, prior to sensor logging start (`2013-05-01 09:00:00`). **176 experiments** fall inside the sensor window.
  - AHU 10: All **103 experiments** fall inside the sensor window.
  - *Usable Experiments Total:* $176 + 103 = \mathbf{279}$ experiments.

### 3.3 Reconciliation of 279 Usable vs. 276 Named Experiments
The discrepancy between 279 usable experiments and the 276 per-type experiment counts is fully resolved:
- Exactly **3 experiments in `fault-experiments.parquet` have a null / missing (`NaN`) `Fault Type`** (and null `Fault Description`).
- All 3 occur on AHU 9 inside the sensor logging window:
  - Row 36: `AHU 9`, `2013-05-13 13:25:00` to `2013-05-13 16:25:00` (3 hours, `Fault Name`: "HW Valve Prx 30%")
  - Row 37: `AHU 9`, `2013-05-14 12:58:00` to `2013-05-14 14:58:00` (2 hours, `Fault Name`: "HW Valve Prx 30%")
  - Row 38: `AHU 9`, `2013-05-17 07:00:00` to `2013-05-17 17:00:00` (10 hours, `Fault Name`: "Undocumented 100% CHW Valve all day?")
- Standard pandas `value_counts()` silently dropped these 3 `NaN` records ($276 + 3 = 279$).

### 3.4 Complete Raw Fault Type Distribution (All 391 Experiments)

| Raw Fault Type | AHU 9 | AHU 10 | AHU 15 (No Sensors) | Total Experiments | In Sensor Window (AHU 9 & 10) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OA Damper Stuck Open** | 35 | 28 | 23 | **86** | 56 (28 in AHU9, 28 in AHU10) |
| **RA Damper Stuck Open** | 35 | 23 | 22 | **80** | 54 (31 in AHU9, 23 in AHU10) |
| **Zone Average Temp Drift** | 28 | 24 | 24 | **76** | 52 (28 in AHU9, 24 in AHU10) |
| **SA Fan Belt Slip** | 36 | 10 | 1 | **47** | 40 (30 in AHU9, 10 in AHU10) |
| **HW Valve Proxy Stuck Open** | 36 | 5 | 2 | **43** | 39 (34 in AHU9, 5 in AHU10) |
| **CHW Valve Proxy Stuck Open** | 10 | 9 | 6 | **25** | 18 (9 in AHU9, 9 in AHU10) |
| **Zone Temp Drift** | 13 | 4 | 2 | **19** | 12 (8 in AHU9, 4 in AHU10) |
| **HW Valve Stuck Open** | 1 | 0 | 10 | **11** | 4 (4 in AHU9, 0 in AHU10) |
| **<Missing / NaN>** | 3 | 0 | 0 | **3** | **3** (3 in AHU9, 0 in AHU10) |
| **SA Duct Leakage** | 1 | 0 | 0 | **1** | **1** (1 in AHU9, 0 in AHU10) |
| **Reconciled Total** | **198** | **103** | **90** | **391** | **279** (176 in AHU9, 103 in AHU10) |

---

## 4. Rigorous All-Pairs Overlap Audit

Replacing adjacent-pair checking with exhaustive all-pairs overlap detection ($\max(s_i, s_j) < \min(e_i, e_j)$) establishes the true overlap geometry:

### 4.1 Experiment Overlap Statistics
- **All-Pairs Overlapping Pairs (Half-Open $[start, end)$):**
  - AHU 9: **34 overlapping pairs** (involving 54 total experiments)
  - AHU 10: **31 overlapping pairs** (involving 49 total experiments)
  - AHU 15: **31 overlapping pairs** (involving 49 total experiments)
  - *Combined Total Across AHU 9 & 10:* **65 overlapping experiment pairs**
  - *Total Across All Three AHUs:* **96 overlapping experiment pairs**
- **All-Pairs Overlapping Pairs (Closed $[start, end]$):**
  - AHU 9: 35 pairs | AHU 10: 31 pairs | AHU 15: 31 pairs (97 total). Exactly one boundary-touching pair exists in AHU 9 where one experiment ends at the exact second the next begins.

### 4.2 Clean vs. Overlapping Experiments in Sensor Window
- **AHU 9 (176 experiments in window):**
  - Overlapping: 52 experiments
  - **Clean Non-Overlapping:** **124 experiments**
- **AHU 10 (103 experiments in window):**
  - Overlapping: 49 experiments
  - **Clean Non-Overlapping:** **54 experiments**
- **Combined (279 experiments in window):**
  - Overlapping: 101 experiments
  - **Clean Non-Overlapping:** **178 experiments** ($124 + 54 = 178$).

---

## 5. Half-Open Sensor Label Mapping & Count Reconciliation

Following the source repository's official convention `Datetime >= start and Datetime < end` (half-open $[start, end)$), sensor rows were mapped to experiments without label overwriting.

### 5.1 Exact Boundary Point Tests
- `AHU9.parquet`: Exactly 40 timestamps coincide with an experiment `Start Datetime` (included); exactly 35 coincide with an `End Datetime` (excluded under $[start, end)$).
- `AHU10.parquet`: Exactly 10 timestamps coincide with `Start Datetime` (included); exactly 8 coincide with `End Datetime` (excluded under $[start, end)$).

### 5.2 Sensor Telemetry Partition Reconciliation

| Partition | `AHU9.parquet` | `AHU10.parquet` | Combined Rows | % of Total Telemetry |
| :--- | :--- | :--- | :--- | :--- |
| **Clean Single-Fault Rows** | 29,924 | 7,096 | **37,020** | 4.21% |
| **Multi-Fault Overlapping Rows** | 2,325 | 2,236 | **4,561** | 0.52% |
| **Total in Documented Injected-Fault Windows** | **32,249** | **9,332** | **41,581** | **4.73%** |
| **Rows Outside Documented Fault Windows** | **425,404** | **412,837** | **838,241** | **95.27%** |
| **Reconciled Total Sensor Rows** | **457,653** | **422,169** | **879,822** | **100.00%** |

*Verification Assertions Passed:*
- $\text{Clean Single-Fault} (37,020) + \text{Multi-Fault} (4,561) = \text{Total Fault Window} (41,581)$.
- $\text{Total Fault Window} (41,581) + \text{Outside Documented Windows} (838,241) = \text{Total Telemetry} (879,822)$.

### 5.3 Explanation of the 41,618 vs. 40,055 Sensor Row Discrepancy
In the prior preliminary audit, row counts did not reconcile because:
1. Under closed intervals $[start, end]$, total fault window rows equaled 41,618. Under the published half-open standard $[start, end)$, boundary rows are excluded, yielding **41,581 rows**.
2. Summing single-label assignments from an overwriting loop produced 40,055 rows because overlapping multi-fault records (4,561 rows) were assigned to whichever single label was evaluated last, and 1,560 rows belonged to the 3 `<Missing / NaN>` experiments.
3. Preserving multi-label records resolves the discrepancy completely.

---

## 6. Audit of Clean Examples & Class Evaluation Feasibility

To determine whether classes have enough independent support for a leak-free train/validation/test split, we distinguish **sensor row count** from **clean independent experiment count**:

### 6.1 Clean Non-Overlapping Single-Fault Support

| Fault Class | Clean Exps (AHU9) | Clean Exps (AHU10) | Total Clean Exps | Clean Sensor Rows (AHU9) | Clean Sensor Rows (AHU10) | Total Clean Sensor Rows | Held-out Evaluation Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RA Damper Stuck Open** | 25 | 17 | **42** | 6,645 | 1,969 | 8,614 | **High** ($\ge 30$ clean exps) |
| **SA Fan Belt Slip** | 27 | 9 | **36** | 8,598 | 1,477 | 10,075 | **High** ($\ge 30$ clean exps) |
| **HW Valve Proxy Stuck Open** | 29 | 1 | **30** | 6,405 | 121 | 6,526 | **High** ($\ge 30$ clean exps) |
| **Zone Average Temp Drift** | 13 | 9 | **22** | 1,769 | 869 | 2,638 | **Moderate** (22 clean exps) |
| **OA Damper Stuck Open** | 10 | 10 | **20** | 1,468 | 1,734 | 3,202 | **Moderate** (20 clean exps) |
| **Zone Temp Drift** | 7 | 3 | **10** | 2,163 | 326 | 2,489 | **Low** (10 clean exps) |
| **CHW Valve Proxy Stuck Open**| 5 | 5 | **10** | 584 | 600 | 1,184 | **Low** (10 clean exps) |
| **HW Valve Stuck Open** | 4 | 0 | **4** | 600 | 0 | 600 | **Deficient** (AHU 9 only, 4 exps) |
| **<Missing / NaN>** | 3 | 0 | **3** | 1,560 | 0 | 1,560 | **Excluded** (Unlabeled) |
| **SA Duct Leakage** | 1 | 0 | **1** | 132 | 0 | 132 | **Infeasible** (1 single exp) |
| **Reconciled Clean Total** | **124** | **54** | **178** | **29,924** | **7,096** | **37,020** | — |

### 6.2 Concurrent / Multi-Fault Sensor Rows (4,561 rows)
When experiments overlap, sensor readings represent compound physical faults:
- `OA Damper Stuck Open + Zone Average Temp Drift`: 2,292 rows (1,145 in AHU9, 1,147 in AHU10)
- `RA Damper Stuck Open + Zone Average Temp Drift`: 846 rows (423 in AHU9, 423 in AHU10)
- `CHW Valve Proxy + HW Valve Proxy`: 844 rows (422 in AHU9, 422 in AHU10)
- `OA Damper Stuck Open + RA Damper Stuck Open`: 365 rows (181 in AHU9, 184 in AHU10)
- `HW Valve Proxy + SA Fan Belt Slip`: 94 rows (AHU9 only)
- `SA Fan Belt Slip + Zone Temp Drift`: 120 rows (60 in AHU9, 60 in AHU10)

---

## 7. Temporal Coverage & Operational Target Definitions

### 7.1 Fault Injection Window vs. Background Observations
Telemetry spans 24 months, but **all fault injections occurred exclusively within a 7-month window in 2013**:

```
AHU 9:  [--- Injected Faults Window (May-Nov 2013) ---] [------ Unmonitored Background (Dec 2013 - May 2015) ------]
AHU 10: [Unmonitored] [Faults (Sep-Nov 2013)]           [------ Unmonitored Background (Dec 2013 - Apr 2015) ------]
```

### 7.2 Monthly Telemetry & Fault Coverage Table

| Month | AHU 9 Total Rows | AHU 9 Fault Rows | AHU 9 Exps Started | AHU 10 Total Rows | AHU 10 Fault Rows | AHU 10 Exps Started |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2013-05** | 25,777 | 4,501 (17.5%) | 25 | 25,777 | 0 (0.0%) | 0 |
| **2013-06** | 17,646 | 1,021 (5.8%) | 9 | 17,646 | 0 (0.0%) | 0 |
| **2013-07** | 29,791 | 1,419 (4.8%) | 6 | 29,791 | 0 (0.0%) | 0 |
| **2013-08** | 29,757 | 12,821 (43.1%)| 18 | 29,757 | 0 (0.0%) | 0 |
| **2013-09** | 28,824 | 5,168 (17.9%) | 26 | 28,824 | 1,555 (5.4%) | 9 |
| **2013-10** | 29,789 | 4,115 (13.8%) | 37 | 29,789 | 4,306 (14.5%)| 39 |
| **2013-11** | 28,767 | 3,204 (11.1%) | 55 | 14,354 | 3,471 (24.2%)| 55 |
| **2013-12 to 2015-05** (18 mos) | 267,302 | **0 (0.0%)** | 0 | 246,231 | **0 (0.0%)** | 0 |

### 7.3 Target Definition Caveat: "Outside Documented Fault Windows"
- Rows outside recorded fault intervals represent **periods outside documented fault injection**.
- They are **not proven to be free of naturally occurring mechanical failures, sensor calibration drift, or undocumented building maintenance**.
- Target definitions in any future experiment must formalize the negative class as *"Outside Documented Injected-Fault Windows"* rather than assuming absolute ground-truth normality.
- **Seasonal Limitation:** Zero fault experiments occurred during the Australian summer (December, January, February). A model cannot be claimed to generalize across all four seasons.

---

## 8. Data Leakage & Evaluation Recommendations

1. **Strict Experiment-Level Group Splitting:**
   - Because 30-second sensor readings within an experiment exhibit extreme autocorrelation, rows from the same experiment ID must never be split across train and test.
   - Cross-validation must employ `GroupKFold` on `experiment_id` or contiguous block time-series splits.
2. **Pruning Deficient Target Classes:**
   - `SA Duct Leakage` (1 experiment) and `HW Valve Stuck Open` (4 experiments) must be excluded from multiclass held-out evaluation.
   - The 3 unlabeled `<Missing / NaN>` experiments (1,560 rows) must be excluded from supervised fault classification.
3. **Compound Fault Handling:**
   - Overlapping intervals (4,561 rows) must either be treated as explicit multi-label targets or quarantined from single-label benchmark evaluation.

---

## 9. GenAI Maintenance Copilot Reality

- `fault-experiments.parquet` supplies factual test metadata (`Fault Type`, `Fault Description`, `Magnitude`, `Duration`).
- It does **not** provide equipment manuals, wiring diagrams, sequence of operations (SOO), or corrective maintenance Standard Operating Procedures (SOPs).
- An evidence-grounded GenAI troubleshooting system requires separate, licensed engineering documentation (e.g. AIRAH DA19 HVAC Maintenance manual, ASHRAE Guideline 36) to avoid hallucinated maintenance advice.

---

## 10. Audit Conclusions & Gate Decision

### 10.1 Summary of Reconciled Facts
1. All three Parquet files are authentic, uncorrupted binary tables.
2. The telemetry has 457,653 rows (AHU9) and 422,169 rows (AHU10), spanning two years with sampling gaps and timezone-naive timestamps.
3. `ahuMaTemp` and `ahuSaTemp` are identical in both AHUs.
4. `fault-experiments.parquet` documents 391 experiments. 279 experiments fall within sensor windows (176 for AHU9, 103 for AHU10). 3 experiments have missing/NaN fault labels.
5. 65 all-pairs overlapping experiment pairs exist across AHU9 and AHU10, covering 4,561 multi-fault sensor rows.
6. 178 clean, non-overlapping experiments exist in the sensor window, covering 37,020 clean single-fault sensor rows.
7. Fault injections are confined to May–November 2013; December 2013 to May 2015 contains zero fault injections.

### 10.2 Quality Gate Decision
> **Verdict:** **CONDITIONALLY PASSES Phase 1A.1 Data-Quality Gate.**  
> The CSIRO dataset is a viable candidate for a controlled signal check, provided that:
> 1. `ahuMaTemp` is excluded as an exact duplicate.
> 2. Evaluation is framed on clean, non-overlapping experiments with $\ge 20$ independent runs (`RA Damper`, `SA Fan Belt Slip`, `HW Valve Proxy`, `Zone Average Temp Drift`, `OA Damper`).
> 3. Normal is defined as "outside documented injection windows".
> 4. Group splitting is enforced at the experiment level.
> 5. No claims of full four-season fault generalization are made.
