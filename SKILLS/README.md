# Skills

> Custom Claude Code skills · the operational playbooks that survive across
> conversations and across team members.

---

## Why this folder exists

Custom skills are markdown prompts invoked as `/<skillname>` slash commands
in Claude Code. They bake operational discipline into reusable artifacts.
Saved at `~/.claude/skills/<name>/SKILL.md` for personal use · or anywhere
in a project tree for team-wide adoption.

This cookbook ships the skills we've earned with receipts · so anyone
cloning the repo can install them locally and inherit the discipline.

---

## Skills in this cookbook · the 6-skill cook stack

```
SKILLS/
├── README.md                                    this file
├── canary-then-cook/SKILL.md                    senior-hack review-loop discipline
│                                                 · 5-stage process · catches silent-
│                                                 corruption bugs before GPU burn
│                                                 · the 65-75% → 20-25% probability swing
├── gpu-miner-review/SKILL.md                    full rig audit + sweet-spot finder ·
│                                                 the rigs are SR Managing Directors ·
│                                                 thermal bands · algorithm classification
│                                                 (compute / memory / I/O bound) · per-cook-
│                                                 grade hardware policy · fleet-wide audit
├── cook-flightsheet/SKILL.md                    every cook gets a flightsheet · the
│                                                 formal pre-flight + in-flight + post-flight
│                                                 doc · 5 sections · sr hack signs off
│                                                 · cap-grade classification (5-cap STNL)
│                                                 · training blocks (segment max_steps)
│                                                 · energy cost-to-cook ($0.10/kWh)
├── cook-monitoring/SKILL.md                     full observability during cooks ·
│                                                 6 telemetry streams · anomaly playbook
│                                                 · feeds flightsheet auto · the production
│                                                 miner's dashboard
├── client-update/SKILL.md                       periodic status reports for the
│                                                 customer/investor/auditor · 6 update types
│                                                 · brief · receipts-grounded · honest
└── cook-om/SKILL.md                             OM (Offering Memorandum) · the sales
                                                 document · CRE-broker 11-section format ·
                                                 Build / Domain / Ecosystem / Credit
                                                 Velocity / Why Buy / Risk / Pricing /
                                                 Track Record / Closing
```

---

## The full discipline (when each skill fires in the cook lifecycle)

```
LIFECYCLE STAGE                       SKILLS THAT FIRE
─────────────────────────────────────────────────────────────────────────
1. Cook design + corpus build         /canary-then-cook (Stage 1 review)
2. Pre-flight checklist               /gpu-miner-review · /cook-flightsheet
                                       (pre-flight · cap-grade · blocks plan)
3. Canary smoke (~10 min)             /canary-then-cook (Stage 2 + 3)
4. Final-look review                  /canary-then-cook (Stage 4)
5. Full cook fires                    /cook-monitoring (persistent monitor)
                                       /gpu-miner-review (during-cook bands)
                                       /cook-flightsheet (in-flight Section 3)
                                       /client-update (Type 1 + cadence)
6. Cook lands                         /cook-flightsheet (Section 4 post-flight)
                                       /client-update (Type 5)
                                       /gpu-miner-review (post-cook validation)
7. Post-cook review                   /canary-then-cook (Stage 5 review)
                                       /cook-flightsheet (Section 5 sign-off)
                                       /client-update (Type 6 sign-off)
8. Production packaging               /cook-om (the sales document)
                                       /client-update (Type 6 final)
```

---

## Installation

### Option 1 · personal install (works in any project)

```bash
cp -r SKILLS/* ~/.claude/skills/
# now /canary-then-cook · /gpu-miner-review · /cook-flightsheet ·
# /cook-monitoring · /client-update · /cook-om all work in any
# Claude Code session
```

### Option 2 · project-scoped install

```bash
mkdir -p .claude/skills
cp -r path/to/atlas-3.6-27B-cook-book/SKILLS/* .claude/skills/
# all 6 skills work inside this project · ships with the repo
```

---

## The discipline ladder · why these 6 skills together

```
1. /canary-then-cook        WHO reviews   (the sr hack discipline)
2. /gpu-miner-review        WHAT to run   (hardware health · the SMD rigs)
3. /cook-flightsheet         WHAT to record (the formal record · sign-off)
4. /cook-monitoring          HOW to watch   (the telemetry stack)
5. /client-update            WHO to tell    (the customer-facing comms)
6. /cook-om                  WHAT to sell   (the offering · the close)
```

These aren't independent skills · they're a STACK. The flightsheet pulls
from monitoring. Client-update pulls from flightsheet. OM pulls from
flightsheet + reviews + monitoring. Senior hack signs off across the stack.

**Pay the lesson once · ship the skill forever. Six lessons paid in full.**

---

## Iconic lines (one per skill)

```
/canary-then-cook    "Loss curves measure absorption.
                      Correction loops measure judgment.
                      Senior hack reviews catch the silent corruption neither sees."

/gpu-miner-review    "Our rigs are SMDs. Treat them that way.
                      The cook that lands at 75°C will land 100 times.
                      The cook that lands at 92°C will land once."

/cook-flightsheet    "The flightsheet is the receipt that survives the engineer.
                      Every cook gets one. The SR hack signs it off."

/cook-monitoring     "Step blocks are signal. Thermal is signal. Disk is signal.
                      NAS sync is signal. Heartbeat is signal.
                      Loss alone is half the picture."

/client-update       "Tell them what's happening. Tell them when something changes.
                      Link to the receipts. That's the entire job."

/cook-om             "The flightsheet is for the engineer.
                      The OM is for the customer. Both are receipts.
                      Both are public. Both close the deal."
```

---

## Contributing a new skill

If a session produced a hard-won lesson worth permanent capture:

```
1. Write the SKILL.md with YAML frontmatter:
   ---
   name: skill-name (kebab-case · matches /slashcommand)
   description: one-line · what it does + when to invoke
   ---
   
   # /skill-name · short tagline
   
   [body]

2. Test · invoke /skill-name in a real session · iterate until clean

3. Commit to this folder + push · also drop into ~/.claude/skills/

4. Reference the skill in any cookbook doc that benefits from the discipline
```
