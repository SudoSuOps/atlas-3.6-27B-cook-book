#!/usr/bin/env python3
"""
Atlas-Qwen-27B Training · Gold Standard recipe + vanilla transformers stack
============================================================================

Adapted from gold_standard_27b.py with one substrate-deviation:
DROPPED Unsloth FastLanguageModel because Unsloth 2026.5.2's bundled FA2 kernels
are not compiled for Blackwell sm_120 (RTX PRO 6000 Workstation Edition).

Replaced with vanilla `transformers.AutoModelForCausalLM` + `peft.LoraConfig` +
`attn_implementation="sdpa"` · which is the EXACT path used by Bookmaker-8B
(0.467 final eval) and Hack-Deed-Maker-3B (0.5383) on the same Blackwell tier.

ALL hyperparameters identical to Gold Standard · only the model loader changes.

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

MODEL_NAME = "/data2/qwen-3.6-27b"               # local · base downloaded earlier (52 GB)
CANONICAL_BASE = "Qwen/Qwen3.6-27B"              # for manifest provenance
TRAIN_FILE = "/data1/atlas-qwen-27b/train.jsonl"
EVAL_FILE = "/data1/atlas-qwen-27b/eval.jsonl"
OUTPUT_DIR = Path("/data1/atlas-qwen-27b/lora-adapter")
MERGED_DIR = Path("/data1/atlas-qwen-27b/merged")
LOG_DIR = Path("/data1/atlas-qwen-27b/logs")
NAS_MIRROR = Path("/mnt/swarm/model_archives/atlas-qwen-27b")  # best-effort
BUILD_NAME = "Atlas-Qwen-27B"

# ═══════════════════════════════════════════════════════════════════════
# GOLD STANDARD HYPERPARAMETERS · DO NOT CHANGE
# (proven on SwarmCurator-27B-v1 · loss 0.477)
# ═══════════════════════════════════════════════════════════════════════

LORA_R = 64
LORA_ALPHA = 32
LORA_DROPOUT = 0.0
LEARNING_RATE = 1e-5            # PROVEN · NEVER 2e-5+ for 27B
MAX_EPOCH_FRACTION = 0.6
BATCH_SIZE = 1                  # vanilla transformers GC needs batch=1 for 27B safety
GRAD_ACCUM = 32                 # effective batch = 32 (matches Gold Standard target)
MAX_SEQ_LEN = 4096
WARMUP_RATIO = 0.05
WEIGHT_DECAY = 0.01
LR_SCHEDULER = "cosine"
EVAL_STEPS = 200
SAVE_STEPS = 200
EARLY_STOPPING_PATIENCE = 3
EARLY_STOPPING_THRESHOLD = 0.001
MAX_EVAL_SAMPLES = 500
SAVE_TOTAL_LIMIT = 5

# Gold Standard target_modules (standard list · GDN params stay frozen)
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


# ═══════════════════════════════════════════════════════════════════════
# DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════

def validate_data(train_path: str, eval_path: str):
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

    print(f"  Train: {train_count:,} records (SHA256: {train_sha[:16]}...)", flush=True)
    print(f"  Eval:  {eval_count:,} records (SHA256: {eval_sha[:16]}...)", flush=True)
    print(f"  System prompt diversity: {len(sys_prompts)} unique", flush=True)

    if train_count < 1000:
        raise ValueError(f"Dataset too small: {train_count} records (min 1000)")
    if len(sys_prompts) < 15:
        print(f"  WARNING: Low system prompt diversity ({len(sys_prompts)}). Target ≥30.", flush=True)

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
            print(f"  WARNING: Dominant prompt at {max_share:.1%} (target <15%)", flush=True)

    return {
        "train_count": train_count,
        "eval_count": eval_count,
        "train_sha256": train_sha,
        "eval_sha256": eval_sha,
        "system_prompt_diversity": len(sys_prompts),
        "max_prompt_share": round(max_share, 4),
    }


# ═══════════════════════════════════════════════════════════════════════
# TRAINING (vanilla transformers + peft)
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description=f"Train {BUILD_NAME} (Gold Standard recipe · vanilla stack)")
    parser.add_argument("--smoke-test", action="store_true",
                        help="500 samples · quick validation")
    parser.add_argument("--pilot", action="store_true",
                        help="5000 samples · medium run")
    parser.add_argument("--max-seq-len", type=int, default=MAX_SEQ_LEN)
    parser.add_argument("--resume", type=str,
                        help="Resume from checkpoint path (ONLY if same LR/config)")
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, EarlyStoppingCallback
    from peft import LoraConfig, get_peft_model
    from trl import SFTTrainer, SFTConfig
    from datasets import load_dataset

    print("=" * 70, flush=True)
    print(f"  {BUILD_NAME} · GOLD STANDARD recipe · vanilla stack (sm_120 / Blackwell)", flush=True)
    print(f"  Base:       {MODEL_NAME}", flush=True)
    print(f"  Method:     bf16 LoRA r={LORA_R} alpha={LORA_ALPHA}", flush=True)
    print(f"  LR:         {LEARNING_RATE}", flush=True)
    print(f"  Batch:      {BATCH_SIZE} x {GRAD_ACCUM} = {BATCH_SIZE * GRAD_ACCUM} effective", flush=True)
    print(f"  Max Seq:    {args.max_seq_len}", flush=True)
    print(f"  Scheduler:  {LR_SCHEDULER}", flush=True)
    print(f"  GPU:        {torch.cuda.get_device_name(0)}", flush=True)
    print(f"  VRAM:       {torch.cuda.get_device_properties(0).total_memory / 1e9:.0f} GB", flush=True)
    print(f"  Attention:  sdpa  (sm_120 compatible · NOT FA2)", flush=True)
    if args.smoke_test:
        print(f"  Mode:       SMOKE TEST (500 samples)", flush=True)
    elif args.pilot:
        print(f"  Mode:       PILOT (5000 samples)", flush=True)
    else:
        print(f"  Mode:       FULL · Block-1-v3 (486K records)", flush=True)
    print("=" * 70, flush=True)

    print("\n[0/5] Validating data...", flush=True)
    data_info = validate_data(TRAIN_FILE, EVAL_FILE)

    print(f"\n[1/5] Loading {MODEL_NAME} (27B bf16 · sdpa attn · ~54 GB)...", flush=True)
    t = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    print(f"      tokenizer loaded · {time.time()-t:.1f}s", flush=True)

    t = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="sdpa",         # Blackwell sm_120 compatible
        trust_remote_code=False,
        low_cpu_mem_usage=True,
    )
    model.config.use_cache = False
    print(f"      base model loaded · {time.time()-t:.1f}s", flush=True)
    print(f"      GPU mem: {torch.cuda.memory_allocated(0)/1e9:.1f} GB", flush=True)

    print("[2/5] Attaching LoRA adapter (r=64 · α=32 · standard target_modules)...", flush=True)
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        target_modules=TARGET_MODULES,
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    trainable, total = 0, 0
    for p in model.parameters():
        total += p.numel()
        if p.requires_grad:
            trainable += p.numel()
    print(f"      trainable: {trainable:,} / {total:,} ({100 * trainable / total:.3f}%)", flush=True)

    print("[3/5] Loading dataset...", flush=True)
    train_dataset = load_dataset("json", data_files=TRAIN_FILE, split="train")
    eval_dataset = load_dataset("json", data_files=EVAL_FILE, split="train")

    if args.smoke_test:
        train_dataset = train_dataset.select(range(min(500, len(train_dataset))))
        eval_dataset = eval_dataset.select(range(min(50, len(eval_dataset))))
    elif args.pilot:
        train_dataset = train_dataset.select(range(min(5000, len(train_dataset))))
        eval_dataset = eval_dataset.select(range(min(200, len(eval_dataset))))

    def format_chat(example):
        # enable_thinking=False · matches SwarmCapitalMarkets-27B (the predecessor
        # cook that produced the original Atlas v1 weights). Our pairs have direct
        # responses · no <think>...</think> blocks · we don't want the chat template
        # to inject them and contaminate the training token stream.
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
            enable_thinking=False,
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

    if len(eval_dataset) > MAX_EVAL_SAMPLES:
        print(f"  Capping eval from {len(eval_dataset):,} to {MAX_EVAL_SAMPLES}", flush=True)
        eval_dataset = eval_dataset.select(range(MAX_EVAL_SAMPLES))

    eff_batch = BATCH_SIZE * GRAD_ACCUM
    full_epoch_steps = len(train_dataset) // eff_batch
    max_steps = max(int(full_epoch_steps * MAX_EPOCH_FRACTION), 5)

    print(f"  Train: {len(train_dataset):,} | Eval: {len(eval_dataset):,}", flush=True)
    print(f"  Eff batch:     {eff_batch}", flush=True)
    print(f"  Full epoch:    {full_epoch_steps} steps", flush=True)
    print(f"  Max steps:     {max_steps} (capped at {MAX_EPOCH_FRACTION} epoch · early stop may fire sooner)", flush=True)

    print("[4/5] Configuring trainer...", flush=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    sft = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        max_steps=max_steps,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=GRAD_ACCUM,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        learning_rate=LEARNING_RATE,
        lr_scheduler_type=LR_SCHEDULER,
        warmup_ratio=WARMUP_RATIO,
        weight_decay=WEIGHT_DECAY,
        bf16=True,
        max_length=args.max_seq_len,                    # TRL 0.24 (was max_seq_length)
        dataset_text_field="text",
        completion_only_loss=False,                     # match prior cooks · whole-sequence loss
        eval_strategy="steps",
        eval_steps=EVAL_STEPS if not args.smoke_test else max(2, max_steps // 3),
        save_strategy="steps",
        save_steps=SAVE_STEPS if not args.smoke_test else max(2, max_steps // 3),
        save_total_limit=SAVE_TOTAL_LIMIT,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        logging_steps=5 if args.smoke_test else 25,
        seed=42,
        data_seed=42,
        dataloader_num_workers=2,
        remove_unused_columns=False,
        ddp_find_unused_parameters=False,
        optim="adamw_torch",
    )

    trainer = SFTTrainer(
        model=model,
        args=sft,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=EARLY_STOPPING_PATIENCE,
                early_stopping_threshold=EARLY_STOPPING_THRESHOLD,
            ),
        ],
    )

    print("\n" + "=" * 70, flush=True)
    print(f"  TRAINING START · {BUILD_NAME}", flush=True)
    print(f"  LR={LEARNING_RATE}, batch={eff_batch}, scheduler={LR_SCHEDULER}", flush=True)
    print(f"  Early stopping: patience={EARLY_STOPPING_PATIENCE}, threshold={EARLY_STOPPING_THRESHOLD}", flush=True)
    print("=" * 70, flush=True)

    if args.resume:
        result = trainer.train(resume_from_checkpoint=args.resume)
    else:
        result = trainer.train()

    elapsed = time.time() - t0

    print("\n" + "=" * 70, flush=True)
    print(f"  TRAINING COMPLETE · {BUILD_NAME}", flush=True)
    print(f"  Loss:    {result.training_loss:.4f}", flush=True)
    print(f"  Steps:   {result.global_step}", flush=True)
    print(f"  Time:    {elapsed/3600:.2f}h ({elapsed/60:.0f}m)", flush=True)
    print("=" * 70, flush=True)

    print(f"\n[5/5] Saving adapter to {OUTPUT_DIR}...", flush=True)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"      adapter saved", flush=True)

    print("\n  Merging LoRA adapter into base for deployment...", flush=True)
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    merged_model = trainer.model.merge_and_unload()
    merged_model.save_pretrained(str(MERGED_DIR), safe_serialization=True, max_shard_size="5GB")
    tokenizer.save_pretrained(str(MERGED_DIR))
    print(f"      merged: {MERGED_DIR}", flush=True)

    try:
        if NAS_MIRROR.parent.exists():
            print(f"\n  Mirroring to NAS at {NAS_MIRROR}...", flush=True)
            NAS_MIRROR.mkdir(parents=True, exist_ok=True)
            os.system(f"rsync -a {OUTPUT_DIR}/ {NAS_MIRROR}/lora-adapter/ 2>&1")
            os.system(f"rsync -a {MERGED_DIR}/ {NAS_MIRROR}/merged/ 2>&1")
            print(f"  NAS mirror complete", flush=True)
        else:
            print(f"  NAS mount missing · skipping mirror (run manually post-cook)", flush=True)
    except Exception as e:
        print(f"  WARN · NAS mirror skipped: {e}", flush=True)

    manifest = {
        "model": BUILD_NAME,
        "base_local_path": MODEL_NAME,
        "base_canonical": CANONICAL_BASE,
        "architecture": "Qwen3_5ForConditionalGeneration · hybrid GDN + standard attention",
        "method": f"bf16 LoRA r={LORA_R} alpha={LORA_ALPHA}",
        "stack": "vanilla transformers + peft + trl + sdpa attn (sm_120 compat)",
        "config_source": "Swarm Gold Standard (SwarmCurator-27B-v1 · loss 0.477)",
        "stack_deviation": "Unsloth dropped due to FA2 sm_120 incompatibility · all "
                           "hyperparameters identical · vanilla path validated on "
                           "Bookmaker-8B + Hack-Deed-Maker-3B Granite cooks",
        "data": {
            "block_version": "Royal Jelly CRE Block-1-v3 (Path B · BALANCED)",
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
            "early_stopping_patience": EARLY_STOPPING_PATIENCE,
            "epoch_fraction": MAX_EPOCH_FRACTION,
            "attention_impl": "sdpa",
        },
        "hardware": {
            "gpu": torch.cuda.get_device_name(0),
            "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9),
            "power_limit_w": 550,
        },
        "gold_standard_reference": {
            "model": "SwarmCurator-27B-v1",
            "loss": 0.4766,
            "steps": 1000,
            "elapsed_hours": 14.38,
        },
        "lineage": {
            "atlas_v1_status": "vanished · weights lost · this is the rebuild",
            "atlas_v1_foundation_in_block_1_v3": 12797,
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
    print(f"\n  Manifest:  {manifest_path}", flush=True)


if __name__ == "__main__":
    main()
