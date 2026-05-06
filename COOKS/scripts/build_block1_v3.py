#!/usr/bin/env python3
"""
Royal Jelly CRE · Block-1-v3 corpus builder · for Atlas-Qwen-27B (Path B · BALANCED).

Block-1-v3 = Block-1-v2 + 19 audit-vetted gold-tier additions Donovan flagged
from the master CATALOG.md scan:

  +bee-hive specialty bees      (4 files · ~3,697 records · agent recovery patterns)
  +finance HONEY/JELLY/ROYAL_J  (9 files · ~63,000 records · highest-grade credit)
  +grants apex tiers            (3 files · ~147,570 records · two royal_jelly + judged)
  +signal canonical             (1 file · 47,538 records · IC memo writing voice)
  +jelly eval                   (1 file · 20,764 records · SwarmJudge eval patterns)
  +legal pipeline_baked         (1 file · 5,989 records · 3-task PARSE/ANALYZE/RESPOND)

Total NEW raw: ~289,000 · expect ~200-250K survive fingerprint dedup
                          (some overlap with bee_hive_train_data superset expected)

Tier order: APEX small files first → bee-hive doctrine → signal narrative →
            grants apex → finance apex → legal → CRE specialty → atlas v1 → ocean.

Eval set: same 996 records as Block-0/Block-1-v2 (cross-cook comparable).

Output:
  /data1/atlas-qwen-27b/train.jsonl
  /data1/atlas-qwen-27b/eval.jsonl   (copy from /data2/atlas-granite-30b/eval.jsonl)
  /data1/atlas-qwen-27b/MANIFEST_SLICE.json
"""
import json
import hashlib
import time
import glob
import os
import shutil
import random
from pathlib import Path

random.seed(42)

OUT_DIR = Path("/data1/atlas-qwen-27b")
OUT_DIR.mkdir(parents=True, exist_ok=True)

EVAL_SOURCE = "/data2/atlas-granite-30b/eval.jsonl"   # same as Block-0/v2 · cross-cook comparable
EVAL_DEST = OUT_DIR / "eval.jsonl"
TRAIN_DEST = OUT_DIR / "train.jsonl"
MANIFEST = OUT_DIR / "MANIFEST_SLICE.json"

BLOCK_1_V2_TRAIN_SHA = "4d90e676442738c4..."  # for compares_to receipt
BLOCK_1_V2_RECORDS = 407076
BLOCK_0_RECORDS = 125651

JELLY_THRESHOLD = 75
MIN_MESSAGES = 2

SOURCES = [
    # ─────── TIER 1 · APEX DOCTRINE (smallest · highest signal · process FIRST) ───────
    {"label": "signal_platinum",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/signal/signal_platinum_20260309.jsonl",
     "cap":   None,
     "category": "doctrine · SwarmCapitalMarkets institutional analyst · PLATINUM tier"},
    {"label": "board_member_500",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/grants/board_member_500.jsonl",
     "cap":   None,
     "category": "doctrine · strategic advisor to Swarm & Bee · governance"},
    {"label": "finance_royal_jelly_apex",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/royal_jelly.jsonl",
     "cap":   None,
     "category": "NEW · finance ROYAL_JELLY apex (highest-tier credit reasoning · 1,221)"},

    # ─────── TIER 2 · BEE-HIVE DOCTRINE BACKBONE (the SwarmRefinery corpus + specialists) ───────
    {"label": "bee_hive_train_data",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/train_data.jsonl",
     "cap":   None,
     "category": "doctrine · SwarmRefinery operational intelligence · 94,768"},
    {"label": "bee_hive_critic",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/critic_train_v1.jsonl",
     "cap":   None,
     "category": "NEW · bee critic · quality-control patterns · 1,316"},
    {"label": "bee_hive_microscout",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/microscout_train_v1.jsonl",
     "cap":   None,
     "category": "NEW · microscout · fast triage · 955"},
    {"label": "bee_hive_filter",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/filter_train_v1.jsonl",
     "cap":   None,
     "category": "NEW · filter bee · routing/dedup/quality-gate · 805"},
    {"label": "bee_hive_repair",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/repair_train_v1.jsonl",
     "cap":   None,
     "category": "NEW · repair bee · failure recovery · 621"},
    {"label": "judge_cre_30k",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/judge/judge_cre_30k.jsonl",
     "cap":   None,
     "category": "evaluation · SwarmJudge CRE · A/B/C grading · 30,000"},
    {"label": "jelly_eval",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/jelly/eval.jsonl",
     "cap":   None,
     "category": "NEW · SwarmJudge agent-trajectory evaluation patterns · 20,764"},

    # ─────── TIER 3 · AGENT COORDINATION (scout/agent/router/peeta) ───────
    {"label": "bee_hive_agent",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/agent_train_v1.jsonl",
     "cap":   None,
     "category": "agent · SwarmAgent conductor · multi-turn tool dispatch"},
    {"label": "bee_hive_router",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/router_train_v1.jsonl",
     "cap":   None,
     "category": "agent · router bee · arena dispatch · routing JSON"},
    {"label": "bee_hive_scout",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/scout_train_v1.jsonl",
     "cap":   None,
     "category": "agent · scout bee · exploration · breadth-first"},
    {"label": "bee_hive_peeta",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/bee-hive/peeta_train_v1.jsonl",
     "cap":   None,
     "category": "agent · SwarmPeeta · 4B stabilizer · repair patterns"},

    # ─────── TIER 4 · SIGNAL NARRATIVE VOICE (IC memo writing prose) ───────
    {"label": "signal_canonical",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/signal/swarmsignal_canonical.jsonl",
     "cap":   None,
     "category": "NEW · sharp technical analysis prose · IC memo voice · 47,538"},

    # ─────── TIER 5 · GRANTS APEX TIERS (royal_jelly · judged · royal_jelly hyphen) ───────
    {"label": "grants_royal_jelly_hyphen",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/grants/royal-jelly.jsonl",
     "cap":   None,
     "category": "NEW · grants royal_jelly APEX · 70,394 (federal grants compliance)"},
    {"label": "grants_judged",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/grants/judged.jsonl",
     "cap":   None,
     "category": "NEW · grants judged decisions · 43,691"},
    {"label": "grants_royal_jelly_underscore",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/grants/royal_jelly.jsonl",
     "cap":   None,
     "category": "NEW · grants royal_jelly apex · 33,485 (federal grant strategy)"},
    {"label": "swarmgrant_train",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/grants/swarmgrant_train.jsonl",
     "cap":   None,
     "category": "grants · OZ / NMTC / HUD / USDA / EDA / EB-5 · 43,689"},

    # ─────── TIER 6 · NEW BUCKETS · BLOCKCHAIN + LEGAL EXPANSION ───────
    {"label": "stream_blockchain",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/capital-markets/stream_blockchain.jsonl",
     "cap":   None,
     "category": "blockchain · RWA · Hedera · stablecoin"},
    {"label": "legal_consumer_pipeline_baked",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/legal/legal_consumer_pipeline_baked_20260319_121600.jsonl",
     "cap":   None,
     "category": "NEW · CreditSniper PARSE/ANALYZE/RESPOND · 5,989"},
    {"label": "legal_consumer_stamped",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/legal/legal_consumer_stamped_openrouter_20260317_111349.jsonl",
     "cap":   None,
     "category": "legal · FDCPA debt defense · lease/LOI/estoppel · 9,160"},
    {"label": "creditsniper_train",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/legal/creditsniper_train.jsonl",
     "cap":   30000,
     "category": "legal · CRE credit + IRAC · cap 30K of 79,910"},

    # ─────── TIER 7 · FINANCE HONEY/JELLY EXPANSION (9 files · ~62K) ───────
    {"label": "finance_honey",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/finance_honey.jsonl",
     "cap":   None,
     "category": "NEW · finance HONEY tier · 14,366"},
    {"label": "finance_judged",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/judged.jsonl",
     "cap":   None,
     "category": "NEW · finance judged credit decisions · 14,276"},
    {"label": "finance_jelly",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/jelly.jsonl",
     "cap":   None,
     "category": "NEW · finance JELLY tier · 13,044"},
    {"label": "finance_honey_secondary",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/honey.jsonl",
     "cap":   None,
     "category": "NEW · finance HONEY · 4,072"},
    {"label": "finance_creditor_collector",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/creditor_collector_branching.jsonl",
     "cap":   None,
     "category": "finance · creditor vs collector branching logic · 208"},
    {"label": "finance_debt_validation",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/swarm_cooks_creditsniper_cook__debt_validation.jsonl",
     "cap":   None,
     "category": "finance · FDCPA debt defense · 9,563"},
    {"label": "finance_rating_agency",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/swarm-honey_finance-propolis__propolis.jsonl",
     "cap":   None,
     "category": "finance · credit rating agency · 13,097"},
    {"label": "finance_approval_engineering",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/approval_engineering.jsonl",
     "cap":   None,
     "category": "NEW · approval workflow patterns · 954"},
    {"label": "finance_workflow_chains",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/workflow_chains.jsonl",
     "cap":   None,
     "category": "NEW · multi-step workflow chains · 483"},
    {"label": "finance_escalation_ladders",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/escalation_ladders.jsonl",
     "cap":   None,
     "category": "NEW · escalation patterns · 426"},
    {"label": "finance_cfpb_flows",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/finance/cfpb_complaint_flows.jsonl",
     "cap":   None,
     "category": "NEW · CFPB regulatory flows · 148"},

    # ─────── TIER 8 · BLOCK-0 SMALL CRE SPECIALTY (preserved) ───────
    {"label": "maturity_wall_workflow",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/capital-markets/stream_debt_maturity.jsonl",
     "cap":   None},
    {"label": "macro_energy",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/capital-markets/stream_energy.jsonl",
     "cap":   None},
    {"label": "streams",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/capital-markets/swarmcapital_streams__shard_*.jsonl",
     "cap":   None,
     "multi_shard": True},

    # ─────── TIER 9 · CAPITAL MARKETS MEDIUM ───────
    {"label": "capital_markets_stamped",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/capital-markets/r2_capital_stamped.jsonl",
     "cap":   None},
    {"label": "capital_markets_neweconomy",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/capital-markets/r2_neweconomy_stamped.jsonl",
     "cap":   None},

    # ─────── TIER 10 · ATLAS V1 FOUNDATION (the rebuild seed) ───────
    {"label": "atlas_v1_foundation",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/capital-markets/swarmcapitalmarkets_train.jsonl",
     "cap":   None},

    # ─────── TIER 11 · OCEAN (CRE volume · capped) ───────
    {"label": "cre_honey_volume",
     "path":  "/mnt/swarm/swarm-and-bee-datasets/cre/cre_honey_stamped.jsonl",
     "cap":   120000,
     "replaces": "canonical_cre_volume (Block-0)"},
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
    print("  Royal Jelly CRE · Block-1-v3 (Path B · BALANCED) · Atlas-Qwen-27B")
    print("=" * 80)

    print("\n[1/4] Reading eval set fingerprints (same 996 as Block-0/v2)...", flush=True)
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

        if src.get("multi_shard"):
            paths = sorted(glob.glob(src["path"]))
        else:
            paths = [src["path"]]

        if not paths or not all(os.path.exists(p) for p in paths):
            print(f"      WARN  {label}: file(s) missing for {src['path']}", flush=True)
            sources_meta.append({
                "label": label, "path": src["path"], "cap": cap,
                "raw_count": 0, "kept_after_cap": 0, "sha256": None,
                "error": "file_not_found",
            })
            continue

        raw_count = 0
        kept = []
        drop_dup = 0
        drop_score = 0
        drop_minmsg = 0
        drop_invalid = 0

        for p in paths:
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        drop_invalid += 1
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

        if src.get("multi_shard"):
            h = hashlib.sha256()
            for p in paths:
                h.update(sha256_file(p).encode())
            source_sha = "multi-shard:" + h.hexdigest()[:32]
        else:
            source_sha = sha256_file(paths[0])

        sources_meta.append({
            "label": label,
            "path": src["path"],
            "shards": len(paths),
            "cap": cap,
            "raw_count": raw_count,
            "drop_invalid_json": drop_invalid,
            "drop_minmsg": drop_minmsg,
            "drop_score_below_75": drop_score,
            "drop_fingerprint_duplicate": drop_dup,
            "kept_after_filter_dedup": kept_after_filter,
            "kept_after_cap": len(kept),
            "sha256": source_sha,
            "category": src.get("category"),
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
            # STRIP all metadata · keep only messages (avoids HF datasets schema-cast issue)
            f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")
    train_sha = sha256_file(TRAIN_DEST)
    train_size_mb = TRAIN_DEST.stat().st_size / (1024 * 1024)
    print(f"      train.jsonl · {len(all_train_records):,} records · {train_size_mb:.1f} MB · sha256 {train_sha[:16]}...", flush=True)

    print("\n[4/4] Writing MANIFEST_SLICE.json...", flush=True)
    manifest = {
        "build": "Atlas-Qwen-27B",
        "step": "slice",
        "block_version": "Block-1-v3 (Path B · BALANCED)",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - t_start, 2),
        "sources": sources_meta,
        "filters": {
            "jelly_threshold_verification_score": JELLY_THRESHOLD,
            "fingerprint_dedup": True,
            "min_messages": MIN_MESSAGES,
            "schema_strip": "messages-only · drops all source-specific metadata",
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
            "note": "Same 996 records as Block-0/Block-1-v2 · cross-cook comparable",
        },
        "compares_to_block_1_v2": {
            "block_1_v2_records": BLOCK_1_V2_RECORDS,
            "block_0_records": BLOCK_0_RECORDS,
            "delta_vs_v2": len(all_train_records) - BLOCK_1_V2_RECORDS,
            "delta_pct_vs_v2": round(100 * (len(all_train_records) - BLOCK_1_V2_RECORDS) / BLOCK_1_V2_RECORDS, 1),
            "delta_vs_block_0": len(all_train_records) - BLOCK_0_RECORDS,
        },
        "doctrine": (
            "Block-1-v3 = Block-1-v2 + 19 audit-vetted gold additions per CATALOG.md scan. "
            "Path B (BALANCED) · skips SwarmJelly train superset (likely overlaps bee_hive_train_data) "
            "· pulls all four royal_jelly apex packages (grants ×2, finance ×1, jelly eval ×1) · "
            "adds 4 bee-hive specialty agents · adds finance HONEY/JELLY expansion · adds signal "
            "narrative voice. Recipe stays identical to Gold Standard (LR 1e-5 · LoRA r=64 α=32 · "
            "cosine · effective batch 32 · max_epoch_fraction 0.6 · early stopping)."
        ),
    }
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"      manifest written · {MANIFEST}", flush=True)

    print()
    print("=" * 80)
    print(f"  BUILD COMPLETE · {time.time() - t_start:.1f}s")
    print("=" * 80)
    print(f"  train.jsonl:    {len(all_train_records):>7,} records · sha256 {train_sha[:32]}...")
    print(f"  eval.jsonl:     {len(eval_fingerprints):>7,} records · sha256 {eval_sha[:32]}...")
    print(f"  vs Block-1-v2:  {len(all_train_records) - BLOCK_1_V2_RECORDS:+,} records "
          f"({round(100 * len(all_train_records) / BLOCK_1_V2_RECORDS, 1)}% of v2)")
    print(f"  vs Block-0:     {len(all_train_records) - BLOCK_0_RECORDS:+,} records "
          f"({round(100 * len(all_train_records) / BLOCK_0_RECORDS, 1)}% of Block-0)")
    print(f"\n  Records by source bucket (top 25):")
    for bucket, count in sorted(by_source.items(), key=lambda x: -x[1])[:25]:
        print(f"    {bucket:35s} {count:>7,}")


if __name__ == "__main__":
    main()
