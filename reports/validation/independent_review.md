# Independent Review — Phase 0 HVAC Dataset Audit

**Review date:** 2026-10-10  
**Reviewed commit:** [d66f4431dfa077dcf9d4ae6e7b7051493a1db353](https://github.com/nayanojwal0810/project_3/commit/d66f4431dfa077dcf9d4ae6e7b7051493a1db353)  
**Decision:** Keep the BuildingOps/HVAC problem direction as a candidate. Do **not** approve the 2019 OEDI archive as the final modeling dataset yet.

## What looks good
- The audit inspected all six CSV files in the downloaded archive and recorded the archive hash and inventory.
- The raw data was not pushed to the repository; the GitHub tree contains reports/scripts rather than the archive.
- The discovered RTU label defect is supported by the official inventory PDF's table listing seven unfaulted dates: https://data.openei.org/files/910/lbnldatasynthesisinventory.pdf
- The official dataset page identifies this as an LBNL-led public benchmark with a CC BY 4.0 license: https://data.openei.org/submissions/910

## Problems that prevent a pass
1. **Unsupported model-performance claim.** The audit report states that random row splits will produce accuracy above 99%. No model was trained in Phase 0, so this is not an observed result. Replace it with a risk statement unless an actual controlled experiment measures it.
2. **Very few independent scenarios.** Minute-level rows are not independent examples. For example, MZVAV-2-2.csv has 37,440 rows but only 26 calendar days and binary labels. That is useful for a preliminary signal check, not proof of robust generalization.
3. **Only binary labels in the CSVs.** Fault types must be reconstructed from the inventory PDF. Several fault scenarios have only one or two days, limiting defensible held-out evaluation by fault type.
4. **Label issues must not be silently patched.** RTU.csv labels every row as faulted even though the inventory identifies seven unfaulted dates. The report also flags a ground-truth discrepancy in MZVAV-2-1.csv. Preserve the raw data and track any correction as a documented derived-data transformation.
5. **Split strategy needs more thought.** Grouping only by calendar day may not prevent leakage across repeated fault scenarios, operating conditions, or related files. The split should follow fault experiment/scenario identifiers when available; a test partition must contain enough independent normal and fault cases.
6. **GenAI grounding is not established yet.** The inventory PDF explains dataset scenarios; it is not, by itself, a maintenance manual. Availability, licensing, and suitable public sources for troubleshooting instructions must be verified before building RAG. Do not assume ASHRAE or manufacturer manuals can be freely redistributed.
7. **Some helper scripts are not self-contained.** inspect_details.py and print_numeric_stats.py expect reports/validation/dataset_audit_raw.json, which was not committed. audit_pdf.py depends on an extracted local PDF. This is not a project blocker, but future reproducibility instructions should state the required local inputs.

## Better small-data candidate to inspect next
The public CSIRO Energy Systems AHU fault-detection repository documents fault-injection experiments on two AHUs in an operating office building, with eight listed fault types. Its README says the data is CC BY-SA 4.0 and describes joining timestamped fault intervals to sensor telemetry:
- Repository: https://github.com/csiro-energy-systems/ahu-fault-detection-dataset
- data/AHU9.parquet: 9,786,479 bytes (Git LFS metadata)
- data/AHU10.parquet: 7,884,660 bytes (Git LFS metadata)
- data/fault-experiments.parquet: 28,276 bytes (Git LFS metadata)

This is a **candidate for the next audit, not yet a winner**. The README says faults were introduced through BMS proxy points; describe it as fault-injection data from an operating building, not naturally occurring failures. Audit complete row coverage, class/interval counts, overlap, missingness, normal periods, and leakage before any model experiment. Respect the CC BY-SA 4.0 license and attribution terms.

Official repository README: https://github.com/csiro-energy-systems/ahu-fault-detection-dataset#readme

## Next gate
1. Keep the downloaded OEDI archive unchanged and ignored by Git.
2. Audit the complete CSIRO Parquet files locally before training. Do not commit the raw files.
3. Only if label coverage and independent fault intervals are adequate, run a minimal baseline-versus-deep-learning signal check with splits grouped by fault experiment/time interval.
4. If that fails, compare the larger official LBNL datasets; do not download them until the small-data candidate is evaluated.

**No model-performance signal has passed yet. Project approval remains pending.**
