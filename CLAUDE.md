# Contributing to Consilium

This repo is the source of the `consilium` skill. To **use** it, invoke `/consilium` in a Claude Code session. This file covers only **editing** the skill.

## Contract

`SKILL.md` is the public contract. Read it before any change — the Constitution (4 principles) and the 8-step workflow govern the skill, not just its users.

For behavioral guidelines (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution, Question Everything), see the global `~/.claude/CLAUDE.md` — they apply here too.

## Commands

Stdlib-only, no test runner. Smoke tests run manually via CLI:

- `python scripts/test_rund2.py` — sequential architecture (skeptic_on_chosen, MODE enum, validate_report extras)
- `python scripts/test_feedback_html.py` — `render_feedback_html` + parser round-trip
- `python scripts/run_evals.py` — regression scenarios from `evals/scenarios.json` (subprocess-based, deterministic; non-zero exit on first FAIL)
- `python scripts/validate_report.py < runs/<file>.json` — Constitution Principle #4 gate; minimum required before any commit touching `prompts/voices/` or `aggregator.py`

Type-check: `pyright` (config: `pyrightconfig.json`, `typeCheckingMode: basic`, Python 3.11, `scripts/` in `extraPaths`).

## Pipeline

Canonical flow of a deliberation:

1. Voices read `prompts/voices/<name>.md`, emit JSON per Constitution
2. `scripts/aggregator.py` merges voice outputs → canonical report
3. `scripts/confidence.py` computes the score; `scripts/priors.py` applies priors
4. `scripts/validate_report.py` is the final gate before writing to `runs/<ts>_<slug>.json`

Mode-specific scripts:
- `dialectic_merge.py` — two-pass merge for Dialectic
- `personalities.py` — Trias lens injection (Pioneer/Architect/Steward)

Sub-agent dispatch (Trias, Skeptic): see `agents/consilium-subagent.md`. All sub-agents use `model: "sonnet"` explicitly — do not inherit Opus.

Architecture visualization: `docs/architecture.html` (open locally). Benchmarks on real problems: `experiments/` (see `experiments/p3-car-wash.html`).

## Python conventions

- **Stdlib-only.** No script introduces external dependencies. If it seems necessary, it likely means the feature exceeds the skill's scope.
- **Small, stand-alone scripts.** Each `scripts/*.py` has a CLI docstring, `argparse`, JSON I/O. Reuse between scripts goes through `importlib.util` (see `priors.py`), not packaging.
- **No tests dir.** Manual smoke-test via CLI; see `python scripts/validate_report.py < runs/<latest>.json` as the minimum.

## Authoritative areas (touch carefully)

- **`prompts/voices/*.md`** — read by each voice at runtime. A change here affects all future deliberations → high `regression_risk` in Conservator. Prefer injecting extra context into the voice's input rather than into the prompt.
  - Core voices: `generator.md`, `control.md`, `conservator.md` — run in any mode
  - Pass-2: `generator_pass2.md`, `control_pass2.md`, `conservator_pass2.md` — used only by Dialectic
  - `skeptic.md` — focal challenger, run in `parallel_skeptic`, `dialectic_skeptic`, `skeptic_on_chosen`
  - `<personality>_lens.md` (Pioneer/Architect/Steward) — prepended over core voices in `trias` and `trias_split`
- **`SKILL.md` Constitution + workflow** — changing steps 0–7 breaks the JSON format expected by `aggregator.py` and `validate_report.py`. Modify both at the same time.

## Available modes

User-selectable modes (SKILL.md documents them in detail):

- **Sequential** (default) — Conservator → Generator → Control single-context.
- **Dialectic** — two-pass with cross-review in Pass-2 (`scripts/dialectic_merge.py`).
- **Trias** — 3 personalities × 3 voices, democratic vote over the 3 chosen results (9 sub-agents).
- **`trias_split`** — Trias with Sonnet Generator + Haiku verifiers (~3.3× Parallel). Shallow-amplifier on problems with implicit constraints — see `experiments/p3-car-wash.html`.
- **`skeptic_on_chosen`** — composable flag over any base mode (+1 sub-agent overhead). Advisory by default; opt-in override via `--skeptic-can-override`. Auto-triggers when `confidence ∈ [0.5, 0.7]`. Replaces the fixed modes `parallel_skeptic` (= `parallel + skeptic_on_chosen`) and `dialectic_skeptic` (= `dialectic + skeptic_on_chosen`) — collapsed on 2026-05-17, legacy names remain in `validate_report.py` MODE enum for backward-compat.

**Parallel removed.** No longer user-selectable (only via `parallel + skeptic_on_chosen`). Remains as an internal auto cross-check when `magnitude=critical ∧ reversibility=irreversible`, plus a silent audit every 20 runs.

## Local files (gitignored)

- `FEEDBACK.html` — real-usage journal, append-only via `scripts/log_feedback.py` (atomic writes). See `scripts/deprecated/migrate_feedback_md_to_html.py` for the migration history from `.md` format (retired one-shot tool).
- `runs/*.json` — output of each deliberation (only `runs/README.md` is tracked).
- `docs/superpowers/plans/`, `docs/superpowers/specs/` — artifacts from `superpowers:writing-plans` / `executing-plans` (one file per non-trivial feature, naming `YYYY-MM-DD-<slug>.md`).

## Self-improvement loop

When editing the skill itself: run `/consilium` on your own change. For changes to core prompts / architecture, consider `trias` over single-context deliberation. Save the run to `runs/` and log it to `FEEDBACK.html` via `log_feedback.py`.

## Git workflow

Rules for any non-trivial change made by Claude in this repo:

1. **New branch from `main`** before editing. Naming: `feat/<slug>` for features / new capabilities, `fix/<slug>` for bugfixes. Slug in kebab-case, descriptive (e.g. `feat/parallel-voices`, `fix/aggregator-null-confidence`). Only these two prefixes.
2. **One commit per branch** — first `git commit`, then `git commit --amend --no-edit` (or with a new message if scope changed) for each subsequent change in the same session. The branch always stays at 1 commit.
3. **Auto-push after commit** — without asking. If the user requests changes before the push — amend + push immediately.
4. **Push once**, then `git checkout main` automatically. After pushing, no amend + force-push without an explicit request — new changes = new branch.
5. **The user creates the PR manually.** Do not run `gh pr create`. At the end, just report the pushed branch.
6. **Exception: typos / 1-line fixes** can go directly to `main` if the user explicitly requests it. Everything else follows the workflow above.
7. **Commit messages** stay in Conventional Commits format (`feat(scope): ...`, `fix(scope): ...`), aligned with the branch prefix.
