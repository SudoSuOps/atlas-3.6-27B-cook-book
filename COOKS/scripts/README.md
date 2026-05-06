# Atlas-Qwen-27B · cook scripts

The artifacts that build and run the Atlas-Qwen-27B cook on Royal Jelly CRE
Block-1-v2 corpus, using the Swarm Gold Standard recipe.

```
train_atlas_qwen_27b.py    Cook script · forked verbatim from gold_standard_27b.py
                           · only the CONFIG section changed (paths + base + name)
                           · Gold Standard hyperparameters DO NOT CHANGE

launch_atlas_qwen_27b.sh   Bash wrapper · launches in screen · CUDA_VISIBLE_DEVICES=0
                           · supports smoke / pilot / full modes

fix_vision_config.py        Post-merge utility · restores vision_config that
                            Unsloth strips during save_pretrained_merged
                            · required before vLLM serving
```

---

## Run order

```bash
# 0. Pre-cook checklist (do these once)
#    [ ] Block-1-v2 corpus at /data1/atlas-qwen-27b/{train,eval}.jsonl
#    [ ] Qwen3.6-27B base downloaded (HF cache or /data2/qwen-3.6-27b/)
#    [ ] No other training processes on the GPU
#    [ ] Unsloth + transformers + TRL versions compatible

# 1. Smoke test (500 records · ~10 min)
./launch_atlas_qwen_27b.sh smoke

# Watch the log:
tail -f /data1/atlas-qwen-27b/cook.log

# Verify smoke success criteria:
#   - tokenizer loads (AutoTokenizer bypass works)
#   - base model loads (no Unsloth compatibility errors)
#   - LoRA attaches (target_modules valid for hybrid architecture)
#   - first step runs (loss is finite, gradients flow)
#   - first eval runs (loss is in plausible range 1.0-3.0)
#   - adapter saves at step ~100 (save mechanism works)

# 2. Full cook (407K records · ~30-35h)
./launch_atlas_qwen_27b.sh full

# 3. Post-cook (after training completes · auto-runs from train script)
#    The train script auto-merges and writes MANIFEST.json
#    Then run vision config fix:
python3 fix_vision_config.py /data1/atlas-qwen-27b/merged/ \
    --base Qwen/Qwen3.6-27B

# 4. Deploy (vLLM serve)
vllm serve /data1/atlas-qwen-27b/merged/ \
    --dtype bfloat16 \
    --enforce-eager \
    --skip-mm-profiling \
    --max-model-len 32768

# 5. Mirror to NAS (auto-runs in train script · run manually if it failed)
rsync -a /data1/atlas-qwen-27b/{lora-adapter,merged,MANIFEST.json} \
    /mnt/swarm/model_archives/atlas-qwen-27b/
```

---

## Qwen-specific gotchas (collected from Gold Standard repo experience)

```
1. AutoTokenizer bypass · MANDATORY
   Unsloth's tokenizer dispatch is broken for Qwen3.5/3.6 VL models.
   Always use AutoTokenizer.from_pretrained() directly · the train script does this.
   The reference: SwarmCurator-27B-v1 README "AutoTokenizer bypass · Unsloth's
   tokenizer dispatch is broken for Qwen3.5 VL models. Always use
   AutoTokenizer.from_pretrained() directly."

2. Packing may be skipped · OK
   Unsloth detects Qwen3.5/3.6 as a VL model and skips packing for safety.
   The cook still hits target loss without packing per SwarmCurator-27B-v1
   receipt (loss 0.477 with skipped packing). Don't fight this.

3. NO QLoRA
   Qwen3.5/3.6 has higher quantization error than predecessors. bf16 LoRA only.
   load_in_4bit=False is set in the train script · do not change.

4. Single GPU · NOT FSDP
   The Gold Standard is single-GPU (CUDA_VISIBLE_DEVICES=0). 27B fits on 96GB
   with Unsloth's optimized GC. FSDP is the wrong tool for this scale on this
   hardware.

5. Vision config strip
   Unsloth's `save_pretrained_merged` strips `vision_config` from config.json.
   vLLM needs it because Qwen3.5/3.6 architecture is `Qwen3_5ForConditionalGeneration`
   (VL even for text-only fine-tunes).
   
   Without the fix · vLLM raises AssertionError at linear.py:1480 (shape mismatch
   at 75% weight loading).
   
   Always run `fix_vision_config.py` after merge.

6. --enforce-eager required for vLLM
   Qwen3.5/3.6 uses Gated DeltaNet (GDN) for 75% of layers. GDN's `causal_conv1d`
   kernel breaks CUDA graphs · vLLM's default graph capture fails.
   --enforce-eager forces eager execution · ~10% throughput hit, but stable.

7. --skip-mm-profiling required for vLLM (text-only deploy)
   We don't ship vision · vLLM's multimodal profiling tries to run image processor
   forward passes that fail on a text-only deployment.

8. Don't continue from merged · always retrain from base
   "Clean retrain from base" is a Gold Standard rule. Don't continue LoRA
   training from a merged checkpoint · always start fresh on base weights.

9. LR sensitivity
   1e-5 is PROVEN. 2e-5 has overshot multiple times (SwarmCapitalMarkets-27B
   attempt 1 was killed at step 205 with toxic optimizer states). Don't try
   "just slightly higher".

10. Optimizer states are toxic if cooked with wrong LR
    If a cook is killed mid-run because of wrong LR · purge the checkpoint
    directory · don't try to "fix and resume" · the Adam states are unrecoverable.
```

---

## Compatibility matrix

```
Component         Tested compatible            Notes
─────────────────────────────────────────────────────────────────────────────
Unsloth           Latest stable                Gold Standard built on Unsloth pre-Mar 2026
                                                · verify FastLanguageModel registers Qwen3.6
                                                · if not, may need to pin transformers + use
                                                  vanilla TRL with manual LoRA setup
transformers      >= 4.57 (Qwen3.6 metadata)   Qwen3.6 config.json says transformers_version 4.57.1
                  Avoid 5.2.0 (rope bug)        See fixes/rope_validation.md in Gold Standard repo
TRL               0.12+                         SFTTrainer + SFTConfig
PEFT              0.10+                         LoRA + standard target_modules
torch             2.x with CUDA 12.x
flash-attn        Optional (Unsloth handles)
bitsandbytes      Not used (NO QLoRA)

If Unsloth doesn't yet support Qwen3.6 in the FastLanguageModel registry:
  Fallback option · use vanilla AutoModelForCausalLM + PEFT LoraConfig directly
  · this loses Unsloth's GC efficiency · may need batch_size=1 · still single-GPU
  · validate at smoke test before committing to full cook
```

---

## Receipts (filled in post-cook)

```
TRAIN START         <timestamp>
TRAIN END           <timestamp>
WALL CLOCK          <h>
FINAL EVAL LOSS     <value>
FINAL TRAIN LOSS    <value>
STEPS               <step / max_steps>
EARLY STOPPED       <yes/no · at which step>

SHA256 RECEIPTS
  base config       <sha>
  train.jsonl       4d90e676442738c4...   (Block-1-v2)
  eval.jsonl        7f025a264210174a...   (Block-1-v2)
  adapter_model.safetensors    <sha>
  merged config     <sha>
  MANIFEST.json     <sha>
```

---

## See also

- `COOKS/atlas-qwen-27b.md` · the cook plan
- `MODELS/qwen-3.6-27b.md` · base model reference
- `LINEAGE/gold_standard_lineage.md` · the proof point chain
- External: `swarm-qwen-27B-Gold-Standard-Build-LLM` · source of truth for the recipe
