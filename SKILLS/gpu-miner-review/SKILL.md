---
name: gpu-miner-review
description: GPU thermal + power discipline for sovereign-compute training cooks · the miner mindset (cards run 24/7 · don't burn them out for marginal speed) · pre-flight + during-cook + post-cook checks
---

# /gpu-miner-review · GPU thermal + power management

The miner mindset: **sovereign compute is a 24/7 fleet, not a one-shot
benchmark run.** PRO 6000 Blackwells cost $7-10K each · the marginal 5%
throughput from running near thermal limits is not worth the 50-70% lifespan
hit · the silent VRM degradation · or the 90°C+ thermal-throttle that can
silently corrupt half a cook.

This skill walks the pre-flight + during-cook + post-cook power/thermal
discipline that production miners use and that we apply to every Swarm cook.

---

## When to invoke

```
Trigger: about to fire any cook expected to run > 4h
Trigger: any cook running hotter than expected (any card > 80°C sustained)
Trigger: any rig + GPU combination not previously thermal-validated
Trigger: any change to ambient (server room temp, airflow, neighboring loads)
Trigger: post-cook · validate cards came down clean · no thermal events logged
```

---

## Pre-flight checklist (BEFORE firing a cook)

```
1. POWER CAP · set per card class
     RTX PRO 6000 Blackwell 96GB    cap at 500W   (max 600W · 17% headroom)
     RTX 5090 32GB                    cap at 500W   (max 575W · 13% headroom)
     RTX 4500 Ada 32GB                cap at 200W   (already at 24/7 sustainable)
     RTX 4090 24GB                    cap at 400W   (max 450W · 11% headroom)
     RTX 3090 / 3090 Ti 24GB         cap at 350W   (max 400-450W · 12-22% headroom)
     RTX A6000 / A6000 Ada 48GB      cap at 280W   (datacenter-class · already conservative)
   
   Apply via:
     sudo nvidia-smi -i <gpu_idx> -pl <watts>
   
   Verify:
     nvidia-smi --query-gpu=index,power.limit,power.max_limit,power.default_limit \
                --format=csv,noheader

2. AMBIENT TEMP CHECK
   · room temp ≤ 24°C ideally · ≤ 28°C absolute max
   · server / rig airflow unobstructed · no clogged intake filters
   · neighboring GPUs idle (if multi-card · they share thermal budget)

3. PRE-COOK BASELINE
     nvidia-smi --query-gpu=index,name,temperature.gpu,memory.used,utilization.gpu --format=csv,noheader
   
   Targets:
     idle temp:        45-65°C  (Blackwell PRO 6000 baseline · varies by ambient)
     idle power:       15-30W
     idle util:        0%
     idle mem:         1-4 MiB (or whatever's resident from prior workload)
   
   If idle temp > 70°C · investigate before firing (neighboring load · airflow ·
   thermal paste history)

4. SCREEN / LOGGING
   · log files write to a known path so you can grep thermal events post-cook
   · don't fire a cook in a screen-less foreground unless you can `nvidia-smi
     dmon` it from another terminal
```

---

## During-cook monitoring

### Quick check (one-liner)

```bash
sshpass -p 'mack' ssh swarmrig 'nvidia-smi --query-gpu=index,memory.used,utilization.gpu,power.draw,temperature.gpu --format=csv,noheader'
```

### Sustained-watch (`dmon` for ~30 sec to see if temps are stable)

```bash
sshpass -p 'mack' ssh swarmrig 'nvidia-smi dmon -c 30 -s puct'
```

### Thermal thresholds · what to do at each band

```
< 75°C    SAFE       no action · within steady-state target
75-82°C   YELLOW     WATCH closely · check power_draw and utilization
                     if utilization is low (< 60%) and temp is high · airflow issue
                     if utilization 100% · approaching spec limit · consider cap drop
82-87°C   ORANGE     DROP power cap by 50W · re-measure in 5 min
                     verify temp comes down · if it doesn't · the silicon is
                     in trouble · find airflow / paste / ambient root cause
87-92°C   RED        DROP power cap by 100W IMMEDIATELY
                     if cook is checkpointable · save and pause · investigate
                     thermal throttle starts kicking in here · cook quality at risk
92°C+     CRITICAL   KILL THE COOK · GPU is in self-protection mode and will
                     throttle hard · silent corruption risk on transformer
                     gradients · resume only after thermal root cause fixed

CRITICAL FOR PRODUCTION COOKS:
  even 87°C sustained for hours degrades VRMs and reduces card lifespan ·
  a 5°C reduction (drop power cap 50W) typically buys you 2-3× lifespan
  on a card that's running 24/7 · trade marginal speed for hardware longevity
```

### Real-world reference receipts

```
Atlas-Qwen-27B cook · 2026-05-07
  GPU 0: PRO 6000 Blackwell · 550W cap · hit 88°C / 543W under steady train
  Action taken: dropped cap from 550W → 500W mid-cook
  Result:       temp dropped 78°C → 74°C · power 285W → 253W · throughput
                impact ~3-5% (acceptable trade vs the thermal margin gain)

Bookmaker-8B cook on smash · single 5090 · 500W cap · ran 8.89h at peak 79°C ·
landed clean

Hack-Deed-Maker-3B cook on rig 99 · single 5090 · 500W cap · 5.20h at peak
73°C · landed clean
```

---

## Power-vs-throughput tradeoff math

```
DON'T MAX THE WATTAGE.  The throughput gain from 500W → 600W is typically
4-8% on a Blackwell PRO 6000 LoRA cook · the temp delta is +8-15°C · the
lifespan delta is HUGE.

The miner formula:
  optimal cap = max_spec × 0.83-0.87
  
  RTX PRO 6000 Blackwell  600W × 0.83 = 500W  ← our default
  RTX 5090                  575W × 0.87 = 500W
  RTX 4090                  450W × 0.89 = 400W
  RTX 3090                  350W × 1.0  = 350W (already at sustainable)

Throughput-per-watt MAXIMUM is typically at 80-85% of stock TDP · NOT at
100%. Most miners run their cards at 65-75% TDP for max efficiency · we
run at 83-87% because LoRA cooks are short (hours-days · not months) · but
we still leave the headroom · always.
```

---

## Multi-card thermal coordination

```
On rigs with 2+ GPUs in the same chassis (e.g. swarmrails 2× PRO 6000):

  · Both cards cap at SAME wattage (500W each)
  · If only one card is being used · the IDLE card still warms from chassis
    air (will sit 60-65°C if neighbor is cooking)
  · If BOTH cards cooking simultaneously · ambient inside chassis rises ·
    drop both caps another 50W (450W each) to keep margin
  · Intake fans should be on max during cooks · most BIOS lets you force this
```

---

## Post-cook validation

```
1. Verify cards cooled down clean
     nvidia-smi --query-gpu=index,temperature.gpu,power.draw --format=csv,noheader
   
   Targets within 10 min of cook end:
     temp ≤ 60°C (idle baseline)
     power ≤ 30W
     util 0%

2. Check `dmesg` for thermal events
     sudo dmesg | grep -iE "thermal|throttle|nvidia"
   
   No output = clean.  Any "thermal throttle" or "nvrm thermal" lines = card
   was in protection mode at some point during the cook · INVESTIGATE before
   firing the next cook.

3. Reset gpu-reset only if needed
     nvidia-smi shows phantom 100% util · 0 MiB · post-NCCL-kill state ·
     happens after FSDP cooks · use:
        sudo nvidia-smi --gpu-reset -i <gpu_idx>
     Don't use prophylactically · only if state is genuinely stuck.

4. Re-apply standard power cap if changed
     If you dropped during-cook · reset to 500W default for the next cook ·
     don't leave at temporary higher/lower values
```

---

## Anti-patterns this skill prevents

```
× Running cards at 100% TDP for marginal throughput
  Counter-pattern: 83-87% TDP is the sweet spot · gain is 4-8% · cost is
  lifespan + thermal margin

× Ignoring thermal during multi-day cooks
  Counter-pattern: dmon snapshot every few hours · catch creep before
  it becomes a problem

× Treating idle GPUs as zero thermal contribution
  Counter-pattern: chassis air pools · idle neighbor still adds 5-10°C
  to active card · plan accordingly

× Killing a hot cook outright vs dropping cap first
  Counter-pattern: cap drop usually buys you 4-8°C in 5 min · let the cook
  continue at slightly reduced throughput rather than restart from scratch

× Forgetting to reset cap after temporary changes
  Counter-pattern: every cook starts with explicit `nvidia-smi -pl <default>`
  in the launch script · no cap drift across cooks

× Not logging thermal · only learning when something cooks itself
  Counter-pattern: dmon snapshots into the cook log every 15 min · grep-able
  post-cook · receipts grounded
```

---

## The miner mindset · iconic

> *"Cards run 24/7. Heat is the enemy. Marginal throughput is not worth a
> burned VRM. The cook that lands at 75°C will land 100 times. The cook
> that lands at 92°C will land once."*

> *"Throttle yourself before the silicon does."*

---

## Reference card thermal profiles

```
RTX PRO 6000 Blackwell Workstation Edition (96GB · sm_120)
  Spec TDP:        600W
  Recommended:     500W cap (83% spec)
  Sustained safe:  78-85°C at 500W under LoRA cook
  Throttle start:  ~90°C
  Hard limit:      95°C
  Idle baseline:   45-65°C (varies by ambient + chassis airflow)
  Cards on Swarm:  swarmrails GPU 0 + GPU 1

RTX 5090 (32GB · sm_120)
  Spec TDP:        575W
  Recommended:     500W cap (87% spec)
  Sustained safe:  73-82°C at 500W
  Cards on Swarm:  smash · rig 99 · others

RTX 4500 Ada (32GB · 200W TDP)
  Spec TDP:        200W
  Recommended:     200W (already 24/7 sustainable)
  Sustained safe:  60-72°C
  Cards on Swarm:  48× across the fleet

RTX 3090 / 3090 Ti (24GB · 350-450W)
  Spec TDP:        350W (3090) · 450W (3090 Ti)
  Recommended:     350W cap (100% / 78%)
  Sustained safe:  68-78°C
  Cards on Swarm:  whale (3090 Ti)

T1000 (4GB · 50W)
  Spec TDP:        50W
  Recommended:     40W cap (already power-limited via systemd unit)
  Sustained safe:  40-55°C
  Cards on Swarm:  swarm desktop (this rig · running SwarmKeeper ollama)
```

---

## See also

- `~/.claude/skills/canary-then-cook/SKILL.md` · the review-loop discipline
  that runs alongside thermal management for every cook
- `granite-models-cookbooks/COOKS/atlas-70b.md` · the 73h cook receipt with
  thermal performance across two PRO 6000s in FSDP
- `atlas-3.6-27B-cook-book/COOKS/atlas-qwen-27b.md` · the cook where the
  88°C → 500W cap drop locked the discipline into doctrine
