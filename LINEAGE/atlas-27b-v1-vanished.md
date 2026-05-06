# Atlas-27B v1 · the original · vanished

The first Atlas. The doctrine model that worked. The weights that were lost.

---

## What it was

Atlas-27B v1 was the original Swarm broker doctrine model — cooked early 2026,
deployed against real CRE workflows, validated against actual deals. The broker
who built it (Donovan, $8B closed in 30 years of CRE) put his name on its
output. **Operationally, it was the strongest doctrine model the Swarm had ever
shipped.**

```
KNOWN FACTS (from internal memory · not all archived)

Base model              Qwen2.5/3.5 lineage (exact base under reconstruction)
Method                  bf16 LoRA r=64 α=32 (the seed of the Gold Standard)
Corpus                  ~19,500 pairs (the early Atlas v1 foundation set ·
                        appears in Block-0 / Block-1-v2 as "atlas_v1_foundation"
                        with 16,938 records after fingerprint dedup of 45,039 raw)
Recipe                  Conservative Gold Standard precursor
                        · LR 1e-5 cosine (the rule that became the standard)
                        · effective batch 32
                        · early stopping
Defendable namespace    atlas.defendable.eth
Role in pipeline        Doctrine analyst · the IC memo brain · the valuation
                        narrative · the recommendation calibration

What it did well        Pass/proceed mental model · IC memo language ·
                        comp framing · cap-rate vocabulary discipline ·
                        narrative tone calibrated for institutional CRE
What got lost           The cooked weights themselves · no surviving archive
What survived           The 16,938-record foundation set · the recipe lineage ·
                        the role in the pipeline · the broker validation
                        memory of how it performed
```

---

## What happened to it

The weights vanished. No archive. No checkpoint mirror on NAS. No backup. The
only known surviving artifact is the **foundation training set** (`atlas_v1_foundation`
in our corpus inventory) — 45,039 raw records that were later deduped to 16,938
unique fingerprints and folded into Block-0 and Block-1-v2.

This isn't a unique-to-Swarm hazard. **All cooked LLM weights are precious and
mortal.** A drive failure, a `rm -rf` on the wrong path, a vast.ai instance reaped
without exporting — any of these can vanish a $1,000-electrons cook in seconds.
The lesson: every future cook **MUST** mirror to NAS at save_steps boundaries
AND on completion, with sha256 receipts, before the cook host is reused.

(That's a discipline now baked into the granite-models-cookbooks training
scripts via `NAS_MIRROR` rsync hooks. It wasn't there for Atlas v1.)

---

## Why we're rebuilding it now

Four substrate-comparison cooks (Llama-3.3-70B + Granite-4.1-3B/8B/30B) on
different recipe families taught us the receipts that pointed us back at where
we started:

```
Llama-3.3-70B (Atlas-70B)          0.5018 final eval · 73h cook · the
                                    comparator that locked nothing definitive
Granite-4.1-8B (Bookmaker-8B)       0.467 final eval · 8.89h · BEAT 70B Llama
Granite-4.1-3B (Hack-Deed-Maker)    0.5383 final eval · 5.20h · intake bee
Granite-4.1-30B (Atlas-Granite)     KILLED pre-step-200 · Donovan's review said
                                    "Granite was wrong family for the doctrine tier"
                                    · Qwen substrate gut-call instead

The 5 correction-loop sessions on Bookmaker-8B + Hack-Deed-Maker-3B identified
3 cook-time blockers that the Numeric Gate addresses at serve-time · but the
underlying SUBSTRATE question kept pointing back: Atlas v1 (Qwen) was operationally
the strongest doctrine the Swarm shipped. The receipts didn't say "Granite at
30B will beat that" — they said "smaller Granite already beats Llama, and we
should test Qwen at the doctrine tier next".

So we cook the substrate that worked the first time · with a corpus 25× larger
· using the proven Gold Standard recipe · on the modern Qwen3.6-27B base.
```

---

## What gets carried forward · what doesn't

```
CARRIED FORWARD into Atlas-Qwen-27B (the rebuild)
  ✓ The role · doctrine analyst at the AIOV pipeline stage 1 (LLM draft)
  ✓ The Defendable namespace · atlas.defendable.eth
  ✓ The 16,938 foundation pairs · folded into Block-1-v2 (atlas_v1_foundation bucket)
  ✓ The recipe lineage · LR 1e-5 cosine · r=64 α=32 · effective batch 32 ·
    epoch 0.6 · early stopping (now the formal Gold Standard)
  ✓ The substrate intuition · Qwen for narrative doctrine tier

DELIBERATELY LEFT BEHIND
  ✗ The vanished weights themselves · they're gone · we don't try to reverse-
    engineer them from outputs · we cook fresh on the bigger corpus
  ✗ The Qwen2.5 base · we move forward to Qwen3.6 (same architecture class ·
    better pre-train · stronger benchmarks)
  ✗ The smaller corpus · Block-1-v2 (407K records) is 25× larger than the
    original 16,938 foundation set · the rebuild gets a richer dataset
  ✗ Any "the original was perfect" mythology · we measure the new cook against
    Bookmaker-8B's 0.467 receipt · honest comparison, not nostalgia

NOT FORGOTTEN · the discipline lesson
  → Every cook from here forward MUST mirror weights to NAS continuously ·
    sha256 anchored · so we don't lose another doctrine model to a failed disk
    or a re-purposed rig.
```

---

## See also

- `LINEAGE/gold_standard_lineage.md` · how the Atlas v1 recipe became the formal
  Gold Standard via SwarmCurator-9B/27B builds
- `COOKS/atlas-qwen-27b.md` · the rebuild plan
- External: `granite-models-cookbooks` · the substrate comparison receipts that
  pointed back at Qwen
