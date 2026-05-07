---
name: gpu-miner-review
description: Full rig audit + sweet-spot finder + power management for sovereign-compute fleet · the rigs are SR Managing Directors · preserve hardware · 24/7 fleet not one-shot benchmarks · pre-flight + during-cook + post-cook + fleet-wide
---

# /gpu-miner-review · The Rigs Are Senior Managing Directors

> *"A Managing Director took 25 years to develop. You don't burn them out for
> one quarter's bonus. You set them up for sustained excellence, you give
> them what they need to do their best work, and you promote them to harder
> problems as they prove themselves.*
>
> *Our rigs are SMDs. Treat them that way."* — Donovan

The doctrine: sovereign-compute cards (PRO 6000 Blackwell, RTX 5090,
A6000, etc.) cost $4-10K each and can serve for **5-7 years** across
**hundreds of cooks** if treated right · or **6-12 months** if abused.
The marginal 5% throughput from running near thermal/power spec limits is
not worth the 5× lifespan compression.

This skill enforces the SMD discipline across four phases:

1. **Pre-flight** · before firing any cook, validate thermal + power baseline
2. **Cook-time** · monitor + intervene at thermal bands · drop cap before silicon does
3. **Post-cook** · cooldown verification + dmesg event audit
4. **Fleet-wide audit** · periodic sweep · find sweet spots · log card health

---

## When to invoke

```
Trigger:  about to fire any cook expected to run > 4h
Trigger:  any cook running hotter than expected (any card > 80°C sustained)
Trigger:  weekly · run full fleet audit on all rigs
Trigger:  any new rig + GPU combination (validate before first cook)
Trigger:  any change to ambient (room temp, airflow, neighboring loads)
Trigger:  post-cook · validate cards came down clean
Trigger:  any time a card seems "off" · slow training · weird thermals
```

---

## The SMD framing · why it matters

```
SMD MENTALITY                        AMATEUR MENTALITY
─────────────────────────────────────────────────────────────────────────
"How long can this card serve?"      "How fast can this cook run?"
                                     
5-7 year horizon                     1-cook horizon
"earn their slot over years"         "max throughput today"
83-87% TDP cap (sustainable)         100% TDP cap (max benchmark)
75-82°C sustained target             92°C+ thermal throttle
fleet-wide quarterly health check    notice when card dies

VALUE OVER TIME:
  SMD-treated PRO 6000:  6 years × 200 cooks/year = 1200 cooks
  Burnt PRO 6000:        1 year × 200 cooks = 200 cooks · then dies
  
  Same card · same hardware cost · 6× more cook capacity from SMD
  treatment.  This is the whole game.
```

---

## Card thermal/power profiles · the canonical fleet sheet

```
RTX PRO 6000 Blackwell Workstation Edition (96GB · sm_120)
  Spec TDP:        600W
  SMD cap:         500W   (83% spec)
  Sustained safe:  74-82°C at 500W under LoRA cook
  Throttle start:  ~90°C
  Hard limit:      95°C
  Idle baseline:   45-65°C
  $4-10K/card · 6-7 year horizon at SMD discipline

RTX 5090 (32GB · sm_120)
  Spec TDP:        575W
  SMD cap:         500W   (87% spec)
  Sustained safe:  70-80°C at 500W
  Throttle start:  ~90°C

RTX 4500 Ada (32GB · 200W TDP)
  Spec TDP:        200W
  SMD cap:         200W   (already 24/7 sustainable)
  Sustained safe:  60-72°C
  Designed for sustained workloads · keep at spec

RTX 4090 (24GB · 450W)
  Spec TDP:        450W
  SMD cap:         400W   (89% spec)
  Sustained safe:  65-75°C

RTX 3090 / 3090 Ti (24GB)
  Spec TDP:        350W (3090) · 450W (3090 Ti)
  SMD cap:         300W (3090) · 350W (3090 Ti)   (~85% / 78%)
  Sustained safe:  68-78°C

RTX A6000 / A6000 Ada (48GB)
  Spec TDP:        300W (A6000) · 300W (Ada)
  SMD cap:         280W   (already datacenter-grade conservative)
  Sustained safe:  60-72°C

T1000 (4GB · 50W)
  Spec TDP:        50W
  SMD cap:         40W via systemd unit
  Sustained safe:  40-55°C
```

---

## Pre-flight checklist (BEFORE firing a cook)

```
1. POWER CAP · apply per card class (table above)
   sudo nvidia-smi -i <gpu_idx> -pl <smd_cap>
   verify:
   nvidia-smi --query-gpu=index,power.limit,power.max_limit,power.default_limit \
              --format=csv,noheader

2. AMBIENT TEMP CHECK
   · room temp ≤ 24°C ideally · ≤ 28°C absolute max
   · server / rig airflow unobstructed
   · neighboring GPUs idle (multi-card chassis share thermal budget)

3. PRE-COOK BASELINE · snapshot
   nvidia-smi --query-gpu=index,name,temperature.gpu,memory.used,utilization.gpu,power.draw \
              --format=csv,noheader > cook_pre_baseline.csv

4. SCREEN / LOGGING
   · log files write to a known path (greppable post-cook)
   · cook fires inside screen so SSH disconnects don't kill it
```

---

## During-cook · 5 thermal bands

```
< 75°C    SAFE       no action · steady-state target
75-82°C   YELLOW     WATCH · check util · if util < 60% but temp high · airflow issue
82-87°C   ORANGE     DROP power cap by 50W · re-measure in 5 min
87-92°C   RED        DROP cap by 100W IMMEDIATELY · save+pause cook if checkpointable
                     thermal throttle starts here · cook quality at risk
92°C+     CRITICAL   KILL THE COOK · investigate root cause before resume
```

### Quick thermal check (one-liner)

```bash
sshpass -p 'mack' ssh swarmrig 'nvidia-smi --query-gpu=index,memory.used,utilization.gpu,power.draw,temperature.gpu --format=csv,noheader'
```

### Sustained-watch (`dmon` for 30 sec)

```bash
sshpass -p 'mack' ssh swarmrig 'nvidia-smi dmon -c 30 -s puct'
```

---

## Cook algorithm classification (the miner profile)

Before tuning anything · **profile the cook to know what it actually needs.**
Real miners don't tune blind · they classify the algorithm first then apply
the right knob. Same for our cooks.

```
ALGORITHM PROFILES · what each looks like + how to tune

────────────────────────────────────────────────────────────────────────────
CORE-INTENSIVE (compute-bound · "shader-heavy")
  Symptom:    sm_active 90-100% · mem_active 30-50% · power 90%+ of cap
  Examples:   27B+ LoRA training at seq 4096 (large dense matmuls)
              Forward passes during eval on big models
              FSDP_FULL_SHARD with all-gather every layer
  Tuning:     LOCK MEMORY CLOCK DOWN  (sudo nvidia-smi -i N -lmc 9000)
              · no perf hit (memory not bottleneck) · saves 30-50W · cooler
              Keep core clock at default (it's the limiter)
  Power cap:  Standard 83-87% spec (e.g. 500W on PRO 6000)

────────────────────────────────────────────────────────────────────────────
MEMORY-INTENSIVE (bandwidth-bound · "HBM/GDDR-heavy")
  Symptom:    sm_active 30-60% · mem_active 80-100% · power 60-75% of cap
  Examples:   Small-model inference (8B/9B serving with batched requests)
              KV cache replay
              Tokenizer-heavy preprocessing
              Dataset loading bottlenecks (DataLoader)
  Tuning:     LOCK CORE CLOCK DOWN  (sudo nvidia-smi -i N -lgc 0,1500)
              · ~5% perf hit · saves 50-100W · much cooler
              Keep memory clock at default (it's the limiter)
  Power cap:  Can run at 70-75% spec (lower than core-intensive default)

────────────────────────────────────────────────────────────────────────────
MEMORY-CAPACITY BOUND (close-to-OOM · "VRAM-heavy")
  Symptom:    memory.used > 85% of memory.total · sm_active varies
              FSDP all-gather thrashing · activation checkpointing forced
  Examples:   30B+ on a single 96GB card · 27B FSDP with poor GC
              Long-context (128K+) training
  Tuning:     This is a recipe problem · not a tuning problem
              · reduce batch · reduce max_seq_len · enable Unsloth GC
              · or move to multi-GPU FSDP
              · don't touch clocks · won't help

────────────────────────────────────────────────────────────────────────────
I/O BOUND (DataLoader / NAS / disk-heavy)
  Symptom:    GPU sm_active fluctuating · long idle moments between steps
              Disk I/O sustained · network sustained
  Examples:   Cook reading from NAS instead of local NVMe
              Slow tokenization in DataLoader
              num_workers too low for the corpus shape
  Tuning:     Not a GPU tuning problem · fix the data pipeline
              · copy corpus to local NVMe · increase DataLoader num_workers
              · pre-tokenize the corpus
              · then re-profile

────────────────────────────────────────────────────────────────────────────
MIXED (most LoRA cooks 27B+ · 50/50 core/memory)
  Symptom:    sm_active 70-85% · mem_active 60-80% · power 80-90% of cap
  Examples:   Atlas-Qwen-27B LoRA cook (current)
              Bookmaker-8B LoRA on 5090 at seq 4096
  Tuning:     Power cap ONLY · 83-87% of spec (the standard SMD cap)
              · don't lock individual clocks · let GPU manage
              · drop cap if temps escalate
```

### How to PROFILE which class your cook is in

```bash
# 30-second profile during steady-state training
sshpass -p 'mack' ssh swarmrig 'nvidia-smi dmon -c 30 -s puct'

Output columns:
  pwr        power draw (W)
  gtemp      core temp (°C)
  sm         shader/SM utilization %  ← CORE intensity proxy
  mem        memory controller util %  ← MEMORY-BW intensity proxy
  enc / dec  encoder/decoder (irrelevant for us)
  mclk       memory clock MHz
  pclk       core clock MHz

Quick read:
  sm avg > 85 + mem avg < 50      = CORE-INTENSIVE      → memclock-down tuning
  sm avg < 60 + mem avg > 80      = MEMORY-INTENSIVE   → coreclock-down tuning
  sm avg 70-85 + mem avg 60-80    = MIXED              → power cap only
  sm avg fluctuating wildly       = I/O BOUND           → fix data pipeline
  power > 95% cap sustained       = at-the-limit       → cap is binding
  power < 75% cap sustained       = headroom available → can drop cap further
```

### Cook-class profile receipts

```
27B LoRA · seq 4096 · effective_batch 32 · vanilla SDPA on Blackwell
  Profile:   MIXED · sm 75-85% · mem 65-75% · power 80-90% of 500W cap
  Tuning:    Power cap 500W (SMD default) · no clock lock needed
  Empirical: pace 63 sec/step · temp 74°C steady · power 280W avg

8-9B LoRA · seq 4096 · effective_batch 32 · 5090
  Profile:   CORE-INTENSIVE leaning · sm 85-95% · mem 55-65%
  Tuning:    Power cap 500W · could lock memclock to ~9000 MHz to save
             20-30W with zero perf hit
  Empirical: pace 27-30 sec/step · temp 73-79°C · 8.89h cook

3-4B LoRA · 5090
  Profile:   STRONGLY CORE-INTENSIVE · sm 92-98% · mem 40-55%
  Tuning:    Power cap 500W · memclock-down lock RECOMMENDED (saves 30-40W ·
             zero perf · cools 3-5°C)
  Empirical: pace 17-20 sec/step · temp 69-73°C · 5.20h cook

vLLM serving (any model class · interactive batched inference)
  Profile:   MEMORY-INTENSIVE · sm 35-55% · mem 75-90% · KV cache thrash
  Tuning:    Power cap 70-75% spec · core-clock-down lock recommended
  Notes:     Serving rigs benefit MORE from per-clock tuning than cook rigs
             since they run 24/7 at lower load
```

---

## Underclock as second-line defense

If the SMD cap (e.g. 500W) isn't enough · temps stay > 82°C sustained ·
underclock memory + core BEFORE you accept higher temps.

```
Memory underclock (most thermal benefit · least throughput hit):
  sudo nvidia-smi -i <gpu_idx> -lmc 9000      # lock mem clock to 9000 MHz
  
  Effect: ~3-5°C cooler · ~2-3% throughput hit · usually invisible

Core underclock (use only if memory clock alone isn't enough):
  sudo nvidia-smi -i <gpu_idx> -lgc 0,1800    # lock core clock 0-1800 MHz
  
  Effect: ~5-8°C cooler · ~5-10% throughput hit

Reset to default after cook:
  sudo nvidia-smi -i <gpu_idx> -rgc           # reset core clock
  sudo nvidia-smi -i <gpu_idx> -rmc           # reset mem clock
  sudo nvidia-smi -i <gpu_idx> -pl <default>  # reset power cap

When to underclock vs cap drop:
  · cap drop first · simpler · clean
  · underclock if temps still high after cap drop AND cook has 24h+ left
  · for cooks < 4h · just live with marginal heat at the lower cap
```

---

## Cook sweet-spot finder · empirical throughput-per-watt

The 83-87% rule is a heuristic. The empirical sweet spot for a given cook
on a given card may differ. Find it:

```
1. PILOT RUN · 100 steps at 4 power caps (record steady-state pace + temp)
   Card class spec / cap candidates:
     PRO 6000 Blackwell:  cap candidates 400 · 450 · 500 · 550 · 600
     5090:                 cap candidates 400 · 450 · 500 · 550 · 575
     4090:                 cap candidates 350 · 400 · 425 · 450
   
2. MEASURE per cap:
     sec_per_step (avg of last 50 steps · steady state)
     sustained_temp (avg of last 50 steps)
     sustained_power_draw (avg)
   
3. CALCULATE throughput-per-watt:
     tput_per_watt = (1 / sec_per_step) / sustained_power_draw
   
4. PICK the cap that maximizes tput_per_watt UNDER the temp ceiling 82°C
   Usually lands at 75-85% of spec TDP.

5. RECORD the sweet spot in the cookbook for that cook class:
     COOKBOOK/cooks/<name>/sweet_spot.json
     {
       "card": "RTX PRO 6000 Blackwell",
       "cook_class": "27B LoRA r=64 + Block-1-v4 + sdpa",
       "optimal_power_cap_w": 500,
       "sec_per_step_at_optimal": 63,
       "sustained_temp_c": 78,
       "throughput_per_watt": 0.0317,
       "throughput_loss_vs_max": "3-5%",
       "thermal_margin_c": 14,
       "valid_for": "5-7 year SMD horizon"
     }

The same cook class on the same card class gets the same sweet spot ·
no need to re-find unless ambient changes substantially.
```

---

## Post-cook validation

```
1. Verify cards cooled down clean (within 10 min of cook end)
   nvidia-smi --query-gpu=index,temperature.gpu,power.draw --format=csv,noheader
   Targets:
     temp ≤ 60°C (idle baseline)
     power ≤ 30W
     util 0%

2. Check `dmesg` for thermal events
   sudo dmesg | grep -iE "thermal|throttle|nvrm thermal|gpu has fallen"
   Empty = clean
   Any output = card was in protection · investigate before next cook

3. Reset gpu-reset only if state genuinely stuck
   nvidia-smi shows phantom 100% util · 0 MiB · post-NCCL-kill state
   sudo nvidia-smi --gpu-reset -i <gpu_idx>

4. Reset power cap + clocks to defaults for next cook (no drift)
   sudo nvidia-smi -i <gpu_idx> -pl <smd_default>
   sudo nvidia-smi -i <gpu_idx> -rgc
   sudo nvidia-smi -i <gpu_idx> -rmc

5. LOG the cook outcome to fleet health log
   {
     cook_id, card_idx, hostname, start_iso, end_iso,
     peak_temp_c, peak_power_w, sec_per_step_avg,
     dmesg_thermal_events, sweet_spot_match
   }
```

---

## Fleet-wide audit (weekly · run on all rigs)

```bash
# Audit script · returns CSV across all known rigs
for host in swarmrails smash rig99 whale; do
  ssh $host "nvidia-smi --query-gpu=index,name,temperature.gpu,power.limit,power.draw,memory.used,utilization.gpu,driver_version,vbios_version --format=csv,noheader" \
    | sed "s/^/$host,/"
done > fleet_health_$(date +%F).csv
```

Per-rig audit checklist:
```
[ ] All cards at expected SMD cap (per card class)
[ ] All idle cards at idle baseline (45-65°C · 15-30W)
[ ] No `dmesg` thermal events since last audit
[ ] Driver version matches across the fleet (consistency)
[ ] No card running > 6 months at sustained > 80°C (lifespan flag)
[ ] Card thermals correlate with rig ambient (no anomalies)
[ ] Fans spinning (audible / RPM sensor)
[ ] Power supply not at > 80% rated (PSU lifespan)
```

Card-health KPIs to track per-cook:
```
peak_temp_c              should NEVER exceed 87°C in steady state
peak_power_w             should be within 95% of cap
avg_temp_c (cook-wide)   should be < 80°C
sec_per_step             measure trend · regression flags issues
dmesg_thermal_events     should be 0 always
```

---

## The fleet (canonical inventory · update as rigs join)

```
swarmrails @ 192.168.0.100
  · 2× RTX PRO 6000 Blackwell 96GB · single-chassis · sm_120
  · primary cook rig · doctrine-tier cooks (27B/30B FSDP or single-GPU)
  · SMD cap 500W per card

smash @ 192.168.0.164
  · 1× RTX 5090 32GB · sm_120
  · 9B / 8B cook tier · vLLM serve tier
  · SMD cap 500W

rig 99 @ 192.168.0.99
  · 1× RTX 5090 32GB · sm_120
  · 3B / 4B cook tier · auxiliary
  · SMD cap 500W

whale (vast.ai-rented currently)
  · 1× RTX 3090 Ti 24GB
  · small model cooks · GGUF quant runs
  · SMD cap 350W

swarm desktop (this rig · 192.168.0.207)
  · 1× T1000 4GB · 40W cap via systemd unit
  · SwarmKeeper ollama serve only · NEVER trains
  · keep at 40W cap forever
```

---

## Real-world receipts

```
Atlas-Qwen-27B cook · 2026-05-07
  GPU 0 hit 88°C / 543W under steady train (550W cap)
  Action: dropped cap 550W → 500W mid-cook
  Result: temp 78°C → 74°C · power 285W → 253W · ~3-5% throughput hit
  Discipline locked: 500W is the SMD default for PRO 6000 Blackwell

Atlas-70B FSDP cook · 73h on 2× PRO 6000
  Cards held 78-82°C across 73 hours · no thermal events · clean cooldown
  Receipt: SMD cap on both cards held the line across the longest cook to date

Bookmaker-8B cook · 8.89h on smash 5090
  Peak 79°C · 500W cap · clean

Hack-Deed-Maker-3B cook · 5.20h on rig 99 5090
  Peak 73°C · 500W cap · clean
```

---

## Anti-patterns this skill prevents

```
× Running cards at 100% TDP for marginal throughput
× Ignoring thermal during multi-day cooks
× Treating idle GPUs as zero thermal contribution (chassis air pools)
× Killing a hot cook outright vs dropping cap first
× Forgetting to reset cap after temporary changes
× Not logging thermal · only learning when something cooks itself
× Skipping the weekly fleet audit · cards drift silently
× Treating rigs as consumable · they're SMDs · they earn their keep
```

---

## Iconic lines

> *"The cook that lands at 75°C will land 100 times.*
> *The cook that lands at 92°C will land once."*

> *"Throttle yourself before the silicon does."*

> *"Our rigs are SMDs. Treat them that way."*

> *"Pay the 3% throughput tax. Earn the 5× lifespan."*

---

## See also

- `/canary-then-cook` · senior-hack review discipline (runs alongside thermal management)
- `/cook-flightsheet` · the formal cook plan/report doc
- `/cook-monitoring` · full observability during cooks
- `/client-update` · periodic status reports to the project owner
