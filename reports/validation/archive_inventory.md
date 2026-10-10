# Archive Inventory Report: HVAC Dataset Feasibility Audit

**Archive File:** `data/raw/hvac_fdd_benchmark.zip`  
**Audit Date:** 2026-10-10  
**Status:** Validated and Extracted to `data/interim/`  

---

## 1. Observed Facts

### 1.1 Archive Integrity and Storage Metrics
- **Raw File Path:** `data/raw/hvac_fdd_benchmark.zip`
- **Compressed Size:** `7,010,416 bytes` (6.69 MiB / 7.01 MB)
- **SHA-256 Digest:** `68c58568e3f0e4e7d0f0de3194a2ce7ca80703c057325ee402a94d3eab5a76c1`
- **Total Archive Members:** 7 items
- **Total Uncompressed Size:** `41,240,106 bytes` (~39.33 MiB)
- **Overall Compression Ratio:** 83.0% reduction

### 1.2 Full Member Manifest
All members were listed via non-destructive archive header inspection prior to extraction:

| Member Filename | Extension | Uncompressed Size (bytes) | Compressed Size (bytes) | Reduction | CRC-32 | Timestamp |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RTU.csv` | `.csv` | 9,861,097 | 2,610,193 | 73.5% | `2470760677` | 2019-02-05 08:56:52 |
| `SZCAV.csv` | `.csv` | 1,582,521 | 281,805 | 82.2% | `1477750133` | 2019-02-05 08:57:02 |
| `SZVAV.csv` | `.csv` | 1,207,524 | 188,862 | 84.4% | `167385970` | 2019-02-05 08:57:12 |
| `LBNLDataSynthesisInventory.pdf` | `.pdf` | 1,222,383 | 1,091,571 | 10.7% | `3262615431` | 2019-02-05 10:03:50 |
| `MZVAV-1.csv` | `.csv` | 22,663,837 | 2,243,758 | 90.1% | `1221674488` | 2019-02-05 08:56:20 |
| `MZVAV-2-1.csv` | `.csv` | 1,755,106 | 195,261 | 88.9% | `72978018` | 2019-02-05 08:56:30 |
| `MZVAV-2-2.csv` | `.csv` | 2,947,638 | 397,976 | 86.5% | `2605330368` | 2019-02-05 08:56:42 |

### 1.3 Security and Extraction Risk Assessment
- **Path Traversal Check:** No entry contains relative directory traversal patterns (`..`).
- **Absolute Path Check:** No entry begins with `/`, `\`, or drive letters (`C:`).
- **Executable / Binary Check:** No `.exe`, `.bat`, `.cmd`, `.sh`, `.ps1`, `.dll`, `.so`, `.vbs`, or script files detected.
- **Nested Archive Check:** No nested `.zip`, `.tar`, `.gz`, or `.7z` archives detected.
- **Storage Feasibility:** Total uncompressed footprint is ~39.33 MB, requiring negligible disk overhead.
- **Extraction Execution:** Extracted to `data/interim/` on 2026-10-10 with zero overwriting or modification of `data/raw/hvac_fdd_benchmark.zip`.

---

## 2. Interpretations
- The archive contents align directly with the LBNL report *"Inventory of Data Sets for AFDD Evaluation"* (February 2019, Granderson & Lin).
- Six CSV files cover four distinct HVAC equipment paradigms:
  1. `RTU.csv`: Rooftop Unit with 10 VAV terminal zones (experimental from ORNL Flexible Research Platform #2).
  2. `SZCAV.csv`: Single-Zone Constant Air Volume Air Handling Unit (experimental from LBNL FLEXLAB).
  3. `SZVAV.csv`: Single-Zone Variable Air Volume Air Handling Unit (experimental from LBNL FLEXLAB).
  4. `MZVAV-1.csv`: Multi-Zone VAV AHU (simulated EnergyPlus co-simulation by PNNL).
  5. `MZVAV-2-1.csv`: Multi-Zone VAV AHU (experimental from Iowa Energy Resource Station / ASHRAE 1312-RP by Drexel).
  6. `MZVAV-2-2.csv`: Multi-Zone VAV AHU (simulated counterpart from ASHRAE 1312-RP by Drexel).
- `LBNLDataSynthesisInventory.pdf` serves as the primary metadata inventory document for all six CSVs.

---

## 3. Unknowns
- Why the uncompressed files are named with hyphens and spaces that differ slightly from the text table references (e.g., `MZVAV-1` vs `MZVAV-2-1`).
- Whether any updated revision of the dataset was released after February 2019 that addresses the label anomalies discovered during the tabular audit.

---

## 4. Recommendations
- Preserve `data/raw/hvac_fdd_benchmark.zip` in its unmodified state.
- Keep `data/interim/` ignored in Git, using automated scripts to extract on-demand if reproducing work on a fresh clone.
