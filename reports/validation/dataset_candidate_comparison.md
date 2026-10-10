# Candidate Comparison — CSIRO AHU vs. LBNL RTU

**Date:** 2026-10-10  
**Purpose:** Choose the dataset to take into the minimal model-signal validation gate. This does not approve the whole BuildingOps AI project.

## Decision
**Advance CSIRO to the signal-validation gate. Do not download the 291 MB LBNL RTU archive yet.** CSIRO better fits our current constraints: small local files, structured event intervals, many repeated fault-injection runs, and manageable audit complexity. Keep LBNL as a documented alternative if CSIRO fails its model-signal check.

## Evidence-based comparison

| Criterion | CSIRO AHU dataset | LBNL RTU data package | Assessment |
|---|---|---|---|
| Data footprint | Three Parquet files ~17.7 MB combined | Official RTU ZIP directory lists 291 MB, and an all-three archive of 293 MB | CSIRO easier for limited time/storage |
| Target labels | 391 event records; 279 experiments intersect the AHU9/AHU10 sensor spans; 3 in-window rows have missing fault type; overlaps need explicit treatment | Labels/scenarios documented by file in separate experimental, field and simulation collections | Both need careful split design; CSIRO interval labels are already audited locally |
| Independent fault support | 178 non-overlapping experiment records in the two sensor windows; five named classes have 20–42 such experiments | Experimental subset: 48 faulted cases and 4 fault-free cases; field subset: two fault cases and corresponding baselines; simulated subset: 24 faulted cases plus one baseline | LBNL has different data sources, but they should not be casually merged as equivalent observations |
| Physical context | Faults injected into BMS proxy points on two AHUs in an operating office building | Experimental RTU uses a research platform with emulated loads; field subset has two fault types/sites; simulation includes six fault types at multiple intensities | CSIRO is a practical balance of operating equipment and multiple recorded fault events |
| Temporal structure | About two-year sensor timestamp spans with gaps, but injected faults concentrated May–November 2013 | Experimental cases represent single-day fault runs across four seasonal periods; simulated faults persist through 100-day simulations | Both risk scenario/time leakage; LBNL simulation can be especially misleading under random row splits |
| Deep-learning signal feasibility | Plausible for binary injected-fault-window detection and a restricted fault-class task, provided tests hold out complete time blocks and events | Plausible, but separate experimental/simulated/field domains and baseline structure need distinct evaluation plans | CSIRO simpler for the first small signal test |
| GenAI grounding | Metadata includes descriptions and magnitude, but not maintenance procedures | Documentation provides detailed equipment/control sequence and fault scenarios, but not necessarily a freely redistributable maintenance SOP corpus | Neither dataset alone is enough for evidence-grounded maintenance advice |
| Execution risk | Low storage, no extra Parquet dependency needed in the audited environment | More data to download/extract and several distinct sub-datasets to audit | CSIRO preferred |

## Verified LBNL source facts
The official 2022 RTU directory lists:
- LBNL_FDD_Data_Sets_RTU.zip: 291 MB
- LBNL_FDD_Data_Sets_RTU_all_3.zip: 293 MB
- LBNL_FDD_Data_Sets_RTU.pdf: 1.6 MB

The official RTU documentation states:
- Experimental RTU data: 48 faulted cases and 4 fault-free cases. Each fault case is a one-day case; the test periods cover Fall 2020, Spring 2021, Summer 2021 and Winter 2022.
- Field-measured RTU data: one fault case at each of two sites, paired with site-specific unfaulted periods.
- Simulated RTU data: 24 files representing six fault types at different intensities, each based on a 100-day simulation, plus one unfaulted baseline.

Sources:
- Official RTU directory: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/
- Official RTU documentation: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU.pdf
- CSIRO repository documentation: https://github.com/csiro-energy-systems/ahu-fault-detection-dataset

## Conditions on advancing CSIRO
1. The first signal check must use the task label “inside a documented fault-injection interval” versus “outside documented fault-injection intervals,” not “faulty vs guaranteed normal.”
2. The single-label fault-class experiment must exclude the three missing-type events and all rows with overlapping fault intervals.
3. Use only the strongest class subset for which clean independent event counts are adequate; do not claim robust multiclass performance from a small validation set.
4. Split by non-overlapping time blocks as well as keeping complete fault events and nearby transitions/buffers in one partition. Fault-event grouping alone is insufficient because the background rows have no event ID.
5. Avoid using raw timestamps or split-correlated identifiers as predictive features.
6. Compare at least one simple baseline against one modest deep-learning model; publish per-class metrics, PR-AUC for the imbalanced binary task, and event/block-level uncertainty. Do not use accuracy alone.
7. Keep the LBNL archive as a backup; do not download it unless CSIRO gives no credible signal or the later architecture needs cross-benchmark evaluation.

## Status
**Dataset candidate for signal check: CSIRO.**  
**Final project approval: pending model-signal evidence.**  
No model has been trained and no performance claims are made.
