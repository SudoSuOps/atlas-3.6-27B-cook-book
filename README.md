# Atlas-Qwen-27B · Cookbook

> Rebuilding Atlas on the substrate that was always right.
>
> **Swarm and Bee LLC** · Florida · D-U-N-S 138652395
>
> **Anchored to the Swarm Gold Standard** — the proven recipe that produced
> SwarmCurator-27B-v1 at loss 0.477 in 14.38h on a single RTX PRO 6000.

---

## What this cook is

**Atlas-Qwen-27B** is the rebuild of the vanished Atlas-27B v1 — the original
broker doctrine model whose weights were lost — on the modern **Qwen3.6-27B**
substrate. Same Defendable namespace at `atlas.defendable.eth`. Same role
(the analyst-tier valuation brain). Same Gold Standard recipe lineage back to
SwarmCurator-27B-v1.

```
LINEAGE
  Atlas-27B v1               Qwen2.5/3.5-based · vanished · no archive
  SwarmCurator-27B-v1        Qwen3.5-27B Dense · 62,525 pairs · loss 0.477 ·
                             14.38h · the receipt that locked the Gold Standard
                             (we're inheriting THIS recipe directly)
  SwarmCapitalMarkets-27B    Qwen3.5-27B Dense · 45,039 pairs · ~12h estimated
                             (sibling cook on overlapping CRE corpus)
  Atlas-Qwen-27B             Qwen3.6-27B base · Block-1-v3 (486K pairs · Path B) ·
                             this cook · the rebuild of Atlas on the proven substrate
                             with the audit-vetted gold pairs from CATALOG.md
```

---

## Why Qwen3.6 — and why we follow the Gold Standard

After running 4 substrate-comparison cooks (Llama-3.3-70B · Granite-4.1-3B/8B/30B)
through a different recipe family, we learned what the Atlas-27B v1 already
proved: **the Qwen substrate + Gold Standard recipe + clean Block corpus is the
combination that produces broker-grade doctrine output**. We're not inventing a
new recipe — we're applying the proven one to the next-gen Qwen base.

**The Gold Standard receipts** (from `swarm-qwen-27B-Gold-Standard-Build-LLM`):

```
Build                         Pairs    Steps   Loss     Time     GPU
SwarmCurator-27B-v1           62,525   1,000   0.477    14.38h   RTX PRO 6000 96GB
SwarmCurator-9B-P1            27,436     500   0.665     2.49h   RTX PRO 6000 96GB
SwarmCurator-9B-P2            22,132     414   0.707     3.37h   RTX PRO 6000 96GB
SwarmCurator-2B-v1             8,963     224   0.880     0.54h   RTX 3090 24GB
SwarmCapitalMarkets-27B       45,039     844   TBD      ~12h     RTX PRO 6000 96GB

GOLD STANDARD CONFIG (proven · do not deviate without a new build to validate)

  base                Qwen3.5/3.6 Dense                    (Qwen3.6-27B for this cook)
  method              bf16 LoRA r=64 α=32 dropout=0.0      single-GPU · NOT FSDP
  learning_rate       1.0e-5                                conservative · NEVER 2e-5+ for 27B
  lr_scheduler        cosine
  warmup_ratio        0.05
  weight_decay        0.01
  batch_size          2                                     27B on 96GB
  grad_accum          16                                    effective batch = 32
  max_seq_len         4096
  epoch_fraction      0.6                                   never full epoch · prevents memorization
  early_stopping      patience=3 · threshold=0.001
  eval_steps          200
  save_steps          200
  load_best_at_end    True                                  best eval-loss checkpoint kept
  packing             True                                  may be skipped by Unsloth VL detection · OK
  quantization        NONE — full bf16                      Qwen3.5/3.6 has higher quantization error
  target_modules      [q_proj, k_proj, v_proj, o_proj,
                       gate_proj, up_proj, down_proj]       standard list · GDN params stay frozen
  framework           Unsloth FastLanguageModel             not vanilla transformers
  tokenizer           AutoTokenizer.from_pretrained()       Unsloth's tokenizer dispatch is broken
                                                             for Qwen3.5/3.6 VL models · always bypass
```

---

## Architecture: Qwen3.6 = Qwen3.5 lineage with new training

Qwen3.6-27B keeps the same architecture class as Qwen3.5: `Qwen3_5ForConditionalGeneration`.
That means **everything proven in the Gold Standard for Qwen3.5 transfers directly
to Qwen3.6** — same Unsloth support, same target_modules, same hyperparameters,
same gotchas.

```
ARCHITECTURE (text)
  Type                hybrid attention · 64 layers
                      75% linear_attention (Gated DeltaNet — GDN)
                      25% full_attention   (standard GQA · every 4th layer)
                      full_attention_interval = 4
  Hidden              5120
  FFN intermediate    17,408
  Attention heads     24 (in full_attention layers)
  KV heads            4  (GQA · 6:1 ratio)
  Head dim            256
  Linear key heads    16 (in linear_attention / GDN layers)
  Linear value heads  48 (in linear_attention / GDN layers)
  Vocab               248,320 (63% larger than Qwen3 · matters for tokenizer mem)
  Context             262,144 native · 1M with YaRN
  RoPE theta          10,000,000
  Tie embeddings      false
  BF16 native

ARCHITECTURE (vision · DISABLED for our text-only CRE cook)
  Vision tower        27 layers · hidden 1152 · 16 heads
  Image / video       reserved tokens 248,056 / 248,057 (we never generate these)
  Vision out_hidden   5120 (must be preserved at deploy via fix_vision_config.py)

WHY GDN MATTERS FOR THIS COOK
  - LoRA targets do NOT include GDN-specific params (in_proj_qkv, in_proj_z,
    in_proj_a, in_proj_b, conv1d, A_log, dt_bias). The Gold Standard says these
    are "fine frozen — the attention heads and MLP gates carry the domain
    knowledge". The 0.477 loss receipt validates this.
  - vLLM serving requires --enforce-eager (GDN's causal_conv1d breaks CUDA graphs)
  - Unsloth packing may be skipped because Qwen3.5/3.6 register as VL · the cook
    still hits target loss without packing per the SwarmCurator-27B-v1 receipt

LICENSE                Apache 2.0 (clean for commercial brokerage use)
```

---

## The cook plan

```
RECIPE         Inherited verbatim from the Gold Standard build of SwarmCurator-27B-v1
               · only the base model and dataset paths change

CORPUS         Royal Jelly CRE Block-1-v2
  train.jsonl  407,076 records · 2.18 GB · sha 4d90e676442738c4...
  eval.jsonl   996 records · 6.3 MB · sha 7f025a264210174a...
  source path  swarmrails:/data1/atlas-qwen-27b/
  19 source buckets (apex doctrine · agent coordination · new economy · grants ·
                     legal · finance · CRE specialty · CRE volume capped 120K of 810K)

HARDWARE       swarmrails @ 192.168.0.100
  GPU          1× RTX PRO 6000 Blackwell 96GB    (single-GPU · NOT FSDP)
  expected     ~96 GB used (per Gold Standard VRAM budget)
  est wall-clock  ~30-35h estimated (extrapolating from 14.38h on 62K pairs ·
                  scaled to 407K pairs at the same recipe · packing throughput)
  electrons    ~$10-15 sovereign compute
  command      CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 \
               python3 train/train_atlas_qwen_27b.py

DEFENDABLE     atlas.defendable.eth (the rebuilt original namespace)
  parent_anchors  Block-1-v2 corpus manifest sha · Gold Standard recipe sha ·
                   base config sha · vision_config fix sha

RECEIPT TARGETS (loose · adjusted as the cook trajectories unfold)
  cook-methodology eval_loss target:  < 0.45  (better than SwarmCurator-27B-v1's 0.477)
  assistant-only target:               < 0.65 / > 82% token acc
  qualitative:                          passes the same correction-loop sessions the
                                        8B/3B did · ideally with the analyst-tier role
                                        cleaner than Bookmaker-8B
```

---

## What this cook unlocks

```
Day +0     Cook launches · single-GPU on swarmrails ·  ~30-35h wall-clock
Day +1.5   Cook completes · final eval lands · adapter saves to /data1/atlas-qwen-27b/lora-adapter/
Day +1.5   Auto-merge runs (model.save_pretrained_merged · Unsloth path)
Day +1.5   fix_vision_config.py runs to restore vision_config (Unsloth strips it during merge)
Day +1.6   MANIFEST.json written with full provenance (data SHA, hyperparams, hardware, timing)
Day +1.7   Run assistant-only eval against the 996-record holdout · apples-to-apples
           vs Bookmaker-8B (0.7051 / 80.17%) and Atlas-70B (1.1739 / 71.70%)
Day +2     Drop in chat UI · run Sessions 6+ correction-loop discipline · 8-test
           broker-realistic batch
Day +2.5   Cookbook write-up · doctrine model decision lock
Day +3     If Atlas-Qwen-27B beats Bookmaker-8B AND passes correction loop:
           → promoted to atlas.defendable.eth (the doctrine slot)
           → AIOV pipeline routes high-stakes valuations through the 27B
           → HACKER-AGX ($2K) provisioning ships Qwen-27B-cooked Q4_K_M GGUF
           → original Atlas-27B is back · better · with full receipts
```

---

## The pipeline this cook plugs into

```
0. HACKER-3B INTAKE      (Hack-Deed-Maker-3B on Granite-4.1-3B)
   the cheap intake bee on every desk
   classifies + extracts deed/lease/OM fields → structured JSON

1. ATLAS-QWEN-27B DRAFT  ← THIS COOK
   the analyst brain in the browser (and the back-office datacenter)
   consumes structured JSON · drafts IC memo + valuation
   under correction-loop-validated system prompts

2. NUMERIC GATE           (deterministic Python · Stage 2)
   re-computes every numeric claim · 6+ rules from the granite-models-cookbooks
   Numeric Gate spec · max 2 retries with structured correction prompts

3. TRIBUNAL              (multi-judge eval · Stage 3)
   honey/jelly/propolis source hierarchy · framing rubric

4. AIOV RENDERS          (Stage 4)
   customer-facing PDF/HTML IC memo · only after stages 1-3 pass

5. HEDERA ANCHORS        (Stage 5)
   Defendable receipt at aiov.defendable.eth/<deal_id>
   parent_anchors point to: Atlas-Qwen-27B weight sha · Block-1-v2 corpus sha ·
   Gold Standard recipe sha · gate ruleset version
```

---

## Repo layout

```
atlas-3.6-27B-cook-book/
├── README.md                          this file
├── LICENSE                            Apache 2.0
├── .gitignore                         weights/corpora never in git
├── MODELS/
│   └── qwen-3.6-27b.md                base model reference · what's different vs 3.5
├── LINEAGE/
│   ├── gold_standard_lineage.md       chain back to SwarmCurator-27B-v1 · the proof point
│   └── atlas-27b-v1-vanished.md       what was lost · what we know about the original
├── COOKS/
│   ├── atlas-qwen-27b.md              this cook · trajectory · live updates as cook progresses
│   └── scripts/
│       ├── README.md                  run order · Qwen-specific gotchas · vision_config fix
│       ├── train_atlas_qwen_27b.py    cook script · forked from gold_standard_27b.py
│       ├── launch_atlas_qwen_27b.sh   the launch command
│       └── fix_vision_config.py       post-merge fix (port from Gold Standard repo)
├── REVIEWS/
│   ├── README.md                      review discipline · template for future cooks
│   └── atlas-qwen-27b-cook-review-chain.md
│                                       full senior-hack review chain · initial → fixes →
│                                       canary → final sign-off · 65-75% → 20-25% probability
│                                       of materially-worse-than-SwarmCurator-27B-v1
├── SKILLS/
│   ├── README.md                      Custom Claude Code skills · operational playbooks
│   ├── canary-then-cook/
│   │   └── SKILL.md                   /canary-then-cook · the 5-stage senior-hack review
│   │                                   discipline that saved this cook · invokable in any
│   │                                   Claude Code session
│   └── gpu-miner-review/
│       └── SKILL.md                   /gpu-miner-review · GPU thermal + power discipline ·
│                                       miner mindset · pre-flight / during-cook / post-cook
│                                       · the 88°C → 500W cap drop locked default
├── AIOV/
│   ├── README.md                      product contract reference
│   └── contracts/
│       ├── deal_input.json            canonical input schema
│       └── decision_output.json       canonical output schema (the AIOV product contract)
└── (future)
    ├── COOKBOOKS/                     Qwen's official cookbooks (annotated for our use)
    └── BEEAI/                         agent runtime integration plan
```

---

## Cross-cookbook references

```
swarm-qwen-27B-Gold-Standard-Build-LLM   The proven Gold Standard recipe + 4
                                          production builds (SwarmCurator + Capital
                                          Markets) · we INHERIT the recipe verbatim
                                          here · do not deviate

granite-models-cookbooks                  The substrate-comparison receipts that
                                          told us "Qwen substrate is right":
                                            - Atlas-70B Llama 0.5018 (the 4-day burn)
                                            - Bookmaker-8B Granite 0.467 (the lift)
                                            - Hack-Deed-3B Granite 0.5383
                                            - Atlas-Granite-30B KILLED pre-step-200
                                          Plus 5 correction-loop sessions + the
                                          Numeric Gate spec + AIOV product pattern
```

---

**Verified · Vetted · Virtu.** The standard isn't *good enough to ship*. The
standard is *something we'd put our own name on*. That holds for this cook too.
