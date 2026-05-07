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

## Skills in this cookbook

```
SKILLS/
├── README.md                          this file
└── canary-then-cook/
    └── SKILL.md                       senior-hack review discipline ·
                                        5-stage process · catches silent-
                                        corruption bugs before GPU burn
```

---

## Installation

Two paths:

### Option 1 · personal install (works in any project)

```bash
cp -r SKILLS/canary-then-cook ~/.claude/skills/
# now /canary-then-cook works in any Claude Code session
```

### Option 2 · project-scoped install

```bash
# inside your project
mkdir -p .claude/skills
cp -r path/to/atlas-3.6-27B-cook-book/SKILLS/canary-then-cook .claude/skills/
# /canary-then-cook works inside this project only · ships with the repo
```

---

## The pattern this folder enforces

For every operational lesson Swarm pays for · we ship the lesson back as a
skill. Receipts in · skills out. Future engineers (and future Donovans)
inherit the discipline without having to re-learn it.

```
Pay the lesson once · ship the skill forever.
```

---

## Contributing a new skill

If a session produced a hard-won lesson worth permanent capture:

```
1. Write the SKILL.md following the YAML-frontmatter format:
   ---
   name: skill-name (kebab-case · matches /slashcommand)
   description: one-line · what it does + when to invoke
   ---
   
   # /skill-name · short tagline
   
   [body]

2. Test it · invoke /skill-name in a real session · iterate until clean

3. Commit to this folder + push · also drop into ~/.claude/skills/ for
   personal use

4. Reference the skill in any cookbook doc that benefits from the discipline
```
