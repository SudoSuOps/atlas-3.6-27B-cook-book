#!/usr/bin/env python3
"""
fix_vision_config.py · Restore vision_config after Unsloth merge

Unsloth's `save_pretrained_merged` strips the `vision_config` block from
config.json during merge. vLLM needs vision_config because Qwen3.5/3.6 uses
`Qwen3_5ForConditionalGeneration` (VL architecture) even for text-only
fine-tunes. Without this fix, vLLM raises:
  AssertionError at linear.py:1480 · shape mismatch at 75% weight loading

This utility:
  1. Reads the BASE model's config.json from HuggingFace cache
  2. Extracts the vision_config block
  3. Writes it into the merged model's config.json
  4. Validates that out_hidden_size matches text_config.hidden_size

Usage:
    python3 fix_vision_config.py /path/to/merged/ --base Qwen/Qwen3.6-27B

After this fix, vLLM can serve the merged model:
    vllm serve /path/to/merged/ \\
        --dtype bfloat16 \\
        --enforce-eager \\
        --skip-mm-profiling
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("ERROR: huggingface_hub not installed · pip install huggingface_hub")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("merged_dir", type=Path, help="Path to merged model directory")
    parser.add_argument("--base", required=True,
                        help="Base model HF id (e.g., Qwen/Qwen3.6-27B)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change without writing")
    args = parser.parse_args()

    merged_config = args.merged_dir / "config.json"
    if not merged_config.exists():
        print(f"ERROR: merged config not found at {merged_config}")
        sys.exit(1)

    print(f"=== fix_vision_config ===")
    print(f"  merged dir:  {args.merged_dir}")
    print(f"  base model:  {args.base}")
    print()

    # Read merged config
    print(f"[1/4] Reading merged config.json...")
    with open(merged_config) as f:
        merged = json.load(f)

    if "vision_config" in merged:
        print(f"  vision_config already present · no fix needed")
        print(f"  hint: out_hidden_size = {merged['vision_config'].get('out_hidden_size')}")
        return

    # Pull base config
    print(f"[2/4] Downloading base model config.json from {args.base}...")
    base_path = snapshot_download(
        repo_id=args.base,
        allow_patterns=["config.json"],
    )
    base_config_path = Path(base_path) / "config.json"
    with open(base_config_path) as f:
        base = json.load(f)

    if "vision_config" not in base:
        print(f"  ERROR: base model has no vision_config either ·")
        print(f"  this base may not be a VL model · no fix needed")
        sys.exit(1)

    # Extract vision_config
    vision_config = base["vision_config"]
    print(f"  base vision_config out_hidden_size: {vision_config.get('out_hidden_size')}")

    # Validate against text hidden_size
    text_hidden = (merged.get("text_config") or merged).get("hidden_size")
    vision_out_hidden = vision_config.get("out_hidden_size")
    if text_hidden and vision_out_hidden and text_hidden != vision_out_hidden:
        print(f"  WARN: text hidden_size ({text_hidden}) != vision out_hidden_size ({vision_out_hidden})")
        print(f"  this may cause shape mismatches · proceeding anyway")

    # Patch merged config
    print(f"[3/4] Patching merged config.json with vision_config...")
    merged["vision_config"] = vision_config

    # Also patch the architectures field if it was stripped
    if merged.get("architectures") != base.get("architectures"):
        print(f"  note: architectures differ · merged={merged.get('architectures')} "
              f"vs base={base.get('architectures')}")
        print(f"  using base architectures (preserves VL support)")
        merged["architectures"] = base.get("architectures")

    # Preserve image/video token IDs and vision_start/end_token_id
    for key in ("image_token_id", "video_token_id",
                "vision_start_token_id", "vision_end_token_id",
                "language_model_only"):
        if key in base and key not in merged:
            merged[key] = base[key]
            print(f"  added {key} = {base[key]}")

    # Write
    if args.dry_run:
        print(f"\n[4/4] DRY RUN · not writing")
        print(json.dumps(merged, indent=2)[:500] + "...")
        return

    print(f"[4/4] Writing patched config.json...")
    with open(merged_config, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"  done · {merged_config}")
    print()
    print(f"Next: deploy with vllm")
    print(f"  vllm serve {args.merged_dir} --dtype bfloat16 --enforce-eager --skip-mm-profiling")


if __name__ == "__main__":
    main()
