# Changelog

All notable changes to Consilium are recorded here, following
[Keep a Changelog](https://keepachangelog.com/). This project is source-available
under the Business Source License 1.1 (see `LICENSE`).

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
