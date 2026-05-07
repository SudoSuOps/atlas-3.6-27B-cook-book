---
name: cook-om
description: Offering Memorandum for cooked models · CRE-broker format · the sales document a customer / investor / brokerage CTO reads to know WHY to buy · what it is · its ecosystem · its credit velocity · its domain · its risk · its terms
---

# /cook-om · The Cook Offering Memorandum

> *"Every cook has a flightsheet (the maintenance log) and an OM (the sales*
> *document). The flightsheet tells engineers what happened. The OM tells*
> *the buyer why they're buying it."* — Donovan

In CRE, an Offering Memorandum is the formal sales document for a property:
what it is, why someone buys it, the ecosystem it lives in, the credit
profile, the location, the risk, the terms. Same discipline applies to a
cooked model · it's an asset · it sells (or licenses) on its merits ·
the OM is the document that closes the deal.

This skill produces the OM for any cooked model in the same format CRE
brokers have used for 30 years.

---

## When to invoke

```
Trigger:  cook is finished + sr-hack-signed-off · time to package for buyers
Trigger:  any pitch / demo / RFP for the model
Trigger:  any time a customer asks "what is this model and why should I license it"
Trigger:  any time the cookbook needs a public-facing summary doc
```

---

## The OM template · 11 sections (CRE-broker convention)

Save at `<cookbook>/OM/<cook-name>-om.md` (one per cook).

### 1 · Executive Summary (the cover page · 1 paragraph)

```markdown
# <Cook Name> · Offering Memorandum

## Executive Summary

[Cook name · 27B/9B/etc · base substrate · cook lineage] · purpose-built for
[primary domain] · [investment-grade tier · 5-cap / 6-cap / 7-cap / etc.] ·
deployed via [HACKER tier / datacenter] · receipts anchored at
[atlas.defendable.eth / etc].

Trained on [N] curated pairs from [Block version] · sha [first 16 chars] ·
recipe [Gold Standard reference] · cooked in [hours]h on [hardware] ·
electrons cost ~$[X].

License tier · [Premium / Honey / Royal Jelly / etc.] · ASKING [$ / unit].
```

### 2 · Build Profile (what the model IS)

```markdown
## Build Profile

| Field             | Value                                       |
|-------------------|---------------------------------------------|
| Build name        | <Atlas-Qwen-27B>                           |
| Base substrate    | Qwen/Qwen3.6-27B (Apache 2.0)              |
| Architecture      | hybrid GDN + standard attention · 64 layers |
| Method            | bf16 LoRA r=64 α=32                        |
| Trainable params  | 318,767,104 (1.171% of 27.2B base)         |
| Final loss        | <eval_loss> (whole-sequence · cook-canon)  |
| Final token acc   | <token_acc>                                |
| Training tokens   | <num_tokens> (cumulative across cook)       |
| Cook wall-clock   | <hours>h                                   |
| Hardware used     | 1× RTX PRO 6000 Blackwell · 500W SMD cap   |
| Electrons cost    | $<X> at $0.10/kWh                          |
| Defendable receipt| atlas.defendable.eth/<cook-id>             |
| Hedera anchor     | topic 0.0.10291838 · tx <hash>             |
```

### 3 · Domain / Location (where this model lives)

```markdown
## Domain · the market this model operates in

**Primary domain:** [Commercial Real Estate · Capital Markets · STNL · etc.]
**Asset classes covered:** office, industrial, multifamily, retail, hotel,
data_center, mixed_use, cold_storage (per AIOV deal_input.json schema)
**Geographic scope:** US-wide · trained on national CRE corpus
**Specialty muscles:** 
  - IC memo writing (signal_canonical voice · 47K Premium tier pairs)
  - Federal grants compliance (royal_jelly tier · 34K pairs · OZ/NMTC/HUD/USDA/EDA)
  - Doctrine reasoning (bee_hive_train_data SwarmRefinery · 95K Premium)
  - Honey-graded credit reasoning (finance HONEY tier · 13K pairs)
  - SwarmJudge agent-trajectory eval (jelly_eval · 21K pairs)
  - Royal Jelly Protocol · CRE classification + scoring discipline

**Competing alternatives in this domain:**
  - GPT-4 / Claude with custom prompts · no doctrine receipts · no AIOV anchor
  - Open-source Qwen3.6-27B base · no CRE specialization
  - Llama-3.3-70B Atlas-style cook · 1/9 the throughput at higher latency
  - Granite-4.1-30B Atlas attempt · killed by sr-hack pre-commit · no receipts

**Why this domain matters:** $4.99T CRE debt outstanding · $1.5T+ refinancing
2026-2027 · 1,374 banks above 300% CRE concentration · pure-document
underwriting workflow that AI wins because it doesn't need tours · the lane
where Atlas IS the answer (per `cre_debt_wall_2026_intel.md`).
```

### 4 · Ecosystem (how it plugs in)

```markdown
## Ecosystem · the AIOV 5-stage pipeline

This model is **stage 1** of the Atlas OS / AIOV pipeline:

```
0. HACKER-3B intake (cheap intake bee · deed/lease/OM extraction)
1. ATLAS-QWEN-27B  ← THIS MODEL · drafts IC memo + structured output
2. Numeric Gate     deterministic Python validator (6+ rules · cap-direction ·
                    refusal-when-data-missing · recommendation cohere ·
                    source hierarchy · status enum · range sanity)
3. Tribunal         multi-judge eval · honey/jelly/propolis source hierarchy
4. AIOV renders     customer-facing PDF/HTML IC memo (only after stages 1-3 pass)
5. Hedera anchors   Defendable receipt at aiov.defendable.eth/<deal_id>
```

The model PRODUCES outputs conformant with the canonical AIOV schemas:

- `deal_input.json` · the structured input the model consumes (asset_type ·
  purchase_price · noi · debt_request · macro_context · sponsor + 17 more)
- `decision_output.json` · the structured output the model produces:
  - decision: enum [approve · approve_with_conditions · restructure · decline ·
    watchlist · distressed_opportunity]
  - confidence: 0-1
  - recommended_max_loan
  - binding_constraint: enum [ltv · dscr · debt_yield]
  - risk_flags · capital_stack_recommendation · scenario_analysis ·
    rationale · memo_summary

The model integrates with:
  - vLLM serving (with --enforce-eager for GDN · --skip-mm-profiling)
  - HACKER-PRO ($599) and HACKER-AGX ($2K) box runtimes
  - BeeAI Framework for agentic dispatch
  - x402 HTTP payment protocol for usage metering
```

### 5 · Credit Velocity (speed-to-value)

```markdown
## Credit Velocity · speed-to-value

**Inference throughput** (post-cook · once deployed):
| Hardware                  | Format       | Throughput        | Context |
|---------------------------|--------------|-------------------|---------|
| 2× RTX PRO 6000 96GB     | bf16 vLLM    | ~88 tok/s × 4 conc| 32K     |
| 1× RTX PRO 6000 96GB     | bf16 vLLM    | ~60 tok/s × 2 conc| 32K     |
| RTX 3090 24GB            | Q4_K_M GGUF  | ~35 tok/s         | 262K    |
| AGX Orin 64GB (HACKER-AGX)| INT4 AWQ     | ~12-18 tok/s      | 32K     |

**Time-to-first-IC-memo:** ~30-90 sec (depending on memo length and hardware)

**Time-to-Defendable-receipt:** stages 1-5 typical end-to-end:
  - Stage 1 LLM draft:        15-60 sec (this model)
  - Stage 2 Numeric Gate:     < 1 sec (deterministic Python)
  - Stage 3 Tribunal:         5-15 sec (multi-judge eval)
  - Stage 4 AIOV render:      < 1 sec (PDF generation)
  - Stage 5 Hedera anchor:    1-3 sec (HCS transaction)
  - **Total: ~25-80 sec per deal**

**Per-deal cost economics** (sovereign compute baseline):
  - Stage 1 inference:  ~50-200 tokens × 88 tok/s × 0.5 kW = 0.0001 kWh per deal
  - Total electrons:    ~$0.0002 per deal at $0.10/kWh
  - Hedera anchor fee:  $0.0008 per anchor
  - Per-deal total:     ~$0.001 (sub-penny per AIOV report)
```

### 6 · Why Buy (the differentiator)

```markdown
## Why Buy · the differentiator

**1. RECEIPTS · not marketing**
   Every claim has a sha256 · every cook has a flightsheet · every customer
   can verify the lineage on-chain at atlas.defendable.eth. We compete with
   "trust me" vendors. We win.

**2. SOVEREIGN COMPUTE · no cloud markup**
   Trained on owned silicon · served on owned silicon · electrons cost
   ~$0.001 per deal. Cloud vendors charge $0.05-0.50 per equivalent inference.
   50-500× margin · structural · permanent.

**3. THE DOCTRINE TRANSFERRED**
   bee_hive_train_data (95K Premium) carries the SwarmRefinery operational
   intelligence engine. Models cooked on this corpus inherit broker-grade
   judgment · not just template memorization.

**4. THE NUMERIC GATE BACKSTOP**
   The model can be wrong about cap-direction · refusal · self-coherence
   without it ever reaching the customer. Stage 2 catches it. The customer
   sees only validated output.

**5. AIOV CONTRACTS · structured I/O**
   The model produces JSON conformant with deal_input.json + decision_output.json
   schemas (the original Atlas v1 contracts · ported verbatim). Customers
   integrate via schema · not screen-scraping.

**6. TIER-ROUTED AT $250 · $599 · $2K · DATACENTER**
   The HACKER ecosystem matches model tier to deal complexity. STNL goes
   through the $250 box. Multi-tenant office goes through HACKER-PRO. IC
   committee escalations go through this 27B at HACKER-AGX.

**7. SR HACK SIGNED-OFF · the discipline transfer**
   This cook went through the 5-stage senior-hack review chain. The receipt
   is in REVIEWS/atlas-qwen-27b-cook-review-chain.md. No silent corruption.
   No shortcut bug. No corpus dilution.
```

### 7 · Risk (limitations · failure modes · what we DON'T claim)

```markdown
## Risk · what we don't claim

**1. Not a tour replacement.**
   This model underwrites from documents. It does NOT tour properties. STNL
   and document-pure deals are the lane. Multi-asset portfolio repositioning
   with on-site judgment is NOT.

**2. Not a market-maker.**
   The model produces decisions and rationale. It does not execute trades or
   sign agreements. Human broker / IC committee owns final decision.

**3. Domain-pure · not a general assistant.**
   Trained on CRE corpus. Outside CRE the base Qwen3.6-27B is what shows
   through. Don't ask it to write Python or compose music.

**4. Cook-grade ≠ ship-grade without validation.**
   Eval_loss is a signal, not a guarantee. The Numeric Gate (Stage 2) catches
   the predictable failure modes (cap-direction · refusal · self-coherence ·
   etc.). We do NOT ship without the Gate in front.

**5. Context window 32K served (262K capable).**
   Large rent rolls + multi-document deal packets fit in 32K but not always
   in INT4 deployment. Plan accordingly.

**6. Receipts are anchored, not legally-binding.**
   The Defendable receipt proves WHAT the model produced and WHEN. It does
   not constitute legal opinion. Counsel still required for binding documents.
```

### 8 · Pricing / Tier (what license tier)

```markdown
## Pricing · the license tiers

This model is licensed via the Atlas OS pricing stack:

| Tier              | What you get                                  | $/mo     |
|-------------------|----------------------------------------------|----------|
| HACKER ($250)     | Hack-Deed-Maker-3B intake · NOT this model    | one-time |
| HACKER-PRO ($599) | Bookmaker-8B analyst · NOT this model         | one-time |
| HACKER-AGX ($2K)  | THIS MODEL (Atlas-Qwen-27B) for branch-tier | one-time |
| Datacenter        | THIS MODEL via api.swarmandbee.ai            | $4,999/yr|
| Royalty           | Per-deal fee on Hedera-anchored AIOV reports | $0.10-1  |

**Volume tier:**
- < 100 deals/mo:   $4,999/yr subscription · $0.50 per anchored deal
- 100-1K deals/mo:  $9,999/yr · $0.30 per anchored deal
- 1K-10K deals/mo:  $24,999/yr · $0.15 per anchored deal
- > 10K deals/mo:   custom enterprise · $0.10 per anchored deal

**Unit economics for the customer:**
- Atlas v1 analyst desk replaced (per Donovan's roster): $180-220K/yr base
  + commission · plus benefits + overhead
- This model + AIOV pipeline: ~$25-40K/yr all-in including subscription +
  per-deal anchors + sovereign-compute hardware amortization
- ~80-85% reduction in analyst desk cost · with full Defendable receipts
- The labor-business model holds.
```

### 9 · Track Record (lineage · receipts · prior cooks)

```markdown
## Track Record · the proof points

**The lineage chain (every cook earned its slot):**

| Cook                           | Final eval_loss | Tokens | Hardware     | Wall-clock |
|--------------------------------|-----------------|--------|--------------|------------|
| SwarmCurator-9B-P1            | 0.665           | 27,436 | PRO 6000 96GB| 2.49h      |
| SwarmCurator-9B-P2            | 0.707           | 22,132 | PRO 6000 96GB| 3.37h      |
| SwarmCurator-2B-v1            | 0.880           | 8,963  | RTX 3090     | 0.54h      |
| SwarmCurator-27B-v1           | 0.477           | 62,525 | PRO 6000 96GB| 14.38h     |
| Atlas-70B (Llama comparator)  | 0.5018          | 125,651| 2× PRO 6000  | 73.57h     |
| Bookmaker-8B (Granite)        | 0.467 ⚡        | 125,651| RTX 5090     | 8.89h      |
| Hack-Deed-Maker-3B (Granite)  | 0.5383          | 125,651| RTX 5090     | 5.20h      |
| **THIS COOK · Atlas-Qwen-27B**| **<TBD>**       |244,725 | PRO 6000 96GB| **<TBD>**  |

⚡ = the moment Granite-8B beat the 70B Llama at step 600 · proving smaller
+ better-curated wins.

**5 senior-hack reviews completed before THIS cook fired** · 65-75% lobotomy
probability reduced to 20-25% via the four-fix prescription. The receipt
chain is in REVIEWS/.

**18+ public commits** to github.com/SudoSuOps/atlas-3.6-27B-cook-book · every
cook decision audit-trailed · every fix linked · every review referenced.
```

### 10 · Closing (terms · next steps)

```markdown
## Closing · the deal

**Available:** Q3 2026 (post sr-hack final sign-off · pending judge_cre_30k
held-out eval).

**Demo:** chat UI live at <hostname>:7860 (LAN-only · pre-greenlight).
Customer can drop real deal packets · run correction-loop discipline · see
the model fail at known clamps (we don't hide failure modes).

**Diligence package:**
  - cookbook (this repo) · github.com/SudoSuOps/atlas-3.6-27B-cook-book
  - sr hack review chain · REVIEWS/atlas-qwen-27b-cook-review-chain.md
  - flightsheet · FLIGHTSHEETS/atlas-qwen-27b-flightsheet.md
  - AIOV contracts · AIOV/contracts/{deal_input,decision_output}.json
  - Defendable receipt · atlas.defendable.eth/<cook-id> (post-cook)
  - Hedera transaction · topic 0.0.10291838

**Contact:** Donovan · Founder · Family Office · Swarm and Bee LLC
  - swarmandbee.eth (ENS · primary handle)
  - @swarmandbee (X)
  - signal at swarmandbee.ai/signal (the public blog)
  - D-U-N-S 138652395

**Verified · Vetted · Virtu.**

The standard isn't *good enough to ship*. The standard is *something we'd
put our own name on*.
```

### 11 · Appendix (sha receipts · cookbook commits · technical spec)

```markdown
## Appendix · technical receipts

[exhaustive sha256s · cookbook commit list · base config · recipe values ·
 corpus manifest entries · canary results · all the engineering detail
 that doesn't belong in the front of the OM but matters for diligence]
```

---

## How to actually generate an OM

```
You:    /cook-om <cook-name>

Claude: I'll pull from:
        - <cookbook>/COOKS/<cook>.md (recipe + projections)
        - <cookbook>/FLIGHTSHEETS/<cook>-flightsheet.md (final receipts)
        - <cookbook>/REVIEWS/<cook>-review-chain.md (sr hack sign-off)
        - <cookbook>/AIOV/contracts/ (the I/O schemas the cook serves)
        - cookbook README (lineage chain · prior cooks)
        
        I'll fill the 11-section template + drop the OM at
        <cookbook>/OM/<cook>-om.md
        
        For sections that need YOUR input (pricing tier, target buyer,
        positioning copy) · I'll prompt you per section.
```

---

## What good OMs do that bad ones don't

```
GOOD OM                              BAD OM
─────────────────────────────────────────────────────────────────────
Receipts grounded                    Marketing copy
Specific (sha · timestamp · cap rate) Vague ("fast" · "smart" · "AI-powered")
Honest about risk                    Hides limitations
Maps to ecosystem                    Standalone hype
Compares to alternatives             Pretends competition doesn't exist
Pricing transparent                  "Contact for pricing"
Lineage shown                        First cook · no track record
Track record open                    Cherry-picked benchmarks
Verifiable on-chain                  "Trust us"
Customer can rebuild                 Black box
```

---

## Iconic line

> *"The flightsheet is for the engineer. The OM is for the customer.*
> *Both are receipts. Both are public. Both close the deal."*

---

## See also

- `/cook-flightsheet` · the formal cook record (engineer-facing · maintenance log)
- `/canary-then-cook` · the senior-hack review chain (cited in OM Section 9)
- `/gpu-miner-review` · the hardware discipline (cited in cost economics)
- `/cook-monitoring` · the telemetry stack (feeds flightsheet · feeds OM cost section)
- `/client-update` · the brief periodic updates (subset of OM ·  cadence-driven)
