# AIOV · Product Contract Reference

> The structured I/O contracts the cooked Atlas-Qwen-27B model produces, and
> the deterministic validators that gate AIOV rendering.

---

## Why this folder exists

After the Atlas-27B v1 (SwarmCapitalMarkets-27B) cook lineage was traced via
the `swarm-capital-markets` repo, the **canonical AIOV I/O contracts** were
recovered. They're ported here as the source of truth for what Atlas-Qwen-27B
should produce post-cook.

The granite-models-cookbooks 5-stage pipeline:

```
1. Bookmaker drafts        →  THIS COOK = analyst tier · IC memo prose
2. Numeric Gate            →  Stage 2 deterministic Python (port from skills/*/validator.js)
3. Tribunal validates      →  Stage 3 multi-judge eval (rubric port from credit_committee skill)
4. AIOV renders            →  Stage 4 customer-facing PDF/HTML  ← uses decision_output.json
5. Receipt anchors         →  Stage 5 Hedera receipt at aiov.defendable.eth/<deal_id>
```

The contracts in `contracts/` are what stages 2-4 enforce. The Atlas-Qwen-27B
cook should produce outputs that conform · the Numeric Gate validates against
the schemas · the AIOV renderer reads from validated outputs.

---

## The contracts

### `contracts/deal_input.json`

The structured input the model consumes. All required fields:

```
asset_type      one of: office · industrial · multifamily · retail · hotel ·
                 data_center · mixed_use · cold_storage
purchase_price  number (USD · raw value · no abbreviations)
noi             number (USD · net operating income)
```

Plus optional:
- `occupancy` (decimal · 0.92 not 92%)
- `debt_request` object (ltv · interest_rate · term · amort · io_period)
- `macro_context` object (sofr · treasury_10yr · cap_rate_trend · cmbs_delinquency)
- `sponsor` object (aum · track_record · net_worth · liquidity · coinvest_pct)
- 17 specialty fields (sf · units · year_built · walt_years · senior_ltv ·
  mezz_rate · equity_pct · dscr_requirement · ltv_limit · debt_yield_min · etc.)

### `contracts/decision_output.json`

The structured output the model produces. Required fields:

```
deal_id      string
decision     one of: approve · approve_with_conditions · restructure · decline ·
                     watchlist · distressed_opportunity
confidence   0.0 - 1.0
analysis     deterministic metrics object:
               cap_rate · dscr · ltv · debt_yield ·
               max_loan_dscr · max_loan_ltv ·
               break_even_occupancy · refinancing_gap ·
               levered_irr · unlevered_irr · equity_multiple
```

Plus structured optional:
- `recommended_max_loan` (rounded to nearest $100K)
- `binding_constraint` enum (ltv · dscr · debt_yield)
- `risk_flags[]` (max 5 · lowercase snake_case)
- `capital_stack_recommendation` object
- `scenario_analysis` (base · downside · severe)
- `conditions[]` (required for approve_with_conditions)
- `rationale` (IC-grade reasoning · min 50 chars)
- `memo_summary` string

---

## How this changes the cook

### Pre-cook (Block-1-v3 already aligns)

Block-1-v3's bee_hive_train_data (94,768 records) and capital-markets streams
(10,209 records · 21 shards) ALREADY produce structured "JSON Intelligence
Object" outputs in the format these schemas describe. The cook learns the
discipline implicitly from the corpus.

The corpus says (per stream_blockchain.jsonl sample):
```
"Return JSON Intelligence Object: {asset_summary, valuation, token_structure: {...}}"
```

The contracts here say specifically what those JSON objects should contain.
Confirms our trajectory.

### Post-cook (Numeric Gate port from skills/*/validator.js)

The Granite cookbook's Numeric Gate spec (6 rules · cap-direction · refusal ·
recommendation cohere · source hierarchy · status enum · range sanity) needs to
align with these schemas. Specifically:

- Status enum from `decision_output.json` is the canonical list. Our earlier
  Numeric Gate listed `INSUFFICIENT-DATA / REJECT / HOLD / PROCEED-TO-DILIGENCE
  / CONDITIONAL-APPROVAL / APPROVE` — the schema says `approve /
  approve_with_conditions / restructure / decline / watchlist /
  distressed_opportunity`. **The schema list is canonical.** Our Granite-side
  Numeric Gate doc should be reconciled.

- The `analysis` object's required metrics (cap_rate · dscr · ltv · debt_yield ·
  etc.) tell us what numbers MUST be present in every output. The Numeric Gate
  validates each.

- `confidence` 0-1 is required. The Gate flags missing or out-of-range confidence.

### Post-cook eval

`eval/eval_swarmcapital.jsonl` from the source repo (180-prompt eval suite per
the commit history) is the SECOND eval pool we should run alongside the
996-record cross-cook holdout. Different angle · same model.

---

## SwarmSkills (the validators · port to Numeric Gate)

The source repo `swarm-capital-markets/skills/` has 7 installable AI skills
each with a deterministic JS validator:

```
deal_packet/         schema.json + validator.js + examples.md
underwrite/          schema.json + validator.js
cap_stack_builder/   schema.json
credit_committee/    schema.json + validator.js
waterfall_model/     schema.json
distress_analyzer/   schema.json + validator.js
loan_workout/        schema.json + validator.js
```

The validator.js files are the operational expression of the Numeric Gate
rules. **Action item for AIOV pipeline build:** port these to Python or wrap
them as a Node subprocess called from the AIOV stage 2.

---

## Lineage

```
SwarmCapitalMarkets-27B (Atlas v1)              The original cook
  · Qwen3.5-27B base · Unsloth · LR 2e-5 → 1e-5 (after kill/restart)
  · 45,039 train pairs
  · weights vanished · dataset survives in swarm-and-bee-datasets/capital-markets/
  · AIOV CONTRACTS preserved here in github.com/SudoSuOps/swarm-capital-markets

Atlas-Qwen-27B (this cook · the rebuild)
  · Qwen3.6-27B base · vanilla transformers + sdpa (sm_120 compat)
  · 486,428 train pairs (Block-1-v3 · Path B)
  · same Gold Standard recipe values
  · same atlas.defendable.eth namespace
  · trained to produce outputs conformant with these AIOV contracts
```

---

## See also

- `contracts/deal_input.json` · canonical input schema (ported verbatim)
- `contracts/decision_output.json` · canonical output schema (ported verbatim)
- External: [`swarm-capital-markets`](https://github.com/SudoSuOps/swarm-capital-markets)
  · the original repo · skills/ · validators · eval suite · cook scripts
- `LINEAGE/atlas-27b-v1-vanished.md` · what was lost
- `COOKS/atlas-qwen-27b.md` · the rebuild plan
- granite-models-cookbooks/COOKS/aiov-numeric-gate-spec.md · the Stage 2 spec
  (needs reconciliation against decision_output.json's status enum)
