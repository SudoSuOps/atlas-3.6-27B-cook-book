#!/usr/bin/env python3
"""
Royal Jelly CRE · Block-1-v4 corpus builder · for Atlas-Qwen-27B.

Block-1-v4 is the DISCIPLINED CULL of Block-1-v3 per senior peer review.

The four-fix prescription required:
  1. packing=False  (SDPA + GDN can't safely pack · cross-contamination risk)
  2. cull to Honey + Royal Jelly tiers only (drop Mixed/Specialist/Taste)
  3. re-baseline max_steps for the smaller corpus
  4. canary 200-step verification before full cook

This script implements (2) · the disciplined cull.

Block-1-v3 had 41 sources · 486K records · 7+ tiers mixed.
Block-1-v4 keeps only:
  - apex tiny (signal_platinum · board_member_500 · finance_royal_jelly_apex)
  - the doctrine backbone (bee_hive_train_data 94,768)
  - evaluation discipline (judge_cre_30k · jelly_eval)
  - apex Royal_Jelly (grants royal_jelly × 2 · finance honey)
  - narrative voice (signal_canonical capped 25K)
  - blockchain new economy (stream_blockchain · doctrine specialty)
  - CRE volume capped TIGHT (cre_honey 20K not 120K)

DROPPED from v3 (Mixed/Specialist/Taste tiers per CATALOG.md):
  - atlas_v1_foundation (12,797)              Mixed
  - capital_markets_stamped (was 0 absorbed)
  - capital_markets_neweconomy (was 0 absorbed)
  - maturity_wall_workflow (5,549)            Specialist
  - macro_energy (14,632)                     Mixed
  - streams (10,209)                          Specialty
  - swarmgrant_train (9,513)                  Mixed
  - legal_consumer_stamped (8,773)            Mixed
  - creditsniper_train (30,000)               Premium · but high-volume · DILUTES doctrine
  - bee_hive specialty bees (4,621)           Specialist (keeping bee_hive_train_data only)
  - finance_judged · finance_jelly · etc.    Mixed/Specialist
  - legal_pipeline_baked (5,989)              Specialist
  - finance approval/workflow/escalation     Specialist/Taste

Total target: ~150-180K records after fingerprint dedup.

Eval set: same 996 records as Block-0/v2/v3 (cross-cook comparable).

Output:
  /data1/atlas-qwen-27b-v4/train.jsonl
  /data1/atlas-qwen-27b-v4/eval.jsonl
  /data1/atlas-qwen-27b-v4/MANIFEST_SLICE.json
"""
import json
import hashlib
import time
import os
import shutil
import random
from pathlib import Path

random.seed(42)

OUT_DIR = Path("/data1/atlas-qwen-27b-v4")
OUT_DIR.mkdir(parents=True, exist_ok=True)

EVAL_SOURCE = "/data1/atlas-qwen-27b/eval.jsonl"
EVAL_DEST = OUT_DIR / "eval.jsonl"
TRAIN_DEST = OUT_DIR / "train.jsonl"
MANIFEST = OUT_DIR / "MANIFEST_SLICE.json"

BLOCK_1_V3_RECORDS = 486428
BLOCK_1_V3_SHA = "0f0456356b211cb2..."

JELLY_THRESHOLD = 75
MIN_MESSAGES = 2

SOURCES = [
    # ─────── TIER 1 · APEX TINY ───────
    {"label": "signal_platinum",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/signal/signal_platinum_20260309.jsonl",
     "cap":   None,
     "tier":  "apex"},
    {"label": "board_member_500",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/grants/board_member_500.jsonl",
     "cap":   None,
     "tier":  "apex"},
    {"label": "finance_royal_jelly_apex",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/royal_jelly.jsonl",
     "cap":   None,
     "tier":  "apex"},

    # ─────── TIER 2 · DOCTRINE BACKBONE ───────
    {"label": "bee_hive_train_data",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/train_data.jsonl",
     "cap":   None,
     "tier":  "premium · the SwarmRefinery doctrine"},

    # ─────── TIER 3 · EVALUATION DISCIPLINE ───────
    {"label": "judge_cre_30k",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/judge/judge_cre_30k.jsonl",
     "cap":   None,
     "tier":  "evaluation · CRE A/B/C grading"},
    {"label": "jelly_eval",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/jelly/eval.jsonl",
     "cap":   None,
     "tier":  "expert · SwarmJudge agent-trajectory eval"},

    # ─────── TIER 4 · ROYAL JELLY APEX ───────
    {"label": "grants_royal_jelly_hyphen",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/grants/royal-jelly.jsonl",
     "cap":   None,
     "tier":  "royal_jelly apex"},
    {"label": "grants_royal_jelly_underscore",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/grants/royal_jelly.jsonl",
     "cap":   None,
     "tier":  "royal_jelly apex"},

    # ─────── TIER 5 · HONEY TIER ───────
    {"label": "finance_honey",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/finance_honey.jsonl",
     "cap":   None,
     "tier":  "honey"},

    # ─────── TIER 6 · NARRATIVE VOICE (capped) ───────
    {"label": "signal_canonical",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/signal/swarmsignal_canonical.jsonl",
     "cap":   25000,                   # cap from 47,538 · dilution control
     "tier":  "premium · capped for ratio"},

    # ─────── TIER 7 · BLOCKCHAIN DOCTRINE (Donovan-flagged · keep) ───────
    {"label": "stream_blockchain",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/capital-markets/stream_blockchain.jsonl",
     "cap":   None,
     "tier":  "specialist · new economy doctrine"},

    # ─────── TIER 8 · CRE VOLUME OCEAN (capped TIGHT) ───────
    {"label": "cre_honey_volume",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/cre/cre_honey_stamped.jsonl",
     "cap":   20000,                   # cap from 810K · v3 had 120K · cull to 20K
     "tier":  "premium · capped tight to prevent dilution"},
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(rec):
    msgs = rec.get("messages", [])
    parts = []
    for m in msgs:
        role = m.get("role", "")
        content = m.get("content") or ""
        parts.append(role + ":" + content[:5000])
    return hashlib.md5("\n".join(parts).encode("utf-8")).hexdigest()


def jelly_score(rec):
    for key in ("verification_score", "jelly_score", "rj_score"):
        if key in rec and isinstance(rec[key], (int, float)):
            return float(rec[key])
    meta = rec.get("metadata") or rec.get("meta") or {}
    if isinstance(meta, dict):
        for key in ("verification_score", "jelly_score", "rj_score"):
            if key in meta and isinstance(meta[key], (int, float)):
                return float(meta[key])
    return None


def main():
    t_start = time.time()
    print("=" * 80)
    print("  Royal Jelly CRE · Block-1-v4 (DISCIPLINED CULL · post peer review)")
    print("=" * 80)

    print("\n[1/4] Reading eval set fingerprints...", flush=True)
    eval_fingerprints = set()
    with open(EVAL_SOURCE) as f:
        for line in f:
            line = line.strip()
            if line:
                eval_fingerprints.add(fingerprint(json.loads(line)))
    print(f"      {len(eval_fingerprints)} eval fingerprints loaded", flush=True)

    shutil.copy(EVAL_SOURCE, EVAL_DEST)
    eval_sha = sha256_file(EVAL_DEST)
    print(f"      eval.jsonl copied · sha256 {eval_sha[:16]}...", flush=True)

    print("\n[2/4] Reading sources + filtering + dedup + cap...", flush=True)
    seen_fingerprints = set(eval_fingerprints)
    sources_meta = []
    all_train_records = []

    for src in SOURCES:
        label = src["label"]
        cap = src.get("cap")
        path = src["path"]

        if not os.path.exists(path):
            print(f"      WARN  {label}: file missing", flush=True)
            sources_meta.append({"label": label, "path": path, "error": "file_not_found"})
            continue

        raw_count = 0
        kept = []
        drop_dup = 0
        drop_score = 0
        drop_minmsg = 0

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                raw_count += 1

                msgs = rec.get("messages", [])
                if len(msgs) < MIN_MESSAGES:
                    drop_minmsg += 1
                    continue

                score = jelly_score(rec)
                if score is not None and score < JELLY_THRESHOLD:
                    drop_score += 1
                    continue

                fp = fingerprint(rec)
                if fp in seen_fingerprints:
                    drop_dup += 1
                    continue

                seen_fingerprints.add(fp)
                kept.append(rec)

        kept_after_filter = len(kept)
        if cap is not None and len(kept) > cap:
            random.shuffle(kept)
            kept = kept[:cap]

        source_sha = sha256_file(path)

        sources_meta.append({
            "label": label,
            "path": path,
            "tier": src.get("tier"),
            "cap": cap,
            "raw_count": raw_count,
            "drop_minmsg": drop_minmsg,
            "drop_score_below_75": drop_score,
            "drop_fingerprint_duplicate": drop_dup,
            "kept_after_filter_dedup": kept_after_filter,
            "kept_after_cap": len(kept),
            "sha256": source_sha,
        })

        cap_note = f" cap→{cap}" if cap else ""
        print(f"      {label:34s}  raw {raw_count:>7} | kept {len(kept):>6}{cap_note} | "
              f"drop dup {drop_dup} score {drop_score} minmsg {drop_minmsg}", flush=True)

        for r in kept:
            r["_source_bucket"] = label
        all_train_records.extend(kept)

    print("\n[3/4] Strip metadata (keep only messages) + shuffle + write train.jsonl...", flush=True)
    random.shuffle(all_train_records)

    by_source = {}
    with open(TRAIN_DEST, "w") as f:
        for r in all_train_records:
            bucket = r.pop("_source_bucket", "unknown")
            by_source[bucket] = by_source.get(bucket, 0) + 1
            f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")
    train_sha = sha256_file(TRAIN_DEST)
    train_size_mb = TRAIN_DEST.stat().st_size / (1024 * 1024)
    print(f"      train.jsonl · {len(all_train_records):,} records · {train_size_mb:.1f} MB · sha256 {train_sha[:16]}...", flush=True)

    print("\n[4/4] Writing MANIFEST_SLICE.json...", flush=True)
    manifest = {
        "build": "Atlas-Qwen-27B",
        "step": "slice",
        "block_version": "Block-1-v4 (DISCIPLINED CULL · post-peer-review)",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - t_start, 2),
        "sources": sources_meta,
        "filters": {
            "jelly_threshold_verification_score": JELLY_THRESHOLD,
            "fingerprint_dedup": True,
            "min_messages": MIN_MESSAGES,
            "schema_strip": "messages-only",
        },
        "train": {
            "path": str(TRAIN_DEST),
            "sha256": train_sha,
            "records": len(all_train_records),
            "size_mb": round(train_size_mb, 1),
            "by_source": by_source,
        },
        "eval": {
            "path": str(EVAL_DEST),
            "sha256": eval_sha,
            "records": len(eval_fingerprints),
            "note": "Same 996 records as Block-0/v2/v3 · cross-cook comparable",
        },
        "compares_to_block_1_v3": {
            "block_1_v3_records": BLOCK_1_V3_RECORDS,
            "delta_vs_v3": len(all_train_records) - BLOCK_1_V3_RECORDS,
            "delta_pct_vs_v3": round(100 * (len(all_train_records) - BLOCK_1_V3_RECORDS) / BLOCK_1_V3_RECORDS, 1),
        },
        "doctrine": (
            "Block-1-v4 = disciplined cull of v3 per senior peer review. "
            "Drops Mixed/Specialist/Taste tiers · keeps apex + Honey + Royal Jelly only. "
            "12 sources (vs 41 in v3) · target 150-180K records. "
            "Designed to pair with packing=False (SDPA + GDN safe) and re-baselined max_steps "
            "for proper 0.4-0.6 epoch training depth."
        ),
    }
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"      manifest written · {MANIFEST}", flush=True)

    print()
    print("=" * 80)
    print(f"  BUILD COMPLETE · {time.time() - t_start:.1f}s")
    print("=" * 80)
    print(f"  train.jsonl:    {len(all_train_records):>7,} records")
    print(f"  vs Block-1-v3:  {len(all_train_records) - BLOCK_1_V3_RECORDS:+,} records "
          f"({round(100 * len(all_train_records) / BLOCK_1_V3_RECORDS, 1)}% of v3)")
    print(f"\n  Records by source bucket:")
    for bucket, count in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"    {bucket:35s} {count:>7,}")


if __name__ == "__main__":
    main()
