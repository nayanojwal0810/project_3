# Next Candidate Decision After CSIRO Signal Check

**Date:** 2026-10-10  
**Decision:** Reject the current CSIRO raw-sensor binary CNN framing. Advance the LBNL 2022 experimental RTU dataset as the next candidate for minimal model-signal validation. The full BuildingOps AI project remains unapproved.

## Why the CSIRO framing is rejected
The submitted primary-test results show average precision of 0.1365 for logistic regression versus 0.1215 for the 1D CNN, at test prevalence 0.1321. Balanced accuracy is approximately 0.50 for both, and the CNN is worse overall. This is not a convincing signal for a resume project whose core promise is deep learning.

Independent code review also identified two implementation gaps: sample cadence is not explicitly checked, and the experiment ID array overwrites overlapping event IDs. Those invalidate the reported event-level metrics and mean that the claimed full evaluation-validity pass is too strong. The window-level results still indicate that this particular binary task/model combination has weak performance; do not tune the same split repeatedly to force a pass.

## Next dataset candidate: official LBNL 2022 experimental RTU subset
The official documentation describes:
- 48 one-day fault cases and four fault-free case files.
- Three fault types: outdoor-air damper stuck, incorrect economizer setpoint, and supply-air-temperature sensor bias.
- Four intensity levels for each fault type.
- Repeated scenarios across Fall 2020, Spring 2021, Summer 2021, and Winter 2022.
- One-minute data and 56 RTU/VAV data points.
- Fault-free files contain multiple days within each season; each faulted CSV contains one day for a specific fault intensity in a single season.
- Data are from a research facility at Oak Ridge National Laboratory with emulated internal loads, not an occupied office building.

This provides a much cleaner independent-case split than treating every 30-second CSIRO sensor row as a separate example. The natural validation design is hold out a complete season (including its fault and fault-free cases), and compare a light baseline against a small deep model on the same windows. Still run a data/schema audit first; do not assume the dataset is clean or that a model will pass.

## Source and size
- Official RTU download directory: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/
- Technical documentation: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU.pdf
- Directory listing reports the RTU ZIP as 291 MB and the all-three archive as 293 MB.
- PDF size: approximately 1.6 MB.

## Alternative noted, not selected yet
A 2026 open-access paper releases eight labeled AHU datasets via Figshare under CC BY 4.0. The full collection is 880.3 MB, with smaller subsets including RBC-Nesbitt (15.2 MB, real-building data, 20 described fault cases) and other datasets. This may be revisited if the LBNL RTU signal check fails:
- Paper: https://doi.org/10.1038/s41597-025-06179-y
- Data: https://figshare.com/articles/dataset/Labeled_Datasets_for_Air_Handling_Units_Operating_in_Faulted_and_Fault-free_States/29297999

## Next gate
1. Download only the official LBNL RTU archive.
2. Inspect the archive inventory, file naming, data sizes, per-season case counts, missingness, and licenses/attribution before model work.
3. If data layout supports one clean case per file and a held-out-season design, run one minimal baseline-vs-small-CNN signal check.
4. If the deep model again fails to add value, reject the candidate instead of repeatedly tuning it.

No LBNL data have been downloaded, and no new model has been trained.