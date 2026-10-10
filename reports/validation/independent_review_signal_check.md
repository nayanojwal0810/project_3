# Independent Review — Phase 1B CSIRO Signal Check

**Review date:** 2026-10-10  
**Reviewed experiment commit:** [dc7b38d8c99026a37be38051c91cd8d6b215c1a8](https://github.com/nayanojwal0810/project_3/commit/dc7b38d8c99026a37be38051c91cd8d6b215c1a8)

## Decision
**Fail the current project framing:** raw sensor windows -> generic binary fault detection -> CNN. The reported test results do not justify continuing this exact model approach. CSIRO is not globally rejected as a dataset, but further tuning on the same split to obtain a pass is not authorized.

## Result summary from the submitted report
- Primary test prevalence: 13.21% (650 positive windows out of 4,922).
- Logistic-regression baseline average precision: 0.1365, only 0.0044 above the test prevalence.
- 1D CNN average precision: 0.1215, below the baseline and test prevalence.
- Balanced accuracy: baseline 0.5015; CNN 0.4867.
- Event-level recall is reported as 20.14% baseline and 18.71% CNN, but this metric needs correction before reuse.
- In the post-injection background period, false-positive rates are 30.92% baseline and 8.33% CNN. Background rows are not guaranteed normal; these rates are stress-test indicators, not authoritative false-alarm rates.

## Independent code-review caveats
1. **Event IDs are overwritten for overlapping faults.** The line assigning each matched experiment ID stores only the last active experiment for each timestamp. Later event-level metrics can miss an event in a multi-fault interval, so the reported unique-event counts and event-level recall are not reliable. Window-level binary labels do remain positive when any injection is active.
2. **Sampling cadence is not explicitly checked.** The script retains bins with exactly 20 rows but does not verify every adjacent timestamp is exactly 30 seconds apart, despite the stated protocol. Add an exact cadence assertion or filter before any future reuse of these windows.
3. **The test is not an independent-unit generalization design.** Training contains normal AHU10 windows but no recorded injected-fault windows for AHU10; most AHU10 fault detection is therefore zero-shot cross-unit transfer. This is useful as a stress test but should not be pooled with same-unit temporal results as if both measure the same task. The AHU-specific results show weak performance even on AHU9.
4. **The test metric evidence still points to failure of the stated task.** The window-level primary-test average precision and balanced accuracy do not show useful discrimination, and the CNN underperforms logistic regression on the overall primary test. Correcting the two audit issues may change a subset of windows/event metrics but cannot be presumed to turn the reported result into a success.
5. **Claim boundaries:** this experiment rejects the current binary target/model framing; it does not prove all HVAC fault-diagnosis tasks or deep learning on all HVAC datasets are unworkable.

## Next decision
Do not keep tuning the current CNN to force a win. Move to data-source selection for the next candidate. The official LBNL 2022 experimental RTU data has a more controlled scenario design: 48 one-day fault cases covering three fault types at four intensities across Fall 2020, Spring 2021, Summer 2021 and Winter 2022, plus four fault-free files. The archive listing is 291 MB; this is acceptable but should not be downloaded until the plan is locked. This benchmark is experimental on a research facility with emulated loads, not occupied-building field data.

Official sources:
- Inventory and download directory: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/
- Technical documentation: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU.pdf

There is also a newer 2026 open-access collection of eight labeled AHU datasets (Figshare archive 880.3 MB, CC BY 4.0), including smaller component datasets; this may be considered in candidate research, but do not download the full 880 MB package before selecting a specific subset. Publication/data source:
- https://doi.org/10.1038/s41597-025-06179-y
- https://figshare.com/articles/dataset/Labeled_Datasets_for_Air_Handling_Units_Operating_in_Faulted_and_Fault-free_States/29297999

## Gate status
- CSIRO binary raw-sensor CNN framing: **FAIL for this project-selection gate**.
- Model-signal result: **negative; do not optimize on this same split to force a pass**.
- Candidate domain: HVAC operations may remain viable, but choose a better-defined next task/dataset.
- Overall project: **not locked**; GenAI implementation has not started.
