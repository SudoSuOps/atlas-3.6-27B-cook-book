# Qwen3.6-27B · base model reference

The substrate for the Atlas rebuild · same architecture class as Qwen3.5
(the Gold Standard substrate) · improved training data and modes.

---

## Identity

```
HuggingFace        Qwen/Qwen3.6-27B
License            Apache 2.0
Architecture class Qwen3_5ForConditionalGeneration  (multimodal native · same as 3.5)
Model type         qwen3_5
Text submodel type qwen3_5_text
Released           April 22, 2026
Context            262,144 tokens native · 1M with YaRN
Multimodal         text + image + video (we use text-only for the CRE cook)
Modes              thinking + non-thinking (single unified checkpoint)
```

---

## Why this base (and not the 35B-A3B sibling)

Qwen3.6 ships in two dense + MoE flavors:
- **Qwen3.6-27B** — dense decoder · the doctrine substrate · this cook
- **Qwen3.6-35B-A3B** — MoE 35B total / 3B active · different architecture class ·
  not a fit for our single-GPU Gold Standard recipe

The 27B is the smallest dense Qwen3.6 variant. It's the closest fit to the
proven SwarmCurator-27B-v1 recipe. The 35B MoE would require recipe rework
(MoE expert routing, different memory profile) that breaks our discipline.

---

## Architecture details

### Text decoder (the part we cook)

```
Layers              64
Hidden size         5120
FFN intermediate    17,408
Vocab size          248,320  (63% larger than Qwen3's 151,936)
RoPE theta          10,000,000
RMS norm eps        1e-6
Tie embeddings      false
Activation          SiLU (SwiGLU pattern in FFN)
Attention bias      false
Attention dropout   0.0
Output gate         attn_output_gate=true (gated output projection)

LAYER PATTERN (the hybrid that defines Qwen3.5/3.6)
  full_attention_interval = 4
  → 75% layers are linear_attention (Gated DeltaNet · GDN)
  → 25% layers are full_attention (standard GQA)
  → block of 4: linear · linear · linear · full · (repeats × 16)

FULL_ATTENTION (every 4th layer · 16 of 64)
  num_attention_heads     24
  num_key_value_heads     4    (GQA · 6:1 reduction)
  head_dim                256

LINEAR_ATTENTION / GDN (3 of every 4 layers · 48 of 64)
  linear_num_key_heads    16
  linear_num_value_heads  48
  linear_key_head_dim     128
  linear_value_head_dim   128
  linear_conv_kernel_dim  4
  output_gate_type        swish
  mamba_ssm_dtype         float32   (sensitive to precision · keep FP32)
```

### Vision tower (kept in checkpoint · stays frozen during text-only cook)

```
Depth                27 layers
Hidden size          1152
Intermediate size    4304
Num heads            16
Patch size           16
Spatial merge size   2
Temporal patch size  2
Out hidden size      5120  (must match text hidden_size at deploy)
Image token id       248,056
Video token id       248,057
Vision start token   248,053
Vision end token     248,054
```

---

## Why Qwen3.6 transfers from the Qwen3.5 Gold Standard

The architecture class `Qwen3_5ForConditionalGeneration` is preserved between
3.5 and 3.6 — Qwen kept the same code path and architecture, with new pre-train
data and improved alignment. This is critical for us because:

1. **Unsloth support transfers.** Unsloth's FastLanguageModel registered Qwen3.5
   support · the same code path loads Qwen3.6 because the architecture class is
   identical. (Verify at smoke test · if Unsloth checks model_id-specific
   compatibility, we may need to override.)

2. **LoRA target_modules transfer.** The same `[q_proj, k_proj, v_proj, o_proj,
   gate_proj, up_proj, down_proj]` standard list applies. GDN params stay
   frozen (proven on SwarmCurator-27B-v1).

3. **Hyperparameters transfer.** LR 1e-5 · cosine · batch 2 grad-accum 16 · max
   seq 4096 · epoch 0.6 · early stopping patience 3 — all proven on 3.5 27B
   Dense · same architecture means same optimal settings.

4. **Vision config behavior transfers.** Unsloth strips vision_config on merge ·
   we apply `fix_vision_config.py` post-merge to restore it (with out_hidden_size=5120).

---

## Inference cost-class

```
27B Dense BF16 weights              ~54 GB on disk · ~58 GB RAM with overhead
Q4_K_M GGUF                         ~16-17 GB on disk · runs on RTX 3090 24GB ·
                                    ~35 tok/s with --enforce-eager
INT8 vLLM                           ~30 GB · 1× RTX PRO 6000 96GB · 88 tok/s × 4 concurrent
INT4 AWQ (HACKER-AGX target)        ~15-17 GB · AGX Orin 64GB at 4-bit · feasible
Q4_K_M Jetson edge                  ~17 GB at INT4 GGUF · doesn't fit Orin Nano 8GB ·
                                    requires AGX Orin 64GB minimum for the 27B
```

---

## What's NEW in Qwen3.6 vs Qwen3.5 (per Qwen's release notes)

```
Coding capability                   Qwen3.6-27B beats Qwen3.5-397B-A17B on every
                                    major coding benchmark:
                                      SWE-bench Verified    77.2 vs 76.2
                                      SWE-bench Pro         53.5 vs 50.9
                                      Terminal-Bench 2.0    59.3 vs 52.5
                                    27B params vs 397B total / 17B active = ~15× smaller
                                    (this matters for our HACK-DG / Hack-fleet work · not
                                     necessarily for the doctrine model)

Multimodal                          Native vision-language thinking + non-thinking
                                    in one unified checkpoint
                                    (we don't use this in the CRE cook · the vision
                                     tower stays frozen)

Reasoning                           Strong across text + multimodal · supports thinking
                                    mode by default · `<think>...</think>` blocks emitted
                                    automatically · suppress with chat_template_kwargs
                                    enable_thinking=False if we want clean output

License                             Apache 2.0 (same as 3.5)
```

For OUR cook (CRE doctrine · text-only), the relevant Qwen3.6 improvements are
the underlying training data quality and the more recent transformers compat
(less risk of architectural drift between cook-time and deploy-time).

---

## Deployment notes (post-cook)

After the cook completes and Unsloth's `save_pretrained_merged` produces the
merged model:

```bash
# 1. Restore vision_config (Unsloth strips it during merge)
python3 deploy/fix_vision_config.py /data2/atlas-qwen-27b/merged/ \
    --base Qwen/Qwen3.6-27B

# 2. vLLM serve
vllm serve /data2/atlas-qwen-27b/merged/ \
    --dtype bfloat16 \
    --enforce-eager \
    --skip-mm-profiling \
    --max-model-len 32768

# Without --enforce-eager: GDN's causal_conv1d kernel breaks CUDA graphs.
# Without --skip-mm-profiling: vLLM tries to load image processor (fails · we don't ship images).
# --max-model-len 32768: comfortable for IC memos · 262K full context not needed for serving.
```

For Q4_K_M GGUF deployment to RTX 3090 24GB or AGX Orin 64GB:

```bash
# Convert to GGUF (post-merge)
python3 -m llama.cpp.convert_hf_to_gguf /data2/atlas-qwen-27b/merged/ \
    --outfile /data2/atlas-qwen-27b/atlas-qwen-27b.gguf

# Quantize Q4_K_M (best size/quality trade for 27B class)
./llama-quantize /data2/atlas-qwen-27b/atlas-qwen-27b.gguf \
    /data2/atlas-qwen-27b/atlas-qwen-27b-q4_k_m.gguf Q4_K_M

# Serve on RTX 3090 24GB
llama-server -m /data2/atlas-qwen-27b/atlas-qwen-27b-q4_k_m.gguf \
    -ngl 99 -c 32768 -fa on \
    --cache-type-k q4_0 --cache-type-v q4_0
```

---

## See also

- `COOKS/atlas-qwen-27b.md` · the cook plan with the locked Gold Standard recipe
- `COOKS/scripts/train_atlas_qwen_27b.py` · the training script (forked from Gold Standard)
- `COOKS/scripts/fix_vision_config.py` · post-merge config fix
- `LINEAGE/gold_standard_lineage.md` · the proof-point chain back to SwarmCurator-27B-v1
- External: [`swarm-qwen-27B-Gold-Standard-Build-LLM`](https://github.com/SudoSuOps/swarm-qwen-27B-Gold-Standard-Build-LLM)
  · the source of truth for the recipe
