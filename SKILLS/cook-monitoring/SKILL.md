---
name: cook-monitoring
description: Full observability during ML cooks · GPU thermal · loss/eval trajectory · disk · NAS sync · heartbeat · anomaly alerts · feeds the cook flightsheet · the production miner's dashboard
---

# /cook-monitoring · The Cook Telemetry Stack

Every cook running > 4h needs full observability. Step events alone don't
tell you when the disk fills up, the NAS rsync hangs, the card thermal-throttles
silently, or the loss curve plateaus into a wasted run.

This skill defines the canonical monitoring stack we apply to every cook ·
the data flows feed the in-flight section of the cook flightsheet automatically.

---

## When to invoke

```
Trigger:  before firing any cook expected to run > 4h
Trigger:  any cook on a new rig that hasn't been monitored before
Trigger:  diagnosing a cook that appears stuck or producing weird output
Trigger:  setting up the persistent monitor for a multi-day cook
```

---

## The 6 telemetry streams · what to watch

### 1 · Training metrics (loss · grad_norm · lr · token_acc)

```
Source:  cook log file · TRL emits per logging_steps (default 25)
Watch:   loss declining monotone · grad_norm stable (< 1.0) · lr following
         schedule · token_acc tracking up
Anomaly: loss going UP after warmup · grad_norm spikes > 2.0 · loss NaN
         · token_acc plateau > 200 steps without movement

Capture command:
  tail -f cook.log | grep -E "^\\{'loss|^\\{'eval"

Persistent monitor (Claude Code):
  Monitor with command that polls log every 5-10 min · emits on each new
  metric block · flags anomalies on regex match
```

### 2 · Eval trajectory (eval_loss · eval_token_acc)

```
Source:  cook log · TRL emits per eval_steps (default 200)
Watch:   eval_loss declining vs prior eval · monotone improvement preferred
         eval > train loss is healthy (eval is fingerprint-disjoint)
Anomaly: eval_loss INCREASING after step 400 · early-stopping should fire
         · eval_loss plateau > 3 evals without movement (patience triggers)
         · eval_token_acc stuck while eval_loss varies (over-fit signal)

Compare:
  eval_loss vs reference cook (e.g. SwarmCurator-27B-v1 0.477)
  But ONLY trajectory shape · NOT absolute numbers across different corpora
```

### 3 · GPU thermal + power (per /gpu-miner-review)

```
Source:  nvidia-smi · poll every 60-300 sec
Watch:   temp 75-82°C steady · power 80-90% of cap · util 90-100%
Anomaly: temp > 87°C → action per /gpu-miner-review thermal bands
         · util fluctuating (I/O bound · investigate)
         · power cap drift (someone changed it)

Quick check:
  sshpass -p 'mack' ssh swarmrig 'nvidia-smi --query-gpu=index,memory.used,utilization.gpu,power.draw,temperature.gpu --format=csv,noheader'

Sustained dmon snapshot (every hour into cook log):
  sshpass -p 'mack' ssh swarmrig 'nvidia-smi dmon -c 5 -s puct' >> cook_thermal.log
```

### 4 · Disk space + I/O

```
Source:  df + iostat
Watch:   /data1 or /data2 free space · enough for next save_steps checkpoint
         · save_total_limit caps but checkpoint size matters
Anomaly: free space < 50 GB on cook target dir · checkpoint write failures
         · iostat sustained > 80% disk util (slow checkpoint saves)

Quick check:
  ssh swarmrig 'df -h /data1; du -sh /data1/<cook-dir>'

Per-cook estimated disk use:
  base model:               ~52 GB (already there)
  lora-adapter + checkpoints: ~5-10 GB (5 checkpoints × ~1-2 GB each)
  merged model:             ~52 GB (post-cook auto-merge)
  cook log:                 ~50-200 MB
  TOTAL for 27B cook:       ~115-130 GB on cook drive
```

### 5 · NAS mirror status

```
Source:  rsync process · NAS mount df
Watch:   rsync running cleanly · NAS dir size growing toward expected
         · no chgrp errors (or accept as known non-blocker)
Anomaly: rsync hung > 10 min on single file (network issue · NAS stuck)
         · NAS dir size flatlines (rsync silently failed)
         · NAS df at > 90% capacity (out of space soon)

Check:
  ssh swarmrig 'ps -ef | grep rsync | grep -v grep'
  ssh swarmrig 'du -sh /mnt/swarm/model_archives/<cook-name>'
  ssh swarmrig 'df -h /mnt/swarm | tail -2'
```

### 6 · Heartbeat (cook process alive)

```
Source:  process inspection · screen status
Watch:   cook process PID alive · screen attached · log file growing
Anomaly: process dead · screen gone · log file unchanged > 10 min

Check:
  ssh swarmrig 'screen -ls | head -5'
  ssh swarmrig 'ps -p <COOK_PID> -o pid,etime,pcpu,rss,cmd'
  ssh swarmrig 'ls -la <cook_dir>/cook.log'  # mtime
```

---

## The persistent monitor pattern

For any cook expected to run > 4h, arm a persistent Claude Code monitor that
fires on material events:

```python
# Pseudo-code · run via Monitor tool with persistent: true
prev = ""
while True:
    cur = ssh_get_cook_log_tail()
    new_events = filter_for_material(cur, prev)  # step blocks · evals · errors
    if new_events:
        emit(new_events)
    if has_terminal_event(cur):
        emit("---COOK TERMINAL---")
        break
    prev = cur
    sleep(600)  # 10 min poll interval

# Filter regex (only material events surface)
MATERIAL = r"trainable|^\\{'loss|^\\{'eval|TRAINING COMPLETE|exit code|" \
           r"saving model|^Traceback|CUDA error|OutOfMemoryError|" \
           r"FAILED \\[|early_stopping|EarlyStopping"
```

The monitor surfaces:
```
- LoRA attach event (trainable params count)
- Per-step block (every 25 logging_steps · ~30 min on 63 sec/step)
- Per-eval block (every 200 eval_steps · ~3.5h on this cook)
- Save events (checkpoint saved at step N)
- Errors (Traceback · CUDA error · OOM)
- Early stopping (when patience triggers)
- Cook completion (TRAINING COMPLETE / exit code)
```

Surfaces are spaced wide enough that the user isn't notification-spammed ·
but every material event reaches them.

---

## Anomaly playbook (what to do at each)

```
LOSS NaN
  KILL the cook · investigate before resume · likely LR too high or grad clip off

GRAD NORM SPIKE > 2.0
  Watch · if sustained 3+ steps · likely a bad batch or unstable layer
  · if it persists, KILL and re-run from prior checkpoint with lower LR

LOSS PLATEAU > 200 steps
  Could be hitting capacity · could be LR too low · could be early-stopping zone
  · let early-stopping decide · don't manually intervene

EVAL_LOSS RISING after step 400
  Overfit signal · early-stopping should fire (patience=3) · let it
  · if patience already exceeded · you've burned past the optimum · 
    use load_best_model_at_end checkpoint

THERMAL > 87°C
  Per /gpu-miner-review thermal bands · drop power cap immediately

DISK FILLING
  Reduce save_total_limit · or switch save_steps to a wider interval
  · or move oldest checkpoints to NAS to free space

NAS RSYNC HUNG
  Don't kill the cook · just kill the rsync subprocess · cook continues writing
  to local disk · re-mirror manually at end of cook

PROCESS DIED (screen gone)
  Check exit code · if SIGSEGV or OOM kill · investigate before resume
  · resume from latest checkpoint with same recipe · don't change LR mid-cook
```

---

## What the monitor feeds

```
Cook flightsheet · Section 3 (in-flight)
  → step blocks auto-appended
  → eval blocks auto-appended
  → thermal events flagged
  → anomalies + actions logged

/canary-then-cook · Stage 5 review
  → trajectory data for sr hack post-cook review
  → anomaly receipts for the auditor

/client-update · periodic reports
  → status snapshot pulled from monitor stream
```

---

## Anti-patterns this skill prevents

```
× Watching a single metric (just loss) and missing thermal / disk / NAS issues
× Polling every 30 seconds (notification spam · drowns out real events)
× Manual intervention on every step block (let early-stopping decide)
× Discovering disk full at hour 20 (should have caught at projection time)
× NAS rsync silently failing for entire cook (no mirror · weights at risk)
× Monitor not persistent · stops watching when session ends (long cooks need it)
```

---

## Reference receipts

```
Atlas-70B Llama cook · 73h
  Persistent monitor armed · fired on 5 step blocks + 5 evals + completion
  · zero notification spam · every material event surfaced
  · disk monitoring caught a near-fill at hour 60 · save_total_limit reduced
    in time · cook landed clean

Atlas-Qwen-27B canary v6 · 5:42 minutes
  Monitor armed for short canary · fired on trainable / 4 step blocks /
  2 evals / TRAINING COMPLETE · validated end-to-end pipeline

Atlas-Qwen-27B full cook · current
  Persistent monitor armed · 600 sec poll · expected events: 90 step blocks
  · 11 evals · 11 saves · completion · ~24h total

Bookmaker-8B cook · 8.89h on smash
  Monitor caught the eval-loss inflection at step 600 (the moment it beat
  the 70B Llama reference) · receipt grounded for the cookbook
```

---

## Iconic line

> *"Step blocks are signal. Thermal is signal. Disk is signal. NAS sync is*
> *signal. Heartbeat is signal. Loss alone is half the picture."*

---

## See also

- `/gpu-miner-review` · GPU thermal + power discipline (feeds stream 3)
- `/cook-flightsheet` · the formal record this monitor feeds (Section 3)
- `/canary-then-cook` · senior-hack review discipline (uses monitor data)
- `/client-update` · pulls status from this monitor for periodic reports
