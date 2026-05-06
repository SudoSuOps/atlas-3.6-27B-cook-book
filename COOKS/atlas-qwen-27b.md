# Atlas-Qwen-27B · the cook · Block-1-v2

The rebuild of Atlas-27B on Qwen3.6-27B substrate · using the Swarm Gold
Standard recipe verbatim · cooked on a single RTX PRO 6000 96GB.

---

## Identity

```
Cook name           Atlas-Qwen-27B
Base model          Qwen/Qwen3.6-27B
Base license        Apache 2.0
Architecture        Qwen3_5ForConditionalGeneration · hybrid GDN + GQA
Status              QUEUED · launches when base download completes
                    + smoke test passes
Rig                 swarmrails · 1× RTX PRO 6000 Blackwell 96GB · sm_120
                    (CUDA_VISIBLE_DEVICES=0 · single-GPU · NOT FSDP)
Adapter path        /data1/atlas-qwen-27b/lora-adapter/
Merged path         /data1/atlas-qwen-27b/merged/
NAS mirror          /mnt/swarm/model_archives/atlas-qwen-27b/
Heartbeat           /tmp/atlas-qwen-27b.heartbeat
Defendable          atlas.defendable.eth (the rebuild · same namespace as Atlas-27B v1)
```

---

## The recipe (Gold Standard · proven · do not deviate)

```yaml
name: atlas-qwen-27b
description: bf16 LoRA fine-tune of Qwen3.6-27B on Royal Jelly CRE Block-1-v2
status: queued

base:
  repo: Qwen/Qwen3.6-27B
  license: Apache 2.0
  arch: Qwen3_5ForConditionalGeneration · 64 layers · 5120 hidden · GDN+GQA hybrid · BF16
  family: Qwen3.5/3.6 (architecture class shared between 3.5 and 3.6)

method:
  type: bf16 LoRA · single-GPU · Unsloth FastLanguageModel
  reason: Gold Standard proven on SwarmCurator-27B-v1 (loss 0.477)
          Qwen3.5/3.6 has higher quantization error · NO QLoRA
          Single 96GB card sufficient · multi-GPU FSDP unnecessary at 27B with packing

lora:
  r: 64
  alpha: 32
  dropout: 0.0
  bias: none
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
  notes: standard list · GDN-specific params (in_proj_qkv, in_proj_z, conv1d, A_log,
         dt_bias, etc.) stay frozen · the attention heads + MLP gates carry the
         domain knowledge per SwarmCurator-27B-v1 receipt

training:
  framework: trl SFTTrainer + Unsloth FastLanguageModel
  learning_rate: 1.0e-5             # PROVEN · NEVER 2e-5+ for 27B
  lr_scheduler: cosine
  warmup_ratio: 0.05
  weight_decay: 0.01
  per_device_batch_size: 2          # 27B bf16 is tight on 96GB
  per_device_eval_batch_size: 1     # OOM prevention during eval
  gradient_accumulation_steps: 16
  effective_batch_size: 32
  max_seq_len: 4096
  max_epoch_fraction: 0.6           # 0.6 of one full epoch · prevents memorization
  packing: true                     # may be skipped by Unsloth VL detection · OK
  early_stopping:
    patience: 3
    threshold: 0.001
  load_best_model_at_end: true
  metric_for_best_model: eval_loss
  greater_is_better: false
  eval_steps: 200
  save_steps: 200
  save_total_limit: 5
  max_eval_samples: 500             # without packing 3K+ samples = 34 min/eval
  logging_steps: 10
  optim: adamw_torch
  bf16: true
  use_gradient_checkpointing: unsloth   # Unsloth's optimized GC
  seed: 42

corpus:
  block_version: Royal Jelly CRE Block-1-v3 (Path B · BALANCED)
  train_file: /data1/atlas-qwen-27b/train.jsonl
  eval_file:  /data1/atlas-qwen-27b/eval.jsonl
  train_records: 486,428
  eval_records:  996
  train_sha256: 0f0456356b211cb221314cc47556f135f34a0228b46e324ebfa8acc8960969ac
  eval_sha256:  7f025a264210174a75c5bad30c5f255011e133272ed33a1917798b3085f075cc
  built_at: 2026-05-06T23:36:58Z (88 second build)
  source_count: 41 processed · 34 contributed
  block_summary:
    11-tier source mix · apex doctrine · bee-hive backbone (94K + 8 specialists) ·
    signal_canonical narrative voice (47K) · grants royal_jelly apex (×2 packages) ·
    finance HONEY+JELLY+ROYAL_JELLY (10 packages) · CRE specialty (capital markets +
    blockchain + atlas v1 foundation) · legal expansion · CRE volume ocean (120K of 810K)

steps_math:
  effective_batch:    32
  full_epoch_steps:   486,428 / 32  = 15,200 steps  (one full pass · we'd never run this)
  max_steps:          15,200 * 0.6  = 9,120 steps   (Gold Standard 0.6 epoch cap)
  early_stopping:     likely triggers earlier (SwarmCurator-27B-v1 stopped at 1000 of 1171
                      with patience=3 · same here)
  expected_landing:   somewhere between 2000-4000 steps based on corpus size and
                      typical cosine plateau · loss target < 0.45 (better than 0.477 reference)

hardware:
  rig: swarmrails (192.168.0.100)
  gpu: 1× RTX PRO 6000 Blackwell · 96GB · sm_120
  vram_budget:
    Qwen-27B bf16 model: ~54 GB
    LoRA adapters:       ~0.5 GB
    Optimizer states:    ~1 GB
    Activations (Unsloth GC): ~20 GB
    Batch=2 headroom:    ~20 GB
    Total estimate:      ~96 GB (full card)
  estimated_cook_time_hours: 30-35
  estimated_electrons_cost: ~$10-15

defendable:
  issuer: swarmandbee.eth
  category: atlas.defendable.eth (the rebuild of Atlas-27B v1 namespace)
  anchor_topic: 0.0.10291838
  parent_anchors:
    block_1_v2_corpus_manifest_sha
    gold_standard_recipe_sha
    qwen_3_6_27b_base_config_sha

post_cook_pipeline:
  - merge:           model.save_pretrained_merged · merged_16bit
  - vision_fix:      python3 fix_vision_config.py /data1/atlas-qwen-27b/merged/
                                                  --base Qwen/Qwen3.6-27B
                     (Unsloth strips vision_config · vLLM needs it)
  - manifest:        MANIFEST.json with full provenance
  - nas_mirror:      rsync to /mnt/swarm/model_archives/atlas-qwen-27b/
  - sha_receipts:    sha256 every artifact for the Defendable receipt
  - inference_test:  vllm serve with --enforce-eager --skip-mm-profiling
                     verify model loads and produces valid output
  - assistant_only_eval:  apples-to-apples vs Bookmaker-8B (0.7051/80.17%)
  - correction_loop:      Sessions 6+ in chat UI (8-test broker batch)
```

---

## Pre-cook checklist (Gold Standard discipline · enforce before launch)

```
DATA
  [ ] /data1/atlas-qwen-27b/train.jsonl exists · sha256 starts with 4d90e676...
  [ ] /data1/atlas-qwen-27b/eval.jsonl  exists · sha256 starts with 7f025a26...
  [ ] System prompt diversity ≥ 30 unique (Block-1-v2 has 19 source buckets · plenty)
  [ ] No dominant prompt > 15% of dataset
  [ ] Records ≥ 1000 (we have 407,076)

BASE MODEL
  [ ] Qwen/Qwen3.6-27B downloaded (~54 GB · check HF cache or /data2/qwen-3.6-27b/)
  [ ] config.json verified: architectures = ["Qwen3_5ForConditionalGeneration"]
  [ ] tokenizer.json + tokenizer_config.json present

ENVIRONMENT
  [ ] Unsloth installed (FastLanguageModel registered for Qwen3.5 · transfers to 3.6)
  [ ] transformers version compatible (>= 4.57 for Qwen3.6 base config)
  [ ] PEFT compatible
  [ ] TRL SFTTrainer compatible
  [ ] CUDA_DEVICE_ORDER=PCI_BUS_ID set
  [ ] CUDA_VISIBLE_DEVICES=0 (single GPU · not 0,1)
  [ ] No other training processes running on target GPU (`nvidia-smi`)

CONFIG (the never-deviate list)
  [ ] LR = 1e-5 (NOT 2e-5)
  [ ] r=64 alpha=32 dropout=0.0
  [ ] batch=2 grad_accum=16 (effective 32)
  [ ] max_seq_len=4096
  [ ] max_epoch_fraction=0.6
  [ ] early_stopping patience=3 threshold=0.001
  [ ] AutoTokenizer.from_pretrained() bypass (NOT Unsloth's tokenizer)
  [ ] format_chat default apply_chat_template (no enable_thinking override)

LAUNCH
  [ ] Smoke test first: ./launch_atlas_qwen_27b.sh smoke   (500 records · ~10 min)
  [ ] Verify smoke loss decreases · adapter saves cleanly
  [ ] Then: ./launch_atlas_qwen_27b.sh full                (407K records · ~30-35h)
  [ ] Persistent monitor armed for step events / evals / errors
```

---

## Live trajectory (updates as cook progresses)

```
step       eval_loss   token_acc    timestamp                notes
─────────────────────────────────────────────────────────────────────────────────
launch     ─           ─            TBD                      full cook · Block-1-v2
   200     pending     pending      TBD                      first eval landing
   400     pending     pending      TBD
   600     pending     pending      TBD
   800     pending     pending      TBD
  1000     pending     pending      TBD                      SwarmCurator-27B stopped here
  1500+    pending     pending      TBD                      possibly continues if loss still drops
─────────────────────────────────────────────────────────────────────────────────
```

(Updates as the cook lands · this doc gets the post-cook MANIFEST.json values.)

---

## What this cook unlocks

```
Day +0     Cook launches · single-GPU · ~30-35h wall-clock
Day +1.5   Cook completes · final eval lands · adapter saves to lora-adapter/
Day +1.5   Auto-merge runs (Unsloth save_pretrained_merged · merged_16bit)
Day +1.5   fix_vision_config.py runs to restore vision_config (Unsloth strips)
Day +1.6   MANIFEST.json written with full provenance
Day +1.6   NAS mirror to /mnt/swarm/model_archives/atlas-qwen-27b/
Day +1.7   Run assistant-only eval against the 996-record holdout · apples-to-apples
           vs Bookmaker-8B (0.7051 / 80.17%) and Atlas-70B (1.1739 / 71.70%)
Day +2     Drop in chat UI · run Sessions 6+ correction-loop · 8-test broker batch
Day +2.5   Cookbook write-up · doctrine model decision lock
Day +3     If Atlas-Qwen-27B beats Bookmaker-8B AND passes correction loop:
           → promoted to atlas.defendable.eth (the doctrine slot)
           → original Atlas-27B is back · better · with full receipts
           → AIOV pipeline routes high-stakes valuations through 27B
           → HACKER-AGX provisioning ships Q4_K_M GGUF
```

---

## Why we're not running FSDP

The Gold Standard recipe is single-GPU. Two reasons:

1. **27B BF16 fits on one PRO 6000 96GB.** The VRAM budget (54GB weights + 0.5GB
   adapters + 1GB optimizer + 20GB activations + 20GB headroom = 96GB) leaves
   no benefit to sharding across two cards. FSDP's overhead (FP32 master weights
   + NCCL all-reduce) would actually use MORE memory per card, not less.

2. **Unsloth's gradient checkpointing is more memory-efficient than vanilla GC.**
   That's the difference that makes 27B fit single-GPU. FSDP is built for cases
   where the model itself doesn't fit on one card · for 27B on 96GB it's the
   wrong tool.

The earlier Atlas-Granite-30B attempt used FSDP across 2 cards. That was based
on the wrong substrate family AND a recipe that wasn't proven for our use case.
The 30B Granite kill freed those cards · we use ONE of them for this cook with
the proven recipe.

---

## See also

- `MODELS/qwen-3.6-27b.md` · base model reference
- `LINEAGE/gold_standard_lineage.md` · the proof point chain
- `LINEAGE/atlas-27b-v1-vanished.md` · what was lost
- `COOKS/scripts/train_atlas_qwen_27b.py` · the training script
- `COOKS/scripts/launch_atlas_qwen_27b.sh` · launch wrapper
- `COOKS/scripts/fix_vision_config.py` · post-merge vision config fix
- External: `swarm-qwen-27B-Gold-Standard-Build-LLM` · the source of truth
