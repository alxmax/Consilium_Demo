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

### Pipeline at a glance

| Stage | Name | Steps |
|-------|------|-------|
| 1 | Setup | **0** Bootstrap · **1** Gather & Goal · **1.5** Scope Gate |
| 2 | Conservator | **2** Risk assessment (runs FIRST) |
| 3 | Voices | **3** Generator · **4** Control |
| 4 | Aggregate | **5** Aggregate · **5b** Confidence · **5c** Meta-critic (advisory) · **5d** Retry (optional) |
| 5 | Output | **6** Report · **7** Auto-pipeline |

Steps **5b, 5c, 5d** are sub-steps within Stage 4: **5b** (confidence) is mandatory; **5c** (meta-critic) is advisory and never blocks; **5d** (retry) runs only when confidence < 0.7 and `chosen` is non-null — skipped in headless mode.

**Pipeline Invariants:**

| Step(s) | Status |
|---------|--------|
| 0 · 1 · 2 · 5 · 5b · 6 | mandatory |
| 1.5 | auto — scope gate, fails open; skippable for non-diff tasks |
| 5c | advisory, never blocks |
| 5d | conditional — only when `confidence < 0.7` and `chosen` non-null, non-headless |
| 7 | **auto-dispatch** when prompt declares deliverables (no confirmation); opt-in otherwise |

---

## Stage 1 — Setup

### 0. Bootstrap (before any grep / Read on the codebase)
Two actions in order:

1. **Read the contracts required by the mode** — minimum 3 core voices: `prompts/voices/generator.md`, `prompts/voices/control.md`, `prompts/voices/conservator.md`. Dialectic also reads `*_pass2.md` (`generator_pass2.md`, `control_pass2.md`, `conservator_pass2.md`); Trias also reads `<personality>_lens.md` (`pioneer_lens.md`, `architect_lens.md`, `steward_lens.md`); skeptic modes also read `prompts/voices/skeptic.md`. They define the exact fields produced by each voice. **Parallel/dialectic note:** the content of each prompt must be *inlined* into the sub-agent dispatch — reading at Step 0 is not enough. **Also:** if running a non-default mode, read `modes/<mode>.md` for the full mode workflow and machine-readable config (subagents, cost_multiplier, confidence_floor).
2. **Run `python scripts/priors.py --label "<short task label>"`** — returns soft priors from `FEEDBACK.html` + `runs/`. The `--label` flag also checks for a prior authoritative run matching this task (see **Prior-deliberation passthrough** below). Three fields can block the current deliberation until resolved:
   - `stale_pendings` non-empty (PEND older than 2 days): ask *"You have N old PEND entries: [date | chosen] × N. Want me to close them (OK/BAD/skip)?"* — update via `mark_outcome.py --date <d> --chosen <id> --outcome OK|BAD` (preferred) or via `Edit` directly on `FEEDBACK.html`. **Do not** use `log_feedback.py` — it duplicates the row. **Headless** (`is_headless()`): log `[priors] stale_pendings: N entries — skipping prompt` to stderr and continue without asking.
   - `missing_feedback_runs` non-empty: run `python scripts/audit_feedback.py --backfill` to create PEND entries for orphan runs, then resolve them as above. If the list is larger than 3, prefer to resolve the gap *before* starting a new deliberation. **Headless**: run `audit_feedback.py --backfill` automatically and continue.
   - `pend_pressure > 0.3` (PEND ratio in the last N=20 entries — threshold lowered from 0.5): soft alert *"{pend_count}/{window_size} recent entries are PEND — consider closing them?"* — do not block, but record the signal. **Headless**: log only, no prompt.

   **Headless (non-interactive — `claude -p` or CI):** `stale_pendings` and `missing_feedback_runs` are automatically suppressed (returned `[]`) when `sys.stdin.isatty()` is `False`. Explicit override: `--headless` flag or `CONSILIUM_HEADLESS=1` env var. Output includes `headless_mode: true` as a marker for consumers.

   **Prior-deliberation passthrough.** If `priors.py --label` returns a non-null `prior_deliberation_match` field, a recent authoritative FEEDBACK entry (outcome OK or GO, within 30 days) matches this task by label substring. Present it to the user:
   > *"Prior deliberation found: `<match.chosen>` (`<match.date>`, outcome=`<match.outcome>`). Proceed directly to implementation without re-deliberating?"*
   
   - **YES** → skip Steps 1–5 entirely; build a passthrough report and go to Step 7:
     ```json
     {
       "success_criterion": "<current task>",
       "chosen_approach": "prior-deliberation",
       "verification": "manual — implement per prior run's chosen_approach",
       "alternatives": [],
       "voice_scores": null,
       "confidence": 0.90,
       "deliberation_log": [{"step": "prior_deliberation_passthrough", "matched": "<match.chosen>", "date": "<match.date>"}],
       "telemetry": {"mode": "prior_deliberation_passthrough", "dispatch_count": 0}
     }
     ```
   - **NO** → continue with the full pipeline from Step 1.
   - **Headless:** skip the prompt; continue with the full pipeline (do not auto-passthrough headlessly).
   - **`CONSILIUM_FORCE_FULL=1`:** always run the full pipeline regardless of match.
   - **Falsification criterion:** if passthrough fires on a case that later gets outcome=BAD, tighten the `--label` value used or add specificity to the task description.

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

## Stage 2 — Conservator

### 2. Conservator — assess risk (runs FIRST)
Use `prompts/voices/conservator.md`. Runs **before** Generator and Control. Its output sets the `tokens_budget` for the other voices.

Required Questions (Q1-Q5): reversibility, magnitude, counterparty_risks, status quo bias check, meta_recommendation.

Output per candidate: `{id, regression_risk: {reversibility, magnitude, net_concern}, counterparty_risks, bias_check, meta_recommendation, tokens_budget: {generator, control}, irreversibility_flag, rollback_recipe, notes}`.

**Categorical flip caveat:** Conservator `magnitude`/`reversibility` labels have a ~40% inter-run flip rate on ambiguous inputs (experiment 2026-05-17). If the deliberation is sensitive to the magnitude/reversibility boundary, consider double-sampling.

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
  `confidence: 0.85` is deliberate — Conservator's judgment is the signal, not a weak guess. Designed to stay above the `[0.0, 0.7]` skeptic auto-trigger band.
- If `meta_recommendation: scale_up` → warn user, add context request before Generator. **Headless**: warning emitted to stderr, the context cannot be requested interactively — continue with existing input.

**Optional — autoprobe:**
```bash
python scripts/probe_change.py                       # working tree vs HEAD
python scripts/probe_change.py --ref main --churn 30 # + commit count per file last 30 days
```
Anchor `magnitude` to `files_changed/lines_*` and `regression_risk.net_concern` to the churn distribution when present.

## Stage 3 — Voices

### 3. Generator — produce alternatives
Use `prompts/voices/generator.md`. Request **3–5 candidates** (including `do_nothing` and any `adversarial_*` — they count toward the budget), including `do_nothing`. Divergent style. Respect `tokens_budget.generator` set by Conservator.

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

## Stage 4 — Aggregate

### 5. Aggregate
```bash
python scripts/aggregator.py --scheme conservative_override
```
Default: **conservative_override** — veto at `risk_score > 0.8` (strictly greater — `risk_score = 0.80` is NOT vetoed; `0.81` IS); ranking by weighted average `(generator + control + safety)` where `safety = 1 - conservator`. On a tie, the safer candidate wins. Alternative: `--scheme risk_adjusted_utility` (sigmoid penalty, no rigid veto). **Veto threshold caveat:** the 0.8 boundary has not been empirically validated in the [0.7, 0.9] region — boundary cases may fire non-deterministically until a follow-up stability experiment closes that gap (see `experiments/voice-score-stability-2026-05-17.md` F4). **All schemes + input shapes: [modes/aggregator_schemes.md](modes/aggregator_schemes.md).**

### 5b. Confidence
```bash
echo '{"candidates": [...], "chosen": "approach_id"}' | python scripts/confidence.py
```
Returns `{confidence, agreement, separation}`. If `chosen` is `null` (all candidates vetoed), the `confidence` field in the response is `null`. Step 5d is skipped in this case — `retry_context.py` is not run when no candidate survived aggregation. **Formula, vote-pattern path, mode floors, calibration caveat: [modes/confidence.md](modes/confidence.md).**

> **Calibration (R2 audit 2026-05-17):** `agreement` measures divergence between roles within ONE run — not inter-run stability. Conservator scores are anchored by categorical formula (see `conservator.md`); Generator/Control scores are unanchored self-assigned floats. A second run with the same input may produce different scores (pstdev estimated 0.12–0.18 on `risk_score`). The `confidence` value is not a calibrated probability — it is an internal-consistency signal.

**Quoting:** Avoid building inline Python via `-c "..."` with JSON payload — apostrophes in the code can break bash quoting. Use stdin piping (as above) or the `--input <file>` flag.

**Mode confidence floor (E1).** After confidence is derived, check whether the mode reached the minimum floor:
```python
from scripts.confidence import check_mode_floor
result = check_mode_floor(telemetry_mode, confidence_value)
# result["below_floor"] == True → log with --outcome WEAK in FEEDBACK.html
```
Floors: `sequential=0.70`, `dialectic=0.75`, `trias=0.80`. A run below floor signals the mode did not deliver value for the cost. The data accumulates in `FEEDBACK.html` — the pattern becomes visible after ≥10 runs per mode.

### 5c. Meta-critic (auto, advisory) — *retired 2026-05-25*
```bash
cat bundle.json | python scripts/deprecated/meta_critic.py
```
Scores **deliberation quality** (not choice correctness). Retained metric: `conservator_spread` (shrug?). Dead metrics `generator_divergence` and `control_concreteness` removed (0/163 fires). Emits `deliberation_quality.flags` — attach to the bundle before Step 6 (build_report passes it through to the report). Non-empty `flags` do not block. Senate verdict: MODIFY (GO 5 · MODIFY 3 · STOP 1, 2026-05-24 `kill-meta-critic-r2`) — trimmed to conservator_spread only, moved to deprecated/. Substance-validation gap accepted as a known limitation (see TODO.md).

### 5d. Retry on low confidence (optional, single pass)
If `confidence < 0.7`, **before** asking the user:
```bash
cat bundle.json | python scripts/retry_context.py
```
Returns the top-2 candidates with files/symbols to read/grep. Use the hints → gather context (Read + Grep) → re-run Generator/Control/Conservator **once** with enriched input. If confidence is still < 0.7, only then ask the user (Step 6).

**Headless** (`is_headless()`): skip Step 5d entirely — go directly to Step 6 where `PEND_HEADLESS` is logged. Empirical note: `retry_context.py` has zero labeled usage in the `runs/` corpus (see senate audit `2026-05-16_220025-flow-and-modes-audit-r2`); skipping in headless is aligned with that deletion-vote and does not lose an active mechanism.

## Stage 5 — Output

### 6. Report

**Telemetry emission (mandatory — before `build_report.py`).**

At each dispatch (voice), immediately after return, accumulate in the bundle:

- `telemetry.voices.<voice_name>`: `{tokens_in: ceil(len(prompt)/4), tokens_out: ceil(len(response)/4), latency_ms: <wall-clock>}` — prompt = full text sent (persona + context + proposal, not just the proposal).
- Sum tokens + latency per voice if there are retries on the same dispatch.
- `telemetry.mode` ← canonical label (`"sequential"`, `"trias"` etc. — from `## Dispatch defaults`).
- `telemetry.dispatch_count` ← total dispatches (including retries).

Why mandatory: `scripts/efficiency.py` returns `null` for any run without telemetry, polluting per-mode averages — a run without telemetry is invisible in efficiency comparisons.

```bash
cat bundle.json | python scripts/build_report.py | python scripts/validate_report.py
```
Bundle schema: `{success_criterion, verification, generator, control, conservator, aggregate, confidence, telemetry}`. `build_report.py` derives `voice_scores`, assembles `alternatives` (with `why_not`) and `deliberation_log`. (`voice_scores` is derived by `build_report.py` from voice outputs — it is not emitted by the voices directly.)

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
chosen: <id> | conf: <X> | .consilium/runs/<file>.json
```

**Validation gate** (mandatory before considering the report final):
```bash
cat .consilium/runs/<file>.json | python scripts/validate_report.py
```
Exit 0 = OK. Exit 1 = missing/empty field or malformed telemetry. Exit 2 = malformed JSON.

**Final actions (mandatory — deliberation is not complete without them):**

The two calls below are **mandatory**. If the orchestrator stops before running them, the report exists on disk but is invisible to priors → the next deliberation will not benefit from this feedback. Periodic audit: `python scripts/audit_feedback.py` lists orphan runs; with `--backfill` it adds default PEND rows.

1. **Persist the report** in `.consilium/runs/YYYY-MM-DD_HHMM_<label>.json`.
2. **Log to `.consilium/FEEDBACK.html`** (confidence-gated, without skipping any case):
   - `confidence >= 0.7` → `python -X utf8 scripts/log_feedback.py --outcome OK --run-path .consilium/runs/<file>.json < .consilium/runs/<file>.json`
   - `confidence < 0.7` → ask: *"Confidence below threshold (`<X>`). Want to override `<chosen>`? Alternatives: `<alt_ids>`. Reply alt_id, 'no', or 'skip'."* Then: `no` → `--outcome OK --force-override`; `<alt_id>` → `--outcome OVR --override-target <alt_id>`; `skip` → no flag (PEND, but **do not let the call be skipped**).
   - `confidence null` (all vetoed) → `python -X utf8 scripts/log_feedback.py --run-path .consilium/runs/<file>.json < .consilium/runs/<file>.json`
   - **Non-interactive path (headless — `claude -p`).** Skip the prompt at `confidence < 0.7` and call directly: `python -X utf8 scripts/log_feedback.py --outcome PEND_HEADLESS --run-path .consilium/runs/<file>.json < .consilium/runs/<file>.json`. `PEND_HEADLESS` is structurally excluded from `pend_pressure` and `stale_pendings` (PEND_HEADLESS ≠ "PEND" in Counter) — it requires no manual resolution.

**Outcome confirmation (retroactive).** The outcome logged in step 2 is subjective — it reflects the immediate impression. If production later reveals a regression or a good choice, overwrite it with the confirmed marker:
```bash
python scripts/mark_outcome.py --run-path .consilium/runs/<file>.json --outcome BAD --reason "broke prod migration"
```
The `[confirmed]` marker appears in the note; `priors.py` weights these rows 2x compared to subjective feedback (see `weighted_bad_rate`).

**Scale_down regret tracking (A2).** If `telemetry.mode == "sequential_scale_down"` and the retroactive outcome is `BAD`:
```bash
python scripts/mark_outcome.py --run-path .consilium/runs/<file>.json --outcome BAD --reason "scale_down regret — full deliberation needed"
```
Calibration signal: if `scale_down` regret rate > 10% over n≥20 runs, Conservator's scale_down threshold is too aggressive — adjust the prompt. If the rate stays < 5%, the optimization is validated.

### 7. Auto-pipeline (post-report)

**Mandatory — auto-dispatch (no confirmation prompt) if the user's prompt contains a header of the form `**Required output file(s):**` or `**Deliverable(s):**` (with or without colon, singular or plural) — authoritative detection regex: `\*\*\s*(?:Required\s+output\s+files?|Deliverables?)\s*\*\*\s*:?` applied per whole line, case-insensitive.** In this case Step 7 fires automatically after Step 6 completes:

```
Agent(subagent_type="consilium-implement-subagent",
      prompt="Implement the chosen approach from .consilium/runs/<file>.json. Spec is the report.")
```

**Preconditions (skip with visible error if not met):** `chosen_approach` ∉ `{do_nothing, skipped}` AND `success_criterion` non-empty AND `verification` non-empty. If either precondition fails, emit an error in the response and stop — do not dispatch.

**Mode-agnostic:** the dispatch is identical regardless of whether the deliberation ran as sequential, dialectic, or trias. The report JSON (validated by `validate_report.py`) is the spec; the subagent handles routing internally via `recommend_implement_mode()` (single-shot for greenfield, Coder→Test Writer∥Reviewer pipeline for regression-risk quadrants). Files must exist on disk before the turn closes.

**Opt-in otherwise** — when the prompt does not declare deliverables (audit, "should I commit", "which approach", "before implementing"-without-code-required), Step 7 is at the user's discretion. When the user confirms, dispatch via the same `Agent(subagent_type="consilium-implement-subagent", ...)` call above.

After Step 6 is complete (report saved, feedback logged), infer and confirm the implementation steps:

```bash
cat .consilium/runs/<file>.json | python scripts/infer_pipeline.py          # interactive
python scripts/infer_pipeline.py --input .consilium/runs/<file>.json --yes  # CI/headless
python scripts/infer_pipeline.py --input .consilium/runs/<file>.json --dry-run  # print only
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

Reject (`n` at prompt) → rejection logged in `.consilium/runs/YYYY-MM-DD_HHMM_pipeline_rejected.json`. Rerun with `--yes` for CI or `--dry-run` for audit without confirmation.

**Skip Step 7 if:** `chosen_approach` is `do_nothing` or `skipped` (the script exits with exit 1 and a clear message). In headless context (`claude -p`), run with `--yes` (non-interactive, no confirmation prompt).

**The skip does NOT apply to the mandatory requirement above:** if the prompt declares deliverables (per the authoritative regex from the mandatory clause above) and you nonetheless arrive at `chosen=do_nothing`, that means the deliberation rejected the implementation of an explicit user request — a case that requires a visible signal (hard error in the response: *"deliberation chose `do_nothing` on a prompt with declared deliverables — the user must decide"*), not silent skip.

#### Implementation pipeline (default for regression-risk changes)

**Full spec: [modes/implement_pipeline.md](modes/implement_pipeline.md).**

The default `implement` step writes code single-shot for greenfield. For **regression-risk changes** (refactor, bugfix, multi-path behavior change on existing code), a 3-role pipeline is the default: **Coder → (Test Writer ∥ Reviewer)**, where the report *is* the spec (`chosen_approach` + `success_criterion` + `verification`). The Reviewer reuses the **Control voice** (`prompts/voices/control.md`) on the *written* code — no separate reviewer prompt.

**Routing gate (single-shot vs pipeline).** `recommend_implement_mode(report)` in `infer_pipeline.py` picks the mode, keyed on **regression risk, not size**: it returns `"pipeline"` when the change warrants a `review` step (the regression-prone quadrants — `moderate×irreversible`, `high×{partial,irreversible}`, `critical×any`), else `"single_shot"`. Greenfield (even large, fully reversible) stays single-shot. **Opt-out:** the routing decision is advisory — the user may override at the Step 7 prompt (press `n`) or by passing `--dry-run` to inspect before committing.

```bash
python -X utf8 scripts/implement_pipeline.py --input .consilium/runs/<file>.json --dry-run   # print dispatch plan
python -X utf8 scripts/implement_pipeline.py --verify-gate --test-cmd "pytest -x" --target <impl_file>
```

Dispatch via `Agent(subagent_type="consilium-implement-subagent", ...)` (see `agents/consilium-implement-subagent.md`). Invariants enforced by the vehicle: **disjoint-path ownership** (Coder writes impl, Test Writer writes `test_*`, Reviewer read-only → collision-free parallel stage), **malformed-JSON hard-fail** (retry once, then abort — never a silent-empty manifest), and the **red→green gate** (a test that passes against a `raise NotImplementedError` stub is rejected).

> **Status: promoted to default for regression-risk changes (2026-05-25).** Combined benchmark R1+R2 (n=6, hidden oracle; see `experiments/pipeline-bench/RESULTS.md`): pipeline **1 win / 5 ties / 0 losses** vs plain single-shot `implement`, at ~1.1× tokens / 3–7× wall-clock. The win was a **refactor with a semantically-isolated secondary branch** (review caught a second-code-path defect the single-shot shipped); on greenfield and algebraically-obvious tasks the base model already nailed the edges (ties). Graduation criterion (≥2/3 wins) not met — promoted on user decision. Audit trail: `runs/2026-05-25_2140_pipeline-step7-default.json` + `experiments/pipeline-bench/`.

### Observe → Think → Act → Learn (descriptive framing)

**This section is descriptive only.** It does not create new behavioral contracts; Steps 0–7 above remain the authoritative workflow. The mapping below is a reading aid for contributors who arrive expecting an Observe–Think–Act–Learn shape — it names what is already present without prescribing anything new.

| OTAL phase | Alias | Step(s) | Script(s) that implement the phase |
|---|---|---|---|
| **Observe** | **EXPLORE** | Step 0 + Step 1 | `priors.py` (reads `FEEDBACK.html` + `runs/*.json`); orchestrator gathers context from the codebase |
| **Think**   | — | Steps 2–5     | `aggregator.py`, `confidence.py`, `meta_critic.py`; Conservator → Generator → Control voices |
| **Act**     | **COMMIT** | Step 6 + Step 7 | `validate_report.py`, `build_report.py` (write `.consilium/runs/<file>.json`); `infer_pipeline.py` (write code) |
| **Learn**   | — | Step 6 final action + retroactive | `log_feedback.py` (append to `FEEDBACK.html`); `mark_outcome.py` (retroactive `[confirmed]` weighting) |

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
    │    │  → .consilium/runs/<file>.json             │
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

**Calibration note (Learn phase).** The Learn phase is presently *partial* in a structural sense: `log_feedback.py` writes outcomes into `.consilium/FEEDBACK.html` (HTML rows), but `.consilium/runs/<file>.json` does not carry a structured `outcome` field. Consequently `priors.py` reads outcomes from the HTML journal, not from a typed JSON field. The loop closes via the journal — naming the gap explicitly so future readers don't assume an unwired feedback channel exists.

**What this framing is not.** This section does not introduce iteration triggers beyond Step 5d's `retry_context.py`, does not name a meta-controller, and does not authorize voices or aggregator to cite "OTAL step X" as ground for new behavior. If a future proposal seeks behavioral iteration triggers (e.g. firing a second pass on `meta_critic.generator_divergence < 0.4`), that requires its own Senate audit with empirical pilot data — `generator_divergence` currently has zero labeled triggering events in `runs/`, so any threshold would be uncalibrated. A dynamic meta-controller is explicitly out of scope: its TODO precondition (item #16) was dropped in triage, and recursive routing contradicts Constitution Principle 2 (Simplicity first).

> **TODO #18 closure rationale** (2026-05-19 Senate audit, `runs/senate/2026-05-19_214850-todo-18-otal-formalization.json`, MODIFY 0-8-1): 8 of 9 senators converged on docs-only framing. Level 2 (iteration triggers) deferred until ≥3 PEND rows in `FEEDBACK.html` demonstrate the current `confidence<0.7` retry underperforms. Level 3 (meta-controller) closed pending #16's revival.

## Skill maintenance

Apply only when editing the skill (`scripts/*.py`, `prompts/*.md`, `SKILL.md`), not at every deliberation.

**Eval harness** — when editing `aggregator.py`, `confidence.py`, `validate_report.py`, `strip_context.py`, or `personalities.py`:
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
| `scripts/aggregator.py` | 5 aggregation schemes + auto-relax on total veto (Step 5); reference: `modes/aggregator_schemes.md` |
| `scripts/confidence.py` | Derives confidence from variance + separation (Step 5b); reference: `modes/confidence.md` |
| `scripts/deprecated/meta_critic.py` | Deliberation quality score (conservator_spread only) — Step 5c retired 2026-05-25 |
| `scripts/retry_context.py` | Hint for single retry when confidence < 0.7 — Step 5d |
| `scripts/build_report.py` | Assemble the canonical report from the bundle (Step 6) |
| `scripts/validate_report.py` | Principle #4 gate: success_criterion + verification + chosen_approach |
| `scripts/log_feedback.py` | Auto-append to FEEDBACK.html at the end of Step 6 |
| `scripts/mark_outcome.py` | Retroactive outcome overwrite (`[confirmed]` in note → 2x weight) |
| `scripts/infer_pipeline.py` | Step 7: infer + confirm implementation steps from the report; `--dry-run` / `--yes` |
| `scripts/implement_pipeline.py` | Step 7: plan the Coder→(Test Writer∥Reviewer) dispatch + red→green gate verifier; default for regression-risk changes; `--dry-run` / `--verify-gate` |
| `agents/consilium-implement-subagent.md` | Vehicle for the implementation pipeline; default for regression-risk changes (Step 7); returns a file manifest + Control verdict |
| `prompts/implement/{coder,test_writer}.md` | Implementation pipeline role templates (Reviewer reuses `prompts/voices/control.md`) |
| `modes/implement_pipeline.md` | Machine-readable config + full spec for the implementation pipeline (roles, routing, invariants, red→green gate, benchmark) |
| `scripts/audit_feedback.py` | List runs without FB row; with `--backfill` adds default PEND |
| `scripts/memory.py` | Uniform read API over the 3 tiers (short/medium/long) |
| `scripts/strip_context.py` | Project previous voice's output to minimum (Steps 3-4 sequential) |
| `scripts/deprecated/dialectic_merge.py` | *(Deprecated — Pass-1+Pass-2 merge for old Dialectic mode; also handled `silently_dropped` candidate recovery for candidates the Pass-2 generator omitted without explicit rejection)* |
| `scripts/personalities.py` | Trias mode — 3 fixed personalities with weights + lens paths |
| `prompts/voices/skeptic.md` | Focal voice for the `skeptic_on_chosen` flag (composable over any mode) — receives only the chosen, produces a concrete objection or `meta_scope_mismatch` |
| `scripts/run_evals.py` + `evals/scenarios.json` | Regression suite for deterministic scripts |
| `scripts/usage.py` | Telemetry rollup from runs/ |
| `agents/consilium-subagent.md` | Subagent for isolated invocation via `Agent(subagent_type="consilium-subagent", ...)` |
| `scripts/vocabulary_map.py` | User-facing translations (reversibility/magnitude/meta_recommendation/verdict) + `compute_tokens_budget(magnitude, reversibility, meta)` |

## COMMIT workflow (post-implementation, descriptive)

**Descriptive only** — no new behavioral contract in Steps 0–7. The authoritative git rules are in `CLAUDE.md` (branch naming, one-commit-per-branch, auto-push, Conventional Commits format).

Standard 5-step sequence: `git checkout main && git pull` → `git checkout -b feat/<slug>` → implement → `git add` → `git commit -m "feat(scope): description"` → `git push -u origin <branch>`.

Automation: `.claude/settings.json` `Stop` hook detects uncommitted changes on `feat/*`/`fix/*` branches after each turn and prompts Claude to complete the workflow. `scripts/commit.ps1 -Message "..."` handles Steps 3–5 (stage → commit → push); `-Amend` flag for subsequent changes on the same branch.

## Feedback loop

All deliberation state lives under **`.consilium/`** at the repo root (gitignored; the single data directory). Paths are centralized in `scripts/utils.py` (`DATA_DIR`/`RUNS_DIR`/`FEEDBACK_PATH`) — scripts import them as defaults, `--runs-dir`/`--feedback` still override.

- **`.consilium/runs/`** — JSON per deliberation in `.consilium/runs/YYYY-MM-DD_HHMM_<label>.json` (schema in `docs/runs-schema.md`). Read by `priors.py` (Step 0), `usage.py`, `feedback.py`. Run-paths are stored relative to `.consilium/` (key `runs/<file>.json`); `--run-path` accepts any spelling (`.consilium/runs/<f>.json`, `runs/<f>.json`, absolute) and `utils.canonical_run_path` normalizes it to that key.
- **`.consilium/FEEDBACK.html`** — one line per use: `date | context | chosen | outcome | note`. Outcome: `OK`, `BAD`, `OVR`, `PEND`. **Drill-down:** when `log_feedback.py` appends, existing rows lose drill-down; use `scripts/deprecated/migrate_feedback_md_to_html.py` for bulk re-population (retired one-shot tool, see scripts/deprecated/).
- **Confirmed outcome.** `mark_outcome.py` adds the `[confirmed]` marker in note. `priors.py` weights these rows 2x in `weighted_bad_rate`. Use when production reality contradicts the subjective outcome from Step 6.

## Memory tiers

Consilium has 3 memory layers with different lifecycles. `scripts/memory.py` provides a uniform read API over all three.

| Tier | Location | Lifetime | Content | Read by |
|---|---|---|---|---|
| **Short** | conversation window | session | bundle under construction (Steps 1–5b), clarity gate, current success_criterion | agent only (not persisted) |
| **Medium** | `.consilium/runs/*.json` | indefinite (gitignored) | one file per deliberation; episodic | `priors.py`, `usage.py`, `memory.py`, `audit_feedback.py` |
| **Long** | `.consilium/FEEDBACK.html` + signals from `priors.py` | indefinite | one row per use; aggregated over time | `priors.py`, `feedback.py`, `memory.py`, `mark_outcome.py` |

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

### Pipeline-execution contract (orchestrator-enforced)

Every `/consilium` invocation MUST terminate by writing a report to `.consilium/runs/` — either a real deliberation report, or a `skipped` / `trivial-direct` report (Step 1.5 / scale_down short-circuit). A run that produces **no** report did not execute the pipeline (it answered directly with the skill merely in context — the gap found in the 2026-05-26 benchmark audit, where `consilium_sequential`/`dialectic` collapsed to bare Sonnet).

**Detection is the orchestrator's responsibility, not the skill's.** A guard written as SKILL.md prose ("assert dispatch happened, else warn") is self-defeating: the skip happens *because* the model didn't execute the steps, so it would skip the guard too — a non-executing process cannot run its own self-check (Senate 2026-05-26, `runs/senate/2026-05-26_215328-trias-dialectic-audit-improvements.json`). Therefore the skill does **not** self-enforce headless execution. Instead, any orchestrator that invokes `claude -p` with this skill detects a skipped deliberation by the **absence of a fresh `runs/` report** for the invocation. Reference implementation: `benchmark/run_task.py` `detect_pipeline_execution()` (writes `pipeline_audit.json`; surfaced in `report.html` as a `pipeline: deliberated|skipped` badge). Interactive (non-headless) use is not silent — the operator sees in the transcript whether the pipeline ran.

> Deliberation of record: `.consilium/runs/2026-05-26_2230_live-path-guard.json` (chosen `doc_only_invariant` over a `.claude/settings.json` Stop hook — the hook has a global blast radius and false-positives on correct `trivial-direct` short-circuits, for a benefit confined to third-party headless orchestration).

## Dispatch defaults (per voice)

Default behavior unless overridden by project memory (`MEMORY.md`). All voices pinned to `model: "sonnet"` per `feedback_subagents_sonnet.md`. Mode sections declare per-invocation overrides (e.g. `opus` Generator for high-stakes) — single source of truth per mode, descriptive not enforced.

Cost multipliers (baseline Sequential = 1×): Parallel 3× · Dialectic 1.33× · Trias 3×. The `skeptic_on_chosen` flag adds +1 sub-agent over the base mode (e.g. Sequential+flag = 1.33×, Parallel+flag = 1.33× Parallel).

## Parallel voices mode

> **Lineage.** Mode metadata single-source-of-truth was settled by prior Consilium deliberation `.consilium/runs/2026-05-25_160009-modes-dir-frontmatter-refactor.json` (YAML frontmatter chosen over JSON-manifest codegen). Doc-vs-impl parity for the 4 invariants below is enforced by `scripts/check_doc_drift.py` (Senate audit `runs/senate/2026-05-28_094832-doc-drift-ssot-mode-docs.json`, Track 2).

**Parallel mode removed.** Parallel dispatch is no longer a user-selectable option. Auto-triggered internally only when `magnitude = critical` AND `reversibility = irreversible`, as a cross-check on the sequential result. The "silent parallel audit every 20 runs" claim from earlier docs has **no implementation in `scripts/`** (verified 2026-05-28 via grep); decision pending in TODO.md HIGH PRIORITY — implement-or-remove.

**Legacy reference (auto cross-check only).** Dispatch follows the 2-turn flow below — Generator alone first, then Control + Conservator in parallel with Generator's candidates. This preserves the data dependency (Control needs candidates to verdict, Conservator needs them to assess risk) while isolating each voice in its own context within a turn.

### How (2 turns)
1. **Turn 1:** dispatch Generator (1 Agent call). Wait for candidates.
2. **Turn 2:** dispatch Control + Conservator in parallel (2 Agent calls in the same message), both receiving candidates from Turn 1.
3. Aggregate directly with `scripts/aggregator.py`.

Continue with Step 5b → 5c → 5d → 6; capture tokens/latency per sub-agent dispatch.

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

## Mode files (machine-readable config)

Each mode has its own `.md` file in `modes/` with YAML frontmatter (`name`, `subagents`, `cost_multiplier`, `confidence_floor`, `models`). Scripts read mode parameters from these files — they are the single source of truth for mode config. Read the mode file at Bootstrap (Step 0) before running a non-default mode.

| Mode | File | Subagents | Cost | Conf. floor |
|---|---|---|---|---|
| Sequential (default) | [modes/sequential.md](modes/sequential.md) | 0 | 1× | 0.70 |
| Dialectic | [modes/dialectic.md](modes/dialectic.md) | 1 | 1.33× | 0.75 |
| Trias | [modes/trias.md](modes/trias.md) | 3 (worst: 7) | 3× | 0.80 |
| skeptic_on_chosen (flag) | [modes/skeptic_on_chosen.md](modes/skeptic_on_chosen.md) | +1 over base | base+1 | N/A |

`modes/` also holds reference docs for sub-components (not selectable modes): [implement_pipeline.md](modes/implement_pipeline.md) (Step 7), [aggregator_schemes.md](modes/aggregator_schemes.md) (Step 5), [confidence.md](modes/confidence.md) (Step 5b).

## Dialectic mode — V2 (opt-in, code-specialized)

Sequential + 1 Skeptic sub-agent. Code-context (language, files, test suite, CI gate) injected into voice inputs. `telemetry.mode: "dialectic"`. **Full workflow: [modes/dialectic.md](modes/dialectic.md).**

## Trias mode (high-stakes opt-in)

3 personalities (Pioneer/Architect/Steward), each runs a full Sequential deliberation internally. Lazy routing auto-downgrades to Dialectic for low/medium/high magnitude — only `critical` magnitude (blocklist hits: auth, security, migrations, CI workflows, secrets) proceeds to full Trias. **Cost: 3× Sequential** (worst-case 7× on 1-1-1 deadlock cascade). `trias_split` deprecated — use standard `trias`. **Full workflow: [modes/trias.md](modes/trias.md).**

## Skeptic-on-chosen mode (`skeptic_on_chosen`)

Cross-cutting flag — +1 Skeptic sub-agent over any base mode post-hoc. Auto-triggers when `confidence ∈ [0.0, 0.7]`. Advisory by default; `--skeptic-can-override` for opt-in. **Full workflow: [modes/skeptic_on_chosen.md](modes/skeptic_on_chosen.md).**

## Routing boundary

When to escalate beyond a standard Consilium mode:

| Decision profile | Mode |
|---|---|
| `confidence ∈ [0.0, 0.7]` from standard mode AND single drift concern | `dialectic + skeptic_on_chosen` |
| 2+ plausible architectural approaches without clear winner | `trias` |
| Bugfix evident OR diff <20 lines / 1 file | Sequential (scope_gate skips) |
| All other PR-level reviews | Sequential / Parallel auto cross-check |

## Sequential mode (default)

Default mode. Conservator → Generator → Control run in-context. 0 sub-agent dispatches, 1× cost. **Full reference: [modes/sequential.md](modes/sequential.md).**

Key veto triggers (inline for quick reference during Steps 2–5):

| Trigger | Source | Effect | Action |
|---|---|---|---|
| `irreversibility_flag: true` | Conservator | BLOCK (hard) | Ask user for explicit consent before Generator |
| `glossary_fail: true` | Control | BLOCK (soft) | Ask user to reformulate with operational terms |
| `disagreements: substantial` | Control | REWORK | Re-run Generator with clarification context |
| `meta_recommendation: scale_down` | Conservator | ADAPT_SHORT | Short path: max 2 candidates, 2-sentence output |
| `meta_recommendation: scale_up` | Conservator | ADAPT_EXTENDED | Warn user, add context before Generator |
| 3+ of above simultaneously | Aggregator | ESCALATE | Present trigger table to user, request decision |

Veto budget for `meta_recommendation`: 5 activations of `scale_up` or `scale_down` per month. On exhaustion → soft warning only, not blocking.
