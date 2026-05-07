---
name: canary-then-cook
description: Senior-hack review-loop discipline for any expensive ML cook · catches silent-corruption bugs and corpus dilution before GPU burn · applies the 5-stage process locked in the Atlas-Qwen-27B cook (saved this cook from a 65-75% lobotomy probability)
---

# /canary-then-cook · Senior Hack Review Discipline

Use this skill before kicking off any LoRA training cook, vLLM deploy, or full
dataset migration that would burn meaningful GPU time or electrons.

The rule (per Donovan, post-Atlas-Qwen-27B cook): **the sr hack always gets
the final look.** Loss curves measure absorption · correction loops measure
judgment · senior hack reviews catch the silent corruption neither sees.

---

## When to invoke

```
Trigger:  any cook expected to burn > 4h GPU or > $10 in electrons
Trigger:  any new corpus going into training (esp. mixed-tier or > 100K records)
Trigger:  any architecture / stack change vs the proven Gold Standard
          (e.g. swapping Unsloth → vanilla, adding packing, changing FA backend,
           moving to new GPU class, etc.)
Trigger:  any second cook after a kill (validate the kill was correct + new
          recipe addresses the root cause)
```

---

## The 5-stage process

```
1. INITIAL REVIEW (pre-launch)
   spawn senior hack agent with full config · brief them honestly:
     - exact recipe values (LR, scheduler, batch, max_seq_len, epoch_fraction)
     - corpus shape (record count, tier mix, sha256, source files)
     - hardware + stack (GPU class, framework versions, attention impl)
     - smoke results so far (if any)
     - what the proven reference is (Gold Standard cook + receipts)
   ask for blunt opinion · disagreement welcome
   capture: bug list + fix prescription + failure probability

2. APPLY FIXES
   address every bug surfaced · don't pick-and-choose
   if a bug is "we accept this risk" - say so explicitly + write WHY
   commit fixes to git with a clear message linking to the review

3. CANARY SMOKE (~5 cook steps · ~10 min)
   tiny dataset slice (500 train · 50 eval) with full corpus loader
   ALL fixes active · verify pipeline end-to-end:
     ✓ tokenizer loads
     ✓ base model loads
     ✓ LoRA attaches with expected trainable count
     ✓ first step runs · loss is finite · gradients flow
     ✓ first eval runs · loss in plausible range
     ✓ adapter saves at checkpoint
     ✓ no CUDA errors · no OOM · no contamination signals

4. FINAL-LOOK REVIEW (post-canary · BEFORE run-to-completion)
   spawn senior hack agent AGAIN with the post-fix state + canary receipts
   explicit ask: greenlight to run-to-completion OR punch-list?
   capture: residual probability + watch-items
   DON'T SHIP FIXES AND ASSUME THEY WORK · LOOP BACK

5. POST-COOK REVIEW (after cook lands)
   senior hack reviews:
     - eval_loss trajectory shape (vs reference cook)
     - held-out judge eval (e.g. judge_cre_30k for CRE work · 180-prompt eval
       for SwarmCapital-style cooks)
     - chat-UI correction-loop sessions (qualitative · catches lobotomization)
     - downstream A/B vs prior reference (proves the cook actually added
       knowledge vs just style)
   greenlight to ship · or punch-list for v(N+1) cook
```

---

## How to actually run this in a Claude Code session

```
You (the user):  /canary-then-cook

Claude:          I'll walk through the 5-stage senior-hack review discipline
                 for your cook. First, give me the inputs:
                 
                 1. Recipe values (or path to train script)
                 2. Corpus stats (records, tier mix, sha256, paths)
                 3. Hardware + stack (GPU, transformers/peft/trl versions, attn impl)
                 4. The proven reference cook (or "first of its kind")
                 
                 OR point me at an existing cookbook (e.g.
                 /tmp/atlas-3.6-27B-cook-book/) and I'll extract the inputs.

You:             [provides inputs]

Claude:          Stage 1 · spawning senior hack for initial peer review...
                 [spawns Agent with general-purpose subagent_type · briefs with
                  full inputs + asks for blunt opinion]

(senior hack returns)

Claude:          Stage 1 found N issues. Apply the fixes? [details]

You:             yes
                 (or "skip fix M because [reason]" - they push back if needed)

Claude:          Stage 2 · applying fixes...
                 [edits scripts · commits to git]
                 
                 Stage 3 · firing canary smoke (5 steps · ~10 min)...
                 [launches with --smoke-test or equivalent]

(canary lands)

Claude:          Canary clean. Final-look review? (recommended)

You:             yes

Claude:          Stage 4 · spawning senior hack for final sign-off with
                 post-fix state + canary receipts...

(senior hack returns greenlight or punch-list)

Claude:          Greenlight received with N watch-items. Fire the full cook?

You:             fire it

Claude:          Stage 5 will fire automatically when the cook lands · senior
                 hack will review against held-out eval + correction-loop
                 sessions before declaring success.
```

---

## Anti-patterns this skill prevents

```
× Shipping fixes and assuming they work
  Counter-pattern: always loop back · the fix may have introduced a fifth bug

× Quoting an absolute eval_loss number from a different corpus
  Counter-pattern: compare TRAJECTORY shape · not absolute numbers across cooks

× Trusting eval_loss alone
  Counter-pattern: hold-out judge eval + chat-UI correction loop · catches
  lobotomization that doesn't show in loss curves

× Bringing fast paths to architectures they weren't validated on
  Counter-pattern: Unsloth's packing kernels work for Qwen3.5 because Unsloth
  has custom GDN-aware packing · TRL's BFD doesn't · adapt assumptions, not
  just API call

× Rubber-stamping reviews
  Counter-pattern: disagreement is the value · engineers who don't push
  back aren't doing review · they're doing approval
```

---

## Reference receipts

This skill encodes the discipline that produced these specific saves:

```
Atlas-Qwen-27B cook · 2026-05-07
  Initial review caught:  TRL #3705 seq_lengths strip
                          padding-free needs FA2 (we're SDPA-only)
                          Gated DeltaNet state-leak under packing
                          7-tier corpus dilution
  Failure probability:    65-75% before fixes → 20-25% after
  Saved:                  ~50h GPU + $25-30 electrons + a quietly-broken model

Atlas-9B CRE cook eval
  Negative result surfaced via base-model A/B comparison:
  fine-tuning gave CRE mechanics but no actual trade knowledge
  → guided next cook's corpus revision rather than shipping a "good-looking"
    model that didn't actually know how to close a deal

Bookmaker-8B + Hack-Deed-Maker-3B cooks · 5 correction-loop sessions
  Each cook passed the canary + math eval BUT correction-loop discipline
  surfaced 3 production blockers:
    cap-rate vocabulary
    multifamily cash flow framing
    IRR refusal under partial data
  Without the loop · the AIOV pipeline would have shipped models that
  produce broker-grade-LOOKING outputs that fail under broker-grade scrutiny
```

---

## Iconic line

> *"Loss curves measure absorption. Correction loops measure judgment.
> Senior hack reviews catch the silent corruption neither sees."*

---

## See also

- `~/.claude/projects/-home-swarm-Desktop/memory/sr_hack_final_look_rule.md`
  durable feedback memory · the rule itself
- `atlas-3.6-27B-cook-book/REVIEWS/atlas-qwen-27b-cook-review-chain.md`
  full worked example · 65-75% → 20-25% probability swing
- `granite-models-cookbooks/COOKS/correction-loop-findings.md`
  qualitative-eval discipline (5 sessions across Bookmaker-8B + 3B)
- `granite-models-cookbooks/COOKS/aiov-numeric-gate-spec.md`
  Stage 2 deterministic validator (the spreadsheet checker behind the LLM)
