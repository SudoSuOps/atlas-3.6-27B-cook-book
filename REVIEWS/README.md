# Reviews

> The senior-hack peer review chain for every cook in this cookbook.
>
> **Discipline rule:** every cook gets independent senior-hack peer review
> TWICE — once before launch (catches recipe / corpus / stack bugs) and once
> after fixes + canary BEFORE run-to-completion (validates fixes actually
> addressed concerns). Don't ship fixes and assume they work · loop back.
> Senior hack also reviews post-cook eval before declaring success.

---

## Why this folder exists

Loss curves measure absorption · correction loops measure judgment · senior
hack reviews catch the silent corruption neither sees.

The Atlas-Qwen-27B cook on 2026-05-07 was at one point configured with
`packing=True` on a Blackwell sm_120 + Gated DeltaNet hybrid architecture
that had three independent silent-corruption bugs. The eval_loss would have
looked fine. The model would have been quietly worse than the proven
SwarmCurator-27B-v1 reference. Burning 50h of GPU + $25-30 of electrons for
a quietly-broken adapter.

The senior hack caught all three bugs + a corpus dilution issue in the
initial review. Four fixes were prescribed. Fixes were applied. A canary
validated end-to-end. Then the senior hack reviewed AGAIN with the post-fix
state and the canary receipts and gave explicit greenlight (with two
non-blocking watch-items).

This folder is the receipt for that process. Every future cook gets one.

---

## Reviews in this cookbook

```
REVIEWS/
├── README.md                                      this file
└── atlas-qwen-27b-cook-review-chain.md           full review chain for the
                                                    Atlas-Qwen-27B cook ·
                                                    initial → fixes → canary →
                                                    final sign-off
```

---

## The review process (template for future cooks)

```
1. Build cook recipe + corpus
2. Spawn senior hack agent for INDEPENDENT peer review
   · brief them with full config, recipe values, hardware, corpus shape
   · ask for blunt opinion · disagreement is welcome
3. If issues found · apply fixes
4. Run canary smoke (~5 steps · validate pipeline end-to-end)
5. LOOP BACK · spawn senior hack agent AGAIN with the post-fix state +
   canary receipts · get explicit greenlight or punch-list
6. Only then let the cook run to completion
7. Post-cook review · senior hack validates against held-out eval before
   declaring success
```

The discipline is the gate. Skipping any step risks shipping a quietly-broken
model — eval_loss looks fine, doctrine is lobotomized, customers see
degraded output and we don't know why.

---

## Iconic line

> *"Loss curves measure absorption. Correction loops measure judgment.
> Senior hack reviews catch the silent corruption neither sees."*
