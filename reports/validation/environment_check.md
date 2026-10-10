# Environment Check Report: HVAC Dataset Feasibility Audit

**Audit Date:** 2026-10-10  
**Auditor:** Automated Data-Audit Engine (Phase 0)  
**Project Workspace:** `D:\project-3`  
**GitHub Repository:** `nayanojwal0810/project_3`  

---

## 1. Observed Facts

### 1.1 Working Directory and Workspace Context
- **Current Working Directory (CWD):** `D:\project-3`
- **Initial Workspace State:**
  - Workspace directory initially contained the downloaded raw archive `hvac_fdd_benchmark.zip` (size: 7,010,416 bytes) at root level.
  - Subdirectory `data/raw/` was created, and the archive was placed at `data/raw/hvac_fdd_benchmark.zip` while preserving the original root archive.
- **Archive Path & Exact File Metrics:**
  - Expected Path: `data/raw/hvac_fdd_benchmark.zip`
  - Existence: Verified (`True`)
  - Size: `7,010,416 bytes` (6.69 MiB / 7.01 MB)
  - SHA-256 Hash: `68c58568e3f0e4e7d0f0de3194a2ce7ca80703c057325ee402a94d3eab5a76c1`

### 1.2 Git Environment & Repository Status
- **Git Version:** `2.55.0.windows.3`
- **Initial Git Status:**
  - The local workspace folder `D:\project-3` initially did not contain a `.git` directory (`fatal: not a git repository`).
  - System-wide search confirmed no separate local clone of `project_3` existed on disks `C:` or `D:`.
- **Remote Repository Connection:**
  - Remote URL verified: `https://github.com/nayanojwal0810/project_3.git`
  - Upstream Head Commit: `07286844c5c21e5404c73254d278f42e65e5a84d` (`chore: ignore local datasets, secrets, and generated artifacts`)
  - Local repository initialized and attached to remote `origin`:
    - Branch: `main` tracking `origin/main`
    - Commit SHA: `07286844c5c21e5404c73254d278f42e65e5a84d`
- **Git Ignore Verification:**
  - `.gitignore` tracked from upstream repo explicitly ignores:
    - `data/raw/`
    - `data/interim/`
    - `data/processed/`
    - `*.zip`, `*.7z`, `*.tar`, `*.tar.gz`
    - `artifacts/`, `checkpoints/`, `models/`
  - Clean working tree verification: neither `hvac_fdd_benchmark.zip` nor any files under `data/` appear in `git status` untracked file listings.

### 1.3 Execution Runtime Environment
- **Operating System:** Windows 11 Home / PowerShell
- **Python Version:** Python 3.13.3
- **Auditing Libraries Available:**
  - `pandas`: 3.0.3
  - `numpy`: 2.4.6
  - `pypdf`: Installed and functional
  - `zipfile`, `hashlib`, `os`, `json`: Standard library

---

## 2. Interpretations
- The archive downloaded by the user matches the published Lawrence Berkeley National Laboratory (LBNL) Building Fault Detection and Diagnostics (AFDD) benchmark submission on the Open Energy Data Initiative (OEDI submission 910).
- The repository `.gitignore` is properly configured to prevent accidental staging or committing of raw archives, extracted interim tabular data, or generated models.

---

## 3. Unknowns
- Whether GitHub push authentication over HTTPS (`credential.helper=manager`) requires interactive token refresh for write permissions to `nayanojwal0810/project_3`.

---

## 4. Recommendations
1. Maintain strict `.gitignore` enforcement: never run `git add -f` on any files inside `data/`.
2. Keep raw archive `data/raw/hvac_fdd_benchmark.zip` read-only and preserved for full provenance reproducibility.
