---
name: consilium
description: Evaluate code changes through Generator/Control/Conservator deliberation. Use when reviewing PRs, planning refactors, assessing risk of proposed changes, before committing non-trivial changes, before implementing non-trivial features (to catch missing tests and prevent code loss), or when uncertain between multiple implementation approaches.
---

# Consilium — Code Deliberation Skill

Multi-perspective deliberation pattern for any code change. Three independent voices collaborate to evaluate a change:

- **Generator** (creative) — proposes alternatives, divergent thinking
- **Control** (analytical) — verifies technical correctness
- **Conservator** (prudent) — evaluates risk and reversibility

## Constitution

Four principles that govern **every** deliberation. They take priority when a voice gives a recommendation that conflicts with them.

1. **Think before coding.** Expose tradeoffs explicitly. If the request has 2 plausible interpretations, list them as separate `candidates` — do not silently pick one.
2. **Simplicity first.** Minimum code. Refuse speculative abstractions and unsolicited features. `do_nothing` is always in the candidate list.
3. **Surgical changes.** Touch only what the goal requires. Conservator measures drift via `scope_drift` — respect a high score.
4. **Goal-driven execution.** Restate the goal as a testable **success criterion** before Generator. The final output includes a **verification** step.

## When to use

Activate this skill when:
- Doing a **PR review** or diff
- Planning a **refactor** that touches 2+ files
- You must choose between **multiple approaches**
- You are about to **commit to shared/core code**
- You want a **risk assessment** before accepting a suggestion
- You are about to **implement** non-trivial functionality (>1 file or >30 lines)
- You want to verify that a completed implementation has not lost existing functionality, edge cases, or tests

Keywords: "review PR", "evaluate change", "refactor planning", "risk assessment", "should I commit", "which approach", "before implementing", "implement feature", "code quality", "missing tests".

## Workflow

### 0. Bootstrap (before any grep / Read on the codebase)
Two actions in order:

1. **Read the contracts of the 3 voices** — `prompts/voices/generator.md`, `prompts/voices/control.md`, `prompts/voices/conservator.md`. They define the exact fields produced by each voice. **Parallel/dialectic note:** the content of each prompt must be *inlined* into the sub-agent dispatch — reading at Step 0 is not enough.
2. **Run `python scripts/priors.py`** — returns soft priors from `FEEDBACK.html` + `runs/`. Three fields can block the current deliberation until resolved:
   - `stale_pendings` non-empty (PEND older than 2 days): ask *"You have N old PEND entries: [date | chosen] × N. Want me to close them (OK/BAD/skip)?"* — update via `mark_outcome.py --date <d> --chosen <id> --outcome OK|BAD` (preferred) or via `Edit` directly on `FEEDBACK.html`. **Do not** use `log_feedback.py` — it duplicates the row. **Headless** (`is_headless()`): log `[priors] stale_pendings: N entries — skipping prompt` to stderr and continue without asking.
   - `missing_feedback_runs` non-empty: run `python scripts/audit_feedback.py --backfill` to create PEND entries for orphan runs, then resolve them as above. If the list is larger than 3, prefer to resolve the gap *before* starting a new deliberation. **Headless**: run `audit_feedback.py --backfill` automatically and continue.
   - `pend_pressure > 0.3` (PEND ratio in the last N=20 entries — threshold lowered from 0.5): soft alert *"{pend_count}/{window_size} recent entries are PEND — consider closing them?"* — do not block, but record the signal. **Headless**: log only, no prompt.

   **Headless (non-interactive — `claude -p` or CI):** `stale_pendings` and `missing_feedback_runs` are automatically suppressed (returned `[]`) when `sys.stdin.isatty()` is `False`. Explicit override: `--headless` flag or `CONSILIUM_HEADLESS=1` env var. Output includes `headless_mode: true` as a marker for consumers.

### 1. Gather context & state the goal
Read the proposed change. Identify scope (files, modules, lines), type (bugfix/feature/refactor/cleanup), blast radius. Formulate `success_criterion` — a testable sentence.

**Clarity gate.** Before Generator: *can you write 2+ plausible distinct interpretations?* If yes — Stop, list them, ask which is the real one. Red flags: vague verbs without a concrete object, undisambiguated references, implicit scope, missing limits. If all are clear → continue without asking. **Non-interactive exception (subagent):** you cannot ask the user — emit each interpretation as a Generator candidate with prefix `interp_a_*`, `interp_b_*` and document the branches in `subagent_notes.clarity_branches`.

### 1.5. Scope gate (auto)
```bash
python scripts/scope_gate.py            # working tree vs HEAD
python scripts/scope_gate.py --ref main # main..HEAD
```
If `should_skip: true`, emit the minimal report and stop:
```json
{
  "success_criterion": "...", "verification": "...",
  "chosen_approach": "skipped", "skipped": true,
  "skip_reason": "...", "signals": {"files_changed": 1, "lines_changed": 4, "blocklist_hits": []},
  "voice_scores": null, "confidence": null, "alternatives": [], "deliberation_log": []
}
```
Defaults: `max_files=1`, `max_lines=15`, conservative blocklist (`auth/`, `security/`, `migrations/`, `.github/workflows/`, `**/secrets*`, `.env*`, `Dockerfile`, `*.tf`, dependency files). Override via `scope_gate.json` (`{max_files, max_lines, blocklist}`). Escape hatch: `CONSILIUM_FORCE_FULL=1` forces `should_skip=false`. Gate **fails open** (no repo / bad ref → `should_skip: false`).

**Non-diff tasks** (audit, architecture review, planning): scope_gate is a no-op — you can skip Step 1.5.

### 2. Conservator — assess risk (runs FIRST)
Use `prompts/voices/conservator.md`. Runs **before** Generator and Control. Its output sets the `tokens_budget` for the other voices.

Required Questions (Q1-Q5): reversibility, magnitude, counterparty_risks, status quo bias check, meta_recommendation.

Output per candidate: `{id, regression_risk: {reversibility, magnitude, net_concern}, counterparty_risks, bias_check, meta_recommendation, tokens_budget: {generator, control}, irreversibility_flag, rollback_recipe, notes}`.

**Sequential-first.** Conservator runs before Generator and Control. Its `tokens_budget` output caps how deep the other voices go. Its `irreversibility_flag: true` BLOCKS the pipeline — confirm user consent before proceeding.

**Veto check (auto, after Conservator output):**
- If `irreversibility_flag: true` → stop, ask user: *"Conservator marks this decision as irreversible. Do you confirm you want to continue?"* — proceed only with explicit YES. **Headless** (`is_headless()`): DO NOT block; set `metadata.headless_overridden: true` in the bundle and continue. The external orchestrator that set `CLAUDE_HEADLESS=1` has assumed the stake.
- If `meta_recommendation: scale_down` → **short-circuit**: skip dispatching Generator AND Control entirely. Build a minimal report directly:
  ```json
  {
    "success_criterion": "<input success_criterion>",
    "verification": "manual review (scope_gate determined trivial)",
    "chosen_approach": "trivial-direct",
    "alternatives": [],
    "voice_scores": {"conservator": "<conservator net_concern>"},
    "confidence": 0.85,
    "deliberation_log": [{"step": "scale_down_short_circuit", "reason": "<conservator notes>"}],
    "telemetry": {"mode": "sequential_scale_down", "dispatch_count": 1}
  }
  ```
  `confidence: 0.85` is deliberate — Conservator's judgment is the signal, not a weak guess. Designed to stay above the `[0.5, 0.7]` skeptic auto-trigger band.
- If `meta_recommendation: scale_up` → warn user, add context request before Generator. **Headless**: warning emitted to stderr, the context cannot be requested interactively — continue with existing input.

**Optional — autoprobe:**
```bash
python scripts/probe_change.py                       # working tree vs HEAD
python scripts/probe_change.py --ref main --churn 30 # + commit count per file last 30 days
```
Anchor `magnitude` to `files_changed/lines_*` and `regression_risk.net_concern` to the churn distribution when present.

### 3. Generator — produce alternatives
Use `prompts/voices/generator.md`. Request **3–5 candidates**, including `do_nothing`. Divergent style. Respect `tokens_budget.generator` set by Conservator.

Output: `{candidates: [{id, summary, sketch, rationale, downside_estimate}], fallback_scenario, coverage_check, challenge_upward, abstain, preferred}`. Adversarial is conditional (the change touches shared/core code OR a function with >3 external callers) — otherwise emit `"adversarial_skipped": "<reason>"`. Unconventional is included by default (unless adversarial already covers that role or the change is mechanically trivial) — emit `"unconventional_skipped": "<reason>"` when omitting.

**Receives from Conservator (selective):** `magnitude`, `counterparty_risks`, `tokens_budget.generator`. Does NOT receive `meta_recommendation` — that is policy, not Generator input.

**Challenge upward:** If Generator sets `challenge_upward.triggered: true`, re-run Conservator with Generator's context before proceeding to Control.

### 4. Control — verify correctness
Use `prompts/voices/control.md`. Per candidate: types, logic, tests, style.

Required Questions (Q1-Q4): glossary (max 5), hidden_assumptions (max 3), disagreements, fixed/negotiable_constraints.

Output: `{glossary, hidden_assumptions, disagreements, fixed_constraints, negotiable_constraints, glossary_fail, glossary_attempts, verdicts: [{id, valid, issues, tests_to_write, notes}]}`. `tests_to_write` mandatory for `valid: true` (exception: `do_nothing`) — 1-4 acceptance tests.

**Receives from both:** full Conservator output + full Generator output.

**Post-Control veto check:**
- If `glossary_fail: true` → BLOCK, request reformulation from user.
- If `disagreements` contains any `type: substantial` → REWORK: re-run Generator with clarification before aggregating.

### 5. Aggregate
```bash
python scripts/aggregator.py --scheme conservative_override
```
Default: **conservative_override** — veto at `risk_score > 0.8`; ranking by weighted average `(generator + control + safety)` where `safety = 1 - conservator`. On a tie, the safer candidate wins. Alternative: `--scheme risk_adjusted_utility` (sigmoid penalty, no rigid veto).

### 5b. Confidence
```bash
echo '{"candidates": [...], "chosen": "approach_id"}' | python scripts/confidence.py
```
Returns `{confidence, agreement, separation}`. If `chosen` is `null` (all vetoed), `confidence` is `null`.

> **Calibration (R2 audit 2026-05-17):** `agreement` measures divergence between roles within ONE run — not inter-run stability. Conservator scores are anchored by categorical formula (see `conservator.md`); Generator/Control scores are unanchored self-assigned floats. A second run with the same input may produce different scores (pstdev estimated 0.12–0.18 on `risk_score`). The `confidence` value is not a calibrated probability — it is an internal-consistency signal.

**Quoting:** Avoid building inline Python via `-c "..."` with JSON payload — apostrophes in the code can break bash quoting. Use stdin piping (as above) or the `--input <file>` flag.

**Mode confidence floor (E1).** After confidence is derived, check whether the mode reached the minimum floor:
```python
from scripts.confidence import check_mode_floor
result = check_mode_floor(telemetry_mode, confidence_value)
# result["below_floor"] == True → log with --outcome WEAK in FEEDBACK.html
```
Floors: `sequential=0.70`, `dialectic=0.75`, `trias=0.80`. A run below floor signals the mode did not deliver value for the cost. The data accumulates in `FEEDBACK.html` — the pattern becomes visible after ≥10 runs per mode.

### 5c. Meta-critic (auto, advisory)
```bash
cat bundle.json | python scripts/meta_critic.py
```
Scores **deliberation quality** (not choice correctness): `generator_divergence` (paraphrasing?), `control_concreteness` (speculation?), `conservator_spread` (shrug?). Emits `deliberation_quality.flags` — attach to the bundle before Step 6 (build_report passes it through to the report). Non-empty `flags` do not block, but must be mentioned in `reasoning`.

### 5d. Retry on low confidence (optional, single pass)
If `confidence < 0.7`, **before** asking the user:
```bash
cat bundle.json | python scripts/retry_context.py
```
Returns the top-2 candidates with files/symbols to read/grep. Use the hints → gather context (Read + Grep) → re-run Generator/Control/Conservator **once** with enriched input. If confidence is still < 0.7, only then ask the user (Step 6).

**Headless** (`is_headless()`): skip Step 5d entirely — go directly to Step 6 where `PEND_HEADLESS` is logged. Empirical note: `retry_context.py` has zero labeled usage in the `runs/` corpus (see senate audit `2026-05-16_220025-flow-and-modes-audit-r2`); skipping in headless is aligned with that deletion-vote and does not lose an active mechanism.

### 6. Report

**Telemetry emission (mandatory — before `build_report.py`).**

At each dispatch (voice or senator), immediately after return, accumulate in the bundle:

- `telemetry.voices.<voice_name>` or `telemetry.senators.<senator_name>` (Senate): `{tokens_in: ceil(len(prompt)/4), tokens_out: ceil(len(response)/4), latency_ms: <wall-clock>}` — prompt = full text sent (persona + context + proposal, not just the proposal).
- Sum tokens + latency per voice if there are retries on the same dispatch.
- `telemetry.mode` ← canonical label (`"sequential"`, `"senate"`, `"trias"` etc. — from `## Dispatch defaults`).
- `telemetry.dispatch_count` ← total dispatches (including retries).

Why mandatory: `scripts/efficiency.py` returns `null` for any run without telemetry, polluting per-mode averages — a run without telemetry is invisible in efficiency comparisons.

```bash
cat bundle.json | python scripts/build_report.py | python scripts/validate_report.py
```
Bundle schema: `{success_criterion, verification, generator, control, conservator, aggregate, confidence, telemetry}`. `build_report.py` derives `voice_scores`, assembles `alternatives` (with `why_not`) and `deliberation_log`.

**Output JSON** (required fields — validated by `validate_report.py`, required by Principle #4):
```json
{
  "success_criterion": "<string — testable sentence>",
  "chosen_approach": "<id from candidates | null>",
  "verification": "<command or concrete check>",
  "alternatives": [{"id": "...", "summary": "...", "why_not": "..."}],
  "voice_scores": {"generator": 0.0, "control": 0.0, "conservator": 0.0},
  "confidence": 0.0,
  "deliberation_log": [{"step": "generator|control|conservator|aggregate", "...": "..."}]
}
```

**Terminal output discipline.** Do not write intermediate JSON bundles to disk (`bundle_*.json`). Pipe outputs directly. The only output visible in the terminal at the end:
```
chosen: <id> | conf: <X> | runs/<file>.json
```

**Validation gate** (mandatory before considering the report final):
```bash
cat runs/<file>.json | python scripts/validate_report.py
```
Exit 0 = OK. Exit 1 = missing/empty field or malformed telemetry. Exit 2 = malformed JSON.

**Final actions (mandatory — deliberation is not complete without them):**

The two calls below are **mandatory**. If the orchestrator stops before running them, the report exists on disk but is invisible to priors → the next deliberation will not benefit from this feedback. Periodic audit: `python scripts/audit_feedback.py` lists orphan runs; with `--backfill` it adds default PEND rows.

1. **Persist the report** in `runs/YYYY-MM-DD_HHMM_<label>.json`.
2. **Log to `FEEDBACK.html`** (confidence-gated, without skipping any case):
   - `confidence >= 0.7` → `python -X utf8 scripts/log_feedback.py --outcome OK --run-path runs/<file>.json < runs/<file>.json`
   - `confidence < 0.7` → ask: *"Confidence below threshold (`<X>`). Want to override `<chosen>`? Alternatives: `<alt_ids>`. Reply alt_id, 'no', or 'skip'."* Then: `no` → `--outcome OK --force-override`; `<alt_id>` → `--outcome OVR --override-target <alt_id>`; `skip` → no flag (PEND, but **do not let the call be skipped**).
   - `confidence null` (all vetoed) → `python -X utf8 scripts/log_feedback.py --run-path runs/<file>.json < runs/<file>.json`
   - **Non-interactive path (headless — `claude -p`).** Skip the prompt at `confidence < 0.7` and call directly: `python -X utf8 scripts/log_feedback.py --outcome PEND_HEADLESS --run-path runs/<file>.json < runs/<file>.json`. `PEND_HEADLESS` is structurally excluded from `pend_pressure` and `stale_pendings` (PEND_HEADLESS ≠ "PEND" in Counter) — it requires no manual resolution.

**Outcome confirmation (retroactive).** The outcome logged in step 2 is subjective — it reflects the immediate impression. If production later reveals a regression or a good choice, overwrite it with the confirmed marker:
```bash
python scripts/mark_outcome.py --run-path runs/<file>.json --outcome BAD --reason "broke prod migration"
```
The `[confirmed]` marker appears in the note; `priors.py` weights these rows 2x compared to subjective feedback (see `weighted_bad_rate`).

**Scale_down regret tracking (A2).** If `telemetry.mode == "sequential_scale_down"` and the retroactive outcome is `BAD`:
```bash
python scripts/mark_outcome.py --run-path runs/<file>.json --outcome BAD --reason "scale_down regret — full deliberation needed"
```
Calibration signal: if `scale_down` regret rate > 10% over n≥20 runs, Conservator's scale_down threshold is too aggressive — adjust the prompt. If the rate stays < 5%, the optimization is validated.

### 7. Auto-pipeline (post-report)

**Mandatory if the user's prompt contains a header of the form `**Required output file(s):**` or `**Deliverable(s):**` (with or without colon, singular or plural) — authoritative detection regex: `\*\*\s*(?:Required\s+output\s+files?|Deliverables?)\s*\*\*\s*:?` applied per whole line, case-insensitive.** In this case Step 7 is no longer optional: after Step 6 is complete, go directly to `infer_pipeline.py` and execute all inferred steps (at minimum `implement` with the Write tool for each declared path). The deliberation report alone does not satisfy the contract — files must exist on disk before the turn closes.

**Opt-in otherwise** — when the prompt does not declare deliverables (audit, "should I commit", "which approach", "before implementing"-without-code-required), Step 7 is at the user's discretion.

After Step 6 is complete (report saved, feedback logged), infer and confirm the implementation steps:

```bash
cat runs/<file>.json | python scripts/infer_pipeline.py          # interactive
python scripts/infer_pipeline.py --input runs/<file>.json --yes  # CI/headless
python scripts/infer_pipeline.py --input runs/<file>.json --dry-run  # print only
```

The script reads `chosen_approach`, `magnitude`, and `reversibility` from the report and looks up the table below:

| magnitude | reversibility | inferred steps |
|---|---|---|
| trivial | complete | implement |
| trivial | partial | implement → compile |
| trivial | irreversible | implement → compile → test |
| moderate | complete | implement → compile |
| moderate | partial | implement → compile → test |
| moderate | irreversible | implement → compile → review → test |
| high/critical | any | implement → compile → review → test |

**Step definitions:**
- `implement` — Write the code per `chosen_approach`. If the prompt contains a header matching the authoritative regex from the mandatory clause (plural or singular, with or without colon), use the Write tool for each declared file at the specified path — do not emit the implementation only as a fenced block in chat. Files must exist on disk, not only in the response.
- `compile` — run the target, verify exit code 0 (runtime check)
- `review` — re-run the Control voice on the actually-written code (not the proposal)
- `test` — run the existing test suite (pytest/unittest autodiscovery)

Output JSON: `{"steps": [...], "rationale": {"chosen": "...", "magnitude": "...", "reversibility": "...", "lookup_key": "..."}}`.

Reject (`n` at prompt) → rejection logged in `runs/YYYY-MM-DD_HHMM_pipeline_rejected.json`. Rerun with `--yes` for CI or `--dry-run` for audit without confirmation.

**Skip Step 7 if:** `chosen_approach` is `do_nothing` or `skipped` (the script exits with exit 1 and a clear message). In headless context (`claude -p`), run with `--yes` (non-interactive, no confirmation prompt).

**The skip does NOT apply to the mandatory requirement above:** if the prompt declares deliverables (per the authoritative regex from the mandatory clause above) and you nonetheless arrive at `chosen=do_nothing`, that means the deliberation rejected the implementation of an explicit user request — a case that requires a visible signal (hard error in the response: *"deliberation chose `do_nothing` on a prompt with declared deliverables — the user must decide"*), not silent skip.

### Observe → Think → Act → Learn (descriptive framing)

**This section is descriptive only.** It does not create new behavioral contracts; Steps 0–7 above remain the authoritative workflow. The mapping below is a reading aid for contributors who arrive expecting an Observe–Think–Act–Learn shape — it names what is already present without prescribing anything new.

| OTAL phase | Step(s) | Script(s) that implement the phase |
|---|---|---|
| **Observe** | Step 0 + Step 1 | `priors.py` (reads `FEEDBACK.html` + `runs/*.json`); orchestrator gathers context from the codebase |
| **Think**   | Steps 2–5     | `aggregator.py`, `confidence.py`, `meta_critic.py`; Conservator → Generator → Control voices |
| **Act**     | Step 6 + Step 7 | `validate_report.py`, `build_report.py` (write `runs/<file>.json`); `infer_pipeline.py` (write code) |
| **Learn**   | Step 6 final action + retroactive | `log_feedback.py` (append to `FEEDBACK.html`); `mark_outcome.py` (retroactive `[confirmed]` weighting) |

```
         ┌────────────────────────────────────────────┐
    ┌───▶│  OBSERVE    (Step 0 + Step 1)              │
    │    │  priors.py · gather context                │
    │    └────────────────────┬───────────────────────┘
    │                         │
    │    ┌────────────────────▼───────────────────────┐
    │    │  THINK      (Steps 2 → 5)                  │
    │    │  Conservator → Generator → Control         │
    │    │  → aggregator.py · meta_critic.py          │
    │    │                                            │
    │    │  ↻ retry_context.py — Step 5d: one in-run  │
    │    │    sub-iteration if confidence < 0.7       │
    │    └────────────────────┬───────────────────────┘
    │                         │
    │    ┌────────────────────▼───────────────────────┐
    │    │  ACT        (Step 6 + Step 7)              │
    │    │  validate_report.py · build_report.py      │
    │    │  → runs/<file>.json                        │
    │    │  infer_pipeline.py → code written          │
    │    └────────────────────┬───────────────────────┘
    │                         │
    │    ┌────────────────────▼───────────────────────┐
    │    │  LEARN      (Step 6 final + retroactive)   │
    │    │  log_feedback.py → FEEDBACK.html           │
    │    │  mark_outcome.py — 2× weight when          │
    │    │  [confirmed] by production reality         │
    │    └────────────────────┬───────────────────────┘
    │                         │
    └─────────────────────────┘
         priors.py reads FEEDBACK.html at the next
         deliberation — this is the closing edge
```

A small in-run sub-iteration exists: at `confidence < 0.7`, Step 5d invokes `retry_context.py` to enrich input and re-run the voices once (`↻` in the diagram). This is the only formal iteration mechanism; there is no meta-controller.

**Calibration note (Learn phase).** The Learn phase is presently *partial* in a structural sense: `log_feedback.py` writes outcomes into `FEEDBACK.html` (HTML rows), but `runs/<file>.json` does not carry a structured `outcome` field. Consequently `priors.py` reads outcomes from the HTML journal, not from a typed JSON field. The loop closes via the journal — naming the gap explicitly so future readers don't assume an unwired feedback channel exists.

**What this framing is not.** This section does not introduce iteration triggers beyond Step 5d's `retry_context.py`, does not name a meta-controller, and does not authorize voices or aggregator to cite "OTAL step X" as ground for new behavior. If a future proposal seeks behavioral iteration triggers (e.g. firing a second pass on `meta_critic.generator_divergence < 0.4`), that requires its own Senate audit with empirical pilot data — `generator_divergence` currently has zero labeled triggering events in `runs/`, so any threshold would be uncalibrated. A dynamic meta-controller is explicitly out of scope: its TODO precondition (item #16) was dropped in triage, and recursive routing contradicts Constitution Principle 2 (Simplicity first).

> **TODO #18 closure rationale** (2026-05-19 Senate audit, `runs/senate/2026-05-19_214850-todo-18-otal-formalization.json`, MODIFY 0-8-1): 8 of 9 senators converged on docs-only framing. Level 2 (iteration triggers) deferred until ≥3 PEND rows in `FEEDBACK.html` demonstrate the current `confidence<0.7` retry underperforms. Level 3 (meta-controller) closed pending #16's revival.

## Skill maintenance

Apply only when editing the skill (`scripts/*.py`, `prompts/*.md`, `SKILL.md`), not at every deliberation.

**Eval harness** — when editing `aggregator.py`, `confidence.py`, `validate_report.py`, or `strip_context.py`:
```bash
python scripts/run_evals.py
```

**Usage rollup** (when you have 10+ runs with telemetry): `python scripts/usage.py [--last 50]`

**Periodic feedback audit**: `python scripts/feedback.py [--recent 10 --runs]` (stats), `python scripts/audit_feedback.py [--backfill]` (runs without FB row).

**Benchmarking discipline** — any quantitative claim about voice behavior (`fab-rate`, `accuracy`, `catch-rate`) must cite an **independent oracle** (a second expert OR explicit citation from the statement/specs that fixes the ground truth), not the evaluator's quick take. Before publishing benchmark results: for each plausible option (A/B/C/D...), document explicitly *"is there an alternative reading of the problem in which answer X becomes correct?"* — explicit answer per option. A "fabrication" verdict on a piece of reasoning remains blocked until oracle review, separate from the evaluator's intuition. Retroactively applied: any existing fab-rate claim in `experiments/` and `runs/` is reviewed through this grid. Operational checklist: `experiments/README.md`. Origin: the P3 corrigendum (see `experiments/p3-car-wash.html`) — the wrong oracle semantically inverted the "fabrication" conclusion → "real constraint catch".

## Resources

| Script | Role |
|---|---|
| `scripts/priors.py` | Soft priors from FEEDBACK.html + runs/ (Step 0). Surfaces `missing_feedback_runs`, `stale_pendings` (2-day threshold), `weighted_bad_rate`. |
| `scripts/scope_gate.py` | Auto-detect skip if scope is small (Step 1.5) |
| `scripts/probe_change.py` | Anchor diff_size to `git diff --numstat` (Step 4) |
| `scripts/aggregator.py` | 4 voting schemes + auto-relax on total veto (Step 5) |
| `scripts/confidence.py` | Derives confidence from variance + separation (Step 5b) |
| `scripts/meta_critic.py` | Deliberation quality score (divergence/concreteness/spread) — Step 5c |
| `scripts/retry_context.py` | Hint for single retry when confidence < 0.7 — Step 5d |
| `scripts/build_report.py` | Assemble the canonical report from the bundle (Step 6) |
| `scripts/validate_report.py` | Principle #4 gate: success_criterion + verification + chosen_approach |
| `scripts/log_feedback.py` | Auto-append to FEEDBACK.html at the end of Step 6 |
| `scripts/mark_outcome.py` | Retroactive outcome overwrite (`[confirmed]` in note → 2x weight) |
| `scripts/infer_pipeline.py` | Step 7: infer + confirm implementation steps from the report; `--dry-run` / `--yes` |
| `scripts/audit_feedback.py` | List runs without FB row; with `--backfill` adds default PEND |
| `scripts/memory.py` | Uniform read API over the 3 tiers (short/medium/long) |
| `scripts/strip_context.py` | Project previous voice's output to minimum (Steps 3-4 sequential) |
| `scripts/deprecated/dialectic_merge.py` | *(Deprecated — Pass-1+Pass-2 merge for old Dialectic mode)* |
| `scripts/personalities.py` | Trias mode — 3 fixed personalities with weights + lens paths |
| `prompts/voices/skeptic.md` | Focal voice for the `skeptic_on_chosen` flag (composable over any mode) — receives only the chosen, produces a concrete objection or `meta_scope_mismatch` |
| `scripts/run_evals.py` + `evals/scenarios.json` | Regression suite for deterministic scripts |
| `scripts/usage.py` | Telemetry rollup from runs/ |
| `agents/consilium-subagent.md` | Subagent for isolated invocation via `Agent(subagent_type="consilium-subagent", ...)` |
| `prompts/senators/*.md` | 7 pre-implementation audit prompts (`senate` mode); each with a distinct specialty (see table in Senate mode) |
| `scripts/vocabulary_map.py` | RUND2: user-facing translations (reversibility/magnitude/meta_recommendation/verdict) + `compute_tokens_budget(magnitude, reversibility, meta)` |
| `scripts/senate_synth.py` | Senate synthesizer: aggregates 7 JSON outputs → verdict `GO/MODIFY/STOP/DEEPLY_SPLIT/UNREACHABLE/OUT_OF_SCOPE` + modify_requests + risks → saves to `runs/senate/`. Supports **multi-round (Laws 2+4)** via schema `{rounds: [...]}` with `cross_questions[]`, `position_changes[]`, and `blocaj_resolution` (5-vote tiebreaker). **Law 3** (`blocaj_pending` advisory signal) active on both modes when `verdict ∈ {MODIFY, DEEPLY_SPLIT}`. **Law 7** (`scope_veto` consensus ≥3 → `OUT_OF_SCOPE`). **Law 8** (`law8_enforce: true` → auto-promote vague-MODIFY). |
| `scripts/senate_priors.py` | Law 6 helper: scans `runs/senate/*.json` for runs with similar label (substring match, stdlib-only) in the last 30 days; returns prior verdict + top 3 modify_requests for context injection. |

## Feedback loop

- **`runs/`** — JSON per deliberation in `runs/YYYY-MM-DD_HHMM_<label>.json` (schema in `runs/README.md`). Gitignored. Read by `priors.py` (Step 0), `usage.py`, `feedback.py`.
- **`FEEDBACK.html`** — one line per use: `date | context | chosen | outcome | note`. Outcome: `OK`, `BAD`, `OVR`, `PEND`. Local, gitignored. **Drill-down:** when `log_feedback.py` appends, existing rows lose drill-down; use `scripts/deprecated/migrate_feedback_md_to_html.py` for bulk re-population (retired one-shot tool, see scripts/deprecated/).
- **Confirmed outcome.** `mark_outcome.py` adds the `[confirmed]` marker in note. `priors.py` weights these rows 2x in `weighted_bad_rate`. Use when production reality contradicts the subjective outcome from Step 6.

## Memory tiers

Consilium has 3 memory layers with different lifecycles. `scripts/memory.py` provides a uniform read API over all three.

| Tier | Location | Lifetime | Content | Read by |
|---|---|---|---|---|
| **Short** | conversation window | session | bundle under construction (Steps 1–5b), clarity gate, current success_criterion | agent only (not persisted) |
| **Medium** | `runs/*.json` | indefinite (gitignored) | one file per deliberation; episodic | `priors.py`, `usage.py`, `memory.py`, `audit_feedback.py` |
| **Long** | `FEEDBACK.html` + signals from `priors.py` | indefinite | one row per use; aggregated over time | `priors.py`, `feedback.py`, `memory.py`, `mark_outcome.py` |

Uniform CLI:
```bash
python scripts/memory.py --tier medium --n 5             # last 5 runs
python scripts/memory.py --tier long --query auth        # substring filter
python scripts/memory.py --tier all --query feedback     # union across 3 tiers
```

## Headless invariants

When `CLAUDE_HEADLESS=1` (set by the external orchestrator that invoked `claude -p`), 4 points in the workflow drop user-facing prompts and use documented defaults. Pattern aligned with `CONSILIUM_FORCE_FULL` from `scope_gate.py`. Helper: `from utils import is_headless`.

| Step | Headless default |
|---|---|
| 0 (`stale_pendings`, `missing_feedback_runs`, `pend_pressure`) | log warning to stderr + continue; for `missing_feedback_runs` run `audit_feedback.py --backfill` automatically |
| 2 (`irreversibility_flag: true`) | set `metadata.headless_overridden: true` in bundle + continue (external orchestrator has assumed the stake) |
| 5d (retry on low confidence) | skip entirely; go directly to Step 6 with `PEND_HEADLESS` |
| 7 (auto-pipeline) | run with `--yes` (non-interactive, no confirmation prompt); **mandatory** if the prompt contains a `**Required output file(s):**` or `**Deliverable(s):**` header (authoritative regex from Step 7 mandatory clause) — actual implementation (Write tool on declared paths) is part of the contract, not an optional post-step |

`is_headless() == False` (env var absent) → current behavior unchanged. Backward compat 100%.

**Pattern adopted:** strict boolean `CLAUDE_HEADLESS=1` (other values → False). Aligned with `CONSILIUM_FORCE_FULL=1` precedent (see `scripts/scope_gate.py`). The external orchestrator (run_task.py, CI script, parent agent) sets the env var before invocation; the skill never modifies the env.

**Senate note:** `runs/senate/2026-05-18_164154-mode-bugfix-performance.json` + mini-senate H2+H4 (verdict B+X 5/7 + 4/7) validated this contract.

## Dispatch defaults (per voice / per senator)

Default behavior unless overridden by project memory (`MEMORY.md`). All voices and senators pinned to `model: "sonnet"` per `feedback_subagents_sonnet.md`. Mode sections declare per-invocation overrides (e.g. `opus` Generator for high-stakes) — single source of truth per mode, descriptive not enforced.

Cost multipliers (baseline Sequential = 1×): Parallel 3× · Dialectic 1.33× · Trias 3× · Senate ~3× (9 senators). The `skeptic_on_chosen` flag adds +1 sub-agent over the base mode (e.g. Sequential+flag = 1.33×, Parallel+flag = 1.33× Parallel).

## Parallel voices mode

<!-- === RUND2 === -->
**Parallel mode removed (RUND2).** Parallel dispatch is no longer a user-selectable option. Auto-triggered internally only when `magnitude = critical` AND `reversibility = irreversible`, as a cross-check on the sequential result. Every 20 runs, a silent parallel audit runs automatically; if systematic divergence is detected, frequency increases to 1/5.
<!-- === END RUND2 === -->

**Legacy reference (auto cross-check only).** Dispatch the 3 voices as independent sub-agents — eliminates cross-contamination completely.

### How (2 turns)
1. **Turn 1:** dispatch Generator (1 Agent call). Wait for candidates.
2. **Turn 2:** dispatch Control + Conservator in parallel (2 Agent calls in the same message), both receiving candidates from Turn 1.
3. Aggregate directly with `scripts/aggregator.py`.

Each sub-agent receives: `success_criterion`, diff/context, **the full content of its voice's prompt**, the instruction to return strict JSON.

**Override semantics (Parallel mode):** `model: "opus"` on Generator for high-stakes/ambiguous cases; `model: "haiku"` on Control/Conservator for small diffs. Default per `## Dispatch defaults`.

**Prompt template:**
```
Goal: <success_criterion>
Change under review: <diff or description>
Codebase context: <files touched, language, framework>

Your role and instructions:
<full content of prompts/<voice>.md>

Return STRICTLY the JSON specified in the "Output format" section above. No prose before or after.
```

**Skip parallel if:** the change is trivial (<10 lines), you don't have the `Agent` tool, or you want to audit the reasoning step-by-step.

**Failure-mode recovery:**
- **Sub-agent crash / timeout:** retry that Agent call once; on a second failure, fall back to Sequential for that voice.
- **Malformed JSON from voice:** reject the voice's output, treat as missing (`{}` for verdicts/scores, or `{"candidates":[]}` for generator) and continue with the others. Log the error in `deliberation_log` with step `"<voice>_parse_error"`.
- **Missing mandatory fields (e.g. `candidates` empty):** raise a warning in the terminal, skip the aggregator and emit a skipped report with `skip_reason: "voice output incomplete after retry"`.
- **Strip_context**: necessary only in Sequential mode (Steps 3-4); in Parallel each voice runs in isolation and does not need `strip_context.py`.

## Dialectic mode — V2 (opt-in, code-specialized)

**Mechanics:** Standard Sequential (Conservator→Generator→Control) with code-specific context injected into the voice inputs, followed by `skeptic_on_chosen`. Cost: 1.33× Sequential (1× Sequential + 1/3 for Skeptic sub-agent). No new prompt files — context is injected via the voice input fields.

### Code-context injection

Inject into each voice's input (not into the prompt file):
- `language` + `framework` + `build_command` (e.g. `pytest -x`, `cargo test`)
- `files_touched[]` — list of affected files with their roles
- `test_files[]` — existing test files the change must not break
- `ci_gate` — the check that must pass before merge

This injection activates code-specific reasoning in the existing voices without new prompt files.

### Skeptic stage

After Sequential produces `chosen`, always dispatch `skeptic_on_chosen` (not conditional on confidence band). The Skeptic receives the chosen + `success_criterion` + the code context. The verification claim must be concrete: a named test, a build command, or a CI check.

### When to use
- Code change where implementation strategy and verification strategy are both non-obvious
- You want a focused challenge on the chosen approach post-deliberation
- Medium-stakes refactor (2–5 files) where Sequential alone feels thin

### Workflow
1. Inject code-context into voice inputs (language, files, test suite, CI gate)
2. Run Sequential (Conservator→Generator→Control) — standard Steps 2–4
3. Run `skeptic_on_chosen` unconditionally (not gated on confidence band)
4. Aggregate + confidence as normal (Steps 5–5b)
5. If Skeptic catches constraint: `skeptic_caught_constraint: true` in report; advisory by default, `--skeptic-can-override` for opt-in override

**telemetry.mode** for this mode: `"dialectic"`. Legacy runs with mode `"dialectic"` (old Pass1+Pass2) are preserved in `runs/` with no schema change — `validate_report.py` keeps `"dialectic"` in `_MULTI_VOICE_MODES`.

**Old Dialectic (Pass1+Pass2) archived.** `scripts/deprecated/dialectic_merge.py` is the retired implementation. `prompts/voices/*_pass2.md` remain on disk for reference but are not dispatched.

## Trias mode (high-stakes opt-in)

**Mechanics:** 3 fixed personalities (Pioneer / Architect / Steward), each dispatched as **one Sequential sub-agent** (Conservator→Generator→Control internally) with the personality lens prepended. Democratic majority vote over the 3 chosen results. Cost: 3× Sequential (3 sub-agents vs 1).

**Previous mechanics (archived):** The old Trias dispatched 9 parallel sub-agents (3 personalities × 3 voices). The new design reduces from 9 to 3 sub-agents — each personality runs its own Sequential deliberation internally. The democratic vote over 3 chosen results is preserved.

### When to use
- Irreversible schema/DB migration
- Security audit (auth, crypto, RCE potential)
- Refactor > 5 files
- 2+ plausible architectural approaches, no clear winner
- Cost of wrong decision >> cost of running (3 sub-agents, 3× Sequential)

### Lazy routing (default: enabled)

**Purpose:** Avoid the 3× Sequential cost when the change does not warrant it. Trias checks magnitude via `scope_gate.py` and auto-downgrades to Dialectic for low/medium changes.

**Default:** `lazy=true` — Trias auto-downgrades low/medium magnitude to Dialectic. To force full Trias, the user must explicitly state "use full Trias" or "no lazy routing" in their request.

**Sequencing contract (mandatory):** Magnitude classification MUST run on the **original unstripped context** BEFORE Phase 1 context stripping is applied. Strip happens after the routing decision.

**Routing logic:**
```bash
gate=$(python -X utf8 scripts/scope_gate.py)          # on original context
magnitude=$(echo "$gate" | python -c "import sys,json; print(json.load(sys.stdin)['magnitude'])")
```
- If `magnitude == "high"` → proceed to full Trias (then apply Phase 1 strip below)
- If `magnitude != "high"` → downgrade to Dialectic and emit structured notification:
  ```json
  {
    "trias_lazy_routed": true,
    "routed_to": "dialectic",
    "magnitude": "<low|medium>",
    "magnitude_score": {"files": <n>, "lines": <n>, "blocklist_hits": <n>},
    "threshold": "high",
    "context_tokens_available": <approx>,
    "override_instruction": "Re-invoke with explicit 'use full Trias' to force 3-sub-agent mode."
  }
  ```

### Workflow
0. **(Phase 2 — lazy routing)** Run scope_gate on original context and check magnitude. If `magnitude != "high"` AND user has not explicitly requested full Trias, downgrade to Dialectic (emit notification above) and stop Trias workflow here.
1. Orchestrator reads `python -X utf8 scripts/personalities.py` — emits the 3 personalities
2. **(Phase 1 — context strip)** Before building each sub-agent prompt, truncate the raw conversation context to ≈15 000 tokens:
   ```bash
   stripped=$(echo "$raw_context" | python -X utf8 scripts/strip_context.py --truncate-text 15000)
   ```
   Use `$stripped` (not `$raw_context`) in each personality sub-agent prompt. This runs **per sub-agent** so each gets the same budget-capped context. The truncation marker `[... context truncated ...]` signals to the sub-agent that context was cut; it should proceed normally.
3. For each personality, spawn a **budget-capped sub-session** via Bash (hard cap $0.50):
   ```bash
   personality_prompt=$(cat prompts/<personality>_lens.md)
   result=$(printf '%s\n\n%s' "$personality_prompt" "$stripped" \
     | claude -p --model claude-sonnet-4-6 --max-budget-usd 0.50 --effort high)
   ```
   The sub-session runs Conservator→Generator→Control internally and returns a full report with `chosen_approach`. If a sub-session hits its $0.50 cap, log `{personality: "<name>", halted: "budget_cap_0.50"}` and treat its vote as abstain (exclude from team_vote).
4. Collect the 3 `chosen_approach` values (one per personality) → `chose` per personality
5. **Unanimous check (B1).** If all 3 personalities chose the same `chose`, skip `team_vote` — the result is unanimous. Set `vote_pattern: "3-0"` and `vote_skipped: true`. Confidence derived directly from `confidence_from_vote_pattern("3-0")`. Log in `deliberation_log` with `reason: "unanimous_personalities"`. If not unanimous, run `team_vote` normally.
6. Orchestrator runs `python -X utf8 scripts/aggregator.py --scheme team_vote` over the 3 chosens (skip if B1 detected unanimity)
7. Confidence derived from vote_pattern — pipe aggregator output directly to `confidence.py`:
   ```bash
   echo '{"personalities":[...],"candidates":[...]}' | python scripts/aggregator.py --scheme team_vote | python scripts/confidence.py
   ```
   Do not manually build `{"candidates":[...],"chosen":"..."}` for Trias — the candidates don't have `scores` per voice.
8. **Deadlock cascade (B2) — only if vote_pattern is 1-1-1 or 0-0-0.** See Failure recovery below.

### Vote patterns
| Pattern | Confidence | Outcome |
|---|---|---|
| 3-0 | 0.95 | OK auto |
| 2-1 | 0.75 | OK auto |
| 2-0 | 0.70 | OK auto |
| 1-1-1 | null | → B2 cascade (Round 2 → Skeptic → PEND) |
| 0-0-0 | null | → B2 cascade (Round 2 → PEND) |

### Failure recovery

**B2 — Deadlock cascade.** Fires when Round 1 yields 1-1-1 or 0-0-0.

**Round 2 (always first):** Re-dispatch all 3 personality sub-agents. Each receives the other two personalities' `{chosen_approach, reasoning_summary}` from Round 1 as additional context. Re-vote via `team_vote`. Cost: +3 sub-agents.

- Round 2 produces 2-1 or 3-0 → cascade exits, report normally. Set `trias_rounds: 2` in telemetry.
- Round 2 still **1-1-1** → proceed to Skeptic tiebreaker (below).
- Round 2 still **0-0-0** → **PEND** (Skeptic cannot arbitrate among nothing). Set `trias_rounds: 2, deadlock: "0-0-0"` in telemetry.
- Round 2 converts 0-0-0 → 1-1-1 → proceed to Skeptic tiebreaker.

**Skeptic tiebreaker (only after Round 2 1-1-1):** Dispatch 1 sub-agent with `prompts/voices/skeptic.md` plus modified input — all 3 competing `{chosen_approach, reasoning_summary}` pairs. Skeptic selects one id as `chosen`. Cost: +1 sub-agent. Set `trias_rounds: 2, tiebreak: "skeptic"` in telemetry.

- Skeptic returns a valid id → chosen confirmed. Confidence: 0.65 (tiebreak path).
- Skeptic abstains or errors → **PEND**.

**Headless (B2):** All Round 2 and Skeptic dispatches run as non-interactive sub-agents — no prompt needed. Final PEND falls through to `PEND_HEADLESS` logging.

**Max cost (worst case 1-1-1 → Round 2 → Skeptic):** 3 + 3 + 1 = 7 sub-agents.

### Skip Trias if
- Diff < 20 lines / 1 file — `scope_gate.py` will skip anyway
- Strict conservatism required (aggregated Trias is −18% Conservator)
- Obvious bugfix — Sequential blind is enough

## Trias split-model mode (`trias_split`) — DEPRECATED

**Removed.** `trias_split` is no longer a user-selectable mode. With Trias reduced from 9 to 3 sub-agents (3× Sequential), `trias_split`'s 3.3× cost advantage over the old 9× Trias no longer exists — both are now effectively the same cost tier. Use standard `trias` instead.

`validate_report.py` maps legacy `trias_split` runs to `trias` via `_LEGACY_MODE_ALIASES` for telemetry backward-compat.

## Skeptic-on-chosen mode (`skeptic_on_chosen`)

**Mechanics:** `skeptic_on_chosen` is a **cross-cutting flag**, not a fixed mode. It composes over any base mode (Sequential, Parallel, Dialectic, Trias): after the base mode produces `chosen` and `confidence`, 1 additional Skeptic voice is dispatched on the resulting `chosen`, with the prompt `prompts/voices/skeptic.md`. The flag runs **sequentially post-hoc** on any mode (vs a fixed mode that includes it in Pass-1). There is no dedicated Python code — orchestration is done via standard dispatch of `prompts/voices/skeptic.md` with the current chosen.

**Cost:** +1 sub-agent over the chosen base mode (whichever it is). E.g.: Parallel + flag = 4 sub-agents (1.33× Parallel); Dialectic + flag = 7 sub-agents (~2.3× Parallel).

> **Legacy note.** The modes `parallel_skeptic` and `dialectic_skeptic` were distinct fixed modes (Parallel/Dialectic with Skeptic baked-in). They were collapsed into this composable flag on 2026-05-17 — the identical functionality is obtained via `parallel + skeptic_on_chosen` and `dialectic + skeptic_on_chosen`. The legacy names remain in `validate_report.py` MODE enum for backward-compat with historical runs.

### When to use

**Auto-trigger conditions** (any is sufficient):
- Confidence ∈ `[0.5, 0.7]` — classic trigger
- Confidence > 0.7 BUT `Conservator.net_concern` > 0.7 — high-conf/high-concern discrepancy is worth probing: `trigger_reason: "high_conf_high_concern"`
- `chosen_approach` coincides with a `BAD` outcome from `FEEDBACK.html` (last 30 days, substring match on label): `trigger_reason: "similar_to_recent_bad"` — Tacitus-lite for classic modes
- `irreversibility_flag: true` — existing consent gate, Skeptic adds object-level check: `trigger_reason: "irreversibility_gate"`

- **Manual opt-in** via `--skeptic-on-chosen` when you want a focal challenger post-hoc regardless of confidence (medium-stakes, problems with known implicit constraints)
- Problems where chosen_confirmation_pass has empirically demonstrated value — particularly situations with implicit constraints not explicitly stated in success_criterion (P3 type: the logical preconditions of the solution don't appear in the statement)
- When you want the focal challenger on any base (Sequential / Parallel / Dialectic / Trias) without dedicated fixed mode cost
- Cases where you want to know whether chosen missed something, but have no basis for comparison (no viable alternatives) — the focal Skeptic on chosen is cheaper than re-running the entire deliberation

### Workflow
1. Run the full base mode (any: Sequential / Parallel / Dialectic / Trias) → produces `chosen`, `confidence`, intermediate report
2. If `confidence ∈ [0.5, 0.7]` (auto) or the `--skeptic-on-chosen` flag is active, dispatch 1 Sonnet 4.6 sub-agent with `prompts/voices/skeptic.md` inline + minimal input:
   ```
   chosen: <id, summary, sketch, rationale>
   success_criterion: <the testable sentence>
   verification: <the command>
   ```
   DO NOT pass other candidates, scores, or deliberation logs.
3. Validate the skeptic output:
   - `can_object: true` with `concrete_concerns` ≥ 2 OR `quoted_scenario` non-null → accept
   - `can_object: true` without evidence → reject (schema fail), ship the original chosen
   - `can_object: false` → ship the original chosen, log that there is no concrete objection
4. Log the result in `deliberation_log` with step `"skeptic_on_chosen"` and set flag `skeptic_caught_constraint: true|false` in the report
5. Apply override semantics (section below)

### Override semantics
**Advisory by default.** The Skeptic's verdict is logged in `deliberation_log` as an entry with step `"skeptic_on_chosen"` and flag `skeptic_caught_constraint: true|false`. `chosen` is **not replaced** — it stays as produced by the base mode. The user sees the objection in the report and can act or ignore.

**Opt-in override via `--skeptic-can-override`.** If the flag is active AND Skeptic produces `addressable: requires_redesign`, the Skeptic's verdict supersedes `chosen`: the orchestrator presents the report's alternatives to the user and asks whether to change the choice. If Skeptic produces `addressable: in_place`, the override does not apply (advisory remains); if it produces `addressable: unaddressable` with `failure_mode: meta_scope_mismatch`, the report is marked `misapplied`.

Summary table:

| Skeptic output | Advisory (default) | With `--skeptic-can-override` |
|---|---|---|
| `can_object: false` | ship original chosen | ship original chosen |
| `in_place` | log + note in report | log + note in report (no override) |
| `requires_redesign` | log + advisory | orchestrator proposes alternatives |
| `unaddressable / meta_scope_mismatch` | mark `misapplied` | mark `misapplied` |

### Skip if
- Confidence ≥ 0.7 and the `--skeptic-on-chosen` flag is not manually active — the Skeptic has no structural motivation to find anything
- Confidence < 0.5 — the band is too low for a single challenger voice; escalate to Trias or the user directly
- Diff is intrinsically high-stakes (auth, migrations, security) — use full Trias with justified cost

**Empirical origin.** The mode emerged from the analysis in `experiments/p3-car-wash.html`: `chosen_confirmation_pass` (the conceptual equivalent of this flag) reached 100% catch-rate in simulation and 4/7 in real reruns on P3 car wash — performance superior to any other mode tested. Mechanism: a single skeptic voice on `chosen` post-hoc forces a re-reading of success_criterion and the detection of implicit constraints missed by all the voices in Pass-1.

## Senate mode (`senate`)

**Scope:** `senate` has two invocation modes:
1. **Default (skill audit):** audits modifications to the skill itself (prompts, scripts, architecture, SKILL.md). Well-tested, gate-validated.
2. **`--on-code` (EXPERIMENTAL_DRAFT):** audits decisions on user code (PRs, refactors, architectural decisions) via `prompts/lenses/domain_lens.md#code_domain`. The orchestrator MUST pre-compute `diff`, `files_touched`, `success_criterion`, `magnitude`, `reversibility`, `blast_radius` before dispatch (see `scripts/dispatch_senate_on_code.py`). NOT wired into the dispatch table until the empirical gate is met (see Drafts footnote at the end of the Senate mode section).

**Mechanics:** 9 sub-agents in a parallel first round + (optional) multi-round cross-questions, each with its prompt from `prompts/senators/`:

| Senator | Specialty | Default model |
|---|---|---|
| Wittgenstein | vague terms, testable definitions | Sonnet |
| Aurelius | reversibility × magnitude, cost/stake proportionality | Sonnet |
| Confucius | authority, precedents in `runs/` + `experiments/` | Sonnet |
| Socrate | undeclared load-bearing premises | Sonnet |
| Musk | aggressive deletion + 10% add-back | Sonnet |
| Dimon | stress test, counterparty, silent failure modes | Sonnet |
| Napoleon | tokens, hours, operator state | Sonnet |
| Deming | statistical discipline, n/variance/calibration | Sonnet |
| Tacitus | retrospective accuracy tracking over `runs/senate/` × `FEEDBACK.html` | **Opus** (per frontmatter — multi-document evidence reconstruction) |

**Cost:** 9 sub-agents (~3× Parallel). On-demand only — no automatic trigger.

**Deep reference:** the workflow steps 1-8, Laws 1-8, MIN_ACTIVE_VOTES, headless invariants, Pilot B context injection, smoke test, and origin notes have been extracted to [`docs/senate.md`](docs/senate.md) to keep SKILL.md focused on the cross-mode contract. Read that file before invoking Senate the first time, or before editing any senator prompt.

### Law 9 — Senate scope

**§1 — When Senate is the right tool** (routing boundary)

| Decision profile | Mode |
|---|---|
| `reversibility=irreversible` OR `magnitude=critical` AND change spans ≥2 architectural layers | `senate --on-code` (*) |
| `confidence ∈ [0.5, 0.7]` from standard mode AND single drift concern | `dialectic + skeptic_on_chosen` |
| 2+ plausible architectural approaches without clear winner | `trias` |
| Bugfix evident OR diff <20 lines / 1 file | Sequential (scope_gate skips) |
| All other PR-level reviews | Sequential / Parallel auto cross-check |

> **(*) Pre-gate caveat — EXPERIMENTAL_DRAFT phase only.** `senate --on-code` routing applies ONLY to pilot dispatches explicitly designated for gate evidence. During the empirical gate phase (≥3 pilot runs required), production critical/irreversible decisions MUST be routed to `trias` or `dialectic + skeptic_on_chosen` (gate-validated modes). Pilots intentionally target the high-stakes profile for falsification evidence but are NOT a substitute for production audits until gate criteria met (≥7/10 info-add over Trias AND `semantic_suspect` ≤20%). This caveat is removed from SKILL.md upon successful gate promotion.

**§2 — Skip Senate if** (negative scope)

- The change is on standard deliberation, not on the skill, AND does not satisfy §1 criteria → use `parallel` / `dialectic` / etc.
- The change is trivial-textual (typo, internal rename, doc fix) — cost-prohibitive
- User explicitly declines

> EXPERIMENTAL_DRAFT footnote, senator context injection (Pilot B), smoke test, and origin notes live in [`docs/senate.md`](docs/senate.md).

<!-- === RUND2 === -->
## Three-layer architecture (RUND2)

| Layer | Components | Role |
|---|---|---|
| **Deliberation** | Conservator → Generator → Control (sequential) | Runs on every user question |
| **Aggregation** | aggregate_rund2() with 8-component veto cascade | Synthesizes voice outputs, decides what user sees |
| **Senate** | 9 senators (Wittgenstein, Aurelius, Confucius, Socrate, Musk, Dimon, Napoleon, Deming, Tacitus) | On-demand audit of proposed changes to consilium itself |

## Sequential dispatch (RUND2)

Default order: **Conservator → Generator → Control**

`strip_context.py` applies ONLY in Sequential mode (Steps 3-4) — Parallel dispatches sub-agents in isolation and does not use it.

1. Conservator sets `tokens_budget` and `irreversibility_flag`
2. Generator receives `magnitude`, `counterparty_risks`, `tokens_budget.generator` (NOT `meta_recommendation`)
3. Control receives full outputs from both Conservator and Generator

**Role separation, not Chinese wall.** Sequential runs the same LLM playing three roles in the same context window; `strip_context.py` strips the prior voice's prompt, but does not clear the model's in-context memory. This is a known, deliberate limitation — role prompts provide separation, not true isolation. True isolation requires Parallel sub-agents.

Auto-parallel cross-check: triggered only when Conservator outputs `magnitude: critical` AND `reversibility: irreversible`. Not user-selectable.

Silent audit: every 20 runs, parallel mode runs silently alongside sequential. If systematic divergence detected → audit frequency increases to 1/5.

## Veto powers (RUND2)

The 8 design components (per spec): vocabulary_map, length_targets, priority_veto_order, tension_expose, metadata, user_profile, multi_confidence, escalation_rule. The `aggregate_rund2()` function produces 7 distinct routing outcomes derived from these components: `BLOCK` (glossary_fail), `BLOCK` (irreversibility), `REWORK`, `ADAPT_SHORT`, `ADAPT_EXTENDED`, `ESCALATE` (3+ triggers), `AGGREGATE` (default).

| Trigger | Source | Effect | Action |
|---|---|---|---|
| `irreversibility_flag: true` | Conservator | BLOCK (hard) | Ask user for explicit consent before Generator |
| `glossary_fail: true` | Control | BLOCK (soft) | Ask user to reformulate with operational terms |
| `disagreements: substantial` | Control | REWORK | Re-run Generator with clarification context |
| `meta_recommendation: scale_down` | Conservator | ADAPT_SHORT | Short path: max 2 candidates, 2-sentence output |
| `meta_recommendation: scale_up` | Conservator | ADAPT_EXTENDED | Warn user, add context before Generator |
| 3+ of above simultaneously | Aggregator | ESCALATE | Present trigger table to user, request decision |

Veto budget for `meta_recommendation`: 5 activations of `scale_up` or `scale_down` per month. On exhaustion → soft warning only, not blocking.

<!-- === END RUND2 === -->
