import os
import glob
import json
import pandas as pd
import numpy as np

def audit_single_file(filepath):
    print(f"\n========================================================")
    print(f"Auditing file: {filepath}")
    file_size = os.path.getsize(filepath)
    
    # Read the dataset
    # Some datasets have timestamps or diverse headers
    df = pd.read_csv(filepath, low_memory=False)
    
    n_rows, n_cols = df.shape
    cols = df.columns.tolist()
    
    # Missing values
    missing_counts = df.isnull().sum()
    missing_pcts = (missing_counts / n_rows) * 100
    
    # Duplicates
    n_duplicates = df.duplicated().sum()
    
    # Constant or near-constant columns
    constant_cols = []
    near_constant_cols = []
    for col in cols:
        val_counts = df[col].value_counts(dropna=False)
        top_freq = val_counts.iloc[0] if len(val_counts) > 0 else 0
        top_pct = (top_freq / n_rows) * 100 if n_rows > 0 else 0
        n_unique = df[col].nunique(dropna=False)
        if n_unique <= 1:
            constant_cols.append({"column": col, "unique": n_unique, "top_pct": top_pct})
        elif top_pct >= 99.0:
            near_constant_cols.append({"column": col, "unique": n_unique, "top_pct": top_pct, "top_val": str(val_counts.index[0])})

    # Numeric summaries & invalid values
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = [c for c in cols if c not in numeric_cols]
    
    numeric_summaries = {}
    for col in numeric_cols:
        series = df[col].dropna()
        n_inf = np.isinf(series).sum() if len(series) > 0 else 0
        numeric_summaries[col] = {
            "min": float(series.min()) if len(series) > 0 else None,
            "max": float(series.max()) if len(series) > 0 else None,
            "mean": float(series.mean()) if len(series) > 0 else None,
            "std": float(series.std()) if len(series) > 0 else None,
            "p25": float(series.quantile(0.25)) if len(series) > 0 else None,
            "p50": float(series.quantile(0.50)) if len(series) > 0 else None,
            "p75": float(series.quantile(0.75)) if len(series) > 0 else None,
            "inf_count": int(n_inf)
        }

    # Inspect candidate label columns
    # Common FDD labels: 'Fault', 'fault', 'Label', 'label', 'Condition', 'Mode', 'Severity', 'type', 'state'
    candidate_labels = []
    for col in cols:
        col_lower = col.lower()
        if any(term in col_lower for term in ['fault', 'label', 'target', 'condition', 'mode', 'status', 'type', 'state', 'flag', 'class']):
            candidate_labels.append(col)
    
    # Also inspect categorical distributions for candidate labels and all non-numeric columns
    cat_distributions = {}
    cols_to_profile = list(set(candidate_labels + non_numeric_cols))
    for col in cols_to_profile:
        vc = df[col].value_counts(dropna=False).head(20).to_dict()
        cat_distributions[col] = {str(k): int(v) for k, v in vc.items()}

    # Check for timestamp column
    timestamp_cols = [c for c in cols if any(t in c.lower() for t in ['time', 'date', 'datetime', 'timestamp'])]
    timestamp_info = {}
    for tc in timestamp_cols:
        n_unique_ts = df[tc].nunique()
        duplicate_ts = n_rows - n_unique_ts
        first_val = str(df[tc].iloc[0]) if n_rows > 0 else ""
        last_val = str(df[tc].iloc[-1]) if n_rows > 0 else ""
        timestamp_info[tc] = {
            "unique": int(n_unique_ts),
            "duplicate_timestamps": int(duplicate_ts),
            "start": first_val,
            "end": last_val
        }

    audit_result = {
        "file_path": filepath,
        "file_size_bytes": file_size,
        "n_rows": int(n_rows),
        "n_cols": int(n_cols),
        "columns": cols,
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "missing_summary": {k: {"count": int(missing_counts[k]), "pct": float(missing_pcts[k])} for k in cols if missing_counts[k] > 0},
        "duplicate_rows": int(n_duplicates),
        "constant_cols": constant_cols,
        "near_constant_cols": near_constant_cols,
        "candidate_labels": candidate_labels,
        "cat_distributions": cat_distributions,
        "timestamp_info": timestamp_info,
        "numeric_summaries": numeric_summaries
    }
    
    print(f"Rows: {n_rows:,}, Cols: {n_cols}")
    print(f"Duplicates: {n_duplicates:,}")
    print(f"Missing cols: {len(audit_result['missing_summary'])}")
    print(f"Candidate labels: {candidate_labels}")
    for lbl in candidate_labels:
        print(f"  Distribution for '{lbl}': {cat_distributions.get(lbl, {})}")
    
    return audit_result

def audit_all(data_dir="data/interim"):
    csv_files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    all_results = {}
    for f in csv_files:
        base = os.path.basename(f)
        all_results[base] = audit_single_file(f)
        
    out_json = "reports/validation/dataset_audit_raw.json"
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(all_results, jf, indent=2)
    print(f"\nSaved complete audit to {out_json}")

if __name__ == "__main__":
    audit_all()
