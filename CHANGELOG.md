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

## [1.1] — 2026-06

### Changed
- Sequential reordered **Generator-first** (anti-anchoring), with the
  irreversibility consent gate moved pre-dispatch (Step 1.6,
  `scope_gate.consent_required`, fail-safe) — #416, Senate 2026-06-13.
- Trias redesigned 6→4 sub-agents: the 3 per-personality pre-vote Skeptics
  replaced by **one post-vote `skeptic_on_chosen`** on the winner; cost
  3× → ~2.67× (skeptic-lever redesign, 2026-06-19).
- Fixed modes `parallel_skeptic` / `dialectic_skeptic` collapsed into the
  composable `skeptic_on_chosen` flag; `trias_split` deprecated (2026-05-17;
  legacy names remain accepted via `_LEGACY_MODE_ALIASES`).

### Removed
- **Parallel mode** and the silent 1-in-20 parallel audit
  (`scripts/audit_counter.py`) — #454, Senate GO_WITH_CONDITIONS, 0 divergences
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
