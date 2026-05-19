# Senate mode — operational & architectural reference

This document is the deep reference for the `senate` Consilium mode.
For the routing decision (when to use Senate vs other modes) and the
9-senator roster, see SKILL.md § "Senate mode (`senate`)".

## Operational definitions

To verify that the Senate ran correctly, two key terms have testable definitions:

- **"Senate run end-to-end"** = (a) bundle `runs/senate/<timestamp>-<label>.json` exists on disk; (b) parseable JSON; (c) contains `verdict ∈ {GO, MODIFY, STOP, DEEPLY_SPLIT, UNREACHABLE, OUT_OF_SCOPE}` and `vote_counts`; (d) `senate_synth.py` exit 0.
- **"Senate does not touch existing voices/modes"** = `git diff <base>..HEAD -- prompts/{generator,control,conservator,skeptic,generator_pass2,control_pass2,conservator_pass2,*_lens}.md scripts/{aggregator,confidence,dialectic_merge,validate_report,build_report,personalities,strip_context,priors}.py` returns empty. Additions to the SKILL.md Resources table or new sections are explicitly allowed.

## When to use (additive cases beyond Law 9 §1)

- Modifications to core `prompts/*.md` or to the Constitution/Workflow in SKILL.md
- New voices/modes before you implement
- Irreversible architectural decisions (`runs/*.json` schema, veto semantics)
- Self-improvement loop on your own changes (a stronger version than `/consilium parallel`)

## Workflow

1. **Formulate the proposal concretely** — paragraph: what you change, why, files touched, success criterion.
2. **Dispatch 9 sub-agents in parallel** (default model per SKILL.md § "Dispatch defaults", but **read the YAML frontmatter** in `prompts/senators/<name>.md`: if the `model:` key exists you use it instead of the default — e.g. `tacitus` runs on Opus per justification in its own prompt). Each with the senator's prompt inline. Identical input:
   ```
   Proposal under audit: <the text>
   Context: <files touched, success criterion>

   Your role and instructions:
   <content of prompts/senators/<senator>.md>

   Return STRICTLY the JSON specified in the "Output format" section. No prose.
   ```
3. **Retry 1× on absent senator / malformed JSON.** On failure, mark `absent` and continue.
4. **Cross-questions (Law 2 — optional, multi-round).** Scan Round 1 outputs for `cross_questions[]`. For each `{to: <senator>, question: ...}`, dispatch focally on the target senator with input "In Round 1 you voted X. Senator Y asks you: <question>. Respond with full updated output — the vote may be different." Counter per senator per round (max 3 — Law 2). Maximum 3 rounds total. If Round 2 raises new cross-Qs, repeat in Round 3 then forced STOP.
5. **Deadlock resolution (Law 3 — optional).** If after Round 3 there are still 2 senators in GO×STOP opposition (synthesizer reports `blocaj_pending`), dispatch the other 5 with the arguments of both sides and ask which is stronger. Collect `votes_from_others: {<senator>: <pair_member>}` and give the orchestrator `blocaj_resolution` in the synth input.
6. **Run the synthesizer:** `cat senate_input.json | python -X utf8 scripts/senate_synth.py`
   - **Input format (multi-round):** `{"proposal": "...", "label": "...", "rounds": [{"round": 1, "senators": {...}}, ...], "blocaj_resolution": {...}, "absent": [...]}` — see docstring.
7. **Bundle automatically saved** in `runs/senate/<YYYY-MM-DD_HHMMSS>-<label>.json` (second granularity + `_v2/_v3...` suffix on collision — no silent overwrite). Bundle includes `rounds`, `position_changes`, `cross_questions_used`, and (if applied) `blocaj_resolution` + `vote_counts_pre_blocaj`.
8. **The verdict is advisory** — the user decides:
   - `GO` (≥7/9 GO **and** MODIFY==0) → you proceed
   - `STOP` (≥7/9 STOP **and** MODIFY==0) → the proposal is blocked; revise or explicit override
   - `MODIFY` (any MODIFY vote > 0) → the proposal must be revised before reaching GO/STOP. Two paths: **accept** (treat `modify_requests` as advisory TODO) or **R2** (re-run Senate with a revised proposal that addresses the `modify_requests`). If R2 produces MODIFY 3 consecutive cycles, soft warning: "consider accepting or decomposing the proposal."
   - `DEEPLY_SPLIT` (neither GO nor STOP reach QUORUM=7, MODIFY==0) → advisory: orchestrator escalates to the user with vote matrix and manual override option.
   - `UNREACHABLE` (active votes < `MIN_ACTIVE_VOTES=5` — absent/timeout senators, NOT abstention) → orchestrator presents the user with two options:
     1. **Re-run the Senate** with retry on absent senators
     2. **Run normal Consilium** (sequential/dialectic/trias mode) on the same proposal — the senate is replaced by standard deliberation

## The 5 Laws (Senate)

| # | Law | Essence |
|---|------|--------|
| 1 | Mandatory output and vote | Each senator emits structured output and a **GO/MODIFY/STOP** vote on every proposal. ABSTAIN is not a valid vote. Senators who cannot form a direct position on the proposal as stated (Deming on non-quantitative proposals, Tacitus on proposals without invoked precedent) emit GO with an explicit `reasoning` field of withdrawal — signaling that they don't block, but don't blanket-validate. The tally remains 1 vote per senator (no weighted voting). |
| 2 | Limited cross-questions | Max 3 cross-Q/senator/round × max 3 rounds. Round 3 = forced STOP. |
| 3 | Deadlock → 5-vote majority | If 2 senators remain in GO×STOP after Round 3, the other 5 vote on which argument is stronger. |
| 4 | Synthesis only at the end | `senate_synth.py` runs AFTER all rounds. Position changes logged in the bundle. |
| 5 | Auditability | All rounds + cross-Q + position changes saved in `runs/senate/`. |

## MIN_ACTIVE_VOTES

`MIN_ACTIVE_VOTES=5`: if fewer than 5 senators voted actively (GO/MODIFY/STOP), the verdict is `UNREACHABLE`. Under the new Law 1 (no-ABSTAIN), `UNREACHABLE` signals exclusively absence (timeout / dispatch failure), not withdrawal — all present senators vote one of the three options. Legacy compat: `runs/senate/*.json` with `senate_schema_version<2` or missing field may contain ABSTAIN votes; they are no longer produced in new runs.

## Senate Laws (6-8)

**Law 6 — Iterative Coherence.** Before Round 1, the orchestrator scans `runs/senate/*.json` for runs with similar labels (substring match) in the last 30 days via `scripts/senate_priors.py`. The prior verdict + top 3 modify_requests become mandatory context for all senators in Round 1, injected as `prior_run_context` in input.

Each senator must explicitly address in output the field `addresses_prior_concerns: true|false|n_a` (n_a only if this senator did not participate in the previous run). If `false`, the vote cannot be GO — the proposal has not evolved enough for an implicit upgrade of the verdict. The orchestrator passes `prior_context_injected: true` in the input of `senate_synth.py` so that warnings about missing `addresses_prior_concerns` are emitted. Validation: `python scripts/validate_report.py --strict-senate`.

**Law 7 — Scope Veto.** Any senator can emit `scope_veto: true` in Round 1 when they consider that the senate is the wrong tool for the proposal — proposal too small (e.g., variable rename, typo fix), proposal already decided in another context, or non-deliberable proposal (e.g., factual question with determinable answer).

`scope_veto` must be accompanied by `recommended_mode` (sequential, trias, direct-implement, skip, etc.) and `veto_reason` (1-2 sentences).

If ≥3 senators emit `scope_veto: true` in Round 1, deliberation stops with verdict `OUT_OF_SCOPE` and the report includes `scope_veto_consensus` with the recommended modes (the most frequently recommended is the default). Rounds 2-3 are not executed. Implemented in `senate_synth.py` (constant `SCOPE_VETO_THRESHOLD=3`).

**Law 8 — Falsifiability Anchor.** Any `modify_request` must include at least one verifiable predicate: a concrete test, a grep search, a file:line edit, or a quantitative assertion. Vague ('clearer', 'better documented', 'more robust') are insufficient.

If `law8_enforce: true` is set in the input of `senate_synth.py`, the votes of senators with vague-MODIFY are auto-promoted to GO with `auto_promoted_from: "MODIFY (no anchor)"` in their output. Audit trail kept in `bundle.auto_promoted_senators` and `bundle.warnings`. Helper `has_falsifiability_anchor()` in `scripts/validate_report.py`; validation: `python scripts/validate_report.py --strict-senate`.

**Verdict OUT_OF_SCOPE** (introduced by Law 7): bundle includes `scope_veto_consensus.recommended_mode_default` for downstream. Validated by `validate_report.py --strict-senate` and by `validate_bundle()` in `senate_synth.py`.

## Senate headless invariants

When `CLAUDE_HEADLESS=1` and Senate is invoked (via `/consilium --mode senate --on-code` or as a benchmark mode), the following applies:

| Phase | Headless default |
|---|---|
| Round 0 priors (`stale_pendings`, `missing_feedback_runs`) | log warnings to stderr + continue; run `audit_feedback.py --backfill` automatically |
| Round 1 clarity gate | if proposal has 2+ plausible interpretations, fork as parallel scenarios; no user prompt |
| Round 1 scope_veto consensus (Law 7) | proceed automatically with `verdict: OUT_OF_SCOPE` if ≥3 vetoes; orchestrator decides downstream |
| Round 2-3 cross-questions | dispatch starred pairs first, then non-starred; budget cap 9 cross-Qs per round |
| Iterative coherence (Law 6) | `prior_run_context` auto-injected from `runs/senate/` scan; `prior_context_injected: true` passed; no user confirmation |
| `DEEPLY_SPLIT` verdict | `chosen_approach: null`, `confidence: null`, `subagent_notes.blocked_reason: "deeply_split"` |
| `UNREACHABLE` quorum | same shape; `blocked_reason: "unreachable_quorum"` |
| `OUT_OF_SCOPE` | same shape; `blocked_reason: "out_of_scope"` + `subagent_notes.recommended_mode` populated |
| Step 7 (implementation, if `--on-code`) | runs `infer_pipeline.py --yes` on `chosen_approach` |
| `log_feedback` | runs with `--outcome PEND_HEADLESS` |

Output contract in headless: after `validate_report.py --strict-senate` exits 0, emit exactly the bundle JSON content as the final message. No prose, no markdown fences. Details in `agents/consilium-senate-subagent.md`.

## Drafts footnote — EXPERIMENTAL_DRAFT modes

- **`senate --on-code`** (status: EXPERIMENTAL_DRAFT). Lens: `prompts/lenses/domain_lens.md#code_domain`. Gate criteria: ≥3 pilot runs with ≥2/3 info-add over Trias (measured via `scripts/compare_senate_vs_trias.py`) AND `semantic_suspect` ≤20% per run. If gate fails after 5 pilots → marked DEPRECATED_DRAFT, `runs/senate/` pilot bundles preserved as forensic evidence. **Do not depend on this mode for critical merge decisions until gate met.**

## Senator context injection (Pilot B)

**Status: pilot — zero code, orchestrator-only behavior.**

At Step 2 (dispatch), before sending each senator's input, the orchestrator can prepend a context block from previous senate runs:

```
Past votes for <senator_name> (inject only if N≥5 senate runs with recorded outcome):
- <label> | <vote> | <outcome>   # most recent
- <label> | <vote> | <outcome>
- <label> | <vote> | <outcome>   # oldest of 3
```

**Operational rules:**
- Injected schema: `{label, vote, outcome}` triples, N=3 most recent, sorted descending by timestamp
- Source: `runs/senate/*.json` — read manually by the orchestrator (no automatic script in Pilot B)
- **Activation gate:** do not inject if `runs/senate/` has fewer than 5 runs with confirmed outcome (OK/BAD) in `FEEDBACK.html`. Below this threshold, the data is too sparse to be a signal.
- **Filter PEND:** inject only runs with OK or BAD outcome — PEND means unconfirmed verdict
- **Falsification signal:** Pilot B produces a measurable signal if a senator's `modify_request` explicitly references a label or outcome from the injected context. Without this signal after 5 runs, Pilot B did not add value.
- **Complete reversibility:** stop injecting → behavior identical to A (do_nothing)

**Escalation to C:** if after 5 runs under Pilot B at least 1 senator references injected context, implement `priors.py --senator <name>`:
- The flag adds per-senator filtering over the existing logic (~50-60 lines)
- Must handle the multi-round schema `{rounds: [...]}`
- Injects the vote from the last round (not round 1)
- `priors.py` without `--senator` returns output identical to today (backward compat guaranteed)
- D (per_senator_json, 7 files + update script) remains off-table until Napoleon's gate: ≥20 senate runs, ≥80% outcome tracking

## Smoke test

Two levels:
```bash
cat scripts/senate_synth_fixture.json | python -X utf8 scripts/senate_synth.py   # fixture quick check
python -X utf8 scripts/test_senate_synth.py                                       # 9-test suite
```
The suite runs: prompt structure, fixture, verdict GO unanimous/GO supermajority (7/9), MODIFY-blocks, UNREACHABLE (under MIN_ACTIVE=5 via absent senators), unrecognized-vote, **multi-round position change (Law 2+4)**, **cross-questions violation (Law 2)**, **blocaj pending + blocaj resolution (Law 3)**, DEEPLY_SPLIT (sub-QUORUM splits), ABSTAIN hard-reject on schema v2 (legacy v1 still read), bundle persistence, collision-safe write. All must PASS before committing to `senate_synth.py` or any `prompts/senators/*.md`. Laws 6-8 are tested via manual CLI (smoke tests per Section E of TODO_SENATE_LAWS_AND_HEADLESS.md).

## Origin + architecture

- **Visual architecture:** [`architecture.html`](architecture.html) — **Senate** tab (dark theme; the 9 senators with specialties + dispatch flow + verdict logic + cross-questions matrix + blocaj resolution + the 5 Laws + file map).
- **Empirical justification:** `../experiments/New phase senat/deliberations/RUND2-deliberari.md`. Post PR `feat/senate-laws-2-3-4`, Laws 2-4 are opt-in multi-round; the multi-round format `{rounds: [...]}` is the only one supported.
