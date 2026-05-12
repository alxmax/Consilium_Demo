# Progress Voices — Design (F2 + F3, drop F1)

**Date:** 2026-05-12
**Topic:** Reduce stagnation bias and minimum-effort bias in Consilium voice prompts.
**Source deliberations:** `runs/2026-05-12_1820_progress-voices-selfreview.json`, `runs/2026-05-12_1900_progress-voices-keep2.json`.

## Problem

Three live deliberations in this session produced **razor-thin separation** between `do_nothing` and the runner-up productive option:

| Run | Chosen | Runner-up | Separation | Confidence |
|---|---|---|---|---|
| `1640_public-readiness` | `do_nothing` | `split_three_prs_with_aliasing` | 0.16 (utility) | 0.42 |
| `1700_audit-last3` | `minimal_hygiene` | `do_nothing` | 0.027 | 0.53 |
| `1820_progress-voices-selfreview` | `do_nothing` | `unconventional_eval_first` | 0.024 | 0.37 |
| `1900_progress-voices-keep2` (this) | `do_nothing` | `drop_f1_keep_f2_f3` | 0.007 | 0.43 |

Two mechanically distinct failure modes:

- **A. Stagnation bias** — `do_nothing` wins on action-shaped goals because Control marks it `valid: true` with empty issues, and Conservator scores zero diff = zero risk. The math has no signal for "this candidate fails the user's stated goal."
- **B. Minimum-effort bias** — among productive options, the smallest diff wins because Conservator's `regression_risk` scales linearly with size while quality-of-progress (tests, rollback path, feature flag) is invisible to the scorer.

Both failure modes have the same root: **no voice quantifies progress toward `success_criterion`**. Generator answers "is this interesting", Control answers "is this correct", Conservator answers "is this safe". None answer "does this solve the problem the user asked us to solve."

## Decision

Edit three prompts (`prompts/control.md`, `prompts/conservator.md`, `prompts/generator.md`) with ~18 lines of additions, no schema changes. Drop the originally-proposed F1 (Generator `unconventional_*` mandate) as speculative and not replay-faithful. Keep:

- **F2 — Conservator `quality_signals` reducer**: addresses minimum-effort bias by rewarding sketches that explicitly demonstrate discipline (tests, rollback, feature flag).
- **F3 — Control goal-fit gate + Generator goal-fit articulation**: addresses stagnation bias by making "fails to address `success_criterion`" a first-class `valid: false` reason.

Math acts via existing channels: `valid: false → control_score = 0` and adjusted `regression_risk → adjusted safety`. No aggregator, scorer, validator, or eval-scenarios changes.

## Architecture

### `prompts/control.md` — add Task step 5

```text
5. **Goal-fit check.** If a candidate (including `do_nothing`) does not
   meaningfully address `success_criterion`, mark `valid: false` with
   `category: "logic"` and `detail` quoting `success_criterion` verbatim.
   Exception: `do_nothing` remains `valid: true` ONLY when the goal is
   verification-only AND verification revealed no action needed.
   Fallback: if ALL candidates fail goal-fit, emit a final verdict with
   `id: "_no_viable_candidate"` and `valid: true` so the aggregator has
   defined input rather than empty.
```

### `prompts/conservator.md` — add subsection after the 4 factors

```text
**Quality-progress adjustment on `regression_risk`.**
If the candidate's `sketch` explicitly includes
  (a) test names that catch the regression class introduced, OR
  (b) a concrete rollback recipe shorter than 3 steps, OR
  (c) a feature flag / config gate,
reduce `regression_risk` by 0.15 (floored at 0.0). Document the reduction
in `notes` (e.g., "regression_risk reduced 0.15 due to explicit test
coverage in sketch"). Disciplined progress is qualitatively safer than
naked diff of equal size.
```

### `prompts/generator.md` — add to Constraints

```text
**Goal-fit articulation in rationale.** For each candidate, `rationale`
must include a one-clause answer to: "How does this advance
`success_criterion`?" For `do_nothing`, explicitly articulate what part
of the goal goes unaddressed — or, rarely, why inaction satisfies the
goal (e.g., verification target already correct).
```

## Data Flow

No JSON schema changes. Voice outputs retain identical keys. Behavioral deltas:

- Control verdicts: more `valid: false` entries on action-shaped goals; new `_no_viable_candidate` sentinel only on degenerate input.
- Conservator scores: numeric drop of 0.15 in `regression_risk` for sketches with quality signals; `notes` field is mandatory when reduction applies.
- Generator candidates: `rationale` slightly longer; required goal-fit clause is prose, not a new field.

`evals/scenarios.json` is untouched — its 17+ scenarios test deterministic aggregator/confidence/validator math, not prompt content.

## Validation Plan

### Replay (mental walk-through under new rules)

**`1640_public-readiness`** (action-shaped goal):
- Control: `do_nothing` → `valid: false` (goal cere acțiune; verification not the goal). `_no_viable_candidate` NOT triggered (4 productive candidates remain).
- Conservator: `split_three_prs_with_aliasing` had explicit per-PR rollback recipe → `regression_risk: 0.34 → 0.19`. `single_branch_bundle` had `git revert <sha>` recipe → `0.58 → 0.43`.
- Aggregator: `split_three_prs_with_aliasing` becomes top with materially better separation.

**`1700_audit-last3`** (action-shaped goal):
- Control: `do_nothing` → `valid: false`.
- Conservator: `scoped_correctness_patches` had 4 explicit `tests_to_write` → `regression_risk: 0.34 → 0.19`. `minimal_hygiene` had 3 tests but also tighter sketch — same reduction → `0.12 → 0.0` (floored).
- Aggregator: `scoped_correctness_patches` climbs because Control now scores `do_nothing` at 0; F2 differentiates among productive candidates by progress quality. Expected pick: `scoped_correctness_patches` (broader goal coverage) over `minimal_hygiene` (narrower).

### Eval suite

`python scripts/run_evals.py` → exit 0. The 17+ scenarios test math, not prompts — should remain green.

### Smoke test (post-implementation)

Run `/consilium` on the very branch implementing this design (self-improvement loop per CLAUDE.md). Expect:
- chosen != `do_nothing` on this action-shaped goal (implement F2+F3)
- confidence ≥ 0.7 OR principled override path with low score-gap

## Rollback Recipe

1. `git revert <commit-sha>` on the branch — single-commit-per-branch makes this atomic per CLAUDE.md.
2. Restore `prompts/conservator.md` and `prompts/control.md` from main; restore `prompts/generator.md` if goal-fit clause was added there.
3. If SKILL.md workflow text references new gate semantics, restore those too.
4. `python scripts/run_evals.py` to confirm green.
5. Run `/consilium` on `runs/2026-05-12_1640_public-readiness.json` input and `runs/2026-05-12_1700_audit-last3.json` input to confirm `chosen_approach` reverts to prior values.
6. Add `FEEDBACK.md` line `BAD | progress-voices-keep2 | drop_f1_keep_f2_f3 | reverted | <reason>` for `priors.py` signal in subsequent deliberations.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| **Overfitting on n=2** (3 sessions agreed razor-thin is the pattern, but evidence base is 2 explicit + 2 derived runs out of 12 archived) | Track `FEEDBACK.md` outcomes on next 5-10 runs post-implementation. If `override_rate` doesn't drop materially relative to baseline, revert per recipe above. |
| **F3 gate too aggressive** (rejects legitimate `do_nothing` on misjudged action-shape) | Documented exception for verification-only goals. SKILL.md Step 6 confidence-gate prompts user for override when below 0.7 — preserves manual escape hatch. |
| **F2 ratchet game** (Generator name-drops tests/rollback to game the reducer) | Conservator's `notes` must cite which of (a)/(b)/(c) triggered the reduction. `priors.py` keyword scan can catch repeated game pattern across runs. |
| **Authoritative-zone touch** (CLAUDE.md regression_risk warning on `prompts/*.md`) | Single branch + single amended commit per CLAUDE.md. Smoke test = `/consilium` on the change itself. F1 dropped specifically to reduce blast radius. |
| **F3 fallback path under-tested** (`_no_viable_candidate` only triggers on degenerate input — never seen in 12 historical runs) | Aggregator already handles `chosen: null` (all-vetoed case) gracefully. `_no_viable_candidate` is just a typed signal of that state; no aggregator change required. |

## Out of Scope

- **F1 (`unconventional_*` mandate)** — dropped per `runs/2026-05-12_1900` deliberation. Speculative effect; replay-unfaithful (historical Generator outputs didn't include unconventional candidates, so we can't post-hoc test the impact). Revisit if F2+F3 don't move the needle empirically on 5-10 future runs.
- **`replay_bias.py` harness** — Control flagged it unfaithful for F1 (cannot manufacture historical candidates that didn't exist). F2 + F3 are replay-testable via mental walk-through of saved runs, which is what this spec uses for validation.
- **SKILL.md workflow text changes** — keep current step ordering and Constitution wording. New gate fits inside existing Step 3 (Control) and Step 4 (Conservator) sub-tasks; mention of the gate in workflow body is optional polish.

## Open Decisions

None. The design is closed:
- F3 fallback: `_no_viable_candidate` sentinel.
- F2 reduction magnitude: 0.15 (one-shot, no calibration knob).
- F2 documentation requirement: notes must cite which signal triggered the reduction.

## Implementation Plan Hand-off

Per brainstorming flow, next step is `superpowers:writing-plans` to produce an implementation plan covering:

- Branch creation (`feat/progress-voices-keep2`)
- The three prompt edits (~18 lines)
- Self-improvement `/consilium` run as smoke test (recorded in `runs/`)
- `FEEDBACK.md` outcome logging post-smoke-test
- User-driven PR (no `gh pr create` per repo convention)

This spec contains architecture and rationale only — not the implementation plan itself.
