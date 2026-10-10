import os
import sys
import json
import pandas as pd
import numpy as np

EXPECTED_FILES = {
    "AHU9.parquet": 9786479,
    "AHU10.parquet": 7884660,
    "fault-experiments.parquet": 28276
}

def verify_file_signatures(data_dir="data/raw/csiro"):
    print("--- 1. File & Parquet Signature Verification ---")
    results = {}
    missing = []
    
    for filename, expected_size in EXPECTED_FILES.items():
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            missing.append(filename)
            continue
        
        actual_size = os.path.getsize(path)
        with open(path, "rb") as f:
            head = f.read(4)
            f.seek(0)
            prefix = f.read(100)
            f.seek(-4, os.SEEK_END)
            tail = f.read(4)
            
        is_lfs = prefix.startswith(b"version https://git-lfs.github.com/spec/v1")
        is_valid_parquet = (head == b"PAR1" and tail == b"PAR1")
        
        results[filename] = {
            "path": path,
            "actual_size": actual_size,
            "expected_size": expected_size,
            "size_match": (actual_size == expected_size),
            "head": head.decode("latin1", errors="replace"),
            "tail": tail.decode("latin1", errors="replace"),
            "is_lfs": is_lfs,
            "is_valid_parquet": is_valid_parquet
        }
        print(f"File: {filename:26} | Size: {actual_size:10,} bytes (Expected: {expected_size:10,}) | Valid PAR1: {is_valid_parquet} | Is LFS: {is_lfs}")

    if missing:
        print(f"ERROR: Missing expected files: {missing}")
        return None, missing
    
    for fname, r in results.items():
        if r["is_lfs"]:
            print(f"ERROR: {fname} is a Git LFS pointer, not a real Parquet file!")
            return None, ["LFS pointer detected"]
        if not r["is_valid_parquet"]:
            print(f"ERROR: {fname} does not have valid PAR1 magic header/trailer!")
            return None, ["Invalid Parquet signature"]
            
    return results, []

def check_dependencies():
    print("\n--- 2. Dependency Check ---")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Pandas version: {pd.__version__}")
    parquet_engine = None
    try:
        import pyarrow
        print(f"PyArrow version: {pyarrow.__version__}")
        parquet_engine = "pyarrow"
    except ImportError:
        try:
            import fastparquet
            print(f"fastparquet version: {fastparquet.__version__}")
            parquet_engine = "fastparquet"
        except ImportError:
            print("ERROR: Neither pyarrow nor fastparquet is installed!")
            print("To fix, run: pip install pyarrow")
            return None
    return parquet_engine

def inspect_sensor_dataset(file_path):
    filename = os.path.basename(file_path)
    print(f"\n=======================================================")
    print(f"Inspecting Sensor Dataset: {filename}")
    df = pd.read_parquet(file_path)
    
    n_rows, n_cols = df.shape
    cols = df.columns.tolist()
    
    # Identify index and timestamp timezone
    index_name = df.index.name
    index_is_dt = isinstance(df.index, pd.DatetimeIndex)
    if index_is_dt:
        dt_series = df.index
        tz_status = "timezone unspecified (naive)" if dt_series.tz is None else str(dt_series.tz)
        ts_min = dt_series.min()
        ts_max = dt_series.max()
        ts_unique = dt_series.nunique()
        duplicate_ts = n_rows - ts_unique
        is_monotonic = dt_series.is_monotonic_increasing
        # Time differences / sampling frequency
        time_diffs = dt_series.to_series().diff().dropna()
        median_freq = time_diffs.median()
        mode_freq = time_diffs.mode().iloc[0] if len(time_diffs.mode()) > 0 else None
        large_gaps = int((time_diffs > (median_freq * 5)).sum())
    else:
        tz_status = "none"
        ts_min, ts_max, duplicate_ts, is_monotonic, median_freq, mode_freq, large_gaps = (None, None, 0, False, None, None, 0)
    
    # Missing values
    missing_counts = df.isnull().sum()
    missing_summary = {c: {"count": int(missing_counts[c]), "pct": float(missing_counts[c] / n_rows * 100)} for c in cols if missing_counts[c] > 0}
    
    # Duplicate rows (consecutive steady-state identical sensor vectors)
    n_duplicates = int(df.duplicated().sum())
    
    # Check MaTemp vs SaTemp identity
    matemp_col = next((c for c in cols if "matemp" in c.lower()), None)
    satemp_col = next((c for c in cols if "satemp" in c.lower() and "sp" not in c.lower()), None)
    is_matemp_satemp_identical = False
    if matemp_col and satemp_col:
        is_matemp_satemp_identical = bool((df[matemp_col] == df[satemp_col]).all())

    # Constant and near-constant columns
    constant_cols = []
    near_constant_cols = []
    for c in cols:
        vc = df[c].value_counts(dropna=False)
        top_pct = float(vc.iloc[0] / n_rows * 100) if len(vc) > 0 else 0.0
        n_unq = int(df[c].nunique(dropna=False))
        if n_unq <= 1:
            constant_cols.append({"column": c, "unique": n_unq, "top_pct": top_pct, "val": str(vc.index[0]) if len(vc) > 0 else None})
        elif top_pct >= 99.0:
            near_constant_cols.append({"column": c, "unique": n_unq, "top_pct": top_pct, "top_val": str(vc.index[0])})

    # Numeric summaries
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_summaries = {}
    for c in numeric_cols:
        s = df[c].dropna()
        n_inf = int(np.isinf(s).sum()) if len(s) > 0 else 0
        numeric_summaries[c] = {
            "min": float(s.min()) if len(s) > 0 else None,
            "max": float(s.max()) if len(s) > 0 else None,
            "mean": float(s.mean()) if len(s) > 0 else None,
            "std": float(s.std()) if len(s) > 0 else None,
            "inf_count": n_inf,
            "zero_count": int((s == 0).sum())
        }

    print(f"Rows: {n_rows:,} | Columns: {n_cols}")
    print(f"Timestamp range: {ts_min} to {ts_max} ({tz_status}) | Monotonic: {is_monotonic} | Duplicate TS: {duplicate_ts}")
    print(f"Sampling Frequency: Median={median_freq}, Mode={mode_freq}, Large Gaps (>2.5 min): {large_gaps}")
    print(f"Repeated identical rows (steady-state): {n_duplicates:,} ({n_duplicates/n_rows*100:.2f}%)")
    print(f"Missing cells: {len(missing_summary)} / {n_cols}")
    print(f"MaTemp == SaTemp exact identity: {is_matemp_satemp_identical}")
    
    return {
        "file_name": filename,
        "n_rows": n_rows,
        "n_cols": n_cols,
        "index_name": str(index_name),
        "tz_status": tz_status,
        "ts_min": str(ts_min),
        "ts_max": str(ts_max),
        "is_monotonic": bool(is_monotonic),
        "duplicate_ts": int(duplicate_ts),
        "sampling_median": str(median_freq),
        "sampling_mode": str(mode_freq),
        "large_gaps": large_gaps,
        "columns": cols,
        "dtypes": {c: str(df[c].dtype) for c in cols},
        "missing_summary": missing_summary,
        "duplicate_rows": n_duplicates,
        "is_matemp_satemp_identical": is_matemp_satemp_identical,
        "constant_cols": constant_cols,
        "near_constant_cols": near_constant_cols,
        "numeric_summaries": numeric_summaries
    }

def audit_fault_experiments(file_path):
    print(f"\n=======================================================")
    print(f"Auditing Fault Experiments Table: {os.path.basename(file_path)}")
    df = pd.read_parquet(file_path)
    
    total_experiments = len(df)
    cols = df.columns.tolist()
    
    # Check timezone of experiment timestamps
    start_tz = "timezone unspecified (naive)" if df["Start Datetime"].dt.tz is None else str(df["Start Datetime"].dt.tz)
    end_tz = "timezone unspecified (naive)" if df["End Datetime"].dt.tz is None else str(df["End Datetime"].dt.tz)
    
    # Raw Fault Type counts INCLUDING nulls
    raw_fault_type_counts = df["Fault Type"].value_counts(dropna=False).to_dict()
    # Replace nan key with string for clean presentation
    raw_fault_types_reconciled = {}
    for k, v in raw_fault_type_counts.items():
        key_str = "<Missing / NaN>" if pd.isna(k) else str(k)
        raw_fault_types_reconciled[key_str] = int(v)
        
    # Durations
    df["duration"] = df["End Datetime"] - df["Start Datetime"]
    min_duration = df["duration"].min()
    max_duration = df["duration"].max()
    median_duration = df["duration"].median()

    null_fault_type_rows = df[df["Fault Type"].isna()]
    n_null_fault_types = len(null_fault_type_rows)

    # Breakdown by AHU
    by_ahu = df["AHU"].value_counts().to_dict()
    by_ahu = {int(k): int(v) for k, v in by_ahu.items()}

    
    # Validity checks
    invalid_times = df[df["End Datetime"] <= df["Start Datetime"]]
    missing_times = df[df["Start Datetime"].isnull() | df["End Datetime"].isnull()]
    duplicate_records = int(df.duplicated().sum())
    
    # ALL-PAIRS Overlap Detection (both half-open and closed)
    # Check all pairs (i, j) with i < j on the same equipment
    overlapping_pairs_half_open = []
    overlapping_pairs_closed = []
    
    # Track overlapping experiment indices
    exp_indices_with_overlap = set()
    
    for ahu_id in df["AHU"].unique():
        sub = df[df["AHU"] == ahu_id].copy().reset_index()
        n_sub = len(sub)
        for i in range(n_sub):
            s_i, e_i = sub.loc[i, "Start Datetime"], sub.loc[i, "End Datetime"]
            orig_idx_i = int(sub.loc[i, "index"])
            for j in range(i + 1, n_sub):
                s_j, e_j = sub.loc[j, "Start Datetime"], sub.loc[j, "End Datetime"]
                orig_idx_j = int(sub.loc[j, "index"])
                
                # Half-open: max(start) < min(end)
                if max(s_i, s_j) < min(e_i, e_j):
                    overlapping_pairs_half_open.append({
                        "ahu": int(ahu_id),
                        "exp1_idx": orig_idx_i,
                        "exp1_fault": str(sub.loc[i, "Fault Type"]),
                        "exp1_start": str(s_i),
                        "exp1_end": str(e_i),
                        "exp2_idx": orig_idx_j,
                        "exp2_fault": str(sub.loc[j, "Fault Type"]),
                        "exp2_start": str(s_j),
                        "exp2_end": str(e_j),
                        "overlap_span": str(min(e_i, e_j) - max(s_i, s_j))
                    })
                    exp_indices_with_overlap.add(orig_idx_i)
                    exp_indices_with_overlap.add(orig_idx_j)
                    
                # Closed: max(start) <= min(end)
                if max(s_i, s_j) <= min(e_i, e_j):
                    overlapping_pairs_closed.append((orig_idx_i, orig_idx_j))
                    
    df["has_overlap_half_open"] = df.index.isin(exp_indices_with_overlap)
    
    print(f"Total Experiments: {total_experiments}")
    print(f"Timestamp Timezone: Start={start_tz}, End={end_tz}")
    print(f"Experiments by AHU: {by_ahu}")
    print(f"Raw Fault Types (including nulls): {raw_fault_types_reconciled}")
    print(f"Missing / NaN Fault Type experiments: {n_null_fault_types}")
    print(f"Durations: Min={min_duration}, Max={max_duration}, Median={median_duration}")
    print(f"Invalid Start/End: {len(invalid_times)} | Duplicates: {duplicate_records}")
    print(f"All-Pairs Overlapping Pairs (Half-Open [start, end)): {len(overlapping_pairs_half_open)}")
    print(f"All-Pairs Overlapping Pairs (Closed [start, end]): {len(overlapping_pairs_closed)}")
    print(f"Total experiments involved in half-open overlaps: {len(exp_indices_with_overlap)}")
    
    # Assert reconciliation
    assert sum(raw_fault_types_reconciled.values()) == total_experiments, "Fault type sum must equal total experiments"
    assert sum(by_ahu.values()) == total_experiments, "AHU sum must equal total experiments"
    
    return {
        "total_experiments": total_experiments,
        "start_tz": start_tz,
        "end_tz": end_tz,
        "by_ahu": by_ahu,
        "raw_fault_types": raw_fault_types_reconciled,
        "null_fault_type_experiments": [
            {
                "index": int(idx),
                "ahu": int(row["AHU"]),
                "fault_name": str(row["Fault Name"]),
                "start": str(row["Start Datetime"]),
                "end": str(row["End Datetime"]),
                "duration": str(row["duration"])
            }
            for idx, row in null_fault_type_rows.iterrows()
        ],
        "durations": {
            "min": str(min_duration),
            "max": str(max_duration),
            "median": str(median_duration)
        },
        "all_pairs_overlapping_pairs_half_open": len(overlapping_pairs_half_open),
        "all_pairs_overlapping_pairs_closed": len(overlapping_pairs_closed),
        "overlapping_pairs_list": overlapping_pairs_half_open,
        "experiments_with_overlap_count": len(exp_indices_with_overlap),
        "clean_experiments_count": total_experiments - len(exp_indices_with_overlap),
        "df": df
    }

def evaluate_half_open_mapping(sensor_files, exp_audit):
    print(f"\n=======================================================")
    print(f"Evaluating Sensor-to-Fault Mapping via Half-Open Intervals [start, end)")
    exp_df = exp_audit["df"]
    
    mapping_results = {}
    
    for s_file in sensor_files:
        fname = os.path.basename(s_file)
        ahu_key = 9 if "9" in fname else 10
        print(f"\nMapping for {fname} (Target AHU: {ahu_key})...")
        s_df = pd.read_parquet(s_file)
        dt_idx = s_df.index
        n_sensor_rows = len(s_df)
        
        # Experiments for this AHU
        ahu_exps = exp_df[exp_df["AHU"] == ahu_key].copy().reset_index()
        s_start, s_end = dt_idx.min(), dt_idx.max()
        
        # Split experiments inside vs outside sensor time window
        exps_before = ahu_exps[ahu_exps["End Datetime"] <= s_start]
        exps_after = ahu_exps[ahu_exps["Start Datetime"] >= s_end]
        exps_in_window = ahu_exps[~((ahu_exps["End Datetime"] <= s_start) | (ahu_exps["Start Datetime"] >= s_end))]
        
        # Boundary checks
        exact_start_boundary_matches = 0
        exact_end_boundary_matches = 0
        for _, exp_row in exps_in_window.iterrows():
            exact_start_boundary_matches += int((dt_idx == exp_row["Start Datetime"]).sum())
            exact_end_boundary_matches += int((dt_idx == exp_row["End Datetime"]).sum())
            
        print(f"Sensor range: {s_start} to {s_end}")
        print(f"Total AHU {ahu_key} experiments: {len(ahu_exps)}")
        print(f"  Prior to sensor logging start: {len(exps_before)}")
        print(f"  After sensor logging end: {len(exps_after)}")
        print(f"  Inside sensor logging span: {len(exps_in_window)}")
        print(f"Boundary point test: Exact start matches = {exact_start_boundary_matches}, Exact end matches = {exact_end_boundary_matches}")
        
        # Build multi-label mapping array
        matched_experiments_per_row = [[] for _ in range(n_sensor_rows)]
        
        for _, exp_row in exps_in_window.iterrows():
            mask = (dt_idx >= exp_row["Start Datetime"]) & (dt_idx < exp_row["End Datetime"])
            matching_indices = np.where(mask)[0]
            ft_label = exp_row["Fault Type"] if pd.notnull(exp_row["Fault Type"]) else "<Missing / NaN>"
            orig_idx = int(exp_row["index"])
            for r_idx in matching_indices:
                matched_experiments_per_row[r_idx].append({
                    "exp_index": orig_idx,
                    "fault_type": ft_label,
                    "magnitude": exp_row["Magnitude"]
                })
                
        # Categorize every sensor row
        n_match = np.array([len(m) for m in matched_experiments_per_row])
        n_outside_window = int((n_match == 0).sum())
        n_in_fault_window = int((n_match > 0).sum())
        n_single_fault = int((n_match == 1).sum())
        n_multi_fault = int((n_match > 1).sum())
        
        # Reconcile sensor row partitions
        assert n_sensor_rows == n_outside_window + n_in_fault_window, "Row partition mismatch"
        assert n_in_fault_window == n_single_fault + n_multi_fault, "Fault row partition mismatch"
        
        # Clean Single-Fault Breakdown per Type
        clean_single_fault_counts = {}
        for r_idx in range(n_sensor_rows):
            if n_match[r_idx] == 1:
                ft = matched_experiments_per_row[r_idx][0]["fault_type"]
                clean_single_fault_counts[ft] = clean_single_fault_counts.get(ft, 0) + 1
                
        # Multi-fault combinations distribution
        multi_fault_combos = {}
        for r_idx in range(n_sensor_rows):
            if n_match[r_idx] > 1:
                types = sorted(set(m["fault_type"] for m in matched_experiments_per_row[r_idx]))
                combo_str = " + ".join(types)
                multi_fault_combos[combo_str] = multi_fault_combos.get(combo_str, 0) + 1
                
        # Experiment-level clean vs overlapping breakdown within sensor window
        exps_in_window_overlap = []
        for _, exp_row in exps_in_window.iterrows():
            orig_idx = int(exp_row["index"])
            is_ov = exp_df.loc[orig_idx, "has_overlap_half_open"]
            exps_in_window_overlap.append(is_ov)
        exps_in_window["has_overlap"] = exps_in_window_overlap
        
        clean_exps = exps_in_window[~exps_in_window["has_overlap"]]
        overlap_exps = exps_in_window[exps_in_window["has_overlap"]]
        
        # Breakdown of clean experiments per fault type
        clean_exp_counts_by_type = clean_exps["Fault Type"].value_counts(dropna=False).to_dict()
        clean_exp_counts_by_type = {"<Missing / NaN>" if pd.isna(k) else str(k): int(v) for k, v in clean_exp_counts_by_type.items()}
        
        # Total experiments in window by type (including nulls)
        total_exp_counts_in_window = exps_in_window["Fault Type"].value_counts(dropna=False).to_dict()
        total_exp_counts_in_window = {"<Missing / NaN>" if pd.isna(k) else str(k): int(v) for k, v in total_exp_counts_in_window.items()}
        
        # Monthly distribution of sensor rows and fault coverage
        monthly_df = pd.DataFrame(index=dt_idx)
        monthly_df["month"] = dt_idx.to_period("M")
        monthly_df["is_fault"] = (n_match > 0)
        monthly_grouped = monthly_df.groupby("month").agg(
            total_rows=("is_fault", "count"),
            fault_rows=("is_fault", "sum")
        )
        monthly_grouped["outside_window_rows"] = monthly_grouped["total_rows"] - monthly_grouped["fault_rows"]
        monthly_grouped["fault_pct"] = (monthly_grouped["fault_rows"] / monthly_grouped["total_rows"] * 100).round(2)
        
        exp_starts_monthly = exps_in_window["Start Datetime"].dt.to_period("M").value_counts().rename("exps_started")
        monthly_table = monthly_grouped.join(exp_starts_monthly).fillna({"exps_started": 0})
        monthly_table["exps_started"] = monthly_table["exps_started"].astype(int)
        
        monthly_summary_dict = {}
        for m_idx, m_row in monthly_table.iterrows():
            monthly_summary_dict[str(m_idx)] = {
                "total_rows": int(m_row["total_rows"]),
                "fault_rows": int(m_row["fault_rows"]),
                "outside_window_rows": int(m_row["outside_window_rows"]),
                "fault_pct": float(m_row["fault_pct"]),
                "exps_started": int(m_row["exps_started"])
            }
            
        print(f"Total Sensor Rows: {n_sensor_rows:,}")
        print(f"  Rows in Documented Fault Windows: {n_in_fault_window:,} ({n_in_fault_window/n_sensor_rows*100:.2f}%)")
        print(f"    - Clean Single-Fault Rows: {n_single_fault:,} ({n_single_fault/n_sensor_rows*100:.2f}%)")
        print(f"    - Multi-Fault / Overlapping Rows: {n_multi_fault:,} ({n_multi_fault/n_sensor_rows*100:.2f}%)")
        print(f"  Rows Outside Documented Fault Windows: {n_outside_window:,} ({n_outside_window/n_sensor_rows*100:.2f}%)")
        print(f"Experiments in Window: {len(exps_in_window)} total ({len(clean_exps)} clean, {len(overlap_exps)} overlapping)")
        print(f"Clean Experiments by Type: {clean_exp_counts_by_type}")
        print(f"Clean Rows by Type: {clean_single_fault_counts}")
        print(f"Multi-Fault Combinations: {multi_fault_combos}")
        
        # Verify reconciliation
        assert sum(clean_single_fault_counts.values()) == n_single_fault
        assert sum(multi_fault_combos.values()) == n_multi_fault
        assert sum(total_exp_counts_in_window.values()) == len(exps_in_window)
        assert sum(clean_exp_counts_by_type.values()) == len(clean_exps)
        
        mapping_results[fname] = {
            "ahu": ahu_key,
            "sensor_rows": n_sensor_rows,
            "sensor_start": str(s_start),
            "sensor_end": str(s_end),
            "exact_start_boundary_matches": exact_start_boundary_matches,
            "exact_end_boundary_matches": exact_end_boundary_matches,
            "total_ahu_experiments": len(ahu_exps),
            "exps_before_sensor": len(exps_before),
            "exps_after_sensor": len(exps_after),
            "exps_in_sensor_window": len(exps_in_window),
            "clean_exps_count": len(clean_exps),
            "overlap_exps_count": len(overlap_exps),
            "rows_in_fault_windows": n_in_fault_window,
            "rows_outside_fault_windows": n_outside_window,
            "rows_clean_single_fault": n_single_fault,
            "rows_multi_fault_overlap": n_multi_fault,
            "clean_exps_by_type": clean_exp_counts_by_type,
            "total_exps_in_window_by_type": total_exp_counts_in_window,
            "clean_single_fault_row_counts": clean_single_fault_counts,
            "multi_fault_combinations": multi_fault_combos,
            "monthly_coverage": monthly_summary_dict
        }
        
    return mapping_results

def run_full_audit(data_dir="data/raw/csiro"):
    sig_results, missing = verify_file_signatures(data_dir)
    if missing:
        return {"error": "Missing or invalid parquet files", "details": missing}
        
    engine = check_dependencies()
    if not engine:
        return {"error": "No Parquet engine available"}
        
    sensor_files = [
        os.path.join(data_dir, "AHU9.parquet"),
        os.path.join(data_dir, "AHU10.parquet")
    ]
    sensor_audits = {}
    for sf in sensor_files:
        sensor_audits[os.path.basename(sf)] = inspect_sensor_dataset(sf)
        
    exp_file = os.path.join(data_dir, "fault-experiments.parquet")
    exp_audit = audit_fault_experiments(exp_file)
    
    mapping_results = evaluate_half_open_mapping(sensor_files, exp_audit)
    
    exp_audit_serializable = {k: v for k, v in exp_audit.items() if k != "df"}
    
    full_audit_data = {
        "signatures": sig_results,
        "engine": engine,
        "sensor_audits": sensor_audits,
        "experiment_audit": exp_audit_serializable,
        "label_mapping": mapping_results
    }
    
    print("\n--- Audit Completed with 100% Reconciled Assertions ---")
    return full_audit_data

if __name__ == "__main__":
    run_full_audit()
