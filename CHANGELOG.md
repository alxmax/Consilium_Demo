# Changelog

All notable changes to Consilium are recorded here, following
[Keep a Changelog](https://keepachangelog.com/). This project is source-available
under the Business Source License 1.1 (see `LICENSE`).

## [1.8.0] — 2026-07-07

### Added
- **Opt-in personality-lens ladder (`--lens <name>`, default OFF).** Sequential can prepend one lens (`--lens essentialist`) to Generator→Conservator→Control; Dialectic's rung (`--lens essentialist`) puts **Essentialist on the decider** and **tints the Skeptic with the Verifier lens** (complementary roles, not a vote — `decider != skeptic`). No new sub-agent dispatch; lens text costs ~18% per-voice prompt tokens, so it is **off by default**, keeping the default path's cost unchanged.
- **Verifier lens Skeptic carve-out** (`prompts/voices/verifier_lens.md`): the Verifier lens is now coherent when tinted onto the Skeptic voice (previously it only described Generator/Control/Conservator roles). This is the "tint, no new file" mechanism — no separate skeptic-lens prompt is added. Locked by a new keyword assertion in `scripts/test_lens_bias.py`.
- **`telemetry.lens_applied`** (`{decider, skeptic?}`), validated by `scripts/validate_report.py`: present only on an opt-in `--lens` run, absent on default runs; for Dialectic the decider and skeptic lenses must differ (runtime `decider != skeptic` enforcement).

**Provenance — shipped OFF-by-default over a MODIFY verdict, documented per the audit's own condition.** Two same-day internal design reviews (2026-07-07, MODIFY; and a pinned refinement, MODIFY) returned MODIFY, not GO. The dominant, twice-repeated condition — ship **opt-in / default OFF** rather than a mode default — is honored here (this satisfies the user's hard cost constraint literally: 0 token delta unless the flag is set). The A-vs-B fork for "Verifier as skeptic" was resolved to **B (tint)** with the required coherence carve-out; pure-A (a new prompt file) was rejected by the audit as violating "no new files / cost unchanged." **Lens value remains empirically unproven** (Trias is 0/6 vs baseline on the only valid instrument — a saturated corpus, i.e. an absent test, not a failed one; `experiments/trias-discriminating-tasks-design.md`). Default-on is therefore **not** shipped and is gated on a future discriminator pilot (n≥10–20 on a non-saturated, oracle-validated code-deliberation corpus). This entry is the deliberate, traceable record of that override, per the design review's own condition.

## [1.7.0] — 2026-07-07

### Changed
- **Sequential's deliberation now runs as one dispatched sub-agent** (`subagents: 0 → 1`), mirroring the atomic unit Trias already uses per personality: Generator → Conservator → Control still run in a single shared context (unchanged internally — `strip_context.py` and Generator's turn-1 blindness still apply), but that context is now the sub-agent's own, not the orchestrator's. The sub-agent returns the three raw voice outputs (`generator_out`, `control_out`, `conservator_out`) **unmodified** — `aggregate_sequential()` is untouched. Dialectic inherits this automatically (`subagents: 1 → 2`, its own definition — "Sequential + Skeptic" — unchanged).
- Real wall-clock instrumentation for Sequential's dispatch (`telemetry.voices.sequential_dispatch.latency_ms`), replacing the previously-hardcoded `0` for in-context voices.
- `docs/architecture/src/modes.jsx` data fields updated to match (subagent counts, isolation description); the animated walkthrough step-by-step diagram for Sequential still depicts the pre-dispatch layout and has not been reworked to show a separate sub-agent box — tracked as a follow-up, not blocking.

**Provenance — shipped over a same-day MODIFY verdict, by explicit user override.** An independent internal design review examined this exact change twice, same day, and returned MODIFY both times (DEEPLY_SPLIT in round 1, MODIFY in round 2 after focal cross-examination) — concerns: unmeasured benefit magnitude, a likely net cost increase from losing prompt-cache warmth in a freshly dispatched sub-agent, and an invalid citation of Trias's atomic-dispatch precedent (Trias isolates personalities to protect voting integrity; Sequential has no vote to protect). The user reviewed both verdicts and instructed an explicit override. Implementation then ran through Trias (3 personalities + post-vote Skeptic) for the *how*, not the *whether*: the Skeptic caught and this release fixes a real correctness gap the review had not named — an earlier draft would have had the sub-agent return only `{chosen_approach, rationale, confidence}`, which would have silently disabled `aggregate_sequential()`'s entire veto cascade (BLOCK/REWORK/SHORT-CIRCUIT/ESCALATE never firing for Sequential again). All accepted tradeoffs are documented in `modes/sequential.md` § Accepted tradeoffs, not silently absorbed.

## [1.6.0] — 2026-07-07

### Added
- Declared falsifier on the chosen approach, **consumer-first** (design review
  `2026-07-07_011914-consilium-falsifier-round2-control-voice`, MODIFY 0/8/1
  — implement-now rejected; this ships the review-revised trim instead of the
  original clause): (1) `build_report.py` now persists Control's
  `strongest_objection` + `no_blocking_defect_attested` into the run JSON's
  control step — previously emitted mid-deliberation but never persisted;
  (2) `mark_outcome.py --auto-suggest` reads the declared falsifier
  (`strongest_objection.reason`) from the run JSON as the default `--reason`
  when scoring an outcome (explicit `--reason` wins; degrades gracefully on
  pre-1.6.0 runs); (3) `prompts/voices/control.md` Q5 amendment: when
  `no_blocking_defect_attested: true`, `strongest_objection.reason` must
  carry a falsifiable exit-claim about the likely-chosen candidate — an
  observable external to the verdict; verdict-restatement invalid.
  Red→green tests in `test_build_report.py` and `test_feedback_html.py`.
  **Measurement protocol (declared before landing):** 1.5.0 + 1.6.0 are one
  bundled treatment for all benchmarking purposes; no separate attribution
  of effects to either round. **Unvalidated for quality** — same discipline
  as 1.5.0, no quality-improvement claim made.

## [1.5.0] — 2026-07-07

### Added
- Prompt-only discipline transplant from an internal design-review framework
  into the 3 core voices (`prompts/voices/generator.md`, `conservator.md`, `control.md`):
  a Conservator silent-failure question (Q6), a merged Control rule requiring
  `strongest_objection` to be a testable claim anchored to a declared
  `hidden_assumptions` premise, a materiality/polite-retreat discipline on all
  three voices, and a `## Limits` disjointness section per voice. No JSON
  schema change, no new dispatches, no `aggregator.py`/`validate_report.py`
  edits — purely additive prompt text. Per design review run
  `2026-07-06_093007` (GO_WITH_CONDITIONS) and the trimmed spec from its
  reviewers' cross-questioning (the final blocking condition). `test_lens_bias.py` (4/4), `test_vote_degeneracy.py` (4/4), and
  `run_evals.py` (65/0) are identical before and after — zero verdict
  inversions. Manually verified on one qualitative example (not part of the
  scored corpus) that the new clauses produce the intended behavior: Q6 names
  the silent-failure mode explicitly instead of it surfacing scattered/implicit
  elsewhere, and `strongest_objection` cites a numbered premise instead of a
  free-floating claim. **Unvalidated for quality** — n=1, manual, no claim of
  improved deliberation quality is made or implied by this change.

## [Unreleased]

- Aggregator gate: reject `generator.preferred` not among the candidate ids (#464).
- Implement-gate: stub all fan-out targets in the red→green gate + pin mode
  confidence floors in the drift gate (#465).
- Deprecated scripts and Pass-2 prompts deleted; normative doc references
  updated (#466).
- Green-gate section + measured benchmark results in the architecture explainer
  and README (#467).
- Architecture explainer: 7 content drifts vs the repo corrected + 5 new drift
  invariants pinned (#468).
- Script robustness: 8 audit fixes — BOM/encoding hardening, empty-candidates
  guard, 0.0-score routing, stub-gate header scan (+RED tests) (#469).
- Docs: strict skeptic-band notation, runs-schema overhaul, stale refs cleaned
  post-#454/#466 (#470).
- Gates/evals: revived the dead pre-commit reqmap gate, driver↔CI parity,
  enforced legacy-alias removal milestones, leak-gate RED tests, #464 eval pins,
  measured benchmark docs (#472).
- Skeptic-lever contract coherence: runner_up input, tiebreak mode,
  addressable-keyed demolish predicate, post-#416 subagent semantics (#473).
- Migrated Sonnet 4.6 references to Claude Sonnet 5 (#474).
- `render_impl_preview.py`: opt-in Step 7 static HTML review page bundling spec,
  rationale, and the multi-file diff (#475).
- Reqmap: version provenance retagged to `CONSILIUM-VERSION-001` + stale
  acceptance/wording reworded (review 2026-07-03 batch b/d/e) (#476).
- Install docs: `.consilium/` gitignore noted as recommended-but-preference
  (keep tracked if you want the trail versioned) (#477).

## [1.4.3] — 2026-07-06

### Fixed
- The "Code integration pipeline" explainer section (`docs/architecture/src/extras.jsx`
  `ImplementSection`) never stated its own sub-agent count (3) or cost multiplier
  (~1.1×) anywhere in its text, unlike every other mode/flag (Sequential,
  Dialectic, Trias, `skeptic_on_chosen`), which all state cost + sub-agent count
  explicitly. Added the missing stat to `GATE_ITEMS` and a new
  `check_doc_drift.py` invariant (`check_implement_pipeline_spec_alignment`)
  pinning it against `modes/implement_pipeline.md`'s frontmatter.

## [1.4.2] — 2026-07-06

### Fixed
- Architecture explainer, README, benchmark instructions, and the
  `consilium_full` poster generator still named the retired Trias personality
  team (Pioneer/Architect/Steward) after the v3 lens rename (PR
  #482) replaced it with Essentialist/Verifier/Sentinel. Renamed everywhere
  (with descriptions rewritten to match each personality's actual lens, not
  just the label), regenerated both derived HTML artifacts, and added a new
  `check_doc_drift.py` invariant (`check_trias_personality_name_parity`) so a
  future personality-team change can't silently miss the explainer again.

## [1.4.1] — 2026-07-06

### Fixed
- Architecture explainer: the "What the CI green-gate runs" section had silently
  fallen behind `ci.yml` — PR #485's `check_versions.py` + CHANGELOG-entry gate
  had no matching `CI_CHECKS` card. Added the missing card and a new
  `check_doc_drift.py` invariant (`check_ci_checks_completeness`) that fails CI
  if a future gate ships with no matching card or explicit allowlist entry.
  Found by a Trias self-audit (3-0, confidence 0.95); the post-vote Skeptic
  caught and fixed an under-specified matching rule before it shipped.

## [1.4.0] — 2026-07-06

### Added
- Plugin manifest version-coherence gate: `scripts/check_versions.py` asserts
  `plugin.json` and `marketplace.json` semver agree, and CI now requires that
  any `plugin.json` version bump ships with a matching CHANGELOG entry —
  mirroring `requirement-manager`'s check. `marketplace.json` gained a
  `version` field for the first time (previously absent, now tracking
  `plugin.json`).

## [1.1] — 2026-06

### Changed
- Sequential reordered **Generator-first** (anti-anchoring), with the
  irreversibility consent gate moved pre-dispatch (Step 1.6,
  `scope_gate.consent_required`, fail-safe) — #416, review 2026-06-13.
- Trias redesigned 6→4 sub-agents: the 3 per-personality pre-vote Skeptics
  replaced by **one post-vote `skeptic_on_chosen`** on the winner; cost
  3× → ~2.67× (skeptic-lever redesign, 2026-06-19).
- Fixed modes `parallel_skeptic` / `dialectic_skeptic` collapsed into the
  composable `skeptic_on_chosen` flag; `trias_split` deprecated (2026-05-17;
  legacy names remain accepted via `_LEGACY_MODE_ALIASES`).

### Removed
- **Parallel mode** and the silent 1-in-20 parallel audit
  (`scripts/audit_counter.py`) — #454, review GO_WITH_CONDITIONS, 0 divergences
  in 41 empirical runs. Historical `mode: "parallel"` runs stay readable.
- Dialectic Pass-2 merge (`dialectic_merge.py` and the `*_pass2.md` prompts).

### Added
- Implement pipeline (post-GO: Coder → Test Writer ∥ Reviewer) with a
  red→green stub gate (`scripts/implement_pipeline.py`).
- Version provenance: git-describe stamp + resolvable `consilium_ref` per run
  (`scripts/version.py`); prior-deliberation passthrough.

## [1.0.0] — 2026-05-16

Initial public release, after a public-readiness pass (2026-05): closed a
benchmark answer-leak, hardened `.gitignore`, fixed three core-script bugs,
corrected benchmark doc-drift, made the architecture explainer's Trias dispatch
claim honest (parallel by spec mandate, serial in practice), added a README
usage example, scrubbed personal paths/artifacts, and added a stdlib CI
green-gate. Each change deliberated via `/consilium`.

### Deliberation engine
- Three adversarial voices — **Conservator** (risk/reversibility), **Generator**
  (alternatives, incl. `do_nothing`), **Control** (correctness + acceptance tests)
  — merged by an 8-component veto cascade (`scripts/aggregator.py`) into one
  canonical, validated report.
- Confidence scoring with per-mode floors (`scripts/confidence.py`); soft priors
  from a file-based feedback loop (`scripts/priors.py` + `.consilium/`).
- Scope gate (`scripts/scope_gate.py`) auto-skips trivial diffs; silent parallel
  cross-check audit (`scripts/audit_counter.py`).

### Modes
- **Sequential** (default, 1×), **Dialectic** (1.33×), **Trias** (3×, three
  personality lenses + democratic vote), and the composable
  **`skeptic_on_chosen`** flag.

### Tooling & docs
- Benchmark harness (`benchmark/`) comparing each mode to bare-model baselines
  against an external hidden oracle.
- Interactive architecture explainer (`docs/architecture.html`; React source
  under `docs/architecture/`, built by `build.py`).
- `run-consilium` companion skill (build / test / smoke / screenshot).
- Deterministic regression suite (`evals/`), mode-doc drift gate
  (`scripts/check_doc_drift.py`), and a stdlib-only CI green-gate.

### License
- Business Source License 1.1 © 2026 Schipor Alexandru; converts to Apache-2.0
  on 2030-05-16.
