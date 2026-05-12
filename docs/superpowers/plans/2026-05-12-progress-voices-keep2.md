# Progress Voices (F2 + F3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate stagnation bias and minimum-effort bias in Consilium voice prompts via two narrow edits — Conservator gets a quality-signals reducer on `regression_risk`; Control gets a goal-fit gate that invalidates `do_nothing` on action-shaped goals. Drop the originally-proposed F1 (Generator `unconventional_*` mandate) as speculative.

**Architecture:** Three prompt files edited (~18 lines total), zero schema changes, zero script changes, zero `evals/scenarios.json` changes. The math acts via existing channels: `valid: false` → `control_score = 0`; reduced `regression_risk` → adjusted `safety`. One git branch (`feat/progress-voices-keep2`), one amended commit per CLAUDE.md workflow. Validation is operational, not unit-test-based — CLAUDE.md mandates no tests dir; smoke testing is via CLI (`run_evals.py` and a self-improvement `/consilium` run on the change itself).

**Tech Stack:** Markdown (prompt files). Python stdlib (existing scripts, untouched). Git CLI.

**Spec:** `docs/superpowers/specs/2026-05-12-progress-voices-design.md`

**Note on worktree:** CLAUDE.md's git workflow specifies `feat/<slug>` branch + single amended commit; no worktree was created during brainstorming. Plan proceeds with a regular branch off `main`.

---

## File Structure

| File | Action | Purpose |
|---|---|---|
| `prompts/control.md` | Modify (lines ~28-30) | Replace the `do_nothing` blanket-valid line with the new goal-fit gate (step 5 of Task) |
| `prompts/conservator.md` | Modify (insert after line 32) | Add quality-progress reducer subsection between the 4 factors and the aggregation rule |
| `prompts/generator.md` | Modify (insert after line 39) | Append goal-fit articulation bullet to Constraints |
| `runs/<ts>_progress-voices-smoke.json` | Create | Self-improvement `/consilium` run on the branch (persisted automatically by skill workflow) |
| `FEEDBACK.md` | Append one line | Outcome log from the smoke-test run |

---

### Task 1: Pre-flight verification

**Files:** none (repo state check only)

- [ ] **Step 1: Confirm clean working tree and on `main`**

Run: `git status && git branch --show-current`
Expected: working tree clean, branch shows `main`.

- [ ] **Step 2: Confirm eval suite is green at baseline**

Run: `python scripts/run_evals.py`
Expected: exit 0, summary line showing all scenarios pass.

- [ ] **Step 3: Read the spec one more time for context**

Run: `cat docs/superpowers/specs/2026-05-12-progress-voices-design.md | head -80`
Expected: spec content streams; no edit yet.

---

### Task 2: Create the feature branch

**Files:** none (branch only)

- [ ] **Step 1: Create branch from main**

Run: `git checkout -b feat/progress-voices-keep2`
Expected: `Switched to a new branch 'feat/progress-voices-keep2'`.

- [ ] **Step 2: Verify branch is at main's tip**

Run: `git log --oneline -1`
Expected: same SHA as `main` (no commits yet on the new branch).

---

### Task 3: Edit `prompts/generator.md` — append goal-fit articulation bullet

**Files:**
- Modify: `prompts/generator.md` (Constraints section, after the existing "Don't pre-filter" bullet at line 39)

- [ ] **Step 1: Apply the edit**

Use the Edit tool with:

`old_string`:
```
- Don't pre-filter for "feasibility" or "risk". The next two voices will handle that.
```

`new_string`:
```
- Don't pre-filter for "feasibility" or "risk". The next two voices will handle that.
- **Goal-fit articulation in rationale.** For each candidate, `rationale` must include a one-clause answer to: *"How does this advance `success_criterion`?"* For `do_nothing`, explicitly articulate what part of the goal goes unaddressed — or, rarely, why inaction satisfies the goal (e.g., verification target already correct).
```

- [ ] **Step 2: Verify the bullet appears in Constraints**

Run: `grep -n "Goal-fit articulation" prompts/generator.md`
Expected: one match showing the new bullet.

- [ ] **Step 3: Verify no other content shifted**

Run: `git diff --stat prompts/generator.md`
Expected: 1 file changed, 1 insertion(+), 0 deletions(-).

---

### Task 4: Edit `prompts/conservator.md` — insert quality-progress reducer

**Files:**
- Modify: `prompts/conservator.md` (insert new subsection between the 4 factors and the aggregation rule at line 34)

- [ ] **Step 1: Apply the edit**

Use the Edit tool with:

`old_string`:
```
Aggregate the factors into a single `risk_score`. Default weighting: average all four equally, **unless** `reversibility > 0.7` — in that case, irreversibility dominates and the final score should not fall below `reversibility`.
```

`new_string`:
```
**Quality-progress adjustment on `regression_risk`.** If the candidate's `sketch` explicitly includes (a) test names that catch the regression class introduced, OR (b) a concrete rollback recipe shorter than 3 steps, OR (c) a feature flag / config gate, reduce `regression_risk` by 0.15 (floored at 0.0). Document the reduction in `notes` (e.g., *"regression_risk reduced 0.15 due to explicit test coverage in sketch"*). Disciplined progress is qualitatively safer than naked diff of equal size.

Aggregate the factors into a single `risk_score`. Default weighting: average all four equally, **unless** `reversibility > 0.7` — in that case, irreversibility dominates and the final score should not fall below `reversibility`.
```

- [ ] **Step 2: Verify subsection appears in correct location**

Run: `grep -n -A1 "Quality-progress adjustment" prompts/conservator.md`
Expected: match around line 34, followed shortly by the existing "Aggregate the factors" line.

- [ ] **Step 3: Verify no other content shifted**

Run: `git diff --stat prompts/conservator.md`
Expected: 1 file changed, ~2 insertions(+), 0 deletions(-) (one for the new paragraph + one blank-line separator).

---

### Task 5: Edit `prompts/control.md` — replace `do_nothing` line with goal-fit gate

**Files:**
- Modify: `prompts/control.md` (replace line 28; this REPLACES the blanket "always valid" rule for `do_nothing` with the conditional gate)

- [ ] **Step 1: Apply the edit**

Use the Edit tool with:

`old_string`:
```
If a candidate is the `do_nothing` baseline, mark it `valid: true` with a note explaining what the codebase loses by not acting.
```

`new_string`:
```
5. **Goal-fit check.** If a candidate (including `do_nothing`) does not meaningfully address `success_criterion`, mark `valid: false` with `category: "logic"` and `detail` quoting `success_criterion` verbatim. Exception: `do_nothing` remains `valid: true` ONLY when the goal is verification-only AND verification revealed no action needed. Fallback: if ALL candidates fail goal-fit, emit a final verdict with `id: "_no_viable_candidate"` and `valid: true` so the aggregator has defined input.
```

- [ ] **Step 2: Verify the gate appears as step 5 in Task**

Run: `grep -n -B2 "Goal-fit check" prompts/control.md`
Expected: match showing `5. **Goal-fit check.**` immediately after the four numbered factors.

- [ ] **Step 3: Verify the old `do_nothing` line is gone**

Run: `grep -c "If a candidate is the \`do_nothing\` baseline" prompts/control.md`
Expected: `0` (line replaced).

- [ ] **Step 4: Verify no other content shifted**

Run: `git diff --stat prompts/control.md`
Expected: 1 file changed, 1 insertion(+), 1 deletion(-).

---

### Task 6: Regression-guard via eval suite

**Files:** none (read-only verification)

- [ ] **Step 1: Run the eval scenarios**

Run: `python scripts/run_evals.py`
Expected: exit 0. Same summary as Task 1 Step 2. Prompts are not in eval scope; this just guards against accidental script-level changes.

- [ ] **Step 2: If non-zero exit, STOP and investigate**

If `run_evals.py` failed, the most likely cause is unrelated drift in `scripts/*.py` since Task 1's baseline. Run `git diff scripts/` — if non-empty, that's the culprit, not our prompt edits. Do not commit until evals are green.

---

### Task 7: Single amended commit per CLAUDE.md workflow

**Files:** none (commits the three prompt edits as one atomic commit)

- [ ] **Step 1: Stage the three modified files**

Run: `git add prompts/generator.md prompts/conservator.md prompts/control.md`
Expected: no error. `git status` shows three files staged, no others.

- [ ] **Step 2: Verify staged diff matches the spec**

Run: `git diff --staged --stat`
Expected: 3 files changed, ~5 insertions(+), 1 deletion(-).

- [ ] **Step 3: Commit with Conventional Commits message**

Run:
```bash
git commit -m "feat(prompts): add goal-fit gate and quality-progress reducer

- Control: goal-fit check (step 5) marks do_nothing valid:false on
  action-shaped goals; falls back to _no_viable_candidate verdict
  when ALL candidates fail goal-fit
- Conservator: quality_signals reducer subtracts 0.15 from regression_risk
  when sketch contains tests / rollback <=3 steps / feature flag
- Generator: rationale must articulate goal-fit per candidate

Addresses stagnation bias (do_nothing winning on action-shaped goals)
and minimum-effort bias (cheapest productive winning over goal-fitting
alternative), observed across runs/2026-05-12_{1640,1700,1820,1900}.

Spec: docs/superpowers/specs/2026-05-12-progress-voices-design.md"
```
Expected: commit created on `feat/progress-voices-keep2`.

- [ ] **Step 4: Verify single-commit-per-branch invariant**

Run: `git log --oneline main..HEAD`
Expected: exactly one commit shown.

---

### Task 8: Self-improvement smoke test — `/consilium` parallel run on this change

**Files:**
- Create: `runs/<YYYY-MM-DD>_<HHMM>_progress-voices-smoke.json` (path determined at run time by skill workflow)

- [ ] **Step 1: Inside this Claude Code session, invoke `/consilium` on the change**

The orchestrator (the agent executing this plan) runs the full Consilium workflow per `SKILL.md`:
- Bootstrap Step 0 (priors + voice prompts)
- Step 1: state success_criterion as: *"The three prompt edits in commit `<sha>` on `feat/progress-voices-keep2` correctly implement F2+F3 from the design spec, with no regression to the eval suite. After the change, /consilium on action-shaped goals does not auto-favor do_nothing."*
- Step 1.5: skip (non-diff design; gate is no-op here, but you may run it for free signal)
- Step 2-5b: dispatch Generator → Control + Conservator in parallel mode (3 sub-agents over 2 turns)
- Step 6: persist `runs/<ts>_progress-voices-smoke.json`, validate with `validate_report.py`

Expected outcomes:
- `validate_report.py` exits 0
- Run is persisted in `runs/`
- The run itself becomes evidence of the new prompts firing (if F3 gate triggers on a candidate like `do_nothing` of the smoke deliberation, that's the post-condition we want).

- [ ] **Step 2: Verify run file shape**

Run: `cat runs/<latest>.json | python scripts/validate_report.py && echo OK`
Expected: `OK` (exit 0).

- [ ] **Step 3: Log feedback per confidence-gated workflow**

Per `SKILL.md` Step 6 final actions:
- If `confidence >= 0.7` → `cat runs/<latest>.json | python scripts/log_feedback.py --outcome OK`
- If `confidence < 0.7` → ask user for override; log per their answer (OK/OVR/PEND)
- If `confidence is null` → `python scripts/log_feedback.py` (default PEND)

Expected: one new line appended to `FEEDBACK.md` describing the smoke run.

---

### Task 9: Hand-off to user

**Files:** none

- [ ] **Step 1: Summarize what was committed**

Report to user:
- Branch: `feat/progress-voices-keep2`
- Commit SHA (run: `git log -1 --format=%H`)
- Files changed: `prompts/{control,conservator,generator}.md`
- Eval suite: green at baseline + post-change
- Smoke run path: `runs/<ts>_progress-voices-smoke.json`
- Smoke confidence + chosen: extract from the run

- [ ] **Step 2: Ask explicit "ok or more changes?" per CLAUDE.md workflow rule 3**

Per the project's git workflow, before push the engineer asks: *"totul ok sau mai vrei schimbări?"*

- If user says **OK** → push: `git push -u origin feat/progress-voices-keep2`, then `git checkout main`. Do NOT run `gh pr create` — user opens PR manually per CLAUDE.md rule 5.
- If user says **changes** → amend with `git commit --amend --no-edit` (or new message if scope shifted) after the edits; re-run Tasks 6 and 8 (regression + smoke); ask again.

- [ ] **Step 3: Report branch ready**

After push, message user with branch URL (or just branch name if no remote URL available) so they can open the PR in their browser.

---

## Self-Review Notes

| Check | Outcome |
|---|---|
| Spec coverage | F2 (Task 4), F3 control gate (Task 5), F3 articulation (Task 3), eval guard (Task 6), commit (Task 7), smoke (Task 8). All sections in spec map to a task. |
| Placeholder scan | No "TBD"/"TODO" — every step has exact commands or exact text. |
| Type consistency | The new step 5 in `control.md` references `success_criterion`, `category: "logic"`, `_no_viable_candidate` — same vocabulary as the spec. The new `regression_risk` reduction in `conservator.md` references existing factor name verbatim. The Generator clause references `success_criterion` consistently. |
| Worktree | Skipped per CLAUDE.md workflow (branch-based, not worktree-based). Noted in header. |

## Open Decisions Carried From Spec

None. Spec was closed before this plan was written.
