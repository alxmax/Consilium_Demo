# Consilium

Multi-perspective deliberation pattern for evaluating code changes. A skill for Claude Code (identifier: `consilium`) that uses three independent voices:

- **Generator** (creative) — proposes alternatives
- **Control** (analytical) — verifies correctness
- **Conservator** (prudent) — evaluates risk

## When to use

- PR review or diff
- Refactor planning across 2+ files
- Decision between multiple implementation approaches
- Before committing to shared/core code
- Risk evaluation for non-trivial changes

## Install

### Linux / macOS

```bash
git clone https://github.com/alxmax/Consilium.git ~/dev/consilium
mkdir -p ~/.claude/skills
ln -s ~/dev/consilium ~/.claude/skills/consilium
```

### Windows (PowerShell)

Junction (recommended — no admin required):

```powershell
git clone https://github.com/alxmax/Consilium.git $HOME\dev\consilium
New-Item -ItemType Directory -Force -Path $HOME\.claude\skills
New-Item -ItemType Junction -Path $HOME\.claude\skills\consilium -Target $HOME\dev\consilium
```

Or symlink (PowerShell as Administrator):

```powershell
New-Item -ItemType SymbolicLink -Path $HOME\.claude\skills\consilium -Target $HOME\dev\consilium
```

## Verify installation

```bash
ls -la ~/.claude/skills/consilium/SKILL.md
```

Then in Claude Code (new session): `Review the last commit using the consilium skill`.

## Structure

```
consilium/
├── SKILL.md                 # contract: Constitution + 8-step workflow
├── README.md
├── FEEDBACK.html            # real-usage journal (gitignored)
├── prompts/
│   ├── voices/              # generator, control, conservator, skeptic,
│   │                        #   *_pass2, pioneer/architect/steward_lens,
│   │                        #   frontend_domain_lens
│   └── senators/            # wittgenstein, aurelius, confucius, socrate,
│                            #   musk, dimon, napoleon (Senate mode)
├── scripts/                 # ~30 stdlib-only scripts (aggregator, confidence,
│                            #   priors, scope_gate, dialectic_merge,
│                            #   senate_synth, log_feedback, …)
├── agents/
│   └── consilium-subagent.md  # isolated dispatch via Agent tool
├── runs/                    # one JSON per deliberation (gitignored)
│   └── senate/              # Senate bundles
├── docs/senate/             # architecture.html (round + deadlock visualizations)
├── experiments/             # benchmarks on real problems
└── evals/                   # regression scenarios for scripts
```

## Usage

The skill activates automatically when keywords such as "review PR", "evaluate change", "refactor planning", "risk assessment", "should I commit", "which approach" appear in the prompt.

**Available modes** (see SKILL.md for per-mode workflow):

- **Sequential** (default) — Conservator → Generator → Control single-context
- **Dialectic** — two-pass; Pass-2 sees outputs from the other voices
- **Trias** — 3 personalities × 3 voices (Pioneer/Architect/Steward); 9 sub-agents
- **`trias_split`** — Trias with Sonnet Generator + Haiku verifiers
- **`skeptic_on_chosen`** — composable flag over any mode (+1 sub-agent overhead). Replaces the fixed modes `parallel_skeptic` / `dialectic_skeptic` (collapsed 2026-05-17; legacy names remain in `validate_report.py` MODE enum for backward-compat)
- **Senate** — audit of skill changes themselves (9 senators, on-demand)

Parallel as a selectable option was removed in RUND2; it remains as an automatic cross-check when `magnitude=critical ∧ reversibility=irreversible`.

**Canonical output** (validated by `scripts/validate_report.py`): JSON with `success_criterion`, `chosen_approach`, `verification`, `alternatives`, `voice_scores`, `confidence`, `deliberation_log`.

For the feedback loop and calibration after real use, see the **Feedback loop** section in `SKILL.md`.

## License

[Business Source License 1.1](LICENSE) © 2026 Schipor Alexandru.

Free for non-commercial use (evaluation, education, research, personal use). Commercial use within an organization that generates revenue from products or services incorporating the Licensed Work requires a commercial license — contact the Licensor. License converts automatically to Apache 2.0 on **2030-05-16**.
