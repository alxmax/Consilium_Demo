# Consilium

**A second opinion, structured.** Consilium is a [Claude Code](https://docs.claude.com/en/docs/claude-code) skill that evaluates a risky code change through three independent voices that don't trust each other — a creative, an analyst, and a skeptic — then aggregates their verdicts under a veto cascade into one canonical decision, with the disagreement preserved on disk.

One LLM reviewing its own proposal has predictable blind spots: it generates an idea and validates it from the same perspective. Consilium splits that into separate roles with disjoint mandates so a change is cross-examined before it ships.

The three core voices:

- **Conservator** (prudent) — scores risk and reversibility; runs *first* and sets the effort budget for the others
- **Generator** (creative) — proposes alternatives, including `do_nothing`
- **Control** (analytical) — verifies correctness and writes acceptance tests

## What's interesting here

- **Adversarial-by-design deliberation** — roles with conflicting incentives, not one model agreeing with itself.
- **An 8-component veto cascade** (`scripts/aggregator.py`) that turns three voice outputs into one decision with 7 distinct routing outcomes (block / rework / adapt / escalate / aggregate).
- **A self-calibrating feedback loop** — every run lands as canonical JSON in `runs/`, outcomes are logged to `FEEDBACK.html`, and the next deliberation reads those priors. Confidence below a per-mode floor is flagged.
- **Cost-aware modes** — from a 1× single-context pass up to a 3× three-personality vote (Trias), with a scope gate that auto-skips trivial diffs.
- **Measured, not asserted** — a benchmark harness (`benchmark/`) compares each mode against bare-model baselines on real coding/reasoning tasks with a hidden oracle.
- **Stdlib-only Python** — no external dependencies; each script is a small, standalone CLI with JSON I/O.

## Architecture explainer

An interactive, single-page walkthrough of the voices, pipeline, modes, voting, and the calibration loop lives at **`docs/architecture.html`** (open it in a browser). It's authored as editable React source in `docs/architecture/` — see that folder's README to preview or rebuild it.

## When to use

- PR review or diff
- Refactor planning across 2+ files
- Choosing between multiple implementation approaches
- Before committing to shared/core code
- Risk assessment for a non-trivial change

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

Then, in a new Claude Code session: `Review the last commit using the consilium skill`.

## Structure

```
consilium/
├── SKILL.md         # the contract: Constitution (4 principles) + 8-step workflow
├── prompts/voices/  # per-voice role prompts (generator, control, conservator, skeptic, lenses)
├── modes/           # per-mode workflow + machine-readable config (cost, sub-agents, floors)
├── scripts/         # stdlib-only CLIs: aggregator, confidence, priors, scope_gate, …
├── agents/          # consilium-subagent — isolated dispatch via the Agent tool
├── benchmark/       # mode-vs-baseline benchmark harness (oracle kept in an external sibling repo)
├── docs/            # architecture.html explainer + its React source under docs/architecture/
├── evals/           # deterministic regression scenarios for the scripts
└── runs/            # one JSON report per deliberation (gitignored)
```

## Modes

| Mode | Cost | What it adds |
|------|------|--------------|
| **Sequential** (default) | 1× | Conservator → Generator → Control in one context |
| **Dialectic** | 1.33× | Sequential + a Skeptic sub-agent on the chosen answer, with code-context injection |
| **Trias** | 3× | 3 personalities (Pioneer / Architect / Steward), each running its own Sequential pass as a sub-agent, then a majority vote |
| **`skeptic_on_chosen`** | base +1 | Composable flag over any mode — a focal Skeptic challenges the chosen answer. Auto-triggers when `confidence ∈ [0.5, 0.7]` |

Parallel dispatch is no longer user-selectable; it remains an automatic cross-check when a change is both `critical` and `irreversible`. All dispatched voices run on Sonnet; the orchestrator runs on Opus.

**Canonical output** (validated by `scripts/validate_report.py`): JSON with `success_criterion`, `chosen_approach`, `verification`, `alternatives`, `voice_scores`, `confidence`, and a `deliberation_log`.

## License

[Business Source License 1.1](LICENSE) © 2026 Schipor Alexandru.

Free for non-commercial use (evaluation, education, research, personal). Commercial use within a revenue-generating organization requires a commercial license — contact the Licensor. Converts automatically to Apache 2.0 on **2030-05-16**.
