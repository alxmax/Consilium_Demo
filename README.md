# Consilium

Three specialized sub-agents (Generator / Control / Conservator) 
are orchestrated by a Claude Code skill that aggregates their outputs 
via configurable voting schemes into a canonical JSON decision. — 
creative, analytical, and risk-focused — then vote on the best approach.

Built as a Claude Code skill (identifier: `consilium`). The three voices 
(Generator / Control / Conservator) run in parallel as separate sub-agents, 
with explicit voting and veto logic aggregated into a canonical JSON report.

- **Generator** (creative) — proposes alternatives, divergent thinking
- **Control** (analytical) — verifies technical correctness
- **Conservator** (prudent) — assesses risk and reversibility

The voices are prompt-constrained from doing each other's job and run as separate sub-agents (via the Claude Code `Agent` tool). Their outputs are aggregated by a voting scheme with veto (default: `conservative_override`) into a canonical JSON report plus a one-line console summary.

> **About this repository.** Public showcase / portfolio demo, maintained by **Schipor Alexandru Ionut**. The live skill source is in a private repository — this repo contains the design, the architecture poster, and a canonical run example. For source-code access requests, see contact details on my CV.

## Live demo

**[https://alxmax.github.io/Consilium_Demo/](https://alxmax.github.io/Consilium_Demo/)**

Open the link in any modern browser — no install needed. Four tabs walk you through the system from overview to interactive flow demo.

## Try the visual architecture

Open [`architecture.html`](./architecture.html) in any modern browser. Four tabs:

- **Architecture** — system overview, the three voices, aggregation schemes
- **Flow** — step-by-step deliberation
- **Modes** — Parallel / Dialectic / Sequential — Blind / Trias
- **Patterns** — interactive flow diagram. Click any flow in the right sidebar to highlight its path through the system. Includes the Voices bias profile, the Trias team weights, the 9-sub-agent Trias deep-dive, and the calibration loop sub-diagram. A **Play tour** button auto-plays the full deliberation cycle in fullscreen.

## When to use

- PR or diff review
- Refactor planning touching 2+ files
- Choosing between several implementation approaches
- Before committing to shared / core code
- Risk assessment for non-trivial changes

## Modes

| Mode | Sub-agents | When |
|---|---|---|
| **Parallel** (default) | 3 voices dispatched in parallel | Most PR reviews. Eliminates cross-contamination. |
| **Dialectic** | 3 voices × 2 rounds — each round sees the others' outputs | Multi-file refactors, when positions need to evolve. |
| **Sequential — Blind** | 3 voices in sequence, with stripped context between them | High-risk decisions where anchoring on the previous voice is a concern. |
| **Trias** | 9 sub-agents (3 personalities × 3 voices), majority vote | High-stakes (migrations, security, large refactors) — see `architecture.html` Patterns tab for the full deep-dive. |

## Install (live skill — private)

The live skill is installed at `~/.claude/skills/consilium/` (via symlink or junction). The source repository is private; access is by request.

Once installed, the skill auto-activates in a Claude Code session when keywords like `review PR`, `evaluate change`, `refactor planning`, or `risk assessment` appear in the prompt.

## Layout (live skill)

```
consilium/
├── SKILL.md             # YAML frontmatter + workflow
├── README.md
├── FEEDBACK.html        # manual outcome log (kept / rejected / partial / pending)
├── .gitignore
├── scripts/
│   ├── aggregator.py    # voting schemes (incl. conservative_override, team_vote)
│   ├── confidence.py    # variance + separation -> confidence score
│   ├── scope_gate.py    # auto-skip for trivial changes (Step 1.5)
│   ├── strip_context.py # sequential-blind context stripper
│   ├── dialectic_merge.py
│   ├── personalities.py # Trias mode — 3 personalities with G/C/K weights
│   ├── priors.py        # loads priors from FEEDBACK.html + runs/
│   └── feedback.py      # stats over FEEDBACK.html + runs/
├── prompts/
│   ├── generator.md     # creative voice prompt
│   ├── control.md       # analytical voice prompt
│   └── conservator.md   # skeptical voice prompt
├── agents/
│   └── consilium-subagent.md  # one-shot sub-agent wrapper for isolated dispatch
├── runs/                # one JSON per deliberation (gitignored)
└── examples/
    └── pr_review_example.md
```

## Usage

The skill auto-activates when keywords like `review PR`, `evaluate change`, `refactor planning`, or `risk assessment` appear in a Claude Code prompt.

Output: a canonical JSON in `runs/YYYY-MM-DD_HHMM_<label>.json` with `chosen_approach`, `alternatives`, `voice_scores`, `confidence`, `deliberation_log`, plus a one-line console summary.

For the feedback loop and post-deliberation calibration, see the **Feedback loop** section in `SKILL.md`.

## Visual architecture

Open [`architecture.html`](./architecture.html) in a browser. Four tabs: **Architecture / Flow / Modes / Patterns**. The Patterns tab includes a click-through of every flow (PR review, Refactor planning, Risk assessment, Veto trigger, Multi-file refactor, Trias deliberation) with the Voices bias profile, Trias team weights, the 9-sub-agent deep-dive, and the calibration loop.
