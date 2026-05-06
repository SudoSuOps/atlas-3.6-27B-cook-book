#!/bin/bash
# Launch Atlas-Qwen-27B cook on swarmrails
# · Single-GPU (Gold Standard recipe · NOT FSDP)
# · CUDA_VISIBLE_DEVICES=0 means GPU 0 (the second card if you want GPU 1, change to =1)
#
# Pre-flight checklist:
#   [ ] /data1/atlas-qwen-27b/train.jsonl exists (Block-1-v2 · sha 4d90e676...)
#   [ ] /data1/atlas-qwen-27b/eval.jsonl  exists (Block-1-v2 · sha 7f025a26...)
#   [ ] No other training process on the target GPU
#   [ ] Qwen3.6-27B base downloaded to HF cache OR /data2/qwen-3.6-27b/
#   [ ] Run --smoke-test first (500 samples · ~10 min) to validate pipeline
#   [ ] Then run full cook (no flag) · ~30-35h ETA
#
# Usage:
#   ./launch_atlas_qwen_27b.sh smoke    # smoke test (500 records)
#   ./launch_atlas_qwen_27b.sh pilot    # pilot (5000 records)
#   ./launch_atlas_qwen_27b.sh full     # FULL COOK · Block-1-v2 (407K records)

set -e

MODE="${1:-smoke}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TRAIN_SCRIPT="$SCRIPT_DIR/train_atlas_qwen_27b.py"
LOG_FILE="/data1/atlas-qwen-27b/cook.log"

mkdir -p /data1/atlas-qwen-27b
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] launching Atlas-Qwen-27B · mode: $MODE" | tee -a "$LOG_FILE"

case "$MODE" in
    smoke)
        FLAG="--smoke-test"
        SCREEN_NAME="atlas-qwen-27b-smoke"
        ;;
    pilot)
        FLAG="--pilot"
        SCREEN_NAME="atlas-qwen-27b-pilot"
        ;;
    full)
        FLAG=""
        SCREEN_NAME="atlas-qwen-27b-cook"
        ;;
    *)
        echo "Usage: $0 [smoke|pilot|full]"
        exit 1
        ;;
esac

screen -dmS "$SCREEN_NAME" bash -c "
  export CUDA_DEVICE_ORDER=PCI_BUS_ID
  export CUDA_VISIBLE_DEVICES=0
  export PATH=/home/swarm/.local/bin:\$PATH
  export TOKENIZERS_PARALLELISM=false
  export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

  echo \"[\$(date -u +%Y-%m-%dT%H:%M:%SZ)] === Atlas-Qwen-27B $MODE launch ===\" | tee -a $LOG_FILE
  python3 $TRAIN_SCRIPT $FLAG 2>&1 | tee -a $LOG_FILE
  echo \"[\$(date -u +%Y-%m-%dT%H:%M:%SZ)] exit code: \$?\" | tee -a $LOG_FILE
"

sleep 3
screen -ls | head -5
echo ""
echo "Cook running in screen: $SCREEN_NAME"
echo "Log: $LOG_FILE"
echo "Attach: screen -r $SCREEN_NAME"
echo "Detach: Ctrl+A then D"
