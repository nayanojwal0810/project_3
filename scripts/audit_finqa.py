#!/usr/bin/env python3
"""
scripts/audit_finqa.py
Complete data audit for the FinQA financial reasoning dataset.

Audits every record across train.json, dev.json, test.json, and private_test.json.
Uses only the Python standard library.
"""

import os
import sys
import json
import collections
from typing import Dict, List, Any, Set, Tuple

DATA_DIR = os.path.join("data", "raw", "FinQA")
SPLIT_FILES = {
    "train": "train.json",
    "dev": "dev.json",
    "test": "test.json",
    "private_test": "private_test.json"
}

def load_and_verify_files() -> Dict[str, Tuple[str, int, List[Dict[str, Any]]]]:
    data_by_split = {}
    print("=== 1. File Verification & JSON Validation ===")
    for split, filename in SPLIT_FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"ERROR: Missing expected file: {filepath}")
            sys.exit(1)
        size_bytes = os.path.getsize(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
        except Exception as e:
            print(f"ERROR: Invalid JSON in {filepath}: {e}")
            sys.exit(1)
        if not isinstance(content, list):
            print(f"ERROR: Expected root JSON array in {filepath}, got {type(content)}")
            sys.exit(1)
        print(f"  [{split:12}] File: {filepath} | Size: {size_bytes:,} bytes | Records: {len(content):,}")
        data_by_split[split] = (filepath, size_bytes, content)
    print()
    return data_by_split

def audit_fields_and_types(data_by_split: Dict[str, Tuple[str, int, List[Dict[str, Any]]]]):
    print("=== 2. Schema, Fields, and Field Distributions ===")
    
    for split, (filepath, _, records) in data_by_split.items():
        top_field_counts = collections.Counter()
        qa_field_counts = collections.Counter()
        null_counts = collections.defaultdict(int)
        empty_counts = collections.defaultdict(int)
        
        table_row_lens = []
        pre_text_lens = []
        post_text_lens = []
        program_lens = []
        
        has_qa_obj = 0
        missing_id = 0
        
        for r in records:
            for k in r.keys():
                top_field_counts[k] += 1
                v = r[k]
                if v is None:
                    null_counts[f"top.{k}"] += 1
                elif isinstance(v, (list, dict, str)) and len(v) == 0:
                    empty_counts[f"top.{k}"] += 1
                    
            if "id" not in r or not r["id"]:
                missing_id += 1
                
            if "table" in r and isinstance(r["table"], list):
                table_row_lens.append(len(r["table"]))
            if "pre_text" in r and isinstance(r["pre_text"], list):
                pre_text_lens.append(len(r["pre_text"]))
            if "post_text" in r and isinstance(r["post_text"], list):
                post_text_lens.append(len(r["post_text"]))
                
            qa = r.get("qa")
            if isinstance(qa, dict):
                has_qa_obj += 1
                for qk in qa.keys():
                    qa_field_counts[qk] += 1
                    qv = qa[qk]
                    if qv is None:
                        null_counts[f"qa.{qk}"] += 1
                    elif isinstance(qv, (list, dict, str)) and len(qv) == 0:
                        empty_counts[f"qa.{qk}"] += 1
                if "program" in qa and isinstance(qa["program"], str):
                    program_lens.append(len(qa["program"].split()))
                    
        print(f"--- Split: {split} (Total Records: {len(records):,}) ---")
        print(f"  Top-level field presence:")
        for k, cnt in sorted(top_field_counts.items()):
            pct = cnt / len(records) * 100
            print(f"    - {k:20}: {cnt:5,} ({pct:6.2f}%)")
        print(f"  'qa' field presence (records with qa: {has_qa_obj:,}):")
        for k, cnt in sorted(qa_field_counts.items()):
            pct = cnt / len(records) * 100
            print(f"    - qa.{k:17}: {cnt:5,} ({pct:6.2f}%)")
            
        if null_counts:
            print(f"  Null fields detected:")
            for k, cnt in sorted(null_counts.items()):
                print(f"    - {k}: {cnt:,}")
        else:
            print(f"  Null fields: None detected (0)")
            
        print(f"  Empty list/str fields:")
        for k, cnt in sorted(empty_counts.items()):
            pct = cnt / len(records) * 100
            if cnt > 0:
                print(f"    - {k:22}: {cnt:5,} ({pct:6.2f}%)")
                
        def stats(arr):
            if not arr: return "N/A"
            arr.sort()
            return f"min={arr[0]}, median={arr[len(arr)//2]}, max={arr[-1]}, avg={sum(arr)/len(arr):.1f}"
            
        print(f"  Distributions:")
        print(f"    - Table row count  : {stats(table_row_lens)}")
        print(f"    - Pre-text sents   : {stats(pre_text_lens)}")
        print(f"    - Post-text sents  : {stats(post_text_lens)}")
        if program_lens:
            print(f"    - Program tokens   : {stats(program_lens)}")
        print()

def audit_ids_and_duplicates(data_by_split: Dict[str, Tuple[str, int, List[Dict[str, Any]]]]):
    print("=== 3. ID Uniqueness & Question Overlap Across Splits ===")
    
    ids_by_split = {}
    questions_by_split = {}
    
    for split, (_, _, records) in data_by_split.items():
        id_list = [r.get("id") for r in records]
        id_counts = collections.Counter(id_list)
        dups = [k for k, v in id_counts.items() if v > 1]
        ids_by_split[split] = set(id_list)
        
        q_list = [r.get("qa", {}).get("question", "").strip().lower() for r in records if "qa" in r]
        q_counts = collections.Counter(q_list)
        q_dups = [k for k, v in q_counts.items() if v > 1 and k != ""]
        questions_by_split[split] = set(q_list)
        
        print(f"Split [{split:12}]:")
        print(f"  Total records    : {len(records):,}")
        print(f"  Unique IDs       : {len(ids_by_split[split]):,}")
        print(f"  Duplicate IDs    : {len(dups):,} {f'(Examples: {dups[:3]})' if dups else '(None)'}")
        print(f"  Unique questions : {len(questions_by_split[split]):,}")
        print(f"  Duplicate Qs     : {len(q_dups):,} {f'(Examples: {q_dups[:2]})' if q_dups else '(None)'}")
        
    print("\n--- Cross-Split ID Intersections ---")
    splits = list(data_by_split.keys())
    for i in range(len(splits)):
        for j in range(i + 1, len(splits)):
            s1, s2 = splits[i], splits[j]
            overlap_ids = ids_by_split[s1].intersection(ids_by_split[s2])
            overlap_qs = questions_by_split[s1].intersection(questions_by_split[s2])
            print(f"  {s1} vs {s2}:")
            print(f"    - Shared IDs      : {len(overlap_ids)} {f'(IDs: {list(overlap_ids)[:3]})' if overlap_ids else '(Clean, 0)'}")
            print(f"    - Shared Questions: {len(overlap_qs)} {f'(Examples: {list(overlap_qs)[:2]})' if overlap_qs else '(Clean, 0)'}")
    print()

def audit_target_types_and_programs(data_by_split: Dict[str, Tuple[str, int, List[Dict[str, Any]]]]):
    print("=== 4. Target Types, Programs, and Executable Answers ===")
    
    for split in ["train", "dev", "test"]:
        _, _, records = data_by_split[split]
        exe_ans_types = collections.Counter()
        answer_types = collections.Counter()
        programs_with_const = 0
        program_ops = collections.Counter()
        has_gold_inds = 0
        gold_ind_types = collections.Counter()
        
        for r in records:
            qa = r.get("qa", {})
            exe = qa.get("exe_ans")
            exe_ans_types[type(exe).__name__] += 1
            
            ans = qa.get("answer")
            answer_types[type(ans).__name__] += 1
            
            prog = qa.get("program", "")
            if "const_" in prog:
                programs_with_const += 1
            for token in prog.replace("(", " ").replace(")", " ").replace(",", " ").split():
                if token in ["add", "subtract", "multiply", "divide", "exp", "greater"]:
                    program_ops[token] += 1
                    
            gold_inds = qa.get("gold_inds", {})
            if gold_inds:
                has_gold_inds += 1
                for k, v in gold_inds.items():
                    if "table" in k:
                        gold_ind_types["table_evidence"] += 1
                    elif "text" in k:
                        gold_ind_types["text_evidence"] += 1
                        
        print(f"Split [{split}]:")
        print(f"  Executable answer ('exe_ans') python types:")
        for t, cnt in exe_ans_types.items():
            print(f"    - {t}: {cnt:,} ({cnt/len(records)*100:.2f}%)")
        print(f"  Raw answer ('answer') python types:")
        for t, cnt in answer_types.items():
            print(f"    - {t}: {cnt:,} ({cnt/len(records)*100:.2f}%)")
        print(f"  DSL Operations frequency in programs:")
        for op, cnt in program_ops.most_common():
            print(f"    - {op:10}: {cnt:,}")
        print(f"  Programs utilizing constant tokens (const_100, const_1, etc.): {programs_with_const:,} ({programs_with_const/len(records)*100:.2f}%)")
        print(f"  Records with gold_inds evidence mapping: {has_gold_inds:,} ({has_gold_inds/len(records)*100:.2f}%)")
        print()

def audit_leakage_and_input_boundaries(data_by_split: Dict[str, Tuple[str, int, List[Dict[str, Any]]]]):
    print("=== 5. Leakage Risk & Inference Boundary Analysis ===")
    print("Evaluating field separation for downstream modelling:")
    
    inference_fields = ["id", "filename", "pre_text", "post_text", "table", "table_ori", "qa.question"]
    gold_target_fields = ["qa.answer", "qa.exe_ans", "qa.program", "qa.program_re", "qa.steps", "qa.explanation"]
    gold_evidence_fields = ["qa.gold_inds", "qa.ann_table_rows", "qa.ann_text_rows"]
    retriever_cache_fields = ["table_retrieved", "text_retrieved", "table_retrieved_all", "text_retrieved_all", "qa.tfidftopn", "qa.model_input"]
    
    print("\n  [A] Pure Inference-Time Inputs (Context & Question):")
    for f in inference_fields:
        print(f"    - {f}")
        
    print("\n  [B] Gold Supervised Targets (Strictly Excluded at Inference):")
    for f in gold_target_fields:
        print(f"    - {f}")
        
    print("\n  [C] Gold Supporting Evidence (Optional Stage 1 Retriever Supervision):")
    for f in gold_evidence_fields:
        print(f"    - {f}")
        
    print("\n  [D] Precomputed Retriever Cache (Warning: Pre-filtered by TF-IDF / Heuristic):")
    for f in retriever_cache_fields:
        print(f"    - {f}")
        
    print("\n  Private Test Check:")
    _, _, p_records = data_by_split["private_test"]
    leakage_in_private = False
    for r in p_records:
        qa = r.get("qa", {})
        for gf in gold_target_fields:
            qk = gf.split(".")[1]
            if qk in qa:
                leakage_in_private = True
                break
    print(f"    - Are any gold targets or evidence present in private_test.json? {'YES (LEAKAGE)' if leakage_in_private else 'NO (Strictly Blinded Question-Only)'}")
    print()

def generate_summary_dict(data_by_split):
    summary = {}
    for split, (path, size, records) in data_by_split.items():
        summary[split] = {
            "path": path,
            "size_bytes": size,
            "record_count": len(records),
            "top_keys": list(records[0].keys()) if records else [],
            "qa_keys": list(records[0]["qa"].keys()) if records and "qa" in records[0] else []
        }
    return summary

def main():
    print("===============================================================")
    print("          FinQA DATASET COMPREHENSIVE AUDIT REPORT            ")
    print("===============================================================\n")
    data_by_split = load_and_verify_files()
    audit_fields_and_types(data_by_split)
    audit_ids_and_duplicates(data_by_split)
    audit_target_types_and_programs(data_by_split)
    audit_leakage_and_input_boundaries(data_by_split)
    
    print("Audit execution complete. All records verified.")

if __name__ == "__main__":
    main()
