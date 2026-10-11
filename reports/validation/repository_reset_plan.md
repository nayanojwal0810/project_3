# Repository Reset Plan

**Status:** Plan only — no files deleted.

## User intent
Use this repository as the sole workspace for Project 3 and clean it so the project can restart with a clear, reviewed history of work.

## Safety-first reset approach
Do not delete repository files until the user confirms the intended scope of “clean everything.” A safer reset is to preserve the existing validation work in Git history or an archive branch, then make a reviewed cleanup commit on `main`.

## Current repository inventory
- `.gitignore`
- `README.md`
- `reports/validation/` — prior HVAC dataset/model audits and decision reports
- `scripts/` — prior audit and signal-check scripts

## Current documented project direction
The repository's README names the provisional project **BuildingOps AI**, an HVAC fault-detection and evidence-grounded diagnostics candidate. The latest decision rejects the previous CSIRO raw-sensor binary CNN framing because the 1D CNN did not outperform the baseline on the reported held-out test. It proposes the official LBNL experimental RTU dataset as the next candidate for minimal validation. The full project is not approved yet.

This direction conflicts with the earlier BankLens financial-document copilot shortlist. Before cleaning or deleting existing work, confirm whether BuildingOps AI is the project direction to continue or whether we are returning to BankLens.

## Proposed cleanup once scope is confirmed
1. Preserve the current state with a tag or archive branch.
2. Remove obsolete scripts and reports from the active project tree only after reviewing each path.
3. Retain or rewrite `.gitignore` so raw datasets, environment files, credentials, model weights and generated artifacts remain excluded.
4. Rewrite `README.md` to document the confirmed candidate and current validation stage.
5. Keep only necessary project decisions, data provenance, validation code and reports.
6. Commit cleanup with a clear message; do not force-push or rewrite history unless explicitly requested.

## Current state
No files have been deleted or overwritten as part of this plan.
