# Changelog

All notable changes to Consilium are recorded here, following
[Keep a Changelog](https://keepachangelog.com/). This project is source-available
under the Business Source License 1.1 (see `LICENSE`).

## [1.7.0] — 2026-07-07

### Reverted
- **Sequential's dispatch-as-sub-agent change (commit `6317a50`) is reverted** — Sequential returns to running Generator→Conservator→Control in the orchestrator's own context (`subagents: 1 → 0`); Dialectic returns to just its Skeptic dispatch (`subagents: 2 → 1`).
- **Why, in sequence, same day:** the change shipped over two same-day design-review MODIFY verdicts by explicit user override, on an admittedly unmeasured cost-benefit claim. A benchmark run then surfaced a real 6-8× cost/turn blowup on one Dialectic task. A third design-review investigation (2 rounds) returned MODIFY again. A fresh n=2 benchmark reproduction across all 6 cells (2 modes × 3 tasks) showed the instability diffuse across **both** modes rather than confined to Dialectic, and the originally-flagged cell did not reproduce on resample — but **5 of 6 cells got more expensive in absolute terms** rep-over-rep (only the one previously-flagged cell got cheaper). A targeted telemetry fix (recording real dispatch latency instead of stubbed zeros) was attempted and empirically failed to take effect even when explicit and present in the loaded docs. A follow-up tiebreaking review on the standing split verdict leaned toward "inconclusive noise, not proven dispatch-specific." A subsequent Trias deliberation (3 personalities + post-vote Skeptic) then recommended *keeping* the architecture and adding a structural turn/cost circuit breaker instead of reverting (2-1 vote; the post-vote Skeptic flagged the verification plan as inadequate but did not overturn the vote).
- **This release does not follow the Trias recommendation.** The user's own read of the absolute cost data (real dollar cost is up across most sampled cells, regardless of whether the underlying cause is cleanly attributable to `6317a50`) took priority: cost is the concern in practice, not settling attribution. The circuit-breaker idea remains a legitimate future addition (for Trias/any mode) but is not a substitute for removing a cost source once the user has decided the cost itself is unacceptable.
- **What is NOT resolved by this revert:** whether `6317a50` was in fact the cause of the observed turn/cost variance, or a pre-existing noise floor was contributing throughout, is still open — the revert removes the suspected cost source pragmatically rather than proving causation. If deliberation-context isolation from the implementation phase is wanted again in the future, an in-context transcript-truncation alternative (rather than a second dispatch boundary) was never prototyped and remains the recommended starting point, per two independent design reviews.

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
