#!/usr/bin/env python3
"""
Atlas-Qwen-27B Training · Forked from Swarm Gold Standard
==========================================================

Fork of `gold_standard_27b.py` from the swarm-qwen-27B-Gold-Standard-Build-LLM
repo · adapted ONLY in the CONFIG section (paths + build name + base model).

The HYPERPARAMETERS section is verbatim · do NOT modify · proven on
SwarmCurator-27B-v1 (loss 0.477 · 1000 steps · 14.38h on RTX PRO 6000 96GB).

Usage:
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 \\
        python3 train_atlas_qwen_27b.py [--smoke-test|--pilot]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ═══════════════════════════════════════════════════════════════════════
# CONFIG · CHANGE FOR THIS BUILD ONLY
# ═══════════════════════════════════════════════════════════════════════

MODEL_NAME = "Qwen/Qwen3.6-27B"
TRAIN_FILE = "/data1/atlas-qwen-27b/train.jsonl"
EVAL_FILE = "/data1/atlas-qwen-27b/eval.jsonl"
OUTPUT_DIR = Path("/data1/atlas-qwen-27b/lora-adapter")
MERGED_DIR = Path("/data1/atlas-qwen-27b/merged")
LOG_DIR = Path("/data1/atlas-qwen-27b/logs")
NAS_MIRROR = Path("/mnt/swarm/model_archives/atlas-qwen-27b")  # best-effort post-cook
BUILD_NAME = "Atlas-Qwen-27B"

# ═══════════════════════════════════════════════════════════════════════
# GOLD STANDARD HYPERPARAMETERS · DO NOT CHANGE
# (proven on SwarmCurator-27B-v1 · loss 0.477)
# ═══════════════════════════════════════════════════════════════════════

LORA_R = 64
LORA_ALPHA = 32
LORA_DROPOUT = 0.0
LEARNING_RATE = 1e-5            # PROVEN · NEVER 2e-5+ for 27B
MAX_EPOCH_FRACTION = 0.6        # never full epoch · prevents memorization
BATCH_SIZE = 2                  # 27B bf16 is tight on 96GB
GRAD_ACCUM = 16                 # effective batch = 32
MAX_SEQ_LEN = 4096
WARMUP_RATIO = 0.05
WEIGHT_DECAY = 0.01
LR_SCHEDULER = "cosine"
EVAL_STEPS = 200
SAVE_STEPS = 200
EARLY_STOPPING_PATIENCE = 3
EARLY_STOPPING_THRESHOLD = 0.001
MAX_EVAL_SAMPLES = 500          # without packing · 3K+ samples = 34 min/eval
SAVE_TOTAL_LIMIT = 5

TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",       # standard attention (25% of layers)
    "gate_proj", "up_proj", "down_proj",            # MLP (all layers)
]
# We do NOT target GDN-specific params (in_proj_qkv, in_proj_z, etc.) · proven
# fine frozen on SwarmCurator-27B-v1.


# ═══════════════════════════════════════════════════════════════════════
# DATA VALIDATION · pre-flight gates
# ═══════════════════════════════════════════════════════════════════════

def validate_data(train_path: str, eval_path: str):
    """Pre-flight data validation. Fails fast on bad data."""
    for label, path in [("Train", train_path), ("Eval", eval_path)]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"{label} file not found: {path}")

    sys_prompts = set()
    train_count = 0
    with open(train_path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON at {train_path}:{i}")
            msgs = rec.get("messages", [])
            if len(msgs) < 2:
                raise ValueError(f"Record at {train_path}:{i} has < 2 messages")
            if msgs[0].get("role") == "system":
                sys_prompts.add(msgs[0]["content"][:100])
            train_count += 1

    eval_count = sum(1 for line in open(eval_path) if line.strip())
    train_sha = hashlib.sha256(open(train_path, "rb").read()).hexdigest()
    eval_sha = hashlib.sha256(open(eval_path, "rb").read()).hexdigest()

    print(f"  Train: {train_count:,} records (SHA256: {train_sha[:16]}...)")
    print(f"  Eval:  {eval_count:,} records (SHA256: {eval_sha[:16]}...)")
    print(f"  System prompt diversity: {len(sys_prompts)} unique")

    if train_count < 1000:
        raise ValueError(f"Dataset too small: {train_count} records (min 1000)")
    if len(sys_prompts) < 15:
        print(f"  WARNING: Low system prompt diversity ({len(sys_prompts)}). Target ≥30.")

    max_share = 0
    if sys_prompts:
        prompt_counts = {}
        with open(train_path) as f:
            for line in f:
                rec = json.loads(line.strip())
                msgs = rec.get("messages", [])
                if msgs and msgs[0].get("role") == "system":
                    key = msgs[0]["content"][:100]
                    prompt_counts[key] = prompt_counts.get(key, 0) + 1
        max_share = max(prompt_counts.values()) / train_count
        if max_share > 0.15:
            print(f"  WARNING: Dominant prompt at {max_share:.1%} (target <15%)")

    return {
        "train_count": train_count,
        "eval_count": eval_count,
        "train_sha256": train_sha,
        "eval_sha256": eval_sha,
        "system_prompt_diversity": len(sys_prompts),
        "max_prompt_share": round(max_share, 4),
    }


# ═══════════════════════════════════════════════════════════════════════
# TRAINING
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description=f"Train {BUILD_NAME} (Gold Standard recipe)")
    parser.add_argument("--smoke-test", action="store_true",
                        help="500 samples · quick validation")
    parser.add_argument("--pilot", action="store_true",
                        help="5000 samples · medium run")
    parser.add_argument("--max-seq-len", type=int, default=MAX_SEQ_LEN)
    parser.add_argument("--resume", type=str,
                        help="Resume from checkpoint path (ONLY if same LR/config)")
    args = parser.parse_args()

    # Imports here so argparse/help works without GPU
    from unsloth import FastLanguageModel
    from transformers import AutoTokenizer, EarlyStoppingCallback
    from trl import SFTTrainer, SFTConfig
    from datasets import load_dataset
    import torch

    # ─── Pre-flight banner ───
    print("=" * 70)
    print(f"  {BUILD_NAME} · GOLD STANDARD RECIPE (forked from SwarmCurator-27B-v1)")
    print(f"  Base:       {MODEL_NAME}")
    print(f"  Method:     bf16 LoRA r={LORA_R} alpha={LORA_ALPHA}")
    print(f"  LR:         {LEARNING_RATE} (proven · never 2e-5+)")
    print(f"  Batch:      {BATCH_SIZE} x {GRAD_ACCUM} = {BATCH_SIZE * GRAD_ACCUM} effective")
    print(f"  Max Seq:    {args.max_seq_len}")
    print(f"  Scheduler:  {LR_SCHEDULER}")
    print(f"  GPU:        {torch.cuda.get_device_name(0)}")
    print(f"  VRAM:       {torch.cuda.get_device_properties(0).total_memory / 1e9:.0f} GB")
    if args.smoke_test:
        print(f"  Mode:       SMOKE TEST (500 samples)")
    elif args.pilot:
        print(f"  Mode:       PILOT (5000 samples)")
    else:
        print(f"  Mode:       FULL · Block-1-v2 (407K records)")
    if args.resume:
        print(f"  Resume:     {args.resume}")
    print("=" * 70)

    # ─── Validate data ───
    print("\n[0/5] Validating data...")
    data_info = validate_data(TRAIN_FILE, EVAL_FILE)

    # ─── Model ───
    print(f"\n[1/5] Loading {MODEL_NAME} (27B bf16, ~54 GB)...")
    model, _ = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=args.max_seq_len,
        dtype=torch.bfloat16,
        load_in_4bit=False,         # NO QLoRA · Qwen3.5/3.6 has higher quantization error
    )

    # ─── Tokenizer (AutoTokenizer bypass · proven discipline) ───
    print("[2/5] Loading tokenizer (AutoTokenizer bypass · Unsloth dispatch broken for Qwen VL)...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.padding_side = "right"

    # ─── LoRA ───
    print("[3/5] Applying LoRA (r=64 · α=32 · standard target_modules)...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=TARGET_MODULES,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )
    model.print_trainable_parameters()

    # ─── Dataset ───
    print("[4/5] Loading dataset...")
    train_dataset = load_dataset("json", data_files=TRAIN_FILE, split="train")
    eval_dataset = load_dataset("json", data_files=EVAL_FILE, split="train")

    if args.smoke_test:
        train_dataset = train_dataset.select(range(min(500, len(train_dataset))))
        eval_dataset = eval_dataset.select(range(min(50, len(eval_dataset))))
    elif args.pilot:
        train_dataset = train_dataset.select(range(min(5000, len(train_dataset))))
        eval_dataset = eval_dataset.select(range(min(200, len(eval_dataset))))

    def format_chat(example):
        """Format messages · Gold Standard discipline: default apply_chat_template, no enable_thinking override."""
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    train_dataset = train_dataset.map(
        format_chat,
        remove_columns=train_dataset.column_names,
        desc="Formatting train",
        num_proc=min(16, os.cpu_count() or 1),
    )
    eval_dataset = eval_dataset.map(
        format_chat,
        remove_columns=eval_dataset.column_names,
        desc="Formatting eval",
        num_proc=4,
    )

    # Cap eval set
    if len(eval_dataset) > MAX_EVAL_SAMPLES:
        print(f"  Capping eval from {len(eval_dataset):,} to {MAX_EVAL_SAMPLES}")
        eval_dataset = eval_dataset.select(range(MAX_EVAL_SAMPLES))

    # Steps math (Gold Standard formula: 0.6 of one full epoch)
    eff_batch = BATCH_SIZE * GRAD_ACCUM
    full_epoch_steps = len(train_dataset) // eff_batch
    max_steps = int(full_epoch_steps * MAX_EPOCH_FRACTION)

    print(f"  Train: {len(train_dataset):,} | Eval: {len(eval_dataset):,}")
    print(f"  Eff batch:     {eff_batch}")
    print(f"  Full epoch:    {full_epoch_steps} steps")
    print(f"  Max steps:     {max_steps} (capped at {MAX_EPOCH_FRACTION} epoch · early stopping may trigger sooner)")

    # ─── Trainer ───
    print("[5/5] Configuring trainer...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=SFTConfig(
            output_dir=str(OUTPUT_DIR),
            max_steps=max_steps,
            per_device_train_batch_size=BATCH_SIZE,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=GRAD_ACCUM,
            learning_rate=LEARNING_RATE,
            lr_scheduler_type=LR_SCHEDULER,
            warmup_ratio=WARMUP_RATIO,
            weight_decay=WEIGHT_DECAY,
            bf16=True,
            logging_steps=10,
            eval_strategy="steps",
            eval_steps=EVAL_STEPS,
            save_strategy="steps",
            save_steps=SAVE_STEPS,
            save_total_limit=SAVE_TOTAL_LIMIT,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to="none",
            max_seq_length=args.max_seq_len,
            packing=True,           # may be skipped by Unsloth VL detection · OK
            dataset_text_field="text",
        ),
        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=EARLY_STOPPING_PATIENCE,
                early_stopping_threshold=EARLY_STOPPING_THRESHOLD,
            ),
        ],
    )

    # ─── Train ───
    print("\n" + "=" * 70)
    print(f"  TRAINING START · {BUILD_NAME}")
    print(f"  LR={LEARNING_RATE}, batch={eff_batch}, scheduler={LR_SCHEDULER}")
    print(f"  Early stopping: patience={EARLY_STOPPING_PATIENCE}, threshold={EARLY_STOPPING_THRESHOLD}")
    print("=" * 70)

    if args.resume:
        result = trainer.train(resume_from_checkpoint=args.resume)
    else:
        result = trainer.train()

    elapsed = time.time() - t0

    # ─── Save ───
    print("\n" + "=" * 70)
    print(f"  TRAINING COMPLETE · {BUILD_NAME}")
    print(f"  Loss:    {result.training_loss:.4f}")
    print(f"  Steps:   {result.global_step}")
    print(f"  Time:    {elapsed/3600:.2f}h ({elapsed/60:.0f}m)")
    print("=" * 70)

    # Save adapter
    trainer.model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"  Adapter saved to: {OUTPUT_DIR}")

    # Merge
    print("\n  Merging adapter into base model...")
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained_merged(
        str(MERGED_DIR),
        tokenizer,
        save_method="merged_16bit",
    )
    print(f"  Merged model saved to: {MERGED_DIR}")

    # ─── NAS mirror (best-effort) ───
    try:
        if NAS_MIRROR.parent.exists():
            print(f"\n  Mirroring to NAS at {NAS_MIRROR}...")
            NAS_MIRROR.mkdir(parents=True, exist_ok=True)
            os.system(f"rsync -a {OUTPUT_DIR}/ {NAS_MIRROR}/lora-adapter/ 2>&1")
            os.system(f"rsync -a {MERGED_DIR}/ {NAS_MIRROR}/merged/ 2>&1")
            print(f"  NAS mirror complete · weights are anchored")
        else:
            print(f"  NAS mount missing · skipping mirror (run manually post-cook)")
    except Exception as e:
        print(f"  WARN · NAS mirror skipped: {e}")

    # ─── Manifest ───
    manifest = {
        "model": BUILD_NAME,
        "base": MODEL_NAME,
        "architecture": "Qwen3_5ForConditionalGeneration · hybrid GDN + standard attention",
        "method": f"bf16 LoRA r={LORA_R} alpha={LORA_ALPHA}",
        "config_source": "Swarm Gold Standard (SwarmCurator-27B-v1 · loss 0.477)",
        "data": {
            "block_version": "Royal Jelly CRE Block-1-v2",
            "train_records": data_info["train_count"],
            "eval_records": data_info["eval_count"],
            "train_sha256": data_info["train_sha256"],
            "eval_sha256": data_info["eval_sha256"],
            "system_prompt_diversity": data_info["system_prompt_diversity"],
            "max_prompt_share": data_info["max_prompt_share"],
        },
        "training": {
            "steps": result.global_step,
            "max_steps": max_steps,
            "final_loss": round(result.training_loss, 4),
            "learning_rate": LEARNING_RATE,
            "lr_scheduler": LR_SCHEDULER,
            "effective_batch": eff_batch,
            "batch_size": BATCH_SIZE,
            "grad_accum": GRAD_ACCUM,
            "max_seq_len": MAX_SEQ_LEN,
            "packing": True,
            "early_stopping_patience": EARLY_STOPPING_PATIENCE,
            "epoch_fraction": MAX_EPOCH_FRACTION,
        },
        "hardware": {
            "gpu": torch.cuda.get_device_name(0),
            "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9),
        },
        "gold_standard_reference": {
            "model": "SwarmCurator-27B-v1",
            "loss": 0.4766,
            "steps": 1000,
            "elapsed_hours": 14.38,
            "data_records": 62525,
        },
        "lineage": {
            "atlas_v1_status": "vanished · weights lost · this is the rebuild",
            "atlas_v1_foundation_records_in_block_1_v2": 16938,
        },
        "elapsed_hours": round(elapsed / 3600, 2),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "adapter_path": str(OUTPUT_DIR),
        "merged_path": str(MERGED_DIR),
        "nas_mirror_path": str(NAS_MIRROR),
    }

    manifest_path = MERGED_DIR.parent / "MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n  Manifest:  {manifest_path}")
    print(f"  Merged:    {MERGED_DIR}")
    print(f"\n  Next steps:")
    print(f"    1. Fix vision_config (Unsloth strips it during merge):")
    print(f"       python3 fix_vision_config.py {MERGED_DIR} --base {MODEL_NAME}")
    print(f"    2. Deploy:")
    print(f"       vllm serve {MERGED_DIR} --dtype bfloat16 --enforce-eager --skip-mm-profiling")
    print("=" * 70)


if __name__ == "__main__":
    main()
