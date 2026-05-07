---
name: client-update
description: Periodic status updates for cooks · the customer/investor/auditor view · pulls from cook flightsheet + monitor + reviews · brief, receipts-grounded, schedule-driven
---

# /client-update · The Customer-Facing Cook Update

Every cook running > 4h gets periodic status updates that go to:

- **The project owner** (Donovan · the broker funding the cook)
- **The brokerage CTO** (the customer of the AIOV product · needs to know cooks are on track)
- **The diligence officer / auditor** (any third party reviewing the receipts)
- **The team** (other engineers who'll inherit this cook's lineage)

The update is **NOT marketing.** It's **receipts in plain English.**
Brief. Honest. Bad news as fast as good news.

---

## When to invoke

```
Trigger:  cook fires (T+0 update · pre-flight summary)
Trigger:  first eval lands (T+~3.5h · first real signal · big update)
Trigger:  every 6 hours during cook (cadence updates · brief)
Trigger:  any anomaly (cap drop · thermal event · early stop · OOM · etc.)
Trigger:  cook lands (T+end · post-cook summary)
Trigger:  post-cook review complete (final · sr hack signed off)
```

---

## The 6 update types

### Type 1 · COOK LAUNCHED (T+0)

```markdown
## Atlas-Qwen-27B · cook launched 2026-05-07 01:52 UTC

**What:** Production doctrine-tier LoRA fine-tune · rebuild of the original
Atlas-27B (vanished) on Qwen3.6-27B substrate.

**Why:** Senior peer review caught 3 silent-corruption bugs + corpus dilution
in v3 config. Four fixes applied · canary validated · senior hack greenlight
secured. Now cooking.

**Recipe:** bf16 LoRA r=64 α=32 · LR 1e-5 cosine · packing=False (sm_120 +
GDN safe path) · MAX_EPOCH_FRACTION 0.30 · 2,294 max_steps.

**Corpus:** Block-1-v4 · 244,725 records · sha 885982da27b5008a · disciplined
cull (apex + Honey + Royal Jelly tiers only).

**Hardware:** swarmrails GPU 0 · RTX PRO 6000 Blackwell 96GB · 500W cap (SMD
discipline · was 550W · dropped after 88°C event).

**ETA:** 23h realistic (early-stop · ~1,200 steps) · 46h worst-case (max).
**Cost:** ~$15-25 sovereign electrons.

**Failure probability:** 20-25% per senior hack · down from 65-75% pre-fixes.

**Receipts:**
- cookbook: github.com/SudoSuOps/atlas-3.6-27B-cook-book commit 8965c5d
- review chain: REVIEWS/atlas-qwen-27b-cook-review-chain.md
- flightsheet: FLIGHTSHEETS/atlas-qwen-27b-flightsheet.md
- monitor: persistent · surfaces material events only

Standing by for first eval at step 200 (~3.5h from now).
```

### Type 2 · FIRST EVAL LANDED (T+~3.5h)

```markdown
## Atlas-Qwen-27B · first eval · step 200

**eval_loss:** X.XXX  (vs SwarmCurator-27B-v1 reference · trajectory comparable)
**eval_token_acc:** XX.XX%
**Pace:** XX sec/step steady · revised ETA YY h to landing

**Trajectory read:** [healthy / yellow / red]
- [healthy] declining monotone · on track for landing < 0.45 by step 1000+
- [yellow] flat · watching next eval to confirm progression
- [red] rising · early-stopping should fire by step 600 · letting it decide

**No anomalies. No thermal events. No OOM. Cook continues.**

Next event: step 400 eval (~7h from now) OR any material anomaly.
```

### Type 3 · CADENCE UPDATE (every 6h · brief)

```markdown
## Atlas-Qwen-27B · T+12h update

**Step:** 600 / 2,294 · **eval_loss:** X.XXX (declining)
**Pace:** XX sec/step · **Temp:** XX°C · **Cards stable**
**Disk:** XX GB free (XX checkpoints written)

**Trajectory:** on track / watching / concerning
**Watch-items:** [step 600 senior-hack checkpoint review fired · verdict X]

Next event: step 800 eval (~3.5h) OR any material anomaly.
```

### Type 4 · ANOMALY (immediate · receipts only)

```markdown
## Atlas-Qwen-27B · anomaly @ T+5h

**What:** GPU 0 hit 88°C / 543W under steady train (cap was 550W)
**Action:** dropped power cap 550W → 500W
**Result:** temp dropped to 74°C in 5 minutes · power 285W → 253W ·
            estimated throughput impact 3-5% (acceptable)
**Cook continues. No rollback needed.**

This is the receipt that locked 500W as the SMD default for PRO 6000 Blackwell ·
also captured as `/gpu-miner-review` skill · also added to flightsheet
Section 3 (in-flight anomalies).
```

### Type 5 · COOK LANDED (T+end · pre-review)

```markdown
## Atlas-Qwen-27B · cook lands · T+XXh

**Final eval_loss:** X.XXX  **Final token_acc:** XX.XX%
**Steps:** XXXX / 2,294 (early-stopped at step XXXX)
**Wall-clock:** XX h · **Cost:** ~$XX electrons

**Receipts:**
- adapter: /data1/atlas-qwen-27b-v4/lora-adapter · sha XXXX
- merged: /data1/atlas-qwen-27b-v4/merged · 12 shards · ~52 GB
- NAS mirror: /mnt/swarm/model_archives/atlas-qwen-27b/
- MANIFEST.json: full provenance receipt

**Trajectory shape:** [analysis vs reference · was the cook clean]

**Next:** Senior-hack post-cook review (Stage 5)
- held-out judge_cre_30k eval
- A/B vs base Qwen3.6-27B (proves cook added knowledge vs just style)
- correction-loop chat-UI sessions (catches lobotomization)

NOT YET CLEARED FOR PRODUCTION. Senior hack signs off the flightsheet first.
```

### Type 6 · SENIOR HACK SIGN-OFF (final · ship or re-cook)

```markdown
## Atlas-Qwen-27B · sr hack post-cook review

**Verdict:** [SHIP to atlas.defendable.eth] / [RE-COOK as v5]
**Signed off by:** <reviewer> on <date>

**Held-out eval results:**
- judge_cre_30k score: XX.XX% (vs base Qwen3.6-27B baseline of XX.XX%)
- A/B comparison: + XX pp · cook added measurable doctrine value
- correction-loop sessions: 5 sessions clean · no lobotomization · doctrine
  voice transferred

**Punch-list items remaining:** [none / list]

**Production deployment:**
- Q4_K_M GGUF target · runs on RTX 3090 24GB at ~35 tok/s · 262K context
- HACKER-AGX ($2K box) provisioning ships v4 weights
- AIOV pipeline routes high-stakes valuations through this 27B

**Cookbook updated:**
- FLIGHTSHEETS/atlas-qwen-27b-flightsheet.md · all 5 sections complete
- REVIEWS/atlas-qwen-27b-cook-review-chain.md · post-cook stage filled in
- COOKS/atlas-qwen-27b.md · trajectory section locked

The original Atlas-27B is back. Better. With full receipts.
```

---

## How to actually generate updates

### Manual (for milestone events)

Operator pulls from flightsheet + monitor stream + sr hack reviews · writes
the update in the format above · sends to relevant channels (Slack, email,
shared doc).

### Semi-automated (for cadence updates)

```bash
# Pull current state
ssh swarmrig 'tail -50 /data1/atlas-qwen-27b-v4/cook.log | grep -E "loss|eval|step"'
ssh swarmrig 'nvidia-smi --query-gpu=temp,power.draw --format=csv,noheader'
ssh swarmrig 'df -h /data1 | tail -1'

# Format into the cadence template
# Send via desired channel
```

### Fully automated (for production · future)

Cron job every 6h pulls cook log + telemetry · auto-formats Type 3 cadence
update · posts to Slack channel · skips if cook complete.

---

## What the update is + isn't

```
IS:                                  IS NOT:
  receipts in plain English            marketing copy
  brief · 200 words max for cadence    long-form analysis
  honest about anomalies                hidden problems
  bad news as fast as good news        only success
  receipts-grounded (sha · timestamp)   "we feel good about it"
  third-party verifiable                first-party trust-me
  schedule-driven                       crisis-driven
```

---

## Update channels

```
Donovan (project owner):
  · Discord / direct chat
  · Major events real-time · cadence updates 6h spacing

Brokerage CTO (customer):
  · Email · weekly digest
  · "Here's what we shipped this week + what's cooking"

Diligence officer / auditor:
  · Cookbook + Hedera receipts (self-serve)
  · They pull · we don't push · receipts speak for themselves

Team (other engineers):
  · Cookbook commits with co-author footer
  · Slack #cooks channel for real-time
```

---

## Anti-patterns this skill prevents

```
× Going dark for 24 hours during a cook · no one knows if it's still alive
× Reporting only when something breaks · sets up surprise anxiety
× Marketing copy that buries the receipts under enthusiasm
× Burying anomalies · "we had a thermal event but everything's fine" without
  the action taken
× Updates that don't link to the underlying receipts (cookbook · flightsheet
  · review chain) · forces customer to ask follow-ups
× Different update style for different audiences · maintain ONE template ·
  filter what to share per channel
```

---

## Reference receipts

```
Atlas-70B Llama cook · 73h
  Updates fired:
    T+0       cook launched (Discord · email)
    T+3.5h    first eval (Discord · "step 200 · eval_loss 0.81 · trending right")
    T+6h, 12h, 18h, 24h, 36h, 48h, 60h    cadence (brief · pace + temp)
    T+73h     cook landed (full report)
    T+74h     sr hack final sign-off (ship to atlasos.eth)
  
  Customer feedback: "this is the only AI vendor I trust because they tell me
                       what's happening between the events I expect."

Atlas-Qwen-27B cook · current
  Updates so far:
    T+0       launched (after canary validated · 4-fix recipe applied)
    T+5min    GPU 0 thermal anomaly (88°C → cap drop → 74°C)
    T+30min   first metric block (loss 2.20 trending down)
    [pending] T+3.5h first eval landing
```

---

## Iconic line

> *"Tell them what's happening. Tell them when something changes. Link to*
> *the receipts. That's the entire job."*

---

## See also

- `/cook-flightsheet` · the source of truth this update pulls from
- `/cook-monitoring` · the telemetry stream that powers cadence updates
- `/canary-then-cook` · senior-hack review chain referenced in updates
- `/gpu-miner-review` · thermal anomalies become Type 4 anomaly updates
