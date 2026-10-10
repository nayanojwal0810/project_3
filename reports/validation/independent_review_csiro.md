# Independent Review — CSIRO AHU Dataset Audit

**Review date:** 2026-10-10  
**Reviewed audit commit:** [c612ecac9099780c85dffcbaf944120ed273d73a](https://github.com/nayanojwal0810/project_3/commit/c612ecac9099780c85dffcbaf944120ed273d73a)  
**Decision:** The dataset is a promising candidate for a small, controlled signal check, but the Phase 1A report and label-mapping implementation need corrections before we treat its counts as reliable. No modeling is approved yet.

## What is supported
- The three Parquet files match the source repository's listed file sizes and passed PAR1 header/trailer checks in the submitted audit.
- The telemetry has 457,653 rows for AHU9 and 422,169 rows for AHU10, and the experiment table contains 391 records according to the audit.
- The source README states that faults were intentionally inserted into the BMS of an operating office building between April and November 2013, using proxy points to override controls or sensor values. Therefore, these are fault-injection experiments on operational equipment—not a dataset of naturally occurring failures. Source: https://github.com/csiro-energy-systems/ahu-fault-detection-dataset
- The reported exact equality between ahuMaTemp and ahuSaTemp needs investigation; do not assume which signal is correct. Exclude one only after the duplicate channel and its provenance are documented.

## Corrections required before Phase 1B

1. **Fault counts do not reconcile.** The report lists 279 usable experiments, but its nine per-type counts sum to 276. The per-type sensor-row counts sum to 40,055 while the stated union of fault-labeled sensor rows is 41,618. Report the omitted/unknown records explicitly and reconcile every count before using class balance or class support in decisions.
2. **Overlapping-pair counting is incomplete.** scripts/audit_csiro_dataset.py compares only adjacent intervals after sorting by start time. That can miss nested or long intervals overlapping multiple later intervals. Replace this with a correct all-pairs or sweep-line interval-overlap method, and report both overlapping experiment pairs and unique sensor timestamps covered by two or more experiments.
3. **Overlapping labels are silently overwritten.** The script initially sets rows to Normal, then iterates over experiments and overwrites assigned_fault on every match. Rows in concurrent faults therefore receive whichever fault is processed last. Do not use those single-label class counts. Preserve multi-label sets/counts and separately define a clean single-fault subset only if justified.
4. **Interval convention differs from the published join.** The source repository's join_ground_truth() uses Datetime >= start and Datetime < end; the audit script currently uses Datetime <= end. Adopt the half-open interval [start, end) and test boundary cases.
5. **Missing fault categories are not reported clearly.** value_counts() excludes null Fault Type values by default, while label assignment substitutes Unknown_Fault. Explicitly count null/blank/unknown types, invalid labels, and experiments not represented in the listed category table.
6. **Timezone claim is unsupported.** The report labels the indexes UTC, but the source conversion uses pd.to_datetime(..., unit='D') without assigning a timezone. Report whether timestamps are timezone-aware; if they are naive, write “timezone unspecified” rather than “UTC”.
7. **Normal is a target assumption.** Rows outside documented injected-fault intervals are outside recorded injection windows. They are not proven to be free of naturally occurring or unrecorded faults. Use this exact target definition in reports and experiments.
8. **Do not call the telemetry continuous.** The files span roughly two calendar years, but the audit reports thousands of gaps and repeated readings. Say “two-year timestamp span with sampling gaps”, not “continuous two-year telemetry”.
9. **Seasonal generalization is not established.** The source says fault injection occurred April–November 2013, although the telemetry spans into 2015. A model cannot be claimed to generalize fault detection across two years/four seasons merely because normal/background records span that period.
10. **The report overstates comparative quality.** Replace phrases such as “exponentially higher quality” with a narrower statement: CSIRO has more structured fault-injection metadata than the LBNL archive reviewed, but still has label ambiguities, overlaps, and only two sensor-equipped AHUs.

## Required next gate — still no model training
Update the audit script and report, then rerun the complete inexpensive audit. Required outputs:
- Reconciled total experiment counts and counts per raw Fault Type, including null/unknown categories.
- Half-open interval joins and tests for exact start/end boundaries.
- Correct overlap-pair count (including nested intervals), count of unique overlapping sensor timestamps, and multi-label distribution.
- Count of valid, non-overlapping single-fault experiments per type after removing ambiguous intervals.
- Coverage table by month/week and AHU, separating known injected-fault windows from all other observations.
- Explicit timestamp timezone status.
- A repeatable check that listed per-type counts and per-class row totals reconcile to source totals.

Only after this report is corrected should we decide whether to run a minimal binary baseline-versus-deep-learning signal check. If the corrected data cannot support leakage-resistant evaluation, stop and reconsider the dataset/task.

## Scope and approval
- Do not edit or overwrite the raw Parquet files.
- Do not build the application or RAG yet.
- Do not claim deep learning will outperform simpler methods without evidence.
- Project direction: still a candidate. Dataset adoption is conditional, and model-signal validation has not passed.
