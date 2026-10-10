import json
import pandas as pd
import numpy as np

with open("reports/validation/dataset_audit_raw.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for fname, d in sorted(data.items()):
    print(f"\n==================== {fname} ====================")
    rows = []
    for col, stats in d["numeric_summaries"].items():
        rows.append({
            "Column": col,
            "Min": f"{stats['min']:.2f}" if stats['min'] is not None else "N/A",
            "Max": f"{stats['max']:.2f}" if stats['max'] is not None else "N/A",
            "Mean": f"{stats['mean']:.2f}" if stats['mean'] is not None else "N/A",
            "Std": f"{stats['std']:.2f}" if stats['std'] is not None else "N/A",
            "P50": f"{stats['p50']:.2f}" if stats['p50'] is not None else "N/A",
            "Inf": stats["inf_count"]
        })
    df_stats = pd.DataFrame(rows)
    print(df_stats.head(15).to_string(index=False))
    if len(df_stats) > 15:
        print(f"... and {len(df_stats)-15} more numeric columns")
