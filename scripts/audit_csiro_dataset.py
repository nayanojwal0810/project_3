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
        print(f"File: {filename} | Size: {actual_size:,} bytes (Expected: {expected_size:,}) | Valid PAR1: {is_valid_parquet} | Is LFS: {is_lfs}")

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
    
    # Identify index and timestamp
    index_name = df.index.name
    index_is_dt = isinstance(df.index, pd.DatetimeIndex)
    if index_is_dt:
        dt_series = df.index
        ts_min = dt_series.min()
        ts_max = dt_series.max()
        ts_unique = dt_series.nunique()
        duplicate_ts = n_rows - ts_unique
        is_monotonic = dt_series.is_monotonic_increasing
        # Time differences / sampling frequency
        time_diffs = dt_series.to_series().diff().dropna()
        median_freq = time_diffs.median()
        mode_freq = time_diffs.mode().iloc[0] if len(time_diffs.mode()) > 0 else None
        large_gaps = (time_diffs > (median_freq * 5)).sum()
    else:
        dt_cols = [c for c in cols if "time" in c.lower() or "date" in c.lower()]
        ts_min, ts_max, duplicate_ts, is_monotonic, median_freq, mode_freq, large_gaps = (None, None, 0, False, None, None, 0)
    
    # Missing values
    missing_counts = df.isnull().sum()
    missing_summary = {c: {"count": int(missing_counts[c]), "pct": float(missing_counts[c] / n_rows * 100)} for c in cols if missing_counts[c] > 0}
    
    # Duplicate rows
    n_duplicates = df.duplicated().sum()
    
    # Constant and near-constant columns
    constant_cols = []
    near_constant_cols = []
    for c in cols:
        vc = df[c].value_counts(dropna=False)
        top_pct = (vc.iloc[0] / n_rows * 100) if len(vc) > 0 else 0
        n_unq = df[c].nunique(dropna=False)
        if n_unq <= 1:
            constant_cols.append({"column": c, "unique": n_unq, "top_pct": top_pct, "val": str(vc.index[0]) if len(vc) > 0 else None})
        elif top_pct >= 99.0:
            near_constant_cols.append({"column": c, "unique": n_unq, "top_pct": top_pct, "top_val": str(vc.index[0])})

    # Numeric summaries, infinities, suspicious readings
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_summaries = {}
    suspicious_readings = []
    
    for c in numeric_cols:
        s = df[c].dropna()
        n_inf = np.isinf(s).sum() if len(s) > 0 else 0
        c_min = float(s.min()) if len(s) > 0 else None
        c_max = float(s.max()) if len(s) > 0 else None
        c_mean = float(s.mean()) if len(s) > 0 else None
        c_std = float(s.std()) if len(s) > 0 else None
        
        numeric_summaries[c] = {
            "min": c_min, "max": c_max, "mean": c_mean, "std": c_std, "inf_count": int(n_inf)
        }
        if n_inf > 0:
            suspicious_readings.append(f"{c}: {n_inf} infinite values")
        # Domain checks for typical HVAC: temperatures outside [-20, 150], control signals outside [0, 100] if percentage or [0, 1]
        if c_min is not None and c_min < -50:
            suspicious_readings.append(f"{c}: Extremely low minimum ({c_min})")
        if c_max is not None and c_max > 500:
            suspicious_readings.append(f"{c}: Extremely high maximum ({c_max})")

    # Columns unsuitable for prediction (e.g. constant setpoints, trivial copies)
    unsuitable_cols = [c["column"] for c in constant_cols]
    
    print(f"Rows: {n_rows:,} | Columns: {n_cols}")
    print(f"Timestamp range: {ts_min} to {ts_max} (Monotonic: {is_monotonic}, Duplicate TS: {duplicate_ts})")
    print(f"Sampling Frequency: Median={median_freq}, Mode={mode_freq}, Large Gaps (>5x median): {large_gaps}")
    print(f"Duplicate rows: {n_duplicates:,}")
    print(f"Missing columns: {len(missing_summary)} / {n_cols}")
    print(f"Constant columns: {[c['column'] for c in constant_cols]}")
    print(f"Near-constant columns: {[c['column'] for c in near_constant_cols]}")
    
    return {
        "file_name": filename,
        "n_rows": n_rows,
        "n_cols": n_cols,
        "index_name": index_name,
        "ts_min": str(ts_min),
        "ts_max": str(ts_max),
        "is_monotonic": bool(is_monotonic),
        "duplicate_ts": int(duplicate_ts),
        "sampling_median": str(median_freq),
        "sampling_mode": str(mode_freq),
        "large_gaps": int(large_gaps),
        "columns": cols,
        "dtypes": {c: str(df[c].dtype) for c in cols},
        "missing_summary": missing_summary,
        "duplicate_rows": int(n_duplicates),
        "constant_cols": constant_cols,
        "near_constant_cols": near_constant_cols,
        "numeric_summaries": numeric_summaries,
        "suspicious_readings": suspicious_readings,
        "unsuitable_cols": unsuitable_cols
    }

def audit_fault_experiments(file_path):
    print(f"\n=======================================================")
    print(f"Auditing Fault Experiments Table: {os.path.basename(file_path)}")
    df = pd.read_parquet(file_path)
    
    print(f"Rows: {len(df)} | Columns: {list(df.columns)}")
    print(f"Data types:\n{df.dtypes}")
    print("\nFirst 5 rows:")
    print(df.head())
    
    # Detect relevant columns
    cols = df.columns.tolist()
    ahu_col = next((c for c in cols if "ahu" in c.lower() or "unit" in c.lower() or "equip" in c.lower()), None)
    fault_col = next((c for c in cols if "fault" in c.lower() or "type" in c.lower() or "desc" in c.lower()), None)
    start_col = next((c for c in cols if "start" in c.lower()), None)
    end_col = next((c for c in cols if "end" in c.lower() or "stop" in c.lower()), None)
    severity_cols = [c for c in cols if any(k in c.lower() for k in ["sev", "mag", "val", "intensity", "param"])]
    
    print(f"\nDerived Mapping: AHU='{ahu_col}', Fault='{fault_col}', Start='{start_col}', End='{end_col}', Severity={severity_cols}")
    
    total_experiments = len(df)
    by_ahu = df[ahu_col].value_counts().to_dict() if ahu_col else {}
    by_fault = df[fault_col].value_counts().to_dict() if fault_col else {}
    
    # Durations
    df["start_dt"] = pd.to_datetime(df[start_col])
    df["end_dt"] = pd.to_datetime(df[end_col])
    df["duration"] = df["end_dt"] - df["start_dt"]
    
    min_duration = df["duration"].min()
    max_duration = df["duration"].max()
    median_duration = df["duration"].median()
    
    # Missing / Invalid times
    invalid_times = df[df["end_dt"] <= df["start_dt"]]
    missing_times = df[df["start_dt"].isnull() | df["end_dt"].isnull()]
    
    # Duplicates
    duplicate_records = df.duplicated().sum()
    
    # Overlapping fault intervals per AHU
    overlaps = []
    for ahu_val in df[ahu_col].unique():
        sub = df[df[ahu_col] == ahu_val].sort_values("start_dt").reset_index()
        for i in range(len(sub) - 1):
            if sub.loc[i, "end_dt"] > sub.loc[i+1, "start_dt"]:
                overlaps.append({
                    "ahu": str(ahu_val),
                    "exp1_idx": int(sub.loc[i, "index"]),
                    "exp1_fault": str(sub.loc[i, fault_col]),
                    "exp1_start": str(sub.loc[i, "start_dt"]),
                    "exp1_end": str(sub.loc[i, "end_dt"]),
                    "exp2_idx": int(sub.loc[i+1, "index"]),
                    "exp2_fault": str(sub.loc[i+1, fault_col]),
                    "exp2_start": str(sub.loc[i+1, "start_dt"]),
                    "exp2_end": str(sub.loc[i+1, "end_dt"]),
                    "overlap_duration": str(sub.loc[i, "end_dt"] - sub.loc[i+1, "start_dt"])
                })

    print(f"\nTotal Experiments: {total_experiments}")
    print(f"By AHU: {by_ahu}")
    print(f"By Fault Type: {by_fault}")
    print(f"Durations: Min={min_duration}, Max={max_duration}, Median={median_duration}")
    print(f"Invalid Start/End (End <= Start): {len(invalid_times)}")
    print(f"Missing Start/End: {len(missing_times)}")
    print(f"Duplicate experiment rows: {duplicate_records}")
    print(f"Overlapping intervals: {len(overlaps)}")
    if overlaps:
        for o in overlaps[:5]:
            print(f"  Overlap on {o['ahu']}: {o['exp1_fault']} [{o['exp1_start']} to {o['exp1_end']}] overlaps {o['exp2_fault']} [{o['exp2_start']} to {o['exp2_end']}] by {o['overlap_duration']}")

    return {
        "total_experiments": total_experiments,
        "ahu_col": ahu_col,
        "fault_col": fault_col,
        "start_col": start_col,
        "end_col": end_col,
        "severity_cols": severity_cols,
        "by_ahu": {str(k): int(v) for k, v in by_ahu.items()},
        "by_fault": {str(k): int(v) for k, v in by_fault.items()},
        "min_duration": str(min_duration),
        "max_duration": str(max_duration),
        "median_duration": str(median_duration),
        "invalid_times_count": len(invalid_times),
        "missing_times_count": len(missing_times),
        "duplicate_records": int(duplicate_records),
        "overlaps": overlaps,
        "df": df
    }

def evaluate_label_mapping(sensor_files, exp_audit):
    print(f"\n=======================================================")
    print(f"Evaluating Sensor-to-Fault Label Mapping")
    exp_df = exp_audit["df"]
    ahu_col = exp_audit["ahu_col"]
    fault_col = exp_audit["fault_col"]
    start_col = "start_dt"
    end_col = "end_dt"
    
    mapping_results = {}
    
    for s_file in sensor_files:
        fname = os.path.basename(s_file)
        # Determine AHU identifier from filename
        ahu_key = None
        for a in exp_df[ahu_col].unique():
            if str(a) in fname or f"AHU{a}" in fname:
                ahu_key = a
                break
        if ahu_key is None:
            # Fallback by matching digits
            if "9" in fname:
                ahu_key = 9 if 9 in exp_df[ahu_col].values else "AHU9"
            elif "10" in fname:
                ahu_key = 10 if 10 in exp_df[ahu_col].values else "AHU10"
        
        print(f"\nMapping for {fname} (Target AHU: {ahu_key})...")
        s_df = pd.read_parquet(s_file)
        dt_idx = s_df.index
        n_sensor_rows = len(s_df)
        
        # Filter experiments for this AHU
        ahu_exps = exp_df[exp_df[ahu_col] == ahu_key].copy()
        
        # Interval check: count how many intervals overlap sensor date range
        s_start, s_end = dt_idx.min(), dt_idx.max()
        exps_outside_sensor = ahu_exps[(ahu_exps[end_col] < s_start) | (ahu_exps[start_col] > s_end)]
        exps_inside_sensor = ahu_exps[~((ahu_exps[end_col] < s_start) | (ahu_exps[start_col] > s_end))]
        
        print(f"Sensor range: {s_start} to {s_end}")
        print(f"Experiments for this AHU: {len(ahu_exps)} total (Inside sensor range: {len(exps_inside_sensor)}, Outside: {len(exps_outside_sensor)})")
        
        # Point-in-interval mapping
        # Create an array of matched labels
        # Check overlaps
        matched_faults = []
        is_fault = np.zeros(n_sensor_rows, dtype=bool)
        match_count = np.zeros(n_sensor_rows, dtype=int)
        assigned_fault = pd.Series(["Normal"] * n_sensor_rows, index=dt_idx, dtype="object")
        
        for _, row in ahu_exps.iterrows():
            mask = (dt_idx >= row[start_col]) & (dt_idx <= row[end_col])
            count = mask.sum()
            f_name = str(row[fault_col]) if pd.notnull(row[fault_col]) else "Unknown_Fault"
            if count > 0:
                is_fault[mask] = True
                match_count[mask] += 1
                assigned_fault[mask] = f_name
        
        n_fault_records = int(is_fault.sum())
        n_normal_records = int((~is_fault).sum())
        n_ambiguous_overlapping = int((match_count > 1).sum())
        
        assigned_dist = {str(k): int(v) for k, v in assigned_fault.value_counts().items()}

        
        # Independent experiment counts per fault type inside sensor range
        exp_counts_by_fault = exps_inside_sensor[fault_col].value_counts().to_dict()
        
        print(f"Sensor rows inside fault intervals: {n_fault_records:,} ({n_fault_records/n_sensor_rows*100:.2f}%)")
        print(f"Sensor rows outside fault intervals (Normal): {n_normal_records:,} ({n_normal_records/n_sensor_rows*100:.2f}%)")
        print(f"Sensor rows in overlapping intervals: {n_ambiguous_overlapping:,} ({n_ambiguous_overlapping/n_sensor_rows*100:.2f}%)")
        print(f"Independent experiments in sensor span: {len(exps_inside_sensor)}")
        print(f"Experiment counts by fault type:")
        for ft, cnt in exp_counts_by_fault.items():
            print(f"   {ft}: {cnt} experiments ({assigned_dist.get(ft, 0):,} sensor records)")
            
        mapping_results[fname] = {
            "ahu_key": str(ahu_key),
            "sensor_rows": n_sensor_rows,
            "sensor_start": str(s_start),
            "sensor_end": str(s_end),
            "total_ahu_experiments": len(ahu_exps),
            "experiments_in_sensor_range": len(exps_inside_sensor),
            "experiments_outside_sensor_range": len(exps_outside_sensor),
            "fault_records": n_fault_records,
            "normal_records": n_normal_records,
            "overlapping_records": n_ambiguous_overlapping,
            "assigned_distribution": assigned_dist,
            "experiment_counts_by_fault": {str(k): int(v) for k, v in exp_counts_by_fault.items()}
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
    
    mapping_results = evaluate_label_mapping(sensor_files, exp_audit)
    
    # Exclude dataframe from json serialization
    exp_audit_serializable = {k: v for k, v in exp_audit.items() if k != "df"}
    
    full_audit_data = {
        "signatures": sig_results,
        "engine": engine,
        "sensor_audits": sensor_audits,
        "experiment_audit": exp_audit_serializable,
        "label_mapping": mapping_results
    }
    
    out_json = "reports/validation/csiro_audit_summary.json"
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(full_audit_data, f, indent=2)
    print(f"\nAudit complete. Summary saved to {out_json}")
    return full_audit_data

if __name__ == "__main__":
    run_full_audit()
