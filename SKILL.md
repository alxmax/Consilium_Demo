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
| 1 | Setup | **0** Bootstrap · **1** Gather & Goal · **1.5** Scope Gate · **1.6** Consent Gate |
| 2 | Generator | **2** Produce alternatives (runs FIRST) |
| 3 | Risk & Verify | **3** Conservator · **4** Control |
| 4 | Aggregate | **5** Aggregate · **5b** Confidence · **5c** Meta-critic (advisory) · **5d** Retry (optional) |
| 5 | Output | **6** Report · **7** Auto-pipeline |

Steps **5b, 5c, 5d** are sub-steps within Stage 4: **5b** (confidence) is mandatory; **5c** (meta-critic) is advisory and never blocks; **5d** (retry) runs only when confidence < 0.7 and `chosen` is non-null — skipped in headless mode.

**Pipeline Invariants:**

| Step(s) | Status |
|---------|--------|
| 0 · 1 · 2 · 3 · 5 · 5b · 6 | mandatory |
| 1.5 | auto — scope gate, fails open; skippable for non-diff tasks |
| 1.6 | auto — consent gate, fails **safe**; pre-dispatch (before Generator) |
| 5c | advisory, never blocks |
| 5d | conditional — only when `confidence < 0.7` and `chosen` non-null, non-headless |
| 7 | **auto-dispatch** when prompt declares deliverables (no confirmation); opt-in otherwise |

---

## Stage 1 — Setup

### 0. Bootstrap (before any grep / Read on the codebase)
Two actions in order:

1. **Read the contracts required by the mode** — minimum 3 core voices: `prompts/voices/generator.md`, `prompts/voices/control.md`, `prompts/voices/conservator.md`. Dialectic also reads `prompts/voices/skeptic.md` (its Skeptic stage); Trias also reads `<personality>_lens.md` (`pioneer_lens.md`, `architect_lens.md`, `steward_lens.md`); skeptic modes also read `prompts/voices/skeptic.md`. They define the exact fields produced by each voice. **Sub-agent dispatch note:** the content of each prompt must be *inlined* into the sub-agent dispatch — reading at Step 0 is not enough. **Also:** if running a non-default mode, read `modes/<mode>.md` for the full mode workflow and machine-readable config (subagents, cost_multiplier, confidence_floor).
2. **Run `python scripts/priors.py --label "<short task label>"`** — returns soft priors from `FEEDBACK.html` + `runs/`. The `--label` flag also checks for a prior authoritative run matching this task (see **Prior-deliberation passthrough** below). Three fields can block the current deliberation until resolved:
   - `stale_pendings` non-empty (PEND older than 2 days): ask *"You have N old PEND entries: [date | chosen] × N. Want me to close them (OK/BAD/skip)?"* — update via `mark_outcome.py --date <d> --chosen <id> --outcome OK|BAD` (preferred) or via `Edit` directly on `FEEDBACK.html`. **Do not** use `log_feedback.py` — it duplicates the row. **Headless** (`is_headless()`): log `[priors] stale_pendings: N entries — skipping prompt` to stderr and continue without asking.
   - `missing_feedback_runs` non-empty: run `python scripts/audit_feedback.py --backfill` to create PEND entries for orphan runs, then resolve them as above. If the list is larger than 3, prefer to resolve the gap *before* starting a new deliberation. **Headless**: run `audit_feedback.py --backfill` automatically and continue.
   - `pend_pressure > 0.3` (PEND ratio in the last N=20 entries — threshold lowered from 0.5): soft alert *"{pend_count}/{window_size} recent entries are PEND — consider closing them?"* — do not block, but record the signal. **Headless**: log only, no prompt.
   - `prompt_drift` non-empty (advisory, **non-blocking**): prompts/ or modes/ changed since the most-recent prior run's `consilium_ref` — surface a one-line note *"{changed_files} prompt/mode file(s) changed since last deliberation ({since_run})"* so the operator knows past comparisons may not be apples-to-apples. Inspect with `python scripts/version.py --drift <since_ref>`. Absent when there is no resolvable prior baseline (older runs predate the stamp) — never blocks.

   **Headless (non-interactive — `claude -p` or CI):** `stale_pendings` and `missing_feedback_runs` are automatically suppressed (returned `[]`) when `sys.stdin.isatty()` is `False`. Explicit override: `--headless` flag or `CONSILIUM_HEADLESS=1` env var. Output includes `headless_mode: true` as a marker for consumers.

   **Prior-deliberation passthrough.** If `priors.py --label` returns a non-null `prior_deliberation_match` field, a recent authoritative FEEDBACK entry (outcome OK, within 30 days) matches this task by label substring. Present it to the user:
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
       "pipeline_executed": false,
       "deliberation_log": [{"step": "prior_deliberation_passthrough", "matched": "<match.chosen>", "date": "<match.date>"}],
       "telemetry": {"mode": "prior_deliberation_passthrough", "dispatch_count": 0, "consilium_version": "<python scripts/version.py>", "consilium_ref": "<python scripts/version.py --ref>"}
     }
     ```
   - **NO** → continue with the full pipeline from Step 1.
   - **Headless:** skip the prompt; continue with the full pipeline (do not auto-passthrough headlessly).
   - **`CONSILIUM_FORCE_FULL=1`:** always run the full pipeline regardless of match.
   - **Falsification criterion:** if passthrough fires on a case that later gets outcome=BAD, tighten the `--label` value used or add specificity to the task description.

   **User-spec passthrough (explicit fiat only).** If the user *explicitly* supplies the approach AND asks to skip deliberation — all three of `chosen_approach` (what to build, concretely), `success_criterion`, and `verification` stated or directly derivable from their message, plus an unambiguous skip instruction ("skip deliberation", "implement exactly this, no deliberation") — build a passthrough report and go straight to Step 7. Never infer the fiat: a detailed request without the explicit skip instruction still gets the full pipeline.
     ```json
     {
       "success_criterion": "<user's criterion>",
       "chosen_approach": "user-spec",
       "verification": "<user's verification>",
       "alternatives": [],
       "voice_scores": null,
       "confidence": 0.90,
       "pipeline_executed": false,
       "deliberation_log": [{"step": "user_spec_passthrough", "spec": "<one-line summary of the user's declared approach>"}],
       "telemetry": {"mode": "user_spec_passthrough", "dispatch_count": 0, "consilium_version": "<python scripts/version.py>", "consilium_ref": "<python scripts/version.py --ref>"}
     }
     ```
   - Step 7 runs **with all gates intact** — implement-mode routing, red→green gate, Reviewer. The fiat skips the deliberation, not the safety net.
   - Persist + log to FEEDBACK like any run (Step 6 final actions) — the `user_spec_passthrough` mode label keeps these runs visible to priors and outcome tracking.
   - **Headless:** works identically — the explicit instruction in the prompt *is* the consent; no confirmation needed.
   - **Falsification criterion:** if `user_spec_passthrough` runs accumulate BAD outcomes, tighten this trigger (e.g. require restating the skip instruction verbatim) — the valve is a convenience, not a right.

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
Defaults: `max_files=1`, `max_lines=15`, conservative blocklist (`auth/`, `security/`, `migrations/`, `.github/workflows/`, `**/*secrets*`, `.env*`, `Dockerfile`, `*.tf`, dependency files). Override via `scope_gate.json` (`{max_files, max_lines, blocklist}`). Escape hatch: `CONSILIUM_FORCE_FULL=1` forces `should_skip=false`. Gate **fails open** (no repo / bad ref → `should_skip: false`).

**Non-diff tasks** (audit, architecture review, planning): scope_gate is a no-op — you can skip Step 1.5.

### 1.6. Pre-dispatch consent gate (auto)
Generator runs **first**, so the irreversibility consent gate fires **before any voice** — consent is never requested after generation effort is already spent. After scope_gate, read `consent_required` from its output:

```bash
python scripts/scope_gate.py   # read `consent_required` (and `signals.blocklist_hits`)
```

- `consent_required: true` (a sensitive/irreversible path — auth, migrations, CI, secrets, deps — or an undeterminable change) → **stop and ask**: *"This change touches an irreversible/sensitive path. Confirm you want to proceed before I deliberate?"* Proceed only on explicit YES. **Headless** (`is_headless()`): do not block; set `metadata.headless_overridden: true` and continue (the orchestrator that set `CLAUDE_HEADLESS=1` has assumed the stake).
- **Text markers complement the path signal:** if the change description or diff contains irreversible-action language ("DROP TABLE", "delete all", "no way back", "force-push", "publish/break API") with no consent documented in the input, treat it as `consent_required` too.
- **Fail-safe, not fail-open.** Unlike `should_skip` (which fails OPEN → deliberate), the consent check fails SAFE: a probe/config failure returns `consent_required: true`. Uncertainty asks; it never silently bypasses consent. Conservator's `irreversibility_flag` (Step 3) is the backstop for what a path/text pre-check cannot see.

**Non-diff tasks:** with no diff to probe, skip Step 1.6 unless the request text itself carries irreversible-action language.

## Stage 2 — Generator

### 2. Generator — produce alternatives (runs FIRST)
Use `prompts/voices/generator.md`. Runs **before** Conservator and Control — blind to risk framing (anti-anchoring). Request **3–5 candidates** (including `do_nothing` and any `adversarial_*`). Divergent style. Generator **self-scales** candidate count/detail from the change's blast radius (diff size, sensitive paths) — there is no upstream `tokens_budget`; default to moderate depth (3 candidates) when the signal is unclear.

Output: `{candidates: [{id, summary, sketch, rationale, downside_estimate}], fallback_scenario, coverage_check, challenge_upward, abstain, preferred}`. Adversarial is conditional (the change touches shared/core code OR a function with >3 external callers) — otherwise emit `"adversarial_skipped": "<reason>"`. Unconventional is included by default (unless adversarial already covers that role or the change is mechanically trivial) — emit `"unconventional_skipped": "<reason>"` when omitting.

**Receives no Conservator output.** Generator runs first; risk framing is deliberately withheld so the candidate set is not anchored by it.

**Challenge upward (risk-escalation flag):** If Generator sets `challenge_upward.triggered: true`, forward that flag into Conservator's input (Conservator runs next) so it scales up its scrutiny. One-way signal forward, not a re-run.

## Stage 3 — Risk & Verify

### 3. Conservator — assess risk (runs after Generator)
Use `prompts/voices/conservator.md`. Receives **Generator's candidates** and scores the risk of each. Its `tokens_budget.control` output caps how deep Control (next) goes.

**Memory context (inject into Conservator input).** Run:
```bash
python scripts/priors.py --memory-summary --label "<task label>"
```
Prepend the output (2–3 lines) to Conservator's input context block — after Generator's candidates, before the required questions. When output is empty (no FEEDBACK data), skip silently. This keeps Conservator aware of recent outcome patterns and any prior deliberation match without altering its authoritative prompt.

Required Questions (Q1-Q5): reversibility, magnitude, counterparty_risks, status quo bias check, meta_recommendation.

Output per candidate: `{id, regression_risk: {reversibility, magnitude, net_concern}, counterparty_risks, bias_check, meta_recommendation, tokens_budget: {generator, control}, irreversibility_flag, rollback_recipe, notes}`.

**Categorical flip caveat:** Conservator `magnitude`/`reversibility` labels have a ~40% inter-run flip rate on ambiguous inputs (experiment 2026-05-17). If the deliberation is sensitive to the magnitude/reversibility boundary, consider double-sampling.

**Veto check (auto, after Conservator output):**
- If `irreversibility_flag: true` (backstop — the pre-dispatch Step 1.6 gate did not already obtain consent) → stop, ask user: *"Conservator marks this decision as irreversible. Do you confirm you want to continue?"* — proceed only with explicit YES. **Headless** (`is_headless()`): DO NOT block; set `metadata.headless_overridden: true` in the bundle and continue. The external orchestrator that set `CLAUDE_HEADLESS=1` has assumed the stake.
- If `meta_recommendation: scale_down` → **short-circuit**: skip dispatching **Control** (Generator already ran). Build a minimal report directly from Generator's candidates + Conservator's risk:
  ```json
  {
    "success_criterion": "<input success_criterion>",
    "verification": "manual review (scope_gate determined trivial)",
    "chosen_approach": "trivial-direct",
    "alternatives": [],
    "voice_scores": {"conservator": "<conservator net_concern>"},
    "confidence": 0.85,
    "pipeline_executed": false,
    "deliberation_log": [{"step": "scale_down_short_circuit", "reason": "<conservator notes>"}],
    "telemetry": {"mode": "sequential_scale_down", "dispatch_count": 2, "consilium_version": "<python scripts/version.py>", "consilium_ref": "<python scripts/version.py --ref>"}
  }
  ```
  `confidence: 0.85` is deliberate — Conservator's judgment is the signal, not a weak guess. Designed to stay above the `[0.0, 0.70)` skeptic auto-trigger band.

  **Dialectic mode exception (scale_down + Skeptic):** when `telemetry.mode = "dialectic"`, the Skeptic stage runs **even on scale_down short-circuits**. Rationale: Dialectic's whole point is a focused post-hoc challenge on the chosen answer; scale_down skipping Control is fine (cost-aware) but skipping Skeptic too defeats the mode. The trivial-direct chosen is the input to Skeptic — if Skeptic produces `can_object: true` with a concrete constraint, log `skeptic_caught_constraint: true` and the orchestrator should reconsider the trivial-direct answer (advisory by default; `--skeptic-can-override` allows the override). Empirical motivation: 2026-05-28 benchmark validation (see `experiments/dialectic-skeptic-on-scale-down-validation-2026-05-28.md`). Dialectic spec already mandates "Skeptic runs unconditionally — not gated on the confidence band" (modes/dialectic.md §"Skeptic stage"); this exception makes the spec real on the scale_down path.
- If `meta_recommendation: scale_up` → warn user, add context request. **Headless**: warning emitted to stderr, the context cannot be requested interactively — continue with existing input.

**Optional — autoprobe:**
```bash
python scripts/probe_change.py                       # working tree vs HEAD
python scripts/probe_change.py --ref main --churn 30 # + commit count per file last 30 days
```
Anchor `magnitude` to `files_changed/lines_*` and `regression_risk.net_concern` to the churn distribution when present.

### 4. Control — verify correctness
Use `prompts/voices/control.md`. Per candidate: types, logic, tests, style.

Required Questions (Q1-Q4): glossary (max 5), hidden_assumptions (max 3), disagreements, fixed/negotiable_constraints.

Output: `{glossary, hidden_assumptions, disagreements, fixed_constraints, negotiable_constraints, glossary_fail, glossary_attempts, verdicts: [{id, valid, issues, tests_to_write, notes}]}`. `tests_to_write` mandatory for `valid: true` (exception: `do_nothing`) — 1-4 acceptance tests.

**Receives from both:** full Generator output + full Conservator output.

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
Returns `{confidence, agreement, separation}`. If `chosen` is `null` (all candidates vetoed), the `confidence` field in the response is `null`. Step 5d is skipped in this case — there is no retry when no candidate survived aggregation. **Formula, vote-pattern path, mode floors, calibration caveat: [modes/confidence.md](modes/confidence.md).**

> **Calibration (R2 audit 2026-05-17):** `agreement` measures divergence between roles within ONE run — not inter-run stability. Conservator scores are anchored by categorical formula (see `conservator.md`); Generator/Control scores are unanchored self-assigned floats. A second run with the same input may produce different scores (pstdev estimated 0.12–0.18 on `risk_score`). The `confidence` value is not a calibrated probability — it is an internal-consistency signal.

**Quoting:** Avoid building inline Python via `-c "..."` with JSON payload — apostrophes in the code can break bash quoting. Use stdin piping (as above) or the `--input <file>` flag.

**Mode confidence floor (E1).** After confidence is derived, check whether the mode reached the minimum floor:
```python
from scripts.confidence import check_mode_floor
result = check_mode_floor(telemetry_mode, confidence_value, vote_pattern)  # vote_pattern only for trias; omit/None otherwise
# result["below_floor"] == True → log with --outcome WEAK in FEEDBACK.html
```
Floors: `sequential=0.70`, `dialectic=0.75`, `trias=0.80`. A run below floor signals the mode did not deliver value for the cost. **Trias exemption:** a decisive vote pattern (`3-0`/`2-1`/`2-0`) is exempt from the WEAK flag — `2-1` (0.75) and `2-0` (0.70) sit *structurally* below the 0.80 floor by design, not because the deliberation was weak; pass `vote_pattern` so the floor flags only genuinely weak runs. The data accumulates in `FEEDBACK.html` — the pattern becomes visible after ≥10 runs per mode.

**Low-confidence auto-escalation (Sequential only).** When `confidence < 0.6` and `mode=sequential`, the orchestrator **automatically re-runs the full pipeline (Steps 1–5) with `--mode dialectic`** — no user action required, no confirmation prompt. The Dialectic result is the final output; the Sequential run is discarded. Pass `auto_escalated: true` in the bundle before calling `build_report.py` so the final report carries the marker (observability + retroactive outcome tracing). One escalation level only — if Dialectic also yields `confidence < 0.6`, no further escalation fires. Threshold distinction: `skeptic_on_chosen` auto-triggers at `confidence < 0.70`; this fires only at `< 0.6` — the genuinely weak band where a higher mode is likely to produce materially different results.

### 5c. Meta-critic (auto, advisory) — *retired 2026-05-25*
```bash
cat bundle.json | python scripts/deprecated/meta_critic.py
```
Scores **deliberation quality** (not choice correctness). Retained metric: `conservator_spread` (shrug?). Dead metrics `generator_divergence` and `control_concreteness` removed (0/163 fires). Emits `deliberation_quality.flags` — attach to the bundle before Step 6 (build_report passes it through to the report). Non-empty `flags` do not block. Senate verdict: MODIFY (GO 5 · MODIFY 3 · STOP 1, 2026-05-24 `kill-meta-critic-r2`) — trimmed to conservator_spread only, moved to deprecated/. Substance-validation gap accepted as a known limitation (see TODO.md).

### 5d. Retry on low confidence (optional, single pass)
If `confidence < 0.7`, **before** asking the user: identify the single question whose answer would discriminate the top-2 candidates (an unverified assumption, a file you haven't read, an empirical check you can run). Gather that evidence yourself (Read + Grep + smoke-run), then re-run Generator/Control/Conservator **once** with the enriched input. If confidence is still < 0.7, only then ask the user (Step 6).

The retry is orchestrator-driven — derive the discriminating evidence from the deliberation itself. (`retry_context.py`, the old hint generator, was retired to `scripts/deprecated/` on 2026-06-10: its hints had zero usage in the corpus, while two same-day orchestrator-driven retries succeeded — 0.697→0.726 and 0.662→0.679.)

**Headless** (`is_headless()`): skip Step 5d entirely — go directly to Step 6 where `PEND_HEADLESS` is logged.

## Stage 5 — Output

### 6. Report

**Telemetry emission (mandatory — before `build_report.py`).**

At each dispatch (voice), immediately after return, accumulate in the bundle:

- `telemetry.voices.<voice_name>`: `{tokens_in: ceil(len(prompt)/4), tokens_out: ceil(len(response)/4), latency_ms: <wall-clock>}` — prompt = full text sent (persona + context + proposal, not just the proposal).
- Sum tokens + latency per voice if there are retries on the same dispatch.
- `telemetry.mode` ← canonical label (`"sequential"`, `"trias"` etc. — from `## Dispatch defaults`).
- `telemetry.dispatch_count` ← total dispatches (including retries).
- `telemetry.consilium_version` / `telemetry.consilium_ref` ← repo version provenance, stamped automatically by `build_report.py` (and by the two hand-built templates above). `consilium_version` = `git describe --tags --always --dirty` (display); `consilium_ref` = the committed HEAD sha or `""` on a dirty/unknown tree (the resolvable diff operand). Lets any run be reproduced via `git checkout` — see `scripts/version.py`.

Why mandatory: a run without telemetry is invisible to cost analysis and per-mode comparisons (the measured tokens-per-dispatch snapshot in the architecture explainer was built from this telemetry).

```bash
cat bundle.json | python scripts/build_report.py | python scripts/validate_report.py
```
Bundle schema: `{success_criterion, verification, generator, control, conservator, aggregate, confidence, telemetry}`. `build_report.py` derives `voice_scores`, assembles `alternatives` (with `why_not`) and `deliberation_log`. (`voice_scores` is derived by `build_report.py` from voice outputs — it is not emitted by the voices directly.)

> **Interception contract.** `build_report.py` accepts only the `AGGREGATE` aggregate shape (which carries `chosen`) or a `skipped` bundle. The non-`AGGREGATE` results of `aggregate_sequential` — `BLOCK` (glossary_fail / irreversibility), `REWORK` (substantial disagreement), `ESCALATE` (3+ triggers), `ADAPT_EXTENDED` (scale_up) — are **interception points** the orchestrator handles *before* Step 6 (ask the user, reformulate, re-run). `ADAPT_SHORT` (scale_down) builds its `trivial-direct` report by hand (SKILL.md Step 3), not via `build_report.py`. So `build_report.py` raising `ValueError` on a `chosen`-less aggregate is the correct hard-fail for a contract violation, not a shape it is expected to render.

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

**Batched finalize (fewer turns).** On the **decision-free path** — `confidence >= 0.7` (OK) or headless (`PEND_HEADLESS`) — run the mechanical tail (assemble → validate → commit → log) as **one `&&`-chained Bash call**, not 3–4 separate tool-call turns. Each extra turn re-reads the full accumulated context at the `cache_read` rate; collapsing the tail saves ~4–5% cost + latency (measured A/B, 2026-06-24).

**Validate BEFORE the run is committed (Constitution #4 invariant).** Build to a `.partial` staging file, validate *that*, and only `mv` it into `runs/<file>.json` on success. A failed `validate_report.py` short-circuits the chain so the run is **never committed** — nothing invalid reaches `priors.py` (which globs `runs/*.json`, not `*.partial`) or `FEEDBACK.html` (`log_feedback` runs last). This closes the silent-failure hole of streaming the write before validation (`tee`-then-validate left an invalid run on disk):
```bash
python scripts/build_report.py < bundle.json > .consilium/runs/<file>.json.partial \
  && python scripts/validate_report.py < .consilium/runs/<file>.json.partial \
  && mv -f .consilium/runs/<file>.json.partial .consilium/runs/<file>.json \
  && python -X utf8 scripts/log_feedback.py --outcome OK --run-path .consilium/runs/<file>.json < .consilium/runs/<file>.json
```
On a validate failure the chain stops with the `.partial` un-promoted (delete it: `rm -f .consilium/runs/<file>.json.partial`); fix the bundle and re-run. **Do not chain** when a decision intervenes — the interactive `confidence < 0.7` override prompt must run *between* validate and log (the user picks OK/OVR/skip first). Chaining is an orchestration convenience, not a contract change: the scripts stay standalone-invocable and the step order is identical.

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
| high | complete | implement → compile → test |
| high | partial | implement → compile → review → test |
| high | irreversible | implement → compile → review → test |
| critical | any | implement → compile → review → test |

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

Descriptive reading aid only — no behavioral contract. Moved to [docs/otal-framing.md](docs/otal-framing.md) (2026-06-10) to keep this contract lean.

## Skill maintenance

Apply only when editing the skill (`scripts/*.py`, `prompts/*.md`, `SKILL.md`), not at every deliberation.

**Eval harness** — when editing `aggregator.py`, `confidence.py`, `validate_report.py`, `strip_context.py`, or `personalities.py`:
```bash
python scripts/run_evals.py
```

**Periodic feedback audit**: `python scripts/feedback.py [--recent 10 --runs]` (stats), `python scripts/audit_feedback.py [--backfill]` (runs without FB row).

**Benchmarking discipline** — any quantitative claim about voice behavior (`fab-rate`, `accuracy`, `catch-rate`) must cite an **independent oracle** (a second expert OR explicit citation from the statement/specs that fixes the ground truth), not the evaluator's quick take. Before publishing benchmark results: for each plausible option (A/B/C/D...), document explicitly *"is there an alternative reading of the problem in which answer X becomes correct?"* — explicit answer per option. A "fabrication" verdict on a piece of reasoning remains blocked until oracle review, separate from the evaluator's intuition. Retroactively applied: any existing fab-rate claim in `experiments/` and `runs/` is reviewed through this grid. Operational checklist: `experiments/README.md`. Origin: the P3 corrigendum (see `experiments/oracle-discipline.md`) — the wrong oracle semantically inverted the "fabrication" conclusion → "real constraint catch".

## Resources

| Script | Role |
|---|---|
| `scripts/priors.py` | Soft priors from FEEDBACK.html + runs/ (Step 0). Surfaces `missing_feedback_runs`, `stale_pendings` (2-day threshold), `weighted_bad_rate`, and `prompt_drift` (advisory — set when prompts/modes changed since the most-recent prior run's `consilium_ref`). |
| `scripts/version.py` | Repo version provenance: `consilium_version()` (git describe stamp), `consilium_ref()` (resolvable committed sha or `""`), `prompts_changed_since(ref)` (guarded drift count). CLI: `(no flag)` prints the display stamp / `--ref` / `--drift <ref>`. |
| `scripts/scope_gate.py` | Auto-detect skip if scope is small (Step 1.5) |
| `scripts/probe_change.py` | Anchor diff_size to `git diff --numstat` (Step 4) |
| `scripts/aggregator.py` | 5 aggregation schemes + auto-relax on total veto (Step 5); reference: `modes/aggregator_schemes.md` |
| `scripts/confidence.py` | Derives confidence from variance + separation (Step 5b); reference: `modes/confidence.md` |
| `scripts/deprecated/meta_critic.py` | Deliberation quality score (conservator_spread only) — Step 5c retired 2026-05-25 |
| `scripts/deprecated/retry_context.py` | *(Retired 2026-06-10 — hint generator for the Step 5d retry; zero hint usage in corpus. The retry itself is orchestrator-driven.)* |
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
| `agents/consilium-subagent.md` | Subagent for isolated invocation via `Agent(subagent_type="consilium-subagent", ...)` |
| `scripts/vocabulary_map.py` | User-facing translations (reversibility/magnitude/meta_recommendation/verdict) + `compute_tokens_budget(magnitude, reversibility, meta)` |

## COMMIT workflow (post-implementation)

The authoritative git rules live in `CLAUDE.md` §Git workflow (branch naming, one-commit-per-branch, auto-push, Conventional Commits, `commit.ps1` helper, Stop-hook automation).

## Feedback loop

All deliberation state lives under **`.consilium/`** at the repo root (gitignored; the single data directory). Paths are centralized in `scripts/utils.py` (`DATA_DIR`/`RUNS_DIR`/`FEEDBACK_PATH`) — scripts import them as defaults, `--runs-dir`/`--feedback` still override.

- **`.consilium/runs/`** — JSON per deliberation in `.consilium/runs/YYYY-MM-DD_HHMM_<label>.json` (schema in `docs/runs-schema.md`). Read by `priors.py` (Step 0), `feedback.py`, `memory.py`. Run-paths are stored relative to `.consilium/` (key `runs/<file>.json`); `--run-path` accepts any spelling (`.consilium/runs/<f>.json`, `runs/<f>.json`, absolute) and `utils.canonical_run_path` normalizes it to that key.
- **`.consilium/FEEDBACK.html`** — one line per use: `date | context | chosen | outcome | note`. Outcome: `OK`, `BAD`, `OVR`, `PEND`. **Drill-down:** when `log_feedback.py` appends, existing rows lose drill-down; use `scripts/deprecated/migrate_feedback_md_to_html.py` for bulk re-population (retired one-shot tool, see scripts/deprecated/).
- **Confirmed outcome.** `mark_outcome.py` adds the `[confirmed]` marker in note. `priors.py` weights these rows 2x in `weighted_bad_rate`. Use when production reality contradicts the subjective outcome from Step 6.

## Memory tiers

3 memory layers (short = conversation window; medium = `.consilium/runs/*.json`; long = `.consilium/FEEDBACK.html`), uniform read API via `scripts/memory.py --tier <short|medium|long|all> [--query <substr>] [--n <N>]`. Full table + lifecycles: [docs/memory-tiers.md](docs/memory-tiers.md).

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

Default behavior unless overridden by project memory (`MEMORY.md`). All voices pinned to `model: "sonnet"` per `feedback_subagents_sonnet.md`. **Trias exception**: each personality uses the model declared in `scripts/personalities.py` — all three (pioneer, architect, steward) → `sonnet`. Mode sections declare per-invocation overrides — single source of truth per mode, descriptive not enforced.

Cost multipliers (baseline Sequential = 1×): Dialectic 1.33× · Trias 2.67×. The `skeptic_on_chosen` flag adds +1 sub-agent over the base mode (e.g. Sequential+flag = 1.33×).

## Parallel voices mode

**Parallel mode removed** (2026-06-26 — Senate GO_WITH_CONDITIONS, 0 divergences in 41 empirical runs). Parallel dispatch is no longer available in any form. Existing `.consilium/runs/*.json` files with `mode: "parallel"` remain valid (backward-compat enum in `validate_report.py`).

**Advisory.** If `magnitude = critical` AND `reversibility = irreversible`, consider upgrading to **Trias** (2.67× cost, 3 independent personalities + post-vote Skeptic — stronger independent-context coverage than Parallel ever provided). Trias does not auto-trigger; you must select it explicitly.

## Mode files (machine-readable config)

Each mode has its own `.md` file in `modes/` with YAML frontmatter (`name`, `subagents`, `cost_multiplier`, `confidence_floor`, `models`). Scripts read mode parameters from these files — they are the single source of truth for mode config. Read the mode file at Bootstrap (Step 0) before running a non-default mode.

| Mode | File | Subagents | Cost | Conf. floor |
|---|---|---|---|---|
| Sequential (default) | [modes/sequential.md](modes/sequential.md) | 0 | 1× | 0.70 |
| Dialectic | [modes/dialectic.md](modes/dialectic.md) | 1 | 1.33× | 0.75 |
| Trias | [modes/trias.md](modes/trias.md) | 4 (worst: 7) | 2.67× | 0.80 |
| skeptic_on_chosen (flag) | [modes/skeptic_on_chosen.md](modes/skeptic_on_chosen.md) | +1 over base | base+1 | N/A |

`modes/` also holds reference docs for sub-components (not selectable modes): [implement_pipeline.md](modes/implement_pipeline.md) (Step 7), [aggregator_schemes.md](modes/aggregator_schemes.md) (Step 5), [confidence.md](modes/confidence.md) (Step 5b).

## Dialectic mode (opt-in)

Sequential + 1 Skeptic sub-agent. Code-context (language, files, test suite, CI gate) injected into voice inputs. `telemetry.mode: "dialectic"`. **Full workflow: [modes/dialectic.md](modes/dialectic.md).**

## Trias mode (high-stakes opt-in)

3 personalities (Pioneer/Architect/Steward), each runs a full Sequential deliberation internally and blind, then a democratic vote, then **one** Skeptic sub-agent (`skeptic_on_chosen`) challenges the winning candidate post-vote (advisory by default; `--skeptic-can-override` re-votes excluding a demolished winner). The 2026-06-19 skeptic-lever redesign replaced the 3 per-personality pre-vote Skeptics with this single post-vote Skeptic (6→4 spawns). Lazy routing graduates by magnitude: low/medium → Sequential, high → Dialectic — only `critical` magnitude (blocklist hits: auth, security, migrations, CI workflows, secrets) proceeds to full Trias. **Cost: ~2.67× Sequential** (worst-case 7 sub-agents on 1-1-1 deadlock cascade). `trias_split` deprecated — use standard `trias`. **Full workflow: [modes/trias.md](modes/trias.md).**

## Skeptic-on-chosen mode (`skeptic_on_chosen`)

Cross-cutting flag — +1 Skeptic sub-agent over any base mode post-hoc. Auto-triggers when `confidence < 0.70` (strictly less than 0.70; the Trias 2-0 canonical value and the Sequential floor are both at 0.70 and are passing). Advisory by default; `--skeptic-can-override` for opt-in. **Full workflow: [modes/skeptic_on_chosen.md](modes/skeptic_on_chosen.md).**

## Routing boundary

When to escalate beyond a standard Consilium mode:

| Decision profile | Mode |
|---|---|
| `confidence < 0.70` from standard mode AND single drift concern | `dialectic + skeptic_on_chosen` |
| 2+ plausible architectural approaches without clear winner | `trias` |
| Bugfix evident OR diff <20 lines / 1 file | Sequential (scope_gate skips) |
| All other PR-level reviews | Sequential (select Trias if critical + irreversible) |

## Sequential mode (default)

Default mode. Generator → Conservator → Control run in-context. 0 sub-agent dispatches, 1× cost. **Full reference: [modes/sequential.md](modes/sequential.md).**

Key veto triggers (inline for quick reference during Steps 2–5):

| Trigger | Source | Effect | Action |
|---|---|---|---|
| `consent_required: true` | scope_gate (Step 1.6) | BLOCK (hard) | Ask user for explicit consent **before Generator** (pre-dispatch) |
| `irreversibility_flag: true` | Conservator | BLOCK (backstop) | Ask consent before finalizing (Step 1.6 already gates the common case) |
| `glossary_fail: true` | Control | BLOCK (soft) | Ask user to reformulate with operational terms |
| `disagreements: substantial` | Control | REWORK | Re-run Generator with clarification context |
| `meta_recommendation: scale_down` | Conservator | ADAPT_SHORT | Short-circuit: skip Control (Generator already ran), emit trivial-direct report (`pipeline_executed: false`) |
| `meta_recommendation: scale_up` | Conservator | ADAPT_EXTENDED | Warn user, add context before Generator |
| 3+ of above simultaneously | Aggregator | ESCALATE | Present trigger table to user, request decision |
