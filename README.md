# Project 3 — BuildingOps AI

**Status:** Candidate under validation. This is not yet a locked project.

## Goal
Evaluate whether an HVAC fault-detection and diagnostics dataset can support a resume-worthy application combining a properly evaluated deep-learning fault model, evidence-grounded GenAI troubleshooting using technical documentation, and a path to an API-based, testable and deployable application.

## Current phase
**Phase 0: dataset validation only.** Do not implement the product, train a production model, build RAG, create an application UI, or add speculative features yet.

## Validation principles
1. Inspect the complete locally available dataset, not a random sample, for file structure, schema, labels, missingness, class balance, duplicates, and likely data leakage.
2. Do not claim results unless they were actually computed. Record exact commands, environment, and output summaries.
3. Separate facts observed in the files from assumptions and recommendations.
4. Establish a simple baseline before proposing a deep-learning model. Use split strategies that prevent leakage across related records or operating conditions when the dataset structure requires it.
5. Do not decide pass/fail from accuracy alone. Consider class imbalance, per-class performance, data leakage, usable labels, and CPU/GPU/runtime constraints.
6. GenAI feasibility requires identifiable technical documents and a defensible way to connect diagnostic labels to evidence. Do not invent manuals or fault-to-symptom mappings.
7. Never commit raw datasets, secrets, API keys, credentials, large model files, or private local paths. Keep raw data under `data/raw/` and ignore it in Git.
8. Use small, inspectable reports. If a task needs substantial compute or long output, print the exact command and STOP for the user to run it.
9. Do not install packages, run downloads, run expensive experiments, or change files outside the requested scope without asking.
10. Do not trust an agent-generated conclusion without checking its supporting evidence.

## Expected validation outputs
- Dataset inventory and provenance record.
- Schema and label audit.
- Data-quality and leakage-risk report.
- A feasibility recommendation with explicit blockers and unresolved questions.
- No model training unless separately approved after the data audit.

## Dataset provenance
Candidate source: Open Energy Data Initiative / Lawrence Berkeley National Laboratory, Building Fault Detection and Diagnostics data.
Official page: https://data.openei.org/submissions/910

Before using or redistributing the data, verify that the downloaded archive is the intended file and record the source, license, and any attribution requirements from the official page.

## Repository workflow
- Commit small, meaningful changes after review.
- Do not commit raw data or generated large artifacts.
- Use clear commit messages.
- Treat `main` as the source of reviewed work.
