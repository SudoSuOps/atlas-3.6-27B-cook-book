---
name: cook-flightsheet
description: Every cook gets a flightsheet · the formal pre-flight + in-flight + post-flight doc · SR hack signs off · all cooks · all rigs · permanent record · the audit trail customers and investors trust
---

# /cook-flightsheet · The Formal Cook Record

> *"Every cook gets a flightsheet · pre-flight, in-flight, post-flight ·
> SR hack signs off · the rigs are SMDs and they don't fly without one."*
> — Donovan, 2026-05-07

A flightsheet is the formal cook record · modeled after a pilot's flight
plan + maintenance log + post-flight report combined. It exists for one
reason: **so an auditor, a customer, or a future engineer can read ONE
document and know everything that happened during this cook.**

Loss curves measure absorption. Correction loops measure judgment. SR hack
reviews catch silent corruption. **Flightsheets are the durable receipt
that pulls all three together into a permanent record any third party
can verify.**

---

## When to invoke

```
Trigger:  before firing any cook · build the pre-flight section
Trigger:  during cook · update with progress receipts
Trigger:  after cook lands · complete the post-flight section
Trigger:  before declaring a cook "production-ready" · SR hack final sign-off
Trigger:  during audit · pull the flightsheet to verify the cook story
```

---

## Cook investment-grade classification (5-cap STNL discipline)

Before writing the flightsheet · classify the cook by investment grade ·
same convention CRE brokers use for STNL deals:

```
COOK CAP-RATE TIER                   INVESTMENT GRADE             DISCIPLINE LEVEL
────────────────────────────────────────────────────────────────────────────────
5-cap (premium · doctrine)           A+ tenant · 15-20yr lease   FULL discipline
                                     trades at 20× rent           · all 5 sections
  Examples: Atlas-Qwen-27B           prime location               · sr hack 3 stages
                                                                  · 6+ year hold

6-cap (production-adjacent)          BBB+ · 10-15yr lease        STANDARD discipline
                                                                  · all 5 sections
  Examples: Bookmaker-8B             good location                · sr hack 2 stages

7-cap (standard production)          BB+ · 7-10yr lease          STANDARD discipline
                                                                  · sections 1+3+4+5
  Examples: Hack-Deed-Maker-3B       secondary market             · sr hack 1 stage

8-cap (experimental side cook)       sub-IG · 5yr lease          MINIMAL discipline
                                                                  · sections 1+4
  Examples: small specialty cooks    tertiary                     · canary only

9-cap (one-off · throwaway)          speculative · short-term    LOG ONLY
  Examples: research probes          turnaround required          · energy + lineage

10-cap+ (distressed · failed)        reject · don't cook          POSTMORTEM
  Examples: any cook the sr hack    distressed                   · what went wrong
            said don't run                                        · lessons captured
```

The tier sets the discipline level. A 5-cap cook gets the full senior-hack
review chain · all 5 flightsheet sections · post-cook held-out eval ·
public OM. A 9-cap cook gets just the energy meter and a one-line lineage
note. **Don't over-discipline a 9-cap. Don't under-discipline a 5-cap.**

---

## Training blocks · segment max_steps into reviewable chunks

A long cook is broken into 5 BLOCKS · each gets its own mini-review:

```
BLOCK 1 · WARMUP             steps 0-20%        cosine warmup · LR ramping
                             review:  is loss falling? grad_norm stable?
                             gate:    if loss diverges · KILL · don't burn

BLOCK 2 · EARLY ABSORPTION   steps 20-40%       core domain shift · biggest gains
                             review:  loss falling fast?
                             gate:    if loss flat · investigate corpus shape

BLOCK 3 · CORE TRAINING      steps 40-60%       LR at peak · main learning
                             review:  eval_loss declining vs prior eval?
                             gate:    if eval_loss rising · early stop here

BLOCK 4 · REFINEMENT         steps 60-80%       cosine decay engaging
                             review:  trajectory shape vs reference cook
                             gate:    early-stopping should fire here typically

BLOCK 5 · CONVERGENCE        steps 80-100%      LR low · final polish
                             review:  has it landed? plateau detected?
                             gate:    rare to reach this block · overcook risk
```

Each block transition · 5 quick checks (~30 sec):
```
1. /gpu-miner-review · thermal + power within bounds
2. eval_loss trajectory · declining vs prior block?
3. disk space · enough for next block's checkpoints?
4. NAS mirror · rsync keeping up?
5. /client-update · brief cadence note pushed
```

Block-by-block discipline lets you intervene with smaller decisions
(throttle one block · skip ahead · early-stop here) instead of one big
"is this whole cook fine?" decision.

---

## Energy cost-to-cook (sovereign compute economics)

Every cook tracks energy as part of the flightsheet · `$0.10/kWh` standard
sovereign-compute cost basis (sub-cloud · ~50-500× cheaper than cloud GPU).

Energy is the **orb** · the underlying value the whole sovereign-compute
thesis is built on. We OWN the silicon + the energy · our marginal cost is
just kWh + capex amortization · everyone else pays cloud markup.

```
Per-cook energy math:
  power_avg_w (per card) × num_cards × wall_clock_hours / 1000 = total kWh
  total_kWh × $0.10/kWh = electrons cost

Reference receipts (real cooks):
  Atlas-70B   2× PRO 6000 ≈ 1 kW avg × 73h = 73 kWh = $7.30
              (was previously over-quoted at $37 · honest math: $7.30)
  Bookmaker-8B 1× RTX 5090 ≈ 0.4 kW avg × 8.89h = 3.6 kWh = $0.36
  Hack-Deed-3B 1× RTX 5090 ≈ 0.35 kW avg × 5.20h = 1.8 kWh = $0.18
  Atlas-Qwen-27B (target) 1× PRO 6000 ≈ 0.4 kW avg × 24h = 9.6 kWh = $0.96
              · plus rig overhead (CPU + fans + drives ~150W) = ~$1.30
```

In-flight energy snapshot (every 30 min during cook · auto-appended):
```
[2026-05-07T05:00 UTC]  power_avg_30min=395W · cumulative_kWh=11.85 · cost=$1.18
[2026-05-07T05:30 UTC]  power_avg_30min=412W · cumulative_kWh=12.05 · cost=$1.21
```

Final energy line in post-flight Section 4:
```
Total electrons: <X> kWh = $<X.XX>  (at sovereign $0.10/kWh basis)
Cloud-equivalent: ~$<5-50× higher>  (vendor markup we don't pay)
Per-deal economics downstream: ~$<X> per AIOV report at deployed throughput
```

> *"Energy is the orb. Everyone else pays cloud markup. We pay $0.10."*

---

## The flightsheet template · 5 sections

Save at `<cookbook>/FLIGHTSHEETS/<cook-name>-flightsheet.md`.

### Section 1 · PRE-FLIGHT (before launch · capture intent)

```markdown
# <Cook Name> · Flightsheet

## Pre-flight · Captured <ISO timestamp> by <operator>

### Intent
- WHY this cook exists (1-2 sentences)
- What success looks like (specific · measurable)
- Reference cook this measures against (loss target · token_acc target)

### Configuration
- Base model: <HF id · sha · architecture class>
- Recipe values (every hyperparameter · LR · scheduler · batch · seq · etc.)
- Stack (transformers · peft · trl · attention impl · framework)

### Corpus
- Block version · sha256 · record count · size MB
- Source manifest path
- Tier distribution (apex / honey / royal_jelly / etc.)
- Eval set sha (cross-cook comparable?)

### Hardware
- Rig + GPU(s) · power cap per card · SMD discipline applied
- Pre-cook thermal baseline (from /gpu-miner-review pre-flight)
- Disk space · NAS mount available

### Projections
- Pace target (sec/step · canary-derived if possible)
- Wall-clock estimate (worst-case + realistic)
- Cost estimate (electrons in $)
- Failure probability · honest estimate
```

### Section 2 · CANARY VALIDATION (smoke results)

```markdown
## Canary Validation · <ISO timestamp>

### Smoke run
- Steps · samples · pace
- Pipeline gates passed (model load · LoRA · gradients · eval · save · merge)
- Eval trajectory (declining · plateau · noise · whichever)
- No CUDA errors · no OOM · no contamination signals

### Receipts
- canary log path
- canary adapter sha (if saved)
- canary merged sha (if merged)

### Decision
- Greenlight to fire full cook? Y/N · with rationale
- Canary fixed any pre-flight issues? · list fixes
```

### Section 3 · IN-FLIGHT (live updates as cook progresses)

```markdown
## In-Flight · live receipts

### Step blocks (every save_steps · auto-appended)
- step / max_steps · loss · grad_norm · lr · entropy · token_acc · epoch
- timestamp · cumulative wall-clock

### Eval blocks (every eval_steps · auto-appended)
- step · eval_loss · eval_token_acc · eval_runtime · eval_num_tokens

### Checkpoints (auto-appended)
- step · path · sha (lora-adapter)
- size MB

### Thermal (every hour · from /gpu-miner-review)
- timestamp · GPU temp · power_draw · util
- thermal events flagged (if any)

### Anomalies (manual entry as encountered)
- timestamp · what happened · action taken
- e.g. "GPU 0 hit 88°C · dropped cap 550W → 500W · cooled to 74°C"
```

### Section 4 · POST-FLIGHT (after cook lands)

```markdown
## Post-flight · <ISO timestamp>

### Final receipts
- final eval_loss · final token_acc · final step / max_steps
- early-stopped? · at which step · why
- total wall-clock · throughput-per-watt
- adapter sha · merged sha · NAS mirror path
- post-cook thermal cooldown clean? · dmesg events?

### Trajectory analysis
- Loss curve shape · monotone decline · plateau · noise
- Compare to reference cook (e.g. SwarmCurator-27B-v1 0.477)
- Compare to projected (Y/N · why if no)

### Held-out judge eval
- Path to held-out eval set
- Per-bucket scores (cap_rate · ic_memo · etc.)
- A/B vs base model (proves cook added knowledge vs just style)

### Correction-loop sessions
- Session count · what surfaced · cookbook updates
- Numeric Gate clamp updates needed?

### Receipts URL pattern
- atlas.defendable.eth/<cook_id>
- Hedera anchor topic · transaction hash
- merged path on NAS
```

### Section 5 · SR HACK SIGN-OFF

```markdown
## SR Hack Sign-Off · <ISO timestamp>

### Pre-flight review (Stage 1)
- Reviewer: <agent / engineer name>
- Verdict: <green / fix-list / kill>
- Failure probability assessment: __%
- Findings + fixes (link to REVIEWS/<cook>-review-chain.md)

### Final-look review (Stage 4 · post-canary · pre-full-cook)
- Reviewer: <agent / engineer name>
- Verdict: <greenlight / kill>
- Residual probability: __%
- Watch-items (numbered)

### Post-cook review (Stage 5 · after lands)
- Reviewer: <agent / engineer name>
- Verdict: <ship / re-cook v(N+1)>
- Held-out eval pass? Y/N
- Doctrine voice transferred? Y/N (per correction loops)

### Sign-off statement
- "<Cook Name> approved for production / ready to ship to <namespace> ·
   signed off by <reviewer> on <date>"
- OR
- "<Cook Name> rejected · re-cook required · see notes above"
```

---

## How to actually generate flightsheets

### Pre-flight (manual + script combo)

```bash
mkdir -p <cookbook>/FLIGHTSHEETS
cat > <cookbook>/FLIGHTSHEETS/<cook-name>-flightsheet.md <<EOF
# <Cook Name> · Flightsheet

## Pre-flight · Captured $(date -u +%Y-%m-%dT%H:%M:%SZ) by <operator>

[fill in template above using inputs from train script + corpus manifest]
EOF
```

Or invoke this skill in Claude Code: `/cook-flightsheet pre-flight <cook-name>`
and Claude will extract values from the train script + manifest + corpus
files automatically.

### In-flight (semi-automated)

The cook script's `--with-flightsheet` flag (when added) appends step / eval
blocks automatically. Or post-process from the cook log:

```bash
grep -E "^\\{'loss|^\\{'eval" cook.log | python3 to_flightsheet.py >> flightsheet.md
```

Plus manual anomaly entries · "GPU hit 88°C · dropped cap" etc.

### Post-flight (manual after cook lands)

Pull from MANIFEST.json + held-out eval results + sr hack final review.

### SR hack sign-off

Spawn senior hack agent with the FULL flightsheet (all 4 sections complete) ·
ask for sign-off statement · paste their verdict into Section 5.

---

## What good flightsheets enable

```
1. AUDITABILITY
   Every customer · every brokerage CTO · every diligence officer can read
   ONE document and know exactly what produced this model and how.

2. REPRODUCIBILITY  
   With recipe + corpus sha + canary results + sr hack sign-off · any third
   party can replicate within ~5% on the same hardware.

3. PROVENANCE
   The flightsheet IS the Defendable receipt content. Hedera anchors a hash
   of the flightsheet · the public can verify the cook's lineage on-chain.

4. POST-MORTEM CLARITY
   When a cook fails (or surprises us positively) · the flightsheet has
   every variable that mattered · we don't lose context to time.

5. TEAM SCALING
   New engineers reading old flightsheets learn the discipline by example ·
   instead of being trained ad-hoc.

6. INVESTOR / CLIENT TRUST
   "Show me the flightsheet" becomes the standard request from any serious
   counterparty · we always have it · we never have to scramble.
```

---

## Anti-patterns this skill prevents

```
× Cook lands · we celebrate · then 6 months later we can't reproduce it
× Customer asks "what was the corpus?" · we have to dig through Slack
× SR hack reviews exist but aren't anchored to a single doc · they get lost
× Held-out eval results live separately · disconnected from cook · 
  hard to audit
× Different engineers cook at different discipline levels · no shared standard
× Hedera anchors a model weight sha but not the cook story · can't audit
  the WHY
× "We trained it on the good data" with no specifics · zero defensibility
```

---

## Real-world worked example

See `<cookbook>/FLIGHTSHEETS/atlas-qwen-27b-flightsheet.md` for the actual
flightsheet of the Atlas-Qwen-27B cook running 2026-05-07. Includes:

- Full pre-flight (Block-1-v4 · 244K · sha · recipe · stack · projections)
- Canary v6 validation (5 cook steps · pipeline validated)
- Live in-flight receipts (step blocks · eval blocks · thermal events)
- Post-flight when it lands
- SR hack sign-off (initial review · final-look · post-cook)

That's the working template every future cook copies.

---

## Iconic line

> *"The flightsheet is the receipt that survives the engineer.*
> *Every cook gets one. The SR hack signs it off. That's the standard."*

---

## See also

- `/canary-then-cook` · the 5-stage senior-hack review discipline
- `/gpu-miner-review` · GPU thermal + power management (feeds in-flight section)
- `/cook-monitoring` · full observability during cooks (feeds in-flight)
- `/client-update` · periodic reports pull from the flightsheet
