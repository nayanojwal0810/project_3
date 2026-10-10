# Independent Review — CSIRO Audit Correction (Phase 1A.1)

**Review date:** 2026-10-10  
**Reviewed commit:** [2552b38bae49c02761085c64139390a7418042c8](https://github.com/nayanojwal0810/project_3/commit/2552b38bae49c02761085c64139390a7418042c8)  
**Decision:** Accept the corrected report as a useful data-quality audit with caveats. The CSIRO dataset remains a leading candidate for a controlled signal check, but this is not approval for model training or for the whole project.

## Fixes that are supported by code and report
- Raw fault type counts include the three missing labels, reconciling 276 named plus 3 missing = 279 experiments in the AHU9/AHU10 sensor windows.
- Overlap detection now checks all experiment pairs on each AHU, rather than only adjacent intervals.
- Sensor-to-fault mapping uses half-open intervals [start, end), preserves multiple matched experiments per timestamp, and asserts the row partitions reconcile.
- The report now correctly calls timestamps timezone-naive and defines observations outside recorded injection intervals as outside those windows, not guaranteed fault-free.
- The report acknowledges injection coverage is concentrated in May–November 2013, despite the telemetry's longer timestamp range.

## Remaining caveats before a signal-check design
1. **Explanation of old count mismatch is not fully convincing.** The report says 41,618 versus 40,055 differed due to inclusive boundaries, overlapping labels overwritten, and missing-label experiments. Those totals are not directly comparable unless the exact previous counting operation and excluded rows are defined. The corrected half-open row partitions do reconcile: 37,020 single-match rows + 4,561 multi-match rows = 41,581 injection-window rows; plus 838,241 outside-window rows = 879,822 total rows. Use only the corrected definitions going forward.
2. **“Clean rows” and “clean experiments” are different sets.** The 37,020 rows are timestamps with exactly one active experiment, and include 1,560 rows whose fault type is missing plus rare/unusable fault types. They are not all eligible for single-label supervised training. The proposed five-class rows total 31,055 before any additional filtering. The signal-check code must explicitly filter to its target classes and publish counts after filtering.
3. **Single-label support is limited.** Three classes have 20–42 non-overlapping runs (RA Damper Stuck Open 42, SA Fan Belt Slip 36, HW Valve Proxy Stuck Open 30, Zone Average Temp Drift 22, OA Damper Stuck Open 20). Counts are candidate-level support, not a promise of robust performance. The HW Valve Proxy class has only one clean AHU10 experiment, so cross-AHU generalization for that class is not supported.
4. **A group split by fault experiment alone is insufficient for every row.** Positive rows belong to fault experiments, but most outside-window rows do not. For validation, keep complete time blocks together, keep each fault event and its nearby transition/buffer in one split, and ensure a split cannot place adjacent/overlapping windows from the same time block in train and test. Measure how many independent events and time blocks land in each partition.
5. **Negative label must remain carefully named.** The achievable label is “inside a documented fault-injection interval” versus “outside documented fault-injection intervals.” It is not proof of general real-world anomaly detection or guaranteed-normal telemetry.
6. **Duplicate sensor column needs provenance review.** Exact equality of ahuMaTemp and ahuSaTemp is credible from the audit, but do not simply conclude which one should be dropped. Record this as a redundant channel and test/explain the practical feature choice.
7. **The report says “single-fault” for every exactly-one matched interval.** That only means one documented experiment interval matched a timestamp; it does not prove other unrecorded faults were absent. Keep the wording bounded to recorded experiments.

## Dataset selection decision
**Keep CSIRO as the current lead. Do not switch domains.** The corrected audit shows enough independent events for a small, carefully grouped experiment on a subset of fault classes. However, because class support is modest and injection windows are temporally concentrated, first compare the official LBNL 2022 RTU dataset before locking a dataset or starting model experiments.

Official LBNL RTU documentation: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU.pdf

Correction to earlier informal summary: the official 2022 RTU documentation describes (a) experimental RTU data with 48 faulted cases and 4 fault-free cases, (b) field-measured data with two fault cases and corresponding baselines, and (c) simulated RTU data with 24 faulted cases plus a baseline. Do not describe this source as a confirmed “74 CSV / 10 fault types” dataset without verifying the current archive and inventory.

## Next gate
Run a **selection comparison only** against official LBNL RTU data:
- use the official source and documentation;
- inspect archive size/member manifest and scenario inventory only initially;
- do not download unless the manifest and licence/terms support proceeding;
- compare independent scenario count, label clarity, normal-baseline design, season coverage, simulation vs field/experimental status, CPU feasibility, and leakage-resistant validation options;
- choose one dataset before writing any model-training script.

**Status: CSIRO = promising lead; corrected Phase 1A.1 audit = accepted with caveats; model-signal validation = not run; project = not locked.**
