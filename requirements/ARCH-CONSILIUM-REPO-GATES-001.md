---
milestone: v1.1
id: ARCH-CONSILIUM-REPO-GATES-001
status: confirmed
level: architecture
layer: aggregate
depends_on: [CONSILIUM-CHECK-DOC-DRIFT-001, CONSILIUM-CHECK-DOC-DRIFT-EXPLAINER-001, CONSILIUM-CHECK-PUBLIC-LEAK-001, CONSILIUM-CHECK-VERSIONS-001, CONSILIUM-RUN-EVALS-001, SKILL-RUN-CONSILIUM-001]
satisfies: [SYS-CONSILIUM-INTEGRITY-001]
owner: alxmax
risk: 1
---

# Repository gates

> The CI checks and local driver that keep the skill's docs, manifests and public tree honest.

## Description

Every line in this section is binding.

- `check_doc_drift.py` enforces parity between authoritative behaviour and the mode docs and explainer. [[CONSILIUM-CHECK-DOC-DRIFT-001]] [[CONSILIUM-CHECK-DOC-DRIFT-EXPLAINER-001]]
- `check_public_leak.py` blocks private-repo names and local paths, and `check_versions.py` keeps the manifests' semver aligned. [[CONSILIUM-CHECK-PUBLIC-LEAK-001]] [[CONSILIUM-CHECK-VERSIONS-001]]
- `run_evals.py` replays the regression scenarios in `evals/scenarios.json`. [[CONSILIUM-RUN-EVALS-001]]
- The run-consilium driver (`driver.py smoke`) runs every gate CI runs, so a local green predicts a green CI. [[SKILL-RUN-CONSILIUM-001]]

## Verify intent

- None - contract confirmed by the owner on 2026-09-21.

## Cases

- **CASE-1** — Given a new `scripts/test_*.py` not listed in `ci.yml`, when `check_doc_drift.py` runs, then it exits 1.
- **CASE-2** — Given a clean checkout, when `driver.py smoke` runs, then it ends with `OK - all green`.
- **CASE-3** — Given `plugin.json` and `marketplace.json` at different versions, when `check_versions.py` runs, then it exits 1.
