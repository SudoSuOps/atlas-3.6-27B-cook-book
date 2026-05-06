# Gold Standard Lineage

How we got from "what works for Qwen 27B" to this cook · the chain of proven
builds that define the recipe we're inheriting.

---

## The chain

```
═══════════════════════════════════════════════════════════════════════════
  PROVEN CHAIN of Qwen3.5 cooks (the Gold Standard family)
═══════════════════════════════════════════════════════════════════════════

SwarmCurator-9B-Phase1            Qwen3.5-9B    27,436 pairs   500 steps    loss 0.665    2.49h
                                  ↓ established LR 1e-5, packing, AutoTokenizer bypass

SwarmCurator-9B-Phase2            Qwen3.5-9B    22,132 pairs   414 steps    loss 0.707    3.37h
                                  ↓ proved clean retrain from base > continue from merged

SwarmCurator-2B-v1                Qwen3.5-2B     8,963 pairs   224 steps    loss 0.880    0.54h
                                  ↓ proved tier-specific adjustments (LR 2e-5, r=32)

SwarmCurator-27B-v1               Qwen3.5-27B   62,525 pairs  1000 steps    loss 0.477   14.38h
                                  ↓ THE GOLD STANDARD reference build · all future
                                    27B cooks inherit this config

SwarmCapitalMarkets-27B           Qwen3.5-27B   45,039 pairs   844 steps    loss TBD    ~12h est
                                  ↓ sibling cook on overlapping CRE corpus
                                    (validates Gold Standard transfers to capital-markets domain)

═══════════════════════════════════════════════════════════════════════════
                           ↓ THIS COOK ↓
═══════════════════════════════════════════════════════════════════════════

Atlas-Qwen-27B (rebuild)          Qwen3.6-27B  407,076 pairs  ~step TBD    loss TBD    ~30-35h est
                                  · same architecture class as Qwen3.5
                                  · same Gold Standard recipe (verbatim)
                                  · larger corpus (Block-1-v2 · 6.5× SwarmCurator's)
                                  · the rebuild of Atlas on the substrate that worked
```

---

## The lessons each prior cook locked

### From SwarmCurator-9B-Phase1 (the first successful Qwen3.5 build on Blackwell)

```
✓ Established LR 1e-5 as the right rate for Qwen3.5 narrative work
  (initial attempts at 2e-5 overshot on clean data · permanent rule for 9B+)
✓ Established the AutoTokenizer bypass discipline
  (Unsloth's tokenizer dispatch is broken for Qwen3.5 VL models)
✓ Established `format_chat` using default `apply_chat_template`
  (no enable_thinking override · let the model emit <think> if it wants)
✓ Established system prompt diversity ≥ 30 unique
  (fewer = template memorization → garbage)
✓ Proved bf16 LoRA outperforms QLoRA on Qwen3.5 architecture
  (higher quantization error in 3.5 vs predecessors)
```

### From SwarmCurator-9B-Phase2

```
✓ "Clean retrain from base" rule
  Don't continue from merged checkpoints · always start LoRA fresh on base
  weights · proven 0.707 (from base) vs hypothetical "continue" path
✓ System prompt diversity scales · 43 unique prompts in P2 (30 from P1 + 13 new)
  produced cleanly · diversity is additive
```

### From SwarmCurator-2B-v1

```
✓ Tier-specific adjustments are NOT deviations · they're calibrated
  - 2B: LR 2e-5 · r=32 · α=16 · epoch 0.8 · seq 2048
  - These are proven settings for the SMALL tier · NOT the 27B/9B settings
  - The 27B/9B Gold Standard stays at LR 1e-5 · r=64 · α=32 · epoch 0.6
✓ Effective batch = 32 holds across all tiers (different batch/grad-accum mix)
```

### From SwarmCurator-27B-v1 (THE Gold Standard)

```
✓ THE reference build · all future 27B cooks measure against 0.477
✓ 1000 steps was when early stopping triggered (max was 1171 · would've gone further
  but loss plateau triggered patience=3)
✓ Packing was skipped by Unsloth VL detection · STILL hit 0.477 · packing is
  preferred but not required
✓ 63 unique system prompts (well above the ≥30 minimum)
✓ Throughput: 88 tok/s × 4 concurrent on Blackwell (the production-serving baseline)
✓ Q4_K_L GGUF deploys on RTX 3090 24GB at 35 tok/s with 262K context
  (the desk-edge inference receipt)
```

### From SwarmCapitalMarkets-27B (the sibling validation)

```
✓ Validated Gold Standard transfers to CRE-specific corpus
  (45K pairs · same recipe · expected loss in similar range)
✓ Documented "killed builds" discipline:
  - Attempt 1: ran with LR 2e-5 instead of 1e-5 · KILLED at step ~205 ·
    optimizer states were "toxic" with wrong LR · purged checkpoint-200 ·
    fresh restart from step 0
  - Lesson: ALWAYS verify against Gold Standard config before launch ·
    no shortcuts · wrong-LR optimizer states are non-recoverable
✓ Documented "killall python3 hazard":
  - Clearing stuck vLLM processes via killall took out the training process
  - Lesson: NEVER killall python3 on a training box · use specific PIDs
```

---

## Why we trust this lineage for Qwen3.6

Qwen kept `architectures: ["Qwen3_5ForConditionalGeneration"]` for the 3.6 family.
Same class. Same code path. Same Unsloth registration. Same target_modules. Same
hyperparameter sensitivity profile. **The Gold Standard transfers.**

What's different in 3.6 (per Qwen's release notes):
- Improved pre-training data
- Stronger coding benchmarks (SWE-bench, Terminal-Bench)
- Native multimodal thinking + non-thinking modes

None of those changes break the proven cook recipe. They give us a stronger
starting point for the same SFT we'd run on 3.5.

---

## Build checklist (inherited from Gold Standard repo · enforced for THIS cook)

Before launching Atlas-Qwen-27B:

```
[ ] Verify LR = 1e-5  (NEVER 2e-5+)
[ ] Verify bf16 LoRA  (NOT QLoRA, NOT fp16)
[ ] Verify r=64, alpha=32
[ ] Verify effective batch = 32  (batch=2 × grad_accum=16 on single GPU)
[ ] Verify epoch fraction = 0.6
[ ] Verify early stopping: patience=3, threshold=0.001
[ ] Verify load_best_model_at_end=True
[ ] Verify dataset SHA256 matches Block-1-v2 manifest
    (train.jsonl  4d90e676442738c4...)
    (eval.jsonl   7f025a264210174a...)
[ ] Verify system prompt diversity ≥ 30  (Block-1-v2 has 19 source buckets · plenty)
[ ] Verify AutoTokenizer.from_pretrained() bypass (NOT Unsloth's tokenizer)
[ ] Verify format_chat uses default apply_chat_template
    (no enable_thinking override · let the model emit <think> if it wants)
[ ] Verify training from base model (not merged checkpoint)
[ ] Verify GPU memory sufficient (96GB Blackwell · per gold standard VRAM budget)
[ ] Verify NO other training processes running on target GPU
[ ] Verify rope validation fix applied if on transformers 5.2.0
[ ] Smoke test 500 records first · confirm loss decreases · then full cook
```

---

## See also

- External: [`swarm-qwen-27B-Gold-Standard-Build-LLM`](https://github.com/SudoSuOps/swarm-qwen-27B-Gold-Standard-Build-LLM)
  · the source of truth for the recipe + the proven build receipts
- `LINEAGE/atlas-27b-v1-vanished.md` · what we know about the original Atlas-27B
  (the cook this rebuild brings back)
- `COOKS/atlas-qwen-27b.md` · this cook's plan
- `MODELS/qwen-3.6-27b.md` · base model reference
