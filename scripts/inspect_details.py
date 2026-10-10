import json
import os

with open("reports/validation/dataset_audit_raw.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for fname, d in sorted(data.items()):
    print("=" * 60)
    print(f"FILE: {fname} (Size: {d['file_size_bytes']:,} bytes)")
    print(f"Shape: {d['n_rows']:,} rows x {d['n_cols']} cols")
    print(f"Duplicate rows: {d['duplicate_rows']}")
    print(f"Missing values by column:")
    for col, m in d['missing_summary'].items():
        print(f"   {col}: {m['count']} ({m['pct']:.2f}%)")
    if not d['missing_summary']:
        print("   None (0% missing across all columns)")
    print(f"Constant columns:")
    for c in d['constant_cols']:
        print(f"   {c['column']} (Unique: {c['unique']})")
    print(f"Near-constant columns (>=99% same value):")
    for nc in d['near_constant_cols']:
        print(f"   {nc['column']} (Unique: {nc['unique']}, Top value: '{nc['top_val']}' at {nc['top_pct']:.2f}%)")
    print("Timestamps:")
    for t_col, t_info in d['timestamp_info'].items():
        print(f"   {t_col}: {t_info['unique']} unique, range: {t_info['start']} to {t_info['end']}, duplicate ts: {t_info['duplicate_timestamps']}")
    print("Candidate Labels & distributions:")
    for lbl in d['candidate_labels']:
        print(f"   {lbl}: {d['cat_distributions'].get(lbl)}")
    print("All Columns:")
    for idx, c in enumerate(d['columns']):
        dtype = d['dtypes'][c]
        print(f"   {idx+1:2d}. {c} ({dtype})")
