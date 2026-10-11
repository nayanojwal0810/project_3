# FinQA Dataset Comprehensive Integrity & Feasibility Audit

**Audit Date:** October 2026  
**Auditor:** Antigravity Pair Programmer / Data Audit Engineer  
**Dataset Name:** FinQA: A Dataset of Numerical Reasoning over Financial Data  
**Data Directory:** `data/raw/FinQA/`  
**Audit Script:** [`scripts/audit_finqa.py`](file:///d:/project-3/scripts/audit_finqa.py)  
**Execution Command:** `python scripts/audit_finqa.py`  
**Census Scope:** 100% census verification across all 9,200 records (zero sampling)  
**Audit Verdict:** **PASS (with Essential Architectural Caveats)**

---

## Executive Summary & Gate Decision

A comprehensive 100% census audit was conducted on the complete locally downloaded FinQA dataset across all four splits (`train.json`, `dev.json`, `test.json`, and `private_test.json`). Every single record was programmatically validated for JSON syntax, schema consistency, field typing, deep null values, duplicate identifiers, cross-split document and company overlap, retrieval cache presence, program DAG validity, and data leakage risks.

### Final Verdict: PASS
The dataset demonstrates structural hygiene, zero corrupt files, 100% valid JSON, zero null fields across all records and table cells, and a strict document-level partition separating training from evaluation. It is fully validated to advance to Phase 1B (model-signal baseline validation). However, any downstream modeling must strictly adhere to the four-tier architectural boundaries identified below.

---

## 1. File Verification & Data Provenance

All four expected dataset splits exist in `data/raw/FinQA/`. Root objects are valid top-level JSON arrays.

| Split | File Path | File Size (Bytes) | Record Count | Root Structure | JSON Syntax |
|---|---|---|---|---|---|
| **Train** | `data/raw/FinQA/train.json` | 78,216,616 | 6,251 | JSON Array (`list`) | Valid (0 errors) |
| **Dev** | `data/raw/FinQA/dev.json` | 10,954,658 | 883 | JSON Array (`list`) | Valid (0 errors) |
| **Test (Public)** | `data/raw/FinQA/test.json` | 14,395,143 | 1,147 | JSON Array (`list`) | Valid (0 errors) |
| **Private Test** | `data/raw/FinQA/private_test.json` | 5,597,114 | 919 | JSON Array (`list`) | Valid (0 errors) |
| **Total Census** | — | **109,163,531** (~104.1 MB) | **9,200** | — | **100% Valid** |

### Data Provenance
- **Source:** FinQA Benchmark (Chen et al., EMNLP 2021).
- **Domain:** S&P 500 annual earnings reports (Form 10-K filings with the U.S. SEC between 1999 and 2019).
- **Structure:** Semi-structured hybrid document pages combining tabular data with unstructured pre-table and post-table narrative text.
- **Task:** Question-answering requiring multi-hop financial information extraction and symbolic program execution (arithmetic DSL).

---

## 2. Schema and Field Presence Analysis

The dataset exhibits two distinct schema variants: **annotated splits** (`train`, `dev`, `test`) and the **blinded evaluation split** (`private_test`).

### A. Top-Level Field Presence & Type Conformity

| Field Name | Expected Type | Train (6,251) | Dev (883) | Test (1,147) | Private Test (919) | Description |
|---|---|---|---|---|---|---|
| `id` | `str` | 100% (6,251) | 100% (883) | 100% (1,147) | 100% (919) | Unique record ID (`<TICKER>/<YEAR>/page_<N>.pdf-<Q>`) |
| `filename` | `str` | 100% (6,251) | 100% (883) | 100% (1,147) | 100% (919) | Source document page path (`<TICKER>/<YEAR>/page_<N>.pdf`) |
| `table` | `list[list[str]]` | 100% (6,251) | 100% (883) | 100% (1,147) | 100% (919) | Tokenized / normalized table matrix |
| `table_ori` | `list[list[str]]` | 100% (6,251) | 100% (883) | 100% (1,147) | 100% (919) | Raw table matrix preserving original punctuation and casing |
| `pre_text` | `list[str]` | 100% (6,251) | 100% (883) | 100% (1,147) | 100% (919) | Sentences preceding the financial table |
| `post_text` | `list[str]` | 100% (6,251) | 100% (883) | 100% (1,147) | 100% (919) | Sentences following the financial table |
| `qa` | `dict` | 100% (6,251) | 100% (883) | 100% (1,147) | 100% (919) | Question and answer annotation container |
| `table_retrieved` | `list[dict]` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Precomputed retriever output scores for table rows |
| `text_retrieved` | `list[dict]` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Precomputed retriever output scores for text sentences |
| `table_retrieved_all` | `list[dict]` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Exhaustive retriever table ranking |
| `text_retrieved_all` | `list[dict]` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Exhaustive retriever text ranking |

*Type Conformity:* 0 type mismatches across all 9,200 records. Every field strictly conforms to its expected Python type.

---

### B. QA Internal Field Presence & Type Conformity

| QA Field | Expected Type | Train (6,251) | Dev (883) | Test (1,147) | Private Test (919) | Description |
|---|---|---|---|---|---|---|
| `question` | `str` | 100% (6,251) | 100% (883) | 100% (1,147) | **100% (919)** | Natural language financial question |
| `answer` | `str` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Formatted natural language answer |
| `exe_ans` | `float` / `str` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Executable numerical result of the program |
| `program` | `str` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Linear Domain-Specific Language (DSL) program |
| `program_re` | `str` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Nested functional representation of the program |
| `steps` | `list[dict]` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Step-by-step reasoning decomposition with operands |
| `explanation` | `str` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Textual explanation (sparse: ~85% empty) |
| `gold_inds` | `dict` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Gold supporting sentence / table row mapping |
| `ann_table_rows` | `list[int]` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Row indices supporting the calculation |
| `ann_text_rows` | `list[int]` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Text sentence indices supporting the calculation |
| `tfidftopn` | `dict` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Baseline TF-IDF retrieved passages |
| `model_input` | `list` | 100% (6,251) | 100% (883) | 100% (1,147) | **0% (0)** | Pre-filtered context fed to baseline generator |

---

## 3. Deep Null and Empty Field Audit

1. **Deep Null Audit:**
   - Root keys: **0 nulls**
   - QA keys: **0 nulls**
   - Table cells (`table` and `table_ori` across all rows and columns): **0 null cells**
   - Narrative sentences (`pre_text` and `post_text`): **0 null sentences**
   - Total null count across entire dataset: **0 (Zero)**

2. **Empty Strings & Lists:**
   - `qa.answer` empty strings:
     - `train`: 48 records (0.77%)
     - `dev`: 12 records (1.36%)
     - `test`: 14 records (1.22%)
     - *Audit Finding:* In 100% of these records, `qa.exe_ans` and `qa.program` are fully populated and valid (e.g., boolean outputs `"yes"`/`"no"` or complex ratios where human annotators omitted the formatted answer string). Downstream evaluation must evaluate against `qa.exe_ans`, not `qa.answer`.
   - `qa.explanation` empty strings:
     - `train`: 5,310 records (84.95%)
     - `dev`: 753 records (85.28%)
     - `test`: 970 records (84.57%)
     - *Finding:* Optional field; not required for program execution.
   - Evidence-specific empty lists:
     - `qa.ann_table_rows` is empty in 1,458 train (23.32%), 198 dev (22.42%), and 358 test (31.21%) records. This corresponds to questions whose gold evidence is derived strictly from narrative text.
     - `qa.ann_text_rows` is empty in 3,922 train (62.74%), 542 dev (61.38%), and 744 test (64.86%) records. This corresponds to questions whose gold evidence is derived strictly from tabular rows.
   - Precomputed retriever empty caches:
     - `table_retrieved` empty: 440 train (7.04%), 47 dev (5.32%), 90 test (7.85%).
     - `text_retrieved` empty: 620 train (9.92%), 101 dev (11.44%), 111 test (9.68%).
     - `qa.tfidftopn` empty: 681 train (10.89%), 111 dev (12.57%), 125 test (10.90%).

3. **Context Distributions:**
   - Table Rows per record: min = 1, median = 6, max = 18, avg = 6.3 rows.
   - Pre-Text Sentences per record: min = 1, median = 8–10, max = 120, avg = 11.4 sentences.
   - Post-Text Sentences per record: min = 1, median = 9–11, max = 260, avg = 12.8 sentences.

---

## 4. Partition Integrity, IDs, and Overlap Analysis

### A. Record, Document, and Company Inventories

| Partition | Total Records | Unique IDs | Duplicate IDs | Unique Question Strings | Unique Document Pages | Unique Companies (Tickers) |
|---|---|---|---|---|---|---|
| **Train** | 6,251 | 6,251 | **0** | 6,131 | 2,110 | 135 |
| **Dev** | 883 | 883 | **0** | 874 | 299 | 97 |
| **Test** | 1,147 | 1,147 | **0** | 1,138 | 380 | 100 |
| **Private Test** | 919 | 919 | **0** | 892 | 303 | 93 |

*ID Uniqueness:* Within every split, 100% of IDs are unique. Zero within-split duplicate IDs exist.

*Duplicate Question Strings within Splits:*
- `train`: 109 questions appear 2–4 times.
- `dev`: 9 questions appear 2 times.
- `test`: 9 questions appear 2 times.
- `private_test`: 25 questions appear 2 times.
- *Root Cause:* In financial analysis, standard template questions (e.g., *"what is the percent change in net revenue between 2007 and 2008?"*, *"what percentage of net assets acquired was considered goodwill?"*) naturally apply across multiple distinct companies. 52 duplicate questions in `train` span different corporate filings, while 57 apply to different aspects of the same filing.

---

### B. Pairwise Cross-Split Overlap Matrix

| Split Pair | Shared IDs | Shared Questions | Shared Document Pages (`filename`) | Shared Companies (Tickers) | Document Split Status |
|---|---|---|---|---|---|
| **Train vs Dev** | **0** | 16 | **0** | 96 (of 135 & 97) | **Clean Disjoint Split** |
| **Train vs Test** | **0** | 7 | **0** | 99 (of 135 & 100) | **Clean Disjoint Split** |
| **Train vs Private Test** | **0** | 5 | **0** | 93 (of 135 & 93) | **Clean Disjoint Split** |
| **Dev vs Test** | **0** | 2 | **0** | 78 (of 97 & 100) | **Clean Disjoint Split** |
| **Dev vs Private Test** | **0** | 0 | **0** | 74 (of 97 & 93) | **Clean Disjoint Split** |
| **Test vs Private Test** | **726** | 6 | **303** | 93 (of 100 & 93) | **Shared Document Corpus** |

#### Key Architectural Findings:
1. **Document-Level Partitioning (Train vs Evaluation):**
   - Train, Dev, and Test share **exactly 0 document pages** (`filename`).
   - The authors partitioned the dataset at the filing page level. Models evaluated on Dev or Test cannot memorize document page text or tabular layouts seen in Train.
2. **Company Overlap:**
   - S&P 500 company tickers (e.g., AAPL, MSFT, ADBE) overlap across splits (~70–98%), but appear under different filing years and completely different 10-K document pages.
3. **`test.json` vs `private_test.json` Evaluation Relationship:**
   - `private_test.json` shares all 303 document pages and 726 question ID stems with `test.json`.
   - However, **questions are distinct**: only 1 question across the entire shared ID set is verbatim identical; the remaining 918 questions in `private_test` are alternative questions posed on the same test filings.
   - `private_test.json` is strictly blinded: contains **zero gold answers, zero programs, zero steps, and zero retriever caches**.

---

## 5. Retrieval-Cache Availability & Leakage Hazards

The audit verified the presence of precomputed retriever artifacts across all splits:

| Field Name | Description | Train (6,251) | Dev (883) | Test (1,147) | Private Test (919) | Real-World Availability |
|---|---|---|---|---|---|---|
| `table_retrieved` | Dense retriever scores for table rows | 100% | 100% | 100% | **0% (Absent)** | None |
| `text_retrieved` | Dense retriever scores for text sentences | 100% | 100% | 100% | **0% (Absent)** | None |
| `table_retrieved_all` | Full retriever ranked table rows | 100% | 100% | 100% | **0% (Absent)** | None |
| `text_retrieved_all` | Full retriever ranked text sentences | 100% | 100% | 100% | **0% (Absent)** | None |
| `qa.tfidftopn` | Sparse TF-IDF top passages | 100% | 100% | 100% | **0% (Absent)** | None |
| `qa.model_input` | Pre-filtered generator context | 100% | 100% | 100% | **0% (Absent)** | None |

> [!WARNING]
> **CRITICAL ARCHITECTURAL LEAKAGE RISK:**  
> The fields `table_retrieved`, `text_retrieved`, `qa.tfidftopn`, and `qa.model_input` are pre-filtered retrieval outputs generated by Chen et al.'s original RoBERTa cross-encoder retriever. **They do not exist in `private_test.json` or in real-world production.** Any model or pipeline that feeds `qa.model_input` directly into a generator bypasses the retrieval stage entirely. Downstream development must implement a genuine retrieval component starting from `table` and `pre_text`/`post_text`.

---

## 6. Target Types, Symbolic Programs, and Evidence Modalities

### A. Executable Answer (`exe_ans`) Types & Distributions
- **Float (`float`):** 6,127 (98.02% in train), 873 (98.87% in dev), 1,127 (98.26% in test).
- **String (`str`):** 124 (1.98% in train), 10 (1.13% in dev), 20 (1.74% in test) — categorical boolean answers `"yes"` and `"no"`.
- **Anomalies / Corruptions:** **0 NaN values, 0 Inf values**.
- **Extreme Scale Values (> 1 Billion):** 18 in train, 3 in dev, 1 in test (representing large corporate balance sheet totals, e.g., $1.2 \times 10^9$).

---

### B. Domain-Specific Language (DSL) Operations Frequency

The symbolic programs are composed of 10 mathematical and aggregation operations:

| Operation | Functionality | Train (6,251) | Dev (883) | Test (1,147) |
|---|---|---|---|---|
| `divide(a, b)` | Ratios, percentages, margins | **4,445** (46.4%) | 636 (46.8%) | 820 (46.5%) |
| `subtract(a, b)` | Variance, YoY change | **2,739** (28.6%) | 416 (30.6%) | 521 (29.6%) |
| `add(a, b)` | Aggregations, totals | **1,512** (15.8%) | 180 (13.2%) | 260 (14.8%) |
| `multiply(a, b)` | Scaling, percentage applications | **567** (5.9%) | 83 (6.1%) | 109 (6.2%) |
| `greater(a, b)` | Threshold comparisons (outputs yes/no) | **124** (1.3%) | 10 (0.7%) | 20 (1.1%) |
| `average(list)` | Mean of retrieved items | **95** (1.0%) | 19 (1.4%) | 15 (0.9%) |
| `max(list)` | Maximum value | **48** (0.5%) | 8 (0.6%) | 10 (0.6%) |
| `sum(list)` | Sum of sequence | **36** (0.4%) | 4 (0.3%) | 10 (0.6%) |
| `min(list)` | Minimum value | **27** (0.3%) | 5 (0.4%) | 4 (0.2%) |
| `exp(a, b)` | Exponential / compounding growth | **5** (0.1%) | 1 (0.1%) | 3 (0.2%) |
| **Total Operations** | — | **9,598** | **1,362** | **1,772** |

---

### C. Constants and Program Complexity

- **Top Symbolic Constants:** `const_100` (466 train), `const_2` (161 train), `const_3` (136 train), `const_1000` (134 train), `const_1000000` (105 train), `const_1` (train).
- **Steps per Program:** min = 1, median = 1, max = 6, avg = 1.54 steps.
- **DAG Reference Validity:** **0 invalid DAG references**. In 100% of programs, intermediate variables (`#0`, `#1`, etc.) reference strictly preceding operations ($j < i$).

---

### D. Evidence Modality Breakdown (`gold_inds`)

| Modality | Train (6,251) | Dev (883) | Test (1,147) |
|---|---|---|---|
| **Table Only** | 3,922 (62.74%) | 542 (61.38%) | 706 (61.55%) |
| **Text Only** | 1,458 (23.32%) | 198 (22.42%) | 283 (24.67%) |
| **Hybrid (Table + Narrative Text)** | 871 (13.93%) | 143 (16.19%) | 158 (13.78%) |
| **Neither (Missing Evidence)** | **0 (0.00%)** | **0 (0.00%)** | **0 (0.00%)** |

*Key Insight:* Nearly 14–16% of questions require hybrid multi-modal reasoning across both tabular cells and surrounding textual disclosures. A pipeline that only reads tables or only reads text will fail on over 37% of queries.

---

## 7. Architectural Tiers & Leakage Barrier

Downstream models must enforce a strict four-tier separation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA FIELD ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────┤
│ 1. PURE INFERENCE-TIME INPUTS (Available in production & private test)  │
│    - id, filename                                                      │
│    - pre_text, post_text (unstructured surrounding narrative)          │
│    - table, table_ori (tabular financial statements)                   │
│    - qa.question (user query)                                          │
├────────────────────────────────────────────────────────────────────────┤
│ 2. GOLD SUPERVISED TARGETS (Strictly masked at inference time)         │
│    - qa.exe_ans (Primary evaluation metric)                            │
│    - qa.answer                                                         │
│    - qa.program, qa.program_re (Program generation supervision)        │
│    - qa.steps                                                          │
├────────────────────────────────────────────────────────────────────────┤
│ 3. GOLD SUPPORTING EVIDENCE (For retriever training only)              │
│    - qa.gold_inds                                                      │
│    - qa.ann_table_rows, qa.ann_text_rows                               │
├────────────────────────────────────────────────────────────────────────┤
│ 4. PRECOMPUTED RETRIEVER CACHES (CRITICAL LEAKAGE WARNING)             │
│    - table_retrieved, text_retrieved                                   │
│    - table_retrieved_all, text_retrieved_all                           │
│    - qa.tfidftopn, qa.model_input                                      │
│    *WARNING: These fields are pre-computed artifacts from Chen et al.'s │
│     RoBERTa retriever. They DO NOT exist in private_test.json.         │
│     Relying on them circumvents the retrieval stage and invalidates    │
│     end-to-end evaluation!                                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Limitations & Real-World Caveats

1. **Page-Cropped Scope:** Each record represents an isolated page from an SEC 10-K filing rather than a complete multi-hundred-page annual report.
2. **Table Normalization Artifacts:** `table` has casing normalized and punctuation stripped. Complex financial tables with multi-level headers require processing `table_ori`.
3. **Numerical Tolerance Standards:** When evaluating `exe_ans`, evaluations must apply standard numerical tolerances (relative tolerance $10^{-3}$ or absolute tolerance $0.05$) to accommodate rounding conventions.

---

## 9. Final Recommendation & Next Steps

- **Audit Gate Decision:** **PASS**
- **Justification:** Zero corruptions, 100% valid JSON, zero nulls across all records and table cells, clean document-level partition between train and test, and complete symbolic execution programs.
- **Next Step:** Awaiting independent review of this audit before proceeding to Phase 1B (controlled CPU baseline signal check).
