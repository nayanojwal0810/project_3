import os
import sys
import time
import json
import random
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_curve
)
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# -------------------------------------------------------------
# Configuration and Reproducibility
# -------------------------------------------------------------
RANDOM_SEED = 42
torch.manual_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(RANDOM_SEED)

DATA_DIR = "data/raw/csiro"
EXPECTED_FILES = [
    os.path.join(DATA_DIR, "AHU9.parquet"),
    os.path.join(DATA_DIR, "AHU10.parquet"),
    os.path.join(DATA_DIR, "fault-experiments.parquet")
]

# -------------------------------------------------------------
# 1. Preflight Verification
# -------------------------------------------------------------
def run_preflight_checks():
    print("=== Step 1: Preflight Verification ===")
    for f in EXPECTED_FILES:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Missing required file: {f}")
        size = os.path.getsize(f)
        print(f"Verified file exists: {f} ({size:,} bytes)")
        
    print(f"Python: {sys.version.split()[0]}")
    print(f"Pandas: {pd.__version__}")
    print(f"Torch: {torch.__version__} (Device: cpu)")
    print("Preflight checks PASSED.\n")

# -------------------------------------------------------------
# 2. Window Extraction & Processing
# -------------------------------------------------------------
def extract_windows_for_ahu(ahu_id, df_exp):
    file_path = os.path.join(DATA_DIR, f"AHU{ahu_id}.parquet")
    print(f"Extracting 10-minute windows for AHU {ahu_id} from {file_path}...")
    df = pd.read_parquet(file_path)
    raw_row_count = len(df)
    
    # Normalize equipment prefixes
    prefix = f"AHU{ahu_id}"
    df.columns = [c[len(prefix):] if c.startswith(prefix) else c for c in df.columns]
    
    # Documented Decision: Drop duplicate sensor channel ahuMaTemp
    # Audit proved (df['ahuMaTemp'] == df['ahuSaTemp']).all() == True across 100% of rows
    if "ahuMaTemp" in df.columns:
        df = df.drop(columns=["ahuMaTemp"])
        print(f"AHU {ahu_id}: Dropped redundant collinear channel 'ahuMaTemp' (retaining 'ahuSaTemp').")
        
    feature_cols = [
        'ahuZoneTemp', 'ahuZoneTemp.1', 'ahuZoneTemp.2', 'ahuAvgZoneTemp',
        'ahuCcValve', 'ahuHcValve', 'ahuOaDamper', 'ahuOaTemp',
        'ahuRaDamper', 'ahuRaRH', 'ahuRaTemp', 'ahuSaTemp',
        'ahuSaTempSP', 'ahuSaRH', 'ahuSaFanSpeed', 'ahuSaPressure'
    ]
    # Verify all feature columns exist
    for col in feature_cols:
        if col not in df.columns:
            raise KeyError(f"Expected feature {col} missing in AHU {ahu_id}")
            
    # Half-open interval matching [start, end)
    exps = df_exp[df_exp["AHU"] == ahu_id].copy().reset_index()
    dt_idx = df.index
    is_fault = np.zeros(len(df), dtype=np.int8)
    exp_id_arr = np.full(len(df), -1, dtype=int)
    
    for _, r in exps.iterrows():
        mask = (dt_idx >= r["Start Datetime"]) & (dt_idx < r["End Datetime"])
        is_fault[mask] = 1
        exp_id_arr[mask] = int(r["index"])
        
    # Vectorized 10-minute binning
    bins = dt_idx.floor("10min")
    bin_changes = np.where(bins[:-1] != bins[1:])[0] + 1
    starts = np.r_[0, bin_changes]
    ends = np.r_[bin_changes, len(df)]
    lens = ends - starts
    
    # Non-overlapping 10-minute windows must have exactly 20 observations at 30s steps
    valid_lens_mask = (lens == 20)
    candidate_starts = starts[valid_lens_mask]
    
    features_raw = df[feature_cols].values # shape: (N, 16)
    
    pure_windows = []
    n_boundary_mixed = 0
    
    for s in candidate_starts:
        lbl_block = is_fault[s:s+20]
        # Check pure label (all 0 or all 1)
        if lbl_block[0] == lbl_block[-1] and (lbl_block == lbl_block[0]).all():
            lbl = int(lbl_block[0])
            eids = list(set(exp_id_arr[s:s+20]) - {-1}) if lbl == 1 else []
            pure_windows.append({
                "ahu": ahu_id,
                "window_start": bins[s],
                "window_end": bins[s] + pd.Timedelta(minutes=10),
                "label": lbl,
                "exp_ids": eids,
                "features_20x16": features_raw[s:s+20].copy() # shape (20, 16)
            })
        else:
            n_boundary_mixed += 1
            
    n_incomplete_bins = len(lens) - len(candidate_starts)
    print(f"AHU {ahu_id} Processed: {raw_row_count:,} raw rows -> {len(pure_windows):,} pure windows.")
    print(f"   (Excluded: {n_boundary_mixed:,} boundary-crossing windows, {n_incomplete_bins:,} incomplete/gapped 10-min bins)")
    return pure_windows

# -------------------------------------------------------------
# 3. Partitioning with Buffer Boundaries
# -------------------------------------------------------------
def partition_windows(all_windows):
    print("\n=== Step 2: Temporal Partitioning with Buffer Days ===")
    
    # Train: May 1 to Aug 30, 2013
    # Buffer 1: Aug 31, 2013 (excluded)
    # Val: Sep 1 to Sep 29, 2013
    # Buffer 2: Sep 30, 2013 (excluded)
    # Primary Test: Oct 1 to Nov 30, 2013
    # Background: Dec 1, 2013 to end
    
    partitions = {
        "train": [],
        "val": [],
        "test": [],
        "background": [],
        "buffer": []
    }
    
    for w in all_windows:
        t = w["window_start"]
        if pd.to_datetime("2013-05-01") <= t < pd.to_datetime("2013-08-31"):
            partitions["train"].append(w)
        elif pd.to_datetime("2013-08-31") <= t < pd.to_datetime("2013-09-01"):
            partitions["buffer"].append(w)
        elif pd.to_datetime("2013-09-01") <= t < pd.to_datetime("2013-09-30"):
            partitions["val"].append(w)
        elif pd.to_datetime("2013-09-30") <= t < pd.to_datetime("2013-10-01"):
            partitions["buffer"].append(w)
        elif pd.to_datetime("2013-10-01") <= t < pd.to_datetime("2013-12-01"):
            partitions["test"].append(w)
        elif t >= pd.to_datetime("2013-12-01"):
            partitions["background"].append(w)
        else:
            partitions["buffer"].append(w)
            
    for name in ["train", "val", "test", "background", "buffer"]:
        wins = partitions[name]
        pos = sum(1 for w in wins if w["label"] == 1)
        neg = sum(1 for w in wins if w["label"] == 0)
        exps = set([eid for w in wins for eid in w["exp_ids"]])
        print(f"Partition {name:12}: Total={len(wins):6,}, Pos={pos:5,} ({pos/len(wins)*100 if wins else 0:5.2f}%), Neg={neg:6,}, Unique Exps={len(exps):3}")
        
    # Pre-training Stop Condition Checks per Section 5
    test_wins = partitions["test"]
    test_pos = sum(1 for w in test_wins if w["label"] == 1)
    test_neg = sum(1 for w in test_wins if w["label"] == 0)
    test_exps = set([eid for w in test_wins for eid in w["exp_ids"]])
    
    if test_pos == 0 or test_neg == 0:
        raise ValueError(f"STOP: Primary test lacks both classes! (Pos={test_pos}, Neg={test_neg})")
    if len(test_exps) < 20:
        raise ValueError(f"STOP: Primary test has fewer than 20 independent fault events! (Found: {len(test_exps)})")
        
    print(f"Evaluation preflight PASSED: Primary test has {len(test_exps)} independent fault events (>= 20 required) and both classes.\n")
    return partitions

# -------------------------------------------------------------
# 4. Feature Extraction & Scaling
# -------------------------------------------------------------
def prepare_feature_arrays(partitions):
    print("=== Step 3: Feature Extraction and Training-Only Scaling ===")
    
    # 1D CNN format: (N, 16_channels, 20_timesteps)
    # Baseline format: (N, 32) -> 16 means + 16 stds
    
    # First, collect all train timesteps to fit StandardScaler
    train_matrices = np.array([w["features_20x16"] for w in partitions["train"]]) # shape: (N_train, 20, 16)
    N_train, T, C = train_matrices.shape
    
    scaler = StandardScaler()
    train_flattened = train_matrices.reshape(-1, C) # (N_train * 20, 16)
    scaler.fit(train_flattened)
    print(f"Fitted StandardScaler on {len(train_flattened):,} training observations across {C} sensor channels.")
    
    processed = {}
    for part_name, wins in partitions.items():
        if not wins:
            continue
        raw_arr = np.array([w["features_20x16"] for w in wins]) # (N, 20, 16)
        N_part = len(raw_arr)
        
        # Scale with training scaler
        scaled_flat = scaler.transform(raw_arr.reshape(-1, C))
        scaled_arr = scaled_flat.reshape(N_part, T, C)
        
        # Baseline features: mean and std along time dimension (axis 1)
        mean_feats = np.mean(scaled_arr, axis=1) # (N, 16)
        std_feats = np.std(scaled_arr, axis=1)   # (N, 16)
        baseline_X = np.hstack([mean_feats, std_feats]) # (N, 32)
        
        # 1D CNN features: channels-first format (N, C, T) -> (N, 16, 20)
        cnn_X = np.transpose(scaled_arr, (0, 2, 1)).astype(np.float32)
        
        labels = np.array([w["label"] for w in wins], dtype=np.int64)
        ahus = np.array([w["ahu"] for w in wins], dtype=np.int32)
        exp_ids = [w["exp_ids"] for w in wins]
        
        processed[part_name] = {
            "baseline_X": baseline_X,
            "cnn_X": cnn_X,
            "y": labels,
            "ahus": ahus,
            "exp_ids": exp_ids,
            "windows": wins
        }
        print(f"Partition '{part_name}': Processed {N_part:,} windows. Baseline X shape: {baseline_X.shape}, CNN X shape: {cnn_X.shape}")
        
    return processed

# -------------------------------------------------------------
# 5. Model Architecture & Training
# -------------------------------------------------------------
class Small1DCNN(nn.Module):
    def __init__(self, in_channels=16, num_classes=1):
        super(Small1DCNN, self).__init__()
        # Block 1: 16 -> 32
        self.conv1 = nn.Conv1d(in_channels, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(32)
        self.relu = nn.ReLU()
        self.pool1 = nn.MaxPool1d(2) # 20 -> 10
        
        # Block 2: 32 -> 64
        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool2 = nn.AdaptiveAvgPool1d(1) # 10 -> 1
        
        # Classification head
        self.fc1 = nn.Linear(64, 32)
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(32, num_classes)
        
    def forward(self, x):
        # x shape: (batch_size, 16, 20)
        x = self.pool1(self.relu(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu(self.bn2(self.conv2(x))))
        x = x.squeeze(-1) # (batch_size, 64)
        x = self.dropout(self.relu(self.fc1(x)))
        out = self.fc2(x) # (batch_size, 1) logits
        return out

def train_models(data):
    print("\n=== Step 4: Training Models on CPU (Seed=42) ===")
    
    y_train = data["train"]["y"]
    y_val = data["val"]["y"]
    
    # ---------------------------------------------
    # A. Dummy Majority-Class Baseline
    # ---------------------------------------------
    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(data["train"]["baseline_X"], y_train)
    print("Trained Dummy Majority-Class Classifier.")
    
    # ---------------------------------------------
    # B. Lightweight Scikit-Learn Logistic Regression Baseline
    # ---------------------------------------------
    # Use balanced class weight to account for 5.7% positive prevalence
    baseline = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED)
    t_base_0 = time.time()
    baseline.fit(data["train"]["baseline_X"], y_train)
    baseline_runtime = time.time() - t_base_0
    print(f"Trained Baseline Logistic Regression in {baseline_runtime:.2f}s.")
    
    # Baseline predicted probabilities
    val_probs_base = baseline.predict_proba(data["val"]["baseline_X"])[:, 1]
    
    # Find optimal threshold on validation set (maximizing F1)
    best_thresh_base = 0.5
    best_f1_base = -1.0
    for th in np.linspace(0.1, 0.9, 81):
        preds = (val_probs_base >= th).astype(int)
        score = f1_score(y_val, preds, zero_division=0)
        if score > best_f1_base:
            best_f1_base = score
            best_thresh_base = th
            
    print(f"Baseline Validation: Max F1={best_f1_base:.4f} at Threshold={best_thresh_base:.2f}")
    
    # ---------------------------------------------
    # C. Small 1D CNN PyTorch Model
    # ---------------------------------------------
    pos_count = (y_train == 1).sum()
    neg_count = (y_train == 0).sum()
    pos_weight = torch.tensor([neg_count / max(pos_count, 1)], dtype=torch.float32)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    model = Small1DCNN(in_channels=16, num_classes=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    
    train_dataset = TensorDataset(
        torch.tensor(data["train"]["cnn_X"]),
        torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    )
    val_dataset = TensorDataset(
        torch.tensor(data["val"]["cnn_X"]),
        torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
    )
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=128, shuffle=False)
    
    num_epochs = 12
    best_val_pr_auc = -1.0
    best_model_weights = None
    
    t_cnn_0 = time.time()
    print(f"\nTraining 1D CNN for {num_epochs} epochs on CPU...")
    for epoch in range(1, num_epochs + 1):
        model.train()
        total_loss = 0.0
        for x_b, y_b in train_loader:
            optimizer.zero_grad()
            out = model(x_b)
            loss = criterion(out, y_b)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(x_b)
            
        # Validation pass
        model.eval()
        val_logits_list = []
        with torch.no_grad():
            for x_v, _ in val_loader:
                out_v = model(x_v)
                val_logits_list.append(out_v.numpy())
                
        val_logits = np.vstack(val_logits_list).squeeze()
        val_probs = 1.0 / (1.0 + np.exp(-val_logits))
        val_pr_auc = average_precision_score(y_val, val_probs)
        
        print(f"  Epoch {epoch:2d}/{num_epochs:2d} | Train Loss: {total_loss/len(train_dataset):.4f} | Val PR-AUC: {val_pr_auc:.4f}")
        if val_pr_auc > best_val_pr_auc:
            best_val_pr_auc = val_pr_auc
            best_model_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            
    cnn_runtime = time.time() - t_cnn_0
    print(f"1D CNN training complete in {cnn_runtime:.2f}s. Best Val PR-AUC: {best_val_pr_auc:.4f}")
    model.load_state_dict(best_model_weights)
    
    # Select threshold on validation set
    model.eval()
    val_logits_list = []
    with torch.no_grad():
        for x_v, _ in val_loader:
            val_logits_list.append(model(x_v).numpy())
    val_probs_cnn = 1.0 / (1.0 + np.exp(-np.vstack(val_logits_list).squeeze()))
    
    best_thresh_cnn = 0.5
    best_f1_cnn = -1.0
    for th in np.linspace(0.1, 0.9, 81):
        preds = (val_probs_cnn >= th).astype(int)
        score = f1_score(y_val, preds, zero_division=0)
        if score > best_f1_cnn:
            best_f1_cnn = score
            best_thresh_cnn = th
            
    print(f"1D CNN Validation: Max F1={best_f1_cnn:.4f} at Threshold={best_thresh_cnn:.2f}")
    
    return {
        "dummy": dummy,
        "baseline": baseline,
        "best_thresh_base": best_thresh_base,
        "baseline_runtime": baseline_runtime,
        "cnn_model": model,
        "best_thresh_cnn": best_thresh_cnn,
        "cnn_runtime": cnn_runtime,
        "val_probs_base": val_probs_base,
        "val_probs_cnn": val_probs_cnn
    }

# -------------------------------------------------------------
# 6. Evaluation on Primary Test & Background Stress Test
# -------------------------------------------------------------
def predict_cnn(model, cnn_X):
    model.eval()
    dataset = TensorDataset(torch.tensor(cnn_X))
    loader = DataLoader(dataset, batch_size=128, shuffle=False)
    logits_list = []
    with torch.no_grad():
        for (xb,) in loader:
            logits_list.append(model(xb).numpy())
    logits = np.vstack(logits_list).squeeze()
    return 1.0 / (1.0 + np.exp(-logits))

def compute_metrics(y_true, y_probs, threshold, exp_ids=None):
    y_pred = (y_probs >= threshold).astype(int)
    
    pr_auc = average_precision_score(y_true, y_probs) if (y_true == 1).any() else 0.0
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    bacc = balanced_accuracy_score(y_true, y_pred) if len(np.unique(y_true)) > 1 else (y_pred == y_true).mean()
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    
    # Event-level recall: fraction of unique positive events with at least one detected window
    event_level_rec = None
    if exp_ids is not None and (y_true == 1).any():
        all_pos_events = set()
        detected_events = set()
        for idx in range(len(y_true)):
            if y_true[idx] == 1:
                eids = exp_ids[idx]
                for eid in eids:
                    all_pos_events.add(eid)
                    if y_pred[idx] == 1:
                        detected_events.add(eid)
        if all_pos_events:
            event_level_rec = len(detected_events) / len(all_pos_events)
            
    return {
        "prevalence": float(np.mean(y_true)),
        "pr_auc": float(pr_auc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "balanced_accuracy": float(bacc),
        "confusion_matrix": cm,
        "event_level_recall": float(event_level_rec) if event_level_rec is not None else None
    }

def run_evaluation(data, models):
    print("\n=== Step 5: Evaluation on Validation, Primary Test & Background ===")
    
    thresh_base = models["best_thresh_base"]
    thresh_cnn = models["best_thresh_cnn"]
    
    results = {}
    
    # Partitions to evaluate
    for part in ["val", "test", "background"]:
        y_true = data[part]["y"]
        exp_ids = data[part]["exp_ids"]
        ahus = data[part]["ahus"]
        
        # Baseline probs
        probs_base = models["baseline"].predict_proba(data[part]["baseline_X"])[:, 1]
        probs_cnn = predict_cnn(models["cnn_model"], data[part]["cnn_X"])
        
        # Overall
        m_base = compute_metrics(y_true, probs_base, thresh_base, exp_ids)
        m_cnn = compute_metrics(y_true, probs_cnn, thresh_cnn, exp_ids)
        
        results[part] = {
            "overall": {
                "baseline": m_base,
                "cnn": m_cnn
            }
        }
        
        # Separate AHU9 and AHU10 on test partition
        if part == "test":
            results[part]["by_ahu"] = {}
            for target_ahu in [9, 10]:
                mask_ahu = (ahus == target_ahu)
                y_ahu = y_true[mask_ahu]
                eids_ahu = [exp_ids[i] for i in range(len(mask_ahu)) if mask_ahu[i]]
                m_base_ahu = compute_metrics(y_ahu, probs_base[mask_ahu], thresh_base, eids_ahu)
                m_cnn_ahu = compute_metrics(y_ahu, probs_cnn[mask_ahu], thresh_cnn, eids_ahu)
                results[part]["by_ahu"][f"AHU{target_ahu}"] = {
                    "baseline": m_base_ahu,
                    "cnn": m_cnn_ahu
                }

    # Background False Positive Rate
    bg_y = data["background"]["y"]
    bg_base_preds = (models["baseline"].predict_proba(data["background"]["baseline_X"])[:, 1] >= thresh_base).astype(int)
    bg_cnn_preds = (predict_cnn(models["cnn_model"], data["background"]["cnn_X"]) >= thresh_cnn).astype(int)
    
    bg_fpr_base = (bg_base_preds == 1).mean()
    bg_fpr_cnn = (bg_cnn_preds == 1).mean()
    
    results["background_fpr"] = {
        "baseline_fpr": float(bg_fpr_base),
        "cnn_fpr": float(bg_fpr_cnn)
    }
    
    print("\n--- RESULTS SUMMARY ---")
    print(f"Validation:")
    print(f"  Baseline (Thresh={thresh_base:.2f}): PR-AUC={results['val']['overall']['baseline']['pr_auc']:.4f}, F1={results['val']['overall']['baseline']['f1']:.4f}, Rec={results['val']['overall']['baseline']['recall']:.4f}")
    print(f"  1D CNN   (Thresh={thresh_cnn:.2f}):  PR-AUC={results['val']['overall']['cnn']['pr_auc']:.4f}, F1={results['val']['overall']['cnn']['f1']:.4f}, Rec={results['val']['overall']['cnn']['recall']:.4f}")
    
    print(f"\nPrimary Test (Oct–Nov 2013):")
    print(f"  Baseline: PR-AUC={results['test']['overall']['baseline']['pr_auc']:.4f}, F1={results['test']['overall']['baseline']['f1']:.4f}, Event Recall={results['test']['overall']['baseline']['event_level_recall']:.4f}, BAcc={results['test']['overall']['baseline']['balanced_accuracy']:.4f}")
    print(f"  1D CNN  : PR-AUC={results['test']['overall']['cnn']['pr_auc']:.4f}, F1={results['test']['overall']['cnn']['f1']:.4f}, Event Recall={results['test']['overall']['cnn']['event_level_recall']:.4f}, BAcc={results['test']['overall']['cnn']['balanced_accuracy']:.4f}")
    
    print(f"\nBackground Period (Dec 2013 - May 2015, No Injected Faults):")
    print(f"  Baseline False Positive Rate: {bg_fpr_base*100:.2f}% ({sum(bg_base_preds):,}/{len(bg_y):,} windows)")
    print(f"  1D CNN   False Positive Rate: {bg_fpr_cnn*100:.2f}% ({sum(bg_cnn_preds):,}/{len(bg_y):,} windows)")
    
    return results

def main():
    t_start = time.time()
    run_preflight_checks()
    
    df_exp = pd.read_parquet(os.path.join(DATA_DIR, "fault-experiments.parquet"))
    win9 = extract_windows_for_ahu(9, df_exp)
    win10 = extract_windows_for_ahu(10, df_exp)
    all_windows = win9 + win10
    
    partitions = partition_windows(all_windows)
    data = prepare_feature_arrays(partitions)
    
    models = train_models(data)
    results = run_evaluation(data, models)
    
    total_time = time.time() - t_start
    print(f"\nCompleted complete signal check in {total_time:.2f}s.")
    
    out_json = "reports/validation/model_signal_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "results": results,
            "baseline_runtime": models["baseline_runtime"],
            "cnn_runtime": models["cnn_runtime"],
            "total_runtime": total_time,
            "random_seed": RANDOM_SEED
        }, f, indent=2)
    print(f"Detailed metric json written to {out_json}")

if __name__ == "__main__":
    main()
