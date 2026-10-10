# Dataset Quality Audit: HVAC Fault-Detection Benchmark

**Audit Date:** 2026-10-10  
**Dataset Location:** `data/interim/`  
**Inspected Scope:** 100% of tabular dataset files (6 CSV files, 398,879 total rows).

---

## 1. Observed Facts

### 1.1 Dataset Inventory Summary

| File Relative Path | Size (bytes) | Rows | Cols | Missing Cells (%) | Duplicates | Ground Truth Label Distribution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `data/interim/RTU.csv` | 9,861,097 | 30,240 | 69 | 100,840 cells (4.83%) | 0 | **1: 30,240 (100.0%)**, 0: 0 (0.0%) |
| `data/interim/SZCAV.csv` | 1,582,521 | 21,600 | 16 | 90 `#VALUE!` errors (0.03%) | 0 | 1: 20,160 (93.33%), 0: 1,440 (6.67%) |
| `data/interim/SZVAV.csv` | 1,207,524 | 15,839 | 16 | 1,180 nulls + 1 `#VALUE!` (0.47%) | 0 | 1: 10,080 (63.64%), 0: 5,759 (36.36%) |
| `data/interim/MZVAV-1.csv` | 22,663,837 | 272,160 | 18 | 0 (0.0%) | 0 | 1: 233,280 (85.71%), 0: 38,880 (14.29%) |
| `data/interim/MZVAV-2-1.csv` | 1,755,106 | 21,600 | 19 | 0 (0.0%) | 0 | 0: 18,720 (86.67%), 1: 2,880 (13.33%) |
| `data/interim/MZVAV-2-2.csv` | 2,947,638 | 37,440 | 19 | 0 (0.0%) | 0 | 0: 18,720 (50.00%), 1: 18,720 (50.00%) |
| **Total** | **40,017,723** | **398,879** | — | — | **0** | — |

---

### 1.2 File-by-File Quality Audit

#### A. `RTU.csv` (Experimental Rooftop Unit, ORNL FRP #2)
- **Shape:** 30,240 rows × 69 columns (1-minute resolution, 25 calendar days between 2017-08-27 and 2018-02-18).
- **Missing Values:**
  - 10 columns (`VAV Box: Room 102 Air Temperature` through `Room 206 Air Temperature`) contain exactly 10,084 missing values each (33.35% missing per column).
- **Constant / Near-Constant Columns:**
  - `Fault Detection Ground Truth`: **100% constant (`1`) across all 30,240 rows.** Zero negative/normal examples exist in the CSV file.
  - `RTU: Natural Gas`: 99.96% zeroes (unique values: 13).
  - `RTU: Compressor 2 On/Off Status`: 96.94% zeroes (compressor stage 2 rarely operates).
- **Numeric Ranges and Physical Violations:**
  - `RTU: Circuit 1 Condenser Outlet Pressure`: Min is **-722.70 psig**, Mean is -381.37 psig, P50 is -479.70 psig. Negative condenser outlet pressure is physically impossible in an operating refrigeration cycle, indicating severe sensor calibration failure or transducer scaling errors.
  - `RTU: Circuit 1 Suction Temperature`: Min is -3.55°F.
- **Critical Ground Truth Defect:**
  - In `LBNLDataSynthesisInventory.pdf` (Table 4-3, pp. 24–25), seven specific days are explicitly documented as **Unfaulted**: `9/1/17`, `11/30/17`, `12/3/17`, `12/9/17`, `12/24/17`, `2/4/18`, and `2/5/18`.
  - In `RTU.csv`, all 1,440 records on every one of these seven dates are coded as `Fault Detection Ground Truth = 1`. The raw file has corrupted ground truth.

#### B. `SZCAV.csv` (Experimental Single-Zone CAV AHU, LBNL FLEXLAB)
- **Shape:** 21,600 rows × 16 columns (1-minute resolution, 15 calendar days from 2017-03-11 to 2017-04-01).
- **Missing / Dirty Strings:**
  - `AHU: Mixed Air Temperature`: Contains 90 records with the literal string `'#VALUE!'` resulting from unhandled spreadsheet formula errors during data export.
- **Near-Constant Columns:**
  - `AHU: Supply Air Fan Status`: 99.58% value `1` (constant fan operation during testing).
  - `AHU: Supply Air Fan Speed Control Signal`: 99.87% value `0.5` (constant volume AHU operating at fixed half speed).
- **Class Balance & Target Column:**
  - Candidate Target: `Fault Detection Ground Truth`.
  - Distribution: Class 1 = 20,160 rows (93.33%), Class 0 = 1,440 rows (6.67%).
  - Only **one single day** (`2017-04-01`) represents the unfaulted normal baseline; 14 days represent 14 distinct fault injection scenarios.

#### C. `SZVAV.csv` (Experimental Single-Zone VAV AHU, LBNL FLEXLAB)
- **Shape:** 15,839 rows × 16 columns (1-minute resolution, 11 calendar days from 2017-09-11 to 2017-09-24).
- **Missing / Dirty Strings:**
  - `AHU: Supply Air Temperature Heating Set Point`: 590 missing values (3.72%).
  - `AHU: Supply Air Temperature Cooling Set Point`: 590 missing values (3.72%).
  - `AHU: Outdoor Air Temperature`: Contains 1 record with `'#VALUE!'`.
- **Constant Columns:**
  - `AHU: Supply Air Fan Status`: 100% constant at `1`.
- **Numeric Anomalies:**
  - `AHU: Exhaust Air Damper Control Signal`: Min is `-0.04` (control signal should strictly reside in `[0.0, 1.0]`).
- **Class Balance & Target Column:**
  - `Fault Detection Ground Truth`: Class 1 = 10,080 rows (63.64%), Class 0 = 5,759 rows (36.36%). (7 faulted days vs 4 normal days).

#### D. `MZVAV-1.csv` (Simulated Multi-Zone VAV AHU, PNNL Co-simulation)
- **Shape:** 272,160 rows × 18 columns (1-minute resolution, 189 calendar days between 2017-01-30 and 2017-12-17).
- **Missing Values:** 0 across all columns.
- **Constant Columns:**
  - `AHU: Supply Air Temperature Set Point`: Constant at `55.04°F`.
  - `AHU: Supply Air Duct Static Pressure Set Point`: Constant at `0.04 in. w.g.`.
- **Near-Constant Columns:**
  - `AHU: Return Air Damper Control Signal`: 99.9% value `0.0` (with anomalous max of `2.45`).
  - `AHU: Heating Coil Valve Control Signal`: 99.8% value `0.0`.
- **Class Balance & Target Column:**
  - `Fault Detection Ground Truth`: Class 1 = 233,280 rows (85.71%), Class 0 = 38,880 rows (14.29%). (162 faulted days vs 27 normal days).
  - Temporal block structure: 100% of days are either entirely faulted (1,440 min) or entirely normal (1,440 min). No partial-day faults.

#### E. `MZVAV-2-1.csv` (Experimental Multi-Zone VAV AHU, Drexel / ASHRAE 1312)
- **Shape:** 21,600 rows × 19 columns (1-minute resolution, 15 calendar days between 2007-08-28 and 2009-05-31).
- **Missing Values:** 0 across all columns.
- **Constant Columns:**
  - `AHU: Supply Air Duct Static Pressure Set Point`: Constant at `1.40 in. w.g.`.
- **Numeric Anomalies:**
  - `AHU: Supply Air Temperature`: Min is `0.00°F` (unpowered sensor dropout).
  - `AHU: Return Air Temperature`: Min is `0.00°F`.
- **Class Balance & Ground Truth Discrepancy:**
  - `Fault Detection Ground Truth`: Class 0 = 18,720 rows (86.67%), Class 1 = 2,880 rows (13.33%).
  - Only **2 days** are labeled faulted (`2007-08-28` and `2007-08-29`).
  - Discrepancy: `2007-08-30` is documented in the PDF (Table 2-2) as "Heating coil valve leaking Stage 3 (2.0 GPM)", but in `MZVAV-2-1.csv` it is labeled as `0` (Unfaulted).

#### F. `MZVAV-2-2.csv` (Simulated Multi-Zone VAV AHU, Drexel / ASHRAE 1312)
- **Shape:** 37,440 rows × 19 columns (1-minute resolution, 26 calendar days between 2007-08-28 and 2009-05-15).
- **Missing Values:** 0 across all columns.
- **Constant Columns:**
  - `AHU: Supply Air Duct Static Pressure Set Point`: Constant at `1.40 in. w.g.`.
- **Class Balance & Target Column:**
  - `Fault Detection Ground Truth`: Class 0 = 18,720 rows (50.0%), Class 1 = 18,720 rows (50.0%). (13 normal days vs 13 faulted days).

---

## 2. Interpretations

### 2.1 Absence of Multiclass Fault Labels in Tabular Files
Across all 6 CSV files, there is **no categorical fault type column**. The only label column is binary `Fault Detection Ground Truth` (0 or 1). Specific fault mechanisms (e.g., damper stuck, valve leakage, sensor bias, condenser fouling) are recorded exclusively in human-readable tables inside `LBNLDataSynthesisInventory.pdf`. A multiclass fault diagnosis model cannot be trained without manually constructing a date-range-to-fault mapping pipeline.

### 2.2 Severe Autocorrelation and Data Leakage Risks
Because telemetry is logged every 60 seconds across continuous 24-hour periods:
1. Contiguous rows exhibit near-1.0 autocorrelation.
2. A random row shuffle (`train_test_split`) leaks the daily weather, occupancy, and thermal drift directly from train into test.
3. Models evaluated on randomly shuffled splits will achieve deceptively perfect test scores (>99% accuracy) that catastrophically fail in real-world generalization.

---

## 3. Unknowns
- Whether the -722 psig pressure reading in `RTU.csv` was due to an uncalibrated pressure transducer or an inverted voltage signal.
- The reason why `RTU.csv` unfaulted days were tagged as `1` in the ground truth column.

---

## 4. Recommendations
1. **Sanitize Dirty Strings:** Replace all `'#VALUE!'` occurrences with `NaN` and cast columns to float before any mathematical operations.
2. **Mandatory Group Splitting:** Group all train/validation/test partitions strictly by calendar date or multi-day experimental blocks (`GroupKFold` or `TimeSeriesSplit`). Never use row-level random sampling.
3. **Correct Ground Truth via Inventory:** For `RTU.csv`, re-assign `Fault Detection Ground Truth = 0` to the seven verified unfaulted dates from Table 4-3 before attempting binary classification.
