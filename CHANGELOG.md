# Changelog

All notable changes to Consilium are recorded here, following
[Keep a Changelog](https://keepachangelog.com/). This project is source-available
under the Business Source License 1.1 (see `LICENSE`).

## [Unreleased]

Public-readiness pass (2026-05) ahead of the first tagged release: closed a
benchmark answer-leak, hardened `.gitignore`, fixed three core-script bugs,
corrected benchmark doc-drift, made the architecture explainer's Trias dispatch
claim honest (parallel by spec mandate, serial in practice), added a README
usage example, scrubbed personal paths/artifacts, and added a stdlib CI
green-gate. Each change deliberated via `/consilium`.

## [1.0.0] — unreleased

Initial public release.

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
